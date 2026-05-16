# Issue 10 Offline Orchestration Service Slice

Last updated: May 16, 2026

This document records the first narrow product-mode service slice for issue `#10`.

The slice adds a small in-process offline orchestration service that consumes the
typed API boundary contracts from
[`ISSUE_10_API_CONTRACTS.md`](ISSUE_10_API_CONTRACTS.md). It still does not add
HTTP routes, persistence, queues, auth, dashboards, a web UI, or live retrieval.

## Scope Landed

- `src/war_room/orchestration_service.py` defines `InMemoryOrchestrationService`
  plus process-local helper functions:
  - `start_run(request: StartRunRequest) -> StartRunResponse`
  - `execute_run(run_id: str) -> GetRunStatusResponse`
  - `get_run_status(run_id: str) -> GetRunStatusResponse`
  - `get_run_outputs(run_id: str) -> OrchestrationServiceOutputs`
- `start_run()` creates a queued in-memory run using `StartRunResponse`,
  canonical run/stage statuses, and not-started timeline stages.
- `execute_run()` maps the typed intake to a curated offline-ready scenario,
  validates the committed fixture bundle, runs the cache-backed runtime with
  `client=None`, and returns a typed `GetRunStatusResponse`.
- The service preserves useful in-memory outputs for local callers:
  research plan, weather, carrier, case law, citation verification, memo
  markdown, evidence board, issue workspace, memo composer, export history, and
  run timeline.
- The status response exposes usable output pointers for weather, carrier,
  case law, citation verification, memo draft, and an audit/read-model bundle.
- Missing or non-offline-ready scenarios become typed failed status responses
  with stage failure details instead of unhandled fixture errors.
- A dependency-free smoke CLI is available:

```bash
python -m war_room.orchestration_service --smoke --scenario milton_pinellas_citizens_ho3
```

## Runtime Shape

This service is intentionally synchronous and process-local.

It is meant to prove the service boundary, response contracts, and offline
fixture execution path before any future HTTP wrapper is added. A future API
route can call the same service methods and serialize the existing typed
responses without changing the status vocabulary.

The service currently supports only curated offline-ready registry scenarios.
The typed `StartRunRequest` does not include a scenario id, so the service maps
requests to fixtures by matching the request intake to the curated scenario
registry.

## Review and Degradation Behavior

- Completed fixture-backed runs may still return `review_required=true`.
- Degraded citation verification and memo assembly stay visible in the typed
  timeline.
- Failed output stages can produce `partial_success` when other usable outputs
  survive.
- Failed planning or missing fixture scenarios return `failed` with a typed
  failure payload.
- The operator-facing run-status presentation checklist lives in
  [`ISSUE_10_STATUS_PRESENTATION.md`](ISSUE_10_STATUS_PRESENTATION.md).

## Out of Scope

This slice intentionally does not add:

- FastAPI, Flask, Streamlit, React, Next.js, or any web framework
- background queues or workers
- database persistence
- auth, access control, user accounts, dashboards, or UI
- retry policy, circuit breakers, or distributed execution
- notebook behavior changes
- fixture, cache-sample, citation-fact, golden-snapshot, dependency, or CI
  changes
- live retrieval

## Focused Tests

`tests/test_orchestration_service.py` covers:

- queued start responses and immediate queued status
- fixture-backed execution for the Milton baseline
- preserved read-model outputs and usable output pointers
- live-retrieval guard behavior
- partial-success behavior when an output stage fails
- typed failed status when a request cannot map to an offline-ready scenario

## Future API Use

Follow-up issue `#78` adds a thin dependency-free transport/request-handler
wrapper over this in-process service in
[`ISSUE_78_THIN_TRANSPORT_WRAPPER.md`](ISSUE_78_THIN_TRANSPORT_WRAPPER.md).
Production HTTP routing, persistence, worker semantics, and retry policy remain
future `#10` work behind the same typed response contracts. The next `#11`
slice can consume the same stage, status, review-required, and usable-output
semantics for guided intake and run status UX.
