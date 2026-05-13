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

from app.presentation.desktop.app_window import App
from instance_lock import check_single_instance, release_instance


def main():
    if not check_single_instance():
        import tkinter.messagebox as mb
        mb.showerror("错误", "程序已在运行中，请勿重复启动！")
        return

    try:
        from app_bootstrap import _init_customtkinter
        from app.domain.services import create_legacy_services
        from backend.api.deps import set_service_container
        _init_customtkinter()
        services = create_legacy_services()
        set_service_container(services)
        app = App(services=services)
        app.mainloop()
    finally:
        release_instance()


if __name__ == "__main__":
    main()
