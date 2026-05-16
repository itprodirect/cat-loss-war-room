# Heartbeat

- Repo: `cat-loss-war-room`
- Current milestone: Keep the notebook demo stable while landing the narrow issue `#11` run-status UX/spec and deterministic preview slices over the existing orchestration `status_presentation` payload; broader `#27` CI/pilot operationalization remains open.
- Current status: V0 demo is stable; active runtime is still `src/war_room/` plus `notebooks/01_case_war_room.ipynb`, not a full web app. The issue `#10` stack now has canonical run/stage vocabulary in `src/war_room/orchestration.py`, typed API boundary contracts in `src/war_room/orchestration_api_contracts.py`, an in-process offline service in `src/war_room/orchestration_service.py`, an operator-facing status presentation layer in `src/war_room/orchestration_status_view.py`, a dependency-free thin transport/request-handler wrapper in `src/war_room/orchestration_transport.py`, and a dev-only standard-library HTTP adapter in `src/war_room/orchestration_http.py`. The first issue `#11` run-status UX/spec slice lives in `docs/ISSUE_11_RUN_STATUS_UX_SPEC.md`, and the deterministic Milton degraded preview lives in `docs/examples/run_status_milton_degraded.md`; both remain documentation-only. #64 and #65 are closed hygiene follow-ups.
- Current branch: `feat/issue-11-run-status-preview`
- Last validated: 2026-05-16 via `git diff --check`, `python -m pytest -q` (`430 passed in 9.79s`), `python -m war_room --verify` (`430 passed` inside verify; manifest `runs/verify/2026-05-16_feat-issue-11-run-status-preview_20260516t214703z.json`), and `python -m war_room.orchestration_service --smoke --scenario milton_pinellas_citizens_ho3` (`status=completed`, `operator_status=degraded`, `usable_outputs_available=true`, review reasons present).
- Current focus: Open the issue `#11` run-status preview PR without expanding into a frontend app, dashboard, persistence, auth, or production API.
- Hot files: `docs/examples/run_status_milton_degraded.md`, `docs/ISSUE_11_RUN_STATUS_UX_SPEC.md`, `docs/HANDOFF.md`, `docs/ROADMAP.md`, `docs/heartbeat.md`, `docs/SESSION_LOG.md`
- Blockers: None for the run-status UX/spec slice.
- Do not touch this sprint: API framework, background queue, database, auth, dashboard, UI design, repo rename, broad product rewrites, placeholder V2 directories as live runtime, dependency churn without approval.
- Related repos: None documented in-repo; treat this repo as the working source of truth.
- Latest session log: `docs/SESSION_LOG.md` session 119
- Next best task: Review/open the issue `#11` run-status preview PR, then continue broader `#27` CI/pilot operationalization or scope the next explicit `#11` guided-intake/status slice without turning the repo into a full web app.
- Owner: Not explicitly named in-repo; maintained for the Merlin Law Group demo effort.
