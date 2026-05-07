"""
Timer ViewModel — bridges TimerService and TimerFrame.
Handles display-state transformation for the timer UI.
"""


class TimerViewModel:
    """Provides timer data in a format ready for UI consumption."""

    def __init__(self, timer_service):
        self._svc = timer_service

    # ---- delegated properties (read-only from service) ----

    @property
    def is_running(self) -> bool:
        return self._svc.is_running

    @property
    def current_user_name(self) -> str:
        return self._svc.current_user_name

    # ---- actions ----

    def start(self, user_name: str) -> bool:
        """Start timing. Returns False if name is empty."""
        return self._svc.start_timer(user_name)

    def stop(self) -> dict:
        """Stop timing and persist. Returns result dict with duration info."""
        return self._svc.stop_timer()

    def get_elapsed_display(self) -> str:
        """Get formatted elapsed time for the timer label (HH:MM:SS)."""
        state = self._svc.get_state()
        return state["elapsed_formatted"]

    def get_state(self) -> dict:
        """Get full timer state dict."""
        return self._svc.get_state()
