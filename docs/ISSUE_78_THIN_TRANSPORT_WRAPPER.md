# Issue 78 Thin Orchestration Transport Wrapper

Last updated: May 16, 2026

This document records issue `#78`, a narrow transport/request-handler slice over
the existing offline orchestration service and status presentation contracts.

The wrapper proves that a future app can start an offline orchestration run,
execute it synchronously, and retrieve status through JSON-safe request-handler
functions. It does not add a production HTTP API.

## Scope Landed

- `src/war_room/orchestration_transport.py` adds dependency-free handlers:
  - `handle_start_run(payload, service=None)`
  - `handle_execute_run(run_id, service=None)`
  - `handle_get_run_status(run_id, service=None)`
  - `transport_response_to_payload(...)`
- `handle_start_run()` validates the incoming payload with the existing
  `StartRunRequest` contract, then calls `InMemoryOrchestrationService`.
- `handle_execute_run()` and `handle_get_run_status()` return the existing
  typed `GetRunStatusResponse` payload from the service.
- Successful transport responses include:
  - `ok`
  - `operation`
  - `payload`
  - `status_presentation`
- `payload` preserves the existing typed contract dictionaries:
  `StartRunResponse` for start and `GetRunStatusResponse` for execute/status.
- `status_presentation` is produced by
  `orchestration_status_view_to_payload()` and includes operator-facing fields
  such as `operator_status`, `headline`, `operator_message`,
  `review_reasons`, degraded/failed stages, typed failure details, and next
  actions.

## Runtime Shape

This is a transport adapter, not a web server.

It sits above:

- [`ISSUE_10_API_CONTRACTS.md`](ISSUE_10_API_CONTRACTS.md) for typed
  request/response payloads
- [`ISSUE_10_SERVICE_SLICE.md`](ISSUE_10_SERVICE_SLICE.md) for the synchronous
  in-memory offline service
- [`ISSUE_10_STATUS_PRESENTATION.md`](ISSUE_10_STATUS_PRESENTATION.md) for the
  operator-facing status view

The wrapper uses the same in-memory service by default, while tests can pass a
fresh service instance to avoid process-global state.

## Error Behavior

Invalid start-run request payloads return `ok=false` with the existing
`OrchestrationErrorResponse` payload shape and code
`invalid_start_run_request`.

Unknown run IDs return `ok=false` with a stable typed error payload such as
`unknown_run_error`.

Offline scenario failures after a run has been accepted remain typed service
status responses rather than transport errors. The response stays `ok=true`,
with `payload.run.status="failed"`, failed-stage details, no usable outputs,
and a failed operator presentation.

## Preserved Outputs and Failure Details

The execute/status payload is still the service's `GetRunStatusResponse`, so it
preserves:

- usable output pointers for completed, review-required, degraded, or
  partial-success runs
- failed stage details when fixture mapping or stage execution fails
- `status.failure_count` and stage-level failure payloads
- presentation-layer failed/degraded stage summaries and next actions

## Out of Scope

This slice intentionally does not add:

- FastAPI, Flask, Streamlit, React, Next.js, or any web framework
- HTTP routes or server startup
- auth, users, sessions, dashboards, or web UI
- database persistence, queues, workers, retries, or circuit breakers
- notebook behavior changes
- fixtures, cache samples, citation facts, golden snapshots, prompts, schemas,
  dependencies, or live retrieval changes

## Focused Tests

`tests/test_orchestration_transport.py` covers:

- queued start-run transport payloads with presentation-compatible shape
- execute/status transport payloads for the Milton offline scenario
- completed runs that surface review-required/degraded operator presentation
- reachable partial-success behavior through an existing service-stage failure
  helper
- unmapped offline scenarios returning typed failed status details
- unknown run IDs returning stable transport error payloads
- invalid start payloads returning typed transport errors

## Local Validation

```bash
python -m pytest tests/test_orchestration_transport.py tests/test_orchestration_service.py tests/test_orchestration_api_contracts.py tests/test_orchestration_status_view.py tests/test_orchestration_state.py -q
python -m pytest -q
python -m war_room --verify
python -m war_room.orchestration_service --smoke --scenario milton_pinellas_citizens_ho3
git diff --check
```
