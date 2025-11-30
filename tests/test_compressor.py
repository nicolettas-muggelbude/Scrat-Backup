"""
Unit-Tests für Compressor
"""

import pytest

from src.core.compressor import Compressor


@pytest.fixture
def temp_dir(tmp_path):
    """Temporäres Verzeichnis für Tests"""
    test_dir = tmp_path / "test_data"
    test_dir.mkdir()
    return test_dir


@pytest.fixture
def sample_files(temp_dir):
    """Erstellt Test-Dateien mit verschiedenen Größen"""
    files = []

    # Kleine Dateien (100KB)
    for i in range(5):
        file_path = temp_dir / f"small_{i}.txt"
        file_path.write_bytes(b"x" * (100 * 1024))
        files.append(file_path)

    # Mittelgroße Dateien (10MB)
    for i in range(3):
        file_path = temp_dir / f"medium_{i}.bin"
        file_path.write_bytes(b"y" * (10 * 1024 * 1024))
        files.append(file_path)

    # Große Datei (100MB)
    large_file = temp_dir / "large.dat"
    large_file.write_bytes(b"z" * (100 * 1024 * 1024))
    files.append(large_file)

    return files


@pytest.fixture
def output_dir(tmp_path):
    """Output-Verzeichnis für Archive"""
    out_dir = tmp_path / "output"
    out_dir.mkdir()
    return out_dir


class TestCompressorInit:
    """Tests für Compressor-Initialisierung"""

    def test_default_init(self):
        """Test Standard-Initialisierung"""
        compressor = Compressor()
        assert compressor.compression_level == 5
        assert compressor.split_size == 500 * 1024 * 1024

    def test_custom_init(self):
        """Test benutzerdefinierte Initialisierung"""
        compressor = Compressor(compression_level=3, split_size=100 * 1024 * 1024)
        assert compressor.compression_level == 3
        assert compressor.split_size == 100 * 1024 * 1024

    def test_invalid_compression_level(self):
        """Test ungültiger Komprimierungs-Level"""
        with pytest.raises(ValueError, match="compression_level muss zwischen 0 und 9 liegen"):
            Compressor(compression_level=10)

        with pytest.raises(ValueError, match="compression_level muss zwischen 0 und 9 liegen"):
            Compressor(compression_level=-1)

    def test_invalid_split_size(self):
        """Test ungültige Split-Size"""
        with pytest.raises(ValueError, match="split_size muss mindestens 1MB sein"):
            Compressor(split_size=500 * 1024)  # 500KB


class TestCompressSingle:
    """Tests für Single-Archive-Komprimierung"""

    def test_compress_single_archive(self, temp_dir, output_dir):
        """Test: Erstelle einzelnes Archiv"""
        # Erstelle kleine Test-Dateien
        files = []
        for i in range(3):
            file_path = temp_dir / f"test_{i}.txt"
            file_path.write_text(f"Test content {i}")
            files.append(file_path)

        compressor = Compressor()
        output_path = output_dir / "test.7z"

        # Komprimiere
        archives = compressor.compress_files(files, output_path)

        # Assertions
        assert len(archives) == 1
        assert archives[0].exists()
        assert archives[0] == output_path
        assert archives[0].stat().st_size > 0

    def test_compress_with_base_dir(self, temp_dir, output_dir):
        """Test: Komprimierung mit base_dir für relative Pfade"""
        # Erstelle Dateien in Unterverzeichnis
        sub_dir = temp_dir / "subdir"
        sub_dir.mkdir()

        files = []
        for i in range(2):
            file_path = sub_dir / f"file_{i}.txt"
            file_path.write_text(f"Content {i}")
            files.append(file_path)

        compressor = Compressor()
        output_path = output_dir / "test_base.7z"

        # Komprimiere mit base_dir
        archives = compressor.compress_files(files, output_path, base_dir=temp_dir)

        # Extrahiere und prüfe Struktur
        extract_dir = output_dir / "extracted"
        extracted = compressor.extract_archive(archives[0], extract_dir)

        # Prüfe, dass relative Pfade erhalten bleiben
        assert len(extracted) == 2
        assert (extract_dir / "subdir" / "file_0.txt").exists()
        assert (extract_dir / "subdir" / "file_1.txt").exists()

    def test_compress_empty_list(self, output_dir):
        """Test: Fehler bei leerer Dateiliste"""
        compressor = Compressor()
        output_path = output_dir / "test.7z"

        with pytest.raises(ValueError, match="Keine Dateien zum Komprimieren angegeben"):
            compressor.compress_files([], output_path)

    def test_compress_with_progress_callback(self, temp_dir, output_dir):
        """Test: Progress-Callback wird aufgerufen"""
        files = []
        for i in range(5):
            file_path = temp_dir / f"test_{i}.txt"
            file_path.write_text(f"Test {i}")
            files.append(file_path)

        compressor = Compressor()
        output_path = output_dir / "test.7z"

        # Callback-Tracker
        progress_calls = []

        def progress_callback(current, total, filename):
            progress_calls.append((current, total, filename))

        # Komprimiere mit Callback
        compressor.compress_files(files, output_path, progress_callback=progress_callback)

        # Prüfe Callbacks
        assert len(progress_calls) == 5
        assert progress_calls[0][0] == 1
        assert progress_calls[-1][0] == 5
        assert all(call[1] == 5 for call in progress_calls)


class TestCompressSplit:
    """Tests für Split-Archive-Komprimierung"""

    def test_compress_split_archives(self, temp_dir, output_dir):
        """Test: Erstelle Split-Archive"""
        # Erstelle Dateien, die größer als split_size sind
        files = []
        file_size = 10 * 1024 * 1024  # 10MB pro Datei

        for i in range(3):
            file_path = temp_dir / f"large_{i}.bin"
            file_path.write_bytes(b"x" * file_size)
            files.append(file_path)

        # Komprimiere mit kleiner Split-Size (15MB)
        compressor = Compressor(split_size=15 * 1024 * 1024)
        output_path = output_dir / "split.7z"

        archives = compressor.compress_files(files, output_path)

        # Prüfe, dass mehrere Archive erstellt wurden
        assert len(archives) > 1
        assert all(archive.exists() for archive in archives)

        # Prüfe Namenskonvention
        assert archives[0].name == "split.001.7z"
        assert archives[1].name == "split.002.7z"

    def test_split_single_large_file(self, temp_dir, output_dir):
        """Test: Einzelne Datei größer als split_size"""
        # Erstelle Datei größer als split_size
        large_file = temp_dir / "huge.bin"
        large_file.write_bytes(b"x" * (30 * 1024 * 1024))  # 30MB

        compressor = Compressor(split_size=20 * 1024 * 1024)  # 20MB
        output_path = output_dir / "test.7z"

        # Komprimiere
        archives = compressor.compress_files([large_file], output_path)

        # Datei sollte in eigenem Archiv sein
        assert len(archives) == 1
        assert archives[0].exists()


class TestExtract:
    """Tests für Archive-Extraktion"""

    def test_extract_archive(self, temp_dir, output_dir):
        """Test: Extrahiere Archiv"""
        # Erstelle und komprimiere Dateien
        files = []
        for i in range(3):
            file_path = temp_dir / f"file_{i}.txt"
            content = f"Test content {i}"
            file_path.write_text(content)
            files.append(file_path)

        compressor = Compressor()
        archive_path = output_dir / "test.7z"
        compressor.compress_files(files, archive_path)

        # Extrahiere
        extract_dir = output_dir / "extracted"
        extracted = compressor.extract_archive(archive_path, extract_dir)

        # Prüfe extrahierte Dateien
        assert len(extracted) == 3
        assert all(f.exists() for f in extracted)

        # Prüfe Inhalte
        for i, file_path in enumerate(extracted):
            assert file_path.name == f"file_{i}.txt"
            assert file_path.read_text() == f"Test content {i}"

    def test_extract_nonexistent_archive(self, output_dir):
        """Test: Fehler bei nicht existierendem Archiv"""
        compressor = Compressor()
        fake_archive = output_dir / "nonexistent.7z"
        extract_dir = output_dir / "extracted"

        with pytest.raises(FileNotFoundError, match="Archiv nicht gefunden"):
            compressor.extract_archive(fake_archive, extract_dir)

    def test_extract_with_progress_callback(self, temp_dir, output_dir):
        """Test: Progress-Callback beim Extrahieren"""
        # Erstelle Archiv
        files = []
        for i in range(5):
            file_path = temp_dir / f"file_{i}.txt"
            file_path.write_text(f"Content {i}")
            files.append(file_path)

        compressor = Compressor()
        archive_path = output_dir / "test.7z"
        compressor.compress_files(files, archive_path)

        # Extrahiere mit Callback
        extract_dir = output_dir / "extracted"
        progress_calls = []

        def progress_callback(current, total, filename):
            progress_calls.append((current, total, filename))

        compressor.extract_archive(archive_path, extract_dir, progress_callback=progress_callback)

        # Prüfe Callbacks
        assert len(progress_calls) == 5
        assert progress_calls[0][0] == 1
        assert progress_calls[-1][0] == 5

    def test_extract_split_archives(self, temp_dir, output_dir):
        """Test: Extrahiere Split-Archive"""
        # Erstelle Split-Archive
        files = []
        for i in range(5):
            file_path = temp_dir / f"file_{i}.bin"
            file_path.write_bytes(b"x" * (10 * 1024 * 1024))
            files.append(file_path)

        compressor = Compressor(split_size=20 * 1024 * 1024)
        output_path = output_dir / "split.7z"
        archives = compressor.compress_files(files, output_path)

        # Extrahiere alle Archive
        extract_dir = output_dir / "extracted"
        extracted = compressor.extract_split_archives(archives, extract_dir)

        # Prüfe
        assert len(extracted) == 5
        assert all(f.exists() for f in extracted)


class TestArchiveInfo:
    """Tests für Archive-Informationen"""

    def test_get_archive_info(self, temp_dir, output_dir):
        """Test: Hole Archiv-Informationen"""
        # Erstelle Archiv
        files = []
        for i in range(3):
            file_path = temp_dir / f"file_{i}.txt"
            file_path.write_text("x" * 1000)
            files.append(file_path)

        compressor = Compressor()
        archive_path = output_dir / "test.7z"
        compressor.compress_files(files, archive_path)

        # Hole Info
        info = compressor.get_archive_info(archive_path)

        # Prüfe Info
        assert "path" in info
        assert "size" in info
        assert "files" in info
        assert "uncompressed_size" in info
        assert "compression_ratio" in info

        assert info["files"] == 3
        assert info["size"] > 0
        assert info["uncompressed_size"] > 0
        assert 0 <= info["compression_ratio"] <= 1

    def test_get_archive_info_nonexistent(self, output_dir):
        """Test: Fehler bei nicht existierendem Archiv"""
        compressor = Compressor()
        fake_archive = output_dir / "nonexistent.7z"

        with pytest.raises(FileNotFoundError, match="Archiv nicht gefunden"):
            compressor.get_archive_info(fake_archive)


class TestSplitPath:
    """Tests für Split-Path-Generierung"""

    def test_get_split_path(self, output_dir):
        """Test: Generiere Split-Pfad"""
        compressor = Compressor()
        base_path = output_dir / "backup.7z"

        # Teste verschiedene Indizes
        assert compressor._get_split_path(base_path, 1) == output_dir / "backup.001.7z"
        assert compressor._get_split_path(base_path, 2) == output_dir / "backup.002.7z"
        assert compressor._get_split_path(base_path, 999) == output_dir / "backup.999.7z"
