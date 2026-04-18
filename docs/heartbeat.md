# Heartbeat

- Repo: `cat-loss-war-room`
- Current milestone: Stabilize the notebook demo while finishing `#27` and the remaining `#6` to `#9` foundation work.
- Current status: V0 demo is stable; active runtime is still `src/war_room/` plus `notebooks/01_case_war_room.ipynb`; the `#27` local release-evidence stack is now merged, including live preflight-backed scorecards, run-scoped verify artifacts, verify manifests, and a stable latest pointer.
- Current branch: `codex/post-merge-status-sync`
- Last validated: 2026-04-18 via `$env:PYTHONPATH='src'; python -m war_room --verify --release-candidate post-merge-status-sync` (`277 passed`; offline preflight passed for 4 fixture scenarios)
- Current focus: Sync repo-status docs and issue tracking to the merged `#27` release-evidence state, then return to the remaining `#6` to `#9` foundation work.
- Hot files: `README.md`, `AGENTS.md`, `docs/HANDOFF.md`, `docs/ROADMAP.md`, `docs/V2_ISSUE_MAP.md`, `docs/repo-brief.md`, `docs/BUILD_CHECKLIST.md`, `docs/V2_RELEASE_RUBRIC.md`
- Blockers: No hard blocker is documented in-repo; main risks are uneven fixture coverage, notebook-first operator UX, and the current venv not being editable-installed by default.
- Do not touch this sprint: repo rename, broad product rewrites, placeholder V2 directories as if they were live runtime, dependency churn without approval.
- Related repos: None documented in-repo; treat this repo as the working source of truth.
- Latest session log: `docs/SESSION_LOG.md`
- Next best task: After the doc/issue sync lands, pick the next smallest foundation slice in `#6` or `#9`, with a slight bias toward broader CI layering or the remaining typed-contract seams.
- Owner: Not explicitly named in-repo; maintained for the Merlin Law Group demo effort.
