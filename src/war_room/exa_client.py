"""Exa search wrapper with retry, budget guard, and normalized output.

All network calls in the war room go through this single wrapper.
It supports both older and newer exa-py APIs for `contents` options.
"""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any

from exa_py import Exa

from war_room.bootstrap import discover_repo_root
from war_room.settings import load_settings


class BudgetExhausted(Exception):
    """Raised when the search budget is exhausted."""


class ExaClient:
    """Thin wrapper around exa-py with retry + budget guard."""

    provider_name = "exa"

    def __init__(
        self,
        api_key: str | None = None,
        max_search_calls: int = 30,
    ):
        self._api_key = api_key or os.getenv("EXA_API_KEY", "") or _load_api_key_from_settings()
        if not self._api_key:
            raise ValueError("EXA_API_KEY is required (pass it or set in env)")
        self._exa = Exa(self._api_key)
        self.max_search_calls = max_search_calls
        self.search_count = 0

    def search(
        self,
        query: str,
        *,
        k: int = 5,
        recency_days: int | None = None,
        include_domains: list[str] | None = None,
        exclude_domains: list[str] | None = None,
        max_chars: int = 3000,
    ) -> list[dict[str, Any]]:
        """Run a single Exa search and return normalized result dicts.

        Raises BudgetExhausted if max_search_calls reached.
        """
        if self.search_count >= self.max_search_calls:
            raise BudgetExhausted(
                f"Search budget exhausted: {self.search_count}/{self.max_search_calls} calls used"
            )

        kwargs: dict[str, Any] = {
            "num_results": k,
            "contents": _build_contents_options(max_chars),
        }
        # Exa only allows one of include_domains or exclude_domains
        if include_domains:
            kwargs["include_domains"] = include_domains
        elif exclude_domains:
            kwargs["exclude_domains"] = exclude_domains
        if recency_days is not None:
            from datetime import UTC, datetime, timedelta
            start = (datetime.now(UTC) - timedelta(days=recency_days)).strftime("%Y-%m-%d")
            kwargs["start_published_date"] = start

        response = self._search_with_retry(query, kwargs)
        self.search_count += 1
        return [self._normalize_result(r) for r in response.results]

    def get_contents(
        self,
        urls: list[str],
        *,
        max_chars: int = 6000,
    ) -> list[dict[str, Any]]:
        """Fetch full contents for a list of URLs."""
        if not urls:
            return []
        try:
            response = self._exa.get_contents(
                urls,
                text={"max_characters": max_chars},
            )
            return [self._normalize_result(r) for r in response.results]
        except Exception:
            return []

    def _search_with_retry(
        self, query: str, kwargs: dict, max_retries: int = 3
    ) -> Any:
        """Simple retry with exponential backoff."""
        for attempt in range(max_retries):
            try:
                return self._exa.search(query, **kwargs)
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                wait = 2 ** attempt
                time.sleep(wait)

    @staticmethod
    def _normalize_result(result: Any) -> dict[str, Any]:
        """Normalize an exa-py Result object to a plain dict."""
        return {
            "title": getattr(result, "title", None) or "",
            "url": getattr(result, "url", "") or "",
            "published_date": getattr(result, "published_date", None) or "",
            "snippet": (getattr(result, "text", "") or "")[:500],
            "text": getattr(result, "text", "") or "",
            "score": getattr(result, "score", None),
        }

    @property
    def budget_remaining(self) -> int:
        return max(0, self.max_search_calls - self.search_count)


def _build_contents_options(max_chars: int) -> dict[str, Any]:
    """Build a version-safe contents options payload for exa-py.

    Older exa-py versions expose `ContentsOptions` in `exa_py.api`.
    Newer versions accept a plain dict and do not export that symbol.
    """
    try:
        from exa_py.api import ContentsOptions  # type: ignore

        return ContentsOptions(text={"max_characters": max_chars})
    except Exception:
        return {"text": {"max_characters": max_chars}}


def _load_api_key_from_settings() -> str:
    """Attempt to resolve the API key from the shared settings loader."""
    try:
        repo_root = discover_repo_root(Path.cwd())
        settings = load_settings(repo_root=repo_root)
        return settings.exa_api_key_value
    except Exception:
        return ""
