# Issue 7 Closure Sanity Audit

Date: 2026-05-13

## Conclusion

Initial audit result: issue `#7` should not have been treated as accurately closed immediately after PR `#56`.

Follow-up resolution: the PR `#57` implementation now fixes the narrow remaining provider-contract gap. Provider `search()` or `get_contents()` paths that return `None` now raise the project-level malformed-response path instead of being normalized as empty result sets.

After this follow-up lands, issue `#7` can be treated as accurately closed against the audited acceptance criteria.

## Evidence Reviewed

- GitHub issue `#7`: closed on 2026-05-13 after PR `#56`.
- PR `#56`: merged and explicitly described itself as a focused `#7` slice, with a follow-up closeout review still required.
- PR `#56` post-merge review comment: flagged that `None` provider responses should raise `RetrievalContractError`, not become empty results.
- Initial local code finding:
  - `src/war_room/retrieval.py` rejected non-list provider responses, but `_normalize_provider_hits(None)` returned `RetrievalHitDiagnostics(hits=[])`.
  - `execute_retrieval_task()` then reported the response as `retrieval_empty` with a degraded task instead of `retrieval_failed`.
  - `fetch_retrieval_contents()` shared the same normalization path.
- Follow-up local code resolution:
  - `_normalize_provider_hits(None)` now raises `RetrievalContractError`.
  - `execute_retrieval_task()` now emits failed retrieval metadata with `error_kind=malformed_response`, `exception=RetrievalContractError`, `retryable=false`, and attempt-count metadata for `None` search responses.
  - `fetch_retrieval_contents()` now applies the same malformed-response rule for `None` content responses.
- Local tests:
  - `tests/test_retrieval_contracts.py` now covers direct search rejection, retrieval-task failure metadata, and content-fetch rejection for `None` provider responses.

## Audit Probe

An offline local probe with a fake provider returning `None` for `search()` produced:

```text
degraded
exa returned no results for 'audit query'.
retrieval_empty
```

The follow-up implementation changes that behavior to the expected malformed-response failure path.

## Recommendation

No separate reopen/follow-up is needed after this PR lands unless review finds another retrieval-contract gap.

Resolved acceptance criteria:

- `_normalize_provider_hits(None)` raises `RetrievalContractError`.
- `execute_retrieval_task()` emits a failed retrieval task with `error_kind=malformed_response`, `exception=RetrievalContractError`, `retryable=false`, and attempt-count metadata.
- `fetch_retrieval_contents()` applies the same malformed-response rule for `None`.
- Deterministic tests cover the `None` search/content response paths without live Exa calls.

## Scope Boundaries

This follow-up changed only the retrieval contract seam, deterministic contract tests, and status/session documentation. It did not change notebooks, dependencies, or fixture data. It did not make live Exa calls and did not start issue `#8`, `#10`, `#12`, or `#14` work.

## Validation

Initial audit validation:

- `python -m pytest tests/test_retrieval_contracts.py tests/test_exa_client.py tests/test_exa_adapter_contract.py tests/test_citation_verify.py -q` -> `40 passed in 8.99s`.
- `python -m pytest -q` -> `331 passed in 22.97s`.
- `python -m war_room --verify --release-candidate issue-7-closure-sanity-audit` -> passed; embedded `pytest -q` reported `331 passed in 13.33s`; verify manifest written under `runs/verify/2026-05-13_issue-7-closure-sanity-audit_20260513t194018z.json`.

Follow-up fix validation:

- `python -m pytest tests/test_retrieval_contracts.py tests/test_exa_client.py tests/test_exa_adapter_contract.py tests/test_citation_verify.py -q` -> `43 passed in 4.57s`.
- `python -m pytest -q` -> `334 passed in 7.90s`.
- `python -m war_room.fixture_snapshots --check` -> passed; snapshot matched `tests/golden/offline_fixture_snapshots.json`.
- `python -m war_room.security_hygiene --check` -> passed; `6/6` checks passed.
- `python -m war_room.offline_e2e --check` -> passed; `4/4` scenarios passed.
- `python -m war_room.dependency_hygiene --check` -> passed; `6/6` checks passed.
- `python -m war_room --verify --release-candidate issue-7-none-response-contract-fix` -> passed; embedded `pytest -q` reported `334 passed in 8.62s`; verify manifest written under `runs/verify/2026-05-13_issue-7-none-response-contract-fix_20260513t195125z.json`.
