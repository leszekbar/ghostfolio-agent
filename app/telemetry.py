import json
import logging
import re
from datetime import datetime, timezone
from typing import Any


DEFAULT_REDACT_FIELDS = {
    "authorization",
    "access_token",
    "ghostfolio_token",
    "authtoken",
    "token",
}

BEARER_PATTERN = re.compile(r"Bearer\s+[A-Za-z0-9._\-]+", re.IGNORECASE)


def _normalize_redact_fields(raw_fields: str | None) -> set[str]:
    if not raw_fields:
        return set(DEFAULT_REDACT_FIELDS)
    items = {item.strip().lower() for item in raw_fields.split(",") if item.strip()}
    return items or set(DEFAULT_REDACT_FIELDS)


def redact_sensitive_value(value: Any, field_name: str | None, redact_fields: set[str]) -> Any:
    if field_name and field_name.lower() in redact_fields:
        return "[REDACTED]"

    if isinstance(value, str):
        return BEARER_PATTERN.sub("Bearer [REDACTED]", value)

    if isinstance(value, dict):
        return {
            key: redact_sensitive_value(val, key, redact_fields)
            for key, val in value.items()
        }

    if isinstance(value, list):
        return [redact_sensitive_value(item, None, redact_fields) for item in value]

    return value


class RedactionFilter(logging.Filter):
    def __init__(self, redact_fields: set[str]) -> None:
        super().__init__()
        self.redact_fields = redact_fields

    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = redact_sensitive_value(record.msg, None, self.redact_fields)
        if isinstance(record.args, tuple):
            record.args = tuple(
                redact_sensitive_value(arg, None, self.redact_fields) for arg in record.args
            )
        elif isinstance(record.args, dict):
            record.args = {
                k: redact_sensitive_value(v, k, self.redact_fields)
                for k, v in record.args.items()
            }

        for key, value in list(record.__dict__.items()):
            if key.startswith("_"):
                continue
            record.__dict__[key] = redact_sensitive_value(value, key, self.redact_fields)
        return True


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        for key, value in record.__dict__.items():
            if key in {
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
            }:
                continue
            payload[key] = value

        return json.dumps(payload, default=str)


def configure_logging(
    *,
    level: str = "INFO",
    log_format: str = "json",
    include_stack: bool = False,
    redact_fields_raw: str | None = None,
) -> None:
    redact_fields = _normalize_redact_fields(redact_fields_raw)
    root = logging.getLogger()
    root.handlers = []
    root.setLevel(level.upper())

    handler = logging.StreamHandler()
    handler.addFilter(RedactionFilter(redact_fields))
    if log_format.lower() == "json":
        handler.setFormatter(JsonFormatter())
    else:
        pattern = "%(asctime)s %(levelname)s %(name)s: %(message)s"
        if include_stack:
            pattern += " | %(pathname)s:%(lineno)d"
        handler.setFormatter(logging.Formatter(pattern))
    root.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
