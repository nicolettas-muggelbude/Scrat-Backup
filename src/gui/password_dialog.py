"""
Passwort-Dialog für Scrat-Backup
Dialog zur Passwort-Eingabe mit Option zum Speichern
"""

import logging
import platform
from typing import Optional, Tuple

from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

from src.utils.credential_manager import get_credential_manager

logger = logging.getLogger(__name__)


class PasswordDialog(QDialog):
    """
    Dialog zur Passwort-Eingabe mit Speicher-Option

    Features:
    - Passwort-Eingabe (masked)
    - "Passwort merken"-Checkbox
    - Automatisches Laden gespeicherter Passwörter
    - Windows Credential Manager Integration
    """

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        title: str = "Passwort eingeben",
        message: str = "Bitte gib das Backup-Passwort ein:",
        show_save_option: bool = True,
    ):
        """
        Initialisiert Dialog

        Args:
            parent: Parent-Widget
            title: Dialog-Titel
            message: Nachricht über Passwort-Feld
            show_save_option: Zeige "Passwort merken"-Option
        """
        super().__init__(parent)

        self.credential_manager = get_credential_manager()
        self.show_save_option = show_save_option

        self._setup_ui(title, message)
        self._load_saved_password()

        logger.debug("PasswordDialog initialisiert")

    def _setup_ui(self, title: str, message: str) -> None:
        """Erstellt UI"""
        self.setWindowTitle(title)
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)

        # Header
        header = QLabel("🔐 " + title)
        header.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(header)

        # Form
        form = QFormLayout()

        # Info-Text
        info_label = QLabel(message)
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #666; margin-bottom: 10px;")
        layout.addWidget(info_label)

        # Passwort-Feld
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.setPlaceholderText("Backup-Passwort...")
        form.addRow("Passwort:", self.password_edit)

        layout.addLayout(form)

        # "Passwort merken"-Checkbox
        if self.show_save_option and self.credential_manager.available:
            sys_name = platform.system()
            if sys_name == "Windows":
                store_name = "Windows Credential Manager"
                store_info = (
                    "Das Passwort wird verschlüsselt im Windows Credential Manager gespeichert.\n"
                    "Nur dein Windows-Benutzer hat Zugriff darauf."
                )
            elif sys_name == "Darwin":
                store_name = "macOS Schlüsselbund"
                store_info = (
                    "Das Passwort wird verschlüsselt im macOS Schlüsselbund gespeichert.\n"
                    "Nur dein macOS-Benutzer hat Zugriff darauf."
                )
            else:
                store_name = "System-Schlüsselbund (GNOME Keyring / KWallet)"
                store_info = (
                    "Das Passwort wird verschlüsselt im System-Schlüsselbund gespeichert.\n"
                    "Nur dein Benutzer hat Zugriff darauf."
                )

            self.save_checkbox = QCheckBox(f"Passwort sicher speichern ({store_name})")
            self.save_checkbox.setStyleSheet("margin-top: 10px;")
            layout.addWidget(self.save_checkbox)

            info = QLabel(store_info)
            info.setWordWrap(True)
            info.setStyleSheet("color: #999; font-size: 10px; margin-top: 5px;")
            layout.addWidget(info)
        else:
            self.save_checkbox = None

            if self.show_save_option and not self.credential_manager.available:
                warning = QLabel(
                    "⚠️ Passwort-Speicherung nicht verfügbar (keyring nicht installiert)"
                )
                warning.setStyleSheet("color: #ff6600; font-size: 11px; margin-top: 10px;")
                layout.addWidget(warning)

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self._accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        # Focus auf Passwort-Feld
        self.password_edit.setFocus()

    def _load_saved_password(self) -> None:
        """Lädt gespeichertes Passwort wenn vorhanden"""
        if not self.credential_manager.available:
            return

        saved_password = self.credential_manager.get_password()
        if saved_password:
            self.password_edit.setText(saved_password)
            if self.save_checkbox:
                self.save_checkbox.setChecked(True)
            logger.info("Gespeichertes Passwort geladen")

    def _accept(self) -> None:
        """Validiert und akzeptiert Dialog"""
        password = self.password_edit.text()

        if not password:
            # Leeres Passwort - Warnung aber erlauben
            from PySide6.QtWidgets import QMessageBox

            reply = QMessageBox.question(
                self,
                "Leeres Passwort",
                "Möchtest du wirklich ein leeres Passwort verwenden?\n\n"
                "Dies ist unsicher und wird nicht empfohlen.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )

            if reply == QMessageBox.StandardButton.No:
                return

        # Passwort speichern wenn gewünscht
        if self.save_checkbox and self.save_checkbox.isChecked():
            success = self.credential_manager.save_password(password)
            if success:
                logger.info("Passwort wurde gespeichert")
            else:
                logger.warning("Passwort konnte nicht gespeichert werden")
        elif self.save_checkbox and not self.save_checkbox.isChecked():
            # Passwort löschen wenn Checkbox nicht gecheckt
            self.credential_manager.delete_password()

        self.accept()

    def get_password(self) -> str:
        """
        Gibt eingegebenes Passwort zurück

        Returns:
            Passwort
        """
        return self.password_edit.text()

    def get_save_password(self) -> bool:
        """
        Gibt zurück ob Passwort gespeichert werden soll

        Returns:
            True wenn Passwort gespeichert werden soll
        """
        if self.save_checkbox:
            return self.save_checkbox.isChecked()
        return False


def get_password(
    parent: Optional[QWidget] = None,
    title: str = "Passwort eingeben",
    message: str = "Bitte gib das Backup-Passwort ein:",
    show_save_option: bool = True,
) -> Tuple[Optional[str], bool]:
    """
    Zeigt Passwort-Dialog und gibt Passwort zurück

    Args:
        parent: Parent-Widget
        title: Dialog-Titel
        message: Nachricht
        show_save_option: Zeige "Passwort merken"-Option

    Returns:
        Tuple (Passwort, Dialog-akzeptiert)
    """
    dialog = PasswordDialog(parent, title, message, show_save_option)

    if dialog.exec() == QDialog.DialogCode.Accepted:
        return dialog.get_password(), True
    else:
        return None, False
