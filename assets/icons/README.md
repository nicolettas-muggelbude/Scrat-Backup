# Scrat-Backup Icons

Dieses Verzeichnis enthält die Icon-Dateien für Scrat-Backup.

## Verfügbare Icons

### SVG (Vektorgrafik)
- `scrat.svg` - Master-Icon in SVG-Format (256x256)

### PNG (Raster-Grafiken)
*Noch zu erstellen - siehe Anleitung unten*

Benötigte Größen:
- `scrat-16.png` - 16x16 (Taskbar, kleines Icon)
- `scrat-32.png` - 32x32 (Standard-Icon)
- `scrat-48.png` - 48x48 (Medium)
- `scrat-64.png` - 64x64 (Medium-Large)
- `scrat-128.png` - 128x128 (Large)
- `scrat-256.png` - 256x256 (Extra Large)

### ICO (Windows)
*Noch zu erstellen - siehe Anleitung unten*

- `scrat.ico` - Multi-Resolution Windows Icon (16, 32, 48, 64, 128, 256)

---

## Icon-Design

**Motiv:** Eichel (Acorn)
**Stil:** Flat Design, minimalistisch
**Farben:**
- Kappe: Brauntöne (#8B6F47, #6B4423)
- Körper: Goldbraun (#D4A574, #B8860B)
- Blatt: Grün (#7A9B59)

**Symbolik:**
> "Wie ein Eichhörnchen seine Eicheln für den Winter sichert,
> so sichert Scrat-Backup deine Daten für die Zukunft."

---

## PNG-Versionen erstellen

### Option 1: Inkscape (Empfohlen)

```bash
# Inkscape installieren (falls nicht vorhanden)
sudo apt install inkscape  # Debian/Ubuntu
# oder
brew install inkscape      # macOS

# PNG-Versionen erstellen
inkscape scrat.svg -w 16 -h 16 -o scrat-16.png
inkscape scrat.svg -w 32 -h 32 -o scrat-32.png
inkscape scrat.svg -w 48 -h 48 -o scrat-48.png
inkscape scrat.svg -w 64 -h 64 -o scrat-64.png
inkscape scrat.svg -w 128 -h 128 -o scrat-128.png
inkscape scrat.svg -w 256 -h 256 -o scrat-256.png
```

### Option 2: rsvg-convert

```bash
# librsvg installieren
sudo apt install librsvg2-bin

# PNG-Versionen erstellen
rsvg-convert -w 16 -h 16 scrat.svg > scrat-16.png
rsvg-convert -w 32 -h 32 scrat.svg > scrat-32.png
rsvg-convert -w 48 -h 48 scrat.svg > scrat-48.png
rsvg-convert -w 64 -h 64 scrat.svg > scrat-64.png
rsvg-convert -w 128 -h 128 scrat.svg > scrat-128.png
rsvg-convert -w 256 -h 256 scrat.svg > scrat-256.png
```

### Option 3: ImageMagick

```bash
# ImageMagick installieren
sudo apt install imagemagick

# PNG-Versionen erstellen
convert -background none scrat.svg -resize 16x16 scrat-16.png
convert -background none scrat.svg -resize 32x32 scrat-32.png
convert -background none scrat.svg -resize 48x48 scrat-48.png
convert -background none scrat.svg -resize 64x64 scrat-64.png
convert -background none scrat.svg -resize 128x128 scrat-128.png
convert -background none scrat.svg -resize 256x256 scrat-256.png
```

### Option 4: Online-Tool

1. Öffne https://svgtopng.com/ oder https://cloudconvert.com/svg-to-png
2. Lade `scrat.svg` hoch
3. Wähle gewünschte Größen
4. Download PNGs

---

## Windows .ico erstellen

### Option 1: ImageMagick

```bash
# Aus PNG-Dateien .ico erstellen
convert scrat-16.png scrat-32.png scrat-48.png scrat-64.png \
        scrat-128.png scrat-256.png scrat.ico
```

### Option 2: Python (mit Pillow)

```python
from PIL import Image

# PNG-Dateien laden
sizes = [16, 32, 48, 64, 128, 256]
images = [Image.open(f'scrat-{size}.png') for size in sizes]

# Als .ico speichern
images[0].save(
    'scrat.ico',
    format='ICO',
    sizes=[(img.width, img.height) for img in images],
    append_images=images[1:]
)
```

### Option 3: Online-Tool

1. Öffne https://convertio.co/de/png-ico/
2. Lade alle PNG-Dateien hoch
3. Konvertiere zu .ico
4. Download

### Option 4: GIMP (GUI)

1. Öffne GIMP
2. Öffne `scrat-256.png`
3. Datei → Exportieren als → `scrat.ico`
4. Wähle "Microsoft Windows Icon" Format

---

## Automatisches Build-Script

Für zukünftige Icon-Updates:

```bash
#!/bin/bash
# build_icons.sh

SVG="scrat.svg"
SIZES=(16 32 48 64 128 256)

echo "Building PNG icons from SVG..."

for size in "${SIZES[@]}"; do
    echo "  Creating ${size}x${size}..."
    inkscape "$SVG" -w $size -h $size -o "scrat-${size}.png"
done

echo "Creating Windows .ico..."
convert scrat-16.png scrat-32.png scrat-48.png \
        scrat-64.png scrat-128.png scrat-256.png \
        scrat.ico

echo "Done! ✅"
```

Ausführbar machen: `chmod +x build_icons.sh`

---

## Icon in PyQt6 verwenden

```python
from PyQt6.QtGui import QIcon
from pathlib import Path

# Icon laden
icon_path = Path(__file__).parent / "assets" / "icons" / "scrat.ico"
app_icon = QIcon(str(icon_path))

# Auf Fenster anwenden
main_window.setWindowIcon(app_icon)

# Auf Application anwenden
app.setWindowIcon(app_icon)
```

---

## Lizenz

Das Scrat-Backup Icon ist Teil des Scrat-Backup Projekts und unter **GPLv3** lizenziert.

Design: Original-Artwork, keine Copyright-Probleme.
