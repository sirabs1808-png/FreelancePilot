"""
Database Backup & Disaster Recovery Service for FreelancePilot.
Supports automatic snapshots, backup listing, and safe rollback restores.
"""

import os
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Tuple

from utils.config import DB_PATH, BACKUP_DIR


class BackupService:
    """
    Automated snapshot and restore manager for the SQLite database.
    """

    @staticmethod
    def create_backup(tag: str = "manual") -> Tuple[bool, str]:
        """
        Creates a timestamped snapshot of the current database.
        """
        if not DB_PATH.exists():
            return False, "Database file does not exist yet."

        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"freelancepilot_{tag}_{timestamp}.db"
        dest_path = BACKUP_DIR / backup_filename

        try:
            shutil.copy2(DB_PATH, dest_path)
            size_kb = dest_path.stat().st_size / 1024
            return True, f"Backup created successfully ({size_kb:.1f} KB) at:\n{dest_path.name}"
        except Exception as e:
            return False, f"Failed to create backup: {e}"

    @staticmethod
    def list_backups() -> List[Dict[str, Any]]:
        """
        Returns a sorted list of all existing backup snapshots.
        """
        if not BACKUP_DIR.exists():
            return []

        backups = []
        for file in BACKUP_DIR.glob("*.db"):
            stat = file.stat()
            backups.append({
                "path": str(file.resolve()),
                "filename": file.name,
                "created_at": datetime.fromtimestamp(stat.st_mtime),
                "size_kb": stat.st_size / 1024
            })

        backups.sort(key=lambda b: b["created_at"], reverse=True)
        return backups

    @staticmethod
    def restore_backup(backup_path: str) -> Tuple[bool, str]:
        """
        Restores the database from a backup file.
        Safely creates a pre-restore backup first to prevent accidental data loss.
        """
        backup_file = Path(backup_path)
        if not backup_file.exists():
            return False, "Selected backup file was not found."

        # 1. Create safety backup first
        BackupService.create_backup(tag="safety_pre_restore")

        # 2. Restore file
        try:
            from database.db import engine
            engine.dispose()  # Release open SQLite connections

            shutil.copy2(backup_file, DB_PATH)
            return True, f"Database restored successfully from '{backup_file.name}'."
        except Exception as e:
            return False, f"Restore failed: {e}"
