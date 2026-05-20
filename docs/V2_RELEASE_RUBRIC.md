# V2 Quality Rubric and Release Scorecard

Last updated: May 20, 2026

This document is the first-pass output of issue `#27`.

It defines a v0.1 quality rubric and release scorecard for CAT-Loss War Room so future work can be judged against one shared standard instead of ad hoc opinions.

This is intentionally a first pass. It should be refined as future fixture-breadth work is scoped and `#19` produces pilot feedback.

Demo-ready threshold calibration is now explicit in the local scorecard workflow. Issue `#9` CI quality-gate coverage is complete for the current acceptance criteria, while broader `#27` pilot operationalization remains open.

The current operationalization keeps the existing rubric and adds clearer reporting categories. Scorecard artifacts now distinguish blocking metrics from advisory metrics so local runs, CI artifacts, and future dashboards can consume the same readiness language without inventing a second rubric.

## 1) Purpose

The repo already has:

- a stable notebook-first demo,
- a cache-first offline lane,
- a written V2 workflow spec,
- a written V2 evidence-schema spec,
- and a growing typed-contract and retrieval boundary layer.

What it does not yet have is one canonical answer to:

- what counts as release-ready,
- which quality dimensions matter most,
- what evidence must exist before a release claim is credible,
- and how to compare current state against future targets.

This document supplies that baseline.

## 2) How to Use This Rubric

Use this rubric for three things:

- release-readiness decisions,
- roadmap prioritization,
- and benchmark discussions across engineering, product, and legal-review work.

Every release candidate should produce a scorecard entry with:

- the target release level,
- the score for each dimension,
- the evidence used to justify each score,
- the category for each metric (`blocking` or `advisory`),
- any blocking gaps,
- and the final ship / no-ship decision.

Use these categories consistently:

| Category | Meaning | Current artifact fields |
|---|---|---|
| `blocking` | A failed item blocks the target readiness claim. | `must_pass_gates`, `calibration_thresholds`, and the no-0-dimension gate |
| `advisory` | A weak item does not block the current target by itself, but it explains risk, roadmap priority, or why a higher readiness level is not claimed. | `dimensions`, scenario/fixture coverage summaries, preflight details, and pilot-readiness gaps |

For this repo, `release-ready` is not a separate fourth maturity level. It means "ready to ship for the target release level named in the scorecard." A candidate can be release-ready for `Demo-ready` while still not being `Pilot-ready`.

## 3) Release Levels

### Demo-ready

Suitable for a narrated or guided demonstration.

Expected characteristics:

- stable offline lane,
- no hard crashes in the primary flow,
- readable memo output,
- clear disclaimer language,
- and enough trust signaling that an attorney understands the output is research support, not legal advice.

### Beta-ready

Suitable for repeated internal use by non-technical operators with engineering support available but not required for routine runs.

Expected characteristics:

- guided workflow beyond notebook-only usage,
- canonical evidence and review surfaces,
- partial-success handling,
- broader scenario coverage,
- measurable quality thresholds,
- and stronger CI and observability.

### Pilot-ready

Suitable for limited real-world attorney or paralegal pilot use with explicit governance.

Expected characteristics:

- review workflow is real,
- provenance survives editing and export,
- security and retention controls are defined,
- operational behavior is measurable,
- and benchmark plus usability thresholds are consistently met.

### Release-ready posture

The scorecard's release-ready posture answers whether the candidate satisfies the blocking metrics for its stated target release level. It should always be read with the target level. For example, the current baseline can pass release-ready posture for a controlled demo while still reporting `Pilot-ready: not claimed`.

## 4) Scoring Scale

Use a 0-3 scale for each dimension.

| Score | Label | Meaning |
|---|---|---|
| 0 | Blocked | Missing, unsafe, or clearly below minimum acceptable quality |
| 1 | Weak | Directionally present but not dependable enough to claim readiness |
| 2 | Acceptable | Good enough for the target release level if no must-pass gate is violated |
| 3 | Strong | Clearly dependable and a positive proof point for the target release level |

A high average does not override a failed must-pass gate.

## 5) Quality Dimensions

### 1. Reliability

What this measures:

- supported test path stays green,
- primary workflow completes without hard failure in the intended lane,
- and partial failures degrade clearly rather than collapsing silently.

Evidence to use:

- `pytest` results,
- fixture-run results,
- CI history,
- reproducible local smoke checks.

### 2. Evidence Quality

What this measures:

- retrieved support is relevant,
- noisy or generic pages are filtered well enough,
- and evidence clustering or grouping helps review instead of obscuring quality.

Evidence to use:

- fixture comparisons,
- representative output review,
- issue-level evidence inspection,
- false-positive / low-value example tracking.

### 3. Trust and Provenance

What this measures:

- important output can be traced back to sources,
- uncertainty is visible,
- disclaimers remain intact,
- and review-required states are not hidden.

Evidence to use:

- memo output review,
- evidence-to-claim links,
- audit-bundle coverage,
- citation-check behavior.

### 4. Workflow Usability

What this measures:

- the intended operator can move through the workflow with minimal engineering help,
- the system explains its state clearly,
- and failure or degraded states remain understandable.

Evidence to use:

- guided-run observations,
- onboarding friction review,
- user walkthrough timing,
- setup and handoff clarity.

### 5. Review and Export Quality

What this measures:

- the memo is reviewable,
- review-required issues remain visible,
- export artifacts preserve trust context,
- and the result is usable as attorney work product input.

Evidence to use:

- export review,
- review-log inspection,
- appendix quality,
- attorney-facing readability checks.

### 6. Operational Readiness

What this measures:

- runtime boundaries are understandable,
- release behavior is observable enough to debug,
- and environment, artifact, and retention expectations are explicit enough for the target level.

Evidence to use:

- environment/bootstrap docs,
- run-state visibility,
- artifact boundaries,
- operational checklists.

### 7. Security and Governance

What this measures:

- legal disclaimers stay intact,
- sensitive handling rules are explicit,
- and external-model or retrieval behavior does not outrun current controls.

Evidence to use:

- safety docs,
- secrets handling,
- redaction expectations,
- access / retention policy docs where applicable.

## 6) Must-Pass Gates By Release Level

### Demo-ready gates

Must pass all of the following:

- supported test path is green,
- offline demo lane completes,
- committed fixture coverage meets the demo-ready calibration threshold,
- required disclaimer language appears in outputs,
- no known blocker prevents a narrated end-to-end demo,
- memo remains readable enough for internal review,
- and no quality dimension is scored `0`.

Advisory score guidance:

- Reliability: `2`
- Trust and Provenance: `2`
- Review and Export Quality: `2`

Scores below these advisory levels explain risk and future work. A score of `0` is blocking because it means the dimension is missing, unsafe, or clearly below minimum quality.

### Beta-ready gates

Must pass all of the following:

- a non-technical operator can complete the core guided workflow,
- evidence review exists as a first-class surface,
- partial-success handling is real,
- multi-scenario fixture coverage exists,
- CI enforces more than a single unit-test lane,
- and release scorecard evidence is generated from repeatable checks.

Recommended minimum scores:

- Reliability: `2`
- Evidence Quality: `2`
- Trust and Provenance: `2`
- Workflow Usability: `2`
- Review and Export Quality: `2`
- Operational Readiness: `2`
- Security and Governance: `1`

### Pilot-ready gates

Must pass all of the following:

- human review workflow is real,
- provenance survives editing and export,
- benchmark and usability thresholds are measured across representative scenarios,
- security baseline is explicit,
- observability and cost controls exist,
- and pilot runs can be audited after the fact.

The current scorecard may list pilot-readiness gaps, but it should not claim to satisfy these gates until `#19` pilot validation, `#26` human review workflow, and the relevant operational/security controls exist. Listing those gaps is advisory for the current demo-ready target; resolving them is blocking for any future pilot-ready claim.

Recommended minimum scores:

- Reliability: `3`
- Evidence Quality: `2`
- Trust and Provenance: `3`
- Workflow Usability: `2`
- Review and Export Quality: `2`
- Operational Readiness: `2`
- Security and Governance: `2`

## 7) Demo-Ready Calibration Thresholds

The local scorecard now evaluates demo-ready fixture calibration against the following minimum thresholds:

- committed scenario count: `>= 3`
- state coverage: `>= 3`
- every scenario includes all four module fixtures (`weather`, `carrier`, `caselaw`, `citation_verify`)
- every scenario includes at least `2` case-law issue buckets
- every scenario includes at least `3` citation checks

These thresholds are intentionally scoped to the current demo-ready release level. Beta-ready and Pilot-ready still need broader scenario coverage, stronger output-quality measures, and CI or pilot evidence beyond the local scorecard.

The committed fixture lane now also has a deterministic golden snapshot check:

```bash
python -m war_room.fixture_snapshots --check
```

That `#8` gate compares `tests/golden/offline_fixture_snapshots.json` against the current offline preflight and committed fixture payloads. It checks scenario coverage metadata, source mix, case count, citation summary consistency, memo section structure, workflow state, evidence/issue read-model counts, and export posture, and now feeds the completed `#9` categorized CI gate stack.

The curated scenario registry now has five offline-ready fixture-backed benchmarks: Milton/Pinellas/Citizens, Ian/Lee/Citizens HO-3, Ida/Orleans/Lloyd's, Texas hail/Tarrant/Allstate HO-B, and Texas hail/Tarrant/Allstate DP-3.

Use `docs/FIXTURE_SEEDING.md` for future fixture promotions. Offline-ready registry scenarios must have a `fixture_case_key` and a complete committed fixture bundle; tests enforce that lightweight guard so live-only or intake-only scenarios are not accidentally treated as cache-only demo paths.

## 8) Current Baseline Snapshot (May 18, 2026)

This is the current scorecard entry using the rubric above.

Target release level: `Demo-ready`

| Dimension | Score | Verdict | Why |
|---|---:|---|---|
| Reliability | 3 | Strong | `432` tests pass on the supported verify path, CI covers fresh-env plus `exa-py` compatibility plus offline fixture smoke/golden snapshot validation, offline e2e demo validation, offline security and dependency hygiene, and release-scorecard artifact validation, and the committed five-scenario FL/TX/LA lane still meets the calibrated demo-ready thresholds. |
| Evidence Quality | 2 | Acceptable | The committed five-scenario fixture set still satisfies explicit demo-ready thresholds for scenario count, state coverage, issue breadth, citation coverage, module completeness, source mix, output structure, and citation-summary consistency, with all five fixture lanes now represented as offline-ready curated registry scenarios. Broader scenario breadth and richer normalization still remain open under `#12` and `#13`; any additional Florida fixture seeding should be scoped by maintainers as follow-up work after the completed `#8` baseline. |
| Trust and Provenance | 2 | Acceptable | Disclaimers, source tiers, citation checks, evidence clusters, and claim/review trace links exist, but they are still notebook-era rather than full product workflow state. |
| Workflow Usability | 1 | Weak | The product is still notebook-first and generally engineer-driven for setup and operation, but the notebook/preflight path now exposes a first workflow layer with research-plan preview, cluster-first evidence-board summary, issue-workspace summary, memo-composer readiness, export-history posture, and explicit run-stage review states. |
| Review and Export Quality | 2 | Acceptable | Memo/export trust signals are stronger and audit structures exist, but export quality is still not polished for repeated client-facing use. |
| Operational Readiness | 1 | Weak | Bootstrap and runtime boundaries are documented, fixture smoke is explicit in CI, and the supported verify path now emits linked preflight, scorecard, manifest, and latest-pointer artifacts, but broader observability and deployment lanes remain future work. |
| Security and Governance | 1 | Weak | Safety posture is disciplined for a demo, and offline repo hygiene gates now check env/secrets/artifact policy drift plus dependency pinning and dependency-file drift, but production-grade controls and live vulnerability scanning are still roadmap items under `#18`. |

Current verdict:

- Passes `Demo-ready`
- Does not pass `Beta-ready`
- Not close to `Pilot-ready`

Current dashboard posture:

- Blocking demo-ready metrics pass when the supported verification command, offline preflight lane, demo calibration thresholds, disclaimer/readability gates, and no-0-dimension gate pass.
- Advisory metrics still show weak Workflow Usability, Operational Readiness, and Security and Governance scores.
- Pilot-ready is explicitly `not claimed`; the artifact lists pilot-readiness gaps without designing or executing a pilot study.
- Release-ready means "passes for the Demo-ready target," not ready for beta, pilot, or production use.

Why the current build still counts as demo-ready:

- it is stable,
- it is honest about uncertainty,
- it runs offline,
- and it produces a reviewable research memo without pretending to be a self-serve product.

## 9) Scorecard Template

Use this template for future release candidates.

```md
## Release Scorecard

- Date:
- Candidate / branch:
- Target release level:
- Evaluator(s):
- Evidence bundle:

| Dimension | Score (0-3) | Evidence | Notes |
|---|---:|---|---|
| Reliability |  |  |  |
| Evidence Quality |  |  |  |
| Trust and Provenance |  |  |  |
| Workflow Usability |  |  |  |
| Review and Export Quality |  |  |  |
| Operational Readiness |  |  |  |
| Security and Governance |  |  |  |

### Must-pass gates
- [ ] Gate 1
- [ ] Gate 2
- [ ] Gate 3

### Reviewer summary
- Target release level:
- Demo-ready posture:
- Beta-ready posture:
- Pilot-ready posture:
- Release-ready posture:
- Blocking failures:
- Advisory attention areas:
- Top advisory gaps:
- Recommended reviewer action:
- Readiness reminder:

### Dashboard readiness summary
- Blocking metrics:
- Advisory metrics needing attention:
- Demo-ready posture:
- Pilot-ready posture:
- Release-ready posture:

### Blocking gaps
- 

### Decision
- Ship / No ship
```

## 9.5) Local Artifact Workflow

The rubric now has a lightweight local operational path.

The supported verification command now writes a paired scorecard artifact automatically:

```bash
python -m war_room --verify
```

Human reviewer guidance for this verify bundle lives in
[`ISSUE_27_RELEASE_EVIDENCE_REVIEW_GUIDE.md`](ISSUE_27_RELEASE_EVIDENCE_REVIEW_GUIDE.md).
That guide explains how to inspect `runs/verify/latest.json`, the run-specific
verify manifest, preflight artifacts, and release-scorecard JSON/Markdown while
preserving this rubric as the only readiness model.

Optional candidate override for local release evidence:

```bash
python -m war_room --verify --release-candidate local-demo
```

What this does now:

- runs the deterministic offline preflight and the supported `pytest -q` path
- writes Markdown and JSON scorecard artifacts into `runs/release_scorecards/`
- writes the underlying machine-readable offline preflight payload into `runs/preflight/`
- writes a `ci_reporting_summary` inventory in the scorecard JSON/Markdown so CI/reporting consumers can find the verify pointer, verify manifest, preflight artifact, scorecard JSON, scorecard Markdown, `reviewer_summary`, and blocking/advisory readiness fields without creating a second readiness model
- writes a top-level `reviewer_summary` convenience summary over the existing `readiness_posture`, rubric dimensions, and blocking/advisory counts; this is not a new scoring framework
- writes a machine-readable `readiness_posture` summary with blocking/advisory counts, demo-ready status, pilot-ready status, release-ready status, blocking failures, advisory gaps, and pilot-readiness gaps
- renders a matching `Reviewer Summary` section before the deeper dashboard readiness details in the Markdown scorecard
- tags gates, calibration thresholds, and scored dimensions with `readiness_category` fields so dashboard consumers do not have to infer blocking versus advisory behavior from display text
- assigns a shared run id to the preflight and scorecard artifacts so repeated same-day verify runs do not overwrite each other
- writes a verify-run manifest into `runs/verify/` that points to the exact preflight and scorecard artifacts for that run
- refreshes `runs/verify/latest.json` so downstream tooling can discover the newest successful verify run without scanning filenames
- records the current demo-ready baseline in a repeatable format from the same supported local verification command
- records the live offline preflight result in the scorecard artifact, so the offline-lane gate is tied to the actual `--verify` run rather than fixture coverage alone
- records that shared run id and the preflight artifact path in the scorecard JSON/Markdown so release evidence can be traced back to the exact offline run
- captures committed fixture coverage from `cache_samples/` so the scorecard reflects the live offline scenario set
- surfaces scenario-registry and offline-ready coverage alongside committed fixture coverage
- evaluates explicit demo-ready fixture thresholds inside the artifact
- can be paired with `python -m war_room.fixture_snapshots --check` for the committed golden fixture snapshot and stricter `#8` quality assertions
- runs in CI, validates the ship thresholds, and uploads the same artifact from the release-scorecard job
- wraps CI gates with `python -m war_room.quality_gates` so unit, offline fixture, offline e2e, golden snapshot, Exa compatibility, release-scorecard, security-hygiene, and dependency-hygiene failures produce categorized JSON, Markdown, and log artifacts
- creates concrete release evidence that future `#27`, `#19`, and pilot-readiness work can extend beyond the current demo-ready gate

Manual and CI-specific scorecard generation still remains available with:

```bash
python -m war_room.release_scorecard \
  --candidate local-demo \
  --verification-summary "432 passed"
```

What it does not do yet:

- replace pilot benchmark inputs from `#19`

## 10) What Should Improve This Rubric Next

This v0.1 rubric should be revised when the following land:

- Additional fixture breadth only if maintainers scope it as follow-up work after the completed `#8` baseline
- `#10`: remaining product/API work beyond the landed contracts/service/status/transport/dev-HTTP slices
- `#11`: real product workflow surfaces beyond the landed UX specs/previews
- `#12` and `#13`: better evidence normalization and case-law quality
- `#19`: pilot feedback and operator usability benchmarks

Likely next revisions:

- refine demo-ready thresholds with broader scenario coverage,
- add time-to-completion targets for the intended operator,
- add latency and cost targets once those are measured,
- and add pilot-specific reviewer signoff requirements.

## 11) Dependency Guidance

### For Completed `#8` and Future Fixture Breadth

Issue `#8` is complete and closed at the five-lane offline fixture baseline. Use this rubric, `docs/FIXTURE_SEEDING.md`, and the committed golden fixture snapshot gate to define any future fixture suites that must exist before Beta-ready can be claimed.

### For `#9`

Issue `#9` is complete for the current CI quality-gate scope. Use `docs/ISSUE_9_CLOSEOUT_AUDIT.md` as the evidence map for the landed unit, fixture, golden snapshot, offline e2e, Exa compatibility, release-scorecard, security hygiene, and dependency hygiene gates.

### For `#10` and `#11`

Treat the current issue `#10` work as landed contracts/service/status/transport/dev-HTTP slices, not a production API. Treat the current issue `#11` work as specs/previews only, not a shipped web UI. Future implementation should add workflow surfaces that can actually satisfy the Beta-ready usability gates in this document.

### For `#19`

Use this rubric as the starting benchmark sheet for pilot evaluation rather than creating a second competing readiness framework.
