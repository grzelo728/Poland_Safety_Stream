import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from app.core.config import get_settings


DB_PATH = Path(get_settings().database_url.replace("sqlite:///", ""))


def init_db() -> None:
    """Create tables if they do not exist."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.executescript(
        """
        CREATE TABLE IF NOT EXISTS posts (
            id TEXT PRIMARY KEY,
            subreddit TEXT,
            title TEXT,
            author TEXT,
            created_utc TEXT,
            url TEXT,
            score INTEGER,
            num_comments INTEGER
        );
        CREATE TABLE IF NOT EXISTS analyses (
            post_id TEXT PRIMARY KEY,
            topic TEXT,
            tone TEXT,
            source TEXT,
            risk TEXT,
            sentiment_score REAL,
            raw JSON,
            processed_at TEXT
        );
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id TEXT,
            risk TEXT,
            reason TEXT,
            created_at TEXT
        );
        """
    )
    conn.commit()
    conn.close()


class Storage:
    """Simple SQLite-backed repository for processed data and alerts."""

    def __init__(self) -> None:
        init_db()
        self.path = DB_PATH

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path)

    def upsert_post(self, post: Dict[str, Any]) -> None:
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO posts (id, subreddit, title, author, created_utc, url, score, num_comments)
            VALUES (:id, :subreddit, :title, :author, :created_utc, :url, :score, :num_comments)
            """,
            {
                "id": post["id"],
                "subreddit": post.get("subreddit"),
                "title": post.get("title"),
                "author": post.get("author"),
                "created_utc": post.get("created_utc"),
                "url": post.get("url"),
                "score": post.get("score", 0),
                "num_comments": post.get("num_comments", 0),
            },
        )
        conn.commit()
        conn.close()

    def save_analysis(self, post_id: str, result: Dict[str, Any]) -> None:
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO analyses
            (post_id, topic, tone, source, risk, sentiment_score, raw, processed_at)
            VALUES (:post_id, :topic, :tone, :source, :risk, :sentiment_score, :raw, :processed_at)
            """,
            {
                "post_id": post_id,
                "topic": result.get("topic"),
                "tone": result.get("tone"),
                "source": result.get("source"),
                "risk": result.get("risk"),
                "sentiment_score": result.get("sentiment_score"),
                "raw": json.dumps(result),
                "processed_at": datetime.utcnow().isoformat(),
            },
        )
        conn.commit()
        conn.close()

    def add_alert(self, post_id: str, risk: str, reason: str) -> None:
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO alerts (post_id, risk, reason, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (post_id, risk, reason, datetime.utcnow().isoformat()),
        )
        conn.commit()
        conn.close()

    def get_alerts(self, limit: int = 50) -> List[Dict[str, Any]]:
        conn = self._connect()
        cursor = conn.cursor()
        rows = cursor.execute(
            """
            SELECT alerts.post_id, alerts.risk, alerts.reason, alerts.created_at, posts.title, posts.subreddit, posts.url
            FROM alerts
            LEFT JOIN posts ON posts.id = alerts.post_id
            ORDER BY alerts.created_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        conn.close()
        return [
            {
                "post_id": row[0],
                "risk": row[1],
                "reason": row[2],
                "created_at": row[3],
                "title": row[4],
                "subreddit": row[5],
                "url": row[6],
            }
            for row in rows
        ]

    def recent_analyses(self, window_hours: int = 24) -> List[Dict[str, Any]]:
        conn = self._connect()
        cursor = conn.cursor()
        since = datetime.utcnow().timestamp() - (window_hours * 3600)
        rows = cursor.execute(
            """
            SELECT analyses.post_id, analyses.topic, analyses.tone, analyses.source, analyses.risk,
                   analyses.sentiment_score, analyses.processed_at, posts.subreddit, posts.title
            FROM analyses
            LEFT JOIN posts ON posts.id = analyses.post_id
            WHERE strftime('%s', analyses.processed_at) >= ?
            ORDER BY analyses.processed_at DESC
            """,
            (since,),
        ).fetchall()
        conn.close()
        return [
            {
                "post_id": row[0],
                "topic": row[1],
                "tone": row[2],
                "source": row[3],
                "risk": row[4],
                "sentiment_score": row[5],
                "processed_at": row[6],
                "subreddit": row[7],
                "title": row[8],
            }
            for row in rows
        ]


storage = Storage()
