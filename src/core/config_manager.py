"""
ConfigManager für persistente App-Einstellungen
Verwaltet Konfiguration in JSON-Datei
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from utils.paths import get_app_data_dir

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
        # Zeitpläne
        "schedules": [],  # Liste von Schedule-Dicts
    }

    def __init__(self, config_file: Optional[Path] = None):
        """
        Initialisiert ConfigManager

        Args:
            config_file: Pfad zur Config-Datei (None = Standard)
        """
        # Config-Datei-Pfad
        if config_file is None:
            config_dir = get_app_data_dir()
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

    # Schedule-Management

    def get_schedules(self) -> list:
        """
        Holt alle Zeitpläne

        Returns:
            Liste von Schedule-Dicts
        """
        return self.config.get("schedules", [])

    def add_schedule(self, schedule: dict) -> None:
        """
        Fügt einen Zeitplan hinzu

        Args:
            schedule: Schedule-Dict
        """
        schedules = self.config.get("schedules", [])
        schedules.append(schedule)
        self.config["schedules"] = schedules
        self.save()
        logger.info(f"Zeitplan hinzugefügt: {schedule.get('name')}")

    def update_schedule(self, schedule_id: int, schedule: dict) -> bool:
        """
        Aktualisiert einen Zeitplan

        Args:
            schedule_id: ID des Zeitplans
            schedule: Neue Schedule-Daten

        Returns:
            True wenn gefunden und aktualisiert
        """
        schedules = self.config.get("schedules", [])

        for i, s in enumerate(schedules):
            if s.get("id") == schedule_id:
                schedules[i] = schedule
                self.config["schedules"] = schedules
                self.save()
                logger.info(f"Zeitplan aktualisiert: {schedule.get('name')}")
                return True

        logger.warning(f"Zeitplan nicht gefunden: ID={schedule_id}")
        return False

    def delete_schedule(self, schedule_id: int) -> bool:
        """
        Löscht einen Zeitplan

        Args:
            schedule_id: ID des Zeitplans

        Returns:
            True wenn gefunden und gelöscht
        """
        schedules = self.config.get("schedules", [])
        original_count = len(schedules)

        schedules = [s for s in schedules if s.get("id") != schedule_id]

        if len(schedules) < original_count:
            self.config["schedules"] = schedules
            self.save()
            logger.info(f"Zeitplan gelöscht: ID={schedule_id}")
            return True

        logger.warning(f"Zeitplan nicht gefunden: ID={schedule_id}")
        return False

    def get_next_schedule_id(self) -> int:
        """
        Generiert nächste Schedule-ID (auto-increment)

        Returns:
            Nächste verfügbare ID
        """
        schedules = self.config.get("schedules", [])
        if not schedules:
            return 1

        max_id = max(s.get("id", 0) for s in schedules)
        return max_id + 1

    # Profil-Management

    def get_profiles(self) -> list:
        """Gibt alle Backup-Profile zurück. Migriert automatisch aus altem destinations[]-Format."""
        if "profiles" not in self.config:
            self._migrate_to_profiles()
        return self.config.get("profiles", [])

    def _migrate_to_profiles(self) -> None:
        """Erstellt profiles[] einmalig aus destinations[]/schedules[] (Rückwärts-Kompatibilität)."""
        destinations = self.config.get("destinations", [])
        schedules = self.config.get("schedules", [])
        profiles = []

        for i, dest in enumerate(destinations):
            schedule_entry = None
            for s in schedules:
                if s.get("destination_id", 0) == i:
                    schedule_entry = {
                        "enabled": s.get("enabled", True),
                        "frequency": s.get("frequency", "daily"),
                        "time": s.get("time", "03:00"),
                        "weekdays": s.get("weekdays", []),
                        "day_of_month": s.get("day_of_month", 1),
                    }
                    break

            profiles.append({
                "id": f"profile_{i + 1}",
                "name": dest.get("name", f"Backup {i + 1}"),
                "destination": {
                    "name": dest.get("name", ""),
                    "type": dest.get("type", "local"),
                    "config": dest.get("config", {}),
                },
                "schedule": schedule_entry,
                "enabled": dest.get("enabled", True),
            })

        self.config["profiles"] = profiles
        if profiles:
            self.save()
            logger.info(f"Migration: {len(profiles)} Profil(e) aus Destinations erstellt")
        else:
            logger.info("Migration: Keine Destinations – leere Profile-Liste angelegt")

    def save_profile(self, profile: dict) -> None:
        """Erstellt oder aktualisiert ein Backup-Profil."""
        if "profiles" not in self.config:
            self.config["profiles"] = []

        profiles = self.config["profiles"]
        profile_id = profile.get("id")

        for i, p in enumerate(profiles):
            if p.get("id") == profile_id:
                profiles[i] = profile
                self.save()
                logger.info(f"Profil aktualisiert: {profile.get('name')}")
                return

        profiles.append(profile)
        self.save()
        logger.info(f"Profil hinzugefügt: {profile.get('name')}")

    def delete_profile(self, profile_id: str) -> bool:
        """Löscht ein Backup-Profil. Gibt True zurück wenn gefunden und gelöscht."""
        profiles = self.config.get("profiles", [])
        original = len(profiles)
        self.config["profiles"] = [p for p in profiles if p.get("id") != profile_id]
        if len(self.config["profiles"]) < original:
            self.save()
            logger.info(f"Profil gelöscht: {profile_id}")
            return True
        return False
