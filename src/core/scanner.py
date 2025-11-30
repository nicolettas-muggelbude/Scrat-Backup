"""
Datei-Scanner für Scrat-Backup
Scannt Quell-Ordner und erkennt Änderungen (Neu, Geändert, Gelöscht)
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, Generator, List, Optional, Set

logger = logging.getLogger(__name__)


@dataclass
class FileInfo:
    """
    Informationen über eine Datei

    Attributes:
        path: Absoluter Pfad zur Datei
        relative_path: Relativer Pfad (ab Quell-Ordner)
        size: Dateigröße in Bytes
        modified: Letzte Änderungs-Zeitstempel
        is_new: Ist die Datei neu (nicht im letzten Backup)?
        is_modified: Wurde die Datei geändert?
        is_deleted: Wurde die Datei gelöscht?
    """

    path: Path
    relative_path: Path
    size: int
    modified: datetime
    is_new: bool = False
    is_modified: bool = False
    is_deleted: bool = False

    def __hash__(self) -> int:
        """Ermöglicht Verwendung in Sets"""
        return hash(self.path)

    def __eq__(self, other: object) -> bool:
        """Gleichheit basiert auf Pfad"""
        if not isinstance(other, FileInfo):
            return False
        return self.path == other.path


@dataclass
class ScanResult:
    """
    Ergebnis eines Datei-Scans

    Attributes:
        total_files: Gesamtanzahl gescannter Dateien
        new_files: Liste neuer Dateien
        modified_files: Liste geänderter Dateien
        deleted_files: Liste gelöschter Dateien
        unchanged_files: Liste unveränderte Dateien
        total_size: Gesamtgröße aller Dateien in Bytes
        errors: Liste von Fehlern während des Scans
    """

    total_files: int
    new_files: List[FileInfo]
    modified_files: List[FileInfo]
    deleted_files: List[FileInfo]
    unchanged_files: List[FileInfo]
    total_size: int
    errors: List[str]

    @property
    def files_to_backup(self) -> List[FileInfo]:
        """Gibt alle Dateien zurück, die gesichert werden müssen"""
        return self.new_files + self.modified_files


class Scanner:
    """
    Scannt Dateien und erkennt Änderungen via Timestamp + Size

    Verantwortlichkeiten:
    - Rekursives Scannen von Verzeichnissen
    - Change Detection via Timestamp + Größen-Vergleich
    - Erkennung neuer, geänderter und gelöschter Dateien
    - Exclude-Pattern-Unterstützung
    """

    DEFAULT_EXCLUDE_PATTERNS = {
        # Windows System-Dateien
        "Thumbs.db",
        "desktop.ini",
        "$RECYCLE.BIN",
        "System Volume Information",
        # Temporäre Dateien
        "*.tmp",
        "*.temp",
        "~$*",
        # Locks
        "*.lock",
        ".~lock.*",
    }

    def __init__(self, exclude_patterns: Optional[Set[str]] = None):
        """
        Initialisiert Scanner

        Args:
            exclude_patterns: Set von Datei-/Ordner-Mustern die ignoriert werden sollen
        """
        self.exclude_patterns = exclude_patterns or self.DEFAULT_EXCLUDE_PATTERNS.copy()

    def scan_directory(
        self,
        source_path: Path,
        previous_files: Optional[Dict[str, FileInfo]] = None,
        progress_callback: Optional[Callable[[Path], None]] = None,
    ) -> ScanResult:
        """
        Scannt ein Verzeichnis rekursiv

        Args:
            source_path: Quell-Verzeichnis zum Scannen
            previous_files: Dict mit Dateien aus letztem Backup (key: relative_path)
            progress_callback: Optional, wird für jede Datei aufgerufen: callback(current_file)

        Returns:
            ScanResult mit allen gescannten Dateien und Änderungen

        Raises:
            ValueError: Wenn source_path nicht existiert
        """
        if not source_path.exists():
            raise ValueError(f"Quell-Pfad existiert nicht: {source_path}")

        if not source_path.is_dir():
            raise ValueError(f"Quell-Pfad ist kein Verzeichnis: {source_path}")

        logger.info(f"Starte Scan: {source_path}")

        # Ergebnis-Container initialisieren
        new_files: List[FileInfo] = []
        modified_files: List[FileInfo] = []
        unchanged_files: List[FileInfo] = []
        errors: List[str] = []
        total_size = 0

        # Set für schnellere Lookups
        previous_files = previous_files or {}
        scanned_paths: Set[str] = set()

        # Rekursiv alle Dateien scannen
        try:
            for file_path in self._walk_directory(source_path):
                try:
                    # Progress-Callback aufrufen
                    if progress_callback:
                        progress_callback(file_path)

                    # Relative Pfad berechnen
                    relative_path = file_path.relative_to(source_path)
                    relative_path_str = str(relative_path)

                    # Datei-Info sammeln
                    stat = file_path.stat()
                    size = stat.st_size
                    modified = datetime.fromtimestamp(stat.st_mtime)

                    # FileInfo erstellen
                    file_info = FileInfo(
                        path=file_path,
                        relative_path=relative_path,
                        size=size,
                        modified=modified,
                    )

                    # Change Detection
                    if relative_path_str in previous_files:
                        # Datei existierte im letzten Backup
                        previous_file = previous_files[relative_path_str]

                        # Vergleich: Timestamp ODER Size unterschiedlich?
                        if (
                            abs((modified - previous_file.modified).total_seconds()) > 1
                            or size != previous_file.size
                        ):
                            file_info.is_modified = True
                            modified_files.append(file_info)
                        else:
                            unchanged_files.append(file_info)
                    else:
                        # Neue Datei
                        file_info.is_new = True
                        new_files.append(file_info)

                    # Tracking
                    scanned_paths.add(relative_path_str)
                    total_size += size

                except (PermissionError, OSError) as e:
                    error_msg = f"Fehler beim Lesen von {file_path}: {e}"
                    logger.warning(error_msg)
                    errors.append(error_msg)

        except Exception as e:
            error_msg = f"Fehler beim Scannen von {source_path}: {e}"
            logger.error(error_msg, exc_info=True)
            errors.append(error_msg)

        # Gelöschte Dateien erkennen
        deleted_files: List[FileInfo] = []
        for relative_path_str, previous_file in previous_files.items():
            if relative_path_str not in scanned_paths:
                # Datei war im letzten Backup, aber jetzt nicht mehr da
                deleted_file = FileInfo(
                    path=source_path / previous_file.relative_path,
                    relative_path=previous_file.relative_path,
                    size=previous_file.size,
                    modified=previous_file.modified,
                    is_deleted=True,
                )
                deleted_files.append(deleted_file)

        total_files = len(new_files) + len(modified_files) + len(unchanged_files)

        logger.info(
            f"Scan abgeschlossen: {total_files} Dateien "
            f"({len(new_files)} neu, {len(modified_files)} geändert, "
            f"{len(deleted_files)} gelöscht, {len(errors)} Fehler)"
        )

        return ScanResult(
            total_files=total_files,
            new_files=new_files,
            modified_files=modified_files,
            deleted_files=deleted_files,
            unchanged_files=unchanged_files,
            total_size=total_size,
            errors=errors,
        )

    def _walk_directory(self, path: Path) -> Generator[Path, None, None]:
        """
        Generiert alle Dateien in einem Verzeichnis rekursiv

        Args:
            path: Verzeichnis zum Durchlaufen

        Yields:
            Path: Jede gefundene Datei
        """
        try:
            for item in path.iterdir():
                # Exclude-Pattern prüfen
                if self._is_excluded(item):
                    logger.debug(f"Ausgeschlossen: {item}")
                    continue

                if item.is_file():
                    yield item
                elif item.is_dir():
                    # Rekursiv in Unterverzeichnis
                    yield from self._walk_directory(item)

        except PermissionError as e:
            logger.warning(f"Keine Berechtigung für {path}: {e}")

    def _is_excluded(self, path: Path) -> bool:
        """
        Prüft ob ein Pfad durch Exclude-Pattern ausgeschlossen ist

        Args:
            path: Zu prüfender Pfad

        Returns:
            True wenn ausgeschlossen, sonst False
        """
        name = path.name

        for pattern in self.exclude_patterns:
            # Exact match
            if pattern == name:
                return True

            # Wildcard match (einfache Implementierung)
            if "*" in pattern:
                # z.B. "*.tmp"
                if pattern.startswith("*") and name.endswith(pattern[1:]):
                    return True
                # z.B. "~$*"
                if pattern.endswith("*") and name.startswith(pattern[:-1]):
                    return True

        return False

    def add_exclude_pattern(self, pattern: str) -> None:
        """
        Fügt ein Exclude-Pattern hinzu

        Args:
            pattern: Pattern das ausgeschlossen werden soll (z.B. "*.log")
        """
        self.exclude_patterns.add(pattern)
        logger.debug(f"Exclude-Pattern hinzugefügt: {pattern}")

    def remove_exclude_pattern(self, pattern: str) -> None:
        """
        Entfernt ein Exclude-Pattern

        Args:
            pattern: Pattern das entfernt werden soll
        """
        self.exclude_patterns.discard(pattern)
        logger.debug(f"Exclude-Pattern entfernt: {pattern}")

    def get_exclude_patterns(self) -> Set[str]:
        """
        Gibt alle aktuellen Exclude-Patterns zurück

        Returns:
            Set mit allen Exclude-Patterns
        """
        return self.exclude_patterns.copy()
