import os
import subprocess

from config import Config


class TTSManager:
    def __init__(self):
        self.output_dir = Config.GENERATED_DIR
        os.makedirs(self.output_dir, exist_ok=True)
        self.ffmpeg_available = self._check_ffmpeg()
        self.espeak_cmd = self._find_espeak_cmd()

    def _check_ffmpeg(self):
        try:
            subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def _find_espeak_cmd(self):
        for command in ["espeak-ng", "espeak"]:
            try:
                subprocess.run([command, "--version"], capture_output=True, check=True)
                return command
            except (subprocess.CalledProcessError, FileNotFoundError):
                continue
        return None

    def generate(self, text, output_path, voice=None, rate=175, pitch=0, volume=200):
        if not text:
            raise ValueError("Text input is required")

        os.makedirs(self.output_dir, exist_ok=True)
        output_filename = os.path.basename(output_path)
        txt_path = output_path + ".txt"
        wav_path = output_path.replace(".mp3", ".wav")

        with open(txt_path, "w", encoding="utf-8") as handle:
            handle.write(text)

        voice_name = voice or "en"
        if voice_name == "auto":
            voice_name = "en"

        amplitude = max(0, min(200, int(volume)))
        if self.espeak_cmd:
            result = subprocess.run(
                [self.espeak_cmd, "-v", voice_name, "-s", str(rate), "-p", str(pitch), "-a", str(amplitude), "-f", txt_path, "-w", wav_path],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode != 0:
                raise RuntimeError(f"eSpeak error: {result.stderr}")
            if not os.path.exists(wav_path) or os.path.getsize(wav_path) == 0:
                raise RuntimeError("Empty audio output")

            if self.ffmpeg_available:
                tempo = max(0.5, min(2.0, rate / 175))
                subprocess.run(
                    ["ffmpeg", "-y", "-i", wav_path, "-af", f"atempo={tempo:.2f}", "-ar", str(Config.AUDIO_SAMPLE_RATE), "-ac", str(Config.AUDIO_CHANNELS), "-b:a", Config.AUDIO_BITRATE, output_path],
                    capture_output=True,
                )
                if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                    os.remove(wav_path)
                else:
                    os.replace(wav_path, output_path)
            else:
                os.replace(wav_path, output_path)
        else:
            with open(output_path, "wb") as handle:
                handle.write(b"placeholder")

        return {
            "filename": output_filename,
            "path": output_path,
            "voice": voice_name,
            "engine": "espeak-ng" if self.espeak_cmd else "placeholder",
            "rate": rate,
            "pitch": pitch,
            "volume": amplitude,
        }
