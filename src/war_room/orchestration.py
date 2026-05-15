"""Minimal V2 orchestration run-state contract.

This module defines the status vocabulary and transition rules that a future
API orchestrator can expose without making the current notebook runtime depend
on an API server, queue, database, or background worker.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Mapping, Sequence

RunStatus = Literal[
    "queued",
    "running",
    "partial_success",
    "failed",
    "completed",
    "cancelled",
]
StageStatus = Literal[
    "not_started",
    "in_progress",
    "completed",
    "degraded",
    "failed",
    "skipped",
]
StageKey = Literal[
    "intake_validation",
    "research_plan",
    "weather",
    "carrier",
    "caselaw",
    "citation_verify",
    "memo_assembly",
    "export",
]

RUN_STATES: tuple[str, ...] = (
    "queued",
    "running",
    "partial_success",
    "failed",
    "completed",
    "cancelled",
)
TERMINAL_RUN_STATES: frozenset[str] = frozenset(
    {"partial_success", "failed", "completed", "cancelled"}
)
RUN_STATE_TRANSITIONS: dict[str, frozenset[str]] = {
    "queued": frozenset({"queued", "running", "failed", "cancelled"}),
    "running": frozenset({"running", "partial_success", "failed", "completed", "cancelled"}),
    "partial_success": frozenset({"partial_success"}),
    "failed": frozenset({"failed"}),
    "completed": frozenset({"completed"}),
    "cancelled": frozenset({"cancelled"}),
}

STAGE_STATUSES: tuple[str, ...] = (
    "not_started",
    "in_progress",
    "completed",
    "degraded",
    "failed",
    "skipped",
)
TERMINAL_STAGE_STATUSES: frozenset[str] = frozenset(
    {"completed", "degraded", "failed", "skipped"}
)
STAGE_STATUS_TRANSITIONS: dict[str, frozenset[str]] = {
    "not_started": frozenset(
        {"not_started", "in_progress", "completed", "degraded", "failed", "skipped"}
    ),
    "in_progress": frozenset({"in_progress", "completed", "degraded", "failed", "skipped"}),
    "completed": frozenset({"completed"}),
    "degraded": frozenset({"degraded"}),
    "failed": frozenset({"failed"}),
    "skipped": frozenset({"skipped"}),
}

STAGE_KEYS: tuple[str, ...] = (
    "intake_validation",
    "research_plan",
    "weather",
    "carrier",
    "caselaw",
    "citation_verify",
    "memo_assembly",
    "export",
)
BLOCKING_STAGE_KEYS: frozenset[str] = frozenset({"intake_validation", "research_plan"})
REVIEWABLE_OUTPUT_STAGE_KEYS: frozenset[str] = frozenset(
    {"weather", "carrier", "caselaw", "citation_verify"}
)
REVIEW_REQUIRED_STAGE_KEYS: frozenset[str] = frozenset(
    {
        "research_plan",
        "weather",
        "carrier",
        "caselaw",
        "citation_verify",
        "memo_assembly",
    }
)


class OrchestrationStateError(ValueError):
    """Base error for orchestration state-contract violations."""


class UnknownRunStateError(OrchestrationStateError):
    """Raised when a run status is outside the canonical V2 contract."""


class UnknownStageStateError(OrchestrationStateError):
    """Raised when a stage key or status is outside the canonical V2 contract."""


class InvalidStateTransitionError(OrchestrationStateError):
    """Raised when a lifecycle transition is not allowed by the contract."""


@dataclass(frozen=True)
class StageStateSnapshot:
    """Normalized stage status used for run-status rollups.

    The shape intentionally mirrors the current ``RunStage`` fields while
    remaining a small dataclass that future API serializers can reuse.
    """

    stage_key: str
    status: str
    review_required: bool = False

    def __post_init__(self) -> None:
        ensure_stage_key(self.stage_key)
        ensure_stage_status(self.status)


def ensure_run_status(status: str) -> str:
    """Return a canonical run status or raise a contract error."""

    if status not in RUN_STATES:
        raise UnknownRunStateError(f"Unknown run status: {status!r}")
    return status


def ensure_stage_status(status: str) -> str:
    """Return a canonical stage status or raise a contract error."""

    if status not in STAGE_STATUSES:
        raise UnknownStageStateError(f"Unknown stage status: {status!r}")
    return status


def ensure_stage_key(stage_key: str) -> str:
    """Return a canonical stage key or raise a contract error."""

    if stage_key not in STAGE_KEYS:
        raise UnknownStageStateError(f"Unknown stage key: {stage_key!r}")
    return stage_key


def validate_run_transition(current_status: str, new_status: str) -> str:
    """Validate a run lifecycle transition and return ``new_status``.

    Repeating the same status is allowed so idempotent API updates and replayed
    events do not fail. Terminal statuses do not transition forward in this
    first slice; retry/circuit-breaker behavior remains future ``#10`` work.
    """

    current = ensure_run_status(current_status)
    new = ensure_run_status(new_status)
    if new not in RUN_STATE_TRANSITIONS[current]:
        raise InvalidStateTransitionError(
            f"Invalid run state transition: {current!r} -> {new!r}"
        )
    return new


def validate_stage_transition(current_status: str, new_status: str) -> str:
    """Validate a stage lifecycle transition and return ``new_status``."""

    current = ensure_stage_status(current_status)
    new = ensure_stage_status(new_status)
    if new not in STAGE_STATUS_TRANSITIONS[current]:
        raise InvalidStateTransitionError(
            f"Invalid stage state transition: {current!r} -> {new!r}"
        )
    return new


def is_terminal_run_status(status: str) -> bool:
    """Return whether a run status is terminal in this contract slice."""

    return ensure_run_status(status) in TERMINAL_RUN_STATES


def is_terminal_stage_status(status: str) -> bool:
    """Return whether a stage status is terminal in this contract slice."""

    return ensure_stage_status(status) in TERMINAL_STAGE_STATUSES


def normalize_stage_state(
    stage: Mapping[str, Any] | StageStateSnapshot | Any,
) -> StageStateSnapshot:
    """Normalize a mapping, dataclass, or RunStage-like object to stage state."""

    if isinstance(stage, StageStateSnapshot):
        return stage
    if isinstance(stage, Mapping):
        return StageStateSnapshot(
            stage_key=str(stage["stage_key"]),
            status=str(stage["status"]),
            review_required=bool(stage.get("review_required", False)),
        )
    return StageStateSnapshot(
        stage_key=str(getattr(stage, "stage_key")),
        status=str(getattr(stage, "status")),
        review_required=bool(getattr(stage, "review_required", False)),
    )


def normalize_stage_states(
    stages: Sequence[Mapping[str, Any] | StageStateSnapshot | Any],
) -> list[StageStateSnapshot]:
    """Normalize a list of stage records into the orchestration contract shape."""

    return [normalize_stage_state(stage) for stage in stages]


def derive_run_status_from_stages(
    stages: Sequence[Mapping[str, Any] | StageStateSnapshot | Any],
    *,
    output_stage_keys: frozenset[str] | set[str] | tuple[str, ...] = REVIEWABLE_OUTPUT_STAGE_KEYS,
    blocking_stage_keys: frozenset[str] | set[str] | tuple[str, ...] = BLOCKING_STAGE_KEYS,
) -> str:
    """Derive the overall run status from stage-level status records.

    The rollup is intentionally conservative:

    - all ``not_started`` stages mean the run is ``queued``;
    - any ``in_progress`` stage means the run is ``running``;
    - failed blocking stages hard-fail the run;
    - failed output stages with at least one usable output produce ``partial_success``;
    - failed output stages with no usable output produce ``failed``;
    - degraded stages require review but do not make the run partial by themselves.
    """

    normalized = normalize_stage_states(stages)
    if not normalized:
        return "queued"

    if all(stage.status == "not_started" for stage in normalized):
        return "queued"

    if any(stage.status == "in_progress" for stage in normalized):
        return "running"

    output_keys = set(output_stage_keys)
    blocking_keys = set(blocking_stage_keys)
    if any(stage.stage_key in blocking_keys and stage.status == "failed" for stage in normalized):
        return "failed"

    usable_outputs = [
        stage
        for stage in normalized
        if stage.stage_key in output_keys and stage.status in {"completed", "degraded"}
    ]
    failed_outputs = [
        stage
        for stage in normalized
        if stage.stage_key in output_keys and stage.status == "failed"
    ]
    if failed_outputs and usable_outputs:
        return "partial_success"
    if failed_outputs:
        return "failed"

    failed_nonblocking = [
        stage
        for stage in normalized
        if stage.status == "failed" and stage.stage_key not in blocking_keys
    ]
    if failed_nonblocking:
        return "partial_success" if usable_outputs else "failed"

    if any(stage.status == "not_started" for stage in normalized):
        return "running"

    return "completed"


def run_requires_review(
    stages: Sequence[Mapping[str, Any] | StageStateSnapshot | Any],
    *,
    review_stage_keys: frozenset[str] | set[str] | tuple[str, ...] = REVIEW_REQUIRED_STAGE_KEYS,
) -> bool:
    """Return whether any review-relevant stage is marked review-required."""

    review_keys = set(review_stage_keys)
    return any(
        stage.stage_key in review_keys and stage.review_required
        for stage in normalize_stage_states(stages)
    )
