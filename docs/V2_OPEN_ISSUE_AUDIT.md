# V2 Open Issue Audit

Date: May 18, 2026

Purpose: classify the open CAT-Loss War Room V2 GitHub issues against current
repo truth before any issue-body edits, issue closures, new issues, or runtime
implementation work.

This is a docs-only audit. It does not edit GitHub issue bodies, close issues,
create issues, change runtime code, change CI, add dependencies, or expand the
repo into a production API, web app, auth system, persistence layer, queue,
worker, dashboard, beta, pilot, or production surface.

## Current Repo Truth Used For This Audit

- Active runtime is still `notebooks/01_case_war_room.ipynb` plus
  `src/war_room/`.
- `apps/`, `workers/`, and `packages/` remain future-boundary placeholders, not
  active runtime surfaces.
- Current readiness language is limited to a guided or narrated `Demo-ready`
  posture. Do not claim Beta-ready, Pilot-ready, production-ready,
  self-serve UI readiness, or client-facing readiness without attorney review.
- Issue `#10` has landed narrow contracts/service/status/transport/dev-HTTP
  slices:
  - `src/war_room/orchestration.py`
  - `src/war_room/orchestration_api_contracts.py`
  - `src/war_room/orchestration_service.py`
  - `src/war_room/orchestration_status_view.py`
  - `src/war_room/orchestration_transport.py`
  - `src/war_room/orchestration_http.py`
- The current `#10` stack is dependency-free, process-local, offline-first, and
  dev-only at the HTTP layer. It is not a production API service.
- Issue `#11` has documentation-only guided-intake and run-status UX specs plus
  deterministic Milton previews. It has no shipped frontend.
- Issue `#27` has the rubric, local verify bundle, linked scorecard artifacts,
  blocking/advisory readiness fields, human reviewer guide, and top-level
  `reviewer_summary` convenience layer. Broader CI and pilot operationalization
  remain open.
- Issues `#6` through `#9`, `#22`, `#23`, and `#24` are complete or closed in
  the repo's current planning docs. Their outputs should be treated as source
  contracts, not proof that the V2 product runtime exists.

## Priority Labels

- `P0`: clean up before more broad V2 execution.
- `P1`: next narrow execution candidate after body cleanup.
- `P2`: important, but should wait for the preceding contract or evidence
  layer.
- `P3`: defer until product surfaces, review workflow, or operational evidence
  exists.
- `P4`: keep parked until a later maturity level.

## Issue Classification Summary

| Issue | Current title | Recommendation | Priority |
|---|---|---|---|
| `#3` | V2 Epic: Rebuild CAT-Loss War Room as a trustworthy product platform | Keep as umbrella, rewrite body | P0 |
| `#10` | Build orchestration API with run state machine and graceful degradation | Rewrite body, split into child issues | P1 |
| `#11` | Ship V2 web intake wizard and run-status UX | Rewrite body, split into child issues | P1 |
| `#12` | Implement evidence normalization and deduplication on top of canonical schema | Split into child issues | P1 |
| `#13` | Caselaw quality v2: relevance ranking, case-only filtering, structured extraction | Split into child issues | P2 |
| `#14` | Citation verification v2: ambiguity detection, official-source preference, audit trail | Defer, split into child issues | P3 |
| `#15` | Memo workspace v2: editable sections, evidence links, and clean exports | Defer, split into child issues | P3 |
| `#16` | Firm memory v1: governed knowledge store with provenance and review workflow | Defer | P4 |
| `#17` | Observability and operations: run traces, quality metrics, and cost budgets | Rewrite body, defer | P3 |
| `#18` | Security baseline: PII redaction, secrets policy, data retention, and access control | Defer, split into child issues | P3 |
| `#19` | Pilot validation: attorney usability study and quality benchmark reporting | Defer, rewrite body later | P4 |
| `#25` | Build evidence-linked AI extraction and drafting guardrails plus eval harness | Defer, split into child issues | P2 |
| `#26` | Design human review workflow: approvals, revisions, and provenance-preserving edits | Split into child issues | P2 |
| `#27` | Define V2 quality rubric, benchmark suite, and release scorecard | Keep as umbrella, rewrite body, split into child issues | P0 |

## Stale Or Dangerous Issue Bodies

These issue bodies are most likely to mislead a future agent into broad
implementation:

- `#3`: still frames a ground-up product-platform rebuild. Keep the epic, but
  add current runtime truth and the narrow execution rule.
- `#10`: still asks for an API service, retries, and circuit breakers without
  acknowledging the landed contract/service/status/transport/dev-HTTP ladder.
- `#11`: still says "Ship V2 web intake wizard" even though current repo truth
  is specs and previews only.
- `#17`: asks for dashboards, alerts, traces, and cost budgets. Some local
  artifacts and scorecard fields exist, but no observability system or operator
  dashboard exists.
- `#18`: includes access control and enforceable retention. Current security
  work is offline repo hygiene, not product security.
- `#27`: has been partially updated, but should now mention the issue `#88`
  `reviewer_summary` layer and keep the remaining scope to broader CI/pilot
  operationalization.

## Recommended Next 5 Child Issues

These are the highest-value issue-creation candidates after this audit. They
are phrased as narrow child issues to avoid umbrella implementation.

1. `#27` child: Broaden release-evidence CI reporting from the existing verify
   bundle without changing readiness levels.
   - Purpose: map the current local/CI artifacts to the next reportable CI
     evidence slice.
   - Non-goals: no pilot claim, no dashboard, no new rubric, no runtime change.
2. `#10` child: Remaining orchestration scope map after landed
   contracts/service/status/transport/dev-HTTP slices.
   - Purpose: update issue `#10` with what is landed, what remains, and what
     must be explicitly deferred.
   - Non-goals: no production API, persistence, queues, auth, retries, circuit
     breakers, workers, or dashboard.
3. `#11` child: Split guided-intake and run-status into contract seam vs future
   UI implementation.
   - Purpose: keep current `status_presentation` and strict intake payload as
     the contract seam before any frontend work.
   - Non-goals: no React, Next.js, dashboard, app shell, auth, persistence, or
     production API.
4. `#12` child: Implement one canonical evidence adapter over existing module
   output with durable provenance IDs.
   - Purpose: start evidence normalization from one narrow existing payload
     path and tests.
   - Non-goals: no database, no global schema rewrite, no AI scoring, no live
     retrieval.
5. `#13` or `#14` child: Add a fixture-backed false-positive and ambiguity
   regression set for case-law and citation quality.
   - Purpose: make noisy authority and ambiguous citation behavior measurable
     before broader ranking or verifier changes.
   - Non-goals: no new provider, no live search requirement, no unsupported
     verification claim.

## Issue-by-Issue Audit

### Issue `#3`

- Current title: `V2 Epic: Rebuild CAT-Loss War Room as a trustworthy product platform`
- Current purpose: umbrella epic for the V2 program, including architecture,
  UX, testing, reliability, security, and pilot validation.
- Current-state mismatch: the body still reads like a broad product-platform
  rebuild charter. Since it predates much of the current repo truth, it does
  not reflect completed definition/foundation issues, the landed narrow `#10`
  slices, the specs-only `#11` state, the issue `#88` scorecard summary, or the
  rule that active runtime remains notebook plus `src/war_room/`.
- Recommended action: keep as umbrella; rewrite body.
- Suggested child issues:
  - Link this audit from the epic after review.
  - Add explicit child links for the next `#27`, `#10`, `#11`, and `#12`
    slices.
- Recommended priority: `P0` governance cleanup.
- Explicit non-goals / overclaiming language to avoid:
  - Do not call the current repo a product platform.
  - Do not imply self-serve legal-team readiness.
  - Do not claim beta, pilot, production, SaaS, auth, persistence, queues,
    workers, dashboards, or a real web app.

### Issue `#10`

- Current title: `Build orchestration API with run state machine and graceful degradation`
- Current purpose: move orchestration out of notebook-only flow; define run
  states; preserve partial results; eventually support API tracking,
  retries, and circuit-breaker behavior.
- Current-state mismatch: the issue body does not acknowledge the landed ladder:
  run-state contract, typed API boundary contracts, in-process offline service,
  operator-facing status presentation, thin transport wrapper, and dev-only
  standard-library HTTP adapter. The body still points directly at an "API
  service" plus retries and circuit breakers, which is too broad for the
  current repo.
- Recommended action: rewrite body; split into child issues.
- Suggested child issues:
  - Remaining-scope map for `#10` after the landed slices.
  - Contract test hardening for accepted failed runs vs transport errors.
  - Cancellation and idempotency policy spec using the existing state
    vocabulary.
  - Retry/circuit-breaker policy note before any implementation.
  - Production API decision record, if maintainers later authorize a framework.
- Recommended priority: `P1`, after the `#27` governance cleanup.
- Explicit non-goals / overclaiming language to avoid:
  - Do not say the repo has a production API.
  - Do not implement FastAPI, Flask, Streamlit, Django, Next.js, React, queues,
    persistence, auth, sessions, retries, circuit breakers, workers, or
    dashboard behavior from this body.
  - Do not invent a second run or stage vocabulary.

### Issue `#11`

- Current title: `Ship V2 web intake wizard and run-status UX`
- Current purpose: implement guided intake and run-status UX for non-technical
  legal users, shaped by workflow issue `#23` and orchestration issue `#10`.
- Current-state mismatch: the current repo has docs-only guided-intake and
  run-status specs plus deterministic Milton previews. No frontend, dashboard,
  app shell, production API, auth, or persistence exists. The title is now
  dangerous because "Ship V2 web..." sounds implementation-ready.
- Recommended action: rewrite body; split into child issues.
- Suggested child issues:
  - Contract seam for guided intake using the strict current runtime payload.
  - Contract seam for run-status UX using `status_presentation` and
    `payload.timeline.stages`.
  - Future UI implementation issue, explicitly blocked on an app boundary and
    maintainers' authorization.
  - Future legal-user usability test script, after a real UI exists.
- Recommended priority: `P1`, but only as contract-splitting before UI work.
- Explicit non-goals / overclaiming language to avoid:
  - Do not claim a shipped web UI.
  - Do not add React, Next.js, dashboard, app shell, auth, persistence,
    production API, uploads, OCR, queues, workers, retries, or circuit breakers
    under this issue without explicit approval.
  - Do not call intake output verified, approved, final, litigation-ready, or
    legally sufficient.

### Issue `#12`

- Current title: `Implement evidence normalization and deduplication on top of canonical schema`
- Current purpose: implement evidence normalization, dedupe, provenance links,
  confidence annotations, and rationale fields on top of the evidence schema
  from `#24`.
- Current-state mismatch: the repo already has transitional evidence clusters,
  evidence-to-claim links, review events, and read models, but the full
  canonical evidence normalization engine from `#12` is not implemented.
  The issue is directionally valid but too broad as a first implementation
  ticket.
- Recommended action: split into child issues.
- Suggested child issues:
  - One canonical adapter for one existing module output.
  - Durable evidence and cluster ID rules applied to current audit output.
  - URL/citation dedupe regression tests over the five fixture lanes.
  - Provenance links from memo claims to evidence clusters in one export path.
- Recommended priority: `P1`, first true product-core implementation after
  `#10`/`#11` cleanup.
- Explicit non-goals / overclaiming language to avoid:
  - Do not add a database or persistence layer as part of the first slice.
  - Do not claim the canonical V2 evidence graph is fully implemented.
  - Do not replace deterministic source scoring with ML scoring.
  - Do not require live retrieval for validation.

### Issue `#13`

- Current title: `Caselaw quality v2: relevance ranking, case-only filtering, structured extraction`
- Current purpose: reduce non-case entries, improve relevance ranking, improve
  court/year/citation extraction, and add tests for false positives and
  ambiguous pages.
- Current-state mismatch: some case-law hardening already exists, including
  commentary filtering, duplicate authority collapse, primary-authority
  preference, and metadata cleanup. The broader measurable quality program is
  still open.
- Recommended action: split into child issues.
- Suggested child issues:
  - Fixture-backed false-positive regression set for commentary-like authority
    rows.
  - Structured metadata confidence audit for court/year/citation extraction.
  - Issue-aware ranking metric over existing offline scenarios.
- Recommended priority: `P2`, after the first `#12` adapter slice or alongside
  it if scoped to tests only.
- Explicit non-goals / overclaiming language to avoid:
  - Do not use live search as a required test path.
  - Do not claim case-law precision is solved across jurisdictions.
  - Do not use ML scoring unless explicitly approved.

### Issue `#14`

- Current title: `Citation verification v2: ambiguity detection, official-source preference, audit trail`
- Current purpose: harden citation checks with ambiguity handling,
  official-source preference, review cues, and audit trail.
- Current-state mismatch: current citation status is `verified`,
  `uncertain`, and `not_found`, with stable display badges of `verified`,
  `warning`, and `not_found`. Current code also records `status_reason`,
  primary-authority signals, conflicting-hit uncertainty, and review events.
  The richer issue-body vocabulary of `likely`, `ambiguous`, and `error`, plus
  persisted citation check audit events, is not implemented.
- Recommended action: defer; split into child issues.
- Suggested child issues:
  - Citation status vocabulary decision note before changing payloads.
  - Ambiguous citation fixture and regression test set.
  - Official-source preference hardening over existing cached checks.
  - Citation-check audit event mapping into the current review/event graph.
- Recommended priority: `P3`, after `#13` and an evidence-normalization slice.
- Explicit non-goals / overclaiming language to avoid:
  - Do not call citation spot-checks legal verification.
  - Do not change status vocabulary in cache fixtures without a migration plan.
  - Do not require live citation retrieval in tests.

### Issue `#15`

- Current title: `Memo workspace v2: editable sections, evidence links, and clean exports`
- Current purpose: provide section-level editing, evidence-linked statements,
  readable legal output, and optional docx/pdf export.
- Current-state mismatch: the current repo has Markdown export, evidence
  clusters, memo claims, review-required export posture, Memo Composer read
  models, and Export History read models. It does not have an editable memo
  workspace, revision history, UI, docx/pdf export workflow, or provenance
  survival after edits.
- Recommended action: defer; split into child issues.
- Suggested child issues:
  - Memo-section review contract tied to `#26`.
  - Export provenance preservation test for Markdown only.
  - Future docx/pdf export decision note after the editable workflow exists.
- Recommended priority: `P3`, after `#26`.
- Explicit non-goals / overclaiming language to avoid:
  - Do not claim client-facing export quality.
  - Do not add a frontend editor, document store, docx/pdf pipeline, or
    approval workflow under a single broad issue.
  - Do not strip disclaimers or review-required markers from export output.

### Issue `#16`

- Current title: `Firm memory v1: governed knowledge store with provenance and review workflow`
- Current purpose: build a governed, versioned, provenance-aware firm-memory
  store integrated into planning and drafting.
- Current-state mismatch: no governed memory store exists in the current code.
  The V2 blueprint explicitly says to delay firm memory until provenance,
  review workflow, and security baseline are stronger.
- Recommended action: defer.
- Suggested child issues:
  - None yet. Create child issues only after `#12`, `#18`, and `#26` establish
    provenance, security, and review workflow requirements.
- Recommended priority: `P4`.
- Explicit non-goals / overclaiming language to avoid:
  - Do not add firm memory to the notebook demo as a platform narrative.
  - Do not mix unreviewed memory into high-confidence output.
  - Do not add a database, vector store, external memory provider, or AI memory
    layer without an explicit security/review contract.

### Issue `#17`

- Current title: `Observability and operations: run traces, quality metrics, and cost budgets`
- Current purpose: add run-level tracing, metrics, thresholds/alerts, and an
  operator dashboard for quality, reliability, latency, and cost.
- Current-state mismatch: current repo has run-scoped verify artifacts,
  release scorecard outputs, quality-gate artifacts, run/status payloads, and
  offline preflight artifacts. It does not have live observability, alerts,
  cost budgets, a dashboard, or production operations.
- Recommended action: rewrite body; defer.
- Suggested child issues:
  - Local artifact inventory and metric naming over existing verify/preflight
    outputs.
  - Cost/latency field contract only after real measurements exist.
  - Future observability/dashboard issue only after a production runtime is
    authorized.
- Recommended priority: `P3`.
- Explicit non-goals / overclaiming language to avoid:
  - Do not build a dashboard now.
  - Do not claim production observability.
  - Do not add external telemetry, alerts, cloud services, or cost tracking
    without a real runtime boundary and explicit approval.

### Issue `#18`

- Current title: `Security baseline: PII redaction, secrets policy, data retention, and access control`
- Current purpose: define and implement PII handling, secrets policy,
  retention/deletion rules, and role-aware access controls.
- Current-state mismatch: offline security hygiene and documented secrets/cache
  policies exist, but product security controls do not. There is no access
  model, auth, persistence, retention enforcement, or pre-retrieval PII
  redaction pipeline for a product runtime.
- Recommended action: defer; split into child issues.
- Suggested child issues:
  - Docs-only security scope map separating demo hygiene from product controls.
  - PII redaction contract for future intake/retrieval boundaries.
  - Retention policy for `cache/`, `output/`, and `runs/` artifacts.
  - Access-control requirements after a product surface is authorized.
- Recommended priority: `P3`.
- Explicit non-goals / overclaiming language to avoid:
  - Do not add auth or access control before an app/runtime boundary exists.
  - Do not claim product compliance from offline hygiene gates.
  - Do not make live provider calls or mutate fixture data for security tests.

### Issue `#19`

- Current title: `Pilot validation: attorney usability study and quality benchmark reporting`
- Current purpose: define and run pilot validation with legal users, benchmark
  scenarios, metrics, reports, and backlog updates.
- Current-state mismatch: the current repo is guided/narrated demo-ready only.
  It has no shipped self-serve workflow, no pilot protocol execution, no
  attorney usability study, and no measured pilot thresholds.
- Recommended action: defer; rewrite body later.
- Suggested child issues:
  - Pilot readiness preconditions checklist after `#11`, `#12`, `#18`, `#26`,
    and broader `#27` operationalization mature.
  - Usability-study script only after there is a real workflow surface to test.
- Recommended priority: `P4`.
- Explicit non-goals / overclaiming language to avoid:
  - Do not claim pilot-ready.
  - Do not run a pilot against a notebook-only experience unless maintainers
    explicitly label it as a guided demo observation, not product validation.
  - Do not create benchmark claims without current artifacts and reviewer
    signoff.

### Issue `#25`

- Current title: `Build evidence-linked AI extraction and drafting guardrails plus eval harness`
- Current purpose: define allowed AI tasks, evidence-linked prompt/response
  contracts, unsupported-claim evals, fallback behavior, and provider controls.
- Current-state mismatch: current repo remains deterministic and cache-first.
  There is no AI extraction/drafting guardrail implementation or eval harness
  for unsupported generated claims. Evidence and review contracts are improving
  but are not yet product-grade.
- Recommended action: defer; split into child issues.
- Suggested child issues:
  - AI boundary policy doc grounded in current evidence/provenance contracts.
  - Unsupported-claim eval fixture design without provider calls.
  - Extractive fallback behavior contract before any generative implementation.
- Recommended priority: `P2`, after `#12` starts and before any drafting AI is
  introduced.
- Explicit non-goals / overclaiming language to avoid:
  - Do not add live model calls in tests.
  - Do not generate legal advice.
  - Do not allow generated statements without evidence IDs or citation anchors.
  - Do not replace deterministic source scoring with AI scoring.

### Issue `#26`

- Current title: `Design human review workflow: approvals, revisions, and provenance-preserving edits`
- Current purpose: define review states, provenance-preserving edits, review
  triggers, role expectations, and revision/approval event requirements.
- Current-state mismatch: current code has `review_required` states,
  `ReviewEvent`, memo claims, evidence clusters, and read models, but there is
  no human approval workflow, revision history, editable UI, or team workflow.
- Recommended action: split into child issues.
- Suggested child issues:
  - Review-state contract across run, evidence, issue, memo, and export
    objects.
  - Revision/approval event schema decision note.
  - Provenance preservation tests for edited memo claims, after edit surfaces
    exist.
  - Role expectations doc for attorney, paralegal, and operator review.
- Recommended priority: `P2`, before `#15` workspace implementation and before
  any Pilot-ready claim.
- Explicit non-goals / overclaiming language to avoid:
  - Do not call current review-required markers an approval workflow.
  - Do not add auth, roles, persistence, or UI unless explicitly scoped.
  - Do not let edits sever evidence, citation, or review-event traceability.

### Issue `#27`

- Current title: `Define V2 quality rubric, benchmark suite, and release scorecard`
- Current purpose: maintain the shared quality rubric, benchmark language, and
  release-scorecard evidence path across engineering, product, and legal
  review.
- Current-state mismatch: the issue body is mostly closer to current truth than
  older V2 issues, but it should now mention the issue `#88` top-level
  `reviewer_summary` convenience layer and the post-PR90 truth-sync. Remaining
  work is broader CI and pilot operationalization, not the first rubric draft,
  not a new readiness framework, and not a readiness upgrade.
- Recommended action: keep as umbrella; rewrite body; split into child issues.
- Suggested child issues:
  - Broader CI reporting from the existing verify bundle and scorecard fields.
  - Pilot-evidence preconditions checklist using the current rubric only.
  - Dashboard-ready artifact field inventory without building a dashboard.
  - Benchmark scenario evidence gap map without adding new fixture lanes unless
    maintainers explicitly scope them.
- Recommended priority: `P0`, active governance and evidence lane.
- Explicit non-goals / overclaiming language to avoid:
  - Do not create a second readiness model.
  - Do not claim Beta-ready, Pilot-ready, production-ready, or self-serve UI
    readiness from the current bundle.
  - Do not add CI workflows, dashboards, pilot studies, fixtures, or runtime
    behavior under a docs-only body cleanup.

## Recommended Cleanup Order

1. Rewrite `#27`, `#10`, `#11`, and `#3` bodies before starting another broad
   V2 implementation issue.
2. Turn `#10`, `#11`, and `#27` into explicit umbrellas with linked child
   issues and landed-slice notes.
3. Keep `#12` as the next narrow product-core implementation lane, starting
   with one evidence adapter and tests.
4. Treat `#13`, `#25`, and `#26` as important but dependent on evidence and
   review contracts.
5. Park `#16`, `#17`, `#18`, and `#19` until the repo has the product/runtime
   surfaces needed to make their acceptance criteria meaningful.
