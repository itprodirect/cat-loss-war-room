"""Tests for cache_io module."""

import json
import tempfile
from pathlib import Path

import pytest

from war_room.cache_io import (
    CACHE_ENTRY_TYPE,
    CACHE_ENTRY_TYPE_KEY,
    CACHE_PAYLOAD_KEY,
    cache_get,
    cache_set,
    cached_call,
    normalize_key,
)
from war_room.models import SCHEMA_VERSION_DEFAULT


def test_normalize_key_basic():
    assert normalize_key("Hello World!") == "hello_world"


def test_normalize_key_special_chars():
    assert normalize_key("  NWS Milton FL 2024  ") == "nws_milton_fl_2024"


def test_normalize_key_already_clean():
    assert normalize_key("clean_key") == "clean_key"


def test_cache_roundtrip():
    with tempfile.TemporaryDirectory() as tmpdir:
        data = {"results": [1, 2, 3], "query": "test"}
        cache_set("test_key", data, tmpdir)
        result = cache_get("test_key", tmpdir)
        assert result == data


def test_cache_set_writes_schema_versioned_envelope():
    with tempfile.TemporaryDirectory() as tmpdir:
        data = {"results": [1, 2, 3], "query": "test"}
        path = cache_set("test_key", data, tmpdir)
        raw = json.loads(path.read_text(encoding="utf-8"))

        assert raw[CACHE_ENTRY_TYPE_KEY] == CACHE_ENTRY_TYPE
        assert raw["schema_version"] == SCHEMA_VERSION_DEFAULT
        assert raw[CACHE_PAYLOAD_KEY] == data
        assert cache_get("test_key", tmpdir) == data


def test_cache_get_reads_legacy_unversioned_payload():
    with tempfile.TemporaryDirectory() as tmpdir:
        data = {"source": "legacy-fixture"}
        path = cache_set("legacy_key", {"source": "placeholder"}, tmpdir)
        path.write_text(
            json.dumps(data),
            encoding="utf-8",
        )

        assert cache_get("legacy_key", tmpdir) == data


def test_cache_get_rejects_unsupported_schema_version():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = cache_set("future_key", {"source": "placeholder"}, tmpdir)
        path.write_text(
            json.dumps(
                {
                    CACHE_ENTRY_TYPE_KEY: CACHE_ENTRY_TYPE,
                    "schema_version": "v999",
                    CACHE_PAYLOAD_KEY: {"source": "future"},
                }
            ),
            encoding="utf-8",
        )

        with pytest.raises(ValueError, match="Unsupported cache schema_version"):
            cache_get("future_key", tmpdir)


def test_cache_get_missing():
    with tempfile.TemporaryDirectory() as tmpdir:
        result = cache_get("nonexistent", tmpdir)
        assert result is None


def test_cached_call_uses_cache():
    with tempfile.TemporaryDirectory() as tmpdir:
        call_count = 0

        def expensive_fn():
            nonlocal call_count
            call_count += 1
            return {"value": 42}

        # First call: hits fn
        result1 = cached_call("my_key", expensive_fn, cache_dir=tmpdir, cache_samples_dir=tmpdir)
        assert result1 == {"value": 42}
        assert call_count == 1

        # Second call: hits cache
        result2 = cached_call("my_key", expensive_fn, cache_dir=tmpdir, cache_samples_dir=tmpdir)
        assert result2 == {"value": 42}
        assert call_count == 1  # fn not called again


def test_cached_call_writes_schema_versioned_runtime_cache():
    with tempfile.TemporaryDirectory() as tmpdir:
        result = cached_call(
            "my_key",
            lambda: {"value": 42},
            cache_dir=tmpdir,
            cache_samples_dir=tmpdir,
        )
        cache_files = list(Path(tmpdir).glob("*.json"))
        raw = json.loads(cache_files[0].read_text(encoding="utf-8"))

        assert result == {"value": 42}
        assert len(cache_files) == 1
        assert raw["schema_version"] == SCHEMA_VERSION_DEFAULT
        assert raw[CACHE_PAYLOAD_KEY] == {"value": 42}


def test_cached_call_bypass_cache():
    with tempfile.TemporaryDirectory() as tmpdir:
        call_count = 0

        def fn():
            nonlocal call_count
            call_count += 1
            return {"v": call_count}

        result = cached_call("k", fn, cache_dir=tmpdir, cache_samples_dir=tmpdir, use_cache=False)
        assert result == {"v": 1}

        # Even with use_cache=False, the result was saved to cache
        result2 = cached_call("k", fn, cache_dir=tmpdir, cache_samples_dir=tmpdir, use_cache=True)
        assert result2 == {"v": 1}  # from cache, fn not called again


def test_cached_call_prefers_samples():
    with tempfile.TemporaryDirectory() as samples_dir, tempfile.TemporaryDirectory() as cache_dir:
        # Pre-seed samples
        cache_set("shared_key", {"source": "samples"}, samples_dir)
        cache_set("shared_key", {"source": "cache"}, cache_dir)

        result = cached_call(
            "shared_key",
            lambda: {"source": "live"},
            cache_samples_dir=samples_dir,
            cache_dir=cache_dir,
        )
        assert result["source"] == "samples"
