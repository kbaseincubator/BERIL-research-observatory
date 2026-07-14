"""Symmetric encryption helpers for secrets stored at rest.

Primarily used to encrypt OpenViking user credentials before persisting
them in the database. The Fernet key comes from ``settings.ov_credential_key``
(a urlsafe-base64-encoded 32-byte key, e.g. ``Fernet.generate_key()``).

The Fernet instance is built lazily on each call rather than cached so that a
settings reset in tests (``app.config._settings = None``) takes effect without
a process restart.
"""

from cryptography.fernet import Fernet, InvalidToken

class CredentialEncryptionError(RuntimeError):
    """Raised when secrets cannot be encrypted or decrypted.

    Covers a missing/invalid encryption key and corrupt ciphertext.
    """


def _fernet(key: str) -> Fernet:
    if not key:
        raise CredentialEncryptionError(
            "Encryption key is not provided — cannot encrypt/decrypt. "
            "Generate a key with Fernet.generate_key()."
        )
    try:
        return Fernet(key.encode() if isinstance(key, str) else key)
    except (ValueError, TypeError) as exc:
        raise CredentialEncryptionError(
            "Given key is not a valid Fernet key "
            "(expected urlsafe-base64-encoded 32 bytes)."
        ) from exc


def encrypt_secret(plaintext: str, key: str) -> str:
    """Encrypt a secret and return a urlsafe Fernet token (str)."""
    return _fernet(key).encrypt(plaintext.encode()).decode()


def decrypt_secret(token: str, key: str) -> str:
    """Decrypt a Fernet token produced by :func:`encrypt_secret`."""
    try:
        return _fernet(key).decrypt(token.encode()).decode()
    except InvalidToken as exc:
        raise CredentialEncryptionError(
            "Stored credential could not be decrypted — the ciphertext is corrupt "
            "or the encryption key has changed."
        ) from exc
