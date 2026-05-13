# Heartbeat

- Repo: `cat-loss-war-room`
- Current milestone: Stabilize the notebook demo while finishing `#27` and the remaining `#8` foundation work.
- Current status: V0 demo is stable; active runtime is still `src/war_room/` plus `notebooks/01_case_war_room.ipynb`; the `#27` local release-evidence stack is merged, `#8` has a deterministic golden snapshot gate plus two registry-backed offline-ready scenarios, and `#9` is complete in `docs/ISSUE_9_CLOSEOUT_AUDIT.md`.
- Current branch: `codex/issue-8-fixture-breadth`
- Last validated: 2026-05-13 via `python -m pytest tests/test_fixture_snapshots.py tests/test_offline_demo_pack.py tests/test_intake_validation.py -q` (`53 passed`), `python -m pytest -q` (`334 passed`), `python -m war_room.fixture_snapshots --check`, `python -m war_room.offline_e2e --check`, and `python -m war_room --verify --release-candidate issue-8-fixture-breadth`; verify manifest `runs/verify/2026-05-13_issue-8-fixture-breadth_20260513t200758z.json`.
- Current focus: Review the `#8` fixture-breadth registry slice.
- Hot files: `scenarios/ida_orleans_lloyds_ho3.json`, `scenarios/index.json`, `tests/golden/offline_fixture_snapshots.json`, `tests/test_fixture_snapshots.py`, `docs/SESSION_LOG.md`
- Blockers: No hard blocker is documented in-repo; main risks are uneven fixture coverage and notebook-first operator UX.
- Do not touch this sprint: repo rename, broad product rewrites, placeholder V2 directories as if they were live runtime, dependency churn without approval.
- Related repos: None documented in-repo; treat this repo as the working source of truth.
- Latest session log: `docs/SESSION_LOG.md` session 102
- Next best task: Continue `#8` with the next safe fixture-seeding path, or continue `#27` pilot/CI operationalization.
- Owner: Not explicitly named in-repo; maintained for the Merlin Law Group demo effort.
