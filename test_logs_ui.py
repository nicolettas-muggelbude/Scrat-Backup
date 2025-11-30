"""
Testskript für Logs-UI
Fügt Test-Logs in die Datenbank ein und startet die GUI
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Füge src zum Python-Path hinzu
sys.path.insert(0, str(Path(__file__).parent))

from src.core.metadata_manager import MetadataManager


def create_test_logs():
    """Erstellt Test-Logs in der Datenbank"""
    db_path = Path.home() / ".scrat-backup" / "metadata.db"
    metadata_manager = MetadataManager(db_path)

    print("Erstelle Test-Logs...")

    # Test-Logs mit verschiedenen Levels
    test_logs = [
        ("INFO", "Scrat-Backup gestartet", None, None),
        ("INFO", "Konfiguration geladen", None, None),
        ("DEBUG", "MetadataManager initialisiert", None, None),
        ("INFO", "Backup-Scan gestartet für Quelle: Dokumente", 1, None),
        ("WARNING", "3 Dateien konnten nicht gelesen werden (keine Berechtigung)", 1, None),
        ("INFO", "Backup abgeschlossen: 1523 Dateien in 12.5 Sekunden", 1, None),
        ("ERROR", "Netzwerk-Verbindung fehlgeschlagen beim Upload zu SFTP-Server", 2, "ConnectionError: [Errno 111] Connection refused\n  at sftp_storage.py:145"),
        ("INFO", "Wiederhole Upload-Versuch (2/3)...", 2, None),
        ("INFO", "Upload erfolgreich nach 3 Versuchen", 2, None),
        ("CRITICAL", "Verschlüsselung fehlgeschlagen: Falsches Passwort", None, "cryptography.exceptions.InvalidKey\n  at encryptor.py:89\n  in encrypt_file()"),
        ("INFO", "Scheduler prüft Zeitpläne...", None, None),
        ("DEBUG", "Nächster geplanter Backup: 27.11.2025 22:00", None, None),
        ("WARNING", "Backup-Ziel fast voll: 95% belegt (450GB von 500GB)", None, None),
        ("INFO", "Automatische Rotation: Ältester Backup (ID=5) wird gelöscht", None, None),
        ("ERROR", "Datei kann nicht wiederhergestellt werden: Archiv beschädigt", 3, "py7zr.exceptions.Bad7zFile\n  at restore_engine.py:234"),
    ]

    # Zeitstempel variieren
    base_time = datetime.now()

    for i, (level, message, backup_id, details) in enumerate(test_logs):
        # Logs zeitlich verteilen (letzte 2 Stunden)
        timestamp_offset = timedelta(hours=2) / len(test_logs) * i

        # Manuell einfügen mit custom timestamp
        cursor = metadata_manager.connection.cursor()
        cursor.execute(
            """
            INSERT INTO logs (timestamp, level, message, backup_id, details)
            VALUES (?, ?, ?, ?, ?)
            """,
            (base_time - timedelta(hours=2) + timestamp_offset, level, message, backup_id, details),
        )

    metadata_manager.connection.commit()

    print(f"✓ {len(test_logs)} Test-Logs erstellt")

    # Zeige Anzahl
    count = metadata_manager.get_log_count()
    print(f"✓ Insgesamt {count} Logs in Datenbank")

    metadata_manager.disconnect()


if __name__ == "__main__":
    create_test_logs()
    print("\nStarte GUI...")

    # GUI starten
    from PyQt6.QtWidgets import QApplication
    from src.gui.main_window import MainWindow
    from src.gui.theme import apply_theme

    app = QApplication(sys.argv)
    app.setApplicationName("Scrat-Backup - Logs Test")
    apply_theme(app)

    window = MainWindow()
    # Direkt zum Logs-Tab wechseln
    window.tab_widget.setCurrentIndex(3)  # Index 3 = Logs-Tab
    window.show()

    sys.exit(app.exec())
