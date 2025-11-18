"""Scheduled Lambda handler for purging expired links."""
from __future__ import annotations

import logging
import time
from typing import Any, Dict

from models.links_repository import LinksRepository
from utils.config import load_config
from utils.responders import configure_logger

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
    now = int(time.time())
    repo = get_repository()
    removed = repo.purge_expired(now)
    LOGGER.info("cleanup_completed", extra={"requestId": request_id, "removed": removed})
    return {"removed": removed}
