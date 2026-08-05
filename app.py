import hashlib
import hmac
import os
import re
import time
import uuid
from collections import defaultdict, deque
from functools import wraps
from threading import Lock
from urllib.parse import quote

from flask import Flask, jsonify, render_template, request, send_from_directory
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

from config import Config
from modules.audio_processor import audio_processor
from modules.database import db
from modules.discover_data import DISCOVER_DATA, search_discover
from modules.drop_generator import generator
from modules.tts_engine import TTSManager


app = Flask(__name__, static_folder="static", template_folder="templates")
app.config["SECRET_KEY"] = Config.SECRET_KEY
app.config["UPLOAD_FOLDER"] = os.path.join(Config.STATIC_DIR, "generated", "uploads")
app.config["MAX_CONTENT_LENGTH"] = 15 * 1024 * 1024  # 15MB cap on all request bodies
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

tts_engine = TTSManager()


# =====================================================================
# Rate limiting
# =====================================================================

_rate_lock = Lock()
_rate_buckets = defaultdict(deque)
RATE_LIMIT = 10          # requests
RATE_WINDOW = 60         # seconds


def rate_limited(key_prefix):
    """
    In-memory per-process rate limiter keyed by client IP. Fine for a single
    Flask process; if you run multiple workers/instances behind a load
    balancer, each one keeps its own counters, so swap this for a shared
    store (e.g. Redis) if you scale out.
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            ip = request.headers.get("X-Forwarded-For", request.remote_addr) or "unknown"
            key = f"{key_prefix}:{ip}"
            now = time.time()
            with _rate_lock:
                bucket = _rate_buckets[key]
                while bucket and now - bucket[0] > RATE_WINDOW:
                    bucket.popleft()
                if len(bucket) >= RATE_LIMIT:
                    return jsonify({
                        "success": False,
                        "error": "Rate limit exceeded. Try again shortly.",
                    }), 429
                bucket.append(now)
            return fn(*args, **kwargs)
        return wrapper
    return decorator


# =====================================================================
# Helpers
# =====================================================================

def _issue_token(user_id):
    timestamp = int(time.time())
    payload = f"{user_id}:{timestamp}"
    signature = hmac.new(
        app.config["SECRET_KEY"].encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return f"{payload}:{signature}"


def _decode_token(token):
    if not token:
        return None
    parts = token.split(":")
    if len(parts) != 3:
        return None
    user_id, timestamp, signature = parts

    # BUGFIX: previously these were cast with int(...) further down with no
    # validation, so a malformed/non-numeric token (e.g. "abc:def:ghi") threw
    # an uncaught ValueError -> Flask 500 instead of a clean "unauthenticated".
    if not user_id.isdigit() or not timestamp.isdigit():
        return None

    payload = f"{user_id}:{timestamp}"
    expected = hmac.new(
        app.config["SECRET_KEY"].encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(signature, expected):
        return None
    if abs(int(time.time()) - int(timestamp)) > 7 * 24 * 60 * 60:
        return None
    return int(user_id)


def get_authenticated_user():
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()
        user_id = _decode_token(token)
        if user_id:
            return db.get_user_by_id(user_id)
    return None


def build_generation_response(script, final_path, cover_filename, drop_id, tts_result, fx_mode):
    """Build a safe JSON response for generation requests."""
    metadata = tts_result or {}
    filename = os.path.basename(final_path)
    return {
        "success": True,
        "script": script,
        "download_url": f"/static/generated/{filename}",
        "image_url": f"/static/generated/{cover_filename}" if cover_filename else None,
        "project": drop_id,
        "offline": not audio_processor.ffmpeg_available,
        "voice_used": metadata.get("voice"),
        "processing": {
            "rate": metadata.get("rate"),
            "pitch": metadata.get("pitch"),
            "volume": metadata.get("volume"),
            "fx_mode": fx_mode,
        },
        "brand": {
            "name": Config.APP_NAME,
            "version": Config.APP_VERSION,
            "focus": "Professional studio-ready audio",
        },
    }


def _mask_key(prefix: str) -> str:
    """Show only the prefix with a visual indicator that the rest is hidden."""
    if not prefix:
        return "****"
    return f"{prefix}..."


def _sanitize_drop_id(raw_drop_id: str) -> str:
    """
    BUGFIX: 'project' was taken straight from client JSON and joined into a
    filesystem path (os.path.join(Config.GENERATED_DIR, f"{drop_id}.mp3")).
    A value like '../../../etc/cron.d/evil' would escape GENERATED_DIR and
    let a client write files elsewhere on disk. Whitelist to safe characters.
    """
    if not raw_drop_id:
        return f"drop_{os.urandom(4).hex()}"
    cleaned = re.sub(r"[^A-Za-z0-9_\-]", "", str(raw_drop_id))[:64]
    return cleaned or f"drop_{os.urandom(4).hex()}"


# =====================================================================
# Pages & PWA
# =====================================================================

@app.get("/")
def index():
    return render_template("index.html")


@app.get("/offline.html")
def offline_page():
    return send_from_directory(app.root_path, "offline.html")


@app.get("/manifest.json")
def manifest():
    return jsonify({
        "name": Config.APP_NAME,
        "short_name": "DJ Drops",
        "description": Config.APP_DESCRIPTION,
        "start_url": "/",
        "scope": "/",
        "display": Config.PWA_DISPLAY,
        "theme_color": Config.PWA_THEME_COLOR,
        "background_color": Config.PWA_BACKGROUND_COLOR,
        "icons": [
            {"src": "/static/icons/icon-192.png", "sizes": "192x192", "type": "image/png"},
            {"src": "/static/icons/icon-512.png", "sizes": "512x512", "type": "image/png"},
        ],
    })


# =====================================================================
# Status & Trends
# =====================================================================

@app.get("/api/status")
def status():
    stats = db.get_stats()
    return jsonify({
        "status": "ok",
        "app": Config.APP_NAME,
        "version": Config.APP_VERSION,
        "ffmpeg_available": audio_processor.ffmpeg_available,
        "online": True,
        "tts_provider": tts_engine.provider,
        "features": [
            "AI voice generation",
            "Premium audio processing",
            "Library management",
            "Creator studio tools",
            "Studio presets and effects",
            "Voice recording workflow",
            "Account-based workflow",
            "Commercial API key management",
            "Professional creator analytics",
        ],
        "generated_count": stats.get("total_drops", 0),
    })


@app.post("/api/wizard_validate")
def wizard_validate():
    data = request.get_json(silent=True) or {}
    step = int(data.get("step", 1))
    errors = []

    if step == 1:
        dj_name = (data.get("dj_name") or "").strip()
        if not dj_name:
            errors.append("Please enter a DJ name")
        elif len(dj_name) < 2:
            errors.append("DJ name must be at least 2 characters")
    elif step == 2:
        if not data.get("genre"):
            errors.append("Please choose a genre")
        if not data.get("drop_type"):
            errors.append("Please choose a drop type")
    elif step == 3:
        if not data.get("voice"):
            errors.append("Please choose a voice profile")

    return jsonify({"valid": not errors, "errors": errors})


@app.get("/api/trends")
def trends():
    return jsonify({
        "success": True,
        "trending": ["Club Banger", "Amapiano", "Afrobeat", "Dancehall", "Radio", "Trap"],
    })


@app.get("/api/city_vibe")
def city_vibe():
    city = (request.args.get("city") or "").strip()
    if not city:
        return jsonify({"success": False, "error": "City is required"})

    lowered = city.lower()
    if any(term in lowered for term in ["lagos", "nairobi", "accra", "cape", "abuja"]):
        mood = "hype"
        temperature = 31
        vibe = "Afro-energy"
    elif any(term in lowered for term in ["london", "paris", "berlin", "amsterdam"]):
        mood = "luxury"
        temperature = 19
        vibe = "European elegance"
    elif any(term in lowered for term in ["miami", "bali", "la", "vegas", "nyc", "new york"]):
        mood = "festival"
        temperature = 28
        vibe = "High-impact nightlife"
    else:
        mood = "smooth"
        temperature = 24
        vibe = "Balanced atmosphere"

    return jsonify({
        "success": True,
        "data": {
            "city": city,
            "temperature": temperature,
            "vibe": vibe,
            "suggested_mood": mood,
        },
    })


@app.get("/api/suggest_names")
def suggest_names():
    style = (request.args.get("style") or "club_banger").lower()
    defaults = {
        "amapiano": ["DJ Ayo", "Kairo Sound", "Luxe Vibes"],
        "dancehall": ["King Riddim", "Bassline Nova", "DJ Sensa"],
        "radio": ["Studio One", "The Pulse Host", "Prime Radio"],
        "club_banger": ["DJ Beshi", "Nova Pulse", "Blast Mode"],
        "afrobeat": ["Afro Pulse", "Sankore", "DJ Mzuri"],
        "trap": ["Trap Crown", "Riot Echo", "Nocturne"],
    }
    suggestions = defaults.get(style, defaults["club_banger"])
    return jsonify({"success": True, "suggestions": suggestions})


@app.get("/api/studio-presets")
def studio_presets():
    presets = {
        "club_banger": {
            "label": "Club Banger",
            "effect": "club",
            "description": "Punchy, bright, and high-energy for event drops.",
            "accent": "#ff6b35",
        },
        "amapiano": {
            "label": "Amapiano",
            "effect": "wide",
            "description": "Smooth and spacious for modern African club sets.",
            "accent": "#00d084",
        },
        "dancehall": {
            "label": "Dancehall",
            "effect": "bass_boost",
            "description": "Heavy bass and swagger for high-impact drops.",
            "accent": "#9b59b6",
        },
        "radio": {
            "label": "Radio",
            "effect": "clean",
            "description": "Balanced and polished for broadcast and promos.",
            "accent": "#3498db",
        },
        "afrobeat": {
            "label": "Afrobeat",
            "effect": "cinematic",
            "description": "Warm, rich, and cinematic for curated mixes.",
            "accent": "#f7c531",
        },
        "trap": {
            "label": "Trap",
            "effect": "reverb",
            "description": "Dark, dramatic, and immersive for modern trap edits.",
            "accent": "#ff4757",
        },
    }
    return jsonify({"success": True, "presets": presets})


# =====================================================================
# Audio & String Tools
# =====================================================================

@app.post("/api/process_voice")
@rate_limited("process_voice")
def process_voice():
    audio_file = request.files.get("audio")
    effect = request.form.get("effect", "none")
    if not audio_file:
        return jsonify({"success": False, "error": "No audio uploaded"})

    filename = secure_filename(f"{uuid.uuid4().hex}_{audio_file.filename or 'voice.webm'}")
    target_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    audio_file.save(target_path)

    processed_path = audio_processor.apply_voice_effect(target_path, effect)
    filename = os.path.basename(processed_path)
    return jsonify({
        "success": True,
        "effect": effect,
        "audio_url": f"/static/generated/uploads/{filename}",
        "processing": {
            "applied": os.path.exists(processed_path),
            "source": "upload",
            "effect": effect,
        },
    })


@app.post("/api/string_tools")
def string_tools():
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    operation = data.get("operation") or "capitalize"

    if operation == "capitalize":
        result = " ".join(word.capitalize() for word in text.split()) if text else ""
    elif operation == "auto_punctuate":
        result = text if text.endswith(("!", "?", ".")) else f"{text}!"
    elif operation == "hashtags":
        words = re.findall(r"[A-Za-z0-9]+", text)
        result = " ".join(f"#{word}" for word in words)
    elif operation == "stutter_classic":
        first_word = text.split()[0] if text.split() else "DJ"
        result = f"{first_word[0]}-{first_word[0]}-{first_word[0]}-{text}" if first_word else text
    else:
        result = text

    return jsonify({"success": True, "result": result})


# =====================================================================
# Authentication
# =====================================================================

@app.post("/api/auth/register")
def register_user():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = (data.get("password") or "").strip()

    if not name or not email or not password:
        return jsonify({"success": False, "error": "Name, email, and password are required"}), 400
    if len(password) < 6:
        return jsonify({"success": False, "error": "Password must be at least 6 characters"}), 400

    existing = db.get_user_by_email(email)
    if existing:
        return jsonify({"success": False, "error": "A user with that email already exists"}), 409

    user = db.create_user({"name": name, "email": email, "password": password})
    return jsonify({
        "success": True,
        "user": {"id": user["id"], "name": user["name"], "email": user["email"]},
        "token": _issue_token(user["id"]),
    })


@app.post("/api/auth/login")
def login_user():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = (data.get("password") or "").strip()

    if not email or not password:
        return jsonify({"success": False, "error": "Email and password are required"}), 400

    user = db.get_user_by_email(email)
    if not user or not check_password_hash(user["password_hash"], password):
        return jsonify({"success": False, "error": "Invalid email or password"}), 401

    return jsonify({
        "success": True,
        "user": {"id": user["id"], "name": user["name"], "email": user["email"]},
        "token": _issue_token(user["id"]),
    })


@app.post("/api/auth/google")
def google_auth():
    """
    FIXED: previously trusted a client-supplied name/email with zero proof
    they came from Google -- anyone could POST an arbitrary email and get a
    valid session token for that account. Now requires the raw signed
    Google ID token ("credential") and verifies it against Google's public
    certs before trusting any claims inside it.
    """
    data = request.get_json(silent=True) or {}
    credential = data.get("credential")
    if not credential:
        return jsonify({"success": False, "error": "Missing credential"}), 400

    try:
        idinfo = id_token.verify_oauth2_token(
            credential, google_requests.Request(), Config.GOOGLE_CLIENT_ID
        )
    except ValueError:
        return jsonify({"success": False, "error": "Invalid Google credential"}), 401

    email = idinfo.get("email")
    if not email or not idinfo.get("email_verified"):
        return jsonify({"success": False, "error": "Google email not verified"}), 401
    name = idinfo.get("name") or idinfo.get("given_name") or "Google User"

    user = db.get_user_by_email(email)
    if not user:
        user = db.create_user({
            "name": name,
            "email": email,
            "password": str(uuid.uuid4()),
        })

    return jsonify({
        "success": True,
        "user": {"id": user["id"], "name": user["name"], "email": user["email"]},
        "token": _issue_token(user["id"]),
    })


@app.get("/api/auth/me")
def current_user():
    user = get_authenticated_user()
    if not user:
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    return jsonify({
        "success": True,
        "user": {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "theme": user.get("theme", "dark"),
            "language": user.get("language", "en"),
            "is_premium": user.get("is_premium", 0),
        },
    })


@app.post("/api/user/profile")
def update_user_profile():
    user = get_authenticated_user()
    if not user:
        return jsonify({"success": False, "error": "Not authenticated"}), 401

    data = request.get_json(silent=True) or {}
    profile_data = {
        "name": data.get("name", user["name"]),
        "bio": data.get("bio", ""),
        "avatar_url": data.get("avatar_url", ""),
        "theme": data.get("theme", "dark"),
        "language": data.get("language", "en"),
    }

    db.update_user_profile(user["id"], profile_data)
    return jsonify({"success": True, "user": profile_data})


# =====================================================================
# Presets
# =====================================================================

@app.post("/api/presets")
def save_preset():
    user = get_authenticated_user()
    if not user:
        return jsonify({"success": False, "error": "Not authenticated"}), 401

    data = request.get_json(silent=True) or {}
    preset_id = db.save_preset(user["id"], data)
    return jsonify({"success": True, "preset_id": preset_id})


@app.get("/api/presets")
def get_presets():
    user = get_authenticated_user()
    if not user:
        return jsonify({"success": False, "error": "Not authenticated"}), 401

    presets = db.get_presets(user["id"])
    return jsonify({"success": True, "presets": presets})


@app.delete("/api/presets/<preset_id>")
def delete_preset(preset_id):
    user = get_authenticated_user()
    if not user:
        return jsonify({"success": False, "error": "Not authenticated"}), 401

    deleted = db.delete_preset(int(preset_id), user["id"])
    return jsonify({"success": deleted})


# =====================================================================
# Prompt History
# =====================================================================

@app.post("/api/prompt-history")
def save_prompt_history():
    user = get_authenticated_user()
    if not user:
        return jsonify({"success": False, "error": "Not authenticated"}), 401

    data = request.get_json(silent=True) or {}
    db.add_prompt_history(user["id"], data)
    return jsonify({"success": True})


@app.get("/api/prompt-history")
def get_prompt_history():
    user = get_authenticated_user()
    if not user:
        return jsonify({"success": False, "error": "Not authenticated"}), 401

    history = db.get_prompt_history(user["id"])
    return jsonify({"success": True, "history": history})


# =====================================================================
# Analytics & Premium
# =====================================================================

@app.get("/api/analytics")
def get_analytics():
    user = get_authenticated_user()
    if not user:
        return jsonify({"success": False, "error": "Not authenticated"}), 401

    analytics = db.get_or_create_analytics(user["id"])
    drops = db.get_drops(user_id=user["id"])
    total_drops = len(drops)

    genres = {}
    for drop in drops:
        genre = drop.get("genre", "Unknown")
        genres[genre] = genres.get(genre, 0) + 1

    favorite_genre = max(genres, key=genres.get) if genres else None

    return jsonify({
        "success": True,
        "analytics": {
            "total_drops": total_drops,
            "favorite_genre": favorite_genre,
            "genre_breakdown": genres,
            "total_shares": analytics.get("total_shares", 0),
        },
    })


@app.post("/api/share")
def track_share():
    user = get_authenticated_user()
    if not user:
        return jsonify({"success": False, "error": "Not authenticated"}), 401

    data = request.get_json(silent=True) or {}
    platform = data.get("platform", "unknown")

    db.log_stat(user["id"], f"share_{platform}")
    current = db.get_or_create_analytics(user["id"])
    db.update_analytics(user["id"], {"total_shares": current.get("total_shares", 0) + 1})

    return jsonify({"success": True})


@app.post("/api/premium/upgrade")
def upgrade_premium():
    user = get_authenticated_user()
    if not user:
        return jsonify({"success": False, "error": "Not authenticated"}), 401

    db.set_premium(user["id"], True)
    return jsonify({"success": True, "message": "Welcome to Premium!"})


# =====================================================================
# API Key Management
# =====================================================================

@app.get("/api/keys")
def list_api_keys():
    user = get_authenticated_user()
    if not user:
        return jsonify({"success": False, "error": "Not authenticated"}), 401

    keys = db.get_api_keys(user["id"])
    safe_keys = []
    for k in keys:
        safe_keys.append({
            "id": k.get("id"),
            "name": k.get("name", "Studio App"),
            "prefix": _mask_key(k.get("key_prefix", "")),
            "created_at": k.get("created_at"),
            "last_used_at": k.get("last_used_at"),
            "is_active": bool(k.get("is_active", 1)),
        })

    return jsonify({"success": True, "keys": safe_keys})


@app.post("/api/keys")
def create_api_key():
    user = get_authenticated_user()
    if not user:
        return jsonify({"success": False, "error": "Not authenticated"}), 401

    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "Studio App").strip()

    if len(name) < 1 or len(name) > 64:
        return jsonify({"success": False, "error": "Key name must be 1–64 characters"}), 400

    if db.count_active_api_keys(user["id"]) >= 10:
        return jsonify({
            "success": False,
            "error": "Maximum 10 active API keys allowed. Revoke an old key first.",
        }), 429

    result = db.create_api_key(user["id"], name)

    return jsonify({
        "success": True,
        "id": result["id"],
        "name": result["name"],
        "key": result["key"],
        "prefix": result["prefix"],
        "warning": "Copy this key now. You will not be able to see it again.",
    })


@app.patch("/api/keys/<int:key_id>")
def update_api_key(key_id):
    user = get_authenticated_user()
    if not user:
        return jsonify({"success": False, "error": "Not authenticated"}), 401

    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()

    if not name:
        return jsonify({"success": False, "error": "Name is required"}), 400
    if len(name) > 64:
        return jsonify({"success": False, "error": "Name must be 64 characters or less"}), 400

    updated = db.update_api_key(key_id, user["id"], {"name": name})
    if not updated:
        return jsonify({"success": False, "error": "Key not found or access denied"}), 404

    return jsonify({"success": True, "message": "API key renamed"})


@app.delete("/api/keys/<int:key_id>")
def delete_api_key(key_id):
    user = get_authenticated_user()
    if not user:
        return jsonify({"success": False, "error": "Not authenticated"}), 401

    deleted = db.delete_api_key(key_id, user["id"])
    if not deleted:
        return jsonify({"success": False, "error": "Key not found or access denied"}), 404

    return jsonify({"success": True, "message": "API key revoked"})


@app.post("/api/keys/validate")
def validate_api_key():
    data = request.get_json(silent=True) or {}
    api_key = (data.get("api_key") or "").strip()

    if not api_key:
        return jsonify({"success": False, "valid": False, "error": "API key is required"}), 400

    record = db.get_api_key_user(api_key)
    if not record:
        return jsonify({"success": False, "valid": False, "error": "Invalid or revoked API key"}), 401

    return jsonify({
        "success": True,
        "valid": True,
        "user_id": record["user_id"],
        "name": record["name"],
    })


# =====================================================================
# Creator Toolkit
# =====================================================================

@app.get("/api/creator-toolkit")
def creator_toolkit():
    goal = (request.args.get("goal") or "youtube").lower()
    genre = (request.args.get("genre") or "club_banger").lower()
    genre_labels = {
        "amapiano": "Amapiano",
        "dancehall": "Dancehall",
        "radio": "Radio",
        "club_banger": "Club Banger",
        "afrobeat": "Afrobeat",
        "trap": "Trap",
    }

    software_matches = [
        {"name": "Serato DJ Pro", "reason": "Best for polished live sets and club-ready cueing.", "level": "Pro"},
        {"name": "Rekordbox", "reason": "Excellent for organizers and performers who need reliable export workflows.", "level": "Beginner-Pro"},
        {"name": "VirtualDJ", "reason": "A flexible option for creators building a fast, modern setup.", "level": "Beginner"},
    ]

    if goal == "software":
        software_matches = [
            {"name": "DJay Pro AI", "reason": "Ideal for creators who want AI-assisted workflow and smooth mobile control.", "level": "Beginner-Pro"},
            {"name": "Serato DJ Pro", "reason": "Great for professional club and event performance setups.", "level": "Pro"},
            {"name": "Mixxx", "reason": "A strong free option for learning and experimenting.", "level": "Free"},
        ]

    youtube_hooks = [
        f"Show the {genre_labels.get(genre, genre)} energy in the first 5 seconds of your teaser.",
        "Use a fast hook, sharp cuts, and a clean CTA to convert viewers into followers.",
        "Pair the drop with a strong caption and a cross-platform promo line.",
    ]

    launch_prompts = [
        f"Launch a {genre_labels.get(genre, genre)} campaign with one premium intro drop and one teaser clip.",
        "Publish a short behind-the-scenes clip to build anticipation before the full drop release.",
        "Use your saved library to create a release pack for DJs, promoters, and radio hosts.",
    ]

    return jsonify({
        "success": True,
        "goal": goal,
        "genre": genre_labels.get(genre, genre),
        "software_matches": software_matches,
        "youtube_hooks": youtube_hooks,
        "launch_prompts": launch_prompts,
    })


# =====================================================================
# Library
# =====================================================================

@app.get("/api/library")
def get_library():
    """
    FIXED: previously called db.get_drops() with no filter, returning every
    user's saved drops (names, scripts, download URLs) to any anonymous
    caller. Now scoped to the authenticated user; anonymous callers get an
    empty list instead of everyone's data.
    """
    user = get_authenticated_user()
    drops = db.get_drops(user_id=user["id"]) if user else []
    return jsonify({"success": True, "drops": drops})


@app.post("/api/library")
def save_library():
    user = get_authenticated_user()
    data = request.get_json(silent=True) or {}
    user_id = user["id"] if user else None
    data["user_id"] = user_id
    saved = db.add_drop(data)
    return jsonify({"success": saved})


@app.delete("/api/library/<drop_id>")
def delete_library(drop_id):
    # BUGFIX: this was the only delete endpoint in the file with no auth
    # check at all -- any anonymous caller could delete any user's saved
    # drop by id. Brought in line with delete_preset/delete_api_key, which
    # both require auth + ownership before deleting.
    user = get_authenticated_user()
    if not user:
        return jsonify({"success": False, "error": "Not authenticated"}), 401

    owned_drops = db.get_drops(user_id=user["id"])
    if not any(str(d.get("id")) == str(drop_id) for d in owned_drops):
        return jsonify({"success": False, "error": "Drop not found or access denied"}), 404

    deleted = db.delete_drop(drop_id)
    return jsonify({"success": deleted})


# =====================================================================
# Search & Discover
# =====================================================================

@app.get("/api/search")
def search():
    query = (request.args.get("q") or "").strip()
    results = search_discover(query) if query else DISCOVER_DATA
    return jsonify({"success": True, "results": results})


@app.get("/api/web_search")
def web_search():
    query = (request.args.get("q") or "").strip()
    if not query:
        return jsonify({"success": True, "results": []})

    encoded_query = quote(query)
    google_url = f"https://www.google.com/search?q={encoded_query}"

    results = []
    for category, items in DISCOVER_DATA.items():
        category_label = category.replace("_", " ")
        if query.lower() in category_label.lower():
            for item in items[:3]:
                results.append({
                    "title": item.get("name") or item.get("title") or "Discover item",
                    "snippet": f"Relevant {category_label} resource for {query}",
                    "source": category_label.title(),
                    "url": google_url,
                    "google_url": google_url,
                })
            if len(results) >= 5:
                break
            continue

        for item in items:
            item_text = " ".join(str(value) for value in item.values())
            if query.lower() in item_text.lower():
                results.append({
                    "title": item.get("name") or item.get("title") or "Discover item",
                    "snippet": f"Relevant {category_label} resource for {query}",
                    "source": category_label.title(),
                    "url": google_url,
                    "google_url": google_url,
                })
        if len(results) >= 5:
            break

    if not results:
        results.append({
            "title": f"Search the web for {query}",
            "snippet": "Open Google to find more results about this topic.",
            "source": "Google",
            "url": google_url,
            "google_url": google_url,
        })

    return jsonify({"success": True, "results": results})


@app.get("/api/dj-groups")
def dj_groups():
    return jsonify({"success": True, **DISCOVER_DATA})


@app.get("/api/streaming-apps")
def streaming_apps():
    return jsonify({"success": True, "streaming_apps": DISCOVER_DATA["streaming_apps"]})


@app.get("/api/dj-software")
def dj_software():
    return jsonify({"success": True, "dj_software": DISCOVER_DATA["dj_software"]})


@app.get("/api/festivals")
def festivals():
    return jsonify({"success": True, "festivals": DISCOVER_DATA["festivals"]})


@app.get("/api/theater-streaming")
def theater_streaming():
    return jsonify({"success": True, "theater_streaming": DISCOVER_DATA["theater_streaming"]})


@app.get("/api/all")
def all_discover_data():
    return jsonify({"success": True, "data": DISCOVER_DATA})


# =====================================================================
# Generation
# =====================================================================

@app.post("/api/generate")
@rate_limited("generate")
def generate_drop():
    data = request.get_json(silent=True) or {}

    dj_name = data.get("dj_name", "Studio Voice")
    genre = data.get("genre", "club_banger")
    drop_type = data.get("drop_type", "intro")
    mood = data.get("mood", "hype")
    energy = data.get("energy", 8)
    fx_mode = data.get("fx_mode", "dry")

    custom_script = (data.get("custom_script") or "").strip()
    training_example = (data.get("training_example") or "").strip()

    if custom_script:
        script = custom_script
    elif training_example:
        script = generator.generate_training_based(dj_name=dj_name, training_example=training_example)
    else:
        script = generator.generate_script(
            dj_name=dj_name,
            genre=genre,
            drop_type=drop_type,
            mood=mood,
            energy=energy,
            city=data.get("city"),
            use_stutter=bool(data.get("use_stutter")),
            user_stutter=data.get("user_stutter"),
        )

    # BUGFIX: drop_id (from client field "project") was joined into a
    # filesystem path with no sanitization -- see _sanitize_drop_id() above.
    drop_id = _sanitize_drop_id(data.get("project"))
    output_path = os.path.join(Config.GENERATED_DIR, f"{drop_id}.mp3")
    tts_result = tts_engine.generate(
        text=script,
        output_path=output_path,
        voice=data.get("voice"),
        rate=data.get("rate", 175),
        pitch=data.get("pitch", 0),
        volume=data.get("volume", 200),
    )

    if audio_processor.ffmpeg_available and fx_mode != "dry":
        try:
            processed_path = audio_processor.apply_fx(output_path, fx_mode, genre, energy)
            if processed_path and os.path.exists(processed_path):
                output_path = processed_path
        except Exception:
            pass

    return jsonify(build_generation_response(
        script=script,
        final_path=output_path,
        cover_filename=None,
        drop_id=drop_id,
        tts_result=tts_result,
        fx_mode=fx_mode,
    ))


# =====================================================================
# Main
# =====================================================================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)