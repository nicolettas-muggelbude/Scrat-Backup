#!/usr/bin/env bash
# Scrat-Backup – Linux Installations-Script
# Installiert AppImage + Desktop-Integration (Menü-Eintrag, Icons)
#
# Verwendung:
#   ./install.sh                        # installiert AppImage im aktuellen Verzeichnis
#   ./install.sh /pfad/zum/AppImage     # installiert angegebenes AppImage

set -e

APP_NAME="ScratBackup"
DESKTOP_NAME="scrat-backup"
INSTALL_DIR="$HOME/.local/bin"
ICON_DIR="$HOME/.local/share/icons/hicolor"
DESKTOP_DIR="$HOME/.local/share/applications"

# AppImage-Pfad bestimmen
if [ -n "$1" ]; then
    APPIMAGE="$1"
else
    APPIMAGE=$(ls -1 ScratBackup-*.AppImage 2>/dev/null | head -1)
fi

if [ -z "$APPIMAGE" ] || [ ! -f "$APPIMAGE" ]; then
    echo "Fehler: Kein AppImage gefunden."
    echo "Verwendung: $0 ScratBackup-vX.X.X-x86_64.AppImage"
    exit 1
fi

echo "Installiere $APPIMAGE ..."

# Verzeichnisse erstellen
mkdir -p "$INSTALL_DIR"
mkdir -p "$ICON_DIR/16x16/apps"
mkdir -p "$ICON_DIR/32x32/apps"
mkdir -p "$ICON_DIR/48x48/apps"
mkdir -p "$ICON_DIR/64x64/apps"
mkdir -p "$ICON_DIR/128x128/apps"
mkdir -p "$ICON_DIR/256x256/apps"
mkdir -p "$ICON_DIR/scalable/apps"
mkdir -p "$DESKTOP_DIR"

# AppImage ins bin-Verzeichnis kopieren und ausführbar machen
cp "$APPIMAGE" "$INSTALL_DIR/$APP_NAME.AppImage"
chmod +x "$INSTALL_DIR/$APP_NAME.AppImage"

# Wrapper-Script erstellen (damit 'scrat-backup' im PATH funktioniert)
cat > "$INSTALL_DIR/scrat-backup" << EOF
#!/usr/bin/env bash
exec "$INSTALL_DIR/$APP_NAME.AppImage" "\$@"
EOF
chmod +x "$INSTALL_DIR/scrat-backup"

# Icons installieren (aus AppImage extrahieren oder aus Quellverzeichnis)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ICONS_SRC="$SCRIPT_DIR/assets/icons"

if [ -d "$ICONS_SRC" ]; then
    for SIZE in 16 32 48 64 128 256; do
        ICON_FILE="$ICONS_SRC/scrat-${SIZE}.png"
        if [ -f "$ICON_FILE" ]; then
            cp "$ICON_FILE" "$ICON_DIR/${SIZE}x${SIZE}/apps/${DESKTOP_NAME}.png"
        fi
    done
    if [ -f "$ICONS_SRC/scrat.svg" ]; then
        cp "$ICONS_SRC/scrat.svg" "$ICON_DIR/scalable/apps/${DESKTOP_NAME}.svg"
    fi
    echo "Icons installiert."
else
    echo "Hinweis: Icon-Verzeichnis nicht gefunden, Icons werden übersprungen."
fi

# Icon-Cache aktualisieren
if command -v gtk-update-icon-cache &>/dev/null; then
    gtk-update-icon-cache -f -t "$ICON_DIR" 2>/dev/null || true
fi

# Desktop-Datei erstellen
cat > "$DESKTOP_DIR/${DESKTOP_NAME}.desktop" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Scrat-Backup
GenericName=Backup-Programm
Comment=Verschlüsseltes Backup-Tool für Privatnutzer
Exec=$INSTALL_DIR/scrat-backup
Icon=${DESKTOP_NAME}
Terminal=false
Categories=Utility;Archiving;
Keywords=backup;verschlüsselung;sicherung;restore;
StartupWMClass=ScratBackup
EOF

# Desktop-Datenbank aktualisieren
if command -v update-desktop-database &>/dev/null; then
    update-desktop-database "$DESKTOP_DIR" 2>/dev/null || true
fi

echo ""
echo "Scrat-Backup wurde installiert!"
echo "  Programm : $INSTALL_DIR/$APP_NAME.AppImage"
echo "  Starter  : $INSTALL_DIR/scrat-backup"
echo "  Menü     : $DESKTOP_DIR/${DESKTOP_NAME}.desktop"
echo ""
echo "Starten: scrat-backup"
echo "(Falls der Befehl nicht gefunden wird: 'source ~/.profile' oder neu einloggen)"

# Prüfen ob ~/.local/bin im PATH ist
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo ""
    echo "Hinweis: $HOME/.local/bin ist nicht im PATH."
    echo "Füge folgende Zeile zu deiner ~/.bashrc oder ~/.profile hinzu:"
    echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""
fi
