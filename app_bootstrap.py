"""
Application bootstrap — assembles all components and starts the app.

Phase 4: supports two UI modes:
  - shell (default): pywebview / webview2 native window loading the React frontend
  - legacy: customtkinter desktop UI (timer.py)
"""
import sys
import os

_PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)


def _init_customtkinter():
    """Shared CTk initialization for legacy desktop mode.
    Called by both bootstrap(mode='legacy') and timer.py main()."""
    import customtkinter as ctk
    ctk.set_appearance_mode("Light")
    ctk.set_default_color_theme("blue")


def bootstrap(mode="legacy", dev_mode=False):
    """Initialize and run the application.

    Args:
        mode: "shell" (new React UI in native window) or "legacy" (customtkinter)
        dev_mode: If True with shell mode, load frontend from Vite dev server
    """
    from app.infrastructure.database.connection import ConnectionManager
    from app.infrastructure.database.schema import init_schema
    from app.infrastructure.database.migration import migrate_from_txt
    from app.core.paths import DB_FILE, OLD_TXT_FILE
    from app.domain.services import create_services

    # Infrastructure
    conn_mgr = ConnectionManager(DB_FILE)
    init_schema(conn_mgr)
    migrate_from_txt(conn_mgr, OLD_TXT_FILE)

    # Services (shared between desktop and API)
    services = create_services(conn_mgr)

    # Share with API layer
    from backend.api.deps import set_service_container
    set_service_container(services)

    if mode == "legacy":
        # Original customtkinter desktop
        _init_customtkinter()
        from app.presentation.desktop.app_window import App
        app = App(services=services)
        app.mainloop()
    else:
        # New React UI in native window
        from desktop.shell import launch
        launch(services=services, dev_mode=dev_mode)
