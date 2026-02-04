"""
Plattform-abstrahierte Autostart-Funktionalität
Unterstützt Windows, Linux und macOS
"""

import logging
import platform
import sys
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class AutostartManager:
    """Verwaltet Autostart-Einträge plattformunabhängig"""

    def __init__(self, app_name: str = "Scrat-Backup"):
        self.app_name = app_name
        self.system = platform.system()

    def enable_autostart(self, command: Optional[str] = None) -> bool:
        """
        Aktiviert Autostart für die Anwendung

        Args:
            command: Optionaler custom Command (default: sys.executable + --tray)

        Returns:
            True bei Erfolg
        """
        if command is None:
            # Standard: Python-Interpreter + Tray-Modus
            command = f'"{sys.executable}" -m scrat_backup --tray'

        if self.system == "Windows":
            return self._enable_windows_autostart(command)
        elif self.system == "Linux":
            return self._enable_linux_autostart(command)
        elif self.system == "Darwin":
            return self._enable_macos_autostart(command)
        else:
            logger.warning(f"Autostart für {self.system} nicht unterstützt")
            return False

    def disable_autostart(self) -> bool:
        """Deaktiviert Autostart"""
        if self.system == "Windows":
            return self._disable_windows_autostart()
        elif self.system == "Linux":
            return self._disable_linux_autostart()
        elif self.system == "Darwin":
            return self._disable_macos_autostart()
        else:
            return False

    def is_autostart_enabled(self) -> bool:
        """Prüft ob Autostart aktiviert ist"""
        if self.system == "Windows":
            return self._check_windows_autostart()
        elif self.system == "Linux":
            return self._check_linux_autostart()
        elif self.system == "Darwin":
            return self._check_macos_autostart()
        else:
            return False

    # ======================================================================
    # WINDOWS
    # ======================================================================

    def _enable_windows_autostart(self, command: str) -> bool:
        """Windows: Registry-Eintrag in CurrentVersion\\Run"""
        try:
            import winreg

            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)

            winreg.SetValueEx(key, self.app_name, 0, winreg.REG_SZ, command)
            winreg.CloseKey(key)

            logger.info("Windows-Autostart aktiviert")
            return True

        except Exception as e:
            logger.error(f"Fehler beim Aktivieren von Windows-Autostart: {e}")
            return False

    def _disable_windows_autostart(self) -> bool:
        """Windows: Registry-Eintrag entfernen"""
        try:
            import winreg

            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)

            try:
                winreg.DeleteValue(key, self.app_name)
                logger.info("Windows-Autostart deaktiviert")
            except FileNotFoundError:
                logger.warning("Autostart-Eintrag existiert nicht")

            winreg.CloseKey(key)
            return True

        except Exception as e:
            logger.error(f"Fehler beim Deaktivieren von Windows-Autostart: {e}")
            return False

    def _check_windows_autostart(self) -> bool:
        """Windows: Prüft ob Registry-Eintrag existiert"""
        try:
            import winreg

            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ)

            try:
                winreg.QueryValueEx(key, self.app_name)
                winreg.CloseKey(key)
                return True
            except FileNotFoundError:
                winreg.CloseKey(key)
                return False

        except Exception as e:
            logger.error(f"Fehler beim Prüfen von Windows-Autostart: {e}")
            return False

    # ======================================================================
    # LINUX
    # ======================================================================

    def _get_linux_autostart_file(self) -> Path:
        """Linux: Pfad zur .desktop-Datei in autostart"""
        autostart_dir = Path.home() / ".config" / "autostart"
        autostart_dir.mkdir(parents=True, exist_ok=True)
        return autostart_dir / f"{self.app_name.lower()}.desktop"

    def _enable_linux_autostart(self, command: str) -> bool:
        """Linux: .desktop-Datei in ~/.config/autostart/ erstellen"""
        try:
            desktop_file = self._get_linux_autostart_file()

            # Finde Icon-Pfad
            icon_path = self._find_icon_path()

            # .desktop-Inhalt
            desktop_content = f"""[Desktop Entry]
Type=Application
Name={self.app_name}
Comment=Automatisches Backup im Hintergrund
Exec={command}
Icon={icon_path}
Terminal=false
Categories=Utility;
X-GNOME-Autostart-enabled=true
"""

            desktop_file.write_text(desktop_content)
            desktop_file.chmod(0o755)

            logger.info(f"Linux-Autostart aktiviert: {desktop_file}")
            return True

        except Exception as e:
            logger.error(f"Fehler beim Aktivieren von Linux-Autostart: {e}")
            return False

    def _disable_linux_autostart(self) -> bool:
        """Linux: .desktop-Datei entfernen"""
        try:
            desktop_file = self._get_linux_autostart_file()

            if desktop_file.exists():
                desktop_file.unlink()
                logger.info("Linux-Autostart deaktiviert")
            else:
                logger.warning("Autostart-Datei existiert nicht")

            return True

        except Exception as e:
            logger.error(f"Fehler beim Deaktivieren von Linux-Autostart: {e}")
            return False

    def _check_linux_autostart(self) -> bool:
        """Linux: Prüft ob .desktop-Datei existiert"""
        return self._get_linux_autostart_file().exists()

    # ======================================================================
    # MACOS
    # ======================================================================

    def _enable_macos_autostart(self, command: str) -> bool:
        """macOS: LaunchAgent erstellen"""
        try:
            launch_agents_dir = Path.home() / "Library" / "LaunchAgents"
            launch_agents_dir.mkdir(parents=True, exist_ok=True)

            plist_file = launch_agents_dir / f"com.{self.app_name.lower()}.plist"

            # plist-Inhalt
            apple_dtd = "http://www.apple.com/DTDs/PropertyList-1.0.dtd"
            plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "{apple_dtd}">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.{self.app_name.lower()}</string>
    <key>ProgramArguments</key>
    <array>
        <string>{sys.executable}</string>
        <string>-m</string>
        <string>scrat_backup</string>
        <string>--tray</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
</dict>
</plist>
"""

            plist_file.write_text(plist_content)
            logger.info(f"macOS-Autostart aktiviert: {plist_file}")
            return True

        except Exception as e:
            logger.error(f"Fehler beim Aktivieren von macOS-Autostart: {e}")
            return False

    def _disable_macos_autostart(self) -> bool:
        """macOS: LaunchAgent entfernen"""
        try:
            plist_file = (
                Path.home() / "Library" / "LaunchAgents" / f"com.{self.app_name.lower()}.plist"
            )

            if plist_file.exists():
                plist_file.unlink()
                logger.info("macOS-Autostart deaktiviert")
            else:
                logger.warning("Autostart-Datei existiert nicht")

            return True

        except Exception as e:
            logger.error(f"Fehler beim Deaktivieren von macOS-Autostart: {e}")
            return False

    def _check_macos_autostart(self) -> bool:
        """macOS: Prüft ob LaunchAgent existiert"""
        plist_file = Path.home() / "Library" / "LaunchAgents" / f"com.{self.app_name.lower()}.plist"
        return plist_file.exists()

    # ======================================================================
    # HELPERS
    # ======================================================================

    def _find_icon_path(self) -> str:
        """Sucht Icon-Datei (für Linux .desktop)"""
        # Mögliche Icon-Pfade
        possible_paths = [
            Path(__file__).parent.parent.parent / "assets" / "scrat_icon.png",
            Path("/usr/share/icons/hicolor/256x256/apps/scrat-backup.png"),
            Path("/usr/local/share/icons/scrat-backup.png"),
        ]

        for path in possible_paths:
            if path.exists():
                return str(path)

        return "scrat-backup"  # Fallback: Icon-Name ohne Pfad
