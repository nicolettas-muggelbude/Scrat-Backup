"""
Plattformspezifische App-Pfade fuer Scrat-Backup.

Windows : %LOCALAPPDATA%/Scrat-Backup/
Linux   : ~/.scrat-backup/
macOS   : ~/.scrat-backup/
"""

import platform
import os
from pathlib import Path


def get_app_data_dir() -> Path:
    """
    Gibt das plattformspezifische Datenverzeichnis zurück.

    Windows : %LOCALAPPDATA%\\Scrat-Backup
    Linux   : ~/.scrat-backup
    macOS   : ~/.scrat-backup
    """
    if platform.system() == "Windows":
        local_app_data = os.environ.get("LOCALAPPDATA")
        if local_app_data:
            return Path(local_app_data) / "Scrat-Backup"
        # Fallback falls LOCALAPPDATA nicht gesetzt
        return Path.home() / "AppData" / "Local" / "Scrat-Backup"
    else:
        return Path.home() / ".scrat-backup"
