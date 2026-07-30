"""DJ Drop Factory Pro v5.0 - eSpeak-NG TTS Engine (Production)"""
import os
import time
import subprocess
import tempfile
from config import Config


class TTSEngine:
    VOICE_MAP = {
        "1": "en-us",
        "2": "en-gb-scotland",
        "3": "en-us+f3",
        "4": "en-ng",
        "5": "en-gb+f2",
        "6": "en-ng+f2",
        "7": "auto",
    }

    GENRE_VOICES = {
        "amapiano": "en-ng",
        "dancehall": "en-gb-scotland",
        "radio": "en-gb+f2",
        "club_banger": "en-us",
        "afrobeat": "en-ng",
        "trap": "en-us",
    }

    DEFAULT_SPEED = 175
    MIN_SPEED = 80
    MAX_SPEED = 450
    DEFAULT_PITCH = 50
    MIN_PITCH = 0
    MAX_PITCH = 99

    def __init__(self):
        self.output_dir = Config.GENERATED_DIR
        os.makedirs(self.output_dir, exist_ok=True)
        self.ffmpeg_available = self._probe_ffmpeg()
        self.espeak_cmd = self._probe_espeak()
        self.espeak_available = self.espeak_cmd is not None
        print(f"[TTS] eSpeak: {'OK (' + self.espeak_cmd + ')' if self.espeak_available else 'NOT FOUND'}")
        print(f"[TTS] FFmpeg: {'OK' if self.ffmpeg_available else 'NOT FOUND'}")

    @staticmethod
    def _probe_ffmpeg():
        try:
            subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True, timeout=5)
            return True
        except Exception:
            return False

    @staticmethod
    def _probe_espeak():
        for cmd in ("espeak-ng", "espeak"):
            try:
                subprocess.run([cmd, "--version"], capture_output=True, check=True, timeout=5)
                return cmd
            except Exception:
                continue
        return None

    def _resolve_voice(self, voice_id, genre=None):
        if voice_id in ("7", "auto"):
            return self.GENRE_VOICES.get(genre, "en-us") if genre else "en-us"
        return self.VOICE_MAP.get(str(voice_id), "en-us")

    def _resolve_speed(self, energy, mood):
        speed = self.DEFAULT_SPEED
        if energy >= 9:
            speed = 220
        elif energy >= 7:
            speed = 200
        elif energy <= 3:
            speed = 130
        if mood in ("aggressive", "hype"):
            speed += 20
        elif mood in ("smooth", "dark"):
            speed -= 20
        return max(self.MIN_SPEED, min(self.MAX_SPEED, speed))

    def _resolve_pitch(self, energy, mood, drop_type):
        pitch = self.DEFAULT_PITCH
        if energy >= 9:
            pitch = 70
        elif energy <= 3:
            pitch = 30
        if mood == "aggressive":
            pitch += 10
        elif mood == "dark":
            pitch -= 15
        elif drop_type == "producer_tag":
            pitch += 20
        return max(self.MIN_PITCH, min(self.MAX_PITCH, pitch))

    def _wav_to_mp3(self, wav_path, mp3_path, speed, pitch):
        if not self.ffmpeg_available:
            os.rename(wav_path, mp3_path)
            return mp3_path
        tempo = max(0.5, min(2.0, speed / self.DEFAULT_SPEED))
        pitch_shift = (pitch - self.DEFAULT_PITCH) / 4
        afilters = f"atempo={tempo:.2f}"
        if abs(pitch_shift) > 0.5:
            afilters += f",rubberband=pitch={pitch_shift:.1f}"
        subprocess.run([
            "ffmpeg", "-y", "-i", wav_path, "-af", afilters,
            "-ar", str(Config.AUDIO_SAMPLE_RATE), "-ac", str(Config.AUDIO_CHANNELS),
            "-b:a", Config.AUDIO_BITRATE, mp3_path,
        ], capture_output=True)
        if os.path.exists(mp3_path) and os.path.getsize(mp3_path) > 0:
            os.remove(wav_path)
            return mp3_path
        os.rename(wav_path, mp3_path)
        return mp3_path

    def generate(self, text, voice_id, energy=8, mood="aggressive", drop_type="intro", output_filename=None):
        if not self.espeak_available:
            raise RuntimeError("eSpeak-NG not installed. Run: pkg install espeak")
        if not output_filename:
            output_filename = f"drop_{int(time.time() * 1000)}.mp3"
        output_path = os.path.join(self.output_dir, output_filename)
        voice = self._resolve_voice(voice_id, genre=None)
        speed = self._resolve_speed(energy, mood)
        pitch = self._resolve_pitch(energy, mood, drop_type)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as txt_file:
            txt_file.write(text)
            txt_path = txt_file.name
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as wav_file:
            wav_path = wav_file.name

        try:
            result = subprocess.run([
                self.espeak_cmd, "-v", voice, "-s", str(speed),
                "-p", str(pitch), "-a", "200", "-f", txt_path, "-w", wav_path,
            ], capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                raise RuntimeError(f"eSpeak error: {result.stderr}")
            if not os.path.exists(wav_path) or os.path.getsize(wav_path) == 0:
                raise RuntimeError("eSpeak produced empty audio")

            self._wav_to_mp3(wav_path, output_path, speed, pitch)

            return {
                "filename": output_filename,
                "path": output_path,
                "voice": f"espeak-{voice}",
                "rate": f"{speed}wpm",
                "pitch": f"{pitch}/99",
                "engine": "espeak-ng",
            }
        finally:
            for tmp in (txt_path, wav_path):
                try:
                    if os.path.exists(tmp):
                        os.remove(tmp)
                except OSError:
                    pass


tts = TTSEngine()
