"""
SMB/CIFS Storage-Backend
Für Windows-Netzwerkfreigaben und NAS-Geräte
"""

import logging
import uuid
from pathlib import Path, PureWindowsPath
from typing import Callable, List, Optional

from src.storage.base import StorageBackend

logger = logging.getLogger(__name__)


class SMBStorage(StorageBackend):
    r"""
    Storage-Backend für SMB/CIFS-Netzwerkfreigaben

    Unterstützt:
    - Windows-Freigaben (\\server\share)
    - NAS-Geräte (Synology, QNAP, etc.)
    - Samba-Server (Linux)

    Verwendet smbprotocol für SMB2/SMB3-Unterstützung.
    """

    def __init__(
        self,
        server: str,
        share: str,
        username: str,
        password: str,
        domain: str = "",
        port: int = 445,
        base_path: str = "/",
    ):
        """
        Initialisiert SMB-Storage

        Args:
            server: Server-Name oder IP (z.B. "nas.local" oder "192.168.1.100")
            share: Freigabe-Name (z.B. "backups")
            username: Benutzername
            password: Passwort
            domain: Windows-Domain (optional)
            port: SMB-Port (Standard: 445)
            base_path: Basis-Pfad auf der Freigabe (z.B. "/scrat-backups")
        """
        self.server = server
        self.share = share
        self.username = username
        self.password = password
        self.domain = domain
        self.port = port
        self.base_path = base_path.strip("/")

        self.session = None
        self.tree = None

        logger.info(f"SMBStorage initialisiert: \\\\{server}\\{share}")

    def connect(self) -> bool:
        """
        Stellt SMB-Verbindung her

        Returns:
            True bei Erfolg

        Raises:
            ConnectionError: Bei Verbindungsproblemen
        """
        try:
            from smbprotocol.connection import Connection
            from smbprotocol.session import Session
            from smbprotocol.tree import TreeConnect

            # Verbindung zum Server
            self.connection = Connection(uuid.uuid4(), self.server, self.port)
            self.connection.connect()

            # Session erstellen
            self.session = Session(self.connection, self.username, self.password, self.domain)
            self.session.connect()

            # Tree Connect (Freigabe mounten)
            tree_path = f"\\\\{self.server}\\{self.share}"
            self.tree = TreeConnect(self.session, tree_path)
            self.tree.connect()

            # Teste Zugriff auf Basis-Pfad
            if self.base_path:
                self._ensure_directory_exists(self.base_path)

            logger.info(f"SMB-Verbindung hergestellt: \\\\{self.server}\\{self.share}")
            return True

        except ImportError:
            raise ConnectionError(
                "smbprotocol nicht installiert. Installiere mit: pip install smbprotocol"
            )
        except Exception as e:
            logger.error(f"SMB-Verbindungsfehler: {e}")
            raise ConnectionError(f"SMB-Verbindung fehlgeschlagen: {e}") from e

    def disconnect(self) -> None:
        """Trennt SMB-Verbindung"""
        if self.tree:
            self.tree.disconnect()
            self.tree = None

        if self.session:
            self.session.disconnect()
            self.session = None

        if self.connection:
            self.connection.disconnect()
            self.connection = None

        logger.info("SMB-Verbindung getrennt")

    def upload_file(
        self,
        local_path: Path,
        remote_path: str,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> bool:
        """
        Lädt Datei per SMB hoch

        Args:
            local_path: Lokale Quell-Datei
            remote_path: Relativer Ziel-Pfad
            progress_callback: Optional Progress-Callback

        Returns:
            True bei Erfolg
        """
        if not self.tree:
            raise ConnectionError("Nicht verbunden. Rufe connect() auf.")

        if not local_path.exists():
            raise FileNotFoundError(f"Quell-Datei nicht gefunden: {local_path}")

        # Vollständiger Remote-Pfad
        full_remote_path = self._join_path(self.base_path, remote_path)

        # Stelle sicher, dass Remote-Verzeichnis existiert
        remote_dir = str(PureWindowsPath(full_remote_path).parent)
        self._ensure_directory_exists(remote_dir)

        try:
            from smbprotocol.open import (
                CreateDisposition,
                CreateOptions,
                FileAttributes,
                FilePipePrinterAccessMask,
                ImpersonationLevel,
                Open,
                ShareAccess,
            )

            # Datei öffnen/erstellen
            file_open = Open(self.tree, full_remote_path)
            file_open.create(
                ImpersonationLevel.Impersonation,
                FilePipePrinterAccessMask.FILE_WRITE_DATA
                | FilePipePrinterAccessMask.FILE_APPEND_DATA,
                FileAttributes.FILE_ATTRIBUTE_NORMAL,
                ShareAccess.FILE_SHARE_READ,
                CreateDisposition.FILE_OVERWRITE_IF,
                CreateOptions.FILE_NON_DIRECTORY_FILE,
            )

            # Upload mit Progress-Tracking
            file_size = local_path.stat().st_size
            bytes_written = 0
            chunk_size = 1024 * 1024  # 1MB

            with open(local_path, "rb") as src_file:
                while True:
                    chunk = src_file.read(chunk_size)
                    if not chunk:
                        break

                    file_open.write(chunk, bytes_written)
                    bytes_written += len(chunk)

                    if progress_callback:
                        progress_callback(bytes_written, file_size)

            file_open.close()

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
        Lädt Datei per SMB herunter

        Args:
            remote_path: Relativer Quell-Pfad
            local_path: Lokaler Ziel-Pfad
            progress_callback: Optional Progress-Callback

        Returns:
            True bei Erfolg
        """
        if not self.tree:
            raise ConnectionError("Nicht verbunden. Rufe connect() auf.")

        full_remote_path = self._join_path(self.base_path, remote_path)

        try:
            from smbprotocol.open import (
                CreateDisposition,
                CreateOptions,
                FileAttributes,
                FilePipePrinterAccessMask,
                ImpersonationLevel,
                Open,
                ShareAccess,
            )

            # Datei öffnen
            file_open = Open(self.tree, full_remote_path)
            file_open.create(
                ImpersonationLevel.Impersonation,
                FilePipePrinterAccessMask.FILE_READ_DATA,
                FileAttributes.FILE_ATTRIBUTE_NORMAL,
                ShareAccess.FILE_SHARE_READ,
                CreateDisposition.FILE_OPEN,
                CreateOptions.FILE_NON_DIRECTORY_FILE,
            )

            # Hole Datei-Größe
            file_info = file_open.query_info()
            file_size = file_info["end_of_file"].get_value()

            # Stelle sicher, dass lokales Verzeichnis existiert
            local_path.parent.mkdir(parents=True, exist_ok=True)

            # Download mit Progress-Tracking
            bytes_read = 0
            chunk_size = 1024 * 1024  # 1MB

            with open(local_path, "wb") as dest_file:
                while bytes_read < file_size:
                    chunk = file_open.read(bytes_read, chunk_size)
                    if not chunk:
                        break

                    dest_file.write(chunk)
                    bytes_read += len(chunk)

                    if progress_callback:
                        progress_callback(bytes_read, file_size)

            file_open.close()

            logger.info(f"Datei heruntergeladen: {remote_path} → {local_path.name}")
            return True

        except FileNotFoundError:
            raise FileNotFoundError(f"Remote-Datei nicht gefunden: {remote_path}")
        except Exception as e:
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
        if not self.tree:
            raise ConnectionError("Nicht verbunden. Rufe connect() auf.")

        full_remote_path = self._join_path(self.base_path, remote_path)

        try:
            from smbprotocol.open import (
                CreateDisposition,
                CreateOptions,
                FileAttributes,
                FilePipePrinterAccessMask,
                ImpersonationLevel,
                Open,
                ShareAccess,
            )

            # Verzeichnis öffnen
            dir_open = Open(self.tree, full_remote_path)
            dir_open.create(
                ImpersonationLevel.Impersonation,
                FilePipePrinterAccessMask.FILE_LIST_DIRECTORY,
                FileAttributes.FILE_ATTRIBUTE_DIRECTORY,
                ShareAccess.FILE_SHARE_READ,
                CreateDisposition.FILE_OPEN,
                CreateOptions.FILE_DIRECTORY_FILE,
            )

            # Liste Dateien
            files = []
            for entry in dir_open.query_directory("*"):
                # Überspringe . und ..
                if entry["file_name"].get_value() in [".", ".."]:
                    continue

                # Nur Dateien (keine Verzeichnisse)
                attrs = entry["file_attributes"].get_value()
                if not (attrs & FileAttributes.FILE_ATTRIBUTE_DIRECTORY):
                    files.append(entry["file_name"].get_value())

            dir_open.close()

            logger.debug(f"Dateien in {remote_path}: {len(files)}")
            return files

        except FileNotFoundError:
            raise FileNotFoundError(f"Verzeichnis nicht gefunden: {remote_path}")
        except Exception as e:
            raise IOError(f"Listing fehlgeschlagen: {e}") from e

    def delete_file(self, remote_path: str) -> bool:
        """
        Löscht Remote-Datei

        Args:
            remote_path: Relativer Pfad zur Datei

        Returns:
            True bei Erfolg
        """
        if not self.tree:
            raise ConnectionError("Nicht verbunden. Rufe connect() auf.")

        full_remote_path = self._join_path(self.base_path, remote_path)

        try:
            from smbprotocol.open import (
                CreateDisposition,
                CreateOptions,
                FileAttributes,
                FilePipePrinterAccessMask,
                ImpersonationLevel,
                Open,
                ShareAccess,
            )

            # Datei öffnen mit DELETE-Berechtigung
            file_open = Open(self.tree, full_remote_path)
            file_open.create(
                ImpersonationLevel.Impersonation,
                FilePipePrinterAccessMask.DELETE,
                FileAttributes.FILE_ATTRIBUTE_NORMAL,
                ShareAccess.FILE_SHARE_DELETE,
                CreateDisposition.FILE_OPEN,
                CreateOptions.FILE_NON_DIRECTORY_FILE | CreateOptions.FILE_DELETE_ON_CLOSE,
            )

            file_open.close()  # DELETE_ON_CLOSE löscht beim Schließen

            logger.info(f"Datei gelöscht: {remote_path}")
            return True

        except FileNotFoundError:
            raise FileNotFoundError(f"Datei nicht gefunden: {remote_path}")
        except Exception as e:
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
        if not self.tree:
            raise ConnectionError("Nicht verbunden. Rufe connect() auf.")

        full_remote_path = self._join_path(self.base_path, remote_path)

        try:
            if recursive:
                self._rmtree(full_remote_path)
            else:
                from smbprotocol.open import (
                    CreateDisposition,
                    CreateOptions,
                    FileAttributes,
                    FilePipePrinterAccessMask,
                    ImpersonationLevel,
                    Open,
                    ShareAccess,
                )

                # Verzeichnis öffnen mit DELETE-Berechtigung
                dir_open = Open(self.tree, full_remote_path)
                dir_open.create(
                    ImpersonationLevel.Impersonation,
                    FilePipePrinterAccessMask.DELETE,
                    FileAttributes.FILE_ATTRIBUTE_DIRECTORY,
                    ShareAccess.FILE_SHARE_DELETE,
                    CreateDisposition.FILE_OPEN,
                    CreateOptions.FILE_DIRECTORY_FILE | CreateOptions.FILE_DELETE_ON_CLOSE,
                )

                dir_open.close()

            logger.info(f"Verzeichnis gelöscht: {remote_path}")
            return True

        except FileNotFoundError:
            raise FileNotFoundError(f"Verzeichnis nicht gefunden: {remote_path}")
        except Exception as e:
            raise IOError(f"Löschen fehlgeschlagen: {e}") from e

    def create_directory(self, remote_path: str) -> bool:
        """
        Erstellt Remote-Verzeichnis

        Args:
            remote_path: Relativer Pfad zum Verzeichnis

        Returns:
            True bei Erfolg
        """
        if not self.tree:
            raise ConnectionError("Nicht verbunden. Rufe connect() auf.")

        full_remote_path = self._join_path(self.base_path, remote_path)

        try:
            self._ensure_directory_exists(full_remote_path)
            logger.info(f"Verzeichnis erstellt: {remote_path}")
            return True

        except Exception as e:
            raise IOError(f"Erstellen fehlgeschlagen: {e}") from e

    def exists(self, remote_path: str) -> bool:
        """
        Prüft ob Remote-Pfad existiert

        Args:
            remote_path: Relativer Pfad

        Returns:
            True wenn existiert
        """
        if not self.tree:
            raise ConnectionError("Nicht verbunden. Rufe connect() auf.")

        full_remote_path = self._join_path(self.base_path, remote_path)

        try:
            from smbprotocol.open import (
                CreateDisposition,
                CreateOptions,
                FileAttributes,
                FilePipePrinterAccessMask,
                ImpersonationLevel,
                Open,
                ShareAccess,
            )

            file_open = Open(self.tree, full_remote_path)
            file_open.create(
                ImpersonationLevel.Impersonation,
                FilePipePrinterAccessMask.FILE_READ_ATTRIBUTES,
                FileAttributes.FILE_ATTRIBUTE_NORMAL,
                ShareAccess.FILE_SHARE_READ,
                CreateDisposition.FILE_OPEN,
                CreateOptions.FILE_NON_DIRECTORY_FILE,
            )
            file_open.close()
            return True

        except FileNotFoundError:
            return False
        except Exception:
            return False

    def get_available_space(self) -> int:
        """
        Gibt verfügbaren Speicherplatz zurück

        Returns:
            Verfügbarer Platz in Bytes, -1 wenn nicht verfügbar
        """
        if not self.tree:
            raise ConnectionError("Nicht verbunden. Rufe connect() auf.")

        try:
            # Hole Freigabe-Informationen
            info = self.tree.query_fs_info()
            # TotalFreeBytes
            return info.get("total_free_bytes", -1)

        except Exception:
            logger.warning("Speicherplatz-Abfrage nicht verfügbar")
            return -1

    def test_connection(self) -> bool:
        """
        Testet SMB-Verbindung

        Returns:
            True wenn Verbindung OK
        """
        if not self.tree:
            return False

        try:
            # Teste mit Query auf Root
            self.tree.query_fs_info()
            return True
        except Exception:
            return False

    def _join_path(self, base: str, relative: str) -> str:
        """
        Verbindet Basis-Pfad mit relativem Pfad (Windows-Style)

        Args:
            base: Basis-Pfad
            relative: Relativer Pfad

        Returns:
            Vollständiger Pfad
        """
        # Nutze PureWindowsPath für konsistente Pfade
        if base:
            return str(PureWindowsPath(base) / relative)
        return relative

    def _ensure_directory_exists(self, path: str) -> None:
        """
        Stellt sicher, dass Verzeichnis existiert (rekursiv)

        Args:
            path: Vollständiger Pfad
        """
        from smbprotocol.open import (
            CreateDisposition,
            CreateOptions,
            FileAttributes,
            FilePipePrinterAccessMask,
            ImpersonationLevel,
            Open,
            ShareAccess,
        )

        # Prüfe ob existiert
        try:
            dir_open = Open(self.tree, path)
            dir_open.create(
                ImpersonationLevel.Impersonation,
                FilePipePrinterAccessMask.FILE_READ_ATTRIBUTES,
                FileAttributes.FILE_ATTRIBUTE_DIRECTORY,
                ShareAccess.FILE_SHARE_READ,
                CreateDisposition.FILE_OPEN,
                CreateOptions.FILE_DIRECTORY_FILE,
            )
            dir_open.close()
            return  # Existiert bereits

        except FileNotFoundError:
            pass

        # Erstelle Parent-Verzeichnis zuerst
        parent = str(PureWindowsPath(path).parent)
        if parent != path and parent != ".":
            self._ensure_directory_exists(parent)

        # Erstelle Verzeichnis
        try:
            dir_open = Open(self.tree, path)
            dir_open.create(
                ImpersonationLevel.Impersonation,
                FilePipePrinterAccessMask.FILE_READ_ATTRIBUTES,
                FileAttributes.FILE_ATTRIBUTE_DIRECTORY,
                ShareAccess.FILE_SHARE_READ,
                CreateDisposition.FILE_CREATE,
                CreateOptions.FILE_DIRECTORY_FILE,
            )
            dir_open.close()

        except Exception:
            # Möglicherweise race condition, prüfe nochmal
            try:
                dir_open = Open(self.tree, path)
                dir_open.create(
                    ImpersonationLevel.Impersonation,
                    FilePipePrinterAccessMask.FILE_READ_ATTRIBUTES,
                    FileAttributes.FILE_ATTRIBUTE_DIRECTORY,
                    ShareAccess.FILE_SHARE_READ,
                    CreateDisposition.FILE_OPEN,
                    CreateOptions.FILE_DIRECTORY_FILE,
                )
                dir_open.close()
            except FileNotFoundError:
                raise

    def _rmtree(self, path: str) -> None:
        """
        Löscht Verzeichnis rekursiv

        Args:
            path: Vollständiger Pfad
        """
        from smbprotocol.open import (
            CreateDisposition,
            CreateOptions,
            FileAttributes,
            FilePipePrinterAccessMask,
            ImpersonationLevel,
            Open,
            ShareAccess,
        )

        # Öffne Verzeichnis
        dir_open = Open(self.tree, path)
        dir_open.create(
            ImpersonationLevel.Impersonation,
            FilePipePrinterAccessMask.FILE_LIST_DIRECTORY | FilePipePrinterAccessMask.DELETE,
            FileAttributes.FILE_ATTRIBUTE_DIRECTORY,
            ShareAccess.FILE_SHARE_READ | ShareAccess.FILE_SHARE_DELETE,
            CreateDisposition.FILE_OPEN,
            CreateOptions.FILE_DIRECTORY_FILE,
        )

        # Liste alle Einträge
        for entry in dir_open.query_directory("*"):
            name = entry["file_name"].get_value()
            if name in [".", ".."]:
                continue

            item_path = str(PureWindowsPath(path) / name)
            attrs = entry["file_attributes"].get_value()

            if attrs & FileAttributes.FILE_ATTRIBUTE_DIRECTORY:
                # Rekursiv löschen
                self._rmtree(item_path)
            else:
                # Datei löschen
                self.delete_file(item_path.replace(self.base_path + "\\", ""))

        dir_open.close()

        # Lösche leeres Verzeichnis
        self.delete_directory(path.replace(self.base_path + "\\", ""), recursive=False)
