"""
Timer frame — login view and running timer view.
Uses grid layout for smooth resize. No fixed dimensions.
"""
import customtkinter as ctk
from PIL import ImageTk
from app.presentation.desktop.theme import (
    COLOR_BG, COLOR_CARD, COLOR_TEXT, COLOR_TEXT_SECONDARY, COLOR_TEXT_MUTED,
    COLOR_BLUE, COLOR_BLUE_HOVER, COLOR_CYAN, COLOR_RED, COLOR_RED_HOVER,
    COLOR_GREEN, COLOR_RUNNING_BG, COLOR_BORDER,
    FONT_TITLE, FONT_HEADING, FONT_BODY, FONT_SMALL, FONT_TIMER
)
from avatar import create_avatar
from logger import app_logger


class TimerFrame(ctk.CTkFrame):
    """Check-in UI — responsive, no fixed sizes."""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=COLOR_BG, corner_radius=0, **kwargs)
        self.master = master
        self._after_id = None
        self.avatar_image = None
        self.current_user_name = ""

        # Full-frame container — grid-based, fully responsive
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Login view and running view share the same grid cell
        self.view_login = ctk.CTkFrame(self, fg_color="transparent")
        self.view_running = ctk.CTkFrame(self, fg_color=COLOR_RUNNING_BG)

        self._build_login()
        self._build_running()
        self.view_login.grid(row=0, column=0, sticky="nsew")

    def _build_login(self):
        self.view_login.grid_rowconfigure(0, weight=1)
        self.view_login.grid_rowconfigure(2, weight=1)
        self.view_login.grid_columnconfigure(0, weight=1)
        self.view_login.grid_columnconfigure(2, weight=1)

        # Centered content column
        content = ctk.CTkFrame(self.view_login, fg_color="transparent")
        content.grid(row=1, column=1)

        # Toast
        self.toast = ctk.CTkFrame(content, fg_color=COLOR_GREEN, corner_radius=8, height=36)
        self.lbl_toast = ctk.CTkLabel(self.toast, text="", font=FONT_SMALL,
                                       text_color="#FFFFFF")
        self.lbl_toast.pack(padx=20, pady=6)

        # Card
        card = ctk.CTkFrame(content, fg_color=COLOR_CARD, corner_radius=16,
                            border_width=1, border_color=COLOR_BORDER)
        card.pack(pady=(0, 0))

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(padx=56, pady=40)

        ctk.CTkLabel(inner, text="开始当前使用会话",
                     font=FONT_TITLE, text_color=COLOR_TEXT).pack(pady=(0, 8))
        ctk.CTkLabel(inner, text="输入姓名后进入计时，记录自动同步到历史与统计",
                     font=FONT_BODY, text_color=COLOR_TEXT_SECONDARY).pack(pady=(0, 24))

        self.entry_user = ctk.CTkEntry(
            inner, placeholder_text="输入当前使用者姓名", width=320, height=48,
            font=("Microsoft YaHei UI", 15), fg_color="#F8F9FB",
            border_width=1, border_color=COLOR_BORDER,
            corner_radius=12, text_color=COLOR_TEXT,
            placeholder_text_color=COLOR_TEXT_MUTED
        )
        self.entry_user.pack(pady=(0, 20))

        self.btn_start = ctk.CTkButton(
            inner, text="开始计时", width=200, height=48,
            font=("Microsoft YaHei UI", 14, "bold"), corner_radius=24,
            fg_color=COLOR_BLUE, hover_color=COLOR_BLUE_HOVER,
            command=self.start_sequence
        )
        self.btn_start.pack()

        self.progress = ctk.CTkProgressBar(
            inner, width=200, height=3, corner_radius=2,
            progress_color=COLOR_CYAN, fg_color=COLOR_BORDER
        )

    def _build_running(self):
        self.view_running.grid_rowconfigure(0, weight=1)
        self.view_running.grid_columnconfigure(0, weight=1)
        self.view_running.grid_columnconfigure(2, weight=1)

        center = ctk.CTkFrame(self.view_running, fg_color="transparent")
        center.grid(row=1, column=1)

        # Status row
        status_row = ctk.CTkFrame(center, fg_color="transparent")
        status_row.pack(pady=(0, 20))
        self.status_dot = ctk.CTkLabel(status_row, text="●", font=("Arial", 10),
                                       text_color=COLOR_GREEN)
        self.status_dot.pack(side="left", padx=(0, 6))
        self.status_label = ctk.CTkLabel(status_row, text="会话进行中",
                                         font=FONT_BODY, text_color="#94A3B8")
        self.status_label.pack(side="left")

        # Avatar
        self.avatar_label = ctk.CTkLabel(center, text="", width=80, height=80)
        self.avatar_label.pack(pady=(0, 12))

        # User name
        self.lbl_user = ctk.CTkLabel(center, text="User", font=FONT_HEADING,
                                     text_color=COLOR_CYAN)
        self.lbl_user.pack(pady=(0, 8))

        # Timer
        self.lbl_timer = ctk.CTkLabel(center, text="00:00:00", font=FONT_TIMER,
                                      text_color="#F8FAFC")
        self.lbl_timer.pack(pady=20)

        self.lbl_time_hint = ctk.CTkLabel(center, text="已持续使用时长",
                                          font=FONT_BODY, text_color="#94A3B8")
        self.lbl_time_hint.pack(pady=(0, 32))

        # Buttons
        btn_row = ctk.CTkFrame(center, fg_color="transparent")
        btn_row.pack()

        self.btn_stop = ctk.CTkButton(
            btn_row, text="停止计时", width=150, height=42, corner_radius=21,
            fg_color=COLOR_RED, hover_color=COLOR_RED_HOVER,
            font=("Microsoft YaHei UI", 13, "bold"), command=self.stop_timer
        )
        self.btn_stop.pack(side="left", padx=8)

        self.btn_compact = ctk.CTkButton(
            btn_row, text="悬浮窗", width=120, height=42, corner_radius=21,
            fg_color="#334155", hover_color="#475569", text_color="#E2E8F0",
            font=("Microsoft YaHei UI", 13), command=self.master.switch_to_compact_mode
        )
        self.btn_compact.pack(side="left", padx=8)

    # ── State transitions ────────────────────────────────────────────

    def start_sequence(self):
        user = self.entry_user.get().strip()
        if not user:
            self.show_toast("请先输入姓名", COLOR_RED, "#FFFFFF")
            return
        self.current_user_name = user
        self.entry_user.configure(state="disabled")
        self.btn_start.configure(state="disabled", text="启动中...")
        self.progress.pack(pady=(12, 0))
        self._animate_progress(0)

    def _animate_progress(self, val):
        if val < 1.0:
            self.progress.set(val)
            self.after(15, lambda: self._animate_progress(val + 0.06))
        else:
            self._enter_running()

    def _enter_running(self):
        self.view_login.grid_remove()
        self.lbl_user.configure(text=self.current_user_name)
        try:
            pil_image = create_avatar(self.current_user_name, 80)
            self.avatar_image = ImageTk.PhotoImage(pil_image)
            self.avatar_label.configure(image=self.avatar_image)
        except Exception:
            pass

        self.master.svc.timer.start_timer(self.current_user_name)
        app_logger.user_login(self.current_user_name)

        self.update_timer()
        self.view_running.grid(row=0, column=0, sticky="nsew")
        self._apply_fullscreen_style()

    def _apply_fullscreen_style(self):
        self.master.sidebar_frame.grid_remove()
        self.configure(fg_color=COLOR_RUNNING_BG)

    def _restore_normal_style(self):
        self.configure(fg_color=COLOR_BG)
        self.master.sidebar_frame.grid()

    def update_timer(self):
        if self.master.svc.timer.is_running:
            state = self.master.svc.timer.get_state()
            time_str = state["elapsed_formatted"]
            self.lbl_timer.configure(text=time_str)
            if hasattr(self.master, "compact_frame") and self.master._compact_frame:
                self.master.compact_frame.lbl_mini_timer.configure(text=time_str)
            if self.master.tray_manager:
                self.master.tray_manager.update_tooltip(f"计时中 {time_str}")
            self._after_id = self.after(1000, self.update_timer)

    def stop_timer(self, show_toast=True):
        if self.master.svc.timer.is_running:
            if self._after_id is not None:
                self.after_cancel(self._after_id)
                self._after_id = None
            result = self.master.svc.timer.stop_timer()
            self.view_running.grid_remove()
            self._restore_normal_style()
            self._reset_login()
            self.view_login.grid(row=0, column=0, sticky="nsew")
            if show_toast and result:
                self.show_toast("记录已保存", COLOR_GREEN, "#FFFFFF")
                app_logger.user_logout(result["user_name"], result["duration_formatted"])

    def _reset_login(self):
        self.entry_user.configure(state="normal")
        self.entry_user.delete(0, "end")
        self.btn_start.configure(state="normal", text="开始计时")
        self.progress.pack_forget()
        self.progress.set(0)

    def show_toast(self, msg, bg, fg):
        self.lbl_toast.configure(text=msg, text_color=fg)
        self.toast.configure(fg_color=bg)
        self.toast.pack(side="top", pady=(0, 12), before=self.entry_user)
        self.after(3000, lambda: self.toast.pack_forget())
