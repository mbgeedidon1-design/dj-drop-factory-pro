"""DJ Drop Factory Pro v5.0 - SQLite Database Module"""
import sqlite3
import os
from datetime import datetime
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
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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

        conn.commit()
        conn.close()

    def add_drop(self, drop_data):
        conn = self._get_conn()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO library 
                (drop_id, title, script, audio_url, image_url, genre, drop_type, mood, energy, voice, dj_name, fx_mode)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
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

    def get_drops(self, limit=100, offset=0):
        conn = self._get_conn()
        cursor = conn.cursor()
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
