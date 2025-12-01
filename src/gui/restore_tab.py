"""
Restore-Tab für Scrat-Backup
GUI für Wiederherstellungs-Operationen
"""

import logging
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.core.metadata_manager import MetadataManager
from src.core.restore_engine import RestoreConfig, RestoreEngine, RestoreProgress, RestoreResult
from src.gui.event_bus import get_event_bus
from src.utils.validators import Validators

logger = logging.getLogger(__name__)


class RestoreTab(QWidget):
    """
    Restore-Tab für Hauptfenster

    Features:
    - Backup-Auswahl aus History
    - Ziel-Verzeichnis-Auswahl
    - Passwort-Eingabe
    - Start/Stop-Buttons
    - Progress-Anzeige mit Details
    """

    # Signals für Thread-safe GUI-Updates
    progress_updated = pyqtSignal(object)  # RestoreProgress
    restore_completed = pyqtSignal(object)  # RestoreResult
    restore_failed = pyqtSignal(str)  # Error message

    def __init__(self, parent: Optional[QWidget] = None):
        """Initialisiert Restore-Tab"""
        super().__init__(parent)

        self.event_bus = get_event_bus()
        self.metadata_manager: Optional[MetadataManager] = None
        self.restore_engine: Optional[RestoreEngine] = None
        self.restore_thread: Optional[threading.Thread] = None
        self.is_restore_running = False
        self.selected_backup_id: Optional[int] = None

        # Setup UI
        self._setup_ui()
        self._connect_signals()

        logger.info("Restore-Tab initialisiert")

    def _setup_ui(self) -> None:
        """Erstellt UI-Komponenten"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Header
        header = QLabel("📦 Wiederherstellen")
        header.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(header)

        # Backup-Auswahl
        backup_group = self._create_backup_selection()
        layout.addWidget(backup_group, 1)  # Stretch-Faktor 1

        # Backup-Details
        details_group = self._create_details_section()
        layout.addWidget(details_group)

        # Restore-Konfiguration
        config_group = self._create_config_section()
        layout.addWidget(config_group)

        # Progress-Anzeige
        progress_group = self._create_progress_section()
        layout.addWidget(progress_group)

    def _create_backup_selection(self) -> QGroupBox:
        """Erstellt Backup-Auswahl-Bereich"""
        group = QGroupBox("Backup auswählen")
        layout = QVBoxLayout()

        # Table
        self.backup_table = QTableWidget()
        self.backup_table.setColumnCount(6)
        self.backup_table.setHorizontalHeaderLabels(
            ["Datum/Uhrzeit", "Typ", "Dateien", "Größe", "Dauer", "Status"]
        )

        # Header-Konfiguration
        header = self.backup_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)

        # Einzelne Zeile auswählbar
        self.backup_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.backup_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.backup_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)

        # Events
        self.backup_table.itemSelectionChanged.connect(self._on_backup_selected)
        self.backup_table.itemDoubleClicked.connect(self._on_backup_double_clicked)

        layout.addWidget(self.backup_table)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        refresh_button = QPushButton("🔄 Aktualisieren")
        refresh_button.clicked.connect(self._load_backups)
        button_layout.addWidget(refresh_button)

        layout.addLayout(button_layout)

        group.setLayout(layout)
        return group

    def _create_details_section(self) -> QGroupBox:
        """Erstellt Backup-Details-Bereich"""
        group = QGroupBox("Backup-Details")
        layout = QVBoxLayout()

        # Details-Label
        self.details_label = QLabel("Wähle ein Backup aus der Liste aus, um Details anzuzeigen.")
        self.details_label.setWordWrap(True)
        self.details_label.setStyleSheet("color: #666; padding: 10px;")
        layout.addWidget(self.details_label)

        group.setLayout(layout)
        group.hide()  # Initial versteckt
        return group

    def _create_config_section(self) -> QGroupBox:
        """Erstellt Konfigurations-Bereich"""
        group = QGroupBox("Wiederherstellungs-Einstellungen")
        layout = QVBoxLayout()

        # Ziel-Verzeichnis
        dest_layout = QHBoxLayout()
        dest_layout.addWidget(QLabel("Ziel-Verzeichnis:"))

        self.dest_path_edit = QLineEdit()
        self.dest_path_edit.setPlaceholderText("Wähle Ziel-Verzeichnis...")
        self.dest_path_edit.setText(str(Path.home() / "scrat-restore"))
        dest_layout.addWidget(self.dest_path_edit, 1)

        browse_button = QPushButton("📁 Durchsuchen")
        browse_button.clicked.connect(self._browse_destination)
        dest_layout.addWidget(browse_button)

        layout.addLayout(dest_layout)

        # Passwort
        pw_layout = QHBoxLayout()
        pw_layout.addWidget(QLabel("Passwort:"))

        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText("Backup-Passwort eingeben...")
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        pw_layout.addWidget(self.password_edit, 1)

        layout.addLayout(pw_layout)

        # Passwort-Speicher-Checkbox
        from src.utils.credential_manager import get_credential_manager

        self.credential_manager = get_credential_manager()
        if self.credential_manager.available:
            self.save_password_checkbox = QCheckBox("Passwort sicher speichern")
            layout.addWidget(self.save_password_checkbox)

            # Lade gespeichertes Passwort
            saved_password = self.credential_manager.get_password()
            if saved_password:
                self.password_edit.setText(saved_password)
                self.save_password_checkbox.setChecked(True)
        else:
            self.save_password_checkbox = None

        # Optionen
        self.overwrite_checkbox = QCheckBox("Existierende Dateien überschreiben")
        self.overwrite_checkbox.setChecked(False)
        layout.addWidget(self.overwrite_checkbox)

        self.restore_permissions_checkbox = QCheckBox("Datei-Berechtigungen wiederherstellen")
        self.restore_permissions_checkbox.setChecked(True)
        layout.addWidget(self.restore_permissions_checkbox)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.restore_button = QPushButton("▶ Wiederherstellen")
        self.restore_button.setEnabled(False)  # Erst aktivieren wenn Backup ausgewählt
        self.restore_button.setStyleSheet(
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
        self.restore_button.clicked.connect(self._on_start_restore)
        button_layout.addWidget(self.restore_button)

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
        self.stop_button.clicked.connect(self._on_stop_restore)
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

    def _connect_signals(self) -> None:
        """Verbindet Signals für Thread-safe Updates"""
        self.progress_updated.connect(self._update_progress_ui)
        self.restore_completed.connect(self._on_restore_completed)
        self.restore_failed.connect(self._on_restore_failed)

    def set_metadata_manager(self, metadata_manager: MetadataManager) -> None:
        """
        Setzt MetadataManager

        Args:
            metadata_manager: MetadataManager-Instanz
        """
        self.metadata_manager = metadata_manager
        self._load_backups()

    def _load_backups(self) -> None:
        """Lädt verfügbare Backups aus MetadataManager"""
        if not self.metadata_manager:
            return

        try:
            # Hole alle Backups (nur completed)
            backups = self.metadata_manager.list_backups(limit=50)
            completed_backups = [b for b in backups if b.get("status") == "completed"]

            # Sortiere nach Datum (neueste zuerst)
            completed_backups.sort(key=lambda b: b.get("timestamp", ""), reverse=True)

            # Table füllen
            self.backup_table.setRowCount(len(completed_backups))

            for row, backup in enumerate(completed_backups):
                # Speichere backup_id in erster Spalte als User-Data
                date_item = QTableWidgetItem()

                # Datum/Uhrzeit
                timestamp = datetime.fromisoformat(backup["timestamp"])
                date_str = timestamp.strftime("%d.%m.%Y %H:%M:%S")
                date_item.setText(date_str)
                date_item.setData(Qt.ItemDataRole.UserRole, backup["backup_id"])
                self.backup_table.setItem(row, 0, date_item)

                # Typ
                backup_type = "📦 Full" if backup["backup_type"] == "full" else "📝 Incr"
                self.backup_table.setItem(row, 1, QTableWidgetItem(backup_type))

                # Dateien
                files = str(backup.get("file_count", 0))
                self.backup_table.setItem(row, 2, QTableWidgetItem(files))

                # Größe
                size_mb = backup.get("size_original", 0) / (1024 * 1024)
                size_str = f"{size_mb:.1f} MB"
                self.backup_table.setItem(row, 3, QTableWidgetItem(size_str))

                # Dauer
                duration_seconds = backup.get("duration_seconds", 0)
                if duration_seconds > 0:
                    if duration_seconds < 60:
                        duration_str = f"{int(duration_seconds)}s"
                    elif duration_seconds < 3600:
                        duration_str = (
                            f"{int(duration_seconds / 60)}m {int(duration_seconds % 60)}s"
                        )
                    else:
                        hours = int(duration_seconds / 3600)
                        minutes = int((duration_seconds % 3600) / 60)
                        duration_str = f"{hours}h {minutes}m"
                else:
                    duration_str = "--"
                self.backup_table.setItem(row, 4, QTableWidgetItem(duration_str))

                # Status
                status = "✅ Bereit"
                self.backup_table.setItem(row, 5, QTableWidgetItem(status))

        except Exception as e:
            logger.error(f"Fehler beim Laden der Backups: {e}", exc_info=True)

    def _on_backup_selected(self) -> None:
        """Callback wenn Backup ausgewählt wurde"""
        selected_rows = self.backup_table.selectedItems()
        if selected_rows:
            # Hole backup_id aus erster Spalte
            first_item = self.backup_table.item(selected_rows[0].row(), 0)
            self.selected_backup_id = first_item.data(Qt.ItemDataRole.UserRole)
            self.restore_button.setEnabled(True)
            logger.debug(f"Backup ausgewählt: {self.selected_backup_id}")

            # Zeige Details
            self._show_backup_details(self.selected_backup_id)
        else:
            self.selected_backup_id = None
            self.restore_button.setEnabled(False)
            # Verstecke Details
            self.details_label.parent().hide()

    def _show_backup_details(self, backup_id: int) -> None:
        """Zeigt Details zum ausgewählten Backup"""
        if not self.metadata_manager:
            return

        try:
            # Hole Backup-Details
            backup = self.metadata_manager.get_backup(backup_id)
            if not backup:
                return

            # Formatiere Details
            timestamp = datetime.fromisoformat(backup["timestamp"])
            date_str = timestamp.strftime("%d.%m.%Y %H:%M:%S")

            backup_type = "Full Backup" if backup["backup_type"] == "full" else "Incremental Backup"
            file_count = backup.get("file_count", 0)
            size_mb = backup.get("size_original", 0) / (1024 * 1024)
            compressed_mb = backup.get("size_compressed", 0) / (1024 * 1024)
            compression_ratio = (
                (1 - backup.get("size_compressed", 0) / backup.get("size_original", 1)) * 100
                if backup.get("size_original", 0) > 0
                else 0
            )

            # Hole Quellen
            sources = backup.get("sources", "").split(";") if backup.get("sources") else []
            sources_str = "\n  • ".join(sources) if sources else "Nicht verfügbar"

            # Hole Ziel
            destination = backup.get("destination_path", "Nicht verfügbar")
            dest_type = backup.get("destination_type", "local").upper()

            # Erstelle Details-Text
            details_html = f"""
<b>Backup vom {date_str}</b><br>
<br>
<b>Typ:</b> {backup_type}<br>
<b>Dateien:</b> {file_count}<br>
<b>Größe (Original):</b> {size_mb:.1f} MB<br>
<b>Größe (Komprimiert):</b> {compressed_mb:.1f} MB ({compression_ratio:.1f}% Kompression)<br>
<br>
<b>Quellen:</b><br>
  • {sources_str}<br>
<br>
<b>Ziel:</b> {destination} ({dest_type})
"""

            self.details_label.setText(details_html)
            self.details_label.parent().show()

        except Exception as e:
            logger.error(f"Fehler beim Laden der Backup-Details: {e}", exc_info=True)

    def _on_backup_double_clicked(self, item) -> None:
        """Callback wenn Backup doppelt geklickt wurde - startet Restore"""
        if self.selected_backup_id and not self.is_restore_running:
            self._on_start_restore()

    def _browse_destination(self) -> None:
        """Öffnet Dialog für Ziel-Verzeichnis"""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Ziel-Verzeichnis wählen",
            str(Path.home()),
        )
        if directory:
            self.dest_path_edit.setText(directory)

    def _on_start_restore(self) -> None:
        """Startet Wiederherstellung"""
        if self.is_restore_running or not self.selected_backup_id:
            return

        # Validiere Passwort
        password = self.password_edit.text()
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
        dest_path = Path(self.dest_path_edit.text())
        is_valid, error_msg = Validators.validate_path(dest_path, must_be_writable=True)
        if not is_valid:
            QMessageBox.critical(
                self,
                "Validierungsfehler",
                f"Ungültiges Wiederherstellungs-Ziel:\n\n{error_msg}\n\n"
                "Bitte wähle ein anderes Verzeichnis.",
            )
            return

        # Passwort speichern wenn gewünscht
        if self.save_password_checkbox and self.save_password_checkbox.isChecked():
            self.credential_manager.save_password(password)
        elif self.save_password_checkbox and not self.save_password_checkbox.isChecked():
            # Passwort löschen wenn Checkbox nicht gecheckt
            self.credential_manager.delete_password()

        # Hole Backup-Info aus Datenbank
        if not self.metadata_manager:
            QMessageBox.warning(self, "Fehler", "Keine Metadaten-Datenbank konfiguriert")
            return

        backup_id = self.selected_backup_id
        if not backup_id:
            QMessageBox.warning(self, "Fehler", "Kein Backup ausgewählt")
            return

        backup_info = self.metadata_manager.get_backup(backup_id)
        if not backup_info:
            QMessageBox.warning(self, "Fehler", f"Backup #{backup_id} nicht gefunden")
            return

        # Storage-Backend aus Backup-Config erstellen
        try:
            from src.storage.usb_storage import USBStorage

            # Hole Destination aus Metadaten
            dest_type = backup_info.get("destination_type", "usb")

            # Für jetzt: Nur USB/Lokal unterstützt (TODO: SFTP, WebDAV, etc.)
            if dest_type != "usb":
                QMessageBox.warning(
                    self,
                    "Nicht unterstützt",
                    f"Storage-Typ '{dest_type}' wird für Wiederherstellung "
                    "noch nicht unterstützt.\n\nAktuell nur USB/Lokal verfügbar.",
                )
                return

            storage_backend = USBStorage()
            storage_config = {"path": backup_info.get("destination_path", "")}
            storage_backend.connect(storage_config)

        except Exception as e:
            logger.error(f"Fehler beim Erstellen des Storage-Backends: {e}", exc_info=True)
            QMessageBox.critical(
                self, "Fehler", f"Storage-Backend konnte nicht initialisiert werden:\n{e}"
            )
            return

        # Restore-Config erstellen
        config = RestoreConfig(
            destination_path=dest_path,
            password=password,
            overwrite_existing=self.overwrite_checkbox.isChecked(),
            restore_permissions=self.restore_permissions_checkbox.isChecked(),
        )

        # Restore-Engine erstellen
        try:
            from src.core.restore_engine import RestoreEngine

            self.restore_engine = RestoreEngine(
                metadata_manager=self.metadata_manager,
                storage_backend=storage_backend,
                config=config,
                progress_callback=self._on_progress_update,
            )

            # UI vorbereiten
            self.is_restore_running = True
            self.restore_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.status_label.setText("Starte Wiederherstellung...")
            self.progress_bar.setValue(0)
            self.error_label.hide()

            # Starte echte Wiederherstellung in Thread
            self._start_restore_thread(backup_id)

        except Exception as e:
            logger.error(f"Fehler beim Starten der Wiederherstellung: {e}", exc_info=True)
            QMessageBox.critical(self, "Fehler", f"Fehler beim Starten:\n{e}")

    def _start_restore_thread(self, backup_id: int) -> None:
        """
        Startet Wiederherstellung in eigenem Thread

        Args:
            backup_id: ID des wiederherzustellenden Backups
        """

        def run_restore():
            try:
                # Führe Wiederherstellung aus
                result = self.restore_engine.restore_full_backup(backup_id)

                # Emit completion signal
                self.restore_completed.emit(result)

            except Exception as e:
                logger.error(f"Fehler bei Wiederherstellung: {e}", exc_info=True)

                # Emit error result
                result = RestoreResult(
                    success=False,
                    files_restored=0,
                    bytes_restored=0,
                    duration_seconds=0,
                    error_message=str(e),
                )
                self.restore_completed.emit(result)

        self.restore_thread = threading.Thread(target=run_restore, daemon=True)
        self.restore_thread.start()

    def _on_progress_update(self, progress: RestoreProgress) -> None:
        """
        Callback für Progress-Updates (läuft in Restore-Thread)

        Args:
            progress: Fortschritts-Informationen
        """
        # Signal an GUI-Thread
        self.progress_updated.emit(progress)

    @pyqtSlot(object)
    def _update_progress_ui(self, progress: RestoreProgress) -> None:
        """
        Aktualisiert Progress-UI (läuft in GUI-Thread)

        Args:
            progress: Fortschritts-Informationen
        """
        # Status
        phase_names = {
            "preparing": "Vorbereite...",
            "downloading": "Lade Archive herunter...",
            "decrypting": "Entschlüssele...",
            "extracting": "Entpacke...",
            "restoring": "Stelle wieder her...",
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
    def _on_restore_completed(self, result: RestoreResult) -> None:
        """
        Callback wenn Restore abgeschlossen ist

        Args:
            result: Restore-Ergebnis
        """
        self.is_restore_running = False
        self.restore_button.setEnabled(True)
        self.stop_button.setEnabled(False)

        if result.success:
            self.status_label.setText("✅ Wiederherstellung erfolgreich!")
            self.progress_bar.setValue(100)

            # Erfolgs-Nachricht
            mb_restored = result.bytes_restored / (1024 * 1024)
            duration_min = result.duration_seconds / 60

            QMessageBox.information(
                self,
                "Wiederherstellung erfolgreich",
                f"Wiederherstellung wurde erfolgreich abgeschlossen!\n\n"
                f"Dateien: {result.files_restored}\n"
                f"Größe: {mb_restored:.1f} MB\n"
                f"Dauer: {duration_min:.1f} Minuten",
            )

        else:
            self.status_label.setText("❌ Wiederherstellung fehlgeschlagen")
            self.progress_bar.setValue(0)

            # Fehler-Nachricht
            errors = "\n".join(result.errors[:5])  # Erste 5 Fehler
            QMessageBox.critical(self, "Wiederherstellung fehlgeschlagen", f"Fehler:\n{errors}")

    @pyqtSlot(str)
    def _on_restore_failed(self, error: str) -> None:
        """
        Callback wenn Restore fehlgeschlagen ist

        Args:
            error: Fehler-Nachricht
        """
        self.is_restore_running = False
        self.restore_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.status_label.setText("❌ Wiederherstellung fehlgeschlagen")
        self.progress_bar.setValue(0)

        # Fehler anzeigen
        self.error_label.setText(f"Fehler: {error}")
        self.error_label.show()

        QMessageBox.critical(self, "Wiederherstellung fehlgeschlagen", f"Fehler:\n{error}")

    def _on_stop_restore(self) -> None:
        """Stoppt laufende Wiederherstellung"""
        # TODO: Implement cancellation
        QMessageBox.information(
            self,
            "Stoppen",
            "Wiederherstellungs-Abbruch wird in einer zukünftigen Version implementiert.",
        )
