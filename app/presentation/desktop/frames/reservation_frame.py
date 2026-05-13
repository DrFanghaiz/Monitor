"""
Reservation frame — date selector + time slot list.
"""
import customtkinter as ctk
from datetime import datetime, timedelta
from app.presentation.desktop.theme import (
    COLOR_BG, COLOR_CARD, COLOR_TEXT, COLOR_TEXT_SECONDARY, COLOR_TEXT_MUTED,
    COLOR_BLUE, COLOR_BLUE_HOVER, COLOR_RED, COLOR_BORDER,
    FONT_HEADING, FONT_BODY, FONT_SMALL
)
from logger import app_logger


class ReservationFrame(ctk.CTkFrame):
    """预约管理"""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=COLOR_BG, corner_radius=0, **kwargs)
        self.master = master
        self.selected_date = datetime.now().strftime("%Y-%m-%d")

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=30, pady=(30, 16))
        ctk.CTkLabel(header, text="预约管理", font=FONT_HEADING,
                     text_color=COLOR_TEXT).pack(side="left")
        ctk.CTkButton(header, text="+ 新建预约", width=100, height=34,
                      font=FONT_SMALL, corner_radius=8,
                      fg_color=COLOR_BLUE, hover_color=COLOR_BLUE_HOVER,
                      command=self._show_add_dialog).pack(side="right")

        # Content: date selector | time slots
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.grid(row=1, column=0, sticky="nsew", padx=30, pady=(0, 30))
        content.grid_columnconfigure(0, weight=1)
        content.grid_columnconfigure(1, weight=3)
        content.grid_rowconfigure(0, weight=1)

        # Date selector
        date_card = ctk.CTkFrame(content, fg_color=COLOR_CARD, corner_radius=12,
                                 border_width=1, border_color=COLOR_BORDER)
        date_card.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        ctk.CTkLabel(date_card, text="选择日期", font=FONT_BODY,
                     text_color=COLOR_TEXT).pack(pady=(16, 8))

        self.date_btns = []
        today = datetime.now()
        for i in range(7):
            d = today + timedelta(days=i)
            ds = d.strftime("%Y-%m-%d")
            if i == 0:
                label = f"今天 {d.strftime('%m/%d')}"
            elif i == 1:
                label = f"明天 {d.strftime('%m/%d')}"
            else:
                wd = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][d.weekday()]
                label = f"{d.strftime('%m/%d')} {wd}"

            is_active = (i == 0)
            btn = ctk.CTkButton(
                date_card, text=label, height=36, font=FONT_SMALL, corner_radius=8,
                fg_color=COLOR_BLUE if is_active else "#F1F5F9",
                text_color="#FFFFFF" if is_active else COLOR_TEXT,
                hover_color=COLOR_BLUE_HOVER if is_active else "#E2E8F0",
                command=lambda ds=ds, idx=i: self._select_date(ds, idx)
            )
            btn.pack(fill="x", padx=14, pady=3)
            self.date_btns.append(btn)

        # Slots
        slot_card = ctk.CTkFrame(content, fg_color=COLOR_CARD, corner_radius=12,
                                 border_width=1, border_color=COLOR_BORDER)
        slot_card.grid(row=0, column=1, sticky="nsew", padx=(12, 0))
        slot_card.grid_rowconfigure(1, weight=1)
        slot_card.grid_columnconfigure(0, weight=1)

        slot_header = ctk.CTkFrame(slot_card, fg_color="transparent")
        slot_header.grid(row=0, column=0, sticky="ew", padx=18, pady=14)
        self.date_label = ctk.CTkLabel(slot_header, text=f"日期: {self.selected_date}",
                                       font=FONT_BODY, text_color=COLOR_TEXT)
        self.date_label.pack(side="left")

        ctk.CTkFrame(slot_card, fg_color=COLOR_BORDER, height=1).grid(
            row=0, column=0, sticky="sew", padx=18)

        self.slots_scroll = ctk.CTkScrollableFrame(slot_card, fg_color="transparent")
        self.slots_scroll.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)

        self.load_reservations()

    def _select_date(self, ds, idx):
        self.selected_date = ds
        self.date_label.configure(text=f"日期: {ds}")
        for i, b in enumerate(self.date_btns):
            if i == idx:
                b.configure(fg_color=COLOR_BLUE, text_color="#FFFFFF",
                           hover_color=COLOR_BLUE_HOVER)
            else:
                b.configure(fg_color="#F1F5F9", text_color=COLOR_TEXT,
                           hover_color="#E2E8F0")
        self.load_reservations()

    def load_reservations(self):
        for w in self.slots_scroll.winfo_children():
            w.destroy()

        reservations = self.master.svc.reservation.get_reservations(self.selected_date)
        reserved = set()
        rmap = {}
        for r in reservations:
            for h in range(r['start_hour'], r['end_hour']):
                reserved.add(h)
                rmap[h] = r

        now_h = datetime.now().hour
        is_today = (self.selected_date == datetime.now().strftime("%Y-%m-%d"))

        for hour in range(8, 22):
            row = ctk.CTkFrame(self.slots_scroll, corner_radius=8)
            row.pack(fill="x", pady=2, padx=2)

            time_str = f"{hour:02d}:00 — {hour+1:02d}:00"
            is_past = is_today and hour < now_h

            if hour in reserved:
                ri = rmap.get(hour)
                name = ri['user_name'] if ri else "已预约"
                row.configure(fg_color="#FEF2F2")
                bar = ctk.CTkFrame(row, fg_color="#EF4444", width=3, corner_radius=2)
                bar.pack(side="left", fill="y", padx=(0, 10))
                ctk.CTkLabel(row, text=time_str, font=("Segoe UI", 11),
                            text_color="#9CA3AF").pack(side="left", padx=(0, 8), pady=10)
                ctk.CTkLabel(row, text=f"已预约 · {name}",
                            font=("Microsoft YaHei UI", 12, "bold"),
                            text_color="#DC2626").pack(side="left", pady=10)
                if ri:
                    ctk.CTkButton(row, text="取消", width=52, height=26,
                                  font=FONT_SMALL, corner_radius=6,
                                  fg_color="#FCA5A5", hover_color="#EF4444",
                                  text_color="#FFFFFF",
                                  command=lambda rid=ri['id']: self._cancel(rid)
                                  ).pack(side="right", padx=10, pady=6)
            elif is_past:
                row.configure(fg_color="#F8FAFC")
                ctk.CTkFrame(row, fg_color="#CBD5E1", width=3,
                            corner_radius=2).pack(side="left", fill="y", padx=(0, 10))
                ctk.CTkLabel(row, text=time_str, font=("Segoe UI", 11),
                            text_color="#CBD5E1").pack(side="left", padx=(0, 8), pady=10)
                ctk.CTkLabel(row, text="已过期", font=FONT_SMALL,
                            text_color="#CBD5E1").pack(side="left", pady=10)
            else:
                row.configure(fg_color="#F0FDF4")
                ctk.CTkFrame(row, fg_color="#22C55E", width=3,
                            corner_radius=2).pack(side="left", fill="y", padx=(0, 10))
                ctk.CTkLabel(row, text=time_str, font=("Segoe UI", 11),
                            text_color="#374151").pack(side="left", padx=(0, 8), pady=10)
                ctk.CTkLabel(row, text="可预约", font=FONT_SMALL,
                            text_color="#22C55E").pack(side="left", pady=10)

    def _cancel(self, rid):
        self.master.svc.reservation.cancel_reservation(rid)
        app_logger.reservation_cancelled(rid)
        self.load_reservations()

    def _show_add_dialog(self):
        dlg = ctk.CTkToplevel(self)
        dlg.title("新建预约")
        dlg.geometry("340x300")
        dlg.resizable(False, False)
        dlg.transient(self.master)
        dlg.grab_set()

        frame = ctk.CTkFrame(dlg, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=24, pady=24)

        ctk.CTkLabel(frame, text="新建预约", font=FONT_HEADING,
                     text_color=COLOR_TEXT).pack(pady=(0, 16))

        ctk.CTkLabel(frame, text="姓名", font=FONT_SMALL,
                     text_color=COLOR_TEXT_SECONDARY).pack(anchor="w")
        name_entry = ctk.CTkEntry(frame, width=280, height=36,
                                  font=FONT_BODY, placeholder_text="输入姓名")
        name_entry.pack(pady=(4, 14))

        ctk.CTkLabel(frame, text="时段", font=FONT_SMALL,
                     text_color=COLOR_TEXT_SECONDARY).pack(anchor="w")
        tf = ctk.CTkFrame(frame, fg_color="transparent")
        tf.pack(fill="x", pady=(4, 0))

        hours = [f"{h:02d}:00" for h in range(8, 23)]
        sv = ctk.StringVar(value="09:00")
        ev = ctk.StringVar(value="10:00")

        ctk.CTkLabel(tf, text="从", font=FONT_SMALL).pack(side="left")
        ctk.CTkOptionMenu(tf, values=hours, variable=sv, width=90,
                          font=FONT_SMALL).pack(side="left", padx=4)
        ctk.CTkLabel(tf, text="到", font=FONT_SMALL).pack(side="left", padx=4)
        ctk.CTkOptionMenu(tf, values=hours, variable=ev, width=90,
                          font=FONT_SMALL).pack(side="left")

        err = ctk.CTkLabel(frame, text="", font=FONT_SMALL, text_color=COLOR_RED)
        err.pack(pady=(8, 0))

        def submit():
            name = name_entry.get().strip()
            if not name:
                err.configure(text="请输入姓名"); return
            sh = int(sv.get().split(":")[0])
            eh = int(ev.get().split(":")[0])
            if sh >= eh:
                err.configure(text="结束时间必须晚于开始时间"); return
            ok, msg, rid = self.master.svc.reservation.create_reservation(
                name, self.selected_date, sh, eh)
            if not ok:
                err.configure(text=msg); return
            app_logger.reservation_added(name, self.selected_date, f"{sh}:00-{eh}:00")
            dlg.destroy()
            self.load_reservations()

        ctk.CTkButton(frame, text="确认预约", width=280, height=38,
                      font=("Microsoft YaHei UI", 13, "bold"), corner_radius=8,
                      fg_color=COLOR_BLUE, hover_color=COLOR_BLUE_HOVER,
                      command=submit).pack(pady=(16, 0))
