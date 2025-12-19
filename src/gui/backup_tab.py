"""
Backup-Tab für Scrat-Backup
GUI für Backup-Operationen mit Progress-Tracking
"""

import logging
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import (
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QListWidget,
    QListWidgetItem,
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
from src.utils.validators import Validators

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
    progress_updated = Signal(object)  # BackupProgress
    backup_completed = Signal(object)  # BackupResult
    backup_failed = Signal(str)  # Error message

    def __init__(self, config_manager=None, parent: Optional[QWidget] = None):
        """Initialisiert Backup-Tab"""
        super().__init__(parent)

        self.event_bus = get_event_bus()
        self.config_manager = config_manager  # Für Quellen/Ziele
        self.metadata_manager: Optional[MetadataManager] = None  # Für Backup-History
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

        # Quellen-Auswahl
        sources_group = QGroupBox("📁 Quellen")
        sources_layout = QVBoxLayout()

        self.sources_list = QListWidget()
        self.sources_list.setMaximumHeight(100)
        sources_layout.addWidget(self.sources_list)

        # Reload-Button
        reload_sources_btn = QPushButton("🔄 Neu laden")
        reload_sources_btn.clicked.connect(self._load_sources)
        sources_layout.addWidget(reload_sources_btn)

        sources_group.setLayout(sources_layout)
        layout.addWidget(sources_group)

        # Ziel-Auswahl
        dest_layout = QHBoxLayout()
        dest_layout.addWidget(QLabel("💾 Ziel:"))

        self.destination_combo = QComboBox()
        dest_layout.addWidget(self.destination_combo, 1)

        # Reload-Button
        reload_dest_btn = QPushButton("🔄")
        reload_dest_btn.setMaximumWidth(40)
        reload_dest_btn.clicked.connect(self._load_destinations)
        dest_layout.addWidget(reload_dest_btn)

        layout.addLayout(dest_layout)

        # Backup-Typ-Auswahl
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("📦 Backup-Typ:"))

        self.type_combo = QComboBox()
        self.type_combo.addItem("Vollbackup (Full)", "full")
        self.type_combo.addItem("Inkrementell (Incremental)", "incremental")
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
        self._load_sources()
        self._load_destinations()
        self._load_history()

    def _load_sources(self) -> None:
        """Lädt Quellen aus ConfigManager"""
        self.sources_list.clear()

        # Lade aus ConfigManager statt MetadataManager
        if not self.config_manager:
            logger.warning("Kein ConfigManager verfügbar")
            item = QListWidgetItem("⚠ Keine Konfiguration geladen")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.sources_list.addItem(item)
            return

        sources = self.config_manager.config.get("sources", [])
        for idx, source in enumerate(sources):
            # Format: {'path': '...', 'name': '...', 'enabled': True, 'exclude_patterns': []}
            source_name = source.get("name", "Unbenannt")
            source_path = source.get("path", "")
            item = QListWidgetItem(f"{source_name} - {source_path}")
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)

            # Standardmäßig aktivierte Quellen sind gecheckt
            if source.get("enabled", True):
                item.setCheckState(Qt.CheckState.Checked)
            else:
                item.setCheckState(Qt.CheckState.Unchecked)

            item.setData(Qt.ItemDataRole.UserRole, idx)  # Index statt ID
            self.sources_list.addItem(item)

        if not sources:
            from PySide6.QtGui import QColor

            item = QListWidgetItem("Keine Quellen konfiguriert")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            item.setForeground(QColor("#999"))
            self.sources_list.addItem(item)

        logger.debug(f"Quellen geladen: {len(sources)} Einträge")

    def _load_destinations(self) -> None:
        """Lädt Ziele aus ConfigManager"""
        self.destination_combo.clear()

        if not self.config_manager:
            logger.warning("Kein ConfigManager verfügbar")
            self.destination_combo.addItem("⚠ Keine Konfiguration geladen", None)
            return

        destinations = self.config_manager.config.get("destinations", [])
        for idx, dest in enumerate(destinations):
            if dest.get("enabled", True):
                dest_name = dest.get("name", "Unbenannt")
                dest_type = dest.get("type", "unknown")
                label = f"{dest_name} ({dest_type.upper()})"
                self.destination_combo.addItem(label, idx)

        if not destinations:
            self.destination_combo.addItem("Keine Ziele konfiguriert", None)

        logger.debug(f"Ziele geladen: {len(destinations)} Einträge")

    def _on_start_backup(self) -> None:
        """Startet Backup"""
        if self.is_backup_running:
            return

        # Config aus UI auslesen
        if not self.metadata_manager:
            QMessageBox.warning(self, "Fehler", "Keine Metadaten-Datenbank konfiguriert")
            return

        # Hole ausgewählte Quellen aus UI (gecheckte Items)
        selected_sources = []
        sources = self.config_manager.config.get("sources", [])
        for i in range(self.sources_list.count()):
            item = self.sources_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                source_idx = item.data(Qt.ItemDataRole.UserRole)
                # Hole Quelle aus ConfigManager (Index, nicht ID)
                if source_idx is not None and source_idx < len(sources):
                    source = sources[source_idx]
                    selected_sources.append(Path(source["path"]))

        if not selected_sources:
            QMessageBox.warning(
                self,
                "Keine Quellen",
                "Keine Backup-Quellen ausgewählt.\n\nBitte wähle mindestens eine Quelle aus.",
            )
            return

        # Hole ausgewähltes Ziel aus UI
        dest_idx = self.destination_combo.currentData()
        if dest_idx is None:
            QMessageBox.warning(
                self,
                "Kein Ziel",
                "Kein Backup-Ziel ausgewählt.\n\nBitte wähle ein Ziel aus.",
            )
            return

        # Hole Ziel aus ConfigManager (Index, nicht ID)
        destinations = self.config_manager.config.get("destinations", [])
        if dest_idx >= len(destinations):
            QMessageBox.warning(self, "Fehler", f"Ziel mit Index {dest_idx} nicht gefunden")
            return

        destination = destinations[dest_idx]

        # Config ist bereits ein Dictionary, kein JSON-String
        dest_config = destination["config"]

        # Backup-Typ aus UI
        backup_type = self.type_combo.currentData()  # "full" oder "incremental"

        # Passwort: Frage User mit Speicher-Option
        from src.gui.password_dialog import get_password

        password, ok = get_password(
            self,
            title="Backup-Passwort",
            message="Bitte gib das Backup-Passwort ein:",
            show_save_option=True,
        )

        if not ok or not password:
            QMessageBox.warning(
                self, "Abgebrochen", "Backup abgebrochen - kein Passwort eingegeben."
            )
            return

        # Validiere Eingaben
        is_valid, error_msg = Validators.validate_paths(
            selected_sources, must_exist=True, must_be_dir=True, min_count=1
        )
        if not is_valid:
            QMessageBox.critical(
                self,
                "Validierungsfehler",
                f"Ungültige Backup-Quellen:\n\n{error_msg}\n\n"
                "Bitte überprüfe die Quellen in den Einstellungen.",
            )
            return

        is_valid, error_msg = Validators.validate_password(
            password, min_length=1, allow_empty=False
        )
        if not is_valid:
            QMessageBox.critical(
                self,
                "Validierungsfehler",
                f"Ungültiges Passwort:\n\n{error_msg}",
            )
            return

        # Validiere Ziel-Pfad
        dest_path = Path(dest_config.get("path", Path.home() / "scrat-backups"))
        is_valid, error_msg = Validators.validate_path(dest_path, must_be_writable=True)
        if not is_valid:
            QMessageBox.critical(
                self,
                "Validierungsfehler",
                f"Ungültiges Backup-Ziel:\n\n{error_msg}\n\n"
                "Bitte überprüfe das Ziel in den Einstellungen.",
            )
            return

        # Erstelle BackupConfig
        config = BackupConfig(
            sources=selected_sources,
            destination_path=Path(dest_config.get("path", Path.home() / "scrat-backups")),
            destination_type=destination["type"],
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

        # Start-Zeit für Speed/ETA-Berechnung
        self.backup_start_time = time.time()

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

    @Slot(object)
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

            # Speed und ETA berechnen
            if hasattr(self, "backup_start_time") and progress.bytes_processed > 0:
                elapsed_time = time.time() - self.backup_start_time
                if elapsed_time > 0:
                    # Speed in MB/s
                    speed_mb_s = mb_processed / elapsed_time
                    stats += f" • {speed_mb_s:.1f} MB/s"

                    # ETA berechnen
                    if speed_mb_s > 0:
                        remaining_mb = mb_total - mb_processed
                        eta_seconds = remaining_mb / speed_mb_s

                        # ETA formatieren
                        if eta_seconds < 60:
                            eta_str = f"{int(eta_seconds)}s"
                        elif eta_seconds < 3600:
                            eta_str = f"{int(eta_seconds / 60)}m {int(eta_seconds % 60)}s"
                        else:
                            hours = int(eta_seconds / 3600)
                            minutes = int((eta_seconds % 3600) / 60)
                            eta_str = f"{hours}h {minutes}m"

                        stats += f" • ETA: {eta_str}"

        self.stats_label.setText(stats)

    @Slot(object)
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

    @Slot(str)
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
