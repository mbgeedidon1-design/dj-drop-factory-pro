"""DJ Drop Factory Pro v5.0 - Production Backend
PWA-Ready Flask API with Edge TTS, FFmpeg Audio Processing, and SQLite Library
"""
import os
import sys
import json
import random
import requests
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory, render_template, make_response
from flask_cors import CORS

# Add modules to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'modules'))

from config import Config
from database import db
from tts_engine import tts
from audio_processor import audio_processor
from drop_generator import generator
from discover_data import DISCOVER_DATA, search_discover
from utils import generate_drop_id, generate_cover_image, sanitize_filename

app = Flask(__name__, 
            template_folder=Config.TEMPLATES_DIR,
            static_folder=Config.STATIC_DIR)
app.config.from_object(Config)
CORS(app)

# =============================================================================
# SECURITY HEADERS (Required for PWA App Capabilities)
# =============================================================================
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Permissions-Policy'] = 'accelerometer=(), camera=(), geolocation=(), gyroscope=(), magnetometer=(), microphone=(self), payment=(), usb=()'
    # Content Security Policy
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data: blob:; "
        "media-src 'self' blob:; "
        "connect-src 'self'; "
        "manifest-src 'self'; "
        "worker-src 'self';"
    )
    return response

# =============================================================================
# STATIC FILES & PWA ASSETS
# =============================================================================
@app.route('/')
def index():
    return send_from_directory(Config.TEMPLATES_DIR, 'index.html')

@app.route('/manifest.json')
def manifest():
    """Serve PWA Manifest with full scoring capability"""
    manifest_data = {
        "id": "/dj-drop-factory/?source=pwa",
        "name": "DJ Drop Factory Pro",
        "short_name": "DJ Drop Factory",
        "description": "AI-powered DJ Drop Generator with premium voice synthesis, audio effects, and library management. Create professional DJ drops in seconds.",
        "start_url": "/",
        "scope": "/",
        "display": "standalone",
        "display_override": ["standalone", "fullscreen", "minimal-ui"],
        "orientation": "portrait",
        "theme_color": "#0a0a0f",
        "background_color": "#050508",
        "lang": "en",
        "dir": "ltr",
        "categories": ["music", "entertainment", "productivity", "utilities"],
        "icons": [
            {
                "src": "/static/icons/icon-192.png",
                "sizes": "192x192",
                "type": "image/png",
                "purpose": "any"
            },
            {
                "src": "/static/icons/icon-512.png",
                "sizes": "512x512",
                "type": "image/png",
                "purpose": "any"
            },
            {
                "src": "/static/icons/icon-maskable-192.png",
                "sizes": "192x192",
                "type": "image/png",
                "purpose": "maskable"
            },
            {
                "src": "/static/icons/icon-maskable-512.png",
                "sizes": "512x512",
                "type": "image/png",
                "purpose": "maskable"
            }
        ],
        "screenshots": [
            {
                "src": "/static/screenshots/screenshot1.png",
                "sizes": "430x932",
                "type": "image/png",
                "form_factor": "narrow",
                "label": "Create DJ Drops with AI"
            },
            {
                "src": "/static/screenshots/screenshot2.png",
                "sizes": "430x932",
                "type": "image/png",
                "form_factor": "narrow",
                "label": "Voice Recorder & Effects"
            },
            {
                "src": "/static/screenshots/screenshot3.png",
                "sizes": "1280x720",
                "type": "image/png",
                "form_factor": "wide",
                "label": "Library & Discover"
            }
        ],
        "shortcuts": [
            {
                "name": "Create Drop",
                "short_name": "Create",
                "description": "Quickly create a new DJ drop",
                "url": "/?action=create",
                "icons": [{"src": "/static/icons/icon-96.png", "sizes": "96x96"}]
            },
            {
                "name": "My Library",
                "short_name": "Library",
                "description": "View saved DJ drops",
                "url": "/?action=library",
                "icons": [{"src": "/static/icons/icon-96.png", "sizes": "96x96"}]
            },
            {
                "name": "Discover",
                "short_name": "Discover",
                "description": "Explore DJ tools and festivals",
                "url": "/?action=discover",
                "icons": [{"src": "/static/icons/icon-96.png", "sizes": "96x96"}]
            }
        ],
        "share_target": {
            "action": "/share-target",
            "method": "POST",
            "enctype": "multipart/form-data",
            "params": {
                "title": "name",
                "text": "description",
                "url": "link"
            }
        },
        "handle_links": "preferred",
        "launch_handler": {
            "client_mode": ["navigate-existing", "auto"]
        },
        "edge_side_panel": {
            "preferred_width": 400
        },
        "related_applications": [
            {
                "platform": "play",
                "url": "https://play.google.com/store/apps/details?id=com.djdropfactory.app",
                "id": "com.djdropfactory.app"
            },
            {
                "platform": "itunes",
                "url": "https://apps.apple.com/app/dj-drop-factory/id1234567890"
            }
        ],
        "prefer_related_applications": False,
        "iarc_rating_id": "",
        "features": ["cross-platform", "offline", "audio-processing"],
        "widgets": []
    }
    return jsonify(manifest_data)

@app.route('/service-worker.js')
def service_worker():
    """Serve the service worker with proper MIME type"""
    response = make_response(send_from_directory(Config.BASE_DIR, 'service-worker.js'))
    response.headers['Content-Type'] = 'application/javascript'
    response.headers['Service-Worker-Allowed'] = '/'
    return response

@app.route('/offline.html')
def offline():
    return send_from_directory(Config.BASE_DIR, 'offline.html')

# =============================================================================
# API ENDPOINTS
# =============================================================================

@app.route('/api/status', methods=['GET'])
def api_status():
    """Check server status and capabilities"""
    return jsonify({
        "success": True,
        "online": True,
        "ffmpeg_available": audio_processor.ffmpeg_available,
        "version": Config.APP_VERSION,
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/heartbeat', methods=['GET'])
def api_heartbeat():
    """Heartbeat endpoint for client health checks"""
    return jsonify({
        "success": True,
        "online": True,
        "ffmpeg": audio_processor.ffmpeg_available,
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/generate', methods=['POST'])
def api_generate():
    """Generate a DJ drop with TTS and audio processing"""
    try:
        data = request.get_json() or {}
        device_id = request.headers.get('X-Device-ID', 'unknown')

        mode = data.get('mode', 'ai')
        dj_name = data.get('dj_name', 'DJ Beshi')
        genre = data.get('genre', 'club_banger')
        drop_type = data.get('drop_type', 'intro')
        mood = data.get('mood', 'aggressive')
        energy = int(data.get('energy', 8))
        voice = data.get('voice', '4')
        city = data.get('city', '')
        use_stutter = data.get('use_stutter', False)
        user_stutter = data.get('user_stutter', '')
        custom_script = data.get('custom_script', '')
        training_example = data.get('training_example', '')
        fx_mode = data.get('fx_mode', 'auto')
        vocal_gain = float(data.get('vocal_gain', Config.DEFAULT_VOCAL_GAIN))
        bg_gain = float(data.get('bg_gain', Config.DEFAULT_BG_GAIN))

        # Generate script
        if mode == 'strict' and custom_script:
            script = custom_script
        elif mode == 'training' and training_example:
            script = generator.generate_training_based(dj_name, training_example)
        else:
            script = generator.generate_script(
                dj_name=dj_name,
                genre=genre,
                drop_type=drop_type,
                mood=mood,
                energy=energy,
                city=city,
                use_stutter=use_stutter,
                user_stutter=user_stutter
            )

        # Generate unique ID
        drop_id = generate_drop_id()
        base_filename = sanitize_filename(f"{dj_name}_{genre}_{drop_id}")

        # Generate TTS audio
        tts_result = tts.generate(
            text=script,
            voice_id=voice,
            energy=energy,
            mood=mood,
            drop_type=drop_type,
            output_filename=f"{base_filename}_raw.mp3"
        )

        # Generate background beat
        bg_beat = audio_processor.generate_background_beat(genre, duration_ms=8000, energy=energy)
        bg_path = os.path.join(Config.GENERATED_DIR, f"{base_filename}_bg.mp3")
        bg_beat.export(bg_path, format="mp3", bitrate=Config.AUDIO_BITRATE)

        # Mix vocal and background
        mixed_path = os.path.join(Config.GENERATED_DIR, f"{base_filename}_mixed.mp3")
        final_path = audio_processor.mix_vocal_and_bg(
            tts_result['path'], bg_path, vocal_gain, bg_gain, mixed_path
        )

        # Apply FX
        if fx_mode != 'dry':
            final_path = audio_processor.apply_fx(final_path, fx_mode, genre, energy)

        # Generate cover image
        cover_filename = generate_cover_image(dj_name, genre, drop_type, Config.GENERATED_DIR)

        # Log stat
        db.log_stat(device_id, 'generate', genre, drop_type)

        return jsonify({
            "success": True,
            "script": script,
            "download_url": f"/static/generated/{os.path.basename(final_path)}",
            "image_url": f"/static/generated/{cover_filename}" if cover_filename else None,
            "project": drop_id,
            "offline": not audio_processor.ffmpeg_available,
            "voice_used": tts_result['voice'],
            "processing": {
                "rate": tts_result['rate'],
                "pitch": tts_result['pitch'],
                "volume": tts_result['volume'],
                "fx_mode": fx_mode
            }
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "offline": True
        }), 500

@app.route('/api/wizard_validate', methods=['POST'])
def api_wizard_validate():
    """Validate wizard step data"""
    data = request.get_json() or {}
    step = data.get('step', 1)

    errors = []
    if step == 1:
        if not data.get('dj_name', '').strip():
            errors.append("DJ Name is required")
    elif step == 2:
        if not data.get('genre'):
            errors.append("Genre is required")

    return jsonify({
        "valid": len(errors) == 0,
        "errors": errors
    })

@app.route('/api/trends', methods=['GET'])
def api_trends():
    """Get trending genres"""
    trending = ["Amapiano", "Afrobeat", "Dancehall", "Trap", "Drill", "Bacardi"]
    return jsonify({
        "success": True,
        "trending": trending,
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/city_vibe', methods=['GET'])
def api_city_vibe():
    """Get city vibe and suggested mood"""
    city = request.args.get('city', '').strip()
    if not city:
        return jsonify({"success": False, "error": "City required"}), 400

    # Simple mapping (in production, use weather API)
    city_moods = {
        "lagos": {"vibe": "Energetic", "suggested_mood": "hype", "temperature": 32},
        "london": {"vibe": "Gritty", "suggested_mood": "dark", "temperature": 15},
        "nyc": {"vibe": "Hustle", "suggested_mood": "aggressive", "temperature": 22},
        "la": {"vibe": "Chill", "suggested_mood": "smooth", "temperature": 25},
        "johannesburg": {"vibe": "Vibrant", "suggested_mood": "hype", "temperature": 28},
        "accra": {"vibe": "Warm", "suggested_mood": "festival", "temperature": 30},
    }

    city_lower = city.lower()
    data = city_moods.get(city_lower, {
        "vibe": "Unique",
        "suggested_mood": "hype",
        "temperature": random.randint(15, 35)
    })

    return jsonify({
        "success": True,
        "data": data
    })

@app.route('/api/suggest_names', methods=['GET'])
def api_suggest_names():
    """Suggest DJ names based on style"""
    style = request.args.get('style', 'club_banger')

    name_pools = {
        "amapiano": ["DJ Piano King", "Yanos Master", "Log Drum", "Ama DJ", "Phori Vibes"],
        "dancehall": ["Selector Fire", "Sound Boy", "Riddim Killer", "Bashment Boss", "Dancehall Don"],
        "club_banger": ["DJ Hype", "Club Crusher", "Bass Drop", "Party Starter", "Turn Up King"],
        "afrobeat": ["Afro Commander", "Naija Vibes", "Afro Fusion", "Wizzy Beats", "Burna Sound"],
        "trap": ["808 God", "Trap Lord", "Hood Legend", "Drill Master", "Street King"],
        "radio": ["Radio Host", "Voice of", "Airwave", "Frequency", "Broadcast King"],
    }

    suggestions = name_pools.get(style, name_pools["club_banger"])
    return jsonify({
        "success": True,
        "suggestions": suggestions
    })

@app.route('/api/process_voice', methods=['POST'])
def api_process_voice():
    """Apply voice effect to uploaded audio"""
    try:
        if 'audio' not in request.files:
            return jsonify({"success": False, "error": "No audio file"}), 400

        audio_file = request.files['audio']
        effect = request.form.get('effect', 'none')

        if effect == 'none':
            return jsonify({"success": True, "audio_url": "", "effect": "none"})

        # Save uploaded file
        upload_id = generate_drop_id()
        input_path = os.path.join(Config.GENERATED_DIR, f"upload_{upload_id}.webm")
        audio_file.save(input_path)

        # Apply effect
        output_path = audio_processor.apply_voice_effect(input_path, effect)

        return jsonify({
            "success": True,
            "audio_url": f"/static/generated/{os.path.basename(output_path)}",
            "effect": effect
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/string_tools', methods=['POST'])
def api_string_tools():
    """Apply string manipulation tools"""
    data = request.get_json() or {}
    text = data.get('text', '')
    operation = data.get('operation', '')

    result = text

    if operation == 'capitalize':
        result = text.title()
    elif operation == 'auto_punctuate':
        result = text.strip()
        if result and result[-1] not in '.!?':
            result += '!'
    elif operation == 'hashtags':
        words = text.split()
        result = ' '.join([f"#{w}" if not w.startswith('#') else w for w in words])
    elif operation == 'stutter_classic':
        words = text.strip().split()
        if words:
            first = words[0]
            stutter = f"{first[0]}-{first[0]}-{first[0]}-{first}"
            result = stutter + ' ' + ' '.join(words[1:])

    return jsonify({
        "success": True,
        "result": result,
        "operation": operation
    })

@app.route('/api/library', methods=['GET', 'POST'])
def api_library():
    """Get or add library items"""
    if request.method == 'POST':
        data = request.get_json() or {}
        success = db.add_drop(data)
        return jsonify({"success": success, "message": "Saved" if success else "Already exists"})

    # GET
    drops = db.get_drops()
    # Format for frontend
    formatted = []
    for drop in drops:
        formatted.append({
            "id": drop['drop_id'],
            "title": drop['title'] or drop['script'][:50] + '...',
            "script": drop['script'],
            "url": drop['audio_url'],
            "image_url": drop['image_url'],
            "genre": drop['genre'],
            "date": drop['created_at'],
            "dj_name": drop['dj_name']
        })

    return jsonify({"success": True, "drops": formatted})

@app.route('/api/library/<drop_id>', methods=['DELETE'])
def api_library_delete(drop_id):
    """Delete a library item"""
    deleted = db.delete_drop(drop_id)
    return jsonify({"success": deleted, "message": "Deleted" if deleted else "Not found"})

@app.route('/api/search', methods=['GET'])
def api_search():
    """Search internal discover data"""
    query = request.args.get('q', '')
    if not query:
        return jsonify({"success": False, "error": "Query required"}), 400

    results = search_discover(query)
    return jsonify({"success": True, "results": results})

@app.route('/api/web_search', methods=['GET'])
def api_web_search():
    """Proxy web search (in production, use a proper search API)"""
    query = request.args.get('q', '')
    if not query:
        return jsonify({"success": False, "error": "Query required"}), 400

    # Return mock results for demo
    # In production, integrate with Google Custom Search, Bing API, etc.
    mock_results = [
        {
            "title": f"{query} - DJ Drop Factory Search",
            "snippet": f"Find the best results for {query} in the DJ world.",
            "url": f"https://www.google.com/search?q={query.replace(' ', '+')}",
            "source": "Google"
        },
        {
            "title": f"{query} - Music Production",
            "snippet": f"Learn about {query} and music production techniques.",
            "url": f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}",
            "source": "YouTube"
        }
    ]

    return jsonify({"success": True, "results": mock_results})

# Discover category endpoints
@app.route('/api/dj-groups', methods=['GET'])
def api_dj_groups():
    return jsonify({"success": True, "dj_groups": DISCOVER_DATA["dj_groups"]})

@app.route('/api/streaming-apps', methods=['GET'])
def api_streaming_apps():
    return jsonify({"success": True, "streaming_apps": DISCOVER_DATA["streaming_apps"]})

@app.route('/api/dj-software', methods=['GET'])
def api_dj_software():
    return jsonify({"success": True, "dj_software": DISCOVER_DATA["dj_software"]})

@app.route('/api/festivals', methods=['GET'])
def api_festivals():
    return jsonify({"success": True, "festivals": DISCOVER_DATA["festivals"]})

@app.route('/api/theater-streaming', methods=['GET'])
def api_theater_streaming():
    return jsonify({"success": True, "theater_streaming": DISCOVER_DATA["theater_streaming"]})

@app.route('/api/all', methods=['GET'])
def api_all():
    return jsonify({"success": True, "data": DISCOVER_DATA})

# =============================================================================
# ERROR HANDLERS
# =============================================================================
@app.errorhandler(404)
def not_found(e):
    return jsonify({"success": False, "error": "Not found"}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({"success": False, "error": "Internal server error"}), 500

# =============================================================================
# MAIN
# =============================================================================
if __name__ == '__main__':
    # Ensure directories exist
    os.makedirs(Config.GENERATED_DIR, exist_ok=True)
    os.makedirs(os.path.join(Config.STATIC_DIR, 'icons'), exist_ok=True)
    os.makedirs(os.path.join(Config.STATIC_DIR, 'screenshots'), exist_ok=True)

    print(f"""
    ╔══════════════════════════════════════════════════════════════╗
    ║  DJ Drop Factory Pro v5.0 - Backend Server                   ║
    ║  Powered by Edge TTS | FFmpeg | Flask                       ║
    ║                                                              ║
    ║  URL: http://localhost:5000                                  ║
    ║  API: http://localhost:5000/api/status                       ║
    ║  FFmpeg: {'Available' if audio_processor.ffmpeg_available else 'Not Found - Using pydub fallback'}  ║
    ╚══════════════════════════════════════════════════════════════╝
    """)

    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
