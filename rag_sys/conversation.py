import sqlite3
import json
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
from contextlib import contextmanager

logger = logging.getLogger(__name__)

@dataclass
class Conversation:
    """Represents a conversation with metadata"""
    id: int
    title: str
    start_time: datetime
    last_updated: datetime
    messages: List[Dict]
    summary: str

class ConversationStore:
    """Manages persistent storage of conversations"""
    
    def __init__(self, db_path: str = "conversations.db"):
        self.db_path = db_path
        self._init_db()

    @contextmanager
    def _get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(
            self.db_path,
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
        )
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self):
        """Initialize the database schema"""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    start_time TIMESTAMP NOT NULL,
                    last_updated TIMESTAMP NOT NULL,
                    messages TEXT NOT NULL,
                    summary TEXT
                )
            """)
            conn.commit()

    def create_conversation(self, title: str) -> int:
        """Create a new conversation and return its ID"""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO conversations (title, start_time, last_updated, messages, summary)
                VALUES (?, ?, ?, ?, ?)
            """, (title, datetime.now(), datetime.now(), "[]", ""))
            conn.commit()
            return cursor.lastrowid

    def update_conversation(self, conv_id: int, messages: List[Dict], summary: str = None):
        """Update an existing conversation"""
        with self._get_connection() as conn:
            conn.execute("""
                UPDATE conversations
                SET messages = ?, last_updated = ?, summary = ?
                WHERE id = ?
            """, (json.dumps(messages), datetime.now(), summary, conv_id))
            conn.commit()

    def get_conversation(self, conv_id: int) -> Optional[Conversation]:
        """Retrieve a conversation by ID"""
        with self._get_connection() as conn:
            row = conn.execute("""
                SELECT * FROM conversations WHERE id = ?
            """, (conv_id,)).fetchone()
            
            if row:
                return Conversation(
                    id=row['id'],
                    title=row['title'],
                    start_time=row['start_time'],
                    last_updated=row['last_updated'],
                    messages=json.loads(row['messages']),
                    summary=row['summary']
                )
        return None

    def list_conversations(self, limit: int = 10, offset: int = 0) -> List[Tuple[int, str, datetime, str]]:
        """List recent conversations with their IDs and summaries"""
        with self._get_connection() as conn:
            return conn.execute("""
                SELECT id, title, last_updated, summary
                FROM conversations
                ORDER BY last_updated DESC
                LIMIT ? OFFSET ?
            """, (limit, offset)).fetchall()

    def search_conversations(self, query: str) -> List[Tuple[int, str, datetime, str]]:
        """Search conversations by content or summary"""
        with self._get_connection() as conn:
            return conn.execute("""
                SELECT id, title, last_updated, summary
                FROM conversations
                WHERE title LIKE ? OR messages LIKE ? OR summary LIKE ?
                ORDER BY last_updated DESC
            """, (f"%{query}%", f"%{query}%", f"%{query}%")).fetchall()