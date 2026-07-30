"""DJ Drop Factory Pro v5.0 - eSpeak-NG TTS Engine"""
import os
import time
import subprocess
import tempfile
from config import Config

class TTSEngine:
    VOICE_MAP = {"1": "en-us", "2": "en-gb-scotland", "3": "en-us+f3", "4": "en-ng", "5": "en-gb+f2", "6": "en-ng+f2", "7": "auto"}
    GENRE_VOICES = {"amapiano": "en-ng", "dancehall": "en-gb-scotland", "radio": "en-gb+f2", "club_banger": "en-us", "afrobeat": "en-ng", "trap": "en-us"}

    def __init__(self):
        self.output_dir = Config.GENERATED_DIR
        os.makedirs(self.output_dir, exist_ok=True)
        self.ffmpeg_available = self._probe_ffmpeg()
        self.espeak_cmd = self._probe_espeak()
        self.espeak_available = self.espeak_cmd is not None
        print(f"[TTS] eSpeak: {'OK' if self.espeak_available else 'NOT FOUND'}")
        print(f"[TTS] FFmpeg: {'OK' if self.ffmpeg_available else 'NOT FOUND'}")

    @staticmethod
    def _probe_ffmpeg():
        try:
            subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True, timeout=5)
            return True
        except:
            return False

    @staticmethod
    def _probe_espeak():
        for cmd in ("espeak-ng", "espeak"):
            try:
                subprocess.run([cmd, "--version"], capture_output=True, check=True, timeout=5)
                return cmd
            except:
                continue
        return None

    def _resolve_voice(self, voice_id, genre=None):
        if voice_id in ("7", "auto"):
            return self.GENRE_VOICES.get(genre, "en-us") if genre else "en-us"
        return self.VOICE_MAP.get(str(voice_id), "en-us")

    def generate(self, text, voice_id, energy=8, mood="aggressive", drop_type="intro", output_filename=None):
        if not self.espeak_available:
            raise RuntimeError("eSpeak-NG not installed")
        if not output_filename:
            output_filename = f"drop_{int(time.time() * 1000)}.mp3"
        output_path = os.path.join(self.output_dir, output_filename)
        voice = self._resolve_voice(voice_id)
        speed = 175
        if energy >= 9: speed = 220
        elif energy >= 7: speed = 200
        elif energy <= 3: speed = 130
        if mood in ("aggressive", "hype"): speed += 20
        elif mood in ("smooth", "dark"): speed -= 20
        speed = max(80, min(450, speed))
        pitch = 50
        if energy >= 9: pitch = 70
        elif energy <= 3: pitch = 30
        if mood == "aggressive": pitch += 10
        elif mood == "dark": pitch -= 15
        elif drop_type == "producer_tag": pitch += 20
        pitch = max(0, min(99, pitch))

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
            f.write(text)
            txt_path = f.name
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            wav_path = f.name

        try:
            result = subprocess.run([self.espeak_cmd, "-v", voice, "-s", str(speed), "-p", str(pitch), "-a", "200", "-f", txt_path, "-w", wav_path], capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                raise RuntimeError(f"eSpeak error: {result.stderr}")
            if not os.path.exists(wav_path) or os.path.getsize(wav_path) == 0:
                raise RuntimeError("Empty audio output")

            if self.ffmpeg_available:
                tempo = max(0.5, min(2.0, speed / 175))
                subprocess.run(["ffmpeg", "-y", "-i", wav_path, "-af", f"atempo={tempo:.2f}", "-ar", str(Config.AUDIO_SAMPLE_RATE), "-ac", str(Config.AUDIO_CHANNELS), "-b:a", Config.AUDIO_BITRATE, output_path], capture_output=True)
                if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                    os.remove(wav_path)
                else:
                    os.rename(wav_path, output_path)
            else:
                os.rename(wav_path, output_path)

            return {"filename": output_filename, "path": output_path, "voice": f"espeak-{voice}", "engine": "espeak-ng"}
        finally:
            for tmp in (txt_path, wav_path):
                try:
                    if os.path.exists(tmp):
                        os.remove(tmp)
                except:
                    pass

tts = TTSEngine()
