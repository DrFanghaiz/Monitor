"""
Backup service — wraps backup_manager so routes don't directly import infrastructure.
"""
from backup import backup_manager


class BackupService:
    """Exposes backup operations to the API layer."""

    def create_backup(self) -> str:
        """Create a manual backup. Returns the backup file path."""
        return backup_manager.create_backup(manual=True)

    def get_backup_list(self) -> list:
        """Get list of recent backups."""
        return backup_manager.get_backup_list()
