"""
Sidebar navigation frame.
Displays nav buttons, status panel, and lock state during active timing.
"""
import customtkinter as ctk
from app.presentation.desktop.theme import (
    COLOR_ACCENT_CYAN, COLOR_ACCENT_GREEN, COLOR_ACCENT_RED,
    COLOR_SIDEBAR_BG, COLOR_SIDEBAR_CARD, COLOR_SIDEBAR_NAV_TEXT,
    COLOR_SIDEBAR_NAV_HOVER, COLOR_SIDEBAR_NAV_ACTIVE
)


class SidebarFrame(ctk.CTkFrame):
    """Sidebar navigation and status surface."""

    def __init__(self, master):
        super().__init__(master, width=228, corner_radius=0, fg_color=COLOR_SIDEBAR_BG)
        self.master = master
        self.grid_rowconfigure(9, weight=1)
        self.is_locked = False

        logo_frame = ctk.CTkFrame(self, fg_color="transparent")
        logo_frame.grid(row=0, column=0, padx=20, pady=(34, 24), sticky="w")

        monogram = ctk.CTkFrame(logo_frame, fg_color="#132338", corner_radius=16, width=36, height=36)
        monogram.pack(side="left", padx=(0, 12))
        monogram.pack_propagate(False)
        ctk.CTkLabel(monogram, text="M", font=("Georgia", 18, "bold"),
                     text_color=COLOR_ACCENT_CYAN).pack(expand=True)
        title_box = ctk.CTkFrame(logo_frame, fg_color="transparent")
        title_box.pack(side="left")
        ctk.CTkLabel(title_box, text="Monitor Pro", font=("Segoe UI Semibold", 18),
                     text_color="#F7FAFC").pack(anchor="w")
        ctk.CTkLabel(title_box, text="control center", font=("Segoe UI", 10),
                     text_color="#6F8198").pack(anchor="w")

        ctk.CTkFrame(self, fg_color="#223147", height=1).grid(row=0, column=0, sticky="sew", padx=15)

        self.btn_timer = self._create_nav_btn("计时打卡", "○", 1)
        self.btn_history = self._create_nav_btn("历史记录", "◎", 2)
        self.btn_stats = self._create_nav_btn("使用统计", "◉", 3)
        self.btn_reservation = self._create_nav_btn("预约管理", "◇", 4)
        self.btn_settings = self._create_nav_btn("系统设置", "□", 5)

        self.btn_timer.configure(command=master.show_timer_frame)
        self.btn_history.configure(command=master.show_history_frame)
        self.btn_stats.configure(command=master.show_stats_frame)
        self.btn_reservation.configure(command=master.show_reservation_frame)
        self.btn_settings.configure(command=master.show_settings_frame)

        self.lock_hint = ctk.CTkLabel(
            self, text="计时进行中，导航已锁定",
            font=("Segoe UI", 12, "bold"), text_color=COLOR_ACCENT_GREEN
        )

        self.status_sep = ctk.CTkFrame(self, fg_color="#223147", height=1)
        self.status_sep.grid(row=6, column=0, sticky="sew", padx=15, pady=(10, 0))

        self.status_card = ctk.CTkFrame(
            self, fg_color=COLOR_SIDEBAR_CARD, corner_radius=16,
            border_width=1, border_color="#223147"
        )
        self.status_card.grid(row=7, column=0, padx=12, pady=(8, 0), sticky="ew")
        self.status_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self.status_card, text="Live Status", font=("Segoe UI Semibold", 11),
            text_color="#9FB2C7"
        ).pack(anchor="w", padx=12, pady=(10, 2))

        self.row_web = ctk.CTkFrame(self.status_card, fg_color="transparent", height=26)
        self.row_web.pack(fill="x", padx=12, pady=(4, 2))
        self.dot_web = ctk.CTkLabel(self.row_web, text="●", font=("Segoe UI", 10),
                                    text_color="#64748B", width=18)
        self.dot_web.pack(side="left")
        self.lbl_web = ctk.CTkLabel(self.row_web, text="Web 服务等待启动",
                                    font=("Segoe UI", 11), text_color="#94A3B8", anchor="w")
        self.lbl_web.pack(side="left", fill="x", expand=True)

        self.row_url = ctk.CTkFrame(self.status_card, fg_color="transparent", height=26)
        self.row_url.pack(fill="x", padx=12, pady=2)
        self.dot_url = ctk.CTkLabel(self.row_url, text="●", font=("Segoe UI", 10),
                                    text_color="#64748B", width=18)
        self.dot_url.pack(side="left")
        self.lbl_url = ctk.CTkLabel(self.row_url, text="公网地址等待连接",
                                    font=("Segoe UI", 10), text_color="#64748B",
                                    anchor="w", wraplength=168)
        self.lbl_url.pack(side="left", fill="x", expand=True)

        self.row_remote = ctk.CTkFrame(self.status_card, fg_color="transparent", height=26)
        self.row_remote.pack(fill="x", padx=12, pady=2)
        self.dot_remote = ctk.CTkLabel(self.row_remote, text="●", font=("Segoe UI", 10),
                                       text_color=COLOR_ACCENT_GREEN, width=18)
        self.dot_remote.pack(side="left")
        self.lbl_remote = ctk.CTkLabel(self.row_remote, text="远程控制未接入",
                                       font=("Segoe UI", 11), text_color="#94A3B8", anchor="w")
        self.lbl_remote.pack(side="left", fill="x", expand=True)

        self.btn_copy_url = ctk.CTkButton(
            self.status_card, text="复制公网地址",
            font=("Segoe UI Semibold", 10), height=30,
            fg_color="#0F172A", text_color="#9FB2C7",
            hover_color="#314762", corner_radius=10,
            command=master.copy_url_to_clipboard
        )
        self.btn_copy_url.pack(fill="x", padx=12, pady=(8, 8))

        self.status_toast = ctk.CTkLabel(self.status_card, text="",
                                         font=("Segoe UI", 9),
                                         text_color=COLOR_ACCENT_GREEN)
        self.status_toast.pack(pady=(0, 6))

    def _create_nav_btn(self, text, icon, row):
        btn = ctk.CTkButton(
            self, text=f"  {icon}   {text}",
            font=("Segoe UI Semibold", 13), anchor="w", height=46,
            fg_color="transparent", text_color=COLOR_SIDEBAR_NAV_TEXT,
            hover_color=COLOR_SIDEBAR_NAV_HOVER, corner_radius=14
        )
        btn.grid(row=row, column=0, padx=12, pady=4, sticky="ew")
        return btn

    def highlight(self, mode):
        for btn in [self.btn_timer, self.btn_history, self.btn_stats, self.btn_reservation, self.btn_settings]:
            btn.configure(fg_color="transparent", text_color=COLOR_SIDEBAR_NAV_TEXT)
        btn_map = {
            "timer": self.btn_timer, "history": self.btn_history,
            "stats": self.btn_stats, "reservation": self.btn_reservation,
            "settings": self.btn_settings
        }
        if mode in btn_map:
            btn_map[mode].configure(fg_color=COLOR_SIDEBAR_NAV_ACTIVE, text_color=COLOR_ACCENT_CYAN)

    def lock_navigation(self):
        self.is_locked = True
        for btn in [self.btn_history, self.btn_stats, self.btn_reservation, self.btn_settings]:
            btn.configure(state="disabled", text_color="#475569")
        self.status_sep.grid_remove()
        self.status_card.grid_remove()
        self.lock_hint.grid(row=7, column=0, padx=20, pady=(0, 25), sticky="s")

    def unlock_navigation(self):
        self.is_locked = False
        for btn in [self.btn_history, self.btn_stats, self.btn_reservation, self.btn_settings]:
            btn.configure(state="normal", text_color=COLOR_SIDEBAR_NAV_TEXT)
        self.lock_hint.grid_forget()
        self.status_sep.grid(row=6, column=0, sticky="sew", padx=15, pady=(10, 0))
        self.status_card.grid(row=7, column=0, padx=12, pady=(8, 0), sticky="ew")

    def update_status(self):
        try:
            port = self.master.svc.web_server.get_port()
            self.dot_web.configure(text_color=COLOR_ACCENT_GREEN)
            self.lbl_web.configure(text=f"Web 面板端口 {port}", text_color="#E2E8F0")
        except Exception:
            self.dot_web.configure(text_color="#64748B")
            self.lbl_web.configure(text="Web 服务未启动", text_color="#64748B")

        tunnel_status = self.master.svc.tunnel.get_status()
        url = tunnel_status.get("public_url")
        if url:
            display_url = url[:30] + "..." if len(url) > 30 else url
            self.dot_url.configure(text_color=COLOR_ACCENT_CYAN)
            self.lbl_url.configure(text=display_url, text_color=COLOR_ACCENT_CYAN)
            self.btn_copy_url.configure(text_color=COLOR_ACCENT_CYAN)
        elif tunnel_status.get("running"):
            self.dot_url.configure(text_color="#94A3B8")
            self.lbl_url.configure(text="公网地址连接中...", text_color="#94A3B8")
        elif tunnel_status.get("error"):
            self.dot_url.configure(text_color=COLOR_ACCENT_RED)
            self.lbl_url.configure(text=tunnel_status["error"][:28], text_color=COLOR_ACCENT_RED)
        else:
            self.dot_url.configure(text_color="#64748B")
            self.lbl_url.configure(text="公网通道未启用", text_color="#64748B")

        remote_status = self.master.svc.remote_monitor.get_status()
        if remote_status.get("is_remote"):
            self.dot_remote.configure(text_color=COLOR_ACCENT_RED)
            self.lbl_remote.configure(
                text=f"远程控制 {remote_status['remote_type']}", text_color="#EF4444"
            )
        else:
            self.dot_remote.configure(text_color=COLOR_ACCENT_GREEN)
            self.lbl_remote.configure(text="远程控制未接入", text_color="#94A3B8")

    def show_status_toast(self, msg):
        self.status_toast.configure(text=msg)
        self.master.after(3000, lambda: self.status_toast.configure(text=""))
