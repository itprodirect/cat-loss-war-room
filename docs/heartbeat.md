# Heartbeat

- Repo: `cat-loss-war-room`
- Current milestone: Preserve the stable notebook/demo lane while planning the next issue `#12` evidence/provenance decision after same-module audit-snapshot dedupe landed.
- Current status: V0 demo is stable; active runtime is still `src/war_room/` plus `notebooks/01_case_war_room.ipynb`, not a full web app. Issue `#10` has landed orchestration contracts/service/status/transport/dev-HTTP slices; issue `#11` has guided-intake and run-status UX/spec slices plus deterministic previews; issue `#27` has release-evidence reviewer and CI/reporting summary layers. Issue `#12` now has named evidence adapters for weather, carrier, caselaw, and citation-verification output; helper deterministic evidence dedupe; same-module audit-snapshot dedupe with explicit `old_id -> retained_id` remapping; provenance-integrity coverage; `not_found` citation dedupe regression coverage; and Markdown Quality Snapshot raw/pre-dedupe vs retained/exported evidence visibility. Cross-module caselaw/citation-verification collapse remains intentionally disabled.
- Current branch: `docs/session-144-closeout`
- Last validated: 2026-05-20 after PR `#138`; Codex reported `git diff --check` passed, `python -m pytest tests/test_memo_contracts.py tests/test_export.py -q` -> `63 passed`, `python -m pytest -q` -> `493 passed`, and `python -m war_room --verify` passed with embedded pytest `493 passed`. GitHub Actions CI and Exa Compatibility Matrix passed for PR `#138` before squash merge.
- Current focus: Docs-only closeout for the May 20 evidence/provenance session so future maintainers and agents can restart from the right current state.
- Hot files: `docs/SESSION_144_CLOSEOUT.md`, `docs/heartbeat.md`, `docs/HANDOFF.md`, `docs/ROADMAP.md`, `docs/ISSUE_12_REMAINING_SCOPE.md`, `docs/ISSUE_12_DEDUPE_INTEGRATION_PLAN.md`, `docs/V2_EVIDENCE_SCHEMA.md`, `src/war_room/models.py`, `src/war_room/export_md.py`, `tests/test_memo_contracts.py`, `tests/test_export.py`, `tests/provenance_integrity.py`
- Blockers: None for the docs-only closeout. The main remaining risk is design drift if future work jumps into cross-module dedupe before issue `#139` is resolved.
- Do not touch this sprint: cross-module evidence collapse, API framework, background queue, database, auth, dashboard, UI design, production runtime claims, broad product rewrites, dependency churn without approval, or retained duplicate/source-role schema changes unless explicitly scoped by a follow-up issue.
- Related repos: None documented in-repo; treat this repo as the working source of truth.
- Latest session closeout: `docs/SESSION_144_CLOSEOUT.md`
- Latest session log entries: `docs/SESSION_LOG.md` sessions 142 and 143 for PRs `#136` and `#138`.
- Next best task: Start with issue `#139` and create a docs-only decision record on retained duplicate/source-role metadata before any future cross-module dedupe discussion. Recommended default: keep cross-module relatedness expressed through `EvidenceCluster` until metadata and reviewer-surface requirements are explicitly designed.
- Owner: Not explicitly named in-repo; maintained for the Merlin Law Group demo effort.
