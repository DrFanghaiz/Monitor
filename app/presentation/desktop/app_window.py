"""
Main application window — assembles frames, manages navigation and lifecycle.
"""
import customtkinter as ctk
from datetime import datetime

from app.presentation.desktop.frames.sidebar_frame import SidebarFrame
from app.presentation.desktop.frames.timer_frame import TimerFrame
from app.presentation.desktop.theme import COLOR_TRANSPARENT_KEY, COLOR_APPLE_BG

from logger import app_logger
from instance_lock import release_instance


class App(ctk.CTk):
    """Main application — frames are created lazily on first navigation."""

    def __init__(self, services=None):
        super().__init__()

        # ---- Service injection ----
        if services is None:
            from app.domain.services import create_legacy_services
            services = create_legacy_services()
        self._svc = services
        self.configure(fg_color=COLOR_APPLE_BG)

        self.title("公用机管理系统 Pro")
        self.geometry("1000x720")
        self.minsize(900, 600)

        if self.svc.config.get("window_always_on_top", True):
            self.attributes('-topmost', True)
        self.attributes('-alpha', 0.98)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # Only Sidebar + Timer are needed immediately
        self._history_frame = None
        self._stats_frame = None
        self._reservation_frame = None
        self._compact_frame = None
        self._settings_frame = None
        self.tray_manager = None

        self.sidebar_frame = SidebarFrame(self)
        self.timer_frame = TimerFrame(self)

        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.show_timer_frame()

        self._drag_data = {"x": 0, "y": 0}

        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Defer heavy startup to after the window renders
        self.after_idle(self._lazy_startup)

    def _lazy_startup(self):
        """Start non-critical services after window is visible."""
        from tray import TrayManager
        from backup import backup_manager

        if self.svc.config.get("minimize_to_tray", True):
            self.tray_manager = TrayManager(self)
            self.tray_manager.start()
            self.bind("<Unmap>", self.on_minimize)

        backup_manager.auto_backup_if_needed()
        app_logger.app_start()

        self.svc.remote_monitor.start()
        self.svc.web_server.start()

        self.after(500, self._start_tunnel)
        self.after(2000, self._update_status_panel)

    # ── Lazy frame factories ─────────────────────────────────────────

    @property
    def history_frame(self):
        if self._history_frame is None:
            from app.presentation.desktop.frames.history_frame import HistoryFrame
            self._history_frame = HistoryFrame(self)
        return self._history_frame

    @property
    def stats_frame(self):
        if self._stats_frame is None:
            from app.presentation.desktop.frames.statistics_frame import StatisticsFrame
            self._stats_frame = StatisticsFrame(self)
        return self._stats_frame

    @property
    def reservation_frame(self):
        if self._reservation_frame is None:
            from app.presentation.desktop.frames.reservation_frame import ReservationFrame
            self._reservation_frame = ReservationFrame(self)
        return self._reservation_frame

    @property
    def compact_frame(self):
        if self._compact_frame is None:
            from app.presentation.desktop.frames.compact_frame import CompactFrame
            self._compact_frame = CompactFrame(self)
        return self._compact_frame

    @property
    def settings_frame(self):
        if self._settings_frame is None:
            from app.presentation.desktop.frames.settings_frame import SettingsFrame
            self._settings_frame = SettingsFrame(self)
        return self._settings_frame

    @property
    def svc(self):
        return self._svc

    def on_minimize(self, event):
        if self.state() == 'iconic' and self.tray_manager:
            self.withdraw()

    def on_closing(self):
        if self.svc.timer.is_running:
            self.timer_frame.stop_timer(show_toast=False)
        if self.tray_manager:
            self.tray_manager.stop()
        self.svc.tunnel.stop()
        self.svc.web_server.stop()
        self.svc.remote_monitor.stop()
        release_instance()
        app_logger.app_exit()
        self.destroy()

    def show_timer_frame(self):
        self.hide_all_frames()
        self.timer_frame.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        self.sidebar_frame.highlight("timer")

    def show_history_frame(self):
        self.hide_all_frames()
        self.history_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.history_frame.load_data()
        self.sidebar_frame.highlight("history")

    def show_stats_frame(self):
        self.hide_all_frames()
        self.stats_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.stats_frame.load_data()
        self.sidebar_frame.highlight("stats")

    def show_reservation_frame(self):
        self.hide_all_frames()
        self.reservation_frame.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        self.reservation_frame.load_reservations()
        self.sidebar_frame.highlight("reservation")

    def show_settings_frame(self):
        self.hide_all_frames()
        self.settings_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.sidebar_frame.highlight("settings")

    def hide_all_frames(self):
        self.timer_frame.grid_forget()
        for f in (self._history_frame, self._stats_frame, self._reservation_frame,
                  self._settings_frame):
            if f is not None:
                f.grid_forget()

    def switch_to_compact_mode(self):
        self.sidebar_frame.grid_forget()
        self.hide_all_frames()
        self.minsize(0, 0)
        self.overrideredirect(True)
        self.config(bg=COLOR_TRANSPARENT_KEY)
        self.wm_attributes('-transparentcolor', COLOR_TRANSPARENT_KEY)
        self.attributes('-alpha', 1.0)

        screen_width = self.winfo_screenwidth()
        self.geometry(f"280x36+{screen_width - 300}+50")

        self.compact_frame.pack(fill="both", expand=True)
        self.compact_frame.sync_state()

        for w in [self.compact_frame, self.compact_frame.lbl_mini_timer,
                  self.compact_frame.btn_mini_stop, self.compact_frame.lbl_mini_user,
                  self.compact_frame.lbl_status]:
            if not isinstance(w, ctk.CTkButton):
                w.bind("<ButtonPress-1>", self.start_drag)
                w.bind("<B1-Motion>", self.do_drag)

    def switch_to_normal_mode(self):
        self.compact_frame.pack_forget()
        self.overrideredirect(False)
        self.wm_attributes('-transparentcolor', "")
        self.configure(fg_color=COLOR_APPLE_BG)
        self.geometry("1000x720")
        self.minsize(900, 600)
        self.attributes('-alpha', 0.98)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.timer_frame.stop_timer()
        self.show_timer_frame()

    def start_drag(self, event):
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y

    def do_drag(self, event):
        x = self.winfo_x() + event.x - self._drag_data["x"]
        y = self.winfo_y() + event.y - self._drag_data["y"]
        self.geometry(f"+{x}+{y}")

    def _start_tunnel(self):
        self.svc.tunnel.start()

    def _update_status_panel(self):
        if hasattr(self, 'sidebar_frame') and self.sidebar_frame.winfo_exists():
            self.sidebar_frame.update_status()
        self.after(3000, self._update_status_panel)

    def copy_url_to_clipboard(self):
        url = self.svc.tunnel.get_public_url()
        if url:
            self.clipboard_clear()
            self.clipboard_append(url)
            self.sidebar_frame.show_status_toast("✅ 已复制到剪贴板")
