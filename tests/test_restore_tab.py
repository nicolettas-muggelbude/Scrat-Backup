"""
Unit-Tests für Restore-Tab GUI
"""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from PyQt6.QtCore import Qt

from src.core.restore_engine import RestoreProgress, RestoreResult
from src.gui.restore_tab import RestoreTab


@pytest.fixture
def restore_tab(qtbot):
    """RestoreTab-Instanz für Tests"""
    tab = RestoreTab()
    qtbot.addWidget(tab)
    return tab


class TestRestoreTabInit:
    """Tests für Initialisierung"""

    def test_init(self, restore_tab):
        """Test dass Tab korrekt initialisiert wird"""
        assert restore_tab is not None
        assert restore_tab.metadata_manager is None
        assert restore_tab.restore_engine is None
        assert restore_tab.is_restore_running is False
        assert restore_tab.selected_backup_id is None

    def test_ui_components_exist(self, restore_tab):
        """Test dass alle UI-Komponenten existieren"""
        # Backup-Auswahl
        assert restore_tab.backup_table is not None

        # Konfiguration
        assert restore_tab.dest_path_edit is not None
        assert restore_tab.password_edit is not None
        assert restore_tab.overwrite_checkbox is not None
        assert restore_tab.restore_permissions_checkbox is not None
        assert restore_tab.restore_button is not None
        assert restore_tab.stop_button is not None

        # Progress
        assert restore_tab.status_label is not None
        assert restore_tab.progress_bar is not None
        assert restore_tab.current_file_label is not None
        assert restore_tab.stats_label is not None
        assert restore_tab.error_label is not None

    def test_initial_state(self, restore_tab):
        """Test initialer Zustand"""
        # Buttons
        assert restore_tab.restore_button.isEnabled() is False  # Kein Backup ausgewählt
        assert restore_tab.stop_button.isEnabled() is False

        # Progress
        assert restore_tab.progress_bar.value() == 0
        assert restore_tab.status_label.text() == "Bereit"

        # Error versteckt
        assert restore_tab.error_label.isHidden() is True


class TestRestoreTabBackupSelection:
    """Tests für Backup-Auswahl"""

    def test_load_backups_no_metadata_manager(self, restore_tab):
        """Test Backup-Laden ohne MetadataManager"""
        # Sollte nicht crashen
        restore_tab._load_backups()
        assert restore_tab.backup_table.rowCount() == 0

    def test_set_metadata_manager(self, restore_tab):
        """Test MetadataManager setzen"""
        mock_manager = Mock()
        mock_manager.list_backups.return_value = []

        restore_tab.set_metadata_manager(mock_manager)

        assert restore_tab.metadata_manager == mock_manager
        mock_manager.list_backups.assert_called_once()

    def test_load_backups_with_data(self, restore_tab):
        """Test Backup-Laden mit Daten"""
        mock_manager = Mock()
        mock_manager.list_backups.return_value = [
            {
                "backup_id": 1,
                "timestamp": "2024-01-01T12:00:00",
                "backup_type": "full",
                "file_count": 100,
                "size_original": 10000000,
                "status": "completed",
            },
            {
                "backup_id": 2,
                "timestamp": "2024-01-02T13:00:00",
                "backup_type": "incremental",
                "file_count": 50,
                "size_original": 5000000,
                "status": "completed",
            },
        ]

        restore_tab.metadata_manager = mock_manager
        restore_tab._load_backups()

        # Table sollte 2 Zeilen haben
        assert restore_tab.backup_table.rowCount() == 2

    def test_backup_selection(self, restore_tab, qtbot):
        """Test Backup-Auswahl"""
        mock_manager = Mock()
        mock_manager.list_backups.return_value = [
            {
                "backup_id": 123,
                "timestamp": "2024-01-01T12:00:00",
                "backup_type": "full",
                "file_count": 100,
                "size_original": 10000000,
                "status": "completed",
            }
        ]

        restore_tab.metadata_manager = mock_manager
        restore_tab._load_backups()

        # Wähle erste Zeile
        restore_tab.backup_table.selectRow(0)

        # Backup sollte ausgewählt sein
        assert restore_tab.selected_backup_id == 123
        assert restore_tab.restore_button.isEnabled() is True


class TestRestoreTabProgressUpdates:
    """Tests für Progress-Updates"""

    def test_update_progress_ui(self, restore_tab):
        """Test dass Progress-UI aktualisiert wird"""
        progress = RestoreProgress(
            phase="extracting",
            files_total=100,
            files_processed=50,
            bytes_total=1000000,
            bytes_processed=500000,
            current_file="test.txt",
        )

        restore_tab._update_progress_ui(progress)

        # Status
        assert "Entpacke" in restore_tab.status_label.text()

        # Progress-Bar
        assert restore_tab.progress_bar.value() == 50

        # Dateiname
        assert "test.txt" in restore_tab.current_file_label.text()

        # Stats
        assert "50/100" in restore_tab.stats_label.text()

    def test_progress_phases(self, restore_tab):
        """Test dass alle Phasen korrekt angezeigt werden"""
        phases = {
            "preparing": "Vorbereite",
            "downloading": "Lade Archive",
            "decrypting": "Entschlüssele",
            "extracting": "Entpacke",
            "restoring": "Stelle wieder her",
        }

        for phase, expected_text in phases.items():
            progress = RestoreProgress(phase=phase)
            restore_tab._update_progress_ui(progress)
            assert expected_text in restore_tab.status_label.text()


class TestRestoreTabCompletion:
    """Tests für Restore-Abschluss"""

    def test_restore_completed_success(self, restore_tab):
        """Test erfolgreicher Restore-Abschluss"""
        result = RestoreResult(
            success=True,
            files_restored=100,
            bytes_restored=10000000,
            duration_seconds=60.0,
        )

        # Mock MessageBox
        with patch("src.gui.restore_tab.QMessageBox.information") as mock_msg:
            restore_tab._on_restore_completed(result)

        # Status
        assert "erfolgreich" in restore_tab.status_label.text()
        assert restore_tab.progress_bar.value() == 100

        # Buttons
        assert restore_tab.restore_button.isEnabled() is True
        assert restore_tab.stop_button.isEnabled() is False

        # MessageBox wurde aufgerufen
        mock_msg.assert_called_once()

    def test_restore_completed_failure(self, restore_tab):
        """Test fehlgeschlagener Restore"""
        result = RestoreResult(
            success=False,
            files_restored=0,
            bytes_restored=0,
            duration_seconds=0.0,
            errors=["Error 1", "Error 2"],
        )

        # Mock MessageBox
        with patch("src.gui.restore_tab.QMessageBox.critical") as mock_msg:
            restore_tab._on_restore_completed(result)

        # Status
        assert "fehlgeschlagen" in restore_tab.status_label.text()
        assert restore_tab.progress_bar.value() == 0

        # MessageBox wurde aufgerufen
        mock_msg.assert_called_once()

    def test_restore_failed(self, restore_tab):
        """Test Restore-Fehler"""
        error_msg = "Test error"

        # Mock MessageBox
        with patch("src.gui.restore_tab.QMessageBox.critical") as mock_msg:
            restore_tab._on_restore_failed(error_msg)

        # Status
        assert "fehlgeschlagen" in restore_tab.status_label.text()

        # Error-Label sichtbar
        assert restore_tab.error_label.isHidden() is False
        assert error_msg in restore_tab.error_label.text()

        # Buttons
        assert restore_tab.restore_button.isEnabled() is True
        assert restore_tab.stop_button.isEnabled() is False


class TestRestoreTabActions:
    """Tests für User-Actions"""

    def test_browse_destination(self, restore_tab):
        """Test Ziel-Verzeichnis durchsuchen"""
        # Mock FileDialog
        with patch(
            "src.gui.restore_tab.QFileDialog.getExistingDirectory",
            return_value="/test/path",
        ):
            restore_tab._browse_destination()

        assert restore_tab.dest_path_edit.text() == "/test/path"

    def test_start_restore_no_password(self, restore_tab):
        """Test Restore-Start ohne Passwort"""
        restore_tab.selected_backup_id = 1
        restore_tab.password_edit.setText("")

        # Mock MessageBox
        with patch("src.gui.restore_tab.QMessageBox.warning") as mock_msg:
            restore_tab._on_start_restore()

        # Warning wurde angezeigt
        mock_msg.assert_called_once()

    def test_start_restore_invalid_dest(self, restore_tab):
        """Test Restore-Start mit ungültigem Ziel"""
        restore_tab.selected_backup_id = 1
        restore_tab.password_edit.setText("password")
        restore_tab.dest_path_edit.setText("/nonexistent/path/subdir")

        # Mock MessageBox
        with patch("src.gui.restore_tab.QMessageBox.warning") as mock_msg:
            restore_tab._on_start_restore()

        # Warning wurde angezeigt
        mock_msg.assert_called_once()

    def test_stop_restore(self, restore_tab):
        """Test Restore-Stopp (TODO: Implementierung)"""
        # Mock MessageBox
        with patch("src.gui.restore_tab.QMessageBox.information") as mock_msg:
            restore_tab._on_stop_restore()

        # Info wurde angezeigt
        mock_msg.assert_called_once()


class TestRestoreTabSignals:
    """Tests für Qt-Signals"""

    def test_signals_exist(self, restore_tab):
        """Test dass alle Signals existieren"""
        # Signals sollten existieren
        assert hasattr(restore_tab, "progress_updated")
        assert hasattr(restore_tab, "restore_completed")
        assert hasattr(restore_tab, "restore_failed")
