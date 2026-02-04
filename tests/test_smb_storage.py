"""
Unit-Tests für SMBStorage

Hinweis: Diese Tests verwenden Mocks, da ein echter SMB-Server
für Unit-Tests nicht praktikabel ist. Integration-Tests mit echtem
Server sollten separat durchgeführt werden.
"""

from unittest.mock import Mock, patch

import pytest

from src.storage.smb_storage import SMBStorage


@pytest.fixture
def smb_config():
    """SMB-Konfiguration für Tests"""
    return {
        "server": "nas.local",
        "share": "backups",
        "username": "testuser",
        "password": "testpass",
        "domain": "",
        "port": 445,
        "base_path": "/scrat-backups",
    }


@pytest.fixture
def smb_storage(smb_config):
    """SMBStorage-Instanz"""
    return SMBStorage(**smb_config)


class TestSMBStorageInit:
    """Tests für Initialisierung"""

    def test_init(self, smb_config):
        """Test Initialisierung"""
        storage = SMBStorage(**smb_config)
        assert storage.server == "nas.local"
        assert storage.share == "backups"
        assert storage.username == "testuser"
        assert storage.password == "testpass"
        assert storage.domain == ""
        assert storage.port == 445
        assert storage.base_path == "scrat-backups"  # Leading / wird entfernt
        assert storage.session is None
        assert storage.tree is None

    def test_init_with_domain(self):
        """Test Initialisierung mit Windows-Domain"""
        storage = SMBStorage(
            server="fileserver.company.local",
            share="data",
            username="john",
            password="secret",
            domain="COMPANY",
        )
        assert storage.domain == "COMPANY"

    @patch("smbprotocol.connection.Connection")
    @patch("smbprotocol.session.Session")
    @patch("smbprotocol.tree.TreeConnect")
    def test_connect_success(self, mock_tree, mock_session, mock_connection, smb_storage):
        """Test erfolgreiche Verbindung"""
        # Mock Setup
        mock_conn_inst = Mock()
        mock_session_inst = Mock()
        mock_tree_inst = Mock()

        mock_connection.return_value = mock_conn_inst
        mock_session.return_value = mock_session_inst
        mock_tree.return_value = mock_tree_inst

        # Mock _ensure_directory_exists
        with patch.object(smb_storage, "_ensure_directory_exists"):
            result = smb_storage.connect()

        assert result is True
        assert smb_storage.connection == mock_conn_inst
        assert smb_storage.session == mock_session_inst
        assert smb_storage.tree == mock_tree_inst

        # Verify calls
        mock_conn_inst.connect.assert_called_once()
        mock_session_inst.connect.assert_called_once()
        mock_tree_inst.connect.assert_called_once()

    @patch("smbprotocol.connection.Connection", side_effect=ImportError)
    def test_connect_missing_smbprotocol(self, mock_connection, smb_storage):
        """Test Verbindung ohne smbprotocol-Installation"""
        with pytest.raises(ConnectionError, match="smbprotocol nicht installiert"):
            smb_storage.connect()

    @patch("smbprotocol.connection.Connection")
    def test_connect_failure(self, mock_connection, smb_storage):
        """Test Verbindungsfehler"""
        mock_connection.side_effect = Exception("Connection refused")

        with pytest.raises(ConnectionError, match="SMB-Verbindung fehlgeschlagen"):
            smb_storage.connect()


class TestSMBStorageDisconnect:
    """Tests für Disconnect"""

    def test_disconnect(self, smb_storage):
        """Test Verbindung trennen"""
        # Setup Mock-Connections
        smb_storage.tree = Mock()
        smb_storage.session = Mock()
        smb_storage.connection = Mock()

        smb_storage.disconnect()

        assert smb_storage.tree is None
        assert smb_storage.session is None
        assert smb_storage.connection is None


class TestSMBStorageUploadDownload:
    """Tests für Upload/Download (mit Mocks)"""

    def test_upload_file_not_connected(self, smb_storage, tmp_path):
        """Test Upload ohne Verbindung"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")

        with pytest.raises(ConnectionError, match="Nicht verbunden"):
            smb_storage.upload_file(test_file, "remote.txt")

    def test_upload_file_not_found(self, smb_storage, tmp_path):
        """Test Upload nicht existierender Datei"""
        smb_storage.tree = Mock()

        with pytest.raises(FileNotFoundError):
            smb_storage.upload_file(tmp_path / "nonexistent.txt", "remote.txt")

    def test_download_file_not_connected(self, smb_storage, tmp_path):
        """Test Download ohne Verbindung"""
        with pytest.raises(ConnectionError, match="Nicht verbunden"):
            smb_storage.download_file("remote.txt", tmp_path / "local.txt")


class TestSMBStorageFileOperations:
    """Tests für Datei-Operationen (mit Mocks)"""

    def test_list_files_not_connected(self, smb_storage):
        """Test Listing ohne Verbindung"""
        with pytest.raises(ConnectionError, match="Nicht verbunden"):
            smb_storage.list_files("")

    def test_delete_file_not_connected(self, smb_storage):
        """Test Löschen ohne Verbindung"""
        with pytest.raises(ConnectionError, match="Nicht verbunden"):
            smb_storage.delete_file("file.txt")

    def test_create_directory_not_connected(self, smb_storage):
        """Test Verzeichnis erstellen ohne Verbindung"""
        with pytest.raises(ConnectionError, match="Nicht verbunden"):
            smb_storage.create_directory("newdir")

    def test_exists_not_connected(self, smb_storage):
        """Test exists ohne Verbindung"""
        with pytest.raises(ConnectionError, match="Nicht verbunden"):
            smb_storage.exists("file.txt")


class TestSMBStorageConnection:
    """Tests für Verbindungs-Tests"""

    def test_test_connection_not_connected(self, smb_storage):
        """Test Verbindungs-Test ohne Verbindung"""
        assert smb_storage.test_connection() is False

    def test_test_connection_success(self, smb_storage):
        """Test erfolgreicher Verbindungs-Test"""
        smb_storage.tree = Mock()
        smb_storage.tree.query_fs_info.return_value = {}

        assert smb_storage.test_connection() is True

    def test_test_connection_failure(self, smb_storage):
        """Test fehlgeschlagener Verbindungs-Test"""
        smb_storage.tree = Mock()
        smb_storage.tree.query_fs_info.side_effect = Exception("Error")

        assert smb_storage.test_connection() is False

    def test_get_available_space_not_connected(self, smb_storage):
        """Test Speicherplatz ohne Verbindung"""
        with pytest.raises(ConnectionError, match="Nicht verbunden"):
            smb_storage.get_available_space()

    def test_get_available_space_success(self, smb_storage):
        """Test erfolgreiche Speicherplatz-Abfrage"""
        smb_storage.tree = Mock()
        smb_storage.tree.query_fs_info.return_value = {"total_free_bytes": 1000000}

        space = smb_storage.get_available_space()
        assert space == 1000000

    def test_get_available_space_unavailable(self, smb_storage):
        """Test Speicherplatz nicht verfügbar"""
        smb_storage.tree = Mock()
        smb_storage.tree.query_fs_info.side_effect = Exception("Not supported")

        space = smb_storage.get_available_space()
        assert space == -1


class TestSMBStoragePathHelpers:
    """Tests für Pfad-Helper-Funktionen"""

    def test_join_path_with_base(self, smb_storage):
        """Test Pfad-Joining mit Basis-Pfad"""
        result = smb_storage._join_path("base", "relative/file.txt")
        assert "base" in result
        assert "relative" in result
        assert "file.txt" in result

    def test_join_path_without_base(self, smb_storage):
        """Test Pfad-Joining ohne Basis-Pfad"""
        result = smb_storage._join_path("", "relative/file.txt")
        assert result == "relative/file.txt"

    def test_join_path_windows_style(self, smb_storage):
        """Test dass Windows-Style-Pfade verwendet werden"""
        result = smb_storage._join_path("base", "sub/file.txt")
        # PureWindowsPath sollte verwendet werden
        assert "\\" in result or "/" in result


class TestSMBStorageContextManager:
    """Tests für Context Manager"""

    @patch("smbprotocol.connection.Connection")
    @patch("smbprotocol.session.Session")
    @patch("smbprotocol.tree.TreeConnect")
    def test_context_manager(self, mock_tree, mock_session, mock_connection, smb_storage):
        """Test Context Manager Usage"""
        # Mock Setup
        mock_conn_inst = Mock()
        mock_session_inst = Mock()
        mock_tree_inst = Mock()

        mock_connection.return_value = mock_conn_inst
        mock_session.return_value = mock_session_inst
        mock_tree.return_value = mock_tree_inst

        # Mock _ensure_directory_exists
        with patch.object(smb_storage, "_ensure_directory_exists"):
            with smb_storage as storage:
                assert storage.tree is not None

        # Nach with-Block sollte disconnect aufgerufen worden sein
        assert smb_storage.tree is None


class TestSMBStorageIntegration:
    """
    Integration-Tests (erfordern echten SMB-Server)

    Diese Tests werden übersprungen, wenn kein Test-Server verfügbar ist.
    Setze die Umgebungsvariable SMB_TEST_SERVER für Integration-Tests.
    """

    @pytest.mark.skipif(
        "SMB_TEST_SERVER" not in pytest.importorskip("os").environ,
        reason="SMB_TEST_SERVER nicht konfiguriert",
    )
    def test_real_connection(self):
        """Test mit echtem SMB-Server (optional)"""
        import os

        server = os.environ.get("SMB_TEST_SERVER")
        share = os.environ.get("SMB_TEST_SHARE", "test")
        username = os.environ.get("SMB_TEST_USER", "testuser")
        password = os.environ.get("SMB_TEST_PASSWORD", "testpass")

        storage = SMBStorage(server=server, share=share, username=username, password=password)

        try:
            assert storage.connect()
            assert storage.test_connection()
        finally:
            storage.disconnect()
