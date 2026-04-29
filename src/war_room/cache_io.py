"""Cache-first data access.

Lookup order: cache_samples/ -> cache/ -> live call -> save to cache/.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Callable, Mapping, Optional

from war_room.models import SCHEMA_VERSION_DEFAULT

CACHE_ENTRY_TYPE = "war_room.cache_entry"
CACHE_ENTRY_TYPE_KEY = "cache_entry_type"
CACHE_PAYLOAD_KEY = "payload"
SUPPORTED_CACHE_SCHEMA_VERSIONS = {SCHEMA_VERSION_DEFAULT}


def normalize_key(raw: str) -> str:
    """Normalize a cache key: lowercase, strip, replace non-alnum with underscores."""
    key = raw.strip().lower()
    key = re.sub(r"[^a-z0-9]+", "_", key)
    key = key.strip("_")
    return key


def _hash_key(key: str) -> str:
    """Short hash for filesystem-safe filenames."""
    return hashlib.sha256(key.encode()).hexdigest()[:16]


def _cache_path(directory: str | Path, key: str) -> Path:
    """Build the JSON file path for a normalized key."""
    return Path(directory) / f"{normalize_key(key)}_{_hash_key(key)}.json"


def cache_get(key: str, cache_dir: str | Path) -> Optional[Any]:
    """Read a cached value, or None if not found."""
    path = _cache_path(cache_dir, key)
    if path.exists():
        return _unwrap_cache_value(json.loads(path.read_text(encoding="utf-8")))
    return None


def cache_set(key: str, value: Any, cache_dir: str | Path) -> Path:
    """Write a value to the cache. Returns the file path."""
    path = _cache_path(cache_dir, key)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(_wrap_cache_value(value), indent=2, default=str),
        encoding="utf-8",
    )
    return path


def cached_call(
    key: str,
    fn: Callable[[], Any],
    *,
    cache_samples_dir: str | Path = "cache_samples",
    cache_dir: str | Path = "cache",
    use_cache: bool = True,
) -> Any:
    """Cache-first call wrapper.

    1. Check cache_samples/ (committed demo fixtures)
    2. Check cache/ (runtime cache)
    3. Call fn(), save result to cache/
    """
    if use_cache:
        # Layer 1: committed samples
        result = cache_get(key, cache_samples_dir)
        if result is not None:
            return result

        # Layer 2: runtime cache
        result = cache_get(key, cache_dir)
        if result is not None:
            return result

    # Layer 3: live call
    result = fn()
    cache_set(key, result, cache_dir)
    return result


def _wrap_cache_value(value: Any) -> dict[str, Any]:
    """Return the current schema-versioned cache envelope for a payload."""
    if _is_cache_envelope(value):
        return dict(value)
    return {
        CACHE_ENTRY_TYPE_KEY: CACHE_ENTRY_TYPE,
        "schema_version": SCHEMA_VERSION_DEFAULT,
        CACHE_PAYLOAD_KEY: value,
    }


def _unwrap_cache_value(raw: Any) -> Any:
    """Read current cache envelopes while preserving legacy raw-cache payloads."""
    if not _is_cache_envelope(raw):
        return raw

    schema_version = str(raw.get("schema_version", "")).strip()
    if schema_version not in SUPPORTED_CACHE_SCHEMA_VERSIONS:
        supported = ", ".join(sorted(SUPPORTED_CACHE_SCHEMA_VERSIONS))
        raise ValueError(
            f"Unsupported cache schema_version '{schema_version}'. "
            f"Supported versions: {supported}."
        )
    return raw[CACHE_PAYLOAD_KEY]


def _is_cache_envelope(value: Any) -> bool:
    return (
        isinstance(value, Mapping)
        and value.get(CACHE_ENTRY_TYPE_KEY) == CACHE_ENTRY_TYPE
        and CACHE_PAYLOAD_KEY in value
    )
