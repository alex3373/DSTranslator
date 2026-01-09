import sqlite3
import threading
import time
import hashlib


class SQLiteTranslationStore:
    def __init__(self, db_path="translations.db"):
        self.db_path = db_path
        self.lock = threading.Lock()
        self._init_db()

    # ==========================
    # INIT
    # ==========================
    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS translations (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    created_at INTEGER
                )
            """)
            conn.commit()

    # ==========================
    # UTIL
    # ==========================
    def _normalize_key(self, text: str) -> str:
        """
        Normaliza texto para matching estable entre sesiones
        (alineado con TranslationCache RAM)
        """
        # --------------------------
        # Normalización base (existente)
        # --------------------------
        normalized = ' '.join(text.strip().split())

        # --------------------------
        # ➕ EXTENSIÓN MULTI-IDIOMA
        # (NO elimina nada existente)
        # --------------------------

        # Normalizar puntos suspensivos
        normalized = normalized.replace('…', '...')

        # Normalizar comillas comunes y japonesas
        QUOTE_MAP = {
            '“': '"',
            '”': '"',
            '„': '"',
            '«': '"',
            '»': '"',
            '‘': "'",
            '’': "'",
            '‚': "'",
            '『': '「',
            '』': '」',
        }

        for src, dst in QUOTE_MAP.items():
            normalized = normalized.replace(src, dst)

        # --------------------------
        # Hash para textos largos
        # --------------------------

        # textos largos → hash
        if len(normalized) > 200:
            return hashlib.md5(normalized.encode()).hexdigest()

        return normalized

    # ==========================
    # GET (cache exacto)
    # ==========================
    def get(self, text: str):
        key = self._normalize_key(text)

        with self.lock, sqlite3.connect(self.db_path) as conn:
            cur = conn.execute(
                "SELECT value FROM translations WHERE key = ?",
                (key,)
            )
            row = cur.fetchone()
            return row[0] if row else None

    # ==========================
    # SET
    # ==========================
    def set(self, text: str, value: str):
        key = self._normalize_key(text)
        ts = int(time.time())

        with self.lock, sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO translations (key, value, created_at)
                VALUES (?, ?, ?)
                """,
                (key, value, ts)
            )
            conn.commit()

    # ==========================
    # HISTORIAL (para overlay)
    # ==========================
    def get_last(self, limit=20):
        """
        Devuelve las últimas traducciones en orden descendente.
        Uso: historial visual / overlay.
        """
        with self.lock, sqlite3.connect(self.db_path) as conn:
            cur = conn.execute(
                """
                SELECT key, value, created_at
                FROM translations
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,)
            )
            rows = cur.fetchall()

        return [
            {
                "key": key,
                "value": value,
                "created_at": created_at
            }
            for key, value, created_at in rows
        ]

    # ==========================
    # STATS
    # ==========================
    def count(self):
        with self.lock, sqlite3.connect(self.db_path) as conn:
            cur = conn.execute("SELECT COUNT(*) FROM translations")
            return cur.fetchone()[0]
