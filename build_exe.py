#!/usr/bin/env python3
"""
Build-Script für Scrat-Backup
Automatisiert den Build-Prozess mit PyInstaller
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path


class BuildScript:
    """Build-Script für Scrat-Backup"""

    def __init__(self):
        self.project_root = Path(__file__).parent
        self.dist_dir = self.project_root / "dist"
        self.build_dir = self.project_root / "build"
        self.spec_file = self.project_root / "scrat-backup.spec"
        self.assets_dir = self.project_root / "assets"

    def print_header(self, text: str):
        """Gibt einen formatierten Header aus"""
        print("\n" + "=" * 60)
        print(f"  {text}")
        print("=" * 60 + "\n")

    def clean_build_dirs(self):
        """Löscht alte Build-Verzeichnisse"""
        self.print_header("Bereinige alte Build-Verzeichnisse")

        for directory in [self.dist_dir, self.build_dir]:
            if directory.exists():
                print(f"Lösche: {directory}")
                shutil.rmtree(directory)
            else:
                print(f"Nicht vorhanden: {directory}")

        print("✓ Bereinigung abgeschlossen")

    def check_icon(self):
        """Prüft ob Icon vorhanden ist"""
        self.print_header("Prüfe Icon-Datei")

        icon_ico = self.assets_dir / "icons" / "scrat.ico"
        icon_png = self.assets_dir / "icons" / "scrat-256.png"

        if icon_ico.exists():
            print(f"✓ Icon gefunden: {icon_ico}")
            return True
        elif icon_png.exists():
            print(f"✓ PNG-Icon gefunden: {icon_png}")
            print("  Hinweis: Für Windows .exe wird .ico empfohlen")
            return True
        else:
            print("⚠ Warnung: Kein Icon gefunden")
            print(f"  Erwartet: {icon_ico} oder {icon_png}")
            return False

    def check_dependencies(self):
        """Prüft ob alle Dependencies installiert sind"""
        self.print_header("Prüfe Dependencies")

        try:
            import PyInstaller
            print(f"✓ PyInstaller: {PyInstaller.__version__}")
        except ImportError:
            print("✗ PyInstaller nicht gefunden!")
            print("  Installiere mit: pip install pyinstaller")
            return False

        try:
            import PyQt6
            print(f"✓ PyQt6: {PyQt6.QtCore.PYQT_VERSION_STR}")
        except ImportError:
            print("✗ PyQt6 nicht gefunden!")
            return False

        # Weitere wichtige Dependencies
        required = [
            'cryptography',
            'py7zr',
            'paramiko',
            'keyring',
        ]

        all_ok = True
        for pkg in required:
            try:
                __import__(pkg)
                print(f"✓ {pkg}")
            except ImportError:
                print(f"✗ {pkg} nicht gefunden!")
                all_ok = False

        return all_ok

    def run_pyinstaller(self):
        """Führt PyInstaller aus"""
        self.print_header("Baue Executable mit PyInstaller")

        if not self.spec_file.exists():
            print(f"✗ Spec-Datei nicht gefunden: {self.spec_file}")
            return False

        print(f"Verwende Spec-Datei: {self.spec_file}")
        print("Dies kann einige Minuten dauern...\n")

        # PyInstaller ausführen
        cmd = [
            sys.executable,
            "-m",
            "PyInstaller",
            str(self.spec_file),
            "--clean",
            "--noconfirm",
        ]

        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                check=True,
                capture_output=False,
            )

            print("\n✓ Build erfolgreich abgeschlossen!")
            return True

        except subprocess.CalledProcessError as e:
            print(f"\n✗ Build fehlgeschlagen mit Exit-Code: {e.returncode}")
            return False

    def show_results(self):
        """Zeigt Build-Ergebnisse an"""
        self.print_header("Build-Ergebnisse")

        exe_path = self.dist_dir / "ScratBackup" / "ScratBackup.exe"

        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"✓ Executable erstellt: {exe_path}")
            print(f"  Größe: {size_mb:.2f} MB")

            # Zähle Dateien im dist-Ordner
            dist_folder = exe_path.parent
            file_count = len(list(dist_folder.rglob("*")))
            print(f"  Dateien im dist-Ordner: {file_count}")

            print("\nZum Testen:")
            print(f"  cd {dist_folder}")
            print(f"  ./ScratBackup.exe")

        else:
            print("✗ Executable nicht gefunden!")
            print(f"  Erwartet: {exe_path}")

    def create_zip(self):
        """Erstellt ZIP-Archiv für Distribution"""
        self.print_header("Erstelle ZIP-Archiv")

        dist_folder = self.dist_dir / "ScratBackup"

        if not dist_folder.exists():
            print("✗ Dist-Ordner nicht gefunden!")
            return False

        zip_name = "ScratBackup-v0.2.0-beta-windows"
        zip_path = self.dist_dir / zip_name

        print(f"Erstelle: {zip_path}.zip")

        try:
            shutil.make_archive(str(zip_path), 'zip', dist_folder)
            zip_size = (zip_path.parent / f"{zip_name}.zip").stat().st_size / (1024 * 1024)
            print(f"✓ ZIP erstellt: {zip_path}.zip ({zip_size:.2f} MB)")
            return True
        except Exception as e:
            print(f"✗ Fehler beim Erstellen des ZIP: {e}")
            return False

    def run(self, skip_clean: bool = False, create_zip: bool = True):
        """Führt kompletten Build-Prozess aus"""
        print("""
╔══════════════════════════════════════════════════════════════╗
║                  Scrat-Backup Build-Script                   ║
║                     Version 0.2.0 Beta                       ║
╚══════════════════════════════════════════════════════════════╝
        """)

        # 1. Bereinigen
        if not skip_clean:
            self.clean_build_dirs()

        # 2. Icon prüfen
        self.check_icon()

        # 3. Dependencies prüfen
        if not self.check_dependencies():
            print("\n✗ Build abgebrochen: Fehlende Dependencies")
            return False

        # 4. PyInstaller ausführen
        if not self.run_pyinstaller():
            print("\n✗ Build abgebrochen: PyInstaller-Fehler")
            return False

        # 5. Ergebnisse anzeigen
        self.show_results()

        # 6. Optional: ZIP erstellen
        if create_zip:
            self.create_zip()

        print("\n" + "=" * 60)
        print("  Build-Prozess abgeschlossen!")
        print("=" * 60 + "\n")

        return True


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Build Scrat-Backup Executable")
    parser.add_argument(
        "--skip-clean",
        action="store_true",
        help="Überspringe Bereinigung alter Build-Verzeichnisse",
    )
    parser.add_argument(
        "--no-zip",
        action="store_true",
        help="Erstelle kein ZIP-Archiv",
    )

    args = parser.parse_args()

    builder = BuildScript()
    success = builder.run(skip_clean=args.skip_clean, create_zip=not args.no_zip)

    sys.exit(0 if success else 1)
