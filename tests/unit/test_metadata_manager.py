"""
Unit-Tests für MetadataManager
"""

from datetime import datetime

import pytest

from core.metadata_manager import MetadataManager


class TestMetadataManager:
    """Tests für MetadataManager-Klasse"""

    @pytest.fixture
    def db_path(self, tmp_path):
        """Temporärer Datenbank-Pfad"""
        return tmp_path / "test.db"

    @pytest.fixture
    def manager(self, db_path):
        """MetadataManager-Instanz für Tests"""
        with MetadataManager(db_path) as mgr:
            yield mgr

    def test_initialization_creates_database(self, db_path):
        """Test: Initialisierung erstellt Datenbank"""
        assert not db_path.exists()

        with MetadataManager(db_path):
            pass

        assert db_path.exists()

    def test_schema_tables_created(self, manager):
        """Test: Alle Tabellen werden erstellt"""
        cursor = manager.connection.cursor()

        # Prüfe ob alle Tabellen existieren
        cursor.execute(
            """
            SELECT name FROM sqlite_master
            WHERE type='table'
            ORDER BY name
        """
        )

        tables = [row[0] for row in cursor.fetchall()]

        expected_tables = [
            "backups",
            "backup_files",
            "sources",
            "destinations",
            "schedules",
            "logs",
            "schema_info",
        ]

        for table in expected_tables:
            assert table in tables, f"Tabelle {table} fehlt"

    def test_create_backup_record(self, manager):
        """Test: Backup-Record erstellen"""
        backup_id = manager.create_backup_record(
            backup_type="full",
            destination_type="usb",
            destination_path="/mnt/usb/backup",
            encryption_key_hash="abcd1234",
        )

        assert backup_id > 0

        # Prüfe ob Record existiert
        backup = manager.get_backup(backup_id)
        assert backup is not None
        assert backup["type"] == "full"
        assert backup["status"] == "running"
        assert backup["destination_type"] == "usb"

    def test_update_backup_progress(self, manager):
        """Test: Backup-Fortschritt aktualisieren"""
        backup_id = manager.create_backup_record(
            backup_type="full",
            destination_type="usb",
            destination_path="/backup",
            encryption_key_hash="hash",
        )

        manager.update_backup_progress(
            backup_id=backup_id, files_processed=10, size_original=1000, size_compressed=500
        )

        backup = manager.get_backup(backup_id)
        assert backup["files_processed"] == 10
        assert backup["size_original"] == 1000
        assert backup["size_compressed"] == 500

    def test_mark_backup_completed(self, manager):
        """Test: Backup als abgeschlossen markieren"""
        backup_id = manager.create_backup_record(
            backup_type="full",
            destination_type="usb",
            destination_path="/backup",
            encryption_key_hash="hash",
        )

        manager.mark_backup_completed(backup_id, files_total=100)

        backup = manager.get_backup(backup_id)
        assert backup["status"] == "completed"
        assert backup["files_total"] == 100
        assert backup["completed_at"] is not None

    def test_mark_backup_failed(self, manager):
        """Test: Backup als fehlgeschlagen markieren"""
        backup_id = manager.create_backup_record(
            backup_type="full",
            destination_type="usb",
            destination_path="/backup",
            encryption_key_hash="hash",
        )

        error_msg = "Connection lost"
        manager.mark_backup_failed(backup_id, error_msg)

        backup = manager.get_backup(backup_id)
        assert backup["status"] == "failed"
        assert backup["error_message"] == error_msg

    def test_add_file_to_backup(self, manager):
        """Test: Datei zu Backup hinzufügen"""
        backup_id = manager.create_backup_record(
            backup_type="full",
            destination_type="usb",
            destination_path="/backup",
            encryption_key_hash="hash",
        )

        file_id = manager.add_file_to_backup(
            backup_id=backup_id,
            source_path="/home/user/test.txt",
            relative_path="test.txt",
            file_size=1024,
            modified_timestamp=datetime.now(),
            archive_name="data.001.7z",
            archive_path="test.txt",
            checksum="abc123",
        )

        assert file_id > 0

        # Prüfe ob Datei abrufbar ist
        files = manager.get_backup_files(backup_id)
        assert len(files) == 1
        assert files[0]["source_path"] == "/home/user/test.txt"
        assert files[0]["file_size"] == 1024

    def test_get_all_backups(self, manager):
        """Test: Alle Backups abrufen"""
        # Erstelle mehrere Backups
        for i in range(3):
            manager.create_backup_record(
                backup_type="full",
                destination_type="usb",
                destination_path=f"/backup{i}",
                encryption_key_hash=f"hash{i}",
            )

        backups = manager.get_all_backups()
        assert len(backups) == 3

    def test_get_backups_filtered_by_status(self, manager):
        """Test: Backups nach Status filtern"""
        # Erstelle Backups mit verschiedenen Status
        backup1 = manager.create_backup_record(
            backup_type="full",
            destination_type="usb",
            destination_path="/backup1",
            encryption_key_hash="hash1",
        )

        backup2 = manager.create_backup_record(
            backup_type="full",
            destination_type="usb",
            destination_path="/backup2",
            encryption_key_hash="hash2",
        )

        manager.mark_backup_completed(backup1, files_total=10)
        # backup2 bleibt 'running'

        completed = manager.get_all_backups(status="completed")
        assert len(completed) == 1
        assert completed[0]["id"] == backup1

        running = manager.get_all_backups(status="running")
        assert len(running) == 1
        assert running[0]["id"] == backup2

    def test_search_files(self, manager):
        """Test: Dateien über alle Backups suchen"""
        backup_id = manager.create_backup_record(
            backup_type="full",
            destination_type="usb",
            destination_path="/backup",
            encryption_key_hash="hash",
        )

        # Füge Dateien hinzu
        manager.add_file_to_backup(
            backup_id=backup_id,
            source_path="/home/user/document.txt",
            relative_path="document.txt",
            file_size=1024,
            modified_timestamp=datetime.now(),
            archive_name="data.001.7z",
            archive_path="document.txt",
        )

        manager.add_file_to_backup(
            backup_id=backup_id,
            source_path="/home/user/image.png",
            relative_path="image.png",
            file_size=2048,
            modified_timestamp=datetime.now(),
            archive_name="data.001.7z",
            archive_path="image.png",
        )

        manager.mark_backup_completed(backup_id, files_total=2)

        # Suche nach .txt Dateien
        results = manager.search_files("document")
        assert len(results) == 1
        assert results[0]["source_path"] == "/home/user/document.txt"

    def test_delete_backup_cascade(self, manager):
        """Test: Backup löschen entfernt auch Dateien (CASCADE)"""
        backup_id = manager.create_backup_record(
            backup_type="full",
            destination_type="usb",
            destination_path="/backup",
            encryption_key_hash="hash",
        )

        # Füge Dateien hinzu
        manager.add_file_to_backup(
            backup_id=backup_id,
            source_path="/home/user/test.txt",
            relative_path="test.txt",
            file_size=1024,
            modified_timestamp=datetime.now(),
            archive_name="data.001.7z",
            archive_path="test.txt",
        )

        files_before = manager.get_backup_files(backup_id)
        assert len(files_before) == 1

        # Lösche Backup
        deleted = manager.delete_backup(backup_id)
        assert deleted is True

        # Prüfe ob Backup weg ist
        backup = manager.get_backup(backup_id)
        assert backup is None

        # Prüfe ob Dateien auch weg sind (CASCADE)
        files_after = manager.get_backup_files(backup_id)
        assert len(files_after) == 0

    def test_get_statistics(self, manager):
        """Test: Statistiken abrufen"""
        # Erstelle Backups
        backup1 = manager.create_backup_record(
            backup_type="full",
            destination_type="usb",
            destination_path="/backup1",
            encryption_key_hash="hash1",
        )

        manager.update_backup_progress(
            backup_id=backup1, files_processed=10, size_original=10000, size_compressed=5000
        )
        manager.mark_backup_completed(backup1, files_total=10)

        backup2 = manager.create_backup_record(
            backup_type="incremental",
            destination_type="usb",
            destination_path="/backup2",
            encryption_key_hash="hash2",
            base_backup_id=backup1,
        )
        manager.update_backup_progress(
            backup_id=backup2, files_processed=5, size_original=5000, size_compressed=2500
        )
        manager.mark_backup_completed(backup2, files_total=5)

        stats = manager.get_statistics()

        assert stats["total_backups"] == 2
        assert stats["completed_backups"] == 2
        assert stats["total_size_original"] == 15000
        assert stats["total_size_compressed"] == 7500

    def test_incremental_backup_with_base(self, manager):
        """Test: Inkrementelles Backup mit Base-Backup"""
        # Erstelle Full-Backup
        full_backup = manager.create_backup_record(
            backup_type="full",
            destination_type="usb",
            destination_path="/backup",
            encryption_key_hash="hash",
        )

        # Erstelle Incremental-Backup
        incr_backup = manager.create_backup_record(
            backup_type="incremental",
            destination_type="usb",
            destination_path="/backup",
            encryption_key_hash="hash",
            base_backup_id=full_backup,
        )

        incr = manager.get_backup(incr_backup)
        assert incr["type"] == "incremental"
        assert incr["base_backup_id"] == full_backup

    def test_context_manager(self, db_path):
        """Test: Context Manager funktioniert"""
        with MetadataManager(db_path) as manager:
            assert manager.connection is not None

            backup_id = manager.create_backup_record(
                backup_type="full",
                destination_type="usb",
                destination_path="/backup",
                encryption_key_hash="hash",
            )

            assert backup_id > 0

        # Nach Context Manager sollte Verbindung geschlossen sein
        # (Können wir nicht direkt testen, aber DB sollte existieren)
        assert db_path.exists()
