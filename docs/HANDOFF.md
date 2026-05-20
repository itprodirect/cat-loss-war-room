# CAT-Loss War Room - Handoff

Start here for a practical orientation to the current repo state.

## 1) What this repo is

A notebook-first litigation research assistant for catastrophic insurance loss work.
Given a case intake, it assembles:

- weather corroboration,
- carrier intelligence,
- issue-organized case law,
- citation spot-checks,
- and a markdown research memo.

This is research acceleration, not legal advice.

## 2) Current status (as of May 20, 2026)

| Item | Status |
|---|---|
| Notebook cells 0-7 | Working |
| Offline demo (`USE_CACHE=true`) | Working |
| Tests | 462 passing under the supported verify path after editable install or `PYTHONPATH=src`; raw-checkout `pytest -q` is not a supported path |
| CI | Fresh-env test gate + offline fixture smoke plus golden snapshot gate + offline e2e gate + offline security and dependency hygiene gates + exa-py compatibility matrix + release-scorecard artifact job with artifact validation, all using editable package install and categorized quality-gate artifacts |
| Exa compatibility hardening (`#4`) | Complete and closed |
| Intake schema alignment (`#5`) | Complete and closed |
| Typed domain contracts (#6) | Complete with closeout audit (intake/query + packs + citation/export contracts + graph/version envelopes + issue/authority contracts + run/retrieval lifecycle contracts + review/export graph-linkage contracts + schema-versioned runtime cache envelopes + Run Timeline, Evidence Board, Issue Workspace, Memo Composer, and Export History read-model contracts; see `docs/ISSUE_6_CLOSEOUT_AUDIT.md`) |
| Retrieval contracts (#7) | Complete: provider seam, notebook retrieval-state emission, citation-verify tracking, deterministic timing, provider failure-mode normalization, and `None` provider-response malformed-contract handling are landed; the PR #57 audit gap is resolved in `docs/ISSUE_7_CLOSURE_SANITY_AUDIT.md` |
| Scenario fixtures (#8) | Complete and closed: five committed scenario directories cover Florida, Texas, and Louisiana; all five now map from the curated registry to offline-ready committed fixture lanes, including Ian/Lee/Citizens HO-3 and the Texas hail/Tarrant/Allstate DP-3 matching benchmark; the deterministic golden snapshot gate checks output structure, source mix, case counts, citation summaries, and coverage metadata; `docs/FIXTURE_SEEDING.md`, `docs/ISSUE_8_NEXT_SCENARIO_AUDIT.md`, and `docs/ISSUE_8_READINESS_AUDIT.md` preserve the fixture-promotion evidence |
| CI quality gates (#9) | Complete with closeout audit in `docs/ISSUE_9_CLOSEOUT_AUDIT.md`: categorized quality-gate artifacts, offline fixture and golden snapshot checks, offline e2e validation, security hygiene, dependency hygiene, Exa compatibility diagnostics, and release-scorecard validation are all wired |
| Product foundation (`#22`) | Complete and closed: packaging/bootstrap lane implemented |
| Workflow IA spec (`#23`) | Complete and closed as the written source of truth in `docs/V2_WORKFLOW_IA.md` |
| Evidence schema spec (`#24`) | Complete and closed as the written source of truth in `docs/V2_EVIDENCE_SCHEMA.md` |
| Quality rubric (`#27`) | First-pass rubric plus local and CI artifact workflows landed in `docs/V2_RELEASE_RUBRIC.md`; demo-ready threshold calibration, blocking/advisory metric categories, live preflight evidence, run-scoped verify artifacts, verify manifests, a stable latest pointer, the human reviewer guide in `docs/ISSUE_27_RELEASE_EVIDENCE_REVIEW_GUIDE.md`, the issue `#88` top-level `reviewer_summary` convenience layer, and the issue `#92` / PR `#93` `ci_reporting_summary` inventory are now explicit, while broader CI and pilot operationalization remain open |
| Orchestration API (`#10`) | First narrow run-state contract slice is implemented in `src/war_room/orchestration.py` and documented in `docs/ISSUE_10_RUN_STATE_CONTRACT.md`; issue `#73` adds typed start-run and get-run-status API boundary contracts in `src/war_room/orchestration_api_contracts.py` and `docs/ISSUE_10_API_CONTRACTS.md`; the first in-process offline service slice is implemented in `src/war_room/orchestration_service.py` and documented in `docs/ISSUE_10_SERVICE_SLICE.md`; the operator-facing status presentation layer is implemented in `src/war_room/orchestration_status_view.py` and documented in `docs/ISSUE_10_STATUS_PRESENTATION.md`; issue `#78` adds the dependency-free thin transport/request-handler wrapper in `src/war_room/orchestration_transport.py` and `docs/ISSUE_78_THIN_TRANSPORT_WRAPPER.md`; the dev-only standard-library HTTP adapter lives in `src/war_room/orchestration_http.py` and `docs/ISSUE_10_DEV_HTTP_WRAPPER.md`; production API routing, queues, persistence, retries, circuit breakers, auth, dashboards, and UI remain future work |
| Guided intake and run-status UX specs (`#11`) | First narrow run-status UX/spec slice is documented in `docs/ISSUE_11_RUN_STATUS_UX_SPEC.md`, with a deterministic Milton degraded preview in `docs/examples/run_status_milton_degraded.md`; a companion guided-intake UX/spec slice is documented in `docs/ISSUE_11_GUIDED_INTAKE_UX_SPEC.md`, with the deterministic Milton guided-intake preview in `docs/examples/guided_intake_milton_preview.md`; future user-facing status screens should consume the existing transport/HTTP `status_presentation` payload and must not infer operator status independently when the presentation payload already provides it; frontend implementation, dashboards, auth, persistence, and production API work remain future work |
| Evidence/provenance adapters and helper-only dedupe (`#12`) | First narrow adapter seams have landed for current weather, carrier, caselaw, and citation-verification module output: issue `#94` / PR `#95` added `caselaw_pack_to_evidence_items(...)`, issue `#96` / PR `#97` added `carrier_doc_pack_to_evidence_items(...)`, issue `#98` / PR `#99` added `weather_brief_to_evidence_items(...)`, and issue `#103` / PR `#105` added `citation_verify_pack_to_evidence_items(...)`; issue `#107` / PR `#108` added helper-only `dedupe_evidence_items(...)` over canonical `EvidenceItem` rows. The helper is local and deterministic but not integrated into audit snapshot assembly, and no `old_id -> retained_id` remapping exists yet; these slices are not a full V2 evidence graph, database, dashboard, API, review workflow, or product runtime |
| Cache samples | Milton/Citizens/Pinellas + Ian/Citizens/Lee + TX hail/Allstate/Tarrant + TX hail matching/Allstate Texas Lloyds/Tarrant DP-3 + Ida/Lloyd's/Orleans committed |

## 3) What changed recently

- Exa client now supports both older and newer `exa-py` contents APIs.
- Dependency versions are pinned for reproducible installs.
- CI now blocks merges if fresh-env tests fail.
- CI also runs an `exa-py` compatibility matrix (`exa-py==2.0.2` and `exa-py==1.14.0`).
- Adapter smoke tests were added for kwargs forwarding contracts.
- Intake JSON now has strict schema validation and file-loading helpers.
- Typed domain contracts now cover intake/query, weather/carrier/caselaw packs, and citation/export memo contracts.
- Audit snapshots now cluster evidence by citation and normalized URL so the export can group related support instead of listing only flat records.
- Memo claims now carry cluster references directly so review and export layers can point to grouped evidence instead of only raw evidence IDs.
- Review events now carry cluster references too, so warnings and citation failures can land on grouped evidence instead of only module-scoped evidence rows.
- Review events and export artifacts now also carry run-scoped linkage fields so memo claims, sections, and exported memo artifacts can be referenced through stable IDs instead of only positional ordering.
- The repo now installs as an editable package and uses shared bootstrap/settings helpers instead of per-file `sys.path` mutation in tests and scripts.
- Runtime environment lanes and artifact boundaries are documented in `docs/FOUNDATION.md`.
- V2 planning was expanded with a deeper rebuild blueprint plus new GitHub issues `#22` through `#27` covering product foundation, UX IA, provenance schema, AI guardrails, human review, and release scorecards.
- A first-pass release rubric now exists in `docs/V2_RELEASE_RUBRIC.md` so release-readiness language is no longer purely roadmap text.
- The offline fixture lane now spans five committed public/redacted scenario directories across Florida, Texas, and Louisiana.
- The curated scenario registry now has five offline-ready fixture-backed benchmarks: Milton/Pinellas/Citizens, Ian/Lee/Citizens, Ida/Orleans/Lloyd's, Texas hail/Tarrant/Allstate HO-B, and Texas hail/Tarrant/Allstate DP-3.
- The fixture-seeding process now lives in `docs/FIXTURE_SEEDING.md`, and scenario tests block marking registry scenarios offline-ready without a fixture key and complete committed fixture bundle.
- CI now includes an explicit offline fixture smoke job, and the local release scorecard records fixture coverage from the committed scenario set.
- The offline fixture lane now also has a deterministic golden snapshot command, `python -m war_room.fixture_snapshots --check`, backed by `tests/golden/offline_fixture_snapshots.json` and quality assertions for source mix, case counts, citation summaries, memo structure, workflow/export posture, and scenario coverage metadata.
- CI gates now emit categorized quality-gate JSON, Markdown, and log artifacts via `python -m war_room.quality_gates`, separating unit, offline fixture, offline e2e, golden snapshot, Exa compatibility, release-scorecard, security-hygiene, and dependency-hygiene failures.
- The security hygiene gate runs offline and checks tracked env files, obvious secret patterns, `.env.example` expectations, runtime artifact commits, and documented secrets policy drift.
- The dependency hygiene gate runs offline and checks exact dependency pins, disallowed editable/local/direct-URL requirements, duplicate/conflicting entries, `requirements.txt` / `pyproject.toml` drift, unsupported dependency files, and documented dependency policy drift.
- The offline e2e gate runs `python -m war_room.offline_e2e --check`, validates the committed fixture workflow through preflight, and writes linked preflight/e2e artifacts under `runs/offline_e2e/`.
- The repository now has a deterministic offline demo preflight command at `python -m war_room --preflight`.
- The repository now also has a one-command local verification wrapper at `python -m war_room --verify`.
- The supported verify flow now emits a linked release-evidence bundle: run-scoped preflight artifacts, run-scoped scorecards with blocking/advisory readiness categories, a top-level `reviewer_summary` convenience summary, verify manifests, a stable `runs/verify/latest.json` pointer, and an integrity test that reloads the linked artifact set.
- The issue `#27` release-evidence reviewer guide now explains how a human should inspect that verify bundle without creating a second readiness model.
- The issue `#92` release-evidence CI reporting summary now maps the existing verify bundle, scorecard artifacts, `reviewer_summary`, and blocking/advisory readiness fields for CI/reporting consumers without changing readiness levels or adding a dashboard.
- The issue `#94` caselaw evidence adapter now maps current case-law output into canonical `EvidenceItem` rows with deterministic provenance-oriented IDs while preserving the current audit snapshot flow.
- The issue `#96` carrier evidence adapter now maps current carrier document output into canonical `EvidenceItem` rows with deterministic provenance-oriented IDs and explicit-vs-inferred source metadata handling.
- The issue `#98` weather evidence adapter now maps current weather source output into canonical `EvidenceItem` rows with deterministic provenance-oriented IDs and explicit-vs-inferred primary-authority handling.
- The issue `#103` / PR `#105` citation-verify evidence adapter now maps current `CitationVerifyPack` output into canonical `EvidenceItem` rows through `citation_verify_pack_to_evidence_items(...)`, replacing positional citation evidence IDs with deterministic provenance-oriented IDs without changing citation verification behavior, status vocabulary, badge semantics, live retrieval, or the `EvidenceItem` schema.
- The issue `#107` / PR `#108` deterministic evidence dedupe helper now provides `dedupe_evidence_items(...)` over canonical `EvidenceItem` rows. It is helper-only, keeps the first retained same-key row unchanged, does not merge candidate summary text, and is not wired into audit snapshot assembly or an `old_id -> retained_id` remapping.
- The notebook and preflight surfaces now expose a workflow-oriented research-plan preview, evidence-board summary, issue-workspace summary, memo-composer summary, export-history summary, and run timeline, so grouped support, issue-level review, section readiness, export posture, and review-required state are visible before the memo is treated as complete.
- The Milton benchmark fixture lane now normalizes cached citation trust metadata, carrier/case-law runtime quality, and markdown/export readability without changing the scenario registry or overall notebook-era runtime flow.
- The Milton rendered-memo path now has an export readability guard that blocks obvious mojibake, scraped navigation text, generic weather pages, Casetext boilerplate, and broken markdown-table rows from reappearing in demo output.
- Runtime cache writes now use a small `v2alpha1` schema-versioned envelope, while cache reads still accept the legacy raw JSON fixture shape already committed in `cache_samples/`.
- The Evidence Board read model now lives behind a typed `v2alpha1` Pydantic contract with a payload adapter, so dict-shaped board data is validated before rendering.
- The Issue Workspace read model now also lives behind a typed `v2alpha1` Pydantic contract with a payload adapter, so issue-level support, citation outcomes, claims, and review events validate before rendering.
- The Memo Composer read model now also lives behind a typed `v2alpha1` Pydantic contract with a payload adapter, so section readiness, claim support links, review events, and export eligibility validate before rendering.
- The Export History read model now also lives behind a typed `v2alpha1` Pydantic contract with a payload adapter, so artifact delivery state, disclaimer state, review-required state, and audit references validate before rendering.
- The Run Timeline read model now has a typed `v2alpha1` envelope over canonical `Run` and `RunStage` records, with payload validation for cross-run stage drift before rendering.
- The first narrow issue `#10` slice now centralizes canonical run states, stage statuses, transition validation, and stage-to-run rollup helpers in `src/war_room/orchestration.py` without changing notebook or preflight behavior.
- The issue `#73` follow-up now adds typed orchestration API request/response contracts for future start-run and get-run-status boundaries without adding HTTP routes, queueing, persistence, auth, retries, circuit breakers, UI, or notebook/runtime changes.
- The first issue `#10` service slice now adds an in-process offline orchestration service that starts typed queued runs, executes committed fixture-backed scenarios with `client=None`, preserves read-model outputs, and returns typed status responses without adding HTTP routes, queueing, persistence, auth, UI, or live retrieval.
- The run-status presentation layer now derives operator-facing status, review reasons, degraded/failed stage summaries, usable-output availability, and next actions from the typed service response without adding UI or transport.
- The thin orchestration transport wrapper now returns JSON-safe dependency-free handler payloads with `ok`, `operation`, typed `payload`, and `status_presentation`; invalid requests and unknown run IDs are transport errors, while accepted offline scenario failures remain `ok=true` typed failed run-status responses.
- The dev-only standard-library HTTP adapter now exposes `GET /healthz`, `POST /runs`, `POST /runs/{run_id}/execute`, and `GET /runs/{run_id}` over the existing transport handlers for local future-app probes while preserving process-local in-memory service state and the transport JSON envelope.
- The first issue `#11` run-status UX/spec slice now explains how a future user-facing status screen should present `operator_status`, headline/message, stage progress, usable outputs, review-required reasons, degraded/failed stages, next actions, and collapsed technical details from the existing status presentation and typed transport payloads without building a frontend app.
- The companion Milton degraded preview in `docs/examples/run_status_milton_degraded.md` shows the top summary copy, stage interpretation, usable outputs, review reasons, next actions, and optional technical details for the existing `milton_pinellas_citizens_ho3` `status_presentation` payload.
- The companion issue `#11` guided-intake UX/spec slice now defines the future intake flow, required vs optional UX fields, validation copy rules, demo/offline scenario behavior, and handoff into run status without adding a frontend or expanding the runtime payload.
- The Milton guided-intake preview in `docs/examples/guided_intake_milton_preview.md` shows deterministic pre-run summary copy, required and optional field treatment, readiness language, review warnings, demo/offline fixture labels, and the handoff from intake to Research Plan Preview and Run Status.
- The notebook Evidence Board now has a styled HTML review surface over the existing typed read model, while the plain text formatter remains available as a fallback.

## 4) Quick run
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e . --no-deps --no-build-isolation
python -m war_room
python -m war_room --preflight
python -m war_room --verify
pytest -q
jupyter notebook notebooks/01_case_war_room.ipynb
```

If you skip editable install for ad hoc local inspection, set `PYTHONPATH=src`. Raw-checkout `pytest -q` is not a supported contributor path.

## 5) Architecture in one line

`CaseIntake -> QueryPlan -> [Weather | Carrier | CaseLaw] -> CitationVerify -> Export`

Core implementation lives in `src/war_room/`.

## 6) Known limitations

- Notebook UX is useful for demos but not ideal for non-technical users.
- Issue `#11` now has run-status and guided-intake UX/spec slices, but the actual product UI remains unbuilt.
- Case law relevance and authority summarization still need stricter filtering/ranking in edge cases.
- Five public/redacted fact patterns are pre-seeded in cache samples, all five are registry-backed for cache-only notebook use, and issue `#8` is closed as completed. Additional Florida fixture seeding is no longer part of `#8` and should be explicitly scoped as follow-up work if maintainers want it.
- Export output quality is materially cleaner than earlier notebook-era baselines, but it is not yet polished for repeated client-facing use across broader fixture coverage.

## 7) Roadmap summary

### Now
- #12 remaining-roadmap review after named adapters and the helper-only deterministic dedupe utility landed; pause implementation before choosing the next provenance-safe integration or hardening child

### Next
- #27 broader CI and pilot operationalization of the release scorecard
- #10 remaining orchestration/API work beyond the landed contracts/service/status/transport/dev-HTTP slices
- #11 future contract seam and UI implementation work beyond the landed guided-intake and run-status UX specs/previews
- #13 caselaw quality v2
- #25 AI guardrails and eval harness
- #26 human review workflow

### Then
- #14 citation verification hardening
- #15 memo workspace v2
- #16 firm memory v1
- #17 observability and cost controls
- #18 security baseline
- #19 attorney pilot validation

## 8) Canonical docs
- [README.md](../README.md): quickstart and current-state summary
- [HANDOFF.md](HANDOFF.md): builder orientation and implemented-vs-planned status
- [FOUNDATION.md](FOUNDATION.md): bootstrap, envs, runtime boundaries, and placeholder repo-shape rules
- [FIXTURE_SEEDING.md](FIXTURE_SEEDING.md): safe process for adding or promoting offline fixture scenarios under the completed `#8` pattern or a future fixture follow-up
- [ISSUE_8_READINESS_AUDIT.md](ISSUE_8_READINESS_AUDIT.md): `#8` readiness/closure audit after the fifth fixture lane and five-lane baseline validation
- [ISSUE_10_DEV_HTTP_WRAPPER.md](ISSUE_10_DEV_HTTP_WRAPPER.md): dev-only standard-library HTTP adapter over the existing orchestration transport layer
- [ISSUE_11_GUIDED_INTAKE_UX_SPEC.md](ISSUE_11_GUIDED_INTAKE_UX_SPEC.md): narrow issue `#11` guided-intake UX/spec slice for the future pre-run intake surface
- [examples/guided_intake_milton_preview.md](examples/guided_intake_milton_preview.md): deterministic issue `#11` Milton guided-intake preview for the future pre-run intake surface
- [ISSUE_11_RUN_STATUS_UX_SPEC.md](ISSUE_11_RUN_STATUS_UX_SPEC.md): narrow issue `#11` run-status UX/spec slice over the existing `status_presentation` payload
- [examples/run_status_milton_degraded.md](examples/run_status_milton_degraded.md): deterministic issue `#11` Milton degraded run-status preview derived from the existing transport/status payload
- [ISSUE_12_REMAINING_SCOPE.md](ISSUE_12_REMAINING_SCOPE.md): docs-only issue `#12` remaining-scope review, now updated after the landed citation-verify adapter and helper-only deterministic dedupe utility
- [ROADMAP.md](ROADMAP.md): plain-language roadmap and active execution order
- [V2_WORKFLOW_IA.md](V2_WORKFLOW_IA.md): canonical V2 workflow, IA, and design-system rules
- [V2_EVIDENCE_SCHEMA.md](V2_EVIDENCE_SCHEMA.md): canonical V2 evidence graph, audit schema, and versioning rules
- [V2_RELEASE_RUBRIC.md](V2_RELEASE_RUBRIC.md): v0.1 quality rubric and release scorecard for `#27`
- [ISSUE_27_RELEASE_EVIDENCE_REVIEW_GUIDE.md](ISSUE_27_RELEASE_EVIDENCE_REVIEW_GUIDE.md): human reviewer guide for reading the `python -m war_room --verify` release-evidence bundle without adding another readiness model
- [V2_ISSUE_MAP.md](V2_ISSUE_MAP.md): issue-by-issue execution map
- [PROJECT_HEALTH_AUDIT_2026-03-10.md](PROJECT_HEALTH_AUDIT_2026-03-10.md): current audit memo, doc drift fixes, and next-2-weeks action plan
- [SESSION_LOG.md](SESSION_LOG.md): build history
- [METHOD.md](METHOD.md): module behavior and methodology
- [SAFETY_GUARDRAILS.md](SAFETY_GUARDRAILS.md): safety boundaries
- [eval/README.md](../eval/README.md): live eval lane rules and intake template
