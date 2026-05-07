"""
Reservation frame — date selector + time slot list for managing reservations.
"""
import customtkinter as ctk
from datetime import datetime, timedelta
from app.presentation.desktop.theme import (
    COLOR_APPLE_BG, COLOR_CARD_WHITE, COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY,
    COLOR_TEXT_MUTED, COLOR_ACCENT_BLUE, COLOR_ACCENT_RED, COLOR_SEPARATOR
)
from logger import app_logger


class ReservationFrame(ctk.CTkFrame):
    """预约管理界面"""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=COLOR_APPLE_BG, corner_radius=0, **kwargs)
        self.master = master
        self.selected_date = datetime.now().strftime("%Y-%m-%d")

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.setup_top_bar()
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.grid(row=1, column=0, sticky="nsew", padx=30, pady=(0, 30))
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(1, weight=2)
        self.content_frame.grid_rowconfigure(0, weight=1)

        self.setup_date_selector()
        self.setup_time_slots()
        self.load_reservations()

    def setup_top_bar(self):
        top_bar = ctk.CTkFrame(self, fg_color="transparent")
        top_bar.grid(row=0, column=0, sticky="ew", padx=30, pady=(30, 20))
        ctk.CTkLabel(top_bar, text="预约管理",
                     font=("Microsoft YaHei UI", 22, "bold"),
                     text_color=COLOR_TEXT_PRIMARY).pack(side="left")
        ctk.CTkButton(top_bar, text="+ 新建预约", width=100,
                      font=("Microsoft YaHei UI", 12, "bold"),
                      fg_color=COLOR_ACCENT_BLUE, hover_color="#0062B8",
                      command=self.show_add_dialog).pack(side="right")

    def setup_date_selector(self):
        date_card = ctk.CTkFrame(self.content_frame, fg_color=COLOR_CARD_WHITE, corner_radius=15)
        date_card.grid(row=0, column=0, sticky="nsew", padx=(0, 15))
        ctk.CTkLabel(date_card, text="选择日期",
                     font=("Microsoft YaHei UI", 14, "bold"),
                     text_color=COLOR_TEXT_PRIMARY).pack(pady=(20, 10))

        self.date_buttons = []
        today = datetime.now()
        for i in range(7):
            date = today + timedelta(days=i)
            date_str = date.strftime("%Y-%m-%d")
            weekday = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][date.weekday()]
            btn_text = f"{date.strftime('%m/%d')} {weekday}"
            if i == 0:
                btn_text = f"今天 {date.strftime('%m/%d')}"
            elif i == 1:
                btn_text = f"明天 {date.strftime('%m/%d')}"

            btn = ctk.CTkButton(
                date_card, text=btn_text, width=140, height=40,
                font=("Microsoft YaHei UI", 12),
                fg_color=COLOR_ACCENT_BLUE if i == 0 else COLOR_APPLE_BG,
                text_color="white" if i == 0 else COLOR_TEXT_PRIMARY,
                hover_color="#0062B8" if i == 0 else "#E5E5EA",
                command=lambda d=date_str, idx=i: self.select_date(d, idx)
            )
            btn.pack(pady=5, padx=20, fill="x")
            self.date_buttons.append(btn)

    def setup_time_slots(self):
        slots_card = ctk.CTkFrame(self.content_frame, fg_color=COLOR_CARD_WHITE, corner_radius=15)
        slots_card.grid(row=0, column=1, sticky="nsew", padx=(15, 0))
        header = ctk.CTkFrame(slots_card, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=15)
        self.date_label = ctk.CTkLabel(header, text=f"日期: {self.selected_date}",
                                       font=("Microsoft YaHei UI", 14, "bold"),
                                       text_color=COLOR_TEXT_PRIMARY)
        self.date_label.pack(side="left")
        ctk.CTkFrame(slots_card, fg_color=COLOR_SEPARATOR, height=1).pack(fill="x", padx=20)
        self.slots_scroll = ctk.CTkScrollableFrame(slots_card, fg_color="transparent")
        self.slots_scroll.pack(fill="both", expand=True, padx=10, pady=10)

    def select_date(self, date_str: str, btn_idx: int):
        self.selected_date = date_str
        self.date_label.configure(text=f"日期: {date_str}")
        for i, btn in enumerate(self.date_buttons):
            if i == btn_idx:
                btn.configure(fg_color=COLOR_ACCENT_BLUE, text_color="white", hover_color="#0062B8")
            else:
                btn.configure(fg_color=COLOR_APPLE_BG, text_color=COLOR_TEXT_PRIMARY, hover_color="#E5E5EA")
        self.load_reservations()

    def load_reservations(self):
        for w in self.slots_scroll.winfo_children():
            w.destroy()

        reservations = self.master.svc.reservation.get_reservations(self.selected_date)
        reserved_hours = set()
        reserved_map = {}
        for res in reservations:
            for h in range(res['start_hour'], res['end_hour']):
                reserved_hours.add(h)
                reserved_map[h] = res

        current_hour = datetime.now().hour
        today_str = datetime.now().strftime("%Y-%m-%d")
        is_today = (self.selected_date == today_str)

        for hour in range(8, 22):
            slot_frame = ctk.CTkFrame(self.slots_scroll, corner_radius=10)
            slot_frame.pack(fill="x", pady=3, padx=5)

            time_text = f"{hour:02d}:00 - {hour+1:02d}:00"
            is_past = is_today and hour < current_hour

            if hour in reserved_hours:
                res_info = reserved_map.get(hour)
                user_name = res_info['user_name'] if res_info else "已预约"
                slot_frame.configure(fg_color="#FEF2F2")
                bar = ctk.CTkFrame(slot_frame, fg_color="#EF4444", width=4, corner_radius=2)
                bar.pack(side="left", fill="y", padx=(0, 12))
                ctk.CTkLabel(slot_frame, text=time_text, font=("Arial", 12),
                             text_color="#9CA3AF").pack(side="left", padx=(0, 10), pady=12)
                ctk.CTkLabel(slot_frame, text=f"🔒 {user_name}",
                             font=("Microsoft YaHei UI", 12, "bold"),
                             text_color="#DC2626").pack(side="left", pady=12)
                if res_info:
                    ctk.CTkButton(slot_frame, text="取消", width=56, height=28,
                                  font=("Microsoft YaHei UI", 10),
                                  fg_color="#FCA5A5", text_color="#FFFFFF",
                                  hover_color="#EF4444",
                                  command=lambda rid=res_info['id']: self.cancel_reservation(rid)
                                  ).pack(side="right", padx=12, pady=8)
            elif is_past:
                slot_frame.configure(fg_color="#F8FAFC")
                bar = ctk.CTkFrame(slot_frame, fg_color="#CBD5E1", width=4, corner_radius=2)
                bar.pack(side="left", fill="y", padx=(0, 12))
                ctk.CTkLabel(slot_frame, text=time_text, font=("Arial", 12),
                             text_color="#CBD5E1").pack(side="left", padx=(0, 10), pady=12)
                ctk.CTkLabel(slot_frame, text="已过期", font=("Microsoft YaHei UI", 11),
                             text_color="#CBD5E1").pack(side="left", pady=12)
            else:
                slot_frame.configure(fg_color="#F0FDF4")
                bar = ctk.CTkFrame(slot_frame, fg_color="#22C55E", width=4, corner_radius=2)
                bar.pack(side="left", fill="y", padx=(0, 12))
                ctk.CTkLabel(slot_frame, text=time_text, font=("Arial", 12),
                             text_color="#374151").pack(side="left", padx=(0, 10), pady=12)
                ctk.CTkLabel(slot_frame, text="● 可预约", font=("Microsoft YaHei UI", 11),
                             text_color="#22C55E").pack(side="left", pady=12)

    def show_add_dialog(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("新建预约")
        dialog.geometry("350x300")
        dialog.resizable(False, False)
        dialog.transient(self.master)
        dialog.grab_set()
        dialog.update_idletasks()
        x = self.master.winfo_x() + (self.master.winfo_width() - 350) // 2
        y = self.master.winfo_y() + (self.master.winfo_height() - 300) // 2
        dialog.geometry(f"+{x}+{y}")

        frame = ctk.CTkFrame(dialog, fg_color="white")
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(frame, text="新建预约", font=("Microsoft YaHei UI", 16, "bold"),
                     text_color=COLOR_TEXT_PRIMARY).pack(pady=(0, 15))

        ctk.CTkLabel(frame, text="姓名", text_color=COLOR_TEXT_SECONDARY).pack(anchor="w")
        name_entry = ctk.CTkEntry(frame, width=280, height=35, placeholder_text="输入您的姓名")
        name_entry.pack(pady=(5, 15))

        ctk.CTkLabel(frame, text="时段", text_color=COLOR_TEXT_SECONDARY).pack(anchor="w")
        time_frame = ctk.CTkFrame(frame, fg_color="transparent")
        time_frame.pack(fill="x", pady=5)

        hours = [f"{h:02d}:00" for h in range(8, 23)]
        start_var = ctk.StringVar(value="09:00")
        end_var = ctk.StringVar(value="10:00")

        ctk.CTkLabel(time_frame, text="从").pack(side="left")
        start_menu = ctk.CTkOptionMenu(time_frame, values=hours, variable=start_var, width=100)
        start_menu.pack(side="left", padx=5)
        ctk.CTkLabel(time_frame, text="到").pack(side="left", padx=5)
        end_menu = ctk.CTkOptionMenu(time_frame, values=hours, variable=end_var, width=100)
        end_menu.pack(side="left", padx=5)

        error_label = ctk.CTkLabel(frame, text="", text_color=COLOR_ACCENT_RED,
                                   font=("Microsoft YaHei UI", 11))
        error_label.pack(pady=5)

        def submit():
            name = name_entry.get().strip()
            if not name:
                error_label.configure(text="请输入姓名")
                return
            start_hour = int(start_var.get().split(":")[0])
            end_hour = int(end_var.get().split(":")[0])
            if start_hour >= end_hour:
                error_label.configure(text="结束时间必须晚于开始时间")
                return

            svc = self.master.svc.reservation
            ok, msg, rid = svc.create_reservation(name, self.selected_date, start_hour, end_hour)
            if not ok:
                error_label.configure(text=msg)
                return
            app_logger.reservation_added(name, self.selected_date, f"{start_hour}:00-{end_hour}:00")
            dialog.destroy()
            self.load_reservations()

        ctk.CTkButton(frame, text="确认预约", width=280, height=40,
                      font=("Microsoft YaHei UI", 13, "bold"),
                      fg_color=COLOR_ACCENT_BLUE, hover_color="#0062B8",
                      command=submit).pack(pady=(10, 0))

    def cancel_reservation(self, reservation_id: int):
        self.master.svc.reservation.cancel_reservation(reservation_id)
        app_logger.reservation_cancelled(reservation_id)
        self.load_reservations()
