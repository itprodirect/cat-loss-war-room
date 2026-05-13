# Heartbeat

- Repo: `cat-loss-war-room`
- Current milestone: Stabilize the notebook demo while finishing `#27` and the remaining `#7` to `#9` foundation work.
- Current status: V0 demo is stable; active runtime is still `src/war_room/` plus `notebooks/01_case_war_room.ipynb`; the `#27` local release-evidence stack is merged, and `#8` now has a first deterministic golden snapshot gate for committed offline fixtures.
- Current branch: `codex/issue-8-fixture-snapshots`
- Last validated: 2026-05-13 via `python -m war_room.fixture_snapshots --check` (passed), `python -m pytest -q` (`298 passed`), and `python -m war_room --verify --release-candidate issue-8-fixture-snapshots` (`298 passed`; offline preflight passed for 4 fixture scenarios)
- Current focus: Finish the review for this `#8` fixture snapshot slice, then continue broader `#8` fixture breadth or `#9` quality-gate expansion.
- Hot files: `src/war_room/fixture_snapshots.py`, `tests/test_fixture_snapshots.py`, `tests/golden/offline_fixture_snapshots.json`, `.github/workflows/ci.yml`, `docs/SESSION_LOG.md`
- Blockers: No hard blocker is documented in-repo; main risks are uneven fixture coverage and notebook-first operator UX.
- Do not touch this sprint: repo rename, broad product rewrites, placeholder V2 directories as if they were live runtime, dependency churn without approval.
- Related repos: None documented in-repo; treat this repo as the working source of truth.
- Latest session log: `docs/SESSION_LOG.md` session 93
- Next best task: Broaden `#8` fixture coverage with a safe, curated scenario or convert this snapshot gate into more granular `#9` CI failure categorization.
- Owner: Not explicitly named in-repo; maintained for the Merlin Law Group demo effort.
