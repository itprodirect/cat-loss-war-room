# Heartbeat

- Repo: `cat-loss-war-room`
- Current milestone: Keep the notebook demo stable while landing the narrow issue `#11` guided-intake UX/spec slice that complements the existing run-status spec and deterministic preview; broader `#27` CI/pilot operationalization remains open.
- Current status: V0 demo is stable; active runtime is still `src/war_room/` plus `notebooks/01_case_war_room.ipynb`, not a full web app. The issue `#10` stack now has canonical run/stage vocabulary in `src/war_room/orchestration.py`, typed API boundary contracts in `src/war_room/orchestration_api_contracts.py`, an in-process offline service in `src/war_room/orchestration_service.py`, an operator-facing status presentation layer in `src/war_room/orchestration_status_view.py`, a dependency-free thin transport/request-handler wrapper in `src/war_room/orchestration_transport.py`, and a dev-only standard-library HTTP adapter in `src/war_room/orchestration_http.py`. Issue `#11` now has documentation-only guided-intake and run-status UX/spec slices in `docs/ISSUE_11_GUIDED_INTAKE_UX_SPEC.md` and `docs/ISSUE_11_RUN_STATUS_UX_SPEC.md`, with the deterministic Milton degraded preview in `docs/examples/run_status_milton_degraded.md`.
- Current branch: `feat/issue-11-guided-intake-spec`
- Last validated: 2026-05-17 via `git diff --check`, `python -m pytest -q` (`430 passed in 14.04s`), `python -m war_room --verify` (`430 passed` inside verify; manifest `runs/verify/2026-05-17_feat-issue-11-guided-intake-spec_20260517t015455z.json`), and `python -m war_room.orchestration_service --smoke --scenario milton_pinellas_citizens_ho3` (`status=completed`, `operator_status=degraded`, `usable_outputs_available=true`, review reasons present, failed stages empty).
- Current focus: Finish the issue `#11` guided-intake UX/spec PR slice without expanding into a frontend app, dashboard, persistence, auth, production API, upload/OCR flow, notebook change, or dependency change.
- Hot files: `docs/ISSUE_11_GUIDED_INTAKE_UX_SPEC.md`, `docs/ISSUE_11_RUN_STATUS_UX_SPEC.md`, `docs/HANDOFF.md`, `docs/ROADMAP.md`, `docs/heartbeat.md`, `docs/SESSION_LOG.md`
- Blockers: None for the run-status UX/spec slice.
- Do not touch this sprint: API framework, background queue, database, auth, dashboard, UI design, repo rename, broad product rewrites, placeholder V2 directories as live runtime, dependency churn without approval.
- Related repos: None documented in-repo; treat this repo as the working source of truth.
- Latest session log: `docs/SESSION_LOG.md` session 120
- Next best task: Open the issue `#11` guided-intake UX/spec PR, then continue broader `#27` CI/pilot operationalization or scope the next explicit `#11` product-spec slice without turning the repo into a full web app.
- Owner: Not explicitly named in-repo; maintained for the Merlin Law Group demo effort.
