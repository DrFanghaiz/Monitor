"""
TODO remove legacy adapter in Phase 3/4.

Compatibility facade over repositories.
All data access now delegates to app/domain/repositories/.
This module exists only to avoid breaking existing import paths
while the UI layer is being migrated to use services directly.
"""
from datetime import datetime, date

from app.infrastructure.database.connection import ConnectionManager
from app.infrastructure.database.schema import init_schema
from app.infrastructure.database.migration import migrate_from_txt
from app.domain.repositories.usage_repository import UsageRepository
from app.domain.repositories.reservation_repository import ReservationRepository
from app.domain.repositories.remote_session_repository import RemoteSessionRepository
from app.domain.repositories.audit_repository import AuditRepository
from app.core.paths import DB_FILE, OLD_TXT_FILE

# ---- One-time initialization (preserves original import-time behavior) ----
_conn_mgr = ConnectionManager(DB_FILE)
init_schema(_conn_mgr)
migrate_from_txt(_conn_mgr, OLD_TXT_FILE)

# ---- Repository instances (created once, shared by the facade) ----
_usage_repo = UsageRepository(_conn_mgr)
_reservation_repo = ReservationRepository(_conn_mgr)
_remote_session_repo = RemoteSessionRepository(_conn_mgr)
_audit_repo = AuditRepository(_conn_mgr)


class Database:
    """Compatibility wrapper — delegates to repositories.
    TODO remove legacy adapter in Phase 3/4.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    # ========== 使用记录 ==========

    def add_usage_record(self, user_name: str, start_time: datetime, end_time: datetime) -> int:
        record_id = _usage_repo.add_usage_record(user_name, start_time, end_time)
        return record_id

    def get_usage_records(self, filter_mode: str = "all") -> list:
        return _usage_repo.get_usage_records(filter_mode)

    def get_user_stats(self, filter_mode: str = "all") -> list:
        return _usage_repo.get_user_stats(filter_mode)

    def delete_usage_record(self, record_id: int):
        _usage_repo.delete_usage_record(record_id)
        _audit_repo.log_action("delete_record", f"删除记录 ID: {record_id}")

    def delete_usage_records(self, record_ids: list):
        _usage_repo.delete_usage_records(record_ids)
        _audit_repo.log_action("delete_records", f"批量删除 {len(record_ids)} 条记录")

    # ========== 预约 ==========

    def add_reservation(self, user_name: str, date_str: str, start_hour: int, end_hour: int) -> int:
        reservation_id = _reservation_repo.add_reservation(user_name, date_str, start_hour, end_hour)
        _audit_repo.log_action("add_reservation", f"{user_name} 预约 {date_str} {start_hour}:00-{end_hour}:00")
        return reservation_id

    def get_reservations(self, date_str: str = None) -> list:
        return _reservation_repo.get_reservations(date_str)

    def check_reservation_conflict(self, date_str: str, start_hour: int, end_hour: int,
                                   exclude_id: int = None) -> bool:
        return _reservation_repo.check_reservation_conflict(date_str, start_hour, end_hour, exclude_id)

    def cancel_reservation(self, reservation_id: int):
        _reservation_repo.cancel_reservation(reservation_id)
        _audit_repo.log_action("cancel_reservation", f"取消预约 ID: {reservation_id}")

    # ========== 审计日志 ==========

    def log_action(self, action: str, details: str = None):
        _audit_repo.log_action(action, details)

    def get_audit_logs(self, limit: int = 100) -> list:
        return _audit_repo.get_audit_logs(limit)

    # ========== 统计数据 ==========

    def get_hourly_stats(self) -> list:
        return _usage_repo.get_hourly_stats()

    def get_daily_stats(self, days: int = 30) -> list:
        return _usage_repo.get_daily_stats(days)

    def get_user_distribution(self, filter_mode: str = "all") -> list:
        return _usage_repo.get_user_distribution(filter_mode)

    # ========== 远程控制会话 ==========

    def add_remote_session(self, remote_type: str) -> int:
        session_id = _remote_session_repo.add_remote_session(remote_type)
        _audit_repo.log_action("remote_start", f"远程控制开始: {remote_type}")
        return session_id

    def end_remote_session(self, session_id: int):
        _remote_session_repo.end_remote_session(session_id)
        _audit_repo.log_action("remote_end", f"远程控制结束: session {session_id}")

    def get_active_remote_session(self) -> dict:
        return _remote_session_repo.get_active_remote_session()

    def get_recent_remote_sessions(self, limit: int = 20) -> list:
        return _remote_session_repo.get_recent_remote_sessions(limit)

    # ========== 综合状态（Phase 3 将迁移到 status_service）==========

    def get_current_status(self) -> dict:
        """
        获取综合状态信息 — 供 Web API 和 GUI 状态面板使用。
        TODO Phase 3: move this aggregation logic to status_service.
        """
        remote_session = _remote_session_repo.get_active_remote_session()
        remote_info = None
        if remote_session:
            start = datetime.strptime(remote_session['start_time'], "%Y-%m-%d %H:%M:%S")
            elapsed = int((datetime.now() - start).total_seconds())
            h, r = divmod(elapsed, 3600)
            m, s = divmod(r, 60)
            remote_info = {
                "is_active": True,
                "remote_type": remote_session['remote_type'],
                "start_time": remote_session['start_time'],
                "elapsed_seconds": elapsed,
                "elapsed_formatted": f"{h:02}:{m:02}:{s:02}"
            }
        else:
            remote_info = {
                "is_active": False,
                "remote_type": None,
                "start_time": None,
                "elapsed_seconds": 0,
                "elapsed_formatted": "00:00:00"
            }

        today_records = _usage_repo.get_today_records()
        today_str = date.today().strftime("%Y-%m-%d")
        today_reservations = _reservation_repo.get_today_reservations(today_str)

        return {
            "remote_control": remote_info,
            "today_records": today_records,
            "today_reservations": today_reservations
        }


# Global database instance (preserved for backward compatibility)
db = Database()
