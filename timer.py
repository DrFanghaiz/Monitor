"""
公用机管理系统 Pro - 兼容入口
TODO Phase 5: retire this file; use main.py exclusively.
"""
import ctypes
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

import customtkinter as ctk
ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("blue")

from app.presentation.desktop.app_window import App
from instance_lock import check_single_instance, release_instance


def main():
    if not check_single_instance():
        import tkinter.messagebox as mb
        mb.showerror("错误", "程序已在运行中，请勿重复启动！")
        return

    try:
        app = App()
        app.mainloop()
    finally:
        release_instance()


if __name__ == "__main__":
    main()
