"""
ConfigManager für persistente App-Einstellungen
Verwaltet Konfiguration in JSON-Datei
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class ConfigManager:
    """
    Verwaltet App-Konfiguration

    Features:
    - Lädt/speichert Settings aus JSON-Datei
    - Standard-Werte für alle Einstellungen
    - Type-safe Getter/Setter
    - Auto-Erstellung von Config-Verzeichnis
    """

    # Standard-Werte
    DEFAULTS = {
        # Allgemein
        "general": {
            "language": "de",  # de, en
            "theme": "system",  # light, dark, system
            "start_with_system": False,
            "minimize_to_tray": False,
        },
        # Backup
        "backup": {
            "default_destination": str(Path.home() / "scrat-backups"),
            "compression_level": 5,  # 0-9
            "archive_split_size_mb": 100,  # MB
            "keep_backups": 10,  # Anzahl zu behaltender Backups
            "verify_after_backup": True,
        },
        # Pfade
        "paths": {
            "metadata_db": "",  # Leer = Standard (~/.scrat-backup/metadata.db)
            "temp_dir": "",  # Leer = System-Temp
            "log_dir": "",  # Leer = Standard (~/.scrat-backup/logs)
        },
        # Erweitert
        "advanced": {
            "log_level": "INFO",  # DEBUG, INFO, WARNING, ERROR
            "max_threads": 4,
            "network_timeout": 300,  # Sekunden
            "retry_count": 3,
        },
        # Storage-Backend-Konfigurationen
        "storage": {
            "sftp_connections": [],  # Liste gespeicherter SFTP-Verbindungen
            "smb_shares": [],  # Liste gespeicherter SMB-Shares
            "webdav_servers": [],  # Liste gespeicherter WebDAV-Server
            "rclone_remotes": [],  # Liste gespeicherter Rclone-Remotes
        },
    }

    def __init__(self, config_file: Optional[Path] = None):
        """
        Initialisiert ConfigManager

        Args:
            config_file: Pfad zur Config-Datei (None = Standard)
        """
        # Config-Datei-Pfad
        if config_file is None:
            config_dir = Path.home() / ".scrat-backup"
            config_dir.mkdir(parents=True, exist_ok=True)
            self.config_file = config_dir / "config.json"
        else:
            self.config_file = config_file

        # Lade Konfiguration
        self.config: Dict[str, Any] = {}
        self.load()

        logger.info(f"ConfigManager initialisiert: {self.config_file}")

    def load(self) -> None:
        """Lädt Konfiguration aus Datei"""
        if self.config_file.exists():
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    loaded_config = json.load(f)

                # Merge mit Defaults (neue Einstellungen hinzufügen)
                self.config = self._merge_config(self.DEFAULTS, loaded_config)

                logger.info(f"Konfiguration geladen: {self.config_file}")

            except Exception as e:
                logger.error(f"Fehler beim Laden der Konfiguration: {e}", exc_info=True)
                # Fallback auf Defaults
                self.config = self._deep_copy(self.DEFAULTS)
        else:
            # Neue Config mit Defaults
            self.config = self._deep_copy(self.DEFAULTS)
            logger.info("Keine Konfiguration gefunden, nutze Defaults")

    def save(self) -> None:
        """Speichert Konfiguration in Datei"""
        try:
            # Erstelle Verzeichnis falls nötig
            self.config_file.parent.mkdir(parents=True, exist_ok=True)

            # Speichere JSON
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)

            logger.info(f"Konfiguration gespeichert: {self.config_file}")

        except Exception as e:
            logger.error(f"Fehler beim Speichern der Konfiguration: {e}", exc_info=True)
            raise

    def reset_to_defaults(self) -> None:
        """Setzt Konfiguration auf Defaults zurück"""
        self.config = self._deep_copy(self.DEFAULTS)
        logger.info("Konfiguration auf Defaults zurückgesetzt")

    def get(self, section: str, key: str, default: Any = None) -> Any:
        """
        Holt Konfigurations-Wert

        Args:
            section: Konfigurations-Sektion (z.B. "general")
            key: Konfigurations-Key (z.B. "language")
            default: Fallback-Wert falls nicht gefunden

        Returns:
            Konfigurations-Wert oder default
        """
        try:
            return self.config[section][key]
        except KeyError:
            return default

    def set(self, section: str, key: str, value: Any) -> None:
        """
        Setzt Konfigurations-Wert

        Args:
            section: Konfigurations-Sektion
            key: Konfigurations-Key
            value: Neuer Wert
        """
        if section not in self.config:
            self.config[section] = {}

        self.config[section][key] = value

    def get_section(self, section: str) -> Dict[str, Any]:
        """
        Holt komplette Sektion

        Args:
            section: Sektions-Name

        Returns:
            Dictionary mit allen Werten der Sektion
        """
        return self.config.get(section, {})

    def set_section(self, section: str, values: Dict[str, Any]) -> None:
        """
        Setzt komplette Sektion

        Args:
            section: Sektions-Name
            values: Alle Werte für Sektion
        """
        self.config[section] = values

    def _merge_config(self, defaults: Dict, loaded: Dict) -> Dict:
        """
        Merged geladene Config mit Defaults (rekursiv)

        Neue Keys aus defaults werden hinzugefügt,
        existierende Werte aus loaded bleiben erhalten.

        Args:
            defaults: Default-Konfiguration
            loaded: Geladene Konfiguration

        Returns:
            Gemergete Konfiguration
        """
        result = self._deep_copy(defaults)

        for key, value in loaded.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                # Rekursiv mergen
                result[key] = self._merge_config(result[key], value)
            else:
                # Wert übernehmen
                result[key] = value

        return result

    def _deep_copy(self, obj: Any) -> Any:
        """
        Erstellt Deep-Copy von dict/list (einfache Variante)

        Args:
            obj: Zu kopierendes Objekt

        Returns:
            Deep-Copy
        """
        if isinstance(obj, dict):
            return {k: self._deep_copy(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._deep_copy(v) for v in obj]
        else:
            return obj
