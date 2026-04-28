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

## 2) Current status (as of April 28, 2026)

| Item | Status |
|---|---|
| Notebook cells 0-7 | Working |
| Offline demo (`USE_CACHE=true`) | Working |
| Tests | 277 passing under the supported verify path after editable install or `PYTHONPATH=src`; raw-checkout `pytest -q` is not a supported path |
| CI | Fresh-env test gate + offline fixture smoke gate + exa-py compatibility matrix + release-scorecard artifact job with artifact validation, all using editable package install |
| Exa compatibility hardening (`#4`) | Complete and closed |
| Intake schema alignment (`#5`) | Complete and closed |
| Typed domain contracts (#6) | Slices 1-7 complete (intake/query + packs + citation/export contracts + graph/version envelopes + issue/authority contracts + run/retrieval lifecycle contracts + review/export graph-linkage contracts) |
| Retrieval contracts (#7) | Four slices landed: provider seam, notebook retrieval-state emission, citation-verify retrieval tracking, and deterministic retrieval-task timing |
| Product foundation (`#22`) | Complete and closed: packaging/bootstrap lane implemented |
| Workflow IA spec (`#23`) | Complete and closed as the written source of truth in `docs/V2_WORKFLOW_IA.md` |
| Evidence schema spec (`#24`) | Complete and closed as the written source of truth in `docs/V2_EVIDENCE_SCHEMA.md` |
| Quality rubric (`#27`) | First-pass rubric plus local and CI artifact workflows landed in `docs/V2_RELEASE_RUBRIC.md`; demo-ready threshold calibration, live preflight evidence, run-scoped verify artifacts, verify manifests, and a stable latest pointer are now explicit, while broader CI and pilot operationalization remain open |
| Cache samples | Milton/Citizens/Pinellas + TX hail/Allstate/Tarrant + TX hail matching/Allstate Texas Lloyds/Tarrant DP-3 + Ida/Lloyd's/Orleans committed |

## 3) What changed recently

- Exa client now supports both older and newer `exa-py` contents APIs.
- Dependency versions are pinned for reproducible installs.
- CI now blocks merges if fresh-env tests fail.
- CI also runs an `exa-py` compatibility matrix (`exa-py==2.0.2` and `exa-py<2`).
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
- The offline fixture lane now spans four committed public/redacted scenario directories across Florida, Texas, and Louisiana.
- CI now includes an explicit offline fixture smoke job, and the local release scorecard records fixture coverage from the committed scenario set.
- The repository now has a deterministic offline demo preflight command at `python -m war_room --preflight`.
- The repository now also has a one-command local verification wrapper at `python -m war_room --verify`.
- The supported verify flow now emits a linked release-evidence bundle: run-scoped preflight artifacts, run-scoped scorecards, verify manifests, a stable `runs/verify/latest.json` pointer, and an integrity test that reloads the linked artifact set.
- The notebook and preflight surfaces now expose a workflow-oriented research-plan preview, evidence-board summary, issue-workspace summary, memo-composer summary, export-history summary, and run timeline, so grouped support, issue-level review, section readiness, export posture, and review-required state are visible before the memo is treated as complete.
- The Milton benchmark fixture lane now normalizes cached citation trust metadata, carrier/case-law runtime quality, and markdown/export readability without changing the scenario registry or overall notebook-era runtime flow.

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
- Case law relevance and authority summarization still need stricter filtering/ranking in edge cases.
- Four public/redacted fact patterns are pre-seeded in cache samples, but broader scenario coverage and thresholds are still needed.
- Export output quality is materially cleaner than earlier notebook-era baselines, but it is not yet polished for repeated client-facing use across broader fixture coverage.

## 7) Roadmap summary

### Now
- #27 broader CI and pilot operationalization of the release scorecard
- #6 typed domain contracts
- #7 retrieval provider abstraction and contracts (provider seam, notebook retrieval-state, and citation-verify slices landed)
- #8 multi-jurisdiction fixtures and snapshots
- #9 expanded CI quality gates

### Next
- #10 API orchestrator
- #11 guided web intake and run-status UX
- #12 evidence normalization and provenance
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
- [ROADMAP.md](ROADMAP.md): plain-language roadmap and active execution order
- [V2_WORKFLOW_IA.md](V2_WORKFLOW_IA.md): canonical V2 workflow, IA, and design-system rules
- [V2_EVIDENCE_SCHEMA.md](V2_EVIDENCE_SCHEMA.md): canonical V2 evidence graph, audit schema, and versioning rules
- [V2_RELEASE_RUBRIC.md](V2_RELEASE_RUBRIC.md): v0.1 quality rubric and release scorecard for `#27`
- [V2_ISSUE_MAP.md](V2_ISSUE_MAP.md): issue-by-issue execution map
- [PROJECT_HEALTH_AUDIT_2026-03-10.md](PROJECT_HEALTH_AUDIT_2026-03-10.md): current audit memo, doc drift fixes, and next-2-weeks action plan
- [SESSION_LOG.md](SESSION_LOG.md): build history
- [METHOD.md](METHOD.md): module behavior and methodology
- [SAFETY_GUARDRAILS.md](SAFETY_GUARDRAILS.md): safety boundaries
- [eval/README.md](../eval/README.md): live eval lane rules and intake template
