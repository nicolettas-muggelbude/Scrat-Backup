# Scrat-Backup – Roadmap

> Aktueller Stand: **v0.3.39-beta** · GPLv3 · Python / PySide6

---

## ✅ Abgeschlossen (v0.3.x-beta)

### Kern
- Vollbackup & Inkrementelle Backups mit Ketten-Traversal
- AES-256-GCM Verschlüsselung (Chunked, 64 MB RAM-Verbrauch)
- zstd-Komprimierung (Level 1, alle CPU-Kerne)
- 3-Versionen-Rotation nach Backup-Ketten (Full + Inkrementelle)
- Frequenzbasierte Full/Inkrementell-Strategie (täglich/wöchentlich/monatlich)
- Metadaten-DB (SQLite) wird nach jedem Backup auf das Zielmedium kopiert

### Oberfläche
- Setup-Wizard (Quelle → Template → Zeitplan → Verschlüsselung → Fertig)
- System Tray (Backup starten, Einstellungen, Restore, Beenden)
- Restore-Wizard (DB-Modus + Verzeichnis-Modus)
- Dark Mode (Auto-Erkennung inkl. Wayland/gsettings)
- Barrierefreiheit: Tastatur-Navigation, Screen-Reader-kompatibel

### Templates & Backends
- USB / lokale Laufwerke
- SFTP (SSH, RejectPolicy + System-Known-Hosts)
- SMB/CIFS (Synology, QNAP, FritzBox)
- WebDAV (Nextcloud, ownCloud)
- OneDrive, Google Drive, Dropbox (via rclone + OAuth)

### Plattform & Betrieb
- Windows: Inno-Setup-Installer (kein Admin nötig, `%LocalAppData%`)
- Linux: AppImage (x86_64), `install.sh` mit FUSE-Erkennung (Ubuntu 22/24/26)
- GitHub Actions CI: Windows EXE + Linux AppImage bei `v*`-Tags
- Auto-Updater (GitHub Releases API, einmal täglich)
- Desktop-Benachrichtigungen (Linux: notify-send, Windows: PowerShell, macOS: osascript)
- Headless-Modus (`--backup`) für cron / Windows Task Scheduler
- Log-Datei: `%LocalAppData%\Scrat-Backup\scrat-backup.log` / `~/.scrat-backup/scrat-backup.log`

---

## 🔜 v0.4 – Stabilisierung & Plattform-Vollständigkeit

### Qualität
- [ ] Tests für alle Template-Handler
- [ ] Dark Mode: verbleibende hardcodierte Farben prüfen

### Windows
- [ ] WinRT AppId im Inno-Setup registrieren → „Scrat-Backup" statt „PowerShell" in Benachrichtigungen
- [ ] Tray-Icon mit Hell/Dunkel-Wechsel

### Linux
- [ ] XDG User Directories (`xdg-user-dir` für Dokumente, Bilder usw.)
- [ ] `.deb`-Paket (Debian/Ubuntu)
- [ ] Desktop-Dateien (`scrat-backup.desktop`, `scrat-backup-tray.desktop`)
- [ ] PyPI-Paket (`pip install scrat-backup`)

### macOS
- [ ] GitHub Actions Build (macOS-Runner)
- [ ] `.dmg`-Installer

### GitHub Actions
- [ ] Auf Node.js 24 / actions v5 aktualisieren (Deadline: Juni 2026)

---

## 🔜 v0.5 – Neue Templates & Erweiterungen

- [ ] SFTP-Template (Community-Wunsch; Handler bereits vorhanden)
- [ ] FTP-Template
- [ ] iCloud-Template (rclone)
- [ ] pCloud-Template (rclone)
- [ ] AWS S3-Template (rclone)
- [ ] Template-Icons (SVG statt Emojis)
- [ ] Template-Manager-Tab im MainWindow
- [ ] Multi-Destination: mehrere Backup-Ziele pro Durchlauf

---

## 🔜 v1.0 – Stabiler Release

- [ ] Lokalisierung DE/EN (Qt-Strings externalisieren)
- [ ] Template-Wizard: eigene Templates aus bestehender Config erstellen
- [ ] Template-Marketplace: Community-Templates aus URL importieren
- [ ] Handler als Plugins (`~/.scrat-backup/plugins/`)
- [ ] Config-Migration: alte Destinations → Template-basiert
- [ ] Benutzerhandbuch (deutsch)

---

## 💡 Zukunft / Pro-Version

- E-Mail-Benachrichtigungen (SMTP)
- Differenzielle Backups
- Deduplizierung (Content-addressable Storage)
- Backup-Reports (PDF/HTML)
- Zentrale Management-Konsole (Web-Dashboard + Client-Agents)
- Komplexe Retention-Policies (7 Tage / 4 Wochen / 12 Monate)
- Audit-Logs (DSGVO / ISO 27001)

Details dazu in [`docs/pro_features.md`](docs/pro_features.md).

---

## Versionsplan

| Version | Fokus | Status |
|---------|-------|--------|
| v0.3.x | Beta – Kern, Templates, CI, Linux-Tests | ✅ Laufend |
| v0.4.x | Stabilisierung, Tests, macOS, .deb | 🔜 Geplant |
| v0.5.x | Neue Templates, Multi-Destination | 🔜 Geplant |
| v1.0 | Stabiler Release, Lokalisierung | 🔜 Geplant |
| v2.0+ | Pro-Features | 💡 Konzept |
