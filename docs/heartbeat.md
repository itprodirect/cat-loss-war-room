# Heartbeat

- Repo: `cat-loss-war-room`
- Current milestone: Stabilize the notebook demo while finishing `#27` and the remaining `#7` to `#9` foundation work after the `#6` closeout-audit PR lands.
- Current status: V0 demo is stable; active runtime is still `src/war_room/` plus `notebooks/01_case_war_room.ipynb`; the `#27` local release-evidence stack is now merged, and the notebook Evidence Board now has a styled HTML review surface over the typed read model.
- Current branch: `codex/issue-6-closeout-audit`
- Last validated: 2026-05-13 via `python -m pytest -q` (`294 passed`) and `python -m war_room --verify --release-candidate issue-6-closeout-audit` (`294 passed`; offline preflight passed for 4 fixture scenarios)
- Current focus: Close issue `#6` after the closeout-audit PR lands, then return to the remaining `#7`, `#8`, `#9`, and `#27` foundation work.
- Hot files: `docs/ISSUE_6_CLOSEOUT_AUDIT.md`, `docs/SESSION_LOG.md`, `docs/ROADMAP.md`, `docs/HANDOFF.md`, `docs/V2_ISSUE_MAP.md`, `docs/BUILD_CHECKLIST.md`
- Blockers: No hard blocker is documented in-repo; main risks are uneven fixture coverage and notebook-first operator UX.
- Do not touch this sprint: repo rename, broad product rewrites, placeholder V2 directories as if they were live runtime, dependency churn without approval.
- Related repos: None documented in-repo; treat this repo as the working source of truth.
- Latest session log: `docs/SESSION_LOG.md` session 92
- Next best task: Close issue `#6` after this PR lands, then move to `#9` quality-gate expansion or `#8` fixture breadth.
- Owner: Not explicitly named in-repo; maintained for the Merlin Law Group demo effort.
