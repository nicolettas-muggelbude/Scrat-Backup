"""
Unit-Tests für WebDAVStorage

Hinweis: Diese Tests verwenden Mocks, da ein echter WebDAV-Server
für Unit-Tests nicht praktikabel ist. Integration-Tests mit echtem
Server sollten separat durchgeführt werden.
"""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.storage.webdav_storage import WebDAVStorage


@pytest.fixture
def webdav_config():
    """WebDAV-Konfiguration für Tests"""
    return {
        "url": "https://nextcloud.example.com/remote.php/dav/files/testuser/",
        "username": "testuser",
        "password": "testpass",
        "base_path": "/scrat-backups",
        "timeout": 30,
    }


@pytest.fixture
def webdav_storage(webdav_config):
    """WebDAVStorage-Instanz"""
    return WebDAVStorage(**webdav_config)


class TestWebDAVStorageInit:
    """Tests für Initialisierung"""

    def test_init(self, webdav_config):
        """Test Initialisierung"""
        storage = WebDAVStorage(**webdav_config)
        assert storage.url == "https://nextcloud.example.com/remote.php/dav/files/testuser"
        assert storage.username == "testuser"
        assert storage.password == "testpass"
        assert storage.base_path == "scrat-backups"
        assert storage.timeout == 30
        assert storage.client is None

    def test_init_url_normalization(self):
        """Test dass trailing slash entfernt wird"""
        storage = WebDAVStorage(
            url="https://example.com/dav/",
            username="user",
            password="pass",
        )
        assert storage.url == "https://example.com/dav"

    def test_init_without_auth(self):
        """Test Initialisierung ohne Authentifizierung (öffentliche Shares)"""
        storage = WebDAVStorage(url="https://example.com/public/share/")
        assert storage.username == ""
        assert storage.password == ""

    @patch("webdav3.client.Client")
    def test_connect_success(self, mock_client_class, webdav_storage):
        """Test erfolgreiche Verbindung"""
        # Mock Client
        mock_client = Mock()
        mock_client.check.return_value = True
        mock_client_class.return_value = mock_client

        result = webdav_storage.connect()

        assert result is True
        assert webdav_storage.client == mock_client

        # Verify Client wurde mit korrekten Optionen erstellt
        mock_client_class.assert_called_once()
        call_args = mock_client_class.call_args[0][0]
        assert (
            call_args["webdav_hostname"]
            == "https://nextcloud.example.com/remote.php/dav/files/testuser"
        )
        assert call_args["webdav_login"] == "testuser"
        assert call_args["webdav_password"] == "testpass"
        assert call_args["webdav_timeout"] == 30

        # Verify check wurde aufgerufen
        mock_client.check.assert_called()

    @patch("webdav3.client.Client")
    def test_connect_without_auth(self, mock_client_class):
        """Test Verbindung ohne Authentifizierung"""
        storage = WebDAVStorage(url="https://example.com/public/")

        mock_client = Mock()
        mock_client.check.return_value = True
        mock_client_class.return_value = mock_client

        storage.connect()

        # Verify keine Login-Daten übergeben wurden
        call_args = mock_client_class.call_args[0][0]
        assert "webdav_login" not in call_args or call_args["webdav_login"] == ""
        assert "webdav_password" not in call_args or call_args["webdav_password"] == ""

    def test_connect_missing_webdavclient(self, webdav_storage):
        """Test Verbindung ohne webdavclient3-Installation"""
        # Patch den Import-Mechanismus
        with patch.dict("sys.modules", {"webdav3.client": None}):
            with patch("builtins.__import__", side_effect=ImportError("No module named 'webdav3'")):
                with pytest.raises(ConnectionError, match="webdavclient3 nicht installiert"):
                    webdav_storage.connect()

    @patch("webdav3.client.Client")
    def test_connect_failure(self, mock_client_class, webdav_storage):
        """Test Verbindungsfehler"""
        mock_client_class.side_effect = Exception("Connection refused")

        with pytest.raises(ConnectionError, match="WebDAV-Verbindung fehlgeschlagen"):
            webdav_storage.connect()

    @patch("webdav3.client.Client")
    def test_connect_server_not_responding(self, mock_client_class, webdav_storage):
        """Test wenn Server nicht antwortet"""
        mock_client = Mock()
        mock_client.check.return_value = False
        mock_client_class.return_value = mock_client

        with pytest.raises(ConnectionError, match="WebDAV-Server antwortet nicht"):
            webdav_storage.connect()


class TestWebDAVStorageDisconnect:
    """Tests für Disconnect"""

    def test_disconnect(self, webdav_storage):
        """Test Verbindung trennen"""
        webdav_storage.client = Mock()
        webdav_storage.disconnect()

        assert webdav_storage.client is None


class TestWebDAVStorageUploadDownload:
    """Tests für Upload/Download (mit Mocks)"""

    def test_upload_file_not_connected(self, webdav_storage, tmp_path):
        """Test Upload ohne Verbindung"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")

        with pytest.raises(ConnectionError, match="Nicht verbunden"):
            webdav_storage.upload_file(test_file, "remote.txt")

    def test_upload_file_not_found(self, webdav_storage, tmp_path):
        """Test Upload nicht existierender Datei"""
        webdav_storage.client = Mock()

        with pytest.raises(FileNotFoundError):
            webdav_storage.upload_file(tmp_path / "nonexistent.txt", "remote.txt")

    def test_upload_file_success(self, webdav_storage, tmp_path):
        """Test erfolgreicher Upload"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")

        mock_client = Mock()
        webdav_storage.client = mock_client

        result = webdav_storage.upload_file(test_file, "remote.txt")

        assert result is True
        mock_client.upload_sync.assert_called_once()

    def test_upload_file_with_progress(self, webdav_storage, tmp_path):
        """Test Upload mit Progress-Callback"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")

        mock_client = Mock()
        webdav_storage.client = mock_client

        progress_calls = []

        def progress_cb(transferred, total):
            progress_calls.append((transferred, total))

        result = webdav_storage.upload_file(test_file, "remote.txt", progress_callback=progress_cb)

        assert result is True
        assert len(progress_calls) == 1

    def test_download_file_not_connected(self, webdav_storage, tmp_path):
        """Test Download ohne Verbindung"""
        with pytest.raises(ConnectionError, match="Nicht verbunden"):
            webdav_storage.download_file("remote.txt", tmp_path / "local.txt")

    def test_download_file_not_found(self, webdav_storage, tmp_path):
        """Test Download nicht existierender Datei"""
        mock_client = Mock()
        mock_client.check.return_value = False
        webdav_storage.client = mock_client

        with pytest.raises(FileNotFoundError, match="Remote-Datei nicht gefunden"):
            webdav_storage.download_file("remote.txt", tmp_path / "local.txt")

    def test_download_file_success(self, webdav_storage, tmp_path):
        """Test erfolgreicher Download"""
        local_file = tmp_path / "local.txt"

        mock_client = Mock()
        mock_client.check.return_value = True
        webdav_storage.client = mock_client

        # Mock download_sync to create file
        def mock_download(remote_path, local_path):
            Path(local_path).write_text("downloaded content")

        mock_client.download_sync.side_effect = mock_download

        result = webdav_storage.download_file("remote.txt", local_file)

        assert result is True
        assert local_file.exists()
        mock_client.download_sync.assert_called_once()


class TestWebDAVStorageFileOperations:
    """Tests für Datei-Operationen (mit Mocks)"""

    def test_list_files_not_connected(self, webdav_storage):
        """Test Listing ohne Verbindung"""
        with pytest.raises(ConnectionError, match="Nicht verbunden"):
            webdav_storage.list_files("")

    def test_list_files_success(self, webdav_storage):
        """Test erfolgreiche Datei-Auflistung"""
        mock_client = Mock()
        # list() gibt Liste mit ".", Dateien und Verzeichnissen zurück
        mock_client.list.return_value = [".", "file1.txt", "file2.txt", "subdir/"]
        mock_client.is_dir.side_effect = lambda p: p.endswith("/")
        webdav_storage.client = mock_client

        files = webdav_storage.list_files("")

        assert "file1.txt" in files
        assert "file2.txt" in files
        assert "subdir/" not in files  # Verzeichnisse sollten nicht enthalten sein
        assert "." not in files  # Current directory sollte nicht enthalten sein

    def test_delete_file_not_connected(self, webdav_storage):
        """Test Löschen ohne Verbindung"""
        with pytest.raises(ConnectionError, match="Nicht verbunden"):
            webdav_storage.delete_file("file.txt")

    def test_delete_file_not_found(self, webdav_storage):
        """Test Löschen nicht existierender Datei"""
        mock_client = Mock()
        mock_client.check.return_value = False
        webdav_storage.client = mock_client

        with pytest.raises(FileNotFoundError, match="Datei nicht gefunden"):
            webdav_storage.delete_file("file.txt")

    def test_delete_file_success(self, webdav_storage):
        """Test erfolgreiche Datei-Löschung"""
        mock_client = Mock()
        mock_client.check.return_value = True
        webdav_storage.client = mock_client

        result = webdav_storage.delete_file("file.txt")

        assert result is True
        mock_client.clean.assert_called_once()

    def test_create_directory_not_connected(self, webdav_storage):
        """Test Verzeichnis erstellen ohne Verbindung"""
        with pytest.raises(ConnectionError, match="Nicht verbunden"):
            webdav_storage.create_directory("newdir")

    def test_create_directory_success(self, webdav_storage):
        """Test erfolgreiche Verzeichnis-Erstellung"""
        mock_client = Mock()
        mock_client.check.return_value = False  # Verzeichnis existiert noch nicht
        webdav_storage.client = mock_client

        result = webdav_storage.create_directory("newdir")

        assert result is True
        mock_client.mkdir.assert_called()

    def test_exists_not_connected(self, webdav_storage):
        """Test exists ohne Verbindung"""
        with pytest.raises(ConnectionError, match="Nicht verbunden"):
            webdav_storage.exists("file.txt")

    def test_exists_true(self, webdav_storage):
        """Test exists für existierende Datei"""
        mock_client = Mock()
        mock_client.check.return_value = True
        webdav_storage.client = mock_client

        assert webdav_storage.exists("file.txt") is True

    def test_exists_false(self, webdav_storage):
        """Test exists für nicht existierende Datei"""
        mock_client = Mock()
        mock_client.check.return_value = False
        webdav_storage.client = mock_client

        assert webdav_storage.exists("file.txt") is False

    def test_delete_directory_not_connected(self, webdav_storage):
        """Test Verzeichnis löschen ohne Verbindung"""
        with pytest.raises(ConnectionError, match="Nicht verbunden"):
            webdav_storage.delete_directory("dir")

    def test_delete_directory_success(self, webdav_storage):
        """Test erfolgreiche Verzeichnis-Löschung"""
        mock_client = Mock()
        mock_client.check.return_value = True
        webdav_storage.client = mock_client

        result = webdav_storage.delete_directory("dir", recursive=True)

        assert result is True
        mock_client.clean.assert_called_once()


class TestWebDAVStorageConnection:
    """Tests für Verbindungs-Tests"""

    def test_test_connection_not_connected(self, webdav_storage):
        """Test Verbindungs-Test ohne Verbindung"""
        assert webdav_storage.test_connection() is False

    def test_test_connection_success(self, webdav_storage):
        """Test erfolgreicher Verbindungs-Test"""
        mock_client = Mock()
        mock_client.check.return_value = True
        webdav_storage.client = mock_client

        assert webdav_storage.test_connection() is True

    def test_test_connection_failure(self, webdav_storage):
        """Test fehlgeschlagener Verbindungs-Test"""
        mock_client = Mock()
        mock_client.check.side_effect = Exception("Connection lost")
        webdav_storage.client = mock_client

        assert webdav_storage.test_connection() is False

    def test_get_available_space_not_connected(self, webdav_storage):
        """Test Speicherplatz ohne Verbindung"""
        with pytest.raises(ConnectionError, match="Nicht verbunden"):
            webdav_storage.get_available_space()

    def test_get_available_space_success(self, webdav_storage):
        """Test erfolgreiche Speicherplatz-Abfrage"""
        mock_client = Mock()
        mock_client.free.return_value = 1000000
        webdav_storage.client = mock_client

        space = webdav_storage.get_available_space()
        assert space == 1000000

    def test_get_available_space_unavailable(self, webdav_storage):
        """Test Speicherplatz nicht verfügbar"""
        mock_client = Mock()
        mock_client.free.side_effect = Exception("Not supported")
        webdav_storage.client = mock_client

        space = webdav_storage.get_available_space()
        assert space == -1

    def test_get_available_space_none(self, webdav_storage):
        """Test Speicherplatz gibt None zurück"""
        mock_client = Mock()
        mock_client.free.return_value = None
        webdav_storage.client = mock_client

        space = webdav_storage.get_available_space()
        assert space == -1


class TestWebDAVStoragePathHelpers:
    """Tests für Pfad-Helper-Funktionen"""

    def test_join_path_with_base(self, webdav_storage):
        """Test Pfad-Joining mit Basis-Pfad"""
        result = webdav_storage._join_path("base", "relative/file.txt")
        assert result == "base/relative/file.txt"

    def test_join_path_without_base(self, webdav_storage):
        """Test Pfad-Joining ohne Basis-Pfad"""
        result = webdav_storage._join_path("", "relative/file.txt")
        assert result == "relative/file.txt"

    def test_join_path_only_base(self, webdav_storage):
        """Test Pfad-Joining nur mit Basis"""
        result = webdav_storage._join_path("base", "")
        assert result == "base"

    def test_join_path_empty(self, webdav_storage):
        """Test Pfad-Joining beide leer"""
        result = webdav_storage._join_path("", "")
        assert result == ""

    def test_join_path_normalization(self, webdav_storage):
        """Test dass Pfade normalisiert werden"""
        result = webdav_storage._join_path("/base/", "/relative/")
        assert result == "base/relative"


class TestWebDAVStorageContextManager:
    """Tests für Context Manager"""

    @patch("webdav3.client.Client")
    def test_context_manager(self, mock_client_class, webdav_storage):
        """Test Context Manager Usage"""
        mock_client = Mock()
        mock_client.check.return_value = True
        mock_client_class.return_value = mock_client

        with webdav_storage as storage:
            assert storage.client is not None

        # Nach with-Block sollte disconnect aufgerufen worden sein
        assert webdav_storage.client is None


class TestWebDAVStorageIntegration:
    """
    Integration-Tests (erfordern echten WebDAV-Server)

    Diese Tests werden übersprungen, wenn kein Test-Server verfügbar ist.
    Setze die Umgebungsvariable WEBDAV_TEST_URL für Integration-Tests.
    """

    @pytest.mark.skipif(
        "WEBDAV_TEST_URL" not in pytest.importorskip("os").environ,
        reason="WEBDAV_TEST_URL nicht konfiguriert",
    )
    def test_real_connection(self):
        """Test mit echtem WebDAV-Server (optional)"""
        import os

        url = os.environ.get("WEBDAV_TEST_URL")
        username = os.environ.get("WEBDAV_TEST_USER", "")
        password = os.environ.get("WEBDAV_TEST_PASSWORD", "")

        storage = WebDAVStorage(
            url=url,
            username=username,
            password=password,
        )

        try:
            assert storage.connect()
            assert storage.test_connection()
        finally:
            storage.disconnect()
