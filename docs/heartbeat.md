# Heartbeat

- Repo: `cat-loss-war-room`
- Current milestone: Stabilize the notebook demo while finishing `#27` and the remaining `#8` foundation work.
- Current status: V0 demo is stable; active runtime is still `src/war_room/` plus `notebooks/01_case_war_room.ipynb`; the `#27` local release-evidence stack is merged, `#8` has a deterministic golden snapshot gate, two registry-backed offline-ready scenarios, and a documented fixture-seeding process with lightweight promotion guards; `#9` is complete in `docs/ISSUE_9_CLOSEOUT_AUDIT.md`.
- Current branch: `codex/issue-8-fixture-seeding-process`
- Last validated: 2026-05-13 via `python -m pytest tests/test_fixture_snapshots.py tests/test_offline_demo_pack.py tests/test_intake_validation.py tests/test_scenarios.py -q` (`64 passed`), `python -m pytest -q` (`336 passed`), `python -m war_room.fixture_snapshots --check`, `python -m war_room.offline_e2e --check`, and `python -m war_room --verify --release-candidate issue-8-fixture-seeding-process`; verify manifest `runs/verify/2026-05-13_issue-8-fixture-seeding-process_20260513t203151z.json`.
- Current focus: Review the `#8` fixture-seeding process slice.
- Hot files: `docs/FIXTURE_SEEDING.md`, `src/war_room/scenarios.py`, `tests/test_scenarios.py`, `docs/SESSION_LOG.md`
- Blockers: No hard blocker is documented in-repo; main risks are uneven fixture coverage and notebook-first operator UX.
- Do not touch this sprint: repo rename, broad product rewrites, placeholder V2 directories as if they were live runtime, dependency churn without approval.
- Related repos: None documented in-repo; treat this repo as the working source of truth.
- Latest session log: `docs/SESSION_LOG.md` session 103
- Next best task: Use the fixture-seeding process for the next safe `#8` scenario addition, or continue `#27` pilot/CI operationalization.
- Owner: Not explicitly named in-repo; maintained for the Merlin Law Group demo effort.
