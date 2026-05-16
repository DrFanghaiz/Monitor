"""
日志系统模块
记录应用操作日志
"""
import logging
import os
from datetime import datetime
from pathlib import Path
from logging.handlers import RotatingFileHandler

# 日志目录
LOG_DIR = Path(__file__).parent
LOG_FILE = LOG_DIR / "app.log"

# 创建 logger
logger = logging.getLogger("MonitorApp")
logger.setLevel(logging.DEBUG)

# 文件处理器（最大 5MB，保留 3 个备份）
file_handler = RotatingFileHandler(
    LOG_FILE,
    maxBytes=5 * 1024 * 1024,
    backupCount=3,
    encoding="utf-8"
)
file_handler.setLevel(logging.INFO)

# 控制台处理器（调试用）
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

# 日志格式
formatter = logging.Formatter(
    "%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# 添加处理器
if not logger.handlers:
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)


class AppLogger:
    """应用日志类"""
    
    @staticmethod
    def info(message: str):
        """记录一般信息"""
        logger.info(message)
    
    @staticmethod
    def warning(message: str):
        """记录警告"""
        logger.warning(message)
    
    @staticmethod
    def error(message: str):
        """记录错误"""
        logger.error(message)
    
    @staticmethod
    def debug(message: str):
        """记录调试信息"""
        logger.debug(message)
    
    # 预定义的日志方法
    @staticmethod
    def app_start():
        logger.info("=" * 50)
        logger.info("应用启动")
    
    @staticmethod
    def app_exit():
        logger.info("应用退出")
        logger.info("=" * 50)
    
    @staticmethod
    def user_login(user_name: str):
        logger.info(f"用户登录: {user_name}")
    
    @staticmethod
    def user_logout(user_name: str, duration: str):
        logger.info(f"用户登出: {user_name}, 使用时长: {duration}")
    
    @staticmethod
    def record_deleted(record_info: str):
        logger.info(f"记录删除: {record_info}")
    
    @staticmethod
    def password_changed():
        logger.info("管理员密码已修改")
    
    @staticmethod
    def backup_created(path: str):
        logger.info(f"备份已创建: {path}")
    
    @staticmethod
    def reservation_added(user_name: str, date: str, time_range: str):
        logger.info(f"预约添加: {user_name} - {date} {time_range}")
    
    @staticmethod
    def reservation_cancelled(reservation_id: int):
        logger.info(f"预约取消: ID {reservation_id}")


# 全局日志实例
app_logger = AppLogger()
