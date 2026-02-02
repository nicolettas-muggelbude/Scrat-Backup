"""
Plattform-abstrahierte Scheduler-Integration
Unterstützt Windows Task Scheduler und Linux Cron
"""

import logging
import platform
import subprocess
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class PlatformScheduler(ABC):
    """Basis-Klasse für plattformspezifische Scheduler"""

    @abstractmethod
    def register_task(
        self, task_name: str, frequency: str, command: str, args: list[str]
    ) -> bool:
        """Registriert einen geplanten Task"""
        pass

    @abstractmethod
    def unregister_task(self, task_name: str) -> bool:
        """Entfernt einen geplanten Task"""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Prüft ob Scheduler verfügbar ist"""
        pass


class WindowsTaskScheduler(PlatformScheduler):
    """Windows Task Scheduler Integration"""

    def register_task(
        self, task_name: str, frequency: str, command: str, args: list[str]
    ) -> bool:
        """Registriert Windows Task mit schtasks"""
        try:
            # Trigger mapping
            trigger_map = {"startup": "ONSTART", "shutdown": "ONLOGOFF"}

            trigger = trigger_map.get(frequency)
            if not trigger:
                logger.error(f"Ungültige Frequenz für Windows Task: {frequency}")
                return False

            # Baue Command
            full_command = f"{command} {' '.join(args)}"

            # schtasks /create
            cmd = [
                "schtasks",
                "/create",
                "/tn",
                f"ScratBackup\\{task_name}",
                "/tr",
                full_command,
                "/sc",
                trigger,
                "/f",  # Force (überschreibe falls existiert)
            ]

            subprocess.run(cmd, check=True, capture_output=True, text=True)
            logger.info(f"Windows Task '{task_name}' erfolgreich registriert")
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
            logger.info(f"Windows Task '{task_name}' erfolgreich entfernt")
            return True

        except subprocess.CalledProcessError as e:
            if "ERROR: The system cannot find the file specified" in e.stderr:
                logger.warning(f"Windows Task '{task_name}' existiert nicht")
                return True
            logger.warning(f"Fehler beim Entfernen von Windows Task: {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"Fehler beim Entfernen von Windows Task: {e}")
            return False

    def is_available(self) -> bool:
        """Prüft ob Windows Task Scheduler verfügbar ist"""
        return sys.platform == "win32"


class LinuxCronScheduler(PlatformScheduler):
    """Linux Cron Integration via crontab"""

    def __init__(self):
        self.cron_comment = "# Scrat-Backup:"

    def register_task(
        self, task_name: str, frequency: str, command: str, args: list[str]
    ) -> bool:
        """Registriert Cron-Job"""
        try:
            # Trigger mapping
            if frequency == "startup":
                # @reboot in crontab
                cron_time = "@reboot"
            elif frequency == "shutdown":
                # Linux hat kein natives Shutdown-Event in cron
                # Workaround: systemd service
                logger.warning(
                    "Shutdown-Events benötigen systemd service unter Linux. "
                    "Cron unterstützt nur @reboot."
                )
                return False
            else:
                logger.error(f"Ungültige Frequenz für Cron: {frequency}")
                return False

            # Baue Cron-Zeile
            full_command = f"{command} {' '.join(args)}"
            cron_line = f"{cron_time} {full_command} {self.cron_comment} {task_name}"

            # Hole aktuelle crontab
            try:
                result = subprocess.run(
                    ["crontab", "-l"], capture_output=True, text=True, check=False
                )
                current_crontab = result.stdout if result.returncode == 0 else ""
            except Exception:
                current_crontab = ""

            # Entferne alte Version falls vorhanden
            lines = [
                line
                for line in current_crontab.split("\n")
                if f"{self.cron_comment} {task_name}" not in line
            ]

            # Füge neue Zeile hinzu
            lines.append(cron_line)

            # Schreibe crontab
            new_crontab = "\n".join(lines)
            process = subprocess.Popen(["crontab", "-"], stdin=subprocess.PIPE, text=True)
            process.communicate(input=new_crontab)

            if process.returncode == 0:
                logger.info(f"Cron-Job '{task_name}' erfolgreich registriert")
                return True
            else:
                logger.error(f"Fehler beim Schreiben der crontab")
                return False

        except Exception as e:
            logger.error(f"Fehler beim Registrieren von Cron-Job: {e}")
            return False

    def unregister_task(self, task_name: str) -> bool:
        """Entfernt Cron-Job"""
        try:
            # Hole aktuelle crontab
            result = subprocess.run(
                ["crontab", "-l"], capture_output=True, text=True, check=False
            )
            if result.returncode != 0:
                logger.warning("Keine crontab gefunden")
                return True

            # Filtere Zeile raus
            lines = [
                line
                for line in result.stdout.split("\n")
                if f"{self.cron_comment} {task_name}" not in line
            ]

            # Schreibe crontab
            new_crontab = "\n".join(lines)
            process = subprocess.Popen(["crontab", "-"], stdin=subprocess.PIPE, text=True)
            process.communicate(input=new_crontab)

            if process.returncode == 0:
                logger.info(f"Cron-Job '{task_name}' erfolgreich entfernt")
                return True
            else:
                logger.error(f"Fehler beim Schreiben der crontab")
                return False

        except Exception as e:
            logger.error(f"Fehler beim Entfernen von Cron-Job: {e}")
            return False

    def is_available(self) -> bool:
        """Prüft ob crontab verfügbar ist"""
        if sys.platform != "linux":
            return False

        try:
            subprocess.run(
                ["which", "crontab"], check=True, capture_output=True, text=True
            )
            return True
        except subprocess.CalledProcessError:
            return False


class MacOSLaunchdScheduler(PlatformScheduler):
    """macOS launchd Integration (Placeholder)"""

    def register_task(
        self, task_name: str, frequency: str, command: str, args: list[str]
    ) -> bool:
        logger.warning("macOS launchd-Integration noch nicht implementiert")
        return False

    def unregister_task(self, task_name: str) -> bool:
        logger.warning("macOS launchd-Integration noch nicht implementiert")
        return False

    def is_available(self) -> bool:
        return sys.platform == "darwin"


def get_platform_scheduler() -> Optional[PlatformScheduler]:
    """
    Factory-Funktion: Gibt passenden Scheduler für aktuelle Plattform zurück

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
    else:
        logger.warning(f"Scheduler für {system} nicht verfügbar")
        return None
