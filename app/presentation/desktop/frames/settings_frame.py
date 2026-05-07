"""
Settings frame — password management, data backup, web service config.
"""
import customtkinter as ctk
from app.presentation.desktop.theme import (
    COLOR_APPLE_BG, COLOR_CARD_WHITE, COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY,
    COLOR_ACCENT_BLUE, COLOR_ACCENT_RED, COLOR_SEPARATOR
)
from backup import backup_manager
from logger import app_logger


class SettingsFrame(ctk.CTkFrame):
    """设置界面"""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=COLOR_APPLE_BG, corner_radius=0, **kwargs)
        self.master = master

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        main_card = ctk.CTkFrame(self, fg_color=COLOR_CARD_WHITE, corner_radius=15)
        main_card.grid(row=0, column=0, sticky="nsew", padx=30, pady=30)

        ctk.CTkLabel(main_card, text="系统设置", font=("Microsoft YaHei UI", 22, "bold"),
                     text_color=COLOR_TEXT_PRIMARY).pack(anchor="w", padx=30, pady=(30, 20))

        settings_container = ctk.CTkFrame(main_card, fg_color="transparent")
        settings_container.pack(fill="both", expand=True, padx=30, pady=(0, 30))

        self._create_section(settings_container, "🔐 密码管理", [
            ("修改管理员密码", self.change_password),
        ])

        self._create_section(settings_container, "💾 数据管理", [
            ("立即备份", self.create_backup),
            ("查看备份列表", self.show_backups),
        ])

        self._create_section(settings_container, "🌐 Web 服务", [
            ("修改 Web 访问密码", self.change_web_password),
        ])

        info_frame = ctk.CTkFrame(settings_container, fg_color=COLOR_APPLE_BG, corner_radius=10)
        info_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(info_frame, text="ℹ️ 系统信息", font=("Microsoft YaHei UI", 14, "bold"),
                     text_color=COLOR_TEXT_PRIMARY).pack(anchor="w", padx=15, pady=(10, 5))
        port = self.master.svc.config.get("web_server_port", 8080)
        tunnel_mode = self.master.svc.config.get("tunnel_mode", "cloudflared")
        ctk.CTkLabel(info_frame,
                     text=f"版本: 2.1.0  |  Web端口: {port}  |  隧道: {tunnel_mode}  |  最后备份: {self._get_last_backup()}",
                     font=("Microsoft YaHei UI", 11), text_color=COLOR_TEXT_SECONDARY
                     ).pack(anchor="w", padx=15, pady=(0, 10))

    def _create_section(self, parent, title, buttons):
        frame = ctk.CTkFrame(parent, fg_color=COLOR_APPLE_BG, corner_radius=10)
        frame.pack(fill="x", pady=10)
        ctk.CTkLabel(frame, text=title, font=("Microsoft YaHei UI", 14, "bold"),
                     text_color=COLOR_TEXT_PRIMARY).pack(anchor="w", padx=15, pady=(10, 5))
        for btn_text, btn_cmd in buttons:
            ctk.CTkButton(frame, text=btn_text, width=200, height=35,
                         fg_color=COLOR_CARD_WHITE, text_color=COLOR_TEXT_PRIMARY,
                         hover_color="#E5E5EA", border_width=1, border_color=COLOR_SEPARATOR,
                         command=btn_cmd).pack(anchor="w", padx=15, pady=5)

    def _get_last_backup(self):
        backups = backup_manager.get_backup_list()
        if backups:
            return backups[0]['created']
        return "无"

    def change_password(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("修改密码")
        dialog.geometry("350x280")
        dialog.resizable(False, False)
        dialog.transient(self.master)
        dialog.grab_set()

        frame = ctk.CTkFrame(dialog, fg_color="white")
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(frame, text="修改管理员密码", font=("Microsoft YaHei UI", 16, "bold")).pack(pady=(0, 15))

        ctk.CTkLabel(frame, text="当前密码", text_color=COLOR_TEXT_SECONDARY).pack(anchor="w")
        old_pwd = ctk.CTkEntry(frame, width=280, height=35, show="*")
        old_pwd.pack(pady=(5, 10))

        ctk.CTkLabel(frame, text="新密码", text_color=COLOR_TEXT_SECONDARY).pack(anchor="w")
        new_pwd = ctk.CTkEntry(frame, width=280, height=35, show="*")
        new_pwd.pack(pady=(5, 10))

        error_label = ctk.CTkLabel(frame, text="", text_color=COLOR_ACCENT_RED)
        error_label.pack(pady=5)

        def submit():
            pwd_mgr = self.master.svc.password_manager
            if pwd_mgr.change_admin_password(old_pwd.get(), new_pwd.get()):
                app_logger.password_changed()
                dialog.destroy()
            else:
                error_label.configure(text="当前密码错误")

        ctk.CTkButton(frame, text="确认修改", width=280, height=40,
                     fg_color=COLOR_ACCENT_BLUE, command=submit).pack(pady=(10, 0))

    def create_backup(self):
        try:
            path = backup_manager.create_backup(manual=True)
            ctk.CTkInputDialog(text=f"备份已保存到:\n{path}", title="备份成功")
        except Exception as e:
            ctk.CTkInputDialog(text=f"备份失败: {e}", title="错误")

    def show_backups(self):
        backups = backup_manager.get_backup_list()
        if not backups:
            ctk.CTkInputDialog(text="暂无备份文件", title="备份列表")
            return
        info = "\n".join([f"  {b['name']} ({b['created']})" for b in backups[:10]])
        ctk.CTkInputDialog(text=f"最近10个备份:\n{info}", title="备份列表")

    def change_web_password(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("修改 Web 密码")
        dialog.geometry("350x250")
        dialog.resizable(False, False)
        dialog.transient(self.master)
        dialog.grab_set()

        frame = ctk.CTkFrame(dialog, fg_color="white")
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(frame, text="修改 Web 访问密码", font=("Microsoft YaHei UI", 16, "bold")).pack(pady=(0, 15))

        ctk.CTkLabel(frame, text="新密码", text_color=COLOR_TEXT_SECONDARY).pack(anchor="w")
        new_pwd = ctk.CTkEntry(frame, width=280, height=35, show="*")
        new_pwd.pack(pady=(5, 10))

        error_label = ctk.CTkLabel(frame, text="", text_color=COLOR_ACCENT_RED)
        error_label.pack(pady=5)

        def submit():
            pwd = new_pwd.get().strip()
            if not pwd:
                error_label.configure(text="密码不能为空")
                return
            self.master.svc.config.set("web_server_password", pwd)
            app_logger.info("Web 访问密码已修改")
            dialog.destroy()

        ctk.CTkButton(frame, text="确认修改", width=280, height=40,
                     fg_color=COLOR_ACCENT_BLUE, command=submit).pack(pady=(10, 0))
