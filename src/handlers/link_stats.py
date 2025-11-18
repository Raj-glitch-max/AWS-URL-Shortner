"""Lambda handler for returning link analytics."""
from __future__ import annotations

import logging
from typing import Any, Dict

from models.links_repository import LinksRepository
from utils.config import load_config
from utils.responders import configure_logger, error, success

CONFIG = load_config()
configure_logger(CONFIG.log_level)
LOGGER = logging.getLogger("auroralink")
REPOSITORY: LinksRepository | None = None


def get_repository() -> LinksRepository:
    global REPOSITORY
    if REPOSITORY is None:
        REPOSITORY = LinksRepository(CONFIG)
    return REPOSITORY


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    code = (event.get("pathParameters") or {}).get("code")
    if not code:
        return error(400, "MISSING_CODE", "Short code path parameter is required")

    repo = get_repository()
    item = repo.get_stats(code)
    if not item:
        return error(404, "NOT_FOUND", "Short link does not exist")

    body = {
        "code": item["code"],
        "destination": item["destination"],
        "clicks": item.get("clicks", 0),
        "createdAt": item.get("createdAt"),
        "expiresAt": item.get("expiresAt"),
    }
    LOGGER.info("stats_reported", extra={"code": code, "clicks": body["clicks"]})
    return success(200, body)
