"""Tests for the first in-process offline orchestration service slice."""

from __future__ import annotations

import json
from pathlib import Path

from war_room.models import CaseIntake, weather_brief_to_payload
from war_room.orchestration import STAGE_KEYS
from war_room.orchestration_api_contracts import (
    GetRunStatusResponse,
    StartRunRequest,
    get_run_status_response_to_payload,
    start_run_response_to_payload,
)
from war_room.orchestration_service import InMemoryOrchestrationService
from war_room.scenarios import load_scenario

ROOT = Path(__file__).resolve().parent.parent


def _service() -> InMemoryOrchestrationService:
    return InMemoryOrchestrationService(repo_root=ROOT, cache_samples_dir=ROOT / "cache_samples")


def _milton_request() -> StartRunRequest:
    scenario = load_scenario("milton_pinellas_citizens_ho3", repo_root=ROOT)
    return StartRunRequest(
        intake=scenario.to_case_intake(),
        environment="offline_service",
    )


def test_start_run_returns_queued_contract_and_immediate_status():
    service = _service()

    response = service.start_run(_milton_request())
    status = service.get_run_status(response.run.run_id)
    payload = start_run_response_to_payload(response)
    status_payload = get_run_status_response_to_payload(status)

    assert payload["run"]["status"] == "queued"
    assert payload["status"]["stage_counts"] == {"not_started": len(STAGE_KEYS)}
    assert all(stage["status"] == "not_started" for stage in payload["timeline"]["stages"])
    assert status_payload["run"]["status"] == "queued"
    assert status_payload["usable_outputs"] == []


def test_execute_run_uses_offline_fixtures_and_preserves_outputs():
    service = _service()
    start_response = service.start_run(_milton_request())

    status = service.execute_run(start_response.run.run_id)
    payload = get_run_status_response_to_payload(status)
    outputs = service.get_run_outputs(start_response.run.run_id)

    json.dumps(payload)
    assert isinstance(status, GetRunStatusResponse)
    assert payload["run"]["status"] == "completed"
    assert payload["run"]["review_required"] is True
    assert payload["timeline"]["stages"][5]["stage_key"] == "citation_verify"
    assert payload["timeline"]["stages"][5]["status"] == "degraded"
    assert payload["timeline"]["stages"][6]["stage_key"] == "memo_assembly"
    assert payload["timeline"]["stages"][6]["status"] == "degraded"

    output_types = {output["output_type"] for output in payload["usable_outputs"]}
    assert output_types == {
        "weather_brief",
        "carrier_doc_pack",
        "caselaw_pack",
        "citation_verify_pack",
        "memo_draft",
        "audit_bundle",
    }
    assert outputs.research_plan is not None
    assert outputs.evidence_board is not None
    assert outputs.evidence_board.total_clusters > 0
    assert outputs.issue_workspace is not None
    assert outputs.issue_workspace.review_required_issue_count > 0
    assert outputs.memo_composer is not None
    assert outputs.memo_composer.export_eligibility == "review_required_export"
    assert outputs.export_history is not None
    assert outputs.export_history.entries[0].delivery_state == "not_written"
    assert outputs.run_timeline is not None
    assert outputs.run_timeline.run.status == "completed"
    assert "NOT LEGAL ADVICE" in outputs.memo_markdown


def test_execute_run_does_not_call_live_retrieval(monkeypatch):
    def _unexpected_live_retrieval(*args, **kwargs):
        raise AssertionError("offline orchestration service should not call live retrieval")

    monkeypatch.setattr("war_room.weather_module.execute_retrieval_task", _unexpected_live_retrieval)
    monkeypatch.setattr("war_room.carrier_module.execute_retrieval_task", _unexpected_live_retrieval)
    monkeypatch.setattr("war_room.caselaw_module.execute_retrieval_task", _unexpected_live_retrieval)
    monkeypatch.setattr("war_room.notebook_runtime.spot_check_citations", _unexpected_live_retrieval)

    service = _service()
    start_response = service.start_run(_milton_request())
    status = service.execute_run(start_response.run.run_id)

    assert status.run.status == "completed"


def test_degraded_or_failed_stage_returns_partial_success_without_crashing(monkeypatch):
    def _empty_weather(*args, **kwargs):
        return weather_brief_to_payload(
            {
                "module": "weather",
                "event_summary": "Offline weather fixture was unavailable.",
                "key_observations": [],
                "metrics": {
                    "max_wind_mph": None,
                    "storm_surge_ft": None,
                    "rain_in": None,
                },
                "sources": [],
                "warnings": ["Offline weather fixture was unavailable."],
            }
        )

    monkeypatch.setattr("war_room.orchestration_service.build_weather_brief", _empty_weather)
    service = _service()
    start_response = service.start_run(_milton_request())

    status = service.execute_run(start_response.run.run_id)
    payload = get_run_status_response_to_payload(status)

    assert payload["run"]["status"] == "partial_success"
    assert payload["run"]["review_required"] is True
    assert any(
        stage["stage_key"] == "weather" and stage["status"] == "failed"
        for stage in payload["timeline"]["stages"]
    )
    assert payload["usable_outputs"]
    assert {output["stage_key"] for output in payload["usable_outputs"]} >= {
        "carrier",
        "caselaw",
        "citation_verify",
    }


def test_missing_offline_scenario_returns_failed_status_response():
    service = _service()
    request = StartRunRequest(
        intake=CaseIntake(
            event_name="Imaginary Storm",
            event_date="2026-01-01",
            state="FL",
            county="Imaginary",
            carrier="No Fixture Carrier",
            policy_type="HO-3",
            posture=["denial"],
        ),
        environment="offline_service",
    )
    start_response = service.start_run(request)

    status = service.execute_run(start_response.run.run_id)
    payload = get_run_status_response_to_payload(status)

    assert payload["run"]["status"] == "failed"
    assert payload["run"]["review_required"] is True
    assert payload["status"]["failure_count"] == 1
    failed_stage = next(
        stage for stage in payload["timeline"]["stages"] if stage["stage_key"] == "research_plan"
    )
    assert failed_stage["status"] == "failed"
    assert failed_stage["failure"]["code"] == "offline_execution_failed"
    assert "offline-ready scenario" in failed_stage["failure"]["detail"]
    assert payload["usable_outputs"] == []
