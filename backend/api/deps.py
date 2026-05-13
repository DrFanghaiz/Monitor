"""
Dependency injection — provides service instances to route handlers.

Two modes (mutually exclusive per process):

1. DESKTOP SHARED (production / main path):
   - app_bootstrap.py or timer.py calls set_service_container(services) before API starts.
   - Desktop and API share the same TimerService / StatusService / etc.
   - This is the primary path. Both startup scripts already do this.

2. API STANDALONE (development / testing only):
   - No desktop running; API creates its own ServiceContainer lazily.
   - Only used for `uvicorn backend.api.app:app` without the desktop process.
   - Timer state in this mode is isolated from any desktop session.
"""
import sys
import os

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

_container = None


def set_service_container(container):
    """Called by bootstrap / desktop to inject the shared ServiceContainer."""
    global _container
    _container = container


def get_service_container():
    """Returns the current ServiceContainer, creating one lazily if needed."""
    global _container
    if _container is None:
        from app.domain.services import create_legacy_services
        _container = create_legacy_services()
    return _container


def get_timer_service():
    return get_service_container().timer


def get_status_service():
    return get_service_container().status


def get_statistics_service():
    return get_service_container().statistics


def get_reservation_service():
    return get_service_container().reservation


def get_config():
    return get_service_container().config


def get_password_manager():
    return get_service_container().password_manager


def get_backup_service():
    from app.domain.services.backup_service import BackupService
    return BackupService()
