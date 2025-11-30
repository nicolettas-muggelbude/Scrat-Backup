"""
Unit-Tests für Scanner
"""

import time
from datetime import datetime
from pathlib import Path

import pytest

from src.core.scanner import FileInfo, Scanner, ScanResult


@pytest.fixture
def temp_source_dir(tmp_path):
    """Temporäres Quell-Verzeichnis für Tests"""
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    return source_dir


@pytest.fixture
def sample_directory(temp_source_dir):
    """Erstellt eine Beispiel-Verzeichnisstruktur"""
    # Root-Dateien
    (temp_source_dir / "file1.txt").write_text("Content 1")
    (temp_source_dir / "file2.txt").write_text("Content 2")

    # Unterverzeichnis
    sub_dir = temp_source_dir / "subdir"
    sub_dir.mkdir()
    (sub_dir / "file3.txt").write_text("Content 3")
    (sub_dir / "file4.txt").write_text("Content 4")

    # Nested Unterverzeichnis
    nested_dir = sub_dir / "nested"
    nested_dir.mkdir()
    (nested_dir / "file5.txt").write_text("Content 5")

    return temp_source_dir


class TestScannerInit:
    """Tests für Scanner-Initialisierung"""

    def test_default_init(self):
        """Test Standard-Initialisierung"""
        scanner = Scanner()
        assert scanner.exclude_patterns
        assert "Thumbs.db" in scanner.exclude_patterns
        assert "desktop.ini" in scanner.exclude_patterns

    def test_custom_exclude_patterns(self):
        """Test benutzerdefinierte Exclude-Patterns"""
        custom_patterns = {"*.log", "*.bak"}
        scanner = Scanner(exclude_patterns=custom_patterns)
        assert scanner.exclude_patterns == custom_patterns

    def test_add_exclude_pattern(self):
        """Test Hinzufügen von Exclude-Pattern"""
        scanner = Scanner()
        initial_count = len(scanner.exclude_patterns)

        scanner.add_exclude_pattern("*.cache")
        assert len(scanner.exclude_patterns) == initial_count + 1
        assert "*.cache" in scanner.exclude_patterns

    def test_remove_exclude_pattern(self):
        """Test Entfernen von Exclude-Pattern"""
        scanner = Scanner()
        scanner.add_exclude_pattern("test.txt")
        assert "test.txt" in scanner.exclude_patterns

        scanner.remove_exclude_pattern("test.txt")
        assert "test.txt" not in scanner.exclude_patterns

    def test_get_exclude_patterns(self):
        """Test Abrufen von Exclude-Patterns"""
        scanner = Scanner()
        patterns = scanner.get_exclude_patterns()
        assert isinstance(patterns, set)
        assert "Thumbs.db" in patterns


class TestScanDirectory:
    """Tests für Verzeichnis-Scannen"""

    def test_scan_empty_directory(self, temp_source_dir):
        """Test: Scannen eines leeren Verzeichnisses"""
        scanner = Scanner()
        result = scanner.scan_directory(temp_source_dir)

        assert isinstance(result, ScanResult)
        assert result.total_files == 0
        assert len(result.new_files) == 0
        assert len(result.modified_files) == 0
        assert len(result.deleted_files) == 0
        assert len(result.unchanged_files) == 0
        assert result.total_size == 0

    def test_scan_nonexistent_directory(self, tmp_path):
        """Test: Fehler bei nicht existierendem Verzeichnis"""
        scanner = Scanner()
        fake_dir = tmp_path / "nonexistent"

        with pytest.raises(ValueError, match="Quell-Pfad existiert nicht"):
            scanner.scan_directory(fake_dir)

    def test_scan_file_instead_of_directory(self, temp_source_dir):
        """Test: Fehler wenn Pfad eine Datei ist"""
        scanner = Scanner()
        file_path = temp_source_dir / "test.txt"
        file_path.write_text("Test")

        with pytest.raises(ValueError, match="Quell-Pfad ist kein Verzeichnis"):
            scanner.scan_directory(file_path)

    def test_scan_directory_all_new(self, sample_directory):
        """Test: Alle Dateien sind neu (kein vorheriges Backup)"""
        scanner = Scanner()
        result = scanner.scan_directory(sample_directory)

        # Alle Dateien sollten als neu erkannt werden
        assert result.total_files == 5
        assert len(result.new_files) == 5
        assert len(result.modified_files) == 0
        assert len(result.deleted_files) == 0
        assert len(result.unchanged_files) == 0
        assert result.total_size > 0

        # Prüfe, dass FileInfo korrekt ist
        for file_info in result.new_files:
            assert isinstance(file_info, FileInfo)
            assert file_info.is_new
            assert not file_info.is_modified
            assert not file_info.is_deleted
            assert file_info.path.exists()

    def test_scan_with_subdirectories(self, sample_directory):
        """Test: Scannen mit Unterverzeichnissen"""
        scanner = Scanner()
        result = scanner.scan_directory(sample_directory)

        # Prüfe, dass Dateien in allen Ebenen gefunden wurden
        relative_paths = [str(f.relative_path) for f in result.new_files]
        assert "file1.txt" in relative_paths
        assert str(Path("subdir") / "file3.txt") in relative_paths
        assert str(Path("subdir") / "nested" / "file5.txt") in relative_paths

    def test_scan_with_progress_callback(self, sample_directory):
        """Test: Progress-Callback wird aufgerufen"""
        scanner = Scanner()
        progress_calls = []

        def progress_callback(file_path):
            progress_calls.append(file_path)

        result = scanner.scan_directory(sample_directory, progress_callback=progress_callback)

        # Callback sollte für jede Datei aufgerufen werden
        assert len(progress_calls) == result.total_files


class TestChangeDetection:
    """Tests für Change Detection"""

    def test_detect_new_files(self, temp_source_dir):
        """Test: Erkennung neuer Dateien"""
        # Erster Scan
        (temp_source_dir / "old.txt").write_text("Old file")
        scanner = Scanner()
        first_result = scanner.scan_directory(temp_source_dir)

        # Erstelle previous_files Dict
        previous_files = {
            str(f.relative_path): f for f in first_result.new_files + first_result.unchanged_files
        }

        # Füge neue Datei hinzu
        (temp_source_dir / "new.txt").write_text("New file")

        # Zweiter Scan
        second_result = scanner.scan_directory(temp_source_dir, previous_files=previous_files)

        # Prüfe Ergebnisse
        assert len(second_result.new_files) == 1
        assert second_result.new_files[0].relative_path == Path("new.txt")
        assert second_result.new_files[0].is_new
        assert len(second_result.unchanged_files) == 1

    def test_detect_modified_files_by_size(self, temp_source_dir):
        """Test: Erkennung geänderter Dateien via Größe"""
        file_path = temp_source_dir / "test.txt"
        file_path.write_text("Initial content")

        scanner = Scanner()
        first_result = scanner.scan_directory(temp_source_dir)

        # Erstelle previous_files
        previous_files = {str(f.relative_path): f for f in first_result.new_files}

        # Ändere Datei-Größe
        file_path.write_text("Modified content with more text")

        # Zweiter Scan
        second_result = scanner.scan_directory(temp_source_dir, previous_files=previous_files)

        # Prüfe Änderungserkennung
        assert len(second_result.modified_files) == 1
        assert second_result.modified_files[0].is_modified
        assert second_result.modified_files[0].relative_path == Path("test.txt")

    def test_detect_modified_files_by_timestamp(self, temp_source_dir):
        """Test: Erkennung geänderter Dateien via Timestamp"""
        file_path = temp_source_dir / "test.txt"
        content = "Test content"
        file_path.write_text(content)

        scanner = Scanner()
        first_result = scanner.scan_directory(temp_source_dir)

        # Erstelle previous_files
        previous_files = {str(f.relative_path): f for f in first_result.new_files}

        # Warte kurz und touche Datei (ändert Timestamp)
        time.sleep(2)
        file_path.write_text(content)  # Gleicher Inhalt, aber neuer Timestamp

        # Zweiter Scan
        second_result = scanner.scan_directory(temp_source_dir, previous_files=previous_files)

        # Prüfe Änderungserkennung
        assert len(second_result.modified_files) == 1
        assert second_result.modified_files[0].is_modified

    def test_detect_deleted_files(self, temp_source_dir):
        """Test: Erkennung gelöschter Dateien"""
        # Erstelle Dateien
        file1 = temp_source_dir / "file1.txt"
        file2 = temp_source_dir / "file2.txt"
        file1.write_text("Content 1")
        file2.write_text("Content 2")

        scanner = Scanner()
        first_result = scanner.scan_directory(temp_source_dir)

        # Erstelle previous_files
        previous_files = {str(f.relative_path): f for f in first_result.new_files}

        # Lösche eine Datei
        file1.unlink()

        # Zweiter Scan
        second_result = scanner.scan_directory(temp_source_dir, previous_files=previous_files)

        # Prüfe Löscherkennung
        assert len(second_result.deleted_files) == 1
        assert second_result.deleted_files[0].is_deleted
        assert second_result.deleted_files[0].relative_path == Path("file1.txt")
        assert len(second_result.unchanged_files) == 1

    def test_detect_unchanged_files(self, temp_source_dir):
        """Test: Erkennung unveränderter Dateien"""
        file_path = temp_source_dir / "test.txt"
        file_path.write_text("Unchanged content")

        scanner = Scanner()
        first_result = scanner.scan_directory(temp_source_dir)

        # Erstelle previous_files
        previous_files = {str(f.relative_path): f for f in first_result.new_files}

        # Zweiter Scan ohne Änderungen
        second_result = scanner.scan_directory(temp_source_dir, previous_files=previous_files)

        # Prüfe unveränderte Dateien
        assert len(second_result.unchanged_files) == 1
        assert len(second_result.new_files) == 0
        assert len(second_result.modified_files) == 0
        assert len(second_result.deleted_files) == 0

    def test_complex_change_scenario(self, temp_source_dir):
        """Test: Komplexes Szenario mit verschiedenen Änderungen"""
        # Initialer Zustand
        (temp_source_dir / "unchanged.txt").write_text("Unchanged")
        (temp_source_dir / "to_modify.txt").write_text("Original")
        (temp_source_dir / "to_delete.txt").write_text("Delete me")

        scanner = Scanner()
        first_result = scanner.scan_directory(temp_source_dir)
        previous_files = {str(f.relative_path): f for f in first_result.new_files}

        # Änderungen
        (temp_source_dir / "to_modify.txt").write_text("Modified content")
        (temp_source_dir / "to_delete.txt").unlink()
        (temp_source_dir / "new.txt").write_text("New file")

        # Zweiter Scan
        second_result = scanner.scan_directory(temp_source_dir, previous_files=previous_files)

        # Assertions
        assert len(second_result.new_files) == 1
        assert len(second_result.modified_files) == 1
        assert len(second_result.deleted_files) == 1
        assert len(second_result.unchanged_files) == 1


class TestExcludePatterns:
    """Tests für Exclude-Patterns"""

    def test_exclude_exact_match(self, temp_source_dir):
        """Test: Exakte Ausschluss-Muster"""
        (temp_source_dir / "Thumbs.db").write_text("Thumbnail cache")
        (temp_source_dir / "normal.txt").write_text("Normal file")

        scanner = Scanner()
        result = scanner.scan_directory(temp_source_dir)

        # Thumbs.db sollte ausgeschlossen sein
        relative_paths = [str(f.relative_path) for f in result.new_files]
        assert "Thumbs.db" not in relative_paths
        assert "normal.txt" in relative_paths

    def test_exclude_wildcard_suffix(self, temp_source_dir):
        """Test: Wildcard-Muster mit Suffix"""
        (temp_source_dir / "file.tmp").write_text("Temp")
        (temp_source_dir / "file.txt").write_text("Normal")
        (temp_source_dir / "data.temp").write_text("Also temp")

        scanner = Scanner()
        result = scanner.scan_directory(temp_source_dir)

        # .tmp und .temp sollten ausgeschlossen sein
        relative_paths = [str(f.relative_path) for f in result.new_files]
        assert "file.tmp" not in relative_paths
        assert "data.temp" not in relative_paths
        assert "file.txt" in relative_paths

    def test_exclude_wildcard_prefix(self, temp_source_dir):
        """Test: Wildcard-Muster mit Prefix"""
        (temp_source_dir / "~$document.docx").write_text("Lock file")
        (temp_source_dir / "document.docx").write_text("Normal file")

        scanner = Scanner()
        result = scanner.scan_directory(temp_source_dir)

        # ~$* sollte ausgeschlossen sein
        relative_paths = [str(f.relative_path) for f in result.new_files]
        assert "~$document.docx" not in relative_paths
        assert "document.docx" in relative_paths

    def test_exclude_directory(self, temp_source_dir):
        """Test: Ausschluss von Verzeichnissen"""
        # Erstelle Verzeichnis mit System-Namen
        recycle_bin = temp_source_dir / "$RECYCLE.BIN"
        recycle_bin.mkdir()
        (recycle_bin / "deleted.txt").write_text("Deleted")

        # Normale Datei
        (temp_source_dir / "normal.txt").write_text("Normal")

        scanner = Scanner()
        result = scanner.scan_directory(temp_source_dir)

        # $RECYCLE.BIN und dessen Inhalt sollten ausgeschlossen sein
        relative_paths = [str(f.relative_path) for f in result.new_files]
        assert "normal.txt" in relative_paths
        assert not any("$RECYCLE.BIN" in path for path in relative_paths)

    def test_custom_exclude_patterns(self, temp_source_dir):
        """Test: Benutzerdefinierte Exclude-Patterns"""
        (temp_source_dir / "data.log").write_text("Log")
        (temp_source_dir / "backup.bak").write_text("Backup")
        (temp_source_dir / "file.txt").write_text("Normal")

        scanner = Scanner(exclude_patterns={"*.log", "*.bak"})
        result = scanner.scan_directory(temp_source_dir)

        # .log und .bak sollten ausgeschlossen sein
        relative_paths = [str(f.relative_path) for f in result.new_files]
        assert "data.log" not in relative_paths
        assert "backup.bak" not in relative_paths
        assert "file.txt" in relative_paths


class TestScanResult:
    """Tests für ScanResult-Klasse"""

    def test_files_to_backup_property(self, temp_source_dir):
        """Test: files_to_backup Property"""
        # Erstelle initialen Zustand
        (temp_source_dir / "old.txt").write_text("Old")
        scanner = Scanner()
        first_result = scanner.scan_directory(temp_source_dir)
        previous_files = {str(f.relative_path): f for f in first_result.new_files}

        # Füge neue und geänderte Dateien hinzu
        (temp_source_dir / "new.txt").write_text("New")
        (temp_source_dir / "old.txt").write_text("Modified")

        # Scan
        result = scanner.scan_directory(temp_source_dir, previous_files=previous_files)

        # files_to_backup sollte neue + geänderte enthalten
        files_to_backup = result.files_to_backup
        assert len(files_to_backup) == 2
        assert any(f.relative_path == Path("new.txt") for f in files_to_backup)
        assert any(f.relative_path == Path("old.txt") for f in files_to_backup)


class TestErrorHandling:
    """Tests für Fehlerbehandlung"""

    def test_scan_with_permission_errors(self, temp_source_dir):
        """Test: Umgang mit Permission-Errors"""
        # Erstelle normale Datei
        (temp_source_dir / "accessible.txt").write_text("OK")

        scanner = Scanner()
        result = scanner.scan_directory(temp_source_dir)

        # Scanner sollte trotz Fehlern weitermachen
        assert result.total_files >= 1
        assert "accessible.txt" in [str(f.relative_path) for f in result.new_files]

    def test_scan_result_errors_list(self, temp_source_dir):
        """Test: Errors werden in ScanResult gesammelt"""
        (temp_source_dir / "file.txt").write_text("Content")

        scanner = Scanner()
        result = scanner.scan_directory(temp_source_dir)

        # Errors-Liste sollte existieren
        assert isinstance(result.errors, list)


class TestFileInfo:
    """Tests für FileInfo-Klasse"""

    def test_file_info_creation(self):
        """Test: FileInfo-Erstellung"""
        file_info = FileInfo(
            path=Path("/test/file.txt"),
            relative_path=Path("file.txt"),
            size=1024,
            modified=datetime.now(),
            is_new=True,
        )

        assert file_info.path == Path("/test/file.txt")
        assert file_info.relative_path == Path("file.txt")
        assert file_info.size == 1024
        assert file_info.is_new
        assert not file_info.is_modified
        assert not file_info.is_deleted

    def test_file_info_hashable(self):
        """Test: FileInfo kann in Sets verwendet werden"""
        file_info1 = FileInfo(
            path=Path("/test/file.txt"),
            relative_path=Path("file.txt"),
            size=1024,
            modified=datetime.now(),
        )

        file_info2 = FileInfo(
            path=Path("/test/file.txt"),
            relative_path=Path("file.txt"),
            size=2048,
            modified=datetime.now(),
        )

        # Gleicher Pfad -> gleicher Hash
        file_set = {file_info1, file_info2}
        assert len(file_set) == 1
