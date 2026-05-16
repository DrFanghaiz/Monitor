"""
Status service — unified state aggregation entry point.
Provides a single source of truth for both desktop sidebar and web API.
"""
from datetime import datetime, date


class StatusService:
    """
    Aggregates local timer state, remote control state, today's records,
    and today's reservations into a single AppStatus dict.

    This is THE unified entry point for both GUI status panel and Web API.
    """

    def __init__(self, timer_service, remote_monitor_service,
                 usage_repo, reservation_repo):
        self._timer = timer_service
        self._remote = remote_monitor_service
        self._usage_repo = usage_repo
        self._reservation_repo = reservation_repo

    def get_full_status(self) -> dict:
        """Get complete aggregated status for GUI and Web consumption."""
        timer_state = self._timer.get_state()
        remote_state = self._remote.get_status()

        # Determine computer status
        if remote_state.get("is_remote"):
            computer_status = "remote_controlled"
        elif timer_state.get("is_running"):
            computer_status = "in_use"
        else:
            computer_status = "idle"

        today_records = self._usage_repo.get_today_records()
        today_str = date.today().strftime("%Y-%m-%d")
        today_reservations = self._reservation_repo.get_today_reservations(today_str)

        return {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "computer_status": computer_status,
            "local_use": {
                "current_user": timer_state.get("current_user"),
                "start_time": timer_state.get("start_time"),
                "elapsed_seconds": timer_state.get("elapsed_seconds", 0),
                "elapsed_formatted": timer_state.get("elapsed_formatted", "00:00:00"),
            },
            "remote_control": remote_state,
            "today_records": today_records,
            "today_reservations": today_reservations,
        }

    def get_sidebar_status(self) -> dict:
        """Get lightweight status for sidebar panel."""
        timer_state = self._timer.get_state()
        remote_state = self._remote.get_status()
        return {
            "is_timing": timer_state.get("is_running", False),
            "current_user": timer_state.get("current_user"),
            "is_remote": remote_state.get("is_remote", False),
            "remote_type": remote_state.get("remote_type"),
        }
