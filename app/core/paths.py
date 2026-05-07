"""
Centralized path definitions for the application.
"""
from pathlib import Path

# Project root (2 levels up from app/core/)
PROJECT_ROOT = Path(__file__).parent.parent.parent

CONFIG_FILE = PROJECT_ROOT / "config.json"
DB_FILE = PROJECT_ROOT / "monitor.db"
LOCK_FILE = PROJECT_ROOT / "monitor.lock"
LOG_FILE = PROJECT_ROOT / "app.log"
BACKUP_DIR = PROJECT_ROOT / "backups"
WEB_DIR = PROJECT_ROOT / "web"
OLD_TXT_FILE = PROJECT_ROOT / "usage_history.txt"
