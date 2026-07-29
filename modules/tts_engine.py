"""DJ Drop Factory Pro v5.0 - Edge TTS Engine"""
import asyncio
import edge_tts
import os
from config import Config

class TTSEngine:
    def __init__(self):
        self.output_dir = Config.GENERATED_DIR
        os.makedirs(self.output_dir, exist_ok=True)

    def _get_voice(self, voice_id, genre=None):
        if voice_id == "7" or voice_id == "auto":
            if genre and genre in Config.GENRE_VOICES:
                return Config.GENRE_VOICES[genre]
            return "en-US-GuyNeural"

        voice_config = Config.VOICES.get(str(voice_id), Config.VOICES["1"])
        return voice_config["voice"]

    def _get_rate(self, energy, mood):
        base_rate = 0
        if energy >= 9:
            base_rate = 15
        elif energy >= 7:
            base_rate = 8
        elif energy >= 5:
            base_rate = 0
        elif energy >= 3:
            base_rate = -8
        else:
            base_rate = -15

        if mood in ["aggressive", "hype"]:
            base_rate += 5
        elif mood in ["smooth", "dark"]:
            base_rate -= 5

        return f"{base_rate:+d}%"

    def _get_pitch(self, mood, drop_type):
        if mood == "aggressive":
            return "+5Hz"
        elif mood == "dark":
            return "-10Hz"
        elif drop_type == "producer_tag":
            return "+15Hz"
        return "+0Hz"

    def _get_volume(self, energy):
        if energy >= 9:
            return "+20%"
        elif energy >= 7:
            return "+10%"
        elif energy >= 5:
            return "+0%"
        return "-10%"

    async def generate_async(self, text, voice_id, energy=8, mood="aggressive", 
                           drop_type="intro", output_filename=None):
        if not output_filename:
            output_filename = f"drop_{int(asyncio.get_event_loop().time() * 1000)}.mp3"

        output_path = os.path.join(self.output_dir, output_filename)
        voice = self._get_voice(voice_id, None)
        rate = self._get_rate(energy, mood)
        pitch = self._get_pitch(mood, drop_type)
        volume = self._get_volume(energy)

        communicate = edge_tts.Communicate(
            text=text,
            voice=voice,
            rate=rate,
            pitch=pitch,
            volume=volume
        )
        await communicate.save(output_path)

        return {
            "filename": output_filename,
            "path": output_path,
            "voice": voice,
            "rate": rate,
            "pitch": pitch,
            "volume": volume
        }

    def generate(self, text, voice_id, energy=8, mood="aggressive", 
                drop_type="intro", output_filename=None):
        return asyncio.run(self.generate_async(
            text, voice_id, energy, mood, drop_type, output_filename
        ))

    async def list_voices_async(self):
        voices = await edge_tts.list_voices()
        return voices

    def list_voices(self):
        return asyncio.run(self.list_voices_async())

tts = TTSEngine()
