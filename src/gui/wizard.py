"""
Setup-Wizard für Erstkonfiguration
Führt Benutzer durch initiales Setup
"""

import logging
import platform
from pathlib import Path
from typing import List, Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
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

        # Version
        version_label = QLabel("<b>Version 0.1.0-dev</b>")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version_label.setStyleSheet("color: #666; font-size: 14px; margin: 10px;")
        layout.addWidget(version_label)

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

        # Persönliche Ordner (Bibliotheken)
        personal_label = QLabel("<b>Persönliche Ordner:</b>")
        layout.addWidget(personal_label)

        self.documents_checkbox = QCheckBox("📄 Dokumente")
        self.documents_checkbox.setChecked(True)
        layout.addWidget(self.documents_checkbox)

        self.pictures_checkbox = QCheckBox("🖼️ Bilder")
        layout.addWidget(self.pictures_checkbox)

        self.music_checkbox = QCheckBox("🎵 Musik")
        layout.addWidget(self.music_checkbox)

        self.videos_checkbox = QCheckBox("🎬 Videos")
        layout.addWidget(self.videos_checkbox)

        self.desktop_checkbox = QCheckBox("🖥️ Desktop")
        layout.addWidget(self.desktop_checkbox)

        self.downloads_checkbox = QCheckBox("📥 Downloads")
        layout.addWidget(self.downloads_checkbox)

        layout.addSpacing(15)

        # Weitere Ordner
        custom_label = QLabel("<b>Weitere Ordner:</b>")
        layout.addWidget(custom_label)

        custom_layout = QHBoxLayout()
        self.custom_path = QLineEdit()
        self.custom_path.setPlaceholderText("Ordner-Pfad eingeben oder durchsuchen...")
        custom_layout.addWidget(self.custom_path)

        browse_btn = QPushButton("📁 Durchsuchen...")
        browse_btn.clicked.connect(self._browse_source)
        custom_layout.addWidget(browse_btn)

        layout.addLayout(custom_layout)
        layout.addStretch()
        self.setLayout(layout)

        # Registriere Felder für Wizard
        self.registerField("source_documents", self.documents_checkbox)
        self.registerField("source_pictures", self.pictures_checkbox)
        self.registerField("source_music", self.music_checkbox)
        self.registerField("source_videos", self.videos_checkbox)
        self.registerField("source_desktop", self.desktop_checkbox)
        self.registerField("source_downloads", self.downloads_checkbox)
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

        # Speicher-Ziel
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Speicher-Ziel:"))
        self.storage_type = QComboBox()
        self.storage_type.addItems(
            [
                "Lokales Laufwerk / USB",
                "SFTP (SSH)",
                "WebDAV (Nextcloud, ownCloud)",
                "Rclone (40+ Cloud-Provider)",
                "Netzwerk-Freigabe (geplant)",
            ]
        )
        self.storage_type.currentIndexChanged.connect(self._on_storage_type_changed)
        type_layout.addWidget(self.storage_type)
        layout.addLayout(type_layout)

        # === Lokales Laufwerk ===
        self.local_widget = QWidget()
        local_layout = QVBoxLayout(self.local_widget)

        # Erkannte Laufwerke
        drives = self._detect_drives()
        if drives:
            drives_label = QLabel("<b>Erkannte Laufwerke:</b>")
            local_layout.addWidget(drives_label)

            self.drives_list = QListWidget()
            self.drives_list.setMaximumHeight(100)
            for drive_path, drive_label in drives:
                item = QListWidgetItem(f"{drive_label} ({drive_path})")
                item.setData(Qt.ItemDataRole.UserRole, drive_path)
                self.drives_list.addItem(item)
            self.drives_list.itemClicked.connect(self._on_drive_selected)
            local_layout.addWidget(self.drives_list)

            local_layout.addSpacing(10)

        # Manueller Pfad
        manual_label = QLabel("<b>Oder manuell eingeben:</b>")
        local_layout.addWidget(manual_label)

        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("Ziel-Ordner:"))
        self.local_path = QLineEdit()
        self.local_path.setPlaceholderText("D:\\Backups")
        path_layout.addWidget(self.local_path)
        browse_btn = QPushButton("📁 Durchsuchen...")
        browse_btn.clicked.connect(self._browse_destination)
        path_layout.addWidget(browse_btn)
        local_layout.addLayout(path_layout)

        layout.addWidget(self.local_widget)

        # === SFTP (versteckt initial) ===
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
        self.sftp_path.setPlaceholderText("/backups")
        path_layout.addWidget(self.sftp_path)
        sftp_layout.addLayout(path_layout)

        self.sftp_widget.setVisible(False)
        layout.addWidget(self.sftp_widget)

        # === WebDAV (versteckt initial) ===
        self.webdav_widget = QWidget()
        webdav_layout = QVBoxLayout(self.webdav_widget)

        url_layout = QHBoxLayout()
        url_layout.addWidget(QLabel("WebDAV-URL:"))
        self.webdav_url = QLineEdit()
        self.webdav_url.setPlaceholderText("https://cloud.example.com/remote.php/dav/files/user/")
        url_layout.addWidget(self.webdav_url)
        webdav_layout.addLayout(url_layout)

        user_layout = QHBoxLayout()
        user_layout.addWidget(QLabel("Benutzername:"))
        self.webdav_user = QLineEdit()
        user_layout.addWidget(self.webdav_user)
        webdav_layout.addLayout(user_layout)

        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("Remote-Pfad:"))
        self.webdav_path = QLineEdit()
        self.webdav_path.setPlaceholderText("Backups")
        path_layout.addWidget(self.webdav_path)
        webdav_layout.addLayout(path_layout)

        self.webdav_widget.setVisible(False)
        layout.addWidget(self.webdav_widget)

        # === Rclone (versteckt initial) ===
        self.rclone_widget = QWidget()
        rclone_layout = QVBoxLayout(self.rclone_widget)

        # Info
        rclone_info = QLabel(
            "⚠️ <b>Hinweis:</b> Rclone muss installiert und konfiguriert sein.\n"
            "Verwende <code>rclone config</code> um ein Remote zu erstellen."
        )
        rclone_info.setWordWrap(True)
        rclone_info.setStyleSheet("background-color: #fff3cd; padding: 10px; border-radius: 5px;")
        rclone_layout.addWidget(rclone_info)

        remote_layout = QHBoxLayout()
        remote_layout.addWidget(QLabel("Remote-Name:"))
        self.rclone_remote = QLineEdit()
        self.rclone_remote.setPlaceholderText("mycloud")
        remote_layout.addWidget(self.rclone_remote)
        rclone_layout.addLayout(remote_layout)

        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("Remote-Pfad:"))
        self.rclone_path = QLineEdit()
        self.rclone_path.setPlaceholderText("Backups")
        path_layout.addWidget(self.rclone_path)
        rclone_layout.addLayout(path_layout)

        self.rclone_widget.setVisible(False)
        layout.addWidget(self.rclone_widget)

        layout.addStretch()
        self.setLayout(layout)

        # Registriere Felder
        self.registerField("storage_type", self.storage_type, "currentText")
        self.registerField("dest_local", self.local_path)
        self.registerField("dest_sftp_host", self.sftp_host)
        self.registerField("dest_sftp_port", self.sftp_port)
        self.registerField("dest_sftp_user", self.sftp_user)
        self.registerField("dest_sftp_path", self.sftp_path)
        self.registerField("dest_webdav_url", self.webdav_url)
        self.registerField("dest_webdav_user", self.webdav_user)
        self.registerField("dest_webdav_path", self.webdav_path)
        self.registerField("dest_rclone_remote", self.rclone_remote)
        self.registerField("dest_rclone_path", self.rclone_path)

    def _detect_drives(self) -> List[tuple]:
        """
        Erkennt verfügbare Laufwerke

        Returns:
            Liste von (Pfad, Label) Tupeln
        """
        drives = []

        if platform.system() == "Windows":
            # Windows: Laufwerksbuchstaben A-Z
            import string

            for letter in string.ascii_uppercase:
                drive_path = f"{letter}:\\"
                if Path(drive_path).exists():
                    # Versuche Typ zu erkennen
                    try:
                        import ctypes

                        drive_type = ctypes.windll.kernel32.GetDriveTypeW(drive_path)
                        # 2 = Removable, 3 = Fixed, 4 = Network, 5 = CD-ROM
                        if drive_type == 2:
                            label = f"💾 {letter}: (USB/Wechseldatenträger)"
                        elif drive_type == 3:
                            label = f"🖴 {letter}: (Festplatte)"
                        elif drive_type == 4:
                            label = f"🌐 {letter}: (Netzlaufwerk)"
                        else:
                            label = f"{letter}:"
                        drives.append((drive_path, label))
                    except Exception:
                        drives.append((drive_path, f"{letter}:"))
        else:
            # Linux/Unix: /media und /mnt
            media_path = Path("/media")
            if media_path.exists():
                for drive in media_path.iterdir():
                    if drive.is_dir():
                        drives.append((str(drive), f"💾 {drive.name}"))

            mnt_path = Path("/mnt")
            if mnt_path.exists():
                for drive in mnt_path.iterdir():
                    if drive.is_dir() and drive.name not in ["wsl", "wslg"]:
                        drives.append((str(drive), f"💾 {drive.name}"))

        return drives

    def _on_drive_selected(self, item: QListWidgetItem):
        """Handler für Laufwerk-Auswahl"""
        drive_path = item.data(Qt.ItemDataRole.UserRole)
        # Füge /Backups Unterordner hinzu
        backup_path = str(Path(drive_path) / "Backups")
        self.local_path.setText(backup_path)

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
            self.webdav_widget.setVisible(False)
            self.rclone_widget.setVisible(False)
        elif index == 1:  # SFTP
            self.local_widget.setVisible(False)
            self.sftp_widget.setVisible(True)
            self.webdav_widget.setVisible(False)
            self.rclone_widget.setVisible(False)
        elif index == 2:  # WebDAV
            self.local_widget.setVisible(False)
            self.sftp_widget.setVisible(False)
            self.webdav_widget.setVisible(True)
            self.rclone_widget.setVisible(False)
        elif index == 3:  # Rclone
            self.local_widget.setVisible(False)
            self.sftp_widget.setVisible(False)
            self.webdav_widget.setVisible(False)
            self.rclone_widget.setVisible(True)
        else:  # Netzwerk-Freigabe (geplant)
            self.local_widget.setVisible(False)
            self.sftp_widget.setVisible(False)
            self.webdav_widget.setVisible(False)
            self.rclone_widget.setVisible(False)


class EncryptionPage(QWizardPage):
    """Seite für Verschlüsselung"""

    def __init__(self):
        super().__init__()
        self.setTitle("Verschlüsselung einrichten")
        self.setSubTitle("Scrat-Backup verschlüsselt ALLE Backups.")

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

    def initializePage(self):
        """Wird aufgerufen wenn Seite angezeigt wird - stellt Passwort wieder her"""
        wizard = self.wizard()
        # Stelle Passwörter wieder her (wenn vorhanden)
        saved_password = wizard.field("password")
        if saved_password:
            self.password.setText(saved_password)
            self.password_confirm.setText(saved_password)

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

        # Retention (Aufbewahrung)
        retention_label = QLabel("<b>Wie viele alte Backups behalten?</b>")
        options_layout.addWidget(retention_label)

        retention_help = QLabel(
            "Legt fest, wie viele Backup-Versionen gespeichert bleiben.\n"
            "Ältere Backups werden automatisch gelöscht."
        )
        retention_help.setStyleSheet("color: #666; font-size: 11px;")
        retention_help.setWordWrap(True)
        options_layout.addWidget(retention_help)

        retention_layout = QHBoxLayout()
        retention_layout.addWidget(QLabel("Anzahl Versionen:"))
        self.retention = QSpinBox()
        self.retention.setRange(1, 100)
        self.retention.setValue(3)
        self.retention.setSuffix(" Backups")
        retention_layout.addWidget(self.retention)
        retention_layout.addStretch()

        # Empfehlung
        retention_rec = QLabel("💡 Empfohlen: 3-7 Backups")
        retention_rec.setStyleSheet("color: #0066cc; font-size: 11px;")
        retention_layout.addWidget(retention_rec)

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
        if wizard.field("source_documents"):
            sources.append("📄 Dokumente")
        if wizard.field("source_pictures"):
            sources.append("🖼️ Bilder")
        if wizard.field("source_music"):
            sources.append("🎵 Musik")
        if wizard.field("source_videos"):
            sources.append("🎬 Videos")
        if wizard.field("source_desktop"):
            sources.append("🖥️ Desktop")
        if wizard.field("source_downloads"):
            sources.append("📥 Downloads")
        custom = wizard.field("source_custom")
        if custom:
            sources.append(f"📁 {custom}")

        sources_list = "<br>  • ".join(sources) if sources else "Keine"
        summary_text += f"<p><b>Backup-Quellen:</b><br>  • {sources_list}</p>"

        # Ziel
        storage_type = wizard.field("storage_type")
        summary_text += f"<p><b>Speicher-Ziel:</b> {storage_type}</p>"

        if "Lokal" in storage_type:
            dest = wizard.field("dest_local")
            summary_text += f"<p><b>Ziel-Ordner:</b> {dest}</p>"
        elif "SFTP" in storage_type:
            host = wizard.field("dest_sftp_host")
            port = wizard.field("dest_sftp_port")
            user = wizard.field("dest_sftp_user")
            path = wizard.field("dest_sftp_path")
            summary_text += f"<p><b>SFTP-Server:</b> {user}@{host}:{port}{path}</p>"
        elif "WebDAV" in storage_type:
            url = wizard.field("dest_webdav_url")
            user = wizard.field("dest_webdav_user")
            path = wizard.field("dest_webdav_path")
            summary_text += (
                f"<p><b>WebDAV-Server:</b> {url}<br>"
                f"<b>Benutzer:</b> {user}<br><b>Pfad:</b> {path}</p>"
            )
        elif "Rclone" in storage_type:
            remote = wizard.field("dest_rclone_remote")
            path = wizard.field("dest_rclone_path")
            summary_text += f"<p><b>Rclone-Remote:</b> {remote}<br>" f"<b>Pfad:</b> {path}</p>"

        # Auto-Backup
        if wizard.field("auto_backup"):
            interval = wizard.field("backup_interval")
            retention = wizard.field("backup_retention")
            summary_text += (
                f"<p><b>Automatische Backups:</b> {interval}, {retention} Backups behalten</p>"
            )
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

        # Button-Texte auf Deutsch
        self.setButtonText(QWizard.WizardButton.BackButton, "Zurück")
        self.setButtonText(QWizard.WizardButton.NextButton, "Weiter")
        self.setButtonText(QWizard.WizardButton.FinishButton, "Fertig")
        self.setButtonText(QWizard.WizardButton.CancelButton, "Abbrechen")

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

        # Quellen - Persönliche Ordner
        if self.field("source_documents"):
            config["sources"].append(str(Path.home() / "Documents"))
        if self.field("source_pictures"):
            config["sources"].append(str(Path.home() / "Pictures"))
        if self.field("source_music"):
            config["sources"].append(str(Path.home() / "Music"))
        if self.field("source_videos"):
            config["sources"].append(str(Path.home() / "Videos"))
        if self.field("source_desktop"):
            config["sources"].append(str(Path.home() / "Desktop"))
        if self.field("source_downloads"):
            config["sources"].append(str(Path.home() / "Downloads"))

        # Weitere Ordner
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
        elif "WebDAV" in storage_type:
            config["storage"] = {
                "type": "webdav",
                "url": self.field("dest_webdav_url"),
                "user": self.field("dest_webdav_user"),
                "path": self.field("dest_webdav_path"),
            }
        elif "Rclone" in storage_type:
            config["storage"] = {
                "type": "rclone",
                "remote": self.field("dest_rclone_remote"),
                "path": self.field("dest_rclone_path"),
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
