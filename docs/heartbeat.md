# Heartbeat

- Repo: `cat-loss-war-room`
- Current milestone: Keep the notebook demo stable while landing tiny docs-only issue `#85` Milton guided-intake preview work that complements the issue `#11` guided-intake UX spec, run-status UX spec, and Milton degraded run-status preview; broader `#27` CI/pilot operationalization remains open.
- Current status: V0 demo is stable; active runtime is still `src/war_room/` plus `notebooks/01_case_war_room.ipynb`, not a full web app. The issue `#10` stack now has canonical run/stage vocabulary in `src/war_room/orchestration.py`, typed API boundary contracts in `src/war_room/orchestration_api_contracts.py`, an in-process offline service in `src/war_room/orchestration_service.py`, an operator-facing status presentation layer in `src/war_room/orchestration_status_view.py`, a dependency-free thin transport/request-handler wrapper in `src/war_room/orchestration_transport.py`, and a dev-only standard-library HTTP adapter in `src/war_room/orchestration_http.py`. Issue `#11` now has documentation-only guided-intake and run-status UX/spec slices in `docs/ISSUE_11_GUIDED_INTAKE_UX_SPEC.md` and `docs/ISSUE_11_RUN_STATUS_UX_SPEC.md`, with deterministic Milton previews in `docs/examples/guided_intake_milton_preview.md` and `docs/examples/run_status_milton_degraded.md`.
- Current branch: `main`
- Last validated: 2026-05-17 via `git diff --check`, `python -m pytest -q` (`430 passed in 20.68s`), `python -m war_room --verify` (`430 passed` inside verify; manifest `runs/verify/2026-05-17_main_20260517t023107z.json`), and `python -m war_room.orchestration_service --smoke --scenario milton_pinellas_citizens_ho3` (`status=completed`, `operator_status=degraded`, `usable_outputs_available=true`, review reasons present, failed stages empty).
- Current focus: Finish the issue `#85` docs-only Milton guided-intake preview slice without expanding into a frontend app, dashboard, persistence, auth, production API, upload/OCR flow, notebook change, runtime behavior change, or dependency change.
- Hot files: `docs/examples/guided_intake_milton_preview.md`, `docs/ISSUE_11_GUIDED_INTAKE_UX_SPEC.md`, `docs/ISSUE_11_RUN_STATUS_UX_SPEC.md`, `docs/HANDOFF.md`, `docs/ROADMAP.md`, `docs/heartbeat.md`, `docs/SESSION_LOG.md`
- Blockers: None for the run-status UX/spec slice.
- Do not touch this sprint: API framework, background queue, database, auth, dashboard, UI design, repo rename, broad product rewrites, placeholder V2 directories as live runtime, dependency churn without approval.
- Related repos: None documented in-repo; treat this repo as the working source of truth.
- Latest session log: `docs/SESSION_LOG.md` session 121
- Next best task: Open the issue `#85` docs-only preview PR, then continue broader `#27` CI/pilot operationalization or scope the next explicit `#11` product-spec slice without turning the repo into a full web app.
- Owner: Not explicitly named in-repo; maintained for the Merlin Law Group demo effort.
