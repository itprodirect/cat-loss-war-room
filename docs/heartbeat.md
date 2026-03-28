# Heartbeat

- Repo: `cat-loss-war-room`
- Current milestone: Stabilize the notebook demo while finishing `#27` and the remaining `#6` to `#9` foundation work.
- Current status: V0 demo is stable; active runtime is still `src/war_room/` plus `notebooks/01_case_war_room.ipynb`; this session adds the memory stack only.
- Current branch: `codex/foundation-focus-slices`
- Last validated: 2026-03-27 via `$env:PYTHONPATH='src'; .venv\Scripts\python.exe -m war_room --verify` (`252 passed`; offline preflight passed for 4 fixture scenarios)
- Current focus: Keep docs and execution memory aligned without broadening scope beyond the current foundation tranche.
- Hot files: `notebooks/01_case_war_room.ipynb`, `src/war_room/preflight.py`, `src/war_room/models.py`, `src/war_room/workflow_summary.py`, `src/war_room/evidence_board.py`, `src/war_room/issue_workspace.py`, `src/war_room/memo_composer.py`, `src/war_room/export_history.py`, `docs/V2_RELEASE_RUBRIC.md`
- Blockers: No hard blocker is documented in-repo; main risks are uneven fixture coverage, notebook-first operator UX, and the current venv not being editable-installed by default.
- Do not touch this sprint: repo rename, broad product rewrites, placeholder V2 directories as if they were live runtime, dependency churn without approval.
- Related repos: None documented in-repo; treat this repo as the working source of truth.
- Latest session log: `logs/2026-03-27-session.md`
- Next best task: Continue `#27` release-scorecard operationalization, then tighten the remaining `#6` to `#9` foundation slices.
- Owner: Not explicitly named in-repo; maintained for the Merlin Law Group demo effort.
