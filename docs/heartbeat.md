# Heartbeat

- Repo: `cat-loss-war-room`
- Current milestone: Keep the notebook demo stable after the merged PR `#79` thin orchestration transport slice; broader `#27` CI/pilot operationalization remains open.
- Current status: V0 demo is stable; active runtime is still `src/war_room/` plus `notebooks/01_case_war_room.ipynb`, not a full web app. The issue `#10` stack now has canonical run/stage vocabulary in `src/war_room/orchestration.py`, typed API boundary contracts in `src/war_room/orchestration_api_contracts.py`, an in-process offline service in `src/war_room/orchestration_service.py`, an operator-facing status presentation layer in `src/war_room/orchestration_status_view.py`, and a dependency-free thin transport/request-handler wrapper in `src/war_room/orchestration_transport.py`. #64 and #65 are closed hygiene follow-ups.
- Current branch: `docs/post-pr79-housekeeping`
- Last validated: 2026-05-16 via `git diff --check`, `python -m pytest -q` (`423 passed in 24.83s`), `python -m war_room --verify` (`423 passed` inside verify; manifest `runs/verify/2026-05-16_docs-post-pr79-housekeeping_20260516t194522z.json`), and `python -m war_room.orchestration_service --smoke --scenario milton_pinellas_citizens_ho3` (`status=completed`, `operator_status=degraded`, usable outputs available).
- Current focus: Open a docs-only post-PR79 status refresh PR without changing runtime behavior.
- Hot files: `docs/HANDOFF.md`, `docs/ISSUE_10_API_CONTRACTS.md`, `docs/heartbeat.md`, `docs/repo-brief.md`, `README.md`, `docs/ROADMAP.md`, `docs/SESSION_LOG.md`
- Blockers: None for the docs-only post-PR79 status refresh.
- Do not touch this sprint: API framework, background queue, database, auth, dashboard, UI design, repo rename, broad product rewrites, placeholder V2 directories as live runtime, dependency churn without approval.
- Related repos: None documented in-repo; treat this repo as the working source of truth.
- Latest session log: `docs/SESSION_LOG.md` session 116
- Next best task: Continue broader `#27` CI/pilot operationalization, or scope the next explicit `#10`/`#11` slice against the existing contracts/service/status/transport stack without turning the repo into a full web app.
- Owner: Not explicitly named in-repo; maintained for the Merlin Law Group demo effort.
