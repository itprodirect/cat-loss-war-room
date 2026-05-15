# Heartbeat

- Repo: `cat-loss-war-room`
- Current milestone: Stabilize the notebook demo while finishing broader `#27` CI/pilot operationalization.
- Current status: V0 demo is stable; active runtime is still `src/war_room/` plus `notebooks/01_case_war_room.ipynb`; `#8` is complete and closed after five committed fixture lanes became registry-backed and offline-ready; `#9` is complete in `docs/ISSUE_9_CLOSEOUT_AUDIT.md`; #64 and #65 are closed hygiene follow-ups.
- Current branch: `chore/issue-27-scorecard-operationalization`
- Last validated: 2026-05-15 via `python -m pytest -q` (`371 passed`), `python -m war_room.fixture_snapshots --check`, `python -m war_room.offline_e2e --check`, `python -m war_room --verify --release-candidate issue-27-scorecard-operationalization` (`371 passed`; preflight passed for 5 committed fixture scenarios; verify manifest `runs/verify/2026-05-15_issue-27-scorecard-operationalization_20260515t051144z.json`), `python -m war_room.release_scorecard --validate-latest --output-dir runs\release_scorecards`, and `git diff --check`.
- Current focus: Open a narrow `#27` PR for dashboard-ready scorecard blocking/advisory readiness categories.
- Hot files: `src/war_room/release_scorecard.py`, `tests/test_release_scorecard.py`, `docs/V2_RELEASE_RUBRIC.md`, `docs/SESSION_LOG.md`
- Blockers: None for the narrow `#27` scorecard operationalization slice.
- Do not touch this sprint: repo rename, broad product rewrites, placeholder V2 directories as if they were live runtime, dependency churn without approval.
- Related repos: None documented in-repo; treat this repo as the working source of truth.
- Latest session log: `docs/SESSION_LOG.md` session 109
- Next best task: Continue `#27` scorecard/rubric operationalization before downstream `#10` implementation.
- Owner: Not explicitly named in-repo; maintained for the Merlin Law Group demo effort.
