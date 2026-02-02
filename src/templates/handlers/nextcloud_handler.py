"""
Nextcloud Handler - Plattformunabhängig via WebDAV
Unterstützt Windows, Linux und macOS
"""

import logging
import subprocess
from typing import Optional, Tuple
from urllib.parse import urljoin, urlparse

from .base import TemplateHandler

logger = logging.getLogger(__name__)


class NextcloudHandler(TemplateHandler):
    """
    Handler für Nextcloud

    Funktionen:
    - WebDAV-Verbindung testen
    - Nextcloud-URL validieren
    - Ordner erstellen
    """

    def check_availability(self) -> Tuple[bool, Optional[str]]:
        """Nextcloud ist immer verfügbar (nutzt Python requests)"""
        return (True, None)

    def setup(self, config: dict) -> Tuple[bool, dict, Optional[str]]:
        """
        Richtet Nextcloud-Backup ein

        Args:
            config: {
                "url": "https://cloud.example.com",
                "user": "username",
                "password": "app-password",
                "path": "Backups"
            }

        Returns:
            (success, result_config, error)
        """
        url = config.get("url")
        user = config.get("user")
        password = config.get("password")
        path = config.get("path", "Backups")

        # Validiere
        if not all([url, user, password]):
            return (False, {}, "Bitte fülle alle Felder aus")

        # Validiere URL
        if not url.startswith(("http://", "https://")):
            return (False, {}, "URL muss mit http:// oder https:// beginnen")

        # Baue WebDAV-URL
        webdav_url = self._build_webdav_url(url, user)

        # Teste Verbindung
        success, error = self.test_connection(url, user, password)
        if not success:
            return (False, {}, f"Verbindung fehlgeschlagen: {error}")

        # Baue Config
        result_config = {
            "type": "webdav",
            "url": webdav_url,
            "user": user,
            "password": password,  # TODO: Keyring
            "path": path,
            "name": "Nextcloud-Backup",
            "enabled": True,
            "config": {
                "nextcloud_url": url,
            },
        }

        return (True, result_config, None)

    def validate(self, config: dict) -> Tuple[bool, Optional[str]]:
        """Validiert Nextcloud-Config"""
        url = config.get("url")
        user = config.get("user")
        password = config.get("password")

        if not all([url, user, password]):
            return (False, "URL, Benutzername und Passwort erforderlich")

        # Teste Verbindung
        success, error = self.test_connection(url, user, password)
        if not success:
            return (False, f"Verbindung fehlgeschlagen: {error}")

        return (True, None)

    # ========================================================================
    # Nextcloud/WebDAV-Funktionen
    # ========================================================================

    def _build_webdav_url(self, nextcloud_url: str, user: str) -> str:
        """
        Baut WebDAV-URL für Nextcloud

        Args:
            nextcloud_url: https://cloud.example.com
            user: username

        Returns:
            https://cloud.example.com/remote.php/dav/files/username/
        """
        # Entferne trailing slash
        base_url = nextcloud_url.rstrip("/")

        # Baue WebDAV-Pfad
        webdav_path = f"/remote.php/dav/files/{user}/"

        return urljoin(base_url, webdav_path)

    def test_connection(
        self, nextcloud_url: str, user: str, password: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Testet WebDAV-Verbindung zu Nextcloud

        Args:
            nextcloud_url: https://cloud.example.com
            user: Benutzername
            password: Passwort

        Returns:
            (success, error)
        """
        try:
            # Python requests für WebDAV-Test
            import requests
            from requests.auth import HTTPBasicAuth

            webdav_url = self._build_webdav_url(nextcloud_url, user)

            # PROPFIND-Request (WebDAV list)
            response = requests.request(
                "PROPFIND",
                webdav_url,
                auth=HTTPBasicAuth(user, password),
                timeout=10,
            )

            if response.status_code in [200, 207]:  # 207 = Multi-Status (WebDAV)
                logger.info(f"Nextcloud-Verbindung erfolgreich: {webdav_url}")
                return (True, None)
            elif response.status_code == 401:
                return (False, "Authentifizierung fehlgeschlagen (falsches Passwort)")
            elif response.status_code == 404:
                return (False, "Nextcloud-Server nicht gefunden (falsche URL)")
            else:
                return (False, f"HTTP {response.status_code}: {response.reason}")

        except ImportError:
            return (
                False,
                "Python requests-Bibliothek fehlt. Installiere: pip install requests",
            )
        except requests.exceptions.ConnectionError:
            return (False, "Verbindung fehlgeschlagen (Server nicht erreichbar)")
        except requests.exceptions.Timeout:
            return (False, "Timeout (Server antwortet nicht)")
        except Exception as e:
            logger.error(f"Fehler beim Nextcloud-Verbindungstest: {e}")
            return (False, str(e))

    def get_server_info(self, nextcloud_url: str, user: str, password: str) -> dict:
        """
        Holt Nextcloud-Server-Informationen

        Returns:
            {"version": "28.0.1", "storage_free": "10 GB", ...}
        """
        try:
            import requests
            from requests.auth import HTTPBasicAuth

            # Nextcloud OCS API
            ocs_url = urljoin(nextcloud_url, "/ocs/v1.php/cloud/capabilities")

            response = requests.get(
                ocs_url,
                auth=HTTPBasicAuth(user, password),
                headers={"OCS-APIRequest": "true"},
                params={"format": "json"},
                timeout=10,
            )

            if response.status_code == 200:
                data = response.json()
                # Parse capabilities
                return {"status": "ok", "data": data}

            return {"status": "error"}

        except Exception as e:
            logger.debug(f"Konnte Server-Info nicht abrufen: {e}")
            return {"status": "error"}
