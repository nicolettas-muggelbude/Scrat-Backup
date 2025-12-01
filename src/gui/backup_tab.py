"""
Backup-Tab für Scrat-Backup
GUI für Backup-Operationen mit Progress-Tracking
"""

import logging
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt6.QtWidgets import (
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.core.backup_engine import BackupConfig, BackupEngine, BackupProgress, BackupResult
from src.core.metadata_manager import MetadataManager
from src.gui.event_bus import get_event_bus

logger = logging.getLogger(__name__)


class BackupTab(QWidget):
    """
    Backup-Tab für Hauptfenster

    Features:
    - Backup-Konfiguration-Auswahl
    - Backup-Typ-Auswahl (Full vs Incremental)
    - Start/Stop-Buttons
    - Progress-Anzeige mit Details
    - Backup-History-Liste
    """

    # Signals für Thread-safe GUI-Updates
    progress_updated = pyqtSignal(object)  # BackupProgress
    backup_completed = pyqtSignal(object)  # BackupResult
    backup_failed = pyqtSignal(str)  # Error message

    def __init__(self, parent: Optional[QWidget] = None):
        """Initialisiert Backup-Tab"""
        super().__init__(parent)

        self.event_bus = get_event_bus()
        self.metadata_manager: Optional[MetadataManager] = None
        self.backup_engine: Optional[BackupEngine] = None
        self.backup_thread: Optional[threading.Thread] = None
        self.is_backup_running = False

        # Setup UI
        self._setup_ui()
        self._connect_signals()

        logger.info("Backup-Tab initialisiert")

    def _setup_ui(self) -> None:
        """Erstellt UI-Komponenten"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Header
        header = QLabel("🔒 Backup")
        header.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(header)

        # Backup-Steuerung
        control_group = self._create_control_section()
        layout.addWidget(control_group)

        # Progress-Anzeige
        progress_group = self._create_progress_section()
        layout.addWidget(progress_group)

        # Backup-History
        history_group = self._create_history_section()
        layout.addWidget(history_group, 1)  # Stretch-Faktor 1

    def _create_control_section(self) -> QGroupBox:
        """Erstellt Steuerungs-Bereich"""
        group = QGroupBox("Backup-Steuerung")
        layout = QVBoxLayout()

        # Konfiguration-Auswahl
        config_layout = QHBoxLayout()
        config_layout.addWidget(QLabel("Konfiguration:"))

        self.config_combo = QComboBox()
        self.config_combo.addItem("Standard-Konfiguration")
        self.config_combo.addItem("-- Neue Konfiguration erstellen --")
        config_layout.addWidget(self.config_combo, 1)

        layout.addLayout(config_layout)

        # Backup-Typ-Auswahl
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Backup-Typ:"))

        self.type_combo = QComboBox()
        self.type_combo.addItem("📦 Vollbackup (Full)", "full")
        self.type_combo.addItem("📝 Inkrementell (Incremental)", "incremental")
        type_layout.addWidget(self.type_combo, 1)

        layout.addLayout(type_layout)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.start_button = QPushButton("▶ Backup starten")
        self.start_button.setStyleSheet(
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
            "QPushButton:disabled {"
            "  background-color: #ccc;"
            "}"
        )
        self.start_button.clicked.connect(self._on_start_backup)
        button_layout.addWidget(self.start_button)

        self.stop_button = QPushButton("⏹ Stoppen")
        self.stop_button.setEnabled(False)
        self.stop_button.setStyleSheet(
            "QPushButton {"
            "  background-color: #d13438;"
            "  color: white;"
            "  padding: 10px 20px;"
            "  border-radius: 5px;"
            "  font-weight: bold;"
            "}"
            "QPushButton:hover {"
            "  background-color: #a52a2d;"
            "}"
            "QPushButton:disabled {"
            "  background-color: #ccc;"
            "}"
        )
        self.stop_button.clicked.connect(self._on_stop_backup)
        button_layout.addWidget(self.stop_button)

        layout.addLayout(button_layout)

        group.setLayout(layout)
        return group

    def _create_progress_section(self) -> QGroupBox:
        """Erstellt Progress-Anzeige"""
        group = QGroupBox("Fortschritt")
        layout = QVBoxLayout()

        # Status-Label
        self.status_label = QLabel("Bereit")
        self.status_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(self.status_label)

        # Progress-Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        layout.addWidget(self.progress_bar)

        # Details
        details_layout = QHBoxLayout()

        # Aktuelle Datei
        self.current_file_label = QLabel("--")
        self.current_file_label.setStyleSheet("color: #666;")
        details_layout.addWidget(self.current_file_label, 1)

        # Statistiken
        self.stats_label = QLabel("--")
        self.stats_label.setStyleSheet("color: #666;")
        self.stats_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        details_layout.addWidget(self.stats_label)

        layout.addLayout(details_layout)

        # Fehler-Bereich (initial versteckt)
        self.error_label = QLabel()
        self.error_label.setStyleSheet(
            "background-color: #ffebee; color: #d32f2f; padding: 10px; border-radius: 5px;"
        )
        self.error_label.setWordWrap(True)
        self.error_label.hide()
        layout.addWidget(self.error_label)

        group.setLayout(layout)
        return group

    def _create_history_section(self) -> QGroupBox:
        """Erstellt Backup-History-Liste"""
        group = QGroupBox("Backup-Verlauf")
        layout = QVBoxLayout()

        # Table
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(6)
        self.history_table.setHorizontalHeaderLabels(
            ["Datum/Uhrzeit", "Typ", "Dateien", "Größe", "Dauer", "Status"]
        )

        # Header-Konfiguration
        header = self.history_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)

        # Keine Bearbeitung
        self.history_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.history_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        layout.addWidget(self.history_table)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        refresh_button = QPushButton("🔄 Aktualisieren")
        refresh_button.clicked.connect(self._load_history)
        button_layout.addWidget(refresh_button)

        layout.addLayout(button_layout)

        group.setLayout(layout)
        return group

    def _connect_signals(self) -> None:
        """Verbindet Signals für Thread-safe Updates"""
        self.progress_updated.connect(self._update_progress_ui)
        self.backup_completed.connect(self._on_backup_completed)
        self.backup_failed.connect(self._on_backup_failed)

    def set_metadata_manager(self, metadata_manager: MetadataManager) -> None:
        """
        Setzt MetadataManager

        Args:
            metadata_manager: MetadataManager-Instanz
        """
        self.metadata_manager = metadata_manager
        self._load_history()

    def _on_start_backup(self) -> None:
        """Startet Backup"""
        if self.is_backup_running:
            return

        # Config aus MetadataManager und UI auslesen
        if not self.metadata_manager:
            QMessageBox.warning(self, "Fehler", "Keine Metadaten-Datenbank konfiguriert")
            return

        # Hole Quellen aus Datenbank (alle aktivierten)
        sources = self.metadata_manager.get_sources()
        enabled_sources = [Path(s["windows_path"]) for s in sources if s.get("enabled", True)]

        if not enabled_sources:
            QMessageBox.warning(
                self,
                "Keine Quellen",
                "Keine Backup-Quellen konfiguriert.\n\nBitte konfiguriere zuerst Quellen in den Einstellungen.",
            )
            return

        # Hole Ziel aus Datenbank (erste aktivierte)
        destinations = self.metadata_manager.get_destinations()
        enabled_dests = [d for d in destinations if d.get("enabled", True)]

        if not enabled_dests:
            QMessageBox.warning(
                self,
                "Kein Ziel",
                "Kein Backup-Ziel konfiguriert.\n\nBitte konfiguriere zuerst ein Ziel in den Einstellungen.",
            )
            return

        first_dest = enabled_dests[0]
        import json

        dest_config = json.loads(first_dest["config"])

        # Backup-Typ aus UI
        backup_type = self.type_combo.currentData()  # "full" oder "incremental"

        # Passwort: Frage User mit Speicher-Option
        from src.gui.password_dialog import get_password

        password, ok = get_password(
            self, title="Backup-Passwort", message="Bitte gib das Backup-Passwort ein:", show_save_option=True
        )

        if not ok or not password:
            QMessageBox.warning(self, "Abgebrochen", "Backup abgebrochen - kein Passwort eingegeben.")
            return

        # Erstelle BackupConfig
        config = BackupConfig(
            sources=enabled_sources,
            destination_path=Path(dest_config.get("path", Path.home() / "scrat-backups")),
            destination_type=first_dest["type"],
            password=password,
            compression_level=5,
            backup_type=backup_type,
        )

        # Backup-Engine erstellen
        self.backup_engine = BackupEngine(
            metadata_manager=self.metadata_manager,
            config=config,
            progress_callback=self._on_progress_update,
        )

        # UI vorbereiten
        self.is_backup_running = True
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.status_label.setText("Starte Backup...")
        self.progress_bar.setValue(0)
        self.error_label.hide()

        # Backup in Thread starten
        backup_type = self.type_combo.currentData()
        self.backup_thread = threading.Thread(
            target=self._run_backup,
            args=(backup_type,),
            daemon=True,
        )
        self.backup_thread.start()

        logger.info(f"Backup gestartet: {backup_type}")

    def _run_backup(self, backup_type: str) -> None:
        """
        Führt Backup aus (läuft in separatem Thread)

        Args:
            backup_type: "full" oder "incremental"
        """
        try:
            if backup_type == "full":
                result = self.backup_engine.create_full_backup()
            else:
                result = self.backup_engine.create_incremental_backup()

            # Signal an GUI
            self.backup_completed.emit(result)

        except Exception as e:
            logger.error(f"Backup fehlgeschlagen: {e}", exc_info=True)
            self.backup_failed.emit(str(e))

    def _on_progress_update(self, progress: BackupProgress) -> None:
        """
        Callback für Progress-Updates (läuft in Backup-Thread)

        Args:
            progress: Fortschritts-Informationen
        """
        # Signal an GUI-Thread
        self.progress_updated.emit(progress)

    @pyqtSlot(object)
    def _update_progress_ui(self, progress: BackupProgress) -> None:
        """
        Aktualisiert Progress-UI (läuft in GUI-Thread)

        Args:
            progress: Fortschritts-Informationen
        """
        # Status
        phase_names = {
            "scanning": "Scanne Dateien...",
            "compressing": "Komprimiere...",
            "encrypting": "Verschlüssele...",
            "uploading": "Lade hoch...",
        }
        self.status_label.setText(phase_names.get(progress.phase, progress.phase))

        # Progress-Bar
        percentage = int(progress.progress_percentage)
        self.progress_bar.setValue(percentage)

        # Aktuelle Datei
        if progress.current_file:
            self.current_file_label.setText(f"📄 {progress.current_file}")
        else:
            self.current_file_label.setText("--")

        # Statistiken
        stats = f"{progress.files_processed}/{progress.files_total} Dateien"
        if progress.bytes_total > 0:
            mb_processed = progress.bytes_processed / (1024 * 1024)
            mb_total = progress.bytes_total / (1024 * 1024)
            stats += f" • {mb_processed:.1f}/{mb_total:.1f} MB"
        self.stats_label.setText(stats)

    @pyqtSlot(object)
    def _on_backup_completed(self, result: BackupResult) -> None:
        """
        Callback wenn Backup abgeschlossen ist

        Args:
            result: Backup-Ergebnis
        """
        self.is_backup_running = False
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

        if result.success:
            self.status_label.setText("✅ Backup erfolgreich abgeschlossen!")
            self.progress_bar.setValue(100)

            # Erfolgs-Nachricht
            mb_original = result.size_original / (1024 * 1024)
            mb_compressed = result.size_compressed / (1024 * 1024)
            duration_min = result.duration_seconds / 60

            QMessageBox.information(
                self,
                "Backup erfolgreich",
                f"Backup wurde erfolgreich abgeschlossen!\n\n"
                f"Typ: {result.backup_type}\n"
                f"Dateien: {result.files_total}\n"
                f"Größe: {mb_original:.1f} MB → {mb_compressed:.1f} MB\n"
                f"Dauer: {duration_min:.1f} Minuten",
            )

            # History aktualisieren
            self._load_history()

        else:
            self.status_label.setText("❌ Backup fehlgeschlagen")
            self.progress_bar.setValue(0)

            # Fehler-Nachricht
            errors = "\n".join(result.errors[:5])  # Erste 5 Fehler
            QMessageBox.critical(self, "Backup fehlgeschlagen", f"Fehler:\n{errors}")

    @pyqtSlot(str)
    def _on_backup_failed(self, error: str) -> None:
        """
        Callback wenn Backup fehlgeschlagen ist

        Args:
            error: Fehler-Nachricht
        """
        self.is_backup_running = False
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.status_label.setText("❌ Backup fehlgeschlagen")
        self.progress_bar.setValue(0)

        # Fehler anzeigen
        self.error_label.setText(f"Fehler: {error}")
        self.error_label.show()

        QMessageBox.critical(self, "Backup fehlgeschlagen", f"Fehler:\n{error}")

    def _on_stop_backup(self) -> None:
        """Stoppt laufendes Backup"""
        # TODO: Implement cancellation
        QMessageBox.information(
            self,
            "Stoppen",
            "Backup-Abbruch wird in einer zukünftigen Version implementiert.",
        )

    def _load_history(self) -> None:
        """Lädt Backup-History aus MetadataManager"""
        if not self.metadata_manager:
            return

        try:
            # Hole alle Backups
            backups = self.metadata_manager.list_backups(limit=50)

            # Table füllen
            self.history_table.setRowCount(len(backups))

            for row, backup in enumerate(backups):
                # Datum/Uhrzeit
                timestamp = datetime.fromisoformat(backup["timestamp"])
                date_str = timestamp.strftime("%d.%m.%Y %H:%M:%S")
                self.history_table.setItem(row, 0, QTableWidgetItem(date_str))

                # Typ
                backup_type = "📦 Full" if backup["backup_type"] == "full" else "📝 Incr"
                self.history_table.setItem(row, 1, QTableWidgetItem(backup_type))

                # Dateien
                files = str(backup.get("file_count", 0))
                self.history_table.setItem(row, 2, QTableWidgetItem(files))

                # Größe
                size_mb = backup.get("size_original", 0) / (1024 * 1024)
                size_str = f"{size_mb:.1f} MB"
                self.history_table.setItem(row, 3, QTableWidgetItem(size_str))

                # Dauer
                duration = backup.get("duration_seconds", 0)
                if duration < 60:
                    duration_str = f"{duration:.0f}s"
                else:
                    duration_str = f"{duration / 60:.1f}min"
                self.history_table.setItem(row, 4, QTableWidgetItem(duration_str))

                # Status
                status = backup.get("status", "unknown")
                status_icon = "✅" if status == "completed" else "❌"
                self.history_table.setItem(row, 5, QTableWidgetItem(f"{status_icon} {status}"))

        except Exception as e:
            logger.error(f"Fehler beim Laden der History: {e}", exc_info=True)
