# AGENTS.md

## Repo purpose

CAT-Loss War Room is a notebook-first litigation research demo for catastrophic insurance loss matters. It takes a case intake, gathers weather corroboration, carrier intelligence, and issue-organized case law, runs citation spot-checks, and exports a structured memo.

This repo exists to support demo-ready legal research acceleration for Merlin Law Group. It is not legal advice, and outputs must keep the repo's disclaimer and verification posture intact.

## Read first

1. [`CLAUDE.md`](./CLAUDE.md) for repo conventions, setup, and hard boundaries.
2. [`docs/HANDOFF.md`](./docs/HANDOFF.md) for current implemented-vs-planned status.
3. [`docs/repo-brief.md`](./docs/repo-brief.md) for the short operating brief.
4. [`docs/heartbeat.md`](./docs/heartbeat.md) for the current branch, focus, and next best task.
5. [`logs/2026-03-27-session.md`](./logs/2026-03-27-session.md) for the latest memory-stack session note.

## Current milestone

Keep the V0 notebook demo stable while operationalizing issue `#27` and completing the remaining `#6` to `#9` foundation slices. The active runtime is still the notebook plus `src/war_room/`; `apps/`, `workers/`, and `packages/` remain future-boundary placeholders.

## Non-goals

- Do not rename the repo.
- Do not broaden scope into architecture or product rewrites.
- Do not treat placeholder V2 directories as active runtime surfaces.
- Do not add dependencies without explicit approval.
- Do not replace deterministic source scoring with ML scoring.
- Do not remove legal/demo disclaimers or present output as legal advice.

## Validation expectations

- Check branch and worktree first with `git status --short --branch`.
- Prefer the supported repo verification path: editable install plus `python -m war_room --verify`.
- `pytest -q` is supported after editable install; for ad hoc local inspection without install, use `PYTHONPATH=src`.
- For narrow doc-only changes, still run the smallest grounded validation the repo already supports and document exactly what ran.
- Inspect changed files before closing the task and confirm docs cross-link cleanly.

## Required output format for agent work

Every substantive agent close-out should use this order:

1. Summary
2. Changed files
3. Validation
4. Any decisions added or not added
5. Unresolved issues
6. Recommended next task
