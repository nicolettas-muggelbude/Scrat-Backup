"""
Setup-Wizard für Erstkonfiguration
Führt Benutzer durch initiales Setup
"""

import logging
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
    QWizard,
    QWizardPage,
)

logger = logging.getLogger(__name__)


class WelcomePage(QWizardPage):
    """Willkommens-Seite"""

    def __init__(self):
        super().__init__()
        self.setTitle("Willkommen bei Scrat-Backup!")
        self.setSubTitle(
            "Dieser Assistent hilft dir, Scrat-Backup zu konfigurieren.\n"
            "Du kannst alle Einstellungen später in den Einstellungen ändern."
        )

        layout = QVBoxLayout()

        # Eichel-Icon
        icon_path = Path(__file__).parent.parent.parent / "assets" / "scrat_icon.png"
        if icon_path.exists():
            icon_label = QLabel()
            pixmap = QPixmap(str(icon_path)).scaled(
                128,
                128,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            icon_label.setPixmap(pixmap)
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(icon_label)

        # Beschreibung
        desc = QLabel(
            "<b>Scrat-Backup</b> schützt deine Daten mit verschlüsselten,\n"
            "komprimierten Backups - genau wie Scrat seine Eicheln bewacht! 🐿️"
        )
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(desc)

        layout.addStretch()
        self.setLayout(layout)


class SourcesPage(QWizardPage):
    """Seite für Backup-Quellen"""

    def __init__(self):
        super().__init__()
        self.setTitle("Was möchtest du sichern?")
        self.setSubTitle("Wähle die Ordner, die gesichert werden sollen.")

        layout = QVBoxLayout()

        # Info
        info = QLabel("Du kannst später weitere Ordner hinzufügen oder entfernen.")
        layout.addWidget(info)

        # Beispiel-Ordner mit Checkboxes
        self.home_checkbox = QCheckBox(f"Heimverzeichnis ({Path.home()})")
        self.home_checkbox.setChecked(True)
        layout.addWidget(self.home_checkbox)

        self.documents_checkbox = QCheckBox(f"Dokumente ({Path.home() / 'Documents'})")
        self.documents_checkbox.setChecked(True)
        layout.addWidget(self.documents_checkbox)

        self.pictures_checkbox = QCheckBox(f"Bilder ({Path.home() / 'Pictures'})")
        layout.addWidget(self.pictures_checkbox)

        # Benutzerdefinierter Ordner
        custom_layout = QHBoxLayout()
        custom_layout.addWidget(QLabel("Eigener Ordner:"))
        self.custom_path = QLineEdit()
        self.custom_path.setPlaceholderText("/pfad/zu/ordner")
        custom_layout.addWidget(self.custom_path)

        browse_btn = QPushButton("Durchsuchen...")
        browse_btn.clicked.connect(self._browse_source)
        custom_layout.addWidget(browse_btn)

        layout.addLayout(custom_layout)
        layout.addStretch()
        self.setLayout(layout)

        # Registriere Felder für Wizard
        self.registerField("source_home", self.home_checkbox)
        self.registerField("source_documents", self.documents_checkbox)
        self.registerField("source_pictures", self.pictures_checkbox)
        self.registerField("source_custom", self.custom_path)

    def _browse_source(self):
        """Öffnet Ordner-Auswahl-Dialog"""
        folder = QFileDialog.getExistingDirectory(self, "Ordner auswählen", str(Path.home()))
        if folder:
            self.custom_path.setText(folder)


class DestinationPage(QWizardPage):
    """Seite für Backup-Ziel"""

    def __init__(self):
        super().__init__()
        self.setTitle("Wo sollen die Backups gespeichert werden?")
        self.setSubTitle("Wähle einen Speicherort für deine Backups.")

        layout = QVBoxLayout()

        # Storage-Typ
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Speicher-Typ:"))
        self.storage_type = QComboBox()
        self.storage_type.addItems(
            ["Lokales Laufwerk / USB", "SFTP (SSH)", "Netzwerk-Freigabe (geplant)"]
        )
        self.storage_type.currentIndexChanged.connect(self._on_storage_type_changed)
        type_layout.addWidget(self.storage_type)
        layout.addLayout(type_layout)

        # Lokales Laufwerk
        self.local_widget = QWidget()
        local_layout = QHBoxLayout(self.local_widget)
        local_layout.addWidget(QLabel("Ziel-Ordner:"))
        self.local_path = QLineEdit()
        self.local_path.setPlaceholderText("/mnt/usb/backups oder D:\\Backups")
        local_layout.addWidget(self.local_path)
        browse_btn = QPushButton("Durchsuchen...")
        browse_btn.clicked.connect(self._browse_destination)
        local_layout.addWidget(browse_btn)
        layout.addWidget(self.local_widget)

        # SFTP (versteckt initial)
        self.sftp_widget = QWidget()
        sftp_layout = QVBoxLayout(self.sftp_widget)

        host_layout = QHBoxLayout()
        host_layout.addWidget(QLabel("Server:"))
        self.sftp_host = QLineEdit()
        self.sftp_host.setPlaceholderText("example.com")
        host_layout.addWidget(self.sftp_host)
        host_layout.addWidget(QLabel("Port:"))
        self.sftp_port = QSpinBox()
        self.sftp_port.setRange(1, 65535)
        self.sftp_port.setValue(22)
        host_layout.addWidget(self.sftp_port)
        sftp_layout.addLayout(host_layout)

        user_layout = QHBoxLayout()
        user_layout.addWidget(QLabel("Benutzername:"))
        self.sftp_user = QLineEdit()
        user_layout.addWidget(self.sftp_user)
        sftp_layout.addLayout(user_layout)

        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("Remote-Pfad:"))
        self.sftp_path = QLineEdit()
        self.sftp_path.setPlaceholderText("/home/user/backups")
        path_layout.addWidget(self.sftp_path)
        sftp_layout.addLayout(path_layout)

        self.sftp_widget.setVisible(False)
        layout.addWidget(self.sftp_widget)

        layout.addStretch()
        self.setLayout(layout)

        # Registriere Felder
        self.registerField("storage_type", self.storage_type, "currentText")
        self.registerField("dest_local", self.local_path)
        self.registerField("dest_sftp_host", self.sftp_host)
        self.registerField("dest_sftp_port", self.sftp_port)
        self.registerField("dest_sftp_user", self.sftp_user)
        self.registerField("dest_sftp_path", self.sftp_path)

    def _browse_destination(self):
        """Öffnet Ordner-Auswahl-Dialog"""
        folder = QFileDialog.getExistingDirectory(self, "Ziel-Ordner auswählen", str(Path.home()))
        if folder:
            self.local_path.setText(folder)

    def _on_storage_type_changed(self, index: int):
        """Handler für Storage-Typ-Änderung"""
        if index == 0:  # Lokal
            self.local_widget.setVisible(True)
            self.sftp_widget.setVisible(False)
        elif index == 1:  # SFTP
            self.local_widget.setVisible(False)
            self.sftp_widget.setVisible(True)
        else:
            self.local_widget.setVisible(False)
            self.sftp_widget.setVisible(False)


class EncryptionPage(QWizardPage):
    """Seite für Verschlüsselung"""

    def __init__(self):
        super().__init__()
        self.setTitle("Verschlüsselung einrichten")
        self.setSubTitle("Scrat-Backup verschlüsselt ALLE Backups mit AES-256-GCM.")

        layout = QVBoxLayout()

        # Info
        info = QLabel(
            "⚠️ <b>Wichtig:</b> Bewahre dein Passwort sicher auf!\n"
            "Ohne Passwort kannst du deine Backups NICHT wiederherstellen."
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        # Passwort
        pw_layout = QHBoxLayout()
        pw_layout.addWidget(QLabel("Passwort:"))
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.password.setPlaceholderText("Mindestens 8 Zeichen")
        pw_layout.addWidget(self.password)
        layout.addLayout(pw_layout)

        # Passwort wiederholen
        confirm_layout = QHBoxLayout()
        confirm_layout.addWidget(QLabel("Wiederholen:"))
        self.password_confirm = QLineEdit()
        self.password_confirm.setEchoMode(QLineEdit.EchoMode.Password)
        confirm_layout.addWidget(self.password_confirm)
        layout.addLayout(confirm_layout)

        # Passwort anzeigen
        self.show_password = QCheckBox("Passwort anzeigen")
        self.show_password.toggled.connect(self._toggle_password_visibility)
        layout.addWidget(self.show_password)

        # Stärke-Indikator (Placeholder)
        self.strength_label = QLabel("")
        layout.addWidget(self.strength_label)
        self.password.textChanged.connect(self._update_password_strength)

        layout.addStretch()
        self.setLayout(layout)

        # Registriere Felder
        self.registerField("password*", self.password)  # * = Required
        self.registerField("password_confirm", self.password_confirm)

    def _toggle_password_visibility(self, checked: bool):
        """Passwort-Sichtbarkeit umschalten"""
        mode = QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
        self.password.setEchoMode(mode)
        self.password_confirm.setEchoMode(mode)

    def _update_password_strength(self, password: str):
        """Aktualisiert Passwort-Stärke-Anzeige"""
        if len(password) == 0:
            self.strength_label.setText("")
        elif len(password) < 8:
            self.strength_label.setText("❌ Zu kurz (mindestens 8 Zeichen)")
        elif len(password) < 12:
            self.strength_label.setText("⚠️ Schwach")
        elif len(password) < 16:
            self.strength_label.setText("✅ Mittel")
        else:
            self.strength_label.setText("✅ Stark")

    def validatePage(self) -> bool:
        """Validiert Passwort-Seite"""
        password = self.password.text()
        confirm = self.password_confirm.text()

        if len(password) < 8:
            return False

        if password != confirm:
            self.strength_label.setText("❌ Passwörter stimmen nicht überein")
            return False

        return True


class SchedulePage(QWizardPage):
    """Seite für Backup-Zeitplan"""

    def __init__(self):
        super().__init__()
        self.setTitle("Automatische Backups (optional)")
        self.setSubTitle("Richte einen Zeitplan für automatische Backups ein.")

        layout = QVBoxLayout()

        # Auto-Backup aktivieren
        self.auto_backup = QCheckBox("Automatische Backups aktivieren")
        self.auto_backup.toggled.connect(self._on_auto_backup_toggled)
        layout.addWidget(self.auto_backup)

        # Optionen
        self.options_widget = QWidget()
        options_layout = QVBoxLayout(self.options_widget)

        # Intervall
        interval_layout = QHBoxLayout()
        interval_layout.addWidget(QLabel("Backup-Intervall:"))
        self.interval = QComboBox()
        self.interval.addItems(["Täglich", "Wöchentlich", "Monatlich"])
        interval_layout.addWidget(self.interval)
        options_layout.addLayout(interval_layout)

        # Retention
        retention_layout = QHBoxLayout()
        retention_layout.addWidget(QLabel("Alte Backups behalten:"))
        self.retention = QSpinBox()
        self.retention.setRange(1, 100)
        self.retention.setValue(3)
        self.retention.setSuffix(" Versionen")
        retention_layout.addWidget(self.retention)
        options_layout.addLayout(retention_layout)

        self.options_widget.setEnabled(False)
        layout.addWidget(self.options_widget)

        layout.addStretch()
        self.setLayout(layout)

        # Registriere Felder
        self.registerField("auto_backup", self.auto_backup)
        self.registerField("backup_interval", self.interval, "currentText")
        self.registerField("backup_retention", self.retention)

    def _on_auto_backup_toggled(self, checked: bool):
        """Handler für Auto-Backup-Toggle"""
        self.options_widget.setEnabled(checked)


class SummaryPage(QWizardPage):
    """Zusammenfassungs-Seite"""

    def __init__(self):
        super().__init__()
        self.setTitle("Zusammenfassung")
        self.setSubTitle("Überprüfe deine Einstellungen.")

        layout = QVBoxLayout()

        self.summary_label = QLabel()
        self.summary_label.setWordWrap(True)
        layout.addWidget(self.summary_label)

        layout.addStretch()
        self.setLayout(layout)

    def initializePage(self):
        """Wird aufgerufen wenn Seite angezeigt wird"""
        wizard = self.wizard()

        # Sammle alle Einstellungen
        summary_text = "<h3>Deine Konfiguration:</h3>"

        # Quellen
        sources = []
        if wizard.field("source_home"):
            sources.append(str(Path.home()))
        if wizard.field("source_documents"):
            sources.append(str(Path.home() / "Documents"))
        if wizard.field("source_pictures"):
            sources.append(str(Path.home() / "Pictures"))
        custom = wizard.field("source_custom")
        if custom:
            sources.append(custom)

        summary_text += (
            f"<p><b>Backup-Quellen:</b><br>{'<br>'.join(sources) if sources else 'Keine'}</p>"
        )

        # Ziel
        storage_type = wizard.field("storage_type")
        summary_text += f"<p><b>Speicher-Typ:</b> {storage_type}</p>"

        if "Lokal" in storage_type:
            dest = wizard.field("dest_local")
            summary_text += f"<p><b>Ziel-Ordner:</b> {dest}</p>"
        elif "SFTP" in storage_type:
            host = wizard.field("dest_sftp_host")
            port = wizard.field("dest_sftp_port")
            user = wizard.field("dest_sftp_user")
            path = wizard.field("dest_sftp_path")
            summary_text += f"<p><b>SFTP-Server:</b> {user}@{host}:{port}{path}</p>"

        # Auto-Backup
        if wizard.field("auto_backup"):
            interval = wizard.field("backup_interval")
            retention = wizard.field("backup_retention")
            summary_text += f"<p><b>Automatische Backups:</b> {interval}, {retention} Versionen</p>"
        else:
            summary_text += "<p><b>Automatische Backups:</b> Deaktiviert</p>"

        self.summary_label.setText(summary_text)


class SetupWizard(QWizard):
    """
    Setup-Wizard für Erstkonfiguration

    Führt Benutzer durch:
    1. Willkommen
    2. Backup-Quellen
    3. Backup-Ziel
    4. Verschlüsselung
    5. Zeitplan
    6. Zusammenfassung
    """

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)

        self.setWindowTitle("Scrat-Backup Einrichtung")
        self.setWizardStyle(QWizard.WizardStyle.ModernStyle)
        self.setOption(QWizard.WizardOption.HaveHelpButton, False)
        self.setMinimumSize(700, 500)

        # Seiten hinzufügen
        self.addPage(WelcomePage())
        self.addPage(SourcesPage())
        self.addPage(DestinationPage())
        self.addPage(EncryptionPage())
        self.addPage(SchedulePage())
        self.addPage(SummaryPage())

        logger.info("Setup-Wizard initialisiert")

    def get_config(self) -> dict:
        """
        Gibt Konfiguration aus Wizard zurück

        Returns:
            Dictionary mit allen Einstellungen
        """
        config = {
            "sources": [],
            "storage": {},
            "encryption": {},
            "schedule": {},
        }

        # Quellen
        if self.field("source_home"):
            config["sources"].append(str(Path.home()))
        if self.field("source_documents"):
            config["sources"].append(str(Path.home() / "Documents"))
        if self.field("source_pictures"):
            config["sources"].append(str(Path.home() / "Pictures"))
        custom = self.field("source_custom")
        if custom:
            config["sources"].append(custom)

        # Storage
        storage_type = self.field("storage_type")
        if "Lokal" in storage_type:
            config["storage"] = {
                "type": "usb",
                "path": self.field("dest_local"),
            }
        elif "SFTP" in storage_type:
            config["storage"] = {
                "type": "sftp",
                "host": self.field("dest_sftp_host"),
                "port": self.field("dest_sftp_port"),
                "user": self.field("dest_sftp_user"),
                "path": self.field("dest_sftp_path"),
            }

        # Verschlüsselung
        config["encryption"] = {
            "password": self.field("password"),
        }

        # Zeitplan
        config["schedule"] = {
            "enabled": self.field("auto_backup"),
            "interval": self.field("backup_interval") if self.field("auto_backup") else None,
            "retention": self.field("backup_retention") if self.field("auto_backup") else 3,
        }

        return config
