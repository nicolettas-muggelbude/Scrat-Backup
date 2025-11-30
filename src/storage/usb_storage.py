"""
USB/Lokales Storage-Backend
Für lokale Laufwerke und USB-Sticks
"""

import logging
import shutil
from pathlib import Path
from typing import Callable, List, Optional

from src.storage.base import StorageBackend

logger = logging.getLogger(__name__)


class USBStorage(StorageBackend):
    """
    Storage-Backend für lokale Laufwerke und USB-Sticks

    Verwendet direkte Dateisystem-Operationen für maximale Performance.
    """

    def __init__(self, base_path: Path):
        """
        Initialisiert USB-Storage

        Args:
            base_path: Basis-Pfad auf dem Laufwerk (z.B. D:\\Backups oder /mnt/usb/backups)
        """
        self.base_path = Path(base_path)
        self.connected = False

        logger.info(f"USBStorage initialisiert: {self.base_path}")

    def connect(self) -> bool:
        """
        Stellt Verbindung her (prüft ob Pfad verfügbar ist)

        Returns:
            True bei Erfolg

        Raises:
            ConnectionError: Wenn Laufwerk nicht verfügbar
        """
        if not self.base_path.exists():
            raise ConnectionError(
                f"Basis-Pfad nicht verfügbar: {self.base_path}. "
                f"Ist das Laufwerk/USB-Stick angeschlossen?"
            )

        if not self.base_path.is_dir():
            raise ConnectionError(f"Basis-Pfad ist kein Verzeichnis: {self.base_path}")

        # Teste Schreibrechte
        test_file = self.base_path / ".scrat_write_test"
        try:
            test_file.write_text("test")
            test_file.unlink()
        except (PermissionError, OSError) as e:
            raise ConnectionError(f"Keine Schreibrechte auf {self.base_path}: {e}")

        self.connected = True
        logger.info(f"Verbindung hergestellt: {self.base_path}")
        return True

    def disconnect(self) -> None:
        """Trennt Verbindung (Cleanup)"""
        self.connected = False
        logger.info("Verbindung getrennt")

    def upload_file(
        self,
        local_path: Path,
        remote_path: str,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> bool:
        """
        Kopiert Datei zum Ziel

        Args:
            local_path: Lokale Quell-Datei
            remote_path: Relativer Ziel-Pfad
            progress_callback: Optional Progress-Callback

        Returns:
            True bei Erfolg
        """
        if not self.connected:
            raise ConnectionError("Nicht verbunden. Rufe connect() auf.")

        if not local_path.exists():
            raise FileNotFoundError(f"Quell-Datei nicht gefunden: {local_path}")

        # Ziel-Pfad konstruieren
        dest_path = self.base_path / remote_path

        # Stelle sicher, dass Ziel-Verzeichnis existiert
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        # Kopiere Datei
        try:
            if progress_callback:
                # Kopiere mit Progress-Tracking
                self._copy_with_progress(local_path, dest_path, progress_callback)
            else:
                # Direkte Kopie (schneller)
                shutil.copy2(local_path, dest_path)

            logger.info(f"Datei hochgeladen: {local_path.name} → {remote_path}")
            return True

        except (OSError, IOError) as e:
            logger.error(f"Fehler beim Upload: {e}")
            raise IOError(f"Upload fehlgeschlagen: {e}") from e

    def download_file(
        self,
        remote_path: str,
        local_path: Path,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> bool:
        """
        Kopiert Datei vom Ziel

        Args:
            remote_path: Relativer Quell-Pfad
            local_path: Lokaler Ziel-Pfad
            progress_callback: Optional Progress-Callback

        Returns:
            True bei Erfolg
        """
        if not self.connected:
            raise ConnectionError("Nicht verbunden. Rufe connect() auf.")

        # Quell-Pfad konstruieren
        source_path = self.base_path / remote_path

        if not source_path.exists():
            raise FileNotFoundError(f"Remote-Datei nicht gefunden: {remote_path}")

        # Stelle sicher, dass Ziel-Verzeichnis existiert
        local_path.parent.mkdir(parents=True, exist_ok=True)

        # Kopiere Datei
        try:
            if progress_callback:
                self._copy_with_progress(source_path, local_path, progress_callback)
            else:
                shutil.copy2(source_path, local_path)

            logger.info(f"Datei heruntergeladen: {remote_path} → {local_path.name}")
            return True

        except (OSError, IOError) as e:
            logger.error(f"Fehler beim Download: {e}")
            raise IOError(f"Download fehlgeschlagen: {e}") from e

    def list_files(self, remote_path: str) -> List[str]:
        """
        Listet Dateien im Verzeichnis auf

        Args:
            remote_path: Relativer Pfad zum Verzeichnis

        Returns:
            Liste von Dateinamen
        """
        if not self.connected:
            raise ConnectionError("Nicht verbunden. Rufe connect() auf.")

        dir_path = self.base_path / remote_path

        if not dir_path.exists():
            raise FileNotFoundError(f"Verzeichnis nicht gefunden: {remote_path}")

        if not dir_path.is_dir():
            raise IOError(f"Pfad ist kein Verzeichnis: {remote_path}")

        # Liste nur Dateien (keine Verzeichnisse)
        files = [f.name for f in dir_path.iterdir() if f.is_file()]

        logger.debug(f"Dateien in {remote_path}: {len(files)}")
        return files

    def delete_file(self, remote_path: str) -> bool:
        """
        Löscht Datei

        Args:
            remote_path: Relativer Pfad zur Datei

        Returns:
            True bei Erfolg
        """
        if not self.connected:
            raise ConnectionError("Nicht verbunden. Rufe connect() auf.")

        file_path = self.base_path / remote_path

        if not file_path.exists():
            raise FileNotFoundError(f"Datei nicht gefunden: {remote_path}")

        if not file_path.is_file():
            raise IOError(f"Pfad ist keine Datei: {remote_path}")

        try:
            file_path.unlink()
            logger.info(f"Datei gelöscht: {remote_path}")
            return True

        except (OSError, IOError) as e:
            logger.error(f"Fehler beim Löschen: {e}")
            raise IOError(f"Löschen fehlgeschlagen: {e}") from e

    def delete_directory(self, remote_path: str, recursive: bool = False) -> bool:
        """
        Löscht Verzeichnis

        Args:
            remote_path: Relativer Pfad zum Verzeichnis
            recursive: Rekursiv löschen?

        Returns:
            True bei Erfolg
        """
        if not self.connected:
            raise ConnectionError("Nicht verbunden. Rufe connect() auf.")

        dir_path = self.base_path / remote_path

        if not dir_path.exists():
            raise FileNotFoundError(f"Verzeichnis nicht gefunden: {remote_path}")

        if not dir_path.is_dir():
            raise IOError(f"Pfad ist kein Verzeichnis: {remote_path}")

        try:
            if recursive:
                shutil.rmtree(dir_path)
            else:
                dir_path.rmdir()  # Nur leere Verzeichnisse

            logger.info(f"Verzeichnis gelöscht: {remote_path}")
            return True

        except (OSError, IOError) as e:
            logger.error(f"Fehler beim Löschen: {e}")
            raise IOError(f"Löschen fehlgeschlagen: {e}") from e

    def create_directory(self, remote_path: str) -> bool:
        """
        Erstellt Verzeichnis

        Args:
            remote_path: Relativer Pfad zum Verzeichnis

        Returns:
            True bei Erfolg
        """
        if not self.connected:
            raise ConnectionError("Nicht verbunden. Rufe connect() auf.")

        dir_path = self.base_path / remote_path

        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Verzeichnis erstellt: {remote_path}")
            return True

        except (OSError, IOError) as e:
            logger.error(f"Fehler beim Erstellen: {e}")
            raise IOError(f"Erstellen fehlgeschlagen: {e}") from e

    def exists(self, remote_path: str) -> bool:
        """
        Prüft ob Pfad existiert

        Args:
            remote_path: Relativer Pfad

        Returns:
            True wenn existiert
        """
        if not self.connected:
            raise ConnectionError("Nicht verbunden. Rufe connect() auf.")

        path = self.base_path / remote_path
        return path.exists()

    def get_available_space(self) -> int:
        """
        Gibt verfügbaren Speicherplatz zurück

        Returns:
            Verfügbarer Platz in Bytes
        """
        if not self.connected:
            raise ConnectionError("Nicht verbunden. Rufe connect() auf.")

        try:
            stat = shutil.disk_usage(self.base_path)
            return stat.free

        except (OSError, IOError) as e:
            logger.error(f"Fehler beim Abrufen von Speicherplatz: {e}")
            return -1

    def test_connection(self) -> bool:
        """
        Testet Verbindung

        Returns:
            True wenn Verbindung OK
        """
        try:
            return self.base_path.exists() and self.base_path.is_dir()
        except Exception:
            return False

    def _copy_with_progress(
        self, source: Path, dest: Path, progress_callback: Callable[[int, int], None]
    ) -> None:
        """
        Kopiert Datei mit Progress-Tracking

        Args:
            source: Quell-Datei
            dest: Ziel-Datei
            progress_callback: Callback(bytes_transferred, total_bytes)
        """
        file_size = source.stat().st_size
        bytes_copied = 0
        chunk_size = 1024 * 1024  # 1MB Chunks

        with open(source, "rb") as src_file:
            with open(dest, "wb") as dest_file:
                while True:
                    chunk = src_file.read(chunk_size)
                    if not chunk:
                        break

                    dest_file.write(chunk)
                    bytes_copied += len(chunk)

                    # Progress-Callback
                    progress_callback(bytes_copied, file_size)

        # Kopiere Metadaten (Timestamps, etc.)
        shutil.copystat(source, dest)
