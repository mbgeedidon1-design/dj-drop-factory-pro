"""DJ Drop Factory Pro v5.0 - Utility Functions"""
import os
import uuid
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from config import Config

def generate_drop_id():
    """Generate unique drop ID"""
    return f"drop_{uuid.uuid4().hex[:12]}_{int(datetime.now().timestamp())}"

def generate_cover_image(dj_name, genre, drop_type, output_dir):
    """Generate a cover image for the drop"""
    try:
        # Create a gradient background based on genre
        genre_colors = {
            "amapiano": ("#1a1a2e", "#16213e", "#0f3460"),
            "dancehall": ("#ff6b35", "#f7931e", "#ffd23f"),
            "radio": ("#2d3436", "#636e72", "#b2bec3"),
            "club_banger": ("#ff006e", "#8338ec", "#3a86ff"),
            "afrobeat": ("#006400", "#228b22", "#32cd32"),
            "trap": ("#000000", "#434343", "#8b0000"),
        }

        colors = genre_colors.get(genre, ("#0a0a0f", "#16161f", "#ff6b35"))

        # Create image
        img = Image.new('RGB', (800, 800), colors[0])
        draw = ImageDraw.Draw(img)

        # Draw gradient-like effect with rectangles
        for i in range(800):
            ratio = i / 800
            r = int(int(colors[0][1:3], 16) * (1 - ratio) + int(colors[1][1:3], 16) * ratio)
            g = int(int(colors[0][3:5], 16) * (1 - ratio) + int(colors[1][3:5], 16) * ratio)
            b = int(int(colors[0][5:7], 16) * (1 - ratio) + int(colors[1][5:7], 16) * ratio)
            draw.line([(0, i), (800, i)], fill=(r, g, b))

        # Draw a circle in the center
        center_x, center_y = 400, 350
        radius = 200
        draw.ellipse([center_x - radius, center_y - radius, center_x + radius, center_y + radius], 
                     fill=colors[2], outline="white", width=5)

        # Add text
        try:
            font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60)
            font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 36)
            font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 28)
        except:
            font_large = ImageFont.load_default()
            font_medium = font_large
            font_small = font_large

        # DJ Name
        bbox = draw.textbbox((0, 0), dj_name, font=font_large)
        text_width = bbox[2] - bbox[0]
        draw.text((400 - text_width // 2, 280), dj_name, fill="white", font=font_large)

        # Genre
        genre_text = genre.replace("_", " ").upper()
        bbox = draw.textbbox((0, 0), genre_text, font=font_medium)
        text_width = bbox[2] - bbox[0]
        draw.text((400 - text_width // 2, 360), genre_text, fill="white", font=font_medium)

        # Drop type
        drop_text = drop_type.replace("_", " ").upper()
        bbox = draw.textbbox((0, 0), drop_text, font=font_small)
        text_width = bbox[2] - bbox[0]
        draw.text((400 - text_width // 2, 420), drop_text, fill="white", font=font_small)

        # Save
        filename = f"cover_{uuid.uuid4().hex[:8]}.png"
        filepath = os.path.join(output_dir, filename)
        img.save(filepath, "PNG")
        return filename
    except Exception as e:
        print(f"Cover image generation error: {e}")
        return None

def sanitize_filename(text):
    """Sanitize text for use in filenames"""
    return "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in text).strip()

def format_time_ago(timestamp_str):
    """Format timestamp as human-readable time ago"""
    try:
        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        now = datetime.now(dt.tzinfo)
        diff = now - dt

        if diff.days > 0:
            return f"{diff.days}d ago"
        elif diff.seconds > 3600:
            return f"{diff.seconds // 3600}h ago"
        elif diff.seconds > 60:
            return f"{diff.seconds // 60}m ago"
        else:
            return "Just now"
    except:
        return timestamp_str
