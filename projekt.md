Scrat-Backup

Implementierungsplan: Windows-Backup-Programm für Privatnutzer
1. Projektziele

Zielgruppe: Privatnutzer mit wenig technischen Kenntnissen.
Hauptfunktionen:

Sicherung der Windows-Bibliotheksordner, selektiv wählbar (Dokumente, Bilder, Musik, Videos, Desktop, Downloads).
Inkrementelle und Vollbackups mit Versionierung (3 Versionen).
Optionale Verschlüsselung und Passwortschutz.
Wiederherstellung einzelner Dateien oder ganzer Backups, unabhängig vom System/User.
Unterstützung für lokale USB-Laufwerke und Netzwerkprotokolle (SFTP, WebDAV).
Benutzerfreundliche GUI im Stil von Windows 11.
Lizenz GPLv3


2. Phasenplan
Phase 1: Anforderungen und Design

Anforderungsanalyse:

Klare Definition der Backup-Quellen (nur Bibliotheksordner).
Festlegung der Backup-Ziele (USB, SFTP, WebDAV, Rclone).
Definition der Benutzerinteraktion (GUI, Popups, Benachrichtigungen).

Technologieauswahl:

Programmiersprache: Python mit PyQt für die GUI.
Backup-Logik: Nutzung von Windows-APIs für schnelle Dateioperationen.
Verschlüsselung: AES-256 (benutzerfreundlich, sicher).
Komprimierung: ZIP oder 7z (schneller Kompromiss).

GUI-Design:

Programmname/Symbol: (ICON "Eichel) Scrat-Backup (Version)

Mockups für die Benutzeroberfläche (einfache Navigation, klare Optionen).
Integration von Windows-11-Designrichtlinien.

Phase 2: Entwicklung der Kernfunktionen

Backup-Modul:

Implementierung von Voll- und inkrementellen Backups.
Versionierung (3 Versionen).
Optionale Verschlüsselung und Passwortschutz.
Komprimierung für schnelle Backups.

Wiederherstellungsmodul:

Auswahl einzelner Dateien oder ganzer Backups.
Wiederherstellung auf beliebigen Systemen.
Option für Zeitpunkt-Wiederherstellung.

Planungsmodul:

Zeitpläne für täglich/wöchentlich/monatlich.
Automatische Sicherung beim Herunterfahren, oder Hochfahren.

Protokollierung:

Logdatei mit Fehlermeldungen und Erfolgsmeldungen. Fehlermeldungen schnell erkennbar.
Popup-Benachrichtigungen.

Phase 3: GUI-Implementierung

Hauptfenster:

Übersicht der Backup-Quellen und -Ziele.
Schaltflächen für manuelles Backup/Wiederherstellung.
Fortschrittsbalken für laufende Backups.

Einstellungen:

Optionen für Verschlüsselung, Komprimierung, Zeitpläne.
Auswahl der Backup-Ziele (USB, SFTP, WebDAV, Rclone).

Benachrichtigungen:

Popups bei Erfolg/Fehler.
Windows-Benachrichtigungscenter-Integration.

Phase 4: Testphase

Funktionstests:

Backup und Wiederherstellung auf verschiedenen Systemen.
Test der Versionierung und Verschlüsselung.
Überprüfung der Protokollierung und Benachrichtigungen.

Benutzerfreundlichkeitstests:

Test mit Privatnutzern (Feedback einholen).
Anpassung der GUI basierend auf Feedback.

Phase 5: Dokumentation und Veröffentlichung

Benutzerhandbuch:

Schritt-für-Schritt-Anleitung für Backup und Wiederherstellung.
Erklärung der Optionen (Verschlüsselung, Zeitpläne).

Technische Dokumentation:

Code-Kommentare und API-Beschreibungen.
Build-Anleitung für Entwickler.

Veröffentlichung:

Open-Source-Repository (z. B. GitHub).
Installationspakete für Windows 10/11.

Beispielstruktur:

scrat-backup/
│
├── LICENSE                  # GPLv3 Lizenztext
├── README.md                # Projektbeschreibung, Installation, Nutzung
├── requirements.txt         # Python-Abhängigkeiten
│
├── src/                     # Quellcode
│   ├── __init__.py
│   ├── main.py              # Hauptskript (Startpunkt der GUI)
│   ├── gui/                 # GUI-Komponenten
│   │   ├── __init__.py
│   │   ├── main_window.py   # Hauptfenster
│   │   ├── settings_window.py # Einstellungen
│   │   └── notification.py  # Benachrichtigungen
│   ├── core/                # Kernfunktionen
│   │   ├── __init__.py
│   │   ├── backup.py        # Backup-Logik (Voll/inkrementell)
│   │   ├── restore.py       # Wiederherstellung
│   │   ├── scheduler.py     # Zeitplanung
│   │   ├── encryption.py    # Verschlüsselung (AES-256)
│   │   └── logging.py       # Protokollierung
│   └── cloud/               # Cloud-Integration
│       ├── __init__.py
│       ├── sftp.py          # SFTP-Unterstützung
│       ├── webdav.py        # WebDAV-Unterstützung
│       └── rclone.py        # Rclone-Integration (optional)
│
├── tests/                   # Unittests
│   ├── __init__.py
│   ├── test_backup.py
│   └── test_restore.py
│
└── docs/                    # Dokumentation
    ├── user_guide.md        # Benutzerhandbuch
    └── developer_guide.md   # Entwicklerdokumentation
