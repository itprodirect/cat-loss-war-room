# CAT-Loss War Room

AI-powered catastrophic insurance loss litigation research tool.
Built for demo at Merlin Law Group.

> **DEMO RESEARCH MEMO - NOT LEGAL ADVICE**
> All outputs are for demonstration purposes only. Verify all citations
> independently before any legal reliance. See [SAFETY_GUARDRAILS.md](docs/SAFETY_GUARDRAILS.md).

## Supported Local Paths

Use one of these supported local setups from repo root.

### Windows PowerShell

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -e . --no-deps --no-build-isolation
Copy-Item .env.example .env
python -m war_room
python -m war_room --preflight
python -m war_room --verify
pytest -q
jupyter notebook notebooks/01_case_war_room.ipynb
```

### macOS / Linux / Git Bash

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e . --no-deps --no-build-isolation
cp .env.example .env
python -m war_room
python -m war_room --preflight
python -m war_room --verify
pytest -q
jupyter notebook notebooks/01_case_war_room.ipynb
```

`EXA_API_KEY` is optional for the offline demo path because committed fixtures in `cache_samples/` let the notebook run from cache.

`python -m war_room --verify` runs the supported local verification path: offline demo preflight plus `pytest -q`.

`pytest -q` is still the underlying supported test command after editable install. If you skip package install for ad hoc local inspection, use `PYTHONPATH=src` instead of a raw-checkout test run.

## Dependency Compatibility

This repo currently pins a tested dependency set in `requirements.txt`
for reproducible behavior, including `exa-py==2.0.2`.

`src/war_room/exa_client.py` also includes a version-safe `contents`
payload builder so Exa calls keep working across older/newer `exa-py`
APIs.

## What it does

Given a catastrophic loss case (hurricane, hail, etc.), the war room notebook:

1. **Intake** - Captures case facts (location, date, carrier, policy type, posture)
2. **Query Plan** - Generates 12-18 targeted research queries across three modules
3. **Weather Intel** - Gathers official weather data (.gov sources preferred)
4. **Carrier Playbook** - Finds carrier denial patterns, regulatory actions, rebuttal angles
5. **Case Law** - Searches relevant precedent organized by legal issue
6. **Export** - Produces a structured research memo with source confidence badges

## Jupyter Kernel (required)

The notebook must run against the project venv. Register it once:

```bash
source .venv/bin/activate
pip install -e . --no-deps --no-build-isolation
python -m pip install ipykernel
python -m ipykernel install --user --name cat-loss-war-room-demo --display-name "cat-loss-war-room-demo (.venv)"
```

Then in JupyterLab select **Kernel -> Change Kernel -> cat-loss-war-room-demo (.venv)**.

## Offline Demo

No API key needed - cached results are committed in `cache_samples/`.

```bash
# Ensure USE_CACHE=true in .env (the default)
source .venv/bin/activate
jupyter notebook notebooks/01_case_war_room.ipynb
# Run All - should complete in < 10 seconds
```

## Benchmark Scenarios

The curated benchmark scenario registry now lives under [`scenarios/`](scenarios).

- The notebook reads a shared `SCENARIO_ID` instead of a hard-coded intake object.
- The default notebook scenario is `milton_pinellas_citizens_ho3`, which maps to the committed offline Milton fixtures.
- The other curated Florida hurricane benchmarks are:
  - `ian_lee_citizens_ho3`
  - `irma_monroe_citizens_ho3`
  - `michael_bay_default_ho3`
  - `idalia_taylor_default_ho3`
- To switch scenarios, change `SCENARIO_ID` in `notebooks/01_case_war_room.ipynb`.
- Use `SCENARIO_OVERRIDES` in the notebook for one-off local intake tweaks without editing the canonical scenario files.

Only the Milton benchmark currently has committed offline cache fixtures, so cache-only demos should stay on the default scenario unless live retrieval is enabled.

## Current Status

**Implemented now:** The notebook-first V0 demo is stable, the offline cache-backed lane works across four committed scenario directories spanning Florida, Texas, and Louisiana, `236` tests are passing under the supported bootstrap path, and CI now enforces:
- Fresh environment install + full test run
- Editable package bootstrap validation
- Offline fixture smoke validation across committed scenarios
- `exa-py` compatibility matrix (`exa-py==2.0.2` and `exa-py<2`)
- Release-scorecard artifact emission plus ship-threshold validation from the calibrated `#27` workflow

**Specified, not built yet:** `docs/V2_WORKFLOW_IA.md`, `docs/V2_EVIDENCE_SCHEMA.md`, and `docs/V2_RELEASE_RUBRIC.md` are the written source-of-truth specs for the current V2 planning layer, while `apps/`, `workers/`, and `packages/` remain placeholder boundaries for later implementation.

Issues `#4`, `#5`, `#22`, `#23`, and `#24` are complete and closed. The written source-of-truth specs for `#23` and `#24` live in `docs/V2_WORKFLOW_IA.md` and `docs/V2_EVIDENCE_SCHEMA.md`, while downstream implementation remains tracked in later issues. Issue `#27` now has a calibrated demo-ready scorecard in `docs/V2_RELEASE_RUBRIC.md` and remains open for CI and pilot operationalization, issue `#6` is underway with slices 1-7 landed, and issue `#7` has four slices landed: the provider seam, notebook retrieval-state emission, citation-verify retrieval tracking, and deterministic retrieval-task timing.

## Roadmap (Simple)

- Read the plain-language roadmap: [docs/ROADMAP.md](docs/ROADMAP.md)
- See issue-by-issue mapping: [docs/V2_ISSUE_MAP.md](docs/V2_ISSUE_MAP.md)
- See the current bootstrap and environment rules: [docs/FOUNDATION.md](docs/FOUNDATION.md)

## Live Eval Lane

For public/redacted scenario validation:

- Intake rules and schema: [eval/README.md](eval/README.md)
- Starter intake template: [eval/intakes/_template_case_intake.json](eval/intakes/_template_case_intake.json)

## Project Structure

See [CLAUDE.md](CLAUDE.md) for full repo layout and conventions.

## Disclaimer

This tool is a research accelerator, not a legal oracle. All outputs carry:
- Source confidence badges (`official` / `professional` / `unvetted`)
- Mandatory "VERIFY ALL CITATIONS" disclaimers
- "DRAFT - ATTORNEY WORK PRODUCT" watermarks on exports

No output should be used without independent verification by a licensed attorney.
