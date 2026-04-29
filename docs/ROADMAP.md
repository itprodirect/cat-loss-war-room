# Roadmap (Simple, Current)

Last updated: April 28, 2026

This is the short version. Clean, practical, no drama.

## Where we are now

- Demo pipeline is stable.
- 279 tests are passing on the supported verify path.
- CI has a fresh-environment gate, editable-package install, an explicit offline fixture smoke job, and the `exa-py` compatibility matrix.
- CI now also emits and validates a release-scorecard artifact from the calibrated `#27` workflow.
- The supported test path is editable install plus `pytest -q`, or `PYTHONPATH=src` for ad hoc local runs. Raw-checkout `pytest -q` is not supported.
- The offline demo path now has a deterministic preflight command: `python -m war_room --preflight`.
- The notebook and preflight surfaces now expose a first workflow layer with research-plan preview, evidence-board summary, issue-workspace summary, memo-composer summary, export-history summary, and run-timeline review state.
- The Milton rendered memo now has a focused readability guard for mojibake, scraped navigation text, generic weather pages, Casetext boilerplate, and markdown table alignment.
- A deeper V2 foundation layer is tracked in issues `#22` through `#27`.
- Issue [#4](https://github.com/itprodirect/cat-loss-war-room/issues/4) is complete and closed.
- Issue [#5](https://github.com/itprodirect/cat-loss-war-room/issues/5) is complete and closed.
- Issue [#22](https://github.com/itprodirect/cat-loss-war-room/issues/22) is complete and closed.
- Issues [#23](https://github.com/itprodirect/cat-loss-war-room/issues/23) and [#24](https://github.com/itprodirect/cat-loss-war-room/issues/24) are complete and closed as written source-of-truth specs.
- Issue [#27](https://github.com/itprodirect/cat-loss-war-room/issues/27) is still open, but the local and CI release-evidence path now includes explicit demo-ready threshold calibration, run-scoped artifacts, verify manifests, and a stable latest pointer in `docs/V2_RELEASE_RUBRIC.md`.
- Issue [#6](https://github.com/itprodirect/cat-loss-war-room/issues/6) is in progress (slices 1-7 landed locally; review/export graph-linkage contract slice now added).
- Placeholder directories under `apps/`, `packages/`, and `workers/` are planned V2 boundaries only. The active runtime remains the notebook plus `src/war_room/`.

## Delivery layers

- V0 implemented now: notebook-first demo, cache-backed offline lane, package bootstrap, and current memo pipeline.
- V2 definition work completed: workflow/IA in `#23`, evidence schema in `#24`, repo/runtime boundary framing in `#22`, and a first-pass release rubric in `#27`.
- V2 implementation work still pending: broaden CI and pilot operationalization from `#27`, complete remaining foundation work in `#6` to `#9`, then build product surfaces in `#10` onward.

## Active Priority Rank

This is the current best-to-worst order for active work on the current build.
Issue [#3](https://github.com/itprodirect/cat-loss-war-room/issues/3) remains the umbrella epic and is not ranked with execution tickets.

Issues [#23](https://github.com/itprodirect/cat-loss-war-room/issues/23) and [#24](https://github.com/itprodirect/cat-loss-war-room/issues/24) are not ranked here because their written source-of-truth docs already landed and those definition issues are closed. Their downstream implementation work lives in `#10`, `#11`, and `#12`.

1. [#27](https://github.com/itprodirect/cat-loss-war-room/issues/27) Broaden CI and pilot operationalization of the calibrated release rubric
2. [#6](https://github.com/itprodirect/cat-loss-war-room/issues/6) Complete remaining typed domain contracts
3. [#9](https://github.com/itprodirect/cat-loss-war-room/issues/9) Expand CI quality gates beyond the lanes already in place
4. [#7](https://github.com/itprodirect/cat-loss-war-room/issues/7) Retrieval provider abstraction + contract tests (four slices landed)
5. [#8](https://github.com/itprodirect/cat-loss-war-room/issues/8) Multi-jurisdiction fixture suite + snapshots
6. [#10](https://github.com/itprodirect/cat-loss-war-room/issues/10) API orchestrator with graceful degradation
7. [#11](https://github.com/itprodirect/cat-loss-war-room/issues/11) Guided web intake + run-status UX
8. [#12](https://github.com/itprodirect/cat-loss-war-room/issues/12) Evidence normalization + provenance implementation
9. [#13](https://github.com/itprodirect/cat-loss-war-room/issues/13) Caselaw quality v2
10. [#25](https://github.com/itprodirect/cat-loss-war-room/issues/25) AI guardrails + eval harness
11. [#26](https://github.com/itprodirect/cat-loss-war-room/issues/26) Human review workflow
12. [#14](https://github.com/itprodirect/cat-loss-war-room/issues/14) Citation verification hardening
13. [#15](https://github.com/itprodirect/cat-loss-war-room/issues/15) Memo workspace v2
14. [#17](https://github.com/itprodirect/cat-loss-war-room/issues/17) Observability + cost controls
15. [#18](https://github.com/itprodirect/cat-loss-war-room/issues/18) Security baseline
16. [#19](https://github.com/itprodirect/cat-loss-war-room/issues/19) Attorney pilot validation
17. [#16](https://github.com/itprodirect/cat-loss-war-room/issues/16) Firm memory v1

## Triage Notes

- No safe issue closures were identified in this pass. The backlog is mostly coherent.
- The main cleanup is scope clarity, not deletion:
  - `#23` and `#24` should be treated as completed definition work; downstream implementation belongs elsewhere.
  - `#6` should track only the remaining typed-contract work.
  - `#9` should track CI expansion beyond the gates already in place.
  - `#11` should explicitly implement the workflow defined in `#23`.
  - `#12` should explicitly implement against the canonical schema defined in `#24`.
- `#27` should now focus on CI and pilot operationalization of the calibrated rubric rather than inventing the first rubric draft.
  - CI artifact emission, local verify evidence bundles, and artifact integrity checks already landed; the remaining work is broader gate coverage and pilot evidence.

## Now (next 2-3 weeks)

Goal: finish the remaining definition/foundation work so V2 implementation starts from stable contracts and quality gates.

- [#27](https://github.com/itprodirect/cat-loss-war-room/issues/27) Broaden CI and pilot operationalization of the calibrated release scorecard
- [#6](https://github.com/itprodirect/cat-loss-war-room/issues/6) Complete remaining typed domain contracts
- [#7](https://github.com/itprodirect/cat-loss-war-room/issues/7) Retrieval provider abstraction + contract tests (provider seam + notebook retrieval-state + citation-verify + deterministic timing slices landed)
- [#8](https://github.com/itprodirect/cat-loss-war-room/issues/8) Multi-jurisdiction fixture suite + snapshots
- [#9](https://github.com/itprodirect/cat-loss-war-room/issues/9) Expand CI quality gates

## Next (30-60 days)

Goal: build the first true product workflow around the research engine.

- [#10](https://github.com/itprodirect/cat-loss-war-room/issues/10) API orchestrator with graceful degradation
- [#11](https://github.com/itprodirect/cat-loss-war-room/issues/11) Guided web intake + run status UX
- [#12](https://github.com/itprodirect/cat-loss-war-room/issues/12) Evidence normalization + provenance
- [#13](https://github.com/itprodirect/cat-loss-war-room/issues/13) Caselaw quality v2
- [#25](https://github.com/itprodirect/cat-loss-war-room/issues/25) AI guardrails + eval harness
- [#26](https://github.com/itprodirect/cat-loss-war-room/issues/26) Human review workflow

## Then (60-90 days)

Goal: trust, polish, and real-world adoption readiness.

- [#14](https://github.com/itprodirect/cat-loss-war-room/issues/14) Citation verification hardening
- [#15](https://github.com/itprodirect/cat-loss-war-room/issues/15) Memo workspace v2
- [#16](https://github.com/itprodirect/cat-loss-war-room/issues/16) Firm memory v1
- [#17](https://github.com/itprodirect/cat-loss-war-room/issues/17) Observability + cost controls
- [#18](https://github.com/itprodirect/cat-loss-war-room/issues/18) Security baseline
- [#19](https://github.com/itprodirect/cat-loss-war-room/issues/19) Attorney pilot validation

## Success checks we care about

- Reliability: tests and CI stay green on every PR.
- Trust: every key statement in output can be traced to sources.
- Evidence shape: related evidence records cluster cleanly by citation or URL before memo/export rendering.
- Reviewability: memo claims should resolve to stable evidence-group references, not only item-level rows.
- Auditability: review events should point at those same grouped evidence references so warnings and citation failures stay traceable.
- Usability: non-technical users can run intake-to-memo with minimal guidance.
- Quality: fewer noisy results, better case law precision, clearer citation confidence.
- Readiness: releases are scored against the same benchmark rubric used in pilot validation.

## Notes

- Detailed architecture plan: [V2_BLUEPRINT.md](V2_BLUEPRINT.md)
- Issue-by-issue map: [V2_ISSUE_MAP.md](V2_ISSUE_MAP.md)
- Current project-health audit: [PROJECT_HEALTH_AUDIT_2026-03-10.md](PROJECT_HEALTH_AUDIT_2026-03-10.md)
- Release rubric source of truth: [V2_RELEASE_RUBRIC.md](V2_RELEASE_RUBRIC.md)
- Workflow and IA source of truth: [V2_WORKFLOW_IA.md](V2_WORKFLOW_IA.md)
- Evidence schema source of truth: [V2_EVIDENCE_SCHEMA.md](V2_EVIDENCE_SCHEMA.md)
