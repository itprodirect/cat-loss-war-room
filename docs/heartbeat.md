# Heartbeat

- Repo: `cat-loss-war-room`
- Current milestone: Stabilize the notebook demo while finishing `#27` and the remaining `#6` to `#9` foundation work.
- Current status: V0 demo is stable; active runtime is still `src/war_room/` plus `notebooks/01_case_war_room.ipynb`; the `#27` local release-evidence stack is now merged, including live preflight-backed scorecards, run-scoped verify artifacts, verify manifests, and a stable latest pointer.
- Current branch: `codex/issue-6-final-contract-docs`
- Last validated: 2026-04-29 via `$env:PYTHONPATH='src'; python -m war_room --verify --release-candidate issue-6-final-contract-docs` (`293 passed`; offline preflight passed for 4 fixture scenarios)
- Current focus: Final `#6` contract/docs closeout: Run Timeline now has a typed `v2alpha1` envelope over canonical `Run` and `RunStage`, completing the workflow read-model contract pass.
- Hot files: `README.md`, `CLAUDE.md`, `docs/BUILD_CHECKLIST.md`, `docs/HANDOFF.md`, `docs/ROADMAP.md`, `docs/V2_EVIDENCE_SCHEMA.md`, `docs/V2_ISSUE_MAP.md`, `docs/V2_RELEASE_RUBRIC.md`, `docs/heartbeat.md`, `docs/SESSION_LOG.md`, `logs/2026-04-28-session.md`, `src/war_room/models.py`, `src/war_room/workflow_summary.py`, `src/war_room/__init__.py`, `tests/test_workflow_summary.py`
- Blockers: No hard blocker is documented in-repo; main risks are uneven fixture coverage, notebook-first operator UX, and the current venv not being editable-installed by default.
- Do not touch this sprint: repo rename, broad product rewrites, placeholder V2 directories as if they were live runtime, dependency churn without approval.
- Related repos: None documented in-repo; treat this repo as the working source of truth.
- Latest session log: `logs/2026-04-28-session.md` plus `docs/SESSION_LOG.md`
- Next best task: Review and merge the final `#6` contract/docs PR, then close or explicitly defer any residual `#6` work before moving to `#9` quality-gate expansion or `#8` fixture breadth.
- Owner: Not explicitly named in-repo; maintained for the Merlin Law Group demo effort.
