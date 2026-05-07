"""
Application bootstrap — assembles all components and starts the app.

Phase 3: creates infrastructure, repositories, services, and injects them into App.
"""
import sys
import os

_PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)


def bootstrap():
    """Initialize and run the application with proper DI."""
    from app.infrastructure.database.connection import ConnectionManager
    from app.infrastructure.database.schema import init_schema
    from app.infrastructure.database.migration import migrate_from_txt
    from app.core.paths import DB_FILE, OLD_TXT_FILE
    from app.domain.services import create_services

    # Infrastructure
    conn_mgr = ConnectionManager(DB_FILE)
    init_schema(conn_mgr)
    migrate_from_txt(conn_mgr, OLD_TXT_FILE)

    # Services (with real repositories)
    services = create_services(conn_mgr)

    # Launch app with injected services
    from app.presentation.desktop.app_window import App
    app = App(services=services)
    app.mainloop()
