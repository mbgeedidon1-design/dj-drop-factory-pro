"""DJ Drop Factory Pro v5.0 - Configuration"""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
   SECRET_KEY = os.getenv('SECRET_KEY', 'dj-drop-factory-secret-key-2026')
   GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")

   # Paths
   BASE_DIR = os.path.dirname(os.path.abspath(__file__))
   STATIC_DIR = os.path.join(BASE_DIR, 'static')
   GENERATED_DIR = os.path.join(STATIC_DIR, 'generated')
   TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')

   # Audio settings
   AUDIO_SAMPLE_RATE = 48000
   AUDIO_CHANNELS = 2
   AUDIO_BITRATE = '320k'
   AUDIO_FORMAT = 'mp3'

   # Default vocal gain
   DEFAULT_VOCAL_GAIN = 1.8
   DEFAULT_BG_GAIN = 0.25

   # Database
   DATABASE_PATH = os.path.join(BASE_DIR, 'dj_drop_factory.db')

   # App info
   APP_NAME = "DJ Drop Factory Pro"
   APP_VERSION = "5.0.0"
   APP_DESCRIPTION = "AI-powered DJ Drop Generator with premium voice synthesis and audio effects"

   # PWA
   PWA_THEME_COLOR = "#0a0a0f"
   PWA_BACKGROUND_COLOR = "#050508"
   PWA_DISPLAY = "standalone"
   PWA_START_URL = "/"
   PWA_SCOPE = "/"

   # Edge TTS voices mapping
   VOICES = {
       "1": {"name": "Deep Studio Heavy (Male US)", "voice": "en-US-GuyNeural", "locale": "en-US", "gender": "Male"},
       "2": {"name": "Crisp Energetic Host (Male UK)", "voice": "en-GB-RyanNeural", "locale": "en-GB", "gender": "Male"},
       "3": {"name": "Smooth High-End (Female US)", "voice": "en-US-JennyNeural", "locale": "en-US", "gender": "Female"},
       "4": {"name": "Natural Afro-Vibe (Male NG)", "voice": "en-NG-AbeoNeural", "locale": "en-NG", "gender": "Male"},
       "5": {"name": "Bright Radio Host (Female UK)", "voice": "en-GB-SoniaNeural", "locale": "en-GB", "gender": "Female"},
       "6": {"name": "Warm Afro Voice (Female NG)", "voice": "en-NG-EzinneNeural", "locale": "en-NG", "gender": "Female"},
       "7": {"name": "Auto by Genre", "voice": "auto", "locale": "auto", "gender": "Auto"},
   }

   # Genre to voice auto-mapping
   GENRE_VOICES = {
       "amapiano": "en-NG-AbeoNeural",
       "dancehall": "en-GB-RyanNeural",
       "radio": "en-GB-SoniaNeural",
       "club_banger": "en-US-GuyNeural",
       "afrobeat": "en-NG-AbeoNeural",
       "trap": "en-US-GuyNeural",
   }

   # Genre display names
   GENRES = {
       "amapiano": "Amapiano",
       "dancehall": "Dancehall",
       "radio": "Radio",
       "club_banger": "Club Banger",
       "afrobeat": "Afrobeat",
       "trap": "Trap",
   }

   # Drop types
   DROP_TYPES = {
       "intro": "Intro",
       "sweeper": "Sweeper",
       "hype": "Hype",
       "promo": "Promo",
       "producer_tag": "Producer Tag",
       "radio_id": "Radio ID",
       "crowd_call": "Crowd Call",
   }

   # Moods
   MOODS = {
       "hype": "Hype",
       "luxury": "Luxury",
       "aggressive": "Aggressive",
       "dark": "Dark",
       "smooth": "Smooth",
       "festival": "Festival",
   }

   # FX modes
   FX_MODES = {
       "auto": "Auto (Genre adaptive)",
       "dry": "Dry (No FX)",
       "clean": "Clean (Subtle polish)",
       "light": "Light",
       "heavy": "Heavy",
       "insane": "Insane",
   }
