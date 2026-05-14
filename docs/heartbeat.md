# Heartbeat

- Repo: `cat-loss-war-room`
- Current milestone: Stabilize the notebook demo while finishing broader `#27` CI/pilot operationalization.
- Current status: V0 demo is stable; active runtime is still `src/war_room/` plus `notebooks/01_case_war_room.ipynb`; `#8` is complete and closed after five committed fixture lanes became registry-backed and offline-ready; `#9` is complete in `docs/ISSUE_9_CLOSEOUT_AUDIT.md`; #64 and #65 remain open as non-blocking hygiene/normalization follow-ups.
- Current branch: `chore/issue-8-closed-status-sync`
- Last validated: 2026-05-14 via `git diff --check`, `python -m war_room.fixture_snapshots --check`, and `python -m war_room --verify --release-candidate issue-8-closed-status-docs-sync` (`343 passed`; preflight passed for 5 committed fixture scenarios; verify manifest `runs/verify/2026-05-14_issue-8-closed-status-docs-sync_20260514t042129z.json`).
- Current focus: Review the `#8` closed-status docs sync PR.
- Hot files: `README.md`, `CLAUDE.md`, `docs/HANDOFF.md`, `docs/ROADMAP.md`, `docs/V2_ISSUE_MAP.md`, `docs/ISSUE_8_READINESS_AUDIT.md`, `docs/SESSION_LOG.md`
- Blockers: None for the `#8` docs sync.
- Do not touch this sprint: repo rename, broad product rewrites, placeholder V2 directories as if they were live runtime, dependency churn without approval.
- Related repos: None documented in-repo; treat this repo as the working source of truth.
- Latest session log: `docs/SESSION_LOG.md` session 108
- Next best task: Continue `#27` scorecard/rubric operationalization before downstream `#10` implementation.
- Owner: Not explicitly named in-repo; maintained for the Merlin Law Group demo effort.
