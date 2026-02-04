"""
Google Drive Handler - Plattformunabhängig via rclone
Unterstützt Windows, Linux und macOS
"""

import logging
import shutil
import subprocess
from typing import Optional, Tuple

from .base import TemplateHandler

logger = logging.getLogger(__name__)


class GoogleDriveHandler(TemplateHandler):
    """
    Handler für Google Drive

    Funktionen:
    - Prüft ob rclone installiert ist
    - Führt OAuth-Authentifizierung durch (Google Account)
    - Testet Google Drive-Verbindung
    """

    def check_availability(self) -> Tuple[bool, Optional[str]]:
        """Prüft ob rclone verfügbar ist"""
        if not self._is_rclone_installed():
            return (
                False,
                "rclone ist nicht installiert. " "Google Drive-Backups benötigen rclone.",
            )

        return (True, None)

    def setup(self, config: dict) -> Tuple[bool, dict, Optional[str]]:
        """
        Richtet Google Drive-Backup ein

        Args:
            config: {
                "path": "Backups" (Unterordner),
                "authenticated": True/False (aus UI)
            }

        Returns:
            (success, result_config, error)
        """
        subpath = config.get("path", "Backups")
        authenticated = config.get("authenticated", False)

        # Prüfe rclone
        if not self._is_rclone_installed():
            return (
                False,
                {},
                "rclone ist nicht installiert. Bitte installiere rclone zuerst.",
            )

        # Prüfe Authentifizierung
        if not authenticated:
            # Führe OAuth-Flow durch
            success, error = self._run_oauth_flow()
            if not success:
                return (False, {}, error)

        # Teste Verbindung
        success, error = self._test_connection()
        if not success:
            return (False, {}, f"Verbindung zu Google Drive fehlgeschlagen: {error}")

        # Baue Config
        result_config = {
            "type": "rclone",
            "remote": "gdrive",
            "path": subpath,
            "name": "Google Drive Backup",
            "enabled": True,
            "config": {
                "rclone_type": "drive",
            },
        }

        return (True, result_config, None)

    def validate(self, config: dict) -> Tuple[bool, Optional[str]]:
        """Validiert Google Drive-Config"""
        if not self._is_rclone_installed():
            return (False, "rclone ist nicht installiert")

        # Prüfe ob Remote existiert
        if not self._remote_exists("gdrive"):
            return (False, "Google Drive ist nicht konfiguriert. Bitte authentifiziere dich.")

        return (True, None)

    # ========================================================================
    # rclone-Integration
    # ========================================================================

    def _is_rclone_installed(self) -> bool:
        """Prüft ob rclone installiert ist"""
        return shutil.which("rclone") is not None

    def _remote_exists(self, remote_name: str) -> bool:
        """Prüft ob rclone-Remote existiert"""
        try:
            result = subprocess.run(
                ["rclone", "listremotes"],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode != 0:
                return False

            remotes = result.stdout.strip().split("\n")
            return f"{remote_name}:" in remotes

        except Exception as e:
            logger.error(f"Fehler beim Prüfen von rclone-Remotes: {e}")
            return False

    def _run_oauth_flow(self) -> Tuple[bool, Optional[str]]:
        """
        Führt OAuth-Authentifizierung mit Google durch

        Returns:
            (success, error)
        """
        try:
            logger.info("Starte OAuth-Flow für Google Drive...")

            # rclone config create gdrive drive
            cmd = [
                "rclone",
                "config",
                "create",
                "gdrive",
                "drive",
            ]

            # Interaktiv (öffnet Browser für Google OAuth)
            result = subprocess.run(
                cmd,
                timeout=300,  # 5 Minuten für User-Interaktion
            )

            if result.returncode == 0:
                logger.info("Google Drive-Authentifizierung erfolgreich")
                return (True, None)
            else:
                return (False, "OAuth-Authentifizierung fehlgeschlagen")

        except subprocess.TimeoutExpired:
            return (False, "Authentifizierung abgelaufen (Timeout)")
        except Exception as e:
            logger.error(f"Fehler beim OAuth-Flow: {e}")
            return (False, f"Fehler bei der Authentifizierung: {e}")

    def check_authentication(self) -> Tuple[bool, str]:
        """
        Prüft ob Google Drive authentifiziert ist

        Returns:
            (authenticated, status_message)
        """
        if not self._is_rclone_installed():
            return (False, "❌ rclone nicht installiert")

        if not self._remote_exists("gdrive"):
            return (False, "⚠️ Nicht angemeldet")

        # Teste Verbindung
        success, error = self._test_connection()

        if success:
            # Hole Account-Info
            account_info = self._get_account_info()
            return (True, f"✅ Angemeldet: {account_info}")
        else:
            return (False, f"⚠️ Verbindung fehlgeschlagen: {error}")

    def _test_connection(self) -> Tuple[bool, Optional[str]]:
        """Testet Google Drive-Verbindung"""
        try:
            # rclone lsd gdrive:
            result = subprocess.run(
                ["rclone", "lsd", "gdrive:"],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                return (True, None)
            else:
                return (False, result.stderr.strip())

        except subprocess.TimeoutExpired:
            return (False, "Timeout bei Verbindungstest")
        except Exception as e:
            return (False, str(e))

    def _get_account_info(self) -> str:
        """Holt Google Drive-Account-Info"""
        try:
            result = subprocess.run(
                ["rclone", "about", "gdrive:"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                # Parse Ausgabe für User-Info
                lines = result.stdout.strip().split("\n")
                for line in lines:
                    if "Total" in line:
                        # Extrahiere Speicher-Info
                        return "Google Drive"

            return "Google-Konto"

        except Exception:
            return "Google-Konto"
