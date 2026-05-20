# Heartbeat

- Repo: `cat-loss-war-room`
- Current milestone: Keep the notebook demo stable while issue `#12` evidence/provenance adapter work continues after the issue `#92` release-evidence reporting slice.
- Current status: V0 demo is stable; active runtime is still `src/war_room/` plus `notebooks/01_case_war_room.ipynb`, not a full web app. The issue `#10` stack now has canonical run/stage vocabulary in `src/war_room/orchestration.py`, typed API boundary contracts in `src/war_room/orchestration_api_contracts.py`, an in-process offline service in `src/war_room/orchestration_service.py`, an operator-facing status presentation layer in `src/war_room/orchestration_status_view.py`, a dependency-free thin transport/request-handler wrapper in `src/war_room/orchestration_transport.py`, and a dev-only standard-library HTTP adapter in `src/war_room/orchestration_http.py`. Issue `#11` has documentation-only guided-intake and run-status UX/spec slices plus deterministic Milton previews. Issue `#27` has the human release-evidence reviewer guide, top-level `reviewer_summary`, and the issue `#92` / PR `#93` `ci_reporting_summary` inventory. Issue `#12` now has narrow evidence adapters landed for issue `#94` / PR `#95` caselaw output, issue `#96` / PR `#97` carrier output, and issue `#98` / PR `#99` weather output; the full V2 evidence graph, persistence layer, dashboard, and production API remain future work.
- Current branch: `docs/issue-101-remaining-issue-12-scope`
- Last validated: 2026-05-20 for issue `#101` via `git diff --check` and `python -m pytest -q` (`449 passed in 11.69s`); the prior current-state sync also passed `python -m war_room --verify` with manifest `runs/verify/2026-05-20_docs-post-adapter-state-sync_20260520t081618z.json`.
- Current focus: Use the issue `#12` remaining-scope review to keep the next citation-verify adapter child narrow.
- Hot files: `README.md`, `CLAUDE.md`, `docs/heartbeat.md`, `docs/HANDOFF.md`, `docs/repo-brief.md`, `docs/ROADMAP.md`, `docs/V2_EVIDENCE_SCHEMA.md`, `docs/V2_RELEASE_RUBRIC.md`, `docs/ISSUE_27_RELEASE_EVIDENCE_REVIEW_GUIDE.md`, `docs/SESSION_LOG.md`
- Blockers: None for issue `#12` citation-verify adapter scoping.
- Do not touch this sprint: API framework, background queue, database, auth, dashboard, UI design, repo rename, broad product rewrites, placeholder V2 directories as live runtime, dependency churn without approval.
- Related repos: None documented in-repo; treat this repo as the working source of truth.
- Latest session log: `docs/SESSION_LOG.md` session 131
- Next best task: Open or implement a narrow citation-verify evidence adapter child for issue `#12`, using the remaining-scope review as the boundary. Do not treat the landed adapters as completion of the full evidence/provenance graph or as Beta-ready, Pilot-ready, production-ready, or a shipped web app.
- Owner: Not explicitly named in-repo; maintained for the Merlin Law Group demo effort.
