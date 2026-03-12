# CAT-Loss War Room

AI-powered catastrophic insurance loss litigation research tool.
Built for demo at Merlin Law Group.

> **DEMO RESEARCH MEMO - NOT LEGAL ADVICE**
> All outputs are for demonstration purposes only. Verify all citations
> independently before any legal reliance. See [SAFETY_GUARDRAILS.md](docs/SAFETY_GUARDRAILS.md).

## Quickstart

```bash
# Clone and setup
git clone <repo-url>
cd cat-loss-war-room-demo
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e . --no-deps --no-build-isolation

# Copy env template
cp .env.example .env
# Edit .env to add your EXA_API_KEY (optional - demo runs from cache)

# Run tests
python -m war_room
pytest -q

# Open the notebook
jupyter notebook notebooks/01_case_war_room.ipynb
```

`pytest -q` assumes the editable install step above has already run. If you skip package install for ad hoc local inspection, use `PYTHONPATH=src` instead of a raw-checkout test run.

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

## Current Status

**Implemented now:** The notebook-first V0 demo is stable, the offline cache-backed lane works across three committed scenarios (FL, TX, LA), `178` tests are passing under the supported bootstrap path, and CI now enforces:
- Fresh environment install + full test run
- Editable package bootstrap validation
- Offline fixture smoke validation across committed scenarios
- `exa-py` compatibility matrix (`exa-py==2.0.2` and `exa-py<2`)

**Specified, not built yet:** `docs/V2_WORKFLOW_IA.md`, `docs/V2_EVIDENCE_SCHEMA.md`, and `docs/V2_RELEASE_RUBRIC.md` are the written source-of-truth specs for the current V2 planning layer, while `apps/`, `workers/`, and `packages/` remain placeholder boundaries for later implementation.

Issues `#4`, `#5`, `#22`, `#23`, and `#24` are complete in their current intended scope. Issue `#27` now has a first-pass release rubric in `docs/V2_RELEASE_RUBRIC.md` but remains open for calibration, issue `#6` is underway with slices 1-6 landed, and issue `#7` has three slices landed: the provider seam, notebook retrieval-state emission, and citation-verify retrieval tracking.

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
