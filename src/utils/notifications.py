"""
Plattformübergreifende Desktop-Benachrichtigungen für Headless-Modus.
Wird von run_backup_headless() genutzt (kein Qt verfügbar).
"""

import logging
import subprocess
import sys

logger = logging.getLogger(__name__)


def _notify_linux(title: str, message: str, urgent: bool = False) -> bool:
    """Sendet Desktop-Notification via notify-send (Linux/Freedesktop)."""
    try:
        urgency = "critical" if urgent else "normal"
        icon = "dialog-error" if urgent else "dialog-information"
        subprocess.Popen(
            ["notify-send", "-u", urgency, "-i", icon, "-a", "Scrat-Backup", title, message],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except FileNotFoundError:
        return False
    except Exception as e:
        logger.debug(f"notify-send fehlgeschlagen: {e}")
        return False


def _notify_windows(title: str, message: str, urgent: bool = False) -> bool:
    """Sendet Desktop-Notification via PowerShell NotifyIcon (Windows)."""
    try:
        title_esc = title.replace("'", "`'")
        message_esc = message.replace("'", "`'")
        ps_script = (
            "Add-Type -AssemblyName System.Windows.Forms; "
            "$n = New-Object System.Windows.Forms.NotifyIcon; "
            "$n.Icon = [System.Drawing.SystemIcons]::Information; "
            "$n.Visible = $true; "
            f"$n.ShowBalloonTip(5000, '{title_esc}', '{message_esc}', "
            f"[System.Windows.Forms.ToolTipIcon]::{'Warning' if urgent else 'Info'}); "
            "Start-Sleep -Seconds 6; "
            "$n.Dispose()"
        )
        subprocess.Popen(
            ["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", ps_script],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        return True
    except FileNotFoundError:
        return False
    except Exception as e:
        logger.debug(f"PowerShell-Notification fehlgeschlagen: {e}")
        return False


def _notify_macos(title: str, message: str, urgent: bool = False) -> bool:
    """Sendet Desktop-Notification via osascript (macOS)."""
    try:
        script = f'display notification "{message}" with title "{title}"'
        subprocess.Popen(
            ["osascript", "-e", script],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except FileNotFoundError:
        return False
    except Exception as e:
        logger.debug(f"osascript-Notification fehlgeschlagen: {e}")
        return False


def send_notification(title: str, message: str, urgent: bool = False) -> None:
    """
    Sendet plattformübergreifende Desktop-Notification.
    Schlägt still fehl wenn keine Notification-Infrastruktur verfügbar.
    """
    platform = sys.platform
    if platform == "linux":
        ok = _notify_linux(title, message, urgent)
    elif platform == "win32":
        ok = _notify_windows(title, message, urgent)
    elif platform == "darwin":
        ok = _notify_macos(title, message, urgent)
    else:
        ok = False

    if not ok:
        logger.debug(f"Desktop-Notification nicht gesendet: {title} – {message}")
