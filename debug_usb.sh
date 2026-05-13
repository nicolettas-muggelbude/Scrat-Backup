#!/bin/bash
# USB-Laufwerks-Erkennung Debug-Skript für Linux
# Zeigt alle potenziellen USB-Mount-Punkte

echo "=== USB-Laufwerks-Debug ==="
echo ""

python3 << 'EOF'
import os
import platform
from pathlib import Path

user = os.environ.get('USER', 'unknown')
print(f"Platform: {platform.system()}")
print(f"User: {user}")
print()

# /media/USER
media_path = Path("/media") / user
print(f"/media/{user}: exists={media_path.exists()}")
if media_path.exists():
    try:
        items = list(media_path.iterdir())
        print(f"  Inhalt: {[i.name for i in items]}")
        for item in items:
            print(f"    - {item} (is_dir={item.is_dir()})")
    except Exception as e:
        print(f"  Fehler: {e}")
print()

# /run/media/USER
run_media = Path("/run/media") / user
print(f"/run/media/{user}: exists={run_media.exists()}")
if run_media.exists():
    try:
        items = list(run_media.iterdir())
        print(f"  Inhalt: {[i.name for i in items]}")
        for item in items:
            print(f"    - {item} (is_dir={item.is_dir()})")
    except Exception as e:
        print(f"  Fehler: {e}")
print()

# /mnt
mnt_path = Path("/mnt")
print(f"/mnt: exists={mnt_path.exists()}")
if mnt_path.exists():
    try:
        items = [i for i in mnt_path.iterdir()]
        print(f"  Inhalt: {[i.name for i in items]}")
        for item in items:
            if item.name not in ["wsl", "wslg"]:
                print(f"    - {item} (is_dir={item.is_dir()})")
    except Exception as e:
        print(f"  Fehler: {e}")
print()

# Gemountete Laufwerke
print("Gemountete externe Laufwerke (df -h):")
import subprocess
result = subprocess.run(["df", "-h"], capture_output=True, text=True)
for line in result.stdout.split('\n'):
    if '/dev/sd' in line or '/media' in line or '/mnt' in line or '/run/media' in line:
        print(f"  {line}")
print()

# lsblk - Block-Devices
print("Block-Devices (lsblk):")
result = subprocess.run(["lsblk", "-o", "NAME,SIZE,TYPE,MOUNTPOINT"], capture_output=True, text=True)
print(result.stdout)
EOF

echo ""
echo "=== Debug-Info Ende ==="
