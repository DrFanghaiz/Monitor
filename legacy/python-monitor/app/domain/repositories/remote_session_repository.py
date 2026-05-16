"""
Remote session repository — handles CRUD for `remote_sessions` table.
"""
from app.infrastructure.database.connection import ConnectionManager


class RemoteSessionRepository:
    """Data access for remote_sessions table."""

    def __init__(self, conn_mgr: ConnectionManager):
        self._conn_mgr = conn_mgr

    def add_remote_session(self, remote_type: str) -> int:
        """Start a new remote session. Returns the session ID."""
        with self._conn_mgr.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO remote_sessions (remote_type, start_time, is_active) VALUES (?, datetime('now', 'localtime'), 1)",
                (remote_type,)
            )
            conn.commit()
            return cursor.lastrowid

    def end_remote_session(self, session_id: int):
        """End a remote session."""
        with self._conn_mgr.connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE remote_sessions
                SET end_time = datetime('now', 'localtime'),
                    duration_seconds = CAST((julianday('now', 'localtime') - julianday(start_time)) * 86400 AS INTEGER),
                    is_active = 0
                WHERE id = ?
            ''', (session_id,))
            conn.commit()

    def get_active_remote_session(self) -> dict:
        """Get the currently active remote session, or None."""
        with self._conn_mgr.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM remote_sessions WHERE is_active = 1 ORDER BY start_time DESC LIMIT 1"
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_recent_remote_sessions(self, limit: int = 20) -> list:
        """Get recent remote sessions."""
        with self._conn_mgr.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM remote_sessions ORDER BY start_time DESC LIMIT ?",
                (limit,)
            )
            return [dict(row) for row in cursor.fetchall()]
