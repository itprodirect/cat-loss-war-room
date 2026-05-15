# Heartbeat

- Repo: `cat-loss-war-room`
- Current milestone: Stabilize the notebook demo while landing the first narrow `#10` run-state contract slice; broader `#27` CI/pilot operationalization remains open after this PR.
- Current status: V0 demo is stable; active runtime is still `src/war_room/` plus `notebooks/01_case_war_room.ipynb`; `#8` is complete and closed after five committed fixture lanes became registry-backed and offline-ready; `#9` is complete in `docs/ISSUE_9_CLOSEOUT_AUDIT.md`; the first `#10` orchestration contract now lives in `src/war_room/orchestration.py`; #64 and #65 are closed hygiene follow-ups.
- Current branch: `feat/issue-10-run-state-contract`
- Last validated: 2026-05-15 via `python -m pytest tests/test_orchestration*.py tests/test_offline_demo_pack.py tests/test_release_scorecard.py -q` (`95 passed`, run through Git Bash for glob expansion), `python -m pytest tests\test_orchestration_state.py tests\test_offline_demo_pack.py tests\test_release_scorecard.py -q` (`95 passed`, explicit PowerShell equivalent), `python -m pytest -q` (`382 passed`), `python -m war_room.fixture_snapshots --check`, `python -m war_room.offline_e2e --check` (`5/5` scenarios; artifact `runs/offline_e2e/2026-05-15_offline-e2e_20260515t054312z.json`), `python -m war_room --verify --release-candidate issue-10-run-state-contract` (`382 passed`; preflight passed for 5 committed fixture scenarios; verify manifest `runs/verify/2026-05-15_issue-10-run-state-contract_20260515t054320z.json`), and `git diff --check`.
- Current focus: Open a narrow draft `#10` PR for the run-state/stage-status contract without adding the API service.
- Hot files: `src/war_room/orchestration.py`, `src/war_room/workflow_summary.py`, `tests/test_orchestration_state.py`, `docs/ISSUE_10_RUN_STATE_CONTRACT.md`, `docs/SESSION_LOG.md`
- Blockers: None for the narrow `#10` run-state contract slice.
- Do not touch this sprint: API framework, background queue, database, auth, dashboard, UI design, repo rename, broad product rewrites, placeholder V2 directories as live runtime, dependency churn without approval.
- Related repos: None documented in-repo; treat this repo as the working source of truth.
- Latest session log: `docs/SESSION_LOG.md` session 110
- Next best task: Review/merge the narrow `#10` run-state contract PR, then continue broader `#27` operationalization or the next explicitly scoped `#10` API slice.
- Owner: Not explicitly named in-repo; maintained for the Merlin Law Group demo effort.
