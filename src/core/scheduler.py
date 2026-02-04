"""
Scheduler für Scrat-Backup
Verwaltet automatische Backups basierend auf Zeitplänen
"""

import logging
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, time, timedelta
from enum import Enum
from pathlib import Path
from typing import Callable, List, Optional

logger = logging.getLogger(__name__)


class ScheduleFrequency(Enum):
    """Zeitplan-Häufigkeiten"""

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    STARTUP = "startup"
    SHUTDOWN = "shutdown"


class Weekday(Enum):
    """Wochentage"""

    MONDAY = 1
    TUESDAY = 2
    WEDNESDAY = 3
    THURSDAY = 4
    FRIDAY = 5
    SATURDAY = 6
    SUNDAY = 7


@dataclass
class Schedule:
    """
    Zeitplan-Konfiguration

    Attributes:
        id: Eindeutige ID (aus Datenbank)
        name: Name des Zeitplans
        enabled: Ist der Zeitplan aktiv?
        frequency: Häufigkeit (daily, weekly, monthly, startup, shutdown)
        time: Uhrzeit (HH:MM) für tägliche/wöchentliche/monatliche Backups
        weekdays: Liste von Wochentagen (nur bei weekly)
        day_of_month: Tag im Monat (1-31, nur bei monthly)
        source_ids: Liste der Quellen-IDs
        destination_id: Ziel-ID
        backup_type: Typ des Backups (full oder incremental)
    """

    id: Optional[int]
    name: str
    enabled: bool
    frequency: ScheduleFrequency
    source_ids: List[int]
    destination_id: int
    time: Optional[time] = None
    weekdays: List[Weekday] = field(default_factory=list)
    day_of_month: Optional[int] = None
    backup_type: str = "incremental"  # full oder incremental


@dataclass
class ScheduledJob:
    """
    Ein geplanter Job

    Attributes:
        schedule: Der Zeitplan
        next_run: Nächster geplanter Lauf
        last_run: Letzter Lauf (oder None)
        is_running: Läuft gerade?
    """

    schedule: Schedule
    next_run: Optional[datetime] = None
    last_run: Optional[datetime] = None
    is_running: bool = False


class Scheduler:
    """
    Scheduler für automatische Backups

    Verwaltet Zeitpläne und triggert Backups zur richtigen Zeit.
    Integriert mit Windows Task Scheduler für System-Events (Startup/Shutdown).
    """

    def __init__(self, callback: Optional[Callable[[Schedule], None]] = None):
        """
        Initialisiert Scheduler

        Args:
            callback: Callback-Funktion die aufgerufen wird wenn ein Backup gestartet werden soll
                     Signatur: callback(schedule: Schedule) -> None
        """
        self.callback = callback
        self.jobs: List[ScheduledJob] = []

        logger.info("Scheduler initialisiert")

    def add_schedule(self, schedule: Schedule) -> None:
        """
        Fügt einen Zeitplan hinzu

        Args:
            schedule: Der Zeitplan
        """
        if not schedule.enabled:
            logger.info(f"Zeitplan '{schedule.name}' ist deaktiviert, wird nicht hinzugefügt")
            return

        # Erstelle Job
        job = ScheduledJob(schedule=schedule)

        # Berechne nächsten Lauf
        job.next_run = self._calculate_next_run(schedule)

        self.jobs.append(job)
        logger.info(f"Zeitplan '{schedule.name}' hinzugefügt, nächster Lauf: {job.next_run}")

        # Bei Startup/Shutdown: Registriere Windows Task
        if schedule.frequency in [ScheduleFrequency.STARTUP, ScheduleFrequency.SHUTDOWN]:
            self._register_windows_task(schedule)

    def remove_schedule(self, schedule_id: int) -> bool:
        """
        Entfernt einen Zeitplan

        Args:
            schedule_id: ID des Zeitplans

        Returns:
            True wenn entfernt, False wenn nicht gefunden
        """
        for job in self.jobs:
            if job.schedule.id == schedule_id:
                # Bei Startup/Shutdown: Deregistriere Windows Task
                if job.schedule.frequency in [
                    ScheduleFrequency.STARTUP,
                    ScheduleFrequency.SHUTDOWN,
                ]:
                    self._unregister_windows_task(job.schedule)

                self.jobs.remove(job)
                logger.info(f"Zeitplan '{job.schedule.name}' entfernt")
                return True

        return False

    def check_due_jobs(self) -> List[Schedule]:
        """
        Prüft welche Jobs fällig sind

        Returns:
            Liste von Zeitplänen deren Jobs jetzt ausgeführt werden sollen
        """
        now = datetime.now()
        due_schedules = []

        for job in self.jobs:
            # Skip wenn schon läuft
            if job.is_running:
                continue

            # Skip Startup/Shutdown (werden durch Windows Task Scheduler getriggert)
            if job.schedule.frequency in [ScheduleFrequency.STARTUP, ScheduleFrequency.SHUTDOWN]:
                continue

            # Prüfe ob fällig
            if job.next_run and now >= job.next_run:
                due_schedules.append(job.schedule)
                job.last_run = now
                job.next_run = self._calculate_next_run(job.schedule, from_time=now)
                logger.info(f"Job '{job.schedule.name}' ist fällig, nächster Lauf: {job.next_run}")

        return due_schedules

    def mark_job_running(self, schedule_id: int, running: bool) -> None:
        """
        Markiert einen Job als laufend oder fertig

        Args:
            schedule_id: ID des Zeitplans
            running: True = läuft, False = fertig
        """
        for job in self.jobs:
            if job.schedule.id == schedule_id:
                job.is_running = running
                break

    def get_next_scheduled_run(self, schedule_id: int) -> Optional[datetime]:
        """
        Holt den nächsten geplanten Lauf für einen Zeitplan

        Args:
            schedule_id: ID des Zeitplans

        Returns:
            Datetime des nächsten Laufs oder None
        """
        for job in self.jobs:
            if job.schedule.id == schedule_id:
                return job.next_run
        return None

    def _calculate_next_run(
        self, schedule: Schedule, from_time: Optional[datetime] = None
    ) -> Optional[datetime]:
        """
        Berechnet nächsten Ausführungszeitpunkt

        Args:
            schedule: Der Zeitplan
            from_time: Ab welchem Zeitpunkt berechnen (default: jetzt)

        Returns:
            Datetime des nächsten Laufs oder None (bei Startup/Shutdown)
        """
        if from_time is None:
            from_time = datetime.now()

        # Startup/Shutdown haben keinen "nächsten Lauf"
        if schedule.frequency in [ScheduleFrequency.STARTUP, ScheduleFrequency.SHUTDOWN]:
            return None

        # Tägliche Backups
        if schedule.frequency == ScheduleFrequency.DAILY:
            if schedule.time is None:
                logger.error(f"Zeitplan '{schedule.name}' hat keine Uhrzeit für daily")
                return None

            next_run = datetime.combine(from_time.date(), schedule.time)

            # Wenn heute schon vorbei, nimm morgen
            if next_run <= from_time:
                next_run += timedelta(days=1)

            return next_run

        # Wöchentliche Backups
        elif schedule.frequency == ScheduleFrequency.WEEKLY:
            if schedule.time is None or not schedule.weekdays:
                logger.error(
                    f"Zeitplan '{schedule.name}' hat keine Uhrzeit oder Wochentage für weekly"
                )
                return None

            # Finde nächsten passenden Wochentag
            current_weekday = from_time.isoweekday()
            weekday_numbers = sorted([wd.value for wd in schedule.weekdays])

            # Finde nächsten Wochentag
            next_weekday = None
            for wd in weekday_numbers:
                if wd > current_weekday:
                    next_weekday = wd
                    break

            # Wenn kein Wochentag diese Woche mehr, nimm ersten der nächsten Woche
            if next_weekday is None:
                next_weekday = weekday_numbers[0]
                days_ahead = (7 - current_weekday) + next_weekday
            else:
                days_ahead = next_weekday - current_weekday

            next_run = datetime.combine(from_time.date(), schedule.time) + timedelta(
                days=days_ahead
            )

            # Wenn heute der richtige Wochentag ist aber Zeit schon vorbei, nimm nächste Woche
            if days_ahead == 0 and next_run <= from_time:
                # Finde nächsten Wochentag (nächste Woche)
                idx = weekday_numbers.index(next_weekday)
                if idx + 1 < len(weekday_numbers):
                    next_weekday = weekday_numbers[idx + 1]
                    days_ahead = next_weekday - current_weekday
                else:
                    next_weekday = weekday_numbers[0]
                    days_ahead = (7 - current_weekday) + next_weekday

                next_run = datetime.combine(from_time.date(), schedule.time) + timedelta(
                    days=days_ahead
                )

            return next_run

        # Monatliche Backups
        elif schedule.frequency == ScheduleFrequency.MONTHLY:
            if schedule.time is None or schedule.day_of_month is None:
                logger.error(f"Zeitplan '{schedule.name}' hat keine Uhrzeit oder Tag für monthly")
                return None

            # Versuche diesen Monat
            try:
                next_run = datetime.combine(
                    from_time.date().replace(day=schedule.day_of_month), schedule.time
                )
            except ValueError:
                # Tag existiert nicht in diesem Monat (z.B. 31. Feb)
                next_run = None

            # Wenn nicht möglich oder schon vorbei, nimm nächsten Monat
            if next_run is None or next_run <= from_time:
                # Nächster Monat
                if from_time.month == 12:
                    next_month = from_time.replace(year=from_time.year + 1, month=1, day=1)
                else:
                    next_month = from_time.replace(month=from_time.month + 1, day=1)

                try:
                    next_run = datetime.combine(
                        next_month.date().replace(day=schedule.day_of_month), schedule.time
                    )
                except ValueError:
                    # Tag existiert auch im nächsten Monat nicht
                    logger.error(
                        f"Tag {schedule.day_of_month} existiert nicht im "
                        f"Monat {next_month.month}"
                    )
                    return None

            return next_run

        return None

    def _register_windows_task(self, schedule: Schedule) -> bool:
        """
        Registriert einen Windows Task Scheduler Task

        Args:
            schedule: Der Zeitplan

        Returns:
            True bei Erfolg
        """
        if sys.platform != "win32":
            logger.warning("Windows Task Scheduler nur unter Windows verfügbar")
            return False

        try:
            task_name = f"ScratBackup_{schedule.name}_{schedule.id}"

            # Python-Executable und Script-Pfad
            python_exe = sys.executable
            script_path = Path(__file__).parent.parent / "main.py"

            # Trigger basierend auf Frequenz
            if schedule.frequency == ScheduleFrequency.STARTUP:
                trigger = "/SC ONSTART"
            elif schedule.frequency == ScheduleFrequency.SHUTDOWN:
                trigger = "/SC ONLOGOFF"  # Closest to shutdown
            else:
                logger.error(f"Ungültige Frequenz für Windows Task: {schedule.frequency}")
                return False

            # Task erstellen
            cmd = [
                "schtasks",
                "/Create",
                "/TN",
                task_name,
                "/TR",
                f'"{python_exe}" "{script_path}" --schedule-id {schedule.id}',
                trigger,
                "/F",  # Force (überschreibe wenn existiert)
            ]

            subprocess.run(cmd, capture_output=True, text=True, check=True)
            logger.info(f"Windows Task '{task_name}' erfolgreich registriert")
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Fehler beim Registrieren von Windows Task: {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"Fehler beim Registrieren von Windows Task: {e}")
            return False

    def _unregister_windows_task(self, schedule: Schedule) -> bool:
        """
        Deregistriert einen Windows Task Scheduler Task

        Args:
            schedule: Der Zeitplan

        Returns:
            True bei Erfolg
        """
        if sys.platform != "win32":
            return True

        try:
            task_name = f"ScratBackup_{schedule.name}_{schedule.id}"

            cmd = ["schtasks", "/Delete", "/TN", task_name, "/F"]

            subprocess.run(cmd, capture_output=True, text=True, check=True)
            logger.info(f"Windows Task '{task_name}' erfolgreich entfernt")
            return True

        except subprocess.CalledProcessError as e:
            logger.warning(f"Fehler beim Entfernen von Windows Task: {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"Fehler beim Entfernen von Windows Task: {e}")
            return False
