# Heartbeat

- Repo: `cat-loss-war-room`
- Current milestone: Stabilize the notebook demo while finishing `#27` and the remaining `#8` foundation work.
- Current status: V0 demo is stable; active runtime is still `src/war_room/` plus `notebooks/01_case_war_room.ipynb`; the `#27` local release-evidence stack is merged, `#8` has a first deterministic golden snapshot gate, and `#9` is documented ready to close in `docs/ISSUE_9_CLOSEOUT_AUDIT.md`.
- Current branch: `codex/issue-7-closure-sanity-audit`
- Last validated: 2026-05-13 via `python -m pytest tests/test_retrieval_contracts.py tests/test_exa_client.py tests/test_exa_adapter_contract.py tests/test_citation_verify.py -q` (`43 passed`), `python -m pytest -q` (`334 passed`), `python -m war_room.fixture_snapshots --check`, `python -m war_room.security_hygiene --check`, `python -m war_room.offline_e2e --check`, `python -m war_room.dependency_hygiene --check`, and `python -m war_room --verify --release-candidate issue-7-none-response-contract-fix`; verify manifest `runs/verify/2026-05-13_issue-7-none-response-contract-fix_20260513t195125z.json`.
- Current focus: Review the `#7` `None` provider-response malformed-contract fix.
- Hot files: `src/war_room/retrieval.py`, `src/war_room/exa_client.py`, `tests/test_retrieval_contracts.py`, `tests/test_exa_client.py`, `docs/SESSION_LOG.md`
- Blockers: No hard blocker is documented in-repo; main risks are uneven fixture coverage and notebook-first operator UX.
- Do not touch this sprint: repo rename, broad product rewrites, placeholder V2 directories as if they were live runtime, dependency churn without approval.
- Related repos: None documented in-repo; treat this repo as the working source of truth.
- Latest session log: `docs/SESSION_LOG.md` session 101
- Next best task: Broaden `#8` fixture coverage with a safe curated scenario, or continue `#27` pilot/CI operationalization.
- Owner: Not explicitly named in-repo; maintained for the Merlin Law Group demo effort.
