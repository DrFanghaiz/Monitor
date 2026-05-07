"""
Usage records repository — handles all CRUD and statistics queries for `usage_records` table.
"""
from datetime import datetime
from app.infrastructure.database.connection import ConnectionManager


class UsageRepository:
    """Data access for usage_records table."""

    def __init__(self, conn_mgr: ConnectionManager):
        self._conn_mgr = conn_mgr

    def add_usage_record(self, user_name: str, start_time: datetime, end_time: datetime) -> int:
        """Add a usage record. Returns the new record ID."""
        duration = int((end_time - start_time).total_seconds())
        with self._conn_mgr.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO usage_records (user_name, start_time, end_time, duration_seconds) VALUES (?, ?, ?, ?)",
                (user_name, start_time.strftime("%Y-%m-%d %H:%M:%S"),
                 end_time.strftime("%Y-%m-%d %H:%M:%S"), duration)
            )
            conn.commit()
            return cursor.lastrowid

    def get_usage_records(self, filter_mode: str = "all") -> list:
        """Get usage records filtered by mode ('今日', '本月', 'all')."""
        with self._conn_mgr.connection() as conn:
            cursor = conn.cursor()
            if filter_mode == "今日":
                cursor.execute(
                    "SELECT * FROM usage_records WHERE date(start_time) = date('now', 'localtime') ORDER BY start_time DESC"
                )
            elif filter_mode == "本月":
                cursor.execute(
                    "SELECT * FROM usage_records WHERE strftime('%Y-%m', start_time) = strftime('%Y-%m', 'now', 'localtime') ORDER BY start_time DESC"
                )
            else:
                cursor.execute("SELECT * FROM usage_records ORDER BY start_time DESC")
            return [dict(row) for row in cursor.fetchall()]

    def get_today_records(self) -> list:
        """Get today's usage records."""
        return self.get_usage_records("今日")

    def get_user_stats(self, filter_mode: str = "all") -> list:
        """Get aggregated user statistics."""
        with self._conn_mgr.connection() as conn:
            cursor = conn.cursor()
            if filter_mode == "今日":
                date_filter = "AND date(start_time) = date('now', 'localtime')"
            elif filter_mode == "本月":
                date_filter = "AND strftime('%Y-%m', start_time) = strftime('%Y-%m', 'now', 'localtime')"
            else:
                date_filter = ""
            cursor.execute(f'''
                SELECT user_name,
                       SUM(duration_seconds) as total_seconds,
                       MAX(end_time) as last_seen
                FROM usage_records
                WHERE 1=1 {date_filter}
                GROUP BY user_name
                ORDER BY total_seconds DESC
            ''')
            return [dict(row) for row in cursor.fetchall()]

    def delete_usage_record(self, record_id: int):
        """Delete a single usage record."""
        with self._conn_mgr.connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM usage_records WHERE id = ?", (record_id,))
            conn.commit()

    def delete_usage_records(self, record_ids: list):
        """Delete multiple usage records."""
        if not record_ids:
            return
        with self._conn_mgr.connection() as conn:
            cursor = conn.cursor()
            placeholders = ",".join("?" * len(record_ids))
            cursor.execute(f"DELETE FROM usage_records WHERE id IN ({placeholders})", record_ids)
            conn.commit()

    def get_hourly_stats(self) -> list:
        """Get hourly usage statistics for heatmap."""
        with self._conn_mgr.connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT date(start_time) as date,
                       CAST(strftime('%H', start_time) as INTEGER) as hour,
                       SUM(duration_seconds) / 3600.0 as hours
                FROM usage_records
                GROUP BY date(start_time), strftime('%H', start_time)
            ''')
            return [dict(row) for row in cursor.fetchall()]

    def get_daily_stats(self, days: int = 30) -> list:
        """Get daily usage statistics for trend chart."""
        with self._conn_mgr.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f'''
                SELECT date(start_time) as date,
                       SUM(duration_seconds) / 3600.0 as hours,
                       COUNT(DISTINCT user_name) as users
                FROM usage_records
                WHERE date(start_time) >= date('now', 'localtime', '-{days} days')
                GROUP BY date(start_time)
                ORDER BY date
            ''')
            return [dict(row) for row in cursor.fetchall()]

    def get_user_distribution(self, filter_mode: str = "all") -> list:
        """Get user distribution for pie chart."""
        return self.get_user_stats(filter_mode)
