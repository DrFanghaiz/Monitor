"""
公网隧道管理模块
支持 Cloudflare Tunnel (cloudflared) 和 ngrok
将本地 Web 服务暴露到公网
"""
import subprocess
import threading
import re
import time
import shutil
from pathlib import Path
from config import config
from logger import app_logger


class TunnelManager:
    """公网隧道管理器（单例）"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance

    def _init(self):
        self._process = None
        self._public_url = None
        self._running = False
        self._thread = None
        self._error_message = None

    def start(self):
        """启动隧道"""
        if self._running:
            return
        if not config.get("tunnel_enabled", True):
            return

        mode = config.get("tunnel_mode", "cloudflared")
        self._running = True
        self._thread = threading.Thread(
            target=self._start_tunnel, args=(mode,), daemon=True
        )
        self._thread.start()

    def stop(self):
        """停止隧道"""
        self._running = False
        if self._process:
            try:
                self._process.terminate()
                time.sleep(0.5)
                if self._process.poll() is None:
                    self._process.kill()
            except Exception:
                pass
            self._process = None
        app_logger.info("隧道已停止")

    def get_public_url(self) -> str:
        """获取公网访问地址"""
        if self._public_url:
            # 确保使用 https
            url = self._public_url.strip()
            if not url.startswith("http"):
                url = "https://" + url
            return url
        return None

    def get_status(self) -> dict:
        """获取隧道状态"""
        return {
            "running": self._running and self._process is not None and self._process.poll() is None,
            "public_url": self.get_public_url(),
            "mode": config.get("tunnel_mode", "cloudflared"),
            "error": self._error_message
        }

    def _start_tunnel(self, mode):
        """启动隧道"""
        if mode == "cloudflared":
            self._start_cloudflared()
        elif mode == "ngrok":
            self._start_ngrok()
        else:
            app_logger.error(f"未知隧道模式: {mode}")
            self._running = False

    def _start_cloudflared(self):
        """启动 Cloudflare Tunnel"""
        port = config.get("web_server_port", 8080)
        exe_path = config.get("tunnel_cloudflared_path", "cloudflared.exe")

        # 查找 cloudflared 可执行文件
        cloudflared = shutil.which(exe_path)
        if not cloudflared:
            # 尝试程序目录下的 cloudflared.exe
            local_path = Path(__file__).parent / exe_path
            if local_path.exists():
                cloudflared = str(local_path)

        if not cloudflared:
            self._error_message = f"未找到 {exe_path}，请下载放置到程序目录"
            app_logger.error(self._error_message)
            self._running = False
            return

        cmd = [
            cloudflared, "tunnel",
            "--url", f"http://localhost:{port}",
            "--no-autoupdate"
        ]

        app_logger.info(f"启动 Cloudflare Tunnel: {' '.join(cmd)}")

        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                startupinfo=startupinfo,
                encoding="utf-8",
                errors="replace"
            )

            # 解析输出获取公网 URL
            url_pattern = re.compile(r'https://[\w-]+\.trycloudflare\.com')
            for line in iter(self._process.stdout.readline, ""):
                if not self._running:
                    break
                match = url_pattern.search(line)
                if match:
                    url = match.group(0)
                    if url != self._public_url:
                        self._public_url = url
                        app_logger.info(f"公网地址: {url}")
                time.sleep(0.1)

        except FileNotFoundError:
            self._error_message = f"无法启动 {cloudflared}，请确认文件存在"
            app_logger.error(self._error_message)
        except Exception as e:
            self._error_message = f"隧道启动失败: {e}"
            app_logger.error(self._error_message)

        self._running = False

    def _start_ngrok(self):
        """启动 ngrok 隧道（备用方案）"""
        port = config.get("web_server_port", 8080)
        auth_token = config.get("tunnel_ngrok_auth_token", "")
        exe_path = config.get("tunnel_ngrok_path", "ngrok.exe")

        ngrok = shutil.which(exe_path)
        if not ngrok:
            local_path = Path(__file__).parent / exe_path
            if local_path.exists():
                ngrok = str(local_path)

        if not ngrok:
            self._error_message = "未找到 ngrok.exe，请下载放置到程序目录"
            app_logger.error(self._error_message)
            self._running = False
            return

        cmd = [ngrok, "http", str(port), "--log=stdout", "--log-format=json"]
        if auth_token:
            cmd.extend(["--authtoken", auth_token])

        app_logger.info(f"启动 ngrok 隧道: ngrok http {port}")

        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                startupinfo=startupinfo,
                encoding="utf-8",
                errors="replace"
            )

            url_pattern = re.compile(r'url=([^\\s]+)')

            for line in iter(self._process.stdout.readline, ""):
                if not self._running:
                    break
                match = url_pattern.search(line)
                if match:
                    url = match.group(1)
                    if url != self._public_url:
                        self._public_url = url
                        app_logger.info(f"公网地址: {url}")
                time.sleep(0.1)

        except FileNotFoundError:
            self._error_message = "无法启动 ngrok.exe"
            app_logger.error(self._error_message)
        except Exception as e:
            self._error_message = f"ngrok 启动失败: {e}"
            app_logger.error(self._error_message)

        self._running = False


# 全局隧道管理器实例
tunnel_manager = TunnelManager()
