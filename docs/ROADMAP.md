# Roadmap (Simple, Current)

Last updated: May 18, 2026

This is the short version. Clean, practical, no drama.

## Where we are now

- Demo pipeline is stable.
- 432 tests are passing on the supported verify path.
- CI has a fresh-environment gate, editable-package install, an explicit offline fixture smoke job with golden snapshot validation, an offline e2e demo gate, offline security and dependency hygiene gates, and the `exa-py` compatibility matrix.
- CI now also emits categorized quality-gate artifacts for unit, offline fixture, offline e2e, golden snapshot, Exa compatibility, release-scorecard, security-hygiene, and dependency-hygiene failures.
- CI emits and validates a release-scorecard artifact from the calibrated `#27` workflow, including machine-readable blocking/advisory readiness categories for dashboard consumers.
- The supported test path is editable install plus `pytest -q`, or `PYTHONPATH=src` for ad hoc local runs. Raw-checkout `pytest -q` is not supported.
- The offline demo path now has a deterministic preflight command: `python -m war_room --preflight`.
- The notebook and preflight surfaces now expose a first workflow layer with research-plan preview, evidence-board summary, issue-workspace summary, memo-composer summary, export-history summary, and run-timeline review state.
- The Milton rendered memo now has a focused readability guard for mojibake, scraped navigation text, generic weather pages, Casetext boilerplate, and markdown table alignment.
- Runtime cache writes now carry a `v2alpha1` schema-versioned envelope while legacy raw fixture caches remain readable.
- The Evidence Board read model now has a typed `v2alpha1` contract and payload adapter, reducing one more loose dict seam in the workflow layer.
- The notebook Evidence Board now renders a styled HTML review view over that typed contract without adding dependencies or treating `apps/` as runtime.
- The Issue Workspace read model now has the same typed `v2alpha1` contract path for issue cards, authorities, citation outcomes, claims, and review events.
- The Memo Composer read model now has the same typed `v2alpha1` contract path for section cards, claim support links, review events, and export eligibility.
- The Export History read model now has the same typed `v2alpha1` contract path for export artifact rows, delivery state, disclaimer state, and audit references.
- The Run Timeline read model now has a typed `v2alpha1` envelope over canonical `Run` and `RunStage` records.
- A first narrow `#10` orchestration slice now defines shared run states, stage statuses, transition validation, and stage-to-run rollup helpers in `src/war_room/orchestration.py`; issue `#73` adds typed start-run and get-run-status API boundary contracts in `src/war_room/orchestration_api_contracts.py`; the first in-process offline service slice now lives in `src/war_room/orchestration_service.py`; the operator-facing status presentation layer lives in `src/war_room/orchestration_status_view.py`; issue `#78` adds a dependency-free thin transport/request-handler wrapper in `src/war_room/orchestration_transport.py`; the dev-only standard-library HTTP adapter lives in `src/war_room/orchestration_http.py`; production HTTP/API routing, persistence, queues, auth, dashboards, and UI remain future work.
- First narrow issue `#11` UX/spec slices now live in `docs/ISSUE_11_RUN_STATUS_UX_SPEC.md` and `docs/ISSUE_11_GUIDED_INTAKE_UX_SPEC.md`; they define how a future guided intake surface should collect and validate pre-run matter facts, then hand off to a run-status screen that consumes the existing `status_presentation` payload without adding a frontend app. Deterministic Milton previews now live in `docs/examples/guided_intake_milton_preview.md` and `docs/examples/run_status_milton_degraded.md`.
- The committed five-scenario offline fixture lane now has a deterministic golden snapshot check for source mix, case counts, citation summaries, output structure, and coverage metadata.
- The curated scenario registry now has five offline-ready fixture-backed benchmarks: Milton/Pinellas/Citizens, Ian/Lee/Citizens HO-3, Ida/Orleans/Lloyd's, Texas hail/Tarrant/Allstate HO-B, and Texas hail/Tarrant/Allstate DP-3.
- The fixture-seeding process now defines when a scenario can be promoted to offline-ready status and tests guard against fixture-key or bundle drift.
- A deeper V2 foundation layer is tracked in issues `#22` through `#27`.
- Issue [#4](https://github.com/itprodirect/cat-loss-war-room/issues/4) is complete and closed.
- Issue [#5](https://github.com/itprodirect/cat-loss-war-room/issues/5) is complete and closed.
- Issue [#22](https://github.com/itprodirect/cat-loss-war-room/issues/22) is complete and closed.
- Issues [#23](https://github.com/itprodirect/cat-loss-war-room/issues/23) and [#24](https://github.com/itprodirect/cat-loss-war-room/issues/24) are complete and closed as written source-of-truth specs.
- Issue [#27](https://github.com/itprodirect/cat-loss-war-room/issues/27) is still open, but the local and CI release-evidence path now includes explicit demo-ready threshold calibration, blocking/advisory metric categories, run-scoped artifacts, verify manifests, a stable latest pointer in `docs/V2_RELEASE_RUBRIC.md`, a reviewer guide in [ISSUE_27_RELEASE_EVIDENCE_REVIEW_GUIDE.md](ISSUE_27_RELEASE_EVIDENCE_REVIEW_GUIDE.md), and the issue `#88` top-level `reviewer_summary` convenience layer derived from the existing readiness posture.
- Issue [#6](https://github.com/itprodirect/cat-loss-war-room/issues/6) is complete. The closeout audit in [ISSUE_6_CLOSEOUT_AUDIT.md](ISSUE_6_CLOSEOUT_AUDIT.md) maps the contract/cache requirements to code, tests, scope boundaries, and validation evidence.
- Issue [#7](https://github.com/itprodirect/cat-loss-war-room/issues/7) is complete. The closure sanity audit in [ISSUE_7_CLOSURE_SANITY_AUDIT.md](ISSUE_7_CLOSURE_SANITY_AUDIT.md) documents the PR #56 gap and the follow-up fix for `None` provider-response malformed-contract handling.
- Issue [#8](https://github.com/itprodirect/cat-loss-war-room/issues/8) is complete and closed. The five-lane offline fixture baseline now covers Milton, Ida, Ian/Lee/Citizens HO-3, Texas hail/Tarrant/Allstate HO-B, and Texas hail/Tarrant/Allstate DP-3 with registry-backed offline-ready scenarios and golden snapshot validation.
- Issue [#9](https://github.com/itprodirect/cat-loss-war-room/issues/9) is complete. The closeout audit in [ISSUE_9_CLOSEOUT_AUDIT.md](ISSUE_9_CLOSEOUT_AUDIT.md) maps the expanded CI quality-gate requirements to workflow jobs, gate categories, tests, artifact evidence, and offline validation.
- Issue [#10](https://github.com/itprodirect/cat-loss-war-room/issues/10) has a first run-state contract slice documented in [ISSUE_10_RUN_STATE_CONTRACT.md](ISSUE_10_RUN_STATE_CONTRACT.md), an issue `#73` API boundary contract slice documented in [ISSUE_10_API_CONTRACTS.md](ISSUE_10_API_CONTRACTS.md), a first in-process offline service slice documented in [ISSUE_10_SERVICE_SLICE.md](ISSUE_10_SERVICE_SLICE.md), an operator-facing status presentation layer documented in [ISSUE_10_STATUS_PRESENTATION.md](ISSUE_10_STATUS_PRESENTATION.md), an issue `#78` thin transport wrapper documented in [ISSUE_78_THIN_TRANSPORT_WRAPPER.md](ISSUE_78_THIN_TRANSPORT_WRAPPER.md), and a dev-only standard-library HTTP adapter documented in [ISSUE_10_DEV_HTTP_WRAPPER.md](ISSUE_10_DEV_HTTP_WRAPPER.md). Production HTTP/API routing, persistence, retries, and circuit-breaker behavior are still pending.
- Issue [#11](https://github.com/itprodirect/cat-loss-war-room/issues/11) has first UX/spec slices documented in [ISSUE_11_GUIDED_INTAKE_UX_SPEC.md](ISSUE_11_GUIDED_INTAKE_UX_SPEC.md) and [ISSUE_11_RUN_STATUS_UX_SPEC.md](ISSUE_11_RUN_STATUS_UX_SPEC.md), plus deterministic Milton previews in [examples/guided_intake_milton_preview.md](examples/guided_intake_milton_preview.md) and [examples/run_status_milton_degraded.md](examples/run_status_milton_degraded.md). Frontend implementation, dashboards, auth, persistence, and production API work remain pending.
- Placeholder directories under `apps/`, `packages/`, and `workers/` are planned V2 boundaries only. The active runtime remains the notebook plus `src/war_room/`.

## Delivery layers

- V0 implemented now: notebook-first demo, cache-backed offline lane, package bootstrap, and current memo pipeline.
- V2 definition work completed: workflow/IA in `#23`, evidence schema in `#24`, repo/runtime boundary framing in `#22`, and a first-pass release rubric in `#27`.
- V2 implementation work still pending: broaden CI and pilot operationalization from `#27`, then continue explicitly scoped product slices in `#10`/`#11` against the existing offline orchestration contracts and the first `#11` run-status UX spec.

## Active Priority Rank

This is the current best-to-worst order for active work on the current build.
Issue [#3](https://github.com/itprodirect/cat-loss-war-room/issues/3) remains the umbrella epic and is not ranked with execution tickets.

Issues [#23](https://github.com/itprodirect/cat-loss-war-room/issues/23) and [#24](https://github.com/itprodirect/cat-loss-war-room/issues/24) are not ranked here because their written source-of-truth docs already landed and those definition issues are closed. Their downstream implementation work lives in `#10`, `#11`, and `#12`.

1. [#27](https://github.com/itprodirect/cat-loss-war-room/issues/27) Broaden CI and pilot operationalization of the calibrated release rubric
2. [#10](https://github.com/itprodirect/cat-loss-war-room/issues/10) Remaining orchestration/API work beyond the landed contracts/service/status/transport/dev-HTTP slices
3. [#11](https://github.com/itprodirect/cat-loss-war-room/issues/11) Future guided-intake/run-status contract seam and UI implementation beyond the landed specs/previews
4. [#12](https://github.com/itprodirect/cat-loss-war-room/issues/12) Evidence normalization + provenance implementation
5. [#13](https://github.com/itprodirect/cat-loss-war-room/issues/13) Caselaw quality v2
6. [#25](https://github.com/itprodirect/cat-loss-war-room/issues/25) AI guardrails + eval harness
7. [#26](https://github.com/itprodirect/cat-loss-war-room/issues/26) Human review workflow
8. [#14](https://github.com/itprodirect/cat-loss-war-room/issues/14) Citation verification hardening
9. [#15](https://github.com/itprodirect/cat-loss-war-room/issues/15) Memo workspace v2
10. [#17](https://github.com/itprodirect/cat-loss-war-room/issues/17) Observability + cost controls
11. [#18](https://github.com/itprodirect/cat-loss-war-room/issues/18) Security baseline
12. [#19](https://github.com/itprodirect/cat-loss-war-room/issues/19) Attorney pilot validation
13. [#16](https://github.com/itprodirect/cat-loss-war-room/issues/16) Firm memory v1

## Triage Notes

- Issues `#6` and `#9` are documented complete in closeout audits. The rest of the backlog is mostly coherent.
- The main cleanup is scope clarity, not deletion:
  - `#23` and `#24` should be treated as completed definition work; downstream implementation belongs elsewhere.
  - `#6` is complete and should stay scoped to closeout follow-through rather than new runtime work.
  - `#9` is complete for the current CI quality-gate acceptance criteria; future security, pilot, and optional fixture-breadth work belongs in `#18`, `#19`, `#27`, or a newly scoped follow-up rather than reopening `#8`.
  - `#11` now has guided-intake and run-status UX/spec slices plus deterministic Milton guided-intake and degraded run-status previews; future implementation should still follow the workflow defined in `#23`.
  - `#12` should explicitly implement against the canonical schema defined in `#24`.
- `#27` should now focus on CI and pilot operationalization of the calibrated rubric rather than inventing the first rubric draft.
  - CI artifact emission, local verify evidence bundles, artifact integrity checks, dashboard-ready blocking/advisory scorecard categories, the top-level `reviewer_summary` convenience summary, and the human release-evidence review guide already landed; the remaining work is broader gate coverage and pilot evidence.

## Now (next 2-3 weeks)

Goal: finish the remaining definition/foundation work so V2 implementation starts from stable contracts and quality gates.

- [#27](https://github.com/itprodirect/cat-loss-war-room/issues/27) Broaden CI and pilot operationalization of the calibrated release scorecard

## Next (30-60 days)

Goal: build the first true product workflow around the research engine.

- [#10](https://github.com/itprodirect/cat-loss-war-room/issues/10) Remaining orchestration/API work beyond the landed contracts/service/status/transport/dev-HTTP slices
- [#11](https://github.com/itprodirect/cat-loss-war-room/issues/11) Future guided-intake/run-status contract seam and UI implementation beyond the landed specs/previews
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
- Release-evidence reviewer guide: [ISSUE_27_RELEASE_EVIDENCE_REVIEW_GUIDE.md](ISSUE_27_RELEASE_EVIDENCE_REVIEW_GUIDE.md)
- Issue `#8` readiness and closure audit: [ISSUE_8_READINESS_AUDIT.md](ISSUE_8_READINESS_AUDIT.md)
- Workflow and IA source of truth: [V2_WORKFLOW_IA.md](V2_WORKFLOW_IA.md)
- Evidence schema source of truth: [V2_EVIDENCE_SCHEMA.md](V2_EVIDENCE_SCHEMA.md)
- Guided-intake UX/spec source for issue `#11`: [ISSUE_11_GUIDED_INTAKE_UX_SPEC.md](ISSUE_11_GUIDED_INTAKE_UX_SPEC.md)
- Guided-intake preview example for issue `#11`: [examples/guided_intake_milton_preview.md](examples/guided_intake_milton_preview.md)
- Run-status UX/spec source for issue `#11`: [ISSUE_11_RUN_STATUS_UX_SPEC.md](ISSUE_11_RUN_STATUS_UX_SPEC.md)
- Run-status preview example for issue `#11`: [examples/run_status_milton_degraded.md](examples/run_status_milton_degraded.md)
