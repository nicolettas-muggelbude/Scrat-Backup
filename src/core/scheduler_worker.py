"""
Scheduler-Worker für Scrat-Backup
Background-Thread der Zeitpläne überwacht und Backups triggert
"""

import logging
from datetime import datetime
from typing import Optional

from PySide6.QtCore import QThread, Signal

from src.core.scheduler import Scheduler

logger = logging.getLogger(__name__)


class SchedulerWorker(QThread):
    """
    Background-Thread für Scheduler

    Läuft im Hintergrund und prüft regelmäßig ob geplante Backups fällig sind.
    Kommuniziert über Signals mit dem Hauptprogramm.

    Signals:
        backup_due: Wird ausgelöst wenn ein Backup fällig ist
                    Args: schedule (Schedule), is_missed (bool)
        next_run_changed: Wird ausgelöst wenn sich nächster Lauf ändert
                         Args: schedule_id (int), next_run (datetime)
        error_occurred: Wird bei Fehlern ausgelöst
                       Args: error_message (str)
    """

    # Signals
    backup_due = Signal(object, bool)  # schedule, is_missed
    next_run_changed = Signal(int, object)  # schedule_id, next_run (datetime)
    error_occurred = Signal(str)  # error_message

    def __init__(self, scheduler: Scheduler, check_interval: int = 60, parent=None):
        """
        Initialisiert Scheduler-Worker

        Args:
            scheduler: Scheduler-Instanz
            check_interval: Prüf-Intervall in Sekunden (default: 60)
            parent: Parent-Objekt
        """
        super().__init__(parent)

        self.scheduler = scheduler
        self.check_interval = check_interval
        self._running = False
        self._paused = False

        # Für Missed-Backup-Detection
        self.last_check_time: Optional[datetime] = None

        logger.info(f"SchedulerWorker initialisiert (Check-Intervall: {check_interval}s)")

    def run(self) -> None:
        """
        Haupt-Loop des Workers

        Läuft solange _running True ist und prüft in regelmäßigen Abständen
        ob Backups fällig sind.
        """
        self._running = True
        self.last_check_time = datetime.now()

        logger.info("SchedulerWorker gestartet")

        while self._running:
            try:
                # Wenn pausiert, warten
                if self._paused:
                    self.msleep(1000)  # 1 Sekunde warten
                    continue

                # Prüfe auf fällige Jobs
                self._check_for_due_jobs()

                # Prüfe auf verpasste Backups
                self._check_for_missed_backups()

                # Update last_check_time
                self.last_check_time = datetime.now()

                # Warte bis zum nächsten Check
                # Unterteile in kleinere Intervalle für responsives Stoppen
                for _ in range(self.check_interval):
                    if not self._running:
                        break
                    self.msleep(1000)  # 1 Sekunde

            except Exception as e:
                logger.error(f"Fehler im SchedulerWorker: {e}", exc_info=True)
                self.error_occurred.emit(str(e))
                # Warte kurz bevor wir weitermachen
                self.msleep(5000)

        logger.info("SchedulerWorker beendet")

    def _check_for_due_jobs(self) -> None:
        """
        Prüft ob Jobs fällig sind und triggert sie
        """
        try:
            # Hole fällige Jobs vom Scheduler
            due_schedules = self.scheduler.check_due_jobs()

            for schedule in due_schedules:
                logger.info(f"Backup fällig: '{schedule.name}'")

                # Markiere als laufend
                self.scheduler.mark_job_running(schedule.id, True)

                # Emittiere Signal (is_missed=False da es pünktlich ist)
                self.backup_due.emit(schedule, False)

                # Emittiere next_run_changed für UI-Update
                next_run = self.scheduler.get_next_scheduled_run(schedule.id)
                if next_run:
                    self.next_run_changed.emit(schedule.id, next_run)

        except Exception as e:
            logger.error(f"Fehler beim Prüfen fälliger Jobs: {e}", exc_info=True)
            self.error_occurred.emit(f"Fehler beim Prüfen fälliger Jobs: {e}")

    def _check_for_missed_backups(self) -> None:
        """
        Prüft ob Backups verpasst wurden

        Wenn das System lange ausgeschaltet war, können geplante Backups
        verpasst worden sein. Diese werden erkannt und dem Benutzer gemeldet.
        """
        if not self.last_check_time:
            return

        try:
            now = datetime.now()

            # Wenn mehr als check_interval + Toleranz seit letztem Check vergangen
            # (z.B. System war im Standby oder ausgeschaltet)
            tolerance_seconds = 300  # 5 Minuten Toleranz
            expected_interval = self.check_interval + tolerance_seconds

            time_since_last_check = (now - self.last_check_time).total_seconds()

            if time_since_last_check > expected_interval:
                logger.warning(
                    f"Lange Pause erkannt ({time_since_last_check:.0f}s). "
                    f"Prüfe auf verpasste Backups..."
                )

                # Prüfe alle Jobs ob sie in der Zwischenzeit fällig waren
                for job in self.scheduler.jobs:
                    if job.next_run and job.last_run:
                        # War der geplante Lauf in der Zwischenzeit?
                        if self.last_check_time < job.next_run <= now:
                            logger.info(
                                f"Verpasstes Backup erkannt: '{job.schedule.name}' "
                                f"(geplant: {job.next_run})"
                            )

                            # Emittiere Signal (is_missed=True)
                            self.backup_due.emit(job.schedule, True)

                            # Berechne neuen next_run
                            job.next_run = self.scheduler._calculate_next_run(
                                job.schedule, from_time=now
                            )

                            # Emittiere next_run_changed
                            if job.next_run:
                                self.next_run_changed.emit(job.schedule.id, job.next_run)

        except Exception as e:
            logger.error(f"Fehler bei Missed-Backup-Detection: {e}", exc_info=True)

    def stop(self) -> None:
        """
        Stoppt den Worker
        """
        logger.info("SchedulerWorker wird gestoppt...")
        self._running = False
        self.wait()  # Warte bis Thread beendet ist

    def pause(self) -> None:
        """
        Pausiert den Worker (prüft keine Jobs mehr)
        """
        logger.info("SchedulerWorker pausiert")
        self._paused = True

    def resume(self) -> None:
        """
        Setzt Worker fort
        """
        logger.info("SchedulerWorker fortgesetzt")
        self._paused = False

    def is_running(self) -> bool:
        """
        Prüft ob Worker läuft

        Returns:
            True wenn läuft
        """
        return self._running and self.isRunning()

    def is_paused(self) -> bool:
        """
        Prüft ob Worker pausiert ist

        Returns:
            True wenn pausiert
        """
        return self._paused

    def mark_job_finished(self, schedule_id: int) -> None:
        """
        Markiert einen Job als abgeschlossen

        Args:
            schedule_id: ID des Zeitplans
        """
        self.scheduler.mark_job_running(schedule_id, False)
        logger.debug(f"Job {schedule_id} als abgeschlossen markiert")

    def reload_schedules(self, schedules: list) -> None:
        """
        Lädt Zeitpläne neu in den Scheduler

        Args:
            schedules: Liste von Schedule-Objekten
        """
        logger.info(f"Lade {len(schedules)} Zeitpläne neu...")

        # Lösche alle vorhandenen Jobs
        self.scheduler.jobs.clear()

        # Füge neue hinzu
        for schedule in schedules:
            if schedule.enabled:
                self.scheduler.add_schedule(schedule)

        logger.info(f"{len(self.scheduler.jobs)} aktive Zeitpläne geladen")
