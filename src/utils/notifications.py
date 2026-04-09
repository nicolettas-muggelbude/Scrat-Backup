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
    """Sendet Windows Toast-Notification – WinRT mit Fallback auf NotifyIcon."""
    import base64

    no_window = getattr(subprocess, "CREATE_NO_WINDOW", 0)

    # Sonderzeichen für XML/PowerShell escapen
    def _xml(s: str) -> str:
        return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

    # 1. Versuch: WinRT Toast (Windows 10/11) – zeigt 'Scrat-Backup' als App-Name
    try:
        t, m = _xml(title), _xml(message)
        ps_script = f"""
try {{
  [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
  [Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null
  $xml = New-Object Windows.Data.Xml.Dom.XmlDocument
  $xml.LoadXml('<toast><visual><binding template="ToastGeneric"><text>{t}</text><text>{m}</text></binding></visual></toast>')
  [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('Scrat-Backup').Show(
      [Windows.UI.Notifications.ToastNotification]::new($xml))
}} catch {{
  Add-Type -AssemblyName System.Windows.Forms
  $n = New-Object System.Windows.Forms.NotifyIcon
  $n.Icon = [System.Drawing.SystemIcons]::Information
  $n.Visible = $true
  $n.ShowBalloonTip(5000, '{_xml(title)}', '{_xml(message)}', [System.Windows.Forms.ToolTipIcon]::{'Warning' if urgent else 'Info'})
  Start-Sleep -Seconds 6
  $n.Dispose()
}}
"""
        encoded = base64.b64encode(ps_script.encode("utf-16-le")).decode("ascii")
        subprocess.Popen(
            ["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-EncodedCommand", encoded],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=no_window,
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
