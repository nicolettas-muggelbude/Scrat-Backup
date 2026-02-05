"""
Setup-Wizard V2 - Mit Template-Manager Integration
Produktionsversion mit echten Templates
"""

import logging

# Template-System importieren
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from PySide6.QtCore import QTime, Qt, Signal
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QRadioButton,
    QScrollArea,
    QSpinBox,
    QTimeEdit,
    QVBoxLayout,
    QWidget,
    QWizard,
    QWizardPage,
)

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.template_manager import Template, TemplateManager  # noqa: E402
from gui.dynamic_template_form import DynamicTemplateForm  # noqa: E402
from gui.theme import get_color  # noqa: E402
from gui.wizard_pages import SourceSelectionPage, StartPage  # noqa: E402
from templates.handlers.base import TemplateHandler  # noqa: E402

logger = logging.getLogger(__name__)

# ============================================================================
# THEME COLORS
# ============================================================================

ACCENT_COLOR = get_color("primary")  # Zentral aus theme.py


# ============================================================================
# PAGE IDS - Für dynamisches Routing
# ============================================================================

PAGE_START = 0
PAGE_SOURCE = 1
PAGE_MODE = 2
PAGE_DESTINATION = 3
PAGE_SCHEDULE = 4
PAGE_FINISH = 5


# ============================================================================
# MODE PAGE (wie im Prototyp)
# ============================================================================


class ModePage(QWizardPage):
    """Auswahl zwischen Normal- und Power-User-Modus"""

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
        icon_path = Path(__file__).parent.parent.parent / "assets" / "icons" / "scrat-128.png"
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

        layout.addSpacing(30)

        # Radio-Buttons ohne Cards
        # Normal-Modus
        self.normal_radio = QRadioButton("🐿️ Einfacher Modus")
        self.normal_radio.setChecked(True)
        self.normal_radio.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(self.normal_radio)

        normal_desc = QLabel("    Geführte Einrichtung mit Vorlagen - ideal für die meisten Nutzer")
        normal_desc.setWordWrap(True)
        normal_desc.setStyleSheet(
            "color: #666; font-size: 13px; margin-left: 30px; margin-bottom: 20px;"
        )
        layout.addWidget(normal_desc)

        layout.addSpacing(15)

        # Experten-Modus
        self.expert_radio = QRadioButton("⚙️ Experten-Modus")
        self.expert_radio.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(self.expert_radio)

        expert_desc = QLabel("    Volle Kontrolle & Anpassungen - für fortgeschrittene Nutzer")
        expert_desc.setWordWrap(True)
        expert_desc.setStyleSheet("color: #666; font-size: 13px; margin-left: 30px;")
        layout.addWidget(expert_desc)

        layout.addSpacing(30)

        # Info
        info = QLabel(
            "💡 <b>Tipp:</b> Der einfache Modus bietet vorgefertigte Vorlagen für "
            "gängige Backup-Ziele (USB, OneDrive, Synology, etc.)."
        )
        info.setWordWrap(True)
        info.setStyleSheet("background-color: #e3f2fd; padding: 15px; border-radius: 5px;")
        layout.addWidget(info)

        layout.addStretch()
        self.setLayout(layout)

        self.registerField("mode_normal", self.normal_radio)

    def _create_mode_card(
        self, title: str, description: str, subtitle: str, is_recommended: bool
    ) -> QWidget:
        """Erstellt Modus-Karte"""
        card = QFrame()
        card.setFrameShape(QFrame.Shape.StyledPanel)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border: 2px solid #cccccc;
                border-radius: 10px;
                padding: 20px;
            }}
            QFrame:hover {{
                border-color: {ACCENT_COLOR};
                background-color: #f5f5f5;
            }}
        """)
        card.setMinimumSize(280, 260)
        card.setMaximumSize(350, 300)

        layout = QVBoxLayout(card)

        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        layout.addSpacing(10)

        desc_label = QLabel(description)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setStyleSheet("font-size: 14px; color: #666;")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)

        layout.addSpacing(10)

        subtitle_label = QLabel(subtitle)
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setStyleSheet("font-size: 11px; color: #999;")
        subtitle_label.setWordWrap(True)
        layout.addWidget(subtitle_label)

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
        if self.expert_radio.isChecked():
            self.expert_mode_requested.emit()
            return False  # Wizard nicht weitergehen bei Experten-Modus
        return True

    def nextId(self) -> int:
        """Nächste Seite: SourceSelectionPage bei Normal-Modus"""
        return PAGE_SOURCE  # Geht zu SourceSelectionPage


# ============================================================================
# TEMPLATE CARD – Kachel mit separaten Icon/Name-Größen
# ============================================================================


class TemplateCard(QFrame):
    """Klickbare Kachel: Icon groß, Name klein, Hover/Checked-Styles"""

    clicked = Signal()

    def __init__(self, icon: str, name: str, is_available: bool, accent_color: str, parent=None):
        super().__init__(parent)
        self._checked = False
        self._is_available = is_available
        self._accent_color = accent_color

        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setMinimumSize(120, 100)
        self.setMaximumSize(150, 115)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(2)
        layout.setContentsMargins(6, 6, 6, 6)

        # Icon-Label (groß)
        self.icon_label = QLabel(icon)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setStyleSheet("border: none; background: transparent;")
        layout.addWidget(self.icon_label)

        # Name-Label (klein, word-wrap)
        self.name_label = QLabel(name)
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name_label.setWordWrap(True)
        self.name_label.setStyleSheet("border: none; background: transparent;")
        layout.addWidget(self.name_label)

        # Warnung bei nicht verfügbar
        if not is_available:
            self.warn_label = QLabel("⚠️")
            self.warn_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.warn_label.setStyleSheet("border: none; background: transparent; font-size: 11px;")
            layout.addWidget(self.warn_label)

        self._update_style()

    # --- Checkable-Interface (wie QPushButton) ---
    def isCheckable(self):
        return True

    def isChecked(self):
        return self._checked

    def setChecked(self, checked: bool):
        self._checked = checked
        self._update_style()

    # --- Maus-Events ---
    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)

    def enterEvent(self, event):
        if not self._checked:
            if self._is_available:
                self.setStyleSheet(
                    "TemplateCard { background-color: #e3f2fd; "
                    f"border: 2px solid {self._accent_color}; "
                    "border-radius: 6px; }"
                )
            else:
                self.setStyleSheet(
                    "TemplateCard { background-color: #fff3e0; "
                    "border: 2px solid #ff9800; border-radius: 6px; }"
                )
        super().enterEvent(event)

    def leaveEvent(self, event):
        if not self._checked:
            self._update_style()
        super().leaveEvent(event)

    # --- Style-Update basierend auf Zustand ---
    def _update_style(self):
        if self._checked:
            self.setStyleSheet(
                f"TemplateCard {{ background-color: {self._accent_color}; "
                f"border: 2px solid {self._accent_color}; "
                "border-radius: 6px; }"
            )
            self.icon_label.setStyleSheet(
                "border: none; background: transparent; font-size: 24px; color: white;"
            )
            self.name_label.setStyleSheet(
                "border: none; background: transparent; font-size: 13px; color: white;"
            )
        elif self._is_available:
            self.setStyleSheet(
                "TemplateCard { background-color: white; "
                "border: 2px solid #cccccc; border-radius: 6px; }"
            )
            self.icon_label.setStyleSheet("border: none; background: transparent; font-size: 24px;")
            self.name_label.setStyleSheet("border: none; background: transparent; font-size: 13px;")
        else:
            self.setStyleSheet(
                "TemplateCard { background-color: #f5f5f5; "
                "border: 2px solid #e0e0e0; border-radius: 6px; }"
            )
            self.icon_label.setStyleSheet(
                "border: none; background: transparent; font-size: 24px; color: #999;"
            )
            self.name_label.setStyleSheet(
                "border: none; background: transparent; font-size: 13px; color: #999;"
            )


# ============================================================================
# TEMPLATE DESTINATION PAGE (NEU: Mit TemplateManager)
# ============================================================================


class TemplateDestinationPage(QWizardPage):
    """Template-basierte Ziel-Auswahl mit echtem TemplateManager"""

    def __init__(self):
        super().__init__()
        self.setTitle("Wo sollen die Backups gespeichert werden?")
        self.setSubTitle("Wähle eine Vorlage für dein Backup-Ziel.")

        # Template-Manager initialisieren
        self.template_manager = TemplateManager()
        self.selected_template: Optional[Template] = None
        self.selected_handler: Optional[TemplateHandler] = None
        self.template_config: Dict[str, Any] = {}
        self.dynamic_form: Optional[DynamicTemplateForm] = None

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # Eine QScrollArea für die gesamte Seite
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_widget)
        self.scroll_layout.setSpacing(16)

        # Info
        info = QLabel(
            "💡 Wähle eine der Vorlagen unten. Die Einrichtung wird automatisch "
            "für dein gewähltes Ziel optimiert."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: #666; font-size: 12px; margin-bottom: 4px;")
        self.scroll_layout.addWidget(info)

        # Lade Templates
        self._load_templates()

        # Dynamisches Formular (in der gleichen ScrollArea wie Kacheln)
        self.form_container = QWidget()
        self.form_layout = QVBoxLayout(self.form_container)
        self.form_container.setVisible(False)
        self.scroll_layout.addWidget(self.form_container)

        self.scroll_layout.addStretch()
        scroll.setWidget(self.scroll_widget)
        layout.addWidget(scroll)

        # Verstecktes QLineEdit als Feld-Träger für template_id
        self._template_id_edit = QLineEdit()
        self._template_id_edit.setVisible(False)
        layout.addWidget(self._template_id_edit)

        self.setLayout(layout)

        # Registriere Feld auf dem versteckten QLineEdit (zuverlässiger als @property)
        self.registerField("template_id*", self._template_id_edit)

    def _load_templates(self):
        """Lädt Templates aus TemplateManager"""
        try:
            # Hole ALLE Templates (auch nicht verfügbare)
            templates = self.template_manager.get_all_templates()
            logger.info(f"Lade {len(templates)} Templates")

            if not templates:
                logger.warning("Keine Templates gefunden!")

            # Option A: Alle Templates in EINEM Grid (kompakt!)
            if templates:
                # Ein einzelnes Grid für alle Templates
                grid = QGridLayout()
                grid.setSpacing(8)

                for i, template in enumerate(templates):
                    btn = self._create_template_button(template)
                    row = i // 5  # 5 Spalten
                    col = i % 5
                    grid.addWidget(btn, row, col)

                self.scroll_layout.addLayout(grid)

        except Exception as e:
            logger.error(f"Fehler beim Laden der Templates: {e}")
            # Fehler-Anzeige
            error_label = QLabel(f"⚠️ Fehler beim Laden der Templates:\n{e}")
            error_label.setStyleSheet("color: red; padding: 10px;")
            self.scroll_layout.addWidget(error_label)

    def _create_template_category(self, category_label: str, templates: list):
        """Erstellt Kategorie-Sektion"""
        # Header
        header = QLabel(f"<b>{category_label}</b>")
        header.setStyleSheet("font-size: 13px; margin-top: 8px; margin-bottom: 5px;")
        self.scroll_layout.addWidget(header)

        # Grid
        grid = QGridLayout()
        grid.setSpacing(8)  # Weniger Abstand

        print(f"DEBUG: Erstelle {len(templates)} Buttons in Grid mit 5 Spalten")
        for i, template in enumerate(templates):
            btn = self._create_template_button(template)
            row = i // 5  # 5 Spalten für kompaktere Darstellung
            col = i % 5
            print(f"  Template {i}: {template.id} -> Position ({row}, {col})")
            grid.addWidget(btn, row, col)

        self.scroll_layout.addLayout(grid)

    def _create_template_button(self, template: Template) -> TemplateCard:
        """Erstellt Template-Kachel"""
        # Prüfe Verfügbarkeit
        handler = self._get_handler_for_template(template)
        is_available = True
        availability_msg = ""

        if handler:
            is_available, availability_msg = handler.check_availability()

        card = TemplateCard(
            icon=template.icon,
            name=template.display_name,
            is_available=is_available,
            accent_color=ACCENT_COLOR,
        )
        card.clicked.connect(lambda: self._on_template_selected(template, card))

        # Tooltip
        tooltip = template.description
        if not is_available:
            tooltip += f"\n\n⚠️ Nicht verfügbar: {availability_msg}"
        card.setToolTip(tooltip)

        return card

    def _get_handler_for_template(self, template: Template):
        """Lädt Handler für Template (ohne Exception)"""
        try:
            handler_name = template.handler_class
            if not handler_name:
                return None

            module_name = f"templates.handlers.{handler_name}"
            class_name = "".join(word.capitalize() for word in handler_name.split("_"))

            module = __import__(module_name, fromlist=[class_name])
            handler_class = getattr(module, class_name)
            return handler_class(template.raw_data)
        except Exception as e:
            logger.debug(f"Konnte Handler für {template.id} nicht laden: {e}")
            return None

    def _on_template_selected(self, template: Template, card: TemplateCard):
        """Handler für Template-Auswahl"""
        # Deselektiere andere Kacheln
        for other in self.findChildren(TemplateCard):
            if other != card:
                other.setChecked(False)

        card.setChecked(True)
        self.selected_template = template
        self._template_id_edit.setText(template.id)

        # Lade Handler
        self._load_handler(template)

        # Zeige Formular
        self._show_template_form()

    def _load_handler(self, template: Template):
        """Lädt Handler für Template"""
        try:
            # Dynamisch Handler laden
            handler_name = template.handler_class
            module_name = f"templates.handlers.{handler_name}"
            class_name = "".join(word.capitalize() for word in handler_name.split("_"))

            module = __import__(module_name, fromlist=[class_name])
            handler_class = getattr(module, class_name)

            self.selected_handler = handler_class(template.raw_data)
            logger.info(f"Handler geladen: {class_name}")

        except Exception as e:
            logger.error(f"Fehler beim Laden des Handlers: {e}")
            self.selected_handler = None
            QMessageBox.warning(
                self,
                "Handler-Fehler",
                f"Handler für {template.display_name} konnte nicht geladen werden:\n{e}",
            )

    def _show_template_form(self):
        """Zeigt Template-spezifisches Formular"""
        if not self.selected_template:
            return

        # Clear Form
        for i in reversed(range(self.form_layout.count())):
            widget = self.form_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        # Header
        header = QLabel(
            f"<h3>{self.selected_template.icon} "
            f"{self.selected_template.display_name} einrichten</h3>"
        )
        self.form_layout.addWidget(header)

        # Beschreibung
        desc = QLabel(self.selected_template.description)
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #666; margin-bottom: 10px;")
        self.form_layout.addWidget(desc)

        # Handler-spezifisches Formular
        if self.selected_handler:
            # Prüfe Verfügbarkeit
            is_available, error = self.selected_handler.check_availability()

            if not is_available:
                # Warnung anzeigen
                warning = QLabel(f"⚠️ {error}")
                warning.setWordWrap(True)
                warning.setStyleSheet(
                    "background-color: #fff3cd; color: #856404; "
                    "padding: 10px; border-radius: 5px;"
                )
                self.form_layout.addWidget(warning)

            # Dynamisches Formular erstellen
            self.dynamic_form = DynamicTemplateForm(
                template=self.selected_template, handler=self.selected_handler, parent=self
            )

            # Signal verbinden: Config-Änderungen speichern
            self.dynamic_form.config_changed.connect(self._on_config_changed)

            # Formular hinzufügen
            self.form_layout.addWidget(self.dynamic_form)

        self.form_container.setVisible(True)

    def _on_config_changed(self, values: Dict[str, Any]):
        """Wird aufgerufen wenn Formular-Werte sich ändern"""
        self.template_config = values
        logger.debug(f"Template-Config geändert: {values}")

    def nextId(self) -> int:
        return PAGE_SCHEDULE

    def validatePage(self) -> bool:
        """Validiert Formular vor Weiter"""
        if not self.selected_template:
            QMessageBox.warning(
                self, "Keine Vorlage gewählt", "Bitte wähle eine Backup-Vorlage aus."
            )
            return False

        # Validiere dynamisches Formular
        if hasattr(self, "dynamic_form") and self.dynamic_form:
            is_valid, error = self.dynamic_form.validate()

            if not is_valid:
                QMessageBox.warning(
                    self, "Ungültige Eingabe", error or "Bitte überprüfe deine Eingaben."
                )
                return False

            # Hole finale Werte
            self.template_config = self.dynamic_form.get_values()

        return True

    # Property für wizard field
    @property
    def selected_template_id(self) -> str:
        return self.selected_template.id if self.selected_template else ""

    def get_template_config(self) -> Dict[str, Any]:
        """Gibt Template-Konfiguration zurück"""
        return self.template_config


# ============================================================================
# SCHEDULE PAGE – Zeitplan / Automatisierung
# ============================================================================


class SchedulePage(QWizardPage):
    """Zeitplan-Einrichtung: wann läuft das Backup automatisch?"""

    def __init__(self):
        super().__init__()
        self.setTitle("Automatisierung")
        self.setSubTitle("Wann soll das Backup automatisch laufen?")

        layout = QVBoxLayout()

        # ── Automatisches Backup aktivieren ────────────────────────────────
        self.auto_checkbox = QCheckBox("Automatisches Backup aktivieren")
        self.auto_checkbox.setChecked(True)
        self.auto_checkbox.setStyleSheet("font-size: 14px; font-weight: bold;")
        self.auto_checkbox.toggled.connect(self._on_auto_toggled)
        layout.addWidget(self.auto_checkbox)

        layout.addSpacing(8)

        # ── Zeitplan-Gruppe ────────────────────────────────────────────────
        self.schedule_group = QGroupBox("⏰ Zeitplan-Optionen")
        sched_layout = QVBoxLayout()

        # Frequenz
        freq_form = QFormLayout()
        self.frequency_combo = QComboBox()
        self.frequency_combo.addItem("📅 Täglich", "daily")
        self.frequency_combo.addItem("📆 Wöchentlich", "weekly")
        self.frequency_combo.addItem("🗓️  Monatlich", "monthly")
        self.frequency_combo.addItem("🚀 Bei System-Start", "startup")
        self.frequency_combo.currentIndexChanged.connect(self._on_frequency_changed)
        freq_form.addRow("Häufigkeit:", self.frequency_combo)
        sched_layout.addLayout(freq_form)

        # Uhrzeit (Täglich / Wöchentlich / Monatlich)
        self.time_group = QGroupBox("🕐 Uhrzeit")
        time_form = QFormLayout()
        self.time_edit = QTimeEdit()
        self.time_edit.setDisplayFormat("HH:mm")
        self.time_edit.setTime(QTime(10, 0))
        time_form.addRow("Zeit:", self.time_edit)
        self.time_group.setLayout(time_form)
        sched_layout.addWidget(self.time_group)

        # Wochentage (nur bei Wöchentlich)
        self.weekdays_group = QGroupBox("📆 Wochentage")
        weekdays_layout = QHBoxLayout()
        self.weekday_checkboxes: dict[int, QCheckBox] = {}
        for day_num, label in [
            (1, "Mo"),
            (2, "Di"),
            (3, "Mi"),
            (4, "Do"),
            (5, "Fr"),
            (6, "Sa"),
            (7, "So"),
        ]:
            cb = QCheckBox(label)
            cb.setChecked(day_num <= 5)  # Mo–Fr default
            self.weekday_checkboxes[day_num] = cb
            weekdays_layout.addWidget(cb)
        self.weekdays_group.setLayout(weekdays_layout)
        sched_layout.addWidget(self.weekdays_group)

        # Tag im Monat (nur bei Monatlich)
        self.monthly_group = QGroupBox("🗓️  Tag im Monat")
        monthly_form = QFormLayout()
        self.day_spin = QSpinBox()
        self.day_spin.setRange(1, 28)
        self.day_spin.setValue(1)
        self.day_spin.setSuffix(". Tag")
        monthly_form.addRow("Tag:", self.day_spin)
        self.monthly_group.setLayout(monthly_form)
        sched_layout.addWidget(self.monthly_group)

        self.schedule_group.setLayout(sched_layout)
        layout.addWidget(self.schedule_group)

        # ── Hinweis ────────────────────────────────────────────────────────
        hint = QLabel("💡 Der Zeitplan kann später in den Einstellungen beliebig geändert werden.")
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #666; font-size: 11px; margin-top: 8px;")
        layout.addWidget(hint)

        self.setLayout(layout)

        # Anfangs nur Uhrzeit sichtbar (daily)
        self._on_frequency_changed(0)

    # ── Signalhandler ──────────────────────────────────────────────────────
    def _on_auto_toggled(self, checked: bool):
        self.schedule_group.setVisible(checked)
        self.schedule_group.setEnabled(checked)

    def _on_frequency_changed(self, _index: int):
        freq = self.frequency_combo.currentData()
        self.time_group.setVisible(freq in ("daily", "weekly", "monthly"))
        self.weekdays_group.setVisible(freq == "weekly")
        self.monthly_group.setVisible(freq == "monthly")

    # ── Navigation ─────────────────────────────────────────────────────────
    def nextId(self) -> int:
        return PAGE_FINISH

    # ── Konfiguration ──────────────────────────────────────────────────────
    def get_schedule_config(self) -> Optional[Dict[str, Any]]:
        """Gibt Zeitplan-Config zurück, oder None wenn deaktiviert."""
        if not self.auto_checkbox.isChecked():
            return None

        freq = self.frequency_combo.currentData()
        config: Dict[str, Any] = {
            "enabled": True,
            "frequency": freq,
        }

        if freq in ("daily", "weekly", "monthly"):
            config["time"] = self.time_edit.time().toString("HH:mm")

        if freq == "weekly":
            config["weekdays"] = [
                day for day, cb in self.weekday_checkboxes.items() if cb.isChecked()
            ]

        if freq == "monthly":
            config["day_of_month"] = self.day_spin.value()

        return config


# ============================================================================
# FINISH PAGE (wie im Prototyp)
# ============================================================================


class NewFinishPage(QWizardPage):
    """Zusammenfassung + Tray-Start + Backup-Option"""

    def __init__(self):
        super().__init__()
        self.setFinalPage(True)
        self.setTitle("Einrichtung abgeschlossen! 🎉")
        self.setSubTitle("Scrat-Backup ist jetzt konfiguriert und bereit.")

        layout = QVBoxLayout()

        self.summary_label = QLabel()
        self.summary_label.setWordWrap(True)
        layout.addWidget(self.summary_label)

        layout.addSpacing(20)

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
        self.start_tray.setChecked(True)
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

        self.registerField("start_backup_now", self.start_backup_now)
        self.registerField("start_tray", self.start_tray)

    def initializePage(self):
        """Wird aufgerufen wenn Seite angezeigt wird - erstellt Zusammenfassung"""
        wizard = self.wizard()

        summary_text = "<h3>📋 Deine Konfiguration:</h3>"
        summary_text += "<table style='margin-top: 10px; width: 100%;'>"

        # 1. Aktion
        action = wizard.field("start_action")
        action_labels = {
            "backup": "🆕 Neues Backup einrichten",
            "restore": "♻️ Backup wiederherstellen",
            "edit": "⚙️ Einstellungen ändern",
            "add_destination": "➕ Neues Ziel hinzufügen",
            "expert": "🔧 Experten-Modus",
        }
        action_label = action_labels.get(action, action)
        summary_text += "<tr><td style='padding: 8px; color: #666;'><b>Aktion:</b></td>"
        summary_text += f"<td style='padding: 8px;'>{action_label}</td></tr>"

        # 2. Quellen (nur bei Backup)
        if action == "backup":
            sources = wizard.field("sources")
            if sources:
                sources_list = sources.split(",")
                summary_text += (
                    "<tr><td style='padding: 8px; color: #666; "
                    "vertical-align: top;'><b>Quellen:</b></td>"
                )
                summary_text += f"<td style='padding: 8px;'>{len(sources_list)} Ordner<br>"

                # Erste 5 Quellen anzeigen
                for source in sources_list[:5]:
                    source_name = Path(source).name or source
                    summary_text += (
                        f"<span style='color: #999; font-size: 11px;'>📁 {source_name}</span><br>"
                    )

                if len(sources_list) > 5:
                    remaining = len(sources_list) - 5
                    summary_text += (
                        "<span style='color: #999; font-size: 11px;'>"
                        f"... und {remaining} weitere</span>"
                    )

                summary_text += "</td></tr>"

            # Ausschlüsse
            excludes = wizard.field("excludes")
            if excludes:
                excludes_list = excludes.split(",")
                summary_text += (
                    "<tr><td style='padding: 8px; color: #666;'>" "<b>Ausschlüsse:</b></td>"
                )
                summary_text += f"<td style='padding: 8px;'>{len(excludes_list)} Muster "
                summary_text += (
                    "<span style='color: #999; font-size: 11px;'>"
                    "(*.tmp, *.cache, ...)</span></td></tr>"
                )

        # 3. Backup-Ziel
        template_id = wizard.field("template_id")
        if template_id:
            # Versuche Template-Info zu holen
            template_name = template_id.replace("_", " ").title()

            # Hole Icon vom Template
            template_icon = "💾"
            template_display = template_name

            # Wenn wir Zugriff auf TemplateManager haben
            if hasattr(wizard, "destination_page"):
                dest_page = wizard.destination_page
                if hasattr(dest_page, "selected_template") and dest_page.selected_template:
                    template_icon = dest_page.selected_template.icon
                    template_display = dest_page.selected_template.display_name

            summary_text += "<tr><td style='padding: 8px; color: #666;'>" "<b>Backup-Ziel:</b></td>"
            summary_text += (
                f"<td style='padding: 8px;'>{template_icon} {template_display}</td></tr>"
            )

        summary_text += "</table>"

        # Hinweis bei Restore
        if action == "restore":
            summary_text += (
                "<br><p style='background-color: #fff3cd; color: #856404; "
                "padding: 15px; border-radius: 5px;'>"
            )
            summary_text += (
                "⚠️ <b>Hinweis:</b> Der Restore-Flow wird in einer "
                "zukünftigen Version implementiert.<br>"
            )
            summary_text += (
                "Aktuell kannst du Backups manuell über das Hauptfenster wiederherstellen."
            )
            summary_text += "</p>"

        self.summary_label.setText(summary_text)


# ============================================================================
# WIZARD V2
# ============================================================================


class SetupWizardV2(QWizard):
    """Setup-Wizard V2 mit TemplateManager-Integration und neuem Flow"""

    def __init__(self, parent: Optional[QWidget] = None, version: str = ""):
        super().__init__(parent)

        # Fenstertitel mit Version (falls übergeben)
        title = "Scrat-Backup Einrichtung"
        if version:
            title += f" v{version}"
        self.setWindowTitle(title)
        self.setWizardStyle(QWizard.WizardStyle.ModernStyle)
        self.setOption(QWizard.WizardOption.HaveHelpButton, False)
        self.setMinimumSize(800, 600)

        # Window-Icon setzen
        icon_path = Path(__file__).parent.parent.parent / "assets" / "icons" / "scrat.ico"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        # Button-Texte
        self.setButtonText(QWizard.WizardButton.BackButton, "Zurück")
        self.setButtonText(QWizard.WizardButton.NextButton, "Weiter")
        self.setButtonText(QWizard.WizardButton.FinishButton, "Fertig")
        self.setButtonText(QWizard.WizardButton.CancelButton, "Abbrechen")

        # Seiten in richtiger Reihenfolge
        # Page 0: Start - Was tun?
        self.start_page = StartPage()
        self.setPage(PAGE_START, self.start_page)

        # Page 1: Source - Was sichern?
        self.source_page = SourceSelectionPage()
        self.setPage(PAGE_SOURCE, self.source_page)

        # Page 2: Mode - Normal vs. Experten (optional, aktuell übersprungen)
        self.mode_page = ModePage()
        self.mode_page.expert_mode_requested.connect(self._open_expert_mode)
        self.setPage(PAGE_MODE, self.mode_page)

        # Page 3: Destination - Wo sichern?
        self.destination_page = TemplateDestinationPage()
        self.setPage(PAGE_DESTINATION, self.destination_page)

        # Page 4: Schedule - Wann? (TODO)
        self.schedule_page = SchedulePage()
        self.setPage(PAGE_SCHEDULE, self.schedule_page)

        # Page 5: Finish
        self.finish_page = NewFinishPage()
        self.setPage(PAGE_FINISH, self.finish_page)

        # Start-Seite
        self.setStartId(PAGE_START)

        # Dynamisches Routing basierend auf Auswahl
        self.start_page.action_selected.connect(self._on_action_selected)

        logger.info("Setup-Wizard V2 initialisiert (neue Pages)")

    def _on_action_selected(self, action: str):
        """Wird aufgerufen wenn Aktion auf StartPage gewählt wird"""
        logger.info(f"Aktion gewählt: {action}")

        # Routing-Logik wird in nextId() von StartPage implementiert
        # Hier könnten wir zusätzliche Logik haben falls nötig

    def _open_expert_mode(self):
        """Öffnet MainWindow für Power-User"""
        logger.info("Power-User-Modus gewählt")
        QMessageBox.information(
            self,
            "Experten-Modus",
            "🛠️ Das Hauptfenster würde jetzt geöffnet werden.\n\n"
            "Diese Funktion wird noch implementiert.",
        )
        # TODO: MainWindow öffnen und Wizard schließen

    def get_config(self) -> dict:
        """Gibt Wizard-Config zurück"""
        # Hole Werte von verschiedenen Seiten
        action = self.field("start_action")
        sources = self.field("sources")
        excludes = self.field("excludes")
        template_id = self.field("template_id")

        # Template-Config von DestinationPage
        template_config = {}
        if hasattr(self.destination_page, "get_template_config"):
            template_config = self.destination_page.get_template_config()

        # Zeitplan von SchedulePage
        schedule_config = None
        if hasattr(self, "schedule_page"):
            schedule_config = self.schedule_page.get_schedule_config()

        config = {
            "action": action,
            "sources": sources.split(",") if sources else [],
            "excludes": excludes.split(",") if excludes else [],
            "template_id": template_id,
            "template_config": template_config,
            "schedule": schedule_config,
            "start_backup_now": self.field("start_backup_now") or False,
            "start_tray": self.field("start_tray") or True,
        }

        logger.info(f"Wizard-Config erstellt: {len(config['sources'])} Quellen")
        return config


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import sys

    from PySide6.QtWidgets import QApplication

    logging.basicConfig(level=logging.INFO)

    app = QApplication(sys.argv)
    wizard = SetupWizardV2()
    wizard.show()

    sys.exit(app.exec())
