# DJ Drop Factory Pro - Studio-Ready Audio Platform

A polished, commercial-ready DJ drop generator built for creators, radio hosts, club promoters, and event brands. The app combines AI script generation, voice controls, audio processing, and a saved library in a modern web experience.

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Install FFmpeg (REQUIRED for audio processing)
# Ubuntu/Debian:
sudo apt-get install ffmpeg
# macOS:
brew install ffmpeg
# Windows: Download from https://ffmpeg.org/download.html

# 3. Run the server
python app.py
```

Server starts at `http://localhost:5000`

## Production Deployment

### Using Gunicorn + Nginx

```bash
# Install gunicorn
pip install gunicorn

# Run with 4 workers
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

### Nginx Config

```nginx
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /path/to/dj_drop_factory_backend/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

## Environment Variables

Create a `.env` file:

```
SECRET_KEY=your-super-secret-key-here
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/status` | Server health check |
| POST | `/api/generate` | Generate DJ drop (TTS + FX + cover) |
| POST | `/api/wizard_validate` | Validate wizard step |
| GET | `/api/trends` | Trending genres |
| GET | `/api/city_vibe` | City mood suggestions |
| GET | `/api/suggest_names` | DJ name suggestions |
| POST | `/api/process_voice` | Apply voice effects |
| POST | `/api/string_tools` | Text formatting |
| GET/POST | `/api/library` | Get/save drops |
| DELETE | `/api/library/<id>` | Delete drop |
| GET | `/api/search` | Search discover data |
| GET | `/api/web_search` | Web search proxy |
| GET | `/api/dj-groups` | DJ groups data |
| GET | `/api/streaming-apps` | Streaming apps |
| GET | `/api/dj-software` | DJ software |
| GET | `/api/festivals` | Festivals 2026 |
| GET | `/api/theater-streaming` | Theater streaming |
| GET | `/api/all` | All discover data |

## PWA Requirements

- HTTPS is **required** for PWA installability
- Icons are included in `static/icons/`
- Screenshots are included in `static/screenshots/`
- Service worker handles offline mode
- Manifest includes all required fields for PWA Builder scoring

## Tech Stack

- **Flask** - Web framework
- **Edge TTS** - Microsoft Edge neural voices (322 voices, 74 languages)
- **FFmpeg** - Audio processing & effects
- **pydub** - Audio manipulation fallback
- **Pillow** - Cover image generation
- **SQLite** - Library & stats storage

## Credits

Created by Macdonald Barasa
Email: simiyumacdonal1@gmail.com
