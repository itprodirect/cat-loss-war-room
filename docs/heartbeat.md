# Heartbeat

- Repo: `cat-loss-war-room`
- Current milestone: Stabilize the notebook demo while finishing `#27` and the remaining `#8` foundation work.
- Current status: V0 demo is stable; active runtime is still `src/war_room/` plus `notebooks/01_case_war_room.ipynb`; the `#27` local release-evidence stack is merged, `#8` has a deterministic golden snapshot gate, three registry-backed offline-ready scenarios, a documented fixture-seeding process, and a next-candidate audit; `#9` is complete in `docs/ISSUE_9_CLOSEOUT_AUDIT.md`.
- Current branch: `codex/issue-8-next-scenario-audit`
- Last validated: 2026-05-13 via `python -m pytest tests/test_scenarios.py tests/test_fixture_snapshots.py tests/test_offline_demo_pack.py -q` (`52 passed`), `python -m pytest -q` (`336 passed`), `python -m war_room.fixture_snapshots --check`, `python -m war_room.offline_e2e --check`, and `python -m war_room --verify --release-candidate issue-8-next-scenario-audit`; verify manifest `runs/verify/2026-05-13_issue-8-next-scenario-audit_20260513t204614z.json`.
- Current focus: Review the `#8` next-scenario candidate audit and Texas hail HO-B registry promotion.
- Hot files: `docs/ISSUE_8_NEXT_SCENARIO_AUDIT.md`, `scenarios/texas_hail_tarrant_allstate_hob.json`, `tests/golden/offline_fixture_snapshots.json`, `docs/SESSION_LOG.md`
- Blockers: No hard blocker is documented in-repo; main risks are uneven fixture coverage and notebook-first operator UX.
- Do not touch this sprint: repo rename, broad product rewrites, placeholder V2 directories as if they were live runtime, dependency churn without approval.
- Related repos: None documented in-repo; treat this repo as the working source of truth.
- Latest session log: `docs/SESSION_LOG.md` session 104
- Next best task: Promote the Texas DP-3 matching fixture lane or begin a reviewed seeding pass for one live-only Florida registry scenario.
- Owner: Not explicitly named in-repo; maintained for the Merlin Law Group demo effort.
