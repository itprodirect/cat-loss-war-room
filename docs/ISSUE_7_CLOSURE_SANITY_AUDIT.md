# Issue 7 Closure Sanity Audit

Date: 2026-05-13

## Conclusion

Issue `#7` should not be treated as accurately closed yet.

PR `#56` landed the fifth retrieval-contract slice and issue `#7` is currently closed on GitHub with state reason `completed`, but the post-merge audit found one narrow remaining provider-contract gap: a provider `search()` or `get_contents()` path that returns `None` is currently normalized as an empty result set instead of a malformed provider response.

That means a provider adapter bug can be reported as `retrieval_empty` / degraded no-results behavior rather than a normalized contract failure. This conflicts with the issue acceptance criteria that adapter drift and malformed responses be reported through normalized errors and retry metadata.

## Evidence Reviewed

- GitHub issue `#7`: closed on 2026-05-13 after PR `#56`.
- PR `#56`: merged and explicitly described itself as a focused `#7` slice, with a follow-up closeout review still required.
- PR `#56` post-merge review comment: flagged that `None` provider responses should raise `RetrievalContractError`, not become empty results.
- Local code:
  - `src/war_room/retrieval.py` rejects non-list provider responses, but `_normalize_provider_hits(None)` currently returns `RetrievalHitDiagnostics(hits=[])`.
  - `execute_retrieval_task()` then reports the response as `retrieval_empty` with a degraded task instead of `retrieval_failed`.
  - `fetch_retrieval_contents()` shares the same normalization path.
- Local tests:
  - `tests/test_retrieval_contracts.py` covers malformed non-list responses, partial malformed rows, missing fields, timeouts, and content normalization.
  - No current test locks the `None` provider-response case.

## Audit Probe

An offline local probe with a fake provider returning `None` for `search()` produced:

```text
degraded
exa returned no results for 'audit query'.
retrieval_empty
```

Expected behavior for the remaining gap should be a normalized malformed-response failure, not an empty-results path.

## Recommendation

Reopen issue `#7`, or create a narrow follow-up issue if the team wants to keep the original issue closed for bookkeeping.

Suggested follow-up title:

`Reject None retrieval provider responses as malformed contract failures`

Suggested acceptance criteria:

- `_normalize_provider_hits(None)` raises `RetrievalContractError`.
- `execute_retrieval_task()` emits a failed retrieval task with `error_kind=malformed_response`, `exception=RetrievalContractError`, `retryable=false`, and attempt-count metadata.
- `fetch_retrieval_contents()` applies the same malformed-response rule for `None`.
- Deterministic tests cover the `None` search/content response paths without live Exa calls.

## Scope Boundaries

This audit did not change runtime code, notebooks, dependencies, or fixture data. It did not make live Exa calls and did not start issue `#8`, `#10`, `#12`, or `#14` work.

## Validation

- `python -m pytest tests/test_retrieval_contracts.py tests/test_exa_client.py tests/test_exa_adapter_contract.py tests/test_citation_verify.py -q` -> `40 passed in 8.99s`.
- `python -m pytest -q` -> `331 passed in 22.97s`.
- `python -m war_room --verify --release-candidate issue-7-closure-sanity-audit` -> passed; embedded `pytest -q` reported `331 passed in 13.33s`; verify manifest written under `runs/verify/2026-05-13_issue-7-closure-sanity-audit_20260513t194018z.json`.
