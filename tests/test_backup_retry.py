"""
Unit-Tests für das Nachholen fehlgeschlagener Backups (src/core/backup_retry.py)
"""

from datetime import date

from src.core import backup_retry as br

# 2026-11-16 ist ein Montag
MONDAY = date(2026, 11, 16)
TUESDAY = date(2026, 11, 17)
SUNDAY = date(2026, 11, 22)

WEEKLY_MON = {"enabled": True, "frequency": "weekly", "time": "10:00", "weekdays": [1]}
MONTHLY_1 = {"enabled": True, "frequency": "monthly", "time": "09:30", "day_of_month": 1}
DAILY = {"enabled": True, "frequency": "daily", "time": "08:00"}


class TestState:
    def test_mark_and_clear(self, tmp_path):
        f = tmp_path / "retry_state.json"
        assert not br.is_pending("p1", f)

        br.mark_failed("p1", "USB nicht angeschlossen", f)
        assert br.is_pending("p1", f)
        assert not br.is_pending("p2", f)

        br.clear("p1", f)
        assert not br.is_pending("p1", f)

    def test_first_failed_is_kept(self, tmp_path):
        import json

        f = tmp_path / "retry_state.json"
        br.mark_failed("p1", "a", f)
        first = json.loads(f.read_text())["p1"]["first_failed"]
        br.mark_failed("p1", "b", f)
        data = json.loads(f.read_text())["p1"]
        assert data["first_failed"] == first
        assert data["reason"] == "b"

    def test_corrupt_file_is_ignored(self, tmp_path):
        f = tmp_path / "retry_state.json"
        f.write_text("{kaputt")
        assert not br.is_pending("p1", f)
        br.mark_failed("p1", "x", f)
        assert br.is_pending("p1", f)


class TestRegularDay:
    def test_weekly(self):
        assert br.is_regular_day(WEEKLY_MON, MONDAY)
        assert not br.is_regular_day(WEEKLY_MON, TUESDAY)

    def test_weekly_sunday_is_7(self):
        sched = {"frequency": "weekly", "weekdays": [7]}
        assert br.is_regular_day(sched, SUNDAY)
        assert not br.is_regular_day(sched, MONDAY)

    def test_monthly(self):
        assert br.is_regular_day(MONTHLY_1, date(2026, 12, 1))
        assert not br.is_regular_day(MONTHLY_1, date(2026, 12, 2))

    def test_daily_always_regular(self):
        assert br.is_regular_day(DAILY, TUESDAY)


class TestNeedsRetryTask:
    def test_weekly_and_monthly(self):
        assert br.needs_retry_task(WEEKLY_MON)
        assert br.needs_retry_task(MONTHLY_1)

    def test_daily_and_startup_not(self):
        assert not br.needs_retry_task(DAILY)
        assert not br.needs_retry_task({"enabled": True, "frequency": "startup"})

    def test_weekly_every_day_not(self):
        sched = {"enabled": True, "frequency": "weekly", "weekdays": [1, 2, 3, 4, 5, 6, 7]}
        assert not br.needs_retry_task(sched)

    def test_disabled_not(self):
        assert not br.needs_retry_task({**WEEKLY_MON, "enabled": False})
        assert not br.needs_retry_task(None)


class TestRetryHint:
    def test_weekly_next_day_free(self):
        assert br.retry_hint(WEEKLY_MON, MONDAY) == "Neuer Versuch morgen um 10:00."

    def test_weekly_next_day_is_regular(self):
        sched = {**WEEKLY_MON, "weekdays": [1, 2]}
        assert "nächsten regulären Termin" in br.retry_hint(sched, MONDAY)

    def test_daily(self):
        assert "nächsten regulären Termin um 08:00" in br.retry_hint(DAILY, MONDAY)

    def test_startup(self):
        assert "Systemstart" in br.retry_hint({"frequency": "startup"}, MONDAY)
