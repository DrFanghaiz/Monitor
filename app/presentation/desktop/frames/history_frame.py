"""
History frame — displays usage records with search, edit, and delete.
"""
import customtkinter as ctk
from PIL import ImageTk
from app.presentation.desktop.theme import (
    COLOR_APPLE_BG, COLOR_CARD_WHITE, COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY,
    COLOR_ACCENT_BLUE, COLOR_ACCENT_RED, COLOR_SEPARATOR
)
from avatar import create_avatar
from logger import app_logger


class HistoryFrame(ctk.CTkFrame):
    """历史记录界面"""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=COLOR_APPLE_BG, corner_radius=0, **kwargs)
        self.master = master
        self.is_edit_mode = False
        self.row_references = []

        self.card = ctk.CTkFrame(self, fg_color=COLOR_CARD_WHITE, corner_radius=15)
        self.card.pack(fill="both", expand=True, padx=30, pady=30)

        self.toast_frame = ctk.CTkFrame(self.card, fg_color="#E8F5E9", corner_radius=10, height=35)
        self.toast_label = ctk.CTkLabel(self.toast_frame, text="",
                                        font=("Microsoft YaHei UI", 12, "bold"),
                                        text_color="#2E7D32")
        self.toast_label.pack(padx=15, pady=5)

        self.top_bar = ctk.CTkFrame(self.card, fg_color="transparent")
        self.top_bar.pack(fill="x", padx=20, pady=20)

        self.normal_top = ctk.CTkFrame(self.top_bar, fg_color="transparent")
        self.normal_top.pack(fill="x")
        ctk.CTkLabel(self.normal_top, text="历史记录", font=("Microsoft YaHei UI", 18, "bold"),
                     text_color=COLOR_TEXT_PRIMARY).pack(side="left")
        ctk.CTkButton(self.normal_top, text="✏️ 编辑", width=80, command=self.request_edit_mode,
                      fg_color=COLOR_APPLE_BG, text_color=COLOR_TEXT_PRIMARY,
                      hover_color="#E5E5EA").pack(side="right", padx=(10, 0))
        ctk.CTkButton(self.normal_top, text="刷新", width=80, command=self.load_data,
                      fg_color=COLOR_APPLE_BG, text_color=COLOR_TEXT_PRIMARY,
                      hover_color="#E5E5EA").pack(side="right")

        self.edit_top = ctk.CTkFrame(self.top_bar, fg_color="transparent")
        self.search_var = ctk.StringVar()
        self.search_var.trace("w", self.filter_data)
        self.entry_search = ctk.CTkEntry(self.edit_top, placeholder_text="🔍 筛选姓名...",
                                         textvariable=self.search_var, width=200)
        self.entry_search.pack(side="left")
        ctk.CTkButton(self.edit_top, text="完成", width=80, command=self.exit_edit_mode,
                      fg_color=COLOR_ACCENT_BLUE, hover_color="#0062B8").pack(side="right")
        ctk.CTkButton(self.edit_top, text="全选", width=80, command=self.toggle_select_all,
                      fg_color=COLOR_APPLE_BG, text_color=COLOR_TEXT_PRIMARY,
                      hover_color="#E5E5EA").pack(side="right", padx=10)

        self.scroll = ctk.CTkScrollableFrame(self.card, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=10, pady=(0, 20))

        self.bottom_bar = ctk.CTkFrame(self.card, fg_color="transparent")
        self.btn_delete_bulk = ctk.CTkButton(self.bottom_bar, text="删除选中记录",
                                             fg_color=COLOR_ACCENT_RED,
                                             hover_color="#D12F26", command=self.delete_bulk)
        self.btn_delete_bulk.pack(pady=10)

    def show_local_toast(self, msg, bg_color, text_color):
        self.toast_label.configure(text=msg, text_color=text_color)
        self.toast_frame.configure(fg_color=bg_color)
        self.toast_frame.pack(fill="x", padx=20, pady=(0, 10), before=self.top_bar)
        self.after(3000, lambda: self.toast_frame.pack_forget())

    def request_edit_mode(self):
        dialog = ctk.CTkInputDialog(text="请输入管理员密码:", title="权限验证")
        pwd = dialog.get_input()
        if pwd and self.master.svc.password_manager.check_admin_password(pwd):
            self.enter_edit_mode()
        elif pwd is not None:
            self.show_local_toast("🚫 密码错误", "#FFEBEE", "#C62828")

    def enter_edit_mode(self):
        self.is_edit_mode = True
        self.normal_top.pack_forget()
        self.edit_top.pack(fill="x")
        self.bottom_bar.pack(fill="x", side="bottom")
        self.search_var.set("")
        self.load_data()

    def exit_edit_mode(self):
        self.is_edit_mode = False
        self.edit_top.pack_forget()
        self.bottom_bar.pack_forget()
        self.normal_top.pack(fill="x")
        self.load_data()

    def filter_data(self, *args):
        self.load_data(filter_text=self.search_var.get())

    def toggle_select_all(self):
        if not self.row_references:
            return
        all_checked = all(var.get() == 1 for _, var in self.row_references)
        new_state = 0 if all_checked else 1
        for _, var in self.row_references:
            var.set(new_state)

    def delete_bulk(self):
        ids_to_delete = [rec_id for rec_id, var in self.row_references if var.get() == 1]
        if not ids_to_delete:
            self.show_local_toast("⚠️ 未选中任何记录", "#FFF3E0", "#E65100")
            return
        try:
            self.master.svc.timer.delete_records(ids_to_delete)
            self.show_local_toast(f"✅ 已删除 {len(ids_to_delete)} 条记录", "#E8F5E9", "#2E7D32")
            self.load_data(filter_text=self.search_var.get())
        except Exception as e:
            app_logger.error(f"删除失败: {e}")
            self.show_local_toast("❌ 删除失败", "#FFEBEE", "#C62828")

    def load_data(self, filter_text=""):
        for w in self.scroll.winfo_children():
            w.destroy()
        self.row_references.clear()

        records = self.master.svc.timer.get_history("all", filter_text)
        if not records:
            ctk.CTkLabel(self.scroll, text="暂无记录", text_color="gray").pack(pady=50)
            return

        self._max_duration = max((r['duration_seconds'] for r in records), default=1)
        for record in records:
            self.create_row(record)

    def create_row(self, record):
        card = ctk.CTkFrame(self.scroll, fg_color=COLOR_CARD_WHITE, corner_radius=10)
        card.pack(fill="x", pady=3, padx=5)
        card.grid_columnconfigure(1, weight=1)

        left_box = ctk.CTkFrame(card, fg_color="transparent")
        left_box.grid(row=0, column=0, padx=10, pady=(10, 6), sticky="w")

        if self.is_edit_mode:
            check_var = ctk.IntVar()
            checkbox = ctk.CTkCheckBox(left_box, text="", variable=check_var, width=24,
                                       checkbox_width=20, checkbox_height=20)
            checkbox.pack(side="left", padx=(0, 10))
            self.row_references.append((record['id'], check_var))

        try:
            pil_img = create_avatar(record['user_name'], 36)
            avatar_photo = ImageTk.PhotoImage(pil_img)
            avatar_lbl = ctk.CTkLabel(left_box, text="", image=avatar_photo, width=36, height=36)
            avatar_lbl.image = avatar_photo
            avatar_lbl.pack(side="left", padx=(0, 10))
        except Exception:
            pass

        info_box = ctk.CTkFrame(left_box, fg_color="transparent")
        info_box.pack(side="left")
        ctk.CTkLabel(info_box, text=f"{record['user_name']}",
                     font=("Microsoft YaHei UI", 14, "bold"),
                     text_color=COLOR_TEXT_PRIMARY).pack(anchor="w")

        start_time = record['start_time'][5:-3] if len(record['start_time']) > 10 else record['start_time']
        end_time = record['end_time'][5:-3] if len(record['end_time']) > 10 else record['end_time']
        ctk.CTkLabel(info_box, text=f"{start_time} ➜ {end_time}", font=("Arial", 12),
                     text_color=COLOR_TEXT_SECONDARY).pack(anchor="w")

        right_box = ctk.CTkFrame(card, fg_color="transparent")
        right_box.grid(row=0, column=2, padx=10, pady=(10, 6), sticky="e")

        h, rv = divmod(record['duration_seconds'], 3600)
        m, s = divmod(rv, 60)
        dur_text = f"{h:02}h {m:02}m"
        ctk.CTkLabel(right_box, text=f"⏱ {dur_text}", font=("Arial", 12, "bold"),
                     text_color=COLOR_ACCENT_BLUE).pack(side="right", padx=(0, 10))

        if not self.is_edit_mode:
            ctk.CTkButton(right_box, text="×", width=28, height=28,
                          fg_color="#FEE2E2", text_color="#DC2626",
                          hover_color="#FCA5A5",
                          command=lambda rid=record['id']: self.ask_delete_single(rid)).pack(side="right")

        pct = min(record['duration_seconds'] / max(self._max_duration, 1), 1.0)
        bar_height = 4
        bar_row = ctk.CTkFrame(card, fg_color=COLOR_APPLE_BG, height=bar_height, corner_radius=2)
        bar_row.grid(row=1, column=0, columnspan=3, padx=12, pady=(0, 10), sticky="ew")
        bar_row.grid_propagate(False)
        bar_row.grid_columnconfigure(0, weight=0)
        bar_row.grid_columnconfigure(1, weight=1)

        bar_width = max(int(pct * 120), 8) if pct > 0 else 6
        bar_fill = ctk.CTkFrame(bar_row, fg_color=COLOR_ACCENT_BLUE, width=bar_width,
                                height=bar_height, corner_radius=2)
        bar_fill.grid(row=0, column=0, sticky="w")

    def ask_delete_single(self, record_id):
        dialog = ctk.CTkInputDialog(text="管理员密码:", title="验证")
        pwd = dialog.get_input()
        if pwd and self.master.svc.password_manager.check_admin_password(pwd):
            try:
                self.master.svc.timer.delete_record(record_id)
                self.show_local_toast("✅ 已删除记录", "#E8F5E9", "#2E7D32")
                self.load_data()
            except Exception as e:
                app_logger.error(f"删除失败: {e}")
                self.show_local_toast("❌ 删除失败", "#FFEBEE", "#C62828")
        elif pwd is not None:
            self.show_local_toast("🚫 密码错误", "#FFEBEE", "#C62828")
