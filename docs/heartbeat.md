# Heartbeat

- Repo: `cat-loss-war-room`
- Current milestone: Stabilize the notebook demo while finishing `#27` and the remaining `#8` foundation work.
- Current status: V0 demo is stable; active runtime is still `src/war_room/` plus `notebooks/01_case_war_room.ipynb`; the `#27` local release-evidence stack is merged, `#8` has a deterministic golden snapshot gate, all four committed fixture lanes registry-backed and offline-ready, a documented fixture-seeding process, a next-candidate audit, and a readiness audit saying `#8` should remain open; `#9` is complete in `docs/ISSUE_9_CLOSEOUT_AUDIT.md`.
- Current branch: `codex/issue-8-readiness-audit`
- Last validated: 2026-05-14 via `python -m pytest tests/test_scenarios.py tests/test_fixture_snapshots.py tests/test_offline_demo_pack.py -q` (`52 passed`), `python -m pytest -q` (`336 passed`), `python -m war_room.fixture_snapshots --check`, `python -m war_room.offline_e2e --check` (`4/4` scenarios passed), and `python -m war_room --verify --release-candidate issue-8-readiness-audit`; verify manifest `runs/verify/2026-05-14_issue-8-readiness-audit_20260514t020751z.json`.
- Current focus: Review the `#8` readiness audit.
- Hot files: `docs/ISSUE_8_READINESS_AUDIT.md`, `docs/SESSION_LOG.md`, `docs/heartbeat.md`
- Blockers: `#8` should remain open until one live-only Florida registry scenario is manually seeded into a fifth committed fixture lane, or that remaining scope is explicitly moved to a follow-up issue.
- Do not touch this sprint: repo rename, broad product rewrites, placeholder V2 directories as if they were live runtime, dependency churn without approval.
- Related repos: None documented in-repo; treat this repo as the working source of truth.
- Latest session log: `docs/SESSION_LOG.md` session 106
- Next best task: Complete one final `#8` fixture-seeding PR for a live-only Florida registry scenario under `docs/FIXTURE_SEEDING.md`, preferably `ian_lee_citizens_ho3` unless source review chooses a stronger candidate; otherwise continue `#27` pilot/CI operationalization.
- Owner: Not explicitly named in-repo; maintained for the Merlin Law Group demo effort.
