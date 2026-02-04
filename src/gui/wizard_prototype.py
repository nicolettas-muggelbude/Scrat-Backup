"""
Setup-Wizard V2 - Prototyp mit Template-System
Template-basierte Konfiguration mit Normal/Power-User Modus
"""

import logging
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
    QWizard,
    QWizardPage,
)

logger = logging.getLogger(__name__)


# ============================================================================
# NEUE SEITEN
# ============================================================================


class ModePage(QWizardPage):
    """
    Neue Startseite: Normal-Modus vs. Power-User-Modus
    """

    expert_mode_requested = Signal()

    def __init__(self):
        super().__init__()
        self.setTitle("Willkommen bei Scrat-Backup!")
        self.setSubTitle(
            "Wähle, wie du Scrat-Backup einrichten möchtest.\n"
            "Du kannst den Modus später jederzeit ändern."
        )

        layout = QVBoxLayout()

        # Eichel-Icon
        icon_path = Path(__file__).parent.parent.parent / "assets" / "scrat_icon.png"
        if icon_path.exists():
            icon_label = QLabel()
            pixmap = QPixmap(str(icon_path)).scaled(
                100,
                100,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            icon_label.setPixmap(pixmap)
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(icon_label)

        layout.addSpacing(20)

        # Überschrift
        header = QLabel("<h2>Wie möchtest du Scrat-Backup nutzen?</h2>")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)

        layout.addSpacing(20)

        # Modus-Auswahl als große Karten
        cards_layout = QHBoxLayout()
        cards_layout.addStretch()

        # === Normal-Modus Karte ===
        normal_card = self._create_mode_card(
            "🐿️ Einfacher Modus",
            "Geführte Einrichtung\nmit Vorlagen",
            "(Empfohlen für die meisten Nutzer)",
            is_recommended=True,
        )
        self.normal_radio = QRadioButton()
        self.normal_radio.setChecked(True)  # Standard
        normal_card_layout = QVBoxLayout()
        normal_card_layout.addWidget(self.normal_radio, alignment=Qt.AlignmentFlag.AlignCenter)
        normal_card_layout.addWidget(normal_card)
        cards_layout.addLayout(normal_card_layout)

        cards_layout.addSpacing(30)

        # === Power-User-Modus Karte ===
        expert_card = self._create_mode_card(
            "⚙️ Experten-Modus",
            "Volle Kontrolle\n& Anpassungen",
            "(Für fortgeschrittene Nutzer)",
            is_recommended=False,
        )
        self.expert_radio = QRadioButton()
        expert_card_layout = QVBoxLayout()
        expert_card_layout.addWidget(self.expert_radio, alignment=Qt.AlignmentFlag.AlignCenter)
        expert_card_layout.addWidget(expert_card)
        cards_layout.addLayout(expert_card_layout)

        cards_layout.addStretch()
        layout.addLayout(cards_layout)

        layout.addSpacing(20)

        # Info-Text
        info = QLabel(
            "💡 <b>Tipp:</b> Der einfache Modus bietet vorgefertigte Vorlagen für "
            "gängige Backup-Ziele (USB, OneDrive, Synology, etc.)."
        )
        info.setWordWrap(True)
        info.setStyleSheet("background-color: #e3f2fd; padding: 15px; border-radius: 5px;")
        layout.addWidget(info)

        layout.addStretch()
        self.setLayout(layout)

        # Registriere Feld für Wizard
        self.registerField("mode_normal", self.normal_radio)

    def _create_mode_card(
        self, title: str, description: str, subtitle: str, is_recommended: bool
    ) -> QWidget:
        """Erstellt eine Modus-Karte"""
        card = QFrame()
        card.setFrameShape(QFrame.Shape.StyledPanel)
        card.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 2px solid #cccccc;
                border-radius: 10px;
                padding: 20px;
            }
            QFrame:hover {
                border-color: #2196F3;
                background-color: #f5f5f5;
            }
        """)
        card.setMinimumSize(250, 200)
        card.setMaximumSize(300, 250)

        layout = QVBoxLayout(card)

        # Titel
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        layout.addSpacing(10)

        # Beschreibung
        desc_label = QLabel(description)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setStyleSheet("font-size: 14px; color: #666;")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)

        layout.addSpacing(10)

        # Untertitel
        subtitle_label = QLabel(subtitle)
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setStyleSheet("font-size: 11px; color: #999;")
        subtitle_label.setWordWrap(True)
        layout.addWidget(subtitle_label)

        # Empfohlen-Badge
        if is_recommended:
            badge = QLabel("✨ Empfohlen")
            badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            badge.setStyleSheet(
                "background-color: #4CAF50; color: white; padding: 5px; "
                "border-radius: 5px; font-size: 12px; font-weight: bold;"
            )
            layout.addWidget(badge)

        layout.addStretch()
        return card

    def validatePage(self) -> bool:
        """Prüft ob Power-User-Modus gewählt wurde"""
        if self.expert_radio.isChecked():
            # Signalisiere dem Wizard, dass MainWindow geöffnet werden soll
            self.expert_mode_requested.emit()
            return True
        return True


class TemplateDestinationPage(QWizardPage):
    """
    Neue Ziel-Seite: Template-basierte Auswahl
    """

    def __init__(self):
        super().__init__()
        self.setTitle("Wo sollen die Backups gespeichert werden?")
        self.setSubTitle("Wähle eine Vorlage für dein Backup-Ziel.")

        self.selected_template = None
        self.template_widgets = {}

        layout = QVBoxLayout()

        # Info
        info = QLabel(
            "💡 Wähle eine der Vorlagen unten. Die Einrichtung wird automatisch "
            "für dein gewähltes Ziel optimiert."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: #666; font-size: 12px; margin-bottom: 10px;")
        layout.addWidget(info)

        # === Template-Auswahl (Kategorisiert) ===
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)

        # Mock-Templates (später aus TemplateManager)
        self._create_template_category(
            scroll_layout, "📁 Lokal", [{"id": "usb", "name": "USB-Laufwerk", "icon": "💾"}]
        )

        self._create_template_category(
            scroll_layout,
            "☁️ Cloud",
            [
                {"id": "onedrive", "name": "Microsoft OneDrive", "icon": "☁️"},
                {"id": "google_drive", "name": "Google Drive", "icon": "📊"},
                {"id": "nextcloud", "name": "Nextcloud", "icon": "☁️"},
                {"id": "dropbox", "name": "Dropbox", "icon": "📦"},
            ],
        )

        self._create_template_category(
            scroll_layout,
            "🖥️ NAS",
            [
                {"id": "synology", "name": "Synology NAS", "icon": "🖴"},
                {"id": "qnap", "name": "QNAP NAS", "icon": "🖴"},
            ],
        )

        self._create_template_category(
            scroll_layout,
            "🌐 Server",
            [
                {"id": "sftp", "name": "SFTP-Server", "icon": "🔐"},
                {"id": "webdav", "name": "WebDAV", "icon": "🌐"},
            ],
        )

        scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)

        # === Dynamisches Template-Formular ===
        self.form_container = QWidget()
        self.form_layout = QVBoxLayout(self.form_container)
        self.form_container.setVisible(False)
        layout.addWidget(self.form_container)

        self.setLayout(layout)

        # Registriere Feld
        self.registerField("template_id*", self, "selected_template_id")

    def _create_template_category(self, parent_layout: QVBoxLayout, category: str, templates: list):
        """Erstellt eine Template-Kategorie"""
        # Kategorie-Header
        category_label = QLabel(f"<b>{category}</b>")
        category_label.setStyleSheet("font-size: 14px; margin-top: 10px;")
        parent_layout.addWidget(category_label)

        # Template-Grid
        grid = QGridLayout()
        grid.setSpacing(10)

        for i, template in enumerate(templates):
            btn = self._create_template_button(template)
            row = i // 3
            col = i % 3
            grid.addWidget(btn, row, col)

        parent_layout.addLayout(grid)

    def _create_template_button(self, template: dict) -> QPushButton:
        """Erstellt einen Template-Button"""
        btn = QPushButton(f"{template['icon']}\n{template['name']}")
        btn.setMinimumSize(150, 80)
        btn.setStyleSheet("""
            QPushButton {
                background-color: white;
                border: 2px solid #cccccc;
                border-radius: 8px;
                padding: 10px;
                font-size: 12px;
            }
            QPushButton:hover {
                border-color: #2196F3;
                background-color: #e3f2fd;
            }
            QPushButton:checked {
                border-color: #2196F3;
                background-color: #2196F3;
                color: white;
            }
        """)
        btn.setCheckable(True)
        btn.clicked.connect(lambda: self._on_template_selected(template, btn))
        return btn

    def _on_template_selected(self, template: dict, button: QPushButton):
        """Handler für Template-Auswahl"""
        # Deselektiere alle anderen Buttons
        for btn in self.findChildren(QPushButton):
            if btn != button and btn.isCheckable():
                btn.setChecked(False)

        button.setChecked(True)
        self.selected_template = template["id"]

        # Zeige Template-spezifisches Formular
        self._show_template_form(template)

    def _show_template_form(self, template: dict):
        """Zeigt Template-spezifisches Konfigurationsformular"""
        # Clear bisheriges Formular
        for i in reversed(range(self.form_layout.count())):
            self.form_layout.itemAt(i).widget().setParent(None)

        self.template_widgets.clear()

        # Header
        header = QLabel(f"<h3>{template['icon']} {template['name']} einrichten</h3>")
        self.form_layout.addWidget(header)

        # Mock-Formular basierend auf Template-ID
        if template["id"] == "usb":
            self._build_usb_form()
        elif template["id"] == "onedrive":
            self._build_onedrive_form()
        elif template["id"] == "synology":
            self._build_synology_form()
        elif template["id"] == "sftp":
            self._build_sftp_form()
        else:
            # Generic Form
            self._build_generic_form(template)

        self.form_container.setVisible(True)

    def _build_usb_form(self):
        """USB-spezifisches Formular"""
        # Laufwerk-Auswahl
        drive_layout = QHBoxLayout()
        drive_layout.addWidget(QLabel("USB-Laufwerk:"))
        drive_combo = QComboBox()
        drive_combo.addItems(["D:\\ (USB-Stick)", "E:\\ (Externe Festplatte)"])
        drive_layout.addWidget(drive_combo)
        refresh_btn = QPushButton("🔄")
        refresh_btn.setMaximumWidth(40)
        drive_layout.addWidget(refresh_btn)
        self.form_layout.addLayout(drive_layout)

        self.template_widgets["drive"] = drive_combo

        # Pfad
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("Unterordner:"))
        path_edit = QLineEdit("/Backups")
        path_layout.addWidget(path_edit)
        self.form_layout.addLayout(path_layout)

        self.template_widgets["path"] = path_edit

    def _build_onedrive_form(self):
        """OneDrive-spezifisches Formular"""
        # Status
        status_label = QLabel("📡 Status: Nicht angemeldet")
        status_label.setStyleSheet("color: #ff9800; font-weight: bold;")
        self.form_layout.addWidget(status_label)

        # Anmelden-Button
        login_btn = QPushButton("🔐 Mit Microsoft anmelden")
        login_btn.setStyleSheet("background-color: #0078D4; color: white; padding: 10px;")
        login_btn.clicked.connect(lambda: self._mock_oauth_login(status_label))
        self.form_layout.addWidget(login_btn)

        # rclone-Hinweis
        rclone_info = QLabel(
            "ℹ️ OneDrive benötigt rclone. " '<a href="#install">rclone automatisch installieren</a>'
        )
        rclone_info.setWordWrap(True)
        rclone_info.setStyleSheet("color: #666; font-size: 11px;")
        self.form_layout.addWidget(rclone_info)

        # Pfad
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("Ordner in OneDrive:"))
        path_edit = QLineEdit("Backups")
        path_layout.addWidget(path_edit)
        self.form_layout.addLayout(path_layout)

        self.template_widgets["path"] = path_edit

    def _build_synology_form(self):
        """Synology-spezifisches Formular"""
        # Host
        host_layout = QHBoxLayout()
        host_layout.addWidget(QLabel("Synology IP/Hostname:"))
        host_edit = QLineEdit()
        host_edit.setPlaceholderText("192.168.1.100 oder nas.local")
        host_layout.addWidget(host_edit)
        self.form_layout.addLayout(host_layout)

        self.template_widgets["host"] = host_edit

        # Freigabe (mit Scan-Funktion)
        share_layout = QHBoxLayout()
        share_layout.addWidget(QLabel("Freigabe:"))
        share_combo = QComboBox()
        share_combo.setEditable(True)
        share_combo.setPlaceholderText("backups")
        share_layout.addWidget(share_combo)
        scan_btn = QPushButton("🔍 Scannen")
        scan_btn.clicked.connect(lambda: self._mock_scan_shares(share_combo))
        share_layout.addWidget(scan_btn)
        self.form_layout.addLayout(share_layout)

        self.template_widgets["share"] = share_combo

        # Benutzer
        user_layout = QHBoxLayout()
        user_layout.addWidget(QLabel("Benutzername:"))
        user_edit = QLineEdit()
        user_layout.addWidget(user_edit)
        self.form_layout.addLayout(user_layout)

        self.template_widgets["user"] = user_edit

        # Passwort
        pw_layout = QHBoxLayout()
        pw_layout.addWidget(QLabel("Passwort:"))
        pw_edit = QLineEdit()
        pw_edit.setEchoMode(QLineEdit.EchoMode.Password)
        pw_layout.addWidget(pw_edit)
        self.form_layout.addLayout(pw_layout)

        self.template_widgets["password"] = pw_edit

        # Verbindung testen
        test_btn = QPushButton("✅ Verbindung testen")
        test_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 8px;")
        test_btn.clicked.connect(self._mock_test_connection)
        self.form_layout.addWidget(test_btn)

    def _build_sftp_form(self):
        """SFTP-spezifisches Formular"""
        # Host & Port
        host_layout = QHBoxLayout()
        host_layout.addWidget(QLabel("Server:"))
        host_edit = QLineEdit()
        host_edit.setPlaceholderText("example.com")
        host_layout.addWidget(host_edit)
        host_layout.addWidget(QLabel("Port:"))
        port_spin = QSpinBox()
        port_spin.setRange(1, 65535)
        port_spin.setValue(22)
        host_layout.addWidget(port_spin)
        self.form_layout.addLayout(host_layout)

        self.template_widgets["host"] = host_edit
        self.template_widgets["port"] = port_spin

        # Benutzer
        user_layout = QHBoxLayout()
        user_layout.addWidget(QLabel("Benutzername:"))
        user_edit = QLineEdit()
        user_layout.addWidget(user_edit)
        self.form_layout.addLayout(user_layout)

        self.template_widgets["user"] = user_edit

        # Pfad
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("Remote-Pfad:"))
        path_edit = QLineEdit("/backups")
        path_layout.addWidget(path_edit)
        self.form_layout.addLayout(path_layout)

        self.template_widgets["path"] = path_edit

    def _build_generic_form(self, template: dict):
        """Generic Formular für nicht-implementierte Templates"""
        info = QLabel(f"🚧 Konfiguration für {template['name']} kommt bald!")
        info.setStyleSheet("color: #ff9800; font-size: 14px;")
        self.form_layout.addWidget(info)

    # Mock-Funktionen für Prototyp
    def _mock_oauth_login(self, status_label: QLabel):
        """Mock OAuth-Login"""
        status_label.setText("✅ Status: Angemeldet als user@example.com")
        status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")

    def _mock_scan_shares(self, combo: QComboBox):
        """Mock Freigaben-Scan"""
        combo.clear()
        combo.addItems(["backups", "data", "homes", "media"])

    def _mock_test_connection(self):
        """Mock Verbindungstest"""
        from PySide6.QtWidgets import QMessageBox

        QMessageBox.information(
            self, "Verbindung erfolgreich", "✅ Verbindung zum Server erfolgreich hergestellt!"
        )

    # Property für Wizard-Field
    @property
    def selected_template_id(self) -> str:
        return self.selected_template or ""


class NewFinishPage(QWizardPage):
    """
    Neue Zusammenfassungs-Seite mit Tray-Start und Backup-Option
    """

    def __init__(self):
        super().__init__()
        self.setTitle("Einrichtung abgeschlossen! 🎉")
        self.setSubTitle("Scrat-Backup ist jetzt konfiguriert und bereit.")

        layout = QVBoxLayout()

        # Zusammenfassung
        self.summary_label = QLabel()
        self.summary_label.setWordWrap(True)
        layout.addWidget(self.summary_label)

        layout.addSpacing(20)

        # === NEUE Optionen ===

        # Backup jetzt starten
        backup_group = QGroupBox()
        backup_group.setStyleSheet("QGroupBox { border: 2px solid #e0e0e0; border-radius: 5px; }")
        backup_layout = QVBoxLayout(backup_group)

        self.start_backup_now = QCheckBox("🚀 Backup jetzt starten")
        self.start_backup_now.setStyleSheet("font-size: 14px; font-weight: bold;")
        backup_layout.addWidget(self.start_backup_now)

        backup_info = QLabel("   Führt sofort ein erstes vollständiges Backup durch")
        backup_info.setStyleSheet("color: #666; font-size: 11px;")
        backup_layout.addWidget(backup_info)

        layout.addWidget(backup_group)

        layout.addSpacing(10)

        # Tray starten
        tray_group = QGroupBox()
        tray_group.setStyleSheet("QGroupBox { border: 2px solid #e0e0e0; border-radius: 5px; }")
        tray_layout = QVBoxLayout(tray_group)

        self.start_tray = QCheckBox("📍 Scrat-Backup im Hintergrund starten (Tray)")
        self.start_tray.setChecked(True)  # Standardmäßig aktiviert
        self.start_tray.setStyleSheet("font-size: 14px; font-weight: bold;")
        tray_layout.addWidget(self.start_tray)

        tray_info = QLabel(
            "   Startet Scrat-Backup im System-Tray für schnellen Zugriff\n"
            "   und automatische Backups"
        )
        tray_info.setStyleSheet("color: #666; font-size: 11px;")
        tray_layout.addWidget(tray_info)

        layout.addWidget(tray_group)

        layout.addSpacing(20)

        # Erfolgs-Hinweis
        success = QLabel(
            "✅ Du kannst den Assistenten jederzeit über das Tray-Menü\n"
            "erneut öffnen, um Einstellungen zu ändern."
        )
        success.setWordWrap(True)
        success.setStyleSheet(
            "background-color: #e8f5e9; color: #2e7d32; " "padding: 15px; border-radius: 5px;"
        )
        layout.addWidget(success)

        layout.addStretch()
        self.setLayout(layout)

        # Registriere Felder
        self.registerField("start_backup_now", self.start_backup_now)
        self.registerField("start_tray", self.start_tray)

    def initializePage(self):
        """Wird aufgerufen wenn Seite angezeigt wird"""
        wizard = self.wizard()

        # Sammle alle Einstellungen für Zusammenfassung
        summary_text = "<h3>📋 Deine Konfiguration:</h3>"

        # Modus
        mode = "Einfacher Modus" if wizard.field("mode_normal") else "Experten-Modus"
        summary_text += f"<p><b>Modus:</b> {mode}</p>"

        # Template (falls Normal-Modus)
        if wizard.field("mode_normal"):
            template_id = wizard.field("template_id")
            summary_text += f"<p><b>Backup-Ziel:</b> {template_id}</p>"

        # TODO: Weitere Details (Quellen, Zeitplan, etc.)
        summary_text += (
            "<p><b>Backup-Quellen:</b> Dokumente, Bilder (Beispiel)</p>"
            "<p><b>Zeitplan:</b> Täglich, 3 Backups behalten (Beispiel)</p>"
        )

        self.summary_label.setText(summary_text)


# ============================================================================
# WIZARD V2 - PROTOTYP
# ============================================================================


class SetupWizardV2(QWizard):
    """
    Setup-Wizard V2 - Prototyp mit Template-System

    Neue Seitenfolge:
    1. ModePage - Normal/Experten-Auswahl
    2. SourcesPage - Backup-Quellen (aus alter wizard.py)
    3. TemplateDestinationPage - Template-basierte Ziel-Auswahl
    4. EncryptionPage - Verschlüsselung (aus alter wizard.py)
    5. SchedulePage - Zeitplan (aus alter wizard.py)
    6. NewFinishPage - Zusammenfassung + Tray-Start
    """

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)

        self.setWindowTitle("Scrat-Backup Einrichtung (V2 Prototyp)")
        self.setWizardStyle(QWizard.WizardStyle.ModernStyle)
        self.setOption(QWizard.WizardOption.HaveHelpButton, False)
        self.setMinimumSize(800, 600)

        # Button-Texte auf Deutsch
        self.setButtonText(QWizard.WizardButton.BackButton, "Zurück")
        self.setButtonText(QWizard.WizardButton.NextButton, "Weiter")
        self.setButtonText(QWizard.WizardButton.FinishButton, "Fertig")
        self.setButtonText(QWizard.WizardButton.CancelButton, "Abbrechen")

        # Seiten hinzufügen
        mode_page = ModePage()
        mode_page.expert_mode_requested.connect(self._open_expert_mode)
        self.addPage(mode_page)

        # TODO: SourcesPage, EncryptionPage, SchedulePage aus wizard.py importieren
        # Für Prototyp: Nur neue Seiten
        self.addPage(TemplateDestinationPage())
        self.addPage(NewFinishPage())

        logger.info("Setup-Wizard V2 (Prototyp) initialisiert")

    def _open_expert_mode(self):
        """Öffnet MainWindow für Power-User"""
        logger.info("Power-User-Modus gewählt - öffne MainWindow")

        # TODO: MainWindow importieren und öffnen
        # from gui.main_window import MainWindow
        # self.expert_window = MainWindow()
        # self.expert_window.show()

        # Für Prototyp: Nachricht anzeigen
        from PySide6.QtWidgets import QMessageBox

        QMessageBox.information(
            self,
            "Experten-Modus",
            "🛠️ Das Hauptfenster würde jetzt geöffnet werden.\n\n"
            "Du kannst weiterhin den Assistenten nutzen oder\n"
            "direkt im Hauptfenster konfigurieren.",
        )

    def accept(self):
        """Wird aufgerufen wenn Wizard abgeschlossen wird"""
        logger.info("Wizard abgeschlossen")

        # Aktionen aus FinishPage
        if self.field("start_tray"):
            self._start_tray()

        if self.field("start_backup_now"):
            self._start_initial_backup()

        super().accept()

    def _start_tray(self):
        """Startet System Tray"""
        logger.info("Starte System Tray...")
        # TODO: Tray starten
        # from gui.system_tray import SystemTray
        # self.tray = SystemTray()
        # self.tray.show()

    def _start_initial_backup(self):
        """Startet erstes Backup"""
        logger.info("Starte initiales Backup...")
        # TODO: Backup starten
        # config = self.get_config()
        # BackupEngine.start(config)

    def get_config(self) -> dict:
        """
        Gibt Konfiguration aus Wizard zurück

        Returns:
            Dictionary mit allen Einstellungen
        """
        config = {
            "mode": "normal" if self.field("mode_normal") else "expert",
            "template_id": self.field("template_id") if self.field("mode_normal") else None,
            "start_backup_now": self.field("start_backup_now"),
            "start_tray": self.field("start_tray"),
            # TODO: Weitere Felder
        }

        return config


# ============================================================================
# MAIN - Zum Testen
# ============================================================================

if __name__ == "__main__":
    import sys

    from PySide6.QtWidgets import QApplication

    logging.basicConfig(level=logging.INFO)

    app = QApplication(sys.argv)
    wizard = SetupWizardV2()
    wizard.show()

    sys.exit(app.exec())
