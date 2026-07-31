import os
import subprocess
import tempfile

from config import Config

try:
    from gtts import gTTS
except Exception:  # pragma: no cover - optional dependency
    gTTS = None


class TTSManager:
    def __init__(self):
        self.output_dir = Config.GENERATED_DIR
        os.makedirs(self.output_dir, exist_ok=True)
        self.ffmpeg_available = self._check_ffmpeg()
        self.espeak_cmd = self._find_espeak_cmd()
        self.provider = self._select_provider()

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

    def _select_provider(self):
        if gTTS is not None:
            return "gTTS"
        if self.espeak_cmd:
            return "espeak"
        return "placeholder"

    def _normalize_voice(self, voice):
        voice_name = voice or "auto"
        if voice_name == "auto":
            return "en"
        if str(voice_name).startswith("en"):
            return str(voice_name)
        if str(voice_name) in {"1", "2", "3", "4", "5", "6", "7"}:
            return "en"
        return "en"

    def _transcode_audio(self, input_path, output_path):
        if not self.ffmpeg_available:
            os.replace(input_path, output_path)
            return

        subprocess.run(
            [
                "ffmpeg", "-y", "-i", input_path,
                "-vn", "-ar", str(Config.AUDIO_SAMPLE_RATE),
                "-ac", str(Config.AUDIO_CHANNELS),
                "-b:a", Config.AUDIO_BITRATE,
                output_path,
            ],
            capture_output=True,
            check=False,
        )
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            os.remove(input_path)
        else:
            os.replace(input_path, output_path)

    def _generate_gtts(self, text, output_path, voice_name):
        if gTTS is None:
            raise RuntimeError("gTTS unavailable")

        lang = "en" if voice_name == "en" else voice_name.split("-")[0]
        if language := lang.split("_")[0].split("-")[0]:
            lang = language

        temp_fd, temp_path = tempfile.mkstemp(suffix=".mp3")
        os.close(temp_fd)
        try:
            tts = gTTS(text=text, lang=lang, slow=False, lang_check=False)
            tts.save(temp_path)
            self._transcode_audio(temp_path, output_path)
            return True
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def generate(self, text, output_path, voice=None, rate=175, pitch=0, volume=200):
        if not text:
            raise ValueError("Text input is required")

        os.makedirs(self.output_dir, exist_ok=True)
        output_filename = os.path.basename(output_path)
        txt_path = output_path + ".txt"
        wav_path = output_path.replace(".mp3", ".wav")

        with open(txt_path, "w", encoding="utf-8") as handle:
            handle.write(text)

        voice_name = self._normalize_voice(voice)
        amplitude = max(0, min(200, int(volume)))

        if self.provider == "gTTS":
            try:
                if self._generate_gtts(text, output_path, voice_name):
                    return {
                        "filename": output_filename,
                        "path": output_path,
                        "voice": voice_name,
                        "engine": "gTTS",
                        "rate": rate,
                        "pitch": pitch,
                        "volume": amplitude,
                    }
            except Exception:
                pass

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
            "engine": self.provider if self.provider != "placeholder" else "placeholder",
            "rate": rate,
            "pitch": pitch,
            "volume": amplitude,
        }
