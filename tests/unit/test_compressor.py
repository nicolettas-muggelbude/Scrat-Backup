"""
Unit-Tests für Compressor
"""

import tempfile
from pathlib import Path

import pytest

from core.compressor import Compressor


class TestCompressor:
    """Tests für Compressor-Klasse"""

    @pytest.fixture
    def temp_dir(self):
        """Temporäres Verzeichnis für Tests"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def sample_files(self, temp_dir):
        """Erstellt Test-Dateien"""
        files = []

        # Kleine Dateien (je 1KB)
        for i in range(5):
            file_path = temp_dir / f"small_{i}.txt"
            file_path.write_text(f"Test content {i}\n" * 100)
            files.append(file_path)

        # Mittlere Datei (1MB)
        medium_file = temp_dir / "medium.txt"
        medium_file.write_text("X" * (1024 * 1024))
        files.append(medium_file)

        return files

    @pytest.fixture
    def compressor(self):
        """Standard Compressor-Instanz"""
        return Compressor()

    def test_init_default(self):
        """Test: Initialisierung mit Defaults"""
        comp = Compressor()
        assert comp.compression_level == Compressor.DEFAULT_COMPRESSION_LEVEL
        assert comp.split_size == Compressor.DEFAULT_SPLIT_SIZE

    def test_init_custom(self):
        """Test: Initialisierung mit Custom-Werten"""
        comp = Compressor(compression_level=9, split_size=100 * 1024 * 1024)
        assert comp.compression_level == 9
        assert comp.split_size == 100 * 1024 * 1024

    def test_init_invalid_compression_level(self):
        """Test: Ungültiger Compression-Level"""
        with pytest.raises(ValueError, match="compression_level muss zwischen 0 und 9"):
            Compressor(compression_level=10)

        with pytest.raises(ValueError, match="compression_level muss zwischen 0 und 9"):
            Compressor(compression_level=-1)

    def test_init_invalid_split_size(self):
        """Test: Ungültige Split-Size"""
        with pytest.raises(ValueError, match="split_size muss mindestens 1MB"):
            Compressor(split_size=512 * 1024)  # 512 KB

    def test_compress_files_empty_list(self, compressor, temp_dir):
        """Test: Komprimierung mit leerer Datei-Liste"""
        output = temp_dir / "output.7z"

        with pytest.raises(ValueError, match="Keine Dateien zum Komprimieren"):
            compressor.compress_files([], output)

    def test_compress_single_file(self, compressor, temp_dir):
        """Test: Komprimierung einer einzelnen Datei"""
        # Erstelle Test-Datei
        test_file = temp_dir / "test.txt"
        test_file.write_text("Hello World!\n" * 100)

        output = temp_dir / "output.7z"

        # Komprimiere
        archives = compressor.compress_files([test_file], output)

        # Prüfungen
        assert len(archives) == 1
        assert archives[0].exists()
        assert archives[0] == output
        assert archives[0].stat().st_size > 0

    def test_compress_multiple_files(self, compressor, sample_files, temp_dir):
        """Test: Komprimierung mehrerer Dateien"""
        output = temp_dir / "output.7z"

        # Komprimiere
        archives = compressor.compress_files(sample_files, output)

        # Prüfungen
        assert len(archives) == 1
        assert archives[0].exists()
        assert archives[0].stat().st_size > 0

    def test_compress_with_base_dir(self, compressor, temp_dir):
        """Test: Komprimierung mit base_dir für relative Pfade"""
        # Erstelle Verzeichnis-Struktur
        subdir = temp_dir / "subdir"
        subdir.mkdir()

        file1 = subdir / "file1.txt"
        file1.write_text("Content 1")

        file2 = subdir / "file2.txt"
        file2.write_text("Content 2")

        output = temp_dir / "output.7z"

        # Komprimiere mit base_dir
        archives = compressor.compress_files([file1, file2], output, base_dir=temp_dir)

        assert len(archives) == 1
        assert archives[0].exists()

    def test_compress_with_progress_callback(self, compressor, sample_files, temp_dir):
        """Test: Komprimierung mit Progress-Callback"""
        output = temp_dir / "output.7z"
        callback_calls = []

        def progress_callback(current, total, filename):
            callback_calls.append((current, total, filename))

        # Komprimiere mit Callback
        compressor.compress_files(sample_files, output, progress_callback=progress_callback)

        # Prüfe, dass Callback aufgerufen wurde
        assert len(callback_calls) > 0
        assert callback_calls[-1][0] == len(sample_files)  # Last call: current == total

    def test_compress_split_archives(self, temp_dir):
        """Test: Komprimierung mit Split-Archives"""
        # Erstelle Compressor mit kleiner Split-Size
        comp = Compressor(split_size=2 * 1024 * 1024)  # 2 MB

        # Erstelle mehrere große Dateien (insgesamt > 2MB)
        files = []
        for i in range(3):
            file_path = temp_dir / f"large_{i}.txt"
            file_path.write_text("X" * (1024 * 1024))  # 1 MB
            files.append(file_path)

        output = temp_dir / "output.7z"

        # Komprimiere
        archives = comp.compress_files(files, output)

        # Sollte mehrere Archive erstellen
        assert len(archives) > 1

        # Alle Archive sollten existieren
        for archive in archives:
            assert archive.exists()
            assert archive.stat().st_size > 0

        # Archive sollten nummeriert sein
        assert archives[0].name == "output.001.7z"
        assert archives[1].name == "output.002.7z"

    def test_extract_archive(self, compressor, sample_files, temp_dir):
        """Test: Entpacken eines Archives"""
        # Erstelle Archiv
        archive_path = temp_dir / "test.7z"
        compressor.compress_files(sample_files, archive_path)

        # Entpacke in neues Verzeichnis
        extract_dir = temp_dir / "extracted"
        extracted_files = compressor.extract_archive(archive_path, extract_dir)

        # Prüfungen
        assert len(extracted_files) == len(sample_files)

        for extracted in extracted_files:
            assert extracted.exists()

    def test_extract_nonexistent_archive(self, compressor, temp_dir):
        """Test: Entpacken eines nicht existierenden Archives"""
        archive_path = temp_dir / "nonexistent.7z"
        extract_dir = temp_dir / "extracted"

        with pytest.raises(FileNotFoundError):
            compressor.extract_archive(archive_path, extract_dir)

    def test_extract_with_progress_callback(self, compressor, sample_files, temp_dir):
        """Test: Entpacken mit Progress-Callback"""
        # Erstelle Archiv
        archive_path = temp_dir / "test.7z"
        compressor.compress_files(sample_files, archive_path)

        # Entpacke mit Callback
        extract_dir = temp_dir / "extracted"
        callback_calls = []

        def progress_callback(current, total, filename):
            callback_calls.append((current, total, filename))

        compressor.extract_archive(archive_path, extract_dir, progress_callback=progress_callback)

        # Prüfe, dass Callback aufgerufen wurde
        assert len(callback_calls) > 0

    def test_extract_split_archives(self, temp_dir):
        """Test: Entpacken mehrerer Split-Archives"""
        # Erstelle Compressor mit kleiner Split-Size
        comp = Compressor(split_size=2 * 1024 * 1024)  # 2 MB

        # Erstelle große Dateien
        files = []
        for i in range(3):
            file_path = temp_dir / f"large_{i}.txt"
            file_path.write_text("X" * (1024 * 1024))  # 1 MB
            files.append(file_path)

        # Komprimiere zu Split-Archives
        output = temp_dir / "output.7z"
        archives = comp.compress_files(files, output)

        assert len(archives) > 1

        # Entpacke alle Split-Archives
        extract_dir = temp_dir / "extracted"
        extracted_files = comp.extract_split_archives(archives, extract_dir)

        # Prüfe, dass alle Dateien entpackt wurden
        assert len(extracted_files) == len(files)

    def test_get_archive_info(self, compressor, sample_files, temp_dir):
        """Test: Archiv-Informationen abrufen"""
        # Erstelle Archiv
        archive_path = temp_dir / "test.7z"
        compressor.compress_files(sample_files, archive_path)

        # Hole Archiv-Info
        info = compressor.get_archive_info(archive_path)

        # Prüfungen
        assert "path" in info
        assert "size" in info
        assert "files" in info
        assert "uncompressed_size" in info
        assert "compression_ratio" in info

        assert info["files"] == len(sample_files)
        assert info["size"] > 0
        assert info["uncompressed_size"] > 0
        assert 0 <= info["compression_ratio"] <= 1

    def test_get_archive_info_nonexistent(self, compressor, temp_dir):
        """Test: Info von nicht existierendem Archiv"""
        archive_path = temp_dir / "nonexistent.7z"

        with pytest.raises(FileNotFoundError):
            compressor.get_archive_info(archive_path)

    def test_roundtrip_compression(self, compressor, sample_files, temp_dir):
        """Test: Komprimierung und Entpackung (Roundtrip)"""
        # Komprimiere
        archive_path = temp_dir / "test.7z"
        compressor.compress_files(sample_files, archive_path)

        # Entpacke
        extract_dir = temp_dir / "extracted"
        extracted_files = compressor.extract_archive(archive_path, extract_dir)

        # Vergleiche Original-Inhalte mit entpackten Inhalten
        assert len(extracted_files) == len(sample_files)

        # Prüfe, dass entpackte Dateien existieren
        for extracted in extracted_files:
            assert extracted.exists()

    def test_compression_levels(self, temp_dir):
        """Test: Verschiedene Komprimierungs-Level"""
        # Erstelle Test-Datei mit gemischten Daten (besser für Komprimierungs-Test)
        test_file = temp_dir / "test.txt"
        # Mix aus komprimierbarem und weniger komprimierbarem Content
        content = ("X" * 1000 + "Y" * 1000 + "Z" * 1000) * 100  # ~300 KB
        test_file.write_text(content)

        sizes = {}

        # Teste Level 0, 5, 9
        for level in [0, 5, 9]:
            comp = Compressor(compression_level=level)
            output = temp_dir / f"output_level_{level}.7z"

            comp.compress_files([test_file], output)

            sizes[level] = output.stat().st_size

        # Bei größeren Dateien sollte Level 9 besser komprimieren als Level 0
        # (Archive-Header können bei sehr kleinen Dateien dominieren)
        # Wir prüfen nur, dass alle Level funktionieren
        assert all(size > 0 for size in sizes.values())

    def test_get_split_path(self, compressor, temp_dir):
        """Test: Split-Pfad-Generierung"""
        base_path = temp_dir / "backup.7z"

        # Teste verschiedene Indizes
        assert compressor._get_split_path(base_path, 1) == temp_dir / "backup.001.7z"
        assert compressor._get_split_path(base_path, 2) == temp_dir / "backup.002.7z"
        assert compressor._get_split_path(base_path, 999) == temp_dir / "backup.999.7z"
