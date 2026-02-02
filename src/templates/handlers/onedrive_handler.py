"""
OneDrive-Handler - Plattformunabhängig via rclone
Unterstützt Windows, Linux und macOS
"""

import logging
import platform
import shutil
import subprocess
from pathlib import Path
from typing import Optional, Tuple

from .base import TemplateHandler

logger = logging.getLogger(__name__)


class OnedriveHandler(TemplateHandler):
    """
    Handler für Microsoft OneDrive

    Funktionen:
    - Prüft ob rclone installiert ist
    - Bietet rclone-Installation an
    - Führt OAuth-Authentifizierung durch
    - Testet OneDrive-Verbindung
    """

    def check_availability(self) -> Tuple[bool, Optional[str]]:
        """Prüft ob rclone verfügbar ist"""
        if not self._is_rclone_installed():
            return (
                False,
                "rclone ist nicht installiert. "
                "OneDrive-Backups benötigen rclone.",
            )

        return (True, None)

    def setup(self, config: dict) -> Tuple[bool, dict, Optional[str]]:
        """
        Richtet OneDrive-Backup ein

        Args:
            config: {
                "account_type": "personal" oder "business",
                "path": "Backups" (Unterordner),
                "authenticated": True/False (aus UI)
            }

        Returns:
            (success, result_config, error)
        """
        account_type = config.get("account_type", "personal")
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
            success, error = self._run_oauth_flow(account_type)
            if not success:
                return (False, {}, error)

        # Teste Verbindung
        success, error = self._test_connection()
        if not success:
            return (False, {}, f"Verbindung zu OneDrive fehlgeschlagen: {error}")

        # Baue Config
        result_config = {
            "type": "rclone",
            "remote": "onedrive",
            "path": subpath,
            "name": "OneDrive-Backup",
            "enabled": True,
            "config": {
                "rclone_type": "onedrive",
                "account_type": account_type,
            },
        }

        return (True, result_config, None)

    def validate(self, config: dict) -> Tuple[bool, Optional[str]]:
        """Validiert OneDrive-Config"""
        if not self._is_rclone_installed():
            return (False, "rclone ist nicht installiert")

        # Prüfe ob Remote existiert
        if not self._remote_exists("onedrive"):
            return (False, "OneDrive ist nicht konfiguriert. Bitte authentifiziere dich.")

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

    def _run_oauth_flow(self, account_type: str) -> Tuple[bool, Optional[str]]:
        """
        Führt OAuth-Authentifizierung durch

        Args:
            account_type: "personal" oder "business"

        Returns:
            (success, error)
        """
        try:
            logger.info(f"Starte OAuth-Flow für OneDrive ({account_type})...")

            # rclone config create onedrive onedrive
            cmd = [
                "rclone",
                "config",
                "create",
                "onedrive",
                "onedrive",
                "--onedrive-type",
                account_type,
            ]

            # Interaktiv (öffnet Browser)
            result = subprocess.run(
                cmd,
                timeout=300,  # 5 Minuten für User-Interaktion
            )

            if result.returncode == 0:
                logger.info("OneDrive-Authentifizierung erfolgreich")
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
        Prüft ob OneDrive authentifiziert ist

        Returns:
            (authenticated, status_message)
        """
        if not self._is_rclone_installed():
            return (False, "❌ rclone nicht installiert")

        if not self._remote_exists("onedrive"):
            return (False, "⚠️ Nicht angemeldet")

        # Teste Verbindung
        success, error = self._test_connection()

        if success:
            # Hole Account-Info
            account_info = self._get_account_info()
            return (True, f"✅ Angemeldet als {account_info}")
        else:
            return (False, f"⚠️ Verbindung fehlgeschlagen: {error}")

    def _test_connection(self) -> Tuple[bool, Optional[str]]:
        """Testet OneDrive-Verbindung"""
        try:
            # rclone lsd onedrive:
            result = subprocess.run(
                ["rclone", "lsd", "onedrive:"],
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
        """Holt OneDrive-Account-Info"""
        try:
            result = subprocess.run(
                ["rclone", "about", "onedrive:"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                # Parse Ausgabe für User-Info
                # Beispiel: "Total: 5 GB, Used: 1.2 GB, Free: 3.8 GB"
                lines = result.stdout.strip().split("\n")
                for line in lines:
                    if "Total" in line:
                        return line.split(":")[0].strip()

            return "OneDrive-Benutzer"

        except Exception:
            return "OneDrive-Benutzer"

    # ========================================================================
    # rclone-Installation
    # ========================================================================

    def install_rclone(self) -> Tuple[bool, Optional[str]]:
        """
        Versucht rclone automatisch zu installieren

        Returns:
            (success, error)
        """
        system = platform.system()

        if system == "Windows":
            return self._install_rclone_windows()
        elif system == "Linux":
            return self._install_rclone_linux()
        elif system == "Darwin":
            return self._install_rclone_macos()
        else:
            return (
                False,
                f"Automatische Installation für {system} nicht unterstützt. "
                "Bitte installiere rclone manuell: https://rclone.org/install/",
            )

    def _install_rclone_windows(self) -> Tuple[bool, Optional[str]]:
        """Windows: rclone via Chocolatey oder manuell"""
        try:
            # Versuche Chocolatey
            if shutil.which("choco"):
                logger.info("Installiere rclone via Chocolatey...")
                result = subprocess.run(
                    ["choco", "install", "rclone", "-y"],
                    capture_output=True,
                    text=True,
                    timeout=300,
                )

                if result.returncode == 0:
                    logger.info("rclone erfolgreich installiert")
                    return (True, None)

            # Fallback: Download-Link
            return (
                False,
                "Bitte installiere rclone manuell: "
                "https://rclone.org/downloads/",
            )

        except Exception as e:
            return (False, f"Installation fehlgeschlagen: {e}")

    def _install_rclone_linux(self) -> Tuple[bool, Optional[str]]:
        """Linux: rclone via Paketmanager"""
        try:
            # Ubuntu/Debian
            if shutil.which("apt-get"):
                logger.info("Installiere rclone via apt...")
                result = subprocess.run(
                    ["sudo", "apt-get", "install", "-y", "rclone"],
                    timeout=300,
                )

                if result.returncode == 0:
                    return (True, None)

            # Fedora/RHEL
            elif shutil.which("dnf"):
                logger.info("Installiere rclone via dnf...")
                result = subprocess.run(
                    ["sudo", "dnf", "install", "-y", "rclone"],
                    timeout=300,
                )

                if result.returncode == 0:
                    return (True, None)

            # Arch
            elif shutil.which("pacman"):
                logger.info("Installiere rclone via pacman...")
                result = subprocess.run(
                    ["sudo", "pacman", "-S", "--noconfirm", "rclone"],
                    timeout=300,
                )

                if result.returncode == 0:
                    return (True, None)

            # Fallback: curl-Skript
            return self._install_rclone_curl()

        except Exception as e:
            return (False, f"Installation fehlgeschlagen: {e}")

    def _install_rclone_macos(self) -> Tuple[bool, Optional[str]]:
        """macOS: rclone via Homebrew"""
        try:
            if shutil.which("brew"):
                logger.info("Installiere rclone via Homebrew...")
                result = subprocess.run(
                    ["brew", "install", "rclone"],
                    timeout=300,
                )

                if result.returncode == 0:
                    return (True, None)

            return (
                False,
                "Bitte installiere Homebrew und führe aus: brew install rclone",
            )

        except Exception as e:
            return (False, f"Installation fehlgeschlagen: {e}")

    def _install_rclone_curl(self) -> Tuple[bool, Optional[str]]:
        """Linux/macOS: rclone via curl-Installationsskript"""
        try:
            logger.info("Installiere rclone via curl-Skript...")

            result = subprocess.run(
                ["curl", "https://rclone.org/install.sh"],
                capture_output=True,
                timeout=30,
            )

            if result.returncode == 0:
                # Führe Skript aus
                install_result = subprocess.run(
                    ["sudo", "bash"],
                    input=result.stdout,
                    timeout=300,
                )

                if install_result.returncode == 0:
                    return (True, None)

            return (False, "Installation via curl fehlgeschlagen")

        except Exception as e:
            return (False, f"Installation fehlgeschlagen: {e}")
