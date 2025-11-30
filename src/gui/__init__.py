"""
GUI-Komponenten für Scrat-Backup
PyQt6-basierte Benutzeroberfläche im Windows 11-Stil
"""

from src.gui.event_bus import EventBus, EventType, get_event_bus

__all__ = ["EventBus", "EventType", "get_event_bus"]
