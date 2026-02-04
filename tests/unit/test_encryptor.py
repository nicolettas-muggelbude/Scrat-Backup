"""
Unit-Tests für Encryptor
"""

import secrets
from io import BytesIO

import pytest
from cryptography.exceptions import InvalidTag

from core.encryptor import Encryptor


class TestEncryptor:
    """Tests für Encryptor-Klasse"""

    @pytest.fixture
    def password(self):
        """Test-Passwort"""
        return "TestPassword123!SuperSicher"

    @pytest.fixture
    def encryptor(self, password):
        """Encryptor-Instanz für Tests"""
        return Encryptor(password)

    def test_initialization_generates_salt(self, password):
        """Test: Initialisierung generiert Salt"""
        enc = Encryptor(password)

        assert enc.salt is not None
        assert len(enc.salt) == Encryptor.SALT_SIZE
        assert enc.key is not None
        assert len(enc.key) == Encryptor.KEY_SIZE

    def test_initialization_with_existing_salt(self, password):
        """Test: Initialisierung mit existierendem Salt"""
        salt = secrets.token_bytes(Encryptor.SALT_SIZE)
        enc = Encryptor(password, salt=salt)

        assert enc.salt == salt
        assert len(enc.key) == Encryptor.KEY_SIZE

    def test_initialization_with_invalid_salt(self, password):
        """Test: Initialisierung mit ungültigem Salt wirft Fehler"""
        invalid_salt = b"too_short"

        with pytest.raises(ValueError, match="Salt muss"):
            Encryptor(password, salt=invalid_salt)

    def test_same_password_same_salt_same_key(self, password):
        """Test: Gleiches Passwort + Salt = Gleicher Key"""
        salt = secrets.token_bytes(Encryptor.SALT_SIZE)

        enc1 = Encryptor(password, salt=salt)
        enc2 = Encryptor(password, salt=salt)

        assert enc1.key == enc2.key
        assert enc1.get_key_hash() == enc2.get_key_hash()

    def test_different_salt_different_key(self, password):
        """Test: Unterschiedliche Salts = Unterschiedliche Keys"""
        enc1 = Encryptor(password)
        enc2 = Encryptor(password)

        assert enc1.salt != enc2.salt
        assert enc1.key != enc2.key

    def test_get_key_hash(self, encryptor):
        """Test: Key-Hash wird korrekt generiert"""
        key_hash = encryptor.get_key_hash()

        assert isinstance(key_hash, str)
        assert len(key_hash) == 64  # SHA-256 hex = 64 Zeichen

    def test_encrypt_decrypt_bytes_roundtrip(self, encryptor):
        """Test: Verschlüsselung und Entschlüsselung (Roundtrip)"""
        plaintext = b"Geheime Daten! 12345"

        # Verschlüsseln
        ciphertext, nonce = encryptor.encrypt_bytes(plaintext)

        assert ciphertext != plaintext
        assert len(nonce) == Encryptor.NONCE_SIZE

        # Entschlüsseln
        decrypted = encryptor.decrypt_bytes(ciphertext, nonce)

        assert decrypted == plaintext

    def test_encrypt_bytes_different_nonce_each_time(self, encryptor):
        """Test: Jede Verschlüsselung hat unterschiedlichen Nonce"""
        plaintext = b"Same data"

        ciphertext1, nonce1 = encryptor.encrypt_bytes(plaintext)
        ciphertext2, nonce2 = encryptor.encrypt_bytes(plaintext)

        assert nonce1 != nonce2
        assert ciphertext1 != ciphertext2  # Wegen unterschiedlichem Nonce

    def test_decrypt_with_wrong_nonce_fails(self, encryptor):
        """Test: Entschlüsselung mit falschem Nonce schlägt fehl"""
        plaintext = b"Secret data"
        ciphertext, _ = encryptor.encrypt_bytes(plaintext)

        # Falscher Nonce
        wrong_nonce = secrets.token_bytes(Encryptor.NONCE_SIZE)

        with pytest.raises(InvalidTag):
            encryptor.decrypt_bytes(ciphertext, wrong_nonce)

    def test_decrypt_with_wrong_password_fails(self, password):
        """Test: Entschlüsselung mit falschem Passwort schlägt fehl"""
        enc1 = Encryptor(password)
        plaintext = b"Secret data"

        ciphertext, nonce = enc1.encrypt_bytes(plaintext)

        # Anderes Passwort (aber gleicher Salt!)
        enc2 = Encryptor("WrongPassword123!", salt=enc1.salt)

        with pytest.raises(InvalidTag):
            enc2.decrypt_bytes(ciphertext, nonce)

    def test_decrypt_with_invalid_nonce_size(self, encryptor):
        """Test: Entschlüsselung mit ungültiger Nonce-Größe"""
        ciphertext = b"some encrypted data"
        invalid_nonce = b"short"

        with pytest.raises(ValueError, match="Nonce muss"):
            encryptor.decrypt_bytes(ciphertext, invalid_nonce)

    def test_encrypt_decrypt_empty_data(self, encryptor):
        """Test: Verschlüsselung von leeren Daten"""
        plaintext = b""

        ciphertext, nonce = encryptor.encrypt_bytes(plaintext)
        decrypted = encryptor.decrypt_bytes(ciphertext, nonce)

        assert decrypted == plaintext

    def test_encrypt_decrypt_large_data(self, encryptor):
        """Test: Verschlüsselung von großen Daten (1 MB)"""
        # 1 MB zufällige Daten
        plaintext = secrets.token_bytes(1024 * 1024)

        ciphertext, nonce = encryptor.encrypt_bytes(plaintext)
        decrypted = encryptor.decrypt_bytes(ciphertext, nonce)

        assert decrypted == plaintext

    def test_encrypt_file(self, encryptor, tmp_path):
        """Test: Datei verschlüsseln"""
        # Test-Datei erstellen
        input_file = tmp_path / "test.txt"
        input_file.write_text("Geheime Datei-Inhalte! 🔒")

        output_file = tmp_path / "test.txt.encrypted"

        # Verschlüsseln
        nonce = encryptor.encrypt_file(input_file, output_file)

        assert output_file.exists()
        assert len(nonce) == Encryptor.NONCE_SIZE

        # Verschlüsselte Datei sollte anders sein
        encrypted_content = output_file.read_bytes()
        original_content = input_file.read_bytes()
        assert encrypted_content != original_content

    def test_encrypt_decrypt_file_roundtrip(self, encryptor, tmp_path):
        """Test: Datei verschlüsseln und entschlüsseln (Roundtrip)"""
        # Test-Datei erstellen
        input_file = tmp_path / "original.txt"
        original_content = "Geheime Datei-Inhalte! 🔒\nZeile 2\nZeile 3"
        input_file.write_text(original_content, encoding="utf-8")

        encrypted_file = tmp_path / "encrypted.bin"
        decrypted_file = tmp_path / "decrypted.txt"

        # Verschlüsseln (Nonce wird in Datei eingebettet)
        _nonce = encryptor.encrypt_file(input_file, encrypted_file)  # noqa: F841

        # Entschlüsseln (Nonce wird aus Datei gelesen)
        encryptor.decrypt_file(encrypted_file, decrypted_file)

        assert decrypted_file.exists()

        # Inhalt muss identisch sein
        decrypted_content = decrypted_file.read_text(encoding="utf-8")
        assert decrypted_content == original_content

    def test_encrypt_file_not_found(self, encryptor, tmp_path):
        """Test: Verschlüsselung nicht-existierender Datei wirft Fehler"""
        input_file = tmp_path / "does_not_exist.txt"
        output_file = tmp_path / "output.bin"

        with pytest.raises(FileNotFoundError):
            encryptor.encrypt_file(input_file, output_file)

    def test_decrypt_file_not_found(self, encryptor, tmp_path):
        """Test: Entschlüsselung nicht-existierender Datei wirft Fehler"""
        input_file = tmp_path / "does_not_exist.bin"
        output_file = tmp_path / "output.txt"

        with pytest.raises(FileNotFoundError):
            encryptor.decrypt_file(input_file, output_file)

    def test_encrypt_file_creates_output_directory(self, encryptor, tmp_path):
        """Test: Verschlüsselung erstellt Output-Verzeichnis"""
        input_file = tmp_path / "test.txt"
        input_file.write_text("Test")

        # Output in noch nicht existierendem Verzeichnis
        output_file = tmp_path / "nested" / "dir" / "encrypted.bin"

        encryptor.encrypt_file(input_file, output_file)

        assert output_file.exists()
        assert output_file.parent.exists()

    def test_encrypt_decrypt_stream(self, encryptor):
        """Test: Stream verschlüsseln und entschlüsseln"""
        plaintext = b"Stream data! 123 \xc3\xa4\xc3\xb6\xc3\xbc"

        # Input-Stream
        input_stream = BytesIO(plaintext)
        encrypted_stream = BytesIO()

        # Verschlüsseln
        nonce = encryptor.encrypt_stream(input_stream, encrypted_stream)

        # Entschlüsseln
        encrypted_stream.seek(0)
        decrypted_stream = BytesIO()
        encryptor.decrypt_stream(encrypted_stream, decrypted_stream, nonce)

        # Vergleichen
        decrypted_stream.seek(0)
        decrypted = decrypted_stream.read()

        assert decrypted == plaintext

    def test_generate_password(self):
        """Test: Passwort-Generierung"""
        password = Encryptor.generate_password()

        assert isinstance(password, str)
        assert len(password) > 0

        # Zwei Aufrufe sollten unterschiedliche Passwörter erzeugen
        password2 = Encryptor.generate_password()
        assert password != password2

    def test_generate_password_custom_length(self):
        """Test: Passwort-Generierung mit benutzerdefinierter Länge"""
        password = Encryptor.generate_password(length=64)

        # Base64 encoding macht String länger als Byte-Input
        assert len(password) >= 64

    def test_validate_password_strength_weak(self):
        """Test: Schwache Passwörter werden erkannt"""
        weak_passwords = [
            "short",  # Zu kurz
            "nouppercase123!",  # Keine Großbuchstaben
            "NOLOWERCASE123!",  # Keine Kleinbuchstaben
            "NoDigitsHere!",  # Keine Ziffern
            "Short1",  # Zu kurz (nur 6 Zeichen)
        ]

        for pwd in weak_passwords:
            is_valid, msg = Encryptor.validate_password_strength(pwd)
            assert is_valid is False, f"Passwort sollte ungültig sein: {pwd}"
            assert len(msg) > 0

    def test_validate_password_strength_strong(self):
        """Test: Starke Passwörter werden akzeptiert"""
        strong_passwords = [
            "ValidPassword123!",
            "SuperSicher2024$Backup",
            "Scrat-Backup-P@ssw0rd",
        ]

        for pwd in strong_passwords:
            is_valid, msg = Encryptor.validate_password_strength(pwd)
            assert is_valid is True, f"Passwort sollte gültig sein: {pwd}"
            assert "sicher" in msg.lower()

    def test_validate_password_strength_no_special_chars(self):
        """Test: Passwort ohne Sonderzeichen (Warnung aber gültig)"""
        # Dieses Passwort sollte gültig sein (hat Groß-, Klein-, Zahlen, >12 Zeichen)
        # aber keine Sonderzeichen
        pwd = "ValidPassword123"

        is_valid, msg = Encryptor.validate_password_strength(pwd)
        assert is_valid is True
        assert "sicher" in msg.lower()

    def test_repr(self, encryptor):
        """Test: String-Repräsentation"""
        repr_str = repr(encryptor)

        assert "Encryptor" in repr_str
        assert "key_hash=" in repr_str
        assert len(repr_str) < 100  # Sollte gekürzt sein

    def test_binary_data_encryption(self, encryptor):
        """Test: Verschlüsselung von Binärdaten"""
        # Zufällige Binärdaten (nicht UTF-8)
        binary_data = bytes(range(256))

        ciphertext, nonce = encryptor.encrypt_bytes(binary_data)
        decrypted = encryptor.decrypt_bytes(ciphertext, nonce)

        assert decrypted == binary_data

    def test_unicode_data_encryption(self, encryptor):
        """Test: Verschlüsselung von Unicode-Daten"""
        unicode_text = "Deutsch: äöü ÄÖÜ ß, Emoji: 🔒🔓, Chinesisch: 你好"
        plaintext = unicode_text.encode("utf-8")

        ciphertext, nonce = encryptor.encrypt_bytes(plaintext)
        decrypted = encryptor.decrypt_bytes(ciphertext, nonce)

        assert decrypted == plaintext
        assert decrypted.decode("utf-8") == unicode_text

    def test_tampered_ciphertext_fails(self, encryptor):
        """Test: Manipulierte Ciphertext-Daten werden erkannt"""
        plaintext = b"Important data"
        ciphertext, nonce = encryptor.encrypt_bytes(plaintext)

        # Manipuliere Ciphertext (flippe ein Bit)
        tampered = bytearray(ciphertext)
        tampered[0] ^= 0x01
        tampered_ciphertext = bytes(tampered)

        # Entschlüsselung sollte fehlschlagen (Authentication Tag ungültig)
        with pytest.raises(InvalidTag):
            encryptor.decrypt_bytes(tampered_ciphertext, nonce)

    def test_multiple_files_with_same_nonce(self, encryptor, tmp_path):
        """Test: Mehrere Dateien mit explizitem Nonce"""
        nonce = secrets.token_bytes(Encryptor.NONCE_SIZE)

        file1 = tmp_path / "file1.txt"
        file1.write_text("File 1 content")

        file2 = tmp_path / "file2.txt"
        file2.write_text("File 2 content")

        enc1 = tmp_path / "file1.enc"
        enc2 = tmp_path / "file2.enc"

        # Verschlüsseln mit gleichem Nonce (NICHT empfohlen in Produktion!)
        returned_nonce1 = encryptor.encrypt_file(file1, enc1, nonce=nonce)
        returned_nonce2 = encryptor.encrypt_file(file2, enc2, nonce=nonce)

        assert returned_nonce1 == nonce
        assert returned_nonce2 == nonce
