# Heartbeat

- Repo: `cat-loss-war-room`
- Current milestone: Keep the notebook demo stable after the landed issue `#88` release-scorecard reviewer-summary operationalization for the issue `#27` verify bundle; broader `#27` CI/pilot operationalization remains open.
- Current status: V0 demo is stable; active runtime is still `src/war_room/` plus `notebooks/01_case_war_room.ipynb`, not a full web app. The issue `#10` stack now has canonical run/stage vocabulary in `src/war_room/orchestration.py`, typed API boundary contracts in `src/war_room/orchestration_api_contracts.py`, an in-process offline service in `src/war_room/orchestration_service.py`, an operator-facing status presentation layer in `src/war_room/orchestration_status_view.py`, a dependency-free thin transport/request-handler wrapper in `src/war_room/orchestration_transport.py`, and a dev-only standard-library HTTP adapter in `src/war_room/orchestration_http.py`. Issue `#11` now has documentation-only guided-intake and run-status UX/spec slices in `docs/ISSUE_11_GUIDED_INTAKE_UX_SPEC.md` and `docs/ISSUE_11_RUN_STATUS_UX_SPEC.md`, with deterministic Milton previews in `docs/examples/guided_intake_milton_preview.md` and `docs/examples/run_status_milton_degraded.md`. Issue `#27` now has a human release-evidence reviewer guide plus a top-level release-scorecard `reviewer_summary` convenience summary derived from the existing readiness posture without adding another readiness model.
- Current branch: `docs/current-state-truth-sync-after-88`
- Last validated: 2026-05-18 via `git diff --check` and `python -m pytest -q` (`432 passed in 23.75s`). Previous issue `#88` release-evidence validation remains recorded in session 123.
- Current focus: Current-state docs truth-sync after issue `#88`, without expanding into runtime code, CI workflow, frontend, dashboard, app shell, dependency, fixture, cache, citation, prompt, schema, live retrieval, notebook, or broader runtime changes.
- Hot files: `docs/heartbeat.md`, `docs/ISSUE_27_RELEASE_EVIDENCE_REVIEW_GUIDE.md`, `docs/V2_BLUEPRINT.md`, `docs/V2_RELEASE_RUBRIC.md`, `docs/HANDOFF.md`, `docs/ROADMAP.md`, `docs/SESSION_LOG.md`
- Blockers: None for the docs truth-sync slice.
- Do not touch this sprint: API framework, background queue, database, auth, dashboard, UI design, repo rename, broad product rewrites, placeholder V2 directories as live runtime, dependency churn without approval.
- Related repos: None documented in-repo; treat this repo as the working source of truth.
- Latest session log: `docs/SESSION_LOG.md` session 124
- Next best task: Map remaining issue `#10` scope after this docs truth-sync, then split issue `#11` into a contract seam and future UI child issues before starting issue `#12` with one canonical evidence adapter.
- Owner: Not explicitly named in-repo; maintained for the Merlin Law Group demo effort.
