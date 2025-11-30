"""
Rclone Storage-Backend
CLI-Wrapper für 40+ Cloud-Provider
"""

import json
import logging
import subprocess
from pathlib import Path
from typing import Callable, List, Optional

from src.storage.base import StorageBackend

logger = logging.getLogger(__name__)


class RcloneStorage(StorageBackend):
    """
    Storage-Backend für Rclone (CLI-Wrapper für Cloud-Provider)

    Unterstützt 40+ Cloud-Provider:
    - Google Drive, Google Cloud Storage
    - Microsoft OneDrive, SharePoint
    - Dropbox
    - Amazon S3, Glacier
    - Backblaze B2
    - Box
    - pCloud
    - MEGA
    - Nextcloud/ownCloud (via WebDAV)
    - ... und viele mehr

    Voraussetzung:
    - Rclone muss installiert sein (https://rclone.org/)
    - Remote muss konfiguriert sein (via `rclone config`)

    Beispiel:
        # Remote "gdrive" muss vorher konfiguriert sein
        storage = RcloneStorage(remote_name="gdrive", remote_path="backups")
        storage.connect()
        storage.upload_file(Path("file.txt"), "backup.txt")
    """

    def __init__(
        self,
        remote_name: str,
        remote_path: str = "",
        rclone_binary: str = "rclone",
    ):
        """
        Initialisiert Rclone-Storage

        Args:
            remote_name: Name des Rclone-Remotes (z.B. "gdrive", "onedrive")
            remote_path: Basis-Pfad auf dem Remote (optional)
            rclone_binary: Pfad zum rclone-Binary (Standard: "rclone" im PATH)
        """
        self.remote_name = remote_name.rstrip(":")
        self.remote_path = remote_path.strip("/")
        self.rclone_binary = rclone_binary

        self._connected = False
        self._rclone_version: Optional[str] = None

        logger.info(f"RcloneStorage initialisiert: {self.remote_name}:{self.remote_path}")

    def connect(self) -> bool:
        """
        Stellt Verbindung zum Rclone-Remote her

        Returns:
            True bei Erfolg

        Raises:
            ConnectionError: Bei Verbindungsproblemen
        """
        try:
            # Prüfe ob rclone installiert ist
            if not self._check_rclone_installed():
                raise ConnectionError(
                    "rclone nicht gefunden. " "Installiere rclone von https://rclone.org/"
                )

            # Prüfe ob Remote konfiguriert ist
            remotes = self._list_remotes()
            if self.remote_name not in remotes:
                raise ConnectionError(
                    f"Remote '{self.remote_name}' nicht konfiguriert. "
                    f"Verfügbare Remotes: {', '.join(remotes) if remotes else 'keine'}\n"
                    f"Konfiguriere Remote mit: rclone config"
                )

            # Teste Verbindung mit about-Befehl
            try:
                self._run_rclone_command(["about", f"{self.remote_name}:"])
            except subprocess.CalledProcessError as e:
                raise ConnectionError(
                    f"Verbindung zu Remote '{self.remote_name}' fehlgeschlagen: {e.stderr}"
                )

            # Erstelle Basis-Pfad falls nötig
            if self.remote_path:
                self._ensure_directory_exists(self.remote_path)

            self._connected = True
            logger.info(f"Rclone-Verbindung hergestellt: {self.remote_name}")
            return True

        except Exception as e:
            logger.error(f"Rclone-Verbindung fehlgeschlagen: {e}")
            raise ConnectionError(f"Rclone-Verbindung fehlgeschlagen: {e}") from e

    def disconnect(self) -> None:
        """Trennt Rclone-Verbindung"""
        # Rclone hat keine persistente Verbindung
        self._connected = False
        logger.info("Rclone-Verbindung getrennt")

    def upload_file(
        self,
        local_path: Path,
        remote_path: str,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> bool:
        """
        Lädt Datei per Rclone hoch

        Args:
            local_path: Lokale Quell-Datei
            remote_path: Relativer Ziel-Pfad
            progress_callback: Optional Progress-Callback (TODO: Implementierung)

        Returns:
            True bei Erfolg
        """
        if not self._connected:
            raise ConnectionError("Nicht verbunden. Rufe connect() auf.")

        if not local_path.exists():
            raise FileNotFoundError(f"Quell-Datei nicht gefunden: {local_path}")

        # Vollständiger Remote-Pfad
        full_remote_path = self._join_remote_path(remote_path)

        try:
            # rclone copyto: kopiert Datei zu exaktem Ziel
            self._run_rclone_command(
                [
                    "copyto",
                    str(local_path),
                    full_remote_path,
                    "--verbose",
                ]
            )

            logger.info(f"Datei hochgeladen: {local_path.name} → {remote_path}")
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Fehler beim Upload: {e.stderr}")
            raise IOError(f"Upload fehlgeschlagen: {e.stderr}") from e

    def download_file(
        self,
        remote_path: str,
        local_path: Path,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> bool:
        """
        Lädt Datei per Rclone herunter

        Args:
            remote_path: Relativer Quell-Pfad
            local_path: Lokaler Ziel-Pfad
            progress_callback: Optional Progress-Callback (TODO: Implementierung)

        Returns:
            True bei Erfolg
        """
        if not self._connected:
            raise ConnectionError("Nicht verbunden. Rufe connect() auf.")

        full_remote_path = self._join_remote_path(remote_path)

        # Prüfe ob Remote-Datei existiert
        if not self.exists(remote_path):
            raise FileNotFoundError(f"Remote-Datei nicht gefunden: {remote_path}")

        # Stelle sicher, dass lokales Verzeichnis existiert
        local_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            # rclone copyto: kopiert Datei zu exaktem Ziel
            self._run_rclone_command(
                [
                    "copyto",
                    full_remote_path,
                    str(local_path),
                    "--verbose",
                ]
            )

            logger.info(f"Datei heruntergeladen: {remote_path} → {local_path.name}")
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Fehler beim Download: {e.stderr}")
            raise IOError(f"Download fehlgeschlagen: {e.stderr}") from e

    def list_files(self, remote_path: str) -> List[str]:
        """
        Listet Dateien im Remote-Verzeichnis auf

        Args:
            remote_path: Relativer Pfad zum Verzeichnis

        Returns:
            Liste von Dateinamen (ohne Unterverzeichnisse)
        """
        if not self._connected:
            raise ConnectionError("Nicht verbunden. Rufe connect() auf.")

        full_remote_path = self._join_remote_path(remote_path)

        try:
            # rclone lsjson: JSON-Output für besseres Parsing
            result = self._run_rclone_command(
                [
                    "lsjson",
                    full_remote_path,
                    "--files-only",  # Nur Dateien, keine Verzeichnisse
                ]
            )

            # Parse JSON-Output
            items = json.loads(result.stdout)
            files = [item["Name"] for item in items if not item.get("IsDir", False)]

            logger.debug(f"Dateien in {remote_path}: {len(files)}")
            return files

        except subprocess.CalledProcessError as e:
            logger.error(f"Fehler beim Listing: {e.stderr}")
            raise IOError(f"Listing fehlgeschlagen: {e.stderr}") from e
        except json.JSONDecodeError as e:
            logger.error(f"JSON-Parsing fehlgeschlagen: {e}")
            raise IOError(f"JSON-Parsing fehlgeschlagen: {e}") from e

    def delete_file(self, remote_path: str) -> bool:
        """
        Löscht Remote-Datei

        Args:
            remote_path: Relativer Pfad zur Datei

        Returns:
            True bei Erfolg
        """
        if not self._connected:
            raise ConnectionError("Nicht verbunden. Rufe connect() auf.")

        full_remote_path = self._join_remote_path(remote_path)

        # Prüfe ob existiert
        if not self.exists(remote_path):
            raise FileNotFoundError(f"Datei nicht gefunden: {remote_path}")

        try:
            # rclone deletefile: löscht einzelne Datei
            self._run_rclone_command(["deletefile", full_remote_path])
            logger.info(f"Datei gelöscht: {remote_path}")
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Fehler beim Löschen: {e.stderr}")
            raise IOError(f"Löschen fehlgeschlagen: {e.stderr}") from e

    def delete_directory(self, remote_path: str, recursive: bool = False) -> bool:
        """
        Löscht Remote-Verzeichnis

        Args:
            remote_path: Relativer Pfad zum Verzeichnis
            recursive: Rekursiv löschen? (Standard: False)

        Returns:
            True bei Erfolg
        """
        if not self._connected:
            raise ConnectionError("Nicht verbunden. Rufe connect() auf.")

        full_remote_path = self._join_remote_path(remote_path)

        # Prüfe ob existiert
        if not self.exists(remote_path):
            raise FileNotFoundError(f"Verzeichnis nicht gefunden: {remote_path}")

        try:
            if recursive:
                # rclone purge: löscht Verzeichnis rekursiv (schneller)
                self._run_rclone_command(["purge", full_remote_path])
            else:
                # rclone rmdir: löscht nur leeres Verzeichnis
                self._run_rclone_command(["rmdir", full_remote_path])

            logger.info(f"Verzeichnis gelöscht: {remote_path}")
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Fehler beim Löschen: {e.stderr}")
            raise IOError(f"Löschen fehlgeschlagen: {e.stderr}") from e

    def create_directory(self, remote_path: str) -> bool:
        """
        Erstellt Remote-Verzeichnis

        Args:
            remote_path: Relativer Pfad zum Verzeichnis

        Returns:
            True bei Erfolg
        """
        if not self._connected:
            raise ConnectionError("Nicht verbunden. Rufe connect() auf.")

        try:
            self._ensure_directory_exists(remote_path)
            logger.info(f"Verzeichnis erstellt: {remote_path}")
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Fehler beim Erstellen: {e.stderr}")
            raise IOError(f"Erstellen fehlgeschlagen: {e.stderr}") from e

    def exists(self, remote_path: str) -> bool:
        """
        Prüft ob Remote-Pfad existiert

        Args:
            remote_path: Relativer Pfad

        Returns:
            True wenn existiert
        """
        if not self._connected:
            raise ConnectionError("Nicht verbunden. Rufe connect() auf.")

        full_remote_path = self._join_remote_path(remote_path)

        try:
            # rclone lsf: schnelles Listing (nur Namen)
            self._run_rclone_command(["lsf", full_remote_path])
            # Wenn kein Fehler, existiert der Pfad
            return True
        except subprocess.CalledProcessError:
            return False

    def get_available_space(self) -> int:
        """
        Gibt verfügbaren Speicherplatz zurück

        Returns:
            Verfügbarer Platz in Bytes, -1 wenn nicht verfügbar
        """
        if not self._connected:
            raise ConnectionError("Nicht verbunden. Rufe connect() auf.")

        try:
            # rclone about: Speicherplatz-Info als JSON
            result = self._run_rclone_command(["about", f"{self.remote_name}:", "--json"])

            about_info = json.loads(result.stdout)
            # free oder free_bytes (je nach Provider)
            free_space = about_info.get("free") or about_info.get("free_bytes")

            if free_space is not None:
                return int(free_space)
            else:
                logger.warning("Provider unterstützt keine Speicherplatz-Abfrage")
                return -1

        except subprocess.CalledProcessError as e:
            logger.warning(f"Speicherplatz-Abfrage fehlgeschlagen: {e.stderr}")
            return -1
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning(f"Fehler beim Parsen der Speicherplatz-Info: {e}")
            return -1

    def test_connection(self) -> bool:
        """
        Testet Rclone-Verbindung

        Returns:
            True wenn Verbindung OK
        """
        if not self._connected:
            return False

        try:
            # Teste mit about-Befehl
            self._run_rclone_command(["about", f"{self.remote_name}:"])
            return True
        except Exception:
            return False

    def _check_rclone_installed(self) -> bool:
        """
        Prüft ob rclone installiert ist

        Returns:
            True wenn installiert
        """
        try:
            result = subprocess.run(
                [self.rclone_binary, "version"],
                capture_output=True,
                text=True,
                check=True,
                timeout=10,
            )
            self._rclone_version = result.stdout.split("\n")[0]
            logger.debug(f"Rclone gefunden: {self._rclone_version}")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def _list_remotes(self) -> List[str]:
        """
        Listet alle konfigurierten Rclone-Remotes auf

        Returns:
            Liste von Remote-Namen
        """
        try:
            result = self._run_rclone_command(["listremotes"])
            # Output: "remote1:\nremote2:\n..."
            remotes = [line.rstrip(":") for line in result.stdout.strip().split("\n") if line]
            return remotes
        except subprocess.CalledProcessError:
            return []

    def _run_rclone_command(
        self,
        args: List[str],
        timeout: int = 300,
    ) -> subprocess.CompletedProcess:
        """
        Führt rclone-Befehl aus

        Args:
            args: Rclone-Argumente (ohne "rclone" selbst)
            timeout: Timeout in Sekunden

        Returns:
            CompletedProcess mit stdout/stderr

        Raises:
            subprocess.CalledProcessError: Bei Fehler
        """
        cmd = [self.rclone_binary] + args

        logger.debug(f"Rclone-Befehl: {' '.join(cmd)}")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            timeout=timeout,
        )

        return result

    def _join_remote_path(self, relative_path: str) -> str:
        """
        Verbindet Remote-Name mit Basis-Pfad und relativem Pfad

        Args:
            relative_path: Relativer Pfad

        Returns:
            Vollständiger Remote-Pfad (z.B. "gdrive:backups/file.txt")
        """
        # Normalisiere Pfade
        relative_path = relative_path.strip("/")

        # Baue Pfad zusammen
        if self.remote_path and relative_path:
            full_path = f"{self.remote_path}/{relative_path}"
        elif self.remote_path:
            full_path = self.remote_path
        elif relative_path:
            full_path = relative_path
        else:
            full_path = ""

        # Formatiere als Rclone-Remote-Pfad
        return f"{self.remote_name}:{full_path}"

    def _ensure_directory_exists(self, path: str) -> None:
        """
        Stellt sicher, dass Verzeichnis existiert (erstellt rekursiv)

        Args:
            path: Relativer Pfad
        """
        full_remote_path = self._join_remote_path(path)

        # rclone mkdir: erstellt Verzeichnis rekursiv
        try:
            self._run_rclone_command(["mkdir", full_remote_path])
        except subprocess.CalledProcessError:
            # Verzeichnis existiert bereits (OK)
            pass
