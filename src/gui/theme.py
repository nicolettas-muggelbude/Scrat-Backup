"""
Windows 11 Theme für Scrat-Backup
Qt Style Sheets (QSS) im modernen Windows 11-Design
"""

import logging

logger = logging.getLogger(__name__)


# Farb-Palette (Windows 11 Style)
COLORS = {
    # Primärfarben
    "primary": "#B8860B",  # Windows Blue
    "primary_hover": "#005A9E",
    "primary_pressed": "#004578",
    # Hintergrund
    "bg_main": "#F3F3F3",  # Light mode background
    "bg_card": "#FFFFFF",
    "bg_hover": "#F9F9F9",
    "bg_pressed": "#E5E5E5",
    # Text
    "text_primary": "#000000",
    "text_secondary": "#605E5C",
    "text_disabled": "#A19F9D",
    "text_on_primary": "#FFFFFF",
    # Borders
    "border_light": "#E1E1E1",
    "border_medium": "#C8C8C8",
    "border_dark": "#8A8A8A",
    # Status
    "success": "#107C10",
    "warning": "#F7630C",
    "error": "#D13438",
    "info": "#B8860B",
    # Accent (kann vom User customized werden)
    "accent": "#B8860B",
}


def get_stylesheet() -> str:
    """
    Gibt komplettes Windows 11 Stylesheet zurück

    Returns:
        QSS-String
    """
    return f"""
/* ===== GLOBALE STYLES ===== */
QWidget {{
    background-color: {COLORS['bg_main']};
    color: {COLORS['text_primary']};
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 14px;
}}

/* ===== MAIN WINDOW ===== */
QMainWindow {{
    background-color: {COLORS['bg_main']};
}}

/* ===== TAB WIDGET ===== */
QTabWidget::pane {{
    border: none;
    background-color: {COLORS['bg_card']};
    border-radius: 8px;
}}

QTabBar::tab {{
    background-color: transparent;
    color: {COLORS['text_secondary']};
    padding: 10px 20px;
    margin-right: 2px;
    border: none;
    border-bottom: 2px solid transparent;
}}

QTabBar::tab:hover {{
    color: {COLORS['text_primary']};
    background-color: {COLORS['bg_hover']};
}}

QTabBar::tab:selected {{
    color: {COLORS['primary']};
    border-bottom: 2px solid {COLORS['primary']};
    background-color: {COLORS['bg_card']};
}}

/* ===== BUTTONS ===== */
QPushButton {{
    background-color: {COLORS['bg_card']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border_light']};
    border-radius: 4px;
    padding: 8px 16px;
    min-width: 80px;
}}

QPushButton:hover {{
    background-color: {COLORS['bg_hover']};
    border: 1px solid {COLORS['border_medium']};
}}

QPushButton:pressed {{
    background-color: {COLORS['bg_pressed']};
}}

QPushButton:disabled {{
    color: {COLORS['text_disabled']};
    background-color: {COLORS['bg_main']};
    border: 1px solid {COLORS['border_light']};
}}

/* Primary Button */
QPushButton[primary="true"] {{
    background-color: {COLORS['primary']};
    color: {COLORS['text_on_primary']};
    border: none;
}}

QPushButton[primary="true"]:hover {{
    background-color: {COLORS['primary_hover']};
}}

QPushButton[primary="true"]:pressed {{
    background-color: {COLORS['primary_pressed']};
}}

/* ===== LINE EDIT ===== */
QLineEdit {{
    background-color: {COLORS['bg_card']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border_light']};
    border-radius: 4px;
    padding: 6px 10px;
}}

QLineEdit:hover {{
    border: 1px solid {COLORS['border_medium']};
}}

QLineEdit:focus {{
    border: 2px solid {COLORS['primary']};
    padding: 5px 9px;
}}

QLineEdit:disabled {{
    background-color: {COLORS['bg_main']};
    color: {COLORS['text_disabled']};
}}

/* ===== TEXT EDIT ===== */
QTextEdit, QPlainTextEdit {{
    background-color: {COLORS['bg_card']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border_light']};
    border-radius: 4px;
    padding: 8px;
}}

QTextEdit:focus, QPlainTextEdit:focus {{
    border: 2px solid {COLORS['primary']};
}}

/* ===== COMBO BOX ===== */
QComboBox {{
    background-color: {COLORS['bg_card']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border_light']};
    border-radius: 4px;
    padding: 6px 10px;
    min-width: 100px;
}}

QComboBox:hover {{
    border: 1px solid {COLORS['border_medium']};
}}

QComboBox:focus {{
    border: 2px solid {COLORS['primary']};
}}

QComboBox::drop-down {{
    border: none;
    width: 20px;
}}

QComboBox::down-arrow {{
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 5px solid {COLORS['text_secondary']};
    margin-right: 5px;
}}

QComboBox QAbstractItemView {{
    background-color: {COLORS['bg_card']};
    border: 1px solid {COLORS['border_light']};
    selection-background-color: {COLORS['primary']};
    selection-color: {COLORS['text_on_primary']};
    outline: none;
}}

/* ===== SPIN BOX ===== */
QSpinBox, QDoubleSpinBox {{
    background-color: {COLORS['bg_card']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border_light']};
    border-radius: 4px;
    padding: 6px 10px;
}}

QSpinBox:hover, QDoubleSpinBox:hover {{
    border: 1px solid {COLORS['border_medium']};
}}

QSpinBox:focus, QDoubleSpinBox:focus {{
    border: 2px solid {COLORS['primary']};
}}

/* ===== CHECKBOX ===== */
QCheckBox {{
    spacing: 8px;
}}

QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border: 1px solid {COLORS['border_medium']};
    border-radius: 4px;
    background-color: {COLORS['bg_card']};
}}

QCheckBox::indicator:hover {{
    border: 1px solid {COLORS['primary']};
}}

QCheckBox::indicator:checked {{
    background-color: {COLORS['primary']};
    border: 1px solid {COLORS['primary']};
}}

QCheckBox::indicator:checked:after {{
    content: "✓";
    color: {COLORS['text_on_primary']};
}}

/* ===== RADIO BUTTON ===== */
QRadioButton {{
    spacing: 8px;
}}

QRadioButton::indicator {{
    width: 18px;
    height: 18px;
    border: 1px solid {COLORS['border_medium']};
    border-radius: 9px;
    background-color: {COLORS['bg_card']};
}}

QRadioButton::indicator:hover {{
    border: 1px solid {COLORS['primary']};
}}

QRadioButton::indicator:checked {{
    background-color: {COLORS['primary']};
    border: 5px solid {COLORS['bg_card']};
}}

/* ===== PROGRESS BAR ===== */
QProgressBar {{
    background-color: {COLORS['bg_main']};
    border: 1px solid {COLORS['border_light']};
    border-radius: 4px;
    text-align: center;
    height: 20px;
}}

QProgressBar::chunk {{
    background-color: {COLORS['primary']};
    border-radius: 3px;
}}

/* ===== SCROLL BAR ===== */
QScrollBar:vertical {{
    background-color: {COLORS['bg_main']};
    width: 12px;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background-color: {COLORS['border_medium']};
    border-radius: 6px;
    min-height: 30px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {COLORS['border_dark']};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

QScrollBar:horizontal {{
    background-color: {COLORS['bg_main']};
    height: 12px;
    margin: 0;
}}

QScrollBar::handle:horizontal {{
    background-color: {COLORS['border_medium']};
    border-radius: 6px;
    min-width: 30px;
}}

QScrollBar::handle:horizontal:hover {{
    background-color: {COLORS['border_dark']};
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0;
}}

/* ===== LIST VIEW ===== */
QListView, QTreeView, QTableView {{
    background-color: {COLORS['bg_card']};
    border: 1px solid {COLORS['border_light']};
    border-radius: 4px;
    outline: none;
}}

QListView::item, QTreeView::item, QTableView::item {{
    padding: 6px;
}}

QListView::item:hover, QTreeView::item:hover, QTableView::item:hover {{
    background-color: {COLORS['bg_hover']};
}}

QListView::item:selected, QTreeView::item:selected, QTableView::item:selected {{
    background-color: {COLORS['primary']};
    color: {COLORS['text_on_primary']};
}}

/* ===== HEADER VIEW ===== */
QHeaderView::section {{
    background-color: {COLORS['bg_card']};
    color: {COLORS['text_secondary']};
    padding: 6px;
    border: none;
    border-bottom: 1px solid {COLORS['border_light']};
    font-weight: bold;
}}

QHeaderView::section:hover {{
    background-color: {COLORS['bg_hover']};
}}

/* ===== MENU ===== */
QMenuBar {{
    background-color: {COLORS['bg_card']};
    border-bottom: 1px solid {COLORS['border_light']};
}}

QMenuBar::item {{
    padding: 6px 12px;
    background-color: transparent;
}}

QMenuBar::item:selected {{
    background-color: {COLORS['bg_hover']};
}}

QMenu {{
    background-color: {COLORS['bg_card']};
    border: 1px solid {COLORS['border_light']};
    border-radius: 4px;
}}

QMenu::item {{
    padding: 6px 24px;
}}

QMenu::item:selected {{
    background-color: {COLORS['primary']};
    color: {COLORS['text_on_primary']};
}}

/* ===== STATUS BAR ===== */
QStatusBar {{
    background-color: {COLORS['bg_card']};
    border-top: 1px solid {COLORS['border_light']};
}}

/* ===== GROUP BOX ===== */
QGroupBox {{
    background-color: {COLORS['bg_card']};
    border: 1px solid {COLORS['border_light']};
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 12px;
    font-weight: bold;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 8px;
    background-color: {COLORS['bg_card']};
}}

/* ===== TOOL TIP ===== */
QToolTip {{
    background-color: {COLORS['bg_card']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border_light']};
    border-radius: 4px;
    padding: 4px 8px;
}}

/* ===== MESSAGE BOX ===== */
QMessageBox {{
    background-color: {COLORS['bg_card']};
}}

/* ===== DIALOG ===== */
QDialog {{
    background-color: {COLORS['bg_main']};
}}

/* ===== WIZARD ===== */
QWizard {{
    background-color: {COLORS['bg_main']};
}}

QWizard QWidget {{
    background-color: {COLORS['bg_card']};
}}

/* ===== CARDS (Custom Class) ===== */
.Card {{
    background-color: {COLORS['bg_card']};
    border: 1px solid {COLORS['border_light']};
    border-radius: 8px;
    padding: 16px;
}}

.Card:hover {{
    border: 1px solid {COLORS['border_medium']};
}}
"""


def apply_theme(app):
    """
    Wendet Windows 11 Theme auf QApplication an

    Args:
        app: QApplication-Instanz
    """
    app.setStyleSheet(get_stylesheet())
    logger.info("Windows 11 Theme angewendet")


def get_color(color_name: str) -> str:
    """
    Gibt Farbe aus Palette zurück

    Args:
        color_name: Name der Farbe (z.B. 'primary')

    Returns:
        Hex-Farbcode
    """
    return COLORS.get(color_name, "#000000")
