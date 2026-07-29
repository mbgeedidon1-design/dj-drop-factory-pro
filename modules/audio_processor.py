"""DJ Drop Factory Pro v5.0 - Audio Processing with FFmpeg"""
import os
import subprocess
import random
import math
import array
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
        """Apply vocal gain using FFmpeg"""
        if not self.ffmpeg_available:
            return audio_path
        output_path = audio_path.replace(".mp3", "_gain.mp3")
        cmd = [
            "ffmpeg", "-y", "-i", audio_path,
            "-af", f"volume={gain_db}dB",
            "-ar", str(Config.AUDIO_SAMPLE_RATE),
            "-ac", str(Config.AUDIO_CHANNELS),
            "-b:a", Config.AUDIO_BITRATE,
            output_path
        ]
        subprocess.run(cmd, capture_output=True)
        return output_path if os.path.exists(output_path) else audio_path
    
    def normalize_audio(self, audio_path):
        """Normalize to broadcast standard"""
        if not self.ffmpeg_available:
            return audio_path
        output_path = audio_path.replace(".mp3", "_norm.mp3")
        cmd = [
            "ffmpeg", "-y", "-i", audio_path,
            "-af", "loudnorm=I=-14:TP=-1.5:LRA=11",
            "-ar", str(Config.AUDIO_SAMPLE_RATE),
            "-ac", str(Config.AUDIO_CHANNELS),
            "-b:a", Config.AUDIO_BITRATE,
            output_path
        ]
        subprocess.run(cmd, capture_output=True)
        return output_path if os.path.exists(output_path) else audio_path
    
    def generate_background_beat(self, genre, duration_ms=5000, energy=8):
        """Generate a simple background beat using FFmpeg"""
        output_path = os.path.join(self.output_dir, f"bg_{genre}_{int(random.random()*10000)}.mp3")
        
        genre_settings = {
            "amapiano": {"bpm": 110, "freq": 60},
            "dancehall": {"bpm": 95, "freq": 50},
            "radio": {"bpm": 120, "freq": 80},
            "club_banger": {"bpm": 128, "freq": 45},
            "afrobeat": {"bpm": 105, "freq": 55},
            "trap": {"bpm": 140, "freq": 40},
        }
        
        settings = genre_settings.get(genre, genre_settings["club_banger"])
        bpm = settings["bpm"]
        freq = settings["freq"]
        duration_sec = duration_ms / 1000
        
        if self.ffmpeg_available:
            # Use FFmpeg to generate a beat
            beat_interval = 60 / bpm
            filters = []
            for i in range(int(duration_sec / beat_interval)):
                t = i * beat_interval
                filters.append(f"aevalsrc=sin({freq}*2*PI*t)*exp(-t*15):s={Config.AUDIO_SAMPLE_RATE}:d=0.1[beat{i}];")
            
            # Simpler approach: use sine wave with rhythm
            cmd = [
                "ffmpeg", "-y", "-f", "lavfi", "-i",
                f"sine=frequency={freq}:duration={duration_sec}",
                "-af", f"volume=0.3,aecho=0.8:0.4:500:0.2",
                "-ar", str(Config.AUDIO_SAMPLE_RATE),
                "-ac", str(Config.AUDIO_CHANNELS),
                "-b:a", Config.AUDIO_BITRATE,
                output_path
            ]
            subprocess.run(cmd, capture_output=True)
        
        if os.path.exists(output_path):
            return output_path
        
        # Fallback: create silent audio
        return self._create_silent_audio(duration_ms, output_path)
    
    def _create_silent_audio(self, duration_ms, output_path):
        """Create silent audio as fallback"""
        if self.ffmpeg_available:
            duration_sec = duration_ms / 1000
            cmd = [
                "ffmpeg", "-y", "-f", "lavfi", "-i",
                f"anullsrc=r={Config.AUDIO_SAMPLE_RATE}:cl=stereo",
                "-t", str(duration_sec),
                "-ac", str(Config.AUDIO_CHANNELS),
                "-b:a", Config.AUDIO_BITRATE,
                output_path
            ]
            subprocess.run(cmd, capture_output=True)
        return output_path if os.path.exists(output_path) else None
    
    def apply_fx(self, audio_path, fx_mode, genre, energy):
        """Apply FX mode using FFmpeg"""
        if fx_mode == "dry" or not self.ffmpeg_available:
            return audio_path
        
        output_path = audio_path.replace(".mp3", f"_fx_{fx_mode}.mp3")
        
        filters = self._build_ffmpeg_filters(fx_mode, genre, energy)
        
        if filters:
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
        
        return audio_path
    
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
            if genre in ["trap", "club_banger", "dancehall"]:
                filters.append("highpass=f=50,lowpass=f=14000,loudnorm=I=-12:TP=-1.0:LRA=8,"
                              "aecho=0.5:0.5:40|50:0.4|0.3")
            elif genre in ["amapiano", "afrobeat"]:
                filters.append("highpass=f=80,lowpass=f=12000,loudnorm=I=-14:TP=-1.5:LRA=11,"
                              "aecho=0.3:0.4:50|60:0.3|0.2")
            else:
                filters.append("highpass=f=80,lowpass=f=12000,loudnorm=I=-14:TP=-1.5:LRA=11")
        
        return ",".join(filters) if filters else None
    
    def mix_vocal_and_bg(self, vocal_path, bg_path, vocal_gain, bg_gain, output_path):
        """Mix vocal track with background beat using FFmpeg"""
        if not self.ffmpeg_available:
            # Just copy vocal if no FFmpeg
            import shutil
            shutil.copy(vocal_path, output_path)
            return output_path
        
        # Convert gains to dB
        vocal_db = (vocal_gain - 1) * 10
        bg_db = (bg_gain - 0.25) * 40 - 20
        
        cmd = [
            "ffmpeg", "-y",
            "-i", vocal_path,
            "-i", bg_path,
            "-filter_complex",
            f"[0:a]volume={vocal_db}dB[v];[1:a]volume={bg_db}dB[b];[v][b]amix=inputs=2:duration=longest:dropout_transition=2",
            "-ar", str(Config.AUDIO_SAMPLE_RATE),
            "-ac", str(Config.AUDIO_CHANNELS),
            "-b:a", Config.AUDIO_BITRATE,
            output_path
        ]
        subprocess.run(cmd, capture_output=True)
        
        if os.path.exists(output_path):
            return output_path
        
        # Fallback: just copy vocal
        import shutil
        shutil.copy(vocal_path, output_path)
        return output_path
    
    def apply_voice_effect(self, audio_path, effect):
        """Apply voice effect using FFmpeg"""
        output_path = audio_path.replace(".mp3", f"_effect_{effect}.mp3")
        
        if not self.ffmpeg_available:
            import shutil
            shutil.copy(audio_path, output_path)
            return output_path
        
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
