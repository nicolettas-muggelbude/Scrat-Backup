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
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QScrollArea,
    QStatusBar,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from src.core.config_manager import ConfigManager
from src.gui.backup_tab import BackupTab
from src.gui.event_bus import get_event_bus
from src.gui.restore_tab import RestoreTab
from src.gui.settings_tab import SettingsTab

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """
    Hauptfenster der Anwendung

    Features:
    - Tab-basierte Navigation (Backup, Restore, Settings, Logs, Info)
    - Statusleiste mit Event-Feedback
    - Eichel-Icon
    - Windows 11 Design
    - Info-Tab mit Copyright, Lizenz, Contributing und Kontakt
    """

    def __init__(self):
        """Initialisiert Hauptfenster"""
        super().__init__()

        self.event_bus = get_event_bus()
        self.config_manager = ConfigManager()  # Lädt/erstellt Konfiguration

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
        self._create_info_tab()

        layout.addWidget(self.tab_widget)

        logger.debug("Tabs erstellt")

    def _create_backup_tab(self) -> None:
        """Erstellt Backup-Tab"""
        self.backup_tab = BackupTab()
        self.tab_widget.addTab(self.backup_tab, "Backup")

    def _create_restore_tab(self) -> None:
        """Erstellt Restore-Tab"""
        self.restore_tab = RestoreTab()
        self.tab_widget.addTab(self.restore_tab, "Wiederherstellen")

    def _create_settings_tab(self) -> None:
        """Erstellt Settings-Tab"""
        self.settings_tab = SettingsTab()
        self.settings_tab.set_config_manager(self.config_manager)
        self.tab_widget.addTab(self.settings_tab, "Einstellungen")

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

    def _create_info_tab(self) -> None:
        """Erstellt Info-Tab mit Copyright, Lizenz, Contributing und Kontakt"""
        tab = QWidget()
        main_layout = QVBoxLayout(tab)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Scroll-Area für längere Inhalte
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        # Content-Widget
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(20)

        # Header mit Eichel-Icon
        header_layout = QHBoxLayout()
        header_layout.setSpacing(15)

        icon_path = Path(__file__).parent.parent.parent / "assets" / "scrat_icon.png"
        if icon_path.exists():
            from PyQt6.QtGui import QPixmap

            icon_label = QLabel()
            pixmap = QPixmap(str(icon_path)).scaled(
                64,
                64,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            icon_label.setPixmap(pixmap)
            header_layout.addWidget(icon_label)

        title_layout = QVBoxLayout()
        title = QLabel("Scrat-Backup")
        title.setStyleSheet("font-size: 32px; font-weight: bold;")
        title_layout.addWidget(title)

        version = QLabel("Version 0.2.0 (Beta)")
        version.setStyleSheet("font-size: 14px; color: #666;")
        title_layout.addWidget(version)

        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Beschreibung
        desc = QLabel(
            "🐿️ <i>Wie ein Eichhörnchen seine Eicheln bewahrt,<br>"
            "so bewahren wir deine Daten.</i>"
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("font-size: 14px; color: #666; margin-bottom: 20px;")
        layout.addWidget(desc)

        # Separator
        separator1 = QLabel()
        separator1.setStyleSheet("background-color: #E1E1E1; max-height: 1px;")
        layout.addWidget(separator1)

        # Copyright
        copyright_title = QLabel("📝 Copyright")
        copyright_title.setStyleSheet("font-size: 18px; font-weight: bold; margin-top: 10px;")
        layout.addWidget(copyright_title)

        copyright_text = QLabel("© 2025 Scrat-Backup Projekt<br>" "Alle Rechte vorbehalten.")
        copyright_text.setWordWrap(True)
        copyright_text.setStyleSheet("font-size: 13px; color: #333; margin-left: 10px;")
        layout.addWidget(copyright_text)

        # Lizenz
        license_title = QLabel("⚖️ Lizenz")
        license_title.setStyleSheet("font-size: 18px; font-weight: bold; margin-top: 20px;")
        layout.addWidget(license_title)

        license_text = QLabel(
            "<b>GNU General Public License v3.0 (GPLv3)</b><br><br>"
            "Dieses Programm ist freie Software. Sie können es unter den Bedingungen<br>"
            "der GNU General Public License, wie von der Free Software Foundation<br>"
            "veröffentlicht, weitergeben und/oder modifizieren, entweder gemäß Version 3<br>"
            "der Lizenz oder (nach Ihrer Option) jeder späteren Version.<br><br>"
            "Die Veröffentlichung dieses Programms erfolgt in der Hoffnung, dass es Ihnen<br>"
            "von Nutzen sein wird, aber <b>OHNE IRGENDEINE GARANTIE</b>, sogar ohne die<br>"
            "implizite Garantie der <b>MARKTREIFE</b> oder der <b>VERWENDBARKEIT FÜR EINEN<br>"
            "BESTIMMTEN ZWECK</b>. Details finden Sie in der GNU General Public License.<br><br>"
            "Vollständige Lizenz: "
            "<a href='https://www.gnu.org/licenses/gpl-3.0.html'>GNU GPLv3</a>"
        )
        license_text.setWordWrap(True)
        license_text.setOpenExternalLinks(True)
        license_text.setStyleSheet("font-size: 12px; color: #333; margin-left: 10px;")
        layout.addWidget(license_text)

        # Separator
        separator2 = QLabel()
        separator2.setStyleSheet("background-color: #E1E1E1; max-height: 1px;")
        layout.addWidget(separator2)

        # Mitmachen
        contribute_title = QLabel("🤝 Mitmachen")
        contribute_title.setStyleSheet("font-size: 18px; font-weight: bold; margin-top: 10px;")
        layout.addWidget(contribute_title)

        contribute_text = QLabel(
            "Scrat-Backup ist ein Open-Source-Projekt und freut sich über Beiträge!<br><br>"
            "<b>Wie du mitmachen kannst:</b><br>"
            "• 🐛 Bugs melden auf GitHub Issues<br>"
            "• 💡 Feature-Vorschläge einreichen<br>"
            "• 🔧 Code beitragen via Pull Requests<br>"
            "• 📖 Dokumentation verbessern<br>"
            "• 🌍 Übersetzungen hinzufügen<br><br>"
            "Alle Beiträge sind willkommen -egal ob groß oder klein!<br><br>"
            "<b>Entwickler-Dokumentation:</b><br>"
            "• CONTRIBUTING.md - Beitrags-Richtlinien<br>"
            "• docs/developer_guide.md - Entwickler-Handbuch<br>"
            "• docs/architecture.md - Architektur-Dokumentation"
        )
        contribute_text.setWordWrap(True)
        contribute_text.setStyleSheet("font-size: 13px; color: #333; margin-left: 10px;")
        layout.addWidget(contribute_text)

        # Separator
        separator3 = QLabel()
        separator3.setStyleSheet("background-color: #E1E1E1; max-height: 1px;")
        layout.addWidget(separator3)

        # Kontakt
        contact_title = QLabel("📧 Kontakt & Links")
        contact_title.setStyleSheet("font-size: 18px; font-weight: bold; margin-top: 10px;")
        layout.addWidget(contact_title)

        contact_text = QLabel(
            "<b>GitHub Repository:</b><br>"
            "<a href='https://github.com/scrat-backup/scrat-backup'>"
            "github.com/scrat-backup/scrat-backup</a><br><br>"
            "<b>Issues & Bug Reports:</b><br>"
            "<a href='https://github.com/scrat-backup/scrat-backup/issues'>"
            "GitHub Issues</a><br><br>"
            "<b>Diskussionen:</b><br>"
            "<a href='https://github.com/scrat-backup/scrat-backup/discussions'>"
            "GitHub Discussions</a><br><br>"
            "<b>Dokumentation:</b><br>"
            "<a href='https://scrat-backup.readthedocs.io'>"
            "scrat-backup.readthedocs.io</a><br><br>"
            "<b>E-Mail:</b><br>"
            "scrat-backup@example.com"
        )
        contact_text.setWordWrap(True)
        contact_text.setOpenExternalLinks(True)
        contact_text.setStyleSheet("font-size: 13px; color: #333; margin-left: 10px;")
        layout.addWidget(contact_text)

        # Separator
        separator4 = QLabel()
        separator4.setStyleSheet("background-color: #E1E1E1; max-height: 1px;")
        layout.addWidget(separator4)

        # Credits
        credits_title = QLabel("🎨 Credits")
        credits_title.setStyleSheet("font-size: 18px; font-weight: bold; margin-top: 10px;")
        layout.addWidget(credits_title)

        credits_text = QLabel(
            "Entwickelt mit:<br>"
            "• Python 3.11+ & PyQt6<br>"
            "• cryptography (AES-256-GCM Verschlüsselung)<br>"
            "• py7zr (7z Komprimierung)<br>"
            "• paramiko (SFTP Support)<br>"
            "• SQLite (Metadaten-Verwaltung)<br><br>"
            "Icon: Eichel 🌰 (Frucht der Eiche) - Symbol für Vorsorge und Bewahrung"
        )
        credits_text.setWordWrap(True)
        credits_text.setStyleSheet("font-size: 12px; color: #666; margin-left: 10px;")
        layout.addWidget(credits_text)

        layout.addStretch()

        # Scroll-Area Setup
        scroll.setWidget(content)
        main_layout.addWidget(scroll)

        self.tab_widget.addTab(tab, "Info")
        self.info_tab = tab

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
