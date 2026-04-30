# Heartbeat

- Repo: `cat-loss-war-room`
- Current milestone: Stabilize the notebook demo while finishing `#27` and the remaining `#6` to `#9` foundation work.
- Current status: V0 demo is stable; active runtime is still `src/war_room/` plus `notebooks/01_case_war_room.ipynb`; the `#27` local release-evidence stack is now merged, and the notebook Evidence Board now has a styled HTML review surface over the typed read model.
- Current branch: `codex/issue-6-final-contract-docs`
- Last validated: 2026-04-30 via `$env:PYTHONPATH='src'; python -m war_room --verify --release-candidate evidence-board-html-ui` (`294 passed`; offline preflight passed for 4 fixture scenarios)
- Current focus: Notebook UI/UX polish on the stable V0 demo surface: Evidence Board HTML is complete; the next logical polish is Issue Workspace or Run Timeline HTML using the same typed-read-model approach.
- Hot files: `notebooks/01_case_war_room.ipynb`, `src/war_room/evidence_board.py`, `src/war_room/__init__.py`, `tests/test_evidence_board.py`, `docs/heartbeat.md`, `docs/SESSION_LOG.md`
- Blockers: No hard blocker is documented in-repo; main risks are uneven fixture coverage, notebook-first operator UX, and the current venv not being editable-installed by default.
- Do not touch this sprint: repo rename, broad product rewrites, placeholder V2 directories as if they were live runtime, dependency churn without approval.
- Related repos: None documented in-repo; treat this repo as the working source of truth.
- Latest session log: `logs/2026-04-28-session.md` plus `docs/SESSION_LOG.md`
- Next best task: Extend the same no-new-dependency HTML treatment to Issue Workspace or Run Timeline, then return to `#9` quality-gate expansion or `#8` fixture breadth.
- Owner: Not explicitly named in-repo; maintained for the Merlin Law Group demo effort.
