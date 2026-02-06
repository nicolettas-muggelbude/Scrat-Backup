"""
Scrat-Backup - Entry Point
Windows Backup-Tool für Privatnutzer
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Projekt-Root zum Python-Path hinzufügen (damit 'from src.…' funktioniert
# unabhängig davon, ob das Skript direkt oder als Modul gestartet wird)
_project_root = str(Path(__file__).resolve().parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from PySide6.QtCore import QLibraryInfo, QTranslator  # noqa: E402
from PySide6.QtGui import QIcon  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from src.core.config_manager import ConfigManager  # noqa: E402
from src.gui.main_window import MainWindow  # noqa: E402
from src.gui.theme_manager import ThemeManager  # noqa: E402
from src.gui.wizard_v2 import SetupWizardV2  # noqa: E402

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
        action = wizard_config.get("action", "backup")

        # Bei Ersteinrichtung oder Änderung: vorherige Quellen/Ziele VOLLSTÄNDIG LÖSCHEN
        # Bei "add_destination": nur neue Destination hinzufügen
        if action in ("backup", "edit"):
            logger.info(f"Aktion '{action}': Lösche alte Quellen und Ziele")
            config_manager.config["sources"] = []
            config_manager.config["destinations"] = []

            # WICHTIG: Explizit speichern damit es persistent ist
            config_manager.save()
            logger.info("Alte Einträge gelöscht und gespeichert")

        # 1. Quellen in Config speichern
        sources = wizard_config.get("sources", [])
        excludes = wizard_config.get("excludes", [])

        # Stelle sicher dass sources-Array existiert
        if "sources" not in config_manager.config:
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


def start_backup_after_wizard(wizard_config: dict) -> None:
    """
    Startet erstes Backup nach Wizard-Abschluss.
    Muster aus backup_tab.py: Password-Dialog → BackupConfig → Thread.
    """
    import threading
    import time

    from PySide6.QtWidgets import QApplication, QMessageBox

    from src.core.backup_engine import BackupConfig, BackupEngine
    from src.core.metadata_manager import MetadataManager
    from src.gui.password_dialog import get_password

    # Passwort vom User holen
    password, ok = get_password(
        None,
        title="Backup-Passwort",
        message="Bitte gib das Passwort für dein Backup ein:",
        show_save_option=True,
    )

    if not ok or not password:
        QMessageBox.warning(
            None,
            "Abgebrochen",
            "Backup wurde abgebrochen – kein Passwort eingegeben.",
        )
        return

    # Quellen aus gespeicherter Config lesen
    config_manager = ConfigManager()
    sources = [
        Path(s["path"]) for s in config_manager.config.get("sources", []) if s.get("enabled", True)
    ]

    if not sources:
        QMessageBox.warning(None, "Fehler", "Keine Backup-Quellen konfiguriert.")
        return

    # Ziel aus gespeicherter Config (letztes = soeben vom Wizard gespeichertes)
    destinations = config_manager.config.get("destinations", [])
    if not destinations:
        QMessageBox.warning(None, "Fehler", "Kein Backup-Ziel konfiguriert.")
        return

    destination = destinations[-1]
    dest_config = destination.get("config", {})
    dest_type = destination.get("type", "local")

    # Zielpfad zusammenbauen
    # Für Remote-Backups (WebDAV, SFTP): Lokalen Temp-Pfad nutzen, Upload später
    # Für lokale Backups (local, usb): Finalen Pfad direkt nutzen

    if dest_type in ("local", "usb"):
        # Lokale Backups: Finaler Dateisystem-Pfad
        drive = dest_config.get("drive", "")
        if drive:
            sub_path = dest_config.get("path", "")
            dest_path = Path(drive) / sub_path if sub_path else Path(drive)
        else:
            dest_path = Path(dest_config.get("path", str(Path.home() / "scrat-backups")))
    else:
        # Remote-Backups: Lokaler Temp-Pfad für BackupEngine
        # (BackupEngine arbeitet nur lokal, Upload erfolgt danach)
        dest_path = Path.home() / "scrat-backup" / "Backup"
        logger.info(f"Remote-Backup ({dest_type}): Nutze lokalen Temp-Pfad {dest_path}")

    # Ausschluss-Muster
    excludes = set(wizard_config.get("excludes", []))

    # Metadaten-DB Pfad
    db_path = Path.home() / ".scrat-backup" / "metadata.db"

    backup_config = BackupConfig(
        sources=sources,
        destination_path=dest_path,
        destination_type=dest_type,
        password=password,
        exclude_patterns=excludes if excludes else None,
        compression_level=5,
    )

    logger.info(f"Backup starten: {len(sources)} Quellen → {dest_path} (Typ: {dest_type})")

    from PySide6.QtWidgets import QProgressDialog

    from src.core.backup_engine import BackupProgress

    # Gemeinsamer Zustand zwischen Thread und Hauptthread
    shared: dict[str, Any] = {"progress": None, "error": None, "result": None}

    def _progress_callback(progress: BackupProgress):
        shared["progress"] = progress

    def _run():
        metadata_manager = None
        try:
            metadata_manager = MetadataManager(db_path)
            engine = BackupEngine(
                metadata_manager=metadata_manager,
                config=backup_config,
                progress_callback=_progress_callback,
            )
            shared["result"] = engine.create_full_backup()
            logger.info(f"Backup erfolgreich: {shared['result']}")
        except Exception as e:
            logger.error(f"Backup fehlgeschlagen: {e}", exc_info=True)
            shared["error"] = str(e)
        finally:
            if metadata_manager:
                metadata_manager.disconnect()

    # Fortschritts-Dialog (nicht schließbar, bleibt oben bis Backup fertig)
    from PySide6.QtCore import Qt as QtCore

    progress_dialog = QProgressDialog("Backup wird erstellt...", None, 0, 100)
    progress_dialog.setWindowTitle("Scrat-Backup – Erstes Backup")
    progress_dialog.setMinimumWidth(420)
    progress_dialog.setCancelButton(None)  # Kein Abbrechen-Button
    progress_dialog.setWindowFlags(
        QtCore.WindowType.Dialog
        | QtCore.WindowType.WindowStaysOnTopHint
        | QtCore.WindowType.CustomizeWindowHint
        | QtCore.WindowType.WindowTitleHint
        # kein WindowCloseButtonHint → kein X-Button
    )
    progress_dialog.show()

    thread = threading.Thread(target=_run, daemon=False)
    thread.start()

    # Auf Thread warten, dabei Events verarbeiten und Dialog aktualisieren
    while thread.is_alive():
        p = shared.get("progress")
        if p:
            if p.phase == "scanning":
                progress_dialog.setLabelText(f"Scanne Dateien...\n{p.current_file or ''}")
                progress_dialog.setValue(5)
            elif p.phase == "compressing":
                if p.files_total > 0:
                    pct = int(10 + (p.files_processed / p.files_total) * 65)
                else:
                    pct = 10
                progress_dialog.setLabelText(
                    f"Komprimiere... {p.files_processed}/{p.files_total} Dateien\n"
                    f"{p.current_file or ''}"
                )
                progress_dialog.setValue(pct)
            elif p.phase == "encrypting":
                progress_dialog.setLabelText("Verschlüssele Backup...")
                progress_dialog.setValue(80)
            elif p.phase == "saving_metadata":
                progress_dialog.setLabelText("Speichere Metadaten...")
                progress_dialog.setValue(95)

        QApplication.processEvents()
        time.sleep(0.1)

    progress_dialog.close()

    # Ergebnis anzeigen & Remote-Upload bei Bedarf
    if shared.get("error"):
        QMessageBox.critical(
            None,
            "Backup fehlgeschlagen",
            f"Das Backup konnte nicht erstellt werden:\n\n{shared['error']}",
        )
    else:
        result = shared.get("result")

        # Bei Remote-Backups (WebDAV, SFTP, etc.): Upload durchführen
        if dest_type not in ("local", "usb"):
            logger.info(f"Remote-Backup ({dest_type}): Starte Upload...")

            # Echtes Ziel für User-Anzeige (nicht Temp-Pfad)
            if dest_type in ("webdav", "nextcloud"):
                remote_display = f"{dest_config.get('url', '')}/{dest_config.get('path', 'Backups')}"
            elif dest_type == "sftp":
                remote_display = f"{dest_config.get('host', '')}:{dest_config.get('path', '')}"
            else:
                remote_display = dest_config.get("path", "Remote-Server")

            # Backup-Pfad konstruieren (BackupResult hat kein backup_path Attribut)
            local_backup_path = dest_path / result.backup_id if result else None

            upload_success = _upload_to_remote(result, dest_type, dest_config, dest_path)

            if upload_success:
                QMessageBox.information(
                    None,
                    "Backup abgeschlossen",
                    f"Das Backup wurde erfolgreich erstellt und hochgeladen!\n\n"
                    f"Quellen: {len(sources)}\n"
                    f"Ziel: {dest_type.upper()}\n"
                    f"Pfad: {remote_display}",
                )
            else:
                QMessageBox.warning(
                    None,
                    "Backup lokal, Upload fehlgeschlagen",
                    f"Das Backup wurde lokal erstellt, aber der Upload zu {dest_type.upper()} ist fehlgeschlagen.\n\n"
                    f"Remote-Ziel: {remote_display}\n"
                    f"Lokaler Pfad: {local_backup_path}\n"
                    f"Bitte Upload manuell durchführen oder Einstellungen prüfen.",
                )
        else:
            QMessageBox.information(
                None,
                "Backup abgeschlossen",
                f"Das erste Backup wurde erfolgreich erstellt!\n\n"
                f"Quellen: {len(sources)}\n"
                f"Ziel: {dest_path}",
            )


def _upload_to_remote(backup_result, dest_type: str, dest_config: dict, local_dest_path: Path) -> bool:
    """
    Lädt Backup-Dateien zu Remote-Ziel hoch (WebDAV, SFTP, etc.)

    Args:
        backup_result: BackupResult mit backup_id
        dest_type: Typ des Ziels (webdav, sftp, etc.)
        dest_config: Destination-Config mit URL, Credentials, etc.
        local_dest_path: Lokaler Pfad wo Backup liegt (z.B. ~/scrat-backup/Backup)

    Returns:
        True bei Erfolg, False bei Fehler
    """
    try:
        if not backup_result or not hasattr(backup_result, "backup_id"):
            logger.error("Kein BackupResult oder backup_id verfügbar")
            return False

        # Backup-Pfad konstruieren: dest_path / backup_id
        local_backup_dir = local_dest_path / backup_result.backup_id
        if not local_backup_dir.exists():
            logger.error(f"Lokales Backup-Verzeichnis nicht gefunden: {local_backup_dir}")
            return False

        # Remote-Ziel für Logging
        if dest_type in ("webdav", "nextcloud"):
            remote_target = f"{dest_config.get('url', '')}/{dest_config.get('path', 'Backups')}"
        elif dest_type == "sftp":
            remote_target = f"{dest_config.get('host', '')}:{dest_config.get('path', '')}"
        else:
            remote_target = dest_type

        logger.info(f"Starte Upload von {local_backup_dir} nach {dest_type}://{remote_target}")

        # Storage Backend initialisieren basierend auf Typ
        # Nextcloud verwendet WebDAV-Backend
        if dest_type in ("webdav", "nextcloud"):
            from storage.webdav_storage import WebDAVStorage

            storage = WebDAVStorage(
                url=dest_config.get("url", ""),
                username=dest_config.get("user", ""),
                password=dest_config.get("password", ""),
                base_path=dest_config.get("path", "Backups"),
            )
        elif dest_type == "sftp":
            from storage.sftp_storage import SFTPStorage

            storage = SFTPStorage(
                host=dest_config.get("host", ""),
                port=dest_config.get("port", 22),
                username=dest_config.get("user", ""),
                password=dest_config.get("password", ""),
                base_path=dest_config.get("path", ""),
            )
        else:
            logger.warning(f"Upload für Typ '{dest_type}' noch nicht implementiert")
            return False

        # Verbindung testen
        if not storage.connect():
            logger.error(f"Verbindung zu {dest_type} fehlgeschlagen")
            return False

        # Alle Dateien im Backup-Verzeichnis hochladen
        uploaded_files = 0
        for file_path in local_backup_dir.rglob("*"):
            if file_path.is_file():
                # Relativer Pfad im Backup-Verzeichnis
                rel_path = file_path.relative_to(local_backup_dir)
                remote_path = f"{backup_result.backup_id}/{rel_path}"

                logger.info(f"Uploade: {file_path.name} → {remote_path}")
                if storage.upload_file(str(file_path), remote_path):
                    uploaded_files += 1
                else:
                    logger.error(f"Upload fehlgeschlagen: {file_path.name}")

        storage.disconnect()

        if uploaded_files > 0:
            logger.info(f"Upload abgeschlossen: {uploaded_files} Datei(en)")
            return True
        else:
            logger.error("Keine Dateien hochgeladen")
            return False

    except Exception as e:
        logger.error(f"Fehler beim Remote-Upload: {e}", exc_info=True)
        return False


def run_gui() -> int:
    """
    Startet GUI-Anwendung

    Der Wizard ist IMMER der Einstiegspunkt.
    Im Wizard kann dann zwischen Normal-Modus und Experten-Modus gewählt werden.

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

    # App-Icon setzen (wird von allen Fenstern geerbt)
    icon_path = Path(__file__).parent.parent / "assets" / "icons" / "scrat.ico"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

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

    # WIZARD IST IMMER DER EINSTIEGSPUNKT
    # (Im Wizard wird dann zwischen Normal-Modus und Experten-Modus gewählt)
    logger.info(">>> WIZARD V2 WIRD GESTARTET <<<")

    # Setup-Wizard V2 anzeigen (mit neuen Pages)
    wizard = SetupWizardV2()
    if wizard.exec():
        # Wizard abgeschlossen
        config = wizard.get_config()
        sources = config.get("sources", [])
        logger.info(f"Setup abgeschlossen: {len(sources)} Quellen konfiguriert")

        # Speichere Konfiguration
        try:
            save_wizard_config(config)
            logger.info("Konfiguration erfolgreich gespeichert")
        except Exception as e:
            logger.error(f"Fehler beim Speichern der Konfiguration: {e}", exc_info=True)
            from PySide6.QtWidgets import QMessageBox

            QMessageBox.warning(
                None,
                "Warnung",
                f"Die Konfiguration konnte nicht vollständig gespeichert werden:\n{e}\n\n"
                f"Das Hauptfenster wird trotzdem geöffnet.",
            )

        # Backup starten wenn gewünscht
        if config.get("start_backup_now"):
            logger.info("Backup wird nach Wizard gestartet...")
            start_backup_after_wizard(config)

        # Tray oder MainWindow starten (abhängig von Wizard-Config)
        if config.get("start_tray", True):
            logger.info("Starte Tray im Hintergrund...")
            # TODO: Tray-Start implementieren
            # from gui.system_tray import SystemTray
            # tray = SystemTray()
            # tray.show()
            logger.warning("Tray-Start noch nicht implementiert - beende")
            return 0
        else:
            logger.info("Öffne Hauptfenster (kein Tray gewünscht)...")
            window = MainWindow()
            window.show()
    else:
        # Wizard abgebrochen
        logger.info("Setup abgebrochen")
        return 1

    logger.info("GUI gestartet - Event-Loop läuft")

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

    # GUI starten (Wizard ist IMMER der Einstiegspunkt)
    try:
        return run_gui()
    except Exception as e:
        logger.error(f"Kritischer Fehler: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
