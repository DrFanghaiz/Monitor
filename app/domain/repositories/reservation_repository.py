"""
Reservation repository — handles all CRUD for `reservations` table.
"""
from app.infrastructure.database.connection import ConnectionManager


class ReservationRepository:
    """Data access for reservations table."""

    def __init__(self, conn_mgr: ConnectionManager):
        self._conn_mgr = conn_mgr

    def add_reservation(self, user_name: str, date: str, start_hour: int, end_hour: int) -> int:
        """Add a reservation. Returns the new record ID."""
        with self._conn_mgr.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO reservations (user_name, date, start_hour, end_hour) VALUES (?, ?, ?, ?)",
                (user_name, date, start_hour, end_hour)
            )
            conn.commit()
            return cursor.lastrowid

    def get_reservations(self, date: str = None) -> list:
        """Get reservations, optionally filtered by date."""
        with self._conn_mgr.connection() as conn:
            cursor = conn.cursor()
            if date:
                cursor.execute(
                    "SELECT * FROM reservations WHERE date = ? AND status = 'active' ORDER BY start_hour",
                    (date,)
                )
            else:
                cursor.execute(
                    "SELECT * FROM reservations WHERE status = 'active' ORDER BY date, start_hour"
                )
            return [dict(row) for row in cursor.fetchall()]

    def check_reservation_conflict(self, date: str, start_hour: int, end_hour: int,
                                   exclude_id: int = None) -> bool:
        """Check if a reservation time slot conflicts with existing ones."""
        with self._conn_mgr.connection() as conn:
            cursor = conn.cursor()
            if exclude_id:
                cursor.execute('''
                    SELECT COUNT(*) FROM reservations
                    WHERE date = ? AND status = 'active' AND id != ?
                    AND ((start_hour < ? AND end_hour > ?) OR (start_hour < ? AND end_hour > ?))
                ''', (date, exclude_id, end_hour, start_hour, end_hour, start_hour))
            else:
                cursor.execute('''
                    SELECT COUNT(*) FROM reservations
                    WHERE date = ? AND status = 'active'
                    AND ((start_hour < ? AND end_hour > ?) OR (start_hour < ? AND end_hour > ?))
                ''', (date, end_hour, start_hour, end_hour, start_hour))
            return cursor.fetchone()[0] > 0

    def cancel_reservation(self, reservation_id: int):
        """Cancel a reservation (soft delete by setting status='cancelled')."""
        with self._conn_mgr.connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE reservations SET status = 'cancelled' WHERE id = ?", (reservation_id,))
            conn.commit()

    def get_today_reservations(self, today_str: str) -> list:
        """Get today's active reservations."""
        return self.get_reservations(today_str)
