# Heartbeat

- Repo: `cat-loss-war-room`
- Current milestone: Keep the notebook demo stable while issue `#27` release-evidence operationalization continues through narrow reporting and review-consumption slices.
- Current status: V0 demo is stable; active runtime is still `src/war_room/` plus `notebooks/01_case_war_room.ipynb`, not a full web app. The issue `#10` stack now has canonical run/stage vocabulary in `src/war_room/orchestration.py`, typed API boundary contracts in `src/war_room/orchestration_api_contracts.py`, an in-process offline service in `src/war_room/orchestration_service.py`, an operator-facing status presentation layer in `src/war_room/orchestration_status_view.py`, a dependency-free thin transport/request-handler wrapper in `src/war_room/orchestration_transport.py`, and a dev-only standard-library HTTP adapter in `src/war_room/orchestration_http.py`. Issue `#11` has documentation-only guided-intake and run-status UX/spec slices plus deterministic Milton previews. Issue `#27` now has a human release-evidence reviewer guide, a top-level release-scorecard `reviewer_summary` convenience summary, and an issue `#92` `ci_reporting_summary` inventory that maps the existing verify bundle and blocking/advisory readiness fields without adding another readiness model.
- Current branch: `codex/issue-92-release-evidence-ci-reporting`
- Last validated: 2026-05-20 via `git diff --check`, `python -m pytest -q` (`433 passed in 25.59s`), and `python -m war_room --verify` (`433 passed in 24.28s` embedded; manifest `runs/verify/2026-05-20_codex-issue-92-release-evidence-ci-reporting_20260520t042606z.json`).
- Current focus: Issue `#92` release-evidence CI/reporting consumption map from the existing verify bundle, without changing readiness levels, runtime behavior, CI workflows, release claims, or product scope.
- Hot files: `src/war_room/release_scorecard.py`, `tests/test_release_scorecard.py`, `tests/test_bootstrap.py`, `docs/ISSUE_27_RELEASE_EVIDENCE_REVIEW_GUIDE.md`, `docs/V2_RELEASE_RUBRIC.md`, `docs/SESSION_LOG.md`, `docs/heartbeat.md`
- Blockers: None for the issue `#92` reporting-consumption slice.
- Do not touch this sprint: API framework, background queue, database, auth, dashboard, UI design, repo rename, broad product rewrites, placeholder V2 directories as live runtime, dependency churn without approval.
- Related repos: None documented in-repo; treat this repo as the working source of truth.
- Latest session log: `docs/SESSION_LOG.md` session 125
- Next best task: Review and merge the issue `#92` PR, then continue broader issue `#27` pilot/reporting operationalization or move to the next explicitly scoped `#10`/`#11` follow-up without treating the repo as Beta-ready, Pilot-ready, production-ready, or a shipped web app.
- Owner: Not explicitly named in-repo; maintained for the Merlin Law Group demo effort.
