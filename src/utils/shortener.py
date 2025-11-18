"""Helpers for generating and decoding short codes."""
from __future__ import annotations

import secrets
import string
from typing import Optional

BASE62_ALPHABET = string.digits + string.ascii_letters


def encode_base62(counter: int) -> str:
    """Encode integer counter into a base62 string."""
    if counter <= 0:
        raise ValueError("Counter must be positive")
    base = len(BASE62_ALPHABET)
    result = []
    value = counter
    while value:
        value, idx = divmod(value, base)
        result.append(BASE62_ALPHABET[idx])
    return "".join(reversed(result))


def random_suffix(length: int = 6) -> str:
    """Generate a cryptographically strong random suffix."""
    alphabet = BASE62_ALPHABET
    return "".join(secrets.choice(alphabet) for _ in range(length))


def normalize_alias(alias: Optional[str]) -> Optional[str]:
    if not alias:
        return None
    sanitized = alias.strip()
    return sanitized or None
