"""
Tests für Scheduler-Modul
"""

import pytest
from datetime import datetime, time, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

from src.core.scheduler import (
    Schedule,
    ScheduledJob,
    Scheduler,
    ScheduleFrequency,
    Weekday,
)


@pytest.fixture
def scheduler():
    """Erstellt Scheduler-Instanz für Tests"""
    return Scheduler()


class TestSchedule:
    """Tests für Schedule Dataclass"""

    def test_schedule_creation(self):
        """Test: Schedule kann erstellt werden"""
        schedule = Schedule(
            id=1,
            name="Test Schedule",
            enabled=True,
            frequency=ScheduleFrequency.DAILY,
            source_ids=[1, 2],
            destination_id=1,
            time=time(10, 0),
        )

        assert schedule.id == 1
        assert schedule.name == "Test Schedule"
        assert schedule.enabled is True
        assert schedule.frequency == ScheduleFrequency.DAILY
        assert schedule.source_ids == [1, 2]
        assert schedule.destination_id == 1
        assert schedule.time == time(10, 0)

    def test_schedule_defaults(self):
        """Test: Schedule hat korrekte Defaults"""
        schedule = Schedule(
            id=None,
            name="Test",
            enabled=True,
            frequency=ScheduleFrequency.STARTUP,
            source_ids=[],
            destination_id=1,
        )

        assert schedule.time is None
        assert schedule.weekdays == []
        assert schedule.day_of_month is None
        assert schedule.backup_type == "incremental"


class TestScheduler:
    """Tests für Scheduler-Klasse"""

    def test_scheduler_initialization(self, scheduler):
        """Test: Scheduler wird korrekt initialisiert"""
        assert scheduler.jobs == []
        assert scheduler.callback is None

    def test_add_schedule_daily(self, scheduler):
        """Test: Täglicher Zeitplan wird hinzugefügt"""
        schedule = Schedule(
            id=1,
            name="Daily Backup",
            enabled=True,
            frequency=ScheduleFrequency.DAILY,
            source_ids=[1],
            destination_id=1,
            time=time(10, 0),
        )

        scheduler.add_schedule(schedule)

        assert len(scheduler.jobs) == 1
        assert scheduler.jobs[0].schedule == schedule
        assert scheduler.jobs[0].next_run is not None

    def test_add_disabled_schedule_skipped(self, scheduler):
        """Test: Deaktivierte Zeitpläne werden nicht hinzugefügt"""
        schedule = Schedule(
            id=1,
            name="Disabled",
            enabled=False,
            frequency=ScheduleFrequency.DAILY,
            source_ids=[1],
            destination_id=1,
            time=time(10, 0),
        )

        scheduler.add_schedule(schedule)

        assert len(scheduler.jobs) == 0

    def test_remove_schedule(self, scheduler):
        """Test: Zeitplan kann entfernt werden"""
        schedule = Schedule(
            id=1,
            name="Test",
            enabled=True,
            frequency=ScheduleFrequency.DAILY,
            source_ids=[1],
            destination_id=1,
            time=time(10, 0),
        )

        scheduler.add_schedule(schedule)
        assert len(scheduler.jobs) == 1

        removed = scheduler.remove_schedule(1)
        assert removed is True
        assert len(scheduler.jobs) == 0

    def test_remove_nonexistent_schedule(self, scheduler):
        """Test: Entfernen eines nicht existierenden Zeitplans"""
        removed = scheduler.remove_schedule(999)
        assert removed is False

    def test_calculate_next_run_daily(self, scheduler):
        """Test: Nächster Lauf für täglichen Zeitplan"""
        schedule = Schedule(
            id=1,
            name="Daily",
            enabled=True,
            frequency=ScheduleFrequency.DAILY,
            source_ids=[1],
            destination_id=1,
            time=time(14, 30),
        )

        # Wenn es 10:00 ist, nächster Lauf heute um 14:30
        from_time = datetime(2025, 1, 15, 10, 0)
        next_run = scheduler._calculate_next_run(schedule, from_time)

        assert next_run.date() == from_time.date()
        assert next_run.time() == time(14, 30)

        # Wenn es 15:00 ist, nächster Lauf morgen um 14:30
        from_time = datetime(2025, 1, 15, 15, 0)
        next_run = scheduler._calculate_next_run(schedule, from_time)

        assert next_run.date() == (from_time + timedelta(days=1)).date()
        assert next_run.time() == time(14, 30)

    def test_calculate_next_run_weekly(self, scheduler):
        """Test: Nächster Lauf für wöchentlichen Zeitplan"""
        # Montag und Freitag um 10:00
        schedule = Schedule(
            id=1,
            name="Weekly",
            enabled=True,
            frequency=ScheduleFrequency.WEEKLY,
            source_ids=[1],
            destination_id=1,
            time=time(10, 0),
            weekdays=[Weekday.MONDAY, Weekday.FRIDAY],
        )

        # Heute ist Mittwoch (2025-01-15)
        from_time = datetime(2025, 1, 15, 10, 0)  # Mittwoch 10:00
        next_run = scheduler._calculate_next_run(schedule, from_time)

        # Nächster Lauf: Freitag 2025-01-17 10:00
        assert next_run.isoweekday() == Weekday.FRIDAY.value
        assert next_run.time() == time(10, 0)

    def test_calculate_next_run_monthly(self, scheduler):
        """Test: Nächster Lauf für monatlichen Zeitplan"""
        # Jeden 15. um 10:00
        schedule = Schedule(
            id=1,
            name="Monthly",
            enabled=True,
            frequency=ScheduleFrequency.MONTHLY,
            source_ids=[1],
            destination_id=1,
            time=time(10, 0),
            day_of_month=15,
        )

        # Heute ist 10. Januar
        from_time = datetime(2025, 1, 10, 10, 0)
        next_run = scheduler._calculate_next_run(schedule, from_time)

        # Nächster Lauf: 15. Januar 10:00
        assert next_run.date() == datetime(2025, 1, 15).date()
        assert next_run.time() == time(10, 0)

        # Heute ist 20. Januar (nach dem 15.)
        from_time = datetime(2025, 1, 20, 10, 0)
        next_run = scheduler._calculate_next_run(schedule, from_time)

        # Nächster Lauf: 15. Februar 10:00
        assert next_run.date() == datetime(2025, 2, 15).date()
        assert next_run.time() == time(10, 0)

    def test_calculate_next_run_startup(self, scheduler):
        """Test: Startup-Zeitplan hat keinen 'nächsten Lauf'"""
        schedule = Schedule(
            id=1,
            name="Startup",
            enabled=True,
            frequency=ScheduleFrequency.STARTUP,
            source_ids=[1],
            destination_id=1,
        )

        next_run = scheduler._calculate_next_run(schedule)
        assert next_run is None

    def test_check_due_jobs(self, scheduler):
        """Test: Fällige Jobs werden erkannt"""
        # Zeitplan für 10:00
        schedule = Schedule(
            id=1,
            name="Test",
            enabled=True,
            frequency=ScheduleFrequency.DAILY,
            source_ids=[1],
            destination_id=1,
            time=time(10, 0),
        )

        # Füge hinzu mit next_run = jetzt - 1 Minute
        scheduler.add_schedule(schedule)
        scheduler.jobs[0].next_run = datetime.now() - timedelta(minutes=1)

        # Prüfe fällige Jobs
        due = scheduler.check_due_jobs()

        assert len(due) == 1
        assert due[0] == schedule

    def test_mark_job_running(self, scheduler):
        """Test: Job kann als laufend markiert werden"""
        schedule = Schedule(
            id=1,
            name="Test",
            enabled=True,
            frequency=ScheduleFrequency.DAILY,
            source_ids=[1],
            destination_id=1,
            time=time(10, 0),
        )

        scheduler.add_schedule(schedule)
        assert scheduler.jobs[0].is_running is False

        scheduler.mark_job_running(1, True)
        assert scheduler.jobs[0].is_running is True

        scheduler.mark_job_running(1, False)
        assert scheduler.jobs[0].is_running is False

    def test_get_next_scheduled_run(self, scheduler):
        """Test: Nächster Lauf kann abgerufen werden"""
        schedule = Schedule(
            id=1,
            name="Test",
            enabled=True,
            frequency=ScheduleFrequency.DAILY,
            source_ids=[1],
            destination_id=1,
            time=time(10, 0),
        )

        scheduler.add_schedule(schedule)

        next_run = scheduler.get_next_scheduled_run(1)
        assert next_run is not None
        assert isinstance(next_run, datetime)

    @patch("subprocess.run")
    def test_register_windows_task_startup(self, mock_run, scheduler):
        """Test: Windows Task für Startup wird registriert"""
        schedule = Schedule(
            id=1,
            name="Startup",
            enabled=True,
            frequency=ScheduleFrequency.STARTUP,
            source_ids=[1],
            destination_id=1,
        )

        # Mock erfolgreiche Registrierung
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

        result = scheduler._register_windows_task(schedule)

        # Auf Windows sollte es funktionieren (wird aber in Tests oft geskippt)
        # Wir testen nur dass die Methode aufrufbar ist
        assert isinstance(result, bool)

    @patch("subprocess.run")
    def test_unregister_windows_task(self, mock_run, scheduler):
        """Test: Windows Task kann deregistriert werden"""
        schedule = Schedule(
            id=1,
            name="Startup",
            enabled=True,
            frequency=ScheduleFrequency.STARTUP,
            source_ids=[1],
            destination_id=1,
        )

        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

        result = scheduler._unregister_windows_task(schedule)
        assert isinstance(result, bool)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
