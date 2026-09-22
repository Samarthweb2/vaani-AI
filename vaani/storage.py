"""SQLite storage for tracking processed mentions and preventing duplicate replies."""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict, Any


class MentionStorage:
    def __init__(self, db_path: str = "data/vaani.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        """Initialize SQLite tables if they do not exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS processed_mentions (
                    tweet_id TEXT PRIMARY KEY,
                    author_id TEXT,
                    author_username TEXT,
                    query_text TEXT,
                    response_text TEXT,
                    reply_tweet_id TEXT,
                    created_at TEXT,
                    processed_at TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS bot_state (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TEXT
                )
            """)
            conn.commit()

    def is_processed(self, tweet_id: str) -> bool:
        """Check if a tweet ID has already been handled."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM processed_mentions WHERE tweet_id = ?", (str(tweet_id),))
            return cursor.fetchone() is not None

    def record_mention(
        self,
        tweet_id: str,
        author_id: str,
        author_username: str,
        query_text: str,
        response_text: str,
        reply_tweet_id: Optional[str] = None,
        created_at: Optional[str] = None
    ) -> None:
        """Store a processed mention record."""
        now = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO processed_mentions
                (tweet_id, author_id, author_username, query_text, response_text, reply_tweet_id, created_at, processed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(tweet_id),
                str(author_id),
                author_username,
                query_text,
                response_text,
                reply_tweet_id,
                created_at or now,
                now
            ))
            conn.commit()

    def get_last_since_id(self) -> Optional[str]:
        """Retrieve the latest processed tweet ID for cursor pagination."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM bot_state WHERE key = 'last_since_id'")
            row = cursor.fetchone()
            return row["value"] if row else None

    def set_last_since_id(self, since_id: str) -> None:
        """Update the latest processed tweet ID."""
        now = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO bot_state (key, value, updated_at)
                VALUES ('last_since_id', ?, ?)
            """, (str(since_id), now))
            conn.commit()

    def get_recent_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieve recent mentions handled by the bot."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM processed_mentions
                ORDER BY processed_at DESC
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]
