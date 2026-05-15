# Heartbeat

- Repo: `cat-loss-war-room`
- Current milestone: Stabilize the notebook demo while landing the issue `#73` orchestration API contract slice; broader `#27` CI/pilot operationalization remains open after this PR.
- Current status: V0 demo is stable; active runtime is still `src/war_room/` plus `notebooks/01_case_war_room.ipynb`; `#8` is complete and closed after five committed fixture lanes became registry-backed and offline-ready; `#9` is complete in `docs/ISSUE_9_CLOSEOUT_AUDIT.md`; the first `#10` orchestration contract now lives in `src/war_room/orchestration.py`; issue `#73` adds typed future API request/response contracts in `src/war_room/orchestration_api_contracts.py`; #64 and #65 are closed hygiene follow-ups.
- Current branch: `codex/issue-73-orchestration-api-contracts`
- Last validated: 2026-05-15 via `python -m pytest tests/test_orchestration*.py tests/test_*api* -q` (`39 passed`, run through Git Bash for glob expansion), `python -m pytest -q` (`400 passed`), `python -m war_room.fixture_snapshots --check`, `python -m war_room.offline_e2e --check` (`5/5` scenarios; artifact `runs/offline_e2e/2026-05-15_offline-e2e_20260515t061619z.json`), `python -m war_room --verify --release-candidate issue-10-api-contracts` (`400 passed`; preflight passed for 5 committed fixture scenarios; verify manifest `runs/verify/2026-05-15_issue-10-api-contracts_20260515t061627z.json`), and `git diff --check`.
- Current focus: Open a narrow draft PR for issue `#73` without adding the API service.
- Hot files: `src/war_room/orchestration_api_contracts.py`, `tests/test_orchestration_api_contracts.py`, `docs/ISSUE_10_API_CONTRACTS.md`, `docs/ISSUE_10_RUN_STATE_CONTRACT.md`, `docs/SESSION_LOG.md`
- Blockers: None for the narrow issue `#73` API contract slice.
- Do not touch this sprint: API framework, background queue, database, auth, dashboard, UI design, repo rename, broad product rewrites, placeholder V2 directories as live runtime, dependency churn without approval.
- Related repos: None documented in-repo; treat this repo as the working source of truth.
- Latest session log: `docs/SESSION_LOG.md` session 111
- Next best task: Review/merge the narrow issue `#73` API contract PR, then continue broader `#27` operationalization or the next explicitly scoped `#10` API implementation slice.
- Owner: Not explicitly named in-repo; maintained for the Merlin Law Group demo effort.
