<div align="center">

<img src="assets/icons/scrat-256.png" alt="Scrat-Backup Logo" width="128"/>

# 🐿️ Scrat-Backup

**Schütze deine Daten wie Scrat seine Eicheln!**

*Ein benutzerfreundliches, plattformübergreifendes Backup-Programm mit Verschlüsselung*

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Development Status](https://img.shields.io/badge/status-beta%20(v0.3.11)-yellow)](https://github.com/nicolettas-muggelbude/Scrat-Backup/releases/latest)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-blue)](#)

[Features](#-features) •
[Installation](#-installation) •
[Verwendung](#-verwendung) •
[Entwicklung](#-entwicklung) •
[Roadmap](#-roadmap) •
[Beitragen](#-beitragen)

</div>

---

## 📋 Übersicht

**Scrat-Backup** ist ein **plattformübergreifendes Open-Source-Backup-Tool** für **Privatnutzer**. Wie ein Eichhörnchen seine Eicheln für den Winter sichert, schützt Scrat-Backup deine wertvollen Daten mit **verschlüsselten, komprimierten Backups**.

**Unterstützte Plattformen:**
- 🪟 **Windows** 10/11
- 🐧 **Linux** (Ubuntu, Fedora, Arch und weitere)
- 🍎 **macOS** (10.15+, experimentell)

### 🎯 Für wen ist Scrat-Backup?

- 👨‍💼 **Privatnutzer** ohne tiefe technische Kenntnisse
- 🏠 **Heimanwender** mit wichtigen Dokumenten, Fotos, Videos
- 🔒 **Sicherheitsbewusste** die Verschlüsselung schätzen
- 💾 **Multi-Storage-Nutzer** (USB, NAS, Cloud)
- 🌍 **Cross-Platform-Nutzer** (gleiche Backups auf allen Systemen)

---

## ✨ Features

### 🔐 Sicherheit
- ✅ **AES-256-GCM Verschlüsselung** für alle Backups
- ✅ **PBKDF2** Key-Derivation (100.000 Iterationen)
- ✅ **Sichere Passwort-Speicherung** (Windows Credential Manager / Linux GNOME Keyring / macOS Schlüsselbund)
- ✅ **SFTP Host-Key-Verifizierung** mit `RejectPolicy` + System Known-Hosts

### 💾 Backup-Funktionen
- ✅ **Vollbackups** und **Inkrementelle Backups**
- ✅ **Versionierung** (konfigurierbare Rotationsanzahl)
- ✅ **Automatische Rotation** (nur bei Scheduler-Backups, manuelle Backups werden nie gelöscht)
- ✅ **metadata.db auf Backup-Ziel** – Restore auf neuem System ohne Originalrechner möglich
- ✅ **Komprimierung** mit zstd Level 1 (~41s für 2 GB)
- ✅ **Chunked Encryption** (64 MB Chunks, kein OOM bei großen Dateien)
- ✅ **Exclude-Patterns** (z.B. `*.tmp`, `node_modules/`)

### 🗄️ Storage-Backends
- 💾 **USB / Lokale Laufwerke** – automatische Laufwerk-Erkennung (Win/Linux/macOS)
- 🌐 **SFTP (SSH)** – für Remote-Server
- ☁️ **WebDAV / Nextcloud** – inkl. ownCloud, SharePoint
- 🚀 **Rclone** – 40+ Cloud-Provider (Google Drive, Dropbox, OneDrive, S3 …)
- 🏢 **SMB/CIFS** – Windows-Netzwerkfreigaben, Synology, QNAP

### 🔄 Wiederherstellung
- ✅ **Restore-Flow im Wizard** – direkt aus dem Setup-Assistenten
- ✅ **DB-Modus** (vorhandene Config) und **Verzeichnis-Modus** (neues System)
- ✅ **Fortschrittsanzeige** mit Phase, Dateiname, Zähler

### 🖥️ Benutzeroberfläche
- ✅ **Moderner Setup-Wizard** mit Template-System (7 Templates)
- ✅ **Dark Mode** mit automatischer System-Erkennung
- ✅ **System Tray** – läuft im Hintergrund, Kontextmenü
- ✅ **Auto-Updater** – prüft täglich auf neue Versionen
- ✅ **Vollständige Tastatur-Navigation**
- ✅ **Deutsche Lokalisierung** (Qt-Übersetzungen)

### ⏰ Automatisierung
- ✅ **Zeitpläne** (Täglich, Wöchentlich, Monatlich, bei Start)
- ✅ **Scheduler-Worker** im Hintergrund
- ✅ **Missed-Backup-Detection**

---

## 📦 Installation

### 🎉 Aktuelle Version: v0.3.11-beta

**[→ Zum Download](https://github.com/nicolettas-muggelbude/Scrat-Backup/releases/latest)**

#### 🪟 Windows 10/11

1. [`ScratBackup-vX.X.X-Setup.exe`](https://github.com/nicolettas-muggelbude/Scrat-Backup/releases/latest) herunterladen
2. Installer ausführen – **kein Administratorrecht erforderlich**
3. Scrat-Backup startet automatisch nach der Installation

> Installiert nach `%LocalAppData%\Scrat-Backup`

#### 🐧 Linux (AppImage)

```bash
# AppImage herunterladen und ausführbar machen
chmod +x ScratBackup-vX.X.X-x86_64.AppImage
./ScratBackup-vX.X.X-x86_64.AppImage
```

**Ubuntu/Debian – falls GUI nicht startet:**
```bash
sudo apt install libxcb-cursor0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 \
                 libxcb-randr0 libxcb-render-util0 libxcb-xinerama0 libxcb-xfixes0
```

#### Aus dem Quellcode (alle Plattformen)

```bash
git clone https://github.com/nicolettas-muggelbude/Scrat-Backup.git
cd Scrat-Backup
python3 -m venv venv
source venv/bin/activate        # Linux/macOS
# venv\Scripts\activate         # Windows
pip install -r requirements.txt
python3 src/main.py
```

**Zusätzliche System-Pakete (Linux):**
```bash
sudo apt install python3-keyring libsecret-1-0 smbclient cron
pip install secretstorage
```

---

## 🎮 Verwendung

### Erste Schritte

1. **Setup-Wizard** öffnet sich beim Start
2. **Aktion wählen:** Backup einrichten, ändern, Wiederherstellen oder Experten-Modus
3. **Quellen** wählen (Dokumente, Bilder, eigene Ordner)
4. **Backup-Ziel** auswählen (USB, Cloud, NAS …)
5. **Zeitplan** konfigurieren (optional)
6. **Passwort** festlegen (wird sicher im Schlüsselbund gespeichert)
7. **Fertig!** – Scrat-Backup läuft im System Tray

### Backup erstellen

```
Tray-Icon → "Backup starten"
oder: Wizard → Experten-Modus → Backup-Tab
```

### Dateien wiederherstellen

```
Tray-Icon → "Wiederherstellen"
oder: Wizard → "Backup wiederherstellen"
```

---

## 🛠️ Technologie-Stack

| Komponente | Technologie | Version |
|------------|-------------|---------|
| **Sprache** | Python | 3.12+ |
| **GUI** | PySide6 (Qt6) | 6.6.0+ |
| **Verschlüsselung** | cryptography (AES-256-GCM) | 41.0.0+ |
| **Komprimierung** | py7zr (zstd Level 1) | 1.0.0+ |
| **Datenbank** | SQLite | built-in |
| **SFTP** | paramiko | 3.4.0+ |
| **WebDAV** | webdavclient3 | 3.14.6+ |
| **SMB** | smbprotocol | 1.12.0+ |
| **Passwörter** | keyring | 24.0.0+ |
| **Testing** | pytest | 7.4.0+ |

---

## 🔧 Entwicklung

### Projektstruktur

```
scrat-backup/
├── src/
│   ├── main.py                       # Entry Point
│   ├── gui/
│   │   ├── wizard_v2.py              # SetupWizardV2, alle Wizard-Seiten
│   │   ├── wizard_pages.py           # StartPage, SourceSelectionPage
│   │   ├── dynamic_template_form.py  # Formular aus Template-ui_fields
│   │   ├── update_dialog.py          # Auto-Updater Dialog
│   │   ├── theme_manager.py          # Dark/Light Mode
│   │   └── ...
│   ├── core/
│   │   ├── backup_engine.py          # Backup-Orchestrierung
│   │   ├── restore_engine.py         # Wiederherstellung
│   │   ├── encryptor.py              # AES-256-GCM (Chunked)
│   │   ├── update_checker.py         # GitHub Releases API Check
│   │   └── ...
│   └── templates/
│       ├── handlers/                 # USB, OneDrive, Nextcloud …
│       └── *.json                    # Template-Definitionen (7 Stück)
├── .github/workflows/
│   └── build-release.yml            # CI: Windows EXE + Linux AppImage
├── installer.iss                    # Inno Setup Installer-Script
├── scrat_backup.spec                # PyInstaller Spec
├── requirements.txt
└── BUILD.md                         # Build-Anleitung
```

### Entwicklungsumgebung

```bash
git clone https://github.com/nicolettas-muggelbude/Scrat-Backup.git
cd Scrat-Backup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 src/main.py
```

### Tests

```bash
pytest
pytest --cov=src --cov-report=html
```

---

## 🗺️ Roadmap

### Abgeschlossen ✅
- [x] Core-Engine (Backup/Restore, AES-256-GCM, zstd)
- [x] 5 Storage-Backends (USB, SFTP, WebDAV, Rclone, SMB)
- [x] Setup-Wizard V3 mit Template-System
- [x] Dark Mode + System Tray
- [x] Scheduler & Automatisierung
- [x] Restore-Flow im Wizard
- [x] GitHub Actions CI (Windows + Linux)
- [x] Auto-Updater

### Geplant
- [ ] SFTP-Template (Community-Wunsch)
- [ ] macOS-Build (GitHub Actions)
- [ ] Desktop-Integration für Linux (.desktop-Datei)
- [ ] Lokalisierung (DE/EN)
- [ ] Template-Marketplace

---

## 🤝 Beitragen

Contributions sind herzlich willkommen! 🎉

1. Fork das Repository
2. Feature-Branch erstellen (`git checkout -b feature/MeinFeature`)
3. Committen (`git commit -m 'feat: MeinFeature'`)
4. Pushen (`git push origin feature/MeinFeature`)
5. Pull Request öffnen

Siehe [CONTRIBUTING.md](CONTRIBUTING.md) für Details.

---

## 🔐 Sicherheit

Sicherheitslücken bitte **nicht** als öffentliches Issue melden, sondern per E-Mail an: **nicoletta@muggelbude.it**

---

## 📄 Lizenz

**GNU General Public License v3.0** – siehe [LICENSE](LICENSE)

---

## 💬 Support

- 🐛 **Bug Reports:** [GitHub Issues](https://github.com/nicolettas-muggelbude/Scrat-Backup/issues)
- 💡 **Feature Requests:** [GitHub Discussions](https://github.com/nicolettas-muggelbude/Scrat-Backup/discussions)
- 📚 **Technische Doku:** [CLAUDE.md](CLAUDE.md)

---

<div align="center">

*Wie ein Eichhörnchen seine Eicheln bewahrt, so bewahren wir deine Daten.* 🐿️🌰

**[⭐ Star das Projekt](https://github.com/nicolettas-muggelbude/Scrat-Backup) • [📥 Download](https://github.com/nicolettas-muggelbude/Scrat-Backup/releases/latest) • [🐛 Bug melden](https://github.com/nicolettas-muggelbude/Scrat-Backup/issues)**

*Entwickelt mit ❤️ und [Claude Code](https://claude.com/claude-code)*

</div>
