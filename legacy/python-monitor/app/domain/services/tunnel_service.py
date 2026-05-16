"""
Tunnel service — wraps legacy tunnel_manager module.
TODO remove legacy adapter in Phase 4 — inline tunnel logic here.
"""
import threading


class TunnelService:
    """
    Service interface for public tunnel management.
    Currently wraps the legacy tunnel_manager singleton.
    """

    def __init__(self, legacy_tunnel_manager=None):
        """
        Args:
            legacy_tunnel_manager: the existing tunnel_manager module singleton.
                                   If None, imports it lazily.
        """
        if legacy_tunnel_manager is None:
            from tunnel import tunnel_manager as _tm
            legacy_tunnel_manager = _tm
        self._legacy = legacy_tunnel_manager

    def start(self):
        self._legacy.start()

    def stop(self):
        self._legacy.stop()

    def get_public_url(self) -> str:
        return self._legacy.get_public_url()

    def get_status(self) -> dict:
        return self._legacy.get_status()
