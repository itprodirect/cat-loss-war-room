# Heartbeat

- Repo: `cat-loss-war-room`
- Current milestone: Stabilize the notebook demo while finishing `#27` and the remaining `#6` to `#9` foundation work.
- Current status: V0 demo is stable; active runtime is still `src/war_room/` plus `notebooks/01_case_war_room.ipynb`; the Milton benchmark trust/readability slice is now closed with cache-backed runtime cleanup for citation trust, carrier/caselaw relevance, and export readability.
- Current branch: `codex/milton-trust-readability-slice`
- Last validated: 2026-03-30 via `$env:PYTHONPATH='src'; .venv\Scripts\python.exe -m war_room --verify` (`268 passed, 1 warning`; offline preflight passed for 4 fixture scenarios)
- Current focus: Close out the Milton benchmark PR cleanly, then return to `#27` operationalization and the remaining `#6` to `#9` foundation work.
- Hot files: `src/war_room/models.py`, `src/war_room/export_md.py`, `src/war_room/evidence_board.py`, `src/war_room/carrier_module.py`, `src/war_room/caselaw_module.py`, `tests/test_memo_contracts.py`, `tests/test_export.py`, `tests/test_evidence_board.py`, `tests/test_carrier.py`, `tests/test_caselaw.py`, `tests/test_offline_demo_pack.py`
- Blockers: No hard blocker is documented in-repo; main risks are uneven fixture coverage, notebook-first operator UX, and the current venv not being editable-installed by default.
- Do not touch this sprint: repo rename, broad product rewrites, placeholder V2 directories as if they were live runtime, dependency churn without approval.
- Related repos: None documented in-repo; treat this repo as the working source of truth.
- Latest session log: `logs/2026-03-27-session.md`
- Next best task: Return to `#27` release-scorecard operationalization or broaden fixture-quality calibration beyond Milton once this narrow benchmark slice is merged.
- Owner: Not explicitly named in-repo; maintained for the Merlin Law Group demo effort.
