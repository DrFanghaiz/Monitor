"""
Service layer — business logic services and the ServiceContainer.

Services are created centrally by app_bootstrap.py and injected into the App.
For backward compat (python timer.py), create_legacy_services() wraps the
existing module-level singletons.
"""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ServiceContainer:
    """Holds all service instances. Injected into App and accessible by all frames."""
    timer: object = None
    reservation: object = None
    statistics: object = None
    status: object = None
    remote_monitor: object = None
    tunnel: object = None
    # Infrastructure references (exposed through container, not imported directly by frames)
    config: object = None
    password_manager: object = None
    web_server: object = None


def create_services(conn_mgr) -> ServiceContainer:
    """
    Factory: create all services with real repositories.
    Called by app_bootstrap.py.
    """
    from app.domain.repositories.usage_repository import UsageRepository
    from app.domain.repositories.reservation_repository import ReservationRepository
    from app.domain.repositories.remote_session_repository import RemoteSessionRepository
    from app.domain.repositories.audit_repository import AuditRepository
    from app.domain.services.timer_service import TimerService
    from app.domain.services.reservation_service import ReservationService
    from app.domain.services.statistics_service import StatisticsService
    from app.domain.services.status_service import StatusService
    from app.domain.services.remote_monitor_service import RemoteMonitorService
    from app.domain.services.tunnel_service import TunnelService
    from app.domain.services.web_access_service import WebAccessService
    from app.presentation.web.server import WebServer
    from config import config
    from password_manager import password_manager
    import web_server as _legacy_ws

    usage_repo = UsageRepository(conn_mgr)
    reservation_repo = ReservationRepository(conn_mgr)
    remote_session_repo = RemoteSessionRepository(conn_mgr)
    audit_repo = AuditRepository(conn_mgr)

    timer_svc = TimerService(usage_repo, audit_repo)
    reservation_svc = ReservationService(reservation_repo, audit_repo)
    statistics_svc = StatisticsService(usage_repo)
    remote_monitor_svc = RemoteMonitorService()
    tunnel_svc = TunnelService()
    status_svc = StatusService(timer_svc, remote_monitor_svc, usage_repo, reservation_repo)
    web_access_svc = WebAccessService(config)

    # Create new service-based web server (replaces legacy singleton)
    web_server_instance = WebServer(config, web_access_svc, status_svc)
    _legacy_ws.set_web_server_instance(web_server_instance)

    return ServiceContainer(
        timer=timer_svc,
        reservation=reservation_svc,
        statistics=statistics_svc,
        status=status_svc,
        remote_monitor=remote_monitor_svc,
        tunnel=tunnel_svc,
        config=config,
        password_manager=password_manager,
        web_server=web_server_instance,
    )


def create_legacy_services() -> ServiceContainer:
    """
    Compatibility layer for `python timer.py` entry point.
    Creates infrastructure then delegates to the primary create_services() factory.
    TODO remove in Phase 5 when legacy entry point is retired.
    """
    from app.infrastructure.database.connection import ConnectionManager
    from app.infrastructure.database.schema import init_schema
    from app.infrastructure.database.migration import migrate_from_txt
    from app.core.paths import DB_FILE, OLD_TXT_FILE

    conn_mgr = ConnectionManager(DB_FILE)
    init_schema(conn_mgr)
    migrate_from_txt(conn_mgr, OLD_TXT_FILE)
    return create_services(conn_mgr)
