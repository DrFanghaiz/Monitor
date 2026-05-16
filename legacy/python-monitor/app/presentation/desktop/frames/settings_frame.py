"""
Settings frame — password, backup, web config.
"""
import customtkinter as ctk
from app.presentation.desktop.theme import (
    COLOR_BG, COLOR_CARD, COLOR_TEXT, COLOR_TEXT_SECONDARY,
    COLOR_BLUE, COLOR_BLUE_HOVER, COLOR_BORDER,
    FONT_HEADING, FONT_BODY, FONT_SMALL
)
from backup import backup_manager
from logger import app_logger


class SettingsFrame(ctk.CTkFrame):
    """系统设置"""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=COLOR_BG, corner_radius=0, **kwargs)
        self.master = master

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        card = ctk.CTkFrame(self, fg_color=COLOR_CARD, corner_radius=12,
                            border_width=1, border_color=COLOR_BORDER)
        card.grid(row=0, column=0, sticky="nsew", padx=30, pady=30)

        ctk.CTkLabel(card, text="系统设置", font=FONT_HEADING,
                     text_color=COLOR_TEXT).pack(anchor="w", padx=28, pady=(24, 16))

        container = ctk.CTkFrame(card, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=28, pady=(0, 24))

        self._section(container, "密码管理", [
            ("修改管理员密码", self._change_password),
        ])
        self._section(container, "数据管理", [
            ("立即备份", self._create_backup),
            ("查看备份列表", self._show_backups),
        ])
        self._section(container, "Web 服务", [
            ("修改 Web 访问密码", self._change_web_password),
        ])

        # Info
        info = ctk.CTkFrame(container, fg_color="#F8F9FB", corner_radius=8)
        info.pack(fill="x", pady=(8, 0))
        port = self.master.svc.config.get("web_server_port", 8080)
        tunnel = self.master.svc.config.get("tunnel_mode", "cloudflared")
        last = self._last_backup()
        ctk.CTkLabel(info, text=f"版本 2.1  ·  端口 {port}  ·  隧道 {tunnel}  ·  最后备份 {last}",
                     font=FONT_SMALL, text_color=COLOR_TEXT_SECONDARY
                     ).pack(anchor="w", padx=14, pady=10)

    def _section(self, parent, title, buttons):
        frame = ctk.CTkFrame(parent, fg_color="#F8F9FB", corner_radius=8)
        frame.pack(fill="x", pady=4)
        ctk.CTkLabel(frame, text=title, font=("Microsoft YaHei UI", 13, "bold"),
                     text_color=COLOR_TEXT).pack(anchor="w", padx=14, pady=(10, 4))
        for text, cmd in buttons:
            ctk.CTkButton(frame, text=text, width=180, height=32,
                         font=FONT_SMALL, corner_radius=6,
                         fg_color=COLOR_CARD, text_color=COLOR_TEXT,
                         hover_color="#E2E8F0", border_width=1,
                         border_color=COLOR_BORDER,
                         command=cmd).pack(anchor="w", padx=14, pady=3)

    def _last_backup(self):
        backups = backup_manager.get_backup_list()
        return backups[0]['created'] if backups else "无"

    def _change_password(self):
        dlg = ctk.CTkToplevel(self)
        dlg.title("修改密码")
        dlg.geometry("340x260")
        dlg.resizable(False, False)
        dlg.transient(self.master)
        dlg.grab_set()

        frame = ctk.CTkFrame(dlg, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=24, pady=24)

        ctk.CTkLabel(frame, text="修改管理员密码", font=FONT_HEADING).pack(pady=(0, 14))

        ctk.CTkLabel(frame, text="当前密码", font=FONT_SMALL,
                     text_color=COLOR_TEXT_SECONDARY).pack(anchor="w")
        old = ctk.CTkEntry(frame, width=280, height=34, show="*", font=FONT_BODY)
        old.pack(pady=(4, 10))

        ctk.CTkLabel(frame, text="新密码", font=FONT_SMALL,
                     text_color=COLOR_TEXT_SECONDARY).pack(anchor="w")
        new = ctk.CTkEntry(frame, width=280, height=34, show="*", font=FONT_BODY)
        new.pack(pady=(4, 10))

        err = ctk.CTkLabel(frame, text="", font=FONT_SMALL, text_color="#DC2626")
        err.pack(pady=4)

        def submit():
            if self.master.svc.password_manager.change_admin_password(old.get(), new.get()):
                app_logger.password_changed()
                dlg.destroy()
            else:
                err.configure(text="当前密码错误")

        ctk.CTkButton(frame, text="确认修改", width=280, height=36,
                      font=("Microsoft YaHei UI", 13, "bold"), corner_radius=8,
                      fg_color=COLOR_BLUE, hover_color=COLOR_BLUE_HOVER,
                      command=submit).pack(pady=(6, 0))

    def _create_backup(self):
        try:
            path = backup_manager.create_backup(manual=True)
            ctk.CTkInputDialog(text=f"备份已保存到:\n{path}", title="备份成功")
        except Exception as e:
            ctk.CTkInputDialog(text=f"备份失败: {e}", title="错误")

    def _show_backups(self):
        backups = backup_manager.get_backup_list()
        if not backups:
            ctk.CTkInputDialog(text="暂无备份文件", title="备份列表")
            return
        info = "\n".join(f"  {b['name']} ({b['created']})" for b in backups[:10])
        ctk.CTkInputDialog(text=f"最近10个备份:\n{info}", title="备份列表")

    def _change_web_password(self):
        dlg = ctk.CTkToplevel(self)
        dlg.title("修改 Web 密码")
        dlg.geometry("340x220")
        dlg.resizable(False, False)
        dlg.transient(self.master)
        dlg.grab_set()

        frame = ctk.CTkFrame(dlg, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=24, pady=24)

        ctk.CTkLabel(frame, text="修改 Web 访问密码", font=FONT_HEADING).pack(pady=(0, 14))

        ctk.CTkLabel(frame, text="新密码", font=FONT_SMALL,
                     text_color=COLOR_TEXT_SECONDARY).pack(anchor="w")
        new = ctk.CTkEntry(frame, width=280, height=34, show="*", font=FONT_BODY)
        new.pack(pady=(4, 10))

        err = ctk.CTkLabel(frame, text="", font=FONT_SMALL, text_color="#DC2626")
        err.pack(pady=4)

        def submit():
            pwd = new.get().strip()
            if not pwd:
                err.configure(text="密码不能为空"); return
            self.master.svc.config.set("web_server_password", pwd)
            app_logger.info("Web 访问密码已修改")
            dlg.destroy()

        ctk.CTkButton(frame, text="确认修改", width=280, height=36,
                      font=("Microsoft YaHei UI", 13, "bold"), corner_radius=8,
                      fg_color=COLOR_BLUE, hover_color=COLOR_BLUE_HOVER,
                      command=submit).pack(pady=(6, 0))
