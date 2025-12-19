#!/usr/bin/env python3
"""
Debug-Script für Wizard-Problem
Testet check_first_run() Logik
"""

import logging
import sys
from pathlib import Path

# Logging konfigurieren
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

# Importiere die Funktion
from src.core.config_manager import ConfigManager


def debug_check_first_run():
    """Debuggt check_first_run() Funktion"""

    print("=" * 60)
    print("DEBUG: Wizard-Start-Problem")
    print("=" * 60)

    config_dir = Path.home() / ".scrat-backup"
    config_file = config_dir / "config.json"

    print(f"\n1. Config-Verzeichnis: {config_dir}")
    print(f"   Existiert: {config_dir.exists()}")

    print(f"\n2. Config-Datei: {config_file}")
    print(f"   Existiert: {config_file.exists()}")

    if config_file.exists():
        print(f"   Größe: {config_file.stat().st_size} Bytes")
        print("\n3. Inhalt der config.json:")
        try:
            with open(config_file, 'r') as f:
                content = f.read()
                print(f"   {content[:500]}")  # Erste 500 Zeichen
        except Exception as e:
            print(f"   Fehler beim Lesen: {e}")

        print("\n4. Lade mit ConfigManager:")
        try:
            config_manager = ConfigManager(config_file)
            print(f"   ✓ ConfigManager geladen")

            print("\n5. Prüfe Quellen:")
            sources = config_manager.config.get("sources", [])
            print(f"   sources: {sources}")
            print(f"   Anzahl: {len(sources)}")
            print(f"   has_sources: {len(sources) > 0}")

            print("\n6. Prüfe Ziele:")
            destinations = config_manager.config.get("destinations", [])
            print(f"   destinations: {destinations}")
            print(f"   Anzahl: {len(destinations)}")
            print(f"   has_destinations: {len(destinations) > 0}")

            print("\n7. Entscheidung:")
            has_sources = len(sources) > 0
            has_destinations = len(destinations) > 0

            if not has_sources or not has_destinations:
                print(f"   → WIZARD STARTEN (unvollständige Config)")
                print(f"      Grund: sources={has_sources}, destinations={has_destinations}")
                return True
            else:
                print(f"   → KEIN WIZARD (gültige Config)")
                return False

        except Exception as e:
            print(f"   ✗ Fehler: {e}")
            print(f"   → WIZARD STARTEN (Fehler beim Laden)")
            return True
    else:
        print("\n3. Config-Datei existiert nicht")
        print("   → WIZARD STARTEN (erster Start)")
        return True


if __name__ == "__main__":
    result = debug_check_first_run()

    print("\n" + "=" * 60)
    print(f"ERGEBNIS: check_first_run() = {result}")
    print("=" * 60)

    if result:
        print("\n✓ Wizard SOLLTE starten")
    else:
        print("\n✗ Wizard sollte NICHT starten")
