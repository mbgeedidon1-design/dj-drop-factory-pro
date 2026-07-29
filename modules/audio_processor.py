"""DJ Drop Factory Pro v5.0 - Audio Processing with FFmpeg & Pydub"""
import os
import subprocess
import random
from pydub import AudioSegment
from pydub.effects import normalize, compress_dynamic_range
from config import Config

class AudioProcessor:
    def __init__(self):
        self.output_dir = Config.GENERATED_DIR
        os.makedirs(self.output_dir, exist_ok=True)
        self.ffmpeg_available = self._check_ffmpeg()

    def _check_ffmpeg(self):
        try:
            subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def apply_vocal_gain(self, audio_path, gain_db):
        """Apply vocal gain using pydub"""
        audio = AudioSegment.from_file(audio_path)
        audio = audio + (gain_db * 10)  # Convert to dB
        return audio

    def normalize_audio(self, audio, target_dBFS=-14.0):
        """Normalize to broadcast standard (-14 LUFS approx)"""
        return normalize(audio, headroom=abs(target_dBFS))

    def compress_audio(self, audio, threshold=-20.0, ratio=4.0, attack=5.0, release=50.0):
        """Apply dynamic range compression"""
        return compress_dynamic_range(audio, threshold=threshold, ratio=ratio, attack=attack, release=release)

    def generate_background_beat(self, genre, duration_ms=5000, energy=8):
        """Generate a simple background beat based on genre"""
        beat = AudioSegment.silent(duration=duration_ms)

        # Genre-specific BPM and patterns
        genre_settings = {
            "amapiano": {"bpm": 110, "base_freq": 60, "hihat_freq": 8000},
            "dancehall": {"bpm": 95, "base_freq": 50, "hihat_freq": 10000},
            "radio": {"bpm": 120, "base_freq": 80, "hihat_freq": 6000},
            "club_banger": {"bpm": 128, "base_freq": 45, "hihat_freq": 12000},
            "afrobeat": {"bpm": 105, "base_freq": 55, "hihat_freq": 9000},
            "trap": {"bpm": 140, "base_freq": 40, "hihat_freq": 14000},
        }

        settings = genre_settings.get(genre, genre_settings["club_banger"])
        bpm = settings["bpm"]
        beat_interval = int(60000 / bpm)

        # Energy affects intensity
        intensity = min(energy / 10.0, 1.0)
        volume_db = -20 + (intensity * 10)

        for i in range(0, duration_ms, beat_interval):
            # Kick drum
            kick = self._generate_tone(settings["base_freq"], 100, volume_db)
            beat = beat.overlay(kick, position=i)

            # Hi-hat on off-beats
            if i + beat_interval // 2 < duration_ms:
                hihat = self._generate_tone(settings["hihat_freq"], 50, volume_db - 5)
                hihat = hihat.high_pass_filter(3000)
                beat = beat.overlay(hihat, position=i + beat_interval // 2)

        return beat

    def _generate_tone(self, freq, duration_ms, volume_db=-20):
        """Generate a simple sine wave tone"""
        sample_rate = Config.AUDIO_SAMPLE_RATE
        samples = []
        import math
        import array

        for i in range(int(sample_rate * duration_ms / 1000)):
            t = i / sample_rate
            # Sine wave with exponential decay for drum-like sound
            envelope = math.exp(-t * 15) if duration_ms < 200 else 1.0
            sample = int(32767 * envelope * math.sin(2 * math.pi * freq * t))
            samples.append(sample)

        audio = AudioSegment(
            data=array.array('h', samples).tobytes(),
            sample_width=2,
            frame_rate=sample_rate,
            channels=1
        )
        return audio + volume_db

    def apply_fx(self, audio_path, fx_mode, genre, energy):
        """Apply FX mode using FFmpeg"""
        if fx_mode == "dry":
            return audio_path

        output_path = audio_path.replace(".mp3", f"_fx_{fx_mode}.mp3")

        filters = self._build_ffmpeg_filters(fx_mode, genre, energy)

        if self.ffmpeg_available and filters:
            cmd = [
                "ffmpeg", "-y", "-i", audio_path,
                "-af", filters,
                "-ar", str(Config.AUDIO_SAMPLE_RATE),
                "-ac", str(Config.AUDIO_CHANNELS),
                "-b:a", Config.AUDIO_BITRATE,
                output_path
            ]
            subprocess.run(cmd, capture_output=True)
            if os.path.exists(output_path):
                return output_path

        # Fallback: use pydub effects
        audio = AudioSegment.from_file(audio_path)
        audio = self._apply_pydub_fx(audio, fx_mode, energy)
        audio.export(output_path, format="mp3", bitrate=Config.AUDIO_BITRATE)
        return output_path

    def _build_ffmpeg_filters(self, fx_mode, genre, energy):
        """Build FFmpeg filter chain based on FX mode"""
        filters = []

        if fx_mode == "clean":
            filters.append("highpass=f=80,lowpass=f=12000,loudnorm=I=-14:TP=-1.5:LRA=11")
        elif fx_mode == "light":
            filters.append("highpass=f=80,lowpass=f=12000,loudnorm=I=-14:TP=-1.5:LRA=11,aecho=0.3:0.4:50|60:0.3|0.2")
        elif fx_mode == "heavy":
            filters.append("highpass=f=60,lowpass=f=14000,loudnorm=I=-12:TP=-1.0:LRA=8,"
                          "aecho=0.5:0.5:40|50|60:0.4|0.3|0.2,"
                          "chorus=0.5:0.9:50|60|70:0.4|0.3|0.2:0.25|0.3|0.35:2|2.3|2.6")
        elif fx_mode == "insane":
            filters.append("highpass=f=40,lowpass=f=16000,loudnorm=I=-10:TP=-0.5:LRA=6,"
                          "aecho=0.7:0.6:30|40|50|60:0.5|0.4|0.3|0.2,"
                          "chorus=0.7:0.9:50|60|70|80:0.5|0.4|0.3|0.2:0.25|0.3|0.35|0.4:2|2.3|2.6|2.9,"
                          "flanger=delay=3:depth=2:regen=0.5:speed=0.5")
        elif fx_mode == "auto":
            # Genre-adaptive FX
            if genre in ["trap", "club_banger", "dancehall"]:
                filters.append("highpass=f=50,lowpass=f=14000,loudnorm=I=-12:TP=-1.0:LRA=8,"
                              "aecho=0.5:0.5:40|50:0.4|0.3")
            elif genre in ["amapiano", "afrobeat"]:
                filters.append("highpass=f=80,lowpass=f=12000,loudnorm=I=-14:TP=-1.5:LRA=11,"
                              "aecho=0.3:0.4:50|60:0.3|0.2")
            else:
                filters.append("highpass=f=80,lowpass=f=12000,loudnorm=I=-14:TP=-1.5:LRA=11")

        return ",".join(filters) if filters else None

    def _apply_pydub_fx(self, audio, fx_mode, energy):
        """Apply effects using pydub when FFmpeg is unavailable"""
        if fx_mode in ["heavy", "insane"]:
            audio = audio + 3  # Boost volume

        audio = normalize(audio)

        if fx_mode in ["light", "heavy", "insane"]:
            audio = compress_dynamic_range(audio)

        return audio

    def mix_vocal_and_bg(self, vocal_path, bg_path, vocal_gain, bg_gain, output_path):
        """Mix vocal track with background beat"""
        vocal = AudioSegment.from_file(vocal_path)
        bg = AudioSegment.from_file(bg_path)

        # Match durations
        max_duration = max(len(vocal), len(bg))
        if len(vocal) < max_duration:
            vocal = vocal + AudioSegment.silent(duration=max_duration - len(vocal))
        if len(bg) < max_duration:
            bg = bg + AudioSegment.silent(duration=max_duration - len(bg))

        # Apply gains
        vocal = vocal + (vocal_gain * 10 - 10)
        bg = bg + (bg_gain * 100 - 100)

        # Mix
        mixed = vocal.overlay(bg)
        mixed = normalize(mixed)

        mixed.export(output_path, format="mp3", bitrate=Config.AUDIO_BITRATE)
        return output_path

    def apply_voice_effect(self, audio_path, effect):
        """Apply voice effect (helium, robot, echo, etc.)"""
        output_path = audio_path.replace(".mp3", f"_effect_{effect}.mp3")

        if not self.ffmpeg_available:
            # Pydub fallback
            audio = AudioSegment.from_file(audio_path)
            if effect == "helium":
                audio = audio._spawn(audio.raw_data, overrides={"frame_rate": int(audio.frame_rate * 1.5)})
                audio = audio.set_frame_rate(Config.AUDIO_SAMPLE_RATE)
            elif effect == "low":
                audio = audio._spawn(audio.raw_data, overrides={"frame_rate": int(audio.frame_rate * 0.7)})
                audio = audio.set_frame_rate(Config.AUDIO_SAMPLE_RATE)
            elif effect == "fast":
                audio = audio.speedup(playback_speed=1.5)
            elif effect == "slow":
                audio = audio._spawn(audio.raw_data, overrides={"frame_rate": int(audio.frame_rate * 0.7)})
                audio = audio.set_frame_rate(Config.AUDIO_SAMPLE_RATE)
            audio.export(output_path, format="mp3", bitrate=Config.AUDIO_BITRATE)
            return output_path

        # FFmpeg effects
        effect_filters = {
            "helium": "asetrate=48000*1.5,aresample=48000",
            "low": "asetrate=48000*0.7,aresample=48000",
            "robot": "afftfilt=real='hypot(re,im)*cos((random(0)*2-1)*2*3.14)':imag='hypot(re,im)*sin((random(0)*2-1)*2*3.14)':win_size=512:overlap=0.75",
            "echo": "aecho=0.8:0.9:1000|1800:0.3|0.25",
            "phone": "highpass=f=300,lowpass=f=3400,acrusher=mix=0.1:mode=log:lvl=10",
            "slow": "atempo=0.7,asetrate=48000*0.85,aresample=48000",
            "fast": "atempo=1.5,asetrate=48000*1.2,aresample=48000",
        }

        filt = effect_filters.get(effect)
        if filt:
            cmd = [
                "ffmpeg", "-y", "-i", audio_path,
                "-af", filt,
                "-ar", str(Config.AUDIO_SAMPLE_RATE),
                "-ac", str(Config.AUDIO_CHANNELS),
                "-b:a", Config.AUDIO_BITRATE,
                output_path
            ]
            subprocess.run(cmd, capture_output=True)

        return output_path if os.path.exists(output_path) else audio_path

audio_processor = AudioProcessor()
