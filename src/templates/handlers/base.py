"""
Basis-Klasse für Template-Handler
Abstraktion für plattformspezifische Implementierungen
"""

import logging
import platform
from abc import ABC, abstractmethod
from typing import Optional

logger = logging.getLogger(__name__)


class TemplateHandler(ABC):
    """
    Abstrakte Basis-Klasse für Template-Handler

    Jeder Handler implementiert die spezifische Logik für ein Backup-Ziel
    (USB, OneDrive, Synology, etc.) und ist plattformunabhängig.
    """

    def __init__(self, template_data: dict):
        """
        Args:
            template_data: Template-Definition aus JSON
        """
        self.template_data = template_data
        self.platform = platform.system()

    @abstractmethod
    def check_availability(self) -> tuple[bool, Optional[str]]:
        """
        Prüft ob Template auf aktueller Plattform verfügbar ist

        Returns:
            (available, error_message)
            - (True, None) wenn verfügbar
            - (False, "Grund") wenn nicht verfügbar
        """
        pass

    @abstractmethod
    def setup(self, config: dict) -> tuple[bool, dict, Optional[str]]:
        """
        Führt Template-spezifisches Setup durch

        Args:
            config: User-Input aus dem Wizard-Formular

        Returns:
            (success, result_config, error_message)
            - result_config: Finales Config-Dict für ConfigManager
        """
        pass

    @abstractmethod
    def validate(self, config: dict) -> tuple[bool, Optional[str]]:
        """
        Validiert eine Konfiguration

        Args:
            config: Zu validierende Config

        Returns:
            (valid, error_message)
        """
        pass

    def is_platform_supported(self) -> bool:
        """
        Prüft ob Template auf aktueller Plattform unterstützt wird

        Returns:
            True wenn unterstützt
        """
        platforms = self.template_data.get("platforms", ["windows", "linux", "darwin"])
        current = self.platform.lower()
        return current in [p.lower() for p in platforms]

    def get_display_name(self) -> str:
        """Gibt anzeigbaren Namen zurück"""
        return self.template_data.get("display_name", self.template_data.get("id", "Unknown"))

    def get_description(self) -> str:
        """Gibt Beschreibung zurück"""
        return self.template_data.get("description", "")

    def get_category(self) -> str:
        """Gibt Kategorie zurück (local, cloud, nas, server)"""
        return self.template_data.get("category", "other")

    def get_icon(self) -> str:
        """Gibt Icon-Pfad oder Emoji zurück"""
        return self.template_data.get("icon", "📦")
