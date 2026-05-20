# CAT-Loss War Room - Claude Code Project Conventions

## Primary objective
Attorney-grade demo readiness and approachability. Every change should make the demo more reliable, the code more understandable, and the documentation more useful for both agents and non-technical professionals.

## What this project is
A Jupyter-notebook-based "war room" tool for catastrophic insurance loss litigation.
It uses Exa search to gather weather data, carrier playbook intel, and case law,
then exports a structured research memo. Built for demo at Merlin Law Group.

**Start here for full orientation:** [`docs/HANDOFF.md`](docs/HANDOFF.md)

## Non-goals
- No big refactors. Keep changes small and reviewable.
- No SaaS build. This is a demo prototype, not a production service.
- No new dependencies without explicit approval.
- No ML-based scoring or classification. Deterministic domain dicts only.

## Quick setup
```bash
python -m venv .venv
source .venv/bin/activate        # Linux/Mac
# source .venv/Scripts/activate  # Windows Git Bash
pip install -r requirements.txt
pip install -e . --no-deps --no-build-isolation
python -m war_room
pytest -q
```

## Repo layout
```
src/war_room/       # All Python logic lives here
  exa_client.py     # Exa search wrapper (retry, budget guard)
  cache_io.py       # Cache-first data access (cache_samples -> cache -> live)
  source_scoring.py # Deterministic URL credibility scoring
  models.py         # Pydantic typed domain models and adapter helpers
  query_plan.py     # CaseIntake + QuerySpec + generate_query_plan()
  weather_module.py # Weather data gathering (gov-first)
  carrier_module.py # Carrier playbook intel + rebuttal angles
  caselaw_module.py # Case law search (issue-organized, case-like filter)
  citation_verify.py# Citation spot-check (best-tier, MAX_CHECKS cap)
  export_md.py      # Markdown export with watermarks
notebooks/          # Jupyter notebooks (the demo surface)
cache_samples/      # Committed demo fixtures (run without API key)
cache/              # Runtime cache (gitignored)
output/             # Generated reports (gitignored)
tests/              # pytest test suite (455 tests, no network)
scripts/            # Seed scripts (manual, not CI)
docs/               # Project documentation
apps/               # V2 app placeholders (web/api)
workers/            # V2 worker placeholders
packages/           # V2 shared-package placeholders
```

## Workflow rules
- **Small diffs.** One concern per commit. Keep changes reviewable.
- **Run `pytest -q` before committing.** All tests must pass.
- **Keep notebooks thin.** Business logic goes in `src/war_room/`, notebooks just call it.
- **Cache-first.** Every external call goes through `cached_call()`. Demo must work offline.
- **No secrets in code.** `.env` is gitignored. Use `.env.example` for the template.
- **Source scoring is deterministic.** Hardcoded domain dicts, not ML.
- **Always include disclaimers.** Every output must say "DEMO RESEARCH MEMO / NOT LEGAL ADVICE / VERIFY ALL CITATIONS."
- **Log your work.** Add a session entry to `docs/SESSION_LOG.md` after each build session.

## How to decide what to change
Prioritize in this order:
1. **Partner trust** - Does this make the demo more credible to an attorney?
2. **Usability** - Does this make the tool easier to run and understand?
3. **Reliability** - Does this reduce the chance of demo failure?
4. **Extensibility** - Does this make future work easier? (lowest priority)

## Boundaries - what Claude Code should NOT do
- Never commit `.env` or any file containing API keys
- Never make live Exa API calls in tests (use mocks/cache)
- Never claim outputs are verified legal advice
- Never remove safety disclaimers from notebooks or exports
- Never install packages not in requirements.txt without asking

## Branch naming
- `chore/` - repo setup, docs, config
- `feat/` - new functionality
- `fix/` - bug fixes

## Current phase
v0-demo shipped, issues #22, #23, #24, #6, #7, #8, and #9 are complete and closed. The issue #10 stack now includes canonical run/stage state, typed API contracts, an in-process offline service, operator-facing status presentation, a dependency-free thin transport wrapper, and a dev-only standard-library HTTP adapter, without a production API framework or real web app. Issue #11 is currently specs and previews only, not a shipped UI. Issue #27 now includes the release-evidence reviewer guide, issue #88 `reviewer_summary`, and issue #92 `ci_reporting_summary` scorecard convenience layers, while broader CI/pilot operationalization remains open. Issue #103 / PR #105 landed the citation-verify adapter, so issue #12 now has named adapter seams for current weather, carrier, caselaw, and citation-verification output; the full V2 evidence graph, dedupe, persistence, API integration, dashboard, review workflow, and product runtime remain future work. Cells 0-7 remain stable and CI runs package-installed tests.

## Next session focus
See [`docs/HANDOFF.md`](docs/HANDOFF.md) for full orientation and status.
Execution roadmap lives in [`docs/ROADMAP.md`](docs/ROADMAP.md) and [`docs/V2_ISSUE_MAP.md`](docs/V2_ISSUE_MAP.md).
Next priority: review the remaining #12 follow-ups after all current evidence-producing source families have named adapters, then decide whether the next narrow child should be a deterministic dedupe helper, provenance link hardening, citation-quality fixture regression under #13/#14, or a docs-only issue-12 closeout/status map. Broader #27 scorecard/rubric operationalization and explicitly scoped #10/#11 follow-ups remain available after that. Issues #64 and #65 are closed hygiene follow-ups.
