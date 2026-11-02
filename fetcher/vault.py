"""Versleutelt de volledige artikelteksten met jouw wachtwoord.

De app staat op een openbare website. Volledige artikels van andere media mogen we daar niet zomaar
voor iedereen leesbaar neerzetten, dus enkel wie het wachtwoord kent (jij) kan ze openen.
De app ontsleutelt ze in je browser (AES-GCM, sleutel afgeleid met PBKDF2).

Het wachtwoord komt uit de omgevingsvariabele FEEDME_KEY (op GitHub: een "secret")
of uit het bestand "Feed Me wachtwoord.txt" naast de .bat (enkel op je eigen pc, nooit online gezet).
"""
import gzip
import json
import os
import secrets
from pathlib import Path

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives import hashes
    AVAILABLE = True
except ImportError:
    AVAILABLE = False

PASSWORD_FILE = Path(__file__).resolve().parent.parent / "Feed Me wachtwoord.txt"
ITERATIONS = 150_000  # moet gelijk zijn aan app.js
MAGIC = b"FM1"


def password():
    key = os.environ.get("FEEDME_KEY", "").strip()
    if not key and PASSWORD_FILE.exists():
        key = PASSWORD_FILE.read_text("utf-8").strip().splitlines()[0].strip()
    return key or None


def seal(obj, out_file):
    """Schrijf obj als versleuteld bestand: MAGIC | salt(16) | iv(12) | AES-GCM(gzip(json))."""
    pw = password()
    if not (AVAILABLE and pw):
        return False
    salt, iv = secrets.token_bytes(16), secrets.token_bytes(12)
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=ITERATIONS)
    key = kdf.derive(pw.encode("utf-8"))
    plain = gzip.compress(json.dumps(obj, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
    out_file.write_bytes(MAGIC + salt + iv + AESGCM(key).encrypt(iv, plain, None))
    return True
