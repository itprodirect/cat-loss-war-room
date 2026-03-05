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

## 2) Current status (as of March 5, 2026)

| Item | Status |
|---|---|
| Notebook cells 0-7 | Working |
| Offline demo (`USE_CACHE=true`) | Working |
| Tests | 109 passing, no network calls in tests |
| CI | Fresh-env test gate + exa-py compatibility matrix |
| Exa compatibility hardening (`#4`) | Complete and closed |
| Intake schema alignment (`#5`) | Implemented and committed |
| Typed domain contracts (`#6`) | Slices 1-3 complete (intake/query + packs + citation/export contracts) |
| Cache samples | Milton/Citizens/Pinellas committed |

## 3) What changed recently

- Exa client now supports both older and newer `exa-py` contents APIs.
- Dependency versions are pinned for reproducible installs.
- CI now blocks merges if fresh-env tests fail.
- CI also runs an `exa-py` compatibility matrix (`exa-py==2.0.2` and `exa-py<2`).
- Adapter smoke tests were added for kwargs forwarding contracts.
- Intake JSON now has strict schema validation and file-loading helpers.
- Typed domain contracts now cover intake/query, weather/carrier/caselaw packs, and citation/export memo contracts.

## 4) Quick run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest -q
jupyter notebook notebooks/01_case_war_room.ipynb
```

## 5) Architecture in one line

`CaseIntake -> QueryPlan -> [Weather | Carrier | CaseLaw] -> CitationVerify -> Export`

Core implementation lives in `src/war_room/`.

## 6) Known limitations

- Notebook UX is useful for demos but not ideal for non-technical users.
- Case law relevance still needs stricter filtering/ranking in edge cases.
- Only one fact pattern is pre-seeded in cache samples.
- Export output quality is serviceable, but not yet polished for repeated client-facing use.

## 7) Roadmap summary

### Now
- #6 typed domain contracts
- #7 retrieval provider abstraction and contracts
- #8 multi-jurisdiction fixtures and snapshots
- #9 expanded CI quality gates

### Next
- #10 API orchestrator
- #11 guided web intake and run-status UX
- #12 evidence normalization and provenance
- #13 caselaw quality v2

### Then
- #14 citation verification hardening
- #15 memo workspace v2
- #16 firm memory v1
- #17 observability and cost controls
- #18 security baseline
- #19 attorney pilot validation

## 8) Canonical docs

- [README.md](../README.md): quickstart and status
- [ROADMAP.md](ROADMAP.md): plain-language roadmap
- [V2_ISSUE_MAP.md](V2_ISSUE_MAP.md): issue-by-issue execution map
- [SESSION_LOG.md](SESSION_LOG.md): build history
- [METHOD.md](METHOD.md): module behavior and methodology
- [SAFETY_GUARDRAILS.md](SAFETY_GUARDRAILS.md): safety boundaries
- [eval/README.md](../eval/README.md): live eval lane rules and intake template
