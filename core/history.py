import os
import sqlite3
import json
from datetime import datetime, timedelta


class HistoryManager:
    """Stores SMS sending history in SQLite."""

    MAX_SESSIONS = 1000
    RETENTION_DAYS = 90  # RODO: auto-purge sessions older than this

    def __init__(self, db_path: str):
        self._db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with self._conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    message TEXT NOT NULL,
                    source_file TEXT NOT NULL,
                    recipients_json TEXT NOT NULL
                )
            """)

    def _conn(self) -> sqlite3.Connection:
        return sqlite3.connect(self._db_path)

    def save_session(self, message: str, source_file: str, recipients: list[dict]) -> int:
        """Save a sending session. Returns session ID."""
        with self._conn() as conn:
            cursor = conn.execute(
                "INSERT INTO sessions (created_at, message, source_file, recipients_json) "
                "VALUES (?, ?, ?, ?)",
                (
                    datetime.now().isoformat(),
                    message,
                    source_file,
                    json.dumps(recipients, ensure_ascii=False),
                ),
            )
            session_id = cursor.lastrowid
            self._enforce_limit(conn)
            self._enforce_retention(conn)
            return session_id

    def delete_session(self, session_id: int) -> None:
        """Permanently delete a single session."""
        with self._conn() as conn:
            conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))

    def clear_all(self) -> None:
        """Permanently delete the entire sending history."""
        with self._conn() as conn:
            conn.execute("DELETE FROM sessions")

    def _enforce_retention(self, conn: sqlite3.Connection) -> None:
        """Delete sessions older than RETENTION_DAYS (RODO data minimisation)."""
        if not self.RETENTION_DAYS:
            return
        cutoff = (datetime.now() - timedelta(days=self.RETENTION_DAYS)).isoformat()
        conn.execute("DELETE FROM sessions WHERE created_at < ?", (cutoff,))

    def list_sessions(self) -> list[dict]:
        """Return all sessions, newest first."""
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT id, created_at, message, source_file, recipients_json "
                "FROM sessions ORDER BY id DESC"
            ).fetchall()

        sessions = []
        for row in rows:
            recipients = json.loads(row[4])
            sessions.append({
                "id": row[0],
                "created_at": row[1],
                "message": row[2],
                "source_file": row[3],
                "total": len(recipients),
                "sent": sum(1 for r in recipients if r["status"] == "sent"),
                "errors": sum(1 for r in recipients if r["status"] == "error"),
            })
        return sessions

    def get_session(self, session_id: int) -> dict | None:
        """Return full session details including recipients."""
        with self._conn() as conn:
            row = conn.execute(
                "SELECT id, created_at, message, source_file, recipients_json "
                "FROM sessions WHERE id = ?",
                (session_id,),
            ).fetchone()

        if not row:
            return None

        recipients = json.loads(row[4])
        return {
            "id": row[0],
            "created_at": row[1],
            "message": row[2],
            "source_file": row[3],
            "recipients": recipients,
            "total": len(recipients),
            "sent": sum(1 for r in recipients if r["status"] == "sent"),
            "errors": sum(1 for r in recipients if r["status"] == "error"),
        }

    def _enforce_limit(self, conn: sqlite3.Connection) -> None:
        count = conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
        if count > self.MAX_SESSIONS:
            excess = count - self.MAX_SESSIONS
            conn.execute(
                "DELETE FROM sessions WHERE id IN "
                "(SELECT id FROM sessions ORDER BY id ASC LIMIT ?)",
                (excess,),
            )
