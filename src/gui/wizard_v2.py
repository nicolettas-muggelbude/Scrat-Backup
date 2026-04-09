"""
Setup-Wizard V2 - Mit Template-Manager Integration
Produktionsversion mit echten Templates
"""

import logging

# Template-System importieren
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from PySide6.QtCore import Qt, QTime, Signal
from PySide6.QtGui import QIcon, QPalette, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
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
from utils.paths import get_app_data_dir  # noqa: E402
from gui.theme import (  # noqa: E402
    get_color,
    style_infobox_hint,
    style_infobox_info,
    style_infobox_success,
    style_infobox_error,
    style_label_hint,
    style_label_secondary,
    style_label_error,
    style_label_success,
    style_list_widget,
)

logger = logging.getLogger(__name__)

# ============================================================================
# THEME COLORS
# ============================================================================

ACCENT_COLOR = get_color("primary")  # Zentral aus theme.py


def _is_dark_mode() -> bool:
    """Erkennt Dark Mode anhand der aktuellen QPalette."""
    app = QApplication.instance()
    if app is None:
        return False
    bg = app.palette().color(QPalette.ColorRole.Window)
    return (bg.red() + bg.green() + bg.blue()) / 3 < 128


# ============================================================================
# PAGE IDS - Für dynamisches Routing
# ============================================================================

PAGE_START = 0
PAGE_SOURCE = 1
PAGE_MODE = 2
PAGE_DESTINATION = 3
PAGE_SCHEDULE = 4
PAGE_FINISH = 5
PAGE_RESTORE = 6
PAGE_ENCRYPTION = 7


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
        expert_desc.setStyleSheet(style_label_secondary() + " margin-left: 30px;")
        layout.addWidget(expert_desc)

        layout.addSpacing(30)

        # Info
        info = QLabel(
            "💡 <b>Tipp:</b> Der einfache Modus bietet vorgefertigte Vorlagen für "
            "gängige Backup-Ziele (USB, OneDrive, Synology, etc.)."
        )
        info.setWordWrap(True)
        info.setStyleSheet(style_infobox_info())
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
        desc_label.setStyleSheet(style_label_secondary())
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)

        layout.addSpacing(10)

        subtitle_label = QLabel(subtitle)
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setStyleSheet(style_label_hint())
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
        cursor = Qt.CursorShape.PointingHandCursor if is_available else Qt.CursorShape.ForbiddenCursor
        self.setCursor(cursor)

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
        if not self._is_available:
            return  # nicht-verfügbare Templates können nicht ausgewählt werden
        self.clicked.emit()
        super().mousePressEvent(event)

    def enterEvent(self, event):
        if not self._checked:
            from gui.theme import colors as _tc
            c = _tc()
            if self._is_available:
                self.setStyleSheet(
                    f"TemplateCard {{ background-color: {c['bg_hover']}; "
                    f"border: 2px solid {self._accent_color}; "
                    "border-radius: 6px; }"
                )
            else:
                self.setStyleSheet(
                    f"TemplateCard {{ background-color: {c['warning_bg']}; "
                    "border: 2px solid #ff9800; border-radius: 6px; }"
                )
        super().enterEvent(event)

    def leaveEvent(self, event):
        if not self._checked:
            self._update_style()
        super().leaveEvent(event)

    # --- Style-Update basierend auf Zustand ---
    def _update_style(self):
        from gui.theme import colors as _tc
        c = _tc()
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
                f"TemplateCard {{ background-color: {c['card_bg']}; "
                f"border: 2px solid {c['border_medium']}; border-radius: 6px; }}"
            )
            self.icon_label.setStyleSheet(
                f"border: none; background: transparent; font-size: 24px; color: {c['text_primary']};"
            )
            self.name_label.setStyleSheet(
                f"border: none; background: transparent; font-size: 13px; color: {c['text_primary']};"
            )
        else:
            self.setStyleSheet(
                f"TemplateCard {{ background-color: {c['bg_disabled']}; "
                f"border: 2px solid {c['border_light']}; border-radius: 6px; }}"
            )
            self.icon_label.setStyleSheet(
                f"border: none; background: transparent; font-size: 24px; color: {c['text_disabled']};"
            )
            self.name_label.setStyleSheet(
                f"border: none; background: transparent; font-size: 13px; color: {c['text_disabled']};"
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
        info.setStyleSheet(style_label_hint() + " margin-bottom: 4px;")
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
            error_label.setStyleSheet(style_infobox_error())
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
        desc.setStyleSheet(style_label_secondary() + " margin-bottom: 10px;")
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
        hint.setStyleSheet(style_label_hint() + " margin-top: 8px;")
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
        return PAGE_ENCRYPTION

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
        self.backup_group = QGroupBox()
        backup_layout = QVBoxLayout(self.backup_group)

        self.start_backup_now = QCheckBox("🚀 Backup jetzt starten")
        self.start_backup_now.setStyleSheet("font-size: 14px; font-weight: bold;")
        backup_layout.addWidget(self.start_backup_now)

        self.backup_info = QLabel("   Führt sofort ein erstes vollständiges Backup durch")
        backup_layout.addWidget(self.backup_info)

        layout.addWidget(self.backup_group)

        layout.addSpacing(10)

        # Tray starten
        self.tray_group = QGroupBox()
        tray_layout = QVBoxLayout(self.tray_group)

        self.start_tray = QCheckBox("📍 Scrat-Backup im Hintergrund starten (Tray)")
        self.start_tray.setChecked(True)
        self.start_tray.setStyleSheet("font-size: 14px; font-weight: bold;")
        tray_layout.addWidget(self.start_tray)

        self.tray_info = QLabel(
            "   Startet Scrat-Backup im System-Tray für schnellen Zugriff\n"
            "   und automatische Backups"
        )
        tray_layout.addWidget(self.tray_info)

        layout.addWidget(self.tray_group)

        layout.addSpacing(20)

        self.success_label = QLabel(
            "✅ Du kannst den Assistenten jederzeit über das Tray-Menü\n"
            "erneut öffnen, um Einstellungen zu ändern."
        )
        self.success_label.setWordWrap(True)
        layout.addWidget(self.success_label)

        layout.addStretch()
        self.setLayout(layout)

        self.registerField("start_backup_now", self.start_backup_now)
        self.registerField("start_tray", self.start_tray)

    def initializePage(self):
        """Wird aufgerufen wenn Seite angezeigt wird - erstellt Zusammenfassung"""
        from gui.theme import colors, style_infobox_success, style_label_hint
        c = colors()
        group_style = f"QGroupBox {{ border: 2px solid {c['group_border']}; border-radius: 5px; }}"
        self.backup_group.setStyleSheet(group_style)
        self.tray_group.setStyleSheet(group_style)
        self.backup_info.setStyleSheet(style_label_hint())
        self.tray_info.setStyleSheet(style_label_hint())
        self.success_label.setStyleSheet(style_infobox_success() + " padding: 15px;")

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

        self.summary_label.setText(summary_text)


# ============================================================================
# ENCRYPTION PAGE
# ============================================================================


class EncryptionPage(QWizardPage):
    """
    Wizard-Seite für Backup-Verschlüsselung.

    - Passwort + Bestätigung
    - Optional: sicher im Keyring speichern
    - Vorbefüllt aus Keyring wenn Passwort bereits gesetzt
    """

    def __init__(self):
        super().__init__()
        self.setTitle("Backup verschlüsseln")
        self.setSubTitle(
            "Wähle ein Passwort für deine verschlüsselten Backups.\n"
            "Ohne dieses Passwort kann kein Backup wiederhergestellt werden."
        )

        self._credential_manager = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(16)

        # ── Passwort-Eingabe ───────────────────────────────────────────
        pw_group = QGroupBox("Passwort")
        pw_layout = QVBoxLayout(pw_group)

        pw1_row = QHBoxLayout()
        pw1_row.addWidget(QLabel("Passwort:"))
        self._pw_edit = QLineEdit()
        self._pw_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self._pw_edit.setPlaceholderText("Mindestens 8 Zeichen …")
        pw1_row.addWidget(self._pw_edit)
        pw_layout.addLayout(pw1_row)

        pw2_row = QHBoxLayout()
        pw2_row.addWidget(QLabel("Bestätigung:"))
        self._pw_confirm = QLineEdit()
        self._pw_confirm.setEchoMode(QLineEdit.EchoMode.Password)
        self._pw_confirm.setPlaceholderText("Passwort wiederholen …")
        pw2_row.addWidget(self._pw_confirm)
        pw_layout.addLayout(pw2_row)

        self._pw_match_label = QLabel()
        self._pw_match_label.setStyleSheet("font-size: 12px;")
        pw_layout.addWidget(self._pw_match_label)

        layout.addWidget(pw_group)

        # ── Keyring-Option ─────────────────────────────────────────────
        self._save_checkbox = QCheckBox("Passwort sicher speichern (Keyring)")
        self._save_checkbox.setChecked(True)
        self._save_checkbox.setToolTip(
            "Speichert das Passwort im Betriebssystem-Schlüsselbund\n"
            "(Windows: Credential Manager, Linux: SecretService/GNOME Keyring, macOS: Keychain).\n"
            "Wird für automatische Zeitplan-Backups benötigt."
        )

        try:
            from utils.credential_manager import get_credential_manager
            self._credential_manager = get_credential_manager()
            if not self._credential_manager.available:
                self._save_checkbox.setEnabled(False)
                self._save_checkbox.setText("Passwort speichern (Keyring nicht verfügbar)")
                self._save_checkbox.setChecked(False)
        except Exception:
            self._save_checkbox.setEnabled(False)
            self._save_checkbox.setChecked(False)

        layout.addWidget(self._save_checkbox)

        # ── Hinweis ────────────────────────────────────────────────────
        hint = QLabel(
            "⚠️ <b>Wichtig:</b> Notiere dein Passwort an einem sicheren Ort. "
            "Bei Verlust können deine Backups <b>nicht</b> wiederhergestellt werden."
        )
        hint.setWordWrap(True)
        hint.setStyleSheet(
            "background-color: #fff3cd; color: #856404; "
            "padding: 10px; border-radius: 5px; font-size: 12px;"
        )
        layout.addWidget(hint)

        layout.addStretch()
        self.setLayout(layout)

        self._pw_edit.textChanged.connect(self._validate)
        self._pw_confirm.textChanged.connect(self._validate)

        self.registerField("backup_password", self._pw_edit, "text")

    def initializePage(self):
        """Vorbefüllen aus Keyring wenn vorhanden."""
        if self._credential_manager and self._credential_manager.available:
            saved = self._credential_manager.get_password()
            if saved:
                self._pw_edit.setText(saved)
                self._pw_confirm.setText(saved)
                self._save_checkbox.setChecked(True)

    def _validate(self):
        pw1 = self._pw_edit.text()
        pw2 = self._pw_confirm.text()

        if not pw1:
            self._pw_match_label.setText("")
        elif len(pw1) < 8:
            self._pw_match_label.setText("❌ Mindestens 8 Zeichen")
            self._pw_match_label.setStyleSheet(style_label_error())
        elif pw2 and pw1 != pw2:
            self._pw_match_label.setText("❌ Passwörter stimmen nicht überein")
            self._pw_match_label.setStyleSheet(style_label_error())
        elif pw2 and pw1 == pw2:
            self._pw_match_label.setText("✅ Passwörter stimmen überein")
            self._pw_match_label.setStyleSheet(style_label_success())
        else:
            self._pw_match_label.setText("")

        self.completeChanged.emit()

    def isComplete(self) -> bool:
        pw1 = self._pw_edit.text()
        pw2 = self._pw_confirm.text()
        return len(pw1) >= 8 and pw1 == pw2

    def validatePage(self) -> bool:
        if not self.isComplete():
            return False
        # Passwort in Keyring speichern wenn gewünscht
        if self._save_checkbox.isChecked() and self._credential_manager:
            try:
                self._credential_manager.save_password(self._pw_edit.text())
                logger.info("Backup-Passwort im Keyring gespeichert")
            except Exception as e:
                logger.warning(f"Keyring-Speicherung fehlgeschlagen: {e}")
        return True

    def nextId(self) -> int:
        return PAGE_FINISH


# ============================================================================
# RESTORE WIZARD PAGE
# ============================================================================


class RestoreWizardPage(QWizardPage):
    """
    Restore-Seite im Setup-Wizard.

    Zwei Modi:
    1. DB-Modus (primär):   Lädt metadata.db aus ~/.scrat-backup/
    2. Verzeichnis-Modus:  User wählt Backup-Ordner; DB wird dort gesucht
                            oder separat angegeben (für Wiederherstellung
                            auf neuem System).
    """

    _progress_updated = Signal(object)   # RestoreProgress
    _restore_done = Signal(object)       # RestoreResult

    def __init__(self):
        super().__init__()
        self.setTitle("Backup wiederherstellen")
        self.setSubTitle(
            "Wähle ein Backup aus und stelle deine Dateien wieder her."
        )
        self.setFinalPage(True)

        self._db_path: Optional[Path] = None
        self._metadata_manager = None
        self._restore_running = False
        self._restore_finished = False
        self._selected_backup_id: Optional[int] = None

        self._setup_ui()
        self._progress_updated.connect(self._on_progress_updated)
        self._restore_done.connect(self._on_restore_done)

    # ── UI-Aufbau ─────────────────────────────────────────────────────────

    def _setup_ui(self):
        outer = QVBoxLayout()
        outer.setSpacing(12)

        # ── Modus-Auswahl ──────────────────────────────────────────────
        source_group = QGroupBox("Backup-Quelle")
        source_layout = QVBoxLayout(source_group)

        self._db_radio = QRadioButton("Aus vorhandener Konfiguration laden")
        self._db_radio.setStyleSheet("font-weight: bold;")
        self._db_radio.setChecked(True)
        self._db_info_label = QLabel()
        self._db_info_label.setStyleSheet(style_label_hint() + " margin-left: 22px;")
        self._db_info_label.setWordWrap(True)

        self._dir_radio = QRadioButton("Aus Backup-Verzeichnis auswählen (neues System)")
        self._dir_radio.setStyleSheet("font-weight: bold;")

        # Verzeichnis-Picker (nur Verzeichnis-Modus)
        self._dir_widget = QWidget()
        dir_layout = QVBoxLayout(self._dir_widget)
        dir_layout.setContentsMargins(22, 4, 0, 0)
        dir_layout.setSpacing(6)

        dir_row = QHBoxLayout()
        dir_row.addWidget(QLabel("Backup-Ordner:"))
        self._dir_path_edit = QLineEdit()
        self._dir_path_edit.setPlaceholderText("Pfad zum Backup-Verzeichnis …")
        dir_row.addWidget(self._dir_path_edit, 1)
        self._dir_browse_btn = QPushButton("📁 Durchsuchen")
        self._dir_browse_btn.clicked.connect(self._browse_backup_dir)
        dir_row.addWidget(self._dir_browse_btn)
        dir_layout.addLayout(dir_row)

        db_row = QHBoxLayout()
        db_row.addWidget(QLabel("metadata.db:"))
        self._db_file_edit = QLineEdit()
        self._db_file_edit.setPlaceholderText("Wird automatisch gesucht …")
        self._db_file_edit.setReadOnly(True)
        db_row.addWidget(self._db_file_edit, 1)
        self._db_file_browse_btn = QPushButton("📂 Wählen")
        self._db_file_browse_btn.clicked.connect(self._browse_metadata_db)
        db_row.addWidget(self._db_file_browse_btn)
        dir_layout.addLayout(db_row)

        db_hint = QLabel(
            "ℹ️ Die metadata.db wird benötigt, um Backups entschlüsseln zu können "
            f"(enthält den Schlüssel-Salt). Auf dem alten System lag sie unter "
            f"{get_app_data_dir() / 'metadata.db'}."
        )
        db_hint.setWordWrap(True)
        db_hint.setStyleSheet(style_infobox_hint())
        dir_layout.addWidget(db_hint)

        self._dir_load_btn = QPushButton("🔍 Backups suchen")
        self._dir_load_btn.clicked.connect(self._load_from_dir)
        dir_layout.addWidget(self._dir_load_btn)

        source_layout.addWidget(self._db_radio)
        source_layout.addWidget(self._db_info_label)
        source_layout.addWidget(self._dir_radio)
        source_layout.addWidget(self._dir_widget)
        outer.addWidget(source_group)

        self._db_radio.toggled.connect(self._on_mode_changed)

        # ── Backup-Liste ──────────────────────────────────────────────
        list_group = QGroupBox("Verfügbare Backups")
        list_layout = QVBoxLayout(list_group)

        self._backup_table = QTableWidget()
        self._backup_table.setColumnCount(5)
        self._backup_table.setHorizontalHeaderLabels(
            ["Datum / Uhrzeit", "Typ", "Dateien", "Größe", "Status"]
        )
        from PySide6.QtWidgets import QHeaderView
        hdr = self._backup_table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for col in range(1, 5):
            hdr.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
        self._backup_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._backup_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._backup_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self._backup_table.setMinimumHeight(140)
        self._backup_table.itemSelectionChanged.connect(self._on_backup_selected)
        list_layout.addWidget(self._backup_table)
        outer.addWidget(list_group)

        # ── Einstellungen ──────────────────────────────────────────────
        settings_group = QGroupBox("Wiederherstellungs-Einstellungen")
        settings_layout = QVBoxLayout(settings_group)

        dest_row = QHBoxLayout()
        dest_row.addWidget(QLabel("Zielordner:"))
        self._dest_edit = QLineEdit()
        self._dest_edit.setText(str(Path.home() / "scrat-restore"))
        dest_row.addWidget(self._dest_edit, 1)
        dest_browse = QPushButton("📁 Durchsuchen")
        dest_browse.clicked.connect(self._browse_dest)
        dest_row.addWidget(dest_browse)
        settings_layout.addLayout(dest_row)

        pw_row = QHBoxLayout()
        pw_row.addWidget(QLabel("Passwort:"))
        self._pw_edit = QLineEdit()
        self._pw_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self._pw_edit.setPlaceholderText("Backup-Passwort …")
        pw_row.addWidget(self._pw_edit, 1)
        settings_layout.addLayout(pw_row)

        self._orig_checkbox = QCheckBox(
            "In Original-Verzeichnisse wiederherstellen"
        )
        self._orig_checkbox.setToolTip(
            "Stellt Dateien an ihren ursprünglichen Ort zurück.\n"
            "Nur sinnvoll auf demselben oder identisch eingerichteten System."
        )
        self._overwrite_checkbox = QCheckBox("Vorhandene Dateien überschreiben")
        self._overwrite_checkbox.setEnabled(False)
        self._orig_checkbox.stateChanged.connect(
            lambda s: self._overwrite_checkbox.setEnabled(bool(s))
        )
        settings_layout.addWidget(self._orig_checkbox)
        settings_layout.addWidget(self._overwrite_checkbox)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self._restore_btn = QPushButton("▶ Wiederherstellen")
        self._restore_btn.setEnabled(False)
        self._restore_btn.setStyleSheet(
            "QPushButton { background-color: #0078d4; color: white; "
            "padding: 8px 20px; border-radius: 5px; font-weight: bold; }"
            "QPushButton:hover { background-color: #005a9e; }"
            "QPushButton:disabled { background-color: #ccc; color: #888; }"
        )
        self._restore_btn.clicked.connect(self._start_restore)
        btn_row.addWidget(self._restore_btn)
        settings_layout.addLayout(btn_row)
        outer.addWidget(settings_group)

        # ── Fortschritt ────────────────────────────────────────────────
        self._progress_group = QGroupBox("Fortschritt")
        prog_layout = QVBoxLayout(self._progress_group)

        self._status_label = QLabel("Bereit")
        self._status_label.setStyleSheet("font-size: 13px; font-weight: bold;")
        prog_layout.addWidget(self._status_label)

        self._progress_bar = QProgressBar()
        self._progress_bar.setValue(0)
        prog_layout.addWidget(self._progress_bar)

        self._file_label = QLabel("--")
        self._file_label.setStyleSheet(style_label_hint())
        prog_layout.addWidget(self._file_label)

        self._progress_group.hide()
        outer.addWidget(self._progress_group)

        self.setLayout(outer)

    # ── Modus-Umschaltung ─────────────────────────────────────────────

    def _on_mode_changed(self, db_checked: bool):
        self._dir_widget.setVisible(not db_checked)
        if db_checked and self._db_path:
            self._load_from_db(self._db_path)

    # ── Initialisierung ───────────────────────────────────────────────

    def initializePage(self):
        local_db = get_app_data_dir() / "metadata.db"
        if local_db.exists():
            self._db_radio.setEnabled(True)
            self._db_info_label.setText(f"Konfiguration: {local_db}")
            self._db_radio.setChecked(True)
            self._dir_widget.setVisible(False)
            self._load_from_db(local_db)
        else:
            self._db_radio.setEnabled(False)
            self._db_info_label.setText("Keine lokale Konfiguration gefunden.")
            self._dir_radio.setChecked(True)
            self._dir_widget.setVisible(True)

    # ── Backup-Liste laden ────────────────────────────────────────────

    def _load_from_db(self, db_path: Path):
        """Lädt Backup-Liste aus metadata.db."""
        try:
            from core.metadata_manager import MetadataManager
            if self._metadata_manager:
                try:
                    self._metadata_manager.disconnect()
                except Exception:
                    pass
            self._metadata_manager = MetadataManager(db_path)
            self._db_path = db_path
            backups = self._metadata_manager.get_all_backups(limit=100)
            completed = sorted(
                [b for b in backups if b.get("status") == "completed"],
                key=lambda b: b.get("timestamp", ""),
                reverse=True,
            )
            self._fill_backup_table(completed)
        except Exception as e:
            logger.error(f"Fehler beim Laden der Backup-DB: {e}")
            QMessageBox.warning(
                self, "Fehler", f"Backup-Datenbank konnte nicht geladen werden:\n{e}"
            )

    def _load_from_dir(self):
        """Sucht Backups im gewählten Verzeichnis (Verzeichnis-Modus)."""
        backup_dir = Path(self._dir_path_edit.text().strip())
        if not backup_dir.is_dir():
            QMessageBox.warning(self, "Kein Verzeichnis", "Bitte zuerst einen gültigen Ordner wählen.")
            return

        # 1. metadata.db suchen: explizit gewählt → Ordner → Unterordner
        db_candidates = []
        explicit = self._db_file_edit.text().strip()
        if explicit and Path(explicit).is_file():
            db_candidates.append(Path(explicit))
        for p in [backup_dir / "metadata.db", backup_dir.parent / "metadata.db"]:
            if p.is_file():
                db_candidates.append(p)

        if db_candidates:
            chosen_db = db_candidates[0]
            self._db_file_edit.setText(str(chosen_db))
            self._load_from_db(chosen_db)
        else:
            # Kein DB gefunden → Verzeichnis direkt scannen (ohne Salt-Info)
            self._scan_dir_without_db(backup_dir)

    def _scan_dir_without_db(self, backup_dir: Path):
        """
        Scannt Verzeichnis nach Backup-Ordnern (YYYYMMDD_HHMMSS_type).
        Ohne DB fehlt der Salt → Restore nicht möglich, aber wir zeigen
        was gefunden wurde und erklären das Problem.
        """
        import re
        pattern = re.compile(r"^\d{8}_\d{6}_(full|incr)$")
        found = []
        for d in sorted(backup_dir.iterdir(), reverse=True):
            if d.is_dir() and pattern.match(d.name):
                enc_files = list(d.glob("*.enc"))
                if enc_files:
                    found.append(d)

        if not found:
            QMessageBox.information(
                self,
                "Keine Backups gefunden",
                f"Im Ordner '{backup_dir}' wurden keine Scrat-Backup-Archive gefunden.\n\n"
                "Scrat-Backup-Ordner haben das Format: YYYYMMDD_HHMMSS_full",
            )
            return

        # Tabelle füllen (ohne DB-ID, als Stub-Einträge)
        from datetime import datetime
        rows = []
        for d in found:
            parts = d.name.split("_")
            try:
                dt = datetime.strptime(f"{parts[0]}_{parts[1]}", "%Y%m%d_%H%M%S")
                date_str = dt.strftime("%d.%m.%Y %H:%M:%S")
            except Exception:
                date_str = d.name
            btype = "📦 Full" if parts[2] == "full" else "📝 Incr"
            enc_count = len(list(d.glob("*.enc")))
            rows.append({
                "date": date_str,
                "type": btype,
                "files": "–",
                "size": f"{enc_count} Archiv(e)",
                "status": "⚠️ Kein DB",
                "id": None,
            })

        self._backup_table.setRowCount(len(rows))
        for row, info in enumerate(rows):
            self._backup_table.setItem(row, 0, QTableWidgetItem(info["date"]))
            self._backup_table.setItem(row, 1, QTableWidgetItem(info["type"]))
            self._backup_table.setItem(row, 2, QTableWidgetItem(info["files"]))
            self._backup_table.setItem(row, 3, QTableWidgetItem(info["size"]))
            self._backup_table.setItem(row, 4, QTableWidgetItem(info["status"]))

        QMessageBox.warning(
            self,
            "metadata.db fehlt",
            f"Es wurden {len(found)} Backup(s) gefunden, aber keine metadata.db.\n\n"
            "Ohne die metadata.db kann kein Backup entschlüsselt werden, da der "
            "Schlüssel-Salt dort gespeichert ist.\n\n"
            f"Bitte kopiere die Datei\n  {get_app_data_dir() / 'metadata.db'}\n"
            "vom alten System in diesen Ordner und klicke erneut auf 'Backups suchen'.",
        )
        self._restore_btn.setEnabled(False)

    def _fill_backup_table(self, backups: list):
        """Füllt die Backup-Tabelle aus DB-Einträgen."""
        from datetime import datetime as dt_cls
        self._backup_table.setRowCount(len(backups))
        for row, b in enumerate(backups):
            try:
                ts = dt_cls.fromisoformat(b["timestamp"])
                date_str = ts.strftime("%d.%m.%Y %H:%M:%S")
            except Exception:
                date_str = str(b.get("timestamp", "–"))

            btype = "📦 Full" if b.get("type") == "full" else "📝 Incr"
            files = str(b.get("files_total", 0))
            size_mb = b.get("size_original", 0) / (1024 * 1024)
            size_str = f"{size_mb:.1f} MB"

            date_item = QTableWidgetItem(date_str)
            date_item.setData(Qt.ItemDataRole.UserRole, b["id"])
            self._backup_table.setItem(row, 0, date_item)
            self._backup_table.setItem(row, 1, QTableWidgetItem(btype))
            self._backup_table.setItem(row, 2, QTableWidgetItem(files))
            self._backup_table.setItem(row, 3, QTableWidgetItem(size_str))
            self._backup_table.setItem(row, 4, QTableWidgetItem("✅ Bereit"))

    # ── Browser ───────────────────────────────────────────────────────

    def _browse_backup_dir(self):
        d = QFileDialog.getExistingDirectory(self, "Backup-Ordner wählen", str(Path.home()))
        if d:
            self._dir_path_edit.setText(d)
            self._db_file_edit.clear()

    def _browse_metadata_db(self):
        f, _ = QFileDialog.getOpenFileName(
            self, "metadata.db wählen", str(Path.home()), "SQLite-Datenbank (*.db)"
        )
        if f:
            self._db_file_edit.setText(f)

    def _browse_dest(self):
        d = QFileDialog.getExistingDirectory(
            self, "Zielordner wählen", str(Path.home())
        )
        if d:
            self._dest_edit.setText(d)

    # ── Backup-Auswahl ────────────────────────────────────────────────

    def _on_backup_selected(self):
        rows = self._backup_table.selectedItems()
        if not rows:
            self._selected_backup_id = None
            self._restore_btn.setEnabled(False)
            return
        item = self._backup_table.item(rows[0].row(), 0)
        backup_id = item.data(Qt.ItemDataRole.UserRole)
        self._selected_backup_id = backup_id
        # Nur aktivieren wenn DB vorhanden (ID != None)
        self._restore_btn.setEnabled(backup_id is not None and not self._restore_running)

    # ── Restore starten ───────────────────────────────────────────────

    def _start_restore(self):
        if self._restore_running or not self._selected_backup_id:
            return

        password = self._pw_edit.text()
        if not password:
            QMessageBox.warning(self, "Passwort fehlt", "Bitte gib das Backup-Passwort ein.")
            return

        dest = Path(self._dest_edit.text().strip())
        if not dest.parent.exists():
            QMessageBox.warning(
                self, "Ungültiger Pfad",
                f"Übergeordnetes Verzeichnis '{dest.parent}' existiert nicht."
            )
            return

        if not self._db_path or not self._metadata_manager:
            QMessageBox.warning(self, "Keine DB", "Bitte lade zuerst eine Backup-Datenbank.")
            return

        from core.restore_engine import RestoreConfig
        config = RestoreConfig(
            destination_path=dest,
            password=password,
            restore_to_original=self._orig_checkbox.isChecked(),
            overwrite_existing=self._overwrite_checkbox.isChecked(),
        )

        self._restore_running = True
        self._restore_btn.setEnabled(False)
        self.wizard().button(QWizard.WizardButton.BackButton).setEnabled(False)
        self.wizard().button(QWizard.WizardButton.FinishButton).setEnabled(False)

        self._progress_group.show()
        self._status_label.setText("Starte …")
        self._progress_bar.setValue(0)

        import threading

        db_path = self._db_path
        backup_id = self._selected_backup_id

        def run():
            from core.metadata_manager import MetadataManager as MM
            from core.restore_engine import RestoreEngine
            thread_mm = None
            try:
                thread_mm = MM(db_path)
                backup_info = thread_mm.get_backup(backup_id)
                if not backup_info:
                    raise ValueError(f"Backup #{backup_id} nicht gefunden.")

                from storage.usb_storage import USBStorage
                dest_path_str = backup_info.get("destination_path", "")
                if not dest_path_str:
                    raise ValueError("Kein destination_path in den Backup-Metadaten gefunden.")
                storage = USBStorage(base_path=Path(dest_path_str))
                storage.connect()

                engine = RestoreEngine(
                    metadata_manager=thread_mm,
                    storage_backend=storage,
                    config=config,
                    progress_callback=lambda p: self._progress_updated.emit(p),
                )
                result = engine.restore_full_backup(backup_id)
                self._restore_done.emit(result)
            except Exception as e:
                logger.error(f"Restore-Fehler: {e}", exc_info=True)
                from core.restore_engine import RestoreResult
                self._restore_done.emit(
                    RestoreResult(success=False, files_restored=0,
                                  bytes_restored=0, duration_seconds=0,
                                  errors=[str(e)])
                )
            finally:
                if thread_mm:
                    thread_mm.disconnect()

        threading.Thread(target=run, daemon=True).start()

    # ── Signal-Handler ────────────────────────────────────────────────

    def _on_progress_updated(self, progress):
        phase_names = {
            "preparing":   "Vorbereiten …",
            "downloading": "Lade Archive …",
            "decrypting":  "Entschlüssele …",
            "extracting":  "Entpacke …",
            "restoring":   "Stelle wieder her …",
        }
        self._status_label.setText(phase_names.get(progress.phase, progress.phase))
        self._progress_bar.setValue(int(progress.progress_percentage))
        if progress.current_file:
            self._file_label.setText(f"📄 {progress.current_file}")

    def _on_restore_done(self, result):
        self._restore_running = False
        self._restore_finished = True
        self.wizard().button(QWizard.WizardButton.BackButton).setEnabled(True)
        self.wizard().button(QWizard.WizardButton.FinishButton).setEnabled(True)

        if result.success:
            self._status_label.setText("✅ Wiederherstellung erfolgreich!")
            self._progress_bar.setValue(100)
            mb = result.bytes_restored / (1024 * 1024)
            QMessageBox.information(
                self,
                "Erfolgreich",
                f"Wiederherstellung abgeschlossen!\n\n"
                f"Dateien: {result.files_restored}\n"
                f"Größe: {mb:.1f} MB\n"
                f"Dauer: {result.duration_seconds:.1f}s",
            )
        else:
            self._status_label.setText("❌ Wiederherstellung fehlgeschlagen")
            errors = "\n".join(result.errors[:5])
            QMessageBox.critical(
                self, "Fehler",
                f"Wiederherstellung fehlgeschlagen:\n\n{errors}"
            )

    def isComplete(self) -> bool:
        return True  # Wizard kann jederzeit abgebrochen werden


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

        # Page 6: Restore
        self.restore_page = RestoreWizardPage()
        self.setPage(PAGE_RESTORE, self.restore_page)

        # Page 7: Encryption
        self.encryption_page = EncryptionPage()
        self.setPage(PAGE_ENCRYPTION, self.encryption_page)

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
        logger.info("Experten-Modus gewählt - öffne MainWindow")

        # MainWindow importieren und öffnen
        from gui.main_window import MainWindow

        self.main_window = MainWindow()
        self.main_window.show()

        # Wizard schließen (mit Rejected, damit main.py nicht Config speichert)
        self.reject()

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

        password = self.field("backup_password") or ""

        config = {
            "action": action,
            "sources": sources.split(",") if sources else [],
            "excludes": excludes.split(",") if excludes else [],
            "template_id": template_id,
            "template_config": template_config,
            "schedule": schedule_config,
            "password": password,
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
