"""
Fernet-based symmetric encryption for API keys at rest.

Uses FERNET_KEY env var (32-byte URL-safe base64 key).
Generate one with:
    python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
"""

import os
from functools import lru_cache

from cryptography.fernet import Fernet


@lru_cache(maxsize=1)
def get_fernet() -> Fernet:
    """Return a cached Fernet instance seeded from the FERNET_KEY env var."""
    key = os.getenv("FERNET_KEY")
    if not key:
        raise RuntimeError(
            "FERNET_KEY environment variable is not set. "
            "Generate one with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
        )
    return Fernet(key.encode())


def encrypt_api_key(plaintext: str) -> str:
    """Encrypt a plaintext API key → base64 ciphertext string."""
    return get_fernet().encrypt(plaintext.encode()).decode()


def decrypt_api_key(ciphertext: str) -> str:
    """Decrypt a stored ciphertext → plaintext API key string."""
    return get_fernet().decrypt(ciphertext.encode()).decode()
