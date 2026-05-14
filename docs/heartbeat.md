# Heartbeat

- Repo: `cat-loss-war-room`
- Current milestone: Stabilize the notebook demo while finishing `#27` and the `#8` closeout review.
- Current status: V0 demo is stable; active runtime is still `src/war_room/` plus `notebooks/01_case_war_room.ipynb`; the `#27` local release-evidence stack is merged, `#8` now has a deterministic golden snapshot gate, five committed fixture lanes registry-backed and offline-ready, a documented fixture-seeding process, next-candidate/readiness audits, and a manually source-reviewed Ian/Lee/Citizens fifth fixture lane; `#9` is complete in `docs/ISSUE_9_CLOSEOUT_AUDIT.md`.
- Current branch: `codex/issue-8-final-florida-fixture`
- Last validated: 2026-05-14 via `python -m pytest tests/test_scenarios.py tests/test_fixture_snapshots.py tests/test_offline_demo_pack.py -q` (`59 passed`), `python -m pytest -q` (`343 passed`), `python -m war_room.fixture_snapshots --check`, `python -m war_room.offline_e2e --check` (`5/5` scenarios passed; artifact `runs/offline_e2e/2026-05-14_offline-e2e_20260514t025227z.json`), and `python -m war_room --verify --release-candidate issue-8-final-florida-fixture`; verify manifest `runs/verify/2026-05-14_issue-8-final-florida-fixture_20260514t025241z.json`.
- Current focus: Review the `#8` final Florida fixture-seeding PR.
- Hot files: `cache_samples/ian_citizens_lee/`, `scenarios/ian_lee_citizens_ho3.json`, `tests/golden/offline_fixture_snapshots.json`, `docs/ISSUE_8_READINESS_AUDIT.md`, `docs/SESSION_LOG.md`
- Blockers: `#8` remains open for maintainer review of the fifth-lane fixture-seeding slice and any decision on whether remaining live-only Florida scenarios should move to a follow-up issue.
- Do not touch this sprint: repo rename, broad product rewrites, placeholder V2 directories as if they were live runtime, dependency churn without approval.
- Related repos: None documented in-repo; treat this repo as the working source of truth.
- Latest session log: `docs/SESSION_LOG.md` session 107
- Next best task: Review the Ian/Lee/Citizens fixture-seeding PR and decide whether to close out `#8` separately or open a follow-up issue for remaining live-only Florida scenarios; otherwise continue `#27` pilot/CI operationalization.
- Owner: Not explicitly named in-repo; maintained for the Merlin Law Group demo effort.
