# Issue 11 Guided Intake UX Spec

Last updated: May 17, 2026

This document defines a narrow product-facing guided-intake spec for issue
`#11`. It complements [`ISSUE_11_RUN_STATUS_UX_SPEC.md`](ISSUE_11_RUN_STATUS_UX_SPEC.md)
by describing the future intake surface that should precede run creation,
without building a frontend app in this repo.

Companion deterministic preview:
[`examples/guided_intake_milton_preview.md`](examples/guided_intake_milton_preview.md)
shows how the existing `milton_pinellas_citizens_ho3` fixture should appear in
a future guided-intake surface before Research Plan Preview and Run Status.

This is a UX/spec slice only. It does not add React, Next.js, a dashboard, app
shell, auth, persistence, production API, document upload, OCR/extraction,
notebook changes, dependencies, fixtures, cache changes, citation changes, or
live retrieval changes.

## Purpose

Guided intake helps a legal operator capture enough matter context to produce a
useful research plan and start a run without needing to understand Python,
Jupyter, provider configuration, or orchestration internals.

The intake surface should:

- make required facts explicit before run creation,
- collect optional facts without blocking useful research,
- preserve the repo's legal-review and demo posture,
- avoid false confidence when facts are missing or uncertain,
- and hand off cleanly to the existing run-status contract after a run starts.

## User Types

### Attorney or Reviewer

Needs to see the matter posture, jurisdiction, policy context, and uncertainty
before reviewing system output. The intake should make weak or missing context
visible without presenting the output as legal advice or final legal analysis.

### Paralegal or Operator

Owns day-to-day matter entry and run launch. The intake should use plain
English, field-specific validation, clear required/optional labels, and a final
review step before run creation.

### Technical Builder or Demo Operator

Needs to confirm the payload shape, selected offline scenario, expected run
contract, and safe demo boundaries. Technical detail should stay secondary to
the operator flow.

## Flow Sections

### Claim and Event Basics

Purpose: identify the catastrophe or loss event that anchors the research.

Required UX fields:

- Event name, mapped to `event_name`.
- Event date, mapped to `event_date` in `YYYY-MM-DD` format.

Optional UX fields:

- Internal matter label.
- Short event notes.
- Known date-range caveat when the exact date is uncertain.

### Property and Location

Purpose: locate the property and jurisdictional starting point.

Required UX fields:

- State, mapped to `state`.
- County or parish, mapped to the current `county` field.

Optional UX fields:

- Property address.
- City.
- ZIP code.
- Redaction note for sensitive location details.

The current runtime contract only requires state and county. A future UI should
not imply that optional address details are persisted or used by the current
notebook/runtime path until a later contract explicitly adds them.

### Policy and Carrier

Purpose: identify the insurance context for carrier and coverage research.

Required UX fields:

- Carrier, mapped to `carrier`.
- Policy type, mapped to `policy_type`.

Optional UX fields:

- Claim number.
- Policy number.
- Coverage form notes.
- Deductible or limit notes.

Optional policy identifiers are useful for human review, but this slice does
not add persistence, uploads, or expanded runtime schema fields.

### Loss Facts

Purpose: capture facts that shape issue hypotheses and research queries.

Optional UX fields:

- Key facts, mapped to `key_facts` as a list of non-empty strings.
- Loss description.
- Reported damage categories.
- Cause-of-loss notes.
- Timing notes for notice, inspection, denial, payment, or appraisal.

Missing loss facts should not block run creation if required event, location,
carrier, policy, and posture fields are complete. The UI may warn that generic
facts can produce broader research queries.

### Dispute Posture

Purpose: capture why the matter needs legal research and review.

Required UX fields:

- Dispute posture, mapped to `posture`.

The current backend defaults missing posture to `denial`, but a guided intake
surface should ask the user to confirm posture explicitly before starting a run.
The UI should normalize choices into snake_case tokens such as `denial`,
`underpayment`, or `bad_faith`.

Optional UX fields:

- Posture notes.
- Known insurer position.
- Requested remedy or procedural status.

### Documents and Evidence Available

Purpose: record what materials the human has available for later review.

Optional UX fields:

- Policy.
- Denial letter.
- Estimate.
- Photos or videos.
- Engineer report.
- Public adjuster report.
- Communications log.
- Prior payments.

This section is a checklist or note surface only for this slice. It does not
add document upload, file storage, OCR, extraction, document parsing, or
document-driven retrieval.

### Jurisdiction and Legal Posture

Purpose: clarify the legal lens for issue planning.

Required UX fields:

- State, already captured in Property and Location.

Optional UX fields:

- Coverage issues, mapped to `coverage_issues` as a list of non-empty strings.
- Venue notes.
- Pre-suit, litigation, appraisal, mediation, or appeal status.
- Known deadlines or statutory issues for human attention.

Optional legal-posture notes should be presented as research guidance, not as
legal conclusions.

### Review and Confirm Before Run

Purpose: give the operator one final chance to catch errors before run start.

The confirmation step should show:

- required fields and normalized values,
- optional fields that will influence the research plan,
- warnings for weak or missing optional context,
- demo/offline scenario labels when applicable,
- legal-review and citation-verification reminders,
- and the action that will start the run.

The primary action should create or start the run, then route the user into the
run-status surface defined in [`ISSUE_11_RUN_STATUS_UX_SPEC.md`](ISSUE_11_RUN_STATUS_UX_SPEC.md).

## Required vs Optional Field Rules

At the UX level, required to start a guided intake run:

- `event_name`
- `event_date`
- `state`
- `county`
- `carrier`
- `policy_type`
- `posture`

Optional but useful for research quality:

- `key_facts`
- `coverage_issues`
- internal matter label
- property address, city, ZIP code, and redaction notes
- claim number, policy number, coverage notes, deductible or limit notes
- loss description, damage categories, timing notes, and cause-of-loss notes
- documents/evidence checklist items
- venue, procedural posture, deadline, and statutory notes

The current strict runtime intake contract accepts only:

- `event_name`
- `event_date`
- `state`
- `county`
- `carrier`
- `policy_type`
- `posture`
- `key_facts`
- `coverage_issues`

A future UI should not send unsupported optional UX fields into the current
strict intake validator unless a later contract expands the payload. Unknown
fields should be handled safely in the UI layer and never produce a technical
stack trace for the operator.

## Validation and Error-Message Rules

- Use plain English.
- Attach every validation message to the field that needs attention when a
  field caused the issue.
- Never show Python exceptions, Pydantic tracebacks, JSON parser internals, or
  raw stack traces to attorneys, reviewers, or operators.
- Tell the user what to fix, not which internal function failed.
- Do not claim a field is legally sufficient or verified.
- Treat missing optional fields as warnings or quality caveats, not blockers.
- Treat missing required fields as blockers before run creation.
- Use safe fallbacks for unknown, not sure, or unavailable values.
- Preserve uncertainty in the review step instead of silently replacing it with
  confident copy.
- For structurally invalid values, say what format is expected, such as
  "Use YYYY-MM-DD for the event date."
- For unsupported extra fields, explain that the field is not part of the
  current guided-intake run contract.

## Demo and Offline Scenario Behavior

A future UI may offer committed offline scenarios for demos, including the
existing Milton scenario used by the orchestration smoke path. When it does:

- label the selection as demo/offline fixture data,
- show the scenario ID as demo metadata,
- avoid implying that the user entered a live claim intake,
- avoid implying production persistence, upload storage, or live retrieval,
- preserve the repo's disclaimer and citation-verification posture,
- and hand the operator to run status after the demo run starts.

Offline scenario selection is a demo shortcut, not a replacement for the
guided intake contract.

See
[`examples/guided_intake_milton_preview.md`](examples/guided_intake_milton_preview.md)
for the deterministic Milton fixture copy pattern.

## Handoff to Run Status

Guided intake should lead to start-run behavior. After a run is accepted, the
future UI should route to the run-status surface and consume the existing
orchestration status/read-model contracts.

The handoff should preserve:

- the accepted run ID,
- the selected scenario ID when a demo/offline scenario was used,
- the canonical run and stage vocabulary from `src/war_room/orchestration.py`,
- typed start-run and status response shapes from the orchestration contracts,
- and `status_presentation` as the product-facing status read model.

The guided intake surface should not invent a parallel run-status system or a
second set of stage labels.

## Copy Rules

- Present the tool as research acceleration, not legal advice.
- Remind users that citations and authorities must be independently verified
  before reliance.
- Do not tell users the intake is complete legal analysis.
- Do not call generated output approved, verified, final, or litigation-ready.
- Use "ready to start research" rather than "ready for legal conclusions."
- Use "review required" for uncertainty that needs human judgment.
- Keep demo/offline fixture labels visible when fixture data is selected.
- Do not hide missing optional context when it may affect research quality.

## Non-Goals

- No frontend implementation.
- No React, Next.js, dashboard, or app shell.
- No auth, sessions, users, or access-control model.
- No persistence, database, queue, worker, retry policy, or circuit breaker.
- No production API.
- No document upload implementation.
- No OCR or extraction implementation.
- No notebook changes.
- No fixture, cache, citation, prompt, schema, or live retrieval changes.
- No dependency changes.

## Acceptance Check

This spec is sufficient for the current slice when:

- a future UI builder can identify the required guided-intake fields,
- optional UX context is clearly separated from the current strict runtime
  payload,
- validation and copy rules preserve uncertainty and legal-review posture,
- demo/offline scenario behavior is labeled as fixture-backed demo behavior,
- the run-start handoff points to the existing orchestration status contracts,
- and the repo still has no frontend implementation or expanded runtime scope.
