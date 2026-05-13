"""
History frame — usage records with search, edit, delete.
"""
import customtkinter as ctk
from PIL import ImageTk
from app.presentation.desktop.theme import (
    COLOR_BG, COLOR_CARD, COLOR_TEXT, COLOR_TEXT_SECONDARY,
    COLOR_BLUE, COLOR_RED, COLOR_RED_HOVER, COLOR_BORDER,
    FONT_HEADING, FONT_BODY, FONT_SMALL
)
from avatar import create_avatar
from logger import app_logger


class HistoryFrame(ctk.CTkFrame):
    """历史记录 — clean list with inline edit mode."""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=COLOR_BG, corner_radius=0, **kwargs)
        self.master = master
        self.is_edit_mode = False
        self.row_refs = []
        self._max_duration = 1

        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=30, pady=(30, 12))
        header.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(header, text="历史记录", font=FONT_HEADING,
                     text_color=COLOR_TEXT).grid(row=0, column=0, sticky="w")

        btn_frame = ctk.CTkFrame(header, fg_color="transparent")
        btn_frame.grid(row=0, column=2, sticky="e")

        ctk.CTkButton(btn_frame, text="编辑", width=72, height=32,
                      font=FONT_SMALL, corner_radius=8,
                      fg_color="#F1F5F9", text_color=COLOR_TEXT,
                      hover_color="#E2E8F0",
                      command=self._ask_edit).pack(side="right", padx=(6, 0))
        ctk.CTkButton(btn_frame, text="刷新", width=72, height=32,
                      font=FONT_SMALL, corner_radius=8,
                      fg_color="#F1F5F9", text_color=COLOR_TEXT,
                      hover_color="#E2E8F0",
                      command=self.load_data).pack(side="right")

        # Edit bar (hidden by default)
        self.edit_bar = ctk.CTkFrame(self, fg_color="transparent")
        self.edit_bar.grid_columnconfigure(1, weight=1)
        self.search_var = ctk.StringVar()
        self.search_var.trace("w", self._filter)
        self.entry_search = ctk.CTkEntry(
            self.edit_bar, placeholder_text="筛选姓名...",
            textvariable=self.search_var, width=180, height=32,
            font=FONT_SMALL
        )
        self.entry_search.grid(row=0, column=0, padx=(30, 10))

        ctk.CTkButton(self.edit_bar, text="全选", width=64, height=32,
                      font=FONT_SMALL, corner_radius=8,
                      fg_color="#F1F5F9", text_color=COLOR_TEXT,
                      hover_color="#E2E8F0",
                      command=self._toggle_all).grid(row=0, column=1, sticky="w")
        ctk.CTkButton(self.edit_bar, text="完成", width=64, height=32,
                      font=FONT_SMALL, corner_radius=8,
                      fg_color=COLOR_BLUE, text_color="#FFFFFF",
                      hover_color="#2563EB",
                      command=self._exit_edit).grid(row=0, column=2, padx=(0, 30))

        # Toast
        self.toast_frame = ctk.CTkFrame(self, fg_color="#ECFDF5", corner_radius=8, height=30)
        self.toast_label = ctk.CTkLabel(self.toast_frame, text="",
                                        font=FONT_SMALL, text_color="#065F46")
        self.toast_label.pack(padx=16, pady=4)

        # Scrollable list
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.grid(row=2, column=0, sticky="nsew", padx=30, pady=(0, 30))

        # Delete bar (shown in edit mode)
        self.delete_bar = ctk.CTkFrame(self, fg_color="transparent")
        ctk.CTkButton(self.delete_bar, text="删除选中记录", width=140, height=36,
                      font=FONT_SMALL, corner_radius=8,
                      fg_color=COLOR_RED, hover_color=COLOR_RED_HOVER,
                      command=self._delete_selected).pack(pady=8)

    # ── Toast ────────────────────────────────────────────────────────

    def _toast(self, msg, ok=True):
        bg = "#ECFDF5" if ok else "#FEF2F2"
        fg = "#065F46" if ok else "#991B1B"
        self.toast_label.configure(text=msg, text_color=fg)
        self.toast_frame.configure(fg_color=bg)
        self.toast_frame.grid(row=1, column=0, padx=30, pady=(0, 8))
        self.after(3000, self.toast_frame.grid_remove)

    # ── Edit mode ────────────────────────────────────────────────────

    def _ask_edit(self):
        dlg = ctk.CTkInputDialog(text="请输入管理员密码:", title="权限验证")
        pwd = dlg.get_input()
        if pwd and self.master.svc.password_manager.check_admin_password(pwd):
            self._enter_edit()
        elif pwd is not None:
            self._toast("密码错误", ok=False)

    def _enter_edit(self):
        self.is_edit_mode = True
        self.edit_bar.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        self.delete_bar.grid(row=3, column=0, pady=(0, 16))
        self.search_var.set("")
        self.load_data()

    def _exit_edit(self):
        self.is_edit_mode = False
        self.edit_bar.grid_remove()
        self.delete_bar.grid_remove()
        self.load_data()

    def _filter(self, *args):
        self.load_data(filter_text=self.search_var.get())

    def _toggle_all(self):
        if not self.row_refs:
            return
        all_on = all(v.get() == 1 for _, v in self.row_refs)
        new = 0 if all_on else 1
        for _, v in self.row_refs:
            v.set(new)

    def _delete_selected(self):
        ids = [rid for rid, v in self.row_refs if v.get() == 1]
        if not ids:
            self._toast("未选中任何记录", ok=False)
            return
        try:
            self.master.svc.timer.delete_records(ids)
            self._toast(f"已删除 {len(ids)} 条记录")
            self.load_data(filter_text=self.search_var.get())
        except Exception as e:
            app_logger.error(f"删除失败: {e}")
            self._toast("删除失败", ok=False)

    # ── Data loading ─────────────────────────────────────────────────

    def load_data(self, filter_text=""):
        for w in self.scroll.winfo_children():
            w.destroy()
        self.row_refs.clear()

        records = self.master.svc.timer.get_history("all", filter_text)
        if not records:
            ctk.CTkLabel(self.scroll, text="暂无记录", font=FONT_BODY,
                         text_color=COLOR_TEXT_SECONDARY).pack(pady=40)
            return

        self._max_duration = max((r['duration_seconds'] for r in records), default=1)
        for r in records:
            self._build_row(r)

    def _build_row(self, record):
        row = ctk.CTkFrame(self.scroll, fg_color=COLOR_CARD, corner_radius=8)
        row.pack(fill="x", pady=2, padx=2)
        row.grid_columnconfigure(1, weight=1)

        # Left: checkbox (edit) + avatar + info
        left = ctk.CTkFrame(row, fg_color="transparent")
        left.grid(row=0, column=0, padx=12, pady=(10, 6), sticky="w")

        if self.is_edit_mode:
            cv = ctk.IntVar()
            cb = ctk.CTkCheckBox(left, text="", variable=cv, width=20,
                                 checkbox_width=18, checkbox_height=18)
            cb.pack(side="left", padx=(0, 10))
            self.row_refs.append((record['id'], cv))

        try:
            pil = create_avatar(record['user_name'], 32)
            photo = ImageTk.PhotoImage(pil)
            al = ctk.CTkLabel(left, text="", image=photo, width=32, height=32)
            al.image = photo
            al.pack(side="left", padx=(0, 10))
        except Exception:
            pass

        info = ctk.CTkFrame(left, fg_color="transparent")
        info.pack(side="left")
        ctk.CTkLabel(info, text=record['user_name'],
                     font=("Microsoft YaHei UI", 13, "bold"),
                     text_color=COLOR_TEXT).pack(anchor="w")

        st = record['start_time']
        et = record['end_time']
        if len(st) > 10:
            st = st[5:-3]
        if len(et) > 10:
            et = et[5:-3]
        ctk.CTkLabel(info, text=f"{st} → {et}",
                     font=("Segoe UI", 11), text_color=COLOR_TEXT_SECONDARY).pack(anchor="w")

        # Right: duration + delete
        right = ctk.CTkFrame(row, fg_color="transparent")
        right.grid(row=0, column=2, padx=12, pady=(10, 6), sticky="e")

        h, rv = divmod(record['duration_seconds'], 3600)
        m, s = divmod(rv, 60)
        ctk.CTkLabel(right, text=f"{h:02}h {m:02}m",
                     font=("Segoe UI", 12, "bold"),
                     text_color=COLOR_BLUE).pack(side="right", padx=(0, 8))

        if not self.is_edit_mode:
            ctk.CTkButton(right, text="×", width=24, height=24,
                          corner_radius=12,
                          fg_color="#FEE2E2", text_color="#DC2626",
                          hover_color="#FCA5A5",
                          command=lambda rid=record['id']: self._delete_one(rid)
                          ).pack(side="right")

        # Duration bar
        pct = min(record['duration_seconds'] / max(self._max_duration, 1), 1.0)
        bar = ctk.CTkFrame(row, fg_color="#F1F5F9", height=3, corner_radius=2)
        bar.grid(row=1, column=0, columnspan=3, padx=12, pady=(0, 10), sticky="ew")
        bar.grid_propagate(False)

        fill_w = max(int(pct * 100), 4) if pct > 0 else 4
        ctk.CTkFrame(bar, fg_color=COLOR_BLUE, width=fill_w,
                     height=3, corner_radius=2).place(x=0, y=0)

    def _delete_one(self, record_id):
        dlg = ctk.CTkInputDialog(text="管理员密码:", title="验证")
        pwd = dlg.get_input()
        if pwd and self.master.svc.password_manager.check_admin_password(pwd):
            try:
                self.master.svc.timer.delete_record(record_id)
                self._toast("已删除记录")
                self.load_data()
            except Exception as e:
                app_logger.error(f"删除失败: {e}")
                self._toast("删除失败", ok=False)
        elif pwd is not None:
            self._toast("密码错误", ok=False)
