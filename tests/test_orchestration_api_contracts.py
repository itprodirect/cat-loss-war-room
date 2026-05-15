"""Tests for future orchestration API request/response contracts."""

from __future__ import annotations

import datetime as dt

import pytest
from pydantic import ValidationError

from war_room.models import CaseIntake, Run
from war_room.orchestration import STAGE_KEYS
from war_room.orchestration_api_contracts import (
    GetRunStatusResponse,
    OrchestrationErrorResponse,
    OrchestrationFailurePayload,
    OrchestrationRunStatusPayload,
    OrchestrationStagePayload,
    OrchestrationTimelinePayload,
    OrchestrationUsableOutputPayload,
    StartRunRequest,
    StartRunResponse,
    get_run_status_response_to_payload,
    orchestration_error_response_to_payload,
    run_status_payload_from_run,
    start_run_request_to_payload,
    start_run_response_to_payload,
)


RUN_ID = "run-api-milton"
NOW = dt.datetime(2026, 5, 15, 12, 0, tzinfo=dt.timezone.utc)


def _intake() -> CaseIntake:
    return CaseIntake(
        event_name="Hurricane Milton",
        event_date="2024-10-09",
        state="FL",
        county="Pinellas",
        carrier="Citizens Property Insurance",
        policy_type="HO-3 Dwelling",
        posture=["denial", "bad_faith"],
        coverage_issues=["wind vs water causation", "scope of repair"],
    )


def _run(status: str, *, review_required: bool = False) -> Run:
    return Run(
        run_id=RUN_ID,
        environment="api",
        status=status,
        review_required=review_required,
        created_at=NOW,
        started_at=NOW if status != "queued" else None,
        completed_at=NOW if status in {"completed", "partial_success", "failed"} else None,
        intake_id=f"{RUN_ID}:intake",
        plan_id=f"{RUN_ID}:plan",
    )


def _stage(
    stage_key: str,
    status: str,
    *,
    review_required: bool = False,
    failure: OrchestrationFailurePayload | None = None,
    error_summary: str = "",
) -> OrchestrationStagePayload:
    return OrchestrationStagePayload(
        stage_id=f"{RUN_ID}:{stage_key}",
        run_id=RUN_ID,
        stage_key=stage_key,
        status=status,
        review_required=review_required,
        started_at=NOW if status != "not_started" else None,
        completed_at=NOW if status in {"completed", "degraded", "failed", "skipped"} else None,
        summary=f"{stage_key} is {status}.",
        error_summary=error_summary,
        failure=failure,
    )


def _failure(stage_key: str, code: str = "stage_failed") -> OrchestrationFailurePayload:
    return OrchestrationFailurePayload(
        code=code,
        message=f"{stage_key} failed with a contract-level error.",
        stage_key=stage_key,
        stage_id=f"{RUN_ID}:{stage_key}",
        retryable=False,
    )


def _status(
    run: Run,
    stages: list[OrchestrationStagePayload],
    *,
    current_stage_key: str | None = None,
    usable_output_count: int = 0,
    failure_count: int = 0,
) -> OrchestrationRunStatusPayload:
    return run_status_payload_from_run(
        run,
        current_stage_key=current_stage_key,
        stage_counts=_stage_counts(stages),
        usable_output_count=usable_output_count,
        failure_count=failure_count,
    )


def _timeline(stages: list[OrchestrationStagePayload]) -> OrchestrationTimelinePayload:
    return OrchestrationTimelinePayload(run_id=RUN_ID, stages=stages)


def _stage_counts(stages: list[OrchestrationStagePayload]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for stage in stages:
        counts[stage.status] = counts.get(stage.status, 0) + 1
    return counts


def test_start_run_request_serializes_intake_without_adding_service_fields():
    request = StartRunRequest(intake=_intake())
    payload = start_run_request_to_payload(request)

    assert payload["schema_version"] == "v2alpha1"
    assert payload["environment"] == "api"
    assert payload["requested_stage_keys"] == [
        "weather",
        "carrier",
        "caselaw",
        "citation_verify",
    ]
    assert payload["intake"]["event_name"] == "Hurricane Milton"

    with pytest.raises(ValidationError):
        StartRunRequest.model_validate(
            {
                "intake": _intake().model_dump(),
                "requested_stage_keys": ["weather", "weather"],
            }
        )


def test_start_run_response_represents_queued_run_after_creation():
    run = _run("queued")
    stages = [_stage(stage_key, "not_started") for stage_key in STAGE_KEYS]
    response = StartRunResponse(
        run=run,
        status=_status(run, stages),
        timeline=_timeline(stages),
    )
    payload = start_run_response_to_payload(response)

    assert payload["run"]["status"] == "queued"
    assert payload["status"]["stage_counts"] == {"not_started": len(STAGE_KEYS)}
    assert all(stage["status"] == "not_started" for stage in payload["timeline"]["stages"])


def test_get_run_status_response_represents_running_stage_progress():
    run = _run("running")
    stages = [
        _stage("intake_validation", "completed"),
        _stage("research_plan", "completed"),
        _stage("weather", "in_progress"),
        _stage("carrier", "not_started"),
    ]
    response = GetRunStatusResponse(
        run=run,
        status=_status(run, stages, current_stage_key="weather"),
        timeline=_timeline(stages),
    )
    payload = get_run_status_response_to_payload(response)

    assert payload["run"]["status"] == "running"
    assert payload["status"]["current_stage_key"] == "weather"
    assert payload["status"]["stage_counts"] == {
        "completed": 2,
        "in_progress": 1,
        "not_started": 1,
    }


def test_get_run_status_response_represents_completed_run():
    run = _run("completed")
    stages = [
        _stage("intake_validation", "completed"),
        _stage("research_plan", "completed"),
        _stage("weather", "completed"),
        _stage("carrier", "completed"),
        _stage("caselaw", "completed"),
        _stage("citation_verify", "completed"),
        _stage("memo_assembly", "completed"),
        _stage("export", "completed"),
    ]
    response = GetRunStatusResponse(
        run=run,
        status=_status(run, stages),
        timeline=_timeline(stages),
    )

    assert get_run_status_response_to_payload(response)["run"]["status"] == "completed"


def test_review_required_completed_response_does_not_fail_whole_run():
    run = _run("completed", review_required=True)
    stages = [
        _stage("intake_validation", "completed"),
        _stage("research_plan", "completed"),
        _stage("weather", "completed"),
        _stage("carrier", "completed"),
        _stage("caselaw", "completed"),
        _stage("citation_verify", "degraded", review_required=True),
        _stage("memo_assembly", "degraded", review_required=True),
        _stage("export", "skipped"),
    ]
    response = GetRunStatusResponse(
        run=run,
        status=_status(run, stages),
        timeline=_timeline(stages),
    )
    payload = get_run_status_response_to_payload(response)

    assert payload["run"]["status"] == "completed"
    assert payload["run"]["review_required"] is True
    assert payload["status"]["failure_count"] == 0


def test_partial_success_response_requires_preserved_usable_outputs():
    run = _run("partial_success", review_required=True)
    stages = [
        _stage("intake_validation", "completed"),
        _stage("research_plan", "completed"),
        _stage(
            "weather",
            "failed",
            review_required=True,
            failure=_failure("weather", code="weather_retrieval_failed"),
        ),
        _stage("carrier", "completed"),
        _stage("caselaw", "completed"),
    ]
    usable_outputs = [
        OrchestrationUsableOutputPayload(
            output_id=f"{RUN_ID}:carrier",
            run_id=RUN_ID,
            stage_key="carrier",
            output_type="carrier_doc_pack",
            label="Carrier document pack",
            review_required=False,
        )
    ]
    response = GetRunStatusResponse(
        run=run,
        status=_status(run, stages, usable_output_count=1, failure_count=1),
        timeline=_timeline(stages),
        usable_outputs=usable_outputs,
    )
    payload = get_run_status_response_to_payload(response)

    assert payload["run"]["status"] == "partial_success"
    assert payload["usable_outputs"][0]["stage_key"] == "carrier"
    assert payload["timeline"]["stages"][2]["failure"]["code"] == "weather_retrieval_failed"

    with pytest.raises(ValidationError, match="usable outputs"):
        GetRunStatusResponse(
            run=run,
            status=_status(run, stages, failure_count=1),
            timeline=_timeline(stages),
        )


def test_failed_response_requires_stage_failure_details():
    run = _run("failed", review_required=True)
    stages = [
        _stage("intake_validation", "completed"),
        _stage(
            "research_plan",
            "failed",
            review_required=True,
            failure=_failure("research_plan", code="research_plan_failed"),
        ),
        _stage("weather", "not_started"),
    ]
    response = GetRunStatusResponse(
        run=run,
        status=_status(run, stages, failure_count=1),
        timeline=_timeline(stages),
    )

    assert (
        get_run_status_response_to_payload(response)["timeline"]["stages"][1]["failure"]["code"]
        == "research_plan_failed"
    )

    with pytest.raises(ValidationError, match="failure details"):
        OrchestrationStagePayload(
            stage_id=f"{RUN_ID}:research_plan",
            run_id=RUN_ID,
            stage_key="research_plan",
            status="failed",
            review_required=True,
        )


def test_status_response_rejects_mismatched_run_and_timeline_state():
    run = _run("completed")
    stages = [
        _stage("intake_validation", "completed"),
        _stage("research_plan", "completed"),
        _stage("weather", "in_progress"),
    ]

    with pytest.raises(ValidationError, match="timeline stages derive"):
        GetRunStatusResponse(
            run=run,
            status=_status(run, stages),
            timeline=_timeline(stages),
        )


def test_timeline_rejects_duplicate_stage_keys():
    with pytest.raises(ValidationError, match="unique"):
        OrchestrationTimelinePayload(
            run_id=RUN_ID,
            stages=[
                _stage("weather", "not_started"),
                _stage("weather", "not_started"),
            ],
        )


def test_orchestration_error_response_serializes_stable_failure_shape():
    response = OrchestrationErrorResponse(
        run_id=RUN_ID,
        error=OrchestrationFailurePayload(
            code="invalid_run_state",
            message="The requested transition is not allowed.",
            retryable=False,
        ),
    )
    payload = orchestration_error_response_to_payload(response)

    assert payload == {
        "schema_version": "v2alpha1",
        "status": "error",
        "run_id": RUN_ID,
        "error": {
            "code": "invalid_run_state",
            "message": "The requested transition is not allowed.",
            "stage_key": None,
            "stage_id": None,
            "retryable": False,
            "detail": "",
        },
    }
