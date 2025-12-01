"""
Input-Validatoren für Scrat-Backup
Validiert Benutzereingaben und Konfigurationen
"""

import re
from pathlib import Path
from typing import List, Optional, Tuple


class ValidationError(Exception):
    """Fehler bei Input-Validierung"""

    pass


class Validators:
    """Sammlung von Validierungs-Methoden"""

    @staticmethod
    def validate_path(
        path: Path,
        must_exist: bool = False,
        must_be_dir: bool = False,
        must_be_writable: bool = False,
    ) -> Tuple[bool, Optional[str]]:
        """
        Validiert Pfad

        Args:
            path: Zu validierender Pfad
            must_exist: Pfad muss existieren
            must_be_dir: Pfad muss Verzeichnis sein
            must_be_writable: Pfad muss schreibbar sein

        Returns:
            Tuple (is_valid, error_message)
        """
        if not isinstance(path, Path):
            return False, "Pfad muss ein Path-Objekt sein"

        if must_exist and not path.exists():
            return False, f"Pfad existiert nicht: {path}"

        if must_be_dir and path.exists() and not path.is_dir():
            return False, f"Pfad ist kein Verzeichnis: {path}"

        if must_be_writable:
            # Prüfe ob Parent-Verzeichnis schreibbar ist
            parent = path.parent if not path.exists() else path
            try:
                # Test-Datei erstellen
                test_file = parent / ".scrat_write_test"
                test_file.touch()
                test_file.unlink()
            except (PermissionError, OSError) as e:
                return False, f"Pfad nicht schreibbar: {path} ({e})"

        return True, None

    @staticmethod
    def validate_paths(
        paths: List[Path],
        must_exist: bool = False,
        must_be_dir: bool = False,
        min_count: int = 0,
        max_count: Optional[int] = None,
    ) -> Tuple[bool, Optional[str]]:
        """
        Validiert Liste von Pfaden

        Args:
            paths: Liste von Pfaden
            must_exist: Alle Pfade müssen existieren
            must_be_dir: Alle Pfade müssen Verzeichnisse sein
            min_count: Minimale Anzahl Pfade
            max_count: Maximale Anzahl Pfade

        Returns:
            Tuple (is_valid, error_message)
        """
        if not isinstance(paths, list):
            return False, "Pfade müssen eine Liste sein"

        if len(paths) < min_count:
            return (
                False,
                f"Mindestens {min_count} Pfad(e) erforderlich, aber nur {len(paths)} angegeben",
            )

        if max_count is not None and len(paths) > max_count:
            return False, f"Maximal {max_count} Pfad(e) erlaubt, aber {len(paths)} angegeben"

        for path in paths:
            is_valid, error_msg = Validators.validate_path(
                path, must_exist=must_exist, must_be_dir=must_be_dir
            )
            if not is_valid:
                return False, error_msg

        return True, None

    @staticmethod
    def validate_password(
        password: str, min_length: int = 1, max_length: int = 1024, allow_empty: bool = False
    ) -> Tuple[bool, Optional[str]]:
        """
        Validiert Passwort

        Args:
            password: Passwort
            min_length: Minimale Länge
            max_length: Maximale Länge
            allow_empty: Erlaube leeres Passwort

        Returns:
            Tuple (is_valid, error_message)
        """
        if not isinstance(password, str):
            return False, "Passwort muss ein String sein"

        if not password and not allow_empty:
            return False, "Passwort darf nicht leer sein"

        if len(password) < min_length and not (allow_empty and not password):
            return False, f"Passwort muss mindestens {min_length} Zeichen lang sein"

        if len(password) > max_length:
            return False, f"Passwort darf maximal {max_length} Zeichen lang sein"

        return True, None

    @staticmethod
    def validate_backup_name(name: str) -> Tuple[bool, Optional[str]]:
        """
        Validiert Backup-Namen

        Args:
            name: Backup-Name

        Returns:
            Tuple (is_valid, error_message)
        """
        if not isinstance(name, str):
            return False, "Name muss ein String sein"

        if not name or not name.strip():
            return False, "Name darf nicht leer sein"

        if len(name) > 255:
            return False, "Name darf maximal 255 Zeichen lang sein"

        # Prüfe auf ungültige Zeichen (nur alphanumerisch, Leerzeichen, -, _)
        if not re.match(r"^[a-zA-Z0-9\s\-_äöüÄÖÜß]+$", name):
            return False, "Name darf nur Buchstaben, Zahlen, Leerzeichen, - und _ enthalten"

        return True, None

    @staticmethod
    def validate_email(email: str) -> Tuple[bool, Optional[str]]:
        """
        Validiert E-Mail-Adresse

        Args:
            email: E-Mail-Adresse

        Returns:
            Tuple (is_valid, error_message)
        """
        if not isinstance(email, str):
            return False, "E-Mail muss ein String sein"

        if not email or not email.strip():
            return False, "E-Mail darf nicht leer sein"

        # Einfache E-Mail-Validierung
        if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
            return False, "Ungültige E-Mail-Adresse"

        return True, None

    @staticmethod
    def validate_port(
        port: int, min_port: int = 1, max_port: int = 65535
    ) -> Tuple[bool, Optional[str]]:
        """
        Validiert Port-Nummer

        Args:
            port: Port-Nummer
            min_port: Minimaler Port
            max_port: Maximaler Port

        Returns:
            Tuple (is_valid, error_message)
        """
        if not isinstance(port, int):
            return False, "Port muss eine Zahl sein"

        if port < min_port or port > max_port:
            return False, f"Port muss zwischen {min_port} und {max_port} liegen"

        return True, None

    @staticmethod
    def validate_url(url: str, schemes: Optional[List[str]] = None) -> Tuple[bool, Optional[str]]:
        """
        Validiert URL

        Args:
            url: URL
            schemes: Erlaubte Schemes (z.B. ['http', 'https'])

        Returns:
            Tuple (is_valid, error_message)
        """
        if not isinstance(url, str):
            return False, "URL muss ein String sein"

        if not url or not url.strip():
            return False, "URL darf nicht leer sein"

        # Einfache URL-Validierung
        url_pattern = r"^[a-zA-Z][a-zA-Z0-9+.-]*://.+"
        if not re.match(url_pattern, url):
            return False, "Ungültiges URL-Format"

        if schemes:
            scheme = url.split("://")[0].lower()
            if scheme not in schemes:
                return False, f"URL-Schema muss eines von {schemes} sein"

        return True, None

    @staticmethod
    def validate_hostname(hostname: str) -> Tuple[bool, Optional[str]]:
        """
        Validiert Hostname

        Args:
            hostname: Hostname oder IP-Adresse

        Returns:
            Tuple (is_valid, error_message)
        """
        if not isinstance(hostname, str):
            return False, "Hostname muss ein String sein"

        if not hostname or not hostname.strip():
            return False, "Hostname darf nicht leer sein"

        # Prüfe auf gültigen Hostname oder IP
        hostname_pattern = r"^[a-zA-Z0-9.-]+$"
        ip_pattern = r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$"

        if not (re.match(hostname_pattern, hostname) or re.match(ip_pattern, hostname)):
            return False, "Ungültiger Hostname oder IP-Adresse"

        return True, None
