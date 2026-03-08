# Roadmap (Simple, Current)

Last updated: March 8, 2026

This is the short version. Clean, practical, no drama.

## Where we are now

- Demo pipeline is stable.
- 159 tests are passing.
- CI has a fresh-environment gate, editable-package install, and `exa-py` compatibility matrix.
- A deeper V2 foundation layer is now tracked in issues `#22` through `#27`.
- Issue [#4](https://github.com/itprodirect/cat-loss-war-room-demo/issues/4) is complete.
- Issue [#5](https://github.com/itprodirect/cat-loss-war-room-demo/issues/5) is complete and closed.
- Issue [#22](https://github.com/itprodirect/cat-loss-war-room-demo/issues/22) is complete.
- Issue [#6](https://github.com/itprodirect/cat-loss-war-room-demo/issues/6) is in progress (slices 1-6 landed locally; run/retrieval lifecycle contract slice now added).
- Test expectations assume the documented bootstrap flow: editable package install or equivalent `PYTHONPATH=src`, not a raw-checkout `pytest -q`.

## Active Priority Rank

This is the current best-to-worst order for active work on the current build.
Issue [#3](https://github.com/itprodirect/cat-loss-war-room-demo/issues/3) remains the umbrella epic and is not ranked with execution tickets.

1. [#23](https://github.com/itprodirect/cat-loss-war-room-demo/issues/23) Define attorney workflow, IA, and design system
2. [#24](https://github.com/itprodirect/cat-loss-war-room-demo/issues/24) Define canonical evidence graph and audit schema
3. [#27](https://github.com/itprodirect/cat-loss-war-room-demo/issues/27) Define quality rubric and release scorecard
4. [#6](https://github.com/itprodirect/cat-loss-war-room-demo/issues/6) Complete remaining typed domain contracts
5. [#7](https://github.com/itprodirect/cat-loss-war-room-demo/issues/7) Retrieval provider abstraction + contract tests (first slice landed)
6. [#8](https://github.com/itprodirect/cat-loss-war-room-demo/issues/8) Multi-jurisdiction fixture suite + snapshots
7. [#9](https://github.com/itprodirect/cat-loss-war-room-demo/issues/9) Expand CI quality gates
8. [#10](https://github.com/itprodirect/cat-loss-war-room-demo/issues/10) API orchestrator with graceful degradation
9. [#11](https://github.com/itprodirect/cat-loss-war-room-demo/issues/11) Guided web intake + run-status UX
10. [#12](https://github.com/itprodirect/cat-loss-war-room-demo/issues/12) Evidence normalization + provenance implementation
11. [#13](https://github.com/itprodirect/cat-loss-war-room-demo/issues/13) Caselaw quality v2
12. [#25](https://github.com/itprodirect/cat-loss-war-room-demo/issues/25) AI guardrails + eval harness
13. [#26](https://github.com/itprodirect/cat-loss-war-room-demo/issues/26) Human review workflow
14. [#14](https://github.com/itprodirect/cat-loss-war-room-demo/issues/14) Citation verification hardening
15. [#15](https://github.com/itprodirect/cat-loss-war-room-demo/issues/15) Memo workspace v2
16. [#17](https://github.com/itprodirect/cat-loss-war-room-demo/issues/17) Observability + cost controls
17. [#18](https://github.com/itprodirect/cat-loss-war-room-demo/issues/18) Security baseline
18. [#19](https://github.com/itprodirect/cat-loss-war-room-demo/issues/19) Attorney pilot validation
19. [#16](https://github.com/itprodirect/cat-loss-war-room-demo/issues/16) Firm memory v1

## Triage Notes

- No safe issue closures were identified in this pass. The backlog is mostly coherent.
- The main cleanup is scope clarity, not deletion:
  - `#6` should track only the remaining typed-contract work.
  - `#9` should track CI expansion beyond the gates already in place.
  - `#11` should explicitly implement the workflow defined in `#23`.
  - `#12` should explicitly implement against the canonical schema defined in `#24`.

## Now (next 2-3 weeks)

Goal: lock the shape of V2 and finish the technical foundation.

- [#23](https://github.com/itprodirect/cat-loss-war-room-demo/issues/23) Define attorney workflow, IA, and design system
- [#24](https://github.com/itprodirect/cat-loss-war-room-demo/issues/24) Define canonical evidence graph and audit schema
- [#27](https://github.com/itprodirect/cat-loss-war-room-demo/issues/27) Define quality rubric and release scorecard
- [#6](https://github.com/itprodirect/cat-loss-war-room-demo/issues/6) Complete remaining typed domain contracts
- [#7](https://github.com/itprodirect/cat-loss-war-room-demo/issues/7) Retrieval provider abstraction + contract tests (provider protocol + Exa compatibility slice landed)
- [#8](https://github.com/itprodirect/cat-loss-war-room-demo/issues/8) Multi-jurisdiction fixture suite + snapshots
- [#9](https://github.com/itprodirect/cat-loss-war-room-demo/issues/9) Expand CI quality gates

## Next (30-60 days)

Goal: build the first true product workflow around the research engine.

- [#10](https://github.com/itprodirect/cat-loss-war-room-demo/issues/10) API orchestrator with graceful degradation
- [#11](https://github.com/itprodirect/cat-loss-war-room-demo/issues/11) Guided web intake + run status UX
- [#12](https://github.com/itprodirect/cat-loss-war-room-demo/issues/12) Evidence normalization + provenance
- [#13](https://github.com/itprodirect/cat-loss-war-room-demo/issues/13) Caselaw quality v2
- [#25](https://github.com/itprodirect/cat-loss-war-room-demo/issues/25) AI guardrails + eval harness
- [#26](https://github.com/itprodirect/cat-loss-war-room-demo/issues/26) Human review workflow

## Then (60-90 days)

Goal: trust, polish, and real-world adoption readiness.

- [#14](https://github.com/itprodirect/cat-loss-war-room-demo/issues/14) Citation verification hardening
- [#15](https://github.com/itprodirect/cat-loss-war-room-demo/issues/15) Memo workspace v2
- [#16](https://github.com/itprodirect/cat-loss-war-room-demo/issues/16) Firm memory v1
- [#17](https://github.com/itprodirect/cat-loss-war-room-demo/issues/17) Observability + cost controls
- [#18](https://github.com/itprodirect/cat-loss-war-room-demo/issues/18) Security baseline
- [#19](https://github.com/itprodirect/cat-loss-war-room-demo/issues/19) Attorney pilot validation

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
- Workflow and IA source of truth: [V2_WORKFLOW_IA.md](V2_WORKFLOW_IA.md)
- Evidence schema source of truth: [V2_EVIDENCE_SCHEMA.md](V2_EVIDENCE_SCHEMA.md)
