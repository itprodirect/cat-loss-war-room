# Issue 10 Run-Status Presentation Checklist

Last updated: May 16, 2026

This checklist explains the small presentation layer added above the offline
orchestration service status response. It is dependency-free and does not add
HTTP routes, a web framework, persistence, queues, auth, or UI.

## Scope Landed

- `src/war_room/orchestration_status_view.py` converts a typed
  `GetRunStatusResponse` into an operator-facing dictionary.
- The view keeps the canonical run `status` and adds `operator_status`,
  `headline`, `operator_message`, usable-output availability, review reasons,
  degraded stages, failed stages, typed failure details, and next actions.
- The smoke CLI now includes those operator-facing fields while preserving the
  existing machine-readable status, stage summary, and usable-output summary.

## Status Meanings

- `completed`: the run completed and usable outputs are available.
- `degraded`: the canonical run status is still `completed`, but one or more
  stages reported limitations. Outputs can be reviewed, but the limitations
  must be inspected before relying on the run.
- `review_required`: the run completed and outputs are usable, but the typed
  status marks the run or outputs as requiring human review.
- `partial_success`: the run did not fully complete, but at least one usable
  output survived and can still be reviewed.
- `failed`: the run did not complete successfully and should not be presented
  as demo-ready. Typed failure details should explain the failed stage or
  service-level problem when available.

Current limitation: the canonical run-state contract does not include separate
`degraded` or `review_required` run statuses. The presentation layer derives
those operator statuses from `completed` runs with degraded stages or
`review_required=true`.

## Smoke CLI

```bash
python -m war_room.orchestration_service --smoke --scenario milton_pinellas_citizens_ho3
```

Before showing a scenario, a demo operator should verify:

- `status` is `completed` or `partial_success`.
- `usable_outputs_available` is `true`.
- `operator_status` is understood before presenting the run.
- `review_reasons`, `degraded_stages`, and `failed_stages` are empty or have
  been inspected.
- `failure_kind` and `failure_message` are empty unless the run is being shown
  specifically as a failure-mode demo.
- The memo disclaimer, citation posture, and review-required outputs have been
  checked.

## Usable Outputs

`usable_outputs` means the service preserved reviewable output pointers even
when the run needs review or did not fully complete.

- For `degraded` and `review_required` runs, outputs are available but require
  human inspection before reliance.
- For `partial_success` runs, surviving outputs can be reviewed, but the run
  must not be described as fully complete.
- For `failed` runs, usable outputs are not expected. Investigate the typed
  failure and rerun after fixing scenario or fixture setup.

## Intentionally Not Included

- no web app
- no API transport or HTTP route
- no live claim intake
- no production auth
- no persistence
- no queues or workers
- no retry policy or circuit breaker behavior
