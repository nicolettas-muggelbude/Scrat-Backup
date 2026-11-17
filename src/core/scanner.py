"""
Datei-Scanner für Scrat-Backup
Scannt Quell-Ordner und erkennt Änderungen (Neu, Geändert, Gelöscht)
"""

import fnmatch
import logging
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, Generator, List, Optional, Set

logger = logging.getLogger(__name__)

_IS_WINDOWS = sys.platform == "win32"

# Windows-Dateiattribute (siehe stat.FILE_ATTRIBUTE_*)
_FILE_ATTRIBUTE_HIDDEN = 0x2
_FILE_ATTRIBUTE_SYSTEM = 0x4
# Reparse-Tags für Verzeichnis-Junctions und Symlinks (keine OneDrive-Cloud-Platzhalter!)
_IO_REPARSE_TAG_MOUNT_POINT = 0xA0000003
_IO_REPARSE_TAG_SYMLINK = 0xA000000C

# Ordner, die unter Windows nie gesichert werden (Programmdaten, gesperrte Dateien,
# Berechtigungsprobleme). AppData ist normalerweise versteckt, wird aber zusätzlich
# per Name ausgeschlossen, falls das Attribut fehlt.
_WINDOWS_ALWAYS_EXCLUDED_DIRS = {"appdata"}

# Inhalte im Home-Ordner, die für ein Backup keinen Sinn ergeben: Caches,
# neu installierbare Erweiterungen/Toolchains/Pakete, Logs. Pfade sind relativ
# zum Quell-Ordner (greifen also nur, wenn "Home" als Quelle gewählt ist) –
# Projekt-Ordner wie "Projekte/foo/.vscode" bleiben unberührt.
# Konfigurationen, Schlüssel und Einstellungen (.ssh, .config, .gitconfig,
# .vscode/argv.json, .docker/config.json, .claude/projects …) werden gesichert.
_HOME_JUNK_PATHS = (
    # Allgemeine Caches / Papierkorb
    ".cache",
    ".thumbnails",
    ".local/share/Trash",
    ".chocolatey",
    # Editor-Erweiterungen (werden beim Einloggen/Sync neu installiert)
    ".vscode/extensions",
    ".vscode/cli",
    ".vscode-server",
    ".cursor/extensions",
    ".antigravity/extensions",
    ".windsurf/extensions",
    # Docker: Binaries, Plugins, Modelle (Konfiguration bleibt)
    ".docker/bin",
    ".docker/cli-plugins",
    ".docker/modules",
    ".docker/models",
    ".docker/desktop-build",
    # Claude Code: Cache/Debug/Downloads (Projekte, Memory, Settings bleiben)
    ".claude/cache",
    ".claude/debug",
    ".claude/downloads",
    ".claude/shell-snapshots",
    # Paket-Caches & Toolchains (neu installierbar)
    ".npm",
    ".nuget/packages",
    ".gradle/caches",
    ".m2/repository",
    ".cargo/registry",
    ".cargo/git",
    ".rustup/toolchains",
    ".conda/pkgs",
    ".vagrant.d/boxes",
    ".minikube/cache",
    # KI-Modelle (mehrere GB, jederzeit neu ladbar)
    ".ollama/models",
    ".lmstudio/models",
    # Logs / Telemetrie
    ".VirtualBox/*.log*",
    ".vivaldi_reporting_data",
    # Scrat-Backup selbst: Datenbanken sind während des Backups geöffnet
    # und werden ohnehin aufs Backup-Ziel kopiert
    ".scrat-backup/*.db*",
    ".scrat-backup/*.log*",
)
_HOME_JUNK_PARTS = tuple(tuple(p.split("/")) for p in _HOME_JUNK_PATHS)


@dataclass
class FileInfo:
    """
    Informationen über eine Datei

    Attributes:
        path: Absoluter Pfad zur Datei
        source_dir: Quell-Verzeichnis (wo der Scan gestartet wurde)
        relative_path: Relativer Pfad (ab Quell-Ordner)
        size: Dateigröße in Bytes
        modified: Letzte Änderungs-Zeitstempel
        is_new: Ist die Datei neu (nicht im letzten Backup)?
        is_modified: Wurde die Datei geändert?
        is_deleted: Wurde die Datei gelöscht?
    """

    path: Path
    source_dir: Path
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
            for file_path in self._walk_directory(source_path, source_path, errors):
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
                        source_dir=source_path,
                        relative_path=relative_path,
                        size=size,
                        modified=modified,
                    )

                    # Tracking (vor der Lesbarkeitsprüfung: eine gesperrte Datei
                    # existiert noch und darf nicht als "gelöscht" gelten)
                    scanned_paths.add(relative_path_str)

                    # Change Detection
                    if relative_path_str in previous_files:
                        # Datei existierte im letzten Backup
                        previous_file = previous_files[relative_path_str]

                        # Vergleich: Timestamp ODER Size unterschiedlich?
                        if (
                            abs((modified - previous_file.modified).total_seconds()) > 1
                            or size != previous_file.size
                        ):
                            # Gesperrte Datei → überspringen, beim nächsten Lauf erneut versuchen
                            self._check_readable(file_path)
                            file_info.is_modified = True
                            modified_files.append(file_info)
                        else:
                            unchanged_files.append(file_info)
                    else:
                        # Neue Datei
                        self._check_readable(file_path)
                        file_info.is_new = True
                        new_files.append(file_info)

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
                    source_dir=source_path,
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

    @staticmethod
    def _check_readable(file_path: Path) -> None:
        """
        Prüft, ob eine Datei gelesen werden kann (z.B. nicht von Windows gesperrt).

        Raises:
            OSError/PermissionError: Wenn die Datei nicht geöffnet werden kann
        """
        with open(file_path, "rb"):
            pass

    def _walk_directory(
        self,
        path: Path,
        source_root: Optional[Path] = None,
        errors: Optional[List[str]] = None,
    ) -> Generator[Path, None, None]:
        """
        Generiert alle Dateien in einem Verzeichnis rekursiv

        Unter Windows werden versteckte/System-Elemente (z.B. AppData, NTUSER.DAT)
        sowie Junctions/Symlinks auf Verzeichnisse (z.B. "Anwendungsdaten",
        "Eigene Dateien") übersprungen – sie führen sonst zu Zugriffsfehlern
        oder Endlosschleifen.

        Args:
            path: Verzeichnis zum Durchlaufen
            source_root: Quell-Verzeichnis (für Pfad-Patterns wie "AppData/Local/Temp/")
            errors: Optional, Liste in die Fehler eingetragen werden

        Yields:
            Path: Jede gefundene Datei
        """
        if source_root is None:
            source_root = path

        try:
            entries = list(os.scandir(path))
        except OSError as e:
            msg = f"Kein Zugriff auf {path}: {e}"
            logger.warning(msg)
            if errors is not None:
                errors.append(msg)
            return

        for entry in entries:
            item = Path(entry.path)
            try:
                # Exclude-Pattern prüfen
                if self._is_excluded(item, source_root):
                    logger.debug(f"Ausgeschlossen: {item}")
                    continue

                if self._is_home_junk(item, source_root):
                    logger.debug(f"Übersprungen (Cache/neu installierbar): {item}")
                    continue

                if _IS_WINDOWS and self._skip_windows_entry(entry):
                    logger.debug(f"Übersprungen (versteckt/System/Junction): {item}")
                    continue

                if entry.is_file():
                    yield item
                elif entry.is_dir():
                    # Rekursiv in Unterverzeichnis
                    yield from self._walk_directory(item, source_root, errors)

            except OSError as e:
                msg = f"Kein Zugriff auf {item}: {e}"
                logger.warning(msg)
                if errors is not None:
                    errors.append(msg)

    @staticmethod
    def _is_home_junk(path: Path, source_root: Path) -> bool:
        """
        Prüft, ob ein Pfad (relativ zum Quell-Ordner) in _HOME_JUNK_PATHS steht.

        Der Vergleich ist am Quell-Ordner verankert: ".vscode/extensions" greift
        nur direkt unter der Quelle, nicht in Projekt-Unterordnern.
        """
        try:
            rel_parts = path.relative_to(source_root).parts
        except ValueError:
            return False

        for pat_parts in _HOME_JUNK_PARTS:
            if len(pat_parts) == len(rel_parts) and all(
                fnmatch.fnmatch(part, pat) for part, pat in zip(rel_parts, pat_parts)
            ):
                return True
        return False

    @staticmethod
    def _skip_windows_entry(entry: "os.DirEntry[str]") -> bool:
        """
        Prüft, ob ein Windows-Verzeichniseintrag übersprungen werden soll.

        Übersprungen werden:
        - AppData (immer, auch wenn nicht versteckt)
        - Elemente mit Attribut "Versteckt" oder "System"
        - Junctions und Symlinks auf Verzeichnisse

        OneDrive-Platzhalter (Cloud-Reparse-Tags) werden NICHT übersprungen.
        """
        if entry.name.lower() in _WINDOWS_ALWAYS_EXCLUDED_DIRS:
            return True

        st = entry.stat(follow_symlinks=False)
        attrs = getattr(st, "st_file_attributes", 0)
        if attrs & (_FILE_ATTRIBUTE_HIDDEN | _FILE_ATTRIBUTE_SYSTEM):
            return True

        reparse_tag = getattr(st, "st_reparse_tag", 0)
        if reparse_tag in (_IO_REPARSE_TAG_MOUNT_POINT, _IO_REPARSE_TAG_SYMLINK):
            return True

        return False

    def _is_excluded(self, path: Path, source_root: Optional[Path] = None) -> bool:
        """
        Prüft ob ein Pfad durch Exclude-Pattern ausgeschlossen ist

        Unterstützte Pattern-Formen:
        - Name/Glob: "Thumbs.db", "*.tmp", "~$*"
        - Ordner mit abschließendem "/": "node_modules/", ".git/"
        - Pfad-Patterns (relativ, beliebige Tiefe): "AppData/Local/Temp/",
          "AppData/Local/*/Cache/" – jedes Segment ist ein Glob

        Unter Windows wird Groß-/Kleinschreibung ignoriert (fnmatch nutzt normcase).

        Args:
            path: Zu prüfender Pfad
            source_root: Quell-Verzeichnis, relativ zu dem Pfad-Patterns geprüft werden

        Returns:
            True wenn ausgeschlossen, sonst False
        """
        name = path.name

        rel_parts: Optional[tuple] = None
        if source_root is not None:
            try:
                rel_parts = path.relative_to(source_root).parts
            except ValueError:
                rel_parts = None

        for raw_pattern in self.exclude_patterns:
            pattern = raw_pattern.strip().replace("\\", "/").rstrip("/")
            if not pattern:
                continue

            if "/" not in pattern:
                if fnmatch.fnmatch(name, pattern):
                    return True
                continue

            # Pfad-Pattern: Segmente müssen am Ende des relativen Pfads passen
            if rel_parts is None:
                continue
            pat_parts = [p for p in pattern.split("/") if p]
            n = len(pat_parts)
            if n > len(rel_parts):
                continue
            tail = rel_parts[-n:]
            if all(fnmatch.fnmatch(part, pat) for part, pat in zip(tail, pat_parts)):
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
