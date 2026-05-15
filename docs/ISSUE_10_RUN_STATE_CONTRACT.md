# Issue 10 Run-State Contract Slice

Last updated: May 15, 2026

This document records the first narrow implementation slice for issue `#10`.

The full issue still calls for an API service, graceful degradation, retries, and circuit-breaker behavior. This slice only adds the run-state and stage-state contract that future API orchestration can build on.

## Scope Landed

- `src/war_room/orchestration.py` defines canonical V2 run states, stage keys, stage statuses, transition rules, and stage-to-run rollup helpers.
- Existing `Run` and `RunStage` typed models now use the status literals from that contract instead of owning duplicate literal definitions.
- `workflow_summary.build_run_timeline()` still derives the same notebook/preflight run states, but its overall-status rollup now delegates to the shared orchestration helper with the current V0 output-stage set.
- `tests/test_orchestration_state.py` covers state vocabulary, valid transitions, invalid transitions, stage-state normalization, partial-success rollup, failed-run rollup, completed-run rollup, queued state, and running state.

## Run States

Canonical run states:

- `queued`
- `running`
- `partial_success`
- `failed`
- `completed`
- `cancelled`

Terminal states in this slice:

- `partial_success`
- `failed`
- `completed`
- `cancelled`

Allowed transitions:

| From | To |
|---|---|
| `queued` | `queued`, `running`, `failed`, `cancelled` |
| `running` | `running`, `partial_success`, `failed`, `completed`, `cancelled` |
| `partial_success` | `partial_success` |
| `failed` | `failed` |
| `completed` | `completed` |
| `cancelled` | `cancelled` |

Repeated same-state transitions are allowed so future event replay or idempotent API updates can reuse the contract safely.

## Stage States

Canonical stage keys:

- `intake_validation`
- `research_plan`
- `weather`
- `carrier`
- `caselaw`
- `citation_verify`
- `memo_assembly`
- `export`

Canonical stage statuses:

- `not_started`
- `in_progress`
- `completed`
- `degraded`
- `failed`
- `skipped`

Terminal stage statuses:

- `completed`
- `degraded`
- `failed`
- `skipped`

The stage contract uses `StageStateSnapshot` as the minimal normalized status shape:

- `stage_key`
- `status`
- `review_required`

It can normalize current `RunStage` records, dict payloads, or future API-facing objects with the same attributes.

## Rollup Rules

`derive_run_status_from_stages()` provides the first shared stage-to-run rollup:

- no stages, or all stages `not_started`, means `queued`
- any `in_progress` stage means `running`
- failed blocking stages (`intake_validation`, `research_plan`) mean `failed`
- failed output stages with at least one usable output mean `partial_success`
- failed output stages with no usable output mean `failed`
- degraded stages require review but do not make the whole run `partial_success` by themselves
- completed/degraded/skipped terminal stage sets without failed outputs mean `completed`

For current notebook/preflight behavior, `workflow_summary` passes the existing V0 output-stage set:

- `weather`
- `carrier`
- `caselaw`
- `citation_verify`

That preserves current behavior where uncertain citations or review-required memo assembly produce `completed` runs with `review_required=true`, while a failed module with surviving usable output produces `partial_success`.

## Future API Use

The future `#10` API service can use this contract for:

- run creation responses (`queued`)
- worker or orchestrator updates (`running`)
- terminal run summaries (`completed`, `partial_success`, `failed`, `cancelled`)
- per-stage timeline payloads
- idempotent transition validation
- degraded-stage display in future `#11` run-status UX

The API should expose these state names as stable response values rather than inventing a second status vocabulary.

## Out of Scope

This slice intentionally does not add:

- HTTP routes or an API framework
- a background queue
- a database or persistence layer
- retry policy or circuit breakers
- auth, security controls, dashboards, UI, or human-review workflow
- fixture, cache, notebook, citation, retrieval, or golden snapshot changes

## Validation Targets

The focused contract tests are:

```bash
python -m pytest tests/test_orchestration*.py -q
```

The full requested validation for this slice remains:

```bash
python -m pytest tests/test_orchestration*.py tests/test_offline_demo_pack.py tests/test_release_scorecard.py -q
python -m pytest -q
python -m war_room.fixture_snapshots --check
python -m war_room.offline_e2e --check
python -m war_room --verify --release-candidate issue-10-run-state-contract
git diff --check
```
