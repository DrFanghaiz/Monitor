"""
History ViewModel — bridges TimerService and HistoryFrame.
Manages edit mode state and record formatting for display.
"""


class HistoryViewModel:
    """Provides history data and edit-mode state for HistoryFrame."""

    def __init__(self, timer_service, password_manager):
        self._svc = timer_service
        self._pwd = password_manager
        self.is_edit_mode = False
        self.search_text = ""

    # ---- data access ----

    def load_records(self, filter_mode: str = "all") -> list:
        """Get usage records, filtered by current search text.
        Returns raw dicts — HistoryFrame handles avatar/time formatting in the view.
        """
        records = self._svc.get_history(filter_mode, self.search_text)
        # Pre-compute max duration for the visual bar
        max_dur = max((r['duration_seconds'] for r in records), default=1)
        return records, max_dur

    def delete_record(self, record_id: int):
        self._svc.delete_record(record_id)

    def delete_records(self, record_ids: list):
        self._svc.delete_records(record_ids)

    # ---- auth ----

    def check_password(self, password: str) -> bool:
        return self._pwd.check_admin_password(password)

    # ---- edit mode ----

    def enter_edit_mode(self):
        self.is_edit_mode = True
        self.search_text = ""

    def exit_edit_mode(self):
        self.is_edit_mode = False
        self.search_text = ""
