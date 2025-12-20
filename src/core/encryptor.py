"""
Encryptor für Scrat-Backup
AES-256-GCM Verschlüsselung mit PBKDF2 Key-Derivation
"""

import logging
import secrets
from pathlib import Path
from typing import BinaryIO, Optional, Tuple

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)


class Encryptor:
    """
    Verschlüsselt und entschlüsselt Daten mit AES-256-GCM

    Verantwortlichkeiten:
    - Master-Key-Ableitung aus Passwort (PBKDF2)
    - AES-256-GCM Verschlüsselung/Entschlüsselung
    - Streaming-Unterstützung für große Dateien
    - Metadaten-Verwaltung (Salt, Nonce)
    """

    # Konstanten
    SALT_SIZE = 32  # 256 bits
    NONCE_SIZE = 12  # 96 bits (GCM-Standard)
    KEY_SIZE = 32  # 256 bits
    PBKDF2_ITERATIONS = 100_000  # 100.000 Iterationen
    CHUNK_SIZE = 8 * 1024 * 1024  # 8 MB Chunks für Streaming

    def __init__(self, password: str, salt: Optional[bytes] = None):
        """
        Initialisiert Encryptor

        Args:
            password: Master-Passwort
            salt: Optional Salt (wenn None: neuer Salt wird generiert)
        """
        self.password = password

        # Salt generieren oder verwenden
        if salt is None:
            self.salt = secrets.token_bytes(self.SALT_SIZE)
            logger.debug("Neuer Salt generiert")
        else:
            if len(salt) != self.SALT_SIZE:
                raise ValueError(f"Salt muss {self.SALT_SIZE} Bytes lang sein")
            self.salt = salt
            logger.debug("Existierender Salt verwendet")

        # Master-Key ableiten
        self.key = self._derive_key(password, self.salt)
        logger.info("Encryption-Key abgeleitet (PBKDF2)")

    def _derive_key(self, password: str, salt: bytes) -> bytes:
        """
        Leitet Encryption-Key aus Passwort ab (PBKDF2-HMAC-SHA256)

        Args:
            password: Master-Passwort
            salt: Salt für Key-Derivation

        Returns:
            32-Byte Encryption-Key
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=self.KEY_SIZE,
            salt=salt,
            iterations=self.PBKDF2_ITERATIONS,
        )

        key = kdf.derive(password.encode("utf-8"))
        return key

    def get_key_hash(self) -> str:
        """
        Gibt Hash des Keys zurück (für Metadata-Speicherung)

        Returns:
            Hex-String des Key-Hashes
        """
        import hashlib

        return hashlib.sha256(self.key).hexdigest()

    def encrypt_bytes(self, plaintext: bytes, nonce: Optional[bytes] = None) -> Tuple[bytes, bytes]:
        """
        Verschlüsselt Bytes (für kleine Daten)

        Args:
            plaintext: Zu verschlüsselnde Daten
            nonce: Optional Nonce (wenn None: wird generiert)

        Returns:
            Tuple (ciphertext, nonce)
        """
        # Nonce generieren oder verwenden
        if nonce is None:
            nonce = secrets.token_bytes(self.NONCE_SIZE)
        elif len(nonce) != self.NONCE_SIZE:
            raise ValueError(f"Nonce muss {self.NONCE_SIZE} Bytes lang sein")

        # Verschlüsseln mit AES-256-GCM
        aesgcm = AESGCM(self.key)
        ciphertext = aesgcm.encrypt(nonce, plaintext, None)

        logger.debug(f"Verschlüsselt: {len(plaintext)} Bytes → {len(ciphertext)} Bytes")
        return ciphertext, nonce

    def decrypt_bytes(self, ciphertext: bytes, nonce: bytes) -> bytes:
        """
        Entschlüsselt Bytes (für kleine Daten)

        Args:
            ciphertext: Verschlüsselte Daten
            nonce: Nonce der Verschlüsselung

        Returns:
            Entschlüsselte Daten

        Raises:
            cryptography.exceptions.InvalidTag: Bei falscher Authentifizierung
        """
        if len(nonce) != self.NONCE_SIZE:
            raise ValueError(f"Nonce muss {self.NONCE_SIZE} Bytes lang sein")

        # Entschlüsseln mit AES-256-GCM
        aesgcm = AESGCM(self.key)
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)

        logger.debug(f"Entschlüsselt: {len(ciphertext)} Bytes → {len(plaintext)} Bytes")
        return plaintext

    def encrypt_file(
        self, input_path: Path, output_path: Path, nonce: Optional[bytes] = None
    ) -> bytes:
        """
        Verschlüsselt Datei (Streaming für große Dateien)

        Args:
            input_path: Quell-Datei
            output_path: Ziel-Datei (verschlüsselt)
            nonce: Optional Nonce (wenn None: wird generiert)

        Returns:
            Verwendeter Nonce

        Raises:
            FileNotFoundError: Wenn Quell-Datei nicht existiert
        """
        if not input_path.exists():
            raise FileNotFoundError(f"Quell-Datei nicht gefunden: {input_path}")

        # Nonce generieren oder verwenden
        if nonce is None:
            nonce = secrets.token_bytes(self.NONCE_SIZE)

        # Sicherstellen, dass Output-Verzeichnis existiert
        output_path.parent.mkdir(parents=True, exist_ok=True)

        file_size = input_path.stat().st_size
        logger.info(f"Verschlüssle Datei: {input_path.name} ({file_size:,} Bytes)")

        # Verschlüsseln
        with open(input_path, "rb") as f_in, open(output_path, "wb") as f_out:
            # Für Streaming müssen wir die gesamte Datei auf einmal verschlüsseln
            # (GCM-Mode funktioniert nicht gut mit Chunking wegen Authentication Tag)
            plaintext = f_in.read()
            ciphertext, used_nonce = self.encrypt_bytes(plaintext, nonce=nonce)

            # Schreibe Nonce am Anfang der Datei (Standard-Praxis für AES-GCM)
            f_out.write(used_nonce)
            f_out.write(ciphertext)

        logger.info(
            f"Datei verschlüsselt: {output_path.name} "
            f"({len(used_nonce) + len(ciphertext):,} Bytes, inkl. {len(used_nonce)} Byte Nonce)"
        )
        return used_nonce

    def decrypt_file(self, input_path: Path, output_path: Path) -> None:
        """
        Entschlüsselt Datei (Nonce wird aus Datei gelesen)

        Args:
            input_path: Verschlüsselte Datei (mit eingebettetem Nonce)
            output_path: Ziel-Datei (entschlüsselt)

        Raises:
            FileNotFoundError: Wenn verschlüsselte Datei nicht existiert
            ValueError: Wenn Datei zu klein ist oder ungültiges Format hat
            cryptography.exceptions.InvalidTag: Bei falscher Authentifizierung
        """
        if not input_path.exists():
            raise FileNotFoundError(f"Verschlüsselte Datei nicht gefunden: {input_path}")

        # Sicherstellen, dass Output-Verzeichnis existiert
        output_path.parent.mkdir(parents=True, exist_ok=True)

        file_size = input_path.stat().st_size
        logger.info(f"Entschlüssle Datei: {input_path.name} ({file_size:,} Bytes)")

        # Datei muss mindestens Nonce-Größe + Authentication-Tag haben
        min_size = self.NONCE_SIZE + 16  # GCM Tag ist 16 Bytes
        if file_size < min_size:
            raise ValueError(
                f"Verschlüsselte Datei zu klein ({file_size} Bytes, "
                f"erwartet mindestens {min_size} Bytes)"
            )

        # Entschlüsseln
        with open(input_path, "rb") as f_in, open(output_path, "wb") as f_out:
            # Lese Nonce vom Anfang der Datei (Standard-Praxis für AES-GCM)
            nonce = f_in.read(self.NONCE_SIZE)
            if len(nonce) != self.NONCE_SIZE:
                raise ValueError(
                    f"Konnte Nonce nicht lesen (erwartet {self.NONCE_SIZE} Bytes, "
                    f"bekommen {len(nonce)} Bytes)"
                )

            # Lese Rest als Ciphertext
            ciphertext = f_in.read()
            plaintext = self.decrypt_bytes(ciphertext, nonce)
            f_out.write(plaintext)

        logger.info(f"Datei entschlüsselt: {output_path.name} ({len(plaintext):,} Bytes)")

    def encrypt_stream(
        self, input_stream: BinaryIO, output_stream: BinaryIO, nonce: Optional[bytes] = None
    ) -> bytes:
        """
        Verschlüsselt Stream (für große Dateien ohne Temp-Dateien)

        Args:
            input_stream: Input-Stream (lesbar)
            output_stream: Output-Stream (schreibbar)
            nonce: Optional Nonce (wenn None: wird generiert)

        Returns:
            Verwendeter Nonce
        """
        # Kompletten Stream lesen und verschlüsseln
        # (GCM benötigt komplette Daten für Authentication Tag)
        plaintext = input_stream.read()
        ciphertext, used_nonce = self.encrypt_bytes(plaintext, nonce=nonce)
        output_stream.write(ciphertext)

        logger.debug(f"Stream verschlüsselt: {len(plaintext):,} Bytes")
        return used_nonce

    def decrypt_stream(self, input_stream: BinaryIO, output_stream: BinaryIO, nonce: bytes) -> None:
        """
        Entschlüsselt Stream (für große Dateien ohne Temp-Dateien)

        Args:
            input_stream: Input-Stream (lesbar, verschlüsselt)
            output_stream: Output-Stream (schreibbar, entschlüsselt)
            nonce: Nonce der Verschlüsselung
        """
        # Kompletten Stream lesen und entschlüsseln
        ciphertext = input_stream.read()
        plaintext = self.decrypt_bytes(ciphertext, nonce)
        output_stream.write(plaintext)

        logger.debug(f"Stream entschlüsselt: {len(ciphertext):,} Bytes")

    @staticmethod
    def generate_password(length: int = 32) -> str:
        """
        Generiert sicheres zufälliges Passwort

        Args:
            length: Länge des Passworts

        Returns:
            Zufälliges Passwort (base64-kodiert)
        """
        import base64

        random_bytes = secrets.token_bytes(length)
        password = base64.b64encode(random_bytes).decode("ascii")

        logger.info(f"Zufälliges Passwort generiert ({length} Bytes)")
        return password

    @staticmethod
    def validate_password_strength(password: str) -> Tuple[bool, str]:
        """
        Validiert Passwort-Stärke

        Args:
            password: Zu validierendes Passwort

        Returns:
            Tuple (ist_sicher, fehlermeldung)
        """
        min_length = 12

        if len(password) < min_length:
            return False, f"Passwort muss mindestens {min_length} Zeichen lang sein"

        # Empfehlung: Mindestens Mix aus Zeichen-Typen
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(not c.isalnum() for c in password)

        if not (has_upper and has_lower and has_digit):
            return (
                False,
                "Passwort sollte Groß-, Kleinbuchstaben und Ziffern enthalten",
            )

        if not has_special:
            logger.warning("Passwort enthält keine Sonderzeichen (empfohlen)")

        return True, "Passwort ist sicher"

    def __repr__(self) -> str:
        """String-Repräsentation"""
        return f"Encryptor(key_hash={self.get_key_hash()[:16]}...)"
