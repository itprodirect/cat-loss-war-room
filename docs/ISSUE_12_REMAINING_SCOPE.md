# Issue 12 Remaining Scope Review

Date: 2026-05-20

## Purpose

Issue [#12](https://github.com/itprodirect/cat-loss-war-room/issues/12) is still the umbrella for evidence normalization, dedupe, provenance, confidence annotations, and canonical evidence behavior. This review narrows the next implementation step after the landed issue `#94`, `#96`, and `#98` evidence-adapter slices.

The current decision is:

- continue with one narrow citation-verify evidence adapter child issue next;
- do not treat issue `#12` as ready for a broad dedupe, persistence, UI, or full evidence graph implementation;
- do not create a separate adapter-status map before the citation-verify slice unless maintainers want to plan multiple adapter families at once.

## Current Adapter Status

The canonical source family for issue `#12` adapter work is the set of current module outputs that become `EvidenceItem` rows in `RunAuditSnapshot`.

| Source family | Current status | Adapter surface | Scope boundary |
| --- | --- | --- | --- |
| Weather corroboration | Landed | `weather_brief_to_evidence_items(...)` in `src/war_room/models.py` | Maps current `WeatherBrief` / `SourceReference` rows to deterministic provenance-oriented `EvidenceItem` IDs. |
| Carrier intelligence | Landed | `carrier_doc_pack_to_evidence_items(...)` in `src/war_room/models.py` | Maps current `CarrierDocPack` / `CarrierDocument` rows to deterministic provenance-oriented `EvidenceItem` IDs. |
| Case law | Landed | `caselaw_pack_to_evidence_items(...)` in `src/war_room/models.py` | Maps current `CaseLawPack` / `CaseIssue` / `CaseEntry` rows to deterministic provenance-oriented `EvidenceItem` IDs. |
| Citation verification | Partially present, adapter not landed | Current `run_audit_snapshot_from_memo_input(...)` builds `citation_verify` evidence rows inline from `CitationVerifyPack` checks | Needs a named adapter seam and stable provenance-oriented IDs before broader issue `#12` work continues. |

The landed weather, carrier, and caselaw adapters are narrow seams over current notebook-era module output. They preserve `RunAuditSnapshot`, Evidence Board, memo/export behavior, fixture-backed tests, and the current offline validation lane. They are not a full V2 evidence graph, storage layer, dedupe engine, dashboard, or API integration.

## Source Families Still Lacking Adapters

Only the citation-verify source family still lacks a dedicated canonical evidence adapter among today's evidence-producing module outputs.

The current code already has typed citation verification contracts through `CitationVerifyPack`, `CitationCheck`, `CitationSummary`, `adapt_citation_verify_pack(...)`, and `citation_verify_pack_to_payload(...)`. It also already emits `citation_verify` `EvidenceItem` rows inside `run_audit_snapshot_from_memo_input(...)`. The missing piece is a named adapter equivalent to the landed source-family adapters, for example `citation_verify_pack_to_evidence_items(...)`.

That adapter should only translate existing citation-check output into canonical `EvidenceItem` rows. It should not change citation search behavior, add live retrieval, harden ambiguity logic, change badge/status vocabulary, or claim legal verification.

Current non-adapter surfaces should stay out of this child issue:

- `RetrievalTask` and `RunEvent` are canonical runtime/audit entities, not evidence source-family adapters.
- `MemoClaim`, `ReviewEvent`, `EvidenceCluster`, and export artifacts are provenance and review-linkage surfaces, not the next adapter target.
- Intake, research-plan, memo-assembly, and export stages should not become evidence adapters just to fill a table.

## Recommended Next Child Issue

Create the next child as:

**Issue #12 child: Add citation-verify evidence adapter over current `CitationVerifyPack` output.**

Narrow implementation intent:

- Add a named adapter from current `CitationVerifyPack` / `CitationCheck` output into canonical `EvidenceItem` rows.
- Replace current positional citation evidence IDs such as `citation-check-1` with deterministic provenance-oriented IDs.
- Preserve citation status semantics: `verified`, `uncertain`, and `not_found` remain confidence signals requiring attorney review as appropriate.
- Preserve trust metadata already produced by citation verification, including `status_reason`, `trust_explanation`, `source_tier`, `source_class`, `is_primary_authority`, `confidence`, `citation`, `case_name`, and `source_url` where present.
- Route `run_audit_snapshot_from_memo_input(...)` through the new adapter while preserving existing Evidence Board, Issue Workspace, Memo Composer, Export History, release-scorecard, and offline fixture behavior.
- Add focused tests for stable IDs, duplicate-row suffixing, metadata preservation, audit-snapshot inclusion, Evidence Board rendering, memo/export evidence-index behavior, and sparse citation metadata.

Validation should stay local and fixture-backed:

```bash
git diff --check
python -m pytest -q
```

## Adapter-Status Map Decision

A separate adapter-status map is not needed before the citation-verify adapter. This review is enough status mapping for the next child because there is only one remaining evidence-producing module family without a named adapter.

Add a dedicated adapter-status map later only if maintainers want to coordinate more than one of these broader tracks:

- URL/citation dedupe regression behavior across all five fixture lanes;
- full canonical graph persistence and API response contracts;
- provenance-through-edits in the human review workflow;
- cross-surface traceability from memo claims to clusters and export artifacts;
- issue `#14` citation verification hardening beyond adapter translation.

## Explicitly Deferred Work

These items remain outside the next adapter slice and outside this docs-only review:

- broad dedupe by URL, content fingerprint, title similarity, or ML scoring;
- a database, persistence layer, storage migration, or full canonical graph store;
- dashboard, frontend, app shell, auth, queues, workers, sessions, or production API routing;
- live retrieval changes, new providers, provider ranking changes, or citation-search behavior changes;
- AI scoring, generative evidence synthesis, or replacement of deterministic source scoring;
- provenance-through-edits, approvals, revisions, or broader human-review workflow design;
- a claim that the V2 evidence graph is complete.

## How Future Codex Work Should Use This

For the next child issue, Codex should start from `src/war_room/models.py` and the existing tests in `tests/test_memo_contracts.py`, `tests/test_evidence_board.py`, `tests/test_export.py`, and `tests/test_issue_workspace.py`. The implementation should mirror the landed weather, carrier, and caselaw adapter pattern and keep the citation-verify change to adapter extraction plus deterministic ID behavior.

Do not turn issue `#12` into a broad implementation umbrella. The next useful code slice is the citation-verify adapter only.
