import base64
import os

from config import config
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def _get_key() -> bytes:
    # Expect base64-encoded 32-byte key
    b64 = config.TOKEN_ENC_KEY
    if not b64:
        raise RuntimeError("Encryption key not configured")
    return base64.b64decode(b64)


def encrypt_token(plaintext: str, version: str | None = None) -> str:
    """Encrypt the given plaintext token and return as a versioned base64 string.

    Args:
        plaintext (str): The token to encrypt.
        version (str | None): Optional version string to prefix. Defaults to config value or 'v1'.

    Returns:
        str: The encrypted token in format "vX$<base64>".
    """
    key = _get_key()
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ct = aesgcm.encrypt(nonce, plaintext.encode(), None)
    blob = nonce + ct
    b64 = base64.b64encode(blob).decode()
    ver = version or getattr(config, 'TOKEN_KEY_VERSION', 'v1')
    return f"{ver}${b64}"


def decrypt_token(blob: str) -> str:
    """Decrypt the given versioned base64 string token and return the plaintext.

    Args:
        blob (str): The encrypted token in format "vX$<base64>".

    Returns:
        str: The decrypted plaintext token.
    """
    # Expect format "v1$<base64>"
    try:
        ver, b64 = blob.split('$', 1)
    except ValueError as e:
        raise ValueError("Invalid token format") from e
    data = base64.b64decode(b64)
    nonce, ct = data[:12], data[12:]
    aesgcm = AESGCM(_get_key())
    pt = aesgcm.decrypt(nonce, ct, None)
    return pt.decode()
