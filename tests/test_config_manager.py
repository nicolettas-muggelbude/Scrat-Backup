"""
Unit-Tests für ConfigManager
"""

import json
from pathlib import Path

import pytest

from src.core.config_manager import ConfigManager


@pytest.fixture
def temp_config_file(tmp_path):
    """Temporäre Config-Datei für Tests"""
    return tmp_path / "test_config.json"


@pytest.fixture
def config_manager(temp_config_file):
    """ConfigManager-Instanz für Tests"""
    return ConfigManager(config_file=temp_config_file)


class TestConfigManagerInit:
    """Tests für Initialisierung"""

    def test_init_creates_config(self, temp_config_file):
        """Test dass Config-Datei erstellt wird"""
        manager = ConfigManager(config_file=temp_config_file)

        assert manager is not None
        assert manager.config_file == temp_config_file
        assert isinstance(manager.config, dict)

    def test_init_loads_defaults(self, config_manager):
        """Test dass Defaults geladen werden"""
        # Alle Sektionen sollten vorhanden sein
        assert "general" in config_manager.config
        assert "backup" in config_manager.config
        assert "paths" in config_manager.config
        assert "advanced" in config_manager.config
        assert "storage" in config_manager.config

    def test_init_default_path(self, tmp_path, monkeypatch):
        """Test Standard-Pfad für Config"""
        # Mock home directory
        monkeypatch.setattr(Path, "home", lambda: tmp_path)

        manager = ConfigManager()

        expected_path = tmp_path / ".scrat-backup" / "config.json"
        assert manager.config_file == expected_path


class TestConfigManagerLoadSave:
    """Tests für Laden/Speichern"""

    def test_save_creates_file(self, config_manager):
        """Test dass save() Datei erstellt"""
        config_manager.save()

        assert config_manager.config_file.exists()

    def test_save_and_load(self, temp_config_file):
        """Test Speichern und Laden"""
        # Erstelle Config
        manager1 = ConfigManager(config_file=temp_config_file)
        manager1.set("general", "language", "en")
        manager1.set("backup", "compression_level", 7)
        manager1.save()

        # Lade Config neu
        manager2 = ConfigManager(config_file=temp_config_file)

        assert manager2.get("general", "language") == "en"
        assert manager2.get("backup", "compression_level") == 7

    def test_load_nonexistent_uses_defaults(self, temp_config_file):
        """Test dass Defaults genutzt werden wenn Datei fehlt"""
        manager = ConfigManager(config_file=temp_config_file)

        # Defaults sollten geladen sein
        assert manager.get("general", "language") == "de"
        assert manager.get("backup", "compression_level") == 5

    def test_load_invalid_json_uses_defaults(self, temp_config_file):
        """Test dass bei ungültigem JSON Defaults genutzt werden"""
        # Schreibe ungültiges JSON
        with open(temp_config_file, "w") as f:
            f.write("{ invalid json }")

        manager = ConfigManager(config_file=temp_config_file)

        # Sollte Defaults nutzen
        assert manager.get("general", "language") == "de"

    def test_save_creates_parent_directory(self, tmp_path):
        """Test dass Verzeichnis erstellt wird"""
        config_file = tmp_path / "subdir" / "config.json"
        manager = ConfigManager(config_file=config_file)

        manager.save()

        assert config_file.parent.exists()
        assert config_file.exists()

    def test_saved_json_format(self, config_manager):
        """Test dass gespeichertes JSON korrekt formatiert ist"""
        config_manager.set("general", "language", "en")
        config_manager.save()

        # Lese JSON direkt
        with open(config_manager.config_file, "r") as f:
            data = json.load(f)

        assert data["general"]["language"] == "en"
        assert isinstance(data, dict)


class TestConfigManagerGetSet:
    """Tests für Getter/Setter"""

    def test_get_existing_value(self, config_manager):
        """Test Wert holen"""
        value = config_manager.get("general", "language")

        assert value == "de"

    def test_get_with_default(self, config_manager):
        """Test get() mit Default-Wert"""
        value = config_manager.get("general", "nonexistent", default="fallback")

        assert value == "fallback"

    def test_get_nonexistent_section(self, config_manager):
        """Test get() mit ungültiger Sektion"""
        value = config_manager.get("invalid_section", "key", default="fallback")

        assert value == "fallback"

    def test_set_existing_value(self, config_manager):
        """Test Wert setzen"""
        config_manager.set("general", "language", "en")

        assert config_manager.get("general", "language") == "en"

    def test_set_new_value(self, config_manager):
        """Test neuen Wert setzen"""
        config_manager.set("general", "new_key", "new_value")

        assert config_manager.get("general", "new_key") == "new_value"

    def test_set_creates_section(self, config_manager):
        """Test dass set() neue Sektion erstellt"""
        config_manager.set("new_section", "key", "value")

        assert "new_section" in config_manager.config
        assert config_manager.get("new_section", "key") == "value"

    def test_get_section(self, config_manager):
        """Test komplette Sektion holen"""
        section = config_manager.get_section("general")

        assert isinstance(section, dict)
        assert "language" in section
        assert section["language"] == "de"

    def test_get_nonexistent_section_returns_empty(self, config_manager):
        """Test dass get_section() leeres dict zurückgibt"""
        section = config_manager.get_section("nonexistent")

        assert section == {}

    def test_set_section(self, config_manager):
        """Test komplette Sektion setzen"""
        new_section = {
            "language": "en",
            "theme": "dark",
            "new_key": "new_value",
        }

        config_manager.set_section("general", new_section)

        assert config_manager.get("general", "language") == "en"
        assert config_manager.get("general", "theme") == "dark"
        assert config_manager.get("general", "new_key") == "new_value"


class TestConfigManagerReset:
    """Tests für Reset-Funktion"""

    def test_reset_to_defaults(self, config_manager):
        """Test Reset auf Defaults"""
        # Ändere Werte
        config_manager.set("general", "language", "en")
        config_manager.set("backup", "compression_level", 9)

        # Reset
        config_manager.reset_to_defaults()

        # Sollte Defaults sein
        assert config_manager.get("general", "language") == "de"
        assert config_manager.get("backup", "compression_level") == 5


class TestConfigManagerMerge:
    """Tests für Config-Merging"""

    def test_merge_adds_new_keys(self, temp_config_file):
        """Test dass neue Keys aus Defaults hinzugefügt werden"""
        # Erstelle Config mit alten Keys
        old_config = {
            "general": {"language": "en"},
            "backup": {"compression_level": 7},
        }

        with open(temp_config_file, "w") as f:
            json.dump(old_config, f)

        # Lade Config
        manager = ConfigManager(config_file=temp_config_file)

        # Alte Werte sollten erhalten bleiben
        assert manager.get("general", "language") == "en"
        assert manager.get("backup", "compression_level") == 7

        # Neue Keys aus Defaults sollten hinzugefügt sein
        assert manager.get("general", "theme") == "system"
        assert manager.get("advanced", "log_level") == "INFO"

    def test_merge_preserves_user_values(self, temp_config_file):
        """Test dass User-Werte bei Merge erhalten bleiben"""
        # Erstelle Config mit User-Werten
        user_config = {
            "general": {
                "language": "en",
                "custom_key": "custom_value",
            },
        }

        with open(temp_config_file, "w") as f:
            json.dump(user_config, f)

        # Lade Config
        manager = ConfigManager(config_file=temp_config_file)

        # User-Werte sollten erhalten bleiben
        assert manager.get("general", "language") == "en"
        assert manager.get("general", "custom_key") == "custom_value"


class TestConfigManagerDefaults:
    """Tests für Default-Werte"""

    def test_default_general_values(self, config_manager):
        """Test General-Defaults"""
        assert config_manager.get("general", "language") == "de"
        assert config_manager.get("general", "theme") == "system"
        assert config_manager.get("general", "start_with_system") is False

    def test_default_backup_values(self, config_manager):
        """Test Backup-Defaults"""
        assert config_manager.get("backup", "compression_level") == 5
        assert config_manager.get("backup", "archive_split_size_mb") == 100
        assert config_manager.get("backup", "keep_backups") == 10

    def test_default_paths_values(self, config_manager):
        """Test Paths-Defaults (leer = auto)"""
        assert config_manager.get("paths", "metadata_db") == ""
        assert config_manager.get("paths", "temp_dir") == ""
        assert config_manager.get("paths", "log_dir") == ""

    def test_default_advanced_values(self, config_manager):
        """Test Advanced-Defaults"""
        assert config_manager.get("advanced", "log_level") == "INFO"
        assert config_manager.get("advanced", "max_threads") == 4
        assert config_manager.get("advanced", "network_timeout") == 300

    def test_default_storage_values(self, config_manager):
        """Test Storage-Defaults (leere Listen)"""
        assert config_manager.get("storage", "sftp_connections") == []
        assert config_manager.get("storage", "smb_shares") == []
        assert config_manager.get("storage", "webdav_servers") == []
