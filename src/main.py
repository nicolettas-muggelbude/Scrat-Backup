"""
Scrat-Backup - Entry Point
Windows Backup-Tool für Privatnutzer
"""

import logging
import sys
from pathlib import Path

from PyQt6.QtWidgets import QApplication

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

            # TODO: Speichere Konfiguration
            # save_config(config)
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
