# Issue 10 Dev-Only HTTP Wrapper

Last updated: May 16, 2026

This note records the narrow dev-only HTTP adapter over the existing issue
`#10` orchestration transport layer.

The adapter exists so a future app can prove it can start, execute, and inspect
offline orchestration runs through HTTP-shaped requests. It is not a production
API service and does not make this repo a web app.

## Scope Landed

- `src/war_room/orchestration_http.py` adds a standard-library-only HTTP
  adapter around `src/war_room/orchestration_transport.py`.
- The adapter uses `http.server`, `json`, and `urllib`-compatible request
  semantics only.
- Tests can create an ephemeral server with `create_dev_http_server(...)` and a
  fresh `InMemoryOrchestrationService` so run state stays memory-only and
  process-local.
- Running `python -m war_room.orchestration_http` starts a local dev server and
  prints a JSON startup payload with `dev_only=true`.

## Dev Routes

| Method | Path | Behavior |
|---|---|---|
| `GET` | `/healthz` | Returns a small dev health envelope. |
| `POST` | `/runs` | Parses a JSON `StartRunRequest`-compatible payload and calls `handle_start_run(...)`. |
| `POST` | `/runs/{run_id}/execute` | Calls `handle_execute_run(...)` for an existing process-local run. |
| `GET` | `/runs/{run_id}` | Calls `handle_get_run_status(...)` for an existing process-local run. |

## Envelope Semantics

The HTTP adapter preserves the transport envelope:

- `ok`
- `operation`
- `payload`
- `status_presentation`

HTTP status codes describe request handling only. They do not replace the JSON
envelope semantics:

- invalid JSON, invalid start payloads, unsupported methods, unknown routes,
  invalid run IDs, and unknown run IDs return `ok=false`.
- accepted orchestration runs that fail during offline execution still return
  `ok=true` with `payload.run.status="failed"`.
- Milton fixture-backed execution still returns `ok=true` with
  `payload.run.status="completed"` and `status_presentation.operator_status`
  derived as `degraded`.

## Example Local Probe

```bash
python -m war_room.orchestration_http --host 127.0.0.1 --port 8765 --scenario-id milton_pinellas_citizens_ho3
```

Then post a `StartRunRequest`-compatible JSON body to `POST /runs`, execute the
returned `run_id` at `POST /runs/{run_id}/execute`, and inspect status with
`GET /runs/{run_id}`.

## Out of Scope

This slice intentionally does not add:

- FastAPI, Flask, Streamlit, Django, Next.js, React, or any app framework
- production API routing
- persistence, database tables, sessions, auth, or access control
- background queues, workers, retries, or circuit breakers
- dashboards, frontend, or notebook changes
- fixture changes, cache sample changes, citation fact changes, prompt/schema
  changes, dependencies, or live retrieval changes

## Focused Tests

`tests/test_orchestration_http.py` covers:

- dev health route
- start, execute, and status retrieval for Milton over HTTP
- Milton operator presentation staying `degraded`
- invalid JSON returning `ok=false`
- invalid start payloads returning `ok=false`
- unknown run IDs returning `ok=false`
- accepted offline run failure staying `ok=true` with
  `payload.run.status="failed"`
- unsupported methods and unknown paths returning JSON error envelopes

## Local Validation

```bash
python -m pytest tests/test_orchestration_http.py tests/test_orchestration_transport.py tests/test_orchestration_service.py -q
python -m pytest -q
python -m war_room --verify
python -m war_room.orchestration_service --smoke --scenario milton_pinellas_citizens_ho3
git diff --check
```
