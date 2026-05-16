"""
Sidebar — navigation and live status panel.
"""
import customtkinter as ctk
from app.presentation.desktop.theme import (
    COLOR_CYAN, COLOR_GREEN, COLOR_RED,
    COLOR_SIDEBAR_BG, COLOR_SIDEBAR_NAV, COLOR_SIDEBAR_NAV_HOVER,
    COLOR_SIDEBAR_NAV_ACTIVE, COLOR_SIDEBAR_ACCENT
)


class SidebarFrame(ctk.CTkFrame):
    """Navigation sidebar with live status indicators."""

    def __init__(self, master):
        super().__init__(master, width=220, corner_radius=0, fg_color=COLOR_SIDEBAR_BG)
        self.master = master
        self.is_locked = False

        # Brand
        brand = ctk.CTkFrame(self, fg_color="transparent")
        brand.grid(row=0, column=0, padx=18, pady=(30, 20), sticky="w")
        ctk.CTkLabel(brand, text="Monitor", font=("Segoe UI", 18, "bold"),
                     text_color="#F1F5F9").pack(side="left")
        ctk.CTkLabel(brand, text="Pro", font=("Segoe UI", 11),
                     text_color="#64748B").pack(side="left", padx=(6, 0))

        # Nav buttons
        self.btn_timer = self._nav_btn("计时打卡", 1)
        self.btn_history = self._nav_btn("历史记录", 2)
        self.btn_stats = self._nav_btn("使用统计", 3)
        self.btn_reservation = self._nav_btn("预约管理", 4)
        self.btn_settings = self._nav_btn("系统设置", 5)

        self.btn_timer.configure(command=master.show_timer_frame)
        self.btn_history.configure(command=master.show_history_frame)
        self.btn_stats.configure(command=master.show_stats_frame)
        self.btn_reservation.configure(command=master.show_reservation_frame)
        self.btn_settings.configure(command=master.show_settings_frame)

        # Spacer
        self.grid_rowconfigure(9, weight=1)

        # Lock hint (shown during active timing)
        self.lock_hint = ctk.CTkLabel(
            self, text="计时中 · 导航已锁定",
            font=("Microsoft YaHei UI", 11, "bold"), text_color=COLOR_GREEN
        )

        # Status card
        self.status_card = ctk.CTkFrame(self, fg_color="#1F2937", corner_radius=12)
        self.status_card.grid(row=10, column=0, padx=12, pady=(0, 16), sticky="ew")

        self._status_rows = {}

        def add_status_row(key, label):
            row = ctk.CTkFrame(self.status_card, fg_color="transparent", height=22)
            row.pack(fill="x", padx=12, pady=3)
            dot = ctk.CTkLabel(row, text="●", font=("Arial", 8), width=16,
                              text_color="#64748B")
            dot.pack(side="left")
            lbl = ctk.CTkLabel(row, text=label, font=("Microsoft YaHei UI", 10),
                              text_color="#94A3B8", anchor="w")
            lbl.pack(side="left", fill="x", expand=True)
            self._status_rows[key] = (dot, lbl)

        add_status_row("web", "Web 等待启动")
        add_status_row("url", "公网未连接")
        add_status_row("remote", "远程未接入")

        self.btn_copy_url = ctk.CTkButton(
            self.status_card, text="复制公网地址",
            font=("Microsoft YaHei UI", 10), height=28,
            fg_color="#0F172A", text_color="#94A3B8",
            hover_color="#1E293B", corner_radius=8,
            command=master.copy_url_to_clipboard
        )
        self.btn_copy_url.pack(fill="x", padx=12, pady=(6, 10))

        self.status_toast = ctk.CTkLabel(self.status_card, text="",
                                         font=("Microsoft YaHei UI", 9),
                                         text_color=COLOR_GREEN)
        self.status_toast.pack(pady=(0, 6))

    def _nav_btn(self, text, row):
        btn = ctk.CTkButton(
            self, text=text,
            font=("Microsoft YaHei UI", 12), anchor="w", height=40,
            fg_color="transparent", text_color=COLOR_SIDEBAR_NAV,
            hover_color=COLOR_SIDEBAR_NAV_HOVER, corner_radius=10
        )
        btn.grid(row=row, column=0, padx=10, pady=2, sticky="ew")
        return btn

    def highlight(self, mode):
        mapping = {
            "timer": self.btn_timer, "history": self.btn_history,
            "stats": self.btn_stats, "reservation": self.btn_reservation,
            "settings": self.btn_settings
        }
        for btn in [self.btn_timer, self.btn_history, self.btn_stats,
                     self.btn_reservation, self.btn_settings]:
            btn.configure(fg_color="transparent", text_color=COLOR_SIDEBAR_NAV)
        if mode in mapping:
            mapping[mode].configure(fg_color=COLOR_SIDEBAR_NAV_ACTIVE,
                                    text_color=COLOR_SIDEBAR_ACCENT)

    def lock_navigation(self):
        self.is_locked = True
        for btn in [self.btn_history, self.btn_stats, self.btn_reservation, self.btn_settings]:
            btn.configure(state="disabled", text_color="#475569")
        self.status_card.grid_remove()
        self.lock_hint.grid(row=9, column=0, padx=16, pady=(0, 20), sticky="s")

    def unlock_navigation(self):
        self.is_locked = False
        for btn in [self.btn_history, self.btn_stats, self.btn_reservation, self.btn_settings]:
            btn.configure(state="normal", text_color=COLOR_SIDEBAR_NAV)
        self.lock_hint.grid_forget()
        self.status_card.grid()

    def update_status(self):
        try:
            port = self.master.svc.web_server.get_port()
            self._set_status("web", COLOR_GREEN, f"Web 端口 {port}", "#E2E8F0")
        except Exception:
            self._set_status("web", "#64748B", "Web 未启动", "#64748B")

        ts = self.master.svc.tunnel.get_status()
        url = ts.get("public_url")
        if url:
            text = url[:28] + "..." if len(url) > 28 else url
            self._set_status("url", COLOR_CYAN, text, COLOR_CYAN)
            self.btn_copy_url.configure(text_color=COLOR_CYAN)
        elif ts.get("running"):
            self._set_status("url", "#94A3B8", "连接中...", "#94A3B8")
        elif ts.get("error"):
            self._set_status("url", COLOR_RED, ts["error"][:24], COLOR_RED)
        else:
            self._set_status("url", "#64748B", "公网未启用", "#64748B")

        rs = self.master.svc.remote_monitor.get_status()
        if rs.get("is_remote"):
            self._set_status("remote", COLOR_RED, f"远程 {rs['remote_type']}", "#EF4444")
        else:
            self._set_status("remote", COLOR_GREEN, "远程未接入", "#94A3B8")

    def _set_status(self, key, dot_color, text, text_color):
        if key in self._status_rows:
            dot, lbl = self._status_rows[key]
            dot.configure(text_color=dot_color)
            lbl.configure(text=text, text_color=text_color)

    def show_status_toast(self, msg):
        self.status_toast.configure(text=msg)
        self.master.after(3000, lambda: self.status_toast.configure(text=""))
