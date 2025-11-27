"""
Metadata Manager für Scrat-Backup
Verwaltet SQLite-Datenbank mit Backup-Metadaten
"""

import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class MetadataManager:
    """
    Verwaltet Backup-Metadaten in SQLite-Datenbank

    Verantwortlichkeiten:
    - Schema-Erstellung und Migrations
    - Backup-Records erstellen/lesen/aktualisieren/löschen
    - Datei-Index verwalten
    - Backup-Suche und Abfragen
    """

    SCHEMA_VERSION = 1

    def __init__(self, db_path: Path):
        """
        Initialisiert Metadata-Manager

        Args:
            db_path: Pfad zur SQLite-Datenbank
        """
        self.db_path = db_path
        self.connection: Optional[sqlite3.Connection] = None

        # Sicherstellen, dass Verzeichnis existiert
        db_path.parent.mkdir(parents=True, exist_ok=True)

        # Verbindung herstellen und Schema initialisieren
        self.connect()
        self._initialize_schema()

    def connect(self) -> None:
        """Stellt Verbindung zur Datenbank her"""
        if self.connection is None:
            self.connection = sqlite3.connect(
                self.db_path, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
            )
            self.connection.row_factory = sqlite3.Row  # Dict-like access

            # Aktiviere Foreign Key Constraints
            self.connection.execute("PRAGMA foreign_keys = ON")

            logger.info(f"Datenbank-Verbindung hergestellt: {self.db_path}")

    def disconnect(self) -> None:
        """Schließt Datenbank-Verbindung"""
        if self.connection:
            self.connection.close()
            self.connection = None
            logger.info("Datenbank-Verbindung geschlossen")

    def _initialize_schema(self) -> None:
        """Erstellt Datenbank-Schema falls noch nicht vorhanden"""
        cursor = self.connection.cursor()

        # Backups-Tabelle
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS backups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                type TEXT NOT NULL CHECK(type IN ('full', 'incremental')),
                base_backup_id INTEGER,
                destination_type TEXT NOT NULL,
                destination_path TEXT NOT NULL,
                status TEXT NOT NULL CHECK(status IN ('running', 'completed', 'failed', 'partial')),
                files_total INTEGER DEFAULT 0,
                files_processed INTEGER DEFAULT 0,
                size_original INTEGER DEFAULT 0,
                size_compressed INTEGER DEFAULT 0,
                encryption_key_hash TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                completed_at DATETIME,
                error_message TEXT,
                FOREIGN KEY (base_backup_id) REFERENCES backups(id) ON DELETE SET NULL
            )
        """
        )

        # Backup-Dateien-Tabelle
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS backup_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                backup_id INTEGER NOT NULL,
                source_path TEXT NOT NULL,
                relative_path TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                modified_timestamp DATETIME NOT NULL,
                archive_name TEXT NOT NULL,
                archive_path TEXT NOT NULL,
                is_deleted BOOLEAN DEFAULT 0,
                checksum TEXT,
                FOREIGN KEY (backup_id) REFERENCES backups(id) ON DELETE CASCADE
            )
        """
        )

        # Quellen-Tabelle
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                windows_path TEXT NOT NULL,
                enabled BOOLEAN DEFAULT 1,
                exclude_patterns TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # Ziele-Tabelle
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS destinations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                type TEXT NOT NULL CHECK(type IN ('usb', 'sftp', 'webdav', 'rclone')),
                config TEXT NOT NULL,
                enabled BOOLEAN DEFAULT 1,
                last_connected DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # Zeitpläne-Tabelle
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS schedules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                enabled BOOLEAN DEFAULT 1,
                frequency TEXT NOT NULL
                    CHECK(frequency IN ('daily', 'weekly', 'monthly', 'startup', 'shutdown')),
                time TEXT,
                days TEXT,
                source_ids TEXT NOT NULL,
                destination_id INTEGER NOT NULL,
                last_run DATETIME,
                next_run DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (destination_id) REFERENCES destinations(id) ON DELETE CASCADE
            )
        """
        )

        # Logs-Tabelle
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                level TEXT NOT NULL
                    CHECK(level IN ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')),
                message TEXT NOT NULL,
                backup_id INTEGER,
                details TEXT,
                FOREIGN KEY (backup_id) REFERENCES backups(id) ON DELETE SET NULL
            )
        """
        )

        # Indizes für Performance
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_backup_files_backup_id
            ON backup_files(backup_id)
        """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_backup_files_source_path
            ON backup_files(source_path)
        """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_backups_timestamp
            ON backups(timestamp DESC)
        """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_backups_status
            ON backups(status)
        """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_logs_timestamp
            ON logs(timestamp DESC)
        """
        )

        # Schema-Version speichern
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_info (
                version INTEGER PRIMARY KEY,
                applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        cursor.execute(
            "INSERT OR IGNORE INTO schema_info (version) VALUES (?)", (self.SCHEMA_VERSION,)
        )

        self.connection.commit()
        logger.info(f"Datenbank-Schema initialisiert (Version {self.SCHEMA_VERSION})")

    def create_backup_record(
        self,
        backup_type: str,
        destination_type: str,
        destination_path: str,
        encryption_key_hash: str,
        base_backup_id: Optional[int] = None,
    ) -> int:
        """
        Erstellt neuen Backup-Eintrag

        Args:
            backup_type: 'full' oder 'incremental'
            destination_type: 'usb', 'sftp', 'webdav', 'rclone'
            destination_path: Pfad zum Backup-Ziel
            encryption_key_hash: Hash des Verschlüsselungs-Keys
            base_backup_id: Bei incremental: ID des Base-Backups

        Returns:
            ID des erstellten Backup-Eintrags
        """
        cursor = self.connection.cursor()

        cursor.execute(
            """
            INSERT INTO backups (
                timestamp, type, base_backup_id, destination_type,
                destination_path, status, encryption_key_hash
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                datetime.now(),
                backup_type,
                base_backup_id,
                destination_type,
                destination_path,
                "running",
                encryption_key_hash,
            ),
        )

        self.connection.commit()
        backup_id = cursor.lastrowid

        logger.info(f"Backup-Record erstellt: ID={backup_id}, Type={backup_type}")
        return backup_id

    def update_backup_progress(
        self, backup_id: int, files_processed: int, size_original: int, size_compressed: int
    ) -> None:
        """
        Aktualisiert Backup-Fortschritt

        Args:
            backup_id: ID des Backups
            files_processed: Anzahl verarbeiteter Dateien
            size_original: Original-Größe in Bytes
            size_compressed: Komprimierte Größe in Bytes
        """
        cursor = self.connection.cursor()

        cursor.execute(
            """
            UPDATE backups
            SET files_processed = ?,
                size_original = ?,
                size_compressed = ?
            WHERE id = ?
        """,
            (files_processed, size_original, size_compressed, backup_id),
        )

        self.connection.commit()

    def mark_backup_completed(self, backup_id: int, files_total: int) -> None:
        """
        Markiert Backup als abgeschlossen

        Args:
            backup_id: ID des Backups
            files_total: Gesamtanzahl der Dateien
        """
        cursor = self.connection.cursor()

        cursor.execute(
            """
            UPDATE backups
            SET status = 'completed',
                files_total = ?,
                completed_at = ?
            WHERE id = ?
        """,
            (files_total, datetime.now(), backup_id),
        )

        self.connection.commit()
        logger.info(f"Backup abgeschlossen: ID={backup_id}, Files={files_total}")

    def mark_backup_failed(self, backup_id: int, error_message: str) -> None:
        """
        Markiert Backup als fehlgeschlagen

        Args:
            backup_id: ID des Backups
            error_message: Fehlermeldung
        """
        cursor = self.connection.cursor()

        cursor.execute(
            """
            UPDATE backups
            SET status = 'failed',
                error_message = ?,
                completed_at = ?
            WHERE id = ?
        """,
            (error_message, datetime.now(), backup_id),
        )

        self.connection.commit()
        logger.error(f"Backup fehlgeschlagen: ID={backup_id}, Error={error_message}")

    def add_file_to_backup(
        self,
        backup_id: int,
        source_path: str,
        relative_path: str,
        file_size: int,
        modified_timestamp: datetime,
        archive_name: str,
        archive_path: str,
        is_deleted: bool = False,
        checksum: Optional[str] = None,
    ) -> int:
        """
        Fügt Datei zu Backup hinzu

        Args:
            backup_id: ID des Backups
            source_path: Absoluter Quell-Pfad
            relative_path: Relativer Pfad
            file_size: Dateigröße in Bytes
            modified_timestamp: Änderungs-Zeitstempel
            archive_name: Name des Archivs
            archive_path: Pfad innerhalb des Archivs
            is_deleted: Ob Datei gelöscht wurde (für incremental)
            checksum: Optional SHA-256 Checksum

        Returns:
            ID des erstellten Datei-Eintrags
        """
        cursor = self.connection.cursor()

        cursor.execute(
            """
            INSERT INTO backup_files (
                backup_id, source_path, relative_path, file_size,
                modified_timestamp, archive_name, archive_path,
                is_deleted, checksum
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                backup_id,
                source_path,
                relative_path,
                file_size,
                modified_timestamp,
                archive_name,
                archive_path,
                is_deleted,
                checksum,
            ),
        )

        self.connection.commit()
        return cursor.lastrowid

    def get_backup(self, backup_id: int) -> Optional[Dict[str, Any]]:
        """
        Holt Backup-Informationen

        Args:
            backup_id: ID des Backups

        Returns:
            Dict mit Backup-Informationen oder None
        """
        cursor = self.connection.cursor()

        cursor.execute(
            """
            SELECT * FROM backups WHERE id = ?
        """,
            (backup_id,),
        )

        row = cursor.fetchone()
        return dict(row) if row else None

    def get_all_backups(
        self, destination_id: Optional[int] = None, status: Optional[str] = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Holt alle Backups (optional gefiltert)

        Args:
            destination_id: Optional Filter nach Ziel
            status: Optional Filter nach Status
            limit: Maximale Anzahl Ergebnisse

        Returns:
            Liste von Backup-Dicts
        """
        cursor = self.connection.cursor()

        query = "SELECT * FROM backups WHERE 1=1"
        params = []

        if destination_id is not None:
            query += " AND destination_id = ?"
            params.append(destination_id)

        if status is not None:
            query += " AND status = ?"
            params.append(status)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    def get_backup_files(self, backup_id: int) -> List[Dict[str, Any]]:
        """
        Holt alle Dateien eines Backups

        Args:
            backup_id: ID des Backups

        Returns:
            Liste von Datei-Dicts
        """
        cursor = self.connection.cursor()

        cursor.execute(
            """
            SELECT * FROM backup_files
            WHERE backup_id = ?
            ORDER BY relative_path
        """,
            (backup_id,),
        )

        return [dict(row) for row in cursor.fetchall()]

    def search_files(self, pattern: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Sucht Dateien über alle Backups

        Args:
            pattern: Such-Pattern (SQL LIKE)
            limit: Maximale Anzahl Ergebnisse

        Returns:
            Liste von Datei-Dicts mit Backup-Info
        """
        cursor = self.connection.cursor()

        cursor.execute(
            """
            SELECT
                bf.*,
                b.timestamp as backup_timestamp,
                b.type as backup_type,
                b.status as backup_status
            FROM backup_files bf
            JOIN backups b ON bf.backup_id = b.id
            WHERE bf.source_path LIKE ?
            AND b.status = 'completed'
            ORDER BY b.timestamp DESC
            LIMIT ?
        """,
            (f"%{pattern}%", limit),
        )

        return [dict(row) for row in cursor.fetchall()]

    def delete_backup(self, backup_id: int) -> bool:
        """
        Löscht Backup und zugehörige Dateien (CASCADE)

        Args:
            backup_id: ID des zu löschenden Backups

        Returns:
            True bei Erfolg
        """
        cursor = self.connection.cursor()

        cursor.execute("DELETE FROM backups WHERE id = ?", (backup_id,))
        self.connection.commit()

        deleted = cursor.rowcount > 0
        if deleted:
            logger.info(f"Backup gelöscht: ID={backup_id}")
        return deleted

    def get_statistics(self) -> Dict[str, Any]:
        """
        Holt Datenbank-Statistiken

        Returns:
            Dict mit Statistiken
        """
        cursor = self.connection.cursor()

        stats = {}

        # Anzahl Backups
        cursor.execute("SELECT COUNT(*) as count FROM backups")
        stats["total_backups"] = cursor.fetchone()["count"]

        # Anzahl erfolgreicher Backups
        cursor.execute("SELECT COUNT(*) as count FROM backups WHERE status = 'completed'")
        stats["completed_backups"] = cursor.fetchone()["count"]

        # Gesamtgröße (original)
        cursor.execute("SELECT SUM(size_original) as total FROM backups WHERE status = 'completed'")
        stats["total_size_original"] = cursor.fetchone()["total"] or 0

        # Gesamtgröße (komprimiert)
        cursor.execute(
            "SELECT SUM(size_compressed) as total FROM backups WHERE status = 'completed'"
        )
        stats["total_size_compressed"] = cursor.fetchone()["total"] or 0

        # Anzahl Dateien
        cursor.execute("SELECT COUNT(*) as count FROM backup_files")
        stats["total_files"] = cursor.fetchone()["count"]

        return stats

    def __enter__(self):
        """Context Manager: Eintritt"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context Manager: Austritt"""
        self.disconnect()
        return False
