"""
Unit-Tests für RcloneStorage

Hinweis: Diese Tests verwenden Mocks, da rclone ein externes CLI-Tool ist.
Integration-Tests mit echtem rclone sollten separat durchgeführt werden.
"""

import json
import subprocess
from unittest.mock import Mock, patch

import pytest

from src.storage.rclone_storage import RcloneStorage


@pytest.fixture
def rclone_config():
    """Rclone-Konfiguration für Tests"""
    return {
        "remote_name": "gdrive",
        "remote_path": "scrat-backups",
        "rclone_binary": "rclone",
    }


@pytest.fixture
def rclone_storage(rclone_config):
    """RcloneStorage-Instanz"""
    return RcloneStorage(**rclone_config)


class TestRcloneStorageInit:
    """Tests für Initialisierung"""

    def test_init(self, rclone_config):
        """Test Initialisierung"""
        storage = RcloneStorage(**rclone_config)
        assert storage.remote_name == "gdrive"
        assert storage.remote_path == "scrat-backups"
        assert storage.rclone_binary == "rclone"
        assert storage._connected is False

    def test_init_remote_name_normalization(self):
        """Test dass trailing ':' entfernt wird"""
        storage = RcloneStorage(remote_name="gdrive:")
        assert storage.remote_name == "gdrive"

    def test_init_remote_path_normalization(self):
        """Test dass leading/trailing slashes entfernt werden"""
        storage = RcloneStorage(remote_name="gdrive", remote_path="/backups/")
        assert storage.remote_path == "backups"

    @patch("subprocess.run")
    def test_connect_success(self, mock_run, rclone_storage):
        """Test erfolgreiche Verbindung"""
        # Mock rclone version
        mock_run.return_value = Mock(stdout="rclone v1.60.0\n", stderr="", returncode=0)

        # Mock rclone listremotes
        def mock_run_side_effect(*args, **kwargs):
            cmd = args[0]
            if "version" in cmd:
                return Mock(stdout="rclone v1.60.0\n", stderr="", returncode=0)
            elif "listremotes" in cmd:
                return Mock(stdout="gdrive:\nonedrive:\n", stderr="", returncode=0)
            elif "about" in cmd:
                return Mock(stdout="{}", stderr="", returncode=0)
            elif "mkdir" in cmd:
                return Mock(stdout="", stderr="", returncode=0)
            else:
                return Mock(stdout="", stderr="", returncode=0)

        mock_run.side_effect = mock_run_side_effect

        result = rclone_storage.connect()

        assert result is True
        assert rclone_storage._connected is True

    @patch("subprocess.run")
    def test_connect_rclone_not_installed(self, mock_run, rclone_storage):
        """Test Verbindung wenn rclone nicht installiert ist"""
        mock_run.side_effect = FileNotFoundError()

        with pytest.raises(ConnectionError, match="rclone nicht gefunden"):
            rclone_storage.connect()

    @patch("subprocess.run")
    def test_connect_remote_not_configured(self, mock_run, rclone_storage):
        """Test Verbindung wenn Remote nicht konfiguriert ist"""

        def mock_run_side_effect(*args, **kwargs):
            cmd = args[0]
            if "version" in cmd:
                return Mock(stdout="rclone v1.60.0\n", stderr="", returncode=0)
            elif "listremotes" in cmd:
                # Remote "gdrive" existiert nicht
                return Mock(stdout="onedrive:\ndropbox:\n", stderr="", returncode=0)
            else:
                return Mock(stdout="", stderr="", returncode=0)

        mock_run.side_effect = mock_run_side_effect

        with pytest.raises(ConnectionError, match="nicht konfiguriert"):
            rclone_storage.connect()

    @patch("subprocess.run")
    def test_connect_remote_unreachable(self, mock_run, rclone_storage):
        """Test Verbindung wenn Remote nicht erreichbar ist"""

        def mock_run_side_effect(*args, **kwargs):
            cmd = args[0]
            if "version" in cmd:
                return Mock(stdout="rclone v1.60.0\n", stderr="", returncode=0)
            elif "listremotes" in cmd:
                return Mock(stdout="gdrive:\n", stderr="", returncode=0)
            elif "about" in cmd:
                raise subprocess.CalledProcessError(1, cmd, stderr="Failed to connect")
            else:
                return Mock(stdout="", stderr="", returncode=0)

        mock_run.side_effect = mock_run_side_effect

        with pytest.raises(ConnectionError, match="fehlgeschlagen"):
            rclone_storage.connect()


class TestRcloneStorageDisconnect:
    """Tests für Disconnect"""

    def test_disconnect(self, rclone_storage):
        """Test Verbindung trennen"""
        rclone_storage._connected = True
        rclone_storage.disconnect()

        assert rclone_storage._connected is False


class TestRcloneStorageUploadDownload:
    """Tests für Upload/Download"""

    def test_upload_file_not_connected(self, rclone_storage, tmp_path):
        """Test Upload ohne Verbindung"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")

        with pytest.raises(ConnectionError, match="Nicht verbunden"):
            rclone_storage.upload_file(test_file, "remote.txt")

    def test_upload_file_not_found(self, rclone_storage, tmp_path):
        """Test Upload nicht existierender Datei"""
        rclone_storage._connected = True

        with pytest.raises(FileNotFoundError):
            rclone_storage.upload_file(tmp_path / "nonexistent.txt", "remote.txt")

    @patch("subprocess.run")
    def test_upload_file_success(self, mock_run, rclone_storage, tmp_path):
        """Test erfolgreicher Upload"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")

        rclone_storage._connected = True
        mock_run.return_value = Mock(stdout="", stderr="", returncode=0)

        result = rclone_storage.upload_file(test_file, "remote.txt")

        assert result is True
        # Verify rclone copyto wurde aufgerufen
        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        assert "copyto" in cmd
        assert str(test_file) in cmd

    def test_download_file_not_connected(self, rclone_storage, tmp_path):
        """Test Download ohne Verbindung"""
        with pytest.raises(ConnectionError, match="Nicht verbunden"):
            rclone_storage.download_file("remote.txt", tmp_path / "local.txt")

    @patch("subprocess.run")
    def test_download_file_not_found(self, mock_run, rclone_storage, tmp_path):
        """Test Download nicht existierender Datei"""
        rclone_storage._connected = True

        # Mock exists() -> False
        mock_run.side_effect = subprocess.CalledProcessError(1, "cmd", stderr="not found")

        with pytest.raises(FileNotFoundError, match="nicht gefunden"):
            rclone_storage.download_file("remote.txt", tmp_path / "local.txt")

    @patch("subprocess.run")
    def test_download_file_success(self, mock_run, rclone_storage, tmp_path):
        """Test erfolgreicher Download"""
        local_file = tmp_path / "local.txt"
        rclone_storage._connected = True

        def mock_run_side_effect(*args, **kwargs):
            cmd = args[0]
            if "lsf" in cmd:
                # exists() check
                return Mock(stdout="remote.txt\n", stderr="", returncode=0)
            elif "copyto" in cmd:
                # Download
                local_file.write_text("downloaded content")
                return Mock(stdout="", stderr="", returncode=0)
            else:
                return Mock(stdout="", stderr="", returncode=0)

        mock_run.side_effect = mock_run_side_effect

        result = rclone_storage.download_file("remote.txt", local_file)

        assert result is True
        assert local_file.exists()


class TestRcloneStorageFileOperations:
    """Tests für Datei-Operationen"""

    def test_list_files_not_connected(self, rclone_storage):
        """Test Listing ohne Verbindung"""
        with pytest.raises(ConnectionError, match="Nicht verbunden"):
            rclone_storage.list_files("")

    @patch("subprocess.run")
    def test_list_files_success(self, mock_run, rclone_storage):
        """Test erfolgreiche Datei-Auflistung"""
        rclone_storage._connected = True

        # Mock rclone lsjson
        files_json = json.dumps(
            [
                {"Name": "file1.txt", "IsDir": False},
                {"Name": "file2.txt", "IsDir": False},
                {"Name": "subdir", "IsDir": True},
            ]
        )
        mock_run.return_value = Mock(stdout=files_json, stderr="", returncode=0)

        files = rclone_storage.list_files("")

        assert "file1.txt" in files
        assert "file2.txt" in files
        assert "subdir" not in files  # Verzeichnisse sollten nicht enthalten sein

    def test_delete_file_not_connected(self, rclone_storage):
        """Test Löschen ohne Verbindung"""
        with pytest.raises(ConnectionError, match="Nicht verbunden"):
            rclone_storage.delete_file("file.txt")

    @patch("subprocess.run")
    def test_delete_file_not_found(self, mock_run, rclone_storage):
        """Test Löschen nicht existierender Datei"""
        rclone_storage._connected = True

        # Mock exists() -> False
        mock_run.side_effect = subprocess.CalledProcessError(1, "cmd", stderr="not found")

        with pytest.raises(FileNotFoundError, match="nicht gefunden"):
            rclone_storage.delete_file("file.txt")

    @patch("subprocess.run")
    def test_delete_file_success(self, mock_run, rclone_storage):
        """Test erfolgreiche Datei-Löschung"""
        rclone_storage._connected = True

        def mock_run_side_effect(*args, **kwargs):
            cmd = args[0]
            if "lsf" in cmd:
                # exists() check
                return Mock(stdout="file.txt\n", stderr="", returncode=0)
            elif "deletefile" in cmd:
                return Mock(stdout="", stderr="", returncode=0)
            else:
                return Mock(stdout="", stderr="", returncode=0)

        mock_run.side_effect = mock_run_side_effect

        result = rclone_storage.delete_file("file.txt")

        assert result is True

    def test_create_directory_not_connected(self, rclone_storage):
        """Test Verzeichnis erstellen ohne Verbindung"""
        with pytest.raises(ConnectionError, match="Nicht verbunden"):
            rclone_storage.create_directory("newdir")

    @patch("subprocess.run")
    def test_create_directory_success(self, mock_run, rclone_storage):
        """Test erfolgreiche Verzeichnis-Erstellung"""
        rclone_storage._connected = True
        mock_run.return_value = Mock(stdout="", stderr="", returncode=0)

        result = rclone_storage.create_directory("newdir")

        assert result is True
        # Verify rclone mkdir wurde aufgerufen
        cmd = mock_run.call_args[0][0]
        assert "mkdir" in cmd

    def test_exists_not_connected(self, rclone_storage):
        """Test exists ohne Verbindung"""
        with pytest.raises(ConnectionError, match="Nicht verbunden"):
            rclone_storage.exists("file.txt")

    @patch("subprocess.run")
    def test_exists_true(self, mock_run, rclone_storage):
        """Test exists für existierende Datei"""
        rclone_storage._connected = True
        mock_run.return_value = Mock(stdout="file.txt\n", stderr="", returncode=0)

        assert rclone_storage.exists("file.txt") is True

    @patch("subprocess.run")
    def test_exists_false(self, mock_run, rclone_storage):
        """Test exists für nicht existierende Datei"""
        rclone_storage._connected = True
        mock_run.side_effect = subprocess.CalledProcessError(1, "cmd", stderr="not found")

        assert rclone_storage.exists("file.txt") is False

    def test_delete_directory_not_connected(self, rclone_storage):
        """Test Verzeichnis löschen ohne Verbindung"""
        with pytest.raises(ConnectionError, match="Nicht verbunden"):
            rclone_storage.delete_directory("dir")

    @patch("subprocess.run")
    def test_delete_directory_success(self, mock_run, rclone_storage):
        """Test erfolgreiche Verzeichnis-Löschung"""
        rclone_storage._connected = True

        def mock_run_side_effect(*args, **kwargs):
            cmd = args[0]
            if "lsf" in cmd:
                # exists() check
                return Mock(stdout="dir/\n", stderr="", returncode=0)
            elif "purge" in cmd or "rmdir" in cmd:
                return Mock(stdout="", stderr="", returncode=0)
            else:
                return Mock(stdout="", stderr="", returncode=0)

        mock_run.side_effect = mock_run_side_effect

        result = rclone_storage.delete_directory("dir", recursive=True)

        assert result is True


class TestRcloneStorageConnection:
    """Tests für Verbindungs-Tests"""

    def test_test_connection_not_connected(self, rclone_storage):
        """Test Verbindungs-Test ohne Verbindung"""
        assert rclone_storage.test_connection() is False

    @patch("subprocess.run")
    def test_test_connection_success(self, mock_run, rclone_storage):
        """Test erfolgreicher Verbindungs-Test"""
        rclone_storage._connected = True
        mock_run.return_value = Mock(stdout="{}", stderr="", returncode=0)

        assert rclone_storage.test_connection() is True

    @patch("subprocess.run")
    def test_test_connection_failure(self, mock_run, rclone_storage):
        """Test fehlgeschlagener Verbindungs-Test"""
        rclone_storage._connected = True
        mock_run.side_effect = Exception("Connection lost")

        assert rclone_storage.test_connection() is False

    def test_get_available_space_not_connected(self, rclone_storage):
        """Test Speicherplatz ohne Verbindung"""
        with pytest.raises(ConnectionError, match="Nicht verbunden"):
            rclone_storage.get_available_space()

    @patch("subprocess.run")
    def test_get_available_space_success(self, mock_run, rclone_storage):
        """Test erfolgreiche Speicherplatz-Abfrage"""
        rclone_storage._connected = True
        about_json = json.dumps({"free": 1000000, "used": 500000, "total": 1500000})
        mock_run.return_value = Mock(stdout=about_json, stderr="", returncode=0)

        space = rclone_storage.get_available_space()
        assert space == 1000000

    @patch("subprocess.run")
    def test_get_available_space_unavailable(self, mock_run, rclone_storage):
        """Test Speicherplatz nicht verfügbar"""
        rclone_storage._connected = True
        mock_run.side_effect = subprocess.CalledProcessError(1, "cmd", stderr="not supported")

        space = rclone_storage.get_available_space()
        assert space == -1

    @patch("subprocess.run")
    def test_get_available_space_no_free_field(self, mock_run, rclone_storage):
        """Test Speicherplatz wenn Provider kein 'free'-Feld liefert"""
        rclone_storage._connected = True
        about_json = json.dumps({"used": 500000})  # kein 'free'
        mock_run.return_value = Mock(stdout=about_json, stderr="", returncode=0)

        space = rclone_storage.get_available_space()
        assert space == -1


class TestRcloneStoragePathHelpers:
    """Tests für Pfad-Helper-Funktionen"""

    def test_join_remote_path_with_base(self, rclone_storage):
        """Test Remote-Pfad-Joining mit Basis-Pfad"""
        result = rclone_storage._join_remote_path("relative/file.txt")
        assert result == "gdrive:scrat-backups/relative/file.txt"

    def test_join_remote_path_without_base(self):
        """Test Remote-Pfad-Joining ohne Basis-Pfad"""
        storage = RcloneStorage(remote_name="gdrive", remote_path="")
        result = storage._join_remote_path("relative/file.txt")
        assert result == "gdrive:relative/file.txt"

    def test_join_remote_path_only_base(self, rclone_storage):
        """Test Remote-Pfad-Joining nur mit Basis"""
        result = rclone_storage._join_remote_path("")
        assert result == "gdrive:scrat-backups"

    def test_join_remote_path_empty(self):
        """Test Remote-Pfad-Joining beide leer"""
        storage = RcloneStorage(remote_name="gdrive", remote_path="")
        result = storage._join_remote_path("")
        assert result == "gdrive:"

    def test_join_remote_path_normalization(self, rclone_storage):
        """Test dass Pfade normalisiert werden"""
        result = rclone_storage._join_remote_path("/relative/")
        assert result == "gdrive:scrat-backups/relative"


class TestRcloneStorageContextManager:
    """Tests für Context Manager"""

    @patch("subprocess.run")
    def test_context_manager(self, mock_run, rclone_storage):
        """Test Context Manager Usage"""

        def mock_run_side_effect(*args, **kwargs):
            cmd = args[0]
            if "version" in cmd:
                return Mock(stdout="rclone v1.60.0\n", stderr="", returncode=0)
            elif "listremotes" in cmd:
                return Mock(stdout="gdrive:\n", stderr="", returncode=0)
            elif "about" in cmd:
                return Mock(stdout="{}", stderr="", returncode=0)
            elif "mkdir" in cmd:
                return Mock(stdout="", stderr="", returncode=0)
            else:
                return Mock(stdout="", stderr="", returncode=0)

        mock_run.side_effect = mock_run_side_effect

        with rclone_storage as storage:
            assert storage._connected is True

        # Nach with-Block sollte disconnect aufgerufen worden sein
        assert rclone_storage._connected is False


class TestRcloneStorageIntegration:
    """
    Integration-Tests (erfordern echtes rclone mit konfiguriertem Remote)

    Diese Tests werden übersprungen, wenn kein Test-Remote verfügbar ist.
    Setze die Umgebungsvariable RCLONE_TEST_REMOTE für Integration-Tests.
    """

    @pytest.mark.skipif(
        "RCLONE_TEST_REMOTE" not in pytest.importorskip("os").environ,
        reason="RCLONE_TEST_REMOTE nicht konfiguriert",
    )
    def test_real_connection(self):
        """Test mit echtem rclone (optional)"""
        import os

        remote_name = os.environ.get("RCLONE_TEST_REMOTE")
        remote_path = os.environ.get("RCLONE_TEST_PATH", "scrat-test")

        storage = RcloneStorage(
            remote_name=remote_name,
            remote_path=remote_path,
        )

        try:
            assert storage.connect()
            assert storage.test_connection()
        finally:
            storage.disconnect()
