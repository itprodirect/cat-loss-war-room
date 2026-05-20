# Issue 12 Remaining Scope Review

Date: 2026-05-20

## Purpose

Issue [#12](https://github.com/itprodirect/cat-loss-war-room/issues/12) is still the umbrella for evidence normalization, dedupe, provenance, confidence annotations, and canonical evidence behavior. This review now reflects the landed issue `#94`, `#96`, `#98`, and `#103` evidence-adapter slices, including PR `#105`, plus the issue `#107` / PR `#108` helper-only deterministic evidence dedupe utility.

The current decision is:

- treat weather, carrier, caselaw, and citation verification as the current named adapter seams;
- do not treat issue `#12` as complete or ready for broad persistence, UI, API, review workflow, or full evidence graph implementation;
- pause implementation and choose the next issue `#12` child from a provenance-safe dedupe integration plan with `old_id -> retained_id` mapping, deterministic dedupe integration into audit snapshot assembly, provenance link hardening across memo claims / evidence clusters / review events, or citation-quality fixture regression under `#13` / `#14`.

## Current Adapter Status

The canonical source family for issue `#12` adapter work is the set of current module outputs that become `EvidenceItem` rows in `RunAuditSnapshot`.

| Source family | Current status | Adapter surface | Scope boundary |
| --- | --- | --- | --- |
| Weather corroboration | Landed | `weather_brief_to_evidence_items(...)` in `src/war_room/models.py` | Maps current `WeatherBrief` / `SourceReference` rows to deterministic provenance-oriented `EvidenceItem` IDs. |
| Carrier intelligence | Landed | `carrier_doc_pack_to_evidence_items(...)` in `src/war_room/models.py` | Maps current `CarrierDocPack` / `CarrierDocument` rows to deterministic provenance-oriented `EvidenceItem` IDs. |
| Case law | Landed | `caselaw_pack_to_evidence_items(...)` in `src/war_room/models.py` | Maps current `CaseLawPack` / `CaseIssue` / `CaseEntry` rows to deterministic provenance-oriented `EvidenceItem` IDs. |
| Citation verification | Landed in issue `#103` / PR `#105` | `citation_verify_pack_to_evidence_items(...)` in `src/war_room/models.py` | Maps current `CitationVerifyPack` / `CitationCheck` rows to deterministic provenance-oriented `EvidenceItem` IDs without changing citation verification behavior. |

The landed weather, carrier, caselaw, and citation-verification adapters are narrow seams over current notebook-era module output. They preserve `RunAuditSnapshot`, Evidence Board, memo/export behavior, fixture-backed tests, and the current offline validation lane. They are not a full V2 evidence graph, storage layer, dashboard, API integration, persistence layer, or review workflow.

## Dedupe Helper Status

Issue `#107` / PR `#108` added `dedupe_evidence_items(...)` over canonical
`EvidenceItem` rows.

What landed:

- The helper is local, deterministic, and helper-only.
- It dedupes conservatively by explainable keys such as normalized URL,
  normalized citation or authority key, and normalized title plus module and
  `evidence_type` fallback.
- It preserves deterministic order and keeps the first retained row unchanged.
- Same-key summary behavior is explicit: the first retained row wins, and the
  candidate summary is not merged into it.
- Selected review/provenance compatibility conflicts keep rows separate.

What did not land:

- No integration into `RunAuditSnapshot` assembly.
- No `old_id -> retained_id` remapping or equivalent provenance-safe linkage
  plan.
- No `EvidenceItem` schema expansion.
- No persistence, API, dashboard, UI, live retrieval, provider-ranking change,
  citation behavior change, fuzzy/ML clustering, AI scoring, readiness claim,
  or full V2 evidence graph.

Future integration should not simply drop duplicate IDs from the audit path.
It needs a remapping or equivalent provenance-safe plan so memo claims,
evidence clusters, review events, and export references do not point at removed
rows after dedupe.

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

The next helper child also landed as issue `#107` / PR `#108`:

**Issue #12 child: Add deterministic evidence dedupe helper over canonical
`EvidenceItem` rows.**

What landed:

- `dedupe_evidence_items(...)` dedupes canonical `EvidenceItem` rows using
  deterministic, explainable keys.
- Rows without a clear key remain distinct.
- The retained first row wins for same-key rows, including summary text.
- Focused tests cover URL, citation/authority, title fallback, sparse metadata,
  conservative cross-module behavior, distinct URL rows, review-required
  conflicts, and same-key summary retention.

Recommended next decision:

- write a provenance-safe dedupe integration plan with `old_id -> retained_id`
  mapping or an equivalent linkage strategy,
- integrate deterministic dedupe into audit snapshot assembly after that plan,
- harden provenance links across memo claims, evidence clusters, and review
  events, or
- add citation-quality fixture regression under issue `#13` / `#14`.

Validation should stay local and fixture-backed:

```bash
git diff --check
python -m pytest -q
python -m war_room --verify
```

## Adapter-Status Map Decision

A separate adapter-status map is no longer needed before the citation-verify adapter because that adapter landed in PR `#105`. A docs-only closeout/status map is also lower priority than the provenance-safe dedupe integration decision now that PR `#108` landed the helper-only utility. A status map may still be useful later if maintainers want a concise issue `#12` view that separates landed adapter seams and helper-only dedupe from the broader open graph, integration, persistence, API, and review-workflow work.

Add a dedicated adapter-status map later only if maintainers want to coordinate more than one of these broader tracks:

- audit snapshot dedupe integration behavior across all five fixture lanes;
- full canonical graph persistence and API response contracts;
- provenance-through-edits in the human review workflow;
- cross-surface traceability from memo claims to clusters and export artifacts;
- issue `#14` citation verification hardening beyond adapter translation.

## Explicitly Deferred Work

These items remain outside the landed adapter slices and outside this docs-only review:

- audit snapshot dedupe integration without a provenance-safe remapping plan;
- broad dedupe by content fingerprint, title similarity, fuzzy matching, or ML scoring;
- a database, persistence layer, storage migration, or full canonical graph store;
- dashboard, frontend, UI, app shell, auth, queues, workers, sessions, or production API routing;
- live retrieval changes, new providers, provider ranking changes, or citation-search behavior changes;
- AI scoring, generative evidence synthesis, or replacement of deterministic source scoring;
- provenance-through-edits, approvals, revisions, or broader human-review workflow design;
- a claim that the V2 evidence graph is complete.

## How Future Codex Work Should Use This

For the next child issue, Codex should start by deciding which narrow follow-up is actually being requested. If the child is dedupe integration, start with a provenance-safe `old_id -> retained_id` remapping plan or equivalent linkage design before changing audit snapshot assembly. If the child is provenance hardening, use the landed adapter output and current audit-snapshot tests as fixtures rather than broadening into storage or UI. If the child is citation-quality regression, keep it under issue `#13` / `#14` and do not change live retrieval or badge semantics without explicit scope.

Do not turn issue `#12` into a broad implementation umbrella. The citation-verify adapter and helper-only dedupe utility are landed; the next useful slice should be a narrow provenance-safe dedupe integration, provenance-link, or citation-quality follow-up.
