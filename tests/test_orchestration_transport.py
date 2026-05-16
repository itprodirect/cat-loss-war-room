"""Tests for the thin offline orchestration transport wrapper."""

from __future__ import annotations

import json
from pathlib import Path

from war_room.models import CaseIntake, weather_brief_to_payload
from war_room.orchestration import STAGE_KEYS
from war_room.orchestration_api_contracts import StartRunRequest, start_run_request_to_payload
from war_room.orchestration_service import InMemoryOrchestrationService
from war_room.orchestration_transport import (
    handle_execute_run,
    handle_get_run_status,
    handle_start_run,
)
from war_room.scenarios import load_scenario

ROOT = Path(__file__).resolve().parent.parent
MILTON_SCENARIO_ID = "milton_pinellas_citizens_ho3"


def _service() -> InMemoryOrchestrationService:
    return InMemoryOrchestrationService(repo_root=ROOT, cache_samples_dir=ROOT / "cache_samples")


def _milton_request_payload() -> dict:
    scenario = load_scenario(MILTON_SCENARIO_ID, repo_root=ROOT)
    request = StartRunRequest(
        intake=scenario.to_case_intake(),
        environment="transport_test",
    )
    return start_run_request_to_payload(request)


def test_start_run_handler_returns_queued_payload_and_presentation_shape():
    service = _service()

    response = handle_start_run(
        _milton_request_payload(),
        service=service,
        scenario_id=MILTON_SCENARIO_ID,
    )

    json.dumps(response)
    assert response["ok"] is True
    assert response["operation"] == "start_run"
    assert response["payload"]["run"]["status"] == "queued"
    assert response["payload"]["status"]["stage_counts"] == {"not_started": len(STAGE_KEYS)}
    assert response["status_presentation"]["scenario_id"] == MILTON_SCENARIO_ID
    assert response["status_presentation"]["operator_status"] == "queued"
    assert response["status_presentation"]["usable_outputs_available"] is False


def test_execute_and_status_handlers_return_completed_milton_run_with_operator_view():
    service = _service()
    start = handle_start_run(_milton_request_payload(), service=service)
    run_id = start["payload"]["run"]["run_id"]

    executed = handle_execute_run(run_id, service=service, scenario_id=MILTON_SCENARIO_ID)
    status = handle_get_run_status(run_id, service=service, scenario_id=MILTON_SCENARIO_ID)

    json.dumps(executed)
    json.dumps(status)
    assert executed["ok"] is True
    assert executed["operation"] == "execute_run"
    assert executed["payload"]["run"]["status"] == "completed"
    assert executed["payload"]["run"]["review_required"] is True
    assert executed["status_presentation"]["operator_status"] == "degraded"
    assert executed["status_presentation"]["usable_outputs_available"] is True
    assert [stage["stage_key"] for stage in executed["status_presentation"]["degraded_stages"]] == [
        "citation_verify",
        "memo_assembly",
    ]
    assert executed["status_presentation"]["review_reasons"]

    assert status["ok"] is True
    assert status["operation"] == "get_run_status"
    assert status["payload"]["run"]["status"] == "completed"
    assert status["status_presentation"]["operator_status"] == "degraded"
    assert {output["output_type"] for output in status["payload"]["usable_outputs"]} == {
        "weather_brief",
        "carrier_doc_pack",
        "caselaw_pack",
        "citation_verify_pack",
        "memo_draft",
        "audit_bundle",
    }


def test_partial_success_status_preserves_surviving_outputs_and_failed_stage(monkeypatch):
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
    start = handle_start_run(_milton_request_payload(), service=service)

    response = handle_execute_run(start["payload"]["run"]["run_id"], service=service)

    assert response["ok"] is True
    assert response["payload"]["run"]["status"] == "partial_success"
    assert response["status_presentation"]["operator_status"] == "partial_success"
    assert response["status_presentation"]["usable_outputs_available"] is True
    assert response["status_presentation"]["failed_stages"][0]["stage_key"] == "weather"
    assert {output["stage_key"] for output in response["payload"]["usable_outputs"]} >= {
        "carrier",
        "caselaw",
        "citation_verify",
    }


def test_unmapped_offline_scenario_returns_failed_status_with_typed_details():
    service = _service()
    start = handle_start_run(
        {
            "intake": CaseIntake(
                event_name="Imaginary Storm",
                event_date="2026-01-01",
                state="FL",
                county="Imaginary",
                carrier="No Fixture Carrier",
                policy_type="HO-3",
                posture=["denial"],
            ).model_dump(),
            "environment": "transport_test",
        },
        service=service,
    )

    response = handle_execute_run(start["payload"]["run"]["run_id"], service=service)
    failed_stage = next(
        stage for stage in response["payload"]["timeline"]["stages"] if stage["status"] == "failed"
    )

    json.dumps(response)
    assert response["ok"] is True
    assert response["payload"]["run"]["status"] == "failed"
    assert response["status_presentation"]["operator_status"] == "failed"
    assert response["status_presentation"]["usable_outputs_available"] is False
    assert failed_stage["stage_key"] == "research_plan"
    assert failed_stage["failure"]["code"] == "offline_execution_failed"
    assert "offline-ready scenario" in failed_stage["failure"]["detail"]
    assert response["payload"]["usable_outputs"] == []


def test_unknown_run_id_returns_stable_transport_error_payload():
    response = handle_get_run_status("run-does-not-exist", service=_service())

    assert response == {
        "schema_version": "v2alpha1",
        "ok": False,
        "operation": "get_run_status",
        "payload": {
            "schema_version": "v2alpha1",
            "status": "error",
            "run_id": "run-does-not-exist",
            "error": {
                "code": "unknown_run_error",
                "message": "Unknown orchestration run_id: run-does-not-exist",
                "stage_key": None,
                "stage_id": None,
                "retryable": False,
                "detail": "",
            },
        },
        "status_presentation": None,
    }


def test_invalid_start_payload_returns_transport_error_without_service_crash():
    response = handle_start_run({"intake": {"event_name": ""}}, service=_service())

    assert response["ok"] is False
    assert response["operation"] == "start_run"
    assert response["payload"]["status"] == "error"
    assert response["payload"]["run_id"] is None
    assert response["payload"]["error"]["code"] == "invalid_start_run_request"
    assert "failed validation" in response["payload"]["error"]["message"]
    assert response["status_presentation"] is None
