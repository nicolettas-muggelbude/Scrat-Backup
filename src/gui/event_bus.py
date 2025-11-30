"""
Event-Bus für GUI-Core-Kommunikation
Thread-sicheres Event-System mit PyQt6 Signals
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from PyQt6.QtCore import QObject, pyqtSignal

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Event-Typen für GUI-Core-Kommunikation"""

    # Backup-Events
    BACKUP_STARTED = "backup_started"
    BACKUP_PROGRESS = "backup_progress"
    BACKUP_COMPLETED = "backup_completed"
    BACKUP_FAILED = "backup_failed"
    BACKUP_CANCELLED = "backup_cancelled"

    # Restore-Events
    RESTORE_STARTED = "restore_started"
    RESTORE_PROGRESS = "restore_progress"
    RESTORE_COMPLETED = "restore_completed"
    RESTORE_FAILED = "restore_failed"
    RESTORE_CANCELLED = "restore_cancelled"

    # Scan-Events
    SCAN_STARTED = "scan_started"
    SCAN_PROGRESS = "scan_progress"
    SCAN_COMPLETED = "scan_completed"
    SCAN_FAILED = "scan_failed"

    # Storage-Events
    STORAGE_CONNECTED = "storage_connected"
    STORAGE_DISCONNECTED = "storage_disconnected"
    STORAGE_ERROR = "storage_error"
    STORAGE_SPACE_LOW = "storage_space_low"

    # System-Events
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    LOG_MESSAGE = "log_message"


@dataclass
class Event:
    """
    Event-Datenstruktur

    Attributes:
        event_type: Typ des Events
        data: Event-Daten (z.B. Progress-Objekt)
        message: Optionale Nachricht
        timestamp: Event-Zeitstempel
        error: Optionale Fehler-Informationen
    """

    event_type: EventType
    data: Optional[Any] = None
    message: Optional[str] = None
    timestamp: datetime = None
    error: Optional[Exception] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class EventBus(QObject):
    """
    Zentraler Event-Bus für GUI-Core-Kommunikation

    Verwendet PyQt6 Signals für thread-sichere Kommunikation.
    Alle Core-Operations laufen in Background-Threads und
    emittieren Events, die von der GUI empfangen werden.

    Usage:
        # In Core-Thread:
        event_bus.emit_event(EventType.BACKUP_PROGRESS, data=progress)

        # In GUI:
        event_bus.subscribe(EventType.BACKUP_PROGRESS, self.on_backup_progress)
    """

    # PyQt Signals für verschiedene Event-Typen
    # Format: (event_type: str, data: Any, message: str, error: Exception)
    event_occurred = pyqtSignal(object)  # Event object

    # Spezifische Signals für häufig genutzte Events (Performance)
    backup_progress = pyqtSignal(object)  # BackupProgress
    backup_completed = pyqtSignal(object)  # BackupResult
    backup_failed = pyqtSignal(str, object)  # message, exception

    restore_progress = pyqtSignal(object)  # RestoreProgress
    restore_completed = pyqtSignal(object)  # RestoreResult
    restore_failed = pyqtSignal(str, object)  # message, exception

    scan_progress = pyqtSignal(object)  # Path or status
    scan_completed = pyqtSignal(object)  # ScanResult

    storage_connected = pyqtSignal(str)  # storage name
    storage_disconnected = pyqtSignal(str)  # storage name
    storage_error = pyqtSignal(str, object)  # message, exception

    error_occurred = pyqtSignal(str, object)  # message, exception
    warning_occurred = pyqtSignal(str)  # message
    info_message = pyqtSignal(str)  # message
    log_message = pyqtSignal(str, str)  # level, message

    def __init__(self):
        """Initialisiert Event-Bus"""
        super().__init__()
        logger.info("Event-Bus initialisiert")

    def emit_event(
        self,
        event_type: EventType,
        data: Optional[Any] = None,
        message: Optional[str] = None,
        error: Optional[Exception] = None,
    ) -> None:
        """
        Emittiert ein Event

        Args:
            event_type: Typ des Events
            data: Event-Daten
            message: Optionale Nachricht
            error: Optionale Fehler-Informationen
        """
        event = Event(event_type=event_type, data=data, message=message, error=error)

        # Emittiere generisches Event
        self.event_occurred.emit(event)

        # Emittiere spezifisches Signal für Performance
        self._emit_specific_signal(event)

        logger.debug(f"Event emittiert: {event_type.value}")

    def _emit_specific_signal(self, event: Event) -> None:
        """Emittiert spezifisches Signal basierend auf Event-Typ"""
        event_type = event.event_type

        # Backup-Events
        if event_type == EventType.BACKUP_PROGRESS:
            self.backup_progress.emit(event.data)
        elif event_type == EventType.BACKUP_COMPLETED:
            self.backup_completed.emit(event.data)
        elif event_type == EventType.BACKUP_FAILED:
            self.backup_failed.emit(event.message or "Backup fehlgeschlagen", event.error)

        # Restore-Events
        elif event_type == EventType.RESTORE_PROGRESS:
            self.restore_progress.emit(event.data)
        elif event_type == EventType.RESTORE_COMPLETED:
            self.restore_completed.emit(event.data)
        elif event_type == EventType.RESTORE_FAILED:
            self.restore_failed.emit(event.message or "Restore fehlgeschlagen", event.error)

        # Scan-Events
        elif event_type == EventType.SCAN_PROGRESS:
            self.scan_progress.emit(event.data)
        elif event_type == EventType.SCAN_COMPLETED:
            self.scan_completed.emit(event.data)

        # Storage-Events
        elif event_type == EventType.STORAGE_CONNECTED:
            self.storage_connected.emit(event.message or "Storage verbunden")
        elif event_type == EventType.STORAGE_DISCONNECTED:
            self.storage_disconnected.emit(event.message or "Storage getrennt")
        elif event_type == EventType.STORAGE_ERROR:
            self.storage_error.emit(event.message or "Storage-Fehler", event.error)

        # System-Events
        elif event_type == EventType.ERROR:
            self.error_occurred.emit(event.message or "Fehler aufgetreten", event.error)
        elif event_type == EventType.WARNING:
            self.warning_occurred.emit(event.message or "Warnung")
        elif event_type == EventType.INFO:
            self.info_message.emit(event.message or "Information")
        elif event_type == EventType.LOG_MESSAGE:
            level = event.data.get("level", "INFO") if isinstance(event.data, dict) else "INFO"
            self.log_message.emit(level, event.message or "")

    def subscribe(self, event_type: EventType, callback) -> None:
        """
        Abonniert ein Event (Legacy-Methode für Kompatibilität)

        Moderne PyQt-Weise: Verbinde direkt mit Signals:
            event_bus.backup_progress.connect(self.on_backup_progress)

        Args:
            event_type: Event-Typ
            callback: Callback-Funktion
        """

        # Für generische Events
        def event_filter(event: Event):
            if event.event_type == event_type:
                callback(event)

        self.event_occurred.connect(event_filter)
        logger.debug(f"Subscriber registriert für {event_type.value}")

    def emit_backup_progress(self, progress) -> None:
        """Convenience-Methode für Backup-Progress"""
        self.emit_event(EventType.BACKUP_PROGRESS, data=progress)

    def emit_backup_completed(self, result) -> None:
        """Convenience-Methode für Backup-Completion"""
        self.emit_event(EventType.BACKUP_COMPLETED, data=result)

    def emit_backup_failed(self, message: str, error: Optional[Exception] = None) -> None:
        """Convenience-Methode für Backup-Fehler"""
        self.emit_event(EventType.BACKUP_FAILED, message=message, error=error)

    def emit_restore_progress(self, progress) -> None:
        """Convenience-Methode für Restore-Progress"""
        self.emit_event(EventType.RESTORE_PROGRESS, data=progress)

    def emit_restore_completed(self, result) -> None:
        """Convenience-Methode für Restore-Completion"""
        self.emit_event(EventType.RESTORE_COMPLETED, data=result)

    def emit_restore_failed(self, message: str, error: Optional[Exception] = None) -> None:
        """Convenience-Methode für Restore-Fehler"""
        self.emit_event(EventType.RESTORE_FAILED, message=message, error=error)

    def emit_error(self, message: str, error: Optional[Exception] = None) -> None:
        """Convenience-Methode für Fehler"""
        self.emit_event(EventType.ERROR, message=message, error=error)

    def emit_warning(self, message: str) -> None:
        """Convenience-Methode für Warnungen"""
        self.emit_event(EventType.WARNING, message=message)

    def emit_info(self, message: str) -> None:
        """Convenience-Methode für Infos"""
        self.emit_event(EventType.INFO, message=message)


# Globale Event-Bus-Instanz
_event_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """
    Gibt globale Event-Bus-Instanz zurück (Singleton)

    Returns:
        EventBus-Instanz
    """
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus
