"""Dependency-free request handlers for offline orchestration transport.

This module is intentionally not an HTTP server. It adapts app-like request
payloads into the in-memory orchestration service and returns JSON-safe
dictionaries that a future route or UI layer can pass through unchanged.
"""

from __future__ import annotations

import re
from typing import Any, Literal, Mapping

from pydantic import ValidationError

from war_room.models import SCHEMA_VERSION_DEFAULT
from war_room.orchestration_api_contracts import (
    GetRunStatusResponse,
    OrchestrationErrorResponse,
    OrchestrationFailurePayload,
    StartRunRequest,
    StartRunResponse,
    adapt_start_run_request,
    get_run_status_response_to_payload,
    orchestration_error_response_to_payload,
    start_run_response_to_payload,
)
from war_room.orchestration_service import (
    InMemoryOrchestrationService,
    OrchestrationServiceError,
    default_service,
)
from war_room.orchestration_status_view import orchestration_status_view_to_payload

TransportOperation = Literal["start_run", "execute_run", "get_run_status"]


def handle_start_run(
    payload: Mapping[str, Any] | StartRunRequest,
    service: InMemoryOrchestrationService | None = None,
    *,
    scenario_id: str | None = None,
) -> dict[str, Any]:
    """Validate a start-run payload, create a queued run, and return transport JSON."""

    operation: TransportOperation = "start_run"
    try:
        typed_request = adapt_start_run_request(payload)
        resolved_service = _resolve_service(service)
        response = resolved_service.start_run(typed_request)
        status_response = resolved_service.get_run_status(response.run.run_id)
    except ValidationError as exc:
        return _error_transport_payload(
            operation=operation,
            code="invalid_start_run_request",
            message="Start-run request payload failed validation.",
            detail=str(exc),
        )
    except OrchestrationServiceError as exc:
        return _service_error_transport_payload(operation=operation, error=exc)

    return transport_response_to_payload(
        response,
        operation=operation,
        status_response=status_response,
        scenario_id=scenario_id,
    )


def handle_execute_run(
    run_id: str,
    service: InMemoryOrchestrationService | None = None,
    *,
    scenario_id: str | None = None,
) -> dict[str, Any]:
    """Execute an existing offline run and return its status transport JSON."""

    operation: TransportOperation = "execute_run"
    try:
        normalized_run_id = _normalize_run_id(run_id)
        response = _resolve_service(service).execute_run(normalized_run_id)
    except ValueError as exc:
        return _error_transport_payload(
            operation=operation,
            code="invalid_run_id",
            message=str(exc),
            run_id=run_id if isinstance(run_id, str) else None,
        )
    except OrchestrationServiceError as exc:
        return _service_error_transport_payload(
            operation=operation,
            error=exc,
            run_id=run_id if isinstance(run_id, str) else None,
        )

    return transport_response_to_payload(
        response,
        operation=operation,
        scenario_id=scenario_id,
    )


def handle_get_run_status(
    run_id: str,
    service: InMemoryOrchestrationService | None = None,
    *,
    scenario_id: str | None = None,
) -> dict[str, Any]:
    """Return status for an existing offline run as transport JSON."""

    operation: TransportOperation = "get_run_status"
    try:
        normalized_run_id = _normalize_run_id(run_id)
        response = _resolve_service(service).get_run_status(normalized_run_id)
    except ValueError as exc:
        return _error_transport_payload(
            operation=operation,
            code="invalid_run_id",
            message=str(exc),
            run_id=run_id if isinstance(run_id, str) else None,
        )
    except OrchestrationServiceError as exc:
        return _service_error_transport_payload(
            operation=operation,
            error=exc,
            run_id=run_id if isinstance(run_id, str) else None,
        )

    return transport_response_to_payload(
        response,
        operation=operation,
        scenario_id=scenario_id,
    )


def transport_response_to_payload(
    response: StartRunResponse | GetRunStatusResponse | OrchestrationErrorResponse,
    *,
    operation: TransportOperation,
    status_response: GetRunStatusResponse | None = None,
    scenario_id: str | None = None,
) -> dict[str, Any]:
    """Wrap a typed orchestration response in the thin transport envelope."""

    if isinstance(response, StartRunResponse):
        if status_response is None:
            raise ValueError("status_response is required for start-run transport payloads.")
        return _success_transport_payload(
            operation=operation,
            payload=start_run_response_to_payload(response),
            status_response=status_response,
            scenario_id=scenario_id,
        )
    if isinstance(response, GetRunStatusResponse):
        return _success_transport_payload(
            operation=operation,
            payload=get_run_status_response_to_payload(response),
            status_response=response,
            scenario_id=scenario_id,
        )
    if isinstance(response, OrchestrationErrorResponse):
        return _wrapped_error_payload(
            operation=operation,
            payload=orchestration_error_response_to_payload(response),
        )
    raise TypeError(f"Unsupported orchestration transport response: {type(response).__name__}")


def _success_transport_payload(
    *,
    operation: TransportOperation,
    payload: dict[str, Any],
    status_response: GetRunStatusResponse,
    scenario_id: str | None,
) -> dict[str, Any]:
    return {
        "schema_version": payload.get("schema_version", SCHEMA_VERSION_DEFAULT),
        "ok": True,
        "operation": operation,
        "payload": payload,
        "status_presentation": orchestration_status_view_to_payload(
            status_response,
            scenario_id=scenario_id,
        ),
    }


def _service_error_transport_payload(
    *,
    operation: TransportOperation,
    error: OrchestrationServiceError,
    run_id: str | None = None,
) -> dict[str, Any]:
    return _error_transport_payload(
        operation=operation,
        code=_stable_error_code(type(error).__name__),
        message=str(error),
        run_id=run_id,
    )


def _error_transport_payload(
    *,
    operation: TransportOperation,
    code: str,
    message: str,
    run_id: str | None = None,
    detail: str = "",
) -> dict[str, Any]:
    response = OrchestrationErrorResponse(
        run_id=run_id,
        error=OrchestrationFailurePayload(
            code=code,
            message=message,
            retryable=False,
            detail=detail,
        ),
    )
    return _wrapped_error_payload(
        operation=operation,
        payload=orchestration_error_response_to_payload(response),
    )


def _wrapped_error_payload(
    *,
    operation: TransportOperation,
    payload: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": payload.get("schema_version", SCHEMA_VERSION_DEFAULT),
        "ok": False,
        "operation": operation,
        "payload": payload,
        "status_presentation": None,
    }


def _resolve_service(
    service: InMemoryOrchestrationService | None,
) -> InMemoryOrchestrationService:
    return service if service is not None else default_service()


def _normalize_run_id(run_id: str) -> str:
    if not isinstance(run_id, str) or not run_id.strip():
        raise ValueError("run_id must be a non-empty string.")
    return run_id.strip()


def _stable_error_code(value: str) -> str:
    separated = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", value.strip())
    normalized = re.sub(r"[^a-z0-9]+", "_", separated.lower()).strip("_")
    return normalized or "orchestration_transport_error"
