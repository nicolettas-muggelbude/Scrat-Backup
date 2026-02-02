"""
Scrat-Backup - Entry Point
Windows Backup-Tool für Privatnutzer
"""

import logging
import sys
from datetime import datetime
from pathlib import Path

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTranslator, QLibraryInfo

from src.core.config_manager import ConfigManager
from src.gui.main_window import MainWindow
from src.gui.theme_manager import ThemeManager, Theme
from src.gui.wizard_v2 import SetupWizardV2

# Logging konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


def check_first_run() -> bool:
    """
    Prüft ob erste Ausführung (keine oder ungültige Konfiguration vorhanden)

    Returns:
        True wenn erster Start oder Konfiguration ungültig
    """
    config_dir = Path.home() / ".scrat-backup"
    config_file = config_dir / "config.json"

    # Wenn config.json nicht existiert → erster Start
    if not config_file.exists():
        logger.info("Keine config.json gefunden → Erster Start")
        return True

    # Config-Datei existiert, prüfe ob sie gültig ist
    try:
        config_manager = ConfigManager(config_file)

        # Prüfe ob Quellen und Ziele konfiguriert sind
        has_sources = (
            config_manager.config.get("sources") and len(config_manager.config["sources"]) > 0
        )
        has_destinations = (
            config_manager.config.get("destinations")
            and len(config_manager.config["destinations"]) > 0
        )

        if not has_sources or not has_destinations:
            logger.info(
                f"Config unvollständig (sources={has_sources}, "
                f"destinations={has_destinations}) → Wizard starten"
            )
            return True

        logger.info("Gültige Konfiguration gefunden → Kein Wizard")
        return False

    except Exception as e:
        logger.warning(f"Fehler beim Laden der Config: {e} → Wizard starten")
        return True


def save_wizard_config(wizard_config: dict) -> None:
    """
    Speichert Wizard-Konfiguration in ConfigManager

    Args:
        wizard_config: Dictionary aus SetupWizardV2.get_config()
                       Format: {
                           "action": "backup",
                           "sources": ["path1", "path2"],
                           "excludes": ["*.tmp", ...],
                           "template_id": "usb",
                           "template_config": {...},
                           "start_backup_now": False,
                           "start_tray": True
                       }
    """
    config_manager = ConfigManager()

    try:
        # 1. Quellen in Config speichern
        sources = wizard_config.get("sources", [])
        excludes = wizard_config.get("excludes", [])

        if not config_manager.config.get("sources"):
            config_manager.config["sources"] = []

        # Erstelle Source-Einträge
        for source_path in sources:
            path_obj = Path(source_path)
            source_entry = {
                "path": source_path,
                "name": path_obj.name if path_obj.name else "Quelle",
                "enabled": True,
                "exclude_patterns": excludes,  # Nutze Ausschlüsse vom Wizard
            }
            config_manager.config["sources"].append(source_entry)
            logger.info(f"Quelle hinzugefügt: {source_path}")

        # 2. Ziel in Config speichern
        template_id = wizard_config.get("template_id")
        template_config = wizard_config.get("template_config", {})

        if template_id and template_config:
            if not config_manager.config.get("destinations"):
                config_manager.config["destinations"] = []

            # Template-Name für bessere Anzeige
            template_names = {
                "usb": "USB-Laufwerk",
                "onedrive": "OneDrive",
                "google_drive": "Google Drive",
                "dropbox": "Dropbox",
                "nextcloud": "Nextcloud",
                "synology": "Synology NAS",
                "qnap": "QNAP NAS",
            }
            template_name = template_names.get(template_id, template_id.replace("_", " ").title())

            destination_entry = {
                "name": f"{template_name}",
                "type": template_config.get("type", template_id),
                "config": template_config,
                "enabled": True,
            }
            config_manager.config["destinations"].append(destination_entry)
            logger.info(f"Ziel hinzugefügt: {template_name} ({template_id})")

        # 3. TODO: Verschlüsselung (wird in zukünftiger Version implementiert)
        # encryption_config = wizard_config.get("encryption", {})

        # 4. TODO: Zeitplan (wird in zukünftiger Version implementiert)
        # Aktuell: Kein Zeitplan-Page im neuen Wizard
        schedule = wizard_config.get("schedule", {})
        if schedule and schedule.get("enabled"):
            if not config_manager.config.get("schedules"):
                config_manager.config["schedules"] = []

            # Berechne source_ids: Indizes der gerade hinzugefügten Quellen
            sources_count = len(config_manager.config.get("sources", []))
            num_new_sources = len(wizard_config.get("sources", []))
            # Die neuen Quellen wurden ans Ende der Liste angehängt
            source_ids = list(range(sources_count - num_new_sources, sources_count))

            # destination_id: Index des gerade hinzugefügten Ziels (letztes Element)
            destinations_count = len(config_manager.config.get("destinations", []))
            destination_id = destinations_count - 1 if destinations_count > 0 else 0

            # Konvertiere interval-String zu frequency
            interval_str = schedule.get("interval", "Täglich")
            frequency_map = {
                "Täglich": "daily",
                "Wöchentlich": "weekly",
                "Monatlich": "monthly",
            }
            frequency = frequency_map.get(interval_str, "daily")

            # Berechne ID für Zeitplan (nächste freie ID)
            existing_schedules = config_manager.config.get("schedules", [])
            next_id = max([s.get("id", 0) for s in existing_schedules], default=0) + 1

            # Erstelle Zeitplan im Scheduler-Format
            schedule_entry = {
                "id": next_id,
                "name": "Automatisches Backup",
                "enabled": True,
                "frequency": frequency,
                "time": "03:00",  # Default: 3:00 Uhr
                "weekdays": [1, 2, 3, 4, 5],  # Mo-Fr für wöchentlich
                "day_of_month": 1,  # 1. Tag des Monats für monatlich
                "source_ids": source_ids,
                "destination_id": destination_id,
                "backup_type": "incremental",  # Default: Incremental
                "retention": schedule.get("retention", 3),
                "created_at": datetime.now().isoformat(),
            }
            config_manager.config["schedules"].append(schedule_entry)
            logger.info(
                f"Zeitplan hinzugefügt: {frequency} um 03:00 Uhr, "
                f"{len(source_ids)} Quellen, Ziel-ID {destination_id}"
            )

        # 5. Speichere Konfiguration
        config_manager.save()

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
    logger.info("=" * 60)
    logger.info("Scrat-Backup GUI wird gestartet")
    logger.info("=" * 60)

    # QApplication erstellen
    app = QApplication(sys.argv)
    app.setApplicationName("Scrat-Backup")
    app.setOrganizationName("Scrat")
    logger.info("QApplication erstellt")

    # Qt-Übersetzungen laden (für deutschen Dialog)
    translator = QTranslator(app)
    translations_path = QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)
    if translator.load("qtbase_de", translations_path):
        app.installTranslator(translator)
        logger.info("Deutsche Qt-Übersetzungen geladen")
    else:
        logger.warning("Deutsche Qt-Übersetzungen nicht gefunden")

    # Theme Manager initialisieren (Auto Dark Mode + Manueller Toggle)
    theme_manager = ThemeManager(app)
    logger.info(f"Theme Manager initialisiert: {theme_manager.get_theme_display_name()}")

    # Prüfe ob erster Start
    logger.info("Prüfe ob erster Start...")
    is_first_run = check_first_run()
    logger.info(f"check_first_run() = {is_first_run}")

    if is_first_run:
        logger.info(">>> WIZARD V2 WIRD GESTARTET <<<")

        # Setup-Wizard V2 anzeigen (mit neuen Pages)
        wizard = SetupWizardV2()
        if wizard.exec():
            # Wizard abgeschlossen
            config = wizard.get_config()
            sources = config.get('sources', [])
            logger.info(f"Setup abgeschlossen: {len(sources)} Quellen konfiguriert")

            # Speichere Konfiguration
            try:
                save_wizard_config(config)
                logger.info("Konfiguration erfolgreich gespeichert")
            except Exception as e:
                logger.error(f"Fehler beim Speichern der Konfiguration: {e}", exc_info=True)
                # Zeige Fehlermeldung, aber fahre trotzdem fort
                from PySide6.QtWidgets import QMessageBox

                QMessageBox.warning(
                    None,
                    "Warnung",
                    f"Die Konfiguration konnte nicht vollständig gespeichert werden:\n{e}\n\n"
                    f"Das Hauptfenster wird trotzdem geöffnet.",
                )
        else:
            # Wizard abgebrochen
            logger.info("Setup abgebrochen")
            return 1
    else:
        logger.info(">>> KEIN WIZARD - Hauptfenster direkt starten <<<")

    # Hauptfenster erstellen und anzeigen
    logger.info("Erstelle Hauptfenster...")
    window = MainWindow()
    window.show()

    logger.info("Hauptfenster angezeigt - GUI gestartet")

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
