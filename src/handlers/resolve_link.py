"""Lambda handler for redirecting short links."""
from __future__ import annotations

import logging
import time
from typing import Any, Dict

from models.links_repository import LinksRepository
from utils.config import load_config
from utils.responders import configure_logger, error, redirect

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
    request_id = getattr(context, "aws_request_id", "unknown")
    code = (event.get("pathParameters") or {}).get("code")
    if not code:
        return error(400, "MISSING_CODE", "Short code path parameter is required")

    repo = get_repository()

    record = repo.get_link(code)
    if not record:
        return error(404, "NOT_FOUND", "Short link does not exist")

    now = int(time.time())
    if record.get("expiresAt") and record["expiresAt"] < now:
        LOGGER.info("link_expired", extra={"code": code, "requestId": request_id})
        return error(410, "LINK_EXPIRED", "This link has expired")

    updated = repo.increment_clicks(code)
    if not updated:
        return error(404, "NOT_FOUND", "Short link no longer exists")

    repo.save_click(updated)
    LOGGER.info("redirecting", extra={"code": code, "destination": updated["destination"]})
    return redirect(updated["destination"], cache_seconds=60)
