# V2 Quality Rubric and Release Scorecard

Last updated: March 18, 2026

This document is the first-pass output of issue `#27`.

It defines a v0.1 quality rubric and release scorecard for CAT-Loss War Room so future work can be judged against one shared standard instead of ad hoc opinions.

This is intentionally a first pass. It should be refined as `#8` expands fixture coverage, `#9` expands CI gates, and `#19` produces pilot feedback.

Demo-ready threshold calibration is now explicit in the local scorecard workflow. CI and pilot operationalization remain open.

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
- any blocking gaps,
- and the final ship / no-ship decision.

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
- and the memo remains readable enough for internal review.

Recommended minimum scores:

- Reliability: `2`
- Trust and Provenance: `2`
- Review and Export Quality: `2`
- No dimension may be `0`

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

## 8) Current Baseline Snapshot (March 18, 2026)

This is the current scorecard entry using the rubric above.

Target release level: `Demo-ready`

| Dimension | Score | Verdict | Why |
|---|---:|---|---|
| Reliability | 3 | Strong | `236` tests pass on the supported bootstrap path, CI covers fresh-env plus `exa-py` compatibility, the offline fixture smoke gate is explicit, and the committed four-scenario FL/TX/LA lane still meets the calibrated demo-ready thresholds. |
| Evidence Quality | 2 | Acceptable | The committed four-scenario fixture set still satisfies explicit demo-ready thresholds for scenario count, state coverage, issue breadth, citation coverage, and module completeness. Broader scenario breadth and richer normalization still remain open under `#8`, `#12`, and `#13`. |
| Trust and Provenance | 2 | Acceptable | Disclaimers, source tiers, citation checks, evidence clusters, and claim/review trace links exist, but they are still notebook-era rather than full product workflow state. |
| Workflow Usability | 1 | Weak | The product is still notebook-first and generally engineer-driven for setup and operation. |
| Review and Export Quality | 2 | Acceptable | Memo/export trust signals are stronger and audit structures exist, but export quality is still not polished for repeated client-facing use. |
| Operational Readiness | 1 | Weak | Bootstrap and runtime boundaries are documented, fixture smoke is now explicit in CI, and local scorecards record fixture coverage, but broader observability and deployment lanes remain future work. |
| Security and Governance | 1 | Weak | Safety posture is disciplined for a demo, but production-grade controls are still roadmap items. |

Current verdict:

- Passes `Demo-ready`
- Does not pass `Beta-ready`
- Not close to `Pilot-ready`

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

### Blocking gaps
- 

### Decision
- Ship / No ship
```

## 9.5) Local Artifact Workflow

The rubric now has a lightweight local operational path.

After running the supported verification command, generate a scorecard artifact with:

```bash
python -m war_room.release_scorecard \
  --candidate local-demo \
  --verification-summary "236 passed"
```

Default verification command recorded in the artifact:

```bash
pytest -q
```

What this does now:

- writes Markdown and JSON scorecard artifacts into `runs/release_scorecards/`
- records the current demo-ready baseline in a repeatable format
- captures committed fixture coverage from `cache_samples/` so the scorecard reflects the live offline scenario set
- surfaces scenario-registry and offline-ready coverage alongside committed fixture coverage
- evaluates explicit demo-ready fixture thresholds inside the artifact
- runs in CI, validates the ship thresholds, and uploads the same artifact from the release-scorecard job
- creates a concrete artifact that later `#9` CI work can extend beyond the current demo-ready gate

What it does not do yet:

- replace broader CI-enforced evidence from `#9`
- replace pilot benchmark inputs from `#19`

## 10) What Should Improve This Rubric Next

This v0.1 rubric should be revised when the following land:

- `#8`: broader fixture and scenario coverage
- `#9`: expanded CI gates and stronger repeatable evidence for release claims, beyond artifact emission
- `#10` and `#11`: real product workflow surfaces
- `#12` and `#13`: better evidence normalization and case-law quality
- `#19`: pilot feedback and operator usability benchmarks

Likely next revisions:

- refine demo-ready thresholds with broader scenario coverage,
- add time-to-completion targets for the intended operator,
- add latency and cost targets once those are measured,
- and add pilot-specific reviewer signoff requirements.

## 11) Dependency Guidance

### For `#8`

Use this rubric to define which fixture suites must exist before Beta-ready can be claimed.

### For `#9`

Turn the repeatable portions of this scorecard into CI-enforced release evidence where practical.

### For `#10` and `#11`

Implement workflow surfaces that can actually satisfy the Beta-ready usability gates in this document.

### For `#19`

Use this rubric as the starting benchmark sheet for pilot evaluation rather than creating a second competing readiness framework.
