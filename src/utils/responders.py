"""HTTP response helpers with structured logging."""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger("auroralink")
_RESERVED = {
    "name",
    "msg",
    "args",
    "levelname",
    "levelno",
    "pathname",
    "filename",
    "module",
    "exc_info",
    "exc_text",
    "stack_info",
    "lineno",
    "funcName",
    "created",
    "msecs",
    "relativeCreated",
    "thread",
    "threadName",
    "processName",
    "process",
    "message",
}


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: Dict[str, Any] = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        context = {
            key: value
            for key, value in record.__dict__.items()
            if key not in _RESERVED and not key.startswith("_")
        }
        if context:
            payload["context"] = context
        return json.dumps(payload, default=str)


def configure_logger(level: str = "INFO") -> None:
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    if logger.handlers:
        return
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)


def _build_body(payload: Dict[str, Any]) -> str:
    return json.dumps(payload, separators=(",", ":"))


def success(status_code: int, body: Dict[str, Any], headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    response_headers = {"Content-Type": "application/json"}
    if headers:
        response_headers.update(headers)
    return {
        "statusCode": status_code,
        "headers": response_headers,
        "body": _build_body(body),
    }


def error(status_code: int, code: str, message: str, details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    payload: Dict[str, Any] = {"error": {"code": code, "message": message}}
    if details:
        payload["error"]["details"] = details
    logger.warning("error_response", extra={"code": code, "message": message, "details": details})
    return success(status_code, payload)


def redirect(location: str, cache_seconds: int | None = None) -> Dict[str, Any]:
    headers = {"Location": location}
    if cache_seconds is not None:
        headers["Cache-Control"] = f"max-age={cache_seconds}"
    return {
        "statusCode": 302,
        "headers": headers,
        "body": "",
    }
