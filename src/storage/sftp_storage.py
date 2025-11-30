"""
SFTP Storage-Backend
Für SSH File Transfer Protocol
"""

import logging
from pathlib import Path
from typing import Callable, List, Optional

import paramiko
from paramiko.sftp_client import SFTPClient
from paramiko.ssh_exception import AuthenticationException, SSHException

from src.storage.base import StorageBackend

logger = logging.getLogger(__name__)


class SFTPStorage(StorageBackend):
    """
    Storage-Backend für SFTP (SSH File Transfer Protocol)

    Unterstützt Passwort- und SSH-Key-Authentifizierung.
    """

    def __init__(
        self,
        host: str,
        port: int = 22,
        username: str = "",
        password: Optional[str] = None,
        key_file: Optional[Path] = None,
        base_path: str = "/",
    ):
        """
        Initialisiert SFTP-Storage

        Args:
            host: Hostname oder IP
            port: SSH-Port (Standard: 22)
            username: Benutzername
            password: Passwort (optional, wenn key_file verwendet wird)
            key_file: Pfad zum SSH-Private-Key (optional)
            base_path: Basis-Pfad auf dem Server
        """
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.key_file = key_file
        self.base_path = base_path

        self.ssh_client: Optional[paramiko.SSHClient] = None
        self.sftp_client: Optional[SFTPClient] = None

        logger.info(f"SFTPStorage initialisiert: {username}@{host}:{port}")

    def connect(self) -> bool:
        """
        Stellt SFTP-Verbindung her

        Returns:
            True bei Erfolg

        Raises:
            ConnectionError: Bei Verbindungsproblemen
            AuthenticationException: Bei Auth-Fehler
        """
        try:
            # SSH-Client erstellen
            self.ssh_client = paramiko.SSHClient()

            # Auto-Add Host Keys (WARNUNG: Unsicher für Production)
            # TODO: Implement proper host key verification
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            # Verbinde
            connect_kwargs = {
                "hostname": self.host,
                "port": self.port,
                "username": self.username,
            }

            if self.key_file:
                # SSH-Key-Authentifizierung
                connect_kwargs["key_filename"] = str(self.key_file)
                logger.info(f"Verbinde mit SSH-Key: {self.key_file}")
            elif self.password:
                # Passwort-Authentifizierung
                connect_kwargs["password"] = self.password
                logger.info("Verbinde mit Passwort")
            else:
                raise ConnectionError("Weder Passwort noch SSH-Key angegeben")

            self.ssh_client.connect(**connect_kwargs)

            # SFTP-Client öffnen
            self.sftp_client = self.ssh_client.open_sftp()

            # Teste Basis-Pfad
            try:
                self.sftp_client.stat(self.base_path)
            except FileNotFoundError:
                # Erstelle Basis-Pfad
                self._create_remote_directory(self.base_path)

            logger.info(f"SFTP-Verbindung hergestellt: {self.username}@{self.host}")
            return True

        except AuthenticationException as e:
            logger.error(f"Authentifizierung fehlgeschlagen: {e}")
            raise ConnectionError(f"Authentifizierung fehlgeschlagen: {e}") from e

        except SSHException as e:
            logger.error(f"SSH-Fehler: {e}")
            raise ConnectionError(f"SSH-Fehler: {e}") from e

        except Exception as e:
            logger.error(f"Verbindungsfehler: {e}")
            raise ConnectionError(f"Verbindung fehlgeschlagen: {e}") from e

    def disconnect(self) -> None:
        """Trennt SFTP-Verbindung"""
        if self.sftp_client:
            self.sftp_client.close()
            self.sftp_client = None

        if self.ssh_client:
            self.ssh_client.close()
            self.ssh_client = None

        logger.info("SFTP-Verbindung getrennt")

    def upload_file(
        self,
        local_path: Path,
        remote_path: str,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> bool:
        """
        Lädt Datei per SFTP hoch

        Args:
            local_path: Lokale Quell-Datei
            remote_path: Relativer Ziel-Pfad
            progress_callback: Optional Progress-Callback

        Returns:
            True bei Erfolg
        """
        if not self.sftp_client:
            raise ConnectionError("Nicht verbunden. Rufe connect() auf.")

        if not local_path.exists():
            raise FileNotFoundError(f"Quell-Datei nicht gefunden: {local_path}")

        # Vollständiger Remote-Pfad
        full_remote_path = self._join_path(self.base_path, remote_path)

        # Stelle sicher, dass Remote-Verzeichnis existiert
        remote_dir = str(Path(full_remote_path).parent)
        self._create_remote_directory(remote_dir)

        try:
            if progress_callback:
                # Upload mit Progress-Tracking
                def sftp_callback(bytes_transferred, total_bytes):
                    progress_callback(bytes_transferred, total_bytes)

                self.sftp_client.put(str(local_path), full_remote_path, callback=sftp_callback)
            else:
                # Direkter Upload
                self.sftp_client.put(str(local_path), full_remote_path)

            logger.info(f"Datei hochgeladen: {local_path.name} → {remote_path}")
            return True

        except (IOError, OSError) as e:
            logger.error(f"Fehler beim Upload: {e}")
            raise IOError(f"Upload fehlgeschlagen: {e}") from e

    def download_file(
        self,
        remote_path: str,
        local_path: Path,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> bool:
        """
        Lädt Datei per SFTP herunter

        Args:
            remote_path: Relativer Quell-Pfad
            local_path: Lokaler Ziel-Pfad
            progress_callback: Optional Progress-Callback

        Returns:
            True bei Erfolg
        """
        if not self.sftp_client:
            raise ConnectionError("Nicht verbunden. Rufe connect() auf.")

        full_remote_path = self._join_path(self.base_path, remote_path)

        # Prüfe ob Remote-Datei existiert
        try:
            self.sftp_client.stat(full_remote_path)
        except FileNotFoundError:
            raise FileNotFoundError(f"Remote-Datei nicht gefunden: {remote_path}")

        # Stelle sicher, dass lokales Verzeichnis existiert
        local_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            if progress_callback:

                def sftp_callback(bytes_transferred, total_bytes):
                    progress_callback(bytes_transferred, total_bytes)

                self.sftp_client.get(full_remote_path, str(local_path), callback=sftp_callback)
            else:
                self.sftp_client.get(full_remote_path, str(local_path))

            logger.info(f"Datei heruntergeladen: {remote_path} → {local_path.name}")
            return True

        except (IOError, OSError) as e:
            logger.error(f"Fehler beim Download: {e}")
            raise IOError(f"Download fehlgeschlagen: {e}") from e

    def list_files(self, remote_path: str) -> List[str]:
        """
        Listet Dateien im Remote-Verzeichnis auf

        Args:
            remote_path: Relativer Pfad zum Verzeichnis

        Returns:
            Liste von Dateinamen
        """
        if not self.sftp_client:
            raise ConnectionError("Nicht verbunden. Rufe connect() auf.")

        full_remote_path = self._join_path(self.base_path, remote_path)

        try:
            # Liste nur Dateien (keine Verzeichnisse)
            all_items = self.sftp_client.listdir_attr(full_remote_path)
            files = [item.filename for item in all_items if not self._is_directory(item)]

            logger.debug(f"Dateien in {remote_path}: {len(files)}")
            return files

        except FileNotFoundError:
            raise FileNotFoundError(f"Verzeichnis nicht gefunden: {remote_path}")
        except (IOError, OSError) as e:
            raise IOError(f"Listing fehlgeschlagen: {e}") from e

    def delete_file(self, remote_path: str) -> bool:
        """
        Löscht Remote-Datei

        Args:
            remote_path: Relativer Pfad zur Datei

        Returns:
            True bei Erfolg
        """
        if not self.sftp_client:
            raise ConnectionError("Nicht verbunden. Rufe connect() auf.")

        full_remote_path = self._join_path(self.base_path, remote_path)

        try:
            self.sftp_client.remove(full_remote_path)
            logger.info(f"Datei gelöscht: {remote_path}")
            return True

        except FileNotFoundError:
            raise FileNotFoundError(f"Datei nicht gefunden: {remote_path}")
        except (IOError, OSError) as e:
            raise IOError(f"Löschen fehlgeschlagen: {e}") from e

    def delete_directory(self, remote_path: str, recursive: bool = False) -> bool:
        """
        Löscht Remote-Verzeichnis

        Args:
            remote_path: Relativer Pfad zum Verzeichnis
            recursive: Rekursiv löschen?

        Returns:
            True bei Erfolg
        """
        if not self.sftp_client:
            raise ConnectionError("Nicht verbunden. Rufe connect() auf.")

        full_remote_path = self._join_path(self.base_path, remote_path)

        try:
            if recursive:
                self._rmtree(full_remote_path)
            else:
                self.sftp_client.rmdir(full_remote_path)

            logger.info(f"Verzeichnis gelöscht: {remote_path}")
            return True

        except FileNotFoundError:
            raise FileNotFoundError(f"Verzeichnis nicht gefunden: {remote_path}")
        except (IOError, OSError) as e:
            raise IOError(f"Löschen fehlgeschlagen: {e}") from e

    def create_directory(self, remote_path: str) -> bool:
        """
        Erstellt Remote-Verzeichnis

        Args:
            remote_path: Relativer Pfad zum Verzeichnis

        Returns:
            True bei Erfolg
        """
        if not self.sftp_client:
            raise ConnectionError("Nicht verbunden. Rufe connect() auf.")

        full_remote_path = self._join_path(self.base_path, remote_path)

        try:
            self._create_remote_directory(full_remote_path)
            logger.info(f"Verzeichnis erstellt: {remote_path}")
            return True

        except (IOError, OSError) as e:
            raise IOError(f"Erstellen fehlgeschlagen: {e}") from e

    def exists(self, remote_path: str) -> bool:
        """
        Prüft ob Remote-Pfad existiert

        Args:
            remote_path: Relativer Pfad

        Returns:
            True wenn existiert
        """
        if not self.sftp_client:
            raise ConnectionError("Nicht verbunden. Rufe connect() auf.")

        full_remote_path = self._join_path(self.base_path, remote_path)

        try:
            self.sftp_client.stat(full_remote_path)
            return True
        except FileNotFoundError:
            return False

    def get_available_space(self) -> int:
        """
        Gibt verfügbaren Speicherplatz zurück

        Returns:
            Verfügbarer Platz in Bytes, -1 wenn nicht verfügbar
        """
        if not self.sftp_client:
            raise ConnectionError("Nicht verbunden. Rufe connect() auf.")

        try:
            # SFTP hat keine Standard-Methode für Speicherplatz
            # Verwende statvfs wenn verfügbar (Linux/Unix)
            stat = self.sftp_client.statvfs(self.base_path)
            # f_bavail * f_frsize = verfügbare Bytes
            return stat.f_bavail * stat.f_frsize

        except (AttributeError, IOError, OSError):
            # statvfs nicht verfügbar
            logger.warning("statvfs nicht verfügbar, kann Speicherplatz nicht ermitteln")
            return -1

    def test_connection(self) -> bool:
        """
        Testet SFTP-Verbindung

        Returns:
            True wenn Verbindung OK
        """
        if not self.sftp_client:
            return False

        try:
            # Teste mit stat auf base_path
            self.sftp_client.stat(self.base_path)
            return True
        except Exception:
            return False

    def _join_path(self, base: str, relative: str) -> str:
        """
        Verbindet Basis-Pfad mit relativem Pfad (Unix-Style)

        Args:
            base: Basis-Pfad
            relative: Relativer Pfad

        Returns:
            Vollständiger Pfad
        """
        # Normalisiere Pfade (Unix-Style)
        base = base.rstrip("/")
        relative = relative.lstrip("/")
        return f"{base}/{relative}"

    def _is_directory(self, attr) -> bool:
        """
        Prüft ob SFTPAttributes ein Verzeichnis ist

        Args:
            attr: SFTPAttributes

        Returns:
            True wenn Verzeichnis
        """
        import stat

        return stat.S_ISDIR(attr.st_mode)

    def _create_remote_directory(self, path: str) -> None:
        """
        Erstellt Remote-Verzeichnis rekursiv

        Args:
            path: Vollständiger Remote-Pfad
        """
        if not self.sftp_client:
            return

        # Prüfe ob existiert
        try:
            self.sftp_client.stat(path)
            return  # Existiert bereits
        except FileNotFoundError:
            pass

        # Erstelle Parent-Verzeichnis zuerst
        parent = str(Path(path).parent)
        if parent != "/" and parent != path:
            self._create_remote_directory(parent)

        # Erstelle Verzeichnis
        try:
            self.sftp_client.mkdir(path)
        except (IOError, OSError):
            # Möglicherweise race condition, prüfe nochmal
            try:
                self.sftp_client.stat(path)
            except FileNotFoundError:
                raise

    def _rmtree(self, path: str) -> None:
        """
        Löscht Verzeichnis rekursiv (wie shutil.rmtree)

        Args:
            path: Vollständiger Remote-Pfad
        """
        if not self.sftp_client:
            return

        # Liste alle Einträge
        for item in self.sftp_client.listdir_attr(path):
            item_path = f"{path}/{item.filename}"

            if self._is_directory(item):
                # Rekursiv löschen
                self._rmtree(item_path)
            else:
                # Datei löschen
                self.sftp_client.remove(item_path)

        # Leeres Verzeichnis löschen
        self.sftp_client.rmdir(path)
