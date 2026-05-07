"""
远程控制检测模块
通过检测目标进程判断电脑是否正在被远程控制（向日葵、RDP、TeamViewer等）
"""
import subprocess
import threading
import time
from datetime import datetime
from config import config
from database import db
from logger import app_logger

# 远程工具关键字映射（tasklist 返回的映像名 -> 可读名称）
PROCESS_NAME_MAP = {
    "SunloginClient.exe": "向日葵",
    "SunloginRemote.exe": "向日葵",
    "mstsc.exe": "Windows远程桌面",
    "TeamViewer.exe": "TeamViewer",
    "TeamViewer_Service.exe": "TeamViewer",
    "AnyDesk.exe": "AnyDesk",
    "Todesk.exe": "ToDesk",
    "ToDesk_Session.exe": "ToDesk",
}


class RemoteMonitor:
    """远程控制检测器（单例，后台线程运行）"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance

    def _init(self):
        self._running = False
        self._thread = None
        self._current_session_id = None
        self._current_remote_type = None
        self._remote_start_time = None

    def start(self):
        """启动监控"""
        if self._running:
            return
        if not config.get("remote_monitor_enabled", True):
            return

        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        app_logger.info("远程控制监控已启动")

    def stop(self):
        """停止监控"""
        self._running = False
        if self._current_session_id:
            self._end_current_session()
        app_logger.info("远程控制监控已停止")

    def get_status(self) -> dict:
        """获取当前远程控制状态"""
        if not self._current_remote_type:
            return {
                "is_remote": False,
                "remote_type": None,
                "start_time": None,
                "elapsed_seconds": 0,
                "elapsed_formatted": "00:00:00"
            }

        elapsed = int((datetime.now() - self._remote_start_time).total_seconds())
        h, r = divmod(elapsed, 3600)
        m, s = divmod(r, 60)

        return {
            "is_remote": True,
            "remote_type": self._current_remote_type,
            "start_time": self._remote_start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "elapsed_seconds": elapsed,
            "elapsed_formatted": f"{h:02}:{m:02}:{s:02}"
        }

    def _check_processes(self) -> str:
        """检测目标进程，返回第一个匹配的进程名"""
        target_tools = config.get("remote_tools", [
            "SunloginClient.exe",
            "SunloginRemote.exe",
            "TeamViewer.exe",
            "TeamViewer_Service.exe",
            "AnyDesk.exe",
            "Todesk.exe",
            "ToDesk_Session.exe",
            "mstsc.exe",
        ])

        try:
            # 运行 tasklist 获取进程列表
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            result = subprocess.run(
                ["tasklist", "/FO", "CSV", "/NH"],
                capture_output=True,
                text=True,
                timeout=5,
                startupinfo=startupinfo
            )

            for line in result.stdout.splitlines():
                line = line.strip()
                if not line:
                    continue
                # tasklist CSV 格式: "映像名称","PID","会话名","会话#","内存使用"
                parts = line.replace('"', '').split(',')
                if len(parts) >= 1:
                    process_name = parts[0].strip()
                    for tool in target_tools:
                        if process_name.lower() == tool.lower():
                            return tool

        except subprocess.TimeoutExpired:
            pass
        except Exception as e:
            app_logger.error(f"进程检测异常: {e}")

        return None

    def _monitor_loop(self):
        """监控循环"""
        interval = config.get("remote_monitor_interval", 3)

        while self._running:
            try:
                detected = self._check_processes()

                if detected:
                    readable_name = PROCESS_NAME_MAP.get(detected, detected)
                    if self._current_session_id is None:
                        # 远程控制刚开始
                        self._current_remote_type = readable_name
                        self._remote_start_time = datetime.now()
                        self._current_session_id = db.add_remote_session(readable_name)
                        app_logger.info(f"检测到远程控制: {readable_name}")
                else:
                    if self._current_session_id is not None:
                        # 远程控制已结束
                        self._end_current_session()
                        app_logger.info("远程控制已断开")

            except Exception as e:
                app_logger.error(f"监控循环异常: {e}")

            time.sleep(interval)

    def _end_current_session(self):
        """结束当前远程会话"""
        if self._current_session_id:
            db.end_remote_session(self._current_session_id)
            self._current_session_id = None
            self._current_remote_type = None
            self._remote_start_time = None


# 全局远程监控实例
remote_monitor = RemoteMonitor()
