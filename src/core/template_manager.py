"""
Template-Manager für Backup-Ziel-Vorlagen
Lädt und verwaltet vordefinierte Konfigurationen
"""

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class Template:
    """Repräsentiert ein Backup-Ziel-Template"""

    id: str
    version: str
    display_name: str
    icon: str
    description: str
    category: str
    storage_type: str
    handler_class: str
    platforms: List[str]
    ui_fields: List[dict]
    config_mapping: dict
    availability_check: dict
    raw_data: dict  # Original JSON

    @classmethod
    def from_dict(cls, data: dict) -> "Template":
        """Erstellt Template aus Dictionary"""
        return cls(
            id=data.get("id", "unknown"),
            version=data.get("version", "1.0"),
            display_name=data.get("display_name", "Unknown"),
            icon=data.get("icon", "📦"),
            description=data.get("description", ""),
            category=data.get("category", "other"),
            storage_type=data.get("storage_type", ""),
            handler_class=data.get("handler", ""),
            platforms=data.get("platforms", ["windows", "linux", "darwin"]),
            ui_fields=data.get("ui_fields", []),
            config_mapping=data.get("config_mapping", {}),
            availability_check=data.get("availability_check", {}),
            raw_data=data,
        )

    def to_dict(self) -> dict:
        """Konvertiert Template zu Dictionary"""
        return self.raw_data


class TemplateManager:
    """
    Verwaltet Backup-Ziel-Templates

    Lädt Templates aus:
    - System-Templates: /usr/share/scrat-backup/templates/ (oder assets/templates/)
    - User-Templates: ~/.scrat-backup/templates/
    """

    def __init__(self):
        # Template-Verzeichnisse
        self.system_templates_dir = self._get_system_templates_dir()
        self.user_templates_dir = Path.home() / ".scrat-backup" / "templates"

        # Erstelle User-Templates-Verzeichnis falls nicht vorhanden
        self.user_templates_dir.mkdir(parents=True, exist_ok=True)

        # Cache
        self._templates: Dict[str, Template] = {}
        self._handlers: Dict[str, type] = {}
        self._loaded = False

        logger.info(
            f"TemplateManager initialisiert: "
            f"System={self.system_templates_dir}, User={self.user_templates_dir}"
        )

    def _get_system_templates_dir(self) -> Path:
        """Ermittelt System-Templates-Verzeichnis"""
        # Option 1: /usr/share/scrat-backup/templates/ (installiert)
        system_path = Path("/usr/share/scrat-backup/templates")
        if system_path.exists():
            return system_path

        # Option 2: assets/templates/ (Development)
        dev_path = Path(__file__).parent.parent.parent / "templates"
        if dev_path.exists():
            return dev_path

        # Option 3: Erstelle assets/templates/
        dev_path.mkdir(parents=True, exist_ok=True)
        return dev_path

    def get_available_templates(self, force_refresh: bool = False) -> List[Template]:
        """
        Gibt Liste aller verfügbaren Templates zurück

        Args:
            force_refresh: Wenn True, lädt Templates neu

        Returns:
            Liste von Template-Objekten (nur verfügbare auf aktueller Plattform)
        """
        if force_refresh or not self._loaded:
            self._load_templates()

        # Filtere nur verfügbare Templates
        available = []
        for template in self._templates.values():
            handler = self._get_handler(template)
            if handler:
                is_available, error = handler.check_availability()
                if is_available:
                    available.append(template)
                else:
                    logger.debug(
                        f"Template '{template.id}' nicht verfügbar: {error}"
                    )
            else:
                # Kein Handler = Template anzeigen aber mit Warnung
                available.append(template)

        return available

    def get_all_templates(self, force_refresh: bool = False) -> List[Template]:
        """
        Gibt ALLE Templates zurück (auch nicht verfügbare)

        Args:
            force_refresh: Wenn True, lädt Templates neu

        Returns:
            Liste von Template-Objekten
        """
        if force_refresh or not self._loaded:
            self._load_templates()

        return list(self._templates.values())

    def get_template_by_id(self, template_id: str) -> Optional[Template]:
        """
        Lädt ein spezifisches Template

        Args:
            template_id: Template-ID

        Returns:
            Template-Objekt oder None
        """
        if not self._loaded:
            self._load_templates()

        return self._templates.get(template_id)

    def create_template(self, template_data: dict, user_template: bool = True) -> Template:
        """
        Erstellt ein neues Template

        Args:
            template_data: Template-Definition
            user_template: Wenn True, speichere in User-Verzeichnis

        Returns:
            Erstelltes Template
        """
        # Validiere
        if not self.validate_template(template_data):
            raise ValueError("Ungültige Template-Definition")

        template = Template.from_dict(template_data)

        # Speichere
        if user_template:
            template_file = self.user_templates_dir / f"{template.id}.json"
        else:
            template_file = self.system_templates_dir / f"{template.id}.json"

        with open(template_file, "w", encoding="utf-8") as f:
            json.dump(template_data, f, indent=2, ensure_ascii=False)

        # Zu Cache hinzufügen
        self._templates[template.id] = template

        logger.info(f"Template '{template.id}' erstellt: {template_file}")
        return template

    def delete_template(self, template_id: str) -> bool:
        """
        Löscht ein User-Template

        Args:
            template_id: Template-ID

        Returns:
            True bei Erfolg
        """
        # Nur User-Templates können gelöscht werden
        template_file = self.user_templates_dir / f"{template_id}.json"

        if not template_file.exists():
            logger.warning(f"Template '{template_id}' existiert nicht")
            return False

        try:
            template_file.unlink()
            if template_id in self._templates:
                del self._templates[template_id]
            logger.info(f"Template '{template_id}' gelöscht")
            return True
        except Exception as e:
            logger.error(f"Fehler beim Löschen von Template '{template_id}': {e}")
            return False

    def validate_template(self, template_data: dict) -> bool:
        """
        Validiert Template-Struktur

        Args:
            template_data: Zu validierendes Template

        Returns:
            True wenn gültig
        """
        required_fields = ["id", "display_name", "storage_type"]

        for field in required_fields:
            if field not in template_data:
                logger.error(f"Template fehlt Pflichtfeld: {field}")
                return False

        return True

    def _load_templates(self):
        """Lädt alle Templates aus System- und User-Verzeichnissen"""
        self._templates.clear()

        # System-Templates
        self._load_templates_from_dir(self.system_templates_dir, is_system=True)

        # User-Templates (können System-Templates überschreiben)
        self._load_templates_from_dir(self.user_templates_dir, is_system=False)

        self._loaded = True
        logger.info(f"{len(self._templates)} Template(s) geladen")

    def _load_templates_from_dir(self, directory: Path, is_system: bool):
        """
        Lädt Templates aus einem Verzeichnis

        Args:
            directory: Verzeichnis-Pfad
            is_system: Ob es System-Templates sind
        """
        if not directory.exists():
            return

        for template_file in directory.glob("*.json"):
            try:
                with open(template_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                template = Template.from_dict(data)
                self._templates[template.id] = template

                source = "System" if is_system else "User"
                logger.debug(f"Template geladen: {template.id} ({source})")

            except Exception as e:
                logger.error(f"Fehler beim Laden von {template_file}: {e}")

    def _get_handler(self, template: Template):
        """
        Lädt Handler-Klasse für Template

        Args:
            template: Template-Objekt

        Returns:
            Handler-Instanz oder None
        """
        handler_name = template.handler_class

        if not handler_name:
            return None

        # Aus Cache
        if handler_name in self._handlers:
            handler_class = self._handlers[handler_name]
            return handler_class(template.raw_data)

        # Dynamisch laden
        try:
            module_name = f"templates.handlers.{handler_name}"
            class_name = "".join(word.capitalize() for word in handler_name.split("_"))

            module = __import__(module_name, fromlist=[class_name])
            handler_class = getattr(module, class_name)

            # Cache
            self._handlers[handler_name] = handler_class

            return handler_class(template.raw_data)

        except Exception as e:
            logger.warning(f"Konnte Handler '{handler_name}' nicht laden: {e}")
            return None

    def get_templates_by_category(self, category: str) -> List[Template]:
        """
        Filtert Templates nach Kategorie

        Args:
            category: Kategorie (local, cloud, nas, server)

        Returns:
            Gefilterte Template-Liste
        """
        if not self._loaded:
            self._load_templates()

        return [
            t for t in self._templates.values()
            if t.category.lower() == category.lower()
        ]

    def get_categories(self) -> List[str]:
        """
        Gibt Liste aller Kategorien zurück

        Returns:
            Liste von Kategorie-Namen
        """
        if not self._loaded:
            self._load_templates()

        categories = set(t.category for t in self._templates.values())
        return sorted(categories)
