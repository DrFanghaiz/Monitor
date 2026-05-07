"""
多实例锁模块
防止同时运行多个程序实例
"""
import os
import sys
from pathlib import Path

LOCK_DIR = Path(__file__).parent
LOCK_FILE = LOCK_DIR / "monitor.lock"


class InstanceLock:
    """单实例锁"""
    
    def __init__(self):
        self._lock_file = None
        self._locked = False
    
    def acquire(self) -> bool:
        """尝试获取锁，成功返回 True"""
        try:
            # Windows 使用 msvcrt
            if sys.platform == "win32":
                import msvcrt
                self._lock_file = open(LOCK_FILE, "w")
                msvcrt.locking(self._lock_file.fileno(), msvcrt.LK_NBLCK, 1)
                self._lock_file.write(str(os.getpid()))
                self._lock_file.flush()
                self._locked = True
                return True
            else:
                # Unix 使用 fcntl
                import fcntl
                self._lock_file = open(LOCK_FILE, "w")
                fcntl.flock(self._lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                self._lock_file.write(str(os.getpid()))
                self._lock_file.flush()
                self._locked = True
                return True
        except (IOError, OSError):
            # 锁已被占用
            return False
    
    def release(self):
        """释放锁"""
        if self._lock_file:
            try:
                if sys.platform == "win32":
                    import msvcrt
                    msvcrt.locking(self._lock_file.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(self._lock_file.fileno(), fcntl.LOCK_UN)
                self._lock_file.close()
                if LOCK_FILE.exists():
                    LOCK_FILE.unlink()
            except Exception:
                pass
            finally:
                self._locked = False
                self._lock_file = None
    
    def is_locked(self) -> bool:
        """检查是否已锁定"""
        return self._locked
    
    def __enter__(self):
        if not self.acquire():
            raise RuntimeError("程序已在运行中")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()


# 全局实例锁
instance_lock = InstanceLock()


def check_single_instance() -> bool:
    """
    检查是否为单实例运行
    返回 True 表示可以运行，False 表示已有实例
    """
    return instance_lock.acquire()


def release_instance():
    """释放实例锁"""
    instance_lock.release()
