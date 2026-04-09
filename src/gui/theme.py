"""
Theme-System für Scrat-Backup
Strikte Trennung zwischen Light und Dark Mode.

Verwendung:
    from gui.theme import get_color, get_style, is_dark

    label.setStyleSheet(get_style("label_secondary"))
    tooltip_css = get_style("tooltip")
"""

import logging

from PySide6.QtGui import QPalette
from PySide6.QtWidgets import QApplication

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Farb-Paletten
# ──────────────────────────────────────────────────────────────────────────────

LIGHT = {
    # Akzent
    "primary":         "#B8860B",
    "primary_hover":   "#9A7009",
    "primary_pressed": "#7A5807",
    # Hintergrund
    "bg_main":         "#F3F3F3",
    "bg_card":         "#FFFFFF",
    "bg_hover":        "#F0F0F0",
    "bg_pressed":      "#E5E5E5",
    "bg_input":        "#FFFFFF",
    "bg_disabled":     "#F3F3F3",
    # Text
    "text_primary":    "#000000",
    "text_secondary":  "#605E5C",
    "text_disabled":   "#A19F9D",
    "text_on_primary": "#FFFFFF",
    "text_hint":       "#666666",
    # Rahmen
    "border_light":    "#E1E1E1",
    "border_medium":   "#C8C8C8",
    "border_dark":     "#8A8A8A",
    # Tooltip
    "tooltip_bg":      "#FFFFCC",
    "tooltip_text":    "#000000",
    "tooltip_border":  "#C8C8C8",
    # Status
    "success_bg":      "#DFF0D8",
    "success_text":    "#107C10",
    "success_border":  "#107C10",
    "warning_bg":      "#FFF3CD",
    "warning_text":    "#856404",
    "warning_border":  "#856404",
    "error_bg":        "#F8D7DA",
    "error_text":      "#D13438",
    "error_border":    "#D13438",
    "info_bg":         "#D1ECF1",
    "info_text":       "#0C5460",
    "info_border":     "#0C5460",
    # Infobox (gelb)
    "hint_bg":         "#FFF3CD",
    "hint_text":       "#856404",
    "hint_border":     "#856404",
    # Karten / Gruppen
    "card_bg":         "#FFFFFF",
    "card_border":     "#E1E1E1",
    "group_border":    "#E0E0E0",
    # Listen
    "list_bg":         "#FFFFFF",
    "list_item_hover": "#F0F0F0",
    "list_selected_bg":"#B8860B",
    "list_selected_fg":"#FFFFFF",
}

DARK = {
    # Akzent
    "primary":         "#D4A017",
    "primary_hover":   "#B8860B",
    "primary_pressed": "#9A7009",
    # Hintergrund
    "bg_main":         "#202020",
    "bg_card":         "#2D2D2D",
    "bg_hover":        "#3A3A3A",
    "bg_pressed":      "#1A1A1A",
    "bg_input":        "#2D2D2D",
    "bg_disabled":     "#252525",
    # Text
    "text_primary":    "#FFFFFF",
    "text_secondary":  "#CCCCCC",
    "text_disabled":   "#7F7F7F",
    "text_on_primary": "#FFFFFF",
    "text_hint":       "#AAAAAA",
    # Rahmen
    "border_light":    "#3F3F3F",
    "border_medium":   "#555555",
    "border_dark":     "#777777",
    # Tooltip
    "tooltip_bg":      "#3A3A00",
    "tooltip_text":    "#FFFF99",
    "tooltip_border":  "#888800",
    # Status
    "success_bg":      "#1A3A1A",
    "success_text":    "#5CB85C",
    "success_border":  "#3A7A3A",
    "warning_bg":      "#3A2A00",
    "warning_text":    "#FFD966",
    "warning_border":  "#AA8800",
    "error_bg":        "#3A1A1A",
    "error_text":      "#FF6B6B",
    "error_border":    "#AA3333",
    "info_bg":         "#1A2A3A",
    "info_text":       "#66B8CC",
    "info_border":     "#336688",
    # Infobox (gelb)
    "hint_bg":         "#3A2A00",
    "hint_text":       "#FFD966",
    "hint_border":     "#AA8800",
    # Karten / Gruppen
    "card_bg":         "#2D2D2D",
    "card_border":     "#3F3F3F",
    "group_border":    "#3F3F3F",
    # Listen
    "list_bg":         "#2D2D2D",
    "list_item_hover": "#3A3A3A",
    "list_selected_bg":"#D4A017",
    "list_selected_fg":"#FFFFFF",
}


# ──────────────────────────────────────────────────────────────────────────────
# Aktive Palette
# ──────────────────────────────────────────────────────────────────────────────

def is_dark() -> bool:
    """True wenn aktuell Dark Mode aktiv ist (QPalette-Check)."""
    app = QApplication.instance()
    if app is None:
        return False
    bg = app.palette().color(QPalette.ColorRole.Window)
    return (bg.red() + bg.green() + bg.blue()) / 3 < 128


def colors() -> dict:
    """Gibt die aktive Farbpalette zurück (LIGHT oder DARK)."""
    return DARK if is_dark() else LIGHT


def get_color(name: str) -> str:
    """Gibt eine einzelne Farbe aus der aktiven Palette zurück."""
    return colors().get(name, "#FF00FF")  # Magenta als Fehlerindikator


# ──────────────────────────────────────────────────────────────────────────────
# Stylesheet-Generierung
# ──────────────────────────────────────────────────────────────────────────────

def get_stylesheet() -> str:
    """Vollständiges App-Stylesheet für das aktive Theme."""
    return _build_stylesheet(DARK if is_dark() else LIGHT)


def get_light_stylesheet() -> str:
    return _build_stylesheet(LIGHT)


def get_dark_stylesheet() -> str:
    return _build_stylesheet(DARK)


def _build_stylesheet(c: dict) -> str:
    return f"""
/* ===== GLOBAL ===== */
QWidget {{
    background-color: {c['bg_main']};
    color: {c['text_primary']};
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 14px;
}}

QMainWindow {{
    background-color: {c['bg_main']};
}}

/* ===== TOOLTIP ===== */
QToolTip {{
    background-color: {c['tooltip_bg']};
    color: {c['tooltip_text']};
    border: 1px solid {c['tooltip_border']};
    border-radius: 4px;
    padding: 4px 8px;
    opacity: 240;
}}

/* ===== BUTTONS ===== */
QPushButton {{
    background-color: {c['bg_card']};
    color: {c['text_primary']};
    border: 1px solid {c['border_light']};
    border-radius: 4px;
    padding: 8px 16px;
    min-width: 80px;
}}

QPushButton:hover {{
    background-color: {c['bg_hover']};
    border: 1px solid {c['border_medium']};
}}

QPushButton:pressed {{
    background-color: {c['bg_pressed']};
}}

QPushButton:disabled {{
    color: {c['text_disabled']};
    background-color: {c['bg_disabled']};
    border: 1px solid {c['border_light']};
}}

QPushButton[primary="true"] {{
    background-color: {c['primary']};
    color: {c['text_on_primary']};
    border: none;
}}

QPushButton[primary="true"]:hover {{
    background-color: {c['primary_hover']};
}}

QPushButton[primary="true"]:pressed {{
    background-color: {c['primary_pressed']};
}}

/* ===== LINE EDIT ===== */
QLineEdit {{
    background-color: {c['bg_input']};
    color: {c['text_primary']};
    border: 1px solid {c['border_light']};
    border-radius: 4px;
    padding: 6px 10px;
}}

QLineEdit:hover {{
    border: 1px solid {c['border_medium']};
}}

QLineEdit:focus {{
    border: 2px solid {c['primary']};
    padding: 5px 9px;
}}

QLineEdit:disabled {{
    background-color: {c['bg_disabled']};
    color: {c['text_disabled']};
}}

/* ===== TEXT EDIT ===== */
QTextEdit, QPlainTextEdit {{
    background-color: {c['bg_input']};
    color: {c['text_primary']};
    border: 1px solid {c['border_light']};
    border-radius: 4px;
    padding: 8px;
}}

QTextEdit:focus, QPlainTextEdit:focus {{
    border: 2px solid {c['primary']};
}}

/* ===== COMBO BOX ===== */
QComboBox {{
    background-color: {c['bg_input']};
    color: {c['text_primary']};
    border: 1px solid {c['border_light']};
    border-radius: 4px;
    padding: 6px 10px;
    min-width: 100px;
}}

QComboBox:hover {{
    border: 1px solid {c['border_medium']};
}}

QComboBox:focus {{
    border: 2px solid {c['primary']};
}}

QComboBox::drop-down {{
    border: none;
    width: 20px;
}}

QComboBox::down-arrow {{
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 5px solid {c['text_secondary']};
    margin-right: 5px;
}}

QComboBox QAbstractItemView {{
    background-color: {c['bg_card']};
    color: {c['text_primary']};
    border: 1px solid {c['border_light']};
    selection-background-color: {c['primary']};
    selection-color: {c['text_on_primary']};
    outline: none;
}}

/* ===== SPIN BOX ===== */
QSpinBox, QDoubleSpinBox {{
    background-color: {c['bg_input']};
    color: {c['text_primary']};
    border: 1px solid {c['border_light']};
    border-radius: 4px;
    padding: 6px 10px;
}}

QSpinBox:hover, QDoubleSpinBox:hover {{
    border: 1px solid {c['border_medium']};
}}

QSpinBox:focus, QDoubleSpinBox:focus {{
    border: 2px solid {c['primary']};
}}

/* ===== CHECKBOX ===== */
QCheckBox {{
    spacing: 8px;
    color: {c['text_primary']};
}}

QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border: 1px solid {c['border_medium']};
    border-radius: 4px;
    background-color: {c['bg_input']};
}}

QCheckBox::indicator:hover {{
    border: 1px solid {c['primary']};
}}

QCheckBox::indicator:checked {{
    background-color: {c['primary']};
    border: 1px solid {c['primary']};
}}

/* ===== RADIO BUTTON ===== */
QRadioButton {{
    spacing: 8px;
    color: {c['text_primary']};
}}

QRadioButton::indicator {{
    width: 18px;
    height: 18px;
    border: 1px solid {c['border_medium']};
    border-radius: 9px;
    background-color: {c['bg_input']};
}}

QRadioButton::indicator:hover {{
    border: 1px solid {c['primary']};
}}

QRadioButton::indicator:checked {{
    background-color: {c['primary']};
    border: 5px solid {c['bg_card']};
}}

/* ===== PROGRESS BAR ===== */
QProgressBar {{
    background-color: {c['bg_main']};
    border: 1px solid {c['border_light']};
    border-radius: 4px;
    text-align: center;
    height: 20px;
    color: {c['text_primary']};
}}

QProgressBar::chunk {{
    background-color: {c['primary']};
    border-radius: 3px;
}}

/* ===== SCROLL BAR ===== */
QScrollBar:vertical {{
    background-color: {c['bg_main']};
    width: 12px;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background-color: {c['border_medium']};
    border-radius: 6px;
    min-height: 30px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {c['border_dark']};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

QScrollBar:horizontal {{
    background-color: {c['bg_main']};
    height: 12px;
    margin: 0;
}}

QScrollBar::handle:horizontal {{
    background-color: {c['border_medium']};
    border-radius: 6px;
    min-width: 30px;
}}

QScrollBar::handle:horizontal:hover {{
    background-color: {c['border_dark']};
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0;
}}

/* ===== LIST / TABLE / TREE ===== */
QListView, QTreeView, QTableView {{
    background-color: {c['list_bg']};
    border: 1px solid {c['border_light']};
    border-radius: 4px;
    outline: none;
    color: {c['text_primary']};
}}

QListView::item, QTreeView::item, QTableView::item {{
    padding: 6px;
}}

QListView::item:hover, QTreeView::item:hover, QTableView::item:hover {{
    background-color: {c['list_item_hover']};
}}

QListView::item:selected, QTreeView::item:selected, QTableView::item:selected {{
    background-color: {c['list_selected_bg']};
    color: {c['list_selected_fg']};
}}

/* ===== HEADER ===== */
QHeaderView::section {{
    background-color: {c['bg_card']};
    color: {c['text_secondary']};
    padding: 6px;
    border: none;
    border-bottom: 1px solid {c['border_light']};
    font-weight: bold;
}}

QHeaderView::section:hover {{
    background-color: {c['bg_hover']};
}}

/* ===== TAB WIDGET ===== */
QTabWidget::pane {{
    border: none;
    background-color: {c['bg_card']};
    border-radius: 8px;
}}

QTabBar::tab {{
    background-color: transparent;
    color: {c['text_secondary']};
    padding: 10px 20px;
    margin-right: 2px;
    border: none;
    border-bottom: 2px solid transparent;
}}

QTabBar::tab:hover {{
    color: {c['text_primary']};
    background-color: {c['bg_hover']};
}}

QTabBar::tab:selected {{
    color: {c['primary']};
    border-bottom: 2px solid {c['primary']};
    background-color: {c['bg_card']};
}}

/* ===== MENU ===== */
QMenuBar {{
    background-color: {c['bg_card']};
    border-bottom: 1px solid {c['border_light']};
    color: {c['text_primary']};
}}

QMenuBar::item {{
    padding: 6px 12px;
    background-color: transparent;
}}

QMenuBar::item:selected {{
    background-color: {c['bg_hover']};
}}

QMenu {{
    background-color: {c['bg_card']};
    border: 1px solid {c['border_light']};
    border-radius: 4px;
    color: {c['text_primary']};
}}

QMenu::item {{
    padding: 6px 24px;
}}

QMenu::item:selected {{
    background-color: {c['primary']};
    color: {c['text_on_primary']};
}}

/* ===== GROUP BOX ===== */
QGroupBox {{
    background-color: {c['bg_card']};
    border: 1px solid {c['group_border']};
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 12px;
    font-weight: bold;
    color: {c['text_primary']};
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 8px;
    background-color: {c['bg_card']};
    color: {c['text_primary']};
}}

/* ===== STATUS BAR ===== */
QStatusBar {{
    background-color: {c['bg_card']};
    border-top: 1px solid {c['border_light']};
    color: {c['text_primary']};
}}

/* ===== MESSAGE BOX ===== */
QMessageBox {{
    background-color: {c['bg_card']};
    color: {c['text_primary']};
}}

/* ===== DIALOG & WIZARD ===== */
QDialog {{
    background-color: {c['bg_main']};
    color: {c['text_primary']};
}}

QWizard {{
    background-color: {c['bg_main']};
    color: {c['text_primary']};
}}

QWizard QWidget {{
    background-color: {c['bg_card']};
    color: {c['text_primary']};
}}
"""


# ──────────────────────────────────────────────────────────────────────────────
# Widget-spezifische Stil-Funktionen
# Geben immer einen CSS-String für setStyleSheet() zurück.
# ──────────────────────────────────────────────────────────────────────────────

def style_label_secondary() -> str:
    c = colors()
    return f"color: {c['text_hint']}; font-size: 13px;"


def style_label_hint() -> str:
    c = colors()
    return f"color: {c['text_secondary']}; font-size: 12px;"


def style_label_error() -> str:
    c = colors()
    return f"color: {c['error_text']}; font-size: 12px;"


def style_label_success() -> str:
    c = colors()
    return f"color: {c['success_text']}; font-size: 12px;"


def style_infobox_hint() -> str:
    """Gelbe Infobox (Hinweis/Warnung)."""
    c = colors()
    return (
        f"color: {c['hint_text']}; "
        f"background-color: {c['hint_bg']}; "
        f"border: 1px solid {c['hint_border']}; "
        f"border-radius: 4px; "
        f"padding: 8px; "
        f"font-size: 11px;"
    )


def style_infobox_success() -> str:
    """Grüne Infobox (Erfolg)."""
    c = colors()
    return (
        f"color: {c['success_text']}; "
        f"background-color: {c['success_bg']}; "
        f"border: 1px solid {c['success_border']}; "
        f"border-radius: 4px; "
        f"padding: 8px; "
        f"font-size: 12px;"
    )


def style_infobox_error() -> str:
    """Rote Infobox (Fehler)."""
    c = colors()
    return (
        f"color: {c['error_text']}; "
        f"background-color: {c['error_bg']}; "
        f"border: 1px solid {c['error_border']}; "
        f"border-radius: 4px; "
        f"padding: 8px; "
        f"font-size: 12px;"
    )


def style_infobox_info() -> str:
    """Blaue Infobox (Information)."""
    c = colors()
    return (
        f"color: {c['info_text']}; "
        f"background-color: {c['info_bg']}; "
        f"border: 1px solid {c['info_border']}; "
        f"border-radius: 4px; "
        f"padding: 8px; "
        f"font-size: 12px;"
    )


def style_card() -> str:
    """Karte / Frame."""
    c = colors()
    return (
        f"background-color: {c['card_bg']}; "
        f"border: 1px solid {c['card_border']}; "
        f"border-radius: 8px; "
        f"padding: 16px;"
    )


def style_list_widget() -> str:
    """QListWidget."""
    c = colors()
    return (
        f"background-color: {c['list_bg']}; "
        f"color: {c['text_primary']}; "
        f"border: 1px solid {c['border_light']}; "
        f"border-radius: 4px;"
    )


def style_group_box() -> str:
    """QGroupBox."""
    c = colors()
    return (
        f"QGroupBox {{ "
        f"background-color: {c['bg_card']}; "
        f"border: 1px solid {c['group_border']}; "
        f"border-radius: 8px; "
        f"margin-top: 12px; "
        f"padding-top: 12px; "
        f"color: {c['text_primary']}; "
        f"}} "
        f"QGroupBox::title {{ "
        f"background-color: {c['bg_card']}; "
        f"color: {c['text_primary']}; "
        f"padding: 0 8px; "
        f"}}"
    )


def style_excludes_label() -> str:
    """Label für Ausschluss-Liste."""
    c = colors()
    return f"color: {c['text_primary']}; font-size: 12px;"


def apply_theme(app) -> None:
    """Wendet das aktuelle Stylesheet auf die QApplication an."""
    app.setStyleSheet(get_stylesheet())
    logger.info(f"Theme angewendet: {'dark' if is_dark() else 'light'}")
