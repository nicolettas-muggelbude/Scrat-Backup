"""
Unit-Tests für Backup-Tab GUI
"""

from unittest.mock import Mock, patch

import pytest

from src.core.backup_engine import BackupProgress, BackupResult
from src.gui.backup_tab import BackupTab


@pytest.fixture
def backup_tab(qtbot):
    """BackupTab-Instanz für Tests"""
    tab = BackupTab()
    qtbot.addWidget(tab)
    return tab


class TestBackupTabInit:
    """Tests für Initialisierung"""

    def test_init(self, backup_tab):
        """Test dass Tab korrekt initialisiert wird"""
        assert backup_tab is not None
        assert backup_tab.metadata_manager is None
        assert backup_tab.backup_engine is None
        assert backup_tab.is_backup_running is False

    def test_ui_components_exist(self, backup_tab):
        """Test dass alle UI-Komponenten existieren"""
        # Steuerung
        assert backup_tab.config_combo is not None
        assert backup_tab.type_combo is not None
        assert backup_tab.start_button is not None
        assert backup_tab.stop_button is not None

        # Progress
        assert backup_tab.status_label is not None
        assert backup_tab.progress_bar is not None
        assert backup_tab.current_file_label is not None
        assert backup_tab.stats_label is not None
        assert backup_tab.error_label is not None

        # History
        assert backup_tab.history_table is not None

    def test_initial_state(self, backup_tab):
        """Test initialer Zustand"""
        # Buttons
        assert backup_tab.start_button.isEnabled() is True
        assert backup_tab.stop_button.isEnabled() is False

        # Progress
        assert backup_tab.progress_bar.value() == 0
        assert backup_tab.status_label.text() == "Bereit"

        # Error versteckt
        assert backup_tab.error_label.isHidden() is True


class TestBackupTabConfigSelection:
    """Tests für Konfigurations-Auswahl"""

    def test_config_combo_has_items(self, backup_tab):
        """Test dass Config-Dropdown Items hat"""
        assert backup_tab.config_combo.count() >= 2

    def test_type_combo_has_items(self, backup_tab):
        """Test dass Typ-Dropdown Items hat"""
        assert backup_tab.type_combo.count() == 2
        assert backup_tab.type_combo.itemData(0) == "full"
        assert backup_tab.type_combo.itemData(1) == "incremental"


class TestBackupTabProgressUpdates:
    """Tests für Progress-Updates"""

    def test_update_progress_ui(self, backup_tab):
        """Test dass Progress-UI aktualisiert wird"""
        progress = BackupProgress(
            backup_id="test123",
            phase="compressing",
            files_total=100,
            files_processed=50,
            bytes_total=1000000,
            bytes_processed=500000,
            current_file="test.txt",
        )

        backup_tab._update_progress_ui(progress)

        # Status
        assert "Komprimiere" in backup_tab.status_label.text()

        # Progress-Bar
        assert backup_tab.progress_bar.value() == 50

        # Dateiname
        assert "test.txt" in backup_tab.current_file_label.text()

        # Stats
        assert "50/100" in backup_tab.stats_label.text()

    def test_progress_phases(self, backup_tab):
        """Test dass alle Phasen korrekt angezeigt werden"""
        phases = {
            "scanning": "Scanne",
            "compressing": "Komprimiere",
            "encrypting": "Verschlüssele",
            "uploading": "Lade hoch",
        }

        for phase, expected_text in phases.items():
            progress = BackupProgress(backup_id="test", phase=phase)
            backup_tab._update_progress_ui(progress)
            assert expected_text in backup_tab.status_label.text()


class TestBackupTabCompletion:
    """Tests für Backup-Abschluss"""

    def test_backup_completed_success(self, backup_tab, qtbot):
        """Test erfolgreicher Backup-Abschluss"""
        result = BackupResult(
            backup_id="test123",
            success=True,
            backup_type="full",
            files_total=100,
            size_original=10000000,
            size_compressed=5000000,
            duration_seconds=60.0,
        )

        # Mock MessageBox
        with patch("src.gui.backup_tab.QMessageBox.information") as mock_msg:
            backup_tab._on_backup_completed(result)

        # Status
        assert "erfolgreich" in backup_tab.status_label.text()
        assert backup_tab.progress_bar.value() == 100

        # Buttons
        assert backup_tab.start_button.isEnabled() is True
        assert backup_tab.stop_button.isEnabled() is False

        # MessageBox wurde aufgerufen
        mock_msg.assert_called_once()

    def test_backup_completed_failure(self, backup_tab, qtbot):
        """Test fehlgeschlagener Backup"""
        result = BackupResult(
            backup_id="test123",
            success=False,
            backup_type="full",
            files_total=0,
            size_original=0,
            size_compressed=0,
            duration_seconds=0.0,
            errors=["Error 1", "Error 2"],
        )

        # Mock MessageBox
        with patch("src.gui.backup_tab.QMessageBox.critical") as mock_msg:
            backup_tab._on_backup_completed(result)

        # Status
        assert "fehlgeschlagen" in backup_tab.status_label.text()
        assert backup_tab.progress_bar.value() == 0

        # MessageBox wurde aufgerufen
        mock_msg.assert_called_once()

    def test_backup_failed(self, backup_tab):
        """Test Backup-Fehler"""
        error_msg = "Test error"

        # Mock MessageBox
        with patch("src.gui.backup_tab.QMessageBox.critical"):
            backup_tab._on_backup_failed(error_msg)

        # Status
        assert "fehlgeschlagen" in backup_tab.status_label.text()

        # Error-Label sichtbar
        assert backup_tab.error_label.isHidden() is False
        assert error_msg in backup_tab.error_label.text()

        # Buttons
        assert backup_tab.start_button.isEnabled() is True
        assert backup_tab.stop_button.isEnabled() is False


class TestBackupTabHistory:
    """Tests für Backup-History"""

    def test_load_history_no_metadata_manager(self, backup_tab):
        """Test History-Laden ohne MetadataManager"""
        # Sollte nicht crashen
        backup_tab._load_history()
        assert backup_tab.history_table.rowCount() == 0

    def test_set_metadata_manager(self, backup_tab):
        """Test MetadataManager setzen"""
        mock_manager = Mock()
        mock_manager.list_backups.return_value = []

        backup_tab.set_metadata_manager(mock_manager)

        assert backup_tab.metadata_manager == mock_manager
        mock_manager.list_backups.assert_called_once()

    def test_load_history_with_backups(self, backup_tab):
        """Test History-Laden mit Backups"""
        mock_manager = Mock()
        mock_manager.list_backups.return_value = [
            {
                "backup_id": "test1",
                "timestamp": "2024-01-01T12:00:00",
                "backup_type": "full",
                "file_count": 100,
                "size_original": 10000000,
                "duration_seconds": 60.0,
                "status": "completed",
            },
            {
                "backup_id": "test2",
                "timestamp": "2024-01-02T13:00:00",
                "backup_type": "incremental",
                "file_count": 50,
                "size_original": 5000000,
                "duration_seconds": 30.0,
                "status": "completed",
            },
        ]

        backup_tab.metadata_manager = mock_manager
        backup_tab._load_history()

        # Table sollte 2 Zeilen haben
        assert backup_tab.history_table.rowCount() == 2

        # Erste Zeile prüfen
        assert "01.01.2024" in backup_tab.history_table.item(0, 0).text()
        assert "Full" in backup_tab.history_table.item(0, 1).text()
        assert "100" in backup_tab.history_table.item(0, 2).text()


class TestBackupTabActions:
    """Tests für User-Actions"""

    def test_start_backup_no_metadata_manager(self, backup_tab, qtbot):
        """Test Backup-Start ohne MetadataManager"""
        # Mock MessageBox
        with patch("src.gui.backup_tab.QMessageBox.warning") as mock_msg:
            backup_tab._on_start_backup()

        # Warning wurde angezeigt
        mock_msg.assert_called_once()

        # Backup wurde nicht gestartet
        assert backup_tab.is_backup_running is False

    def test_stop_backup(self, backup_tab):
        """Test Backup-Stopp (TODO: Implementierung)"""
        # Mock MessageBox
        with patch("src.gui.backup_tab.QMessageBox.information") as mock_msg:
            backup_tab._on_stop_backup()

        # Info wurde angezeigt
        mock_msg.assert_called_once()


class TestBackupTabSignals:
    """Tests für Qt-Signals"""

    def test_signals_exist(self, backup_tab):
        """Test dass alle Signals existieren"""
        # Signals sollten existieren
        assert hasattr(backup_tab, "progress_updated")
        assert hasattr(backup_tab, "backup_completed")
        assert hasattr(backup_tab, "backup_failed")
