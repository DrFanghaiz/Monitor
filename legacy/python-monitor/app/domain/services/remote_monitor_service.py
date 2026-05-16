"""
Remote monitor service — wraps legacy remote_monitor module.
TODO remove legacy adapter in Phase 4 — inline process detection logic here.
"""
import threading


class RemoteMonitorService:
    """
    Service interface for remote control detection.
    Currently wraps the legacy remote_monitor singleton.
    """

    def __init__(self, legacy_remote_monitor=None):
        """
        Args:
            legacy_remote_monitor: the existing remote_monitor module singleton.
                                   If None, imports it lazily.
        """
        if legacy_remote_monitor is None:
            from remote_monitor import remote_monitor as _rm
            legacy_remote_monitor = _rm
        self._legacy = legacy_remote_monitor

    def start(self):
        self._legacy.start()

    def stop(self):
        self._legacy.stop()

    def get_status(self) -> dict:
        return self._legacy.get_status()
