"""Tests for the dev-only orchestration HTTP adapter."""

from __future__ import annotations

import json
from pathlib import Path
from threading import Thread
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from war_room.models import CaseIntake
from war_room.orchestration_api_contracts import StartRunRequest, start_run_request_to_payload
from war_room.orchestration_http import MAX_REQUEST_BODY_BYTES, create_dev_http_server
from war_room.orchestration_service import InMemoryOrchestrationService
from war_room.scenarios import load_scenario

ROOT = Path(__file__).resolve().parent.parent
MILTON_SCENARIO_ID = "milton_pinellas_citizens_ho3"


def _service() -> InMemoryOrchestrationService:
    return InMemoryOrchestrationService(repo_root=ROOT, cache_samples_dir=ROOT / "cache_samples")


def _milton_request_payload() -> dict[str, Any]:
    scenario = load_scenario(MILTON_SCENARIO_ID, repo_root=ROOT)
    request = StartRunRequest(
        intake=scenario.to_case_intake(),
        environment="http_adapter_test",
    )
    return start_run_request_to_payload(request)


def _unmapped_request_payload() -> dict[str, Any]:
    return {
        "intake": CaseIntake(
            event_name="Imaginary Storm",
            event_date="2026-01-01",
            state="FL",
            county="Imaginary",
            carrier="No Fixture Carrier",
            policy_type="HO-3",
            posture=["denial"],
        ).model_dump(),
        "environment": "http_adapter_test",
    }


@pytest.fixture
def http_base_url():
    server = create_dev_http_server(
        ("127.0.0.1", 0),
        service=_service(),
        scenario_id=MILTON_SCENARIO_ID,
    )
    thread = Thread(target=server.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        yield f"http://{host}:{port}"
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()


def _request(
    base_url: str,
    method: str,
    path: str,
    *,
    payload: dict[str, Any] | None = None,
    raw_body: bytes | None = None,
) -> tuple[int, dict[str, Any]]:
    data = raw_body
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    elif raw_body is not None:
        headers["Content-Type"] = "application/json"

    request = Request(f"{base_url}{path}", data=data, headers=headers, method=method)
    try:
        with urlopen(request, timeout=10) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        return exc.code, json.loads(exc.read().decode("utf-8"))


def test_health_route_returns_dev_only_json_envelope(http_base_url):
    status, body = _request(http_base_url, "GET", "/healthz")

    assert status == 200
    assert body["ok"] is True
    assert body["operation"] == "healthz"
    assert body["payload"] == {
        "dev_only": True,
        "service": "war_room.orchestration_http",
        "status": "ok",
        "transport": "war_room.orchestration_transport",
    }
    assert body["status_presentation"] is None


def test_start_execute_and_fetch_milton_through_http_adapter(http_base_url):
    start_status, start = _request(
        http_base_url,
        "POST",
        "/runs",
        payload=_milton_request_payload(),
    )
    run_id = start["payload"]["run"]["run_id"]

    execute_status, executed = _request(
        http_base_url,
        "POST",
        f"/runs/{run_id}/execute",
    )
    fetch_status, fetched = _request(http_base_url, "GET", f"/runs/{run_id}")

    json.dumps(start)
    json.dumps(executed)
    json.dumps(fetched)
    assert start_status == 201
    assert start["ok"] is True
    assert start["operation"] == "start_run"
    assert start["payload"]["run"]["status"] == "queued"

    assert execute_status == 200
    assert executed["ok"] is True
    assert executed["operation"] == "execute_run"
    assert executed["payload"]["run"]["status"] == "completed"
    assert executed["status_presentation"]["scenario_id"] == MILTON_SCENARIO_ID
    assert executed["status_presentation"]["operator_status"] == "degraded"
    assert executed["status_presentation"]["usable_outputs_available"] is True

    assert fetch_status == 200
    assert fetched["ok"] is True
    assert fetched["operation"] == "get_run_status"
    assert fetched["payload"]["run"]["status"] == "completed"
    assert fetched["status_presentation"]["operator_status"] == "degraded"


def test_invalid_json_returns_http_error_with_transport_style_envelope(http_base_url):
    status, body = _request(
        http_base_url,
        "POST",
        "/runs",
        raw_body=b"{not valid json",
    )

    assert status == 400
    assert body["ok"] is False
    assert body["operation"] == "start_run"
    assert body["payload"]["status"] == "error"
    assert body["payload"]["error"]["code"] == "invalid_json"
    assert body["status_presentation"] is None




def test_request_body_too_large_returns_clear_json_error(http_base_url):
    oversized = b"{" + (b" " * MAX_REQUEST_BODY_BYTES) + b"}"
    status, body = _request(
        http_base_url,
        "POST",
        "/runs",
        raw_body=oversized,
    )

    assert status == 400
    assert body["ok"] is False
    assert body["operation"] == "start_run"
    assert body["payload"]["error"]["code"] == "request_too_large"


def test_create_server_rejects_non_loopback_host_by_default():
    with pytest.raises(ValueError, match="loopback hosts"):
        create_dev_http_server(("0.0.0.0", 0), service=_service(), scenario_id=MILTON_SCENARIO_ID)

def test_invalid_start_payload_returns_transport_error_over_http(http_base_url):
    status, body = _request(
        http_base_url,
        "POST",
        "/runs",
        payload={"intake": {"event_name": ""}},
    )

    assert status == 400
    assert body["ok"] is False
    assert body["operation"] == "start_run"
    assert body["payload"]["error"]["code"] == "invalid_start_run_request"
    assert body["status_presentation"] is None


def test_unknown_run_id_returns_ok_false_without_hiding_json_envelope(http_base_url):
    status, body = _request(http_base_url, "GET", "/runs/run-does-not-exist")

    assert status == 404
    assert body["ok"] is False
    assert body["operation"] == "get_run_status"
    assert body["payload"]["run_id"] == "run-does-not-exist"
    assert body["payload"]["error"]["code"] == "unknown_run_error"
    assert body["status_presentation"] is None


def test_accepted_run_failure_remains_ok_true_with_failed_run_status(http_base_url):
    start_status, start = _request(
        http_base_url,
        "POST",
        "/runs",
        payload=_unmapped_request_payload(),
    )
    run_id = start["payload"]["run"]["run_id"]

    execute_status, executed = _request(
        http_base_url,
        "POST",
        f"/runs/{run_id}/execute",
    )

    assert start_status == 201
    assert start["ok"] is True
    assert execute_status == 200
    assert executed["ok"] is True
    assert executed["payload"]["run"]["status"] == "failed"
    assert executed["status_presentation"]["operator_status"] == "failed"
    assert executed["status_presentation"]["usable_outputs_available"] is False


def test_unsupported_method_and_path_return_clear_json_errors(http_base_url):
    method_status, method_body = _request(http_base_url, "PUT", "/runs")
    path_status, path_body = _request(http_base_url, "GET", "/does-not-exist")

    assert method_status == 405
    assert method_body["ok"] is False
    assert method_body["operation"] == "http_request"
    assert method_body["payload"]["error"]["code"] == "unsupported_method"

    assert path_status == 404
    assert path_body["ok"] is False
    assert path_body["operation"] == "http_request"
    assert path_body["payload"]["error"]["code"] == "unknown_route"
