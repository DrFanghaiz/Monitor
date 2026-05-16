"""
Audit log repository — handles read/write for `audit_log` table.
"""
from app.infrastructure.database.connection import ConnectionManager


class AuditRepository:
    """Data access for audit_log table."""

    def __init__(self, conn_mgr: ConnectionManager):
        self._conn_mgr = conn_mgr

    def log_action(self, action: str, details: str = None):
        """Write an audit log entry."""
        with self._conn_mgr.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO audit_log (action, details) VALUES (?, ?)",
                (action, details)
            )
            conn.commit()

    def get_audit_logs(self, limit: int = 100) -> list:
        """Get recent audit log entries."""
        with self._conn_mgr.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM audit_log ORDER BY timestamp DESC LIMIT ?",
                (limit,)
            )
            return [dict(row) for row in cursor.fetchall()]
