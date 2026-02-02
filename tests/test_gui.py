"""
Unit-Tests für GUI-Komponenten
"""

import pytest
from PySide6.QtWidgets import QApplication

from src.gui.event_bus import EventBus, EventType, get_event_bus
from src.gui.main_window import MainWindow
from src.gui.theme import apply_theme, get_color
from src.gui.wizard import SetupWizard


@pytest.fixture(scope="session")
def qapp():
    """QApplication-Instanz für Tests"""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


class TestEventBus:
    """Tests für Event-Bus"""

    def test_singleton(self):
        """Test Singleton-Pattern"""
        bus1 = get_event_bus()
        bus2 = get_event_bus()
        assert bus1 is bus2

    def test_emit_event(self, qapp):
        """Test Event emittieren"""
        bus = EventBus()
        events_received = []

        def handler(event):
            events_received.append(event)

        bus.event_occurred.connect(handler)
        bus.emit_event(EventType.INFO, message="Test message")

        assert len(events_received) == 1
        assert events_received[0].event_type == EventType.INFO
        assert events_received[0].message == "Test message"

    def test_specific_signals(self, qapp):
        """Test spezifische Signals"""
        bus = EventBus()
        progress_calls = []

        def progress_handler(progress):
            progress_calls.append(progress)

        bus.backup_progress.connect(progress_handler)
        bus.emit_backup_progress("test_progress")

        assert len(progress_calls) == 1
        assert progress_calls[0] == "test_progress"


class TestMainWindow:
    """Tests für Hauptfenster"""

    def test_init(self, qapp):
        """Test Initialisierung"""
        window = MainWindow()
        assert window.windowTitle() == "Scrat-Backup"
        assert window.minimumWidth() == 1000
        assert window.minimumHeight() == 700

    def test_tabs_created(self, qapp):
        """Test dass alle Tabs erstellt wurden"""
        window = MainWindow()
        assert window.tab_widget.count() == 5
        assert window.tab_widget.tabText(0) == "Backup"
        assert window.tab_widget.tabText(1) == "Wiederherstellen"
        assert window.tab_widget.tabText(2) == "Einstellungen"
        assert window.tab_widget.tabText(3) == "Logs"
        assert window.tab_widget.tabText(4) == "Info"

    def test_statusbar(self, qapp):
        """Test Statusleiste"""
        window = MainWindow()
        assert window.status_bar is not None
        assert window.status_label.text() == "Bereit"

    def test_event_handlers_connected(self, qapp):
        """Test dass Event-Handlers verbunden sind"""
        window = MainWindow()
        # Teste durch Emittieren von Events
        window.event_bus.emit_info("Test Info")
        assert "Test Info" in window.status_label.text()


class TestWizard:
    """Tests für Setup-Wizard"""

    def test_init(self, qapp):
        """Test Initialisierung"""
        wizard = SetupWizard()
        assert wizard.windowTitle() == "Scrat-Backup Einrichtung"
        # Wizard hat 6 Seiten
        assert wizard.pageIds() is not None

    def test_get_config(self, qapp):
        """Test Konfiguration abrufen"""
        wizard = SetupWizard()
        config = wizard.get_config()

        assert "sources" in config
        assert "storage" in config
        assert "encryption" in config
        assert "schedule" in config
        assert isinstance(config["sources"], list)


class TestTheme:
    """Tests für Theme"""

    def test_get_stylesheet(self):
        """Test Stylesheet generieren"""
        stylesheet = get_color("primary")
        assert stylesheet.startswith("#")
        assert len(stylesheet) == 7  # #RRGGBB

    def test_apply_theme(self, qapp):
        """Test Theme anwenden"""
        # Sollte keine Exception werfen
        apply_theme(qapp)
        assert qapp.styleSheet() != ""

    def test_get_color(self):
        """Test Farbe abrufen"""
        assert get_color("primary") == "#B8860B"
        assert get_color("success") == "#107C10"
        assert get_color("error") == "#D13438"
        # Unbekannte Farbe
        assert get_color("unknown") == "#000000"
