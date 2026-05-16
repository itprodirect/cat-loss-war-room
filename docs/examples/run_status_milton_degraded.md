# Issue 11 Run-Status Preview: Milton Degraded

Last updated: May 16, 2026

This is a tiny deterministic preview for a future run-status product surface.
It is derived from the existing orchestration transport envelope for
`milton_pinellas_citizens_ho3`, using:

- `status_presentation` for the operator-facing copy, review posture, usable
  output list, degraded stage list, review reasons, and next actions.
- `payload.timeline.stages` for stage progress interpretation.
- `payload.run`, `payload.status.stage_counts`, `payload.failure`, `ok`, and
  `operation` only as secondary technical details.

This is not a frontend implementation. It does not add React, Next.js, a
dashboard, a production API, auth, persistence, queues, workers, dependencies,
notebook changes, fixture changes, citation changes, cache changes, or live
retrieval changes.

## Source Payload

Command used to inspect the same deterministic scenario:

```bash
python -m war_room.orchestration_service --smoke --scenario milton_pinellas_citizens_ho3
```

The markdown below follows the transport/status shape covered by
`tests/test_orchestration_transport.py`: `handle_execute_run(...)` returns
`ok=true`, `operation="execute_run"`, canonical `payload.run.status="completed"`,
and `status_presentation.operator_status="degraded"` for the Milton offline
scenario.

Runtime timestamps are intentionally omitted from the preview copy because
`created_at` and `started_at` vary by local run. The stable run identity and
status fields are preserved.

## Top Summary Card Copy

Badge: `degraded`

Headline: Run completed with degraded stages.

Message: Outputs are usable, but `citation_verify` and `memo_assembly`
reported limitations that a human should review.

Secondary metadata:

- Scenario: `milton_pinellas_citizens_ho3`
- Run ID: `run-offline-hurricane-milton-fl-pinellas-citizens-property-insurance`
- Canonical run status: `completed`
- Review required: `true`
- Usable outputs available: `true`

Presentation note: the main card should say the outputs are usable for human
review. It should not call this run verified, approved, clean, final, or legal
advice.

## Stage Progress Interpretation

Use `payload.timeline.stages`, not the smoke CLI `stage_summary`, for this
section.

| Stage | Status | Review | User-facing interpretation |
|---|---:|---:|---|
| `intake_validation` | `completed` | `false` | Required intake fields validated for Hurricane Milton in Pinellas County, FL. |
| `research_plan` | `completed` | `false` | Research plan produced 18 queries across 3 planned modules. |
| `weather` | `completed` | `false` | Weather brief completed with 9 sources and 2 observations. |
| `carrier` | `completed` | `false` | Carrier document pack completed with 4 documents and 2 defenses. |
| `caselaw` | `completed` | `false` | Case-law pack completed with 2 issues and 5 authorities. |
| `citation_verify` | `degraded` | `true` | Citation checks ran, but 5 uncertain citations require review. |
| `memo_assembly` | `degraded` | `true` | Memo/audit read models exist, but 1 review event requires follow-up. |
| `export` | `skipped` | `false` | Export was not written in this flow. |

The product surface should elevate `citation_verify` and `memo_assembly`
because they are listed in `status_presentation.degraded_stages`.

## Usable Outputs

Render `status_presentation.usable_outputs` as the default product-facing list.
Label review-required outputs as usable for review, not verified final support.

- Weather brief (9 sources)
  - Type: `weather_brief`
  - Stage: `weather`
  - Review required: `false`
  - URI: `memory://runs/run-offline-hurricane-milton-fl-pinellas-citizens-property-insurance/outputs/weather`
- Carrier document pack (4 documents)
  - Type: `carrier_doc_pack`
  - Stage: `carrier`
  - Review required: `false`
  - URI: `memory://runs/run-offline-hurricane-milton-fl-pinellas-citizens-property-insurance/outputs/carrier`
- Case-law pack (5 authorities)
  - Type: `caselaw_pack`
  - Stage: `caselaw`
  - Review required: `false`
  - URI: `memory://runs/run-offline-hurricane-milton-fl-pinellas-citizens-property-insurance/outputs/caselaw`
- Citation verification (6 checks)
  - Type: `citation_verify_pack`
  - Stage: `citation_verify`
  - Review required: `true`
  - URI: `memory://runs/run-offline-hurricane-milton-fl-pinellas-citizens-property-insurance/outputs/citation_verify`
- Memo draft (12 sections)
  - Type: `memo_draft`
  - Stage: `memo_assembly`
  - Review required: `true`
  - URI: `memory://runs/run-offline-hurricane-milton-fl-pinellas-citizens-property-insurance/outputs/memo_markdown`
- Audit read-model bundle (17 clusters, 5 issues)
  - Type: `audit_bundle`
  - Stage: `memo_assembly`
  - Review required: `true`
  - URI: `memory://runs/run-offline-hurricane-milton-fl-pinellas-citizens-property-insurance/outputs/audit_bundle`

## Review-Required Reasons

Render `status_presentation.review_reasons` prominently:

- `citation_verify`: 5 uncertain and 0 not found citations require review.
- `memo_assembly`: 1 review events require follow-up.
- Citation verification (6 checks) requires review.
- Memo draft (12 sections) requires review.
- Audit read-model bundle (17 clusters, 5 issues) requires review.

Concrete degraded stage anchors:

- `citation_verify`
- `memo_assembly`

Failed stage anchors: none.

## Next Actions

Render `status_presentation.next_actions` as the operator checklist:

1. Inspect review reasons, degraded stages, and review-required outputs.
2. Verify citations, memo warnings, and disclaimers before showing the
   scenario.

The operator should move next into citation review, memo-warning review, and
disclaimer verification before any external-facing demo use.

<details>
<summary>Optional technical details</summary>

```json
{
  "ok": true,
  "operation": "execute_run",
  "payload": {
    "run": {
      "run_id": "run-offline-hurricane-milton-fl-pinellas-citizens-property-insurance",
      "status": "completed",
      "review_required": true
    },
    "status": {
      "stage_counts": {
        "completed": 5,
        "degraded": 2,
        "skipped": 1
      },
      "usable_output_count": 6,
      "failure_count": 0
    },
    "failure": null
  },
  "status_presentation": {
    "operator_status": "degraded",
    "headline": "Run completed with degraded stages.",
    "usable_outputs_available": true,
    "review_required": true,
    "degraded_stages": [
      {
        "stage_key": "citation_verify",
        "status": "degraded",
        "review_required": true,
        "summary": "6 checks, 1 verified, 5 uncertain, 0 not found.",
        "error_summary": "5 uncertain and 0 not found citations require review.",
        "failure_kind": null,
        "failure_message": "5 uncertain and 0 not found citations require review."
      },
      {
        "stage_key": "memo_assembly",
        "status": "degraded",
        "review_required": true,
        "summary": "24 evidence items, 17 evidence clusters, 4 memo claims.",
        "error_summary": "1 review events require follow-up.",
        "failure_kind": null,
        "failure_message": "1 review events require follow-up."
      }
    ],
    "failed_stages": [],
    "failure_kind": null,
    "failure_message": ""
  }
}
```

Keep this detail collapsed or secondary in a future product surface. The
attorney/operator path should read the summary, stage progress, usable outputs,
review reasons, and next actions first.

</details>
