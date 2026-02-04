"""
Dynamic Template Form Generator
Generiert automatisch UI-Formulare aus Template-Definitionen
"""

import logging
import re
from typing import Any, Dict, List, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core.template_manager import Template

logger = logging.getLogger(__name__)


class DynamicTemplateForm(QWidget):
    """
    Dynamisches Formular basierend auf Template ui_fields

    Features:
    - Unterstützt verschiedene Feldtypen (text, password, combo, button, status)
    - Validierung (required, regex)
    - Handler-Integration (Actions wie scan_shares, test_connection)
    - Dynamische Optionen (z.B. gescannte Freigaben)
    - Conditions (zeige/verstecke Felder basierend auf State)
    """

    # Signals
    config_changed = Signal(dict)  # Wird gefeuert wenn Config sich ändert
    action_requested = Signal(str, dict)  # (action_name, current_values)

    def __init__(
        self, template: Template, handler: Optional[Any] = None, parent: Optional[QWidget] = None
    ):
        super().__init__(parent)

        self.template = template
        self.handler = handler
        self.fields: Dict[str, QWidget] = {}  # name -> widget
        self.field_configs: Dict[str, dict] = {}  # name -> field_config

        self._init_ui()
        self._build_form()

    def _init_ui(self):
        """Initialisiert Layout"""
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        # Formular-Layout
        self.form_layout = QFormLayout()
        self.form_layout.setLabelAlignment(Qt.AlignRight)
        self.form_layout.setVerticalSpacing(12)
        self.layout.addLayout(self.form_layout)

    def _build_form(self):
        """Baut Formular aus ui_fields"""
        if not self.template.ui_fields:
            logger.warning(f"Template {self.template.id} hat keine ui_fields")
            return

        for field_config in self.template.ui_fields:
            field_type = field_config.get("type")
            field_name = field_config.get("name")

            if not field_name:
                logger.warning(f"Feld ohne Namen übersprungen: {field_config}")
                continue

            # Speichere Config
            self.field_configs[field_name] = field_config

            # Erstelle Feld basierend auf Typ
            if field_type == "text":
                self._add_text_field(field_config)
            elif field_type == "password":
                self._add_password_field(field_config)
            elif field_type == "combo":
                self._add_combo_field(field_config)
            elif field_type == "drive_selector":
                self._add_drive_selector_field(field_config)
            elif field_type == "checkbox":
                self._add_checkbox_field(field_config)
            elif field_type == "button":
                self._add_button_field(field_config)
            elif field_type == "status":
                self._add_status_field(field_config)
            else:
                logger.warning(f"Unbekannter Feldtyp: {field_type}")

    # ========================================================================
    # Feld-Ersteller
    # ========================================================================

    def _add_text_field(self, config: dict):
        """Fügt Text-Eingabefeld hinzu"""
        name = config["name"]
        label = config.get("label", name)
        required = config.get("required", False)
        placeholder = config.get("placeholder", "")
        default = config.get("default", "")
        help_text = config.get("help", "")

        # Label mit Pflichtfeld-Marker
        label_text = f"{label} *" if required else label

        # Eingabefeld
        line_edit = QLineEdit()
        line_edit.setPlaceholderText(placeholder)
        if default:
            line_edit.setText(default)

        # Tooltip
        if help_text:
            line_edit.setToolTip(help_text)

        # Bei Änderung -> Signal
        line_edit.textChanged.connect(self._on_field_changed)

        self.fields[name] = line_edit
        self.form_layout.addRow(label_text, line_edit)

    def _add_password_field(self, config: dict):
        """Fügt Passwort-Feld hinzu"""
        name = config["name"]
        label = config.get("label", name)
        required = config.get("required", False)
        help_text = config.get("help", "")

        label_text = f"{label} *" if required else label

        line_edit = QLineEdit()
        line_edit.setEchoMode(QLineEdit.EchoMode.Password)

        if help_text:
            line_edit.setToolTip(help_text)

        line_edit.textChanged.connect(self._on_field_changed)

        self.fields[name] = line_edit
        self.form_layout.addRow(label_text, line_edit)

    def _add_combo_field(self, config: dict):
        """Fügt ComboBox hinzu"""
        name = config["name"]
        label = config.get("label", name)
        required = config.get("required", False)
        editable = config.get("editable", False)
        placeholder = config.get("placeholder", "")
        help_text = config.get("help", "")

        label_text = f"{label} *" if required else label

        combo = QComboBox()
        combo.setEditable(editable)

        if editable and placeholder:
            combo.setCurrentText(placeholder)

        if help_text:
            combo.setToolTip(help_text)

        combo.currentTextChanged.connect(self._on_field_changed)

        self.fields[name] = combo
        self.form_layout.addRow(label_text, combo)

    def _add_drive_selector_field(self, config: dict):
        """Fügt USB-Laufwerk-Auswahl hinzu"""
        name = config["name"]
        label = config.get("label", name)
        required = config.get("required", False)
        auto_refresh = config.get("auto_refresh", True)
        help_text = config.get("help", "")

        label_text = f"{label} *" if required else label

        # Layout für ComboBox + Refresh-Button
        layout = QHBoxLayout()

        # ComboBox
        combo = QComboBox()
        combo.setMinimumWidth(300)

        if help_text:
            combo.setToolTip(help_text)

        combo.currentTextChanged.connect(self._on_field_changed)

        # Refresh-Button
        refresh_btn = QPushButton("🔄")
        refresh_btn.setMaximumWidth(40)
        refresh_btn.setToolTip("Laufwerke neu laden")
        refresh_btn.clicked.connect(lambda: self._refresh_drives(combo))

        layout.addWidget(combo)
        layout.addWidget(refresh_btn)

        self.fields[name] = combo
        self.form_layout.addRow(label_text, layout)

        # Initial laden
        if auto_refresh:
            self._refresh_drives(combo)

    def _add_checkbox_field(self, config: dict):
        """Fügt Checkbox hinzu"""
        name = config["name"]
        label = config.get("label", name)
        default = config.get("default", False)
        help_text = config.get("help", "")

        checkbox = QCheckBox(label)
        checkbox.setChecked(default)

        if help_text:
            checkbox.setToolTip(help_text)

        checkbox.stateChanged.connect(self._on_field_changed)

        self.fields[name] = checkbox
        # Checkbox ohne Label in Formular (Label ist in der Checkbox selbst)
        self.form_layout.addRow("", checkbox)

    def _add_button_field(self, config: dict):
        """Fügt Button hinzu"""
        name = config["name"]
        label = config.get("label", "Button")
        icon = config.get("icon", "")
        action = config.get("action")
        style = config.get("style", "default")  # default, primary, success
        help_text = config.get("help", "")

        button = QPushButton(f"{icon} {label}" if icon else label)

        if help_text:
            button.setToolTip(help_text)

        # Style
        if style == "primary":
            button.setStyleSheet("background-color: #007bff; color: white;")
        elif style == "success":
            button.setStyleSheet("background-color: #28a745; color: white;")

        # Action verbinden
        if action:
            button.clicked.connect(lambda: self._execute_action(action))

        self.fields[name] = button

        # Button ohne Label (in zweiter Spalte)
        self.form_layout.addRow("", button)

    def _add_status_field(self, config: dict):
        """Fügt Status-Anzeige hinzu"""
        name = config["name"]
        label = config.get("label", name)
        dynamic = config.get("dynamic", False)
        check_method = config.get("check_method")

        status_label = QLabel("Prüfe...")
        status_label.setStyleSheet("color: #666;")

        self.fields[name] = status_label
        self.form_layout.addRow(label, status_label)

        # Dynamische Status-Prüfung
        if dynamic and check_method and self.handler:
            self._update_status_field(name, check_method)

    # ========================================================================
    # Event-Handler
    # ========================================================================

    def _on_field_changed(self):
        """Wird aufgerufen wenn ein Feld geändert wird"""
        # Sammle aktuelle Werte
        values = self.get_values()

        # Emit Signal
        self.config_changed.emit(values)

        # Re-evaluiere Conditions
        self._update_conditional_fields()

    def _execute_action(self, action_name: str):
        """Führt Handler-Action aus"""
        if not self.handler:
            logger.warning(f"Keine Handler-Instanz für Action: {action_name}")
            return

        # Hole aktuelle Werte
        values = self.get_values()

        logger.info(f"Führe Action aus: {action_name} mit Werten: {values}")

        # Spezielle Actions
        if action_name == "scan_shares":
            self._action_scan_shares(values)
        elif action_name == "test_connection":
            self._action_test_connection(values)
        elif action_name == "oauth_login":
            self._action_oauth_login(values)
        else:
            # Generische Action
            self.action_requested.emit(action_name, values)

    def _action_scan_shares(self, values: dict):
        """Scannt SMB-Freigaben"""
        host = values.get("host", "")
        user = values.get("user")
        password = values.get("password")

        if not host:
            QMessageBox.warning(self, "Fehler", "Bitte Host-Adresse eingeben")
            return

        if not hasattr(self.handler, "scan_shares"):
            logger.warning("Handler hat keine scan_shares-Methode")
            return

        # Führe Scan aus
        try:
            success, shares, error = self.handler.scan_shares(host, user, password)

            if success and shares:
                # Füge Shares zur ComboBox hinzu
                share_combo = self.fields.get("share")
                if isinstance(share_combo, QComboBox):
                    share_combo.clear()
                    share_combo.addItems(shares)

                QMessageBox.information(
                    self,
                    "Scan erfolgreich",
                    f"Gefundene Freigaben: {len(shares)}\n\n" + "\n".join(shares),
                )
            else:
                QMessageBox.warning(
                    self, "Scan fehlgeschlagen", f"Fehler beim Scannen: {error or 'Unbekannt'}"
                )

        except Exception as e:
            logger.error(f"Fehler beim Share-Scan: {e}")
            QMessageBox.critical(self, "Fehler", f"Scan fehlgeschlagen:\n{e}")

    def _action_test_connection(self, values: dict):
        """Testet Verbindung"""
        if not hasattr(self.handler, "test_connection"):
            logger.warning("Handler hat keine test_connection-Methode")
            return

        try:
            # Verschiedene Handler haben unterschiedliche Signaturen
            # Versuche herauszufinden welche Parameter benötigt werden

            if self.template.storage_type == "smb":
                # SMB: host, share, user, password
                host = values.get("host", "")
                share = values.get("share", "")
                user = values.get("user", "")
                password = values.get("password", "")

                if not all([host, share, user, password]):
                    QMessageBox.warning(self, "Fehler", "Bitte fülle alle Felder aus")
                    return

                success, error = self.handler.test_connection(host, share, user, password)

            elif self.template.storage_type == "webdav":
                # WebDAV: url, user, password
                url = values.get("url", "")
                user = values.get("user", "")
                password = values.get("password", "")

                if not all([url, user, password]):
                    QMessageBox.warning(self, "Fehler", "Bitte fülle alle Felder aus")
                    return

                success, error = self.handler.test_connection(url, user, password)

            else:
                # Generisch
                success, error = self.handler.test_connection()

            # Zeige Ergebnis
            if success:
                QMessageBox.information(
                    self, "✅ Verbindung erfolgreich", "Die Verbindung wurde erfolgreich getestet!"
                )
            else:
                QMessageBox.warning(
                    self, "❌ Verbindung fehlgeschlagen", f"Fehler: {error or 'Unbekannt'}"
                )

        except Exception as e:
            logger.error(f"Fehler beim Verbindungstest: {e}")
            QMessageBox.critical(self, "Fehler", f"Verbindungstest fehlgeschlagen:\n{e}")

    def _refresh_drives(self, combo: QComboBox):
        """Lädt USB-Laufwerke neu"""
        if not self.handler or not hasattr(self.handler, "detect_usb_drives"):
            logger.warning("Handler hat keine detect_usb_drives-Methode")
            combo.addItem("Keine Laufwerke gefunden")
            return

        try:
            drives = self.handler.detect_usb_drives()

            combo.clear()

            if drives:
                for drive in drives:
                    path = drive.get("path", "")
                    label = drive.get("label", "")
                    size = drive.get("size", "")

                    # Display: "D:\ - USB-Stick (16 GB)"
                    display_text = path
                    if label:
                        display_text += f" - {label}"
                    if size:
                        display_text += f" ({size})"

                    combo.addItem(display_text, path)  # Display-Text, User-Data = Pfad

                logger.info(f"USB-Laufwerke geladen: {len(drives)}")
            else:
                combo.addItem("Kein USB-Laufwerk gefunden")
                logger.warning("Keine USB-Laufwerke gefunden")

        except Exception as e:
            logger.error(f"Fehler beim Laden der Laufwerke: {e}")
            combo.addItem(f"Fehler: {e}")

    def _action_oauth_login(self, values: dict):
        """Führt OAuth-Login durch"""
        if not hasattr(self.handler, "_run_oauth_flow"):
            logger.warning("Handler hat keine _run_oauth_flow-Methode")
            return

        try:
            QMessageBox.information(
                self,
                "OAuth-Anmeldung",
                "Ein Browser-Fenster wird geöffnet.\n"
                "Bitte melde dich an und erlaube den Zugriff.",
            )

            success, error = self.handler._run_oauth_flow()

            if success:
                QMessageBox.information(
                    self, "✅ Anmeldung erfolgreich", "Du bist jetzt angemeldet!"
                )

                # Update Status-Feld
                self._update_all_status_fields()
            else:
                QMessageBox.warning(
                    self, "❌ Anmeldung fehlgeschlagen", f"Fehler: {error or 'Unbekannt'}"
                )

        except Exception as e:
            logger.error(f"Fehler beim OAuth-Login: {e}")
            QMessageBox.critical(self, "Fehler", f"Anmeldung fehlgeschlagen:\n{e}")

    # ========================================================================
    # Status-Updates
    # ========================================================================

    def _update_status_field(self, field_name: str, check_method: str):
        """Aktualisiert Status-Feld"""
        if not self.handler:
            return

        if not hasattr(self.handler, check_method):
            logger.warning(f"Handler hat keine Methode: {check_method}")
            return

        try:
            method = getattr(self.handler, check_method)
            authenticated, status_text = method()

            status_label = self.fields.get(field_name)
            if isinstance(status_label, QLabel):
                status_label.setText(status_text)

                # Farbe basierend auf Status
                if authenticated:
                    status_label.setStyleSheet("color: #28a745;")  # Grün
                else:
                    status_label.setStyleSheet("color: #ffc107;")  # Orange

        except Exception as e:
            logger.error(f"Fehler beim Status-Update: {e}")

    def _update_all_status_fields(self):
        """Aktualisiert alle Status-Felder"""
        for field_name, config in self.field_configs.items():
            if config.get("type") == "status":
                check_method = config.get("check_method")
                if check_method:
                    self._update_status_field(field_name, check_method)

    def _update_conditional_fields(self):
        """Aktualisiert Felder mit Conditions"""
        # TODO: Implementierung für condition-Logik
        # Beispiel: "condition": "!authenticated"
        pass

    # ========================================================================
    # Validierung & Werte
    # ========================================================================

    def get_values(self) -> Dict[str, Any]:
        """Gibt alle Formular-Werte zurück"""
        values = {}

        for name, widget in self.fields.items():
            if isinstance(widget, QLineEdit):
                values[name] = widget.text()
            elif isinstance(widget, QComboBox):
                # Für drive_selector: UserData (Pfad) statt Display-Text
                user_data = widget.currentData()
                if user_data:
                    values[name] = user_data
                else:
                    values[name] = widget.currentText()
            elif isinstance(widget, QCheckBox):
                values[name] = widget.isChecked()
            elif isinstance(widget, QLabel):
                # Status-Felder überspringen
                pass
            elif isinstance(widget, QPushButton):
                # Buttons überspringen
                pass

        return values

    def validate(self) -> tuple[bool, Optional[str]]:
        """
        Validiert alle Felder

        Returns:
            (is_valid, error_message)
        """
        for name, config in self.field_configs.items():
            # Prüfe Required
            required = config.get("required", False)
            if required:
                widget = self.fields.get(name)

                if isinstance(widget, QLineEdit):
                    if not widget.text().strip():
                        label = config.get("label", name)
                        return (False, f"Feld '{label}' ist erforderlich")

                elif isinstance(widget, QComboBox):
                    # Prüfe UserData oder Text
                    user_data = widget.currentData()
                    text = widget.currentText().strip()
                    if not user_data and not text:
                        label = config.get("label", name)
                        return (False, f"Feld '{label}' ist erforderlich")
                    # Zusätzliche Prüfung für drive_selector
                    if text.startswith("Kein") or text.startswith("Fehler"):
                        label = config.get("label", name)
                        return (False, f"{label}: {text}")

                elif isinstance(widget, QCheckBox):
                    # Checkbox muss gecheckt sein wenn required
                    if not widget.isChecked():
                        label = config.get("label", name)
                        return (False, f"'{label}' muss aktiviert sein")

            # Prüfe Validation-Pattern
            validation = config.get("validation")
            if validation:
                widget = self.fields.get(name)

                if isinstance(widget, QLineEdit):
                    value = widget.text()
                    if value and not re.match(validation, value):
                        label = config.get("label", name)
                        return (False, f"Feld '{label}' hat ungültiges Format")

        return (True, None)

    def set_values(self, values: Dict[str, Any]):
        """Setzt Formular-Werte"""
        for name, value in values.items():
            widget = self.fields.get(name)

            if isinstance(widget, QLineEdit):
                widget.setText(str(value))
            elif isinstance(widget, QComboBox):
                widget.setCurrentText(str(value))
            elif isinstance(widget, QCheckBox):
                widget.setChecked(bool(value))
