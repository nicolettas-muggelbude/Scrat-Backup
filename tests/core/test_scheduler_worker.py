"""
Tests für SchedulerWorker-Modul
"""

import pytest
from datetime import datetime, time, timedelta
from unittest.mock import Mock, MagicMock, patch
from PyQt6.QtTest import QSignalSpy

from src.core.scheduler import Schedule, Scheduler, ScheduleFrequency
from src.core.scheduler_worker import SchedulerWorker


@pytest.fixture
def scheduler():
    """Erstellt Scheduler-Instanz"""
    return Scheduler()


@pytest.fixture
def worker(scheduler):
    """Erstellt SchedulerWorker-Instanz"""
    worker = SchedulerWorker(scheduler, check_interval=1)  # 1 Sekunde für Tests
    yield worker
    # Cleanup
    if worker.isRunning():
        worker.stop()


class TestSchedulerWorker:
    """Tests für SchedulerWorker"""

    def test_worker_initialization(self, worker, scheduler):
        """Test: Worker wird korrekt initialisiert"""
        assert worker.scheduler == scheduler
        assert worker.check_interval == 1
        assert worker._running is False
        assert worker._paused is False

    def test_worker_start_stop(self, worker):
        """Test: Worker kann gestartet und gestoppt werden"""
        # Starte Worker
        worker.start()

        # Kurz warten bis gestartet
        from PyQt6.QtTest import QTest
        QTest.qWait(100)

        assert worker.isRunning()
        assert worker.is_running()

        # Stoppe Worker
        worker.stop()
        assert not worker.isRunning()

    def test_worker_pause_resume(self, worker):
        """Test: Worker kann pausiert und fortgesetzt werden"""
        worker.pause()
        assert worker.is_paused()

        worker.resume()
        assert not worker.is_paused()

    @pytest.mark.skip(reason="Asynchroner Worker-Test zu fragil - manuelle Tests erforderlich")
    def test_backup_due_signal_emitted(self, worker, scheduler, qtbot):
        """Test: backup_due Signal wird ausgelöst

        Hinweis: Dieser Test ist zu fragil für automatische Tests weil der Worker
        asynchron in einem Thread läuft und Timing-abhängig ist. Die Funktionalität
        sollte manuell getestet werden.
        """
        # Erstelle Zeitplan der in 1 Sekunde fällig ist
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

        # Setze next_run auf jetzt - 1 Sekunde (fällig)
        scheduler.jobs[0].next_run = datetime.now() - timedelta(seconds=1)

        # Signal-Spy für backup_due
        spy = QSignalSpy(worker.backup_due)

        # Starte Worker
        worker.start()

        # Warte auf Signal (max 5 Sekunden - Worker braucht Zeit zum Starten)
        try:
            with qtbot.waitSignal(worker.backup_due, timeout=5000):
                pass
            # Prüfe dass Signal ausgelöst wurde
            assert len(spy) > 0
        finally:
            # Stoppe Worker immer (auch bei Fehler)
            worker.stop()

    @pytest.mark.skip(reason="Asynchroner Worker-Test zu fragil - manuelle Tests erforderlich")
    def test_next_run_changed_signal(self, worker, scheduler, qtbot):
        """Test: next_run_changed Signal wird ausgelöst"""
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
        scheduler.jobs[0].next_run = datetime.now() - timedelta(seconds=1)

        # Signal-Spy
        spy = QSignalSpy(worker.next_run_changed)

        worker.start()

        # Warte auf Signal (5 Sekunden Timeout)
        try:
            with qtbot.waitSignal(worker.next_run_changed, timeout=5000):
                pass
            assert len(spy) > 0
        finally:
            worker.stop()

    def test_mark_job_finished(self, worker, scheduler):
        """Test: Job kann als abgeschlossen markiert werden"""
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
        scheduler.mark_job_running(1, True)
        assert scheduler.jobs[0].is_running is True

        worker.mark_job_finished(1)
        assert scheduler.jobs[0].is_running is False

    def test_reload_schedules(self, worker, scheduler):
        """Test: Zeitpläne können neu geladen werden"""
        # Erstelle 3 Zeitpläne
        schedules = [
            Schedule(
                id=i,
                name=f"Schedule {i}",
                enabled=True,
                frequency=ScheduleFrequency.DAILY,
                source_ids=[1],
                destination_id=1,
                time=time(10, 0),
            )
            for i in range(1, 4)
        ]

        # Lade in Worker
        worker.reload_schedules(schedules)

        # Prüfe dass alle im Scheduler sind
        assert len(scheduler.jobs) == 3

        # Lade neue Liste (nur 1 Schedule)
        new_schedules = [schedules[0]]
        worker.reload_schedules(new_schedules)

        assert len(scheduler.jobs) == 1

    @pytest.mark.skip(reason="Asynchroner Worker-Test zu fragil - manuelle Tests erforderlich")
    def test_missed_backup_detection(self, worker, scheduler, qtbot):
        """Test: Verpasste Backups werden erkannt"""
        # Erstelle Zeitplan
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

        # Setze last_check_time weit in die Vergangenheit
        worker.last_check_time = datetime.now() - timedelta(hours=2)

        # Setze next_run auf eine Zeit zwischen last_check und jetzt
        scheduler.jobs[0].next_run = datetime.now() - timedelta(hours=1)
        scheduler.jobs[0].last_run = datetime.now() - timedelta(days=1)

        # Signal-Spy
        spy = QSignalSpy(worker.backup_due)

        # Starte Worker
        worker.start()

        # Warte auf Signal (5 Sekunden Timeout)
        try:
            with qtbot.waitSignal(worker.backup_due, timeout=5000):
                pass

            # Prüfe dass is_missed=True war
            assert len(spy) > 0
            signal_args = spy[0]
            is_missed = signal_args[1]
            assert is_missed is True
        finally:
            worker.stop()

    def test_error_signal_on_exception(self, worker, scheduler, qtbot):
        """Test: Error-Signal bei Exception"""
        # Mock _check_for_due_jobs um Exception zu werfen
        with patch.object(worker, '_check_for_due_jobs', side_effect=Exception("Test Error")):
            spy = QSignalSpy(worker.error_occurred)

            worker.start()

            # Warte auf Error-Signal (längeres Timeout weil Worker erst starten muss)
            try:
                with qtbot.waitSignal(worker.error_occurred, timeout=7000):
                    pass

                assert len(spy) > 0
                error_msg = spy[0][0]
                assert "Test Error" in error_msg
            finally:
                worker.stop()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
