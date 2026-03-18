# V2 Foundation

Last updated: March 11, 2026

This document is the concrete output of issue `#22`.

## Current foundation decisions

- Packaging: the repo is installable as an editable package via `pip install -e . --no-deps --no-build-isolation`.
- Runtime bootstrap: scripts, tests, and notebooks load configuration through `war_room.bootstrap` and `war_room.settings`.
- Test/bootstrap contract: contributors should run tests after editable install, or use `PYTHONPATH=src` for ad hoc local runs. Raw-checkout `pytest -q` is not a supported path.
- Environment lanes:
  - `local`: default contributor environment.
  - `demo`: cache-first offline lane. Live retrieval is disabled.
  - `staging`: production-like verification lane.
  - `production`: reserved for future product deployment assumptions.
- Artifact boundaries:
  - `cache/`: runtime cache.
  - `cache_samples/`: committed offline fixtures.
  - `output/`: rendered memo exports.
  - `runs/`: run-level artifacts and future audit snapshots.
- Current active runtime surfaces:
  - `src/war_room/`: Python package and current implementation
  - `notebooks/01_case_war_room.ipynb`: demo/diagnostic surface
  - `python -m war_room`: bootstrap check and runtime summary
  - `python -m war_room --verify`: supported local verification path

## Local bootstrap

From repo root:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e . --no-deps --no-build-isolation
python -m war_room
python -m war_room --verify
pytest -q
```

On Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -e . --no-deps --no-build-isolation
python -m war_room
python -m war_room --verify
pytest -q
```

`python -m war_room` is the bootstrap check. It resolves the repo root, loads `.env`, creates runtime directories when needed, and prints the active runtime summary.

`python -m war_room --verify` is the supported contributor verification wrapper. It runs the deterministic offline preflight and then the supported test command (`pytest -q`).

## Notebook and script conventions

- Notebooks and scripts must import `war_room.bootstrap.bootstrap_runtime` instead of mutating `sys.path`.
- The notebook remains a demo/diagnostic surface, not the primary product runtime.
- The offline fixture lane stays first-class through `WAR_ROOM_ENV=demo` plus committed `cache_samples/`.
- The committed fixture lane now includes three public/redacted scenario directories spanning Florida, Texas, and Louisiana, plus a fourth Texas matching-dispute runtime fixture.

## Planned V2 repo shape

The future runtime boundaries remain:

```text
apps/
  web/
  api/
workers/
  research/
packages/
  domain/
  retrieval/
  pipeline/
  export/
  evals/
```

For the current build, this remains a documented target rather than a code move. The implemented foundation work in this issue is the packaging/bootstrap layer that makes that transition clean.

The top-level `apps/`, `workers/`, and `packages/` directories currently contain README placeholders only. They document future boundaries and should not be read as active runtime entrypoints.

## Deployment lanes

- `local`: contributor bootstrap, editable install, notebook/script/test workflows.
- `demo`: offline fixture lane used for demos and smoke verification.
- `staging`: future integrated validation lane for API/UI/runtime checks.
- `production`: future attorney-facing deployment lane with stricter secrets, retention, and audit controls.
