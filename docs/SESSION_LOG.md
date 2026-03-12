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
