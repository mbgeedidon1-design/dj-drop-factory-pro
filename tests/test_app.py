import sys
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
