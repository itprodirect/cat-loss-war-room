"""Citation spot-check module.

For each case citation, runs ONE Exa search to check if it appears
on a court/legal site. Reports confidence level, not verification.

Mandatory disclaimer: KeyCite/Shepardize before reliance.
"""

from __future__ import annotations

from typing import Any

from war_room.cache_io import cached_call
from war_room.exa_client import BudgetExhausted, ExaClient
from war_room.models import citation_verify_pack_to_payload
from war_room.source_scoring import score_url


DISCLAIMER = (
    "CITATION SPOT-CHECK ONLY - These are confidence signals, not verification. "
    "KeyCite / Shepardize every citation before reliance."
)

MAX_CHECKS = 6  # Cap citation checks per run to conserve Exa budget


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
    client: ExaClient,
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

    checks = []
    for case in all_cases[:max_checks]:
        name = case["name"]
        citation = case["citation"]
        search_term = f"{name} {citation}".strip()

        check_key = f"{case_key_base}__{search_term}"

        def _verify(q=search_term) -> dict[str, Any]:
            return _do_check(q, client)

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
        }
    )


# Tier priority: lower = better
_TIER_RANK = {"official": 0, "professional": 1, "unvetted": 2, "paywalled": 3}


def _do_check(query: str, client: ExaClient) -> dict[str, Any]:
    """Run a single citation spot-check."""
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

    # Score all hits and pick the best tier
    scored_hits = []
    for hit in hits:
        score = score_url(hit["url"])
        scored_hits.append((hit, score))
    scored_hits.sort(key=lambda item: _TIER_RANK.get(item[1]["tier"], 9))

    best_hit, best_score = scored_hits[0]

    if best_score["tier"] == "official":
        return {
            "status": "verified",
            "badge": "verified",
            "source_url": best_hit["url"],
            "note": f"Found on official source: {best_score['hostname']}",
        }
    if best_score["tier"] == "professional":
        return {
            "status": "uncertain",
            "badge": "warning",
            "source_url": best_hit["url"],
            "note": f"Found on professional source: {best_score['hostname']} - verify independently",
        }

    return {
        "status": "uncertain",
        "badge": "warning",
        "source_url": best_hit["url"],
        "note": f"Found on {best_score['hostname']} - unvetted source, verify independently",
    }
