import os
import re
import uuid
from flask import Flask, jsonify, render_template, request, send_from_directory
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
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

tts_engine = TTSManager()


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
            "Discover marketplace insights",
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
    suggestions = {
        "amapiano": ["DJ Ayo", "Kairo Sound", "Luxe Vibes"],
        "dancehall": ["King Riddim", "Bassline Nova", "DJ Sensa"],
        "radio": ["Studio One", "The Pulse Host", "Prime Radio"],
        "club_banger": ["DJ Beshi", "Nova Pulse", "Blast Mode"],
        "afrobeat": ["Afro Pulse", "Sankore", "DJ Mzuri"],
        "trap": ["Trap Crown", "Riot Echo", "Nocturne"],
    }.get(style, suggestions["club_banger"])
    return jsonify({"success": True, "suggestions": suggestions})


@app.post("/api/process_voice")
def process_voice():
    audio_file = request.files.get("audio")
    effect = request.form.get("effect", "none")
    if not audio_file:
        return jsonify({"success": False, "error": "No audio uploaded"})

    filename = secure_filename(f"{uuid.uuid4().hex}_{audio_file.filename or 'voice.webm'}")
    target_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    audio_file.save(target_path)

    return jsonify({
        "success": True,
        "effect": effect,
        "audio_url": f"/static/generated/uploads/{filename}",
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


@app.get("/api/library")
def get_library():
    drops = db.get_drops()
    return jsonify({"success": True, "drops": drops})


@app.post("/api/library")
def save_library():
    data = request.get_json(silent=True) or {}
    saved = db.add_drop(data)
    return jsonify({"success": saved})


@app.delete("/api/library/<drop_id>")
def delete_library(drop_id):
    deleted = db.delete_drop(drop_id)
    return jsonify({"success": deleted})


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

    results = []
    for category, items in DISCOVER_DATA.items():
        for item in items:
            item_text = " ".join(str(value) for value in item.values())
            if query.lower() in item_text.lower():
                results.append({
                    "title": item.get("name") or item.get("title") or "Discover item",
                    "snippet": f"Relevant {category.replace('_', ' ')} resource for {query}",
                    "source": category.replace("_", " ").title(),
                    "url": "#",
                })
        if len(results) >= 5:
            break

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


@app.post("/api/generate")
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

    drop_id = data.get("project") or f"drop_{os.urandom(4).hex()}"
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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)

