import io
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app


def test_build_generation_response_handles_missing_tts_metadata():
    response = app.build_generation_response(
        script="test drop",
        final_path="/tmp/drop.mp3",
        cover_filename=None,
        drop_id="drop_123",
        tts_result={},
        fx_mode="dry",
    )

    assert response["success"] is True
    assert response["voice_used"] is None
    assert response["processing"]["rate"] is None
    assert response["processing"]["pitch"] is None
    assert response["processing"]["volume"] is None
    assert response["processing"]["fx_mode"] == "dry"


def test_status_endpoint_returns_commercial_metadata():
    client = app.app.test_client()
    response = client.get("/api/status")

    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "ok"
    assert data["app"] == "DJ Drop Factory Pro"
    assert data["online"] is True
    assert data["tts_provider"] in {"gTTS", "edge-tts", "espeak", "placeholder"}
    assert "AI voice generation" in data["features"]


def test_string_tools_endpoint_formats_text():
    client = app.app.test_client()
    response = client.post(
        "/api/string_tools",
        json={"text": "hello world", "operation": "capitalize"},
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert data["result"] == "Hello World"


def test_auth_register_and_login_flow():
    client = app.app.test_client()
    username = "tester"
    email = f"tester_{uuid.uuid4().hex[:8]}@example.com"

    register_response = client.post(
        "/api/auth/register",
        json={"name": username, "email": email, "password": "StrongPass123!"},
    )
    assert register_response.status_code == 200
    register_data = register_response.get_json()
    assert register_data["success"] is True
    assert register_data["user"]["email"] == email

    login_response = client.post(
        "/api/auth/login",
        json={"email": email, "password": "StrongPass123!"},
    )
    assert login_response.status_code == 200
    login_data = login_response.get_json()
    assert login_data["success"] is True
    assert login_data["token"]

    me_response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {login_data['token']}"},
    )
    assert me_response.status_code == 200
    me_data = me_response.get_json()
    assert me_data["user"]["email"] == email


def test_process_voice_endpoint_applies_effect_and_returns_metadata():
    client = app.app.test_client()
    response = client.post(
        "/api/process_voice",
        data={
            "audio": (io.BytesIO(b"fake audio data"), "voice.wav"),
            "effect": "robot",
        },
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert data["effect"] == "robot"
    assert data["processing"]["applied"] is True
    assert data["processing"]["source"] == "upload"
    assert data["audio_url"].startswith("/static/generated/uploads/")


def test_studio_presets_endpoint_returns_creative_options():
    client = app.app.test_client()
    response = client.get("/api/studio-presets")

    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert "club_banger" in data["presets"]
    assert data["presets"]["club_banger"]["effect"] == "club"
