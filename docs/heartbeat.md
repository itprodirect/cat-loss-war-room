# Heartbeat

- Repo: `cat-loss-war-room`
- Current milestone: Stabilize the notebook demo while finishing `#27` and the remaining `#6` to `#9` foundation work.
- Current status: V0 demo is stable; active runtime is still `src/war_room/` plus `notebooks/01_case_war_room.ipynb`; the `#27` local release-evidence stack is now merged, including live preflight-backed scorecards, run-scoped verify artifacts, verify manifests, and a stable latest pointer.
- Current branch: `codex/export-readability-guard`
- Last validated: 2026-04-28 local / 2026-04-29 UTC via `$env:PYTHONPATH='src'; python -m war_room --verify --release-candidate export-readability-guard` (`279 passed`; offline preflight passed for 4 fixture scenarios)
- Current focus: Export readability guard for the Milton memo path, keeping stale navigation text, mojibake, generic weather pages, Casetext boilerplate, and table drift out of demo output.
- Hot files: `README.md`, `CLAUDE.md`, `docs/HANDOFF.md`, `docs/ROADMAP.md`, `docs/heartbeat.md`, `docs/SESSION_LOG.md`, `logs/2026-04-28-session.md`, `src/war_room/weather_module.py`, `tests/test_export.py`
- Blockers: No hard blocker is documented in-repo; main risks are uneven fixture coverage, notebook-first operator UX, and the current venv not being editable-installed by default.
- Do not touch this sprint: repo rename, broad product rewrites, placeholder V2 directories as if they were live runtime, dependency churn without approval.
- Related repos: None documented in-repo; treat this repo as the working source of truth.
- Latest session log: `logs/2026-04-28-session.md` plus `docs/SESSION_LOG.md`
- Next best task: Review and merge the export readability guard PR, then pick the next smallest `#6` or `#9` foundation slice.
- Owner: Not explicitly named in-repo; maintained for the Merlin Law Group demo effort.
