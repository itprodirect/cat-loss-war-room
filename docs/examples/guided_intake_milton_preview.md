# Issue 11 Guided-Intake Preview: Milton

Last updated: May 17, 2026

This is a tiny deterministic preview for a future guided-intake product
surface. It uses the existing offline scenario identity
`milton_pinellas_citizens_ho3` and complements:

- [`../ISSUE_11_GUIDED_INTAKE_UX_SPEC.md`](../ISSUE_11_GUIDED_INTAKE_UX_SPEC.md)
- [`../ISSUE_11_RUN_STATUS_UX_SPEC.md`](../ISSUE_11_RUN_STATUS_UX_SPEC.md)
- [`run_status_milton_degraded.md`](run_status_milton_degraded.md)
- [`../V2_WORKFLOW_IA.md`](../V2_WORKFLOW_IA.md)

This is not a frontend implementation. It does not add React, Next.js, a
dashboard, app shell, auth, persistence, a production API, queues, workers,
dependencies, notebook changes, fixture changes, cache changes, citation
changes, prompts, schemas, or live retrieval changes.

## Source Scenario / Purpose

Source scenario: `scenarios/milton_pinellas_citizens_ho3.json`

Scenario identity:

- Scenario ID: `milton_pinellas_citizens_ho3`
- Fixture key: `milton_citizens_pinellas`
- Scenario title: Hurricane Milton (Pinellas baseline)
- Offline demo ready: true

Purpose: show what a future legal operator would see before starting research
for the existing Milton demo scenario. The preview helps a builder align the
guided-intake flow with the current Issue 11 specs without changing runtime
behavior.

This preview presents the tool as research acceleration, not legal advice. It
does not say the intake is legally sufficient, citation-checked, or ready for
legal conclusions. It only shows that the required guided-intake facts are
ready to start research for this demo fixture.

## Matter/Intake Summary Card Copy

Card title: Hurricane Milton - Pinellas County, FL

Badge: Demo/offline fixture

Status: Ready to start research

Summary copy:

> The Milton demo intake has the required event, location, carrier, policy, and
> posture fields needed to prepare a research plan. Optional facts and coverage
> issues are included to guide weather corroboration, carrier research, and
> case-law issue grouping. Human review and citation verification remain
> required before any reliance on generated output.

Secondary metadata:

- Scenario: `milton_pinellas_citizens_ho3`
- Fixture key: `milton_citizens_pinellas`
- Event date: `2024-10-09`
- Carrier: Citizens Property Insurance
- Policy type: HO-3 Dwelling
- Posture: denial, bad faith

Presentation note: the summary card should not call this intake verified,
approved, final, litigation-ready, or legally sufficient.

## Required Fields Table

These are required by the Issue 11 guided-intake UX before a run starts.

| UX field | Runtime field | Milton preview value | Preview state | Operator copy |
|---|---|---|---|---|
| Event name | `event_name` | Hurricane Milton | Present | Event anchor is present for research planning. |
| Event date | `event_date` | `2024-10-09` | Present | Date uses `YYYY-MM-DD` format. |
| State | `state` | FL | Present | Jurisdiction starter is present. |
| County or parish | `county` | Pinellas | Present | County is present for local weather and venue-aware research. |
| Carrier | `carrier` | Citizens Property Insurance | Present | Carrier is present for carrier-document research. |
| Policy type | `policy_type` | HO-3 Dwelling | Present | Policy context is present for coverage research. |
| Dispute posture | `posture` | `denial`, `bad_faith` | Present | Posture is explicitly confirmed for the guided-intake preview. |

## Optional Fields Table

Optional fields improve research quality but do not block moving to Research
Plan Preview when required fields are present.

| UX field | Runtime field or preview-only note | Milton preview value | Preview state | Operator copy |
|---|---|---|---|---|
| Key facts | `key_facts` | Category 3 winds reached the west coast with broad Pinellas roof and envelope damage reports; interior water intrusion was reported within 48 hours after the claimed wind event; the carrier position attributed the loss to pre-existing wear and excluded water damage. | Included | These facts guide issue hypotheses and query specificity. |
| Coverage issues | `coverage_issues` | wind vs water causation; anti-concurrent causation clause; duty to investigate | Included | These issues shape the Research Plan Preview and later Issue Workspace grouping. |
| Internal matter label | UI-only until a later contract adds persistence | Hurricane Milton (Pinellas baseline) | Demo metadata only | Use as an operator label; do not send as an unsupported runtime intake field. |
| Property address, city, ZIP code | UI-only until a later contract expands the payload | Not supplied | Optional caveat | Missing address details do not block this demo research run. |
| Claim number or policy number | UI-only until a later contract expands the payload | Not supplied | Optional caveat | Missing identifiers do not block research, but a human may need them for file review. |
| Documents and evidence checklist | UI-only note surface for this slice | Not supplied | Optional caveat | This preview does not add upload, storage, OCR, or document extraction. |
| Redaction or sharing notes | UI-only note surface for this slice | Not supplied | Optional caveat | Operators should avoid entering sensitive details not needed for the demo fixture. |

## Validation and Readiness State

Readiness state: Ready to start research.

Plain-English validation copy:

- Required guided-intake fields are present.
- Event date uses the expected `YYYY-MM-DD` format.
- Posture values are normalized as snake_case runtime tokens.
- Optional field gaps are warnings, not blockers.
- Unsupported optional UX notes should remain in the UI layer until a later
  contract expands the strict runtime intake payload.

This readiness state means the future UI can move to Research Plan Preview. It
does not mean the facts are legally sufficient, the citations are checked, or
the output is ready for legal conclusions.

## Warnings and Review Notes

Show these notes before the operator starts research:

- This is demo/offline fixture data for `milton_pinellas_citizens_ho3`, not a
  live claim intake.
- Generated research materials are research acceleration only and are not legal
  advice.
- Citations and authorities must be independently verified before reliance.
- The later Milton run-status preview is degraded because citation verification
  and memo assembly require human review.
- Missing optional address, claim, policy-number, and document-checklist details
  may limit file-specific review, but they do not block this demo research run.
- Do not add sensitive client facts to a demo/offline fixture unless the repo's
  redaction and fixture rules explicitly allow it.

## Demo/Offline Fixture Labeling

Visible fixture label:

> Demo/offline fixture: `milton_pinellas_citizens_ho3`

Supporting label copy:

> This selection uses committed cache-backed fixture data for a deterministic
> demo. It does not create a live claim record, persist user-uploaded files,
> call live retrieval providers, or replace human review.

Builder note: offline scenario selection is a demo shortcut. It should not be
presented as a replacement for the guided-intake contract.

## Handoff to Research Plan Preview

Primary action copy: Continue to Research Plan Preview

Handoff copy:

> Build a research plan for Hurricane Milton in Pinellas County, FL, using
> Citizens Property Insurance, HO-3 Dwelling policy context, and the confirmed
> dispute posture. The plan should show planned weather, carrier, and case-law
> research before any run starts.

The Research Plan Preview should show:

- planned modules: weather, carrier, case law, and citation review,
- issue buckets from `coverage_issues`,
- representative query groups or question groups,
- broad-query or missing-context caveats,
- demo/offline fixture labeling,
- and citation verification and human-review reminders.

If required fields were missing or structurally invalid, the UI would route back
to guided intake with field-specific messages instead of starting a run.

## Handoff from Research Plan Preview to Run Status

Primary action copy: Start demo research run

Handoff copy:

> Start the Milton demo research run and open Run Status. Keep the scenario ID,
> accepted run ID, canonical run/stage vocabulary, and `status_presentation`
> contract available for the run-status surface.

Expected run-status destination:

- Run-status spec:
  [`../ISSUE_11_RUN_STATUS_UX_SPEC.md`](../ISSUE_11_RUN_STATUS_UX_SPEC.md)
- Milton degraded run-status preview:
  [`run_status_milton_degraded.md`](run_status_milton_degraded.md)
- Stable scenario ID: `milton_pinellas_citizens_ho3`
- Stable run ID for the existing service smoke path:
  `run-offline-hurricane-milton-fl-pinellas-citizens-property-insurance`

The Run Status view should consume the existing orchestration contracts and
`status_presentation` payload. The guided-intake preview should not invent a
parallel status system or a second set of stage labels.

<details>
<summary>Optional technical details</summary>

Current strict runtime intake fields:

```json
{
  "event_name": "Hurricane Milton",
  "event_date": "2024-10-09",
  "state": "FL",
  "county": "Pinellas",
  "carrier": "Citizens Property Insurance",
  "policy_type": "HO-3 Dwelling",
  "posture": [
    "denial",
    "bad_faith"
  ],
  "key_facts": [
    "Category 3 winds reached the west coast with broad Pinellas roof and envelope damage reports.",
    "Interior water intrusion was reported within 48 hours after the claimed wind event.",
    "The carrier position attributed the loss to pre-existing wear and excluded water damage."
  ],
  "coverage_issues": [
    "wind vs water causation",
    "anti-concurrent causation clause",
    "duty to investigate"
  ]
}
```

Current boundary notes:

- The strict runtime intake contract accepts only `event_name`, `event_date`,
  `state`, `county`, `carrier`, `policy_type`, `posture`, `key_facts`, and
  `coverage_issues`.
- The Issue 11 guided-intake UX may display additional optional notes, but this
  preview does not send unsupported fields into `validate_case_intake_payload`.
- Start-run and run-status handoff should use the existing typed orchestration
  contracts and the product-facing `status_presentation` read model.

</details>
