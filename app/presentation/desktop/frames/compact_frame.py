"""
Compact floating capsule window shown during active timing.
"""
import customtkinter as ctk
import tkinter as tk
from app.presentation.desktop.theme import (
    COLOR_TRANSPARENT_KEY, COLOR_ACCENT_GREEN, COLOR_ACCENT_RED, COLOR_ACCENT_CYAN
)


class CompactFrame(ctk.CTkFrame):
    """胶囊模式悬浮窗"""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="#1E293B", bg_color=COLOR_TRANSPARENT_KEY,
                         corner_radius=24, border_width=1, border_color="#334155",
                         **kwargs)
        self.master = master

        left_frame = ctk.CTkFrame(self, fg_color="transparent")
        left_frame.pack(side="left", padx=(16, 0), pady=7)

        self.lbl_dot = ctk.CTkLabel(left_frame, text="●", font=("Arial", 10),
                                    text_color=COLOR_ACCENT_GREEN)
        self.lbl_dot.pack(side="left", padx=(0, 8))

        self.lbl_mini_user = ctk.CTkLabel(left_frame, text="User",
                                          font=("Segoe UI", 12, "bold"),
                                          text_color="#F1F5F9")
        self.lbl_mini_user.pack(side="left")

        sep = ctk.CTkFrame(self, fg_color="#334155", width=1, height=22)
        sep.pack(side="left", padx=14)

        self.lbl_mini_timer = ctk.CTkLabel(self, text="00:00:00",
                                           font=("Consolas", 18, "bold"),
                                           text_color=COLOR_ACCENT_CYAN)
        self.lbl_mini_timer.pack(side="left", padx=(0, 12))

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(side="right", padx=(0, 8), pady=6)

        self.btn_expand = ctk.CTkButton(
            btn_frame, text="⬜", width=28, height=28, corner_radius=14,
            fg_color="#334155", hover_color="#475569",
            text_color=COLOR_ACCENT_CYAN, font=("Arial", 10),
            command=self.expand_to_normal
        )
        self.btn_expand.pack(side="left", padx=(0, 6))

        self.btn_mini_stop = ctk.CTkButton(
            btn_frame, text="■", width=28, height=28, corner_radius=14,
            fg_color="#7F1D1D", hover_color="#DC2626",
            text_color="#FECACA", font=("Arial", 10),
            command=self.master.switch_to_normal_mode
        )
        self.btn_mini_stop.pack(side="left")

        self._tooltips = []
        self._create_tooltip(self.btn_expand, "展开窗口")
        self._create_tooltip(self.btn_mini_stop, "停止计时")

        self.lbl_status = self.lbl_dot

    def _create_tooltip(self, widget, text):
        tooltip_window = [None]

        def show_tooltip(event):
            if tooltip_window[0]:
                return
            x = widget.winfo_rootx()
            y = widget.winfo_rooty() + widget.winfo_height() + 3
            tw = tk.Toplevel(widget)
            tw.wm_overrideredirect(True)
            tw.wm_geometry(f"+{x}+{y}")
            tw.attributes('-topmost', True)
            tw.configure(bg="#1E293B")
            label = tk.Label(tw, text=text, font=("Segoe UI", 10),
                           bg="#1E293B", fg="#FFFFFF", padx=8, pady=4)
            label.pack()
            tooltip_window[0] = tw

        def hide_tooltip(event):
            if tooltip_window[0]:
                tooltip_window[0].destroy()
                tooltip_window[0] = None

        widget.bind("<Enter>", show_tooltip)
        widget.bind("<Leave>", hide_tooltip)
        self._tooltips.append((widget, show_tooltip, hide_tooltip))

    def expand_to_normal(self):
        self.pack_forget()
        self.master.overrideredirect(False)
        self.master.wm_attributes('-transparentcolor', "")
        self.master.config(bg="#F0F0F0")
        self.master.geometry("1000x720")
        self.master.minsize(900, 600)
        self.master.attributes('-alpha', 0.98)
        self.master.timer_frame.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        self.master.timer_frame.card.place_forget()
        self.master.timer_frame.card.place(relx=0, rely=0, anchor="nw", relwidth=1, relheight=1)
        self.master.timer_frame.card.configure(corner_radius=0)

    def sync_state(self):
        user = self.master.svc.timer.current_user_name
        disp = user if len(user) < 6 else user[:5] + ".."
        self.lbl_mini_user.configure(text=f"使用者: {disp}")

        remote_status = self.master.svc.remote_monitor.get_status()
        if remote_status.get("is_remote"):
            self.lbl_dot.configure(text_color=COLOR_ACCENT_RED)
        else:
            self.lbl_dot.configure(text_color=COLOR_ACCENT_GREEN)
