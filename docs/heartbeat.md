# Heartbeat

- Repo: `cat-loss-war-room`
- Current milestone: Keep the notebook demo stable while landing the dev-only issue `#10` HTTP adapter over the existing transport layer; broader `#27` CI/pilot operationalization remains open.
- Current status: V0 demo is stable; active runtime is still `src/war_room/` plus `notebooks/01_case_war_room.ipynb`, not a full web app. The issue `#10` stack now has canonical run/stage vocabulary in `src/war_room/orchestration.py`, typed API boundary contracts in `src/war_room/orchestration_api_contracts.py`, an in-process offline service in `src/war_room/orchestration_service.py`, an operator-facing status presentation layer in `src/war_room/orchestration_status_view.py`, a dependency-free thin transport/request-handler wrapper in `src/war_room/orchestration_transport.py`, and a dev-only standard-library HTTP adapter in `src/war_room/orchestration_http.py`. #64 and #65 are closed hygiene follow-ups.
- Current branch: `feat/issue-10-dev-http-wrapper`
- Last validated: 2026-05-16 via `python -m pytest tests/test_orchestration_http.py tests/test_orchestration_transport.py tests/test_orchestration_service.py -q` (`19 passed in 3.19s`), `python -m pytest -q` (`430 passed in 14.29s`), `python -m war_room --verify` (`430 passed` inside verify; manifest `runs/verify/2026-05-16_feat-issue-10-dev-http-wrapper_20260516t204511z.json`), `python -m war_room.orchestration_service --smoke --scenario milton_pinellas_citizens_ho3` (`status=completed`, `operator_status=degraded`, usable outputs available), and `git diff --check`.
- Current focus: Open the dev-only HTTP adapter PR without expanding into a production API or web app.
- Hot files: `src/war_room/orchestration_http.py`, `tests/test_orchestration_http.py`, `docs/ISSUE_10_DEV_HTTP_WRAPPER.md`, `docs/HANDOFF.md`, `docs/ROADMAP.md`, `docs/heartbeat.md`, `docs/SESSION_LOG.md`
- Blockers: None for the dev-only HTTP adapter slice.
- Do not touch this sprint: API framework, background queue, database, auth, dashboard, UI design, repo rename, broad product rewrites, placeholder V2 directories as live runtime, dependency churn without approval.
- Related repos: None documented in-repo; treat this repo as the working source of truth.
- Latest session log: `docs/SESSION_LOG.md` session 117
- Next best task: Review/open the dev-only HTTP adapter PR, then continue broader `#27` CI/pilot operationalization or scope the next explicit `#10`/`#11` slice without turning the repo into a full web app.
- Owner: Not explicitly named in-repo; maintained for the Merlin Law Group demo effort.
