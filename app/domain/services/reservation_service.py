"""
Reservation service — handles reservation business logic.
"""
from app.domain.repositories.reservation_repository import ReservationRepository
from app.domain.repositories.audit_repository import AuditRepository


class ReservationService:
    """Manages reservation lifecycle: create, query, conflict check, cancel."""

    def __init__(self, reservation_repo: ReservationRepository, audit_repo: AuditRepository):
        self._repo = reservation_repo
        self._audit_repo = audit_repo

    def get_reservations(self, date: str = None) -> list:
        """Get reservations, optionally filtered by date."""
        return self._repo.get_reservations(date)

    def create_reservation(self, user_name: str, date: str,
                           start_hour: int, end_hour: int) -> tuple:
        """
        Create a reservation. Returns (success: bool, message: str, id: int|None).
        """
        name = user_name.strip() if user_name else ""
        if not name:
            return False, "请输入姓名", None

        if start_hour >= end_hour:
            return False, "结束时间必须晚于开始时间", None

        if self._repo.check_reservation_conflict(date, start_hour, end_hour):
            return False, "该时段已被预约", None

        rid = self._repo.add_reservation(name, date, start_hour, end_hour)
        self._audit_repo.log_action("add_reservation",
                                     f"{name} 预约 {date} {start_hour}:00-{end_hour}:00")
        return True, "预约成功", rid

    def cancel_reservation(self, reservation_id: int):
        """Cancel a reservation."""
        self._repo.cancel_reservation(reservation_id)
        self._audit_repo.log_action("cancel_reservation", f"取消预约 ID: {reservation_id}")

    def check_conflict(self, date: str, start_hour: int, end_hour: int,
                       exclude_id: int = None) -> bool:
        """Check if a time slot conflicts with existing reservations."""
        return self._repo.check_reservation_conflict(date, start_hour, end_hour, exclude_id)

    def get_today_reservations(self, today_str: str) -> list:
        """Get today's active reservations."""
        return self._repo.get_today_reservations(today_str)
