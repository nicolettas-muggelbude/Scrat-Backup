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
    if [ -z "$APPIMAGE" ]; then
        APPIMAGE=$(ls -1 ScratBackup*.AppImage 2>/dev/null | head -1)
    fi
fi

if [ -z "$APPIMAGE" ] || [ ! -f "$APPIMAGE" ]; then
    echo "Fehler: Kein AppImage gefunden."
    echo "Verwendung: $0 ScratBackup-vX.X.X-x86_64.AppImage"
    exit 1
fi

# Absoluten Pfad sicherstellen
APPIMAGE="$(cd "$(dirname "$APPIMAGE")" && pwd)/$(basename "$APPIMAGE")"
echo "Installiere $APPIMAGE ..."

# Verzeichnisse erstellen
mkdir -p "$INSTALL_DIR"
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

# Icons aus dem AppImage extrahieren
echo "Extrahiere Icons aus AppImage ..."
TMPDIR_ICONS=$(mktemp -d)
cd "$TMPDIR_ICONS"

# AppImage unterstützt --appimage-extract [pattern]
"$INSTALL_DIR/$APP_NAME.AppImage" --appimage-extract 'scrat-backup.png' 2>/dev/null || true
"$INSTALL_DIR/$APP_NAME.AppImage" --appimage-extract 'usr/share/icons' 2>/dev/null || true

ICON_INSTALLED=false

# Primär: eingebettetes Root-Icon (256x256)
if [ -f "$TMPDIR_ICONS/squashfs-root/scrat-backup.png" ]; then
    cp "$TMPDIR_ICONS/squashfs-root/scrat-backup.png" \
       "$ICON_DIR/256x256/apps/${DESKTOP_NAME}.png"
    ICON_INSTALLED=true
fi

# Sekundär: Icons aus usr/share/icons
if [ -d "$TMPDIR_ICONS/squashfs-root/usr/share/icons" ]; then
    find "$TMPDIR_ICONS/squashfs-root/usr/share/icons" -name "*.png" | while read -r f; do
        rel="${f#$TMPDIR_ICONS/squashfs-root/usr/share/icons/hicolor/}"
        size=$(echo "$rel" | cut -d'/' -f1)
        mkdir -p "$ICON_DIR/$size/apps"
        cp "$f" "$ICON_DIR/$size/apps/${DESKTOP_NAME}.png" 2>/dev/null || true
        ICON_INSTALLED=true
    done
fi

rm -rf "$TMPDIR_ICONS"
cd - > /dev/null

if [ "$ICON_INSTALLED" = true ]; then
    echo "Icons installiert."
else
    echo "Hinweis: Icons konnten nicht extrahiert werden – Menü-Eintrag ohne Icon."
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

# PATH automatisch setzen wenn ~/.local/bin fehlt
PATH_LINE='export PATH="$HOME/.local/bin:$PATH"'
PATH_ADDED=false
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    for RC in "$HOME/.bashrc" "$HOME/.profile"; do
        if [ -f "$RC" ] && ! grep -q '.local/bin' "$RC"; then
            echo "" >> "$RC"
            echo "# Scrat-Backup: lokale Programme" >> "$RC"
            echo "$PATH_LINE" >> "$RC"
            PATH_ADDED=true
            echo "PATH wurde zu $RC hinzugefügt."
            break
        fi
    done
    # Für aktuelle Shell-Session sofort übernehmen
    export PATH="$HOME/.local/bin:$PATH"
fi

echo ""
echo "Scrat-Backup wurde installiert!"
echo "  Programm : $INSTALL_DIR/$APP_NAME.AppImage"
echo "  Starter  : $INSTALL_DIR/scrat-backup"
echo "  Menü     : $DESKTOP_DIR/${DESKTOP_NAME}.desktop"
echo ""

if [ "$PATH_ADDED" = true ]; then
    echo "Starten: source ~/.bashrc && scrat-backup"
else
    echo "Starten: scrat-backup"
fi
