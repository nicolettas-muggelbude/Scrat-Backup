"""
Performance-Logger für Scrat-Backup
Misst und loggt Ausführungszeiten von Operationen
"""

import functools
import logging
import time
from typing import Any, Callable

logger = logging.getLogger(__name__)


def log_performance(operation_name: str = None):
    """
    Decorator zum Messen und Loggen der Ausführungszeit

    Args:
        operation_name: Name der Operation (optional, nutzt Funktionsname wenn nicht gesetzt)

    Example:
        @log_performance("Backup erstellen")
        def create_backup():
            # ...

        @log_performance()
        def scan_files():
            # Nutzt "scan_files" als operation_name
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            op_name = operation_name or func.__name__
            start_time = time.time()

            try:
                logger.debug(f"[PERFORMANCE] Start: {op_name}")
                result = func(*args, **kwargs)
                elapsed = time.time() - start_time

                # Log-Level basierend auf Dauer
                if elapsed > 60:  # > 1 Minute
                    logger.warning(f"[PERFORMANCE] {op_name} dauerte {elapsed:.2f}s (>{60}s!)")
                elif elapsed > 10:  # > 10 Sekunden
                    logger.info(f"[PERFORMANCE] {op_name} abgeschlossen in {elapsed:.2f}s")
                else:
                    logger.debug(f"[PERFORMANCE] {op_name} abgeschlossen in {elapsed:.2f}s")

                return result

            except Exception as e:
                elapsed = time.time() - start_time
                logger.error(
                    f"[PERFORMANCE] {op_name} fehlgeschlagen nach {elapsed:.2f}s: {e}",
                    exc_info=True,
                )
                raise

        return wrapper

    return decorator


class PerformanceTimer:
    """
    Context Manager zum Messen von Code-Blöcken

    Example:
        with PerformanceTimer("Dateien scannen"):
            files = scan_directory()
    """

    def __init__(self, operation_name: str, log_level: str = "INFO"):
        """
        Initialisiert Timer

        Args:
            operation_name: Name der Operation
            log_level: Log-Level (DEBUG, INFO, WARNING, ERROR)
        """
        self.operation_name = operation_name
        self.log_level = log_level.upper()
        self.start_time = None
        self.end_time = None

    def __enter__(self):
        """Startet Timer"""
        self.start_time = time.time()
        logger.debug(f"[PERFORMANCE] Start: {self.operation_name}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stoppt Timer und loggt Ergebnis"""
        self.end_time = time.time()
        elapsed = self.end_time - self.start_time

        if exc_type is not None:
            # Fehler aufgetreten
            logger.error(
                f"[PERFORMANCE] {self.operation_name} fehlgeschlagen nach {elapsed:.2f}s",
                exc_info=True,
            )
        else:
            # Erfolgreich
            log_method = getattr(logger, self.log_level.lower(), logger.info)
            log_method(f"[PERFORMANCE] {self.operation_name} abgeschlossen in {elapsed:.2f}s")

    @property
    def elapsed(self) -> float:
        """Gibt verstrichene Zeit zurück"""
        if self.start_time is None:
            return 0.0
        end = self.end_time or time.time()
        return end - self.start_time
