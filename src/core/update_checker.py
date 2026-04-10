"""
Auto-Updater für Scrat-Backup
Prüft GitHub Releases API auf neue Versionen.
"""

import json
import logging
import re
import ssl
import sys
import threading
from datetime import date, datetime
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError

from PySide6.QtCore import QObject, Signal

from utils.paths import get_app_data_dir

logger = logging.getLogger(__name__)

GITHUB_API = "https://api.github.com/repos/nicolettas-muggelbude/Scrat-Backup/releases/latest"
RELEASES_URL = "https://github.com/nicolettas-muggelbude/Scrat-Backup/releases/latest"
CHECK_INTERVAL_DAYS = 1


def _parse_version(version_str: str) -> tuple:
    """Wandelt '0.3.3-beta' in (0, 3, 3, 'beta') um – zum Vergleichen."""
    version_str = version_str.lstrip("v")
    match = re.match(r"(\d+)\.(\d+)\.(\d+)(?:[-.](.+))?", version_str)
    if not match:
        return (0, 0, 0, "")
    major, minor, patch, suffix = match.groups()
    return (int(major), int(minor), int(patch), suffix or "")


def _is_newer(latest: str, current: str) -> bool:
    """True wenn latest > current."""
    l = _parse_version(latest)
    c = _parse_version(current)
    # Numerische Teile vergleichen
    if l[:3] != c[:3]:
        return l[:3] > c[:3]
    # Gleiche Nummer: Release ohne Suffix > mit Suffix (beta, rc usw.)
    l_suffix = l[3]
    c_suffix = c[3]
    if l_suffix == c_suffix:
        return False
    if not l_suffix and c_suffix:
        return True   # "" > "beta"
    if l_suffix and not c_suffix:
        return False  # "beta" < ""
    return l_suffix > c_suffix


def _last_check_path() -> Path:
    return get_app_data_dir() / "last_update_check"


def _should_check() -> bool:
    path = _last_check_path()
    if not path.exists():
        return True
    try:
        last = date.fromisoformat(path.read_text().strip())
        return (date.today() - last).days >= CHECK_INTERVAL_DAYS
    except Exception:
        return True


def _save_check_date() -> None:
    path = _last_check_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(date.today().isoformat())


def _download_url_for_platform(assets: list) -> str:
    """Gibt die passende Download-URL für das aktuelle Betriebssystem zurück."""
    platform = sys.platform
    for asset in assets:
        name: str = asset.get("name", "")
        url: str = asset.get("browser_download_url", "")
        if platform == "win32" and name.endswith("-Setup.exe"):
            return url
        if platform == "linux" and name.endswith(".AppImage"):
            return url
        if platform == "darwin" and (".dmg" in name or "macos" in name.lower()):
            return url
    return RELEASES_URL


class UpdateChecker(QObject):
    """
    Hintergrund-Check für neue Versionen via GitHub Releases API.
    Läuft in einem Daemon-Thread – blockiert den App-Exit nicht.
    """

    update_available = Signal(str, str, str, str)
    # args: latest_version, release_notes, download_url, release_url

    def __init__(self, current_version: str, parent=None):
        super().__init__(parent)
        self.current_version = current_version

    def start(self) -> None:
        t = threading.Thread(target=self._run, daemon=True, name="UpdateChecker")
        t.start()

    def terminate(self) -> None:
        pass  # Daemon-Thread wird automatisch beim App-Exit beendet

    def _run(self) -> None:
        if not _should_check():
            logger.debug("Update-Check übersprungen (heute bereits geprüft)")
            return

        try:
            # SSL-Kontext: certifi bevorzugen (PyInstaller-Bundle), sonst System-Certs
            ssl_context = None
            try:
                import certifi
                ca_file = certifi.where()
                # Im PyInstaller-Bundle liegt certifi in _MEIPASS/certifi/cacert.pem
                if getattr(sys, "frozen", False):
                    import os
                    bundle_ca = os.path.join(sys._MEIPASS, "certifi", "cacert.pem")
                    if os.path.exists(bundle_ca):
                        ca_file = bundle_ca
                ssl_context = ssl.create_default_context(cafile=ca_file)
            except ImportError:
                try:
                    ssl_context = ssl.create_default_context()
                except Exception:
                    ssl_context = ssl._create_unverified_context()

            req = Request(
                GITHUB_API,
                headers={"User-Agent": f"Scrat-Backup/{self.current_version}"},
            )
            with urlopen(req, timeout=5, context=ssl_context) as resp:
                data = json.loads(resp.read())

            _save_check_date()

            latest_tag: str = data.get("tag_name", "")
            release_notes: str = data.get("body", "")
            assets: list = data.get("assets", [])
            html_url: str = data.get("html_url", RELEASES_URL)

            if not latest_tag:
                return

            latest_version = latest_tag.lstrip("v")
            logger.info(f"Update-Check: aktuell={self.current_version}, neueste={latest_version}")

            if _is_newer(latest_version, self.current_version):
                download_url = _download_url_for_platform(assets)
                logger.info(f"Neue Version verfügbar: {latest_version}")
                self.update_available.emit(
                    latest_version, release_notes, download_url, html_url
                )

        except URLError as e:
            logger.debug(f"Update-Check fehlgeschlagen (kein Internet?): {e}")
        except Exception as e:
            logger.warning(f"Update-Check Fehler: {e}")
