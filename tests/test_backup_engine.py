"""
Integration-Tests für Backup-Engine
"""

import shutil
import time
from pathlib import Path

import pytest

from src.core.backup_engine import BackupConfig, BackupEngine, BackupProgress
from src.core.metadata_manager import MetadataManager


@pytest.fixture
def temp_source_dir(tmp_path):
    """Temporäres Quell-Verzeichnis mit Test-Dateien"""
    source_dir = tmp_path / "source"
    source_dir.mkdir()

    # Erstelle Test-Dateien
    (source_dir / "file1.txt").write_text("Content 1")
    (source_dir / "file2.txt").write_text("Content 2")

    sub_dir = source_dir / "subdir"
    sub_dir.mkdir()
    (sub_dir / "file3.txt").write_text("Content 3")

    return source_dir


@pytest.fixture
def temp_destination_dir(tmp_path):
    """Temporäres Ziel-Verzeichnis"""
    dest_dir = tmp_path / "destination"
    dest_dir.mkdir()
    return dest_dir


@pytest.fixture
def metadata_db(tmp_path):
    """MetadataManager für Tests"""
    db_path = tmp_path / "test_metadata.db"
    manager = MetadataManager(db_path)
    yield manager
    manager.disconnect()


@pytest.fixture
def backup_config(temp_source_dir, temp_destination_dir):
    """Standard Backup-Konfiguration"""
    return BackupConfig(
        sources=[temp_source_dir],
        destination_path=temp_destination_dir,
        destination_type="usb",
        password="test_password_123",
        compression_level=3,  # Schneller für Tests
        split_size=10 * 1024 * 1024,  # 10MB für Tests
        max_versions=3,
    )


class TestBackupEngineInit:
    """Tests für Backup-Engine-Initialisierung"""

    def test_init_success(self, metadata_db, backup_config):
        """Test erfolgreiche Initialisierung"""
        engine = BackupEngine(metadata_db, backup_config)

        assert engine.metadata_manager == metadata_db
        assert engine.config == backup_config
        assert engine.scanner is not None
        assert engine.compressor is not None
        assert engine.encryptor is not None

    def test_init_with_progress_callback(self, metadata_db, backup_config):
        """Test Initialisierung mit Progress-Callback"""
        callback_called = []

        def progress_callback(progress: BackupProgress):
            callback_called.append(progress)

        engine = BackupEngine(metadata_db, backup_config, progress_callback=progress_callback)
        assert engine.progress_callback == progress_callback


class TestFullBackup:
    """Tests für Vollbackup"""

    def test_full_backup_success(self, metadata_db, backup_config, temp_source_dir):
        """Test erfolgreiches Vollbackup"""
        engine = BackupEngine(metadata_db, backup_config)

        # Erstelle Vollbackup
        result = engine.create_full_backup()

        # Prüfe Result
        assert result.success is True
        assert result.backup_type == "full"
        assert result.files_total == 3
        assert result.size_original > 0
        assert result.size_compressed > 0
        assert result.duration_seconds > 0

        # Prüfe Datenbank
        backups = metadata_db.get_all_backups()
        assert len(backups) == 1
        assert backups[0]["type"] == "full"
        assert backups[0]["status"] == "completed"

        # Prüfe Backup-Verzeichnis
        backup_dirs = list(backup_config.destination_path.iterdir())
        assert len(backup_dirs) == 1
        assert backup_dirs[0].is_dir()

        # Prüfe verschlüsselte Archive
        encrypted_files = list(backup_dirs[0].glob("*.enc"))
        assert len(encrypted_files) > 0

    def test_full_backup_with_progress_callback(self, metadata_db, backup_config, temp_source_dir):
        """Test Vollbackup mit Progress-Tracking"""
        progress_updates = []

        def progress_callback(progress: BackupProgress):
            progress_updates.append(progress)

        engine = BackupEngine(metadata_db, backup_config, progress_callback=progress_callback)
        result = engine.create_full_backup()

        assert result.success is True
        assert len(progress_updates) > 0

        # Prüfe verschiedene Phasen
        phases = [p.phase for p in progress_updates]
        assert "scanning" in phases
        assert "compressing" in phases
        assert "encrypting" in phases

    def test_full_backup_empty_source(self, metadata_db, backup_config, tmp_path):
        """Test Vollbackup mit leerem Quell-Verzeichnis"""
        empty_source = tmp_path / "empty_source"
        empty_source.mkdir()

        config = BackupConfig(
            sources=[empty_source],
            destination_path=backup_config.destination_path,
            destination_type="usb",
            password="test123",
        )

        engine = BackupEngine(metadata_db, config)
        result = engine.create_full_backup()

        # Sollte erfolgreich sein, aber 0 Dateien
        assert result.success is True
        assert result.files_total == 0

    def test_full_backup_multiple_sources(self, metadata_db, backup_config, tmp_path):
        """Test Vollbackup mit mehreren Quellen"""
        # Erstelle zweite Quelle
        source2 = tmp_path / "source2"
        source2.mkdir()
        (source2 / "extra1.txt").write_text("Extra 1")
        (source2 / "extra2.txt").write_text("Extra 2")

        config = BackupConfig(
            sources=[backup_config.sources[0], source2],
            destination_path=backup_config.destination_path,
            destination_type="usb",
            password="test123",
        )

        engine = BackupEngine(metadata_db, config)
        result = engine.create_full_backup()

        # Sollte Dateien aus beiden Quellen haben
        assert result.success is True
        assert result.files_total == 5  # 3 aus source1 + 2 aus source2


class TestIncrementalBackup:
    """Tests für inkrementelles Backup"""

    def test_incremental_without_base_fails(self, metadata_db, backup_config):
        """Test inkrementelles Backup ohne Basis schlägt fehl"""
        engine = BackupEngine(metadata_db, backup_config)

        with pytest.raises(ValueError, match="Kein Basis-Backup gefunden"):
            engine.create_incremental_backup()

    def test_incremental_backup_with_changes(self, metadata_db, backup_config, temp_source_dir):
        """Test inkrementelles Backup mit Änderungen"""
        engine = BackupEngine(metadata_db, backup_config)

        # Erstelle Basis-Backup
        full_result = engine.create_full_backup()
        assert full_result.success is True

        # Warte kurz
        time.sleep(1)

        # Füge neue Datei hinzu
        (temp_source_dir / "new_file.txt").write_text("New content")

        # Ändere existierende Datei
        (temp_source_dir / "file1.txt").write_text("Modified content")

        # Erstelle inkrementelles Backup
        incr_result = engine.create_incremental_backup()

        # Sollte 2 geänderte Dateien haben
        assert incr_result.success is True
        assert incr_result.backup_type == "incremental"
        assert incr_result.files_total == 2

        # Prüfe Datenbank
        backups = metadata_db.get_all_backups()
        assert len(backups) == 2
        assert backups[0]["type"] == "incremental"

    def test_incremental_backup_no_changes(self, metadata_db, backup_config, temp_source_dir):
        """Test inkrementelles Backup ohne Änderungen"""
        engine = BackupEngine(metadata_db, backup_config)

        # Erstelle Basis-Backup
        full_result = engine.create_full_backup()
        assert full_result.success is True

        # Erstelle inkrementelles Backup ohne Änderungen
        incr_result = engine.create_incremental_backup()

        # Sollte erfolgreich sein mit 0 Dateien
        assert incr_result.success is True
        assert incr_result.files_total == 0

    def test_incremental_backup_with_deletion(self, metadata_db, backup_config, temp_source_dir):
        """Test inkrementelles Backup mit gelöschten Dateien"""
        engine = BackupEngine(metadata_db, backup_config)

        # Erstelle Basis-Backup
        full_result = engine.create_full_backup()
        assert full_result.success is True

        # Lösche Datei
        (temp_source_dir / "file1.txt").unlink()

        # Warte kurz
        time.sleep(1)

        # Erstelle inkrementelles Backup
        incr_result = engine.create_incremental_backup()

        # Prüfe, dass gelöschte Datei in DB markiert ist
        backups = metadata_db.get_all_backups()
        incr_backup_id = backups[0]["id"]

        files = metadata_db.get_backup_files(incr_backup_id)
        deleted_files = [f for f in files if f.get("is_deleted")]
        assert len(deleted_files) == 1


class TestVersionRotation:
    """Tests für Versionierungs-Rotation"""

    def test_rotation_with_max_versions(self, metadata_db, backup_config, temp_source_dir):
        """Test Rotation bei Überschreitung max_versions"""
        engine = BackupEngine(metadata_db, backup_config)

        # Erstelle mehr Backups als max_versions (3)
        for i in range(5):
            if i == 0:
                engine.create_full_backup()
            else:
                # Ändere Datei für inkrementelles Backup
                (temp_source_dir / "file1.txt").write_text(f"Content {i}")
                time.sleep(0.1)
                engine.create_incremental_backup()

        # Prüfe, dass nur max_versions Backups existieren
        backups = metadata_db.get_all_backups()
        completed_backups = [b for b in backups if b["status"] == "completed"]
        assert len(completed_backups) == backup_config.max_versions

    def test_no_rotation_below_max_versions(self, metadata_db, backup_config, temp_source_dir):
        """Test keine Rotation wenn unter max_versions"""
        engine = BackupEngine(metadata_db, backup_config)

        # Erstelle nur 2 Backups
        engine.create_full_backup()

        (temp_source_dir / "file1.txt").write_text("Modified")
        time.sleep(0.1)
        engine.create_incremental_backup()

        # Beide sollten noch existieren
        backups = metadata_db.get_all_backups()
        assert len(backups) == 2


class TestBackupProgress:
    """Tests für BackupProgress"""

    def test_progress_percentage_calculation(self):
        """Test Progress-Percentage-Berechnung"""
        progress = BackupProgress(
            backup_id="test",
            phase="compressing",
            bytes_total=1000,
            bytes_processed=250,
        )

        assert progress.progress_percentage == 25.0

    def test_progress_percentage_zero_total(self):
        """Test Progress mit zero total"""
        progress = BackupProgress(
            backup_id="test", phase="scanning", bytes_total=0, bytes_processed=0
        )

        assert progress.progress_percentage == 0.0


class TestBackupWithExcludePatterns:
    """Tests für Backup mit Exclude-Patterns"""

    def test_backup_excludes_patterns(self, metadata_db, backup_config, tmp_path):
        """Test Backup schließt Patterns aus"""
        # Erstelle Quelle mit ausgeschlossenen Dateien
        source = tmp_path / "source_exclude"
        source.mkdir()

        (source / "include.txt").write_text("Include me")
        (source / "exclude.tmp").write_text("Exclude me")
        (source / "Thumbs.db").write_text("System file")

        config = BackupConfig(
            sources=[source],
            destination_path=backup_config.destination_path,
            destination_type="usb",
            password="test123",
            exclude_patterns={"*.tmp", "Thumbs.db"},
        )

        engine = BackupEngine(metadata_db, config)
        result = engine.create_full_backup()

        # Sollte nur 1 Datei gesichert haben
        assert result.success is True
        assert result.files_total == 1


class TestBackupErrorHandling:
    """Tests für Fehlerbehandlung"""

    def test_backup_handles_scan_errors(self, metadata_db, backup_config, tmp_path):
        """Test Backup behandelt Scan-Fehler"""
        # Erstelle Quelle
        source = tmp_path / "source_errors"
        source.mkdir()
        (source / "good.txt").write_text("Good file")

        engine = BackupEngine(metadata_db, backup_config)

        # Backup sollte trotz möglicher Fehler durchlaufen
        result = engine.create_full_backup()
        assert result.success is True
