"""
配置文件管理模块
使用 JSON 格式存储应用配置
"""
import os
import json
from pathlib import Path

# 配置文件路径
CONFIG_DIR = Path(__file__).parent
CONFIG_FILE = CONFIG_DIR / "config.json"

# 默认配置
DEFAULT_CONFIG = {
    "admin_password_hash": "",  # 空表示使用默认密码
    "default_password": "123456",  # 仅当 hash 为空时使用
    "theme": "light",
    "backup_path": "./backups",
    "max_daily_hours": 0,  # 0 表示不限制
    "language": "zh-CN",
    "auto_backup": True,
    "backup_retention_days": 30,
    "window_always_on_top": True,
    "minimize_to_tray": True,
    # ===== Web 服务 =====
    "web_server_enabled": True,
    "web_server_port": 8080,
    "web_server_password": "123456",
    # ===== 远程监控 =====
    "remote_monitor_enabled": True,
    "remote_monitor_interval": 3,
    "remote_tools": [
        "SunloginClient.exe",
        "SunloginRemote.exe",
        "TeamViewer.exe",
        "AnyDesk.exe",
        "Todesk.exe",
        "ToDesk_Session.exe",
        "mstsc.exe",
    ],
    # ===== 公网隧道 =====
    "tunnel_enabled": True,
    "tunnel_mode": "cloudflared",
    "tunnel_ngrok_auth_token": "",
    "tunnel_ngrok_path": "ngrok.exe",
    "tunnel_cloudflared_path": "cloudflared.exe",
}


class Config:
    """配置管理类"""
    
    _instance = None
    _config = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load()
        return cls._instance
    
    def _load(self):
        """加载配置文件"""
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    self._config = json.load(f)
                # 合并默认配置（添加新配置项时兼容旧文件）
                for key, value in DEFAULT_CONFIG.items():
                    if key not in self._config:
                        self._config[key] = value
            except (json.JSONDecodeError, IOError) as e:
                print(f"加载配置文件失败: {e}")
                self._config = DEFAULT_CONFIG.copy()
        else:
            self._config = DEFAULT_CONFIG.copy()
            self._save()
    
    def _save(self):
        """保存配置到文件"""
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self._config, f, ensure_ascii=False, indent=2)
        except IOError as e:
            print(f"保存配置文件失败: {e}")
    
    def get(self, key: str, default=None):
        """获取配置项"""
        return self._config.get(key, default)
    
    def set(self, key: str, value):
        """设置配置项并保存"""
        self._config[key] = value
        self._save()
    
    def get_all(self) -> dict:
        """获取所有配置"""
        return self._config.copy()
    
    def reset(self):
        """重置为默认配置"""
        self._config = DEFAULT_CONFIG.copy()
        self._save()


# 全局配置实例
config = Config()
