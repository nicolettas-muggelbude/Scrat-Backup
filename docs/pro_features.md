# Scrat-Backup Pro - Feature-Planung

## Übersicht

Scrat-Backup ist primär für **Privat-Nutzer** konzipiert. Für **Enterprise-Umgebungen** und **professionelle Anwender** ist eine **Pro-Version** geplant.

---

## Free Version (Privat-Nutzer)

✅ **Bereits implementiert:**

### Core-Features
- ✅ Vollbackup & Inkrementelle Backups
- ✅ AES-256-GCM Verschlüsselung (Pflicht)
- ✅ 7z-Komprimierung mit Split-Archives
- ✅ 3-Versionen-Rotation (Grandfather-Father-Son)
- ✅ Zeitpunkt-basierte Wiederherstellung
- ✅ Partial-Restore (einzelne Dateien)

### Storage-Backends
- ✅ **USB/Lokale Laufwerke** (USBStorage)
- ✅ **SFTP** (SSH-Server, z.B. Raspberry Pi)
- ✅ **SMB/CIFS** (NAS-Geräte wie Synology, QNAP, FritzBox)
  - ✅ Passwort-Authentifizierung
  - ❌ Windows-Domain (→ Pro)

### GUI
- ✅ Windows 11 Design
- ✅ Setup-Wizard
- ✅ Event-System
- 🚧 Backup-Tab (Phase 7)
- 🚧 Restore-Tab (Phase 8)
- 🚧 Scheduler (Phase 9)

---

## Pro Version (Enterprise/Professionelle Nutzer)

💼 **Geplante Pro-Features:**

### 1. Enterprise-Storage-Backends

#### SMB/CIFS mit Domain-Authentifizierung
- **Status:** Technisch bereits implementiert, aber UI-seitig gesperrt
- **Use Case:** Windows-Domänen in Unternehmen
- **Code:** `domain` Parameter in `SMBStorage.__init__()`
- **Aktivierung:** Pro-Lizenz-Check in GUI

```python
# Pro-Feature: Domain-Auth
storage = SMBStorage(
    server="fileserver.company.local",
    share="backups",
    username="backup_service",
    password="...",
    domain="COMPANY"  # ← Pro-Feature
)
```

#### WebDAV (Nextcloud, ownCloud, SharePoint)
- **Status:** Dependency bereits vorhanden (`webdavclient3`)
- **Use Case:** Nextcloud/ownCloud-Instanzen, SharePoint
- **Umsetzung:** Neue Klasse `WebDAVStorage(StorageBackend)`

#### Cloud-Provider via Rclone
- **Status:** Geplant
- **Use Case:** Google Drive, OneDrive, Dropbox, S3, etc.
- **Umsetzung:** `RcloneStorage` als Wrapper um rclone CLI
- **Vorteil:** Unterstützt 40+ Cloud-Provider ohne individuelle APIs

### 2. Advanced Backup-Features

#### Deduplizierung
- **Status:** Aktuell bewusst NICHT implementiert (Einfachheit)
- **Use Case:** Speicherplatz sparen bei vielen gleichen Dateien
- **Technologie:** Content-addressable Storage (Hash-basiert)
- **Trade-off:** Höhere Komplexität, längere Restore-Zeiten

#### Differenzielle Backups
- **Status:** Geplant
- **Aktuell:** Full + Incremental
- **Pro:** Full + Differential (schnelleres Restore als Incremental)

#### Backup-Chains mit Auto-Full
- **Status:** Geplant
- **Feature:** Automatisches Full-Backup nach X Incrementals
- **Vorteil:** Backup-Chains nicht zu lang

### 3. Monitoring & Reporting

#### E-Mail-Benachrichtigungen
- **Status:** Geplant
- **Feature:** E-Mail bei Erfolg/Fehler
- **Config:** SMTP-Server in Settings

#### Backup-Reports (PDF/HTML)
- **Status:** Geplant
- **Feature:** Monatliche Reports mit Statistiken
- **Inhalt:** Erfolgsrate, gesicherte Daten, Trends

#### Prometheus/Grafana-Integration
- **Status:** Geplant (für IT-Abteilungen)
- **Feature:** Metrics-Export für Monitoring-Systeme

### 4. Multi-User & Zentrale Verwaltung

#### Zentrale Management-Konsole
- **Status:** Konzept-Phase
- **Use Case:** IT-Admin verwaltet Backups für mehrere Clients
- **Architektur:** Web-Dashboard + Client-Agents

#### Backup-Policies (Group Policy)
- **Status:** Konzept-Phase
- **Feature:** Admin definiert Backup-Policies zentral
- **Use Case:** Unternehmen mit vielen Clients

### 5. Compliance & Audit

#### Audit-Logs
- **Status:** Geplant
- **Feature:** Unveränderbare Logs für Compliance
- **Use Case:** DSGVO, ISO 27001

#### Backup-Verifikation mit Hash-Validierung
- **Status:** Teilweise (Verschlüsselung prüft Integrität)
- **Pro:** Zusätzliche Hash-Checks beim Restore

#### Retention-Policies
- **Status:** Basis vorhanden (3-Versionen)
- **Pro:** Komplexe Policies (7 Tage, 4 Wochen, 12 Monate, etc.)

---

## Lizenzmodell (Idee)

### Free (Privat)
- ✅ Alle Core-Features
- ✅ Bis zu 3 Backup-Ziele
- ✅ USB, SFTP, SMB (ohne Domain)
- ✅ Community-Support

### Pro (Einmalzahlung oder Abo)
- ✅ Alle Free-Features
- ✅ Unbegrenzte Backup-Ziele
- ✅ SMB mit Domain-Auth
- ✅ WebDAV, Rclone (Cloud)
- ✅ E-Mail-Benachrichtigungen
- ✅ Priority-Support

### Enterprise (Volumen-Lizenz)
- ✅ Alle Pro-Features
- ✅ Zentrale Management-Konsole
- ✅ Multi-User-Support
- ✅ Backup-Policies
- ✅ Audit-Logs & Compliance
- ✅ Dedicated Support

---

## Technische Umsetzung (Lizenz-Check)

### Free ↔ Pro Unterscheidung

```python
# config.json
{
    "license": {
        "type": "free",  # free | pro | enterprise
        "key": null,     # Lizenz-Schlüssel (Pro/Enterprise)
        "expires": null  # Ablaufdatum (bei Abo)
    }
}
```

### Feature-Gating im Code

```python
from src.core.license import get_license, LicenseType

def create_smb_storage_with_domain(domain: str):
    license = get_license()

    if domain and license.type == LicenseType.FREE:
        raise PermissionError(
            "Domain-Authentifizierung ist ein Pro-Feature. "
            "Upgrade auf Scrat-Backup Pro für Enterprise-Support."
        )

    return SMBStorage(..., domain=domain)
```

### GUI-Kennzeichnung

```python
# In wizard.py - SFTP-Domain-Feld
domain_field = QLineEdit()
domain_field.setPlaceholderText("Domain (Pro-Feature)")
domain_field.setEnabled(license.is_pro_or_higher)

if not license.is_pro_or_higher:
    domain_field.setToolTip("⭐ Upgrade auf Pro für Domain-Authentifizierung")
```

---

## Roadmap

### Phase 1: Free-Version (v1.0)
- ✅ Alle Core-Features
- ✅ USB, SFTP, SMB (ohne Domain)
- 🚧 GUI komplett
- 🚧 Scheduler

### Phase 2: Pro-Vorbereitung (v1.5)
- Lizenz-System implementieren
- Feature-Gating im Code
- Pro-Features markieren in GUI

### Phase 3: Pro-Launch (v2.0)
- SMB mit Domain freischalten
- WebDAV implementieren
- E-Mail-Benachrichtigungen
- Pro-Lizenz verkaufen

### Phase 4: Enterprise (v3.0)
- Zentrale Management-Konsole
- Multi-User
- Audit-Logs
- Rclone-Integration

---

## Notizen

- **Aktueller Fokus:** Free-Version für Privat-Nutzer perfektionieren
- **Domain-Auth:** Code ist fertig, wird nur für Pro gesperrt
- **Monetarisierung:** Erst nach erfolgreicher Free-Version
- **Open-Source:** Free bleibt Open-Source (GPLv3), Pro evtl. Dual-License

**Motto:** Erst perfekte Free-Version, dann Pro für Power-User! 🚀
