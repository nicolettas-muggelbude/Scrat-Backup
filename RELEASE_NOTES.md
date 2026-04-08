# 🎉 Scrat-Backup v0.3.11-beta Release Notes

## 💾 Downloads

| Plattform | Download |
|-----------|----------|
| 🪟 **Windows** (x64) | [⬇ ScratBackup-v0.3.11-beta-Setup.exe](https://github.com/nicolettas-muggelbude/Scrat-Backup/releases/download/v0.3.11-beta/ScratBackup-v0.3.11-beta-Setup.exe) |
| 🐧 **Linux** (x86_64) | [⬇ ScratBackup-v0.3.11-beta-x86_64.AppImage](https://github.com/nicolettas-muggelbude/Scrat-Backup/releases/download/v0.3.11-beta/ScratBackup-v0.3.11-beta-x86_64.AppImage) |

---

## 🐿️ Installer, Auto-Updater & Linux Desktop-Integration!

**Scrat-Backup v0.3.11-beta** bringt einen echten Windows-Installer, tägliche Update-Prüfung, alle 7 Templates und eine vollständige Linux Desktop-Integration – plus zahlreiche Packaging-Fixes damit die App auf beiden Plattformen zuverlässig startet.

**Wie ein Eichhörnchen seine Eicheln immer wiederfindet, so findest du deine Daten jetzt auf jedem Gerät.** 🌰

---

## ✨ Highlights dieser Version

### 🪟 Windows-Installer (kein Admin nötig)

Statt eines ZIP-Archivs gibt es jetzt einen echten Inno Setup Installer:

- Installiert nach `%LocalAppData%\Scrat-Backup` – **kein Administratorrecht erforderlich**
- Erstellt Startmenü-Eintrag und optionalen Desktop-Shortcut
- Deinstallation über Windows Einstellungen

### 🔔 Auto-Updater

Scrat-Backup prüft automatisch einmal täglich auf neue Versionen:

- Vergleich mit GitHub Releases API
- Dialog mit Release-Notes und direktem Download-Link
- Plattformspezifischer Download (Setup.exe / AppImage)

### 🐧 Linux Desktop-Integration

Mit dem mitgelieferten `install.sh` wird Scrat-Backup vollständig ins System integriert:

- AppImage nach `~/.local/bin/` kopieren
- Icons in allen Größen (16–256px) installieren
- Menü-Eintrag in `~/.local/share/applications/` erstellen
- **Kein sudo nötig** – alles im Home-Verzeichnis

```bash
./install.sh ScratBackup-vX.X.X-x86_64.AppImage
```

### 📁 Plattformspezifische Config-Pfade

Die Konfiguration liegt jetzt dort, wo das System sie erwartet:

- **Windows:** `%LocalAppData%\Scrat-Backup\`
- **Linux/macOS:** `~/.scrat-backup/`

---

## 🚀 Neue Features

### Linux Desktop-Integration
- ✅ **`install.sh`** – installiert AppImage, Icons und Menü-Eintrag ohne sudo
- ✅ **`scrat-backup.desktop`** – für manuelle Installation
- ✅ Icons in allen Größen (16, 32, 48, 64, 128, 256px) + SVG

### Auto-Updater
- ✅ **`UpdateChecker`** (QThread) – prüft GitHub Releases API einmal täglich
- ✅ **`UpdateDialog`** – zeigt Release-Notes, Download-Button, Release-Seite
- ✅ Plattformspezifischer Download-Link aus Release-Assets

### Windows Installer
- ✅ **Inno Setup** statt ZIP – `ScratBackup-vX.X.X-Setup.exe`
- ✅ Installation nach `%LocalAppData%\Scrat-Backup` (kein Admin)
- ✅ CI übergibt Version automatisch per `/DMyAppVersion=`

### Plattformspezifische Pfade
- ✅ **`src/utils/paths.py`** – zentrale `get_app_data_dir()` Funktion
- ✅ Windows: `%LocalAppData%\Scrat-Backup\`, Linux: `~/.scrat-backup\`
- ✅ Alle 10 betroffenen Dateien umgestellt

### Templates
- ✅ Alle **7 Template-JSON-Dateien** angelegt: USB, Nextcloud, OneDrive, Google Drive, Dropbox, Synology, QNAP

### Wizard Start-Screen
- ✅ **Immer** sichtbar: "Backup einrichten" + "Backup wiederherstellen"
- ✅ **Zusätzlich** wenn Config vorhanden: "Einstellungen ändern" + "Neues Ziel"
- ✅ Korrekte Subtitles je nach Status ("erste Verwendung" vs. "bereits eingerichtet")

---

## 🔧 Was funktioniert

### Core-Funktionen
- ✅ **Backup-Engine** – Vollbackups und inkrementelle Backups
- ✅ **Restore-Engine** – Einzelne Dateien oder komplette Backups
- ✅ **AES-256-GCM Verschlüsselung** – Alle Backups verschlüsselt (Chunked, 64MB)
- ✅ **zstd-Komprimierung** – ~5–10× schneller als LZMA, Level 1
- ✅ **Versionierung** – Konfigurierbare Rotationsanzahl
- ✅ **metadata.db-Portabilität** – Restore auf beliebigem Gerät

### Storage-Backends
- ✅ **USB / Lokale Laufwerke** (Win + Linux, inkl. externer Festplatten)
- ✅ **SFTP (SSH)** – mit sicherer Host-Key-Prüfung
- ✅ **WebDAV / Nextcloud**
- ✅ **Rclone** (Google Drive, Dropbox, OneDrive, 40+ Provider)
- ✅ **SMB/CIFS** (Synology, QNAP, Windows-Freigaben)

### Wizard
- ✅ **StartPage** – Aktionsauswahl (Backup einrichten / ändern / Restore / Experten-Modus)
- ✅ **SourceSelectionPage** – Quellen mit Bibliotheks-Checkboxen, eigene Ordner, Ausschlüsse
- ✅ **TemplateDestinationPage** – Template-Kacheln, nicht verfügbare Backends gesperrt
- ✅ **SchedulePage** – Täglich/Wöchentlich/Monatlich/beim Start, Zeitangabe, Wochentag
- ✅ **EncryptionPage** – Passwort + Keyring (NEU)
- ✅ **RestoreWizardPage** – DB- und Verzeichnis-Modus (NEU)
- ✅ **FinishPage** – Tray-Start oder Experten-Modus

### Dark Mode
- ✅ Auto-Detection + manuelles Umschalten
- ✅ Alle Wizard-Seiten theme-aware (TemplateCards, Ordner-Liste, Ausschlüsse, FinishPage)

---

## ⚠️ Bekannte Limitierungen (Beta)

- ❌ **macOS-Build** – noch kein macOS-Runner in CI
- ❌ **Internationalisierung** – aktuell nur Deutsch
- ❌ **Template-Manager-Tab** im MainWindow noch nicht implementiert
- ⚠️ **SFTP:** Unbekannte Hosts werden abgelehnt – vorher `ssh user@host` ausführen (einmalig)
- ⚠️ **Upgrade von älteren Versionen (Windows):** Config-Pfad hat sich geändert – alte Config von `%USERPROFILE%\.scrat-backup\` nach `%LocalAppData%\Scrat-Backup\` verschieben

---

## 📋 Systemanforderungen

| | Minimum | Empfohlen |
|---|---|---|
| **Windows** | Windows 10 64-bit | Windows 11 64-bit |
| **Linux** | Ubuntu 22.04 / vergleichbar | Ubuntu 24.04 |
| **RAM** | 4 GB | 8 GB |
| **Speicher** | 500 MB | 1 GB |
| **Python** | nicht nötig (Standalone) | – |

---

## 📊 Statistiken

- **Commits seit v0.3.0-beta:** 11
- **Neue Dateien:** `install.sh`, `scrat-backup.desktop`, `src/utils/paths.py`, `src/core/update_checker.py`, `src/gui/update_dialog.py`, 7× Template-JSON
- **CI-Jobs:** 2 (Windows Installer, Linux AppImage)
- **AppImage-Größe:** ~70 MB

---

## 🗺️ Was kommt als Nächstes

- [ ] Weitere Templates: SFTP, FTP, iCloud, AWS S3
- [ ] macOS-Build (GitHub Actions)
- [ ] Dark Mode: restliche Dialoge und Tabs
- [ ] Template-Manager-Tab im MainWindow
- [ ] XDG User Directories (Linux)
- [ ] `.deb`-Paket für Debian/Ubuntu

---

## 📖 Weitere Informationen

- **Changelog:** [CHANGELOG.md](CHANGELOG.md)
- **Build-Anleitung:** [BUILD.md](BUILD.md)
- **Contributing:** [CONTRIBUTING.md](CONTRIBUTING.md)

---

## 💬 Support & Community

- 🐛 **Bug Reports:** [GitHub Issues](https://github.com/nicolettas-muggelbude/Scrat-Backup/issues)
- 💡 **Feature Requests:** [GitHub Discussions](https://github.com/nicolettas-muggelbude/Scrat-Backup/discussions)
- ❓ **Fragen:** [GitHub Discussions Q&A](https://github.com/nicolettas-muggelbude/Scrat-Backup/discussions/categories/q-a)

---

## ⚖️ Lizenz

Scrat-Backup ist **Open Source** unter der **GNU General Public License v3.0**.

- ✅ Kostenlos für alle Zwecke
- ✅ Quellcode einsehbar und modifizierbar
- ✅ Weitergabe unter gleicher Lizenz

Siehe [LICENSE](LICENSE) für Details.

---

<div align="center">

## 🎊 Viel Spaß beim Testen!

**Wie ein Eichhörnchen seine Eicheln bewahrt, so bewahren wir deine Daten.** 🐿️🌰

[📥 Download](https://github.com/nicolettas-muggelbude/Scrat-Backup/releases/tag/v0.3.11-beta) • [⭐ Star auf GitHub](https://github.com/nicolettas-muggelbude/Scrat-Backup) • [🐛 Bug melden](https://github.com/nicolettas-muggelbude/Scrat-Backup/issues)

</div>

---

*Erstellt mit ❤️ und [Claude Code](https://claude.com/claude-code)*
