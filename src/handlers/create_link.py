"""Lambda handler for creating short links."""
from __future__ import annotations

import json
import logging
from typing import Any, Dict

from models.links_repository import LinksRepository
from utils.config import load_config
from utils.responders import configure_logger, error, success
from utils.shortener import encode_base62, normalize_alias, random_suffix
from utils.validators import validate_alias, validate_ttl, validate_url

CONFIG = load_config()
configure_logger(CONFIG.log_level)
LOGGER = logging.getLogger("auroralink")
REPOSITORY: LinksRepository | None = None


def get_repository() -> LinksRepository:
    global REPOSITORY
    if REPOSITORY is None:
        REPOSITORY = LinksRepository(CONFIG)
    return REPOSITORY


def _parse_body(event: Dict[str, Any]) -> Dict[str, Any]:
    try:
        raw_body = event.get("body") or "{}"
        return json.loads(raw_body)
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON body")


def _generate_code(alias: str | None, repo: LinksRepository) -> str:
    if alias:
        return alias
    counter_value = repo.next_counter()
    return f"{encode_base62(counter_value)}{random_suffix(2)}"


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    request_id = getattr(context, "aws_request_id", "unknown")
    LOGGER.info("create_link_invoked", extra={"requestId": request_id})

    try:
        body = _parse_body(event)
    except ValueError as exc:
        return error(400, "INVALID_PAYLOAD", str(exc))

    destination = (body.get("destination") or "").strip()
    ttl_seconds = body.get("ttlSeconds")
    owner = body.get("owner") or "anonymous"
    alias = normalize_alias(body.get("alias"))

    url_result = validate_url(destination, CONFIG)
    if not url_result.is_valid:
        return error(400, "INVALID_URL", url_result.message or "Invalid URL")

    alias_result = validate_alias(alias, CONFIG)
    if not alias_result.is_valid:
        return error(400, "INVALID_ALIAS", alias_result.message or "Invalid alias")

    ttl_result = validate_ttl(ttl_seconds, CONFIG)
    if not ttl_result.is_valid:
        return error(400, "INVALID_TTL", ttl_result.message or "Invalid TTL")

    ttl_value = ttl_seconds or CONFIG.default_ttl_seconds

    repo = get_repository()

    try:
        code = _generate_code(alias, repo)
        record = repo.create_link(
            code=code,
            destination=destination,
            owner=owner,
            ttl_seconds=ttl_value,
        )
    except ValueError as exc:
        return error(409, "ALIAS_CONFLICT", str(exc))
    except Exception as exc:  # pragma: no cover - logged for ops
        LOGGER.exception("create_link_failed", extra={"requestId": request_id})
        return error(500, "CREATE_FAILED", "Unable to create short link", {"detail": str(exc)})

    short_url = f"{CONFIG.short_domain.rstrip('/')}/{record['code']}"
    LOGGER.info("create_link_succeeded", extra={"code": record["code"], "owner": owner})
    return success(
        201,
        {
            "code": record["code"],
            "destination": record["destination"],
            "expiresAt": record["expiresAt"],
            "shortUrl": short_url,
        },
    )
