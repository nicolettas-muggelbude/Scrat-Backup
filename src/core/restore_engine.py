"""
Restore-Engine für Scrat-Backup
Wiederherstellung von Backups
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable, List, Optional

from src.core.compressor import Compressor
from src.core.encryptor import Encryptor
from src.core.metadata_manager import MetadataManager
from src.storage.base import StorageBackend

logger = logging.getLogger(__name__)


@dataclass
class RestoreConfig:
    """
    Konfiguration für Wiederherstellung

    Attributes:
        destination_path: Ziel-Pfad für wiederhergestellte Dateien
        password: Entschlüsselungs-Passwort
        restore_to_original: In Original-Verzeichnisse wiederherstellen?
        overwrite_existing: Existierende Dateien überschreiben?
        restore_permissions: Datei-Permissions wiederherstellen?
    """

    destination_path: Path
    password: str
    restore_to_original: bool = False
    overwrite_existing: bool = False
    restore_permissions: bool = True


@dataclass
class RestoreProgress:
    """
    Fortschritts-Informationen für Wiederherstellung

    Attributes:
        phase: Aktuelle Phase (downloading, decrypting, extracting, restoring)
        files_total: Gesamtanzahl wiederherzustellender Dateien
        files_processed: Anzahl verarbeiteter Dateien
        bytes_total: Gesamtgröße in Bytes
        bytes_processed: Verarbeitete Bytes
        current_file: Aktuell verarbeitete Datei
        errors: Liste von Fehlern
    """

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
        if self.files_total == 0:
            return 0.0
        return (self.files_processed / self.files_total) * 100


@dataclass
class RestoreResult:
    """
    Ergebnis einer Wiederherstellung

    Attributes:
        success: Wiederherstellung erfolgreich?
        files_restored: Anzahl wiederhergestellter Dateien
        bytes_restored: Wiederhergestellte Bytes
        duration_seconds: Dauer in Sekunden
        errors: Liste von Fehlern
    """

    success: bool
    files_restored: int
    bytes_restored: int
    duration_seconds: float
    errors: List[str] = field(default_factory=list)


@dataclass
class FileEntry:
    """
    Eintrag einer Datei aus Backup-Metadaten

    Attributes:
        relative_path: Relativer Pfad
        file_size: Dateigröße in Bytes
        modified_timestamp: Änderungs-Zeitstempel
        archive_name: Name des Archives
        archive_path: Pfad zum Archiv
        backup_id: ID des Backups
        is_deleted: Wurde gelöscht?
    """

    relative_path: str
    file_size: int
    modified_timestamp: datetime
    archive_name: str
    archive_path: str
    backup_id: int
    is_deleted: bool = False


class RestoreEngine:
    """
    Engine für Wiederherstellungs-Operationen

    Verantwortlichkeiten:
    - Wiederherstellung kompletter Backups
    - Teilweise Wiederherstellung (einzelne Dateien)
    - Zeitpunkt-basierte Wiederherstellung
    - Datei-Suche in Metadaten
    """

    def __init__(
        self,
        metadata_manager: MetadataManager,
        storage_backend: StorageBackend,
        config: RestoreConfig,
        progress_callback: Optional[Callable[[RestoreProgress], None]] = None,
    ):
        """
        Initialisiert Restore-Engine

        Args:
            metadata_manager: MetadataManager-Instanz
            storage_backend: Storage-Backend für Downloads
            config: Restore-Konfiguration
            progress_callback: Optional Callback für Progress-Updates
        """
        self.metadata_manager = metadata_manager
        self.storage = storage_backend
        self.config = config
        self.progress_callback = progress_callback

        # Initialisiere Komponenten
        self.compressor = Compressor()
        # Encryptor wird erst erstellt, wenn Salt aus Backup-Metadaten geladen wurde
        self.encryptor = None

        logger.info("Restore-Engine initialisiert")

    def restore_full_backup(self, backup_id: int) -> RestoreResult:
        """
        Stellt komplettes Backup wieder her

        Args:
            backup_id: ID des Backups

        Returns:
            RestoreResult mit Statistiken

        Raises:
            ValueError: Wenn Backup nicht gefunden
            RuntimeError: Bei Restore-Fehler
        """
        start_time = datetime.now()

        logger.info(f"Starte Wiederherstellung von Backup {backup_id}")

        try:
            # Hole Backup-Informationen
            backup = self.metadata_manager.get_backup(backup_id)
            if not backup:
                raise ValueError(f"Backup {backup_id} nicht gefunden")

            if backup["status"] != "completed":
                raise ValueError(
                    f"Backup {backup_id} hat Status '{backup['status']}', "
                    f"nur 'completed' Backups können wiederhergestellt werden"
                )

            # Lade Salt aus Metadaten und erstelle Encryptor
            salt = backup.get("salt")
            if not salt:
                raise ValueError(
                    f"Backup {backup_id} hat keinen Salt gespeichert. "
                    "Möglicherweise wurde es mit einer älteren Version erstellt."
                )

            # Initialisiere Encryptor mit korrektem Salt
            self.encryptor = Encryptor(password=self.config.password, salt=salt)
            logger.info(f"Encryptor initialisiert mit Salt aus Backup {backup_id}")

            # Log: Restore gestartet
            self.metadata_manager.add_log(
                level="INFO",
                message=f"Wiederherstellung gestartet",
                backup_id=backup_id,
                details=f"Ziel: {self.config.destination_path}",
            )

            # Progress initialisieren
            progress = RestoreProgress(phase="preparing")
            self._report_progress(progress)

            # Hole alle Dateien des Backups
            files = self.metadata_manager.get_backup_files(backup_id)
            non_deleted_files = [f for f in files if not f.get("is_deleted", False)]

            progress.files_total = len(non_deleted_files)
            progress.bytes_total = sum(f["file_size"] for f in non_deleted_files)

            logger.info(
                f"Backup {backup_id}: {len(non_deleted_files)} Dateien, "
                f"{progress.bytes_total / 1024 / 1024:.1f}MB"
            )

            # Erstelle temporäres Verzeichnis für Archive
            temp_dir = self.config.destination_path / ".scrat_restore_temp"
            temp_dir.mkdir(parents=True, exist_ok=True)

            try:
                # 1. Lade Archive vom Storage
                progress.phase = "downloading"
                self._report_progress(progress)

                archive_paths = self._download_archives(backup, temp_dir, progress)

                # 2. Entschlüssele Archive
                progress.phase = "decrypting"
                self._report_progress(progress)

                decrypted_paths = self._decrypt_archives(archive_paths, temp_dir, progress)

                # 3. Entpacke Archive
                progress.phase = "extracting"
                self._report_progress(progress)

                extracted_files = self._extract_archives(
                    decrypted_paths, temp_dir / "extracted", progress
                )

                # 4. Stelle Dateien wieder her
                progress.phase = "restoring"
                self._report_progress(progress)

                files_restored = self._restore_files(extracted_files, non_deleted_files, progress)

                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()

                logger.info(
                    f"Wiederherstellung abgeschlossen: {files_restored} Dateien, "
                    f"Dauer: {duration:.1f}s"
                )

                # Log: Restore erfolgreich
                self.metadata_manager.add_log(
                    level="INFO",
                    message=f"Wiederherstellung erfolgreich abgeschlossen",
                    backup_id=backup_id,
                    details=f"Dateien: {files_restored}, Bytes: {progress.bytes_total / 1024 / 1024:.1f}MB, "
                    f"Dauer: {duration:.1f}s",
                )

                return RestoreResult(
                    success=True,
                    files_restored=files_restored,
                    bytes_restored=progress.bytes_total,
                    duration_seconds=duration,
                    errors=progress.errors,
                )

            finally:
                # Cleanup: Lösche temporäre Dateien
                try:
                    import shutil

                    shutil.rmtree(temp_dir)
                except Exception as e:
                    logger.warning(f"Fehler beim Cleanup: {e}")

        except Exception as e:
            logger.error(f"Fehler bei Wiederherstellung: {e}", exc_info=True)

            # Log: Restore fehlgeschlagen
            try:
                self.metadata_manager.add_log(
                    level="ERROR",
                    message=f"Wiederherstellung fehlgeschlagen",
                    backup_id=backup_id,
                    details=str(e),
                )
            except Exception:
                pass

            raise RuntimeError(f"Wiederherstellung fehlgeschlagen: {e}") from e

    def restore_to_point_in_time(self, target_datetime: datetime) -> RestoreResult:
        """
        Stellt Dateien zu einem bestimmten Zeitpunkt wieder her

        Findet letztes Full-Backup vor dem Zeitpunkt und wendet
        alle Incrementals chronologisch an.

        Args:
            target_datetime: Ziel-Zeitpunkt

        Returns:
            RestoreResult mit Statistiken

        Raises:
            ValueError: Wenn kein Backup für Zeitpunkt gefunden
        """
        logger.info(f"Starte Point-in-Time-Restore für {target_datetime}")

        # Hole alle Backups bis zum Zeitpunkt
        all_backups = self.metadata_manager.get_all_backups()
        relevant_backups = [
            b
            for b in all_backups
            if b["timestamp"] <= target_datetime and b["status"] == "completed"
        ]

        if not relevant_backups:
            raise ValueError(f"Kein Backup vor {target_datetime} gefunden")

        # Sortiere nach Timestamp (neueste zuerst)
        relevant_backups.sort(key=lambda b: b["timestamp"], reverse=True)

        # Finde letztes Full-Backup
        base_backup = None
        for backup in relevant_backups:
            if backup["type"] == "full":
                base_backup = backup
                break

        if not base_backup:
            raise ValueError(f"Kein Full-Backup vor {target_datetime} gefunden")

        base_backup_id = base_backup["id"]
        logger.info(f"Basis-Backup: {base_backup_id} vom {base_backup['timestamp']}")

        # Lade Salt aus Metadaten und erstelle Encryptor
        salt = base_backup.get("salt")
        if not salt:
            raise ValueError(
                f"Basis-Backup {base_backup_id} hat keinen Salt gespeichert. "
                "Möglicherweise wurde es mit einer älteren Version erstellt."
            )

        # Initialisiere Encryptor mit korrektem Salt
        self.encryptor = Encryptor(password=self.config.password, salt=salt)
        logger.info(f"Encryptor initialisiert mit Salt aus Backup {base_backup_id}")

        # Finde alle Incrementals nach dem Base-Backup bis zum Zeitpunkt
        incrementals = [
            b
            for b in relevant_backups
            if b["type"] == "incremental"
            and b["timestamp"] > base_backup["timestamp"]
            and b["timestamp"] <= target_datetime
        ]

        # Sortiere Incrementals chronologisch
        incrementals.sort(key=lambda b: b["timestamp"])

        logger.info(f"Gefunden: 1 Full + {len(incrementals)} Incrementals")

        # Sammle alle Dateien (Base + Incrementals)
        file_state = self._build_file_state(base_backup_id, incrementals)

        # Stelle Dateien wieder her
        return self._restore_file_state(file_state)

    def restore_specific_files(self, backup_id: int, file_patterns: List[str]) -> RestoreResult:
        """
        Stellt spezifische Dateien wieder her (Partial Restore)

        Args:
            backup_id: ID des Backups
            file_patterns: Liste von Datei-Mustern (z.B. ["*.pdf", "Documents/*"])

        Returns:
            RestoreResult mit Statistiken
        """
        logger.info(f"Starte Partial-Restore aus Backup {backup_id}")

        # Hole Backup-Informationen
        backup = self.metadata_manager.get_backup(backup_id)
        if not backup:
            raise ValueError(f"Backup {backup_id} nicht gefunden")

        # Hole alle Dateien
        all_files = self.metadata_manager.get_backup_files(backup_id)

        # Filtere nach Patterns
        matching_files = []
        for file_entry in all_files:
            if file_entry.get("is_deleted"):
                continue

            relative_path = file_entry["relative_path"]
            if self._matches_pattern(relative_path, file_patterns):
                matching_files.append(file_entry)

        logger.info(f"Gefunden: {len(matching_files)} passende Dateien")

        if not matching_files:
            return RestoreResult(
                success=True, files_restored=0, bytes_restored=0, duration_seconds=0.0
            )

        # TODO: Implementiere selektive Wiederherstellung
        # (Nur benötigte Archive herunterladen/entpacken)

        # Für jetzt: Vereinfachte Implementierung - stelle komplettes Backup wieder her
        # und kopiere nur passende Dateien
        logger.warning("Partial-Restore nutzt vorerst Full-Restore-Implementierung")
        return self.restore_full_backup(backup_id)

    def search_files(self, search_term: str, backup_id: Optional[int] = None) -> List[FileEntry]:
        """
        Sucht Dateien in Metadaten

        Args:
            search_term: Suchbegriff (in Dateinamen)
            backup_id: Optional: Nur in bestimmtem Backup suchen

        Returns:
            Liste von FileEntry-Objekten
        """
        logger.info(f"Suche nach '{search_term}'")

        results = self.metadata_manager.search_files(source_path=search_term, backup_id=backup_id)

        # Konvertiere zu FileEntry-Objekten
        file_entries = []
        for result in results:
            entry = FileEntry(
                relative_path=result["relative_path"],
                file_size=result["file_size"],
                modified_timestamp=result["modified_timestamp"],
                archive_name=result["archive_name"],
                archive_path=result["archive_path"],
                backup_id=result.get("backup_id", backup_id or 0),
                is_deleted=result.get("is_deleted", False),
            )
            file_entries.append(entry)

        logger.info(f"Gefunden: {len(file_entries)} Dateien")
        return file_entries

    def _download_archives(
        self, backup: dict, temp_dir: Path, progress: RestoreProgress
    ) -> List[Path]:
        """
        Lädt Archive vom Storage herunter

        Args:
            backup: Backup-Informationen
            temp_dir: Temporäres Verzeichnis
            progress: Progress-Objekt

        Returns:
            Liste heruntergeladener Archive-Pfade
        """
        # Rekonstruiere backup_id wie BackupEngine es erstellt
        # Format: YYYYMMDD_HHMMSS_type (z.B. "20251220_103931_full")
        timestamp_str = backup.get("timestamp", "")
        backup_type = backup.get("type", "full")

        if timestamp_str:
            # Parse ISO timestamp und konvertiere zu BackupEngine-Format
            try:
                from datetime import datetime

                dt = datetime.fromisoformat(timestamp_str)
                backup_id_str = dt.strftime("%Y%m%d_%H%M%S") + f"_{backup_type}"
            except Exception:
                # Fallback bei Parse-Fehler
                backup_id_str = f"backup_{backup['id']}"
        else:
            backup_id_str = f"backup_{backup['id']}"

        # Konstruiere Backup-Pfad
        # BackupEngine erstellt: destination_path / backup_id / *.7z.enc
        backup_base = Path(backup["destination_path"])
        backup_dir = backup_base / backup_id_str

        logger.info(f"Suche Archive in: {backup_dir}")

        if not backup_dir.exists():
            raise ValueError(f"Backup-Verzeichnis nicht gefunden: {backup_dir}")

        # Finde alle verschlüsselten Archive (.enc Dateien)
        enc_files = list(backup_dir.glob("*.enc"))

        if not enc_files:
            raise ValueError(f"Keine verschlüsselten Archive gefunden in {backup_dir}")

        logger.info(f"Gefunden: {len(enc_files)} verschlüsselte Archive")

        # Für USB/Local Storage: Kopiere Archive ins temp_dir
        downloaded = []
        for enc_file in enc_files:
            dest_path = temp_dir / enc_file.name
            logger.debug(f"Kopiere {enc_file.name} nach {dest_path}")

            # Nutze Storage-Backend für Copy
            # (Für jetzt: Direkte Kopie, später über storage.download())
            import shutil

            shutil.copy2(enc_file, dest_path)
            downloaded.append(dest_path)

            # Progress aktualisieren
            progress.bytes_processed += enc_file.stat().st_size
            self._report_progress(progress)

        logger.info(f"Archive heruntergeladen: {len(downloaded)}")
        return downloaded

    def _decrypt_archives(
        self, archive_paths: List[Path], temp_dir: Path, progress: RestoreProgress
    ) -> List[Path]:
        """Entschlüsselt Archive"""
        decrypted = []

        for archive_path in archive_paths:
            decrypted_path = temp_dir / f"{archive_path.stem}_decrypted.7z"
            self.encryptor.decrypt_file(archive_path, decrypted_path)
            decrypted.append(decrypted_path)
            progress.files_processed += 1
            self._report_progress(progress)

        return decrypted

    def _extract_archives(
        self, archive_paths: List[Path], extract_dir: Path, progress: RestoreProgress
    ) -> List[Path]:
        """Entpackt Archive"""
        extract_dir.mkdir(parents=True, exist_ok=True)
        all_extracted = []

        for archive_path in archive_paths:
            extracted = self.compressor.extract_archive(archive_path, extract_dir)
            all_extracted.extend(extracted)

        return all_extracted

    def _restore_files(
        self,
        extracted_files: List[Path],
        file_metadata: List[dict],
        progress: RestoreProgress,
    ) -> int:
        """Kopiert extrahierte Dateien zu ihren Ziel-Pfaden"""
        import shutil

        restored_count = 0

        # Bestimme extract_dir (wo die Dateien entpackt wurden)
        # extracted_files liegen in temp_dir/extracted/relative_path
        if extracted_files:
            # Nimm erste Datei und finde extract_dir
            first_file = extracted_files[0]
            # Gehe hoch bis wir "extracted" finden
            extract_dir = first_file.parent
            while extract_dir.name != "extracted" and extract_dir.parent != extract_dir:
                extract_dir = extract_dir.parent
            logger.info(f"Extract-Dir: {extract_dir}")
        else:
            logger.warning("Keine extrahierten Dateien gefunden!")
            return 0

        for file_meta in file_metadata:
            relative_path = file_meta["relative_path"]
            source_path = file_meta.get("source_path", "")

            # Konstruiere Ziel-Pfad basierend auf restore_to_original Option
            if self.config.restore_to_original and source_path:
                # Original-Restore: Zurück zum ursprünglichen Ort
                dest_path = Path(source_path) / relative_path
                logger.info(f"[RESTORE] Modus: Original-Location")
            else:
                # Custom-Restore: In benutzerdefinierten Ordner
                if source_path:
                    source_dir_name = Path(source_path).name
                    dest_path = Path(self.config.destination_path) / source_dir_name / relative_path
                else:
                    # Fallback wenn source_path fehlt
                    dest_path = Path(self.config.destination_path) / relative_path
                logger.info(f"[RESTORE] Modus: Custom-Location")

            # Debug-Logging
            logger.info(f"[RESTORE] source_path={source_path}")
            logger.info(f"[RESTORE] relative_path={relative_path}")
            logger.info(f"[RESTORE] dest_path={dest_path}")
            logger.info(f"[RESTORE] dest_path.parent={dest_path.parent}")

            # Finde extrahierte Datei
            # Direkter Lookup: extract_dir/relative_path
            source_file = extract_dir / relative_path

            if not source_file.exists():
                logger.warning(f"Extrahierte Datei nicht gefunden: {source_file}")
                logger.debug(f"Gesucht: {relative_path} in {extract_dir}")
                continue

            # Prüfe ob source_file eine Datei ist (nicht Verzeichnis)
            if not source_file.is_file():
                logger.warning(f"Überspringe Verzeichnis: {source_file}")
                continue

            # WICHTIG: Erstelle nur das PARENT-Verzeichnis, NICHT dest_path selbst!
            parent_dir = dest_path.parent
            logger.info(f"[RESTORE] Erstelle Parent-Dir: {parent_dir}")
            parent_dir.mkdir(parents=True, exist_ok=True)

            # Prüfe ob Datei bereits existiert
            if dest_path.exists():
                if dest_path.is_dir():
                    logger.warning(f"⚠️  FEHLER: Ziel existiert bereits als VERZEICHNIS: {dest_path}")
                    logger.warning(f"⚠️  Lösche Verzeichnis: {dest_path}")
                    import shutil as shutil_module
                    shutil_module.rmtree(dest_path)
                else:
                    # Datei existiert bereits
                    if not self.config.overwrite_existing:
                        logger.warning(f"⏭️  Überspringe (existiert bereits): {dest_path}")
                        progress.files_processed += 1
                        progress.current_file = relative_path
                        self._report_progress(progress)
                        continue
                    else:
                        logger.info(f"Überschreibe existierende Datei: {dest_path}")

            # Kopiere Datei
            try:
                shutil.copy2(source_file, dest_path)
                logger.info(f"Wiederhergestellt: {relative_path} → {dest_path}")
                restored_count += 1
            except Exception as e:
                logger.error(f"Fehler beim Kopieren von {relative_path}: {e}")
                continue

            progress.files_processed += 1
            progress.current_file = relative_path
            self._report_progress(progress)

        return restored_count

    def _build_file_state(self, base_backup_id: int, incrementals: List[dict]) -> dict:
        """Baut Datei-Zustand zu einem Zeitpunkt auf"""
        # Hole Dateien aus Base-Backup
        file_state = {}
        base_files = self.metadata_manager.get_backup_files(base_backup_id)

        for file_entry in base_files:
            relative_path = file_entry["relative_path"]
            file_state[relative_path] = file_entry

        # Wende Incrementals an
        for incr_backup in incrementals:
            incr_files = self.metadata_manager.get_backup_files(incr_backup["id"])

            for file_entry in incr_files:
                relative_path = file_entry["relative_path"]

                if file_entry.get("is_deleted"):
                    # Datei wurde gelöscht
                    if relative_path in file_state:
                        del file_state[relative_path]
                else:
                    # Datei wurde hinzugefügt/geändert
                    file_state[relative_path] = file_entry

        return file_state

    def _restore_file_state(self, file_state: dict) -> RestoreResult:
        """Stellt Dateien aus File-State wieder her"""
        # Placeholder: Nutze restore_full_backup-Logik
        logger.warning("Point-in-Time-Restore noch nicht vollständig implementiert")
        return RestoreResult(
            success=False, files_restored=0, bytes_restored=0, duration_seconds=0.0
        )

    def _matches_pattern(self, file_path: str, patterns: List[str]) -> bool:
        """Prüft ob Datei-Pfad zu einem Pattern passt"""
        import fnmatch

        for pattern in patterns:
            if fnmatch.fnmatch(file_path, pattern):
                return True
        return False

    def _report_progress(self, progress: RestoreProgress) -> None:
        """Meldet Fortschritt via Callback"""
        if self.progress_callback:
            self.progress_callback(progress)

        logger.debug(
            f"Progress: {progress.phase}, "
            f"{progress.files_processed}/{progress.files_total} Dateien"
        )
