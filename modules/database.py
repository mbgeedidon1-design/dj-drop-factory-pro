"""DJ Drop Factory Pro v5.0 - SQLite Database Module"""
import hashlib
import os
import secrets
import sqlite3
from datetime import datetime
from werkzeug.security import generate_password_hash
from config import Config

class Database:
    def __init__(self):
        self.db_path = Config.DATABASE_PATH
        self._init_db()

    def _get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS library (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                drop_id TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                script TEXT NOT NULL,
                audio_url TEXT NOT NULL,
                image_url TEXT,
                genre TEXT,
                drop_type TEXT,
                mood TEXT,
                energy INTEGER,
                voice TEXT,
                dj_name TEXT,
                fx_mode TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT,
                action TEXT,
                genre TEXT,
                drop_type TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                avatar_url TEXT,
                bio TEXT,
                theme TEXT DEFAULT 'dark',
                language TEXT DEFAULT 'en',
                is_premium INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS presets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                name TEXT NOT NULL,
                genre TEXT,
                voice TEXT,
                mood TEXT,
                energy INTEGER,
                fx_mode TEXT,
                vocal_gain REAL,
                bg_gain REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS prompt_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                dj_name TEXT,
                city TEXT,
                genre TEXT,
                drop_type TEXT,
                mood TEXT,
                energy INTEGER,
                script TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                total_drops INTEGER DEFAULT 0,
                favorite_genre TEXT,
                total_shares INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS api_keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                key_prefix TEXT NOT NULL,
                key_hash TEXT NOT NULL UNIQUE,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_used_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        conn.commit()
        conn.close()

    def create_user(self, user_data):
        conn = self._get_conn()
        cursor = conn.cursor()
        password_hash = generate_password_hash(user_data.get("password", ""))
        try:
            cursor.execute(
                "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                (user_data.get("name", "User"), user_data.get("email", ""), password_hash),
            )
            conn.commit()
            user_id = cursor.lastrowid
            return {"id": user_id, "name": user_data.get("name", "User"), "email": user_data.get("email", "")}
        finally:
            conn.close()

    def get_user_by_email(self, email):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def get_user_by_id(self, user_id):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def update_user_profile(self, user_id, profile_data):
        conn = self._get_conn()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                UPDATE users 
                SET name = ?, bio = ?, avatar_url = ?, theme = ?, language = ?
                WHERE id = ?
            """, (
                profile_data.get('name'),
                profile_data.get('bio'),
                profile_data.get('avatar_url'),
                profile_data.get('theme', 'dark'),
                profile_data.get('language', 'en'),
                user_id
            ))
            conn.commit()
            return True
        finally:
            conn.close()

    def save_preset(self, user_id, preset_data):
        conn = self._get_conn()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO presets 
                (user_id, name, genre, voice, mood, energy, fx_mode, vocal_gain, bg_gain)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                preset_data.get('name', 'Untitled Preset'),
                preset_data.get('genre'),
                preset_data.get('voice'),
                preset_data.get('mood'),
                preset_data.get('energy'),
                preset_data.get('fx_mode'),
                preset_data.get('vocal_gain'),
                preset_data.get('bg_gain')
            ))
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def get_presets(self, user_id):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM presets WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def delete_preset(self, preset_id, user_id):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM presets WHERE id = ? AND user_id = ?", (preset_id, user_id))
        conn.commit()
        deleted = cursor.rowcount > 0
        conn.close()
        return deleted

    def add_prompt_history(self, user_id, prompt_data):
        conn = self._get_conn()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO prompt_history 
                (user_id, dj_name, city, genre, drop_type, mood, energy, script)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                prompt_data.get('dj_name'),
                prompt_data.get('city'),
                prompt_data.get('genre'),
                prompt_data.get('drop_type'),
                prompt_data.get('mood'),
                prompt_data.get('energy'),
                prompt_data.get('script')
            ))
            conn.commit()
            return True
        finally:
            conn.close()

    def get_prompt_history(self, user_id, limit=20):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM prompt_history 
            WHERE user_id = ? 
            ORDER BY created_at DESC 
            LIMIT ?
        """, (user_id, limit))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def get_or_create_analytics(self, user_id):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM analytics WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        if not row:
            cursor.execute(
                "INSERT INTO analytics (user_id) VALUES (?)",
                (user_id,)
            )
            conn.commit()
            cursor.execute("SELECT * FROM analytics WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def update_analytics(self, user_id, analytics_data):
        conn = self._get_conn()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                UPDATE analytics 
                SET total_drops = ?, favorite_genre = ?, total_shares = ?, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
            """, (
                analytics_data.get('total_drops', 0),
                analytics_data.get('favorite_genre'),
                analytics_data.get('total_shares', 0),
                user_id
            ))
            conn.commit()
            return True
        finally:
            conn.close()

    def set_premium(self, user_id, is_premium):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET is_premium = ? WHERE id = ?", (1 if is_premium else 0, user_id))
        conn.commit()
        conn.close()
        return True

    def create_api_key(self, user_id, name):
        api_key = f"df_live_{secrets.token_urlsafe(24)}"
        key_hash = hashlib.sha256(api_key.encode("utf-8")).hexdigest()
        prefix = api_key[:12]
        conn = self._get_conn()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO api_keys (user_id, name, key_prefix, key_hash) VALUES (?, ?, ?, ?)",
                (user_id, name or "Studio App", prefix, key_hash),
            )
            conn.commit()
            return {"id": cursor.lastrowid, "key": api_key, "prefix": prefix, "name": name or "Studio App"}
        finally:
            conn.close()

    def get_api_keys(self, user_id):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM api_keys WHERE user_id = ? AND is_active = 1 ORDER BY created_at DESC", (user_id,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def delete_api_key(self, key_id, user_id):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("UPDATE api_keys SET is_active = 0 WHERE id = ? AND user_id = ?", (key_id, user_id))
        conn.commit()
        deleted = cursor.rowcount > 0
        conn.close()
        return deleted

    def get_api_key_user(self, api_key):
        if not api_key:
            return None
        key_hash = hashlib.sha256(api_key.encode("utf-8")).hexdigest()
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, id, name FROM api_keys WHERE key_hash = ? AND is_active = 1", (key_hash,))
        row = cursor.fetchone()
        if row:
            cursor.execute("UPDATE api_keys SET last_used_at = CURRENT_TIMESTAMP WHERE id = ?", (row["id"],))
            conn.commit()
        conn.close()
        return dict(row) if row else None

    def add_drop(self, drop_data):
        conn = self._get_conn()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO library 
                (user_id, drop_id, title, script, audio_url, image_url, genre, drop_type, mood, energy, voice, dj_name, fx_mode)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                drop_data.get("user_id"),
                drop_data.get("id", str(int(datetime.now().timestamp() * 1000))),
                drop_data.get("title", "Untitled Drop"),
                drop_data.get("script", ""),
                drop_data.get("url", ""),
                drop_data.get("image_url", ""),
                drop_data.get("genre", ""),
                drop_data.get("drop_type", ""),
                drop_data.get("mood", ""),
                drop_data.get("energy", 8),
                drop_data.get("voice", ""),
                drop_data.get("dj_name", "DJ Beshi"),
                drop_data.get("fx_mode", "auto")
            ))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()

    def get_drops(self, limit=100, offset=0, user_id=None):
        conn = self._get_conn()
        cursor = conn.cursor()
        if user_id:
            cursor.execute("""
                SELECT * FROM library 
                WHERE user_id = ? OR user_id IS NULL
                ORDER BY created_at DESC 
                LIMIT ? OFFSET ?
            """, (user_id, limit, offset))
        else:
            cursor.execute("SELECT * FROM library ORDER BY created_at DESC LIMIT ? OFFSET ?", (limit, offset))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def get_drop(self, drop_id):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM library WHERE drop_id = ?", (drop_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def delete_drop(self, drop_id):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM library WHERE drop_id = ?", (drop_id,))
        conn.commit()
        deleted = cursor.rowcount > 0
        conn.close()
        return deleted

    def log_stat(self, device_id, action, genre=None, drop_type=None):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO stats (device_id, action, genre, drop_type) VALUES (?, ?, ?, ?)",
                      (device_id, action, genre, drop_type))
        conn.commit()
        conn.close()

    def get_stats(self):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as total FROM library")
        total_drops = cursor.fetchone()["total"]
        cursor.execute("SELECT genre, COUNT(*) as count FROM library GROUP BY genre ORDER BY count DESC")
        genre_stats = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return {"total_drops": total_drops, "genre_breakdown": genre_stats}

db = Database()
