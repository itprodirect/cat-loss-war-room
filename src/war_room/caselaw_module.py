"""Case law search module.

Runs caselaw queries via Exa. Organizes results by legal issue.
Prefers CourtListener / official courts / scholar.google.com.
Avoids Westlaw/Lexis as primary sources.
"""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse

from war_room.cache_io import cache_get, cached_call
from war_room.exa_client import ExaClient
from war_room.models import caselaw_pack_to_payload
from war_room.query_plan import CaseIntake, generate_query_plan
from war_room.source_scoring import PAYWALLED_DOMAINS, score_url

CASELAW_EXCLUDE_DOMAINS = list(PAYWALLED_DOMAINS)

_CASE_NAME_RE = re.compile(r"(?:^|\s)(v\.|vs\.|in re|ex rel\.)(?:\s|$)", re.IGNORECASE)

LEGAL_CASE_HOST_SUFFIXES = {
    "casetext.com",
    "courtlistener.com",
    "scholar.google.com",
    "law.cornell.edu",
    "justia.com",
    "leagle.com",
}


def _is_legal_case_host(url: str) -> bool:
    """Return True when URL host is a known case-law host or official .gov court host."""
    try:
        hostname = (urlparse(url).hostname or "").lower().removeprefix("www.")
    except Exception:
        return False

    if not hostname:
        return False
    if hostname.endswith(".gov"):
        return True

    for suffix in LEGAL_CASE_HOST_SUFFIXES:
        if hostname == suffix or hostname.endswith("." + suffix):
            return True
    return False


def _is_case_like(result: dict) -> bool:
    """Conservative guard: keep only results that look like actual cases.

    Rules:
    - Case-name pattern is sufficient (e.g., "Smith v. Jones").
    - Citation-only results must also come from a known legal/court host.
    """
    name = result.get("name", "") or result.get("title", "") or ""
    if _CASE_NAME_RE.search(name):
        return True

    citation = (result.get("citation") or "").strip()
    if citation:
        url = (result.get("url") or "").strip()
        if url and _is_legal_case_host(url):
            return True

    return False


def build_caselaw_pack(
    intake: CaseIntake,
    client: ExaClient | None,
    *,
    use_cache: bool = True,
    cache_dir: str = "cache",
    cache_samples_dir: str = "cache_samples",
) -> dict[str, Any]:
    """Build a case law pack organized by legal issue."""
    case_key = f"caselaw__{intake.event_name}__{intake.carrier}__{intake.state}"

    # Graceful fallback: no client available. Prefer cache, then return safe empty payload.
    if client is None:
        if use_cache:
            cached = cache_get(case_key, cache_samples_dir)
            if cached is None:
                cached = cache_get(case_key, cache_dir)
            if cached is not None:
                return cached
        return _empty_caselaw_pack(
            "No Exa client available and no cached case-law pack found.",
        )

    def _fetch() -> dict[str, Any]:
        queries = [q for q in generate_query_plan(intake) if q.module == "caselaw"]
        all_results: list[dict] = []

        for query in queries:
            hits = client.search(
                query.query,
                k=5,
                include_domains=query.preferred_domains or None,
                exclude_domains=CASELAW_EXCLUDE_DOMAINS,
            )
            for hit in hits:
                hit["category"] = query.category
            all_results.extend(hits)

        return _assemble_pack(intake, all_results)

    return cached_call(
        case_key,
        _fetch,
        cache_samples_dir=cache_samples_dir,
        cache_dir=cache_dir,
        use_cache=use_cache,
    )


def _empty_caselaw_pack(reason: str) -> dict[str, Any]:
    """Return a structured empty caselaw payload when live retrieval is unavailable."""
    return caselaw_pack_to_payload({
        "module": "caselaw",
        "issues": [],
        "sources": [],
        "warnings": [reason],
    })


def _assemble_pack(
    intake: CaseIntake,
    results: list[dict],
) -> dict[str, Any]:
    """Organize results by legal issue."""
    # Deduplicate
    seen: set[str] = set()
    unique: list[dict] = []
    for result in results:
        if result["url"] and result["url"] not in seen:
            seen.add(result["url"])
            unique.append(result)

    # Score and filter out paywalled
    scored = []
    for result in unique:
        score = score_url(result["url"])
        if score["tier"] != "paywalled":
            scored.append({**result, "_score": score})

    # Map categories to legal issues
    issue_map = {
        "carrier_precedent": f"{intake.carrier} Precedent",
        "coverage_law": "Coverage / Denial Law",
        "concurrent_causation": "Concurrent Causation Doctrine",
        "bad_faith_precedent": "Bad Faith Standards",
        "bad_faith_law": "Bad Faith - Duty to Investigate",
        "underpayment_law": "Underpayment / Appraisal",
        "coverage_issue": "Coverage Issue",
    }

    # Group by issue
    issues_dict: dict[str, list[dict]] = {}
    for result in scored:
        category = result.get("category", "general")
        issue_label = issue_map.get(category, category.replace("_", " ").title())
        issues_dict.setdefault(issue_label, []).append(result)

    # Build issues list, limit to 6-12 cases total
    issues = []
    total_cases = 0
    for issue_label, issue_results in issues_dict.items():
        if total_cases >= 12:
            break
        cases = []
        for result in issue_results[:6]:  # scan up to 6, keep max 3
            if total_cases >= 12 or len(cases) >= 3:
                break
            case_info = _extract_case_info(result)
            if not _is_case_like(case_info):
                continue
            cases.append(case_info)
            total_cases += 1

        if cases:
            issues.append({
                "issue": issue_label,
                "cases": cases,
                "notes": [_issue_note(issue_label, intake)],
            })

    # Sources
    sources = []
    for result in scored[:15]:
        score = result["_score"]
        sources.append({
            "title": result.get("title", ""),
            "url": result["url"],
            "badge": score["badge"],
            "reason": score["label"],
        })

    return caselaw_pack_to_payload({
        "module": "caselaw",
        "issues": issues,
        "sources": sources,
    })


def _extract_case_info(result: dict) -> dict[str, Any]:
    """Extract case name, citation, court, year from a search result."""
    title = result.get("title", "") or ""
    text = result.get("text", "") or ""
    snippet = result.get("snippet", "") or ""
    score = result["_score"]

    # Try to extract case name from title
    case_name = title.strip()

    # Try to find a citation pattern (e.g., "123 So. 3d 456" or "2024 WL 12345")
    citation = ""
    cite_patterns = [
        r"\d+\s+(?:So\.|F\.|S\.W\.|N\.E\.|N\.W\.|P\.|A\.)\s*\d*d?\s+\d+",
        r"\d{4}\s+WL\s+\d+",
        r"\d+\s+F\.\s*(?:Supp|App)\.\s*\d*d?\s+\d+",
    ]
    for pattern in cite_patterns:
        match = re.search(pattern, text[:1000])
        if match:
            citation = match.group(0)
            break

    # Try to extract court
    court = ""
    court_patterns = [
        r"(?:Supreme Court|Circuit Court|District Court|Court of Appeal)[^.]{0,30}",
        r"(?:Fla\.|Cal\.|Tex\.|N\.Y\.)\s*(?:App\.|Dist\.)?\s*\d{4}",
    ]
    for pattern in court_patterns:
        match = re.search(pattern, text[:1000], re.IGNORECASE)
        if match:
            court = match.group(0).strip()
            break

    # Year
    year = ""
    year_match = re.search(r"\b(19|20)\d{2}\b", text[:500])
    if year_match:
        year = year_match.group(0)

    # One-liner from snippet
    one_liner = snippet[:200].strip()
    if not one_liner:
        one_liner = text[:200].strip()

    return {
        "name": case_name,
        "citation": citation,
        "court": court,
        "year": year,
        "one_liner": one_liner,
        "url": result["url"],
        "badge": score["badge"],
    }


def _issue_note(issue_label: str, intake: CaseIntake) -> str:
    """Generate a contextual note for a legal issue."""
    notes = {
        "Concurrent Causation Doctrine": (
            f"Key issue in {intake.state} hurricane cases - "
            "determines whether wind or water exclusion controls"
        ),
        "Bad Faith Standards": (
            f"Review {intake.state} bad faith standards - "
            "statutory penalties and fee-shifting may apply"
        ),
        "Bad Faith - Duty to Investigate": (
            f"Failure to adequately investigate is a common bad faith theory in {intake.state}"
        ),
    }
    return notes.get(
        issue_label,
        f"Review for applicability to {intake.carrier} / {intake.event_name}",
    )
