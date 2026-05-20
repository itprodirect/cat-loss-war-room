# Issue 12 Dedupe Integration Plan

Date: 2026-05-20

## Purpose

Issue [#12](https://github.com/itprodirect/cat-loss-war-room/issues/12) remains the umbrella for evidence normalization, dedupe, provenance, confidence annotations, and canonical evidence behavior.

This plan defines the provenance-safe contract for integrating deterministic evidence dedupe into audit snapshot assembly later. It is a docs/spec slice only. It does not wire dedupe into runtime code.

The key risk is that dropping duplicate `EvidenceItem` rows without a complete ID remapping would orphan references from clusters, memo claims, review events, workflow read models, markdown export, quality snapshots, and release-evidence artifacts. Citation verification is the sharpest edge: a citation-check row can share a URL or citation with a case-law row but still carries citation-specific status, badge, note, and review-required meaning.

## Current Landed State

The current issue `#12` state is:

- Named evidence adapters are landed for the current source families:
  - `weather_brief_to_evidence_items(...)`
  - `carrier_doc_pack_to_evidence_items(...)`
  - `caselaw_pack_to_evidence_items(...)`
  - `citation_verify_pack_to_evidence_items(...)`
- `dedupe_evidence_items(...)` exists in `src/war_room/models.py`.
- Dedupe is helper-only.
- Audit snapshot assembly is not deduped.
- No `old_id -> retained_id` remapping exists.
- Current clustering can group related rows by citation or URL, but clustering does not remove evidence rows.

This means a later implementation must treat dedupe as an ID-rewrite operation, not only as a list-filtering operation.

## Current Provenance Chain

The current provenance chain starts in `run_audit_snapshot_from_memo_input(...)` and flows through these surfaces:

- `evidence_items`
- `evidence_ids_by_module`
- `EvidenceCluster.evidence_ids`
- `MemoClaim.evidence_ids`
- `MemoClaim.cluster_ids`
- `ReviewEvent.related_evidence_ids`
- `ReviewEvent.related_cluster_ids`
- Evidence Board read model and rendered Evidence Board
- Issue Workspace read model and rendered Issue Workspace
- Memo Composer read model and rendered Memo Composer
- Markdown Evidence Clusters appendix
- Markdown Evidence Index
- Markdown Review Log
- quality snapshots, including evidence counts, duplicate-authority counts, and provenance-link counts
- release evidence / verify artifacts, including preflight, offline e2e, golden fixture snapshots, verify manifests, release scorecards, and CI quality-gate artifacts that consume those outputs

Any runtime dedupe integration must rewrite or recompute all references that can contain evidence IDs or evidence-derived counts.

## Remapping Contract

Future runtime integration must produce an explicit `old_id -> retained_id` mapping for every duplicate row that is removed.

Required behavior:

- Every pre-dedupe `EvidenceItem.evidence_id` must resolve either to itself or to a retained evidence ID.
- The mapping must be deterministic for a given ordered input list.
- The retained row must preserve the current first-row-wins behavior.
- Duplicate rows must not disappear from auditability just because they are removed from the retained `evidence_items` list.
- The mapping must be available before clusters, memo claims, review events, quality snapshots, and export surfaces are finalized.

Conceptual location:

- For the first implementation, the mapping should live next to audit snapshot assembly as a runtime-local integration product, for example an internal `dedupe_result` with:
  - `retained_items`
  - `old_id_to_retained_id`
  - `removed_duplicate_ids`
  - `retained_id_to_duplicate_ids`
- It should be created after all source-family adapters emit canonical `EvidenceItem` rows and before `evidence_ids_by_module`, clusters, memo claims, review events, quality snapshots, and export metadata are finalized.
- It should not require persistence, API shape changes, or UI changes for the first runtime integration.

Auditing removed duplicate IDs:

- A removed duplicate ID remains auditable if `old_id_to_retained_id[old_id]` points to the retained row and validation proves every old reference resolves after rewriting.
- A retained row may later need duplicate/source metadata if maintainers want exported artifacts to show collapsed aliases directly.
- That retained-row metadata should be a separate explicit schema decision. It is not required for the first provenance-safe runtime integration if the remapping is retained long enough for validation and artifact generation.

## Cross-Module Collapse Policy

The safest first runtime integration should forbid cross-module collapse.

Policy:

- Same-module duplicate collapse may be integrated first when the remapping contract and invariants are proven.
- Cross-module URL/citation collapse must be gated behind a later issue.
- Citation-verification rows must not collapse into case-law rows in the first runtime integration.
- Case-law rows must not collapse into citation-verification rows in the first runtime integration.
- Cross-module rows may continue to share an `EvidenceCluster` by citation or URL. Clustering can express relatedness without deleting module-specific evidence rows.

Reason:

- `caselaw` evidence usually represents an authority candidate.
- `citation_verify` evidence represents the status of a spot-check against that authority or citation.
- If a citation verification row collapses into a case-law row, citation-specific status, badge, review-required state, note text, and related review-event references can be silently dropped or misattributed.
- The current helper has conservative compatibility checks, but the audit-snapshot integration problem is broader than helper-level row equality because downstream surfaces need the removed IDs rewritten and the source role preserved.

Later cross-module collapse can be revisited only after:

- retained rows have explicit duplicate/source-role metadata or equivalent artifact-level visibility;
- test fixtures prove citation-review events still point to the correct retained evidence and clusters;
- Evidence Board, Issue Workspace, Memo Composer, Markdown export, quality snapshots, and release evidence all render the intended provenance.

## Per-Surface Rewrite Rules

### `evidence_ids_by_module`

- Build module-scoped evidence ID lists from pre-dedupe adapter output.
- Rewrite each old ID through `old_id_to_retained_id`.
- Preserve module membership after rewrite, even if the retained evidence row came from the same module only.
- De-duplicate rewritten IDs within each module while preserving first appearance order.
- For the first runtime integration, do not rewrite one module to a retained ID from another module because cross-module collapse is forbidden.

### Evidence clusters

- Build clusters from retained evidence rows after same-module dedupe.
- Cluster `evidence_ids` must contain only retained IDs.
- Cluster IDs must remain deterministic for the retained evidence order.
- Cluster `member_count`, `modules`, `provenance_urls`, `review_required`, `citation`, `url`, and `authority_key` must be recomputed from retained rows.
- If a removed duplicate contributes a URL or source role that must remain visible, that is a later retained-row metadata/schema decision, not an implicit cluster side effect.

### Memo claims

- Rewrite every `MemoClaim.evidence_ids` entry through `old_id_to_retained_id`.
- Remove duplicate rewritten IDs within a claim while preserving first appearance order.
- Recompute `MemoClaim.cluster_ids` from the rewritten retained evidence IDs and the final cluster map.
- Claim status must not become less strict because a duplicate row was removed.

### Review events

- Rewrite every `ReviewEvent.related_evidence_ids` entry through `old_id_to_retained_id`.
- Remove duplicate rewritten IDs within the event while preserving first appearance order.
- Recompute `ReviewEvent.related_cluster_ids` from the rewritten retained evidence IDs and final cluster map.
- Review events must not be dropped just because the duplicate evidence row that first triggered the event was removed.
- Citation review events must continue to scope only to non-verified citation-check evidence.

### Export evidence index

- The Markdown Evidence Index should list retained evidence rows only after dedupe is integrated.
- If duplicate aliases need to be visible in the export, add a separately scoped schema/export decision for retained-row duplicate metadata.
- The Markdown Evidence Clusters appendix and Review Log must only reference retained evidence IDs and retained cluster IDs.
- Exported claim traces must show cluster IDs recomputed from retained evidence rows.

### Quality counts

- `raw_evidence_count` should represent pre-dedupe adapter output count.
- `evidence_item_count` should represent retained exported evidence rows after dedupe.
- `evidence_cluster_count`, `grouped_evidence_count`, `normalized_authority_count`, `duplicate_authority_count`, and `provenance_link_count` must be recomputed from the final retained evidence rows and clusters unless a later schema explicitly adds separate raw-vs-retained duplicate metrics.
- Counts must not imply cross-module collapse when cross-module collapse is disabled.

### Release evidence artifacts

- Preflight, offline e2e, golden fixture snapshots, verify manifests, release scorecards, and CI quality-gate artifacts must consume the same retained snapshot behavior as markdown export once dedupe is integrated.
- Golden snapshots should be updated only after a focused provenance-integrity test harness proves there are no dangling IDs.
- Release evidence must distinguish a planned/runtime dedupe integration from a completed full V2 evidence graph.

## Provenance-Integrity Invariants

The runtime implementation must prove these invariants with fixture-backed validation:

- No dangling evidence IDs exist in clusters, memo claims, review events, read models, markdown export, quality snapshots, or release evidence artifacts.
- Retained IDs are deterministic for the same ordered adapter output.
- No provenance is silently dropped when a duplicate row is removed.
- Every rewritten reference resolves to a retained `EvidenceItem`.
- Every retained `EvidenceCluster.evidence_ids` entry resolves to a retained `EvidenceItem`.
- Every `MemoClaim.evidence_ids` entry resolves to a retained `EvidenceItem`.
- Every `MemoClaim.cluster_ids` entry resolves to a retained `EvidenceCluster`.
- Every `ReviewEvent.related_evidence_ids` entry resolves to a retained `EvidenceItem`.
- Every `ReviewEvent.related_cluster_ids` entry resolves to a retained `EvidenceCluster`.
- Citation-review events still reference citation-verification evidence after dedupe.
- Evidence Board, Issue Workspace, Memo Composer, Markdown Evidence Index, quality snapshots, and release evidence all render without stale IDs.
- Fixture-backed tests cover at least one duplicate URL case, one duplicate citation case, one same-module duplicate, and one cross-module citation/case-law case that stays uncollapsed in the first runtime integration.

## Phased Implementation Sequence

1. Land this docs/spec PR.
2. Add a runtime test harness that proves no dangling references across the current audit snapshot, read models, markdown export, quality snapshot, and release-evidence paths.
3. Integrate dedupe behind an explicit remapping contract, initially same-module only.
4. Update golden snapshots after the harness proves the intended retained IDs, rewritten references, and count changes.
5. Harden cross-surface provenance further, including any retained-row duplicate/source metadata needed before cross-module collapse is reconsidered.

## Recommended Next GitHub Issues

Create these issues in order. Do not create them from this PR.

### 1. Add provenance-integrity harness before audit-snapshot dedupe wiring

Suggested body:

> Add fixture-backed tests that walk `RunAuditSnapshot`, Evidence Board, Issue Workspace, Memo Composer, Markdown export, quality snapshots, and release-evidence artifacts to prove every evidence and cluster reference resolves before dedupe is wired into runtime assembly.
>
> Scope:
> - add helper assertions for no dangling evidence IDs;
> - cover clusters, memo claims, review events, read models, export appendices, quality counts, and verify/release evidence consumers;
> - include a cross-module caselaw/citation-verify fixture that must stay uncollapsed for now.
>
> Non-goals:
> - no runtime dedupe integration;
> - no schema changes;
> - no persistence, API, UI, auth, queues, workers, fuzzy/ML clustering, or AI scoring.
>
> Acceptance:
> - focused tests fail if any downstream reference points at a missing evidence row or cluster;
> - `python -m war_room --verify` remains green.

### 2. Integrate same-module evidence dedupe into audit snapshot assembly behind ID remapping

Suggested body:

> Wire deterministic evidence dedupe into `run_audit_snapshot_from_memo_input(...)` only after all adapter rows are created, and only with an explicit `old_id -> retained_id` remapping that rewrites module ID lists, clusters, memo claims, review events, export appendices, and quality counts.
>
> Scope:
> - same-module duplicate collapse only;
> - first-row-wins retained rows;
> - deterministic mapping and rewritten references;
> - no dangling IDs across read models and markdown export.
>
> Non-goals:
> - no cross-module URL/citation collapse;
> - no retained-row duplicate metadata unless separately approved;
> - no schema/persistence/API/UI/auth/queue changes.
>
> Acceptance:
> - provenance-integrity harness passes;
> - focused dedupe tests prove deterministic retained IDs and rewritten references;
> - `python -m war_room --verify` passes.

### 3. Update golden fixture snapshots for remapped dedupe behavior

Suggested body:

> Refresh the golden offline fixture snapshots after same-module dedupe integration changes retained evidence counts, cluster counts, or provenance summaries.
>
> Scope:
> - update expected fixture snapshots only after the dedupe/remapping tests pass;
> - document any count changes in the PR body;
> - keep scenario registry and source fixtures unchanged unless a test exposes a real fixture defect.
>
> Non-goals:
> - no new fixtures;
> - no live retrieval;
> - no scoring or citation behavior changes.
>
> Acceptance:
> - golden snapshot gate passes;
> - count deltas are explained and traceable to retained IDs.

### 4. Harden cross-surface provenance metadata for removed duplicate IDs

Suggested body:

> Decide whether retained evidence rows, audit bundles, or export artifacts need explicit duplicate/source metadata so removed IDs remain visible to reviewers after dedupe.
>
> Scope:
> - evaluate retained-row duplicate metadata versus artifact-local remapping metadata;
> - preserve attorney-review visibility of removed duplicate source roles;
> - keep current disclaimer and review-required posture intact.
>
> Non-goals:
> - no broad V2 graph persistence;
> - no API/UI/dashboard/auth/queue implementation;
> - no cross-module collapse until this decision is complete.
>
> Acceptance:
> - the chosen metadata approach is documented and test-covered;
> - exports remain provenance-auditable.

### 5. Evaluate gated cross-module URL/citation collapse for caselaw and citation verification

Suggested body:

> Revisit cross-module collapse only after same-module runtime dedupe, remapping, golden snapshots, and duplicate metadata are stable.
>
> Scope:
> - explicitly test citation_verify plus caselaw rows that share citation or URL;
> - preserve citation-check status, badge, note, review-required state, and review-event linkage;
> - define whether any cross-module collapse is safe or whether clustering is the final policy.
>
> Non-goals:
> - no fuzzy/ML clustering;
> - no AI scoring;
> - no citation-search behavior change;
> - no claim that the V2 evidence graph is complete.
>
> Acceptance:
> - if cross-module collapse remains forbidden, document that as the durable policy;
> - if any gated collapse is allowed, prove no citation-specific provenance is lost.

## Explicit Non-Goals

This PR and plan do not add:

- runtime code;
- tests;
- schema changes;
- persistence;
- API, UI, or dashboard;
- auth;
- queues or workers;
- fuzzy or ML clustering;
- AI scoring;
- live retrieval changes;
- provider-ranking changes;
- citation-search or citation-verification behavior changes;
- notebook behavior changes;
- fixture changes;
- dependency changes;
- CI changes;
- a claim that the V2 evidence graph is complete.

## Validation Expectations For Later Runtime PRs

A later implementation PR should run at least:

```bash
git diff --check
python -m pytest tests/test_memo_contracts.py tests/test_evidence_board.py tests/test_issue_workspace.py tests/test_memo_composer.py tests/test_export.py tests/test_preflight.py tests/test_fixture_snapshots.py -q
python -m war_room --verify
```

The first docs/spec PR should stay docs-only and use `git diff --check` plus the smallest repo-grounded validation needed for Markdown/link sanity.
