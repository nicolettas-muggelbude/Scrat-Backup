"""
Unit-Tests für USBStorage
"""

from pathlib import Path

import pytest

from src.storage.usb_storage import USBStorage


@pytest.fixture
def storage_base(tmp_path):
    """Temporäres Storage-Verzeichnis"""
    storage_dir = tmp_path / "storage"
    storage_dir.mkdir()
    return storage_dir


@pytest.fixture
def usb_storage(storage_base):
    """USBStorage-Instanz"""
    storage = USBStorage(storage_base)
    storage.connect()
    yield storage
    storage.disconnect()


class TestUSBStorageInit:
    """Tests für Initialisierung"""

    def test_init(self, storage_base):
        """Test Initialisierung"""
        storage = USBStorage(storage_base)
        assert storage.base_path == storage_base
        assert not storage.connected

    def test_connect_success(self, storage_base):
        """Test erfolgreiche Verbindung"""
        storage = USBStorage(storage_base)
        assert storage.connect()
        assert storage.connected
        storage.disconnect()

    def test_connect_nonexistent_path(self, tmp_path):
        """Test Verbindung zu nicht existierendem Pfad"""
        storage = USBStorage(tmp_path / "nonexistent")
        with pytest.raises(ConnectionError, match="Basis-Pfad nicht verfügbar"):
            storage.connect()

    def test_connect_file_instead_of_dir(self, tmp_path):
        """Test Verbindung zu Datei statt Verzeichnis"""
        file_path = tmp_path / "file.txt"
        file_path.write_text("test")
        storage = USBStorage(file_path)
        with pytest.raises(ConnectionError, match="ist kein Verzeichnis"):
            storage.connect()


class TestUSBStorageUploadDownload:
    """Tests für Upload/Download"""

    def test_upload_file_success(self, usb_storage, tmp_path):
        """Test erfolgreicher Upload"""
        # Erstelle Test-Datei
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content")

        # Upload
        result = usb_storage.upload_file(test_file, "uploaded.txt")
        assert result is True

        # Prüfe dass Datei existiert
        uploaded = usb_storage.base_path / "uploaded.txt"
        assert uploaded.exists()
        assert uploaded.read_text() == "Test content"

    def test_upload_file_with_subdirs(self, usb_storage, tmp_path):
        """Test Upload in Unterverzeichnis"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Content")

        result = usb_storage.upload_file(test_file, "subdir/file.txt")
        assert result is True
        assert (usb_storage.base_path / "subdir" / "file.txt").exists()

    def test_upload_nonexistent_file(self, usb_storage, tmp_path):
        """Test Upload nicht existierender Datei"""
        with pytest.raises(FileNotFoundError):
            usb_storage.upload_file(tmp_path / "nonexistent.txt", "dest.txt")

    def test_upload_while_disconnected(self, storage_base, tmp_path):
        """Test Upload ohne Verbindung"""
        storage = USBStorage(storage_base)
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test")

        with pytest.raises(ConnectionError, match="Nicht verbunden"):
            storage.upload_file(test_file, "dest.txt")

    def test_download_file_success(self, usb_storage, tmp_path):
        """Test erfolgreicher Download"""
        # Erstelle Datei im Storage
        source = usb_storage.base_path / "source.txt"
        source.write_text("Download me")

        # Download
        dest = tmp_path / "downloaded.txt"
        result = usb_storage.download_file("source.txt", dest)
        assert result is True
        assert dest.read_text() == "Download me"

    def test_download_nonexistent_file(self, usb_storage, tmp_path):
        """Test Download nicht existierender Datei"""
        with pytest.raises(FileNotFoundError):
            usb_storage.download_file("nonexistent.txt", tmp_path / "dest.txt")


class TestUSBStorageFileOperations:
    """Tests für Datei-Operationen"""

    def test_list_files(self, usb_storage):
        """Test Dateien auflisten"""
        # Erstelle Test-Dateien
        (usb_storage.base_path / "file1.txt").write_text("1")
        (usb_storage.base_path / "file2.txt").write_text("2")
        subdir = usb_storage.base_path / "subdir"
        subdir.mkdir()

        files = usb_storage.list_files("")
        assert len(files) == 2
        assert "file1.txt" in files
        assert "file2.txt" in files
        assert "subdir" not in files  # Nur Dateien, keine Verzeichnisse

    def test_list_files_in_subdir(self, usb_storage):
        """Test Dateien in Unterverzeichnis auflisten"""
        subdir = usb_storage.base_path / "subdir"
        subdir.mkdir()
        (subdir / "nested.txt").write_text("nested")

        files = usb_storage.list_files("subdir")
        assert len(files) == 1
        assert "nested.txt" in files

    def test_list_files_nonexistent_dir(self, usb_storage):
        """Test Listing in nicht existierendem Verzeichnis"""
        with pytest.raises(FileNotFoundError):
            usb_storage.list_files("nonexistent")

    def test_delete_file(self, usb_storage):
        """Test Datei löschen"""
        file_path = usb_storage.base_path / "to_delete.txt"
        file_path.write_text("Delete me")

        result = usb_storage.delete_file("to_delete.txt")
        assert result is True
        assert not file_path.exists()

    def test_delete_nonexistent_file(self, usb_storage):
        """Test Löschen nicht existierender Datei"""
        with pytest.raises(FileNotFoundError):
            usb_storage.delete_file("nonexistent.txt")


class TestUSBStorageDirectoryOperations:
    """Tests für Verzeichnis-Operationen"""

    def test_create_directory(self, usb_storage):
        """Test Verzeichnis erstellen"""
        result = usb_storage.create_directory("newdir")
        assert result is True
        assert (usb_storage.base_path / "newdir").is_dir()

    def test_create_nested_directory(self, usb_storage):
        """Test verschachteltes Verzeichnis erstellen"""
        result = usb_storage.create_directory("a/b/c")
        assert result is True
        assert (usb_storage.base_path / "a" / "b" / "c").is_dir()

    def test_delete_empty_directory(self, usb_storage):
        """Test leeres Verzeichnis löschen"""
        dir_path = usb_storage.base_path / "emptydir"
        dir_path.mkdir()

        result = usb_storage.delete_directory("emptydir", recursive=False)
        assert result is True
        assert not dir_path.exists()

    def test_delete_directory_recursive(self, usb_storage):
        """Test Verzeichnis rekursiv löschen"""
        dir_path = usb_storage.base_path / "fulldir"
        dir_path.mkdir()
        (dir_path / "file.txt").write_text("content")

        result = usb_storage.delete_directory("fulldir", recursive=True)
        assert result is True
        assert not dir_path.exists()

    def test_exists_file(self, usb_storage):
        """Test exists für Datei"""
        file_path = usb_storage.base_path / "exists.txt"
        file_path.write_text("I exist")

        assert usb_storage.exists("exists.txt")
        assert not usb_storage.exists("not_exists.txt")

    def test_exists_directory(self, usb_storage):
        """Test exists für Verzeichnis"""
        dir_path = usb_storage.base_path / "existsdir"
        dir_path.mkdir()

        assert usb_storage.exists("existsdir")


class TestUSBStorageSpaceAndConnection:
    """Tests für Speicherplatz und Verbindung"""

    def test_get_available_space(self, usb_storage):
        """Test Speicherplatz abrufen"""
        space = usb_storage.get_available_space()
        assert space > 0

    def test_test_connection(self, usb_storage):
        """Test Verbindung testen"""
        assert usb_storage.test_connection() is True

    def test_test_connection_after_disconnect(self, storage_base):
        """Test Verbindung nach Disconnect"""
        storage = USBStorage(storage_base)
        storage.connect()
        storage.disconnect()
        # test_connection sollte trotzdem funktionieren
        assert storage.test_connection() is True


class TestUSBStorageContextManager:
    """Tests für Context Manager"""

    def test_context_manager(self, storage_base, tmp_path):
        """Test Context Manager Usage"""
        with USBStorage(storage_base) as storage:
            test_file = tmp_path / "test.txt"
            test_file.write_text("Context test")
            storage.upload_file(test_file, "ctx_test.txt")

        # Nach with-Block sollte Datei existieren
        assert (storage_base / "ctx_test.txt").exists()


class TestUSBStorageProgressCallback:
    """Tests für Progress-Callback"""

    def test_upload_with_progress(self, usb_storage, tmp_path):
        """Test Upload mit Progress-Callback"""
        # Erstelle größere Test-Datei
        test_file = tmp_path / "large.bin"
        test_file.write_bytes(b"x" * (5 * 1024 * 1024))  # 5MB

        progress_calls = []

        def progress_callback(bytes_transferred, total_bytes):
            progress_calls.append((bytes_transferred, total_bytes))

        usb_storage.upload_file(test_file, "large.bin", progress_callback=progress_callback)

        # Callback sollte aufgerufen worden sein
        assert len(progress_calls) > 0
        # Letzter Call sollte 100% sein
        last_call = progress_calls[-1]
        assert last_call[0] == last_call[1]

    def test_download_with_progress(self, usb_storage, tmp_path):
        """Test Download mit Progress-Callback"""
        # Erstelle Datei im Storage
        source = usb_storage.base_path / "large.bin"
        source.write_bytes(b"y" * (5 * 1024 * 1024))  # 5MB

        progress_calls = []

        def progress_callback(bytes_transferred, total_bytes):
            progress_calls.append((bytes_transferred, total_bytes))

        usb_storage.download_file(
            "large.bin", tmp_path / "downloaded.bin", progress_callback=progress_callback
        )

        assert len(progress_calls) > 0
