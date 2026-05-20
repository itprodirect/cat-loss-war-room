# Issue 27 Release-Evidence Review Guide

Last updated: May 20, 2026

This guide explains how a human reviewer should read the release-evidence
bundle produced by:

```bash
python -m war_room --verify
```

It uses the readiness model in
[`V2_RELEASE_RUBRIC.md`](V2_RELEASE_RUBRIC.md). It does not create a second
readiness framework, rename the release levels, or expand the current runtime
scope.

## Purpose

The verify bundle gives a reviewer one traceable path from a local supported
verification run to the evidence used for the current issue `#27` release
posture.

Use it to answer:

- did the supported test path pass,
- did the offline demo preflight pass,
- did the committed fixture lane meet the current Demo-ready thresholds,
- did the release scorecard record blocking and advisory readiness categories,
- and does the current build remain honest about Beta-ready and Pilot-ready
gaps.

Do not use this guide to override the rubric. The source of truth for release
levels, scoring dimensions, and blocking/advisory semantics remains
[`V2_RELEASE_RUBRIC.md`](V2_RELEASE_RUBRIC.md).

## Current Target Release Level: Demo-ready

The current scorecard target is `Demo-ready`.

`Demo-ready` means suitable for a narrated or guided demonstration with a stable
offline lane, no hard crashes in the primary flow, readable memo output,
visible disclaimer language, and enough trust signaling that a reviewer
understands the output is research support, not legal advice.

`release-ready` is target-scoped. In the current bundle, `release-ready` means
release-ready for the stated `Demo-ready` target. It does not mean
Beta-ready, Pilot-ready, production-ready, or client-facing without attorney
review.

## What Files and Artifacts Are Produced

`python -m war_room --verify` runs the offline demo preflight, then the
supported `pytest -q` path. When both pass, it writes a linked evidence bundle:

- `runs/verify/latest.json`: stable pointer to the newest successful verify
  manifest.
- `runs/verify/<date>_<candidate>_<run_id>.json`: verify manifest for one
  run.
- `runs/preflight/<date>_<candidate>_<run_id>.json`: machine-readable offline
  preflight artifact for the same run.
- `runs/release_scorecards/<date>_<candidate>_<run_id>.json`: structured
  release scorecard.
- `runs/release_scorecards/<date>_<candidate>_<run_id>.md`: reviewer-friendly
  Markdown rendering of the same scorecard.

The verify manifest is the hub. Start with `runs/verify/latest.json`, open the
manifest it references, then follow the manifest paths to the preflight and
release-scorecard artifacts.

## What To Inspect First

Review in this order:

1. `runs/verify/latest.json`, to confirm which run is being reviewed.
2. The verify manifest under `runs/verify/`, to confirm the shared `run_id`,
   candidate, `pytest -q` summary, preflight path, and scorecard paths.
3. The preflight artifact, to confirm the offline demo lane passed and each
   committed scenario remained reviewable.
4. The release-scorecard Markdown, to read the human summary.
5. The release-scorecard JSON, to inspect exact `readiness_posture`,
   `must_pass_gates`, `calibration_thresholds`, and `dimensions` fields.

If any linked artifact is missing, has a different `run_id`, or contradicts the
manifest, do not treat the bundle as release evidence for a narrated demo until
the verify run is regenerated and reviewed.

## How To Read `runs/verify/latest.json`

`latest.json` is a discovery pointer, not the full evidence bundle.

Expected fields:

- `run_id`: shared identifier used by the linked verify, preflight, and
  scorecard artifacts.
- `created_at`: timestamp from the preflight run.
- `candidate`: branch or release-candidate label used for the verify run.
- `verify_manifest_path`: path to the run-specific manifest under
  `runs/verify/`.

Use `latest.json` only to find the newest successful manifest. The review
decision should be based on the manifest and linked artifacts, not on the
pointer alone.

## How To Read The Verify Manifest Under `runs/verify/`

The verify manifest records the exact evidence set produced by one successful
`--verify` run.

Expected fields:

- `run_id`: must match `latest.json`, the preflight artifact, and the
  scorecard JSON.
- `created_at`: timestamp for the run.
- `candidate`: branch or release-candidate label.
- `verification_command`: currently `pytest -q`.
- `verification_summary`: final pytest summary, for example
  `432 passed in <duration>s`.
- `repo_root`: checkout used for the run.
- `preflight_artifact_path`: linked preflight JSON.
- `release_scorecard_json_path`: linked scorecard JSON.
- `release_scorecard_markdown_path`: linked scorecard Markdown.

For reviewer purposes, the manifest passes its first check when all referenced
paths exist and the linked files use the same `run_id`.

## How The Manifest Links To Preflight And Release-scorecard Artifacts

The manifest connects the operational evidence:

- `preflight_artifact_path` points to the offline demo preflight result for the
  run.
- `release_scorecard_json_path` points to the machine-readable readiness
  summary.
- `release_scorecard_markdown_path` points to the same scorecard in a
  human-readable format.

The preflight artifact tells the reviewer whether the committed offline demo
lane completed. The scorecard tells the reviewer whether that evidence is
enough for the current `Demo-ready` target under the existing rubric.

## How To Read The Preflight Artifact

In the preflight JSON, inspect:

- top-level `passed`: must be `true` for the current narrated demo gate.
- top-level `scenario_count`: expected to cover the committed offline fixture
  scenarios used by the current demo lane.
- top-level `run_id`: must match the verify manifest.
- each `scenarios[]` entry:
  - `case_key` and `intake_path`, to identify the scenario,
  - `availability.status`, which should be `offline-ready`,
  - `workflow_status`, which should be reviewable for demo use,
  - `workflow_review_required`, which may be `true` and means attorney review
    is still required,
  - `checks[]`, where any failed check should be treated as a demo blocker
    until reviewed,
  - `workflow_stage_statuses`, especially degraded citation or memo stages,
  - evidence, issue, memo, and export counts, which should be nonzero for
    reviewable output,
  - `export_eligibility` and `export_delivery_state`, to confirm the output is
    reviewable and not silently treated as final delivery.

The current repo can pass preflight while still marking scenarios
`workflow_review_required=true`. That is expected for this demo posture.
Review-required output is usable for human review, not verified legal advice.

## How To Read The Release-scorecard JSON And Markdown

Read the Markdown first for a reviewer-friendly summary, then check the JSON
for exact fields.

In the Markdown, inspect:

- `Evidence bundle`
- `CI Reporting Summary`
- `Reviewer Summary`
- `Dashboard Readiness Summary`
- `Offline Preflight`
- `Fixture Coverage`
- `Scenario Registry`
- `Threshold Calibration`
- quality dimension table
- `Must-pass gates`
- `Blocking gaps`
- `Decision`

In the JSON, inspect:

- `target_release_level`: should be `Demo-ready` for the current target.
- `decision`: should be read together with the blocking gates and posture.
- `preflight_artifact_path` and `preflight_summary`: tie the scorecard back to
  the live preflight artifact.
- `fixture_coverage` and `scenario_registry`: show current committed fixture
  and curated scenario coverage.
- `ci_reporting_summary`: CI/reporting field inventory for the existing verify
  bundle and scorecard artifacts. It maps artifact roles, run identity fields,
  reviewer-summary fields, and blocking/advisory readiness fields without
  adding a second readiness model.
- `reviewer_summary`: top-level reviewer convenience summary derived from the
  existing `readiness_posture`, blocking/advisory counts, and advisory gaps.
- `readiness_posture`: dashboard-oriented summary of blocking and advisory
  readiness.
- `calibration_thresholds`: Demo-ready fixture thresholds, all tagged
  `blocking`.
- `must_pass_gates`: Demo-ready gates, all tagged `blocking`.
- `dimensions`: rubric dimensions, tagged `advisory` for the current
  Demo-ready target.
- `blocking_gaps`: any explicit blocking gaps recorded by the scorecard.

The Markdown and JSON should tell the same story. If they diverge, use the JSON
as the machine-readable artifact and treat the divergence as a documentation or
rendering issue to fix before relying on the bundle.

## CI/Reporting Consumption Map

The scorecard JSON and Markdown now include `ci_reporting_summary`, a compact
inventory for CI/reporting consumers. It is a map of the existing bundle, not a
new readiness framework.

The expected artifact chain is:

| Consumer question | Artifact or field to read | Purpose |
|---|---|---|
| What is the newest successful verify run? | `runs/verify/latest.json` | Stable discovery pointer. |
| What artifacts belong to this run? | `verify_manifest_path` | Run-specific hub with the shared `run_id`, candidate, verification summary, preflight path, scorecard JSON path, and scorecard Markdown path. |
| Did the offline demo preflight pass? | `preflight_artifact_path` | Machine-readable preflight payload for the same run. |
| What machine-readable release posture should CI/reporting consume? | `release_scorecard_json_path` | Structured scorecard with `ci_reporting_summary`, `reviewer_summary`, `readiness_posture`, blocking gates, advisory dimensions, thresholds, and gaps. |
| What human-readable release posture should a reviewer read first? | `release_scorecard_markdown_path` | Markdown rendering of the same scorecard. |
| What concise human-review status should be surfaced? | `release_scorecard_json_path#reviewer_summary` | Convenience summary derived from `readiness_posture`. |

For blocking readiness, consume:

- `readiness_posture.blocking_metric_count`
- `readiness_posture.blocking_metric_failed_count`
- `readiness_posture.blocking_failures`
- `must_pass_gates[].readiness_category`
- `calibration_thresholds[].readiness_category`
- `blocking_gaps`

For advisory readiness, consume:

- `readiness_posture.advisory_metric_count`
- `readiness_posture.advisory_attention_count`
- `readiness_posture.advisory_gaps`
- `readiness_posture.pilot_readiness_gaps`
- `dimensions[].readiness_category`

These fields preserve the rubric's existing distinction between failed
blocking metrics and advisory gaps. They do not upgrade the repo beyond the
current guided/narrated `Demo-ready` target and should not be used to claim
Beta-ready, Pilot-ready, production-ready, self-serve UI readiness, or
client-facing legal-product readiness.

## How To Interpret `reviewer_summary`

`reviewer_summary` is a concise convenience summary over the existing
`readiness_posture` and rubric data. It is not a new readiness model and does
not rename release levels or change scoring thresholds.

Key fields:

- `target_release_level`: the stated scorecard target, currently `Demo-ready`.
- `demo_ready`: boolean convenience value derived from
  `readiness_posture.demo_ready`.
- `beta_ready`: currently `not claimed`.
- `pilot_ready`: mirrors `readiness_posture.pilot_ready`, currently
  `not claimed`.
- `release_ready`: mirrors the target-scoped
  `readiness_posture.release_ready` value.
- `blocking_failure_count`: mirrors
  `readiness_posture.blocking_metric_failed_count`.
- `advisory_attention_count`: mirrors
  `readiness_posture.advisory_attention_count`.
- `top_advisory_gaps`: the leading advisory attention areas derived from
  `readiness_posture.advisory_gaps`.
- `recommended_action`: short human-review guidance for the current target.
- `readiness_warning`: reminder not to claim Beta-ready, Pilot-ready, or
  production readiness from the current Demo-ready bundle.

## How To Interpret `readiness_posture`

`readiness_posture` is a compact summary for the existing rubric, not a new
rubric.

Key fields:

- `target_release_level`: the target being evaluated, currently `Demo-ready`.
- `demo_ready`: whether blocking metrics pass for the current demo target.
- `pilot_ready`: currently `not claimed`.
- `release_ready`: target-scoped release posture, for example
  `passes for Demo-ready target`.
- `blocking_metric_count`: count of blocking gates plus blocking calibration
  thresholds.
- `blocking_metric_failed_count`: number of blocking metrics that failed.
- `advisory_metric_count`: count of advisory dimensions.
- `advisory_attention_count`: advisory dimensions that need attention.
- `blocking_failures`: failures that block the target readiness claim.
- `advisory_gaps`: weaknesses to carry into roadmap, beta, or pilot work.
- `pilot_readiness_gaps`: reasons Pilot-ready is not claimed.

For a narrated demo, `blocking_metric_failed_count` should be `0`, and
`blocking_failures` should be empty. Advisory gaps can remain present, but they
should be acknowledged and tracked rather than used to claim a higher release
level.

## Blocking Vs Advisory Categories

Use the existing categories from
[`V2_RELEASE_RUBRIC.md`](V2_RELEASE_RUBRIC.md):

- `blocking`: a failed item blocks the target readiness claim.
- `advisory`: a weak item does not block the current target by itself, but it
  explains risk, roadmap priority, or why a higher readiness level is not
  claimed.

For the current `Demo-ready` target, blocking categories include:

- supported test path is green,
- offline demo lane completes,
- committed fixture coverage meets Demo-ready thresholds,
- required disclaimer language appears in outputs,
- no known blocker prevents a narrated end-to-end demo,
- memo remains readable enough for internal review,
- no quality dimension is scored `0`,
- fixture scenario count threshold,
- fixture state coverage threshold,
- module completeness threshold,
- issue breadth threshold,
- citation-check threshold.

Advisory categories include the seven rubric dimensions. Weak advisory
dimensions, such as Workflow Usability, Operational Readiness, or Security and
Governance, explain why the current repo should not claim Beta-ready or
Pilot-ready even when the Demo-ready blocking gates pass.

## Why Demo-ready Can Pass While Beta-ready And Pilot-ready Remain Not Claimed

The current repo is notebook-first and demo-scoped. It can pass `Demo-ready`
when the offline demo lane, tests, fixture thresholds, disclaimer posture, and
readability gates pass.

That does not satisfy `Beta-ready` because repeated internal use by
non-technical operators still needs more than the current notebook-first flow:
guided workflow surfaces, stronger evidence review surfaces, broader scenario
coverage, and operational support beyond the narrated demo path.

That also does not satisfy `Pilot-ready` because limited real-world attorney or
paralegal pilot use requires real human-review workflow, editing/export
provenance, measured benchmark and usability thresholds, security baseline,
observability, cost controls, and auditability after pilot runs.

The scorecard should therefore read as:

- `Demo-ready`: can pass for the current narrated demo target.
- `Beta-ready`: not claimed by the current evidence bundle.
- `Pilot-ready`: not claimed by the current repo.
- `release-ready`: release-ready for the stated target level only.

## Reviewer Checklist For Narrated Demo Readiness

Before presenting a narrated demo, confirm:

- `python -m war_room --verify` completed successfully.
- `runs/verify/latest.json` points to the intended candidate and run.
- the verify manifest exists and links to existing preflight and scorecard
  artifacts.
- manifest, preflight, and scorecard JSON share the same `run_id`.
- `verification_command` is `pytest -q` and `verification_summary` is passing.
- preflight top-level `passed` is `true`.
- each committed scenario has `availability.status=offline-ready`.
- each scenario's failed checks list is empty.
- memo disclaimer and review-required posture remain visible.
- scorecard `target_release_level` is `Demo-ready`.
- scorecard `readiness_posture.demo_ready` passes.
- scorecard `readiness_posture.pilot_ready` is `not claimed`.
- scorecard `readiness_posture.release_ready` is explicitly tied to the
  `Demo-ready` target.
- scorecard `blocking_metric_failed_count` is `0`.
- `blocking_gaps` is empty or explicitly resolved before demo use.
- advisory gaps are captured for roadmap, Beta-ready, or Pilot-ready work.

Any failed preflight check, failed pytest summary, missing artifact, mismatched
`run_id`, failed blocking gate, missing disclaimer evidence, or score of `0` in
a quality dimension blocks a clean narrated demo readiness claim until reviewed
and corrected.

## What Would Need To Change Before Beta-ready Or Pilot-ready Could Be Claimed

Before `Beta-ready` could be claimed, the evidence bundle would need to show
that the Beta-ready gates in
[`V2_RELEASE_RUBRIC.md`](V2_RELEASE_RUBRIC.md) are satisfied. That means real
guided workflow operation for non-technical users, first-class evidence review,
partial-success handling in product surfaces, broader scenario coverage,
stronger repeatable quality thresholds, and operational support beyond the
current narrated demo path.

Before `Pilot-ready` could be claimed, the repo would need real human review
workflow, provenance that survives editing and export, measured benchmark and
usability thresholds across representative scenarios, explicit security and
retention controls, observability and cost controls, and auditable pilot runs.

The current `pilot_readiness_gaps` field should be treated as advisory for the
current `Demo-ready` target and blocking for any future `Pilot-ready` claim.

## Non-goals

This guide does not add:

- a new readiness model,
- new scoring categories,
- renamed release levels,
- runtime behavior changes,
- CI workflow changes,
- a dashboard, frontend, or app shell,
- persistence, auth, queues, workers, production API, retries, or circuit
  breakers,
- fixture, cache sample, citation, prompt, schema, live retrieval, or notebook
  behavior changes,
- dependency changes,
- or a production-readiness claim.

The active runtime remains the notebook plus `src/war_room/`.
