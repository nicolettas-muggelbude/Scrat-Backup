"""
Plattform-abstrahierte Scheduler-Integration
Unterstuetzt Windows Task Scheduler und Linux Cron
"""

import logging
import platform
import subprocess
import sys
from abc import ABC, abstractmethod
from typing import Optional

logger = logging.getLogger(__name__)


class PlatformScheduler(ABC):
    """Basis-Klasse fuer plattformspezifische Scheduler"""

    @abstractmethod
    def register_task(self, task_name: str, schedule: dict, command: str, args: list) -> bool:
        """
        Registriert einen geplanten Task.

        Args:
            task_name: Eindeutiger Name des Tasks
            schedule: Dict mit Zeitplan-Konfiguration:
                {
                    "frequency": "daily" | "weekly" | "monthly" | "startup",
                    "time": "HH:MM",          # fuer daily/weekly/monthly
                    "weekdays": [1..7],        # fuer weekly (1=Mo, 7=So)
                    "day_of_month": 1..28      # fuer monthly
                }
            command: Auszufuehrender Befehl (Pfad zur EXE / Python-Skript)
            args: Argumente fuer den Befehl
        """
        pass

    @abstractmethod
    def unregister_task(self, task_name: str) -> bool:
        """Entfernt einen geplanten Task"""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Prueft ob Scheduler verfuegbar ist"""
        pass


class WindowsTaskScheduler(PlatformScheduler):
    """Windows Task Scheduler Integration via schtasks"""

    _WEEKDAY_MAP = {1: "MON", 2: "TUE", 3: "WED", 4: "THU", 5: "FRI", 6: "SAT", 7: "SUN"}

    def register_task(self, task_name: str, schedule: dict, command: str, args: list) -> bool:
        """Registriert Windows Task mit schtasks"""
        try:
            frequency = schedule.get("frequency", "daily")
            time_str = schedule.get("time", "03:00")
            weekdays = schedule.get("weekdays", [1, 2, 3, 4, 5])
            day_of_month = schedule.get("day_of_month", 1)

            full_command = f'"{command}" {" ".join(args)}' if args else f'"{command}"'
            task_path = f"ScratBackup\\{task_name}"

            cmd = [
                "schtasks", "/create",
                "/tn", task_path,
                "/tr", full_command,
                "/f",  # Ueberschreiben falls schon vorhanden
            ]

            if frequency == "startup":
                cmd += ["/sc", "ONSTART"]

            elif frequency == "daily":
                cmd += ["/sc", "DAILY", "/st", time_str]

            elif frequency == "weekly":
                days_str = ",".join(
                    self._WEEKDAY_MAP[d] for d in sorted(weekdays) if d in self._WEEKDAY_MAP
                ) or "MON"
                cmd += ["/sc", "WEEKLY", "/d", days_str, "/st", time_str]

            elif frequency == "monthly":
                cmd += ["/sc", "MONTHLY", "/d", str(day_of_month), "/st", time_str]

            else:
                logger.error(f"Unbekannte Frequenz: {frequency}")
                return False

            subprocess.run(cmd, check=True, capture_output=True, text=True)
            logger.info(f"Windows Task '{task_name}' registriert ({frequency})")
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Fehler beim Registrieren von Windows Task: {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"Fehler beim Registrieren von Windows Task: {e}")
            return False

    def unregister_task(self, task_name: str) -> bool:
        """Entfernt Windows Task"""
        try:
            cmd = ["schtasks", "/delete", "/tn", f"ScratBackup\\{task_name}", "/f"]
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            logger.info(f"Windows Task '{task_name}' entfernt")
            return True
        except subprocess.CalledProcessError as e:
            if "cannot find" in e.stderr.lower() or "nicht gefunden" in e.stderr.lower():
                return True
            logger.warning(f"Fehler beim Entfernen von Windows Task: {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"Fehler beim Entfernen von Windows Task: {e}")
            return False

    def is_available(self) -> bool:
        return sys.platform == "win32"


class LinuxCronScheduler(PlatformScheduler):
    """Linux Cron Integration via crontab"""

    def __init__(self):
        self.cron_comment = "# Scrat-Backup:"

    def register_task(self, task_name: str, schedule: dict, command: str, args: list) -> bool:
        """Registriert Cron-Job"""
        try:
            frequency = schedule.get("frequency", "daily")
            time_str = schedule.get("time", "03:00")
            weekdays = schedule.get("weekdays", [1, 2, 3, 4, 5])
            day_of_month = schedule.get("day_of_month", 1)

            full_command = f"{command} {' '.join(args)}" if args else command

            # Cron-Zeitausdruck aufbauen
            if frequency == "startup":
                cron_time = "@reboot"

            elif frequency == "daily":
                hour, minute = time_str.split(":")
                cron_time = f"{minute} {hour} * * *"

            elif frequency == "weekly":
                hour, minute = time_str.split(":")
                # cron: 0=So, 1=Mo ... 6=Sa; unsere: 1=Mo ... 7=So
                dow_map = {1: "1", 2: "2", 3: "3", 4: "4", 5: "5", 6: "6", 7: "0"}
                dow_str = ",".join(dow_map[d] for d in sorted(weekdays) if d in dow_map) or "1"
                cron_time = f"{minute} {hour} * * {dow_str}"

            elif frequency == "monthly":
                hour, minute = time_str.split(":")
                cron_time = f"{minute} {hour} {day_of_month} * *"

            else:
                logger.error(f"Unbekannte Frequenz fuer Cron: {frequency}")
                return False

            cron_line = f"{cron_time} {full_command} {self.cron_comment} {task_name}"

            # Aktuelle crontab laden, alten Eintrag entfernen, neu schreiben
            result = subprocess.run(
                ["crontab", "-l"], capture_output=True, text=True, check=False
            )
            current = result.stdout if result.returncode == 0 else ""
            lines = [
                line for line in current.split("\n")
                if f"{self.cron_comment} {task_name}" not in line
            ]
            lines.append(cron_line)

            process = subprocess.Popen(["crontab", "-"], stdin=subprocess.PIPE, text=True)
            process.communicate(input="\n".join(lines) + "\n")

            if process.returncode == 0:
                logger.info(f"Cron-Job '{task_name}' registriert ({frequency}): {cron_time}")
                return True
            else:
                logger.error("Fehler beim Schreiben der crontab")
                return False

        except Exception as e:
            logger.error(f"Fehler beim Registrieren von Cron-Job: {e}")
            return False

    def unregister_task(self, task_name: str) -> bool:
        """Entfernt Cron-Job"""
        try:
            result = subprocess.run(["crontab", "-l"], capture_output=True, text=True, check=False)
            if result.returncode != 0:
                return True

            lines = [
                line for line in result.stdout.split("\n")
                if f"{self.cron_comment} {task_name}" not in line
            ]
            process = subprocess.Popen(["crontab", "-"], stdin=subprocess.PIPE, text=True)
            process.communicate(input="\n".join(lines) + "\n")
            logger.info(f"Cron-Job '{task_name}' entfernt")
            return True
        except Exception as e:
            logger.error(f"Fehler beim Entfernen von Cron-Job: {e}")
            return False

    def is_available(self) -> bool:
        if sys.platform != "linux":
            return False
        try:
            subprocess.run(["which", "crontab"], check=True, capture_output=True, text=True)
            return True
        except subprocess.CalledProcessError:
            return False


class MacOSLaunchdScheduler(PlatformScheduler):
    """macOS launchd Integration (Placeholder)"""

    def register_task(self, task_name: str, schedule: dict, command: str, args: list) -> bool:
        logger.warning("macOS-Scheduler noch nicht implementiert")
        return False

    def unregister_task(self, task_name: str) -> bool:
        return False

    def is_available(self) -> bool:
        return sys.platform == "darwin"


def get_platform_scheduler() -> Optional[PlatformScheduler]:
    """
    Factory-Funktion: Gibt passenden Scheduler fuer aktuelle Plattform zurueck

    Returns:
        PlatformScheduler-Instanz oder None
    """
    system = platform.system()

    if system == "Windows":
        scheduler = WindowsTaskScheduler()
    elif system == "Linux":
        scheduler = LinuxCronScheduler()
    elif system == "Darwin":
        scheduler = MacOSLaunchdScheduler()
    else:
        logger.warning(f"Unbekannte Plattform: {system}")
        return None

    if scheduler.is_available():
        return scheduler

    logger.warning(f"Scheduler fuer {system} nicht verfuegbar")
    return None
