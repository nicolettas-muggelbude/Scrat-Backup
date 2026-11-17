#!/usr/bin/env python3
"""
Scrat-Backup Icon Builder
Erstellt PNG- und ICO-Dateien aus dem SVG-Master-Icon

Requirements:
    pip install cairosvg pillow

Usage:
    python build_icons.py
"""

import sys
from pathlib import Path
from typing import List

try:
    import cairosvg
    from PIL import Image
except ImportError as e:
    print("❌ Fehlende Dependencies!")
    print()
    print("Bitte installieren:")
    print("  pip install cairosvg pillow")
    print()
    print(f"Fehler: {e}")
    sys.exit(1)


def svg_to_png(svg_path: Path, png_path: Path, size: int) -> None:
    """
    Konvertiert SVG zu PNG mit spezifischer Größe

    Args:
        svg_path: Pfad zur SVG-Datei
        png_path: Pfad zur Ziel-PNG-Datei
        size: Gewünschte Größe (Breite und Höhe)
    """
    cairosvg.svg2png(
        url=str(svg_path),
        write_to=str(png_path),
        output_width=size,
        output_height=size
    )


def create_ico(png_files: List[Path], ico_path: Path) -> None:
    """
    Erstellt .ico Datei aus mehreren PNG-Dateien

    Args:
        png_files: Liste von PNG-Dateien (verschiedene Größen)
        ico_path: Pfad zur Ziel-.ico-Datei
    """
    images = []
    for png_file in png_files:
        if png_file.exists():
            img = Image.open(png_file)
            images.append(img)

    if images:
        images[0].save(
            ico_path,
            format='ICO',
            sizes=[(img.width, img.height) for img in images],
            append_images=images[1:]
        )


def main():
    """Hauptfunktion"""
    # Pfade
    script_dir = Path(__file__).parent
    svg_file = script_dir / "scrat.svg"

    if not svg_file.exists():
        print(f"❌ SVG-Datei nicht gefunden: {svg_file}")
        sys.exit(1)

    # Größen für PNG-Dateien
    sizes = [16, 32, 48, 64, 128, 256]

    print("=" * 60)
    print("Scrat-Backup Icon Builder")
    print("=" * 60)
    print()
    print(f"SVG-Quelle: {svg_file.name}")
    print()

    # PNG-Dateien erstellen
    print("Erstelle PNG-Dateien...")
    png_files = []

    for size in sizes:
        png_file = script_dir / f"scrat-{size}.png"
        print(f"  ├─ {png_file.name} ({size}x{size})", end=" ")

        try:
            svg_to_png(svg_file, png_file, size)
            png_files.append(png_file)
            print("✅")
        except Exception as e:
            print(f"❌ Fehler: {e}")

    print()

    # .ico Datei erstellen
    ico_file = script_dir / "scrat.ico"
    print(f"Erstelle Windows Icon: {ico_file.name}", end=" ")

    try:
        create_ico(png_files, ico_file)
        print("✅")
    except Exception as e:
        print(f"❌ Fehler: {e}")

    print()
    print("=" * 60)
    print("Fertig! 🎉")
    print("=" * 60)
    print()
    print("Erstellte Dateien:")
    for png_file in png_files:
        if png_file.exists():
            size = png_file.stat().st_size
            print(f"  ✅ {png_file.name:20s} ({size:,} Bytes)")

    if ico_file.exists():
        size = ico_file.stat().st_size
        print(f"  ✅ {ico_file.name:20s} ({size:,} Bytes)")

    print()


if __name__ == "__main__":
    main()
