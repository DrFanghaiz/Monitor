"""
Timer frame: login view and fullscreen running view.
Timer state is read from TimerService (single source of truth).
"""
import customtkinter as ctk
from PIL import ImageTk
from app.presentation.desktop.theme import (
    COLOR_APPLE_BG, COLOR_CARD_WHITE, COLOR_TEXT_PRIMARY, COLOR_TEXT_MUTED,
    COLOR_ACCENT_BLUE, COLOR_ACCENT_CYAN, COLOR_ACCENT_RED, COLOR_ACCENT_GREEN,
    COLOR_RUNNING_BG, COLOR_CARD_ALT, COLOR_BORDER_SOFT,
    FONT_NORMAL, FONT_TIMER, FONT_TIMER_LABEL
)
from avatar import create_avatar
from logger import app_logger


class TimerFrame(ctk.CTkFrame):
    """Check-in UI driven by TimerService."""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=COLOR_APPLE_BG, corner_radius=0, **kwargs)
        self.master = master
        self._after_id = None
        self.avatar_image = None
        self.current_user_name = ""

        self.card = ctk.CTkFrame(
            self, fg_color=COLOR_CARD_WHITE, corner_radius=28, width=540, height=460,
            border_width=1, border_color=COLOR_BORDER_SOFT
        )
        self.card.place(relx=0.5, rely=0.5, anchor="center")
        self.card.grid_propagate(False)

        self.view_login = ctk.CTkFrame(self.card, fg_color="transparent")
        self.view_running = ctk.CTkFrame(self.card, fg_color=COLOR_RUNNING_BG)

        self.setup_login_ui()
        self.setup_running_ui()
        self.view_login.place(relx=0.5, rely=0.5, anchor="center", relwidth=1, relheight=1)

    def setup_login_ui(self):
        box = ctk.CTkFrame(self.view_login, fg_color="transparent")
        box.place(relx=0.5, rely=0.5, anchor="center")

        self.toast = ctk.CTkFrame(box, fg_color="#0D9488", corner_radius=22, height=42)
        self.lbl_toast = ctk.CTkLabel(
            self.toast, text="", font=("Segoe UI", 13, "bold"), text_color="#FFFFFF"
        )
        self.lbl_toast.pack(padx=24, pady=8)

        badge = ctk.CTkFrame(box, fg_color=COLOR_CARD_ALT, corner_radius=18)
        badge.pack(pady=(0, 18))
        ctk.CTkLabel(
            badge, text="  LIVE SESSION  ", font=("Segoe UI", 11, "bold"),
            text_color=COLOR_ACCENT_CYAN
        ).pack(padx=10, pady=6)

        ctk.CTkLabel(box, text="✦", font=("Georgia", 42), text_color=COLOR_ACCENT_BLUE).pack(pady=(0, 6))
        ctk.CTkLabel(
            box, text="开始当前使用会话", font=("Segoe UI", 30, "bold"),
            text_color=COLOR_TEXT_PRIMARY
        ).pack(pady=(4, 6))
        ctk.CTkLabel(
            box, text="输入姓名后进入专注计时，记录会自动同步到历史与统计。",
            font=("Segoe UI", 13), text_color=COLOR_TEXT_MUTED
        ).pack(pady=(0, 26))

        self.entry_user = ctk.CTkEntry(
            box, placeholder_text="输入当前使用者姓名", width=336, height=56,
            font=("Segoe UI", 16), fg_color=COLOR_CARD_ALT,
            border_width=1, border_color=COLOR_BORDER_SOFT,
            corner_radius=18, text_color=COLOR_TEXT_PRIMARY,
            placeholder_text_color=COLOR_TEXT_MUTED
        )
        self.entry_user.pack(pady=12)

        self.btn_start = ctk.CTkButton(
            box, text="开始计时", width=220, height=54,
            font=("Segoe UI", 15, "bold"), corner_radius=27,
            fg_color=COLOR_ACCENT_BLUE, hover_color="#245BC3",
            command=self.start_sequence
        )
        self.btn_start.pack(pady=20)

        self.progress = ctk.CTkProgressBar(
            box, width=280, height=4, corner_radius=2,
            progress_color=COLOR_ACCENT_CYAN, fg_color="#E2E8F0"
        )

    def setup_running_ui(self):
        self.view_running.configure(fg_color=COLOR_RUNNING_BG)

        center_box = ctk.CTkFrame(self.view_running, fg_color="transparent")
        center_box.place(relx=0.5, rely=0.5, anchor="center")

        status_row = ctk.CTkFrame(center_box, fg_color="transparent")
        status_row.pack(pady=(0, 28))

        self.status_dot = ctk.CTkLabel(status_row, text="●", font=("Arial", 12),
                                       text_color=COLOR_ACCENT_GREEN)
        self.status_dot.pack(side="left", padx=(0, 8))

        self.status_label = ctk.CTkLabel(
            status_row, text="当前会话进行中", font=FONT_NORMAL, text_color="#8EA0B4"
        )
        self.status_label.pack(side="left")

        self.avatar_label = ctk.CTkLabel(center_box, text="", width=100, height=100)
        self.avatar_label.pack(pady=(0, 16))

        self.lbl_user = ctk.CTkLabel(
            center_box, text="User", font=("Segoe UI", 20, "bold"), text_color=COLOR_ACCENT_CYAN
        )
        self.lbl_user.pack(pady=(0, 10))

        self.lbl_timer = ctk.CTkLabel(center_box, text="00:00:00", font=FONT_TIMER, text_color="#F8FAFC")
        self.lbl_timer.pack(pady=30)

        self.lbl_time_hint = ctk.CTkLabel(
            center_box, text="已持续使用时长", font=FONT_TIMER_LABEL, text_color="#8EA0B4"
        )
        self.lbl_time_hint.pack(pady=(0, 40))

        btn_box = ctk.CTkFrame(center_box, fg_color="transparent")
        btn_box.pack()

        self.btn_stop = ctk.CTkButton(
            btn_box, text="停止计时", width=160, height=50, corner_radius=25,
            fg_color=COLOR_ACCENT_RED, hover_color="#D65554",
            font=("Segoe UI", 14, "bold"), command=self.stop_timer
        )
        self.btn_stop.pack(side="left", padx=12)

        self.btn_compact = ctk.CTkButton(
            btn_box, text="悬浮窗", width=140, height=50, corner_radius=25,
            fg_color="#243246", hover_color="#32445E", text_color="#E2E8F0",
            font=("Segoe UI", 14, "bold"), command=self.master.switch_to_compact_mode
        )
        self.btn_compact.pack(side="left", padx=12)

    def start_sequence(self):
        user = self.entry_user.get().strip()
        if not user:
            self.show_toast("请先输入姓名", "#FFEBEE", "#C62828")
            return
        self.current_user_name = user
        self.entry_user.configure(state="disabled")
        self.btn_start.configure(state="disabled", text="正在启动...")
        self.progress.pack(pady=10)
        self.loading_val = 0
        self.animate()

    def animate(self):
        if self.loading_val < 1.05:
            self.loading_val += 0.05
            self.progress.set(self.loading_val)
            self.after(20, self.animate)
        else:
            self.view_login.place_forget()
            self.lbl_user.configure(text=self.current_user_name)

            try:
                pil_image = create_avatar(self.current_user_name, 100)
                self.avatar_image = ImageTk.PhotoImage(pil_image)
                self.avatar_label.configure(image=self.avatar_image)
            except Exception:
                pass

            self.master.svc.timer.start_timer(self.current_user_name)
            app_logger.user_login(self.current_user_name)

            self.update_timer()
            self.view_running.place(relx=0.5, rely=0.5, anchor="center", relwidth=1, relheight=1)
            self.transition_to_fullscreen()

    def transition_to_fullscreen(self):
        self.master.sidebar_frame.grid_forget()
        self.configure(fg_color=COLOR_RUNNING_BG)
        self.card.configure(fg_color=COLOR_RUNNING_BG, border_width=0, border_color=COLOR_RUNNING_BG)
        self.card.place_forget()
        self.card.place(relx=0, rely=0, anchor="nw", relwidth=1, relheight=1)
        self.card.configure(corner_radius=0)

    def update_timer(self):
        if self.master.svc.timer.is_running:
            state = self.master.svc.timer.get_state()
            time_str = state["elapsed_formatted"]
            self.lbl_timer.configure(text=time_str)
            if hasattr(self.master, "compact_frame"):
                self.master.compact_frame.lbl_mini_timer.configure(text=time_str)
            if hasattr(self.master, "tray_manager") and self.master.tray_manager:
                self.master.tray_manager.update_tooltip(f"计时中 {time_str}")
            self._after_id = self.after(1000, self.update_timer)

    def stop_timer(self, show_toast=True):
        if self.master.svc.timer.is_running:
            if self._after_id is not None:
                self.after_cancel(self._after_id)
                self._after_id = None
            result = self.master.svc.timer.stop_timer()
            self.view_running.place_forget()
            self.reset_login()
            self.view_login.place(relx=0.5, rely=0.5, anchor="center", relwidth=1, relheight=1)
            self.transition_from_fullscreen()
            if show_toast and result:
                self.show_toast("记录已保存", "#E8F5E9", "#2E7D32")
                app_logger.user_logout(result["user_name"], result["duration_formatted"])

    def transition_from_fullscreen(self):
        self.card.place_forget()
        self.card.configure(
            width=540, height=460, corner_radius=28, fg_color=COLOR_CARD_WHITE,
            border_width=1, border_color=COLOR_BORDER_SOFT
        )
        self.card.place(relx=0.5, rely=0.5, anchor="center")
        self.configure(fg_color=COLOR_APPLE_BG)
        self.master.sidebar_frame.grid(row=0, column=0, sticky="nsew")

    def reset_login(self):
        self.entry_user.configure(state="normal")
        self.entry_user.delete(0, "end")
        self.btn_start.configure(state="normal", text="开始计时")
        self.progress.pack_forget()
        self.progress.set(0)

    def show_toast(self, msg, bg, fg):
        self.lbl_toast.configure(text=msg, text_color=fg)
        self.toast.configure(fg_color=bg)
        self.toast.pack(side="top", pady=(10, 0), before=self.entry_user)
        self.after(3000, lambda: self.toast.pack_forget())
