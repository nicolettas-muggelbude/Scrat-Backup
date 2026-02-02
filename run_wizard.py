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

    # QApplication erstellen
    app = QApplication(sys.argv)
    app.setApplicationName("Scrat-Backup Wizard V2")
    app.setOrganizationName("Scrat")

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

    # Wizard erstellen und anzeigen
    wizard = SetupWizardV2()
    wizard.show()

    # Event-Loop starten
    sys.exit(app.exec())
