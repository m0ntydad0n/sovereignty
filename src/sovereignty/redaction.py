from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

SECRET_KEY_PARTS = (
    "api_key",
    "apikey",
    "secret",
    "token",
    "password",
    "credential",
    "authorization",
    "bearer",
)
PRIVATE_KEY_PARTS = ("base_url", "url", "path", "endpoint", "host")
TOKEN_VALUE_RE = re.compile(
    r"(?i)(bearer\s+[a-z0-9._\-]{20,}|gho_[a-z0-9_]{10,}|sk-[a-z0-9_\-]{10,})"
)
PRIVATE_PATH_RE = re.compile(r"(^/Users/|^/home/|^/private/|^~/?|[A-Za-z]:\\)")
LOCAL_URL_RE = re.compile(r"(?i)^https?://(localhost|127\.0\.0\.1|0\.0\.0\.0|[\w.-]+\.local)(:|/|$)")


def redact_model_metadata(metadata: Mapping[str, Any]) -> dict[str, Any]:
    """Return model metadata with secrets and host-local details removed."""
    clean: dict[str, Any] = {}
    for key, value in metadata.items():
        lowered = key.lower()
        if any(part in lowered for part in SECRET_KEY_PARTS):
            continue
        if any(part in lowered for part in PRIVATE_KEY_PARTS):
            if _looks_private(value):
                continue
        if isinstance(value, Mapping):
            nested = redact_model_metadata(value)
            if nested:
                clean[key] = nested
            continue
        if _looks_secret_value(value) or _looks_private(value):
            continue
        clean[key] = value
    return clean


def _looks_secret_value(value: Any) -> bool:
    return isinstance(value, str) and TOKEN_VALUE_RE.search(value) is not None


def _looks_private(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    return PRIVATE_PATH_RE.search(value) is not None or LOCAL_URL_RE.search(value) is not None
