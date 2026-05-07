"""
General utility functions shared across the application.
"""
from datetime import datetime


def format_duration(seconds: int) -> str:
    """Format seconds into HH:MM:SS string."""
    h, r = divmod(seconds, 3600)
    m, s = divmod(r, 60)
    return f"{h:02}:{m:02}:{s:02}"


def format_duration_cn(seconds: int) -> str:
    """Format seconds into Chinese duration string."""
    h, r = divmod(seconds, 3600)
    m, s = divmod(r, 60)
    return f"{h:02}小时{m:02}分{s:02}秒"


def today_str() -> str:
    """Get today's date as YYYY-MM-DD string."""
    return datetime.now().strftime("%Y-%m-%d")


def now_str() -> str:
    """Get current datetime as YYYY-MM-DD HH:MM:SS string."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
