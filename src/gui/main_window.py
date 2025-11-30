"""
Hauptfenster für Scrat-Backup
Enthält Tab-Navigation und zentrale UI-Komponenten
"""

import logging
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QLabel,
    QMainWindow,
    QMessageBox,
    QStatusBar,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from src.gui.event_bus import get_event_bus

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """
    Hauptfenster der Anwendung

    Features:
    - Tab-basierte Navigation (Backup, Restore, Settings, Logs)
    - Statusleiste mit Event-Feedback
    - Eichel-Icon
    - Windows 11 Design
    """

    def __init__(self):
        """Initialisiert Hauptfenster"""
        super().__init__()

        self.event_bus = get_event_bus()

        # Setup UI
        self._setup_window()
        self._create_tabs()
        self._create_statusbar()
        self._connect_events()

        logger.info("Hauptfenster initialisiert")

    def _setup_window(self) -> None:
        """Konfiguriert Fenster-Eigenschaften"""
        self.setWindowTitle("Scrat-Backup")
        self.setMinimumSize(1000, 700)
        self.resize(1200, 800)

        # Setze Eichel-Icon
        icon_path = Path(__file__).parent.parent.parent / "assets" / "scrat_icon.png"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
        else:
            logger.warning(f"Icon nicht gefunden: {icon_path}")

    def _create_tabs(self) -> None:
        """Erstellt Tab-Widget mit allen Haupt-Tabs"""
        # Zentrales Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Layout
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # Tab-Widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setDocumentMode(True)
        self.tab_widget.setTabPosition(QTabWidget.TabPosition.North)

        # Tabs erstellen
        self._create_backup_tab()
        self._create_restore_tab()
        self._create_settings_tab()
        self._create_logs_tab()

        layout.addWidget(self.tab_widget)

        logger.debug("Tabs erstellt")

    def _create_backup_tab(self) -> None:
        """Erstellt Backup-Tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Placeholder
        label = QLabel("🔒 Backup-Tab")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("font-size: 24px; color: #666;")
        layout.addWidget(label)

        info = QLabel("Wird in Phase 7 implementiert")
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info.setStyleSheet("font-size: 14px; color: #999;")
        layout.addWidget(info)

        self.tab_widget.addTab(tab, "Backup")
        self.backup_tab = tab

    def _create_restore_tab(self) -> None:
        """Erstellt Restore-Tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Placeholder
        label = QLabel("📦 Restore-Tab")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("font-size: 24px; color: #666;")
        layout.addWidget(label)

        info = QLabel("Wird in Phase 7 implementiert")
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info.setStyleSheet("font-size: 14px; color: #999;")
        layout.addWidget(info)

        self.tab_widget.addTab(tab, "Wiederherstellen")
        self.restore_tab = tab

    def _create_settings_tab(self) -> None:
        """Erstellt Settings-Tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Placeholder
        label = QLabel("⚙️ Einstellungen-Tab")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("font-size: 24px; color: #666;")
        layout.addWidget(label)

        info = QLabel("Wird in Phase 7 implementiert")
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info.setStyleSheet("font-size: 14px; color: #999;")
        layout.addWidget(info)

        self.tab_widget.addTab(tab, "Einstellungen")
        self.settings_tab = tab

    def _create_logs_tab(self) -> None:
        """Erstellt Logs-Tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Placeholder
        label = QLabel("📋 Logs-Tab")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("font-size: 24px; color: #666;")
        layout.addWidget(label)

        info = QLabel("Wird in Phase 7 implementiert")
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info.setStyleSheet("font-size: 14px; color: #999;")
        layout.addWidget(info)

        self.tab_widget.addTab(tab, "Logs")
        self.logs_tab = tab

    def _create_statusbar(self) -> None:
        """Erstellt Statusleiste"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # Status-Label
        self.status_label = QLabel("Bereit")
        self.status_bar.addWidget(self.status_label)

        # Permanentes Info-Label (rechts)
        self.info_label = QLabel("")
        self.status_bar.addPermanentWidget(self.info_label)

        logger.debug("Statusleiste erstellt")

    def _connect_events(self) -> None:
        """Verbindet Event-Bus-Signals mit Slots"""
        # Backup-Events
        self.event_bus.backup_progress.connect(self._on_backup_progress)
        self.event_bus.backup_completed.connect(self._on_backup_completed)
        self.event_bus.backup_failed.connect(self._on_backup_failed)

        # Restore-Events
        self.event_bus.restore_progress.connect(self._on_restore_progress)
        self.event_bus.restore_completed.connect(self._on_restore_completed)
        self.event_bus.restore_failed.connect(self._on_restore_failed)

        # System-Events
        self.event_bus.error_occurred.connect(self._on_error)
        self.event_bus.warning_occurred.connect(self._on_warning)
        self.event_bus.info_message.connect(self._on_info)

        # Storage-Events
        self.event_bus.storage_connected.connect(self._on_storage_connected)
        self.event_bus.storage_error.connect(self._on_storage_error)

        logger.debug("Event-Handlers verbunden")

    # Event-Handler (Slots)

    def _on_backup_progress(self, progress) -> None:
        """Handler für Backup-Progress"""
        if hasattr(progress, "progress_percentage"):
            percent = progress.progress_percentage
            phase = getattr(progress, "phase", "backup")
            self.status_label.setText(f"Backup läuft: {phase} - {percent:.1f}%")

    def _on_backup_completed(self, result) -> None:
        """Handler für Backup-Completion"""
        files = getattr(result, "files_backed_up", 0)
        duration = getattr(result, "duration_seconds", 0)
        self.status_label.setText(f"Backup abgeschlossen: {files} Dateien in {duration:.1f}s")
        QMessageBox.information(
            self,
            "Backup erfolgreich",
            f"Backup wurde erfolgreich abgeschlossen!\n\n"
            f"Dateien: {files}\nDauer: {duration:.1f}s",
        )

    def _on_backup_failed(self, message: str, error: Optional[Exception]) -> None:
        """Handler für Backup-Fehler"""
        self.status_label.setText(f"Backup fehlgeschlagen: {message}")
        error_text = str(error) if error else "Unbekannter Fehler"
        QMessageBox.critical(self, "Backup fehlgeschlagen", f"{message}\n\nFehler: {error_text}")

    def _on_restore_progress(self, progress) -> None:
        """Handler für Restore-Progress"""
        if hasattr(progress, "progress_percentage"):
            percent = progress.progress_percentage
            phase = getattr(progress, "phase", "restore")
            self.status_label.setText(f"Wiederherstellung: {phase} - {percent:.1f}%")

    def _on_restore_completed(self, result) -> None:
        """Handler für Restore-Completion"""
        files = getattr(result, "files_restored", 0)
        duration = getattr(result, "duration_seconds", 0)
        self.status_label.setText(f"Wiederherstellung abgeschlossen: {files} Dateien")
        QMessageBox.information(
            self,
            "Wiederherstellung erfolgreich",
            f"Wiederherstellung erfolgreich abgeschlossen!\n\n"
            f"Dateien: {files}\nDauer: {duration:.1f}s",
        )

    def _on_restore_failed(self, message: str, error: Optional[Exception]) -> None:
        """Handler für Restore-Fehler"""
        self.status_label.setText(f"Wiederherstellung fehlgeschlagen: {message}")
        error_text = str(error) if error else "Unbekannter Fehler"
        QMessageBox.critical(
            self, "Wiederherstellung fehlgeschlagen", f"{message}\n\nFehler: {error_text}"
        )

    def _on_error(self, message: str, error: Optional[Exception]) -> None:
        """Handler für Fehler"""
        self.status_label.setText(f"Fehler: {message}")
        logger.error(f"Fehler: {message}", exc_info=error)

    def _on_warning(self, message: str) -> None:
        """Handler für Warnungen"""
        self.status_label.setText(f"Warnung: {message}")
        logger.warning(message)

    def _on_info(self, message: str) -> None:
        """Handler für Infos"""
        self.status_label.setText(message)
        logger.info(message)

    def _on_storage_connected(self, storage_name: str) -> None:
        """Handler für Storage-Verbindung"""
        self.info_label.setText(f"📡 {storage_name}")
        self.status_label.setText(f"Verbunden mit {storage_name}")

    def _on_storage_error(self, message: str, error: Optional[Exception]) -> None:
        """Handler für Storage-Fehler"""
        self.status_label.setText(f"Storage-Fehler: {message}")
        logger.error(f"Storage-Fehler: {message}", exc_info=error)

    def show_welcome_wizard(self) -> bool:
        """
        Zeigt Setup-Wizard (bei erstem Start)

        Returns:
            True wenn Wizard abgeschlossen, False wenn abgebrochen
        """
        # Placeholder - wird in wizard.py implementiert
        logger.info("Wizard wird aufgerufen (TODO: Implementierung)")
        return True

    def closeEvent(self, event) -> None:
        """Handler für Fenster-Schließen"""
        # TODO: Prüfe ob laufende Operationen existieren
        # TODO: Frage Benutzer ob wirklich beenden

        logger.info("Anwendung wird beendet")
        event.accept()
