"""Input validation helpers."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

from .config import AppConfig

_URL_REGEX = re.compile(r"^(https?://)[^\s]+$", re.IGNORECASE)
_ALIAS_REGEX = re.compile(r"^[A-Za-z0-9_-]+$")


@dataclass
class ValidationResult:
    is_valid: bool
    message: Optional[str] = None


def validate_url(url: Optional[str], config: AppConfig) -> ValidationResult:
    if not url:
        return ValidationResult(False, "Destination URL is required")
    if len(url) > config.max_url_length:
        return ValidationResult(False, "URL exceeds maximum length")
    if not _URL_REGEX.match(url.strip()):
        return ValidationResult(False, "URL must start with http:// or https://")
    return ValidationResult(True)


def validate_alias(alias: Optional[str], config: AppConfig) -> ValidationResult:
    if alias is None:
        return ValidationResult(True)
    if not config.allow_custom_alias:
        return ValidationResult(False, "Custom aliases are disabled")
    if len(alias) > config.max_alias_length:
        return ValidationResult(False, "Alias exceeds maximum length")
    if not _ALIAS_REGEX.match(alias):
        return ValidationResult(False, "Alias can contain alphanumeric, '_' or '-' characters")
    return ValidationResult(True)


def validate_ttl(seconds: Optional[int], config: AppConfig) -> ValidationResult:
    if seconds is None:
        return ValidationResult(True)
    if seconds <= 0:
        return ValidationResult(False, "TTL must be positive")
    if seconds > config.max_ttl_seconds:
        return ValidationResult(False, "TTL exceeds maximum allowed duration")
    return ValidationResult(True)
