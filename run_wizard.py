#!/usr/bin/env python3
"""
Starter-Script für Wizard V2
Startet den Wizard aus dem Projekt-Root
"""

import sys
from pathlib import Path

# Füge src/ zum Python-Path hinzu
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root))

if __name__ == "__main__":
    import logging
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import QTranslator, QLibraryInfo

    # Logging konfigurieren
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Theme Manager importieren
    from gui.theme_manager import ThemeManager

    # Wizard importieren
    from gui.wizard_v2 import SetupWizardV2

    # Version importieren
    from src import __version__

    from PySide6.QtGui import QIcon

    # QApplication erstellen
    app = QApplication(sys.argv)
    app.setApplicationName(f"Scrat-Backup Wizard v{__version__}")
    app.setOrganizationName("Scrat")

    # App-Icon setzen (wird von allen Fenstern geerbt)
    icon_path = project_root / "assets" / "icons" / "scrat.ico"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    # Qt-Übersetzungen laden (für deutschen Dialog)
    translator = QTranslator(app)
    translations_path = QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)
    if translator.load("qtbase_de", translations_path):
        app.installTranslator(translator)
        logging.info("Deutsche Qt-Übersetzungen geladen")
    else:
        logging.warning("Deutsche Qt-Übersetzungen nicht gefunden")

    # Theme Manager initialisieren
    theme_manager = ThemeManager(app)
    print(f"Theme: {theme_manager.get_theme_display_name()}")

    # Config-Speicherung importieren
    from src.main import save_wizard_config, start_backup_after_wizard

    # Wizard erstellen und modal ausführen
    wizard = SetupWizardV2(version=__version__)
    result = wizard.exec()

    if result:
        config = wizard.get_config()
        logging.info(f"Wizard abgeschlossen: {config}")
        try:
            save_wizard_config(config)
            logging.info("Konfiguration erfolgreich gespeichert")
        except Exception as e:
            logging.error(f"Fehler beim Speichern: {e}")

        # Backup starten wenn gewünscht
        if config.get("start_backup_now"):
            logging.info("Backup wird gestartet...")
            start_backup_after_wizard(config)
    else:
        logging.info("Wizard abgebrochen")

    sys.exit(0)
