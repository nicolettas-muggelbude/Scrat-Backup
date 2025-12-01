"""
Logs-Tab für Scrat-Backup
Zeigt Log-Einträge aus der Datenbank an
"""

import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from src.core.metadata_manager import MetadataManager

logger = logging.getLogger(__name__)


class LogDetailDialog(QDialog):
    """Dialog für Log-Details"""

    def __init__(self, log_entry: dict, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.log_entry = log_entry
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Erstellt UI"""
        self.setWindowTitle("Log-Details")
        self.setMinimumSize(600, 400)

        layout = QVBoxLayout(self)

        # Info-Felder
        info_layout = QFormLayout()

        # Timestamp
        timestamp_label = QLabel(str(self.log_entry.get("timestamp", "")))
        info_layout.addRow("Zeitstempel:", timestamp_label)

        # Level
        level = self.log_entry.get("level", "")
        level_label = QLabel(self._get_level_icon(level) + " " + level)
        info_layout.addRow("Level:", level_label)

        # Backup-ID
        backup_id = self.log_entry.get("backup_id")
        backup_label = QLabel(str(backup_id) if backup_id else "-")
        info_layout.addRow("Backup-ID:", backup_label)

        layout.addLayout(info_layout)

        # Nachricht
        message_group = QGroupBox("Nachricht")
        message_layout = QVBoxLayout()
        message_text = QTextEdit()
        message_text.setPlainText(self.log_entry.get("message", ""))
        message_text.setReadOnly(True)
        message_text.setMaximumHeight(100)
        message_layout.addWidget(message_text)
        message_group.setLayout(message_layout)
        layout.addWidget(message_group)

        # Details (falls vorhanden)
        details = self.log_entry.get("details")
        if details:
            details_group = QGroupBox("Details")
            details_layout = QVBoxLayout()
            details_text = QTextEdit()
            details_text.setPlainText(details)
            details_text.setReadOnly(True)
            details_text.setStyleSheet("font-family: monospace; font-size: 10px;")
            details_layout.addWidget(details_text)
            details_group.setLayout(details_layout)
            layout.addWidget(details_group)

        # Close-Button
        close_btn = QPushButton("Schließen")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

    def _get_level_icon(self, level: str) -> str:
        """Gibt Icon für Log-Level zurück"""
        icons = {
            "DEBUG": "🔍",
            "INFO": "ℹ️",
            "WARNING": "⚠️",
            "ERROR": "❌",
            "CRITICAL": "🔥",
        }
        return icons.get(level, "")


class LogsTab(QWidget):
    """
    Logs-Tab für Hauptfenster

    Features:
    - Tabelle mit Log-Einträgen
    - Filter nach Level, Datum, Suchbegriff
    - Details-Ansicht per Doppelklick
    - Export zu Textdatei
    - Logs löschen (mit Bestätigung)
    """

    def __init__(self, metadata_manager: MetadataManager, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.metadata_manager = metadata_manager

        self._setup_ui()
        self._connect_signals()

        # Initial laden
        self._load_logs()

        # Auto-Refresh alle 10 Sekunden
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self._load_logs)
        self.refresh_timer.start(10000)  # 10 Sekunden

        logger.debug("LogsTab initialisiert")

    def _setup_ui(self) -> None:
        """Erstellt UI"""
        layout = QVBoxLayout(self)

        # Header
        header = QLabel("📋 System-Logs")
        header.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(header)

        # Filter-Bereich
        filter_group = self._create_filter_group()
        layout.addWidget(filter_group)

        # Tabelle
        self.logs_table = QTableWidget()
        self.logs_table.setColumnCount(5)
        self.logs_table.setHorizontalHeaderLabels(
            ["ID", "Zeitstempel", "Level", "Nachricht", "Backup-ID"]
        )

        # Spaltenbreiten
        header = self.logs_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # ID
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Timestamp
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Level
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)  # Message
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Backup-ID

        # Alternating row colors
        self.logs_table.setAlternatingRowColors(True)

        # Doppelklick für Details
        self.logs_table.doubleClicked.connect(self._show_log_details)

        layout.addWidget(self.logs_table)

        # Buttons
        button_layout = QHBoxLayout()

        self.refresh_btn = QPushButton("🔄 Aktualisieren")
        button_layout.addWidget(self.refresh_btn)

        self.export_btn = QPushButton("💾 Exportieren")
        button_layout.addWidget(self.export_btn)

        self.clear_btn = QPushButton("🗑️ Löschen (älter als 30 Tage)")
        button_layout.addWidget(self.clear_btn)

        button_layout.addStretch()

        # Log-Anzahl
        self.count_label = QLabel("0 Einträge")
        self.count_label.setStyleSheet("color: #666; font-size: 12px;")
        button_layout.addWidget(self.count_label)

        layout.addLayout(button_layout)

    def _create_filter_group(self) -> QGroupBox:
        """Erstellt Filter-Bereich"""
        group = QGroupBox("🔍 Filter")
        layout = QHBoxLayout()

        # Level-Filter
        level_label = QLabel("Level:")
        layout.addWidget(level_label)

        self.level_combo = QComboBox()
        self.level_combo.addItem("Alle", None)
        self.level_combo.addItem("🔍 DEBUG", "DEBUG")
        self.level_combo.addItem("ℹ️ INFO", "INFO")
        self.level_combo.addItem("⚠️ WARNING", "WARNING")
        self.level_combo.addItem("❌ ERROR", "ERROR")
        self.level_combo.addItem("🔥 CRITICAL", "CRITICAL")
        layout.addWidget(self.level_combo)

        # Datum-Filter
        date_label = QLabel("Von:")
        layout.addWidget(date_label)

        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(datetime.now().date())
        self.start_date.setDisplayFormat("dd.MM.yyyy")
        layout.addWidget(self.start_date)

        to_label = QLabel("Bis:")
        layout.addWidget(to_label)

        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(datetime.now().date())
        self.end_date.setDisplayFormat("dd.MM.yyyy")
        layout.addWidget(self.end_date)

        # Such-Feld
        search_label = QLabel("Suche:")
        layout.addWidget(search_label)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Suche in Nachricht...")
        layout.addWidget(self.search_input)

        # Filter anwenden
        self.filter_btn = QPushButton("Anwenden")
        layout.addWidget(self.filter_btn)

        # Reset
        self.reset_filter_btn = QPushButton("Zurücksetzen")
        layout.addWidget(self.reset_filter_btn)

        group.setLayout(layout)
        return group

    def _connect_signals(self) -> None:
        """Verbindet Signals"""
        self.refresh_btn.clicked.connect(self._load_logs)
        self.export_btn.clicked.connect(self._export_logs)
        self.clear_btn.clicked.connect(self._clear_old_logs)
        self.filter_btn.clicked.connect(self._load_logs)
        self.reset_filter_btn.clicked.connect(self._reset_filters)

    def _load_logs(self) -> None:
        """Lädt Logs aus Datenbank"""
        # Filter-Werte
        level = self.level_combo.currentData()
        search_term = self.search_input.text().strip() or None

        # Datum-Filter (nur wenn aktiviert)
        start_date = None
        end_date = None

        # Hole Logs
        try:
            logs = self.metadata_manager.get_logs(
                level=level,
                start_date=start_date,
                end_date=end_date,
                search_term=search_term,
                limit=1000,
            )

            # Tabelle füllen
            self.logs_table.setRowCount(len(logs))

            for row, log in enumerate(logs):
                # ID
                id_item = QTableWidgetItem(str(log["id"]))
                id_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.logs_table.setItem(row, 0, id_item)

                # Timestamp
                timestamp = log.get("timestamp", "")
                if isinstance(timestamp, str):
                    # Formatiere ISO-String
                    try:
                        dt = datetime.fromisoformat(timestamp)
                        timestamp_str = dt.strftime("%d.%m.%Y %H:%M:%S")
                    except ValueError:
                        timestamp_str = timestamp
                else:
                    timestamp_str = str(timestamp)

                timestamp_item = QTableWidgetItem(timestamp_str)
                self.logs_table.setItem(row, 1, timestamp_item)

                # Level (mit Icon)
                level_text = log.get("level", "")
                level_icon = self._get_level_icon(level_text)
                level_item = QTableWidgetItem(f"{level_icon} {level_text}")
                level_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                # Farbcodierung
                if level_text == "ERROR":
                    level_item.setBackground(Qt.GlobalColor.red)
                elif level_text == "CRITICAL":
                    level_item.setBackground(Qt.GlobalColor.darkRed)
                elif level_text == "WARNING":
                    level_item.setBackground(Qt.GlobalColor.yellow)
                elif level_text == "DEBUG":
                    level_item.setForeground(Qt.GlobalColor.gray)

                self.logs_table.setItem(row, 2, level_item)

                # Nachricht (gekürzt auf 100 Zeichen)
                message = log.get("message", "")
                if len(message) > 100:
                    message = message[:100] + "..."
                message_item = QTableWidgetItem(message)
                self.logs_table.setItem(row, 3, message_item)

                # Backup-ID
                backup_id = log.get("backup_id")
                backup_item = QTableWidgetItem(str(backup_id) if backup_id else "-")
                backup_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.logs_table.setItem(row, 4, backup_item)

                # Speichere kompletten Log in UserRole für Details
                id_item.setData(Qt.ItemDataRole.UserRole, log)

            # Anzahl aktualisieren
            self.count_label.setText(f"{len(logs)} Einträge")

            logger.debug(f"Logs geladen: {len(logs)} Einträge")

        except Exception as e:
            logger.error(f"Fehler beim Laden der Logs: {e}", exc_info=True)
            QMessageBox.critical(self, "Fehler", f"Fehler beim Laden der Logs:\n{e}")

    def _show_log_details(self) -> None:
        """Zeigt Log-Details in Dialog"""
        current_row = self.logs_table.currentRow()
        if current_row < 0:
            return

        # Hole Log-Daten aus UserRole
        id_item = self.logs_table.item(current_row, 0)
        log_entry = id_item.data(Qt.ItemDataRole.UserRole)

        if log_entry:
            dialog = LogDetailDialog(log_entry, self)
            dialog.exec()

    def _export_logs(self) -> None:
        """Exportiert Logs zu Textdatei"""
        # Datei-Dialog
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Logs exportieren",
            str(Path.home() / "scrat-backup-logs.txt"),
            "Textdateien (*.txt)",
        )

        if not file_path:
            return

        try:
            # Filter-Werte
            level = self.level_combo.currentData()
            search_term = self.search_input.text().strip() or None

            # Alle Logs holen (kein Limit)
            logs = self.metadata_manager.get_logs(
                level=level, search_term=search_term, limit=100000  # Sehr hoher Limit
            )

            # In Datei schreiben
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("=" * 80 + "\n")
                f.write("Scrat-Backup - System-Logs\n")
                f.write(f"Exportiert am: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n")
                f.write(f"Anzahl Einträge: {len(logs)}\n")
                f.write("=" * 80 + "\n\n")

                for log in logs:
                    timestamp = log.get("timestamp", "")
                    level_text = log.get("level", "")
                    message = log.get("message", "")
                    backup_id = log.get("backup_id", "")
                    details = log.get("details", "")

                    f.write(f"[{timestamp}] [{level_text}]")
                    if backup_id:
                        f.write(f" [Backup-ID: {backup_id}]")
                    f.write(f"\n{message}\n")

                    if details:
                        f.write(f"\nDetails:\n{details}\n")

                    f.write("-" * 80 + "\n\n")

            QMessageBox.information(
                self,
                "Export erfolgreich",
                f"Logs erfolgreich exportiert:\n{file_path}\n\n{len(logs)} Einträge",
            )

            logger.info(f"Logs exportiert: {file_path} ({len(logs)} Einträge)")

        except Exception as e:
            logger.error(f"Fehler beim Export: {e}", exc_info=True)
            QMessageBox.critical(self, "Fehler", f"Fehler beim Export:\n{e}")

    def _clear_old_logs(self) -> None:
        """Löscht alte Logs (älter als 30 Tage)"""
        reply = QMessageBox.question(
            self,
            "Logs löschen",
            "Möchtest du alle Logs löschen, die älter als 30 Tage sind?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                deleted_count = self.metadata_manager.clear_logs(older_than_days=30)

                QMessageBox.information(
                    self, "Logs gelöscht", f"{deleted_count} alte Logs wurden gelöscht."
                )

                # Neu laden
                self._load_logs()

                logger.info(f"Alte Logs gelöscht: {deleted_count} Einträge")

            except Exception as e:
                logger.error(f"Fehler beim Löschen: {e}", exc_info=True)
                QMessageBox.critical(self, "Fehler", f"Fehler beim Löschen:\n{e}")

    def _reset_filters(self) -> None:
        """Setzt Filter zurück"""
        self.level_combo.setCurrentIndex(0)  # "Alle"
        self.search_input.clear()
        self.start_date.setDate(datetime.now().date())
        self.end_date.setDate(datetime.now().date())
        self._load_logs()

    def _get_level_icon(self, level: str) -> str:
        """Gibt Icon für Log-Level zurück"""
        icons = {
            "DEBUG": "🔍",
            "INFO": "ℹ️",
            "WARNING": "⚠️",
            "ERROR": "❌",
            "CRITICAL": "🔥",
        }
        return icons.get(level, "")

    def cleanup(self) -> None:
        """Cleanup beim Schließen"""
        if self.refresh_timer:
            self.refresh_timer.stop()
