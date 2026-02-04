"""
Theme Manager - Dark Mode Support
Automatische Erkennung + Manueller Toggle
"""

import logging
from enum import Enum
from typing import Optional

from PySide6.QtCore import QObject, QSettings, Signal
from PySide6.QtGui import QColor, QGuiApplication, QPalette
from PySide6.QtWidgets import QApplication

logger = logging.getLogger(__name__)


class Theme(Enum):
    """Theme-Modi"""

    AUTO = "auto"  # Folgt System-Einstellung
    LIGHT = "light"  # Heller Modus
    DARK = "dark"  # Dunkler Modus


class ThemeManager(QObject):
    """
    Verwaltet Application Theme (Light/Dark Mode)

    Features:
    - Automatische Erkennung des System-Themes
    - Manueller Toggle zwischen Light/Dark
    - Speichert Präferenz in QSettings
    - Signal bei Theme-Änderung
    """

    # Signal wenn Theme geändert wird
    theme_changed = Signal(str)  # "light" oder "dark"

    def __init__(self, app: QApplication, parent: Optional[QObject] = None):
        super().__init__(parent)

        self.app = app
        self.settings = QSettings("ScratBackup", "Theme")

        # Lade gespeicherte Präferenz
        saved_theme = self.settings.value("theme", "auto")
        self.current_theme = Theme(saved_theme)

        # Initial-Theme anwenden
        self._apply_theme()

    def get_current_theme(self) -> Theme:
        """Gibt aktuellen Theme-Modus zurück"""
        return self.current_theme

    def set_theme(self, theme: Theme):
        """
        Setzt Theme-Modus

        Args:
            theme: AUTO, LIGHT oder DARK
        """
        if theme == self.current_theme:
            return

        self.current_theme = theme
        self.settings.setValue("theme", theme.value)

        logger.info(f"Theme geändert: {theme.value}")
        self._apply_theme()

    def toggle_theme(self):
        """
        Wechselt zwischen Light und Dark
        (Auto → Light → Dark → Light → ...)
        """
        if self.current_theme == Theme.AUTO:
            # Von Auto zu Light
            self.set_theme(Theme.LIGHT)
        elif self.current_theme == Theme.LIGHT:
            # Von Light zu Dark
            self.set_theme(Theme.DARK)
        else:
            # Von Dark zu Light
            self.set_theme(Theme.LIGHT)

    def is_dark_mode(self) -> bool:
        """
        Prüft ob aktuell Dark Mode aktiv ist

        Returns:
            True wenn Dark Mode, False wenn Light Mode
        """
        if self.current_theme == Theme.AUTO:
            return self._is_system_dark_mode()
        else:
            return self.current_theme == Theme.DARK

    def _is_system_dark_mode(self) -> bool:
        """
        Erkennt System-Dark-Mode

        Returns:
            True wenn System im Dark Mode
        """
        # Qt 6.5+ hat colorScheme()
        try:
            from PySide6.QtCore import Qt

            hints = QGuiApplication.styleHints()

            if hasattr(hints, "colorScheme"):
                scheme = hints.colorScheme()
                return scheme == Qt.ColorScheme.Dark
        except:
            pass

        # Fallback: Prüfe Palette-Helligkeit
        palette = self.app.palette()
        window_color = palette.color(QPalette.ColorRole.Window)

        # Wenn Hintergrund dunkel (RGB < 128) → Dark Mode
        brightness = (window_color.red() + window_color.green() + window_color.blue()) / 3
        return brightness < 128

    def _apply_theme(self):
        """Wendet aktuelles Theme an"""
        is_dark = self.is_dark_mode()

        if is_dark:
            self._apply_dark_theme()
        else:
            self._apply_light_theme()

        # Signal aussenden
        theme_name = "dark" if is_dark else "light"
        self.theme_changed.emit(theme_name)
        logger.info(f"Theme angewendet: {theme_name}")

    def _apply_dark_theme(self):
        """Aktiviert Dark Theme (Windows 11 Dark Style)"""
        # Fusion Style mit dunkler Palette
        self.app.setStyle("Fusion")

        dark_palette = QPalette()

        # Farben definieren
        dark_color = QColor(32, 32, 32)
        disabled_color = QColor(127, 127, 127)

        dark_palette.setColor(QPalette.ColorRole.Window, dark_color)
        dark_palette.setColor(QPalette.ColorRole.WindowText, QColor(255, 255, 255))
        dark_palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
        dark_palette.setColor(QPalette.ColorRole.AlternateBase, dark_color)
        dark_palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(45, 45, 45))
        dark_palette.setColor(QPalette.ColorRole.ToolTipText, QColor(255, 255, 255))
        dark_palette.setColor(QPalette.ColorRole.Text, QColor(255, 255, 255))
        dark_palette.setColor(QPalette.ColorRole.Button, dark_color)
        dark_palette.setColor(QPalette.ColorRole.ButtonText, QColor(255, 255, 255))
        dark_palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 0, 0))
        dark_palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))

        # Disabled-Farben
        dark_palette.setColor(
            QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, disabled_color
        )
        dark_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, disabled_color)
        dark_palette.setColor(
            QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, disabled_color
        )
        dark_palette.setColor(
            QPalette.ColorGroup.Disabled, QPalette.ColorRole.Highlight, QColor(80, 80, 80)
        )
        dark_palette.setColor(
            QPalette.ColorGroup.Disabled, QPalette.ColorRole.HighlightedText, disabled_color
        )

        self.app.setPalette(dark_palette)

        # Windows 11 Dark Theme Stylesheet
        stylesheet = """
/* ===== GLOBALE STYLES ===== */
QWidget {
    background-color: #202020;
    color: #ffffff;
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 14px;
}

QMainWindow {
    background-color: #202020;
}

/* ===== BUTTONS ===== */
QPushButton {
    background-color: #2d2d2d;
    color: #ffffff;
    border: 1px solid #3f3f3f;
    border-radius: 4px;
    padding: 8px 16px;
    min-width: 80px;
}

QPushButton:hover {
    background-color: #3a3a3a;
    border: 1px solid #555555;
}

QPushButton:pressed {
    background-color: #1a1a1a;
}

QPushButton:disabled {
    color: #7f7f7f;
    background-color: #252525;
}

QPushButton[primary="true"] {
    background-color: #B8860B;
    color: #ffffff;
    border: none;
}

QPushButton[primary="true"]:hover {
    background-color: #005A9E;
}

QPushButton[primary="true"]:pressed {
    background-color: #004578;
}

/* ===== LINE EDIT ===== */
QLineEdit {
    background-color: #2d2d2d;
    color: #ffffff;
    border: 1px solid #3f3f3f;
    border-radius: 4px;
    padding: 6px 10px;
}

QLineEdit:hover {
    border: 1px solid #555555;
}

QLineEdit:focus {
    border: 2px solid #B8860B;
    padding: 5px 9px;
}

QLineEdit:disabled {
    background-color: #252525;
    color: #7f7f7f;
}

/* ===== TEXT EDIT ===== */
QTextEdit, QPlainTextEdit {
    background-color: #2d2d2d;
    color: #ffffff;
    border: 1px solid #3f3f3f;
    border-radius: 4px;
    padding: 8px;
}

QTextEdit:focus, QPlainTextEdit:focus {
    border: 2px solid #B8860B;
}

/* ===== COMBO BOX ===== */
QComboBox {
    background-color: #2d2d2d;
    color: #ffffff;
    border: 1px solid #3f3f3f;
    border-radius: 4px;
    padding: 6px 10px;
    min-width: 100px;
}

QComboBox:hover {
    border: 1px solid #555555;
}

QComboBox:focus {
    border: 2px solid #B8860B;
}

QComboBox::drop-down {
    border: none;
    width: 20px;
}

QComboBox::down-arrow {
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 5px solid #cccccc;
    margin-right: 5px;
}

QComboBox QAbstractItemView {
    background-color: #2d2d2d;
    color: #ffffff;
    border: 1px solid #3f3f3f;
    selection-background-color: #B8860B;
    selection-color: #ffffff;
    outline: none;
}

/* ===== CHECKBOX & RADIO ===== */
QCheckBox {
    spacing: 8px;
    color: #ffffff;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border: 1px solid #555555;
    border-radius: 4px;
    background-color: #2d2d2d;
}

QCheckBox::indicator:hover {
    border: 1px solid #B8860B;
}

QCheckBox::indicator:checked {
    background-color: #B8860B;
    border: 1px solid #B8860B;
}

QRadioButton {
    spacing: 8px;
    color: #ffffff;
}

QRadioButton::indicator {
    width: 18px;
    height: 18px;
    border: 1px solid #555555;
    border-radius: 9px;
    background-color: #2d2d2d;
}

QRadioButton::indicator:hover {
    border: 1px solid #B8860B;
}

QRadioButton::indicator:checked {
    background-color: #B8860B;
    border: 5px solid #2d2d2d;
}

/* ===== PROGRESS BAR ===== */
QProgressBar {
    background-color: #1a1a1a;
    border: 1px solid #3f3f3f;
    border-radius: 4px;
    text-align: center;
    height: 20px;
    color: #ffffff;
}

QProgressBar::chunk {
    background-color: #B8860B;
    border-radius: 3px;
}

/* ===== SCROLL BAR ===== */
QScrollBar:vertical {
    background: #1a1a1a;
    width: 12px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background: #555555;
    border-radius: 6px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background: #666666;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

QScrollBar:horizontal {
    background: #1a1a1a;
    height: 12px;
    margin: 0;
}

QScrollBar::handle:horizontal {
    background: #555555;
    border-radius: 6px;
    min-width: 30px;
}

QScrollBar::handle:horizontal:hover {
    background: #666666;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0;
}

/* ===== LIST/TABLE/TREE ===== */
QListView, QTreeView, QTableView {
    background-color: #2d2d2d;
    border: 1px solid #3f3f3f;
    border-radius: 4px;
    outline: none;
    color: #ffffff;
}

QListView::item, QTreeView::item, QTableView::item {
    padding: 6px;
}

QListView::item:hover, QTreeView::item:hover, QTableView::item:hover {
    background-color: #3a3a3a;
}

QListView::item:selected, QTreeView::item:selected, QTableView::item:selected {
    background-color: #B8860B;
    color: #ffffff;
}

/* ===== HEADER ===== */
QHeaderView::section {
    background-color: #2d2d2d;
    color: #cccccc;
    padding: 6px;
    border: none;
    border-bottom: 1px solid #3f3f3f;
    font-weight: bold;
}

QHeaderView::section:hover {
    background-color: #3a3a3a;
}

/* ===== TABS ===== */
QTabWidget::pane {
    border: none;
    background-color: #2d2d2d;
    border-radius: 8px;
}

QTabBar::tab {
    background-color: transparent;
    color: #cccccc;
    padding: 10px 20px;
    margin-right: 2px;
    border: none;
    border-bottom: 2px solid transparent;
}

QTabBar::tab:hover {
    color: #ffffff;
    background-color: #3a3a3a;
}

QTabBar::tab:selected {
    color: #B8860B;
    border-bottom: 2px solid #B8860B;
    background-color: #2d2d2d;
}

/* ===== MENU ===== */
QMenuBar {
    background-color: #2d2d2d;
    border-bottom: 1px solid #3f3f3f;
    color: #ffffff;
}

QMenuBar::item {
    padding: 6px 12px;
    background-color: transparent;
}

QMenuBar::item:selected {
    background-color: #3a3a3a;
}

QMenu {
    background-color: #2d2d2d;
    border: 1px solid #3f3f3f;
    border-radius: 4px;
    color: #ffffff;
}

QMenu::item {
    padding: 6px 24px;
}

QMenu::item:selected {
    background-color: #B8860B;
    color: #ffffff;
}

/* ===== GROUP BOX ===== */
QGroupBox {
    background-color: #2d2d2d;
    border: 1px solid #3f3f3f;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 12px;
    font-weight: bold;
    color: #ffffff;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 8px;
    background-color: #2d2d2d;
}

/* ===== TOOLTIP ===== */
QToolTip {
    background-color: #2d2d2d;
    color: #ffffff;
    border: 1px solid #3f3f3f;
    border-radius: 4px;
    padding: 4px 8px;
}

/* ===== DIALOG & WIZARD ===== */
QDialog, QWizard {
    background-color: #202020;
}

QWizard QWidget {
    background-color: #2d2d2d;
}

/* ===== STATUS BAR ===== */
QStatusBar {
    background-color: #2d2d2d;
    border-top: 1px solid #3f3f3f;
    color: #ffffff;
}

/* ===== SPIN BOX ===== */
QSpinBox, QDoubleSpinBox {
    background-color: #2d2d2d;
    color: #ffffff;
    border: 1px solid #3f3f3f;
    border-radius: 4px;
    padding: 6px 10px;
}

QSpinBox:hover, QDoubleSpinBox:hover {
    border: 1px solid #555555;
}

QSpinBox:focus, QDoubleSpinBox:focus {
    border: 2px solid #B8860B;
}
"""

        self.app.setStyleSheet(stylesheet)

    def _apply_light_theme(self):
        """Aktiviert Light Theme (Windows 11 Style)"""
        # Nutze Windows 11 Theme aus theme.py
        try:
            from gui.theme import get_stylesheet

            stylesheet = get_stylesheet()
            self.app.setStyleSheet(stylesheet)
            logger.info("Windows 11 Light Theme angewendet")
        except ImportError:
            # Fallback: System-Default
            self.app.setStyle("")
            self.app.setPalette(self.app.style().standardPalette())
            self.app.setStyleSheet("")
            logger.warning("Konnte Windows 11 Theme nicht laden, nutze System-Default")

    def get_theme_display_name(self) -> str:
        """
        Gibt lesbaren Theme-Namen zurück

        Returns:
            "Hell", "Dunkel" oder "Automatisch"
        """
        if self.current_theme == Theme.AUTO:
            actual = "Dunkel" if self.is_dark_mode() else "Hell"
            return f"Automatisch ({actual})"
        elif self.current_theme == Theme.LIGHT:
            return "Hell"
        else:
            return "Dunkel"
