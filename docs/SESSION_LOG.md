# CAT-Loss War Room - Session Log

This is the concise, current session timeline.

## Session 1 - Foundation
Date: 2026-02-25
Status: Complete

- Established repo structure, core modules, and initial docs.
- Built notebook baseline (cells 0-3).
- Added initial tests.

## Session 2 - Exa Integration
Date: 2026-02-25
Status: Complete

- Added weather, carrier, caselaw, citation verification, and export flow.
- Seeded cache samples for offline demo behavior.
- Expanded tests.

## Session 3 - Reliability Patch Pass
Date: 2026-02-25
Status: Complete

- Improved caselaw filtering.
- Hardened citation-check behavior and search-budget handling.
- Fixed hostname normalization bug.
- Brought test suite to 75 passing.

## Session 4 - V2 Planning and Issue Setup
Date: 2026-03-04
Status: Complete

- Added V2 blueprint and issue map docs.
- Created GitHub roadmap issues #3 through #19.

## Session 5 - V2 Issue #4 Execution
Date: 2026-03-04
Status: Complete

- Implemented exa-py compatibility support in `exa_client.py`.
- Pinned tested dependencies for reproducible setup.
- Added adapter regression tests.
- Added CI fresh-env test gate and exa-py compatibility matrix.
- Expanded test suite to 81 passing.

## Session 6 - PR and Merge
Date: 2026-03-04
Status: Complete

- Opened PR #20 for issue #4 work.
- Verified all CI checks passed.
- Merged to `main`.

## Current Snapshot
Date: 2026-03-07

- Branch baseline: `main` contains PR #20 and PR #21 changes.
- Test status: 168 passing.
- Roadmap source of truth: `docs/ROADMAP.md` and `docs/V2_ISSUE_MAP.md`.
- Issues #4, #5, and #22 complete. Issue #6 slices 1-6 landed. Issue #7 provider, notebook retrieval-state, and citation-verify slices landed.
- V2 foundation issues #22-#27 created and documented.
- Next priority: start #23, continue #24 and #27 framing, and finish #6 remaining scope.

## Session 7 - Documentation Refresh and Roadmap Simplification
Date: 2026-03-04
Status: Complete

- Updated canonical docs to match current state (81 tests, CI gates, issue #4 closed).
- Rewrote `docs/HANDOFF.md` for cleaner onboarding.
- Added `docs/ROADMAP.md` for a plain-language, issue-linked plan.
- Updated `docs/V2_BLUEPRINT.md` and `docs/V2_ISSUE_MAP.md` to reflect completed #4 and next priorities.
- Replaced legacy prompt/checklist docs with current, execution-focused versions.
- Verified repository test suite remains green (`81 passed`).

## Session 8 - Eval Lane Formalization
Date: 2026-03-04
Status: Complete

- Formalized the `eval/` workspace as a tracked project surface.
- Added `eval/README.md` with clear usage and data rules.
- Added a CaseIntake-aligned starter template at `eval/intakes/_template_case_intake.json`.
- Updated `eval/results/README.md` and `.gitignore` behavior for local eval artifacts.
- Linked the live eval lane from README and HANDOFF docs.
- Verification: `pytest -q` -> 81 passed.

## Session 9 - Hardening Pass: Null-Client Safety + Caselaw Precision
Date: 2026-03-05
Status: Complete

- Added graceful null-client fallbacks in weather/carrier/caselaw module entrypoints.
- Modules now prefer cache when available and return structured empty payloads when live retrieval is unavailable.
- Tightened caselaw case-like filtering:
  - citation-only items now require a trusted legal/court host,
  - case-name patterns still pass.
- Softened assertive carrier phrasing to evidence-oriented language.
- Added regression tests for all fallback and filter hardening behavior.
- Updated V2 blueprint note to reference `_template_case_intake.json`.
- Verification: `pytest -q` -> 85 passed.

## Session 10 - Issue #5 Intake Validation and Schema Lock
Date: 2026-03-05
Status: Complete

- Added strict intake ingestion helpers in `src/war_room/query_plan.py`:
  - `validate_case_intake_payload(payload)`
  - `load_case_intake(path)`
  - `IntakeValidationError`
- Enforced canonical schema boundaries:
  - required fields must exist,
  - unknown fields are rejected,
  - no type coercion,
  - `event_date` must be valid `YYYY-MM-DD`,
  - `posture` must be a non-empty list of snake_case tokens.
- Exported intake validation API and schema constants from `war_room.__init__`.
- Added coverage in `tests/test_intake_validation.py` for valid/invalid payloads and JSON ingest errors.
- Updated `eval/README.md` with explicit required/optional fields for both demo and live-eval lanes plus strict validation behavior.
- Updated build checklist to reflect issue #5 completion.
- Verification: `pytest -q` -> 96 passed.

## Session 11 - Issue #6 Slice 1: Typed Intake/Query Models (Pydantic)
Date: 2026-03-05
Status: Complete (slice 1)

- Added `src/war_room/models.py` with initial typed domain models:
  - `CaseIntake` (Pydantic, strict extra-field rejection, field validation)
  - `QuerySpec` (Pydantic, typed query contract)
- Rewired `src/war_room/query_plan.py` to use the typed models for all query planning interfaces.
- Preserved existing `#5` intake loader/validator behavior and error message patterns for compatibility.
- Added `tests/test_models.py` covering model validation and serialization round-trip behavior.
- Added `pydantic==2.11.7` to `requirements.txt` for reproducible typed-model support.
- Verification: `pytest -q` -> 100 passed.

## Session 12 - Issue #6 Slice 2: Typed Module Pack Models + Adapters
Date: 2026-03-05
Status: Complete (slice 2)

- Expanded `src/war_room/models.py` with typed payload contracts for:
  - `WeatherBrief`, `WeatherMetrics`, and `SourceReference`
  - `CarrierDocPack`, `CarrierSnapshot`, and `CarrierDocument`
  - `CaseLawPack`, `CaseIssue`, and `CaseEntry`
- Added adapter helpers for validation + normalized payload dumping:
  - `adapt_weather_brief` / `weather_brief_to_payload`
  - `adapt_carrier_doc_pack` / `carrier_doc_pack_to_payload`
  - `adapt_caselaw_pack` / `caselaw_pack_to_payload`
- Wired weather/carrier/caselaw modules to emit adapter-validated payloads for both empty and assembled responses.
- Added `tests/test_pack_adapters.py` to lock typed adapter behavior and validation failures.
- Verification: `pytest -q` -> 105 passed.

## Session 13 - Issue #6 Slice 3: Typed Citation + Export Contracts
Date: 2026-03-05
Status: Complete (slice 3)

- Extended `src/war_room/models.py` with typed citation and memo-render contracts:
  - `CitationCheck`, `CitationSummary`, `CitationVerifyPack`
  - `MemoRenderInput`
  - adapter helpers: `adapt_citation_verify_pack`, `citation_verify_pack_to_payload`, `memo_render_input_from_parts`
- Updated `src/war_room/citation_verify.py` to emit adapter-validated typed payloads while preserving legacy caselaw input compatibility for sparse `issues/cases` shapes.
- Updated `src/war_room/export_md.py` to normalize memo inputs through typed contracts before rendering markdown.
- Expanded package exports in `src/war_room/__init__.py` for new citation/export contract helpers.
- Added regression tests:
  - `tests/test_memo_contracts.py` (citation summary validation + memo input normalization)
  - updated `tests/test_citation_verify.py` assertions for normalized badge tokens.
- Verification: `pytest -q` -> 109 passed.

## Session 14 - Nightly Wrap-Up: Documentation Sync
Date: 2026-03-05
Status: Complete

- Audited core docs for stale roadmap/status references after PR #21 merge.
- Updated `CLAUDE.md` test-count and next-priority guidance.
- Updated `docs/ROADMAP.md` to current state:
  - #5 closed,
  - #6 in progress (slices 1-3 merged),
  - 109 passing tests.
- Updated `docs/V2_ISSUE_MAP.md` phase status notes for #5 and #6.
- Verified repository test suite remains green (`109 passed`).

## Session 15 - Nightly Close-Out: Final Docs Alignment
Date: 2026-03-05
Status: Complete

- Confirmed README, HANDOFF, roadmap, and issue-map status sections are aligned.
- Updated `docs/HANDOFF.md` to mark issue #5 as complete/closed.
- Updated `docs/V2_BLUEPRINT.md` immediate next actions to reflect post-#5 and post-#6-slice-3 state.
- Re-validated docs consistency against current issue and test status.


## Session 16 - V2 Rebuild Deep Dive and Roadmap Expansion
Date: 2026-03-06
Status: Complete

- Audited the repo as a product candidate, not just a codebase:
  - read the core docs,
  - inspected all major modules,
  - reviewed CI/workflow setup,
  - ran the cached end-to-end pipeline,
  - and verified `pytest -q` still passes (`109 passed`).
- Rewrote `docs/V2_BLUEPRINT.md` into a more opinionated rebuild plan:
  - current-state scorecard,
  - keep/kill/rewrite guidance,
  - UX verdict and experience blueprint,
  - modular-monolith architecture recommendation,
  - AI guardrails,
  - phased V2 roadmap.
- Expanded planning docs to reflect the deeper V2 foundation layer:
  - `docs/ROADMAP.md`
  - `docs/V2_ISSUE_MAP.md`
- Created new GitHub issues to support the rebuild:
  - `#22` product foundation,
  - `#23` workflow + design system,
  - `#24` canonical evidence graph + audit schema,
  - `#25` AI guardrails + eval harness,
  - `#26` human review workflow,
  - `#27` quality rubric + release scorecard.

## Session 17 - Issue Triage and Roadmap Ranking
Date: 2026-03-06
Status: Complete

- Audited all open and closed GitHub issues against the current repo docs and current build state.
- Confirmed there were no safe duplicate/stale issues to close outright.
- Tightened active roadmap language to reflect the true work order for the current version.
- Narrowed stale issue scope on GitHub so partially-complete issues no longer read like untouched work:
  - `#6` remaining typed-contract work only,
  - `#9` CI expansion beyond existing gates,
  - `#11` implementation follows `#23`,
  - `#12` implementation follows `#24`.
- Added a best-to-worst ranked priority list to `docs/ROADMAP.md`.

## Session 18 - Issue #22 Product Foundation
Date: 2026-03-06
Status: Complete

- Added editable package metadata with `pyproject.toml` for the existing `src/` layout.
- Added shared runtime bootstrap and typed settings helpers:
  - `src/war_room/bootstrap.py`
  - `src/war_room/settings.py`
  - `src/war_room/__main__.py`
- Regenerated the notebook so it uses the shared bootstrap/settings flow instead of `sys.path` mutation and ad hoc env loading.
- Updated `scripts/seed_cache_samples.py` to use the shared bootstrap path.
- Removed per-file `sys.path` mutation from the test suite and switched CI to package-installed test execution.
- Added foundation verification coverage:
  - `tests/test_settings.py`
  - `tests/test_bootstrap.py`
  - Exa client fallback-to-settings coverage in `tests/test_exa_client.py`
- Added runtime and repo-boundary documentation:
  - `docs/FOUNDATION.md`
  - placeholder `apps/`, `workers/`, and `packages/` directories
- Verification:
  - `.venv\Scripts\python -m war_room`
  - `.venv\Scripts\python -m pytest -q` -> `122 passed`

## Session 19 - PR #28 CI Fix
Date: 2026-03-06
Status: Complete

- Inspected failing GitHub Actions runs for PR `#28`.
- Identified one root cause across all three failing checks:
  - editable install step failed in Actions with `BackendUnavailable: Cannot import 'setuptools.build_meta'`
- Updated both workflows to install `setuptools>=69` before `pip install -e . --no-build-isolation`:
  - `.github/workflows/ci.yml`
  - `.github/workflows/exa-compat-matrix.yml`
- Verification:
  - `.venv\Scripts\python -m pytest -q` -> `122 passed`


## Session 20 - Carrier and Case-Law Quality Hardening
Date: 2026-03-07
Status: Complete

- Tightened carrier-result curation to drop low-value regulator navigation pages and prefer document-like regulatory evidence.
- Tightened case-law filtering to exclude commentary/explainer titles from case slots and prefer legal-host, citation-bearing authorities.
- Added stronger regression coverage in:
  - `tests/test_carrier.py`
  - `tests/test_caselaw.py`
  - `tests/test_caselaw_filter.py`
  - `tests/test_offline_demo_pack.py`
- Curated the committed offline demo fixtures so the sample carrier, caselaw, and citation-check payloads match the higher quality bar.
- Verification:
  - `.venv\Scripts\python -m pytest tests/test_carrier.py tests/test_caselaw.py tests/test_caselaw_filter.py tests/test_offline_demo_pack.py -q` -> `39 passed`
  - `.venv\Scripts\python -m pytest -q` -> `122 passed`



## Session 21 - Weather and Citation Quality Hardening
Date: 2026-03-07
Status: Complete

- Tightened weather-result curation to demote generic reference pages, prefer county/report-like sources, and filter navigation-heavy observations.
- Tightened citation spot-check ranking to require citation/name alignment before trusting a hit and to prefer legal-host matches over unrelated official pages.
- Added stronger regression coverage in:
  - `tests/test_weather.py`
  - `tests/test_citation_verify.py`
  - `tests/test_offline_demo_pack.py`
- Curated the committed weather fixture so the offline demo lane reflects the higher relevance bar.
- Verification:
  - `.venv\Scripts\python -m pytest tests/test_weather.py tests/test_citation_verify.py tests/test_offline_demo_pack.py -q` -> `34 passed`
  - `.venv\Scripts\python -m pytest -q` -> `128 passed`

## Session 22 - Memo Export Trust-Signal Pass
Date: 2026-03-07
Status: Complete

- Reworked markdown export structure to surface trust signals earlier in the memo.
- Added a top-of-memo trust snapshot with source counts, case counts, and citation-check summary.
- Added review-required flags so module warnings and citation uncertainty are visible before the appendix.
- Tightened section presentation:
  - carrier docs now render as highest-value documents,
  - citation confidence is summarized ahead of case detail,
  - source lists now include source-tier reasons.
- Added regression coverage in:
  - `tests/test_export.py`
  - `tests/test_memo_contracts.py`
- Verification:
  - `.venv\Scripts\python -m pytest tests/test_export.py tests/test_memo_contracts.py -q` -> `9 passed`
  - `.venv\Scripts\python -m pytest -q` -> `134 passed`

## Session 23 - Query Plan and Source-Tiering Hardening
Date: 2026-03-07
Status: Complete

- Tightened query-plan specificity so legal and carrier searches carry better domain hints and more matter-specific context.
- Added coverage-issue query deduplication to avoid repeated legal searches from near-duplicate intake phrasing.
- Expanded deterministic source-tier coverage for additional legal and carrier-adjacent domains.
- Switched source badge tokens to stable ASCII labels for cleaner downstream rendering and testing.
- Added regression coverage in:
  - `tests/test_query_plan.py`
  - `tests/test_source_scoring.py`
- Verification:
  - `.venv\Scripts\python -m pytest tests/test_query_plan.py tests/test_source_scoring.py -q` -> `23 passed`
  - `.venv\Scripts\python -m pytest -q` -> `134 passed`

## Session 24 - Adapter and Runtime Contract Consistency
Date: 2026-03-07
Status: Complete

- Added canonical intake/query-plan adapters and payload helpers in `src/war_room/models.py`:
  - `adapt_query_plan`
  - `case_intake_to_payload`
  - `query_spec_to_payload`
  - `query_plan_to_payloads`
- Updated runtime module imports so `CaseIntake` now comes from `war_room.models` instead of leaking through `query_plan.py`.
- Tightened render/query-plan boundaries:
  - `render_markdown_memo()` now advertises mixed dict/model inputs across the full memo contract,
  - `format_query_plan()` now normalizes mixed dict/model query payloads before formatting.
- Expanded regression coverage in:
  - `tests/test_models.py`
- Verification:
  - `$env:PYTHONPATH="src"; pytest -q tests/test_models.py tests/test_memo_contracts.py` -> `20 passed`
  - `$env:PYTHONPATH="src"; pytest -q` -> `151 passed`

## Session 25 - Evidence and Audit Schema Slice
Date: 2026-03-07
Status: Complete

- Added canonical evidence/audit entities in `src/war_room/models.py`:
  - `EvidenceItem`
  - `MemoClaim`
  - `ReviewEvent`
  - `ExportArtifact`
  - `RunAuditSnapshot`
- Added deterministic audit builders so the current V0 memo flow now emits a typed audit snapshot from existing module packs instead of introducing a parallel runtime.
- Wired markdown export to surface the new schema in output:
  - `Appendix: Evidence Index`
  - `Appendix: Review Log` when review events exist
- Added regression coverage in:
  - `tests/test_export.py`
  - `tests/test_memo_contracts.py`
- Verification:
  - `$env:PYTHONPATH="src"; python -m pytest -q tests/test_models.py tests/test_export.py tests/test_memo_contracts.py` -> `20 passed`
  - `$env:PYTHONPATH="src"; python -m pytest -q` -> `142 passed`

## Session 26 - Evidence Cluster Normalization Slice
Date: 2026-03-07
Status: Complete

- Extended the canonical audit schema in `src/war_room/models.py` with `EvidenceCluster` and added deterministic clustering across memo evidence items.
- Grouped evidence by durable identifiers in priority order:
  - case citation,
  - normalized URL,
  - derived module/type/title fallback.
- Updated markdown export so audit snapshots now render:
  - `Appendix: Evidence Clusters`
  - `Appendix: Evidence Index`
  - `Appendix: Review Log` when review events exist.
- Expanded regression coverage in:
  - `tests/test_export.py`
  - `tests/test_memo_contracts.py`
- Verification:
  - `$env:PYTHONPATH="src"; python -m pytest -q tests/test_export.py tests/test_memo_contracts.py` -> `14 passed`
  - `$env:PYTHONPATH="src"; python -m pytest -q` -> `143 passed`

## Session 27 - Claim Cluster Trace Slice
Date: 2026-03-07
Status: Complete

- Extended `MemoClaim` in `src/war_room/models.py` so each claim now carries `cluster_ids` in addition to raw `evidence_ids`.
- Wired audit assembly to resolve claim-level cluster references from the canonical evidence-cluster map.
- Updated markdown export in `src/war_room/export_md.py` to surface claim status plus evidence-cluster references within the memo sections.
- Expanded regression coverage in:
  - `tests/test_export.py`
  - `tests/test_memo_contracts.py`
- Verification:
  - `$env:PYTHONPATH="src"; python -m pytest -q tests/test_export.py tests/test_memo_contracts.py` -> `15 passed`
  - `$env:PYTHONPATH="src"; python -m pytest -q` -> `144 passed`

## Session 28 - Review Event Cluster Trace Slice
Date: 2026-03-07
Status: Complete

- Extended `ReviewEvent` in `src/war_room/models.py` so audit events now carry `related_cluster_ids` alongside `related_evidence_ids`.
- Wired review-event assembly to resolve grouped evidence references from the canonical evidence-cluster map.
- Updated markdown export in `src/war_room/export_md.py` so the review log now prints the related evidence clusters for each warning or citation issue.
- Expanded regression coverage in:
  - `tests/test_export.py`
  - `tests/test_memo_contracts.py`
- Verification:
  - `$env:PYTHONPATH="src"; python -m pytest -q tests/test_export.py tests/test_memo_contracts.py` -> `15 passed`
  - `$env:PYTHONPATH="src"; python -m pytest -q` -> `144 passed`

## Session 29 - Workflow IA Source of Truth
Date: 2026-03-08
Status: Complete

- Added `docs/V2_WORKFLOW_IA.md` as the canonical written spec for issue `#23`.
- Locked the end-to-end V2 workflow:
  - Intake
  - Research Plan Preview
  - Run Timeline
  - Evidence Board
  - Issue Workspace
  - Memo Composer
  - Export and Audit Bundle
- Defined the primary V2 operator as the first non-technical legal user, with partner and associate flows layered onto the same evidence-first workflow.
- Standardized V2 workflow contracts for:
  - canonical run states,
  - stage progress states,
  - review-required semantics,
  - evidence-to-claim traceability expectations.
- Recorded narrowing product decisions in `docs/DECISION_LOG.md`.
- Aligned roadmap and handoff docs with current repo state:
  - `144` passing tests,
  - `#22` marked complete in `docs/BUILD_CHECKLIST.md`,
  - bootstrap expectation clarified in `docs/ROADMAP.md`,
  - workflow spec linked from canonical-doc references.
- Verification:
  - `$env:PYTHONPATH="src"; pytest -q` -> `144 passed`

## Session 30 - Evidence Graph Source of Truth
Date: 2026-03-08
Status: Complete

- Added `docs/V2_EVIDENCE_SCHEMA.md` as the canonical written spec for issue `#24`.
- Defined the V2 evidence graph around one run-scoped canonical boundary linking:
  - intake,
  - research plan,
  - run and stage state,
  - retrieval tasks,
  - evidence items and clusters,
  - legal issues,
  - memo sections and claims,
  - review events,
  - export artifacts.
- Standardized durable-ID expectations so future V2 persistence does not depend on list ordering such as `cluster-1` or `evidence-3`.
- Added explicit schema-versioning rules for canonical graph envelopes, starting with `v2alpha1`.
- Mapped the current typed audit models to their intended V2 roles so `RunAuditSnapshot` remains useful as an audit bundle while no longer standing in for the full product persistence model.
- Linked the new schema spec from roadmap and handoff docs, and updated `docs/V2_ISSUE_MAP.md` so downstream work uses it as the source of truth.
- Verification:
  - `$env:PYTHONPATH="src"; pytest -q` -> `144 passed`


## Session 31 - Typed Graph Contract Slice
Date: 2026-03-08
Status: Complete

- Extended `src/war_room/models.py` with the next `#6` typed-contract slice from the `#24` schema spec.
- Added canonical typed entities for:
  - `ResearchPlan`
  - `Run`
  - `RunStage`
  - `MemoSection`
- Added envelope-level `schema_version` support to:
  - `MemoRenderInput`
  - `RunAuditSnapshot`
- Added typed adapter and payload helpers for the new graph models and exported them through `war_room.__init__`.
- Kept the current memo/export flow intact while allowing the audit snapshot path to carry explicit schema versions.
- Expanded regression coverage in:
  - `tests/test_models.py`
  - `tests/test_memo_contracts.py`
- Verification:
  - `$env:PYTHONPATH="src"; pytest -q tests/test_models.py tests/test_memo_contracts.py` -> `18 passed`
  - `$env:PYTHONPATH="src"; pytest -q` -> `149 passed`


## Session 32 - Issue and Authority Contract Slice
Date: 2026-03-08
Status: Complete

- Extended `src/war_room/models.py` with the next `#6` typed-contract slice for issue-oriented review.
- Added canonical typed entities for:
  - `LegalIssue`
  - `CaseCandidate`
- Added typed adapter and payload helpers for those entities and exported them through `war_room.__init__`.
- Kept the current `CaseIssue` / `CaseEntry` export-facing shapes intact while introducing the canonical V2 issue/workspace contracts in parallel.
- Expanded regression coverage in:
  - `tests/test_models.py`
- Verification:
  - `$env:PYTHONPATH="src"; pytest -q tests/test_models.py tests/test_memo_contracts.py` -> `20 passed`
  - `$env:PYTHONPATH="src"; pytest -q` -> `151 passed`


## Session 33 - Run Lifecycle Contract Slice
Date: 2026-03-08
Status: Complete

- Extended `src/war_room/models.py` with the next `#6` typed-contract slice for run lifecycle and retrieval work.
- Added canonical typed entities for:
  - `RunEvent`
  - `RetrievalTask`
- Added typed adapter and payload helpers for those entities and exported them through `war_room.__init__`.
- Expanded regression coverage in:
  - `tests/test_models.py`
- Verification:
  - `$env:PYTHONPATH="src"; pytest -q tests/test_models.py tests/test_memo_contracts.py` -> `23 passed`
  - `python -m compileall src/war_room` -> success
  - `$env:PYTHONPATH="src"; pytest -q` -> `154 passed`


## Session 34 - Retrieval Provider Contract Slice
Date: 2026-03-08
Status: Complete

- Added `src/war_room/retrieval.py` as the first `#7` boundary layer for retrieval providers.
- Introduced:
  - `RetrievalProvider` protocol
  - `RetrievalSearchRequest`
  - `RetrievalContentsRequest`
  - `query_spec_to_retrieval_task()`
  - `execute_retrieval_search()`
  - `fetch_retrieval_contents()`
- Marked `ExaClient` as the current `provider_name="exa"` adapter and added Exa-backed compatibility coverage.
- Updated weather, carrier, caselaw, and citation-verification module type boundaries to accept the provider protocol instead of a concrete Exa client.
- Expanded regression coverage in:
  - `tests/test_retrieval_contracts.py`
  - `tests/test_exa_adapter_contract.py`
- Verification:
  - `$env:PYTHONPATH="src"; pytest -q tests/test_retrieval_contracts.py tests/test_exa_adapter_contract.py tests/test_exa_client.py tests/test_weather.py tests/test_carrier.py tests/test_caselaw.py tests/test_citation_verify.py tests/test_models.py tests/test_memo_contracts.py` -> `69 passed`
  - `python -m compileall src/war_room` -> success
  - `$env:PYTHONPATH="src"; pytest -q` -> `159 passed`


## Session 35 - Notebook Retrieval State Slice
Date: 2026-03-08
Status: Complete

- Extended the `#7` retrieval seam so notebook-era module loops now construct canonical `RetrievalTask` records per query-plan row and emit `RunEvent` attempt metadata.
- Added notebook-oriented retrieval helpers in `src/war_room/retrieval.py` for:
  - deterministic notebook run IDs
  - task execution with completion/degraded/failed state
  - per-attempt run-event emission
- Updated weather, carrier, and caselaw module payloads to carry `retrieval_tasks` and `run_events` without breaking legacy omission of empty fields.
- Extended `RunAuditSnapshot` aggregation to preserve retrieval-task and run-event state from module payloads.
- Expanded regression coverage in:
  - `tests/test_retrieval_contracts.py`
  - `tests/test_weather.py`
  - `tests/test_carrier.py`
  - `tests/test_caselaw.py`
  - `tests/test_memo_contracts.py`
- Verification:
  - `$env:PYTHONPATH="src"; pytest -q tests/test_retrieval_contracts.py tests/test_weather.py tests/test_carrier.py tests/test_caselaw.py tests/test_memo_contracts.py tests/test_pack_adapters.py tests/test_exa_adapter_contract.py tests/test_models.py` -> `65 passed`
  - `python -m compileall src/war_room` -> success
  - `$env:PYTHONPATH="src"; pytest -q` -> `167 passed`


## Session 36 - Citation Verify Retrieval State Slice
Date: 2026-03-08
Status: Complete

- Extended the `#7` retrieval-state path into `src/war_room/citation_verify.py` so citation checks now construct canonical `RetrievalTask` records and emit `RunEvent` attempt metadata.
- Added retrieval-state support to `CitationVerifyPack` and extended `RunAuditSnapshot` aggregation to include citation-verify retrieval tasks and run events.
- Populated `raw_artifact_refs` from returned hit URLs during retrieval-task execution so successful attempts retain lightweight artifact linkage.
- Expanded regression coverage in:
  - `tests/test_citation_verify.py`
  - `tests/test_retrieval_contracts.py`
  - `tests/test_memo_contracts.py`
- Verification:
  - `$env:PYTHONPATH="src"; pytest -q tests/test_citation_verify.py tests/test_memo_contracts.py tests/test_retrieval_contracts.py tests/test_pack_adapters.py` -> `31 passed`
  - `$env:PYTHONPATH="src"; pytest -q` -> `168 passed`

## Session 37 - Project Health Audit and Docs Realignment
Date: 2026-03-10
Status: Complete

- Audited the canonical docs against local repo state for bootstrap, roadmap, and repo-shape drift.
- Reconfirmed the supported test posture and documented that raw-checkout `pytest -q` is not a supported contributor path.
- Added `docs/PROJECT_HEALTH_AUDIT_2026-03-10.md` with:
  - implemented-now vs planned-V2 status memo,
  - docs inconsistency list,
  - contributor friction notes,
  - next-2-weeks action plan.
- Realigned the core builder docs so they tell the same story:
  - `README.md`
  - `docs/HANDOFF.md`
  - `docs/ROADMAP.md`
  - `docs/FOUNDATION.md`
  - `docs/V2_ISSUE_MAP.md`
  - `docs/BUILD_CHECKLIST.md`
- Added `D017` to `docs/DECISION_LOG.md` to lock the rule that written V2 specs and placeholder directories are not the same thing as shipped runtime surfaces.
- Verification:
  - `$env:PYTHONPATH="src"; pytest -q` -> `168 passed`

## Session 38 - Issue #27 First-Pass Release Rubric
Date: 2026-03-10
Status: Complete

- Added `docs/V2_RELEASE_RUBRIC.md` as the first-pass v0.1 output of `#27`.
- Defined the shared quality dimensions for release decisions:
  - reliability,
  - evidence quality,
  - trust and provenance,
  - workflow usability,
  - review and export quality,
  - operational readiness,
  - security and governance.
- Defined release levels and gates for:
  - demo-ready,
  - beta-ready,
  - pilot-ready.
- Added a current-state baseline scorecard for the repo as of March 10, 2026.
- Synced the canonical docs so `#27` now reads as first-pass landed but still open for calibration:
  - `README.md`
  - `docs/HANDOFF.md`
  - `docs/ROADMAP.md`
  - `docs/BUILD_CHECKLIST.md`
  - `docs/V2_ISSUE_MAP.md`
- Verification:
  - `$env:PYTHONPATH="src"; pytest -q` -> `168 passed`

## Session 39 - Issue #27 Scorecard Artifact Generator
Date: 2026-03-11
Status: Complete

- Added `src/war_room/release_scorecard.py` to operationalize the `#27` rubric as a repeatable local artifact instead of docs-only guidance.
- Added a lightweight CLI:
  - `python -m war_room.release_scorecard --candidate <label> --verification-summary "<result>"`
- The generator writes both Markdown and JSON artifacts into `runs/release_scorecards/` using the existing bootstrap/runtime settings.
- Seeded the artifact with the current demo-ready baseline so release discussions can attach to concrete files while `#8`, `#9`, and `#19` remain open.
- Added regression coverage in:
  - `tests/test_release_scorecard.py`
- Updated `docs/V2_RELEASE_RUBRIC.md` and `docs/BUILD_CHECKLIST.md` to point at the new local workflow.

## Session 40 - Issue #8 Backup Fixture Scenario
Date: 2026-03-11
Status: Complete

- Added a second committed fixture scenario under `cache_samples/tx_hail_allstate_tarrant/` to broaden the offline validation lane beyond the Milton / Citizens / Pinellas baseline.
- Added matching root-level cache artifacts so the backup scenario resolves through the existing cache-first runtime path, not only through folder-level fixture reads.
- Added `eval/intakes/tx_hail_allstate_tarrant.json` so the backup scenario also exists as a canonical intake payload.
- Expanded `tests/test_offline_demo_pack.py` to validate all committed scenarios and to exercise cache-first runtime resolution for each scenario.
- Expanded `tests/test_intake_validation.py` so committed eval intakes are validated against the canonical schema.

## Session 41 - Issue #9 Fixture Smoke CI Gate
Date: 2026-03-11
Status: Complete

- Updated GitHub Actions workflow triggers so `codex/**` branch pushes receive the same CI coverage as `feat/**`, `fix/**`, and `chore/**` branches.
- Added an explicit `Offline Fixture Smoke` job to `.github/workflows/ci.yml` that runs:
  - `pytest -q tests/test_offline_demo_pack.py tests/test_intake_validation.py`
- Kept the existing full fresh-env test job and exa compatibility matrix intact so this remains a narrow CI-signal improvement rather than a workflow redesign.

## Session 42 - Issue #8 Louisiana Stretch Fixture
Date: 2026-03-11
Status: Complete

- Added a third committed fixture scenario under `cache_samples/ida_lloyds_orleans/` so the offline lane now covers Florida, Texas, and Louisiana.
- Added matching root-level cache artifacts plus `eval/intakes/ida_lloyds_orleans.json` so the Louisiana scenario resolves through the cache-first runtime and the canonical intake contract.
- Expanded the shared scenario map in `tests/test_offline_demo_pack.py` so the existing offline fixture validation now exercises all three committed jurisdictions.

## Session 43 - Issue #27 Fixture-Calibrated Scorecard
Date: 2026-03-11
Status: Complete

- Updated `src/war_room/release_scorecard.py` so scorecard artifacts inspect committed fixture scenario folders under `cache_samples/` instead of relying only on a hardcoded baseline narrative.
- Added fixture coverage to the scorecard JSON/Markdown artifact, including scenario count, covered states, and per-scenario issue/citation-check summaries.
- Expanded `tests/test_release_scorecard.py` so the scorecard generator is validated against the committed three-scenario fixture set.
- Updated `docs/V2_RELEASE_RUBRIC.md` so the local artifact workflow explicitly calls out fixture-coverage capture as part of `#27` calibration.


## Session 44 - Closing Sync and Clean Repo State
Date: 2026-03-11
Status: Complete

- Synced the canonical docs to the current repo state: `178` passing tests, three committed fixture scenarios (FL/TX/LA), explicit fixture smoke CI, and fixture-calibrated release-scorecard artifacts.
- Added `D018` to `docs/DECISION_LOG.md` so release scorecards derive fixture coverage from committed `cache_samples/` scenario folders instead of a hardcoded narrative.
- Cleaned the committed notebook file back to a source-controlled state by stripping execution counts and outputs before session close.
- Added an explicit `pytest-asyncio` loop-scope setting in `pyproject.toml` so the supported verification path is warning-free.
- Verification:
  - `$env:PYTHONPATH="src"; pytest -q` -> `178 passed`

## Session 45 - Issue #27 Verification Command Alignment
Date: 2026-03-17
Status: Complete

- Updated `src/war_room/release_scorecard.py` so the default verification command recorded in scorecard artifacts is `pytest -q`, matching the repo's supported editable-install test path instead of the ad hoc `PYTHONPATH=src` lane.
- Expanded `tests/test_release_scorecard.py` with an explicit regression check for the default verification command.
- Updated `docs/V2_RELEASE_RUBRIC.md` so the documented local scorecard workflow matches the code and canonical repo guidance.

## Session 46 - Collaborator-Facing Doc Readability Cleanup
Date: 2026-03-17
Status: Complete

- Rewrote `docs/METHOD.md` in clean ASCII so the methodology narrative no longer contains mojibake and now matches current badge/status terminology.
- Rewrote `docs/DEMO_SCRIPT.md` in clean ASCII so stakeholder-facing demo guidance reads cleanly instead of showing broken punctuation and symbol substitutions.
- Updated `README.md` so the supported local setup path is explicit for Windows PowerShell and macOS/Linux/Git Bash, clarified the supported editable-install test path, tightened the `#23`/`#24` status wording, and updated the current-state test count from `178` to `179`.

## Session 47 - Issue #27 Threshold Calibration
Date: 2026-03-18
Status: Complete

- Updated `src/war_room/release_scorecard.py` so the local scorecard computes explicit demo-ready calibration thresholds instead of relying only on narrative baseline text.
- Added measurable fixture thresholds for:
  - committed scenario count,
  - state coverage,
  - module completeness,
  - issue-bucket breadth,
  - citation-check breadth.
- Promoted threshold results into the emitted Markdown and JSON artifacts and wired a must-pass gate for calibrated fixture coverage.
- Expanded `tests/test_release_scorecard.py` to lock threshold rendering, calibrated score changes, and failed-verification behavior.
- Synced the canonical docs so `#27` now reads as threshold-calibrated while CI and pilot operationalization remain open:
  - `README.md`
  - `docs/HANDOFF.md`
  - `docs/ROADMAP.md`
  - `docs/BUILD_CHECKLIST.md`
  - `docs/V2_ISSUE_MAP.md`
  - `docs/V2_RELEASE_RUBRIC.md`
- Verification:
  - `$env:PYTHONPATH="src"; pytest -q tests/test_release_scorecard.py` -> `5 passed`
  - `$env:PYTHONPATH="src"; pytest -q` -> `180 passed`

## Session 48 - Fixture Badge Token Cleanup
Date: 2026-03-18
Status: Complete

- Normalized the committed Milton fixture scenario under `cache_samples/milton_citizens_pinellas/` so badge tokens now use the stable ASCII values expected by the current source-scoring and citation-check contracts.
- Replaced placeholder badge values in:
  - `weather.json`
  - `carrier.json`
  - `caselaw.json`
  - `citation_verify.json`
- Expanded `tests/test_offline_demo_pack.py` with a cross-scenario regression guard so committed fixture badges must stay within the stable source and citation badge vocabularies.
- Synced the current-state docs to the new suite count:
  - `README.md`
  - `docs/HANDOFF.md`
  - `docs/ROADMAP.md`
  - `docs/V2_RELEASE_RUBRIC.md`
- Verification:
  - `$env:PYTHONPATH="src"; pytest -q tests/test_offline_demo_pack.py` -> `25 passed`
  - `$env:PYTHONPATH="src"; pytest -q` -> `186 passed`

## Session 48 - Issue #9 Release Scorecard CI Artifact
Date: 2026-03-18
Status: Complete

- Updated `.github/workflows/ci.yml` so the fresh-env test job now exposes its verification summary and a dedicated release-scorecard job can generate the calibrated artifact in CI.
- Added CI artifact upload for the generated Markdown and JSON scorecard under `runs/release_scorecards/`.
- Synced the rubric and roadmap docs so `#9` now reads as release-scorecard artifact emission having landed, while broader CI layering remains open.
- Verification:
  - `$env:PYTHONPATH="src"; pytest -q` -> `180 passed`
  - `python -m war_room.release_scorecard --candidate codex/quality-hardening --verification-summary "180 passed"`

## Session 49 - Demo Preflight Smoke Command
Date: 2026-03-18
Status: Complete

- Added `src/war_room/preflight.py` as the deterministic offline smoke layer for the demo path.
- Wired `python -m war_room --preflight` through the shared bootstrap CLI so contributors can verify the offline demo lane without opening Jupyter first.
- The smoke command now checks committed scenario coverage, cache-backed module loading, citation-check summary integrity, and memo rendering for the committed fixture scenarios.
- Added regression coverage in:
  - `tests/test_preflight.py`
- Updated the canonical docs so the new preflight command is visible in the supported run path and build checklist:
  - `README.md`
  - `docs/HANDOFF.md`
  - `docs/ROADMAP.md`
  - `docs/BUILD_CHECKLIST.md`
- Verification:
  - `$env:PYTHONPATH="src"; pytest -q tests/test_preflight.py tests/test_release_scorecard.py` -> `8 passed`
  - `$env:PYTHONPATH="src"; pytest -q` -> `186 passed`
## Session 50 - Supported Local Verification Wrapper
Date: 2026-03-18
Status: Complete

- Extended `war_room.bootstrap` so `python -m war_room --verify` now runs the supported local verification path in one command.
- The wrapper runs:
  - deterministic offline preflight
  - `pytest -q`
- Expanded `tests/test_bootstrap.py` to lock the subprocess invocation and nonzero exit behavior.
- Updated the canonical bootstrap docs so the wrapper is part of the supported contributor path:
  - `README.md`
  - `docs/FOUNDATION.md`
  - `docs/HANDOFF.md`
  - `docs/BUILD_CHECKLIST.md`
- Verification:
  - `$env:PYTHONPATH="src"; pytest -q tests/test_bootstrap.py tests/test_preflight.py` -> `7 passed`
  - `$env:PYTHONPATH="src"; pytest -q` -> `188 passed`
  - `$env:PYTHONPATH="src"; python -m war_room --verify` -> success

## Session 51 - Issue #9 Release Scorecard CI Enforcement
Date: 2026-03-18
Status: Complete

- Tightened `.github/workflows/ci.yml` so the release-scorecard job now validates the generated JSON artifact before upload.
- The CI check now fails if:
  - calibration thresholds are missing,
  - any calibrated threshold fails,
  - the demo-ready fixture gate fails,
  - or the scorecard decision is not `Ship`.
- Kept the existing artifact upload path intact so CI evidence is both generated and enforced.
- Verification:
  - `$env:PYTHONPATH="src"; pytest -q` -> `188 passed`
  - `$env:PYTHONPATH="src"; python -m war_room.release_scorecard --candidate codex/quality-hardening --verification-summary "188 passed"` -> success

## Session 52 - Issue #6 Review and Export Graph Linkage
Date: 2026-03-18
Status: Complete

- Extended `src/war_room/models.py` with the next `#6` typed-contract slice for run-scoped review and export linkage.
- Added stable linkage fields to:
  - `ReviewEvent`
  - `ExportArtifact`
- The audit snapshot builder now derives:
  - a deterministic run ID from intake data,
  - stable section IDs from memo section titles,
  - and run-scoped linkage between review events, memo claims, and the exported memo artifact.
- Expanded regression coverage in:
  - `tests/test_models.py`
  - `tests/test_memo_contracts.py`
- Verification:
  - `$env:PYTHONPATH="src"; pytest -q tests/test_models.py tests/test_memo_contracts.py` -> `25 passed`
  - `$env:PYTHONPATH="src"; pytest -q` -> `189 passed`

## Session 53 - Issue #7 Deterministic Retrieval Task Timing
Date: 2026-03-18
Status: Complete

- Tightened `src/war_room/retrieval.py` so `execute_retrieval_task()` now uses the provided `now` value consistently across completed, degraded, and failed execution paths.
- This keeps `RetrievalTask.completed_at` and emitted `RunEvent.created_at` values deterministic for contract tests and replayable audit snapshots.
- Expanded regression coverage in:
  - `tests/test_retrieval_contracts.py`
- Verification:
  - `$env:PYTHONPATH="src"; pytest -q tests/test_retrieval_contracts.py tests/test_citation_verify.py` -> `18 passed`
  - `$env:PYTHONPATH="src"; pytest -q` -> `189 passed`

## Session 54 - Issue #8 Texas Matching Dispute Fixture
Date: 2026-03-18
Status: Complete

- Added a fourth committed offline runtime fixture lane for a Texas hail matching dispute against Allstate Texas Lloyds, including:
  - a committed eval intake in `eval/intakes/`
  - cache-backed weather, carrier, and case-law fixture payloads in `cache_samples/`
- Expanded fixture regression coverage so the offline lane now checks:
  - the new intake file is schema-valid,
  - committed carrier fixtures include policy-type metadata,
  - the matching-dispute scenario resolves end-to-end through cache-first runtime execution,
  - and preflight assertions derive scenario counts from the shared scenario map instead of hardcoded values.
- Synced the canonical docs to the repo state at that point:
  - `README.md`
  - `docs/HANDOFF.md`
  - `docs/FOUNDATION.md`
  - `docs/BUILD_CHECKLIST.md`
  - `docs/ROADMAP.md`
  - `docs/V2_ISSUE_MAP.md`
  - `docs/V2_RELEASE_RUBRIC.md`
- Verification:
  - `$env:PYTHONPATH="src"; pytest -q tests/test_intake_validation.py tests/test_offline_demo_pack.py tests/test_preflight.py` -> `41 passed`
  - `$env:PYTHONPATH="src"; pytest -q` -> `190 passed`
  - `$env:PYTHONPATH="src"; python -m war_room --preflight --json` -> success (`scenario_count: 3`)

## Session 55 - Issue #8 Fixture Directory Alignment for Preflight and Scorecard
Date: 2026-03-18
Status: Complete

- Promoted the Texas matching-dispute cache assets into a full committed scenario directory at `cache_samples/tx_hail_allstate_tarrant_dp3/`.
- Restored canonical cache-first runtime coverage in `tests/test_offline_demo_pack.py` so all committed scenario directories execute through the same runtime path.
- Tightened `src/war_room/release_scorecard.py` so scorecard fixture counting now matches preflight semantics by counting only complete scenario directories with all four module fixtures.
- Updated regression coverage in:
  - `tests/test_offline_demo_pack.py`
  - `tests/test_preflight.py`
  - `tests/test_release_scorecard.py`
- Synced the canonical docs so `#8`, preflight, and `#27` all describe the same four-scenario committed fixture set:
  - `README.md`
  - `docs/HANDOFF.md`
  - `docs/FOUNDATION.md`
  - `docs/BUILD_CHECKLIST.md`
  - `docs/ROADMAP.md`
  - `docs/V2_ISSUE_MAP.md`
  - `docs/V2_RELEASE_RUBRIC.md`
- Verification:
  - `$env:PYTHONPATH="src"; pytest -q tests/test_offline_demo_pack.py tests/test_preflight.py tests/test_release_scorecard.py` -> `41 passed`
  - `$env:PYTHONPATH="src"; pytest -q` -> `197 passed`
  - `$env:PYTHONPATH="src"; python -m war_room --preflight --json` -> success (`scenario_count: 4`)
  - `$env:PYTHONPATH="src"; python -m war_room.release_scorecard --candidate codex/quality-hardening --verification-summary "197 passed"` -> success

## Session 56 - Issue Status and Docs Sync
Date: 2026-03-18
Status: Complete

- Audited the live GitHub issue tracker against the canonical roadmap docs after the merge back to `main`.
- Confirmed issue drift: `#23` and `#24` were still open in GitHub even though the repo already treated them as completed written source-of-truth specs.
- Synced the canonical status docs so `README.md`, `docs/HANDOFF.md`, `docs/ROADMAP.md`, `docs/V2_ISSUE_MAP.md`, `docs/PROJECT_HEALTH_AUDIT_2026-03-10.md`, and `CLAUDE.md` all describe `#23` and `#24` as complete-and-closed definition issues.
- Left `#27`, `#6`, `#7`, `#8`, and `#9` open because the docs still show real remaining implementation and operationalization scope.

## Session 57 - Blueprint Follow-Up Sync
Date: 2026-03-18
Status: Complete

- Updated `docs/V2_BLUEPRINT.md` so the immediate-next-actions section no longer treats `#23` and `#24` as future work.
- Confirmed the remaining active foundation sequence still centers on `#27` plus the unfinished `#6` to `#9` slices before major V2 implementation.

## Session 58 - Retrieval Quality Tranche 1
Date: 2026-03-19
Status: Complete

- Implemented a first coherent retrieval-quality tranche across the notebook-era runtime without breaking offline/demo support:
  - stronger deterministic source-class tagging in `src/war_room/source_scoring.py`
  - primary-authority-biased case-law ranking and citation-based dedup in `src/war_room/caselaw_module.py`
  - safer citation-check degradation with structured confidence/reason fields in `src/war_room/citation_verify.py`
  - lightweight run-level quality telemetry plus explainable evidence clustering in `src/war_room/models.py`
  - memo trust-snapshot and quality appendix updates in `src/war_room/export_md.py`
- Case-law outputs now distinguish authority classes more cleanly:
  - `court_opinion`
  - `statute_regulation`
  - `government_guidance`
  - `commentary`
  - `news`
  - `other`
- Core case-law ranking now prefers primary authorities over commentary-style legal explainers and collapses duplicate authorities by citation before memo assembly.
- Citation spot-check outputs now keep the existing top-level buckets (`verified`, `uncertain`, `not_found`) but add:
  - `confidence`
  - `status_reason`
  - `trust_explanation`
  - `source_tier`
  - `source_class`
  - `is_primary_authority`
- Audit snapshots now emit a structured `quality_snapshot` with:
  - normalized source-class counts
  - primary vs secondary source counts
  - citation status and reason buckets
  - evidence item / cluster counts
  - grouped-evidence count
- Memo export now surfaces the new quality hooks in:
  - `Trust Snapshot`
  - `Appendix: Quality Snapshot`
  - expanded citation review table columns
  - evidence-cluster member counts
- Added regression coverage in:
  - `tests/test_source_scoring.py`
  - `tests/test_caselaw.py`
  - `tests/test_citation_verify.py`
  - `tests/test_export.py`
  - `tests/test_memo_contracts.py`
- Why this tranche:
  - the local live retrieval notebook already worked end-to-end
  - the largest trust gaps were authority mixing, weak citation uncertainty routing, noisy duplicate support, and missing retrieval-quality telemetry
- What remains:
  - broader fixture refresh so committed samples expose the richer source-class and citation-reason fields
  - additional evidence-normalization work under `#12` beyond citation/url grouping
  - stronger benchmark and release-evidence wiring for these new quality signals
- Recommended next sprint / issue:
  - continue `#12` evidence normalization with fixture-backed output calibration
  - then tighten `#13` and `#14` against refreshed live/fixture comparisons
- Verification:
  - `$env:PYTHONPATH="src"; pytest -q tests/test_source_scoring.py tests/test_caselaw.py tests/test_citation_verify.py tests/test_export.py tests/test_memo_contracts.py` -> `52 passed`
  - `.venv\Scripts\python.exe -m war_room --verify` -> `202 passed` and offline preflight success

## Session 59 - Retrieval Quality Tranche 2
Date: 2026-03-19
Status: Complete

- Implemented the next retrieval-quality tranche as a normalization-first follow-through on `#12`, with narrow supporting work in `#13`, `#14`, and lightweight `#17` telemetry:
  - canonical authority-key normalization in `src/war_room/models.py`
  - provenance-aware evidence clustering and dedup metrics in `src/war_room/models.py`
  - tighter court-host source classification in `src/war_room/source_scoring.py`
  - citation-spacing normalization and ambiguity tracking in `src/war_room/citation_verify.py`
  - stronger thin-metadata penalties in `src/war_room/caselaw_module.py`
  - memo/export visibility for canonical-authority counts, provenance counts, and alternate citation candidates in `src/war_room/export_md.py`
- What changed:
  - evidence items now carry deterministic `authority_key` values where possible
  - evidence clusters now preserve `provenance_urls` and `authority_key`
  - quality snapshots now report:
    - `raw_evidence_count`
    - `normalized_authority_count`
    - `duplicate_authority_count`
    - `provenance_link_count`
  - citation checks now normalize reporter spacing before match evaluation and report `alternate_candidate_count`
  - court-host `.gov` pages are no longer treated as primary law unless the path or title actually looks opinion-like
- Why:
  - tranche 1 improved ranking and telemetry, but normalization still leaned cluster-first instead of canonical-authority-first
  - citation ambiguity still needed more explicit routing
  - official court hosts needed a narrower primary-authority rule to avoid over-trusting search or lookup pages
- Added/updated regression coverage in:
  - `tests/test_source_scoring.py`
  - `tests/test_caselaw.py`
  - `tests/test_citation_verify.py`
  - `tests/test_export.py`
  - `tests/test_memo_contracts.py`
- Remaining risks:
  - committed fixture payloads still do not expose the richer optional normalization/citation metadata
  - the release-scorecard path does not yet consume the new dedup/provenance metrics
  - preflight intentionally still checks only the stable top-level section set, not the richer appendix surface
- Recommended next issue / sprint:
  - continue `#12` with fixture-backed canonical-evidence calibration and optional fixture refresh
  - then fold the new dedup/provenance metrics into `#17` scorecard and release-evidence reporting
- Verification:
  - `$env:PYTHONPATH="src"; pytest -q tests/test_source_scoring.py tests/test_caselaw.py tests/test_citation_verify.py tests/test_export.py tests/test_memo_contracts.py` -> `58 passed`
  - `.venv\Scripts\python.exe -m war_room --verify` -> `208 passed`, offline preflight success
  - `.venv\Scripts\python.exe -m war_room --preflight --json` -> success (`scenario_count: 4`, `passed: true`)

## Session 60 - Five-Storm Scenario Registry
Date: 2026-03-19
Status: Complete

- Added a canonical top-level `scenarios/` registry for five curated Florida hurricane benchmark matters:
  - Hurricane Milton / Pinellas
  - Hurricane Ian / Lee
  - Hurricane Irma / Monroe
  - Hurricane Michael / Bay
  - Hurricane Idalia / Taylor
- Added `src/war_room/scenarios.py` with shared loader and validation helpers:
  - `list_scenarios()`
  - `load_scenario()`
  - `load_scenario_for_fixture_case()`
  - `validate_scenario()`
  - `default_scenario_id()`
- Kept the canonical `CaseIntake` schema strict and backward-compatible by validating scenario intake fields through the existing intake contract instead of widening `CaseIntake` for scenario-only metadata.
- Simplified the notebook so Cell 2 now uses:
  - `SCENARIO_ID`
  - shared scenario loading
  - optional `SCENARIO_OVERRIDES`
  - a default `case_key` derived from the selected scenario
- Preserved the current offline demo path:
  - the default notebook scenario remains Milton
  - Milton still maps to the committed offline fixture key `milton_citizens_pinellas`
  - preflight now prefers registry-backed intake data for matching fixture scenarios instead of a hard-coded fallback payload
- Added regression coverage in:
  - `tests/test_scenarios.py`
  - `tests/test_preflight.py`
- Why:
  - the benchmark matters now live in one stable source of truth instead of being split across notebook cells, test constants, and preflight fallback code
  - notebook, tests, and future app code can now load the same curated intake definitions through one reusable module
- Remaining risks:
  - only the Milton benchmark currently has committed offline cache fixtures
  - the other four Florida scenarios are registry-ready for notebook and future app use, but still rely on live retrieval or future fixture seeding for full offline execution
  - `eval/intakes/` still exists for the separate live-eval lane and is intentionally not replaced in this slice
- Recommended next issue / sprint:
  - seed committed cache fixtures for the remaining four Florida hurricane benchmarks under `#8`
  - then teach release-scorecard and benchmark reporting to surface registry coverage alongside cache fixture coverage

## Session 61 - Scenario Settings Stability
Date: 2026-03-19
Status: Complete

- What broke:
  - the new scenario-selection notebook cell directly referenced `SETTINGS.live_retrieval_enabled`
  - if the bootstrap/config cell had not already run, notebook execution could fail with `NameError: SETTINGS is not defined`
  - the tracked notebook had also drifted into an inconsistent state with both the new scenario cell and stale hard-coded intake/export cells still present
- Root cause:
  - scenario prep logic lived partly in notebook globals instead of one reusable runtime helper
  - the notebook assumed cell execution order for settings/bootstrap state instead of resolving runtime context safely
- What changed:
  - added `src/war_room/notebook_runtime.py` as the shared notebook-support layer
  - added helper APIs for:
    - `ensure_runtime_context()`
    - `resolve_live_retrieval_enabled()`
    - `load_selected_scenario()`
    - `build_intake_from_scenario()`
    - `scenario_warning_message()`
    - `prepare_notebook_scenario()`
  - notebook scenario prep now bootstraps safely even if `SETTINGS` is missing from globals
  - notebook scenario warnings are now deterministic:
    - Milton stays silent in offline mode because it is fixture-backed
    - Ian / Irma / Michael / Idalia warn in cache-only mode
    - those warnings clear when live retrieval is enabled
  - rewrote the tracked notebook back to one clean path:
    - bootstrap/config cell
    - helper-driven scenario cell
    - no stale hard-coded `CaseIntake(...)` cell
    - no duplicate export cell
  - later notebook cells now read runtime settings from `ensure_runtime_context()` instead of assuming earlier globals exist
- Tests added or expanded:
  - `tests/test_notebook_runtime.py`
  - `tests/test_scenarios.py`
  - existing preflight/bootstrap/settings coverage re-run against the new helper flow
- Remaining limitations:
  - only Milton is currently fully offline-ready because it is the only Florida benchmark with committed cache fixtures
  - non-Milton Florida scenarios still need live retrieval or future fixture seeding for end-to-end cache-only runs
  - the notebook still assumes scenario/intake cells run before module cells, which is reasonable for the demo surface; this fix targeted settings/bootstrap robustness rather than arbitrary cell-order support for every downstream cell
- Recommended next step:
  - seed committed cache fixtures for the remaining four Florida hurricane benchmarks under `#8`
  - then add a small benchmark-facing summary surface so notebook users can see offline-ready vs live-only scenario status before execution

## Session 62 - Foundation Focus Slices
Date: 2026-03-20
Status: Complete

- Landed three bounded foundation slices on `codex/foundation-focus-slices`:
  - release-scorecard artifacts now include scenario-registry coverage alongside committed fixture coverage
  - notebook and preflight flows now surface explicit scenario availability (`offline-ready` vs `live-only`)
  - weather, carrier, and caselaw builders now accept a shared query plan instead of always regenerating module-local slices
- Exported the new query-plan and scenario-availability helpers from `war_room.__init__` so later callers can consume the shared seams through the package surface.
- Synced the canonical docs to the current verified test baseline (`235` passing under the supported path).
- Why:
  - `#27` and `#9` need more repeatable release evidence than fixture counts alone
  - notebook-era flows still needed clearer visibility into which scenarios are cache-only safe
  - `#6` and `#7` still had needless query-plan regeneration across modules instead of one reusable plan seam
- Verification:
  - `$env:PYTHONPATH='src'; pytest -q` -> `235 passed`
  - `$env:PYTHONPATH='src'; python -m war_room --verify` -> passed, offline preflight success
- Commits pushed on this branch:
  - `74dbea2` `feat: add registry coverage to release scorecards`
  - `1b4bd5e` `feat: share query plans across module builders`
  - `844a7fe` `feat: surface scenario availability in demo flows`

## Session 63 - Shared Research Plan Through Demo Callers
Date: 2026-03-20
Status: Complete

- Threaded one canonical `ResearchPlan` through the remaining demo callers instead of regenerating query slices at the preflight call site and tracked notebook flow.
- What changed:
  - `src/war_room/preflight.py` now builds `research_plan = build_research_plan(intake)` once per scenario and passes `research_plan.query_plan` into weather, carrier, caselaw, and memo rendering.
  - `notebooks/01_case_war_room.ipynb` now builds the shared research plan once in the query-plan cell and reuses `queries` for downstream module calls.
  - regression coverage now checks the tracked notebook content and preflight runtime so this seam does not drift back to per-module plan regeneration.
- Why:
  - the module seam for shared query plans had landed, but the actual demo callers still regenerated plan state
  - this closes the loop on the immediate next recommendation from the previous session and pushes one layer higher in the orchestration stack
- Verification:
  - `$env:PYTHONPATH='src'; pytest -q tests/test_preflight.py tests/test_scenarios.py` -> `13 passed`
  - `$env:PYTHONPATH='src'; pytest -q` -> `236 passed`
  - `$env:PYTHONPATH='src'; python -m war_room --verify` -> passed, offline preflight success

## Session 64 - Workflow Summary Surface Slice
Date: 2026-03-20
Status: Complete

- Added `src/war_room/workflow_summary.py` so the current notebook-era flow can derive a research-plan preview plus canonical run/stage timeline from existing typed contracts instead of leaving operators to infer trust state from scattered prints.
- What changed:
  - `format_research_plan_preview()` now renders planned modules, issue hypotheses, preferred domains, and estimated scope from `ResearchPlan`.
  - `build_run_timeline()` now derives `Run` plus `RunStage` state from the shared research plan, module payloads, citation results, and audit snapshot.
  - `notebooks/01_case_war_room.ipynb` now prints the plan preview before query rows and prints a run timeline after memo export.
  - `src/war_room/preflight.py` now records workflow status plus stage-status summaries so the offline smoke report shows review-required run health explicitly.
  - package exports and regression coverage were updated for the new helper surface.
- Why:
  - the last slice unified the shared `ResearchPlan`, but the operator still had to infer workflow state manually from raw module output
  - this adds the first thin workflow surface without pretending the planned V2 web app already exists
- Verification:
  - `$env:PYTHONPATH='src'; pytest -q tests/test_workflow_summary.py` -> `4 passed`
  - `$env:PYTHONPATH='src'; pytest -q tests/test_preflight.py tests/test_scenarios.py` -> `13 passed`
  - `$env:PYTHONPATH='src'; pytest -q` -> `240 passed`
  - `$env:PYTHONPATH='src'; python -m war_room --verify` -> passed, offline preflight now reports workflow review state

## Session 65 - Evidence Board Read Model Slice
Date: 2026-03-20
Status: Complete

- Added `src/war_room/evidence_board.py` so the current notebook-era flow can derive a cluster-first Evidence Board read model from `RunAuditSnapshot` instead of forcing operators to read appendix tables or infer grouped support manually.
- What changed:
  - `build_evidence_board()` and `build_evidence_board_from_parts()` now derive cluster cards with source-tier summary, issue labels, linked claims, linked review events, and compact evidence previews.
  - `format_evidence_board()` now renders a notebook-friendly cluster-first summary with review-required clusters elevated first.
  - `notebooks/01_case_war_room.ipynb` now prints the evidence-board summary immediately after citation spot-check results.
  - `src/war_room/preflight.py` now records evidence-board counts so the deterministic offline smoke lane surfaces grouped-support posture alongside workflow status.
  - package exports and regression coverage were updated for the new read model.
- Why:
  - the workflow summary slice exposed run/stage state, but there was still no first-class grouped-support review surface between retrieval output and memo export
  - this adds the next thin V2-aligned surface without inventing a separate UI runtime
- Verification:
  - `$env:PYTHONPATH='src'; pytest -q tests/test_evidence_board.py` -> `3 passed`
  - `$env:PYTHONPATH='src'; pytest -q tests/test_preflight.py tests/test_scenarios.py` -> `13 passed`
  - `$env:PYTHONPATH='src'; pytest -q` -> `243 passed`
  - `$env:PYTHONPATH='src'; python -m war_room --verify` -> passed, offline preflight now reports evidence-board cluster counts

## Session 66 - Issue Workspace Read Model Slice
Date: 2026-03-20
Status: Complete

- Added `src/war_room/issue_workspace.py` so the current notebook-era flow can derive an Issue Workspace read model from `RunAuditSnapshot` instead of forcing operators to infer issue-level support from case-law buckets and appendix tables.
- What changed:
  - `build_issue_workspace()` and `build_issue_workspace_from_parts()` now derive issue cards with linked clusters, case candidates, citation outcomes, linked memo claims, and open review events.
  - `format_issue_workspace()` now renders a notebook-friendly issue summary with strongest authorities and citation state kept inside the issue view.
  - `notebooks/01_case_war_room.ipynb` now prints the issue-workspace summary immediately after the evidence-board summary.
  - `src/war_room/preflight.py` now records issue-workspace counts so the deterministic offline smoke lane surfaces issue-level review posture alongside workflow and evidence-board status.
  - package exports and regression coverage were updated for the new read model.
- Why:
  - the evidence-board slice exposed grouped support, but there was still no first-class issue-level review surface between clusters and memo export
  - this adds the next thin V2-aligned surface without inventing a separate UI runtime
- Verification:
  - `$env:PYTHONPATH='src'; pytest -q tests/test_issue_workspace.py` -> `3 passed`
  - `$env:PYTHONPATH='src'; pytest -q tests/test_preflight.py tests/test_scenarios.py` -> `13 passed`
  - `$env:PYTHONPATH='src'; pytest -q` -> `246 passed`
  - `$env:PYTHONPATH='src'; python -m war_room --verify` -> passed, offline preflight now reports issue-workspace counts

## Session 67 - Memo Composer Read Model Slice
Date: 2026-03-20
Status: Complete

- Added `src/war_room/memo_composer.py` so the current notebook-era flow can derive a Memo Composer read model from `RunAuditSnapshot` instead of forcing operators to infer section readiness and export posture from the final markdown alone.
- What changed:
  - `build_memo_composer()` and `build_memo_composer_from_parts()` now derive section cards with claim support links, review-event links, review-required state, and export eligibility.
  - `format_memo_composer()` now renders a notebook-friendly section summary with claim-level cluster linkage and explicit export posture.
  - `notebooks/01_case_war_room.ipynb` now prints the memo-composer summary in the export cell before the run timeline.
  - `src/war_room/preflight.py` now records memo-composer counts so the deterministic offline smoke lane surfaces section readiness and export eligibility alongside workflow, evidence-board, and issue-workspace status.
  - package exports and regression coverage were updated for the new read model.
- Why:
  - the issue-workspace slice exposed issue-level review, but there was still no first-class section/readiness surface between issue review and export
  - this adds the last missing workflow stage before export history without inventing a separate UI runtime
- Verification:
  - `$env:PYTHONPATH='src'; pytest -q tests/test_memo_composer.py` -> `3 passed`
  - `$env:PYTHONPATH='src'; pytest -q tests/test_preflight.py tests/test_scenarios.py` -> `13 passed`
  - `$env:PYTHONPATH='src'; pytest -q` -> `249 passed`
  - `$env:PYTHONPATH='src'; python -m war_room --verify` -> passed, offline preflight now reports memo-composer counts and export eligibility

## Session 68 - Export History Read Model Slice
Date: 2026-03-20
Status: Complete

- Added `src/war_room/export_history.py` so the current notebook-era flow can derive an Export History read model from the canonical export artifact and run status instead of forcing operators to infer export posture from the written markdown path alone.
- What changed:
  - `build_export_history()` and `build_export_history_from_parts()` now derive export entries with artifact type, timestamp, disclaimer state, run status, delivery state, and audit-snapshot pointer.
  - `format_export_history()` now renders a notebook-friendly export-history summary with written vs not-written state called out explicitly.
  - `notebooks/01_case_war_room.ipynb` now prints the export-history summary in the export cell after the run timeline is available.
  - `src/war_room/preflight.py` now records export-history counts so the deterministic offline smoke lane surfaces final export posture alongside workflow, evidence-board, issue-workspace, and memo-composer status.
  - package exports and regression coverage were updated for the new read model.
- Why:
  - the memo-composer slice exposed section readiness, but there was still no first-class final-stage surface showing whether an export artifact existed, what state it was in, and how it linked back to the audit snapshot
  - this closes the last missing written workflow stage before a PR
- Verification:
  - `$env:PYTHONPATH='src'; pytest -q tests/test_export_history.py` -> `3 passed`
  - `$env:PYTHONPATH='src'; pytest -q tests/test_preflight.py tests/test_scenarios.py` -> `13 passed`
  - `$env:PYTHONPATH='src'; pytest -q` -> `252 passed`
  - `$env:PYTHONPATH='src'; python -m war_room --verify` -> passed, offline preflight now reports export-history state

## Session 69 - Milton Trust And Export Readability Slice
Date: 2026-03-30
Status: Complete

- Inspected the committed `milton_pinellas_citizens_ho3` fixture lane end to end using an empty temp cache so the review reflected `cache_samples/` rather than stale local runtime cache.
- What changed:
  - `src/war_room/models.py` now backfills sparse citation-check trust metadata from existing source URLs when older cached fixtures omit `status_reason`, `source_tier`, `source_class`, `trust_explanation`, and calibrated confidence.
  - Citation review events now target only the non-verified citation evidence rows instead of attaching review-required state to every citation cluster in the run.
  - `src/war_room/export_md.py` now normalizes multiline free text before rendering bullets and tables so weather observations, carrier document rows, case-law entries, and appendix tables stay readable in markdown output.
  - `src/war_room/evidence_board.py` now keeps cluster cards scoped to cluster-level review state instead of inheriting a blanket review-required marker from a degraded section claim.
  - Regression coverage was added and updated across citation contract, export, evidence-board, and issue-workspace tests.
- Why:
  - the Milton benchmark memo was surfacing blank citation reasons, low-confidence verified checks, broken markdown table rows, and a falsely degraded verified citation cluster, which reduced operator trust in the export and evidence telemetry
  - this keeps the current notebook/runtime flow intact while tightening one benchmark scenario's trust/readability posture
- Verification:
  - `$env:PYTHONPATH='src'; .venv\Scripts\python.exe -m pytest tests/test_memo_contracts.py tests/test_export.py tests/test_evidence_board.py tests/test_issue_workspace.py -q` -> `30 passed`
  - `$env:PYTHONPATH='src'; .venv\Scripts\python.exe -m war_room --verify` -> passed, `256 passed, 1 warning`; offline preflight passed for 4 committed fixture scenarios

## Session 70 - Milton Carrier And Caselaw Source Cleanup
Date: 2026-03-30
Status: Complete

- Continued the Milton benchmark slice by tightening carrier and case-law payload normalization in the offline cache-backed path instead of rewriting retrieval or fixture files.
- What changed:
  - `src/war_room/carrier_module.py` now normalizes cached/live carrier packs before returning them, filtering generic regulator navigation pages and low-value brochure/support rows from the runtime output.
  - Carrier note text now strips obvious boilerplate markers so `why_it_matters` fields are cleaner when older cached snippets include repeated navigation text.
  - `src/war_room/caselaw_module.py` now normalizes cached/live case-law packs before returning them, dropping commentary-like authorities from issue case lists and trimming low-value support sources from the source appendix.
  - Offline pack smoke tests were updated to assert against normalized runtime behavior for the Milton fixture lane.
- Why:
  - the first Milton trust slice improved citation telemetry and export formatting, but the offline runtime was still surfacing noisy carrier support rows and commentary/homepage-style case-law sources because raw cached payloads bypassed the newer quality filters
  - this keeps the benchmark slice narrow while improving trust in the actual cache-backed demo output
- Verification:
  - `$env:PYTHONPATH='src'; .venv\Scripts\python.exe -m pytest tests/test_offline_demo_pack.py tests/test_carrier.py tests/test_caselaw.py -q` -> `54 passed`
  - `$env:PYTHONPATH='src'; .venv\Scripts\python.exe -m war_room --verify` -> passed, `260 passed, 1 warning`; offline preflight passed for 4 committed fixture scenarios

## Session 71 - Milton Carrier Ordering Tightening
Date: 2026-03-30
Status: Complete

- Tightened the Milton carrier runtime output one step further by moving strong-evidence ordering into carrier payload normalization so cached fixture output no longer inherits stale document/source ordering.
- What changed:
  - `src/war_room/carrier_module.py` now re-sorts normalized carrier documents and sources with regulator exam reports, orders, and carrier/regulator materials ahead of news/commentary rows.
  - Carrier snippet cleaning now strips simple markdown heading/list markers that leaked into `why_it_matters` text from cached snippets.
  - Carrier regression and offline smoke coverage were updated to assert the new runtime ordering behavior directly.
- Why:
  - the prior cleanup removed obvious noise, but the Milton carrier pack was still leading with unvetted denial-pattern/news links because cached payload order was preserved
  - this keeps the slice narrow while making the first visible carrier evidence rows more credible for the demo
- Verification:
  - `$env:PYTHONPATH='src'; .venv\Scripts\python.exe -m pytest tests/test_offline_demo_pack.py tests/test_carrier.py -q` -> `45 passed`
  - `$env:PYTHONPATH='src'; .venv\Scripts\python.exe -m war_room --verify` -> passed, `261 passed, 1 warning`; offline preflight passed for 4 committed fixture scenarios

## Session 72 - Milton Carrier Suppression Tightening
Date: 2026-03-30
Status: Complete

- Tightened the carrier runtime normalization one step further so unvetted carrier rows are suppressed from the Milton document pack and source appendix once enough stronger official/professional carrier evidence is already present.
- What changed:
  - `src/war_room/carrier_module.py` now counts strong carrier evidence in normalized output and drops unvetted rows from the pack/source list when that threshold is met.
  - Carrier regression and Milton runtime smoke tests were updated to assert the stronger-evidence-only runtime behavior.
- Why:
  - the ordering pass improved which rows appeared first, but the pack still contained avoidable unvetted carrier noise lower in the list
  - this keeps the benchmark slice narrow while making the visible carrier evidence set substantially more credible for demo review
- Verification:
  - `$env:PYTHONPATH='src'; .venv\Scripts\python.exe -m pytest tests/test_carrier.py tests/test_offline_demo_pack.py -q` -> `47 passed`
  - `$env:PYTHONPATH='src'; .venv\Scripts\python.exe -m war_room --verify` -> passed, `263 passed, 1 warning`; offline preflight passed for 4 committed fixture scenarios

## Session 73 - Milton Caselaw Appendix Relevance Tightening
Date: 2026-03-30
Status: Complete

- Tightened the Milton case-law source appendix one more step by requiring supplemental non-case sources to be on-point for the active intake when the issue buckets already contain enough stronger authorities.
- What changed:
  - `src/war_room/caselaw_module.py` now passes intake context into case-law payload normalization and drops tangential supplemental authorities when they are not clearly tied to the intake state, carrier, event, county, or issue labels.
  - Caselaw regression and Milton runtime smoke tests were updated to assert removal of the tangential Texas `Lyons` authority from the runtime source appendix.
- Why:
  - the prior cleanup left one remaining tangential support authority in the Milton appendix even though the issue buckets already contained stronger on-point Florida authorities
  - this keeps the benchmark slice narrow while making the case-law appendix cleaner and easier to trust during demo review
- Verification:
  - `$env:PYTHONPATH='src'; .venv\Scripts\python.exe -m pytest tests/test_caselaw.py tests/test_offline_demo_pack.py -q` -> `47 passed`
  - `$env:PYTHONPATH='src'; .venv\Scripts\python.exe -m war_room --verify` -> passed, `265 passed, 1 warning`; offline preflight passed for 4 committed fixture scenarios

## Session 74 - Milton Cached Authority Field Cleanup
Date: 2026-03-30
Status: Complete

- Closed the Milton benchmark slice by tightening cached case-authority field cleanup in the case-law normalization path instead of rewriting fixture JSON or changing retrieval flow.
- What changed:
  - `src/war_room/caselaw_module.py` now strips leftover Casetext boilerplate from cached case one-liners, removes truncated bracket-only fragments, and normalizes obviously broken court labels before downstream export/read models consume them.
  - `tests/test_caselaw.py` now covers cached authority cleanup directly for the Milton-shaped `Siegle` and `Quesada` fixture patterns.
  - `tests/test_offline_demo_pack.py` now asserts that the Milton runtime case-law pack no longer surfaces `Citing Cases` boilerplate or bracket-fragment summaries.
- Why:
  - the earlier Milton source cleanup made the authority set more trustworthy, but several cached case entries still rendered with scraped Casetext scaffolding and visibly truncated court/summary fields
  - this keeps the slice narrow while making the memo and appendix easier to read without touching the scenario registry, fixtures, or retrieval architecture
- Verification:
  - `$env:PYTHONPATH='src'; .venv\Scripts\python.exe -m pytest tests/test_caselaw.py tests/test_offline_demo_pack.py -q` -> `50 passed, 1 warning`
  - `$env:PYTHONPATH='src'; .venv\Scripts\python.exe -m war_room --verify` -> passed, `268 passed, 1 warning`; offline preflight passed for 4 committed fixture scenarios

## Session 75 - Verify Command Release Scorecard Emission
Date: 2026-04-18
Status: Complete

- Tightened the `#27` local operational path by making the supported verification command emit release-scorecard artifacts directly instead of requiring a second manual command after verification passes.
- What changed:
  - `src/war_room/bootstrap.py` now accepts an optional `--release-candidate` override for `python -m war_room --verify`.
  - Successful verify runs now capture the pytest result summary, resolve a candidate label from the current branch when available, and write paired JSON/Markdown release-scorecard artifacts into `runs/release_scorecards/`.
  - When branch detection is unavailable or detached, the verify path falls back to `local-verify` instead of failing the supported command.
  - `tests/test_bootstrap.py` now covers verify-path scorecard emission, candidate override/fallback behavior, and pytest summary extraction.
  - `docs/V2_RELEASE_RUBRIC.md` and `docs/BUILD_CHECKLIST.md` now describe the one-command local release-evidence flow while keeping the standalone scorecard CLI documented for CI/manual use.
- Why:
  - `#27` already had a rubric, local scorecard generator, and CI artifact job, but the supported local verification path still required a second manual step to create matching release evidence.
  - Wiring scorecard emission into `python -m war_room --verify` makes the documented contributor path closer to the actual release-readiness workflow without changing notebook-era runtime behavior.
- Verification:
  - `$env:PYTHONPATH='src'; python -m pytest tests/test_bootstrap.py tests/test_release_scorecard.py -q` -> `15 passed`
  - `$env:PYTHONPATH='src'; python -m war_room --verify --release-candidate local-verify` -> passed, `272 passed`; offline preflight passed for 4 committed fixture scenarios; scorecard artifacts written under `runs/release_scorecards/2026-04-18_local-verify.*`

## Session 76 - Release Scorecard Live Preflight Evidence
Date: 2026-04-18
Status: Complete

- Continued the `#27` operationalization path by teaching verify-driven scorecards to record the actual offline preflight result instead of inferring the offline gate only from committed fixture presence.
- What changed:
  - `src/war_room/release_scorecard.py` now defines a structured preflight summary, can summarize `DemoPreflightReport`, and includes an `Offline Preflight` section in Markdown artifacts when live preflight evidence is available.
  - The scorecard's `Offline demo lane completes` must-pass gate now uses the live preflight result when `python -m war_room --verify` generated the artifact, while the standalone scorecard CLI still falls back to fixture-based evidence.
  - `src/war_room/bootstrap.py` now passes the already-computed preflight report into scorecard generation so the verify path produces one coherent release-evidence artifact.
  - `tests/test_release_scorecard.py` and `tests/test_bootstrap.py` now cover preflight-summary capture, failed preflight gating, and verify-path handoff of the live report.
  - `docs/V2_RELEASE_RUBRIC.md` and `docs/BUILD_CHECKLIST.md` now describe the live-preflight-backed verify workflow.
- Why:
  - the previous slice made `python -m war_room --verify` emit scorecards automatically, but the offline-lane gate inside the artifact still depended on fixture coverage instead of the actual preflight result from that same run.
  - this keeps the artifact closer to real release evidence without broadening scope into new CI layers or changing notebook runtime behavior.
- Verification:
  - `$env:PYTHONPATH='src'; python -m pytest tests/test_bootstrap.py tests/test_release_scorecard.py tests/test_preflight.py -q` -> `21 passed`
  - `$env:PYTHONPATH='src'; python -m war_room --verify --release-candidate local-verify` -> passed, `274 passed`; offline preflight passed for 4 committed fixture scenarios; scorecard artifacts refreshed under `runs/release_scorecards/2026-04-18_local-verify.*`

## Session 77 - Linked Preflight Artifacts For Verify
Date: 2026-04-18
Status: Complete

- Continued the `#27` evidence path by persisting the live preflight payload from `python -m war_room --verify` and linking that artifact from the release scorecard.
- What changed:
  - `src/war_room/preflight.py` now writes machine-readable preflight JSON artifacts under `runs/preflight/`.
  - `src/war_room/bootstrap.py` now writes that preflight artifact during `--verify`, prints its path, and passes the path into scorecard generation.
  - `src/war_room/release_scorecard.py` now records `preflight_artifact_path` in the structured scorecard artifact and surfaces it in the Markdown evidence bundle.
  - `tests/test_preflight.py`, `tests/test_bootstrap.py`, and `tests/test_release_scorecard.py` now cover preflight artifact writing, verify-path handoff, and scorecard-path persistence.
  - `docs/V2_RELEASE_RUBRIC.md` and `docs/BUILD_CHECKLIST.md` now describe the linked preflight-artifact workflow.
- Why:
  - the prior slice summarized the live preflight result inside the scorecard, but the scorecard still did not point to the exact machine-readable offline artifact produced by that verify run.
  - this keeps release evidence auditable without adding new dependencies or broadening scope into CI redesign.
- Verification:
  - `$env:PYTHONPATH='src'; python -m pytest tests/test_bootstrap.py tests/test_release_scorecard.py tests/test_preflight.py -q` -> `22 passed`
  - `$env:PYTHONPATH='src'; python -m war_room --verify --release-candidate local-verify` -> passed, `275 passed`; offline preflight passed for 4 committed fixture scenarios; preflight artifact written under `runs/preflight/2026-04-18_local-verify.json`; scorecard artifacts refreshed under `runs/release_scorecards/2026-04-18_local-verify.*`

## Session 78 - Shared Run Id For Verify Evidence
Date: 2026-04-18
Status: Complete

- Continued the `#27` release-evidence path by making verify-generated preflight and scorecard artifacts run-scoped instead of day-scoped.
- What changed:
  - `src/war_room/preflight.py` now accepts a shared `run_id` when writing artifacts, stores that `run_id` in the preflight JSON payload, and includes it in the artifact filename.
  - `src/war_room/release_scorecard.py` now records `run_id` on the structured scorecard artifact and includes that `run_id` in scorecard filenames and Markdown output.
  - `src/war_room/bootstrap.py` now resolves one shared run id from the live preflight timestamp and uses it for both the preflight artifact and the scorecard artifact during `python -m war_room --verify`.
  - `tests/test_preflight.py`, `tests/test_release_scorecard.py`, and `tests/test_bootstrap.py` now cover the shared run id, the new filename shapes, and the persisted payload fields.
  - `docs/V2_RELEASE_RUBRIC.md` and `docs/BUILD_CHECKLIST.md` now describe the run-scoped verify artifact flow.
- Why:
  - the prior slice linked the preflight artifact from the scorecard, but repeated verify runs on the same day for the same candidate still overwrote the prior evidence files.
  - adding a shared run id keeps the preflight and scorecard artifacts paired while making repeated validations auditable instead of lossy.
- Verification:
  - `$env:PYTHONPATH='src'; python -m pytest tests/test_bootstrap.py tests/test_release_scorecard.py tests/test_preflight.py -q` -> `22 passed`
  - `$env:PYTHONPATH='src'; python -m war_room --verify --release-candidate local-verify` -> passed, `275 passed`; offline preflight passed for 4 committed fixture scenarios; preflight artifact written under `runs/preflight/2026-04-18_local-verify_20260418t162818z.json`; scorecard artifacts written under `runs/release_scorecards/2026-04-18_local-verify_20260418t162818z.*`

## Session 79 - Verify Run Manifest
Date: 2026-04-18
Status: Complete

- Continued the `#27` release-evidence path by adding a single verify-run manifest that points to the exact artifacts generated by each supported `--verify` run.
- What changed:
  - `src/war_room/bootstrap.py` now writes a JSON manifest into `runs/verify/` after the preflight and scorecard artifacts are written.
  - The verify manifest records `run_id`, `created_at`, `candidate`, `verification_summary`, `repo_root`, and the exact preflight / scorecard artifact paths for that run.
  - Verify console output now prints a dedicated `Verify Manifest` section before the preflight and scorecard paths.
  - `tests/test_bootstrap.py` now covers manifest creation and ensures failed test runs do not write a manifest.
  - `docs/V2_RELEASE_RUBRIC.md` and `docs/BUILD_CHECKLIST.md` now describe the new `runs/verify/` top-level evidence pointer.
- Why:
  - the previous slice made preflight and scorecard artifacts collision-safe, but there was still no single machine-readable file that indexed the whole verify run.
  - the manifest makes each verify run queryable without scanning multiple directories or reconstructing artifact relationships from filenames.
- Verification:
  - `$env:PYTHONPATH='src'; python -m pytest tests/test_bootstrap.py tests/test_release_scorecard.py tests/test_preflight.py -q` -> `22 passed`
  - `$env:PYTHONPATH='src'; python -m war_room --verify --release-candidate local-verify` -> passed, `275 passed`; offline preflight passed for 4 committed fixture scenarios; verify manifest written under `runs/verify/2026-04-18_local-verify_20260418t163443z.json`; preflight artifact written under `runs/preflight/2026-04-18_local-verify_20260418t163443z.json`; scorecard artifacts written under `runs/release_scorecards/2026-04-18_local-verify_20260418t163443z.*`

## Session 80 - Latest Verify Pointer
Date: 2026-04-18
Status: Complete

- Continued the `#27` release-evidence path by adding a stable discovery pointer for the newest successful supported verify run.
- What changed:
  - `src/war_room/bootstrap.py` now writes `runs/verify/latest.json` after each successful verify manifest write.
  - The latest pointer records the newest verify `run_id`, `created_at`, `candidate`, and the exact manifest path to follow for the full evidence bundle.
  - Verify console output now surfaces the `latest.json` path directly in the `Verify Manifest` section.
  - `tests/test_bootstrap.py` now covers latest-pointer emission during successful verify runs, the guard that failed runs do not write it, and the concrete `latest.json` payload shape.
  - `docs/V2_RELEASE_RUBRIC.md` and `docs/BUILD_CHECKLIST.md` now describe the stable verify discovery pointer.
- Why:
  - the previous slice made each verify run queryable through its own manifest, but consumers still had to scan `runs/verify/` to find the newest run.
  - `latest.json` keeps the current workflow simple while giving downstream tooling one stable file to open first.
- Verification:
  - `$env:PYTHONPATH='src'; python -m pytest tests/test_bootstrap.py tests/test_release_scorecard.py tests/test_preflight.py -q` -> `23 passed`
  - `$env:PYTHONPATH='src'; python -m war_room --verify --release-candidate local-verify` -> passed, `276 passed`; offline preflight passed for 4 committed fixture scenarios; verify manifest written under `runs/verify/2026-04-18_local-verify_20260418t164252z.json`; latest pointer refreshed at `runs/verify/latest.json`; preflight artifact written under `runs/preflight/2026-04-18_local-verify_20260418t164252z.json`; scorecard artifacts written under `runs/release_scorecards/2026-04-18_local-verify_20260418t164252z.*`

## Session 81 - Verify Artifact Consistency Guard
Date: 2026-04-18
Status: Complete

- Continued the `#27` release-evidence path by adding an end-to-end test that reloads the verify manifest and checks the linked artifact bundle for consistency.
- What changed:
  - `tests/test_bootstrap.py` now writes a real preflight artifact, a real release scorecard artifact, and a real verify manifest into a temporary `runs/` tree during one focused test.
  - That test reloads the manifest JSON, asserts the linked preflight and scorecard artifact paths exist, and verifies that the manifest, preflight payload, and scorecard payload all share the same `run_id`.
  - `docs/BUILD_CHECKLIST.md` now notes that the end-to-end artifact consistency guard has landed in the local `#27` verification path.
- Why:
  - the previous slice made the newest verify run easy to discover through `runs/verify/latest.json`, but there was still no explicit regression guard proving that the manifest and its linked artifacts stayed internally consistent.
  - this gives the release-evidence workflow one concrete integrity check before packaging the PR.
- Verification:
  - `$env:PYTHONPATH='src'; python -m pytest tests/test_bootstrap.py tests/test_release_scorecard.py tests/test_preflight.py -q` -> `24 passed`
  - `$env:PYTHONPATH='src'; python -m war_room --verify --release-candidate local-verify` -> passed, `277 passed`; offline preflight passed for 4 committed fixture scenarios; verify manifest written under `runs/verify/2026-04-18_local-verify_20260418t164745z.json`; latest pointer refreshed at `runs/verify/latest.json`; preflight artifact written under `runs/preflight/2026-04-18_local-verify_20260418t164745z.json`; scorecard artifacts written under `runs/release_scorecards/2026-04-18_local-verify_20260418t164745z.*`

## Session 82 - Post-Merge Status Sync
Date: 2026-04-18
Status: Complete

- Synced the repo-status docs and active milestone issues to the merged `#27` release-evidence state instead of leaving the codebase framed by pre-merge March notes.
- What changed:
  - `README.md`, `AGENTS.md`, `docs/HANDOFF.md`, `docs/heartbeat.md`, `docs/repo-brief.md`, `docs/ROADMAP.md`, `docs/V2_ISSUE_MAP.md`, `docs/BUILD_CHECKLIST.md`, `docs/DECISION_LOG.md`, and `docs/V2_RELEASE_RUBRIC.md` now reflect the live repo name, current test count, current `#27` status, and the merged verify-evidence workflow.
  - Broken GitHub issue links pointing at `cat-loss-war-room-demo` were updated to the live `cat-loss-war-room` repository across the planning and status docs.
  - GitHub issues `#6`, `#7`, `#8`, `#9`, and `#27` now include current-status sections that match the merged codebase instead of older March-era progress notes.
  - `docs/heartbeat.md` and `AGENTS.md` now point builders at the live session log rather than the old one-off March memory file.
- Why:
  - the local release-evidence stack was merged cleanly, but the repo still described itself in several places as if that work were pending or as if the old repo slug were still current.
  - this keeps the repo orientation docs and active issue tracker aligned with the actual codebase before the next implementation slice starts.
- Verification:
  - `$env:PYTHONPATH='src'; python -m war_room --verify --release-candidate post-merge-status-sync` -> passed, `277 passed`; offline preflight passed for 4 committed fixture scenarios; verify manifest written under `runs/verify/2026-04-18_post-merge-status-sync_20260418t170708z.json`; latest pointer refreshed at `runs/verify/latest.json`; preflight artifact written under `runs/preflight/2026-04-18_post-merge-status-sync_20260418t170708z.json`; scorecard artifacts written under `runs/release_scorecards/2026-04-18_post-merge-status-sync_20260418t170708z.*`

## Session 83 - Final Docs Closeout
Date: 2026-04-28
Status: Complete

- Ran a final closeout pass after the `#27` release-evidence sync had landed on `main`.
- What changed:
  - `docs/HANDOFF.md`, `docs/ROADMAP.md`, and `docs/V2_RELEASE_RUBRIC.md` now carry the April 28 status date.
  - `docs/heartbeat.md` now points to the closeout branch, latest validation command, current focus, and April 28 session log.
  - `MEMORY.md` now points to the latest file under `logs/`.
  - `CLAUDE.md` now reflects the current 277-test baseline and next-session focus.
  - `docs/repo-brief.md` now describes the remaining `#27` work as broader CI/pilot operationalization rather than the already-merged local verify bundle.
  - `tests/test_preflight.py` now derives the expected preflight artifact date from the report timestamp instead of hard-coding the prior April 18 validation date.
  - `logs/2026-04-28-session.md` records the final closeout state for future resumption.
- Why:
  - the repo was functionally current, but the end-of-night orientation docs still had a few stale branch/date/session pointers.
  - the supported verification path exposed one date-rollover test expectation that needed to follow the live preflight report date.
  - this keeps the memory stack clean before the next foundation slice starts.
- Verification:
  - `$env:PYTHONPATH='src'; python -m war_room --verify --release-candidate final-docs-closeout` -> passed, `277 passed`; offline preflight passed for 4 committed fixture scenarios.

## Session 84 - Export Readability Guard
Date: 2026-04-28 local / 2026-04-29 UTC
Status: Complete

- Added a focused guard for the rendered Milton memo so embarrassing demo-output regressions fail in tests instead of surfacing in a walkthrough.
- What changed:
  - `tests/test_export.py` now renders the Milton fixture path through the runtime modules and asserts the memo keeps required demo sections and disclaimers.
  - The same export test now rejects obvious mojibake prefixes, `CONTINUE TO SITE`, weather navigation text, Casetext boilerplate, generic weather pages, and filler carrier rows.
  - `tests/test_export.py` also checks contiguous markdown table blocks for stable pipe counts, catching table-cell escaping regressions.
  - `src/war_room/weather_module.py` now normalizes cached/live weather payloads before memo and workflow consumers see them, dropping stale navigation-heavy observations and generic low-value weather sources from older cache samples.
  - Active status docs now reflect the 279-test baseline.
- Why:
  - the prior runtime was cleaner than the old notebook-era output, but the top-level Milton weather cache still leaked stale navigation text into the rendered memo.
  - this keeps the default demo memo credible without broad fixture rewrites, new dependencies, or changes to the notebook surface.
- Verification:
  - `$env:PYTHONPATH='src'; python -m pytest tests/test_export.py tests/test_weather.py tests/test_offline_demo_pack.py -q` -> `62 passed`
  - `$env:PYTHONPATH='src'; python -m war_room --verify --release-candidate export-readability-guard` -> passed, `279 passed`; offline preflight passed for 4 committed fixture scenarios; Milton weather sources reduced to 9 after cached weather normalization.

## Session 85 - Issue 6 Cache Schema Envelope
Date: 2026-04-28 local / 2026-04-29 UTC
Status: Complete

- Continued `#6` by making runtime cache compatibility explicit without changing the committed raw fixture shape.
- What changed:
  - `src/war_room/cache_io.py` now writes new cache entries inside a small `war_room.cache_entry` envelope with `schema_version: v2alpha1`.
  - `cache_get()` unwraps the current envelope transparently so existing module callers still receive the original payload shape.
  - `cache_get()` remains backward-compatible with legacy raw JSON payloads already present in `cache_samples/` and `cache/`.
  - Unsupported future cache schema versions now fail explicitly instead of being consumed silently.
  - `tests/test_cache_io.py` now covers envelope writing, legacy raw-cache loading, unsupported-version rejection, and `cached_call()` runtime writes.
  - Active status docs now reflect the 283-test baseline and `#6` slice 8.
- Why:
  - issue `#6` explicitly calls for schema-versioned cache adapters and backward-compatible loaders.
  - this gives new runtime cache artifacts a version marker while preserving the offline demo lane and avoiding a broad fixture rewrite.
- Verification:
  - `$env:PYTHONPATH='src'; python -m pytest tests/test_cache_io.py -q` -> `12 passed`
  - `$env:PYTHONPATH='src'; python -m pytest tests/test_cache_io.py tests/test_offline_demo_pack.py tests/test_weather.py tests/test_carrier.py tests/test_caselaw.py tests/test_citation_verify.py -q` -> `98 passed`
  - `$env:PYTHONPATH='src'; python -m war_room --verify --release-candidate issue-6-cache-envelope` -> passed, `283 passed`; offline preflight passed for 4 committed fixture scenarios.

## Session 86 - Issue 6 Evidence Board Read Model Contract
Date: 2026-04-28 local / 2026-04-29 UTC
Status: Complete

- Continued `#6` by replacing the Evidence Board's local dataclass read model with a typed `v2alpha1` Pydantic contract.
- What changed:
  - `src/war_room/models.py` now defines `EvidenceBoardItemPreview`, `EvidenceBoardClusterCard`, and `EvidenceBoardReadModel`.
  - `adapt_evidence_board()` and `evidence_board_to_payload()` now validate and serialize the board contract.
  - `src/war_room/evidence_board.py` now builds the typed model and validates dict-shaped payloads before rendering.
  - `tests/test_evidence_board.py` now covers schema-versioned payload round-trip and rejection of unexpected nested fields.
  - Active status docs now reflect the 285-test baseline and `#6` slice 9.
- Why:
  - the V2 evidence schema calls out workflow read models as first-class contracts, and Evidence Board is the highest-value board seam because it carries cluster, review, claim, and source-tier state.
  - this keeps the current notebook rendering behavior stable while making future API/UI consumers less dependent on loose dict shape assumptions.
- Verification:
  - `$env:PYTHONPATH='src'; python -m pytest tests/test_evidence_board.py tests/test_preflight.py -q` -> `11 passed`
  - `$env:PYTHONPATH='src'; python -m pytest tests/test_memo_contracts.py tests/test_export_history.py tests/test_issue_workspace.py tests/test_memo_composer.py -q` -> `20 passed`
  - `$env:PYTHONPATH='src'; python -m war_room --verify --release-candidate issue-6-evidence-board-contract` -> passed, `285 passed`; offline preflight passed for 4 committed fixture scenarios.

## Session 87 - Issue 6 Issue Workspace Read Model Contract
Date: 2026-04-28 local / 2026-04-29 UTC
Status: Complete

- Continued `#6` by replacing the Issue Workspace's local dataclass read model with a typed `v2alpha1` Pydantic contract.
- What changed:
  - `src/war_room/models.py` now defines `IssueWorkspaceCaseCandidate`, `IssueWorkspaceCitationOutcome`, `IssueWorkspaceCard`, and `IssueWorkspaceReadModel`.
  - `adapt_issue_workspace()` and `issue_workspace_to_payload()` now validate and serialize the issue-workspace contract.
  - `src/war_room/issue_workspace.py` now builds the typed model and validates dict-shaped payloads before rendering.
  - `tests/test_issue_workspace.py` now covers schema-versioned payload round-trip and rejection of unexpected nested fields.
  - Active status docs now reflect the 287-test baseline and `#6` slice 10.
- Why:
  - the V2 evidence schema requires a stable Issue Workspace read model for issue-level support, authority review, citation outcomes, memo claims, and open review events.
  - this keeps the notebook renderer behavior stable while reducing another workflow-layer loose dict seam before future API/UI work.
- Verification:
  - `$env:PYTHONPATH='src'; python -m pytest tests/test_issue_workspace.py tests/test_preflight.py -q` -> `10 passed`
  - `$env:PYTHONPATH='src'; python -m pytest tests/test_memo_contracts.py tests/test_evidence_board.py tests/test_export_history.py tests/test_memo_composer.py -q` -> `23 passed`
  - `$env:PYTHONPATH='src'; python -m war_room --verify --release-candidate issue-6-issue-workspace-contract` -> passed, `287 passed`; offline preflight passed for 4 committed fixture scenarios.

## Session 88 - Issue 6 Memo Composer Read Model Contract
Date: 2026-04-28 local / 2026-04-29 UTC
Status: Complete

- Continued `#6` by replacing the Memo Composer's local dataclass read model with a typed `v2alpha1` Pydantic contract.
- What changed:
  - `src/war_room/models.py` now defines `MemoComposerClaimLink`, `MemoComposerSectionCard`, and `MemoComposerReadModel`.
  - `adapt_memo_composer()` and `memo_composer_to_payload()` now validate and serialize the memo-composer contract.
  - `src/war_room/memo_composer.py` now builds the typed model and validates dict-shaped payloads before rendering.
  - `tests/test_memo_composer.py` now covers schema-versioned payload round-trip and rejection of unexpected nested fields.
  - Active status docs now reflect the 289-test baseline and `#6` slice 11.
- Why:
  - the V2 evidence schema requires a stable Memo Composer read model for ordered sections, claim support links, review-required state, and export eligibility.
  - this keeps the notebook renderer behavior stable while reducing another workflow-layer loose dict seam before future API/UI work.
- Verification:
  - `$env:PYTHONPATH='src'; python -m pytest tests/test_memo_composer.py tests/test_preflight.py -q` -> `10 passed`
  - `$env:PYTHONPATH='src'; python -m pytest tests/test_memo_contracts.py tests/test_evidence_board.py tests/test_issue_workspace.py tests/test_export_history.py -q` -> `25 passed`
  - `$env:PYTHONPATH='src'; python -m war_room --verify --release-candidate issue-6-memo-composer-contract` -> passed, `289 passed`; offline preflight passed for 4 committed fixture scenarios.

## Session 89 - Issue 6 Export History Read Model Contract
Date: 2026-04-29
Status: Complete

- Continued `#6` by replacing the Export History's local dataclass read model with a typed `v2alpha1` Pydantic contract.
- What changed:
  - `src/war_room/models.py` now defines `ExportHistoryEntry` and `ExportHistoryReadModel`.
  - `adapt_export_history()` and `export_history_to_payload()` now validate and serialize the export-history contract.
  - `src/war_room/export_history.py` now builds the typed model and validates dict-shaped payloads before rendering.
  - `tests/test_export_history.py` now covers schema-versioned payload round-trip and rejection of unexpected nested fields.
  - Active status docs now reflect the 291-test baseline and `#6` slice 12.
- Why:
  - the V2 evidence schema requires a stable Export History read model for artifact list, delivery state, disclaimer state, review-required state, and audit-bundle pointers.
  - this keeps the notebook renderer behavior stable while closing the last obvious workflow-layer local dataclass seam.
- Verification:
  - `$env:PYTHONPATH='src'; python -m pytest tests/test_export_history.py tests/test_preflight.py -q` -> `10 passed`
  - `$env:PYTHONPATH='src'; python -m pytest tests/test_memo_contracts.py tests/test_evidence_board.py tests/test_issue_workspace.py tests/test_memo_composer.py -q` -> `27 passed`
  - `$env:PYTHONPATH='src'; python -m war_room --verify --release-candidate issue-6-export-history-contract` -> passed, `291 passed`; offline preflight passed for 4 committed fixture scenarios.

## Session 90 - Issue 6 Final Contract and Docs Closeout
Date: 2026-04-29
Status: Complete

- Completed the final `#6` workflow read-model contract pass by adding a schema-versioned Run Timeline envelope over the existing canonical `Run` and `RunStage` contracts.
- What changed:
  - `src/war_room/models.py` now defines `RunTimelineReadModel`.
  - `adapt_run_timeline()` and `run_timeline_to_payload()` now validate and serialize the run-timeline contract.
  - `src/war_room/workflow_summary.py` now exposes `build_run_timeline_read_model()` while keeping the existing `build_run_timeline()` tuple API intact.
  - `format_run_timeline()` now accepts a typed read model or dict payload and still supports the old `Run` plus stage-list call shape.
  - `tests/test_workflow_summary.py` now covers schema-versioned payload round-trip and rejection of stages from a different run.
  - Active status docs now reflect the 293-test baseline and `#6` slice 13.
- Why:
  - the other workflow read models were already behind `v2alpha1` payload contracts, and Run Timeline was the remaining read-model surface called out by the V2 evidence schema.
  - this keeps the notebook/preflight behavior stable while giving future API/UI work one typed contract path for the timeline surface.
- Verification:
  - `$env:PYTHONPATH='src'; python -m pytest tests/test_workflow_summary.py tests/test_preflight.py -q` -> `11 passed`
  - `$env:PYTHONPATH='src'; python -m pytest tests/test_memo_contracts.py tests/test_evidence_board.py tests/test_issue_workspace.py tests/test_memo_composer.py tests/test_export_history.py -q` -> `32 passed`
  - `$env:PYTHONPATH='src'; python -m war_room --verify --release-candidate issue-6-final-contract-docs` -> passed, `293 passed`; offline preflight passed for 4 committed fixture scenarios.

## Session 91 - Evidence Board HTML UI Slice
Date: 2026-04-30
Status: Complete

- Started the notebook UI/UX polish lane with the Evidence Board, because it is the most attorney-facing review surface before memo prose.
- What changed:
  - `src/war_room/evidence_board.py` now exposes `render_evidence_board_html()` over the existing typed `EvidenceBoardReadModel`.
  - The HTML view renders cluster-first cards with review-required status, source balance, source-tier chips, linked claims, review events, provenance counts, and evidence previews.
  - HTML output escapes model content and suppresses non-http source links before rendering anchors.
  - `notebooks/01_case_war_room.ipynb` now displays the styled Evidence Board in Cell 6 while preserving the existing text formatter as a fallback.
  - `src/war_room/__init__.py` exports the new renderer.
  - `tests/test_evidence_board.py` now covers HTML review cues and escaping behavior.
- Why:
  - the workflow contracts were already solid, but the notebook demo still made the primary evidence-review surface feel like console output.
  - this gives the current V0 notebook a materially better review UI without treating `apps/` as an active runtime or adding dependencies.
- Verification:
  - `$env:PYTHONPATH='src'; python -m pytest tests/test_evidence_board.py -q` -> `7 passed`
  - `$env:PYTHONPATH='src'; python -m pytest tests/test_scenarios.py::test_notebook_uses_helper_driven_scenario_prep_and_has_no_stale_hardcoded_intake -q` -> `1 passed`
  - `$env:PYTHONPATH='src'; python -m war_room --verify --release-candidate evidence-board-html-ui` -> passed, `294 passed`; offline preflight passed for 4 committed fixture scenarios.

## Session 92 - Issue 6 Closeout Audit
Date: 2026-05-13
Status: Complete

- Completed the final closeout audit for issue `#6` without changing runtime code, notebooks, dependencies, or live-retrieval behavior.
- What changed:
  - Added `docs/ISSUE_6_CLOSEOUT_AUDIT.md` with a prompt-to-artifact checklist mapping the `#6` typed-contract and cache-hardening requirements to code, tests, validation, and explicit out-of-scope compatibility surfaces.
  - Updated `README.md`, `CLAUDE.md`, `docs/HANDOFF.md`, `docs/ROADMAP.md`, `docs/V2_ISSUE_MAP.md`, `docs/BUILD_CHECKLIST.md`, `docs/repo-brief.md`, and `docs/heartbeat.md` so `#6` is no longer described as pending implementation.
- Why:
  - the runtime slices were already landed and merged, but issue `#6` still needed an auditable closeout artifact that proves cache compatibility is versioned and test-covered, remaining dict seams are either typed or explicitly transitional, and the issue is ready to close after this PR lands.
- Verification:
  - `python -m pytest -q` -> `294 passed in 5.97s`
  - `python -m war_room --verify --release-candidate issue-6-closeout-audit` -> passed; embedded `pytest -q` reported `294 passed in 5.98s`; offline preflight passed for 4 committed fixture scenarios; verify manifest written under `runs/verify/2026-05-13_issue-6-closeout-audit_20260513t042737z.json`.

## Session 93 - Issue 8 Offline Fixture Golden Snapshots
Date: 2026-05-13
Status: Complete

- Completed the next reviewable `#8` slice by adding a deterministic golden snapshot framework for the existing committed offline fixture scenarios instead of broadening runtime behavior.
- What changed:
  - Added `src/war_room/fixture_snapshots.py` with `--check` and `--write` CLI paths for committed offline fixture snapshots.
  - Added `tests/golden/offline_fixture_snapshots.json` as the first golden fixture snapshot for the four committed FL/TX/LA scenario directories.
  - Added `tests/test_fixture_snapshots.py` with quality assertions for scenario coverage metadata, source mix, case count, citation summary consistency, memo section structure, workflow state, evidence/issue counts, and export posture.
  - Extended the CI fixture-smoke job to run the snapshot tests and `python -m war_room.fixture_snapshots --check`.
  - Synced status docs to the 298-test baseline and the new `#8` snapshot gate.
- Why:
  - issue `#8` needs reviewable fixture/output drift before broader fixture seeding will make `#9` CI gates meaningful.
  - existing committed scenarios already cover Florida, Texas, and Louisiana, so this slice tightens deterministic assertions around known-good offline fixtures without live retrieval, dependency churn, notebook edits, or generated runtime artifact changes.
- Decision not added:
  - no new formal decision-log entry was added; this is an implementation slice of the existing `#8` fixture/snapshot direction.
  - no new scenario fixture was added in this PR because adding a credible new offline scenario safely would require either live retrieval or a separate curated fixture-seeding pass. The existing four-scenario set is the right foundation for the first golden snapshot gate.
- Verification:
  - `python -m war_room.fixture_snapshots --check` -> passed; snapshot matched `tests/golden/offline_fixture_snapshots.json`.
  - `python -m pytest tests/test_fixture_snapshots.py tests/test_offline_demo_pack.py tests/test_intake_validation.py -q` -> `53 passed in 2.77s`.
  - `python -m pytest -q` -> `298 passed in 7.38s`.
  - `python -m war_room --verify --release-candidate issue-8-fixture-snapshots` -> passed; embedded `pytest -q` reported `298 passed in 7.16s`; offline preflight passed for 4 committed fixture scenarios; verify manifest written under `runs/verify/2026-05-13_issue-8-fixture-snapshots_20260513t044322z.json`.

## Session 94 - Issue 9 CI Failure Categorization
Date: 2026-05-13
Status: Complete

- Completed the next focused `#9` slice by adding categorized CI quality-gate artifacts around the existing deterministic lanes.
- What changed:
  - Added `src/war_room/quality_gates.py`, a small wrapper that runs existing commands, preserves their exit codes, and writes per-gate JSON, Markdown, and log artifacts under `runs/quality_gates/`.
  - Split CI steps so unit tests, offline fixture tests, golden snapshot tests, direct golden snapshot diff checks, Exa compatibility tests, release-scorecard generation, and release-scorecard validation have distinct gate names and artifact files.
  - Added always-run CI summary/upload steps so failed gates still leave a diagnostic artifact.
  - Moved release-scorecard artifact validation into `src/war_room/release_scorecard.py` with a reusable `--validate-latest` CLI path.
  - Added focused tests for quality-gate artifacts and release-scorecard validation behavior.
  - Synced status docs to the 306-test baseline and the first `#9` failure-categorization slice.
- Why:
  - issue `#9` explicitly needs CI reports that distinguish unit, fixture-quality, Exa compatibility, and release-artifact failures.
  - this keeps the existing offline-safe commands as the source of truth and only adds a diagnostic/artifact layer around them.
- Decision not added:
  - no new formal decision-log entry was added; this is an implementation slice of the existing `#9` CI quality-gate direction.
  - this does not add e2e or security scans yet, so it does not fully close `#9`.
- Verification:
  - `python -m pytest tests/test_quality_gates.py tests/test_release_scorecard.py -q` -> `17 passed in 7.22s`.
  - `python -m pytest -q` -> `306 passed in 11.89s`.
  - `python -m war_room.fixture_snapshots --check` -> passed; snapshot matched `tests/golden/offline_fixture_snapshots.json`.
  - `python -m war_room.quality_gates run --gate golden-snapshot-check --output-dir runs/quality_gates/local -- python -m war_room.fixture_snapshots --check` -> passed; wrote `runs/quality_gates/local/golden-snapshot-check.json`.
  - `python -m war_room.quality_gates run --gate release-scorecard-validate --output-dir runs/quality_gates/local -- python -m war_room.release_scorecard --validate-latest --output-dir runs/release_scorecards` -> passed; wrote `runs/quality_gates/local/release-scorecard-validate.json`.
  - `python -m war_room.quality_gates summarize --output-dir runs/quality_gates/local --summary-path runs/quality_gates/local/summary.md --fail-on-failed` -> passed; `2/2` quality gates passed.
  - `python -m war_room --verify --release-candidate issue-9-ci-failure-categorization` -> passed; embedded `pytest -q` reported `306 passed in 13.43s`; offline preflight passed for 4 committed fixture scenarios; verify manifest written under `runs/verify/2026-05-13_issue-9-ci-failure-categorization_20260513t050202z.json`.

## Session 95 - Issue 9 Security Hygiene Quality Gate
Date: 2026-05-13
Status: Complete

- Completed the next focused `#9` slice by adding an offline-safe security hygiene quality gate through the existing categorized quality-gates wrapper.
- What changed:
  - Added `src/war_room/security_hygiene.py`, a stdlib-only checker for tracked `.env` files, obvious API key/token patterns, `.env.example` expectations, `.gitignore` policy, runtime artifact commits, and documented secrets/cache policy drift.
  - Added `security-hygiene-check` to `src/war_room/quality_gates.py` so local and CI runs emit the same JSON, Markdown, and log artifact shape as the other `#9` lanes.
  - Added a dedicated CI `Security Hygiene` job that runs `python -m war_room.quality_gates run --gate security-hygiene-check -- python -m war_room.security_hygiene --check`, summarizes results, and uploads gate artifacts.
  - Added focused tests for current-repo pass behavior, compliant synthetic repos, committed env/runtime artifact failures, synthetic secret assignment failures, env-template drift, and the new gate category.
  - Synced status docs to the 312-test baseline and the new offline security hygiene gate.
- Why:
  - issue `#9` asks for security-relevant checks on PR/main builds and diagnostic artifacts that distinguish security failures from unit, fixture, Exa, and release-scorecard failures.
  - this slice protects practical repo hygiene without live network calls, dependency changes, notebooks, production auth, PII redaction, retention enforcement, or broader `#18` security architecture.
- Decision not added:
  - no new formal decision-log entry was added; this is an implementation slice of the existing `#9` quality-gate direction.
  - this does not fully close `#9`; broader integration/e2e gates remain open, and production security controls remain under `#18`.
- Verification:
  - `python -m pytest tests/test_quality_gates.py tests/test_release_scorecard.py -q` -> `18 passed in 8.71s`.
  - `python -m pytest -q` -> `312 passed in 19.20s`.
  - `python -m war_room.fixture_snapshots --check` -> passed; snapshot matched `tests/golden/offline_fixture_snapshots.json`.
  - `python -m war_room.quality_gates run --gate security-hygiene-check --output-dir runs/quality_gates/local -- python -m war_room.security_hygiene --check` -> passed; wrote `runs/quality_gates/local/security-hygiene-check.json`.
  - `python -m war_room.quality_gates summarize --output-dir runs/quality_gates/local --summary-path runs/quality_gates/local/summary.md --fail-on-failed` -> passed; `3/3` quality gates passed.
  - `python -m war_room --verify --release-candidate issue-9-security-hygiene-gate` -> passed; embedded `pytest -q` reported `312 passed in 17.52s`; offline preflight passed for 4 committed fixture scenarios; verify manifest written under `runs/verify/2026-05-13_issue-9-security-hygiene-gate_20260513t052904z.json`.

## Session 96 - Issue 9 Offline E2E Quality Gate
Date: 2026-05-13
Status: Complete

- Completed the next focused `#9` slice by adding an offline-safe integration/e2e quality gate through the existing categorized quality-gates wrapper.
- What changed:
  - Added `src/war_room/offline_e2e.py`, a stdlib-only CLI that runs the committed offline demo preflight, validates fixture coverage, workflow stages, memo/review surfaces, export posture, and linked preflight artifacts, then writes JSON and Markdown reports under `runs/offline_e2e/`.
  - Added `e2e-offline-demo` to `src/war_room/quality_gates.py` so local and CI runs emit the same categorized JSON, Markdown, and log artifact shape as the other `#9` lanes.
  - Added a dedicated CI `Offline E2E` job that runs the new gate through `python -m war_room.quality_gates`, summarizes quality-gate status, and uploads both quality-gate and offline-e2e artifacts.
  - Added focused tests for e2e artifact structure, CLI behavior, synthetic failure reporting, and the new gate category.
  - Synced status docs to the 316-test baseline and the new offline e2e gate.
- Why:
  - issue `#9` asks for smoke integration/e2e coverage that proves the deterministic offline demo path can move from committed fixtures through preflight-style execution into structured artifacts.
  - this slice raises CI signal above unit tests without live network calls, dependency changes, notebook edits, API/UI work, or broad runtime rewrites.
- Decision not added:
  - no new formal decision-log entry was added; this is an implementation slice of the existing `#9` quality-gate direction.
  - this does not fully close `#9`; broader CI hardening and any remaining acceptance criteria should be evaluated after this gate lands.
- Verification:
  - `python -m pytest tests/test_quality_gates.py tests/test_security_hygiene.py tests/test_release_scorecard.py -q` -> `24 passed in 5.36s`.
  - `python -m pytest -q` -> `316 passed in 9.45s`.
  - `python -m war_room.fixture_snapshots --check` -> passed; snapshot matched `tests/golden/offline_fixture_snapshots.json`.
  - `python -m war_room.security_hygiene --check` -> passed; `6/6` checks passed.
  - `python -m war_room.quality_gates run --gate e2e-offline-demo --output-dir runs/quality_gates/local -- python -m war_room.offline_e2e --check` -> passed; wrote `runs/quality_gates/local/e2e-offline-demo.json`.
  - `python -m war_room.quality_gates summarize --output-dir runs/quality_gates/local --summary-path runs/quality_gates/local/summary.md --fail-on-failed` -> passed; `4/4` quality gates passed.
  - `python -m war_room --verify --release-candidate issue-9-offline-e2e-gate` -> passed; embedded `pytest -q` reported `316 passed in 15.29s`; offline preflight passed for 4 committed fixture scenarios; verify manifest written under `runs/verify/2026-05-13_issue-9-offline-e2e-gate_20260513t055236z.json`.
  - `python -m pytest tests/test_offline_e2e.py tests/test_quality_gates.py -q` -> `10 passed in 2.19s` after final test-file style cleanup.

## Session 97 - Issue 9 Dependency Hygiene Quality Gate
Date: 2026-05-13
Status: Complete

- Completed one final focused `#9` quality-gate slice by adding an offline-safe dependency hygiene gate through the existing categorized quality-gates wrapper.
- What changed:
  - Added `src/war_room/dependency_hygiene.py`, a stdlib-only checker for exact `requirements.txt` pins, disallowed editable/local/direct-URL requirements, duplicate/conflicting entries, `requirements.txt` / `pyproject.toml` drift, unsupported dependency files, and documented dependency policy drift.
  - Added `dependency-hygiene-check` to `src/war_room/quality_gates.py` so local and CI runs emit the same JSON, Markdown, and log artifact shape as the other `#9` lanes.
  - Added a dedicated CI `Dependency Hygiene` job that runs `python -m war_room.quality_gates run --gate dependency-hygiene-check -- python -m war_room.dependency_hygiene --check`, summarizes results, and uploads gate artifacts.
  - Addressed PR review by moving that CI gate before dependency installation and running it with `PYTHONPATH=src`, so the dependency scanner checks manifests before installing from them.
  - Made the package initializer lazy and removed bootstrap/settings imports from `quality_gates` and `dependency_hygiene`, so `python -m war_room.quality_gates` can start without installed third-party packages.
  - Added focused temp-repo tests for clean dependency files plus unpinned requirements, unsupported sources, duplicate/conflicting entries, pyproject drift, unsupported dependency files, documentation drift, nested `pyproject.toml`, and nested `requirements.txt`.
  - Synced status docs to the 324-test baseline and documented that `#9` is ready for closeout review after this slice lands.
- Why:
  - issue `#9` asks for dependency, secret, and security scanning where it materially protects the repo and for CI reports that categorize failure sources.
  - this slice protects the dependency manifest boundary without live vulnerability scanning, dependency changes, notebook edits, production security controls, or live network calls.
- Decision not added:
  - no new formal decision-log entry was added; this follows the existing `#9` quality-gate direction.
  - live vulnerability scanning was intentionally not added because it would require network access and belongs outside this offline/no-new-dependency slice.
- Verification:
  - `PYTHONPATH=src python -S -m war_room.quality_gates run --gate dependency-hygiene-check --output-dir runs/quality_gates/local-no-site -- python -S -m war_room.dependency_hygiene --check` -> passed, confirming the gate path works without site packages.
  - `python -m pytest tests/test_dependency_hygiene.py tests/test_quality_gates.py -q` -> `15 passed in 0.78s`.
  - `python -m pytest -q` -> `324 passed in 7.23s`.
  - `PYTHONPATH=src python -m war_room.quality_gates run --gate dependency-hygiene-check --output-dir runs/quality_gates/local -- python -m war_room.dependency_hygiene --check` -> passed; wrote `runs/quality_gates/local/dependency-hygiene-check.json`.
  - `python -m war_room.dependency_hygiene --check` -> passed; `6/6` checks passed.
  - `python -m war_room --verify --release-candidate issue-9-dependency-hygiene-gate` -> passed; embedded `pytest -q` reported `324 passed in 11.65s`; offline preflight passed for 4 committed fixture scenarios; verify manifest written under `runs/verify/2026-05-13_issue-9-dependency-hygiene-gate_20260513t062318z.json`.

## Session 98 - Issue 9 Closeout Audit
Date: 2026-05-13
Status: Complete

- Completed the `#9` closeout review after the fixture snapshot, CI quality-gate categorization, security hygiene, offline e2e, and dependency hygiene slices landed.
- What changed:
  - Added `docs/ISSUE_9_CLOSEOUT_AUDIT.md`, mapping issue `#9` deliverables and acceptance criteria to the landed workflow jobs, quality-gate categories, tests, artifact outputs, and offline validation commands.
  - Synced README, handoff, roadmap, issue-map, release-rubric, build-checklist, repo-brief, and heartbeat status so `#9` is documented as ready to close when this PR lands.
- Why:
  - issue `#9` now has smoke/e2e coverage, fixture-quality and golden snapshot gates, dependency/secret/security hygiene checks, categorized CI artifacts, and offline demo/fixture compatibility.
  - remaining beta, pilot, production-security, product API/UI, and broader fixture-breadth work belongs to `#27`, `#19`, `#18`, `#10` to `#12`, and `#8` rather than staying hidden inside `#9`.
- Decision not added:
  - no runtime code, dependencies, notebooks, or generated committed artifacts were changed for this closeout.
  - no new formal decision-log entry was added; the closeout audit is the evidence artifact for this status change.
- Verification:
  - `python -m pytest -q` -> `324 passed in 9.66s`.
  - `python -m war_room.fixture_snapshots --check` -> passed; snapshot matched `tests/golden/offline_fixture_snapshots.json`.
  - `python -m war_room.security_hygiene --check` -> passed; `6/6` checks passed.
  - `python -m war_room.offline_e2e --check` -> passed; `4/4` scenarios passed and artifacts were written under `runs/offline_e2e/`.
  - `python -m war_room.dependency_hygiene --check` -> passed; `6/6` checks passed.
  - `python -m war_room --verify --release-candidate issue-9-closeout-review` -> passed; embedded `pytest -q` reported `324 passed in 8.81s`; offline preflight passed for 4 committed fixture scenarios; verify manifest written under `runs/verify/2026-05-13_issue-9-closeout-review_20260513t064805z.json`.

## Session 99 - Issue 7 Retrieval Failure-Mode Contracts
Date: 2026-05-13
Status: Complete

- Completed the next focused `#7` slice by hardening retrieval provider contract tests and normalized failure behavior.
- What changed:
  - `src/war_room/retrieval.py` now normalizes provider search/content rows at the project retrieval seam, rejects non-list provider responses with a project `RetrievalContractError`, and records partial/missing-field result sets as degraded retrieval tasks with review-required warning events instead of letting consumers crash on provider-shaped data.
  - Retrieval failure messages now include normalized `error_kind`, exception class, retryability, and attempt-count metadata for timeout, malformed response, budget exhaustion, and generic provider errors.
  - `src/war_room/exa_client.py` now raises `ExaResponseError` when Exa search responses are missing an iterable `results` payload, so adapter response drift is explicit and normalized by the retrieval seam.
  - `tests/test_retrieval_contracts.py` now covers timeout metadata, malformed provider responses, partial malformed rows, missing fields, empty results, content normalization, and provider mismatch behavior without live calls.
  - `tests/test_exa_client.py` now covers malformed Exa search responses and confirms they count against the search budget.
  - Status docs now reflect the 331-test baseline and the fifth landed `#7` slice.
- Why:
  - issue `#7` requires retrieval consumers to depend on project interfaces rather than provider SDK types, and specifically calls for deterministic failure-mode tests for timeouts, partial responses, malformed objects, and normalized error handling.
- Decision not added:
  - no new dependencies, notebooks, broad orchestration work, or evidence-normalization work were added.
  - this is a focused `#7` slice rather than a full closeout; a separate closeout review should confirm whether issue `#7` can now be closed.
- Verification:
  - `python -m pytest tests/test_retrieval_contracts.py tests/test_exa_client.py tests/test_exa_adapter_contract.py tests/test_citation_verify.py -q` -> `40 passed in 4.50s`.
  - `python -m pytest tests/test_weather.py tests/test_carrier.py tests/test_caselaw.py tests/test_workflow_summary.py -q` -> `42 passed in 0.35s`.
  - `python -m pytest -q` -> `331 passed in 8.41s`.
  - `python -m war_room.fixture_snapshots --check` -> passed; snapshot matched `tests/golden/offline_fixture_snapshots.json`.
  - `python -m war_room.security_hygiene --check` -> passed; `6/6` checks passed.
  - `python -m war_room.offline_e2e --check` -> passed; `4/4` scenarios passed and artifacts were written under `runs/offline_e2e/`.
  - `python -m war_room.dependency_hygiene --check` -> passed; `6/6` checks passed.
  - `python -m war_room --verify --release-candidate issue-7-retrieval-contract-hardening` -> passed; embedded `pytest -q` reported `331 passed in 8.75s`; offline preflight passed for 4 committed fixture scenarios; verify manifest written under `runs/verify/2026-05-13_issue-7-retrieval-contract-hardening_20260513t070332z.json`.

## Session 100 - Issue 7 Closure Sanity Audit
Date: 2026-05-13
Status: Complete

- Completed a short post-merge closure sanity audit for issue `#7` after PR `#56`.
- Audit conclusion:
  - issue `#7` is closed on GitHub with state reason `completed`, but closure is not accurate yet.
  - PR `#56` landed the fifth retrieval-contract slice, but a post-merge P2 review note and local probe show that provider responses of `None` still flow through the empty-results path instead of the malformed-response path.
- What changed:
  - Added `docs/ISSUE_7_CLOSURE_SANITY_AUDIT.md` with the closure decision, evidence reviewed, remaining gap, and recommended disposition.
  - Synced README, handoff, roadmap, issue-map, repo-brief, heartbeat, and CLAUDE status language so `#7` is described as needing a narrow reopen/follow-up rather than an unqualified close.
- Recommendation:
  - Reopen `#7`, or create a narrow follow-up issue titled `Reject None retrieval provider responses as malformed contract failures`.
- Decisions not added:
  - No runtime code, dependency, notebook, fixture, issue `#8`, issue `#10`, issue `#12`, or issue `#14` work was started.
- Validation:
  - `python -m pytest tests/test_retrieval_contracts.py tests/test_exa_client.py tests/test_exa_adapter_contract.py tests/test_citation_verify.py -q` -> `40 passed in 8.99s`.
  - `python -m pytest -q` -> `331 passed in 22.97s`.
  - `python -m war_room --verify --release-candidate issue-7-closure-sanity-audit` -> passed; embedded `pytest -q` reported `331 passed in 13.33s`; offline preflight passed for 4 committed fixture scenarios; verify manifest written under `runs/verify/2026-05-13_issue-7-closure-sanity-audit_20260513t194018z.json`.

## Session 101 - Issue 7 None Response Contract Fix
Date: 2026-05-13
Status: Complete

- Completed the narrow `#7` follow-up from the PR `#57` closure sanity audit.
- What changed:
  - `src/war_room/retrieval.py` now treats provider search/content responses of `None` as malformed provider responses by raising `RetrievalContractError` instead of normalizing them to empty result sets.
  - `execute_retrieval_task()` now emits failed retrieval metadata for `None` search responses with `error_kind=malformed_response`, `exception=RetrievalContractError`, `retryable=false`, and attempt-count metadata.
  - `fetch_retrieval_contents()` now applies the same malformed-response rule for `None` content responses.
  - `tests/test_retrieval_contracts.py` now covers direct search rejection, retrieval-task failure metadata, and content-fetch rejection for `None` provider responses without live Exa calls.
  - Status docs now mark the PR `#57` audit gap resolved and move `#7` back to complete/closed status.
- Why:
  - PR `#57` identified one remaining provider-contract gap after PR `#56`: a provider adapter returning `None` was indistinguishable from a legitimate no-results response.
- Decisions not added:
  - no dependencies, notebooks, fixture data, live Exa calls, issue `#8`, issue `#10`, issue `#12`, or issue `#14` work were added.
- Validation:
  - `python -m pytest tests/test_retrieval_contracts.py -q` -> `17 passed in 0.38s`.
  - `python -m pytest tests/test_retrieval_contracts.py tests/test_exa_client.py tests/test_exa_adapter_contract.py tests/test_citation_verify.py -q` -> `43 passed in 4.57s`.
  - `python -m pytest -q` -> `334 passed in 7.90s`.
  - `python -m war_room.fixture_snapshots --check` -> passed; snapshot matched `tests/golden/offline_fixture_snapshots.json`.
  - `python -m war_room.security_hygiene --check` -> passed; `6/6` checks passed.
  - `python -m war_room.offline_e2e --check` -> passed; `4/4` scenarios passed and artifacts were written under `runs/offline_e2e/`.
  - `python -m war_room.dependency_hygiene --check` -> passed; `6/6` checks passed.
  - `python -m war_room --verify --release-candidate issue-7-none-response-contract-fix` -> passed; embedded `pytest -q` reported `334 passed in 8.62s`; offline preflight passed for 4 committed fixture scenarios; verify manifest written under `runs/verify/2026-05-13_issue-7-none-response-contract-fix_20260513t195125z.json`.

## Session 102 - Issue 8 Fixture Breadth Registry Slice
Date: 2026-05-13
Status: Complete

- Completed the next focused `#8` fixture-breadth slice by promoting the existing committed Ida/Lloyd's/Orleans fixture lane into the curated scenario registry.
- What changed:
  - Added `scenarios/ida_orleans_lloyds_ho3.json` as an offline-ready registry scenario backed by the already committed `cache_samples/ida_lloyds_orleans` payloads.
  - Updated the scenario registry order, notebook-runtime/scenario/release-scorecard tests, and the golden offline fixture snapshot so registry-backed and offline-ready fixture counts now report Milton plus Ida.
  - Synced README, handoff, roadmap, issue-map, release-rubric, build-checklist, and repo-brief status language to say `#8` has a second registry-backed offline scenario while broader fixture breadth remains open.
- Why:
  - The existing Ida fixture lane is credible to promote without live retrieval or invented data because its intake and all four module fixtures are already committed.
  - Adding a brand-new fifth cache fixture directory would still require live retrieval or a separate curated fixture-seeding pass, so this PR intentionally broadens registry-backed coverage without changing fixture payload data.
- Decisions not added:
  - no dependencies, notebooks, live Exa calls, new cache payloads, or issue `#10` product-orchestration work were added.
  - no new formal decision-log entry was added; this is a narrow `#8` implementation slice under the existing fixture/snapshot direction.
- Validation:
  - `python -m pytest tests/test_fixture_snapshots.py tests/test_offline_demo_pack.py tests/test_intake_validation.py -q` -> `53 passed in 2.24s`.
  - `python -m pytest -q` -> `334 passed in 12.30s`.
  - `python -m war_room.fixture_snapshots --check` -> passed; snapshot matched `tests/golden/offline_fixture_snapshots.json`.
  - `python -m war_room.offline_e2e --check` -> passed; `4/4` scenarios passed and artifacts were written under `runs/offline_e2e/2026-05-13_offline-e2e_20260513t200751z.json`.
  - `python -m war_room --verify --release-candidate issue-8-fixture-breadth` -> passed; embedded `pytest -q` reported `334 passed in 12.66s`; offline preflight passed for 4 committed fixture scenarios; verify manifest written under `runs/verify/2026-05-13_issue-8-fixture-breadth_20260513t200758z.json`.
- Remaining issue status:
  - issue `#8` should remain open because the committed fixture directory count is still four and broader multi-jurisdiction fixture breadth/seeding work remains.

## Session 103 - Issue 8 Fixture Seeding Process
Date: 2026-05-13
Status: Complete

- Completed the next focused `#8` process slice by documenting how future curated offline scenarios should be seeded and promoted.
- What changed:
  - Added `docs/FIXTURE_SEEDING.md` with definitions for curated registry scenarios, committed fixture lanes, offline-demo-ready scenarios, and live-eval/intake-only scenarios.
  - Documented required evidence before `offline_demo_ready` promotion, including reviewed public/redacted facts, complete four-module fixture bundles, source/citation quality, disclaimer posture, snapshot review, and validation commands.
  - Added a lightweight scenario validation guard requiring `offline_demo_ready` scenarios to define `fixture_case_key`.
  - Added scenario tests proving offline-ready registry scenarios have complete committed fixture bundles and that unsafe promotion without a fixture key fails.
  - Synced status docs to the 336-test baseline and linked the fixture-seeding process from current `#8` status.
- Why:
  - issue `#8` still needs broader fixture breadth, but future additions need a repeatable, reviewable path that prevents intake-only or live-only scenarios from being treated as cache-only demos.
- Decisions not added:
  - no invented fixture payloads, live Exa calls, dependencies, notebooks, golden snapshot changes, or issue `#10` orchestration work were added.
  - no new formal decision-log entry was added; this is a process and guardrail slice under the existing `#8` fixture/snapshot direction.
- Validation:
  - `python -m pytest tests/test_fixture_snapshots.py tests/test_offline_demo_pack.py tests/test_intake_validation.py tests/test_scenarios.py -q` -> `64 passed in 6.15s`.
  - `python -m pytest -q` -> `336 passed in 16.48s`.
  - `python -m war_room.fixture_snapshots --check` -> passed; snapshot matched `tests/golden/offline_fixture_snapshots.json`.
  - `python -m war_room.offline_e2e --check` -> passed; `4/4` scenarios passed and artifacts were written under `runs/offline_e2e/2026-05-13_offline-e2e_20260513t203143z.json`.
  - `python -m war_room --verify --release-candidate issue-8-fixture-seeding-process` -> passed; embedded `pytest -q` reported `336 passed in 17.61s`; offline preflight passed for 4 committed fixture scenarios; verify manifest written under `runs/verify/2026-05-13_issue-8-fixture-seeding-process_20260513t203151z.json`.
- Remaining issue status:
  - issue `#8` should remain open because this slice defines and guards the process but does not add a new committed fixture lane.

## Session 104 - Issue 8 Next Scenario Candidate Audit
Date: 2026-05-13
Status: Complete

- Completed a focused `#8` next-scenario candidate audit using the fixture-seeding process.
- Audit conclusion:
  - top candidate: `tx_hail_allstate_tarrant`.
  - classification: ready to promote from existing committed fixture lane.
  - reason: it already has a validated intake, complete four-module fixture bundle, official weather support, carrier/caselaw/citation evidence, one verified citation, and passing snapshot/e2e posture.
- What changed:
  - Added `docs/ISSUE_8_NEXT_SCENARIO_AUDIT.md` with candidate classifications for committed fixture lanes, live-only registry scenarios, already-promoted lanes, and non-suitable template input.
  - Added `scenarios/texas_hail_tarrant_allstate_hob.json` as the first Texas hail homeowners registry-backed offline benchmark, mapped to `cache_samples/tx_hail_allstate_tarrant`.
  - Updated `scenarios/index.json`, scenario/notebook-runtime/release-scorecard/snapshot tests, and `tests/golden/offline_fixture_snapshots.json` so the Texas hail HO-B lane is registry-backed and offline-ready.
  - Synced status docs to note three registry-backed offline benchmarks while `#8` remains open.
- Decisions not added:
  - no invented fixture payloads, live retrieval, dependencies, notebooks, or issue `#10` orchestration work were added.
  - the narrower `tx_hail_allstate_tarrant_dp3` fixture lane remains a ready follow-up candidate rather than being promoted in this PR.
- Validation:
  - `python -m pytest tests/test_scenarios.py tests/test_fixture_snapshots.py tests/test_offline_demo_pack.py -q` -> `52 passed in 8.31s`.
  - `python -m pytest -q` -> `336 passed in 19.13s`.
  - `python -m war_room.fixture_snapshots --check` -> passed; snapshot matched `tests/golden/offline_fixture_snapshots.json`.
  - `python -m war_room.offline_e2e --check` -> passed; `4/4` scenarios passed and artifacts were written under `runs/offline_e2e/2026-05-13_offline-e2e_20260513t204601z.json`.
  - `python -m war_room --verify --release-candidate issue-8-next-scenario-audit` -> passed; embedded `pytest -q` reported `336 passed in 16.70s`; offline preflight passed for 4 committed fixture scenarios; verify manifest written under `runs/verify/2026-05-13_issue-8-next-scenario-audit_20260513t204614z.json`.
- Remaining issue status:
  - issue `#8` should remain open because broader fixture breadth, the Texas DP-3 promotion, and manual fixture seeding for live-only Florida scenarios remain incomplete.

## Session 105 - Issue 8 DP-3 Fixture Promotion
Date: 2026-05-13
Status: Complete

- Completed the next narrow `#8` fixture-breadth slice by promoting `tx_hail_allstate_tarrant_dp3` into the curated registry after checking it against `docs/FIXTURE_SEEDING.md`.
- Promotion conclusion:
  - `tx_hail_allstate_tarrant_dp3` satisfies the checklist because it has a validated intake, complete four-module committed fixture bundle, official weather support, carrier evidence tied to Texas/Allstate/DP-3, two case-law issue buckets, three citation checks, one verified citation, and passing offline preflight/e2e posture with disclaimers and review-required export state intact.
- What changed:
  - Added `scenarios/texas_hail_tarrant_allstate_dp3.json` as an offline-ready registry scenario backed by the existing committed `cache_samples/tx_hail_allstate_tarrant_dp3` fixture lane.
  - Updated `scenarios/index.json`, scenario/preflight/notebook-runtime/release-scorecard/snapshot tests, and `tests/golden/offline_fixture_snapshots.json` so all four committed fixture lanes are now registry-backed and offline-ready.
  - Synced active status docs and the prior next-candidate audit to remove stale language that treated the DP-3 lane as only a future promotion.
- Decisions not added:
  - no invented fixture payloads, live retrieval, dependencies, notebooks, or issue `#10` orchestration work were added.
  - issue `#8` remains open because broader fixture breadth and manual fixture seeding for live-only Florida registry scenarios remain incomplete.
- Validation:
  - `python -m pytest tests/test_scenarios.py tests/test_fixture_snapshots.py tests/test_offline_demo_pack.py -q` -> `52 passed in 2.35s`.
  - `python -m pytest -q` -> `336 passed in 7.61s`.
  - `python -m war_room.fixture_snapshots --check` -> passed; snapshot matched `tests/golden/offline_fixture_snapshots.json`.
  - `python -m war_room.offline_e2e --check` -> passed; `4/4` scenarios passed and artifacts were written under `runs/offline_e2e/2026-05-13_offline-e2e_20260513t205728z.json`.
  - `python -m war_room --verify --release-candidate issue-8-dp3-fixture-promotion` -> passed; embedded `pytest -q` reported `336 passed in 9.27s`; offline preflight passed for 4 committed fixture scenarios; verify manifest written under `runs/verify/2026-05-13_issue-8-dp3-fixture-promotion_20260513t205736z.json`.

## Session 106 - Issue 8 Readiness Audit
Date: 2026-05-14
Status: Complete

- Completed the requested `#8` readiness/closeout audit after all four committed fixture lanes became registry-backed and offline-ready.
- Audit conclusion:
  - issue `#8` should remain open.
  - all four committed fixture lanes are registry-backed and offline-ready, and the snapshot/quality gates satisfy the current four-lane acceptance criteria.
  - the remaining blocker is the issue deliverable for fixture breadth beyond the four committed directories: the repo still has exactly four complete fixture lanes.
- What changed:
  - Added `docs/ISSUE_8_READINESS_AUDIT.md` mapping issue `#8` deliverables and acceptance criteria to the current registry, fixture, snapshot, and offline-e2e state.
  - Documented current breadth across states, perils, carriers, policy types, and postures.
  - Documented remaining live-only Florida registry candidates and confirmed there is no unpromoted standalone intake-only fact pattern beyond the template.
  - Synced README, handoff, roadmap, issue map, repo brief, CLAUDE, and heartbeat status language to point at the new audit and the exact remaining blocker.
- Recommendation:
  - keep `#8` open for one final fixture-seeding PR that manually seeds a live-only Florida registry scenario, preferably `ian_lee_citizens_ho3` unless source review chooses a stronger candidate.
  - if maintainers decide four registry-backed fixture lanes are enough for `#8`, create a follow-up issue titled `Manually seed live-only Florida fixture scenarios` before closing `#8`.
- Decisions not added:
  - no fixture payloads, invented data, live retrieval, dependencies, notebooks, or issue `#10` orchestration work were added.
  - this PR intentionally leaves issue `#8` open for maintainer review.
- Validation:
  - `python -m pytest tests/test_scenarios.py tests/test_fixture_snapshots.py tests/test_offline_demo_pack.py -q` -> `52 passed in 10.10s`.
  - `python -m pytest -q` -> `336 passed in 23.19s`.
  - `python -m war_room.fixture_snapshots --check` -> passed; snapshot matched `tests/golden/offline_fixture_snapshots.json`.
  - `python -m war_room.offline_e2e --check` -> passed; `4/4` scenarios passed and artifacts were written under `runs/offline_e2e/2026-05-14_offline-e2e_20260514t020742z.json`.
  - `python -m war_room --verify --release-candidate issue-8-readiness-audit` -> passed; embedded `pytest -q` reported `336 passed in 19.04s`; offline preflight passed for 4 committed fixture scenarios; verify manifest written under `runs/verify/2026-05-14_issue-8-readiness-audit_20260514t020751z.json`.

## Session 107 - Issue 8 Final Florida Fixture Lane
Date: 2026-05-14
Status: Complete

- Completed the requested final safe `#8` fixture-seeding slice by manually source-reviewing and promoting `ian_lee_citizens_ho3` into the committed offline fixture suite as `ian_citizens_lee`.
- Candidate conclusion:
  - `ian_lee_citizens_ho3` was the safest Florida candidate because the registry scenario already existed and the public source review supported the Hurricane Ian Lee County event, Citizens carrier context, HO-3 policy context, and Florida Supreme Court authorities without inventing facts.
  - the fixture lane contains complete `weather`, `carrier`, `caselaw`, and `citation_verify` payloads, plus the matching flat cache keys required by the cache-first runtime.
- What changed:
  - Added `cache_samples/ian_citizens_lee/` and matching flat cache files for weather, carrier, case law, and citation checks.
  - Promoted `scenarios/ian_lee_citizens_ho3.json` to `offline_demo_ready: true` with `fixture_case_key: ian_citizens_lee`.
  - Updated offline pack, scenario, notebook-runtime, bootstrap, offline-e2e, release-scorecard, and snapshot tests for the five-lane baseline.
  - Refreshed `tests/golden/offline_fixture_snapshots.json`; the intentional diff adds `ian_citizens_lee` and updates registry counts/lists from four to five lanes.
  - Synced README, handoff, roadmap, issue map, rubric, repo brief, CLAUDE, build checklist, foundation, heartbeat, and `#8` audit docs to the five-lane state.
- Decisions not added:
  - no live retrieval was added to tests, snapshot checks, offline e2e, or verify.
  - no dependencies, notebooks, invented facts, invented sources, invented citations, or issue `#10` orchestration work were added.
  - this PR intentionally keeps issue `#8` open for maintainer review and avoids auto-close keywords.
- Validation:
  - `python -m pytest tests/test_scenarios.py tests/test_fixture_snapshots.py tests/test_offline_demo_pack.py -q` -> `59 passed in 5.24s`.
  - `python -m pytest -q` -> `343 passed in 27.82s`.
  - `python -m war_room.fixture_snapshots --check` -> passed; snapshot matched `tests/golden/offline_fixture_snapshots.json`.
  - `python -m war_room.offline_e2e --check` -> passed; `5/5` scenarios passed and artifacts were written under `runs/offline_e2e/2026-05-14_offline-e2e_20260514t025227z.json`.
  - `python -m war_room --verify --release-candidate issue-8-final-florida-fixture` -> passed; embedded `pytest -q` reported `343 passed in 19.77s`; offline preflight passed for 5 committed fixture scenarios; verify manifest written under `runs/verify/2026-05-14_issue-8-final-florida-fixture_20260514t025241z.json`.

## Session 108 - Issue 8 Closed-Status Docs Sync
Date: 2026-05-14
Status: Complete

- Completed a focused docs-only status sync after issue `#8` was closed as completed and PR #63 was merged.
- What changed:
  - Updated current-state docs so `#8` now reads as complete/closed after the five registry-backed offline-ready fixture lanes landed.
  - Kept #64 and #65 documented as non-blocking hygiene/normalization follow-ups rather than `#8` blockers.
  - Moved the next roadmap focus back to `#27` scorecard/rubric operationalization.
- Decisions not added:
  - no runtime code, fixture data, dependencies, notebooks, or live retrieval work were added.
  - no additional Florida fixture seeding was scoped in this docs-only closeout sync.
- Validation:
  - `git diff --check` -> passed.
  - `python -m war_room.fixture_snapshots --check` -> passed; snapshot matched `tests/golden/offline_fixture_snapshots.json`.
  - `python -m war_room --verify --release-candidate issue-8-closed-status-docs-sync` -> passed; embedded `pytest -q` reported `343 passed in 17.15s`; offline preflight passed for 5 committed fixture scenarios; verify manifest written under `runs/verify/2026-05-14_issue-8-closed-status-docs-sync_20260514t042129z.json`.

## Session 109 - Issue 27 Scorecard Operationalization
Date: 2026-05-15
Status: Complete

- Completed a narrow `#27` operationalization slice for the existing V2 release rubric and scorecard.
- What changed:
  - `src/war_room/release_scorecard.py` now tags must-pass gates and calibration thresholds as `blocking`, scored dimensions as `advisory`, and writes a top-level `readiness_posture` summary for dashboard consumers.
  - Release scorecard Markdown now includes a Dashboard Readiness Summary with demo-ready, pilot-ready, and release-ready posture language plus blocking/advisory counts.
  - Scorecard validation now fails artifacts that omit dashboard readiness posture or readiness categories.
  - `tests/test_release_scorecard.py` covers the new JSON/Markdown fields, category validation, failed verification posture, and failed preflight posture.
  - `docs/V2_RELEASE_RUBRIC.md` now clarifies blocking vs advisory metrics, release-ready posture, benchmark scenario evidence, and pilot-ready language without adding a new rubric.
  - Current-state docs were synced to the 371-test baseline and the merged #64/#65 hygiene follow-ups.
- Decisions not added:
  - no fixture facts, citation facts, cache samples, notebooks, live retrieval behavior, dependencies, `#17` observability implementation, `#19` pilot execution, or `#25` AI guardrail implementation were changed.
  - no pilot-study design, new benchmark scenarios, or actual pilot-readiness claim was added.
- Validation:
  - `python -m pytest tests/test_release_scorecard.py tests/test_bootstrap.py tests/test_quality_gates.py -q` -> `32 passed in 3.47s`.
  - `python -m pytest -q` -> `371 passed in 11.95s`.
  - `python -m war_room.fixture_snapshots --check` -> passed; snapshot matched `tests/golden/offline_fixture_snapshots.json`.
  - `python -m war_room.offline_e2e --check` -> passed; `5/5` scenarios passed and artifacts were written under `runs/offline_e2e/2026-05-15_offline-e2e_20260515t051126z.json`.
  - `python -m war_room --verify --release-candidate issue-27-scorecard-operationalization` -> passed; embedded `pytest -q` reported `371 passed in 10.62s`; offline preflight passed for 5 committed fixture scenarios; verify manifest written under `runs/verify/2026-05-15_issue-27-scorecard-operationalization_20260515t051144z.json`.
  - `python -m war_room.release_scorecard --validate-latest --output-dir runs\release_scorecards` -> passed; latest scorecard validation selected `runs\release_scorecards\2026-05-15_issue-27-scorecard-operationalization_20260515t051144z.json`.
  - `git diff --check` -> passed.

## Session 110 - Issue 10 Run-State Contract Slice
Date: 2026-05-15
Status: Complete

- Completed the first narrow `#10` orchestration slice without adding the API service or changing notebook/demo runtime behavior.
- What changed:
  - Added `src/war_room/orchestration.py` with canonical run states, stage keys, stage statuses, transition validation, terminal-state helpers, a `StageStateSnapshot` normalization shape, stage-to-run rollup logic, and review-required rollup logic.
  - Reused the new status literals from `src/war_room/models.py` so canonical `Run` and `RunStage` records share the same state vocabulary as the orchestration contract.
  - Updated `src/war_room/workflow_summary.py` so current run-timeline status derivation delegates to the shared rollup helper while preserving the existing V0 output-stage semantics.
  - Added `tests/test_orchestration_state.py` covering valid/invalid run transitions, valid/invalid stage transitions, stage normalization, partial-success behavior, failed-stage behavior, completed-run behavior, queued state, and running state.
  - Added `docs/ISSUE_10_RUN_STATE_CONTRACT.md` and linked current docs to clarify how the contract supports future `#10` API orchestration.
  - Synced current-state docs to the `382`-test baseline and this branch's validation trail.
- Decisions not added:
  - no HTTP API framework, API routes, background queue, database, persistence layer, auth, dashboard, UI design, retry policy, circuit breaker behavior, or human-review workflow was added.
  - no dependencies, fixture facts, citation facts, cache samples, notebooks, live retrieval behavior, golden snapshots, or placeholder V2 runtime surfaces were changed.
- Validation:
  - `python -m pytest tests/test_orchestration*.py tests/test_offline_demo_pack.py tests/test_release_scorecard.py -q` -> `95 passed in 2.01s` when run through Git Bash for glob expansion.
  - `python -m pytest tests\test_orchestration_state.py tests\test_offline_demo_pack.py tests\test_release_scorecard.py -q` -> `95 passed in 2.40s` as the explicit PowerShell equivalent.
  - `python -m pytest -q` -> `382 passed in 9.75s`.
  - `python -m war_room.fixture_snapshots --check` -> passed; snapshot matched `tests/golden/offline_fixture_snapshots.json`.
  - `python -m war_room.offline_e2e --check` -> passed; `5/5` scenarios passed and artifacts were written under `runs/offline_e2e/2026-05-15_offline-e2e_20260515t054312z.json`.
  - `python -m war_room --verify --release-candidate issue-10-run-state-contract` -> passed; embedded `pytest -q` reported `382 passed in 10.25s`; offline preflight passed for 5 committed fixture scenarios; verify manifest written under `runs/verify/2026-05-15_issue-10-run-state-contract_20260515t054320z.json`.
  - `git diff --check` -> passed.

## Session 111 - Issue 73 Orchestration API Contracts
Date: 2026-05-15
Status: Complete

- Completed the issue `#73` contract-first slice for future issue `#10` API work without adding a live API service or changing notebook/offline demo behavior.
- What changed:
  - Added `src/war_room/orchestration_api_contracts.py` with typed Pydantic contracts for future start-run request, start-run response, get-run-status response, stage/status/timeline payloads, preserved usable outputs, stage failure details, and a small error response shape.
  - Reused the canonical run statuses, stage keys, and stage statuses from `src/war_room/orchestration.py`, while nesting existing canonical `Run`, `RunStage`, and `RunEvent` concepts where appropriate.
  - Added `tests/test_orchestration_api_contracts.py` covering serialization, validation, invalid states, queued creation, running progress, completed runs, partial-success with preserved outputs, failed runs with stage failure details, and review-required completed runs.
  - Added `docs/ISSUE_10_API_CONTRACTS.md` and linked current docs to clarify these are API contracts only, not a live service.
  - Synced current-state docs to the `400`-test baseline and this branch's validation trail.
- Decisions not added:
  - no HTTP routes, API framework, background queue, database tables, persistence, auth, retry policy, circuit breakers, dashboard work, UI, or placeholder V2 runtime surface was added.
  - no fixtures, cache samples, citation facts, notebooks, live retrieval behavior, golden snapshots, or dependencies were changed.
- Validation:
  - `python -m pytest tests/test_orchestration*.py tests/test_*api* -q` -> `39 passed in 0.50s` when run through Git Bash for glob expansion.
  - `python -m pytest -q` -> `400 passed in 11.52s`.
  - `python -m war_room.fixture_snapshots --check` -> passed; snapshot matched `tests/golden/offline_fixture_snapshots.json`.
  - `python -m war_room.offline_e2e --check` -> passed; `5/5` scenarios passed and artifacts were written under `runs/offline_e2e/2026-05-15_offline-e2e_20260515t061619z.json`.
  - `python -m war_room --verify --release-candidate issue-10-api-contracts` -> passed; embedded `pytest -q` reported `400 passed in 11.77s`; offline preflight passed for 5 committed fixture scenarios; verify manifest written under `runs/verify/2026-05-15_issue-10-api-contracts_20260515t061627z.json`.
  - `git diff --check` -> passed.

## Session 112 - Offline Notebook Citation Review Fix
Date: 2026-05-15
Status: Complete

- Fixed the offline notebook citation-review runtime failure without changing the broader research engine.
- Root cause:
  - Cell 6 passed `client=None` to `spot_check_citations(...)` in offline mode.
  - `spot_check_citations(...)` reads `client.provider_name` before per-citation cache lookup can run, so the offline notebook crashed before `citecheck` existed.
- What changed:
  - Added notebook-runtime citation helpers that load `cache_samples/<case_key>/citation_verify.json` for offline cache-backed notebook runs.
  - Preserved the live citation spot-check path when live retrieval is enabled and a real retrieval client exists.
  - Added a safe review-required fallback payload when an offline scenario citation fixture is missing, without attempting live retrieval.
  - Updated Cell 6 to call the helper and cleared stale failed notebook outputs while preserving the default `milton_pinellas_citizens_ho3` scenario.
  - Added focused tests for fixture loading, null-client offline behavior, live delegation, and missing-fixture fallback.
- Decisions not added:
  - no live retrieval, fixture changes, cache-sample changes, memo generation changes, golden snapshot updates, package dependencies, CI changes, or broader citation-engine refactor were added.
  - no legal/demo disclaimer or citation-review warning language was weakened.
- Validation:
  - `python -m pytest tests\test_notebook_runtime.py tests\test_citation_verify.py tests\test_preflight.py -q` -> `34 passed in 3.16s`.
  - `python -m jupyter nbconvert --execute notebooks/01_case_war_room.ipynb --to notebook --output-dir runs/notebook_smoke --output 01_case_war_room.executed.ipynb --ExecutePreprocessor.timeout=180` -> passed; executed notebook written to `runs/notebook_smoke/01_case_war_room.executed.ipynb`.
  - Executed notebook evidence: Cell 1 output showed `USE_CACHE: True` and `LIVE_RETRIEVAL: False`; Cell 6 output included Citation Spot-Check, Evidence Board, and ISSUE WORKSPACE; Cell 7 output included MEMO COMPOSER, RUN TIMELINE, EXPORT HISTORY, and a saved memo path.
  - `python -m war_room --preflight` -> passed; `5/5` offline scenarios passed.
  - `python -m war_room --verify` -> passed; embedded `pytest -q` reported `405 passed in 10.46s`; verify manifest written under `runs/verify/2026-05-16_docs-notebook-demo-narrative-polish_20260516t012421z.json`.
  - `python -m pytest -q` -> `405 passed in 9.95s`.
  - `python -m war_room.fixture_snapshots --check` -> passed; snapshot matched `tests/golden/offline_fixture_snapshots.json`.
  - `python -m war_room.offline_e2e --check` -> passed; `5/5` scenarios passed and artifact `runs/offline_e2e/2026-05-16_offline-e2e_20260516t012508z.json` was written.
  - `python -m json.tool notebooks/01_case_war_room.ipynb | Out-Null` -> passed.
  - `git diff --check` -> passed.

## Session 113 - Issue 10 Offline Orchestration Service Slice
Date: 2026-05-16
Status: Complete

- Completed the first narrow issue `#10` product-mode service slice without adding HTTP routes, web UI, persistence, queues, auth, dashboard, dependencies, fixture changes, or live retrieval.
- Root design choice:
  - added a synchronous in-process service boundary over the existing offline notebook-era runtime so future HTTP/API wrapping can reuse the same typed start-run and get-run-status contracts.
- What changed:
  - Added `src/war_room/orchestration_service.py` with `InMemoryOrchestrationService`, process-local `start_run`, `execute_run`, `get_run_status`, and `get_run_outputs` helpers, typed failure payload conversion, preserved in-memory output containers, and a dependency-free smoke CLI.
  - The service accepts `StartRunRequest`, creates a queued `StartRunResponse`, maps the typed intake to a curated offline-ready scenario, executes committed fixture-backed weather/carrier/caselaw/citation paths with `client=None`, builds evidence-board, issue-workspace, memo-composer, export-history, and run-timeline read models, and returns typed `GetRunStatusResponse` payloads.
  - Added `tests/test_orchestration_service.py` covering queued start/status, fixture-backed execution, preserved usable outputs, no live retrieval calls, partial-success behavior for a failed output stage, and typed failed status for missing offline scenarios.
  - Added `docs/ISSUE_10_SERVICE_SLICE.md` and synced README, handoff, roadmap, repo brief, CLAUDE, and heartbeat status to the 411-test service-slice baseline.
  - Fixed a security-hygiene false positive where notebook output text `EXA_API_KEY: not set` was treated as a committed secret assignment; added regression coverage in `tests/test_security_hygiene.py`.
- Decisions not added:
  - no FastAPI, Flask, Streamlit, React, Next.js, background workers, database, persistence, auth, access control, retry policy, circuit breakers, dashboard, web intake UI, dependency changes, fixture edits, golden snapshot edits, notebook behavior changes, or live retrieval were added.
  - `notebooks/01_case_war_room.ipynb` and `Untitled.ipynb` were already dirty before this slice and were not part of the service implementation.
- Smoke validation:
  - `python -m war_room.orchestration_service --smoke --scenario milton_pinellas_citizens_ho3` -> passed; status `completed`, `review_required=true`, stages included `citation_verify=degraded`, `memo_assembly=degraded`, `export=skipped`, and usable outputs included weather, carrier, caselaw, citation verification, memo draft, and audit bundle summaries.
- Validation:
  - `python -m pytest tests/test_orchestration_service.py tests/test_orchestration_api_contracts.py tests/test_orchestration_state.py -q` -> `35 passed in 3.44s`.
  - `python -m pytest tests/test_security_hygiene.py -q` -> `6 passed in 2.55s`.
  - `python -m pytest tests/test_orchestration*.py tests/test_notebook_runtime.py tests/test_preflight.py -q` -> `56 passed in 13.32s` when run through Git Bash for glob expansion.
  - `python -m pytest -q` -> `411 passed in 15.59s` after the final docs/session-log update.
  - `python -m war_room --preflight` -> passed; `5/5` offline scenarios passed.
  - `python -m war_room --verify` -> passed; embedded `pytest -q` reported `411 passed in 24.39s`; verify manifest written under `runs/verify/2026-05-16_feat-issue-10-offline-orchestration-service_20260516t031924z.json`.
  - `python -m war_room.fixture_snapshots --check` -> passed; snapshot matched `tests/golden/offline_fixture_snapshots.json`.
  - `python -m war_room.offline_e2e --check` -> passed; `5/5` scenarios passed and artifact `runs/offline_e2e/2026-05-16_offline-e2e_20260516t032031z.json` was written.
  - `python -m war_room.security_hygiene --check` -> passed; `6/6` checks passed.
  - `python -m war_room.dependency_hygiene --check` -> passed; `6/6` checks passed.
  - `git diff --check` -> passed.

## Session 114 - Issue 10 Run-Status Presentation Contract
Date: 2026-05-16
Status: Complete

- Completed a small orchestration run-status presentation contract without adding
  a web framework, HTTP route, persistence, queues, auth, workers, dependencies,
  fixture changes, or live retrieval.
- What changed:
  - Added `src/war_room/orchestration_status_view.py` with a dataclass-based
    `OrchestrationStatusView` and payload helper that converts typed
    `GetRunStatusResponse` values into stable operator-facing fields:
    canonical `status`, derived `operator_status`, `headline`,
    `operator_message`, usable-output availability, review reasons, degraded
    stages, failed stages, typed failure details, and next actions.
  - Updated the offline service smoke CLI so
    `python -m war_room.orchestration_service --smoke --scenario milton_pinellas_citizens_ho3`
    now prints the operator-facing summary while preserving the existing
    machine-readable status, stage summary, and usable-output summary.
  - Added focused presentation tests for completed, review-required, degraded,
    partial-success, and failed run outcomes, plus a smoke CLI output assertion.
  - Added `docs/ISSUE_10_STATUS_PRESENTATION.md` with run-status meanings, the
    smoke command, demo-operator checks, usable-output semantics, and explicit
    out-of-scope items.
- Decisions not added:
  - no distinct canonical `degraded` or `review_required` run state was added;
    the presentation layer derives those operator statuses from completed runs
    with degraded stages or `review_required=true`.
  - no API transport, web app, live claim intake, production auth, persistence,
    queues, retries, circuit breakers, dashboards, fixture changes, notebook
    changes, or dependency changes were added.
- Validation:
  - `python -m pytest tests/test_orchestration_status_view.py tests/test_orchestration_service.py -q` -> `11 passed in 3.51s`.
  - `python -m pytest tests/test_orchestration_service.py tests/test_orchestration_api_contracts.py tests/test_orchestration_state.py -q` -> `36 passed in 2.78s`.
  - `python -m pytest -q` -> `417 passed in 22.09s`.
  - `python -m war_room --verify` -> passed; embedded `pytest -q` reported `417 passed in 22.32s`; verify manifest written under `runs/verify/2026-05-16_codex-orchestration-status-presentation-contract_20260516t040535z.json`.
  - `python -m war_room.orchestration_service --smoke --scenario milton_pinellas_citizens_ho3` -> passed; status `completed`, `operator_status=degraded`, `usable_outputs_available=true`, `review_required=true`, degraded stages included `citation_verify` and `memo_assembly`, and usable output summaries included weather, carrier, caselaw, citation verification, memo draft, and audit bundle.
  - `git diff --check` -> passed.

## Session 115 - Issue 78 Thin Orchestration Transport Wrapper
Date: 2026-05-16
Status: Complete

- Completed issue `#78` as a narrow dependency-free transport/request-handler
  wrapper over the existing offline orchestration service and status
  presentation contracts.
- What changed:
  - Added `src/war_room/orchestration_transport.py` with
    `handle_start_run`, `handle_execute_run`, `handle_get_run_status`, and
    `transport_response_to_payload`.
  - The transport handlers accept existing typed request/status contracts,
    return JSON-safe dictionaries with `ok`, `operation`, `payload`, and
    `status_presentation`, and keep the service's usable outputs and typed
    failure details intact.
  - Added public lazy exports for the transport helpers from
    `src/war_room/__init__.py`.
  - Added `tests/test_orchestration_transport.py` covering queued start
    payloads, Milton execute/status behavior, review-required/degraded
    operator presentation, reachable partial-success behavior, unmapped
    scenario failure details, unknown run IDs, and invalid start payloads.
  - Added `docs/ISSUE_78_THIN_TRANSPORT_WRAPPER.md` with the wrapper shape,
    error semantics, explicit non-goals, and local validation commands.
  - Cross-linked the new transport note from the service and status
    presentation docs without changing their original slice boundaries.
- Decisions not added:
  - no FastAPI, Flask, Streamlit, React, Next.js, HTTP routing, server startup,
    auth, sessions, persistence, queues, background workers, retries, circuit
    breakers, dashboards, web UI, dependencies, notebook changes, fixtures,
    cache samples, citation facts, prompts, schemas, golden snapshots, or live
    retrieval changes were added.
  - offline scenario failures after a run is accepted remain service-level
    typed failed status responses (`ok=true`) rather than transport errors.
- Validation:
  - `python -m pytest tests/test_orchestration_transport.py -q` -> `6 passed in 6.63s`.
  - `python -m pytest tests/test_orchestration_transport.py tests/test_orchestration_service.py tests/test_orchestration_api_contracts.py tests/test_orchestration_status_view.py tests/test_orchestration_state.py -q` -> `47 passed in 7.67s`.
  - `python -m pytest -q` -> `423 passed in 19.60s`.
  - `python -m war_room --verify` -> passed; embedded `pytest -q` reported `423 passed in 18.67s`; verify manifest written under `runs/verify/2026-05-16_codex-issue-78-thin-orchestration-transport_20260516t043722z.json`.
  - `python -m war_room.orchestration_service --smoke --scenario milton_pinellas_citizens_ho3` -> passed; status `completed`, `operator_status=degraded`, `usable_outputs_available=true`, `review_required=true`, degraded stages included `citation_verify` and `memo_assembly`, and usable output summaries included weather, carrier, caselaw, citation verification, memo draft, and audit bundle.
  - `git diff --check` -> passed.

## Session 116 - Post-PR79 Status Docs Refresh
Date: 2026-05-16
Status: Complete

- Refreshed repo status docs after merged PR `#79` without changing runtime
  behavior.
- What changed:
  - Started from latest `main` at PR `#79` and inspected the existing stash
    `wip docs after issue 10 service slice`.
  - Kept the useful service-slice wording from that stash, then updated the
    status docs to include the PR `#77` status presentation layer and PR `#79`
    thin transport/request-handler wrapper.
  - Synced handoff, heartbeat, repo brief, README, roadmap, Claude/agent
    guidance, repo memory front door, and the issue `#73` API contract note to
    the `423`-test post-transport baseline.
- Decisions not added:
  - no runtime code, dependencies, routes, FastAPI/Flask/Streamlit/React/Next.js
    surfaces, persistence, queues, auth, retries, circuit breakers, dashboards,
    UI, fixture changes, notebook changes, or live retrieval were added.
  - preserved the transport distinction that invalid requests or unknown run
    IDs return `ok=false`, while accepted orchestration run failures stay
    `ok=true` with `payload.run.status="failed"`.
- Validation:
  - `git diff --check` -> passed.
  - `python -m pytest -q` -> `423 passed in 24.83s`.
  - `python -m war_room --verify` -> passed; embedded `pytest -q` reported
    `423 passed in 19.46s`; verify manifest written under
    `runs/verify/2026-05-16_docs-post-pr79-housekeeping_20260516t194522z.json`.
  - `python -m war_room.orchestration_service --smoke --scenario milton_pinellas_citizens_ho3`
    -> passed; status `completed`, `operator_status=degraded`, and usable
    outputs were available.
