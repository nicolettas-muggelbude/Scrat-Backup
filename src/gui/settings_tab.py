"""
Settings-Tab für Scrat-Backup
GUI für Applikations-Einstellungen
"""

import logging
from typing import Optional

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from src.core.config_manager import ConfigManager

logger = logging.getLogger(__name__)


class SettingsTab(QWidget):
    """
    Settings-Tab für Hauptfenster

    Features:
    - Allgemeine Einstellungen (Sprache, Theme)
    - Backup-Einstellungen (Standard-Werte)
    - Speicherpfade (Datenbank, Temp, Logs)
    - Erweiterte Einstellungen (Logging, Performance)
    - Speichern/Abbrechen/Reset-Buttons
    """

    # Signals
    settings_changed = pyqtSignal()  # Wenn Einstellungen gespeichert wurden

    def __init__(self, parent: Optional[QWidget] = None):
        """Initialisiert Settings-Tab"""
        super().__init__(parent)

        self.config_manager: Optional[ConfigManager] = None
        self.original_config: dict = {}  # Backup für Cancel-Funktion

        # Setup UI
        self._setup_ui()

        logger.info("Settings-Tab initialisiert")

    def _setup_ui(self) -> None:
        """Erstellt UI-Komponenten"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Header
        header = QLabel("⚙️ Einstellungen")
        header.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(header)

        # Scroll-Area für Settings
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")

        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setSpacing(15)

        # Settings-Gruppen
        scroll_layout.addWidget(self._create_general_section())
        scroll_layout.addWidget(self._create_backup_section())
        scroll_layout.addWidget(self._create_paths_section())
        scroll_layout.addWidget(self._create_advanced_section())
        scroll_layout.addStretch()

        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll, 1)  # Stretch-Faktor 1

        # Buttons
        button_layout = self._create_button_section()
        layout.addLayout(button_layout)

    def _create_general_section(self) -> QGroupBox:
        """Erstellt Allgemeine Einstellungen"""
        group = QGroupBox("🌍 Allgemeine Einstellungen")
        form = QFormLayout()

        # Sprache
        self.language_combo = QComboBox()
        self.language_combo.addItem("🇩🇪 Deutsch", "de")
        self.language_combo.addItem("🇬🇧 English", "en")
        form.addRow("Sprache:", self.language_combo)

        # Theme
        self.theme_combo = QComboBox()
        self.theme_combo.addItem("💡 Hell", "light")
        self.theme_combo.addItem("🌙 Dunkel", "dark")
        self.theme_combo.addItem("🖥️ System", "system")
        form.addRow("Theme:", self.theme_combo)

        # Autostart
        self.autostart_checkbox = QCheckBox("Mit System starten")
        form.addRow("", self.autostart_checkbox)

        # Minimize to Tray
        self.minimize_tray_checkbox = QCheckBox("In Systemablage minimieren")
        form.addRow("", self.minimize_tray_checkbox)

        group.setLayout(form)
        return group

    def _create_backup_section(self) -> QGroupBox:
        """Erstellt Backup-Einstellungen"""
        group = QGroupBox("💾 Backup-Einstellungen")
        form = QFormLayout()

        # Standard-Zielverzeichnis
        dest_layout = QHBoxLayout()
        self.default_dest_edit = QLineEdit()
        dest_layout.addWidget(self.default_dest_edit, 1)

        browse_btn = QPushButton("📁 Durchsuchen")
        browse_btn.clicked.connect(self._browse_default_destination)
        dest_layout.addWidget(browse_btn)

        form.addRow("Standard-Ziel:", dest_layout)

        # Komprimierungslevel
        self.compression_spin = QSpinBox()
        self.compression_spin.setRange(0, 9)
        self.compression_spin.setSuffix(" (0=schnell, 9=klein)")
        form.addRow("Komprimierung:", self.compression_spin)

        # Archive-Split-Größe
        self.split_size_spin = QSpinBox()
        self.split_size_spin.setRange(1, 10000)
        self.split_size_spin.setSuffix(" MB")
        form.addRow("Archive-Teilgröße:", self.split_size_spin)

        # Backup-Aufbewahrung
        self.keep_backups_spin = QSpinBox()
        self.keep_backups_spin.setRange(1, 100)
        self.keep_backups_spin.setSuffix(" Backups")
        form.addRow("Aufbewahrung:", self.keep_backups_spin)

        # Verify after Backup
        self.verify_checkbox = QCheckBox("Nach Backup verifizieren")
        form.addRow("", self.verify_checkbox)

        group.setLayout(form)
        return group

    def _create_paths_section(self) -> QGroupBox:
        """Erstellt Speicherpfade-Einstellungen"""
        group = QGroupBox("📂 Speicherpfade")
        form = QFormLayout()

        # Metadaten-Datenbank
        db_layout = QHBoxLayout()
        self.metadata_db_edit = QLineEdit()
        self.metadata_db_edit.setPlaceholderText("Leer = Standard (~/.scrat-backup/metadata.db)")
        db_layout.addWidget(self.metadata_db_edit, 1)

        db_browse_btn = QPushButton("📁")
        db_browse_btn.setMaximumWidth(40)
        db_browse_btn.clicked.connect(self._browse_metadata_db)
        db_layout.addWidget(db_browse_btn)

        form.addRow("Metadaten-DB:", db_layout)

        # Temporäres Verzeichnis
        temp_layout = QHBoxLayout()
        self.temp_dir_edit = QLineEdit()
        self.temp_dir_edit.setPlaceholderText("Leer = System-Temp")
        temp_layout.addWidget(self.temp_dir_edit, 1)

        temp_browse_btn = QPushButton("📁")
        temp_browse_btn.setMaximumWidth(40)
        temp_browse_btn.clicked.connect(self._browse_temp_dir)
        temp_layout.addWidget(temp_browse_btn)

        form.addRow("Temp-Verzeichnis:", temp_layout)

        # Log-Verzeichnis
        log_layout = QHBoxLayout()
        self.log_dir_edit = QLineEdit()
        self.log_dir_edit.setPlaceholderText("Leer = Standard (~/.scrat-backup/logs)")
        log_layout.addWidget(self.log_dir_edit, 1)

        log_browse_btn = QPushButton("📁")
        log_browse_btn.setMaximumWidth(40)
        log_browse_btn.clicked.connect(self._browse_log_dir)
        log_layout.addWidget(log_browse_btn)

        form.addRow("Log-Verzeichnis:", log_layout)

        group.setLayout(form)
        return group

    def _create_advanced_section(self) -> QGroupBox:
        """Erstellt Erweiterte Einstellungen"""
        group = QGroupBox("🔧 Erweiterte Einstellungen")
        form = QFormLayout()

        # Logging-Level
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItem("🐛 DEBUG", "DEBUG")
        self.log_level_combo.addItem("ℹ️ INFO", "INFO")
        self.log_level_combo.addItem("⚠️ WARNING", "WARNING")
        self.log_level_combo.addItem("❌ ERROR", "ERROR")
        form.addRow("Log-Level:", self.log_level_combo)

        # Max Threads
        self.max_threads_spin = QSpinBox()
        self.max_threads_spin.setRange(1, 16)
        self.max_threads_spin.setSuffix(" Threads")
        form.addRow("Max. Threads:", self.max_threads_spin)

        # Network Timeout
        self.network_timeout_spin = QSpinBox()
        self.network_timeout_spin.setRange(30, 3600)
        self.network_timeout_spin.setSuffix(" Sekunden")
        form.addRow("Netzwerk-Timeout:", self.network_timeout_spin)

        # Retry Count
        self.retry_count_spin = QSpinBox()
        self.retry_count_spin.setRange(0, 10)
        self.retry_count_spin.setSuffix(" Versuche")
        form.addRow("Wiederholungen:", self.retry_count_spin)

        group.setLayout(form)
        return group

    def _create_button_section(self) -> QHBoxLayout:
        """Erstellt Button-Bereich"""
        layout = QHBoxLayout()
        layout.addStretch()

        # Reset-Button
        self.reset_button = QPushButton("🔄 Standard wiederherstellen")
        self.reset_button.clicked.connect(self._on_reset)
        layout.addWidget(self.reset_button)

        # Abbrechen-Button
        self.cancel_button = QPushButton("❌ Abbrechen")
        self.cancel_button.clicked.connect(self._on_cancel)
        layout.addWidget(self.cancel_button)

        # Speichern-Button
        self.save_button = QPushButton("💾 Speichern")
        self.save_button.setStyleSheet(
            "QPushButton {"
            "  background-color: #0078d4;"
            "  color: white;"
            "  padding: 10px 20px;"
            "  border-radius: 5px;"
            "  font-weight: bold;"
            "}"
            "QPushButton:hover {"
            "  background-color: #005a9e;"
            "}"
        )
        self.save_button.clicked.connect(self._on_save)
        layout.addWidget(self.save_button)

        return layout

    def set_config_manager(self, config_manager: ConfigManager) -> None:
        """
        Setzt ConfigManager und lädt Settings in UI

        Args:
            config_manager: ConfigManager-Instanz
        """
        self.config_manager = config_manager
        self._load_settings()

    def _load_settings(self) -> None:
        """Lädt Settings aus ConfigManager in UI"""
        if not self.config_manager:
            return

        # Backup für Cancel
        self.original_config = {
            "general": self.config_manager.get_section("general").copy(),
            "backup": self.config_manager.get_section("backup").copy(),
            "paths": self.config_manager.get_section("paths").copy(),
            "advanced": self.config_manager.get_section("advanced").copy(),
        }

        # Allgemein
        language = self.config_manager.get("general", "language", "de")
        index = self.language_combo.findData(language)
        if index >= 0:
            self.language_combo.setCurrentIndex(index)

        theme = self.config_manager.get("general", "theme", "system")
        index = self.theme_combo.findData(theme)
        if index >= 0:
            self.theme_combo.setCurrentIndex(index)

        self.autostart_checkbox.setChecked(
            self.config_manager.get("general", "start_with_system", False)
        )
        self.minimize_tray_checkbox.setChecked(
            self.config_manager.get("general", "minimize_to_tray", False)
        )

        # Backup
        self.default_dest_edit.setText(
            self.config_manager.get("backup", "default_destination", "")
        )
        self.compression_spin.setValue(
            self.config_manager.get("backup", "compression_level", 5)
        )
        self.split_size_spin.setValue(
            self.config_manager.get("backup", "archive_split_size_mb", 100)
        )
        self.keep_backups_spin.setValue(self.config_manager.get("backup", "keep_backups", 10))
        self.verify_checkbox.setChecked(
            self.config_manager.get("backup", "verify_after_backup", True)
        )

        # Pfade
        self.metadata_db_edit.setText(self.config_manager.get("paths", "metadata_db", ""))
        self.temp_dir_edit.setText(self.config_manager.get("paths", "temp_dir", ""))
        self.log_dir_edit.setText(self.config_manager.get("paths", "log_dir", ""))

        # Erweitert
        log_level = self.config_manager.get("advanced", "log_level", "INFO")
        index = self.log_level_combo.findData(log_level)
        if index >= 0:
            self.log_level_combo.setCurrentIndex(index)

        self.max_threads_spin.setValue(self.config_manager.get("advanced", "max_threads", 4))
        self.network_timeout_spin.setValue(
            self.config_manager.get("advanced", "network_timeout", 300)
        )
        self.retry_count_spin.setValue(self.config_manager.get("advanced", "retry_count", 3))

    def _save_settings(self) -> None:
        """Speichert Settings aus UI in ConfigManager"""
        if not self.config_manager:
            return

        # Allgemein
        self.config_manager.set("general", "language", self.language_combo.currentData())
        self.config_manager.set("general", "theme", self.theme_combo.currentData())
        self.config_manager.set(
            "general", "start_with_system", self.autostart_checkbox.isChecked()
        )
        self.config_manager.set(
            "general", "minimize_to_tray", self.minimize_tray_checkbox.isChecked()
        )

        # Backup
        self.config_manager.set("backup", "default_destination", self.default_dest_edit.text())
        self.config_manager.set("backup", "compression_level", self.compression_spin.value())
        self.config_manager.set("backup", "archive_split_size_mb", self.split_size_spin.value())
        self.config_manager.set("backup", "keep_backups", self.keep_backups_spin.value())
        self.config_manager.set("backup", "verify_after_backup", self.verify_checkbox.isChecked())

        # Pfade
        self.config_manager.set("paths", "metadata_db", self.metadata_db_edit.text())
        self.config_manager.set("paths", "temp_dir", self.temp_dir_edit.text())
        self.config_manager.set("paths", "log_dir", self.log_dir_edit.text())

        # Erweitert
        self.config_manager.set("advanced", "log_level", self.log_level_combo.currentData())
        self.config_manager.set("advanced", "max_threads", self.max_threads_spin.value())
        self.config_manager.set("advanced", "network_timeout", self.network_timeout_spin.value())
        self.config_manager.set("advanced", "retry_count", self.retry_count_spin.value())

        # Speichere in Datei
        self.config_manager.save()

    def _on_save(self) -> None:
        """Speichert Einstellungen"""
        try:
            self._save_settings()

            QMessageBox.information(
                self,
                "Einstellungen gespeichert",
                "Die Einstellungen wurden erfolgreich gespeichert.",
            )

            # Signal an MainWindow
            self.settings_changed.emit()

            logger.info("Einstellungen gespeichert")

        except Exception as e:
            logger.error(f"Fehler beim Speichern: {e}", exc_info=True)
            QMessageBox.critical(
                self, "Fehler", f"Fehler beim Speichern der Einstellungen:\n{e}"
            )

    def _on_cancel(self) -> None:
        """Verwirft Änderungen"""
        if not self.config_manager:
            return

        # Stelle Original-Config wieder her
        for section, values in self.original_config.items():
            self.config_manager.set_section(section, values)

        # Lade Settings neu in UI
        self._load_settings()

        QMessageBox.information(self, "Abgebrochen", "Änderungen wurden verworfen.")

    def _on_reset(self) -> None:
        """Setzt auf Defaults zurück"""
        reply = QMessageBox.question(
            self,
            "Standard wiederherstellen",
            "Möchten Sie wirklich alle Einstellungen auf die Standardwerte zurücksetzen?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            if self.config_manager:
                self.config_manager.reset_to_defaults()
                self._load_settings()

                QMessageBox.information(
                    self, "Zurückgesetzt", "Einstellungen wurden auf Standardwerte zurückgesetzt."
                )

    def _browse_default_destination(self) -> None:
        """Öffnet Dialog für Standard-Zielverzeichnis"""
        path = QFileDialog.getExistingDirectory(self, "Standard-Zielverzeichnis auswählen")
        if path:
            self.default_dest_edit.setText(path)

    def _browse_metadata_db(self) -> None:
        """Öffnet Dialog für Metadaten-Datenbank"""
        path, _ = QFileDialog.getSaveFileName(
            self, "Metadaten-Datenbank auswählen", "", "SQLite Database (*.db)"
        )
        if path:
            self.metadata_db_edit.setText(path)

    def _browse_temp_dir(self) -> None:
        """Öffnet Dialog für Temp-Verzeichnis"""
        path = QFileDialog.getExistingDirectory(self, "Temporäres Verzeichnis auswählen")
        if path:
            self.temp_dir_edit.setText(path)

    def _browse_log_dir(self) -> None:
        """Öffnet Dialog für Log-Verzeichnis"""
        path = QFileDialog.getExistingDirectory(self, "Log-Verzeichnis auswählen")
        if path:
            self.log_dir_edit.setText(path)
