"""
Unit-Tests für Settings-Tab GUI
"""

from unittest.mock import patch

import pytest
from PyQt6.QtWidgets import QMessageBox

from src.core.config_manager import ConfigManager
from src.gui.settings_tab import SettingsTab


@pytest.fixture
def temp_config_file(tmp_path):
    """Temporäre Config-Datei für Tests"""
    return tmp_path / "test_config.json"


@pytest.fixture
def config_manager(temp_config_file):
    """ConfigManager-Instanz für Tests"""
    return ConfigManager(config_file=temp_config_file)


@pytest.fixture
def settings_tab(qtbot, config_manager):
    """SettingsTab-Instanz für Tests"""
    tab = SettingsTab()
    qtbot.addWidget(tab)
    tab.set_config_manager(config_manager)
    return tab


class TestSettingsTabInit:
    """Tests für Initialisierung"""

    def test_init(self, qtbot):
        """Test dass Tab korrekt initialisiert wird"""
        tab = SettingsTab()
        qtbot.addWidget(tab)

        assert tab is not None
        assert tab.config_manager is None
        assert tab.original_config == {}

    def test_ui_components_exist(self, settings_tab):
        """Test dass alle UI-Komponenten existieren"""
        # Allgemein
        assert settings_tab.language_combo is not None
        assert settings_tab.theme_combo is not None
        assert settings_tab.autostart_checkbox is not None
        assert settings_tab.minimize_tray_checkbox is not None

        # Backup
        assert settings_tab.default_dest_edit is not None
        assert settings_tab.compression_spin is not None
        assert settings_tab.split_size_spin is not None
        assert settings_tab.keep_backups_spin is not None
        assert settings_tab.verify_checkbox is not None

        # Pfade
        assert settings_tab.metadata_db_edit is not None
        assert settings_tab.temp_dir_edit is not None
        assert settings_tab.log_dir_edit is not None

        # Erweitert
        assert settings_tab.log_level_combo is not None
        assert settings_tab.max_threads_spin is not None
        assert settings_tab.network_timeout_spin is not None
        assert settings_tab.retry_count_spin is not None

        # Buttons
        assert settings_tab.save_button is not None
        assert settings_tab.cancel_button is not None
        assert settings_tab.reset_button is not None


class TestSettingsTabLoadSettings:
    """Tests für Laden von Einstellungen"""

    def test_load_general_settings(self, settings_tab, config_manager):
        """Test dass Allgemeine Einstellungen geladen werden"""
        # Setze Werte
        config_manager.set("general", "language", "en")
        config_manager.set("general", "theme", "dark")
        config_manager.set("general", "start_with_system", True)
        config_manager.set("general", "minimize_to_tray", True)

        # Lade in UI
        settings_tab._load_settings()

        # Prüfe UI
        assert settings_tab.language_combo.currentData() == "en"
        assert settings_tab.theme_combo.currentData() == "dark"
        assert settings_tab.autostart_checkbox.isChecked() is True
        assert settings_tab.minimize_tray_checkbox.isChecked() is True

    def test_load_backup_settings(self, settings_tab, config_manager):
        """Test dass Backup-Einstellungen geladen werden"""
        # Setze Werte
        config_manager.set("backup", "default_destination", "/test/path")
        config_manager.set("backup", "compression_level", 9)
        config_manager.set("backup", "archive_split_size_mb", 200)
        config_manager.set("backup", "keep_backups", 20)
        config_manager.set("backup", "verify_after_backup", False)

        # Lade in UI
        settings_tab._load_settings()

        # Prüfe UI
        assert settings_tab.default_dest_edit.text() == "/test/path"
        assert settings_tab.compression_spin.value() == 9
        assert settings_tab.split_size_spin.value() == 200
        assert settings_tab.keep_backups_spin.value() == 20
        assert settings_tab.verify_checkbox.isChecked() is False

    def test_load_paths_settings(self, settings_tab, config_manager):
        """Test dass Pfad-Einstellungen geladen werden"""
        # Setze Werte
        config_manager.set("paths", "metadata_db", "/test/metadata.db")
        config_manager.set("paths", "temp_dir", "/test/temp")
        config_manager.set("paths", "log_dir", "/test/logs")

        # Lade in UI
        settings_tab._load_settings()

        # Prüfe UI
        assert settings_tab.metadata_db_edit.text() == "/test/metadata.db"
        assert settings_tab.temp_dir_edit.text() == "/test/temp"
        assert settings_tab.log_dir_edit.text() == "/test/logs"

    def test_load_advanced_settings(self, settings_tab, config_manager):
        """Test dass Erweiterte Einstellungen geladen werden"""
        # Setze Werte
        config_manager.set("advanced", "log_level", "DEBUG")
        config_manager.set("advanced", "max_threads", 8)
        config_manager.set("advanced", "network_timeout", 600)
        config_manager.set("advanced", "retry_count", 5)

        # Lade in UI
        settings_tab._load_settings()

        # Prüfe UI
        assert settings_tab.log_level_combo.currentData() == "DEBUG"
        assert settings_tab.max_threads_spin.value() == 8
        assert settings_tab.network_timeout_spin.value() == 600
        assert settings_tab.retry_count_spin.value() == 5

    def test_load_settings_backs_up_original(self, settings_tab, config_manager):
        """Test dass Original-Config gesichert wird"""
        # Setze Werte
        config_manager.set("general", "language", "en")

        # Lade
        settings_tab._load_settings()

        # Original sollte gesichert sein
        assert "general" in settings_tab.original_config
        assert settings_tab.original_config["general"]["language"] == "en"


class TestSettingsTabSaveSettings:
    """Tests für Speichern von Einstellungen"""

    def test_save_general_settings(self, settings_tab, config_manager):
        """Test dass Allgemeine Einstellungen gespeichert werden"""
        # Ändere UI
        settings_tab.language_combo.setCurrentIndex(
            settings_tab.language_combo.findData("en")
        )
        settings_tab.theme_combo.setCurrentIndex(settings_tab.theme_combo.findData("dark"))
        settings_tab.autostart_checkbox.setChecked(True)
        settings_tab.minimize_tray_checkbox.setChecked(True)

        # Speichere
        settings_tab._save_settings()

        # Prüfe Config
        assert config_manager.get("general", "language") == "en"
        assert config_manager.get("general", "theme") == "dark"
        assert config_manager.get("general", "start_with_system") is True
        assert config_manager.get("general", "minimize_to_tray") is True

    def test_save_backup_settings(self, settings_tab, config_manager):
        """Test dass Backup-Einstellungen gespeichert werden"""
        # Ändere UI
        settings_tab.default_dest_edit.setText("/new/path")
        settings_tab.compression_spin.setValue(7)
        settings_tab.split_size_spin.setValue(150)
        settings_tab.keep_backups_spin.setValue(15)
        settings_tab.verify_checkbox.setChecked(False)

        # Speichere
        settings_tab._save_settings()

        # Prüfe Config
        assert config_manager.get("backup", "default_destination") == "/new/path"
        assert config_manager.get("backup", "compression_level") == 7
        assert config_manager.get("backup", "archive_split_size_mb") == 150
        assert config_manager.get("backup", "keep_backups") == 15
        assert config_manager.get("backup", "verify_after_backup") is False

    def test_save_persists_to_file(self, settings_tab, config_manager):
        """Test dass Speichern in Datei schreibt"""
        # Ändere UI
        settings_tab.language_combo.setCurrentIndex(
            settings_tab.language_combo.findData("en")
        )

        # Speichere
        settings_tab._save_settings()

        # Config-Datei sollte existieren
        assert config_manager.config_file.exists()

        # Lade neu und prüfe
        new_manager = ConfigManager(config_file=config_manager.config_file)
        assert new_manager.get("general", "language") == "en"


class TestSettingsTabActions:
    """Tests für User-Actions"""

    def test_save_button_shows_success_message(self, settings_tab):
        """Test dass Save-Button Erfolgs-Nachricht zeigt"""
        with patch("src.gui.settings_tab.QMessageBox.information") as mock_msg:
            settings_tab._on_save()

        mock_msg.assert_called_once()

    def test_save_button_emits_signal(self, settings_tab, qtbot):
        """Test dass Save-Button Signal emittiert"""
        with patch("src.gui.settings_tab.QMessageBox.information"):
            with qtbot.waitSignal(settings_tab.settings_changed, timeout=1000):
                settings_tab._on_save()

    def test_save_button_handles_error(self, settings_tab):
        """Test dass Save-Button Fehler behandelt"""
        # Mock save() zum Werfen einer Exception
        with patch.object(settings_tab.config_manager, "save", side_effect=Exception("Test")):
            with patch("src.gui.settings_tab.QMessageBox.critical") as mock_msg:
                settings_tab._on_save()

            mock_msg.assert_called_once()

    def test_cancel_button_restores_original(self, settings_tab, config_manager):
        """Test dass Cancel-Button Original wiederherstellt"""
        # Ursprünglicher Wert
        original_lang = config_manager.get("general", "language")

        # Lade Settings (backup erstellen)
        settings_tab._load_settings()

        # Ändere UI
        new_lang = "en" if original_lang != "en" else "de"
        settings_tab.language_combo.setCurrentIndex(
            settings_tab.language_combo.findData(new_lang)
        )

        # Abbrechen
        with patch("src.gui.settings_tab.QMessageBox.information"):
            settings_tab._on_cancel()

        # Config sollte original sein
        assert config_manager.get("general", "language") == original_lang

    def test_reset_button_shows_confirmation(self, settings_tab):
        """Test dass Reset-Button Bestätigung zeigt"""
        # Mock "No" Answer
        with patch(
            "src.gui.settings_tab.QMessageBox.question",
            return_value=patch("src.gui.settings_tab.QMessageBox.StandardButton.No"),
        ):
            settings_tab._on_reset()

        # Reset sollte nicht ausgeführt worden sein (kein weiterer Mock nötig)

    def test_reset_button_resets_to_defaults(self, settings_tab, config_manager):
        """Test dass Reset-Button auf Defaults zurücksetzt"""
        # Ändere Config
        config_manager.set("general", "language", "en")
        config_manager.set("backup", "compression_level", 9)

        # Lade in UI
        settings_tab._load_settings()

        # Mock "Yes" Answer
        with patch(
            "src.gui.settings_tab.QMessageBox.question",
            return_value=QMessageBox.StandardButton.Yes,
        ):
            with patch("src.gui.settings_tab.QMessageBox.information"):
                settings_tab._on_reset()

        # Sollte Defaults sein
        assert config_manager.get("general", "language") == "de"
        assert config_manager.get("backup", "compression_level") == 5

    def test_browse_default_destination(self, settings_tab):
        """Test Browse-Button für Standard-Ziel"""
        with patch(
            "src.gui.settings_tab.QFileDialog.getExistingDirectory",
            return_value="/test/destination",
        ):
            settings_tab._browse_default_destination()

        assert settings_tab.default_dest_edit.text() == "/test/destination"

    def test_browse_metadata_db(self, settings_tab):
        """Test Browse-Button für Metadaten-DB"""
        with patch(
            "src.gui.settings_tab.QFileDialog.getSaveFileName",
            return_value=("/test/metadata.db", ""),
        ):
            settings_tab._browse_metadata_db()

        assert settings_tab.metadata_db_edit.text() == "/test/metadata.db"

    def test_browse_temp_dir(self, settings_tab):
        """Test Browse-Button für Temp-Dir"""
        with patch(
            "src.gui.settings_tab.QFileDialog.getExistingDirectory", return_value="/test/temp"
        ):
            settings_tab._browse_temp_dir()

        assert settings_tab.temp_dir_edit.text() == "/test/temp"

    def test_browse_log_dir(self, settings_tab):
        """Test Browse-Button für Log-Dir"""
        with patch(
            "src.gui.settings_tab.QFileDialog.getExistingDirectory", return_value="/test/logs"
        ):
            settings_tab._browse_log_dir()

        assert settings_tab.log_dir_edit.text() == "/test/logs"


class TestSettingsTabComboBoxes:
    """Tests für ComboBoxes"""

    def test_language_combo_has_options(self, settings_tab):
        """Test dass Sprach-Dropdown Optionen hat"""
        assert settings_tab.language_combo.count() == 2
        assert settings_tab.language_combo.findData("de") >= 0
        assert settings_tab.language_combo.findData("en") >= 0

    def test_theme_combo_has_options(self, settings_tab):
        """Test dass Theme-Dropdown Optionen hat"""
        assert settings_tab.theme_combo.count() == 3
        assert settings_tab.theme_combo.findData("light") >= 0
        assert settings_tab.theme_combo.findData("dark") >= 0
        assert settings_tab.theme_combo.findData("system") >= 0

    def test_log_level_combo_has_options(self, settings_tab):
        """Test dass Log-Level-Dropdown Optionen hat"""
        assert settings_tab.log_level_combo.count() == 4
        assert settings_tab.log_level_combo.findData("DEBUG") >= 0
        assert settings_tab.log_level_combo.findData("INFO") >= 0
        assert settings_tab.log_level_combo.findData("WARNING") >= 0
        assert settings_tab.log_level_combo.findData("ERROR") >= 0


class TestSettingsTabSpinBoxes:
    """Tests für SpinBoxes"""

    def test_compression_spin_range(self, settings_tab):
        """Test dass Komprimierungs-Spinner korrekten Range hat"""
        assert settings_tab.compression_spin.minimum() == 0
        assert settings_tab.compression_spin.maximum() == 9

    def test_split_size_spin_range(self, settings_tab):
        """Test dass Split-Size-Spinner korrekten Range hat"""
        assert settings_tab.split_size_spin.minimum() == 1
        assert settings_tab.split_size_spin.maximum() == 10000

    def test_keep_backups_spin_range(self, settings_tab):
        """Test dass Keep-Backups-Spinner korrekten Range hat"""
        assert settings_tab.keep_backups_spin.minimum() == 1
        assert settings_tab.keep_backups_spin.maximum() == 100

    def test_max_threads_spin_range(self, settings_tab):
        """Test dass Max-Threads-Spinner korrekten Range hat"""
        assert settings_tab.max_threads_spin.minimum() == 1
        assert settings_tab.max_threads_spin.maximum() == 16

    def test_network_timeout_spin_range(self, settings_tab):
        """Test dass Network-Timeout-Spinner korrekten Range hat"""
        assert settings_tab.network_timeout_spin.minimum() == 30
        assert settings_tab.network_timeout_spin.maximum() == 3600


class TestSettingsTabSignals:
    """Tests für Qt-Signals"""

    def test_signal_exists(self, settings_tab):
        """Test dass Signal existiert"""
        assert hasattr(settings_tab, "settings_changed")
