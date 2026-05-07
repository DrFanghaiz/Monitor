"""
Timer service — single source of truth for timer state and usage record persistence.
TimerFrame subscribes to this service for display; no dual state.
"""
import time
from datetime import datetime
from app.domain.repositories.usage_repository import UsageRepository
from app.domain.repositories.audit_repository import AuditRepository


class TimerService:
    """Manages timer lifecycle. The single authoritative source of timer state."""

    def __init__(self, usage_repo: UsageRepository, audit_repo: AuditRepository):
        self._usage_repo = usage_repo
        self._audit_repo = audit_repo
        self._reset_state()

    # ---- public state (read by TimerFrame and StatusService) ----
    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def current_user_name(self) -> str:
        return self._user_name

    @property
    def start_timestamp(self):
        return self._start_timestamp

    @property
    def start_counter(self) -> float:
        return self._start_counter

    # ---- lifecycle ----

    def _reset_state(self):
        self._running = False
        self._user_name = ""
        self._start_timestamp = None
        self._start_counter = 0.0

    def start_timer(self, user_name: str) -> bool:
        """Start timing for a user. Returns False if name is empty.
        Caller (TimerFrame) should call this AFTER any entry animation completes,
        so the recorded start time matches the display start time.
        """
        name = user_name.strip() if user_name else ""
        if not name:
            return False
        self._user_name = name
        self._start_timestamp = datetime.now()
        self._start_counter = time.time()
        self._running = True
        self._audit_repo.log_action("timer_start", f"{name} 开始计时")
        return True

    def stop_timer(self) -> dict:
        """Stop timing, persist the usage record. Returns result dict or None.
        This is the ONLY path to persist a completed usage record.
        """
        if not self._running:
            return None
        end_dt = datetime.now()
        sec = int((end_dt - self._start_timestamp).total_seconds())
        self._usage_repo.add_usage_record(self._user_name, self._start_timestamp, end_dt)

        h, r = divmod(sec, 3600)
        m, s = divmod(r, 60)
        result = {
            "user_name": self._user_name,
            "duration_seconds": sec,
            "duration_formatted": f"{h:02}小时{m:02}分{s:02}秒",
            "elapsed_formatted": f"{h:02}:{m:02}:{s:02}",
        }
        self._audit_repo.log_action("timer_stop",
                                     f"{self._user_name} 停止计时, 时长{sec}秒")
        self._reset_state()
        return result

    def get_state(self) -> dict:
        """Get current timer state (for GUI display and web API)."""
        if not self._running:
            return {
                "is_running": False,
                "current_user": None,
                "start_time": None,
                "elapsed_seconds": 0,
                "elapsed_formatted": "00:00:00",
            }
        elapsed = int(time.time() - self._start_counter)
        h, r = divmod(elapsed, 3600)
        m, s = divmod(r, 60)
        return {
            "is_running": True,
            "current_user": self._user_name,
            "start_time": self._start_timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "elapsed_seconds": elapsed,
            "elapsed_formatted": f"{h:02}:{m:02}:{s:02}",
        }

    # ---- History / record management ----

    def get_history(self, filter_mode: str = "all", filter_text: str = "") -> list:
        """Get usage records, optionally filtered by name."""
        records = self._usage_repo.get_usage_records(filter_mode)
        if filter_text:
            records = [r for r in records if filter_text.lower() in r["user_name"].lower()]
        return records

    def delete_record(self, record_id: int):
        """Delete a single usage record."""
        self._usage_repo.delete_usage_record(record_id)
        self._audit_repo.log_action("delete_record", f"删除记录 ID: {record_id}")

    def delete_records(self, record_ids: list):
        """Delete multiple usage records."""
        if not record_ids:
            return
        self._usage_repo.delete_usage_records(record_ids)
        self._audit_repo.log_action("delete_records", f"批量删除 {len(record_ids)} 条记录")
