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
python -m war_room.fixture_snapshots --check
python -m war_room.quality_gates run --gate golden-snapshot-check -- python -m war_room.fixture_snapshots --check
python -m war_room.quality_gates run --gate security-hygiene-check -- python -m war_room.security_hygiene --check
python -m war_room.quality_gates run --gate dependency-hygiene-check -- python -m war_room.dependency_hygiene --check
python -m war_room.quality_gates run --gate e2e-offline-demo -- python -m war_room.offline_e2e --check
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
python -m war_room.fixture_snapshots --check
python -m war_room.quality_gates run --gate golden-snapshot-check -- python -m war_room.fixture_snapshots --check
python -m war_room.quality_gates run --gate security-hygiene-check -- python -m war_room.security_hygiene --check
python -m war_room.quality_gates run --gate dependency-hygiene-check -- python -m war_room.dependency_hygiene --check
python -m war_room.quality_gates run --gate e2e-offline-demo -- python -m war_room.offline_e2e --check
pytest -q
jupyter notebook notebooks/01_case_war_room.ipynb
```

`EXA_API_KEY` is optional for the offline demo path because committed fixtures in `cache_samples/` let the notebook run from cache.

`python -m war_room --verify` runs the supported local verification path: offline demo preflight plus `pytest -q`.

`python -m war_room.fixture_snapshots --check` compares committed offline fixture coverage and output-structure metrics against the golden snapshot in `tests/golden/offline_fixture_snapshots.json`.

`python -m war_room.quality_gates run ...` wraps an existing check with categorized logs, JSON, and Markdown artifacts under `runs/quality_gates/`; CI uses it to distinguish unit, offline fixture, offline e2e, golden snapshot, Exa compatibility, release-scorecard, security-hygiene, and dependency-hygiene failures.

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
2. **Research Plan Preview** - Shows planned modules, issue hypotheses, preferred domains, and query scope before execution
3. **Weather Intel** - Gathers official weather data (.gov sources preferred)
4. **Carrier Playbook** - Finds carrier denial patterns, regulatory actions, rebuttal angles
5. **Case Law** - Searches relevant precedent organized by legal issue
6. **Evidence Board** - Groups support by evidence cluster with review-required markers and claim usage
7. **Issue Workspace** - Summarizes issue-level support, strongest authorities, citation state, and open review items
8. **Memo Composer** - Shows ordered sections, claim support links, review-required state, and export readiness
9. **Export History** - Captures export artifact state, disclaimer presence, delivery status, and audit linkage
10. **Run Timeline** - Surfaces stage-by-stage status plus explicit review-required states before reliance
11. **Export** - Produces a structured research memo with source confidence badges

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
- The additional registry-backed offline benchmark is `ida_orleans_lloyds_ho3`, which maps to the committed Ida/Lloyd's/Orleans fixtures.
- The other curated live-only Florida hurricane benchmarks are:
  - `ian_lee_citizens_ho3`
  - `irma_monroe_citizens_ho3`
  - `michael_bay_default_ho3`
  - `idalia_taylor_default_ho3`
- To switch scenarios, change `SCENARIO_ID` in `notebooks/01_case_war_room.ipynb`.
- Use `SCENARIO_OVERRIDES` in the notebook for one-off local intake tweaks without editing the canonical scenario files.

Milton and Ida now map from the curated notebook scenario registry to committed offline cache fixtures. The broader offline preflight lane also covers two eval-intake Texas fixture scenarios; cache-only notebook demos should use one of the offline-ready registry scenarios unless live retrieval is enabled.

## Current Status

**Implemented now:** The notebook-first V0 demo is stable, the offline cache-backed lane works across four committed scenario directories spanning Florida, Texas, and Louisiana, two of those fixture lanes now have curated offline-ready registry entries, the notebook and preflight path now expose a research-plan preview, styled evidence-board review view, issue-workspace summary, memo-composer summary, export-history summary, and run-timeline summary on top of the canonical contracts, `334` tests are passing under the supported bootstrap path, the supported `--verify` flow now writes a linked run-scoped release-evidence bundle, and CI now enforces:
- Fresh environment install + full test run with categorized unit-test gate artifacts
- Editable package bootstrap validation
- Offline fixture smoke validation plus the committed golden fixture snapshot check across committed scenarios, with separate offline-fixture and golden-snapshot gate artifacts
- `exa-py` compatibility matrix (`exa-py==2.0.2` and `exa-py<2`) with categorized compatibility artifacts
- Release-scorecard artifact emission plus ship-threshold validation from the calibrated `#27` workflow, with separate generation and validation gate artifacts
- Offline security hygiene validation for committed env files, obvious API key patterns, `.env.example` expectations, runtime artifact commits, and documented secrets policy drift, with categorized security artifacts
- Offline dependency hygiene validation for pinned requirements, disallowed editable/local/direct-URL dependencies, duplicate/conflicting entries, `requirements.txt` / `pyproject.toml` drift, unsupported dependency files, and documented dependency policy drift
- Offline e2e validation that runs the committed fixture demo workflow through preflight and verifies linked preflight/e2e artifacts, workflow state, memo/review surface counts, and export posture

**Specified, not built yet:** `docs/V2_WORKFLOW_IA.md`, `docs/V2_EVIDENCE_SCHEMA.md`, and `docs/V2_RELEASE_RUBRIC.md` are the written source-of-truth specs for the current V2 planning layer, while `apps/`, `workers/`, and `packages/` remain placeholder boundaries for later implementation.

Issues `#4`, `#5`, `#22`, `#23`, and `#24` are complete and closed. The written source-of-truth specs for `#23` and `#24` live in `docs/V2_WORKFLOW_IA.md` and `docs/V2_EVIDENCE_SCHEMA.md`, while downstream implementation remains tracked in later issues. Issue `#27` now has a calibrated demo-ready scorecard, CI artifact emission plus validation, and a linked local verify-evidence workflow in `docs/V2_RELEASE_RUBRIC.md`, and remains open for broader CI/pilot operationalization. Issue `#6` is complete with a closeout audit in `docs/ISSUE_6_CLOSEOUT_AUDIT.md`, including schema-versioned runtime cache envelopes with legacy raw-cache loading plus typed Run Timeline, Evidence Board, Issue Workspace, Memo Composer, and Export History read-model contracts. Issue `#7` is complete after the provider seam, notebook retrieval-state emission, citation-verify retrieval tracking, deterministic retrieval-task timing, retrieval provider failure-mode normalization, and `None` provider-response malformed-contract follow-up landed; the follow-up resolves the gap documented in `docs/ISSUE_7_CLOSURE_SANITY_AUDIT.md`. Issue `#8` now has its first deterministic golden snapshot gate for committed offline scenarios plus a second curated offline-ready registry-backed benchmark for the existing Ida/Lloyd's/Orleans fixture lane, with broader fixture breadth still open. Issue `#9` is complete with a closeout audit in `docs/ISSUE_9_CLOSEOUT_AUDIT.md`; the landed gates cover categorized CI artifacts, offline fixture and golden snapshot checks, offline security and dependency hygiene checks, release-scorecard validation, Exa compatibility diagnostics, and an offline e2e demo gate. Broader beta/pilot hardening remains downstream roadmap work.

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
