"""Minimal structured JSON logging — no external dependencies."""

from __future__ import annotations

import json
import logging
import sys


class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "context"):
            payload.update(record.context)  # type: ignore[attr-defined]
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload)


def configure_logging(level: int = logging.INFO) -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(_JsonFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level)


_logger = logging.getLogger("neuracore")


def _emit(level: int, event: str, **context) -> None:
    _logger.log(level, event, extra={"context": context})


def info(event: str, **context) -> None:
    _emit(logging.INFO, event, **context)


def warning(event: str, **context) -> None:
    _emit(logging.WARNING, event, **context)


def error(event: str, **context) -> None:
    _emit(logging.ERROR, event, **context)
