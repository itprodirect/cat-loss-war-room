"""Retrieval provider contracts and task-bound helper functions."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from war_room.models import QuerySpec, RetrievalTask


class RetrievalProvider(Protocol):
    """Minimal provider interface for retrieval adapters."""

    provider_name: str

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
        """Run a provider search and return normalized hits."""

    def get_contents(
        self,
        urls: list[str],
        *,
        max_chars: int = 6000,
    ) -> list[dict[str, Any]]:
        """Fetch full contents for URLs and return normalized hits."""


@dataclass(slots=True)
class RetrievalSearchRequest:
    """Search request bound to a canonical retrieval task."""

    task: RetrievalTask
    k: int = 5
    recency_days: int | None = None
    include_domains: list[str] = field(default_factory=list)
    exclude_domains: list[str] = field(default_factory=list)
    max_chars: int = 3000


@dataclass(slots=True)
class RetrievalContentsRequest:
    """Content-fetch request optionally bound to a retrieval task."""

    urls: list[str]
    task: RetrievalTask | None = None
    max_chars: int = 6000


def query_spec_to_retrieval_task(
    query_spec: QuerySpec,
    *,
    run_id: str,
    stage_id: str,
    provider: str,
    retrieval_task_id: str | None = None,
    review_required: bool = False,
) -> RetrievalTask:
    """Create a canonical retrieval task from a query-plan row."""

    return RetrievalTask(
        retrieval_task_id=retrieval_task_id or f"{stage_id}:{query_spec.category}",
        run_id=run_id,
        stage_id=stage_id,
        provider=provider,
        query_text=query_spec.query,
        review_required=review_required,
    )


def execute_retrieval_search(
    provider: RetrievalProvider,
    request: RetrievalSearchRequest,
) -> list[dict[str, Any]]:
    """Execute a retrieval task through a provider after contract validation."""

    _validate_provider_match(provider, request.task)
    return provider.search(
        request.task.query_text,
        k=request.k,
        recency_days=request.recency_days,
        include_domains=request.include_domains or None,
        exclude_domains=request.exclude_domains or None,
        max_chars=request.max_chars,
    )


def fetch_retrieval_contents(
    provider: RetrievalProvider,
    request: RetrievalContentsRequest,
) -> list[dict[str, Any]]:
    """Fetch full contents through a provider after contract validation."""

    if request.task is not None:
        _validate_provider_match(provider, request.task)
    return provider.get_contents(request.urls, max_chars=request.max_chars)


def _validate_provider_match(provider: RetrievalProvider, task: RetrievalTask) -> None:
    if task.provider != provider.provider_name:
        raise ValueError(
            f"RetrievalTask provider '{task.provider}' does not match "
            f"adapter '{provider.provider_name}'."
        )
