"""Citation spot-check module.

For each case citation, runs ONE Exa search to check if it appears
on a court/legal site. Reports confidence level, not verification.

Mandatory disclaimer: KeyCite/Shepardize before reliance.
"""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse

from war_room.cache_io import cached_call
from war_room.exa_client import BudgetExhausted
from war_room.retrieval import (
    RetrievalProvider,
    RetrievalSearchRequest,
    execute_retrieval_task,
    query_spec_to_retrieval_task,
)
from war_room.models import QuerySpec, citation_verify_pack_to_payload
from war_room.source_scoring import score_url


DISCLAIMER = (
    "CITATION SPOT-CHECK ONLY - These are confidence signals, not verification. "
    "KeyCite / Shepardize every citation before reliance."
)

MAX_CHECKS = 6  # Cap citation checks per run to conserve Exa budget

_LEGAL_HOST_SUFFIXES = {
    "casetext.com",
    "courtlistener.com",
    "flcourts.gov",
    "law.cornell.edu",
    "justia.com",
    "leagle.com",
    "scholar.google.com",
    "uscourts.gov",
}

_STOP_WORDS = {"co", "corp", "corporation", "company", "inc", "insurance", "the", "v", "vs"}


def _extract_cases(caselaw_pack: Any) -> list[dict[str, str]]:
    """Extract name/citation pairs from either dict-like or typed caselaw payloads."""
    if isinstance(caselaw_pack, dict):
        issues = caselaw_pack.get("issues", [])
    else:
        issues = getattr(caselaw_pack, "issues", [])

    cases: list[dict[str, str]] = []
    for issue in issues:
        if isinstance(issue, dict):
            issue_cases = issue.get("cases", [])
        else:
            issue_cases = getattr(issue, "cases", [])

        for case in issue_cases:
            if isinstance(case, dict):
                name = (case.get("name") or "").strip()
                citation = (case.get("citation") or "").strip()
            else:
                name = (getattr(case, "name", "") or "").strip()
                citation = (getattr(case, "citation", "") or "").strip()

            if citation and name:
                cases.append({"name": name, "citation": citation})

    return cases


def spot_check_citations(
    caselaw_pack: dict[str, Any],
    client: RetrievalProvider,
    *,
    use_cache: bool = True,
    cache_dir: str = "cache",
    cache_samples_dir: str = "cache_samples",
    max_checks: int = MAX_CHECKS,
) -> dict[str, Any]:
    """Spot-check citations in a caselaw pack.

    Returns dict with: module, disclaimer, checks, summary.
    """
    case_key_base = "citecheck"
    all_cases = _extract_cases(caselaw_pack)
    run_id = _run_id_from_caselaw_pack(caselaw_pack)
    stage_id = f"{run_id}:citation_verify"

    checks = []
    retrieval_tasks = []
    run_events = []
    for index, case in enumerate(all_cases[:max_checks], 1):
        name = case["name"]
        citation = case["citation"]
        search_term = f"{name} {citation}".strip()
        task = query_spec_to_retrieval_task(
            QuerySpec(
                module="citation_verify",
                query=search_term,
                category="citation_check",
            ),
            run_id=run_id,
            stage_id=stage_id,
            provider=client.provider_name,
            retrieval_task_id=f"{stage_id}:citation_check:{index}",
        )

        check_key = f"{case_key_base}__{search_term}"

        def _verify(
            q=search_term,
            case_name=name,
            cite=citation,
            retrieval_task=task,
        ) -> dict[str, Any]:
            return _do_check(q, client, retrieval_task=retrieval_task, case_name=case_name, citation=cite)

        result = cached_call(
            check_key,
            _verify,
            cache_samples_dir=cache_samples_dir,
            cache_dir=cache_dir,
            use_cache=use_cache,
        )
        result["case_name"] = name
        result["citation"] = citation
        checks.append(result)
        retrieval_tasks.append(result.pop("_retrieval_task", None))
        run_events.extend(result.pop("_run_events", []))

    retrieval_tasks = [task for task in retrieval_tasks if task is not None]

    # Summary counts
    verified = sum(1 for c in checks if c["status"] == "verified")
    uncertain = sum(1 for c in checks if c["status"] == "uncertain")
    not_found = sum(1 for c in checks if c["status"] == "not_found")

    return citation_verify_pack_to_payload(
        {
            "module": "citation_verify",
            "disclaimer": DISCLAIMER,
            "checks": checks,
            "summary": {
                "total": len(checks),
                "verified": verified,
                "uncertain": uncertain,
                "not_found": not_found,
            },
            "retrieval_tasks": retrieval_tasks,
            "run_events": run_events,
        }
    )


# Tier priority: lower = better
_TIER_RANK = {"official": 0, "professional": 1, "unvetted": 2, "paywalled": 3}


def _do_check(
    query: str,
    client: RetrievalProvider,
    *,
    retrieval_task=None,
    case_name: str | None = None,
    citation: str | None = None,
) -> dict[str, Any]:
    """Run a single citation spot-check."""
    run_events = []
    task = retrieval_task
    hits = []
    if retrieval_task is not None:
        execution = execute_retrieval_task(
            client,
            RetrievalSearchRequest(task=retrieval_task, k=5),
        )
        task = execution.task
        run_events = execution.run_events
        hits = execution.hits
        if task.status == "failed":
            return {
                "status": "uncertain",
                "badge": "warning",
                "source_url": None,
                "note": execution.warning or "Search error - could not verify",
                "_retrieval_task": task,
                "_run_events": run_events,
            }
        if not hits:
            return {
                "status": "not_found",
                "badge": "not_found",
                "source_url": None,
                "note": execution.warning or "No results found",
                "_retrieval_task": task,
                "_run_events": run_events,
            }
    else:
        try:
            hits = client.search(query, k=5)
        except BudgetExhausted:
            return {
                "status": "uncertain",
                "badge": "warning",
                "source_url": None,
                "note": "Budget exhausted - could not verify",
            }
        except Exception as exc:
            return {
                "status": "uncertain",
                "badge": "warning",
                "source_url": None,
                "note": f"Search error - could not verify: {type(exc).__name__}",
            }

        if not hits:
            return {
                "status": "not_found",
                "badge": "not_found",
                "source_url": None,
                "note": "No results found",
            }

    scored_hits = []
    for hit in hits:
        score = score_url(hit["url"])
        scored_hits.append((hit, score, _match_strength(hit, case_name, citation)))

    if citation or case_name:
        scored_hits = [item for item in scored_hits if item[2][0] > 0 or item[2][1] > 0]
        if not scored_hits:
            result = {
                "status": "not_found",
                "badge": "not_found",
                "source_url": None,
                "note": "No relevant citation match found",
            }
            if task is not None:
                result["_retrieval_task"] = task
                result["_run_events"] = run_events
            return result

    scored_hits.sort(key=lambda item: _hit_priority(item[0], item[1], item[2]))

    best_hit, best_score, best_match = scored_hits[0]

    result: dict[str, Any]
    if best_score["tier"] == "official":
        result = {
            "status": "verified",
            "badge": "verified",
            "source_url": best_hit["url"],
            "note": f"Found on official source: {best_score['hostname']}",
        }
    elif best_score["tier"] == "professional":
        detail = "citation-aligned result" if best_match[0] > 0 else "professional source"
        result = {
            "status": "uncertain",
            "badge": "warning",
            "source_url": best_hit["url"],
            "note": f"Found on {detail}: {best_score['hostname']} - verify independently",
        }
    else:
        result = {
            "status": "uncertain",
            "badge": "warning",
            "source_url": best_hit["url"],
            "note": f"Found on {best_score['hostname']} - unvetted source, verify independently",
        }
    if task is not None:
        result["_retrieval_task"] = task
        result["_run_events"] = run_events
    return result


def _hit_priority(hit: dict[str, Any], score: dict[str, Any], match: tuple[int, int, int]) -> tuple[int, int, int, int, str]:
    """Prefer citation-aligned legal hosts over generic domain-tier ranking alone."""
    citation_match, name_match, legal_host = match
    title = (hit.get("title", "") or "").lower()
    return (
        0 if citation_match else 1,
        0 if legal_host else 1,
        _TIER_RANK.get(score["tier"], 9),
        0 if name_match else 1,
        title,
    )


def _match_strength(hit: dict[str, Any], case_name: str | None, citation: str | None) -> tuple[int, int, int]:
    """Return citation match, case-name match, and legal-host signals for a hit."""
    combined_text = " ".join(
        [
            hit.get("title", "") or "",
            hit.get("snippet", "") or "",
            (hit.get("text", "") or "")[:1200],
            hit.get("url", "") or "",
        ]
    ).lower()

    citation_match = 0
    if citation and citation.lower() in combined_text:
        citation_match = 1

    name_match = 0
    if case_name:
        tokens = _significant_tokens(case_name)
        if tokens:
            matched = sum(1 for token in tokens if token in combined_text)
            if matched >= min(2, len(tokens)):
                name_match = 1

    legal_host = 1 if _is_legal_host(hit.get("url", "") or "") else 0
    return (citation_match, name_match, legal_host)


def _significant_tokens(case_name: str) -> list[str]:
    cleaned = re.sub(r"[^a-z0-9 ]+", " ", case_name.lower())
    tokens = [token for token in cleaned.split() if len(token) > 2 and token not in _STOP_WORDS]
    return tokens[:4]


def _is_legal_host(url: str) -> bool:
    try:
        hostname = (urlparse(url).hostname or "").lower().removeprefix("www.")
    except Exception:
        return False

    if not hostname:
        return False
    if hostname.endswith(".gov"):
        return True
    return any(hostname == suffix or hostname.endswith("." + suffix) for suffix in _LEGAL_HOST_SUFFIXES)


def _run_id_from_caselaw_pack(caselaw_pack: Any) -> str:
    if isinstance(caselaw_pack, dict):
        retrieval_tasks = caselaw_pack.get("retrieval_tasks", []) or []
    else:
        retrieval_tasks = getattr(caselaw_pack, "retrieval_tasks", []) or []
    if retrieval_tasks:
        first = retrieval_tasks[0]
        if isinstance(first, dict):
            run_id = first.get("run_id")
        else:
            run_id = getattr(first, "run_id", None)
        if run_id:
            return run_id
    return "run-notebook-citation-verify"
