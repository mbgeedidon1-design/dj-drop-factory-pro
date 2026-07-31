import os
from flask import Flask, jsonify, request

from config import Config
from modules.audio_processor import audio_processor
from modules.drop_generator import generator
from modules.tts_engine import TTSManager


app = Flask(__name__)
app.config["SECRET_KEY"] = Config.SECRET_KEY

tts_engine = TTSManager()


def build_generation_response(script, final_path, cover_filename, drop_id, tts_result, fx_mode):
    """Build a safe JSON response for generation requests."""
    metadata = tts_result or {}

    return {
        "success": True,
        "script": script,
        "download_url": f"/static/generated/{os.path.basename(final_path)}",
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
    }


@app.get("/api/status")
def status():
    return jsonify({
        "status": "ok",
        "app": Config.APP_NAME,
        "version": Config.APP_VERSION,
        "ffmpeg_available": audio_processor.ffmpeg_available,
    })


@app.post("/api/generate")
def generate_drop():
    data = request.get_json(silent=True) or {}

    dj_name = data.get("dj_name", "Studio Voice")
    genre = data.get("genre", "club_banger")
    drop_type = data.get("drop_type", "intro")
    mood = data.get("mood", "hype")
    energy = data.get("energy", 8)
    fx_mode = data.get("fx_mode", "dry")
    script = data.get("script") or generator.generate_script(
        dj_name=dj_name,
        genre=genre,
        drop_type=drop_type,
        mood=mood,
        energy=energy,
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

