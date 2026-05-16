"""Tests for orchestration run-status presentation helpers."""

from __future__ import annotations

import datetime as dt
import json

from war_room.models import Run
from war_room.orchestration import STAGE_KEYS
from war_room.orchestration_api_contracts import (
    GetRunStatusResponse,
    OrchestrationFailurePayload,
    OrchestrationRunStatusPayload,
    OrchestrationStagePayload,
    OrchestrationTimelinePayload,
    OrchestrationUsableOutputPayload,
    run_status_payload_from_run,
)
from war_room.orchestration_status_view import orchestration_status_view_to_payload

RUN_ID = "run-status-view"
NOW = dt.datetime(2026, 5, 16, 12, 0, tzinfo=dt.timezone.utc)


def _run(status: str, *, review_required: bool = False) -> Run:
    return Run(
        run_id=RUN_ID,
        environment="offline_service",
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
    summary: str = "",
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
        summary=summary or f"{stage_key} is {status}.",
        error_summary=error_summary,
        failure=failure,
    )


def _failure(stage_key: str, code: str) -> OrchestrationFailurePayload:
    return OrchestrationFailurePayload(
        code=code,
        message=f"{stage_key} failed with a typed contract error.",
        stage_key=stage_key,
        stage_id=f"{RUN_ID}:{stage_key}",
        retryable=False,
        detail=f"{stage_key} fixture detail",
    )


def _status(
    run: Run,
    stages: list[OrchestrationStagePayload],
    *,
    usable_output_count: int = 0,
    failure_count: int = 0,
) -> OrchestrationRunStatusPayload:
    return run_status_payload_from_run(
        run,
        stage_counts=_stage_counts(stages),
        usable_output_count=usable_output_count,
        failure_count=failure_count,
    )


def _timeline(stages: list[OrchestrationStagePayload]) -> OrchestrationTimelinePayload:
    return OrchestrationTimelinePayload(run_id=RUN_ID, stages=stages)


def _output(
    stage_key: str,
    output_type: str,
    *,
    review_required: bool = False,
) -> OrchestrationUsableOutputPayload:
    return OrchestrationUsableOutputPayload(
        output_id=f"{RUN_ID}:{stage_key}",
        run_id=RUN_ID,
        stage_key=stage_key,
        output_type=output_type,
        label=f"{stage_key} output",
        uri=f"memory://runs/{RUN_ID}/outputs/{stage_key}",
        review_required=review_required,
    )


def _stage_counts(stages: list[OrchestrationStagePayload]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for stage in stages:
        counts[stage.status] = counts.get(stage.status, 0) + 1
    return counts


def _response(
    run: Run,
    stages: list[OrchestrationStagePayload],
    *,
    usable_outputs: list[OrchestrationUsableOutputPayload] | None = None,
    failure_count: int = 0,
) -> GetRunStatusResponse:
    outputs = usable_outputs or []
    return GetRunStatusResponse(
        run=run,
        status=_status(
            run,
            stages,
            usable_output_count=len(outputs),
            failure_count=failure_count,
        ),
        timeline=_timeline(stages),
        usable_outputs=outputs,
    )


def test_completed_view_reports_usable_outputs_for_operator():
    run = _run("completed")
    stages = [_stage(stage_key, "completed") for stage_key in STAGE_KEYS]
    response = _response(
        run,
        stages,
        usable_outputs=[_output("weather", "weather_brief")],
    )

    view = orchestration_status_view_to_payload(response, scenario_id="milton_pinellas")

    json.dumps(view)
    assert view["scenario_id"] == "milton_pinellas"
    assert view["status"] == "completed"
    assert view["operator_status"] == "completed"
    assert view["headline"] == "Run completed with usable outputs."
    assert view["usable_outputs_available"] is True
    assert view["review_required"] is False
    assert view["review_reasons"] == []
    assert view["next_actions"]


def test_review_required_completed_view_without_degraded_stage_names_human_review():
    run = _run("completed", review_required=True)
    stages = [
        _stage("intake_validation", "completed"),
        _stage("research_plan", "completed"),
        _stage("weather", "completed", review_required=True),
        _stage("carrier", "completed"),
    ]
    response = _response(
        run,
        stages,
        usable_outputs=[_output("weather", "weather_brief", review_required=True)],
    )

    view = orchestration_status_view_to_payload(response)

    assert view["operator_status"] == "review_required"
    assert "requires human review" in view["headline"]
    assert view["review_required"] is True
    assert any("weather" in reason for reason in view["review_reasons"])
    assert any("Inspect review reasons" in action for action in view["next_actions"])


def test_degraded_completed_view_preserves_outputs_and_stage_reasons():
    run = _run("completed", review_required=True)
    stages = [
        _stage("intake_validation", "completed"),
        _stage("research_plan", "completed"),
        _stage("weather", "completed"),
        _stage("carrier", "completed"),
        _stage("caselaw", "completed"),
        _stage(
            "citation_verify",
            "degraded",
            review_required=True,
            summary="Citation checks need attorney confirmation.",
        ),
        _stage(
            "memo_assembly",
            "degraded",
            review_required=True,
            summary="Memo can be exported only after review.",
        ),
        _stage("export", "skipped"),
    ]
    response = _response(
        run,
        stages,
        usable_outputs=[
            _output("citation_verify", "citation_verify_pack", review_required=True),
            _output("memo_assembly", "memo_draft", review_required=True),
        ],
    )

    view = orchestration_status_view_to_payload(response)

    assert view["status"] == "completed"
    assert view["operator_status"] == "degraded"
    assert view["usable_outputs_available"] is True
    assert [stage["stage_key"] for stage in view["degraded_stages"]] == [
        "citation_verify",
        "memo_assembly",
    ]
    assert any("Citation checks" in reason for reason in view["review_reasons"])
    assert "Outputs are usable" in view["operator_message"]


def test_partial_success_view_keeps_surviving_outputs_and_failure_details():
    run = _run("partial_success", review_required=True)
    stages = [
        _stage("intake_validation", "completed"),
        _stage("research_plan", "completed"),
        _stage(
            "weather",
            "failed",
            review_required=True,
            failure=_failure("weather", "weather_retrieval_failed"),
        ),
        _stage("carrier", "completed"),
        _stage("caselaw", "completed"),
    ]
    response = _response(
        run,
        stages,
        usable_outputs=[_output("carrier", "carrier_doc_pack")],
        failure_count=1,
    )

    view = orchestration_status_view_to_payload(response)

    assert view["operator_status"] == "partial_success"
    assert view["usable_outputs_available"] is True
    assert view["usable_outputs"][0]["stage_key"] == "carrier"
    assert view["failed_stages"][0]["stage_key"] == "weather"
    assert view["failure_kind"] == "weather_retrieval_failed"
    assert "usable outputs survived" in view["operator_message"]


def test_failed_view_surfaces_typed_failure_and_blocks_demo_use():
    run = _run("failed", review_required=True)
    stages = [
        _stage("intake_validation", "completed"),
        _stage(
            "research_plan",
            "failed",
            review_required=True,
            failure=_failure("research_plan", "research_plan_failed"),
        ),
        _stage("weather", "not_started"),
    ]
    response = _response(run, stages, failure_count=1)

    view = orchestration_status_view_to_payload(response)

    assert view["operator_status"] == "failed"
    assert view["usable_outputs_available"] is False
    assert view["failure_kind"] == "research_plan_failed"
    assert "research_plan failed" in view["failure_message"]
    assert any("Do not present" in action for action in view["next_actions"])
