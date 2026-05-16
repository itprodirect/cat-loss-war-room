# Issue 10 API Contract Slice

Last updated: May 16, 2026

This document records issue `#73`, the second narrow contract-first slice for
issue `#10`.

It adds typed request and response payloads for future orchestration API
boundaries. This slice itself did not add a live API service or transport.

Follow-up work in [`ISSUE_10_SERVICE_SLICE.md`](ISSUE_10_SERVICE_SLICE.md)
uses these contracts in a small in-process offline service without adding HTTP
routes, persistence, queues, auth, dashboards, UI, or live retrieval.

Later follow-up work adds an operator-facing status presentation layer in
[`ISSUE_10_STATUS_PRESENTATION.md`](ISSUE_10_STATUS_PRESENTATION.md) and a thin
dependency-free transport/request-handler wrapper in
[`ISSUE_78_THIN_TRANSPORT_WRAPPER.md`](ISSUE_78_THIN_TRANSPORT_WRAPPER.md).
Those layers still do not add HTTP routes, a production API framework,
persistence, queues, auth, dashboards, UI, or live retrieval.

## Scope Landed

- `src/war_room/orchestration_api_contracts.py` defines Pydantic contracts for:
  - `StartRunRequest`
  - `StartRunResponse`
  - `GetRunStatusResponse`
  - `OrchestrationStagePayload`
  - `OrchestrationRunStatusPayload`
  - `OrchestrationTimelinePayload`
  - `OrchestrationUsableOutputPayload`
  - `OrchestrationFailurePayload`
  - `OrchestrationErrorResponse`
- The contracts reuse the canonical run states, stage keys, and stage statuses
  from `src/war_room/orchestration.py`.
- The response contracts reuse the existing canonical `Run`, `RunStage`, and
  `RunEvent` concepts from `src/war_room/models.py`.
- `tests/test_orchestration_api_contracts.py` covers serialization, validation,
  invalid state combinations, and representative queued/running/completed/
  partial-success/failed/review-required payloads.

## Represented States

The start-run response is intentionally limited to a created run in `queued`
state, with a timeline whose stages are not yet started.

The get-run-status response can represent:

- `running` with an active stage and per-stage counts
- `completed` with no stage failures
- `completed` plus `review_required=true`, without treating the run as failed
- `partial_success` with at least one preserved usable output
- `failed` with explicit stage or response failure details

Partial-success responses must carry `usable_outputs` so future API consumers
do not lose reviewable work from successful stages when another stage fails.

Failed stages must include either `failure` details or an `error_summary`.

## Out of Scope

This slice does not add:

- HTTP routes or an API framework
- a background queue
- database tables or persistence
- auth, retry policy, circuit breakers, dashboard work, or UI
- notebook/runtime behavior changes
- fixture, cache sample, citation fact, live retrieval, or golden snapshot
  changes

The current V0 notebook/offline demo remains the active runtime surface.

## Future API Use

Future issue `#10` implementation can keep routing handlers or worker updates
through these contracts and the thin transport wrapper. Production HTTP routing,
persistence, queue semantics, retries, and operational policy remain future
work.
