# Heartbeat

- Repo: `cat-loss-war-room`
- Current milestone: Stabilize the notebook demo while finishing `#27`, the narrow `#7` closure follow-up, and the remaining `#8` foundation work.
- Current status: V0 demo is stable; active runtime is still `src/war_room/` plus `notebooks/01_case_war_room.ipynb`; the `#27` local release-evidence stack is merged, `#8` has a first deterministic golden snapshot gate, and `#9` is documented ready to close in `docs/ISSUE_9_CLOSEOUT_AUDIT.md`.
- Current branch: `codex/issue-7-retrieval-contract-hardening`
- Last validated: 2026-05-13 via `python -m pytest tests/test_retrieval_contracts.py tests/test_exa_client.py tests/test_exa_adapter_contract.py tests/test_citation_verify.py -q` (`40 passed`), `python -m pytest -q` (`331 passed`), and `python -m war_room --verify --release-candidate issue-7-closure-sanity-audit`; verify manifest `runs/verify/2026-05-13_issue-7-closure-sanity-audit_20260513t194018z.json`.
- Current focus: `#7` closure sanity audit found one remaining provider-response contract gap; recommend reopening `#7` or creating a narrow follow-up.
- Hot files: `src/war_room/retrieval.py`, `src/war_room/exa_client.py`, `tests/test_retrieval_contracts.py`, `tests/test_exa_client.py`, `docs/SESSION_LOG.md`
- Blockers: No hard blocker is documented in-repo; main risks are uneven fixture coverage and notebook-first operator UX.
- Do not touch this sprint: repo rename, broad product rewrites, placeholder V2 directories as if they were live runtime, dependency churn without approval.
- Related repos: None documented in-repo; treat this repo as the working source of truth.
- Latest session log: `docs/SESSION_LOG.md` session 100
- Next best task: Fix or track the `#7` `None` provider-response contract gap, then broaden `#8` fixture coverage with a safe curated scenario.
- Owner: Not explicitly named in-repo; maintained for the Merlin Law Group demo effort.
