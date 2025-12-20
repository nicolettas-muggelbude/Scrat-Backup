"""
Backup-Engine für Scrat-Backup
Orchestriert Vollbackups und inkrementelle Backups
"""

import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable, List, Optional

from src.core.compressor import Compressor
from src.core.encryptor import Encryptor
from src.core.metadata_manager import MetadataManager
from src.core.scanner import FileInfo, Scanner

logger = logging.getLogger(__name__)


@dataclass
class BackupConfig:
    """
    Konfiguration für ein Backup

    Attributes:
        sources: Liste der zu sichernden Quell-Verzeichnisse
        destination_path: Ziel-Pfad für Backup
        destination_type: Typ des Ziels (usb, sftp, webdav, rclone)
        password: Verschlüsselungs-Passwort
        compression_level: Komprimierungs-Level (0-9)
        split_size: Maximale Größe pro Archive-Teil in Bytes
        exclude_patterns: Set von Exclude-Patterns
        max_versions: Maximale Anzahl zu behaltender Versionen (Standard: 3)
    """

    sources: List[Path]
    destination_path: Path
    destination_type: str
    password: str
    compression_level: int = 5
    split_size: int = 500 * 1024 * 1024  # 500 MB
    exclude_patterns: Optional[set] = None
    max_versions: int = 3


@dataclass
class BackupProgress:
    """
    Fortschritts-Informationen für ein laufendes Backup

    Attributes:
        backup_id: ID des Backups
        phase: Aktuelle Phase (scanning, compressing, encrypting, uploading)
        files_total: Gesamtanzahl zu sichernder Dateien
        files_processed: Anzahl verarbeiteter Dateien
        bytes_total: Gesamtgröße in Bytes
        bytes_processed: Verarbeitete Bytes
        current_file: Aktuell verarbeitete Datei
        errors: Liste von Fehlern
    """

    backup_id: str
    phase: str
    files_total: int = 0
    files_processed: int = 0
    bytes_total: int = 0
    bytes_processed: int = 0
    current_file: Optional[str] = None
    errors: List[str] = field(default_factory=list)

    @property
    def progress_percentage(self) -> float:
        """Berechnet Fortschritt in Prozent"""
        if self.bytes_total == 0:
            return 0.0
        return (self.bytes_processed / self.bytes_total) * 100


@dataclass
class BackupResult:
    """
    Ergebnis eines Backups

    Attributes:
        backup_id: ID des Backups
        success: Backup erfolgreich?
        backup_type: full oder incremental
        files_total: Anzahl gesicherter Dateien
        size_original: Original-Größe in Bytes
        size_compressed: Komprimierte Größe in Bytes
        duration_seconds: Dauer in Sekunden
        errors: Liste von Fehlern
    """

    backup_id: str
    success: bool
    backup_type: str
    files_total: int
    size_original: int
    size_compressed: int
    duration_seconds: float
    errors: List[str] = field(default_factory=list)


class BackupEngine:
    """
    Haupt-Engine für Backup-Operationen

    Verantwortlichkeiten:
    - Orchestrierung von Voll- und inkrementellen Backups
    - Koordination von Scanner, Compressor, Encryptor, MetadataManager
    - Progress-Tracking und Fehlerbehandlung
    - Versionierungs-Verwaltung (Rotation)
    """

    def __init__(
        self,
        metadata_manager: MetadataManager,
        config: BackupConfig,
        progress_callback: Optional[Callable[[BackupProgress], None]] = None,
    ):
        """
        Initialisiert Backup-Engine

        Args:
            metadata_manager: MetadataManager-Instanz
            config: Backup-Konfiguration
            progress_callback: Optional Callback für Progress-Updates
        """
        self.metadata_manager = metadata_manager
        self.config = config
        self.progress_callback = progress_callback

        # Initialisiere Komponenten
        self.scanner = Scanner(exclude_patterns=config.exclude_patterns)
        self.compressor = Compressor(
            compression_level=config.compression_level, split_size=config.split_size
        )
        self.encryptor = Encryptor(password=config.password)

        # Password-Hash für Metadaten
        self.password_hash = self._hash_password(config.password)

        logger.info("Backup-Engine initialisiert")

    def _hash_password(self, password: str) -> str:
        """
        Erstellt Hash des Passworts für Metadaten

        Args:
            password: Passwort

        Returns:
            SHA256-Hash des Passworts
        """
        return hashlib.sha256(password.encode()).hexdigest()

    def create_full_backup(self) -> BackupResult:
        """
        Erstellt Vollbackup aller konfigurierten Quellen

        Returns:
            BackupResult mit Statistiken

        Raises:
            ValueError: Bei ungültiger Konfiguration
            RuntimeError: Bei Backup-Fehler
        """
        start_time = datetime.now()
        backup_id = self._generate_backup_id("full")

        logger.info(f"Starte Vollbackup: {backup_id}")

        try:
            # Erstelle Backup-Record in DB
            db_backup_id = self.metadata_manager.create_backup_record(
                backup_type="full",
                destination_type=self.config.destination_type,
                destination_path=str(self.config.destination_path),
                encryption_key_hash=self.password_hash,
                salt=self.encryptor.salt,
            )

            # Log: Backup gestartet
            self.metadata_manager.add_log(
                level="INFO",
                message=f"Vollbackup gestartet: {backup_id}",
                backup_id=db_backup_id,
                details=f"Quellen: {len(self.config.sources)}, Ziel: {self.config.destination_path}",
            )

            # Progress initialisieren
            progress = BackupProgress(backup_id=backup_id, phase="scanning")
            self._report_progress(progress)

            # 1. Scannen aller Quellen
            all_files: List[FileInfo] = []
            total_size = 0

            for source_path in self.config.sources:
                logger.info(f"Scanne Quelle: {source_path}")

                def scan_progress(file_path: Path) -> None:
                    progress.current_file = str(file_path)
                    self._report_progress(progress)

                scan_result = self.scanner.scan_directory(
                    source_path=source_path, progress_callback=scan_progress
                )

                all_files.extend(scan_result.new_files)
                total_size += scan_result.total_size
                progress.errors.extend(scan_result.errors)

            progress.files_total = len(all_files)
            progress.bytes_total = total_size
            logger.info(
                f"Scan abgeschlossen: {len(all_files)} Dateien, {total_size / 1024 / 1024:.1f}MB"
            )

            # Update Backup-Record mit Datei-Anzahl
            self.metadata_manager.update_backup_progress(
                backup_id=db_backup_id,
                files_processed=0,
                size_original=total_size,
                size_compressed=0,
            )

            # Wenn keine Dateien gefunden wurden, markiere als erfolgreich und beende
            if not all_files:
                logger.info("Keine Dateien zum Sichern gefunden - Backup als leer markiert")
                self.metadata_manager.mark_backup_completed(backup_id=db_backup_id, files_total=0)

                end_time = datetime.now()
                duration_seconds = (end_time - start_time).total_seconds()

                result = BackupResult(
                    success=True,
                    backup_id=backup_id,
                    backup_type="full",
                    files_total=0,
                    size_original=0,
                    size_compressed=0,
                    duration_seconds=duration_seconds,
                    errors=progress.errors,
                )
                logger.info("Vollbackup erfolgreich abgeschlossen (leer)")
                return result

            # 2. Komprimieren
            progress.phase = "compressing"
            self._report_progress(progress)

            # Erstelle Backup-Verzeichnis
            backup_dir = self.config.destination_path / backup_id
            backup_dir.mkdir(parents=True, exist_ok=True)

            # Komprimiere alle Dateien
            archive_base_path = backup_dir / "data.7z"

            def compress_progress(current: int, total: int, filename: str) -> None:
                progress.files_processed = current
                progress.current_file = filename
                self._report_progress(progress)

            file_paths = [f.path for f in all_files]
            archives = self.compressor.compress_files(
                files=file_paths,
                output_path=archive_base_path,
                progress_callback=compress_progress,
            )

            logger.info(f"Komprimierung abgeschlossen: {len(archives)} Archive")

            # 3. Verschlüsseln
            progress.phase = "encrypting"
            self._report_progress(progress)

            encrypted_archives: List[Path] = []
            for idx, archive_path in enumerate(archives):
                progress.current_file = archive_path.name
                self._report_progress(progress)

                encrypted_path = archive_path.parent / f"{archive_path.name}.enc"
                self.encryptor.encrypt_file(archive_path, encrypted_path)
                encrypted_archives.append(encrypted_path)

                # Lösche unkomprimiertes Archiv
                archive_path.unlink()

                logger.debug(f"Verschlüsselt: {archive_path.name}")

            # Berechne komprimierte Größe
            size_compressed = sum(p.stat().st_size for p in encrypted_archives)

            # 4. Metadaten speichern
            progress.phase = "saving_metadata"
            self._report_progress(progress)

            # Speichere Datei-Informationen in DB
            for file_info in all_files:
                # Bestimme in welchem Archiv die Datei ist (vereinfacht)
                archive_name = encrypted_archives[0].name if encrypted_archives else ""

                self.metadata_manager.add_file_to_backup(
                    backup_id=db_backup_id,
                    source_path=str(file_info.path),
                    relative_path=str(file_info.relative_path),
                    file_size=file_info.size,
                    modified_timestamp=file_info.modified,
                    archive_name=archive_name,
                    archive_path=str(backup_dir),
                )

            # Update Backup als abgeschlossen
            end_time = datetime.now()
            self.metadata_manager.update_backup_progress(
                backup_id=db_backup_id,
                files_processed=len(all_files),
                size_original=total_size,
                size_compressed=size_compressed,
            )
            self.metadata_manager.mark_backup_completed(
                backup_id=db_backup_id, files_total=len(all_files)
            )

            # Versionierungs-Rotation
            self._rotate_old_backups()

            duration = (end_time - start_time).total_seconds()

            logger.info(
                f"Vollbackup abgeschlossen: {len(all_files)} Dateien, "
                f"{total_size / 1024 / 1024:.1f}MB → {size_compressed / 1024 / 1024:.1f}MB, "
                f"Dauer: {duration:.1f}s"
            )

            # Log: Backup erfolgreich
            self.metadata_manager.add_log(
                level="INFO",
                message=f"Vollbackup erfolgreich abgeschlossen",
                backup_id=db_backup_id,
                details=f"Dateien: {len(all_files)}, Original: {total_size / 1024 / 1024:.1f}MB, "
                f"Komprimiert: {size_compressed / 1024 / 1024:.1f}MB, Dauer: {duration:.1f}s",
            )

            return BackupResult(
                backup_id=backup_id,
                success=True,
                backup_type="full",
                files_total=len(all_files),
                size_original=total_size,
                size_compressed=size_compressed,
                duration_seconds=duration,
                errors=progress.errors,
            )

        except Exception as e:
            logger.error(f"Fehler beim Vollbackup: {e}", exc_info=True)

            # Log: Backup fehlgeschlagen
            try:
                self.metadata_manager.add_log(
                    level="ERROR",
                    message=f"Vollbackup fehlgeschlagen",
                    backup_id=db_backup_id,
                    details=str(e),
                )
            except Exception:
                pass

            # Markiere Backup als fehlgeschlagen
            try:
                self.metadata_manager.mark_backup_failed(
                    backup_id=db_backup_id, error_message=str(e)
                )
            except Exception:
                pass

            raise RuntimeError(f"Backup fehlgeschlagen: {e}") from e

    def create_incremental_backup(self) -> BackupResult:
        """
        Erstellt inkrementelles Backup (nur geänderte Dateien)

        Returns:
            BackupResult mit Statistiken

        Raises:
            ValueError: Wenn kein Basis-Backup existiert
            RuntimeError: Bei Backup-Fehler
        """
        # Prüfe Basis-Backup BEVOR try-Block (ValueError soll durchkommen)
        base_backups = self.metadata_manager.get_all_backups()
        completed_backups = [b for b in base_backups if b["status"] == "completed"]

        if not completed_backups:
            raise ValueError("Kein Basis-Backup gefunden. " "Erstelle zuerst ein Vollbackup.")

        start_time = datetime.now()
        backup_id = self._generate_backup_id("incr")

        logger.info(f"Starte inkrementelles Backup: {backup_id}")

        try:
            # Neuestes Backup als Basis
            base_backup = completed_backups[0]
            base_backup_id = base_backup["id"]

            logger.info(f"Basis-Backup: {base_backup_id} vom {base_backup['timestamp']}")

            # Erstelle Backup-Record
            db_backup_id = self.metadata_manager.create_backup_record(
                backup_type="incremental",
                destination_type=self.config.destination_type,
                destination_path=str(self.config.destination_path),
                encryption_key_hash=self.password_hash,
                salt=self.encryptor.salt,
                base_backup_id=base_backup_id,
            )

            # Log: Backup gestartet
            self.metadata_manager.add_log(
                level="INFO",
                message=f"Inkrementelles Backup gestartet: {backup_id}",
                backup_id=db_backup_id,
                details=f"Basis: #{base_backup_id}, Quellen: {len(self.config.sources)}",
            )

            # Progress initialisieren
            progress = BackupProgress(backup_id=backup_id, phase="scanning")
            self._report_progress(progress)

            # 1. Scannen mit Basis-Backup-Vergleich
            all_changed_files: List[FileInfo] = []
            total_size = 0

            for source_path in self.config.sources:
                logger.info(f"Scanne Quelle: {source_path}")

                # Hole Dateien aus letztem Backup für diesen Pfad
                all_previous_files = self.metadata_manager.get_backup_files(base_backup_id)

                # Filtere nach source_path
                previous_files_list = [
                    f for f in all_previous_files if f["source_path"].startswith(str(source_path))
                ]

                # Konvertiere zu Dict für Scanner
                previous_files = {}
                for pf in previous_files_list:
                    # Konvertiere Timestamp-String zu datetime, falls nötig
                    modified_ts = pf["modified_timestamp"]
                    if isinstance(modified_ts, str):
                        modified_ts = datetime.fromisoformat(modified_ts)

                    file_info = FileInfo(
                        path=Path(pf["source_path"]),
                        relative_path=Path(pf["relative_path"]),
                        size=pf["file_size"],
                        modified=modified_ts,
                    )
                    previous_files[pf["relative_path"]] = file_info

                def scan_progress(file_path: Path) -> None:
                    progress.current_file = str(file_path)
                    self._report_progress(progress)

                # Scan mit Change Detection
                scan_result = self.scanner.scan_directory(
                    source_path=source_path,
                    previous_files=previous_files,
                    progress_callback=scan_progress,
                )

                # Nur neue und geänderte Dateien
                changed_files = scan_result.files_to_backup
                all_changed_files.extend(changed_files)
                total_size += sum(f.size for f in changed_files)
                progress.errors.extend(scan_result.errors)

                # Speichere gelöschte Dateien
                for deleted_file in scan_result.deleted_files:
                    self.metadata_manager.add_file_to_backup(
                        backup_id=db_backup_id,
                        source_path=str(deleted_file.path),
                        relative_path=str(deleted_file.relative_path),
                        file_size=0,
                        modified_timestamp=deleted_file.modified,
                        archive_name="",
                        archive_path="",
                        is_deleted=True,
                    )

            progress.files_total = len(all_changed_files)
            progress.bytes_total = total_size

            logger.info(
                f"Scan abgeschlossen: {len(all_changed_files)} geänderte Dateien, "
                f"{total_size / 1024 / 1024:.1f}MB"
            )

            if len(all_changed_files) == 0:
                logger.info("Keine Änderungen gefunden, Backup übersprungen")

                # Markiere als abgeschlossen ohne Daten
                self.metadata_manager.mark_backup_completed(backup_id=db_backup_id, files_total=0)

                # Versionierungs-Rotation
                self._rotate_old_backups()

                return BackupResult(
                    backup_id=backup_id,
                    success=True,
                    backup_type="incremental",
                    files_total=0,
                    size_original=0,
                    size_compressed=0,
                    duration_seconds=(datetime.now() - start_time).total_seconds(),
                    errors=progress.errors,
                )

            # Update Backup-Record
            self.metadata_manager.update_backup_progress(
                backup_id=db_backup_id,
                files_processed=0,
                size_original=total_size,
                size_compressed=0,
            )

            # 2-4: Komprimieren, Verschlüsseln, Metadaten speichern
            # (gleicher Prozess wie Vollbackup)
            progress.phase = "compressing"
            self._report_progress(progress)

            backup_dir = self.config.destination_path / backup_id
            backup_dir.mkdir(parents=True, exist_ok=True)
            archive_base_path = backup_dir / "data.7z"

            def compress_progress(current: int, total: int, filename: str) -> None:
                progress.files_processed = current
                progress.current_file = filename
                self._report_progress(progress)

            file_paths = [f.path for f in all_changed_files]
            archives = self.compressor.compress_files(
                files=file_paths,
                output_path=archive_base_path,
                progress_callback=compress_progress,
            )

            # Verschlüsseln
            progress.phase = "encrypting"
            self._report_progress(progress)

            encrypted_archives: List[Path] = []
            for archive_path in archives:
                encrypted_path = archive_path.parent / f"{archive_path.name}.enc"
                self.encryptor.encrypt_file(archive_path, encrypted_path)
                encrypted_archives.append(encrypted_path)
                archive_path.unlink()

            size_compressed = sum(p.stat().st_size for p in encrypted_archives)

            # Metadaten speichern
            progress.phase = "saving_metadata"
            self._report_progress(progress)

            for file_info in all_changed_files:
                archive_name = encrypted_archives[0].name if encrypted_archives else ""
                self.metadata_manager.add_file_to_backup(
                    backup_id=db_backup_id,
                    source_path=str(file_info.path),
                    relative_path=str(file_info.relative_path),
                    file_size=file_info.size,
                    modified_timestamp=file_info.modified,
                    archive_name=archive_name,
                    archive_path=str(backup_dir),
                )

            # Abschließen
            end_time = datetime.now()
            self.metadata_manager.update_backup_progress(
                backup_id=db_backup_id,
                files_processed=len(all_changed_files),
                size_original=total_size,
                size_compressed=size_compressed,
            )
            self.metadata_manager.mark_backup_completed(
                backup_id=db_backup_id, files_total=len(all_changed_files)
            )

            # Versionierungs-Rotation
            self._rotate_old_backups()

            duration = (end_time - start_time).total_seconds()

            logger.info(
                f"Inkrementelles Backup abgeschlossen: {len(all_changed_files)} Dateien, "
                f"{total_size / 1024 / 1024:.1f}MB → {size_compressed / 1024 / 1024:.1f}MB, "
                f"Dauer: {duration:.1f}s"
            )

            # Log: Backup erfolgreich
            self.metadata_manager.add_log(
                level="INFO",
                message=f"Inkrementelles Backup erfolgreich abgeschlossen",
                backup_id=db_backup_id,
                details=f"Dateien: {len(all_changed_files)}, Original: {total_size / 1024 / 1024:.1f}MB, "
                f"Komprimiert: {size_compressed / 1024 / 1024:.1f}MB, Dauer: {duration:.1f}s",
            )

            return BackupResult(
                backup_id=backup_id,
                success=True,
                backup_type="incremental",
                files_total=len(all_changed_files),
                size_original=total_size,
                size_compressed=size_compressed,
                duration_seconds=duration,
                errors=progress.errors,
            )

        except Exception as e:
            logger.error(f"Fehler beim inkrementellen Backup: {e}", exc_info=True)

            # Log: Backup fehlgeschlagen
            try:
                self.metadata_manager.add_log(
                    level="ERROR",
                    message=f"Inkrementelles Backup fehlgeschlagen",
                    backup_id=db_backup_id,
                    details=str(e),
                )
            except Exception:
                pass

            try:
                self.metadata_manager.mark_backup_failed(
                    backup_id=db_backup_id, error_message=str(e)
                )
            except Exception:
                pass

            raise RuntimeError(f"Backup fehlgeschlagen: {e}") from e

    def _rotate_old_backups(self) -> None:
        """
        Rotiert alte Backups (3-Versionen-Rotation)

        Löscht älteste Backups wenn mehr als max_versions vorhanden
        """
        logger.info("Prüfe Versionierungs-Rotation")

        all_backups = self.metadata_manager.get_all_backups()
        completed_backups = [b for b in all_backups if b["status"] == "completed"]

        if len(completed_backups) <= self.config.max_versions:
            logger.info(
                f"Rotation nicht nötig: {len(completed_backups)} von "
                f"{self.config.max_versions} Versionen"
            )
            return

        # Sortiere nach Timestamp (älteste zuerst)
        completed_backups.sort(key=lambda b: b["timestamp"])

        # Lösche älteste Backups
        backups_to_delete = completed_backups[: -self.config.max_versions]

        for backup in backups_to_delete:
            backup_id = backup["id"]
            logger.info(f"Lösche altes Backup: {backup_id} vom {backup['timestamp']}")

            # Lösche Backup-Verzeichnis auf Disk
            # (Konstruiere Pfad aus destination_path)
            # TODO: Implementierung abhängig von Storage-Backend (Phase 4)

            # Lösche aus Datenbank (CASCADE löscht auch Dateien)
            self.metadata_manager.delete_backup(backup_id)

        logger.info(f"Rotation abgeschlossen: {len(backups_to_delete)} alte Backups gelöscht")

    def _generate_backup_id(self, backup_type: str) -> str:
        """
        Generiert eindeutige Backup-ID

        Args:
            backup_type: full oder incr

        Returns:
            Backup-ID im Format: YYYYMMDD_HHMMSS_type
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{timestamp}_{backup_type}"

    def _report_progress(self, progress: BackupProgress) -> None:
        """
        Meldet Fortschritt via Callback

        Args:
            progress: Aktuelle Progress-Informationen
        """
        if self.progress_callback:
            # Sende Kopie, nicht Referenz (wichtig für korrekte Progress-Tracking)
            from dataclasses import replace

            progress_copy = replace(progress, errors=progress.errors.copy())  # Auch errors kopieren
            self.progress_callback(progress_copy)

        logger.debug(
            f"Progress: {progress.phase}, "
            f"{progress.files_processed}/{progress.files_total} Dateien, "
            f"{progress.progress_percentage:.1f}%"
        )
