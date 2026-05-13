"""
Desktop shell — starts FastAPI backend and loads React UI in a native WebView2 window.

Lifecycle matches the legacy customtkinter path:
  - remote_monitor, tunnel, web_server start/stop
  - auto backup, app start/exit logging, instance lock release

Phase 2 (active): window control bridge via per-session random token.
  - ?desktop=<uuid> marks the shell page (cannot be guessed by browsers).
  - queue.Queue + single daemon loop dispatches min/max/close actions.
  - Restore is intentionally omitted (webview2 does not report window state).
"""
import os
import sys
import queue
import threading
import time
import uuid
import tempfile

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

_running = False
_api_thread = None
_window = None
_window_actions = queue.Queue()
_desktop_token = str(uuid.uuid4())
_window_maximized = False


def _run_api(app, host="127.0.0.1", port=8000):
    import uvicorn
    uvicorn.run(app, host=host, port=port, log_level="warning")


def launch(services=None, dev_mode=False):
    global _running, _api_thread

    from backend.api.app import create_app
    from backend.api.deps import set_service_container
    from backup import backup_manager
    from instance_lock import release_instance
    from logger import app_logger

    # ---- Pre-flight ----
    if not dev_mode:
        dist_index = os.path.join(_PROJECT_ROOT, "frontend", "dist", "index.html")
        if not os.path.exists(dist_index):
            print("=" * 56)
            print("  ERROR: frontend build not found.")
            print(f"  Expected: {dist_index}")
            print()
            print("  Run:  cd frontend && npm run build")
            print("  Then retry:  python main.py")
            print()
            print("  Or use dev mode:  python main.py --dev")
            print("=" * 56)
            sys.exit(1)

    if services:
        set_service_container(services)

    # ---- FastAPI ----
    app = create_app()

    # Register window-control routes (Phase 2: min/max/close bridge)
    from backend.api.routes.window import register_window_routes
    register_window_routes(app)

    if not dev_mode:
        from fastapi.staticfiles import StaticFiles
        frontend_dist = os.path.join(_PROJECT_ROOT, "frontend", "dist")
        app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="static")

    # ---- Background services ----
    backup_manager.auto_backup_if_needed()
    app_logger.app_start()

    if services:
        services.remote_monitor.start()
        services.tunnel.start()
        services.web_server.start()

    # ---- Start API ----
    _api_thread = threading.Thread(target=_run_api, args=(app,), daemon=True)
    _api_thread.start()

    base = "http://127.0.0.1:5173" if dev_mode else "http://127.0.0.1:8000"
    url = f"{base}{'?desktop=' + _desktop_token if not dev_mode else ''}"

    if not dev_mode and not _wait_for_ready(f"{base}/api/status", timeout=12):
        print("[desktop] ERROR: API did not become ready within timeout.")
        sys.exit(1)

    _running = True
    try:
        _create_window(url, fallback_url=base)
    finally:
        print("[desktop] Shutting down...")
        if services:
            services.tunnel.stop()
            services.remote_monitor.stop()
            services.web_server.stop()
        app_logger.app_exit()
        release_instance()
        _running = False


def _wait_for_ready(health_url: str, timeout: float = 12) -> bool:
    import urllib.request
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            urllib.request.urlopen(health_url, timeout=2)
            return True
        except Exception:
            time.sleep(0.4)
    return False


def _create_window(url: str, fallback_url: str = ""):
    global _window
    try:
        from webview2 import Window
        cache_dir = _get_webview2_cache_dir()
        _window = Window(
            title="Monitor · 公用机管理系统",
            url=url,
            size="1200x800",
            cache=cache_dir,
        )
        _start_action_loop()
        import asyncio
        asyncio.run(_window.run())
    except ImportError:
        _fallback_browser(fallback_url or url)
    except Exception as exc:
        print(f"[desktop] WebView2 error: {exc}")
        _fallback_browser(fallback_url or url)


def _start_action_loop():
    """Single daemon thread that polls window actions. No recursive Timer."""
    def _loop():
        global _window_maximized
        while _running:
            if _window is not None:
                try:
                    while True:
                        action = _window_actions.get_nowait()
                        if action == "minimize":
                            _window.minimize()
                        elif action == "maximize":
                            _window.maximize()
                            _window_maximized = True
                        elif action == "close":
                            _window.close()
                        elif action == "toggle_maximize":
                            _toggle_maximize()
                        elif action == "drag":
                            _do_drag()
                except queue.Empty:
                    pass
            time.sleep(0.15)
    threading.Thread(target=_loop, daemon=True).start()


def _do_drag():
    """Get real HWND from WebView2 DLL at drag time, then initiate Win32 move."""
    try:
        from webview2.base import dll
        import ctypes
        dll.get_window.restype = ctypes.c_void_p
        hwnd = dll.get_window()
        if not hwnd:
            print("[desktop] drag failed: dll.get_window() returned 0")
            return
        import win32gui, win32con
        win32gui.ReleaseCapture()
        win32gui.SendMessage(hwnd, win32con.WM_NCLBUTTONDOWN, win32con.HTCAPTION, 0)
    except Exception as exc:
        print(f"[desktop] drag failed: {exc}")


def _toggle_maximize():
    """Toggle between maximized and restored state.
    State is tracked internally — webview2 does not report real window state.
    If the user changes state via the system (e.g. Win+Up), our flag may drift."""
    global _window_maximized
    try:
        if _window_maximized:
            _window.restore()
            _window_maximized = False
        else:
            _window.maximize()
            _window_maximized = True
    except Exception as exc:
        print(f"[desktop] toggle_maximize failed: {exc}")


def _get_webview2_cache_dir() -> str:
    candidates = []
    local_appdata = os.environ.get("LOCALAPPDATA")
    if local_appdata:
        candidates.append(os.path.join(local_appdata, "MonitorApp", "WebView2"))
    appdata = os.environ.get("APPDATA")
    if appdata:
        candidates.append(os.path.join(appdata, "MonitorApp", "WebView2"))
    candidates.append(os.path.join(tempfile.gettempdir(), "MonitorApp", "WebView2"))
    for candidate in candidates:
        try:
            os.makedirs(candidate, exist_ok=True)
            return candidate
        except OSError:
            continue
    raise RuntimeError("Unable to create a writable WebView2 cache directory.")


def _fallback_browser(url: str):
    import webbrowser
    print(f"[desktop] WebView2 not available, opening in browser: {url}")
    webbrowser.open(url)
    try:
        while _running:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
