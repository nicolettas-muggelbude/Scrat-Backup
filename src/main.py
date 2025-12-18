"""
Scrat-Backup - Entry Point
Windows Backup-Tool für Privatnutzer
"""

import logging
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from src.core.config_manager import ConfigManager
from src.core.metadata_manager import MetadataManager
from src.gui.main_window import MainWindow
from src.gui.theme import apply_theme
from src.gui.wizard import SetupWizard

# Logging konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


def check_first_run() -> bool:
    """
    Prüft ob erste Ausführung (keine Konfiguration vorhanden)

    Returns:
        True wenn erster Start
    """
    config_dir = Path.home() / ".scrat-backup"
    config_file = config_dir / "config.json"

    return not config_file.exists()


def save_wizard_config(wizard_config: dict) -> None:
    """
    Speichert Wizard-Konfiguration in ConfigManager und MetadataManager

    Args:
        wizard_config: Dictionary aus SetupWizard.get_config()
    """
    config_manager = ConfigManager()
    db_path = Path.home() / ".scrat-backup" / "metadata.db"
    metadata_manager = MetadataManager(db_path)

    try:
        # 1. Quellen in MetadataManager speichern
        for i, source_path in enumerate(wizard_config.get("sources", [])):
            # Bestimme Namen aus Pfad
            path_obj = Path(source_path)
            name = path_obj.name if path_obj.name else "Quelle"

            metadata_manager.add_source(
                name=f"{name} ({i+1})",
                windows_path=source_path,
                enabled=True,
                exclude_patterns=None,
            )
            logger.info(f"Quelle hinzugefügt: {source_path}")

        # 2. Ziel in MetadataManager speichern
        storage = wizard_config.get("storage", {})
        if storage:
            import json

            metadata_manager.add_destination(
                name=f"Backup-Ziel ({storage.get('type', 'unknown')})",
                dest_type=storage.get("type", "usb"),
                config=json.dumps(storage),  # Speichere komplette Storage-Config
                enabled=True,
            )
            logger.info(f"Ziel hinzugefügt: {storage.get('type')}")

        # 3. Verschlüsselungs-Passwort (optional in Config speichern - WARNUNG: Unsicher!)
        # Für jetzt: Nicht speichern, User muss bei jedem Backup eingeben
        # In Zukunft: Windows Credential Manager nutzen

        # 4. Zeitplan (optional)
        schedule = wizard_config.get("schedule", {})
        if schedule:
            # TODO: Schedule in ConfigManager speichern wenn implementiert
            pass

        config_manager.save()
        metadata_manager.disconnect()

        logger.info("Wizard-Konfiguration erfolgreich gespeichert")

    except Exception as e:
        logger.error(f"Fehler beim Speichern der Wizard-Config: {e}", exc_info=True)
        raise


def run_gui() -> int:
    """
    Startet GUI-Anwendung

    Returns:
        int: Exit-Code (0 = Erfolg)
    """
    # QApplication erstellen
    app = QApplication(sys.argv)
    app.setApplicationName("Scrat-Backup")
    app.setOrganizationName("Scrat")

    # Theme anwenden
    apply_theme(app)

    # Prüfe ob erster Start
    if check_first_run():
        logger.info("Erster Start erkannt - zeige Setup-Wizard")

        # Setup-Wizard anzeigen
        wizard = SetupWizard()
        if wizard.exec():
            # Wizard abgeschlossen
            config = wizard.get_config()
            logger.info(f"Setup abgeschlossen: {len(config['sources'])} Quellen konfiguriert")

            # Speichere Konfiguration
            save_wizard_config(config)
        else:
            # Wizard abgebrochen
            logger.info("Setup abgebrochen")
            return 1

    # Hauptfenster erstellen und anzeigen
    window = MainWindow()
    window.show()

    logger.info("GUI gestartet")

    # Event-Loop starten
    return app.exec()


def main() -> int:
    """
    Haupteinstiegspunkt für Scrat-Backup

    Returns:
        int: Exit-Code (0 = Erfolg)
    """
    logger.info("=" * 60)
    logger.info("Scrat-Backup v0.2.0 - Windows Backup-Tool")
    logger.info("=" * 60)

    # GUI starten
    try:
        return run_gui()
    except Exception as e:
        logger.error(f"Kritischer Fehler: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
