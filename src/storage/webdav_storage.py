"""
WebDAV Storage-Backend
Für WebDAV-kompatible Server (Nextcloud, ownCloud, SharePoint, etc.)
"""

import logging
from pathlib import Path
from typing import Callable, List, Optional

from src.storage.base import StorageBackend

logger = logging.getLogger(__name__)


class WebDAVStorage(StorageBackend):
    """
    Storage-Backend für WebDAV-Server

    Unterstützt alle WebDAV-kompatiblen Server:
    - Nextcloud
    - ownCloud
    - SharePoint
    - Box.com
    - Andere WebDAV-Implementierungen
    """

    def __init__(
        self,
        url: str,
        username: str = "",
        password: str = "",
        base_path: str = "/",
        timeout: int = 30,
    ):
        """
        Initialisiert WebDAV-Storage

        Args:
            url: WebDAV-URL (z.B. https://nextcloud.example.com/remote.php/dav/files/username/)
            username: Benutzername (optional für öffentliche Shares)
            password: Passwort (optional für öffentliche Shares)
            base_path: Basis-Pfad auf dem Server (relativ zur URL)
            timeout: Timeout in Sekunden (Standard: 30)
        """
        self.url = url.rstrip("/")
        self.username = username
        self.password = password
        self.base_path = base_path.strip("/")
        self.timeout = timeout

        self.client = None

        logger.info(f"WebDAVStorage initialisiert: {url}")

    def connect(self) -> bool:
        """
        Stellt WebDAV-Verbindung her

        Returns:
            True bei Erfolg

        Raises:
            ConnectionError: Bei Verbindungsproblemen
            ImportError: Wenn webdavclient3 nicht installiert ist
        """
        try:
            from webdav3.client import Client
        except ImportError as e:
            raise ConnectionError(
                "webdavclient3 nicht installiert. " "Installiere mit: pip install webdavclient3"
            ) from e

        try:
            # WebDAV-Client-Optionen
            options = {
                "webdav_hostname": self.url,
                "webdav_timeout": self.timeout,
            }

            # Authentifizierung (falls vorhanden)
            if self.username:
                options["webdav_login"] = self.username
            if self.password:
                options["webdav_password"] = self.password

            # Client erstellen
            self.client = Client(options)

            # Teste Verbindung mit check auf Root
            if not self.client.check("/"):
                raise ConnectionError("WebDAV-Server antwortet nicht")

            # Erstelle Basis-Pfad falls nötig
            if self.base_path:
                self._ensure_directory_exists(self.base_path)

            logger.info(f"WebDAV-Verbindung hergestellt: {self.url}")
            return True

        except Exception as e:
            logger.error(f"WebDAV-Verbindung fehlgeschlagen: {e}")
            raise ConnectionError(f"WebDAV-Verbindung fehlgeschlagen: {e}") from e

    def disconnect(self) -> None:
        """Trennt WebDAV-Verbindung"""
        # webdavclient3 hat keine explizite disconnect-Methode
        self.client = None
        logger.info("WebDAV-Verbindung getrennt")

    def upload_file(
        self,
        local_path: Path,
        remote_path: str,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> bool:
        """
        Lädt Datei per WebDAV hoch

        Args:
            local_path: Lokale Quell-Datei
            remote_path: Relativer Ziel-Pfad
            progress_callback: Optional Progress-Callback

        Returns:
            True bei Erfolg
        """
        if not self.client:
            raise ConnectionError("Nicht verbunden. Rufe connect() auf.")

        if not local_path.exists():
            raise FileNotFoundError(f"Quell-Datei nicht gefunden: {local_path}")

        # Vollständiger Remote-Pfad
        full_remote_path = self._join_path(self.base_path, remote_path)

        # Stelle sicher, dass Remote-Verzeichnis existiert
        remote_dir = str(Path(full_remote_path).parent)
        self._ensure_directory_exists(remote_dir)

        try:
            # webdavclient3 upload_sync: (remote_path, local_path)
            self.client.upload_sync(
                remote_path=full_remote_path,
                local_path=str(local_path),
            )

            # Progress-Callback (webdavclient3 hat kein natives Progress-Tracking)
            if progress_callback:
                file_size = local_path.stat().st_size
                progress_callback(file_size, file_size)

            logger.info(f"Datei hochgeladen: {local_path.name} → {remote_path}")
            return True

        except Exception as e:
            logger.error(f"Fehler beim Upload: {e}")
            raise IOError(f"Upload fehlgeschlagen: {e}") from e

    def download_file(
        self,
        remote_path: str,
        local_path: Path,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> bool:
        """
        Lädt Datei per WebDAV herunter

        Args:
            remote_path: Relativer Quell-Pfad
            local_path: Lokaler Ziel-Pfad
            progress_callback: Optional Progress-Callback

        Returns:
            True bei Erfolg
        """
        if not self.client:
            raise ConnectionError("Nicht verbunden. Rufe connect() auf.")

        full_remote_path = self._join_path(self.base_path, remote_path)

        # Prüfe ob Remote-Datei existiert
        if not self.client.check(full_remote_path):
            raise FileNotFoundError(f"Remote-Datei nicht gefunden: {remote_path}")

        # Stelle sicher, dass lokales Verzeichnis existiert
        local_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            # webdavclient3 download_sync: (remote_path, local_path)
            self.client.download_sync(
                remote_path=full_remote_path,
                local_path=str(local_path),
            )

            # Progress-Callback
            if progress_callback:
                file_size = local_path.stat().st_size
                progress_callback(file_size, file_size)

            logger.info(f"Datei heruntergeladen: {remote_path} → {local_path.name}")
            return True

        except Exception as e:
            logger.error(f"Fehler beim Download: {e}")
            raise IOError(f"Download fehlgeschlagen: {e}") from e

    def list_files(self, remote_path: str) -> List[str]:
        """
        Listet Dateien im Remote-Verzeichnis auf

        Args:
            remote_path: Relativer Pfad zum Verzeichnis

        Returns:
            Liste von Dateinamen (ohne Unterverzeichnisse)
        """
        if not self.client:
            raise ConnectionError("Nicht verbunden. Rufe connect() auf.")

        full_remote_path = self._join_path(self.base_path, remote_path)

        try:
            # Liste alle Items
            all_items = self.client.list(full_remote_path)

            # Filter: Nur Dateien (nicht "." und Verzeichnisse)
            files = []
            for item in all_items:
                # Entferne trailing slash
                item_name = item.rstrip("/")

                # Skip "." (current directory)
                if item_name == "." or item_name == "":
                    continue

                # Prüfe ob Datei oder Verzeichnis
                item_full_path = f"{full_remote_path}/{item_name}"
                if not self.client.is_dir(item_full_path):
                    files.append(item_name)

            logger.debug(f"Dateien in {remote_path}: {len(files)}")
            return files

        except Exception as e:
            logger.error(f"Fehler beim Listing: {e}")
            raise IOError(f"Listing fehlgeschlagen: {e}") from e

    def delete_file(self, remote_path: str) -> bool:
        """
        Löscht Remote-Datei

        Args:
            remote_path: Relativer Pfad zur Datei

        Returns:
            True bei Erfolg
        """
        if not self.client:
            raise ConnectionError("Nicht verbunden. Rufe connect() auf.")

        full_remote_path = self._join_path(self.base_path, remote_path)

        try:
            if not self.client.check(full_remote_path):
                raise FileNotFoundError(f"Datei nicht gefunden: {remote_path}")

            self.client.clean(full_remote_path)
            logger.info(f"Datei gelöscht: {remote_path}")
            return True

        except FileNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Fehler beim Löschen: {e}")
            raise IOError(f"Löschen fehlgeschlagen: {e}") from e

    def delete_directory(self, remote_path: str, recursive: bool = False) -> bool:
        """
        Löscht Remote-Verzeichnis

        Args:
            remote_path: Relativer Pfad zum Verzeichnis
            recursive: Rekursiv löschen? (Standard: False)

        Returns:
            True bei Erfolg
        """
        if not self.client:
            raise ConnectionError("Nicht verbunden. Rufe connect() auf.")

        full_remote_path = self._join_path(self.base_path, remote_path)

        try:
            if not self.client.check(full_remote_path):
                raise FileNotFoundError(f"Verzeichnis nicht gefunden: {remote_path}")

            # webdavclient3.clean() löscht rekursiv
            self.client.clean(full_remote_path)
            logger.info(f"Verzeichnis gelöscht: {remote_path}")
            return True

        except FileNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Fehler beim Löschen: {e}")
            raise IOError(f"Löschen fehlgeschlagen: {e}") from e

    def create_directory(self, remote_path: str) -> bool:
        """
        Erstellt Remote-Verzeichnis

        Args:
            remote_path: Relativer Pfad zum Verzeichnis

        Returns:
            True bei Erfolg
        """
        if not self.client:
            raise ConnectionError("Nicht verbunden. Rufe connect() auf.")

        full_remote_path = self._join_path(self.base_path, remote_path)

        try:
            self._ensure_directory_exists(full_remote_path)
            logger.info(f"Verzeichnis erstellt: {remote_path}")
            return True

        except Exception as e:
            logger.error(f"Fehler beim Erstellen: {e}")
            raise IOError(f"Erstellen fehlgeschlagen: {e}") from e

    def exists(self, remote_path: str) -> bool:
        """
        Prüft ob Remote-Pfad existiert

        Args:
            remote_path: Relativer Pfad

        Returns:
            True wenn existiert
        """
        if not self.client:
            raise ConnectionError("Nicht verbunden. Rufe connect() auf.")

        full_remote_path = self._join_path(self.base_path, remote_path)

        try:
            return self.client.check(full_remote_path)
        except Exception:
            return False

    def get_available_space(self) -> int:
        """
        Gibt verfügbaren Speicherplatz zurück

        Returns:
            Verfügbarer Platz in Bytes, -1 wenn nicht verfügbar
        """
        if not self.client:
            raise ConnectionError("Nicht verbunden. Rufe connect() auf.")

        try:
            # webdavclient3.free() gibt verfügbaren Platz zurück
            space = self.client.free()
            return int(space) if space else -1

        except Exception as e:
            logger.warning(f"Speicherplatz-Abfrage fehlgeschlagen: {e}")
            return -1

    def test_connection(self) -> bool:
        """
        Testet WebDAV-Verbindung

        Returns:
            True wenn Verbindung OK
        """
        if not self.client:
            return False

        try:
            # Teste mit check auf Root
            return self.client.check("/")
        except Exception:
            return False

    def _join_path(self, base: str, relative: str) -> str:
        """
        Verbindet Basis-Pfad mit relativem Pfad

        Args:
            base: Basis-Pfad
            relative: Relativer Pfad

        Returns:
            Vollständiger Pfad
        """
        # Normalisiere Pfade
        base = base.strip("/")
        relative = relative.strip("/")

        if base and relative:
            return f"{base}/{relative}"
        elif base:
            return base
        elif relative:
            return relative
        else:
            return ""

    def _ensure_directory_exists(self, path: str) -> None:
        """
        Stellt sicher, dass Verzeichnis existiert (rekursiv)

        Args:
            path: Vollständiger Remote-Pfad
        """
        if not self.client:
            return

        # Normalisiere Pfad (WebDAV benötigt führenden Slash)
        path = "/" + path.strip("/")
        if path == "/":
            return

        # Prüfe ob existiert
        if self.client.check(path):
            return

        # Erstelle Parent-Verzeichnis zuerst (rekursiv)
        parent = str(Path(path).parent)
        if parent != "/" and parent != path:
            self._ensure_directory_exists(parent)

        # Erstelle Verzeichnis
        try:
            self.client.mkdir(path)
        except Exception as e:
            # Möglicherweise race condition, prüfe nochmal
            if not self.client.check(path):
                raise
