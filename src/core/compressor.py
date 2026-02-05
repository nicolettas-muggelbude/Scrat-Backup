"""
Compressor für Scrat-Backup
7z-Komprimierung mit Split-Archive-Unterstützung
"""

import logging
from pathlib import Path
from typing import Callable, List, Optional

import py7zr

logger = logging.getLogger(__name__)


class Compressor:
    """
    Komprimiert Dateien zu 7z-Archiven

    Verantwortlichkeiten:
    - 7z-Archive erstellen
    - Split-Archive bei konfigurierbarer Größe
    - Progress-Callbacks für GUI
    - Entpacken von Archiven
    """

    # Konstanten
    DEFAULT_COMPRESSION_LEVEL = 5  # Balance zwischen Speed und Compression
    DEFAULT_SPLIT_SIZE = 128 * 1024 * 1024  # 128 MB (reduziert für RAM-Effizienz)

    def __init__(
        self,
        compression_level: int = DEFAULT_COMPRESSION_LEVEL,
        split_size: int = DEFAULT_SPLIT_SIZE,
    ):
        """
        Initialisiert Compressor

        Args:
            compression_level: Komprimierungs-Level (0-9, Standard: 5)
            split_size: Maximale Größe pro Archive-Teil in Bytes (Standard: 500MB)
        """
        if not 0 <= compression_level <= 9:
            raise ValueError("compression_level muss zwischen 0 und 9 liegen")

        if split_size < 1024 * 1024:  # Mindestens 1MB
            raise ValueError("split_size muss mindestens 1MB sein")

        self.compression_level = compression_level
        self.split_size = split_size

        logger.info(
            f"Compressor initialisiert: Level={compression_level}, "
            f"Split-Size={split_size / 1024 / 1024:.0f}MB"
        )

    def compress_files(
        self,
        files: List[Path],
        output_path: Path,
        base_dir: Optional[Path] = None,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
    ) -> List[Path]:
        """
        Komprimiert Dateien zu einem oder mehreren 7z-Archiven

        Args:
            files: Liste der zu komprimierenden Dateien
            output_path: Basis-Pfad für Output-Archive (z.B. backup.7z)
            base_dir: Basis-Verzeichnis für relative Pfade im Archiv
            progress_callback: Optional Callback(current, total, filename)

        Returns:
            Liste der erstellten Archive-Pfade
        """
        if not files:
            raise ValueError("Keine Dateien zum Komprimieren angegeben")

        logger.info(f"Starte Komprimierung von {len(files)} Dateien")

        # Archive-Liste
        archives: List[Path] = []

        # Prüfe, ob Split nötig ist
        total_size = sum(f.stat().st_size for f in files if f.exists())
        needs_split = total_size > self.split_size

        if needs_split:
            logger.info(
                f"Gesamt-Größe {total_size / 1024 / 1024:.1f}MB "
                f"überschreitet Split-Size, erstelle Multi-Volume-Archiv"
            )
            archives = self._compress_split(files, output_path, base_dir, progress_callback)
        else:
            logger.info("Erstelle Single-Volume-Archiv")
            archives = [self._compress_single(files, output_path, base_dir, progress_callback)]

        logger.info(f"Komprimierung abgeschlossen: {len(archives)} Archive erstellt")
        return archives

    def _compress_single(
        self,
        files: List[Path],
        output_path: Path,
        base_dir: Optional[Path] = None,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
    ) -> Path:
        """
        Komprimiert Dateien zu einem einzelnen 7z-Archiv

        Args:
            files: Liste der zu komprimierenden Dateien
            output_path: Output-Archiv-Pfad
            base_dir: Basis-Verzeichnis für relative Pfade
            progress_callback: Optional Callback

        Returns:
            Pfad zum erstellten Archiv
        """
        # Stelle sicher, dass Output-Verzeichnis existiert
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Erstelle 7z-Archiv
        # NOTE: multithread=True wird nicht von allen py7zr-Versionen unterstützt
        # und py7zr nutzt standardmäßig Multi-Threading wenn verfügbar
        with py7zr.SevenZipFile(
            output_path,
            "w",
            filters=[{"id": py7zr.FILTER_LZMA2, "preset": self.compression_level}],
        ) as archive:

            for idx, file_path in enumerate(files):
                if not file_path.exists():
                    logger.warning(f"Datei nicht gefunden, überspringe: {file_path}")
                    continue

                # Berechne relativen Pfad im Archiv
                arcname: str
                if base_dir:
                    try:
                        arcname = str(file_path.relative_to(base_dir))
                    except ValueError:
                        # Datei ist nicht unter base_dir
                        arcname = file_path.name
                else:
                    arcname = file_path.name

                # Füge Datei zum Archiv hinzu
                archive.write(file_path, arcname=arcname)

                # Progress-Callback
                if progress_callback:
                    progress_callback(idx + 1, len(files), str(file_path))

                logger.debug(f"Hinzugefügt: {arcname}")

        archive_size = output_path.stat().st_size
        logger.info(f"Archiv erstellt: {output_path.name} " f"({archive_size / 1024 / 1024:.1f}MB)")

        return output_path

    def _compress_split(
        self,
        files: List[Path],
        output_path: Path,
        base_dir: Optional[Path] = None,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
    ) -> List[Path]:
        """
        Komprimiert Dateien zu mehreren 7z-Archiven (Split)

        Args:
            files: Liste der zu komprimierenden Dateien
            output_path: Basis-Pfad für Output-Archive
            base_dir: Basis-Verzeichnis für relative Pfade
            progress_callback: Optional Callback

        Returns:
            Liste der erstellten Archive-Pfade
        """
        archives: List[Path] = []

        # Sortiere Dateien nach Größe (größte zuerst)
        sorted_files = sorted(
            files, key=lambda f: f.stat().st_size if f.exists() else 0, reverse=True
        )

        # Teile Dateien in Chunks basierend auf split_size
        current_chunk: List[Path] = []
        current_size = 0
        chunk_index = 1

        for file_path in sorted_files:
            if not file_path.exists():
                continue

            file_size = file_path.stat().st_size

            # Wenn aktuelle Datei alleine schon zu groß ist
            if file_size > self.split_size:
                # Speichere aktuellen Chunk, falls vorhanden
                if current_chunk:
                    archive_path = self._get_split_path(output_path, chunk_index)
                    archives.append(
                        self._compress_single(
                            current_chunk, archive_path, base_dir, progress_callback
                        )
                    )
                    chunk_index += 1
                    current_chunk = []
                    current_size = 0

                # Erstelle eigenes Archiv für große Datei
                logger.warning(
                    f"Datei {file_path.name} ist größer als split_size "
                    f"({file_size / 1024 / 1024:.1f}MB), "
                    f"erstelle eigenes Archiv"
                )
                archive_path = self._get_split_path(output_path, chunk_index)
                archives.append(
                    self._compress_single([file_path], archive_path, base_dir, progress_callback)
                )
                chunk_index += 1
                continue

            # Prüfe, ob Datei in aktuellen Chunk passt
            if current_size + file_size > self.split_size and current_chunk:
                # Speichere aktuellen Chunk
                archive_path = self._get_split_path(output_path, chunk_index)
                archives.append(
                    self._compress_single(current_chunk, archive_path, base_dir, progress_callback)
                )
                chunk_index += 1
                current_chunk = []
                current_size = 0

            # Füge Datei zu aktuellem Chunk hinzu
            current_chunk.append(file_path)
            current_size += file_size

        # Speichere letzten Chunk
        if current_chunk:
            archive_path = self._get_split_path(output_path, chunk_index)
            archives.append(
                self._compress_single(current_chunk, archive_path, base_dir, progress_callback)
            )

        return archives

    def _get_split_path(self, base_path: Path, index: int) -> Path:
        """
        Generiert Pfad für Split-Archive

        Args:
            base_path: Basis-Pfad (z.B. backup.7z)
            index: Index des Splits (1-basiert)

        Returns:
            Pfad für Split-Archive (z.B. backup.001.7z)
        """
        stem = base_path.stem  # backup
        suffix = base_path.suffix  # .7z
        parent = base_path.parent

        split_name = f"{stem}.{index:03d}{suffix}"
        return parent / split_name

    def extract_archive(
        self,
        archive_path: Path,
        output_dir: Path,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
    ) -> List[Path]:
        """
        Entpackt 7z-Archiv

        Args:
            archive_path: Pfad zum Archiv
            output_dir: Ziel-Verzeichnis
            progress_callback: Optional Callback(current, total, filename)

        Returns:
            Liste der entpackten Dateien
        """
        if not archive_path.exists():
            raise FileNotFoundError(f"Archiv nicht gefunden: {archive_path}")

        logger.info(f"Entpacke Archiv: {archive_path}")

        # Erstelle Output-Verzeichnis
        output_dir.mkdir(parents=True, exist_ok=True)

        extracted_files: List[Path] = []

        # Entpacke Archiv
        with py7zr.SevenZipFile(archive_path, "r") as archive:
            # Hole Liste aller Dateien im Archiv
            all_names = archive.getnames()
            total_files = len(all_names)

            logger.info(f"Archiv enthält {total_files} Dateien")

            # Entpacke alle Dateien
            archive.extractall(path=output_dir)

            # Sammle entpackte Dateien (nur Dateien, keine Verzeichnisse!)
            for idx, name in enumerate(all_names):
                extracted_path = output_dir / name

                # Nur Dateien hinzufügen, keine Verzeichnisse
                if extracted_path.is_file():
                    extracted_files.append(extracted_path)
                    logger.debug(f"Entpackt (Datei): {name}")
                else:
                    logger.debug(f"Entpackt (Verzeichnis, übersprungen): {name}")

                # Progress-Callback
                if progress_callback:
                    progress_callback(idx + 1, total_files, name)

        logger.info(f"Entpacken abgeschlossen: {len(extracted_files)} Dateien")
        return extracted_files

    def extract_split_archives(
        self,
        archive_paths: List[Path],
        output_dir: Path,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
    ) -> List[Path]:
        """
        Entpackt mehrere Split-Archive

        Args:
            archive_paths: Liste der Archive-Pfade (in Reihenfolge)
            output_dir: Ziel-Verzeichnis
            progress_callback: Optional Callback

        Returns:
            Liste aller entpackten Dateien
        """
        all_extracted: List[Path] = []

        for archive_path in archive_paths:
            extracted = self.extract_archive(archive_path, output_dir, progress_callback)
            all_extracted.extend(extracted)

        return all_extracted

    def get_archive_info(self, archive_path: Path) -> dict:
        """
        Liefert Informationen über ein Archiv

        Args:
            archive_path: Pfad zum Archiv

        Returns:
            Dict mit Archiv-Informationen
        """
        if not archive_path.exists():
            raise FileNotFoundError(f"Archiv nicht gefunden: {archive_path}")

        with py7zr.SevenZipFile(archive_path, "r") as archive:
            file_list = archive.list()
            total_files = len(file_list)

            # Berechne Gesamt-Größe (unkomprimiert)
            total_size = sum(f.uncompressed for f in file_list)

            info = {
                "path": str(archive_path),
                "size": archive_path.stat().st_size,
                "files": total_files,
                "uncompressed_size": total_size,
                "compression_ratio": (
                    (1 - (archive_path.stat().st_size / total_size)) if total_size > 0 else 0
                ),
            }

        return info
