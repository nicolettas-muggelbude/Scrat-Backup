"""
Credential Manager für sichere Passwort-Speicherung
Nutzt Windows Credential Manager (oder keyring für Cross-Platform)
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class CredentialManager:
    """
    Verwaltet verschlüsselte Passwort-Speicherung

    Features:
    - Windows Credential Manager Integration (via keyring)
    - Sichere Speicherung (nur für aktuellen User)
    - Plattform-unabhängig (Windows, Linux, macOS)
    - Fallback wenn nicht verfügbar
    """

    SERVICE_NAME = "ScratBackup"
    USERNAME = "backup_password"

    def __init__(self):
        """Initialisiert Credential Manager"""
        self.available = self._check_availability()

        if self.available:
            logger.info("Credential Manager verfügbar")
        else:
            logger.warning(
                "Credential Manager nicht verfügbar - Passwörter können nicht gespeichert werden"
            )

    def _check_availability(self) -> bool:
        """
        Prüft ob Credential Storage verfügbar ist.

        Prüft Modul-Pfad (nicht nur Klassenname) und testet einen echten
        Keyring-Zugriff, um native Crashes (z.B. KWallet ohne laufende Session)
        sicher abzufangen.

        Returns:
            True wenn verfügbar und funktionsfähig
        """
        try:
            import keyring
            from keyring.errors import NoKeyringError

            backend = keyring.get_keyring()
            backend_module = backend.__class__.__module__
            backend_name = backend.__class__.__name__
            full_name = f"{backend_module}.{backend_name}"

            # Fail-Backend anhand des Modul-Pfads erkennen (Klassenname ist nur "Keyring")
            if "fail" in backend_module.lower():
                logger.warning(f"Kein Keyring-Backend verfügbar: {full_name}")
                return False

            logger.info(f"Keyring-Backend: {full_name}")

            # Echten Zugriff testen – schlägt bei fehlender D-Bus-Session fehl
            try:
                keyring.get_password("__scrat_test__", "__test__")
            except NoKeyringError:
                logger.warning("Keyring-Backend antwortet nicht (NoKeyringError)")
                return False

            return True

        except ImportError:
            logger.warning("keyring-Bibliothek nicht installiert")
            return False
        except Exception as e:
            logger.warning(f"Keyring nicht nutzbar: {e}")
            return False

    def save_password(self, password: str) -> bool:
        """
        Speichert Passwort im Credential Manager

        Args:
            password: Zu speicherndes Passwort

        Returns:
            True wenn erfolgreich gespeichert
        """
        if not self.available:
            logger.warning("Credential Manager nicht verfügbar - kann Passwort nicht speichern")
            return False

        try:
            import keyring

            keyring.set_password(self.SERVICE_NAME, self.USERNAME, password)
            logger.info("Passwort erfolgreich gespeichert")
            return True

        except Exception as e:
            logger.error(f"Fehler beim Speichern des Passworts: {e}", exc_info=True)
            return False

    def get_password(self) -> Optional[str]:
        """
        Lädt Passwort aus Credential Manager

        Returns:
            Passwort oder None wenn nicht verfügbar
        """
        if not self.available:
            return None

        try:
            import keyring

            password = keyring.get_password(self.SERVICE_NAME, self.USERNAME)

            if password:
                logger.info("Passwort erfolgreich geladen")
            else:
                logger.debug("Kein gespeichertes Passwort gefunden")

            return password

        except Exception as e:
            logger.error(f"Fehler beim Laden des Passworts: {e}", exc_info=True)
            return None

    def delete_password(self) -> bool:
        """
        Löscht gespeichertes Passwort

        Returns:
            True wenn erfolgreich gelöscht
        """
        if not self.available:
            return False

        try:
            import keyring

            keyring.delete_password(self.SERVICE_NAME, self.USERNAME)
            logger.info("Passwort erfolgreich gelöscht")
            return True

        except keyring.errors.PasswordDeleteError:
            logger.debug("Kein Passwort zum Löschen vorhanden")
            return True  # Kein Fehler wenn nicht vorhanden

        except Exception as e:
            logger.error(f"Fehler beim Löschen des Passworts: {e}", exc_info=True)
            return False

    def has_saved_password(self) -> bool:
        """
        Prüft ob ein Passwort gespeichert ist

        Returns:
            True wenn Passwort vorhanden
        """
        password = self.get_password()
        return password is not None and password != ""


# Singleton-Instanz
_credential_manager = None


def get_credential_manager() -> CredentialManager:
    """
    Gibt Singleton-Instanz des CredentialManagers zurück

    Returns:
        CredentialManager-Instanz
    """
    global _credential_manager

    if _credential_manager is None:
        _credential_manager = CredentialManager()

    return _credential_manager
