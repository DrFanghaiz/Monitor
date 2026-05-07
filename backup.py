"""
数据备份模块
支持自动备份和手动备份/恢复
"""
import shutil
import zipfile
from datetime import datetime
from pathlib import Path
from config import config, CONFIG_FILE
from database import DB_FILE
from logger import app_logger

# 备份目录
BACKUP_DIR = Path(__file__).parent / "backups"


class BackupManager:
    """备份管理器"""
    
    def __init__(self):
        self._ensure_backup_dir()
    
    def _ensure_backup_dir(self):
        """确保备份目录存在"""
        BACKUP_DIR.mkdir(exist_ok=True)
    
    def create_backup(self, manual: bool = False) -> str:
        """
        创建备份
        
        Args:
            manual: 是否为手动备份
        
        Returns:
            备份文件路径
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        prefix = "manual" if manual else "auto"
        backup_name = f"{prefix}_backup_{timestamp}.zip"
        backup_path = BACKUP_DIR / backup_name
        
        try:
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # 备份数据库
                if DB_FILE.exists():
                    zipf.write(DB_FILE, DB_FILE.name)
                
                # 备份配置文件
                if CONFIG_FILE.exists():
                    zipf.write(CONFIG_FILE, CONFIG_FILE.name)
            
            app_logger.backup_created(str(backup_path))
            
            # 清理旧备份
            if not manual:
                self._cleanup_old_backups()
            
            return str(backup_path)
        
        except Exception as e:
            app_logger.error(f"备份失败: {e}")
            raise
    
    def restore_backup(self, backup_path: str) -> bool:
        """
        从备份恢复
        
        Args:
            backup_path: 备份文件路径
        
        Returns:
            是否恢复成功
        """
        try:
            backup_file = Path(backup_path)
            if not backup_file.exists():
                return False
            
            # 解压到临时目录
            temp_dir = BACKUP_DIR / "temp_restore"
            temp_dir.mkdir(exist_ok=True)
            
            with zipfile.ZipFile(backup_file, 'r') as zipf:
                zipf.extractall(temp_dir)
            
            # 恢复数据库
            temp_db = temp_dir / DB_FILE.name
            if temp_db.exists():
                shutil.copy2(temp_db, DB_FILE)
            
            # 恢复配置文件
            temp_config = temp_dir / CONFIG_FILE.name
            if temp_config.exists():
                shutil.copy2(temp_config, CONFIG_FILE)
            
            # 清理临时目录
            shutil.rmtree(temp_dir)
            
            app_logger.info(f"从备份恢复成功: {backup_path}")
            return True
        
        except Exception as e:
            app_logger.error(f"恢复备份失败: {e}")
            return False
    
    def _cleanup_old_backups(self):
        """清理过期的自动备份"""
        retention_days = config.get("backup_retention_days", 30)
        cutoff = datetime.now().timestamp() - (retention_days * 24 * 3600)
        
        for backup_file in BACKUP_DIR.glob("auto_backup_*.zip"):
            if backup_file.stat().st_mtime < cutoff:
                try:
                    backup_file.unlink()
                    app_logger.info(f"清理过期备份: {backup_file.name}")
                except Exception:
                    pass
    
    def get_backup_list(self) -> list:
        """获取备份列表"""
        backups = []
        for backup_file in sorted(BACKUP_DIR.glob("*.zip"), reverse=True):
            stat = backup_file.stat()
            backups.append({
                "name": backup_file.name,
                "path": str(backup_file),
                "size": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                "is_manual": backup_file.name.startswith("manual_")
            })
        return backups
    
    def should_auto_backup(self) -> bool:
        """检查是否需要自动备份（每日首次启动）"""
        if not config.get("auto_backup", True):
            return False
        
        today = datetime.now().strftime("%Y%m%d")
        for backup_file in BACKUP_DIR.glob(f"auto_backup_{today}*.zip"):
            return False  # 今天已有备份
        
        return True
    
    def auto_backup_if_needed(self):
        """如果需要则执行自动备份"""
        if self.should_auto_backup():
            try:
                self.create_backup(manual=False)
            except Exception:
                pass  # 静默失败


# 全局备份管理器
backup_manager = BackupManager()
