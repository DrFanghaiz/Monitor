"""
系统托盘模块
支持最小化到托盘和托盘菜单
"""
import pystray
from PIL import Image, ImageDraw
import threading


def create_tray_icon(size: int = 64) -> Image.Image:
    """创建托盘图标"""
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    # 绘制一个简单的时钟图标
    # 外圆
    padding = 4
    draw.ellipse(
        [padding, padding, size - padding, size - padding],
        fill="#007AFF",
        outline="#0062B8",
        width=2
    )

    # 时钟指针
    center = size // 2
    # 时针
    draw.line(
        [center, center, center, center - size // 4],
        fill="white",
        width=3
    )
    # 分针
    draw.line(
        [center, center, center + size // 5, center - size // 6],
        fill="white",
        width=2
    )
    # 中心点
    draw.ellipse(
        [center - 3, center - 3, center + 3, center + 3],
        fill="white"
    )

    return image


class TrayManager:
    """托盘管理器"""

    def __init__(self, app):
        self.app = app
        self.icon = None
        self._running = False

    def _create_menu(self):
        """创建托盘菜单"""
        from tunnel import tunnel_manager

        url = tunnel_manager.get_public_url()
        copy_text = "📋 复制公网地址" if url else "📋 公网地址 (未连接)"
        copy_enabled = url is not None

        return pystray.Menu(
            pystray.MenuItem("显示主窗口", self._on_show),
            pystray.MenuItem("开始计时", self._on_start_timer),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(copy_text, self._on_copy_url, enabled=copy_enabled),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("退出", self._on_quit)
        )

    def _on_show(self, icon, item):
        """显示主窗口"""
        self.app.after(0, self._show_window)

    def _show_window(self):
        """在主线程中显示窗口"""
        self.app.deiconify()
        self.app.lift()
        self.app.focus_force()

    def _on_start_timer(self, icon, item):
        """开始计时"""
        self.app.after(0, self._show_and_focus_timer)

    def _show_and_focus_timer(self):
        """显示窗口并聚焦计时器"""
        self._show_window()
        self.app.show_timer_frame()

    def _on_copy_url(self, icon, item):
        """复制公网地址"""
        self.app.after(0, self.app.copy_url_to_clipboard)

    def _on_quit(self, icon, item):
        """退出程序"""
        self.stop()
        self.app.after(0, self.app.on_closing)

    def start(self):
        """启动托盘图标"""
        if self._running:
            return

        self.icon = pystray.Icon(
            "monitor_app",
            create_tray_icon(),
            "公用机管理系统",
            menu=self._create_menu()
        )

        self._running = True
        # 在后台线程运行托盘
        self._thread = threading.Thread(target=self.icon.run, daemon=True)
        self._thread.start()

    def stop(self):
        """停止托盘图标"""
        if self.icon and self._running:
            self.icon.stop()
            self._running = False

    def update_tooltip(self, text: str):
        """更新托盘提示文字"""
        if self.icon:
            self.icon.title = text

    def show_notification(self, title: str, message: str):
        """显示托盘通知"""
        if self.icon:
            try:
                self.icon.notify(message, title)
            except Exception:
                pass  # 某些系统可能不支持通知
