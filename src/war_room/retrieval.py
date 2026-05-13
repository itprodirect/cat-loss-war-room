"""Retrieval provider contracts and task-bound helper functions."""

from __future__ import annotations

import datetime as dt
import re
from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol

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


class RetrievalContractError(ValueError):
    """Raised when a provider returns a shape outside the project contract."""


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


@dataclass(frozen=True, slots=True)
class RetrievalHitDiagnostics:
    """Provider-result normalization metadata for one retrieval call."""

    hits: list[dict[str, Any]]
    dropped_malformed_count: int = 0
    missing_url_count: int = 0

    @property
    def has_warnings(self) -> bool:
        return self.dropped_malformed_count > 0 or self.missing_url_count > 0


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

    return _execute_retrieval_search_with_diagnostics(provider, request).hits


def _execute_retrieval_search_with_diagnostics(
    provider: RetrievalProvider,
    request: RetrievalSearchRequest,
) -> RetrievalHitDiagnostics:
    """Execute search and normalize provider rows to the project contract."""

    _validate_provider_match(provider, request.task)
    raw_hits = provider.search(
        request.task.query_text,
        k=request.k,
        recency_days=request.recency_days,
        include_domains=request.include_domains or None,
        exclude_domains=request.exclude_domains or None,
        max_chars=request.max_chars,
    )
    return _normalize_provider_hits(raw_hits)


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
        diagnostics = _execute_retrieval_search_with_diagnostics(provider, request)
        hits = diagnostics.hits
    except Exception as exc:
        completed_at = now or dt.datetime.now(dt.UTC)
        failure = _normalize_retrieval_failure(provider, request, exc, attempt_count=attempt_count)
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
                message=failure,
                created_at=completed_at,
            )
        )
        return RetrievalExecutionResult(
            task=failed_task,
            hits=[],
            run_events=run_events,
            warning=failure,
        )

    completed_at = now or dt.datetime.now(dt.UTC)
    raw_artifact_refs = _artifact_refs_from_hits(hits)
    if hits and diagnostics.has_warnings:
        warning = _normalization_warning(provider, request, diagnostics)
        final_task = running_task.model_copy(
            update={
                "completed_at": completed_at,
                "review_required": True,
                "status": "degraded",
                "raw_artifact_refs": raw_artifact_refs,
            }
        )
        final_event = RunEvent(
            run_event_id=f"{request.task.retrieval_task_id}:attempt-{attempt_count}:degraded",
            run_id=request.task.run_id,
            stage_id=request.task.stage_id,
            event_type="retrieval_degraded",
            severity="warning",
            message=warning,
            created_at=completed_at,
            artifact_refs=raw_artifact_refs,
        )
    elif hits:
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
        warning = (
            _normalization_warning(provider, request, diagnostics)
            if diagnostics.has_warnings
            else f"{provider.provider_name} returned no results for '{request.task.query_text}'."
        )
        final_task = running_task.model_copy(
            update={
                "completed_at": completed_at,
                "review_required": True,
                "status": "degraded",
                "raw_artifact_refs": raw_artifact_refs,
            }
        )
        final_event = RunEvent(
            run_event_id=(
                f"{request.task.retrieval_task_id}:attempt-{attempt_count}:degraded"
                if diagnostics.has_warnings
                else f"{request.task.retrieval_task_id}:attempt-{attempt_count}:empty"
            ),
            run_id=request.task.run_id,
            stage_id=request.task.stage_id,
            event_type="retrieval_degraded" if diagnostics.has_warnings else "retrieval_empty",
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
    raw_hits = provider.get_contents(request.urls, max_chars=request.max_chars)
    return _normalize_provider_hits(raw_hits).hits


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


def _normalize_provider_hits(raw_hits: Any) -> RetrievalHitDiagnostics:
    if raw_hits is None:
        raise RetrievalContractError(
            "retrieval provider returned a malformed response: expected list[dict]"
        )
    if not isinstance(raw_hits, list):
        raise RetrievalContractError(
            "retrieval provider returned a malformed response: expected list[dict]"
        )

    hits: list[dict[str, Any]] = []
    dropped_malformed_count = 0
    missing_url_count = 0
    for raw_hit in raw_hits:
        if not isinstance(raw_hit, Mapping):
            dropped_malformed_count += 1
            continue
        hit = _normalize_provider_hit(raw_hit)
        if not hit["url"]:
            missing_url_count += 1
        hits.append(hit)
    return RetrievalHitDiagnostics(
        hits=hits,
        dropped_malformed_count=dropped_malformed_count,
        missing_url_count=missing_url_count,
    )


def _normalize_provider_hit(raw_hit: Mapping[str, Any]) -> dict[str, Any]:
    text = _string_value(raw_hit.get("text"))
    snippet = _string_value(raw_hit.get("snippet")) or text[:500]
    normalized = dict(raw_hit)
    normalized.update(
        {
            "title": _string_value(raw_hit.get("title")),
            "url": _string_value(raw_hit.get("url")),
            "published_date": _string_value(raw_hit.get("published_date")),
            "snippet": snippet,
            "text": text,
            "score": raw_hit.get("score"),
        }
    )
    return normalized


def _normalize_retrieval_failure(
    provider: RetrievalProvider,
    request: RetrievalSearchRequest,
    exc: Exception,
    *,
    attempt_count: int,
) -> str:
    error_kind, retryable = _classify_retrieval_error(exc)
    return (
        f"{provider.provider_name} retrieval failed for '{request.task.query_text}': "
        f"error_kind={error_kind}; exception={type(exc).__name__}; "
        f"retryable={str(retryable).lower()}; attempts={attempt_count}."
    )


def _classify_retrieval_error(exc: Exception) -> tuple[str, bool]:
    name = type(exc).__name__.lower()
    message = str(exc).lower()
    if isinstance(exc, TimeoutError) or "timeout" in name or "timed out" in message:
        return "timeout", True
    if isinstance(exc, RetrievalContractError) or "responseerror" in name or "malformed response" in message:
        return "malformed_response", False
    if "budgetexhausted" in name or "budget exhausted" in message:
        return "budget_exhausted", False
    return "provider_error", True


def _normalization_warning(
    provider: RetrievalProvider,
    request: RetrievalSearchRequest,
    diagnostics: RetrievalHitDiagnostics,
) -> str:
    details = []
    if diagnostics.dropped_malformed_count:
        details.append(f"dropped_malformed={diagnostics.dropped_malformed_count}")
    if diagnostics.missing_url_count:
        details.append(f"missing_url={diagnostics.missing_url_count}")
    suffix = "; ".join(details)
    return (
        f"{provider.provider_name} returned partial or incomplete retrieval results "
        f"for '{request.task.query_text}': {suffix}."
    )


def _string_value(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


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
