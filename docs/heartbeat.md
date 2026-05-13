# Heartbeat

- Repo: `cat-loss-war-room`
- Current milestone: Stabilize the notebook demo while finishing `#27` and the remaining `#7` to `#9` foundation work.
- Current status: V0 demo is stable; active runtime is still `src/war_room/` plus `notebooks/01_case_war_room.ipynb`; the `#27` local release-evidence stack is merged, `#8` has a first deterministic golden snapshot gate, and `#9` now has categorized quality-gate artifacts plus offline security, dependency hygiene, and offline e2e gates.
- Current branch: `codex/issue-9-dependency-hygiene-gate`
- Last validated: 2026-05-13 via `python -m pytest -q` (`322 passed`), `python -m war_room.quality_gates run --gate dependency-hygiene-check --output-dir runs/quality_gates/local -- python -m war_room.dependency_hygiene --check`, and `python -m war_room --verify --release-candidate issue-9-dependency-hygiene-gate`; verify manifest `runs/verify/2026-05-13_issue-9-dependency-hygiene-gate_20260513t060742z.json`.
- Current focus: Finish review for this final `#9` dependency hygiene gate slice, then put `#9` through closeout review.
- Hot files: `src/war_room/dependency_hygiene.py`, `src/war_room/quality_gates.py`, `.github/workflows/ci.yml`, `tests/test_dependency_hygiene.py`, `tests/test_quality_gates.py`, `docs/SESSION_LOG.md`
- Blockers: No hard blocker is documented in-repo; main risks are uneven fixture coverage and notebook-first operator UX.
- Do not touch this sprint: repo rename, broad product rewrites, placeholder V2 directories as if they were live runtime, dependency churn without approval.
- Related repos: None documented in-repo; treat this repo as the working source of truth.
- Latest session log: `docs/SESSION_LOG.md` session 97
- Next best task: Close out `#9` after this PR lands, or broaden `#8` fixture coverage with a safe curated scenario.
- Owner: Not explicitly named in-repo; maintained for the Merlin Law Group demo effort.
