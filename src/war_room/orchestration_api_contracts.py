"""Typed orchestration API boundary contracts.

These models define request and response payloads for a future issue #10 API
service. They intentionally do not add routes, queueing, persistence, auth, or
runtime behavior to the current notebook demo.
"""

from __future__ import annotations

import datetime as dt
from typing import Any, Literal, Mapping

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from war_room.models import (
    CaseIntake,
    Run,
    RunEvent,
    RunStage,
    SCHEMA_VERSION_DEFAULT,
    adapt_case_intake,
    adapt_run,
    run_to_payload,
)
from war_room.orchestration import (
    STAGE_STATUSES,
    RunStatus,
    StageKey,
    StageStatus,
    derive_run_status_from_stages,
    run_requires_review,
)

DEFAULT_START_STAGE_KEYS: tuple[StageKey, ...] = (
    "weather",
    "carrier",
    "caselaw",
    "citation_verify",
)

UsableOutputType = Literal[
    "weather_brief",
    "carrier_doc_pack",
    "caselaw_pack",
    "citation_verify_pack",
    "memo_draft",
    "export_artifact",
    "audit_bundle",
]


def _validate_schema_version(value: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ValueError("schema_version must be non-empty.")
    return cleaned


def _model_to_payload(model: BaseModel) -> dict[str, Any]:
    return model.model_dump()


class OrchestrationFailurePayload(BaseModel):
    """Structured failure details for failed stages or API errors."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    code: str = Field(min_length=1, pattern=r"^[a-z][a-z0-9_]*$")
    message: str = Field(min_length=1)
    stage_key: StageKey | None = None
    stage_id: str | None = None
    retryable: bool = False
    detail: str = ""


class OrchestrationStagePayload(BaseModel):
    """API-facing stage status payload for run timelines."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    stage_id: str = Field(min_length=1)
    run_id: str = Field(min_length=1)
    stage_key: StageKey
    status: StageStatus = "not_started"
    review_required: bool = False
    started_at: dt.datetime | None = None
    completed_at: dt.datetime | None = None
    summary: str = ""
    error_summary: str = ""
    failure: OrchestrationFailurePayload | None = None

    @model_validator(mode="after")
    def _validate_failure_details(self) -> "OrchestrationStagePayload":
        if self.status == "failed" and self.failure is None and not self.error_summary:
            raise ValueError("failed stage payloads must include failure details.")
        if self.failure is not None:
            if self.failure.stage_key is not None and self.failure.stage_key != self.stage_key:
                raise ValueError("stage failure stage_key must match the stage payload.")
            if self.failure.stage_id is not None and self.failure.stage_id != self.stage_id:
                raise ValueError("stage failure stage_id must match the stage payload.")
        return self


class OrchestrationRunStatusPayload(BaseModel):
    """Compact API status summary for a run."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    run_id: str = Field(min_length=1)
    status: RunStatus
    review_required: bool = False
    current_stage_key: StageKey | None = None
    stage_counts: dict[StageStatus, int] = Field(default_factory=dict)
    usable_output_count: int = Field(default=0, ge=0)
    failure_count: int = Field(default=0, ge=0)

    @field_validator("stage_counts")
    @classmethod
    def _validate_stage_counts(cls, value: dict[StageStatus, int]) -> dict[StageStatus, int]:
        valid_statuses = set(STAGE_STATUSES)
        for status, count in value.items():
            if status not in valid_statuses:
                raise ValueError(f"Unknown stage status in stage_counts: {status!r}")
            if count < 0:
                raise ValueError("stage_counts values must be non-negative.")
        return value


class OrchestrationTimelinePayload(BaseModel):
    """API-facing run timeline payload."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    run_id: str = Field(min_length=1)
    stages: list[OrchestrationStagePayload] = Field(default_factory=list)
    recent_events: list[RunEvent] = Field(default_factory=list)

    @model_validator(mode="after")
    def _validate_timeline_links(self) -> "OrchestrationTimelinePayload":
        stage_keys: set[str] = set()
        for stage in self.stages:
            if stage.run_id != self.run_id:
                raise ValueError("all timeline stages must belong to the response run.")
            if stage.stage_key in stage_keys:
                raise ValueError("timeline stage keys must be unique within a run.")
            stage_keys.add(stage.stage_key)
        for event in self.recent_events:
            if event.run_id != self.run_id:
                raise ValueError("all timeline events must belong to the response run.")
        return self


class OrchestrationUsableOutputPayload(BaseModel):
    """Pointer to output that survives a partial-success or review-required run."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    output_id: str = Field(min_length=1)
    run_id: str = Field(min_length=1)
    stage_key: StageKey
    output_type: UsableOutputType
    label: str = Field(min_length=1)
    uri: str | None = None
    review_required: bool = False


class StartRunRequest(BaseModel):
    """Request body for a future start-run API boundary."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    schema_version: str = SCHEMA_VERSION_DEFAULT
    intake: CaseIntake
    environment: str = "api"
    requested_stage_keys: list[StageKey] = Field(
        default_factory=lambda: list(DEFAULT_START_STAGE_KEYS)
    )

    @field_validator("schema_version")
    @classmethod
    def _validate_schema_version(cls, value: str) -> str:
        return _validate_schema_version(value)

    @field_validator("requested_stage_keys")
    @classmethod
    def _validate_requested_stage_keys(cls, value: list[StageKey]) -> list[StageKey]:
        if not value:
            raise ValueError("requested_stage_keys must contain at least one stage.")
        if len(set(value)) != len(value):
            raise ValueError("requested_stage_keys must not contain duplicates.")
        return value


class StartRunResponse(BaseModel):
    """Response body after a future API creates a queued run."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    schema_version: str = SCHEMA_VERSION_DEFAULT
    run: Run
    status: OrchestrationRunStatusPayload
    timeline: OrchestrationTimelinePayload

    @field_validator("schema_version")
    @classmethod
    def _validate_schema_version(cls, value: str) -> str:
        return _validate_schema_version(value)

    @model_validator(mode="after")
    def _validate_start_response(self) -> "StartRunResponse":
        _validate_response_identity(self.run, self.status, self.timeline)
        if self.run.status != "queued":
            raise ValueError("start-run responses must represent a queued run.")
        _validate_stage_rollup(self.run, self.timeline)
        _validate_status_counts(self.status, self.timeline, usable_output_count=0)
        return self


class GetRunStatusResponse(BaseModel):
    """Response body for a future get-run-status API boundary."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    schema_version: str = SCHEMA_VERSION_DEFAULT
    run: Run
    status: OrchestrationRunStatusPayload
    timeline: OrchestrationTimelinePayload
    usable_outputs: list[OrchestrationUsableOutputPayload] = Field(default_factory=list)
    failure: OrchestrationFailurePayload | None = None

    @field_validator("schema_version")
    @classmethod
    def _validate_schema_version(cls, value: str) -> str:
        return _validate_schema_version(value)

    @model_validator(mode="after")
    def _validate_status_response(self) -> "GetRunStatusResponse":
        _validate_response_identity(self.run, self.status, self.timeline)
        _validate_stage_rollup(self.run, self.timeline)
        _validate_usable_outputs(self.run, self.usable_outputs)
        failed_stage_count = sum(stage.status == "failed" for stage in self.timeline.stages)
        _validate_status_counts(
            self.status,
            self.timeline,
            usable_output_count=len(self.usable_outputs),
            failure_count=failed_stage_count + (1 if self.failure else 0),
        )
        if self.run.status == "partial_success" and not self.usable_outputs:
            raise ValueError("partial_success responses must preserve usable outputs.")
        if self.run.status == "failed" and failed_stage_count == 0 and self.failure is None:
            raise ValueError("failed responses must include stage or response failure details.")
        return self


class OrchestrationErrorResponse(BaseModel):
    """Small API error response shape for future orchestration boundaries."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    schema_version: str = SCHEMA_VERSION_DEFAULT
    status: Literal["error"] = "error"
    run_id: str | None = None
    error: OrchestrationFailurePayload

    @field_validator("schema_version")
    @classmethod
    def _validate_schema_version(cls, value: str) -> str:
        return _validate_schema_version(value)


def _validate_response_identity(
    run: Run,
    status: OrchestrationRunStatusPayload,
    timeline: OrchestrationTimelinePayload,
) -> None:
    if status.run_id != run.run_id:
        raise ValueError("status.run_id must match run.run_id.")
    if timeline.run_id != run.run_id:
        raise ValueError("timeline.run_id must match run.run_id.")
    if status.status != run.status:
        raise ValueError("status.status must match run.status.")
    if status.review_required != run.review_required:
        raise ValueError("status.review_required must match run.review_required.")


def _validate_stage_rollup(run: Run, timeline: OrchestrationTimelinePayload) -> None:
    if run.status == "cancelled":
        return
    derived_status = derive_run_status_from_stages(timeline.stages)
    if derived_status != run.status:
        raise ValueError(
            f"timeline stages derive {derived_status!r}, not run status {run.status!r}."
        )
    if run_requires_review(timeline.stages) and not run.review_required:
        raise ValueError("run.review_required must be true when any review stage requires review.")


def _validate_usable_outputs(
    run: Run,
    usable_outputs: list[OrchestrationUsableOutputPayload],
) -> None:
    for output in usable_outputs:
        if output.run_id != run.run_id:
            raise ValueError("usable output run_id must match run.run_id.")


def _validate_status_counts(
    status: OrchestrationRunStatusPayload,
    timeline: OrchestrationTimelinePayload,
    *,
    usable_output_count: int,
    failure_count: int = 0,
) -> None:
    if status.usable_output_count != usable_output_count:
        raise ValueError("status.usable_output_count must match usable_outputs.")
    if status.failure_count != failure_count:
        raise ValueError("status.failure_count must match failed stage and response failures.")
    if not status.stage_counts:
        return

    expected_counts: dict[str, int] = {}
    for stage in timeline.stages:
        expected_counts[stage.status] = expected_counts.get(stage.status, 0) + 1
    if dict(status.stage_counts) != expected_counts:
        raise ValueError("status.stage_counts must match timeline stage statuses.")


def adapt_start_run_request(payload: Mapping[str, Any] | StartRunRequest) -> StartRunRequest:
    """Validate/coerce a future start-run request payload."""
    if isinstance(payload, StartRunRequest):
        return payload
    return StartRunRequest.model_validate(payload)


def adapt_orchestration_stage(
    payload: Mapping[str, Any] | RunStage | OrchestrationStagePayload,
) -> OrchestrationStagePayload:
    """Validate/coerce a run-stage-like payload into the API stage contract."""
    if isinstance(payload, OrchestrationStagePayload):
        return payload
    if isinstance(payload, RunStage):
        return OrchestrationStagePayload.model_validate(payload.model_dump())
    return OrchestrationStagePayload.model_validate(payload)


def adapt_start_run_response(
    payload: Mapping[str, Any] | StartRunResponse,
) -> StartRunResponse:
    """Validate/coerce a future start-run response payload."""
    if isinstance(payload, StartRunResponse):
        return payload
    return StartRunResponse.model_validate(payload)


def adapt_get_run_status_response(
    payload: Mapping[str, Any] | GetRunStatusResponse,
) -> GetRunStatusResponse:
    """Validate/coerce a future get-run-status response payload."""
    if isinstance(payload, GetRunStatusResponse):
        return payload
    return GetRunStatusResponse.model_validate(payload)


def adapt_orchestration_error_response(
    payload: Mapping[str, Any] | OrchestrationErrorResponse,
) -> OrchestrationErrorResponse:
    """Validate/coerce a future orchestration error response payload."""
    if isinstance(payload, OrchestrationErrorResponse):
        return payload
    return OrchestrationErrorResponse.model_validate(payload)


def start_run_request_to_payload(
    payload: Mapping[str, Any] | StartRunRequest,
) -> dict[str, Any]:
    """Return a start-run request normalized against the API contract."""
    typed = adapt_start_run_request(payload)
    data = _model_to_payload(typed)
    data["intake"] = adapt_case_intake(typed.intake).model_dump()
    return data


def start_run_response_to_payload(
    payload: Mapping[str, Any] | StartRunResponse,
) -> dict[str, Any]:
    """Return a start-run response normalized against the API contract."""
    return _model_to_payload(adapt_start_run_response(payload))


def get_run_status_response_to_payload(
    payload: Mapping[str, Any] | GetRunStatusResponse,
) -> dict[str, Any]:
    """Return a get-run-status response normalized against the API contract."""
    return _model_to_payload(adapt_get_run_status_response(payload))


def orchestration_error_response_to_payload(
    payload: Mapping[str, Any] | OrchestrationErrorResponse,
) -> dict[str, Any]:
    """Return an orchestration error response normalized against the API contract."""
    return _model_to_payload(adapt_orchestration_error_response(payload))


def run_status_payload_from_run(
    run: Mapping[str, Any] | Run,
    *,
    current_stage_key: StageKey | None = None,
    stage_counts: dict[StageStatus, int] | None = None,
    usable_output_count: int = 0,
    failure_count: int = 0,
) -> OrchestrationRunStatusPayload:
    """Build a compact API status payload from an existing canonical run."""
    typed_run = adapt_run(run)
    return OrchestrationRunStatusPayload(
        run_id=typed_run.run_id,
        status=typed_run.status,
        review_required=typed_run.review_required,
        current_stage_key=current_stage_key,
        stage_counts=stage_counts or {},
        usable_output_count=usable_output_count,
        failure_count=failure_count,
    )


def run_payload_for_api(run: Mapping[str, Any] | Run) -> dict[str, Any]:
    """Return a canonical run payload suitable for API response nesting."""
    return run_to_payload(run)
