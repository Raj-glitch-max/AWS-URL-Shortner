"""Application configuration loader for AuroraLink Forge."""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional


def _get_bool(value: Optional[str], default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y"}


def _get_int(value: Optional[str], default: int) -> int:
    try:
        return int(value) if value is not None else default
    except ValueError:
        return default


@dataclass(frozen=True)
class AppConfig:
    table_name: str
    short_domain: str
    default_ttl_seconds: int
    max_ttl_seconds: int
    allow_custom_alias: bool
    max_alias_length: int
    max_url_length: int
    log_level: str
    cleanup_batch_size: int
    region_name: str


_config: Optional[AppConfig] = None


def load_config() -> AppConfig:
    """Load and cache application configuration from environment variables."""
    global _config
    if _config is not None:
        return _config

    _config = AppConfig(
        table_name=os.getenv("LINKS_TABLE_NAME", "auroralinkforge-links"),
        short_domain=os.getenv("SHORT_DOMAIN", "https://auroralink.io/"),
        default_ttl_seconds=_get_int(os.getenv("DEFAULT_TTL_SECONDS"), 7 * 24 * 3600),
        max_ttl_seconds=_get_int(os.getenv("MAX_TTL_SECONDS"), 365 * 24 * 3600),
        allow_custom_alias=_get_bool(os.getenv("ALLOW_CUSTOM_ALIAS"), True),
        max_alias_length=_get_int(os.getenv("MAX_ALIAS_LENGTH"), 24),
        max_url_length=_get_int(os.getenv("MAX_URL_LENGTH"), 2048),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        cleanup_batch_size=_get_int(os.getenv("CLEANUP_BATCH_SIZE"), 100),
        region_name=os.getenv("AWS_REGION", os.getenv("AWS_DEFAULT_REGION", "us-east-1")),
    )
    return _config
