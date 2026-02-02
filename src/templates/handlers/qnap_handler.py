"""
QNAP-Handler - Plattformunabhängig via SMB/CIFS
Unterstützt Windows, Linux und macOS
"""

import logging
import platform
import shutil
import subprocess
from typing import List, Optional, Tuple

from .base import TemplateHandler

logger = logging.getLogger(__name__)


class QnapHandler(TemplateHandler):
    """
    Handler für QNAP NAS

    Funktionen:
    - Scannt verfügbare SMB-Freigaben
    - Testet SMB-Verbindung
    - Plattformunabhängig (smbclient auf Linux, Windows SMB built-in)
    """

    def check_availability(self) -> Tuple[bool, Optional[str]]:
        """Prüft ob SMB-Client verfügbar ist"""
        system = platform.system()

        if system == "Windows":
            # Windows hat SMB built-in
            return (True, None)

        elif system in ["Linux", "Darwin"]:
            # Linux/macOS: smbclient benötigt
            if not shutil.which("smbclient"):
                return (
                    False,
                    "smbclient ist nicht installiert. "
                    "Installiere smbclient für SMB-Zugriff.",
                )
            return (True, None)

        else:
            return (False, f"SMB-Unterstützung für {system} nicht implementiert")

    def setup(self, config: dict) -> Tuple[bool, dict, Optional[str]]:
        """
        Richtet QNAP-Backup ein

        Args:
            config: {
                "host": "192.168.1.100" oder "nas.local",
                "share": "backups",
                "user": "admin",
                "password": "***",
                "path": "/scrat-backups"
            }

        Returns:
            (success, result_config, error)
        """
        host = config.get("host")
        share = config.get("share")
        user = config.get("user")
        password = config.get("password")
        subpath = config.get("path", "/scrat-backups")

        # Validiere Pflichtfelder
        if not all([host, share, user, password]):
            return (False, {}, "Bitte fülle alle Felder aus")

        # Teste Verbindung
        success, error = self.test_connection(host, share, user, password)
        if not success:
            return (False, {}, f"Verbindung fehlgeschlagen: {error}")

        # Baue Config
        result_config = {
            "type": "smb",
            "server": host,
            "port": 445,
            "share": share,
            "user": user,
            "password": password,  # TODO: Keyring-Integration
            "path": subpath,
            "name": f"QNAP-Backup ({host})",
            "enabled": True,
            "config": {
                "device_type": "qnap",
            },
        }

        return (True, result_config, None)

    def validate(self, config: dict) -> Tuple[bool, Optional[str]]:
        """Validiert QNAP-Config"""
        required_fields = ["server", "share", "user"]

        for field in required_fields:
            if not config.get(field):
                return (False, f"Feld '{field}' fehlt")

        # Teste Verbindung
        server = config.get("server")
        share = config.get("share")
        user = config.get("user")
        password = config.get("password", "")

        success, error = self.test_connection(server, share, user, password)
        if not success:
            return (False, f"Verbindung fehlgeschlagen: {error}")

        return (True, None)

    # ========================================================================
    # SMB-Funktionen
    # ========================================================================

    def scan_shares(
        self, host: str, user: Optional[str] = None, password: Optional[str] = None
    ) -> Tuple[bool, List[str], Optional[str]]:
        """
        Scannt verfügbare SMB-Freigaben auf QNAP

        Args:
            host: QNAP IP/Hostname
            user: Benutzername (optional für anonymous scan)
            password: Passwort (optional)

        Returns:
            (success, shares_list, error)
        """
        system = platform.system()

        if system == "Windows":
            return self._scan_shares_windows(host, user, password)
        elif system in ["Linux", "Darwin"]:
            return self._scan_shares_smbclient(host, user, password)
        else:
            return (False, [], f"Plattform {system} nicht unterstützt")

    def _scan_shares_smbclient(
        self, host: str, user: Optional[str], password: Optional[str]
    ) -> Tuple[bool, List[str], Optional[str]]:
        """Linux/macOS: smbclient -L"""
        try:
            cmd = ["smbclient", "-L", f"//{host}", "-N"]  # -N = no password

            if user:
                cmd.extend(["-U", user])

            # Password via stdin
            result = subprocess.run(
                cmd,
                input=password.encode() if password else None,
                capture_output=True,
                text=False,
                timeout=10,
            )

            if result.returncode != 0:
                return (False, [], result.stderr.decode().strip())

            # Parse Ausgabe
            shares = []
            output = result.stdout.decode()

            for line in output.split("\n"):
                # Beispiel: "  backups          Disk      Backup Storage"
                if "Disk" in line and not line.strip().startswith("IPC"):
                    parts = line.split()
                    if parts:
                        share_name = parts[0].strip()
                        if share_name and share_name not in ["$", "IPC$"]:
                            shares.append(share_name)

            logger.info(f"Gefundene Freigaben auf {host}: {shares}")
            return (True, shares, None)

        except subprocess.TimeoutExpired:
            return (False, [], "Timeout beim Scannen der Freigaben")
        except Exception as e:
            logger.error(f"Fehler beim Scannen: {e}")
            return (False, [], str(e))

    def _scan_shares_windows(
        self, host: str, user: Optional[str], password: Optional[str]
    ) -> Tuple[bool, List[str], Optional[str]]:
        """Windows: net view"""
        try:
            cmd = ["net", "view", f"\\\\{host}"]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode != 0:
                return (False, [], result.stderr.strip())

            # Parse Ausgabe
            shares = []
            output = result.stdout

            for line in output.split("\n"):
                # Beispiel: "backups          Disk      Backup Storage"
                if "Disk" in line:
                    parts = line.split()
                    if parts:
                        share_name = parts[0].strip()
                        if share_name and share_name not in ["$", "IPC$"]:
                            shares.append(share_name)

            logger.info(f"Gefundene Freigaben auf {host}: {shares}")
            return (True, shares, None)

        except subprocess.TimeoutExpired:
            return (False, [], "Timeout beim Scannen der Freigaben")
        except Exception as e:
            logger.error(f"Fehler beim Scannen: {e}")
            return (False, [], str(e))

    def test_connection(
        self, host: str, share: str, user: str, password: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Testet SMB-Verbindung zu QNAP

        Args:
            host: QNAP IP/Hostname
            share: Freigabe-Name
            user: Benutzername
            password: Passwort

        Returns:
            (success, error)
        """
        system = platform.system()

        if system == "Windows":
            return self._test_connection_windows(host, share, user, password)
        elif system in ["Linux", "Darwin"]:
            return self._test_connection_smbclient(host, share, user, password)
        else:
            return (False, f"Plattform {system} nicht unterstützt")

    def _test_connection_smbclient(
        self, host: str, share: str, user: str, password: str
    ) -> Tuple[bool, Optional[str]]:
        """Linux/macOS: smbclient -c ls"""
        try:
            cmd = [
                "smbclient",
                f"//{host}/{share}",
                "-U",
                user,
                "-c",
                "ls",
            ]

            result = subprocess.run(
                cmd,
                input=password.encode(),
                capture_output=True,
                text=False,
                timeout=10,
            )

            if result.returncode == 0:
                logger.info(f"SMB-Verbindungstest erfolgreich: {host}/{share}")
                return (True, None)
            else:
                error = result.stderr.decode().strip()
                logger.warning(f"SMB-Verbindungstest fehlgeschlagen: {error}")
                return (False, error)

        except subprocess.TimeoutExpired:
            return (False, "Timeout bei Verbindungstest")
        except Exception as e:
            return (False, str(e))

    def _test_connection_windows(
        self, host: str, share: str, user: str, password: str
    ) -> Tuple[bool, Optional[str]]:
        """Windows: net use"""
        try:
            # Temporärer Mount für Test
            unc_path = f"\\\\{host}\\{share}"

            # net use Z: \\host\share /user:username password
            cmd = ["net", "use", unc_path, f"/user:{user}", password]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0 or "already in use" in result.stdout.lower():
                logger.info(f"SMB-Verbindungstest erfolgreich: {unc_path}")

                # Cleanup: Verbindung trennen
                subprocess.run(
                    ["net", "use", unc_path, "/delete"],
                    capture_output=True,
                    timeout=5,
                )

                return (True, None)
            else:
                return (False, result.stderr.strip())

        except subprocess.TimeoutExpired:
            return (False, "Timeout bei Verbindungstest")
        except Exception as e:
            return (False, str(e))

    # ========================================================================
    # Hilfsfunktionen
    # ========================================================================

    def get_share_info(
        self, host: str, share: str, user: str, password: str
    ) -> Tuple[bool, dict, Optional[str]]:
        """
        Holt Informationen über eine Freigabe

        Returns:
            (success, info_dict, error)
            info_dict: {"size": "100 GB", "free": "50 GB", "used": "50 GB"}
        """
        system = platform.system()

        if system in ["Linux", "Darwin"]:
            return self._get_share_info_smbclient(host, share, user, password)
        elif system == "Windows":
            return self._get_share_info_windows(host, share, user, password)
        else:
            return (False, {}, f"Plattform {system} nicht unterstützt")

    def _get_share_info_smbclient(
        self, host: str, share: str, user: str, password: str
    ) -> Tuple[bool, dict, Optional[str]]:
        """Linux/macOS: smbclient -c du"""
        try:
            cmd = [
                "smbclient",
                f"//{host}/{share}",
                "-U",
                user,
                "-c",
                "du",
            ]

            result = subprocess.run(
                cmd,
                input=password.encode(),
                capture_output=True,
                text=False,
                timeout=10,
            )

            if result.returncode != 0:
                return (False, {}, result.stderr.decode().strip())

            # Parse du-Ausgabe
            output = result.stdout.decode()
            # TODO: Parse disk usage

            return (True, {"status": "ok"}, None)

        except Exception as e:
            return (False, {}, str(e))

    def _get_share_info_windows(
        self, host: str, share: str, user: str, password: str
    ) -> Tuple[bool, dict, Optional[str]]:
        """Windows: wmic"""
        # TODO: Implementierung
        return (True, {"status": "ok"}, None)
