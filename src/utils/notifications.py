"""
Plattformübergreifende Desktop-Benachrichtigungen für Headless-Modus.
Wird von run_backup_headless() genutzt (kein Qt verfügbar).
"""

import logging
import subprocess
import sys

logger = logging.getLogger(__name__)


def _clean_env_for_system_process() -> dict:
    """
    Gibt eine bereinigte Umgebung für System-Subprozesse zurück.
    Entfernt LD_LIBRARY_PATH des AppImage damit System-Libs (libnotify,
    libglib) nicht durch ältere AppImage-Versionen überschrieben werden.
    """
    import os
    env = os.environ.copy()
    env.pop("LD_LIBRARY_PATH", None)
    env.pop("LD_PRELOAD", None)
    return env


def _notify_linux(title: str, message: str, urgent: bool = False) -> bool:
    """Sendet Desktop-Notification via notify-send (Linux/Freedesktop)."""
    try:
        import glob as _glob
        import os
        env = _clean_env_for_system_process()
        uid = os.getuid()

        # D-Bus-Session für Notification-Daemon (wichtigste Voraussetzung)
        if "DBUS_SESSION_BUS_ADDRESS" not in env:
            dbus_sock = f"/run/user/{uid}/bus"
            if os.path.exists(dbus_sock):
                env["DBUS_SESSION_BUS_ADDRESS"] = f"unix:path={dbus_sock}"

        # XDG_RUNTIME_DIR für Wayland/D-Bus
        env.setdefault("XDG_RUNTIME_DIR", f"/run/user/{uid}")

        # DISPLAY/WAYLAND_DISPLAY – wird von modernem notify-send nicht
        # zwingend benötigt, ältere Versionen brauchen es aber
        if "DISPLAY" not in env and "WAYLAND_DISPLAY" not in env:
            wayland_socks = _glob.glob(f"/run/user/{uid}/wayland-*")
            if wayland_socks:
                env["WAYLAND_DISPLAY"] = os.path.basename(wayland_socks[0])
            else:
                env["DISPLAY"] = ":0"

        urgency = "critical" if urgent else "normal"
        icon = "dialog-error" if urgent else "dialog-information"

        logger.info(
            f"notify-send: DISPLAY={env.get('DISPLAY','–')} "
            f"WAYLAND={env.get('WAYLAND_DISPLAY','–')} "
            f"DBUS={'gesetzt' if 'DBUS_SESSION_BUS_ADDRESS' in env else 'fehlt'}"
        )

        result = subprocess.run(
            ["notify-send", "-u", urgency, "-i", icon, "-a", "Scrat-Backup", title, message],
            env=env,
            capture_output=True,
            timeout=5,
        )
        if result.returncode != 0:
            logger.warning(f"notify-send Fehler (rc={result.returncode}): {result.stderr.decode().strip()}")
            return False
        return True
    except FileNotFoundError:
        logger.warning("notify-send nicht gefunden – keine Desktop-Benachrichtigung")
        return False
    except Exception as e:
        logger.warning(f"notify-send fehlgeschlagen: {e}")
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
