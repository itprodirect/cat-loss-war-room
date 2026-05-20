# Issue 12 Remaining Scope Review

Date: 2026-05-20

## Purpose

Issue [#12](https://github.com/itprodirect/cat-loss-war-room/issues/12) is still the umbrella for evidence normalization, dedupe, provenance, confidence annotations, and canonical evidence behavior. This review now reflects the landed issue `#94`, `#96`, `#98`, and `#103` evidence-adapter slices, including PR `#105`.

The current decision is:

- treat weather, carrier, caselaw, and citation verification as the current named adapter seams;
- do not treat issue `#12` as complete or ready for broad persistence, UI, API, review workflow, or full evidence graph implementation;
- choose the next issue `#12` child from a narrow deterministic dedupe helper, provenance link hardening, citation-quality fixture regression under `#13` / `#14`, or a docs-only issue-12 closeout/status map.

## Current Adapter Status

The canonical source family for issue `#12` adapter work is the set of current module outputs that become `EvidenceItem` rows in `RunAuditSnapshot`.

| Source family | Current status | Adapter surface | Scope boundary |
| --- | --- | --- | --- |
| Weather corroboration | Landed | `weather_brief_to_evidence_items(...)` in `src/war_room/models.py` | Maps current `WeatherBrief` / `SourceReference` rows to deterministic provenance-oriented `EvidenceItem` IDs. |
| Carrier intelligence | Landed | `carrier_doc_pack_to_evidence_items(...)` in `src/war_room/models.py` | Maps current `CarrierDocPack` / `CarrierDocument` rows to deterministic provenance-oriented `EvidenceItem` IDs. |
| Case law | Landed | `caselaw_pack_to_evidence_items(...)` in `src/war_room/models.py` | Maps current `CaseLawPack` / `CaseIssue` / `CaseEntry` rows to deterministic provenance-oriented `EvidenceItem` IDs. |
| Citation verification | Landed in issue `#103` / PR `#105` | `citation_verify_pack_to_evidence_items(...)` in `src/war_room/models.py` | Maps current `CitationVerifyPack` / `CitationCheck` rows to deterministic provenance-oriented `EvidenceItem` IDs without changing citation verification behavior. |

The landed weather, carrier, caselaw, and citation-verification adapters are narrow seams over current notebook-era module output. They preserve `RunAuditSnapshot`, Evidence Board, memo/export behavior, fixture-backed tests, and the current offline validation lane. They are not a full V2 evidence graph, storage layer, dedupe engine, dashboard, API integration, persistence layer, or review workflow.

## Adapter Gap Status

All current evidence-producing source families now have named evidence adapter seams.

PR `#105` added `citation_verify_pack_to_evidence_items(...)` over the existing `CitationVerifyPack` / `CitationCheck` output and routed `run_audit_snapshot_from_memo_input(...)` through that adapter. Citation evidence rows now follow the same named-adapter pattern as weather, carrier, and caselaw output.

That landed adapter only translates existing citation-check output into canonical `EvidenceItem` rows. It does not change citation search behavior, add live retrieval, harden ambiguity logic, change badge/status vocabulary, change badge/display semantics, expand `EvidenceItem`, or claim legal verification.

Current non-adapter surfaces should stay out of this child issue:

- `RetrievalTask` and `RunEvent` are canonical runtime/audit entities, not evidence source-family adapters.
- `MemoClaim`, `ReviewEvent`, `EvidenceCluster`, and export artifacts are provenance and review-linkage surfaces, not additional source-family adapter targets.
- Intake, research-plan, memo-assembly, and export stages should not become evidence adapters just to fill a table.

## Recommended Next Child Issue

The prior recommended child landed as issue `#103` / PR `#105`:

**Issue #12 child: Add citation-verify evidence adapter over current `CitationVerifyPack` output.**

What landed:

- `citation_verify_pack_to_evidence_items(...)` maps current `CitationVerifyPack` / `CitationCheck` output into canonical `EvidenceItem` rows.
- Citation evidence IDs are deterministic and provenance-oriented instead of positional IDs such as `citation-check-1`.
- Citation status semantics, live retrieval behavior, badge/display semantics, and the `EvidenceItem` schema stayed unchanged.
- `run_audit_snapshot_from_memo_input(...)` now routes citation evidence rows through the named adapter while preserving current downstream surfaces.
- Focused tests cover stable IDs, duplicate-row suffixing, existing-field metadata preservation, audit-snapshot inclusion, Evidence Board rendering, export evidence-index behavior, and sparse citation metadata.

Recommended next decision:

- choose a deterministic dedupe helper,
- harden provenance links across current audit output,
- add citation-quality fixture regression under issue `#13` / `#14`, or
- write a docs-only issue-12 closeout/status map that separates landed adapter seams from the still-open full evidence graph.

Validation should stay local and fixture-backed:

```bash
git diff --check
python -m pytest -q
```

## Adapter-Status Map Decision

A separate adapter-status map is no longer needed before the citation-verify adapter because that adapter landed in PR `#105`. A docs-only closeout/status map may still be useful if maintainers want a concise issue `#12` view that separates landed adapter seams from the broader open graph, dedupe, persistence, API, and review-workflow work.

Add a dedicated adapter-status map later only if maintainers want to coordinate more than one of these broader tracks:

- URL/citation dedupe regression behavior across all five fixture lanes;
- full canonical graph persistence and API response contracts;
- provenance-through-edits in the human review workflow;
- cross-surface traceability from memo claims to clusters and export artifacts;
- issue `#14` citation verification hardening beyond adapter translation.

## Explicitly Deferred Work

These items remain outside the landed adapter slices and outside this docs-only review:

- broad dedupe by URL, content fingerprint, title similarity, or ML scoring;
- a database, persistence layer, storage migration, or full canonical graph store;
- dashboard, frontend, UI, app shell, auth, queues, workers, sessions, or production API routing;
- live retrieval changes, new providers, provider ranking changes, or citation-search behavior changes;
- AI scoring, generative evidence synthesis, or replacement of deterministic source scoring;
- provenance-through-edits, approvals, revisions, or broader human-review workflow design;
- a claim that the V2 evidence graph is complete.

## How Future Codex Work Should Use This

For the next child issue, Codex should start by deciding which narrow follow-up is actually being requested. If the child is dedupe or provenance hardening, use the landed adapter output and current audit-snapshot tests as fixtures rather than broadening into storage or UI. If the child is citation-quality regression, keep it under issue `#13` / `#14` and do not change live retrieval or badge semantics without explicit scope.

Do not turn issue `#12` into a broad implementation umbrella. The citation-verify adapter is landed; the next useful slice should be a narrow dedupe, provenance, citation-quality, or status-map follow-up.
