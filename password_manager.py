"""
密码管理模块
使用 bcrypt 加密存储密码
"""
import bcrypt
from config import config


class PasswordManager:
    """密码管理器"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """加密密码"""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """验证密码"""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
        except Exception:
            return False
    
    @staticmethod
    def check_admin_password(password: str) -> bool:
        """
        检查管理员密码
        如果未设置密码哈希，使用默认密码
        """
        stored_hash = config.get("admin_password_hash", "")
        
        if not stored_hash:
            # 未设置密码，使用默认密码
            default_pwd = config.get("default_password", "123456")
            return password == default_pwd
        
        return PasswordManager.verify_password(password, stored_hash)
    
    @staticmethod
    def set_admin_password(new_password: str):
        """设置新的管理员密码"""
        hashed = PasswordManager.hash_password(new_password)
        config.set("admin_password_hash", hashed)
    
    @staticmethod
    def change_admin_password(old_password: str, new_password: str) -> bool:
        """
        修改管理员密码
        
        Args:
            old_password: 旧密码
            new_password: 新密码
        
        Returns:
            是否修改成功
        """
        if not PasswordManager.check_admin_password(old_password):
            return False
        
        PasswordManager.set_admin_password(new_password)
        return True
    
    @staticmethod
    def is_password_set() -> bool:
        """检查是否已设置自定义密码"""
        return bool(config.get("admin_password_hash", ""))
    
    @staticmethod
    def reset_to_default():
        """重置为默认密码"""
        config.set("admin_password_hash", "")


# 全局密码管理器
password_manager = PasswordManager()
