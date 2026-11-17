"""
Nachholen fehlgeschlagener automatischer Backups

Schlägt ein geplantes Backup fehl (z.B. externe Festplatte nicht angeschlossen),
wird das Profil als "nachzuholen" markiert. Ein zusätzlicher OS-Task
(AutoBackupRetry_<profile_id>) läuft täglich zur selben Uhrzeit und versucht das
Backup erneut – so lange, bis es erfolgreich war.

Regeln:
- Nachgeholt wird nur an Tagen, an denen KEIN regulärer Termin liegt
  (Überschneidung → der reguläre Termin übernimmt).
- Tägliche Zeitpläne brauchen keinen Nachhol-Task: der nächste Versuch wäre
  immer zugleich der nächste reguläre Termin.
- Jedes erfolgreiche Backup des Profils löscht die Markierung.

Der Zustand liegt in einer eigenen Datei (retry_state.json), damit der
Headless-Prozess nicht in die von der GUI bearbeitete config.json schreibt.
"""

import json
import logging
import threading
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

RETRY_TASK_PREFIX = "AutoBackupRetry_"

_lock = threading.Lock()


def retry_task_name(profile_id: str) -> str:
    """Name des OS-Tasks für das Nachholen eines Profils"""
    return f"{RETRY_TASK_PREFIX}{profile_id}"


def _state_file() -> Path:
    from src.utils.paths import get_app_data_dir

    return get_app_data_dir() / "retry_state.json"


def _load(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except (OSError, ValueError) as e:
        logger.warning(f"Nachhol-Status nicht lesbar ({path}): {e} – starte leer")
        return {}


def _save(path: Path, state: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(path)


def mark_failed(profile_id: str, reason: str = "", state_file: Optional[Path] = None) -> None:
    """Markiert ein Profil als nachzuholen (erster Fehlschlag bleibt als Zeitpunkt erhalten)"""
    path = state_file or _state_file()
    with _lock:
        state = _load(path)
        entry = state.get(profile_id) or {"first_failed": datetime.now().isoformat(timespec="seconds")}
        entry["last_failed"] = datetime.now().isoformat(timespec="seconds")
        entry["reason"] = reason
        state[profile_id] = entry
        _save(path, state)
    logger.info(f"Profil '{profile_id}' zum Nachholen vorgemerkt ({reason})")


def clear(profile_id: str, state_file: Optional[Path] = None) -> None:
    """Entfernt die Nachhol-Markierung eines Profils"""
    path = state_file or _state_file()
    with _lock:
        state = _load(path)
        if profile_id in state:
            del state[profile_id]
            _save(path, state)
            logger.info(f"Nachhol-Markierung für Profil '{profile_id}' entfernt")


def is_pending(profile_id: str, state_file: Optional[Path] = None) -> bool:
    """True wenn für das Profil ein fehlgeschlagenes Backup nachzuholen ist"""
    path = state_file or _state_file()
    with _lock:
        return profile_id in _load(path)


def is_regular_day(schedule: Optional[dict], day: date) -> bool:
    """
    Prüft, ob an diesem Tag ein regulärer Backup-Termin liegt.

    "startup" und unbekannte Frequenzen gelten als regulär (→ kein Nachholen).
    """
    if not schedule:
        return True
    frequency = schedule.get("frequency", "daily")
    if frequency == "weekly":
        weekdays = schedule.get("weekdays") or [1]
        return day.isoweekday() in weekdays
    if frequency == "monthly":
        return day.day == int(schedule.get("day_of_month", 1))
    return True  # daily, startup, unbekannt


def needs_retry_task(schedule: Optional[dict]) -> bool:
    """
    True wenn für diesen Zeitplan ein täglicher Nachhol-Task sinnvoll ist.

    Nur bei wöchentlich (nicht an allen 7 Tagen) und monatlich – sonst fällt der
    Nachholtermin immer mit einem regulären Termin zusammen.
    """
    if not schedule or not schedule.get("enabled", True):
        return False
    frequency = schedule.get("frequency")
    if frequency == "monthly":
        return True
    if frequency == "weekly":
        weekdays = set(schedule.get("weekdays") or [1])
        return not {1, 2, 3, 4, 5, 6, 7}.issubset(weekdays)
    return False


def retry_hint(schedule: Optional[dict], today: Optional[date] = None) -> str:
    """
    Text für die Fehler-Benachrichtigung: wann der nächste Versuch stattfindet.
    """
    today = today or date.today()
    if (schedule or {}).get("frequency") == "startup":
        return "Neuer Versuch beim nächsten Systemstart."
    time_str = (schedule or {}).get("time", "")
    at = f" um {time_str}" if time_str else ""
    tomorrow = today + timedelta(days=1)
    if needs_retry_task(schedule) and not is_regular_day(schedule, tomorrow):
        return f"Neuer Versuch morgen{at}."
    return f"Neuer Versuch beim nächsten regulären Termin{at}."
