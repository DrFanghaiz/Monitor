"""
公用机管理系统 Pro — 主入口

启动方式:
  python main.py              → customtkinter 桌面 (默认, 无需额外依赖)
  python main.py --shell       → React UI (需要 WebView2 运行时)
  python main.py --dev         → 开发模式 (load from Vite dev server)
"""
import sys
import os

# DPI awareness (required by customtkinter)
import ctypes
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

_PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)


if __name__ == "__main__":
    args = sys.argv[1:]
    mode = "legacy"
    dev = False

    if "--shell" in args:
        mode = "shell"
    if "--dev" in args:
        dev = True

    # Single-instance lock (applies to all modes)
    from instance_lock import check_single_instance
    if not check_single_instance():
        import tkinter.messagebox as mb
        mb.showerror("Error", "程序已在运行中，请勿重复启动！")
        sys.exit(1)

    from app_bootstrap import bootstrap
    bootstrap(mode=mode, dev_mode=dev)
