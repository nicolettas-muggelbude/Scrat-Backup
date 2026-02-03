"""
USB-Handler - Plattformunabhängige USB-Laufwerks-Erkennung
Unterstützt Windows, Linux und macOS
"""

import logging
import os
import platform
import shutil
import tempfile
from pathlib import Path
from typing import List, Optional, Tuple

from .base import TemplateHandler

logger = logging.getLogger(__name__)


class UsbHandler(TemplateHandler):
    """
    Handler für USB-Laufwerke

    Funktionen:
    - Erkennt USB-Laufwerke auf Windows, Linux und macOS
    - Prüft Schreibzugriff
    - Erstellt Backup-Ordner
    """

    def check_availability(self) -> Tuple[bool, Optional[str]]:
        """Prüft ob USB-Laufwerke verfügbar sind"""
        drives = self.detect_usb_drives()

        if not drives:
            return (
                False,
                "Kein USB-Laufwerk gefunden. Bitte USB-Stick oder "
                "externe Festplatte anschließen.",
            )

        return (True, None)

    def setup(self, config: dict) -> Tuple[bool, dict, Optional[str]]:
        """
        Richtet USB-Backup ein

        Args:
            config: {
                "drive": "/media/usb" oder "D:\\" (ausgewähltes Laufwerk),
                "path": "Backups" (Unterordner),
                "verify_writable": True (Schreibtest)
            }

        Returns:
            (success, result_config, error)
        """
        drive = config.get("drive")
        subpath = config.get("path", "Backups")
        verify = config.get("verify_writable", True)

        if not drive:
            return (False, {}, "Kein Laufwerk ausgewählt")

        # Baue finalen Pfad
        full_path = Path(drive) / subpath

        # Erstelle Ordner
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"USB-Backup-Ordner erstellt: {full_path}")
        except Exception as e:
            return (False, {}, f"Fehler beim Erstellen des Ordners: {e}")

        # Schreibtest
        if verify:
            success, error = self._test_write_access(full_path)
            if not success:
                return (False, {}, error)

        # Ermittle Laufwerks-Label für Display-Name
        drive_label = self._get_drive_label(drive)

        # Baue Config für ConfigManager
        result_config = {
            "type": "local",
            "path": str(full_path),
            "name": f"USB-Backup ({drive_label})",
            "enabled": True,
        }

        return (True, result_config, None)

    def validate(self, config: dict) -> Tuple[bool, Optional[str]]:
        """Validiert USB-Config"""
        path = config.get("path")

        if not path:
            return (False, "Kein Pfad angegeben")

        path_obj = Path(path)

        if not path_obj.exists():
            return (False, f"Pfad existiert nicht: {path}")

        if not path_obj.is_dir():
            return (False, f"Pfad ist kein Verzeichnis: {path}")

        # Prüfe Schreibzugriff
        if not os.access(path, os.W_OK):
            return (False, f"Kein Schreibzugriff auf {path}")

        return (True, None)

    # ========================================================================
    # USB-Laufwerks-Erkennung (Plattformspezifisch)
    # ========================================================================

    def detect_usb_drives(self) -> List[dict]:
        """
        Erkennt USB-Laufwerke plattformspezifisch

        Returns:
            Liste von Dicts: [
                {"path": "/media/usb", "label": "USB-Stick", "size": 16GB},
                ...
            ]
        """
        system = platform.system()
        logger.info(f"USB-Erkennung: platform.system() = '{system}'")

        if system == "Windows":
            drives = self._detect_windows_drives()
        elif system == "Linux":
            drives = self._detect_linux_drives()
        elif system == "Darwin":  # macOS
            drives = self._detect_macos_drives()
        else:
            logger.warning(f"Unbekanntes System: {system}")
            drives = []

        logger.info(f"USB-Erkennung: {len(drives)} Laufwerk(e) gefunden")
        return drives

    def _detect_windows_drives(self) -> List[dict]:
        """
        Windows: Erkennbare Laufwerke
        - Typ 2 (Removable): USB-Sticks
        - Typ 3 (Fixed) außer Systemlaufwerk: Externe Festplatten
        """
        drives = []

        try:
            import ctypes
            import string

            # Systemlaufwerk ausschließen (z.B. C:)
            system_drive = os.environ.get("SystemDrive", "C:").upper().rstrip("\\")

            logger.info(f"USB-Erkennung: Systemlaufwerk = '{system_drive}'")

            for letter in string.ascii_uppercase:
                drive_path = f"{letter}:\\"

                if not Path(drive_path).exists():
                    continue

                # GetDriveTypeW: 2 = Removable, 3 = Fixed, 4 = Network, 6 = CD-ROM
                drive_type = ctypes.windll.kernel32.GetDriveTypeW(drive_path)
                logger.info(f"USB-Erkennung: {letter}: existiert, Typ={drive_type}")

                # Systemlaufwerk überspringen
                if f"{letter}:".upper() == system_drive:
                    logger.info(f"USB-Erkennung: {letter}: übersprungen (Systemlaufwerk)")
                    continue

                if drive_type not in (2, 3):
                    logger.info(f"USB-Erkennung: {letter}: übersprungen (Typ {drive_type})")
                    continue

                label = self._get_windows_volume_label(drive_path)
                size = self._get_drive_size(drive_path)

                drives.append({
                    "path": drive_path,
                    "label": label or f"Laufwerk {letter}:",
                    "size": size,
                    "is_usb": drive_type == 2,
                })

                logger.debug(f"Laufwerk gefunden: {letter}: Typ={drive_type} ({label})")

        except Exception as e:
            logger.error(f"Fehler bei Windows-Laufwerks-Erkennung: {e}")

        return drives

    def _detect_linux_drives(self) -> List[dict]:
        """
        Linux: Mehrere Quellen prüfen
        - /media/USER/*
        - /mnt/*
        - /run/media/USER/*
        """
        drives = []

        # 1. /media/USER/* (Ubuntu, Debian)
        try:
            username = os.getlogin()
            media_path = Path("/media") / username

            if media_path.exists():
                for drive in media_path.iterdir():
                    if drive.is_dir() and self._is_removable_linux(drive):
                        size = self._get_drive_size(str(drive))
                        drives.append({
                            "path": str(drive),
                            "label": drive.name,
                            "size": size,
                            "is_usb": True,
                        })
                        logger.debug(f"USB-Laufwerk gefunden: {drive}")

        except Exception as e:
            logger.debug(f"Konnte /media nicht scannen: {e}")

        # 2. /run/media/USER/* (Fedora, RHEL)
        try:
            username = os.getlogin()
            run_media = Path("/run/media") / username

            if run_media.exists():
                for drive in run_media.iterdir():
                    if drive.is_dir() and self._is_removable_linux(drive):
                        # Duplikat-Check
                        if not any(d["path"] == str(drive) for d in drives):
                            size = self._get_drive_size(str(drive))
                            drives.append({
                                "path": str(drive),
                                "label": drive.name,
                                "size": size,
                                "is_usb": True,
                            })
                            logger.debug(f"USB-Laufwerk gefunden: {drive}")

        except Exception as e:
            logger.debug(f"Konnte /run/media nicht scannen: {e}")

        # 3. /mnt/* (manuell gemountet)
        try:
            mnt_path = Path("/mnt")

            if mnt_path.exists():
                for drive in mnt_path.iterdir():
                    if drive.is_dir() and drive.name not in ["wsl", "wslg"]:
                        # Prüfe ob gemountet
                        if self._is_mounted_linux(drive):
                            # Duplikat-Check
                            if not any(d["path"] == str(drive) for d in drives):
                                size = self._get_drive_size(str(drive))
                                drives.append({
                                    "path": str(drive),
                                    "label": drive.name,
                                    "size": size,
                                    "is_usb": False,  # Kann nicht sicher sein
                                })
                                logger.debug(f"Laufwerk gefunden: {drive}")

        except Exception as e:
            logger.debug(f"Konnte /mnt nicht scannen: {e}")

        return drives

    def _detect_macos_drives(self) -> List[dict]:
        """macOS: /Volumes/*"""
        drives = []

        try:
            volumes_path = Path("/Volumes")

            if volumes_path.exists():
                for drive in volumes_path.iterdir():
                    if drive.is_dir() and drive.name != "Macintosh HD":
                        size = self._get_drive_size(str(drive))
                        drives.append({
                            "path": str(drive),
                            "label": drive.name,
                            "size": size,
                            "is_usb": True,  # Meistens externe Laufwerke
                        })
                        logger.debug(f"Laufwerk gefunden: {drive}")

        except Exception as e:
            logger.error(f"Fehler bei macOS-Laufwerks-Erkennung: {e}")

        return drives

    # ========================================================================
    # Hilfsfunktionen
    # ========================================================================

    def _is_removable_linux(self, path: Path) -> bool:
        """
        Prüft ob Linux-Laufwerk removable ist

        Liest /sys/block/*/removable
        """
        try:
            # Finde Block-Device für Mount-Point
            import subprocess

            result = subprocess.run(
                ["findmnt", "-no", "SOURCE", str(path)],
                capture_output=True,
                text=True,
                timeout=2,
            )

            if result.returncode != 0:
                return False

            device = result.stdout.strip()

            # Extrahiere Block-Device-Name (z.B. /dev/sdb1 -> sdb)
            device_name = Path(device).name.rstrip("0123456789")

            # Prüfe /sys/block/*/removable
            removable_file = Path(f"/sys/block/{device_name}/removable")

            if removable_file.exists():
                return removable_file.read_text().strip() == "1"

        except Exception as e:
            logger.debug(f"Konnte Removable-Status nicht prüfen: {e}")

        return False

    def _is_mounted_linux(self, path: Path) -> bool:
        """Prüft ob Pfad ein Mount-Point ist"""
        try:
            import subprocess

            result = subprocess.run(
                ["mountpoint", "-q", str(path)],
                capture_output=True,
                timeout=2,
            )

            return result.returncode == 0

        except Exception:
            return False

    def _get_windows_volume_label(self, drive_path: str) -> Optional[str]:
        """Holt Volume-Label unter Windows"""
        try:
            import ctypes

            volumeNameBuffer = ctypes.create_unicode_buffer(1024)
            fileSystemNameBuffer = ctypes.create_unicode_buffer(1024)

            ctypes.windll.kernel32.GetVolumeInformationW(
                ctypes.c_wchar_p(drive_path),
                volumeNameBuffer,
                ctypes.sizeof(volumeNameBuffer),
                None,
                None,
                None,
                fileSystemNameBuffer,
                ctypes.sizeof(fileSystemNameBuffer),
            )

            return volumeNameBuffer.value or None

        except Exception:
            return None

    def _get_drive_label(self, drive_path: str) -> str:
        """Gibt anzeigbaren Label für Laufwerk zurück"""
        drives = self.detect_usb_drives()

        for drive in drives:
            if drive["path"] == drive_path:
                return drive["label"]

        # Fallback
        return Path(drive_path).name or drive_path

    def _get_drive_size(self, path: str) -> Optional[str]:
        """Gibt formatierte Laufwerksgröße zurück"""
        try:
            stat = shutil.disk_usage(path)
            total_gb = stat.total / (1024**3)

            if total_gb < 1:
                return f"{stat.total / (1024**2):.0f} MB"
            else:
                return f"{total_gb:.1f} GB"

        except Exception:
            return None

    def _test_write_access(self, path: Path) -> Tuple[bool, Optional[str]]:
        """Testet Schreibzugriff auf Pfad"""
        try:
            # Erstelle temporäre Testdatei
            test_file = path / ".scrat-backup-test"

            test_file.write_text("test")
            test_file.unlink()

            logger.info(f"Schreibtest erfolgreich: {path}")
            return (True, None)

        except Exception as e:
            return (False, f"Kein Schreibzugriff: {e}")
