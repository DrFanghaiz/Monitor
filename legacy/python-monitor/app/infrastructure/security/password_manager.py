"""
密码管理模块
使用 bcrypt 加密存储密码
"""
import bcrypt


class PasswordManager:
    """密码管理器"""

    def __init__(self, config_provider):
        """
        Args:
            config_provider: object with get(key, default) and set(key, value) methods
        """
        self._config = config_provider

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

    def check_admin_password(self, password: str) -> bool:
        """
        检查管理员密码
        如果未设置密码哈希，使用默认密码
        """
        stored_hash = self._config.get("admin_password_hash", "")

        if not stored_hash:
            default_pwd = self._config.get("default_password", "123456")
            return password == default_pwd

        return PasswordManager.verify_password(password, stored_hash)

    def set_admin_password(self, new_password: str):
        """设置新的管理员密码"""
        hashed = PasswordManager.hash_password(new_password)
        self._config.set("admin_password_hash", hashed)

    def change_admin_password(self, old_password: str, new_password: str) -> bool:
        """
        修改管理员密码
        Returns: 是否修改成功
        """
        if not self.check_admin_password(old_password):
            return False

        self.set_admin_password(new_password)
        return True

    def is_password_set(self) -> bool:
        """检查是否已设置自定义密码"""
        return bool(self._config.get("admin_password_hash", ""))

    def reset_to_default(self):
        """重置为默认密码"""
        self._config.set("admin_password_hash", "")
