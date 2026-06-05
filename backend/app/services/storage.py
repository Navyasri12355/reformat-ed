"""File storage abstraction.

Defaults to the local filesystem (no S3/cloud needed for dev). The interface
mirrors an object store (put/get by key) so it can be swapped for S3 later
without touching callers.
"""

from __future__ import annotations

import uuid
from pathlib import Path

from app.config import settings

_BASE = Path(settings.storage_dir)


def _ensure_base() -> Path:
    _BASE.mkdir(parents=True, exist_ok=True)
    return _BASE


def build_key(file_name: str) -> str:
    """Unique storage key that preserves the original extension."""
    ext = file_name.rsplit(".", 1)[-1].lower() if "." in file_name else "bin"
    return f"{uuid.uuid4().hex}.{ext}"


def put(key: str, data: bytes) -> None:
    base = _ensure_base()
    (base / key).write_bytes(data)


def get(key: str) -> bytes:
    return (_BASE / key).read_bytes()


def delete(key: str) -> None:
    path = _BASE / key
    if path.exists():
        path.unlink()
