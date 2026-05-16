"""
Compatibility wrapper — delegates to app.presentation.web.server.WebServer.
TODO retire this file when all consumers use the service container directly.
"""
from app.presentation.web.server import WebServer as _WebServer

# Lazy-imported legacy singletons (only used when no services are injected)
_legacy_config = None
_legacy_web_access = None
_legacy_status = None


def _ensure_legacy():
    """Create a WebServer backed by legacy singletons (backward compat path)."""
    global _legacy_config, _legacy_web_access, _legacy_status
    if _legacy_config is None:
        from config import config as _c
        _legacy_config = _c
    if _legacy_web_access is None:
        from app.domain.services.web_access_service import WebAccessService
        _legacy_web_access = WebAccessService(_legacy_config)
    if _legacy_status is None:
        from app.domain.services.status_service import StatusService
        from app.domain.services.timer_service import TimerService
        from app.domain.services.remote_monitor_service import RemoteMonitorService
        from app.domain.repositories.usage_repository import UsageRepository
        from app.domain.repositories.reservation_repository import ReservationRepository
        from app.domain.repositories.audit_repository import AuditRepository
        from app.infrastructure.database.connection import ConnectionManager
        from app.infrastructure.database.schema import init_schema
        from app.infrastructure.database.migration import migrate_from_txt
        from app.core.paths import DB_FILE, OLD_TXT_FILE

        conn_mgr = ConnectionManager(DB_FILE)
        init_schema(conn_mgr)
        migrate_from_txt(conn_mgr, OLD_TXT_FILE)
        usage_repo = UsageRepository(conn_mgr)
        reservation_repo = ReservationRepository(conn_mgr)
        audit_repo = AuditRepository(conn_mgr)
        timer_svc = TimerService(usage_repo, audit_repo)
        remote_svc = RemoteMonitorService()
        _legacy_status = StatusService(timer_svc, remote_svc, usage_repo, reservation_repo)

    return _WebServer(_legacy_config, _legacy_web_access, _legacy_status)


# Module-level singleton (backward compat for old importers)
_configured_instance = None


def set_web_server_instance(instance):
    """Called by bootstrap to inject the properly-configured WebServer.
    After this call, the module-level `web_server` returns the injected instance.
    """
    global _configured_instance
    _configured_instance = instance


class _WebServerProxy:
    """Proxy that returns the injected instance or creates a legacy fallback."""

    def __getattr__(self, name):
        if _configured_instance is not None:
            return getattr(_configured_instance, name)
        return getattr(_ensure_legacy(), name)


web_server = _WebServerProxy()


# ---- Deprecated: kept for backward compat only ----
# set_local_state_callback is now a no-op. Local state is provided by status_service.
_local_state_callback = None


def set_local_state_callback(callback):
    """
    DEPRECATED — local state is now provided exclusively by status_service.
    This function is kept as a no-op for backward compat.
    """
    global _local_state_callback
    _local_state_callback = callback
