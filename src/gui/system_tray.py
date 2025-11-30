"""
System Tray Icon für Scrat-Backup
Ermöglicht Minimize to Tray und schnellen Zugriff auf Funktionen
"""

import logging
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import QMenu, QSystemTrayIcon

logger = logging.getLogger(__name__)


class SystemTray(QObject):
    """
    System Tray Icon mit Context-Menu

    Signals:
        show_main_window: Hauptfenster anzeigen
        start_backup: Backup starten
        start_restore: Restore starten
        show_settings: Einstellungen anzeigen
        quit_application: Anwendung beenden
    """

    # Signals
    show_main_window = pyqtSignal()
    start_backup = pyqtSignal()
    start_restore = pyqtSignal()
    show_settings = pyqtSignal()
    quit_application = pyqtSignal()

    def __init__(self, parent=None):
        """
        Initialisiert System Tray Icon

        Args:
            parent: Parent-Widget (meist QApplication)
        """
        super().__init__(parent)

        # Tray Icon erstellen
        self.tray_icon = QSystemTrayIcon(parent)

        # Icon laden (Eichel)
        icon_path = self._get_icon_path()
        if icon_path and icon_path.exists():
            self.tray_icon.setIcon(QIcon(str(icon_path)))
        else:
            # Fallback: Standard-Icon
            logger.warning(f"Tray-Icon nicht gefunden: {icon_path}")
            self.tray_icon.setIcon(QIcon.fromTheme("application-x-executable"))

        # Tooltip
        self.tray_icon.setToolTip("Scrat-Backup")

        # Context-Menu erstellen
        self.menu = self._create_menu()
        self.tray_icon.setContextMenu(self.menu)

        # Doppelklick auf Tray-Icon zeigt Hauptfenster
        self.tray_icon.activated.connect(self._on_activated)

        logger.info("System Tray Icon initialisiert")

    def _get_icon_path(self) -> Optional[Path]:
        """
        Holt Pfad zum Tray-Icon

        Returns:
            Pfad zum Icon oder None
        """
        # Suche in verschiedenen Pfaden
        possible_paths = [
            Path(__file__).parent.parent.parent / "assets" / "icons" / "scrat.ico",
            Path(__file__).parent.parent.parent / "assets" / "icons" / "scrat.png",
            Path(__file__).parent.parent.parent / "assets" / "icons" / "scrat.svg",
        ]

        for path in possible_paths:
            if path.exists():
                return path

        return None

    def _create_menu(self) -> QMenu:
        """
        Erstellt Context-Menu für Tray-Icon

        Returns:
            QMenu
        """
        menu = QMenu()

        # Hauptfenster anzeigen
        show_action = QAction("Hauptfenster anzeigen", menu)
        show_action.triggered.connect(self.show_main_window.emit)
        menu.addAction(show_action)

        menu.addSeparator()

        # Backup starten
        backup_action = QAction("Backup starten", menu)
        backup_action.triggered.connect(self.start_backup.emit)
        menu.addAction(backup_action)

        # Restore starten
        restore_action = QAction("Wiederherstellen", menu)
        restore_action.triggered.connect(self.start_restore.emit)
        menu.addAction(restore_action)

        menu.addSeparator()

        # Einstellungen
        settings_action = QAction("Einstellungen", menu)
        settings_action.triggered.connect(self.show_settings.emit)
        menu.addAction(settings_action)

        menu.addSeparator()

        # Beenden
        quit_action = QAction("Beenden", menu)
        quit_action.triggered.connect(self.quit_application.emit)
        menu.addAction(quit_action)

        return menu

    def _on_activated(self, reason):
        """
        Wird aufgerufen wenn Tray-Icon aktiviert wird

        Args:
            reason: Aktivierungs-Grund (Klick, Doppelklick, etc.)
        """
        # Doppelklick oder einfacher Klick zeigt Hauptfenster
        if reason in [
            QSystemTrayIcon.ActivationReason.DoubleClick,
            QSystemTrayIcon.ActivationReason.Trigger,
        ]:
            self.show_main_window.emit()

    def show(self):
        """Zeigt Tray-Icon an"""
        self.tray_icon.show()
        logger.info("Tray-Icon angezeigt")

    def hide(self):
        """Versteckt Tray-Icon"""
        self.tray_icon.hide()
        logger.info("Tray-Icon versteckt")

    def is_visible(self) -> bool:
        """
        Prüft ob Tray-Icon sichtbar ist

        Returns:
            True wenn sichtbar
        """
        return self.tray_icon.isVisible()

    def show_message(
        self,
        title: str,
        message: str,
        icon: QSystemTrayIcon.MessageIcon = QSystemTrayIcon.MessageIcon.Information,
        timeout: int = 5000,
    ):
        """
        Zeigt Balloon-Notification

        Args:
            title: Titel der Nachricht
            message: Nachricht
            icon: Icon-Typ (Information, Warning, Critical, NoIcon)
            timeout: Anzeigedauer in Millisekunden
        """
        if self.tray_icon.isVisible():
            self.tray_icon.showMessage(title, message, icon, timeout)
            logger.debug(f"Tray-Notification: {title} - {message}")
        else:
            logger.warning("Tray-Icon nicht sichtbar, Notification nicht angezeigt")

    def show_backup_started(self, backup_name: str = "Backup"):
        """
        Zeigt Notification dass Backup gestartet wurde

        Args:
            backup_name: Name des Backups
        """
        self.show_message(
            "Backup gestartet",
            f"{backup_name} wird durchgeführt...",
            QSystemTrayIcon.MessageIcon.Information,
        )

    def show_backup_completed(
        self, backup_name: str = "Backup", files_count: int = 0, duration: float = 0.0
    ):
        """
        Zeigt Notification dass Backup abgeschlossen wurde

        Args:
            backup_name: Name des Backups
            files_count: Anzahl gesicherter Dateien
            duration: Dauer in Sekunden
        """
        message = f"{backup_name} abgeschlossen: {files_count} Dateien in {duration:.1f}s"
        self.show_message(
            "Backup erfolgreich",
            message,
            QSystemTrayIcon.MessageIcon.Information,
        )

    def show_backup_failed(self, backup_name: str = "Backup", error: str = ""):
        """
        Zeigt Notification dass Backup fehlgeschlagen ist

        Args:
            backup_name: Name des Backups
            error: Fehlermeldung
        """
        message = f"{backup_name} fehlgeschlagen"
        if error:
            message += f": {error}"

        self.show_message(
            "Backup fehlgeschlagen",
            message,
            QSystemTrayIcon.MessageIcon.Critical,
            timeout=10000,  # Länger anzeigen bei Fehlern
        )

    def show_restore_completed(self, file_count: int = 0):
        """
        Zeigt Notification dass Restore abgeschlossen wurde

        Args:
            file_count: Anzahl wiederhergestellter Dateien
        """
        self.show_message(
            "Wiederherstellung erfolgreich",
            f"{file_count} Dateien wiederhergestellt",
            QSystemTrayIcon.MessageIcon.Information,
        )

    def show_scheduled_backup(self, scheduled_time: str):
        """
        Zeigt Notification über anstehendes geplantes Backup

        Args:
            scheduled_time: Zeitpunkt des geplanten Backups
        """
        self.show_message(
            "Geplantes Backup",
            f"Nächstes automatisches Backup: {scheduled_time}",
            QSystemTrayIcon.MessageIcon.Information,
        )

    def update_tooltip(self, status: str):
        """
        Aktualisiert Tooltip des Tray-Icons

        Args:
            status: Status-Text (z.B. "Backup läuft...")
        """
        self.tray_icon.setToolTip(f"Scrat-Backup - {status}")
