# 🎉 Scrat-Backup v0.3.14-beta Release Notes

## 💾 Downloads

| Plattform | Download |
|-----------|----------|
| 🪟 **Windows** (x64) | [⬇ ScratBackup-v0.3.14-beta-Setup.exe](https://github.com/nicolettas-muggelbude/Scrat-Backup/releases/download/v0.3.14-beta/ScratBackup-v0.3.14-beta-Setup.exe) |
| 🐧 **Linux** (x86_64, versioniert) | [⬇ ScratBackup-v0.3.14-beta-x86_64.AppImage](https://github.com/nicolettas-muggelbude/Scrat-Backup/releases/download/v0.3.14-beta/ScratBackup-v0.3.14-beta-x86_64.AppImage) |
| 🐧 **Linux** (x86_64, neutral) | [⬇ ScratBackup-x86_64.AppImage](https://github.com/nicolettas-muggelbude/Scrat-Backup/releases/download/v0.3.14-beta/ScratBackup-x86_64.AppImage) |
| 🐧 **Linux** Desktop-Integration | [⬇ install.sh](https://github.com/nicolettas-muggelbude/Scrat-Backup/releases/download/v0.3.14-beta/install.sh) |

---

## 🐿️ USB funktioniert, Update-Benachrichtigung aktiv!

**Scrat-Backup v0.3.14-beta** behebt mehrere kritische Bugs: USB-Backup übergibt Laufwerk und Pfad jetzt korrekt, die Update-Benachrichtigung erscheint während der Wizard offen ist, und es gibt ein versionsloses AppImage für stabile Download-Links.

**Wie ein Eichhörnchen seine Eicheln immer wiederfindet, so findest du deine Daten jetzt auf jedem Gerät.** 🌰

---

## ✨ Highlights dieser Version

### 🔌 USB-Backup funktioniert jetzt wirklich

- Laufwerksauswahl und Unterordner werden korrekt übergeben
- Handler-Ladepfad war falsch konstruiert – behoben
- Formularfelder wurden übersprungen (JSON `"id"` vs. Code `"name"`) – behoben

### 🔔 Update-Benachrichtigung während Wizard läuft

- UpdateChecker startet jetzt im Hintergrund bevor der Wizard erscheint
- Dialog erscheint während der Wizard offen ist, nicht erst danach

### 🐧 Neutrales AppImage für stabile Links

- `ScratBackup-x86_64.AppImage` ohne Versionsnummer
- Stabiler Link: `releases/latest/download/ScratBackup-x86_64.AppImage`

### 🪟 Windows-Installer (kein Admin nötig)

Statt eines ZIP-Archivs gibt es einen echten Inno Setup Installer:

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
- ✅ **EncryptionPage** – Passwort + Keyring
- ✅ **RestoreWizardPage** – DB- und Verzeichnis-Modus
- ✅ **FinishPage** – Tray-Start oder Experten-Modus

### Dark Mode
- ✅ Auto-Detection + manuelles Umschalten
- ✅ Alle Wizard-Seiten theme-aware (TemplateCards, Ordner-Liste, Ausschlüsse, FinishPage)

### Sonstiges
- ✅ **Auto-Updater** – tägliche Prüfung, Dialog mit Release Notes
- ✅ **System Tray** – vollständig verdrahtet
- ✅ **Linux Desktop-Integration** – install.sh, .desktop-Datei, Icons

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

**Wie ein Eichhörnchen seine Eicheln bewahrt, so bewahren wir deine Daten.** 🐿️🌰

[📥 Download](https://github.com/nicolettas-muggelbude/Scrat-Backup/releases/tag/v0.3.14-beta) • [⭐ Star auf GitHub](https://github.com/nicolettas-muggelbude/Scrat-Backup) • [🐛 Bug melden](https://github.com/nicolettas-muggelbude/Scrat-Backup/issues)

</div>

---

*Erstellt mit ❤️ und [Claude Code](https://claude.com/claude-code)*
