"""
Abstrakte Basis-Klasse für Storage-Backends
Definiert einheitliche Schnittstelle für verschiedene Backup-Ziele
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Callable, List, Optional


class StorageBackend(ABC):
    """
    Abstrakte Basis-Klasse für Storage-Backends

    Alle Storage-Backends (USB, SFTP, WebDAV, Rclone) müssen
    diese Schnittstelle implementieren.
    """

    @abstractmethod
    def connect(self) -> bool:
        """
        Stellt Verbindung zum Storage her

        Returns:
            True bei Erfolg, False bei Fehler

        Raises:
            ConnectionError: Bei Verbindungsproblemen
        """
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """
        Trennt Verbindung zum Storage

        Sollte immer aufgerufen werden, auch im Fehlerfall (try/finally)
        """
        pass

    @abstractmethod
    def upload_file(
        self,
        local_path: Path,
        remote_path: str,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> bool:
        """
        Lädt Datei zum Storage hoch

        Args:
            local_path: Lokaler Pfad zur Datei
            remote_path: Ziel-Pfad auf dem Storage
            progress_callback: Optional Callback(bytes_transferred, total_bytes)

        Returns:
            True bei Erfolg, False bei Fehler

        Raises:
            FileNotFoundError: Wenn lokale Datei nicht existiert
            IOError: Bei Upload-Fehler
        """
        pass

    @abstractmethod
    def download_file(
        self,
        remote_path: str,
        local_path: Path,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> bool:
        """
        Lädt Datei vom Storage herunter

        Args:
            remote_path: Pfad auf dem Storage
            local_path: Lokaler Ziel-Pfad
            progress_callback: Optional Callback(bytes_transferred, total_bytes)

        Returns:
            True bei Erfolg, False bei Fehler

        Raises:
            FileNotFoundError: Wenn Remote-Datei nicht existiert
            IOError: Bei Download-Fehler
        """
        pass

    @abstractmethod
    def list_files(self, remote_path: str) -> List[str]:
        """
        Listet Dateien im angegebenen Pfad auf

        Args:
            remote_path: Pfad auf dem Storage

        Returns:
            Liste von Dateinamen (ohne Pfad)

        Raises:
            FileNotFoundError: Wenn Pfad nicht existiert
            IOError: Bei Listing-Fehler
        """
        pass

    @abstractmethod
    def delete_file(self, remote_path: str) -> bool:
        """
        Löscht Datei vom Storage

        Args:
            remote_path: Pfad zur Datei auf dem Storage

        Returns:
            True bei Erfolg, False bei Fehler

        Raises:
            FileNotFoundError: Wenn Datei nicht existiert
            IOError: Bei Lösch-Fehler
        """
        pass

    @abstractmethod
    def delete_directory(self, remote_path: str, recursive: bool = False) -> bool:
        """
        Löscht Verzeichnis vom Storage

        Args:
            remote_path: Pfad zum Verzeichnis
            recursive: Rekursiv löschen inkl. Inhalt?

        Returns:
            True bei Erfolg, False bei Fehler

        Raises:
            FileNotFoundError: Wenn Verzeichnis nicht existiert
            IOError: Bei Lösch-Fehler
        """
        pass

    @abstractmethod
    def create_directory(self, remote_path: str) -> bool:
        """
        Erstellt Verzeichnis auf dem Storage

        Args:
            remote_path: Pfad zum zu erstellenden Verzeichnis

        Returns:
            True bei Erfolg, False bei Fehler

        Raises:
            IOError: Bei Erstellungs-Fehler
        """
        pass

    @abstractmethod
    def exists(self, remote_path: str) -> bool:
        """
        Prüft ob Datei/Verzeichnis existiert

        Args:
            remote_path: Pfad auf dem Storage

        Returns:
            True wenn existiert, sonst False
        """
        pass

    @abstractmethod
    def get_available_space(self) -> int:
        """
        Gibt verfügbaren Speicherplatz zurück

        Returns:
            Verfügbarer Speicherplatz in Bytes, -1 wenn unbekannt

        Raises:
            IOError: Bei Fehler beim Abrufen
        """
        pass

    @abstractmethod
    def test_connection(self) -> bool:
        """
        Testet Verbindung zum Storage

        Returns:
            True wenn Verbindung funktioniert, sonst False
        """
        pass

    def __enter__(self):
        """Context Manager: Verbindung herstellen"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context Manager: Verbindung trennen"""
        self.disconnect()
        return False
