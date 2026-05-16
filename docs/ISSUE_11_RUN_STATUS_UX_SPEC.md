# Issue 11 Run-Status UX Spec

Last updated: May 16, 2026

This document defines a narrow product-facing run-status screen spec for issue
`#11`. It explains how a future user-facing surface should consume and present
the existing orchestration `status_presentation` payload without building a
frontend app in this repo.

Companion deterministic preview: [`examples/run_status_milton_degraded.md`](examples/run_status_milton_degraded.md)
shows how a future product surface should present the current Milton degraded
`status_presentation` payload without adding a frontend.

This is a UX/spec/read-model slice only. It does not add React, Next.js, a
dashboard, auth, persistence, a production API, notebook changes, dependencies,
fixtures, cache changes, citation changes, or live retrieval changes.

## Purpose

The run-status screen answers five user questions:

- Has the run been accepted, started, completed, degraded, partially completed,
  failed, or cancelled?
- Are any outputs usable for human review?
- Which stages need attention?
- What should the operator do next?
- What technical detail is available if a builder needs to troubleshoot?

The screen is a transition surface, not the final destination. When usable
outputs exist, it should route the user toward Evidence Review, Issue
Workspace, Memo Composer, or Export surfaces as appropriate. It must preserve
the repo's demo and legal-review posture: outputs are research acceleration
materials, not legal advice, and citations must be independently verified
before reliance.

## User Types

### Attorney or Reviewer

Needs a concise trust posture before reading or relying on output. The screen
must make review-required, degraded, partial-success, and failed states visible
without requiring the reviewer to inspect raw logs.

### Paralegal or Operator

Owns day-to-day run monitoring. The screen must show the current operator
status, stage progress, usable outputs, review reasons, and next actions in
plain English.

### Technical Builder or Demo Operator

Needs the same operator view plus enough collapsed technical detail to validate
the transport payload, run ID, scenario ID, canonical status, failed-stage
details, and typed error payloads during demos or local development.

## Authoritative Data Contract

A future UI should consume the transport or dev-HTTP envelope:

- `ok`
- `operation`
- `payload`
- `status_presentation`

For successful orchestration responses, `status_presentation` is the
authoritative user-facing read model. The UI should use its `operator_status`,
`headline`, `operator_message`, `review_reasons`, `degraded_stages`,
`failed_stages`, `usable_outputs`, and `next_actions` instead of independently
deriving run meaning.

The typed `payload` remains the source for canonical machine detail:

- `payload.run.status`
- `payload.run.review_required`
- `payload.status.stage_counts`
- `payload.timeline.stages`
- `payload.usable_outputs`
- `payload.failure`

If a dev smoke summary provides convenience fields such as `stage_summary` or
`usable_output_summary`, treat them as local smoke CLI conveniences only. They
are not transport or HTTP envelope fields, and a future UI should not treat them
as canonical product contract fields. When consuming the transport or HTTP
envelope, build the stage progress list from `payload.timeline.stages` and the
usable-output list from `status_presentation.usable_outputs`, while keeping the
full `status_presentation` payload as the authoritative product-facing read
model. Use `payload.usable_outputs` as typed technical detail, not as the
default product-facing list when the presentation payload is present.

For `ok=false` transport responses, `status_presentation` is `null`. The UI
should present the typed `payload.error` as a request or lookup problem, not as
an accepted run's product status unless the accepted run payload itself reports
`payload.run.status="failed"`.

## Primary Status States

| Operator status | User-facing meaning | Presentation rule |
|---|---|---|
| `queued` | The run was accepted but has not started. | Show a neutral waiting state and avoid implying work has begun. |
| `running` | The run is in progress. | Show stage progress and tell the operator to check again before relying on outputs. |
| `completed` | The run completed with usable outputs and no surfaced review/degraded operator condition. | Show outputs, next actions, and standard legal/demo verification reminders. |
| `degraded` | The canonical run may be complete, but one or more stages reported limitations. | Treat as operator-facing review required; show degraded stages and reasons prominently. |
| `review_required` | Outputs are usable, but the run or output contract says human review is required. | Mark outputs as usable but not clean final support. |
| `partial_success` | The run did not fully complete, but at least one usable output survived. | Clearly distinguish surviving usable outputs from failed stages; never call it complete. |
| `failed` | The run did not produce a reviewable bundle. | Block demo-ready language and direct the operator to failure details and rerun steps. |
| `cancelled` | The run was stopped after acceptance before reaching a completed, partial-success, or failed terminal state. | Show a neutral terminal stopped state, do not present the run as demo-ready, and direct the operator to start a fresh run or inspect technical details. |

## Field Presentation

### Top Summary Card

- `operator_status`: primary badge and state label.
- `headline`: main status sentence.
- `operator_message`: plain-English explanation beneath the headline.
- `run_id` and `scenario_id`: visible as secondary metadata.
- `payload.run.status`: available in technical details when it differs from
  `operator_status`; do not make the user reconcile both statuses in the main
  summary.

### Stage Progress List

- Render every stage from `payload.timeline.stages`.
- Do not use dev smoke CLI `stage_summary` as the default UI source. It is only
  a flat `{stage_key: status}` convenience summary and does not carry stage
  `summary`, `error_summary`, or `review_required` detail.
- Show stage key, status, short summary, error summary when present, and
  review-required marker.
- Elevate stages listed in `degraded_stages` and `failed_stages`.
- Do not hide degraded, skipped, or failed stages in logs.

### Usable Outputs Section

- Render `status_presentation.usable_outputs` as the default product-facing
  output list.
- Do not use dev smoke CLI `usable_output_summary` as the default UI source. It
  is a compact smoke convenience view, not a transport or HTTP envelope field.
- Show output label, output type, stage key, URI when available, and
  `review_required`.
- Label review-required outputs as usable for review, not verified final
  support.

### Review-Required Section

- Show `review_reasons` as primary operator-facing reasons.
- Include `degraded_stages` and `failed_stages` as concrete anchors.
- If there are no reasons but `review_required=true`, display the generic
  contract reason from the presentation payload.

### Next Actions Section

- Render `next_actions` as the operator checklist.
- For `failed`, use blocking language such as "Do not present this run as
  demo-ready."
- For `cancelled`, use neutral stopped-run language and direct the operator to
  start a fresh run or inspect technical details before attempting another demo
  path.
- For `degraded`, `review_required`, and `partial_success`, make inspection and
  citation/disclaimer review the next action before any external-facing demo.

### Technical Details

- Collapsed by default.
- Include canonical `payload.run.status`, `payload.status.stage_counts`,
  `payload.failure`, stage failure payloads, transport `operation`, and `ok`.
- Keep raw JSON available for a builder/demo operator, not as the primary
  attorney/paralegal reading surface.

## Copy Rules

- Use plain English and stable state labels.
- Do not claim legal sufficiency, citation verification, or final readiness.
- Do not describe a `degraded`, `review_required`, or `partial_success` run as
  fully clean.
- Clearly mark review-required outputs in the main flow and output list.
- Clearly distinguish usable-but-needs-review from failed.
- Preserve the repo's demo, not-legal-advice, and verify-all-citations
  disclaimers.
- Prefer "usable for human review" over "approved", "verified", or "ready".
- Use stage names from the payload; do not invent new product-stage names that
  conflict with the orchestration contract.
- Do not infer UI contract meaning from smoke CLI `stage_summary` or
  `usable_output_summary`; those summaries are convenience output for local dev
  smoke checks only.

## Layout and IA Guidance

1. Top summary card.
2. Stage progress list.
3. Usable outputs section.
4. Review-required section.
5. Next actions section.
6. Technical details collapsed by default.

The screen should stay consistent with `docs/V2_WORKFLOW_IA.md`: Run Status is
a timeline and trust-posture view that hands users into evidence and review
surfaces. It should not become a generic dashboard or the final product
destination.

## Non-Goals

- No frontend implementation.
- No React, Next.js, dashboard, or app framework.
- No auth, sessions, users, or access-control model.
- No persistence, database, queue, worker, retry policy, or circuit breaker.
- No production API.
- No new dependencies.
- No notebook changes.
- No fixture, cache, citation, prompt, schema, or live retrieval changes.

## Acceptance Check

This spec is sufficient for the current slice when:

- a future UI builder can identify `status_presentation` as the primary
  product-facing read model,
- the screen behavior for queued, running, completed, degraded,
  review-required, partial-success, failed, and cancelled runs is explicit,
- usable outputs are distinguished from failed or unreviewed outputs,
- review-required language is prominent and preserves disclaimers,
- technical details remain available but secondary,
- and the repo still has no frontend implementation or expanded runtime scope.
