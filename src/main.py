"""
Scrat-Backup - Entry Point
Windows Backup-Tool für Privatnutzer
"""

import sys


def main() -> int:
    """
    Haupteinstiegspunkt für Scrat-Backup

    Returns:
        int: Exit-Code (0 = Erfolg)
    """
    print("=" * 60)
    print("Scrat-Backup v0.1.0 - Windows Backup-Tool")
    print("=" * 60)
    print()
    print("🌰 Wie ein Eichhörnchen seine Eicheln bewahrt,")
    print("   so bewahren wir deine Daten.")
    print()
    print("⚠️  HINWEIS: Projekt in Entwicklung - Phase 1 (Setup)")
    print()
    print("Status:")
    print("  ✅ Projekt-Struktur erstellt")
    print("  ✅ Git-Repository initialisiert")
    print("  ⏳ Core-Module in Entwicklung")
    print("  ⏳ GUI in Planung")
    print()
    print("Für weitere Informationen siehe:")
    print("  - README.md")
    print("  - claude.md (Vollständige Dokumentation)")
    print("  - projekt.md (Implementierungsplan)")
    print()
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
