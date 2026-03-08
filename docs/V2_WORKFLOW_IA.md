# V2 Workflow IA and Design System

Last updated: March 8, 2026

This document is the concrete output of issue `#23`.

It defines the intended V2 user workflow, information architecture, and interface rules for CAT-Loss War Room. It is written so later work on `#10` (API orchestrator) and `#11` (guided web intake and run-status UX) can proceed without inventing product flow decisions.

## 1) Purpose

The current v0 product is a notebook-first research demo.

V2 is a guided legal workbench for non-technical operators who need to move a matter from intake to evidence-backed memo without Python, Jupyter, or narrated engineering support.

This document locks four things:

- the user journey,
- the concrete application views,
- the trust and review behaviors that must remain visible,
- and the minimum workflow contracts future engineering must preserve.

## 2) Product Position

### Current v0

- Primary runtime is notebook-driven.
- Output is useful for demo and internal review.
- An engineer usually drives the session.
- The system is reliable offline, but not yet shaped for self-serve legal users.

### Intended V2

- Primary runtime is a guided web product.
- The first-class user is a non-technical legal operator.
- The memo is a downstream artifact, not the primary object.
- The primary product surface is evidence review, issue analysis, and human approval.

## 3) Primary Users

### Paralegal

- Primary V2 operator.
- Owns intake, launches runs, monitors progress, and assembles first-pass materials.
- Needs clear validation, partial-progress visibility, and safe defaults.

### Associate

- Reviews issue groupings, checks authority quality, edits claims, and tightens memo language.
- Needs direct traceability from claim to evidence cluster to source.

### Partner

- Reviews trust posture, uncertainty, and export quality.
- Needs concise run summaries, visible review-required states, and clean export bundles.

## 4) Workflow Principle

Optimize the product around the first non-technical operator, then support higher-skill reviewers without branching into a separate workflow.

That means:

- intake must be guided,
- evidence must appear before prose,
- uncertainty must be visible in the main flow,
- and partial completion must still produce reviewable output.

## 5) End-to-End Workflow

The canonical V2 workflow is:

`Intake -> Research Plan Preview -> Run Timeline -> Evidence Board -> Issue Workspace -> Memo Composer -> Export/Audit Bundle`

Each stage below is a required product stage, even if some views later share layout or route structure.

### Stage 1: Intake

**User goal**

Capture matter facts accurately enough to generate a useful research plan without requiring legal-tech expertise.

**Required inputs**

- event name
- event date
- state
- county or parish
- carrier
- policy type
- posture

**Optional inputs**

- key facts
- coverage issues
- internal matter label
- redaction-safe internal notes

**System outputs**

- validated intake record
- clear field-level errors
- normalized posture tokens
- readiness state for plan generation

**Trust and uncertainty signals**

- required vs optional fields are explicit
- validation errors are field-specific and blocking only when necessary
- any redaction or external-sharing warning is shown before run creation

**Failure or partial-success behavior**

- invalid required fields block progression
- incomplete optional fields do not block progression
- if a field is structurally valid but weak, show a warning instead of blocking

**Handoff**

The system converts the intake into a draft research plan and routes the user to Research Plan Preview.

### Stage 2: Research Plan Preview

**User goal**

Understand what the system will research before spending time or provider budget.

**Required inputs**

- validated intake

**System outputs**

- planned modules
- planned issue buckets
- representative queries or question groups
- preferred source domains
- estimated run scope, time, and confidence caveats

**Trust and uncertainty signals**

- show which modules are planned and why
- show when the plan depends heavily on generic or broad queries
- surface when coverage issues are under-specified

**Failure or partial-success behavior**

- if one module cannot be planned, the rest of the plan still renders
- if inputs are too vague for a useful plan, route back to intake with targeted guidance

**Handoff**

User confirms the plan and starts a run. The system creates a run record and moves to Run Timeline.

### Stage 3: Run Timeline

**User goal**

Track progress and understand whether the run is healthy, degraded, or complete.

**Required inputs**

- run record
- stage execution updates

**System outputs**

- current run state
- per-stage progress
- retries and recoveries
- budget-sensitive warnings
- partial outputs as they become available

**Trust and uncertainty signals**

- each module shows its current status
- degraded stages are marked explicitly, not hidden in logs
- partial completion is labeled as usable but review-required where appropriate

**Failure or partial-success behavior**

- one module failing does not collapse the run if others can finish
- runs may end in `partial_success` with evidence and memo sections still available
- hard failure is reserved for runs that cannot produce a reviewable bundle

**Handoff**

When at least one module yields reviewable evidence, the user can move into Evidence Board. When all stages finish, the run also exposes the memo and export surfaces.

### Stage 4: Evidence Board

**User goal**

Review gathered support before relying on system-generated prose.

**Required inputs**

- normalized evidence items
- evidence clusters
- source metadata
- review events

**System outputs**

- evidence cards grouped by issue or cluster
- source tier, provenance, and review-required markers
- exclusions or low-value findings where available

**Trust and uncertainty signals**

- evidence clusters are the default view, not flat raw rows
- source confidence always appears as text plus color/state treatment
- review-required evidence is visually elevated in the primary list

**Failure or partial-success behavior**

- if clustering is incomplete, fall back to item view with a clear warning
- low-confidence evidence remains visible but cannot masquerade as high-confidence support

**Handoff**

User selects or inspects issue areas and moves into Issue Workspace.

### Stage 5: Issue Workspace

**User goal**

Evaluate evidence and authorities by legal issue rather than by retrieval source alone.

**Required inputs**

- issue groupings
- linked evidence clusters
- case authorities
- citation-check outcomes

**System outputs**

- issue-level summaries
- strongest supporting authorities
- contradictions, gaps, and review-required items
- evidence-to-claim candidates for drafting

**Trust and uncertainty signals**

- every issue summary links back to evidence clusters
- case authority quality is distinct from generic commentary
- citation uncertainty is shown inside the issue view, not deferred to export

**Failure or partial-success behavior**

- if an issue lacks sufficient support, keep the issue visible with a review-required state
- if case law is noisy, preserve the evidence but prevent it from silently becoming strong support

**Handoff**

Issue-reviewed content feeds Memo Composer as evidence-linked sections and claims.

### Stage 6: Memo Composer

**User goal**

Assemble a usable draft memo while preserving traceability and human review.

**Required inputs**

- issue-organized evidence
- memo claims
- review events
- export contract metadata

**System outputs**

- section-based draft memo
- claim-level support links
- review-required flags
- missing-support warnings

**Trust and uncertainty signals**

- claims must remain linked to evidence clusters
- unsupported or weakly supported text is marked for review
- system-generated prose cannot outrun the evidence surface

**Failure or partial-success behavior**

- sections may be available even when other sections are still incomplete
- unsupported sections remain draft-only and review-required
- the product must not imply completed legal analysis when only partial evidence exists

**Handoff**

User finalizes a review state and generates export artifacts plus audit bundle.

### Stage 7: Export and Audit Bundle

**User goal**

Produce a clean deliverable plus the review context needed to trust it.

**Required inputs**

- reviewed memo
- evidence index
- review log
- export metadata

**System outputs**

- memo export
- evidence appendix
- review log
- audit snapshot and export history entry

**Trust and uncertainty signals**

- disclaimer language is mandatory
- review-required issues remain visible in export metadata and appendix views
- export history preserves run provenance

**Failure or partial-success behavior**

- export can proceed for reviewable partial runs if the product clearly marks the result as partial or review-required
- export must never strip disclaimers or provenance links

**Handoff**

The run is stored in export history for later retrieval, comparison, and follow-up review.

## 6) Information Architecture

The V2 IA should be implemented as the following primary views.

### Matter Intake

- Create matter
- Edit intake facts
- Validate readiness
- Start from matter context, not raw query or provider configuration

### Run Setup / Plan Review

- Preview research plan
- Review planned modules, issue areas, and source preferences
- Confirm run start

### Run Status

- Timeline of stage execution
- Module health and retries
- Partial-results entry point into evidence

### Evidence Review

- Cluster-first evidence board
- Filtering by issue, module, source tier, and review state
- Quick access to raw source links and provenance

### Issue-Focused Analysis

- Legal-issue workspace
- Case authorities and support grouped by issue
- Contradictions, missing support, and citation uncertainty visible inline

### Memo and Review Workspace

- Section-based memo composer
- Claim-level evidence trace
- Review-required states and human edits

### Export and History

- Export actions
- Prior exports
- Run summary, disclaimer state, and audit attachments

## 7) View-Level Rules

These rules are part of the IA contract.

- Do not make the run timeline the final destination. It is a transition view into evidence and review.
- Do not make the memo the first or default review surface.
- Do not bury warnings in appendices or secondary tabs.
- Do not present raw provider output as if it were reviewed evidence.
- Do not force users to understand retrieval jargon to complete a matter.

## 8) Design System Rules

This section is intentionally small. It exists to prevent later UI work from drifting into generic dashboard patterns.

### Tone

- Serious, calm, and editorial.
- Closer to a legal workbench than a startup analytics dashboard.

### Layout

- Dense enough for evidence comparison.
- Strong reading hierarchy for long-form review.
- Document-aware rather than widget-first.

### Trust Signals

- Confidence must use text plus color, never color alone.
- Review-required states must be prominent in the main flow.
- Evidence must be readable before prose derived from that evidence.

### Interaction Rules

- Prefer partial output over hard failure.
- Keep retry, degraded, and review-required states explicit.
- Use stable labels for module states and run states across the entire product.

### Motion and Visual Restraint

- Minimal motion.
- Use motion only for progress, state change, and navigation continuity.
- Avoid decorative animation.

## 9) Workflow Interfaces That Become Public Contracts

Later engineering may change implementation details, but these interface semantics should be treated as product contracts.

### Canonical Run States

- `queued`
- `running`
- `partial_success`
- `failed`
- `completed`
- `cancelled`

### Stage Progress States

- `not_started`
- `in_progress`
- `completed`
- `degraded`
- `failed`
- `skipped`

Recommended stage keys:

- `intake_validation`
- `research_plan`
- `weather`
- `carrier`
- `caselaw`
- `citation_verify`
- `memo_assembly`
- `export`

### Review-Required Semantics

- `review_required` means the output is usable for human review but not trustworthy as clean final support.
- `review_required` does not mean hidden, discarded, or blocked by default.
- Review-required status may exist at run, stage, issue, evidence cluster, claim, and export levels.

### Traceability Contract

- Every important memo claim must resolve to evidence IDs and evidence cluster IDs.
- Every review event must point to the affected evidence or evidence cluster when available.
- Export artifacts must preserve disclaimer state, section list, and provenance references.

## 10) Dependency on Other Issues

This document intentionally narrows downstream work.

### For `#10` API Orchestrator

- Build API flows around the stage sequence in this document.
- Expose run state, stage state, review-required state, and evidence-first navigation.
- Do not build memo-only orchestration responses.

### For `#11` Guided Web Intake and Run Status UX

- Implement the views defined here.
- Optimize for non-technical operator success, not engineer convenience.
- Treat evidence review and issue workspace as first-class destinations.

### For `#24` Canonical Evidence Graph and Audit Schema

- Preserve the entity relationships needed by the Evidence Board, Issue Workspace, Memo Composer, and Export History.
- The workflow assumes stable run, evidence, cluster, claim, review-event, and export relationships.

## 11) Explicit Non-Goals

- No SaaS multi-tenant scope in this document.
- No design mockups or pixel-perfect wireframes.
- No attempt to redefine the retrieval engine here.
- No removal of disclaimer, provenance, or review surfaces in the name of UX simplification.

## 12) Acceptance Criteria for This Spec

This document is sufficient when:

- another engineer can begin `#10` or `#11` without inventing the user flow,
- each stage has explicit input/output/trust/failure/handoff semantics,
- the first non-technical operator is clearly the primary UX target,
- and the workflow preserves evidence-first review instead of memo-first automation.
