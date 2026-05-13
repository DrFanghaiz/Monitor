"""
Compact floating capsule window during active timing.
"""
import customtkinter as ctk
import tkinter as tk
from app.presentation.desktop.theme import (
    COLOR_TRANSPARENT_KEY, COLOR_GREEN, COLOR_RED, COLOR_CYAN, COLOR_COMPACT_BG
)


class CompactFrame(ctk.CTkFrame):
    """Capsule-style floating window — draggable, minimal."""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=COLOR_COMPACT_BG,
                         bg_color=COLOR_TRANSPARENT_KEY,
                         corner_radius=20, border_width=1, border_color="#334155",
                         **kwargs)

        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=14, pady=6)

        self.lbl_dot = ctk.CTkLabel(inner, text="●", font=("Arial", 9),
                                    text_color=COLOR_GREEN)
        self.lbl_dot.pack(side="left", padx=(0, 8))

        self.lbl_mini_user = ctk.CTkLabel(inner, text="User",
                                          font=("Microsoft YaHei UI", 11, "bold"),
                                          text_color="#F1F5F9")
        self.lbl_mini_user.pack(side="left")

        sep = ctk.CTkFrame(inner, fg_color="#334155", width=1, height=20)
        sep.pack(side="left", padx=12)

        self.lbl_mini_timer = ctk.CTkLabel(inner, text="00:00:00",
                                           font=("Consolas", 16, "bold"),
                                           text_color=COLOR_CYAN)
        self.lbl_mini_timer.pack(side="left", padx=(0, 12))

        btn_frame = ctk.CTkFrame(inner, fg_color="transparent")
        btn_frame.pack(side="right")

        self.btn_expand = ctk.CTkButton(
            btn_frame, text="⬜", width=26, height=26, corner_radius=13,
            fg_color="#334155", hover_color="#475569",
            text_color=COLOR_CYAN, font=("Arial", 10),
            command=self._expand
        )
        self.btn_expand.pack(side="left", padx=(0, 6))

        self.btn_mini_stop = ctk.CTkButton(
            btn_frame, text="■", width=26, height=26, corner_radius=13,
            fg_color="#7F1D1D", hover_color="#DC2626",
            text_color="#FECACA", font=("Arial", 10),
            command=self.master.switch_to_normal_mode
        )
        self.btn_mini_stop.pack(side="left")

        self.lbl_status = self.lbl_dot

    def sync_state(self):
        user = self.master.svc.timer.current_user_name
        disp = user if len(user) < 6 else user[:5] + ".."
        self.lbl_mini_user.configure(text=disp)

        remote = self.master.svc.remote_monitor.get_status()
        self.lbl_dot.configure(text_color=COLOR_RED if remote.get("is_remote") else COLOR_GREEN)

    def _expand(self):
        """Return to full window with timer still running."""
        self.pack_forget()
        self.master.overrideredirect(False)
        self.master.wm_attributes('-transparentcolor', "")
        self.master.configure(fg_color="#0F172A")
        self.master.geometry("1000x720")
        self.master.minsize(900, 600)
        self.master.attributes('-alpha', 1.0)
        self.master.timer_frame.grid(row=0, column=1, sticky="nsew")
