"""Retrieval provider contracts and task-bound helper functions."""

from __future__ import annotations

import datetime as dt
import re
from dataclasses import dataclass, field
from typing import Any, Protocol

from war_room.models import CaseIntake, QuerySpec, RetrievalTask, RunEvent


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


@dataclass(slots=True)
class RetrievalExecutionResult:
    """Normalized result of executing one retrieval task attempt."""

    task: RetrievalTask
    hits: list[dict[str, Any]]
    run_events: list[RunEvent]
    warning: str | None = None


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


def execute_retrieval_task(
    provider: RetrievalProvider,
    request: RetrievalSearchRequest,
    *,
    now: dt.datetime | None = None,
) -> RetrievalExecutionResult:
    """Execute a retrieval task and emit attempt metadata for notebook-era flows."""

    started_at = now or dt.datetime.now(dt.UTC)
    attempt_count = request.task.attempt_count + 1
    requested_at = request.task.requested_at or started_at
    running_task = request.task.model_copy(
        update={
            "attempt_count": attempt_count,
            "requested_at": requested_at,
            "status": "running",
        }
    )
    run_events = [
        RunEvent(
            run_event_id=f"{request.task.retrieval_task_id}:attempt-{attempt_count}:started",
            run_id=request.task.run_id,
            stage_id=request.task.stage_id,
            event_type="retrieval_started",
            severity="info",
            message=f"{provider.provider_name} retrieval attempt {attempt_count} started.",
            created_at=started_at,
        )
    ]

    try:
        hits = execute_retrieval_search(provider, request)
    except Exception as exc:
        completed_at = now or dt.datetime.now(dt.UTC)
        warning = (
            f"{provider.provider_name} retrieval failed for '{request.task.query_text}': "
            f"{type(exc).__name__}."
        )
        failed_task = running_task.model_copy(
            update={
                "completed_at": completed_at,
                "review_required": True,
                "status": "failed",
            }
        )
        run_events.append(
            RunEvent(
                run_event_id=f"{request.task.retrieval_task_id}:attempt-{attempt_count}:failed",
                run_id=request.task.run_id,
                stage_id=request.task.stage_id,
                event_type="retrieval_failed",
                severity="error",
                message=warning,
                created_at=completed_at,
            )
        )
        return RetrievalExecutionResult(
            task=failed_task,
            hits=[],
            run_events=run_events,
            warning=warning,
        )

    completed_at = now or dt.datetime.now(dt.UTC)
    raw_artifact_refs = _artifact_refs_from_hits(hits)
    if hits:
        final_task = running_task.model_copy(
            update={
                "completed_at": completed_at,
                "status": "completed",
                "raw_artifact_refs": raw_artifact_refs,
            }
        )
        final_event = RunEvent(
            run_event_id=f"{request.task.retrieval_task_id}:attempt-{attempt_count}:completed",
            run_id=request.task.run_id,
            stage_id=request.task.stage_id,
            event_type="retrieval_completed",
            severity="info",
            message=f"{provider.provider_name} returned {len(hits)} hit(s).",
            created_at=completed_at,
            artifact_refs=raw_artifact_refs,
        )
        warning = None
    else:
        warning = f"{provider.provider_name} returned no results for '{request.task.query_text}'."
        final_task = running_task.model_copy(
            update={
                "completed_at": completed_at,
                "review_required": True,
                "status": "degraded",
                "raw_artifact_refs": raw_artifact_refs,
            }
        )
        final_event = RunEvent(
            run_event_id=f"{request.task.retrieval_task_id}:attempt-{attempt_count}:empty",
            run_id=request.task.run_id,
            stage_id=request.task.stage_id,
            event_type="retrieval_empty",
            severity="warning",
            message=warning,
            created_at=completed_at,
            artifact_refs=raw_artifact_refs,
        )
    run_events.append(final_event)
    return RetrievalExecutionResult(
        task=final_task,
        hits=hits,
        run_events=run_events,
        warning=warning,
    )


def fetch_retrieval_contents(
    provider: RetrievalProvider,
    request: RetrievalContentsRequest,
) -> list[dict[str, Any]]:
    """Fetch full contents through a provider after contract validation."""

    if request.task is not None:
        _validate_provider_match(provider, request.task)
    return provider.get_contents(request.urls, max_chars=request.max_chars)


def notebook_run_id_from_intake(intake: CaseIntake) -> str:
    """Derive a deterministic notebook-era run identifier from intake fields."""

    parts = (
        intake.event_name,
        intake.state,
        intake.county,
        intake.carrier,
    )
    slug = "-".join(_slug_token(part) for part in parts if part.strip())
    return f"run-notebook-{slug}"


def _validate_provider_match(provider: RetrievalProvider, task: RetrievalTask) -> None:
    if task.provider != provider.provider_name:
        raise ValueError(
            f"RetrievalTask provider '{task.provider}' does not match "
            f"adapter '{provider.provider_name}'."
        )


def _slug_token(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", value.lower())
    return normalized.strip("-")


def _artifact_refs_from_hits(hits: list[dict[str, Any]]) -> list[str]:
    refs: list[str] = []
    for hit in hits:
        url = (hit.get("url") or "").strip()
        if url and url not in refs:
            refs.append(url)
    return refs
