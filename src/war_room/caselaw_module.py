"""Case law search module.

Runs caselaw queries via Exa. Organizes results by legal issue.
Prefers CourtListener / official courts / scholar.google.com.
Avoids Westlaw/Lexis as primary sources.
"""

from __future__ import annotations

import html
import re
from typing import Any, Mapping, Sequence
from urllib.parse import urlparse

from war_room.cache_io import cache_get, cached_call
from war_room.retrieval import (
    RetrievalProvider,
    RetrievalSearchRequest,
    execute_retrieval_task,
    notebook_run_id_from_intake,
    query_spec_to_retrieval_task,
)
from war_room.models import CaseIntake, QuerySpec, caselaw_pack_to_payload
from war_room.query_plan import generate_query_plan, query_plan_for_module
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

_COMMENTARY_TITLE_TERMS = (
    "blog",
    "faq",
    "guide",
    "how to",
    "in the wake of",
    "jd supra",
    "lessons",
    "must know",
    "overview",
    "state of",
    "what homeowners must know",
)


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


def _looks_like_commentary_title(name: str) -> bool:
    normalized = name.lower()
    if " | " in name or " - " in name:
        return True
    return any(term in normalized for term in _COMMENTARY_TITLE_TERMS)


def _is_case_like(result: dict) -> bool:
    """Conservative guard: keep only results that look like actual cases.

    Rules:
    - Case-name pattern is sufficient only on trusted legal/court hosts or when the
      title does not look like commentary.
    - Citation-only results must also come from a known legal/court host.
    """
    name = result.get("name", "") or result.get("title", "") or ""
    url = (result.get("url") or "").strip()
    legal_host = bool(url) and _is_legal_case_host(url)
    source_class = result.get("source_class")

    if source_class in {"commentary", "news"}:
        return False

    if _CASE_NAME_RE.search(name):
        if legal_host:
            return True
        return not _looks_like_commentary_title(name)

    citation = (result.get("citation") or "").strip()
    if citation and legal_host and not _looks_like_commentary_title(name):
        return True

    return False


def _normalized_result_url(url: str) -> str:
    return url.strip().rstrip("/").lower()


def _normalize_case_citation(citation: str) -> str:
    return " ".join((citation or "").lower().split())


def _normalize_case_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (name or "").lower()).strip()


def _case_dedupe_key(case_info: dict[str, Any]) -> tuple[str, str]:
    citation = _normalize_case_citation(case_info.get("citation", ""))
    if citation:
        return ("citation", citation)
    url = _normalized_result_url(case_info.get("url", ""))
    if url:
        return ("url", url)
    return ("name", _normalize_case_name(case_info.get("name", "")))


def _dedupe_case_results(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Collapse duplicate authorities by citation first, then normalized URL/name."""
    deduped: dict[tuple[str, str], dict[str, Any]] = {}
    order: list[tuple[str, str]] = []

    for result in results:
        url = (result.get("url") or "").strip()
        if not url:
            continue
        score = score_url(url, result.get("title", ""))
        if score["tier"] == "paywalled":
            continue
        enriched = {**result, "_score": score}
        case_info = _extract_case_info(enriched)
        enriched["_case_info"] = case_info
        key = _case_dedupe_key(case_info if _is_case_like(case_info) else {"url": url, "name": result.get("title", "")})
        if key not in deduped:
            deduped[key] = enriched
            order.append(key)
            continue
        if _case_result_priority(enriched) < _case_result_priority(deduped[key]):
            deduped[key] = enriched

    return [deduped[key] for key in order]


def build_caselaw_pack(
    intake: CaseIntake,
    client: RetrievalProvider | None,
    *,
    query_plan: Sequence[Mapping[str, Any] | QuerySpec] | None = None,
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
                return _normalize_caselaw_pack(cached, intake=intake)
        return _normalize_caselaw_pack(
            _empty_caselaw_pack(
                "No Exa client available and no cached case-law pack found.",
            ),
            intake=intake,
        )

    def _fetch() -> dict[str, Any]:
        queries = _caselaw_queries(intake, query_plan)
        all_results: list[dict] = []
        retrieval_tasks = []
        run_events = []
        warnings: list[str] = []
        run_id = notebook_run_id_from_intake(intake)
        stage_id = f"{run_id}:caselaw"

        for index, query in enumerate(queries, 1):
            task = query_spec_to_retrieval_task(
                query,
                run_id=run_id,
                stage_id=stage_id,
                provider=client.provider_name,
                retrieval_task_id=f"{stage_id}:{query.category}:{index}",
            )
            execution = execute_retrieval_task(
                client,
                RetrievalSearchRequest(
                    task=task,
                    k=5,
                    include_domains=query.preferred_domains,
                    exclude_domains=CASELAW_EXCLUDE_DOMAINS,
                ),
            )
            retrieval_tasks.append(execution.task)
            run_events.extend(execution.run_events)
            if execution.warning:
                warnings.append(execution.warning)
            for hit in execution.hits:
                hit["category"] = query.category
            all_results.extend(execution.hits)

        payload = _assemble_pack(intake, all_results)
        if warnings:
            payload["warnings"] = list(dict.fromkeys((payload.get("warnings") or []) + warnings))
        payload["retrieval_tasks"] = retrieval_tasks
        payload["run_events"] = run_events
        return caselaw_pack_to_payload(payload)

    pack = cached_call(
        case_key,
        _fetch,
        cache_samples_dir=cache_samples_dir,
        cache_dir=cache_dir,
        use_cache=use_cache,
    )
    return _normalize_caselaw_pack(pack, intake=intake)


def _caselaw_queries(
    intake: CaseIntake,
    query_plan: Sequence[Mapping[str, Any] | QuerySpec] | None,
) -> list[QuerySpec]:
    if query_plan is not None:
        return query_plan_for_module(query_plan, "caselaw")
    return [query for query in generate_query_plan(intake) if query.module == "caselaw"]


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
    scored = _dedupe_case_results(results)
    scored.sort(key=_case_result_priority)

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
    supporting_sources: list[dict[str, Any]] = []
    seen_supporting_urls: set[str] = set()
    for result in scored:
        category = result.get("category", "general")
        issue_label = issue_map.get(category, category.replace("_", " ").title())
        case_info = result.get("_case_info") or _extract_case_info(result)
        if _is_case_like(case_info):
            issues_dict.setdefault(issue_label, []).append(result)
            continue
        if result["url"] not in seen_supporting_urls:
            seen_supporting_urls.add(result["url"])
            supporting_sources.append(result)

    # Build issues list, limit to 6-12 cases total
    issues = []
    total_cases = 0
    used_case_urls: set[str] = set()
    for issue_label, issue_results in issues_dict.items():
        if total_cases >= 12:
            break
        cases = []
        for result in issue_results[:6]:  # scan up to 6, keep max 3
            if total_cases >= 12 or len(cases) >= 3:
                break
            case_info = result.get("_case_info") or _extract_case_info(result)
            if not _is_case_like(case_info):
                continue
            cases.append(case_info)
            used_case_urls.add(case_info["url"])
            total_cases += 1

        if cases:
            issues.append({
                "issue": issue_label,
                "cases": cases,
                "notes": [_issue_note(issue_label, intake)],
            })

    # Sources
    sources = []
    source_candidates = [result for result in scored if result["url"] in used_case_urls]
    source_candidates.extend(supporting_sources)
    seen_source_urls: set[str] = set()
    for result in source_candidates:
        if result["url"] in seen_source_urls:
            continue
        seen_source_urls.add(result["url"])
        score = result["_score"]
        sources.append({
            "title": result.get("title", ""),
            "url": result["url"],
            "badge": score["badge"],
            "reason": f"{score['label']} - {score['source_class_label']}",
            "source_class": score["source_class"],
            "is_primary_authority": score["is_primary_authority"],
        })
        if len(sources) >= 15:
            break

    return caselaw_pack_to_payload({
        "module": "caselaw",
        "issues": issues,
        "sources": sources,
    })


def _normalize_caselaw_pack(
    payload: Mapping[str, Any],
    *,
    intake: CaseIntake | None = None,
) -> dict[str, Any]:
    """Clean cached/live caselaw payloads before downstream read models consume them."""
    pack = caselaw_pack_to_payload(payload)
    issues = []
    kept_case_urls: set[str] = set()
    for issue in pack["issues"]:
        cases = []
        for case in issue.get("cases", []):
            normalized = _normalize_case_entry(case)
            if not _is_case_like(normalized):
                continue
            cases.append(normalized)
            if normalized.get("url"):
                kept_case_urls.add(normalized["url"])
        if not cases:
            continue
        issues.append(
            {
                **issue,
                "cases": cases,
            }
        )
    issue_labels = [issue["issue"] for issue in issues]

    sources = []
    seen_source_urls: set[str] = set()
    for source in pack["sources"]:
        url = source.get("url", "")
        if not url or url in seen_source_urls:
            continue
        if url not in kept_case_urls and not _is_high_value_caselaw_support_source(
            source,
            intake=intake,
            issue_labels=issue_labels,
            strong_case_count=len(kept_case_urls),
        ):
            continue
        seen_source_urls.add(url)
        sources.append(source)

    return caselaw_pack_to_payload(
        {
            **pack,
            "issues": issues,
            "sources": sources,
        }
    )


def _case_result_priority(result: dict[str, Any]) -> tuple[int, int, int, int, int, int, str]:
    """Prefer primary-law authorities with citations over commentary and news."""
    tier_rank = {"official": 0, "professional": 1, "unvetted": 2, "paywalled": 3}
    source_class_rank = {
        "court_opinion": 0,
        "statute_regulation": 1,
        "government_guidance": 2,
        "commentary": 3,
        "news": 4,
        "other": 5,
    }
    case_info = result.get("_case_info") or _extract_case_info(result)
    title = (case_info.get("name", "") or "").lower()

    primary_authority_penalty = 0 if result["_score"].get("is_primary_authority") else 1
    source_class_penalty = source_class_rank.get(result["_score"].get("source_class"), 9)
    legal_host_bonus = 0 if _is_legal_case_host(result["url"]) else 1
    citation_bonus = 0 if case_info.get("citation") else 1
    metadata_penalty = _thin_case_metadata_penalty(case_info)
    commentary_penalty = 1 if _looks_like_commentary_title(case_info.get("name", "")) else 0

    return (
        primary_authority_penalty,
        source_class_penalty,
        tier_rank.get(result["_score"]["tier"], 9),
        legal_host_bonus,
        commentary_penalty,
        citation_bonus,
        metadata_penalty,
        title,
    )


def _normalize_case_entry(case: Mapping[str, Any]) -> dict[str, Any]:
    score = score_url(case.get("url", ""), case.get("name", ""))
    name = _clean_case_text(case.get("name", ""))
    citation = _clean_case_text(case.get("citation", ""))
    court = _clean_case_court(case.get("court", ""))
    year = _clean_case_text(case.get("year", "")) or _extract_case_year(
        " ".join(
            str(part or "")
            for part in (
                case.get("year"),
                case.get("court"),
                case.get("one_liner"),
                case.get("name"),
            )
        )
    )
    return {
        **case,
        "name": name,
        "citation": citation,
        "court": court,
        "year": year,
        "one_liner": _clean_case_one_liner(
            case.get("one_liner", ""),
            case_name=name,
            citation=citation,
        ),
        "source_class": case.get("source_class") or score["source_class"],
        "source_tier": case.get("source_tier") or score["tier"],
        "is_primary_authority": bool(
            case.get("is_primary_authority", score["is_primary_authority"])
        ),
    }


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
    year_match = re.search(r"\b(?:19|20)\d{2}\b", text[:500])
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
        "source_class": score["source_class"],
        "source_tier": score["tier"],
        "is_primary_authority": score["is_primary_authority"],
    }


def _clean_case_text(value: str) -> str:
    text = html.unescape(str(value or ""))
    text = text.replace("\r", " ").replace("\n", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _clean_case_court(value: str) -> str:
    text = _clean_case_text(value)
    text = re.split(r"\bDate published\b", text, maxsplit=1, flags=re.IGNORECASE)[0]
    text = re.sub(r"\bDate publi\w*$", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\bDat$", "", text, flags=re.IGNORECASE)
    text = re.sub(r",\s*[A-Z]$", "", text)
    if text.isupper():
        text = text.title()
    return text.strip(" -,:;")


def _clean_case_one_liner(
    value: str,
    *,
    case_name: str,
    citation: str,
) -> str:
    text = _clean_case_text(value)
    text = re.sub(r"\|\s*Casetext Search\s*\+\s*Citator", "", text, flags=re.IGNORECASE)
    if "Citing Cases" in text:
        candidate = text.split("Citing Cases", 1)[1]
        candidate = re.sub(r"^\s*\[[^\]]+\]\s*", "", candidate)
        candidate = _clean_case_text(candidate)
        if candidate and not candidate.startswith("["):
            text = candidate
    case_name_without_citation = case_name
    if citation:
        case_name_without_citation = re.sub(
            rf",?\s*{re.escape(citation)}$",
            "",
            case_name_without_citation,
            flags=re.IGNORECASE,
        ).strip()
    if case_name:
        text = re.sub(rf"^{re.escape(case_name)}\s*", "", text, flags=re.IGNORECASE)
    if case_name_without_citation:
        text = re.sub(
            rf"^{re.escape(case_name_without_citation)}\s*",
            "",
            text,
            flags=re.IGNORECASE,
        )
    if citation:
        text = re.sub(rf"^{re.escape(citation)}\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^#+\s*", "", text)
    text = re.sub(r"^Citing Cases\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^\s*\[[^\]]+\]\s*", "", text)
    if text.startswith("["):
        return ""
    text = text.lstrip(" ,.;:-|")
    return text[:200]


def _extract_case_year(value: str) -> str:
    match = re.search(r"\b(?:19|20)\d{2}\b", value)
    return match.group(0) if match else ""


def _is_high_value_caselaw_support_source(
    source: Mapping[str, Any],
    *,
    intake: CaseIntake | None = None,
    issue_labels: Sequence[str] = (),
    strong_case_count: int = 0,
) -> bool:
    title = source.get("title", "") or ""
    url = source.get("url", "") or ""
    score = score_url(source.get("url", ""), title)
    if score["source_class"] in {"commentary", "news", "other"}:
        return False
    if _looks_like_commentary_title(title):
        return False
    if strong_case_count >= 4 and intake is not None:
        if not _is_on_point_support_source(title, url, intake, issue_labels):
            return False
    return True


def _is_on_point_support_source(
    title: str,
    url: str,
    intake: CaseIntake,
    issue_labels: Sequence[str],
) -> bool:
    haystack = f"{title} {url}".lower()
    issue_tokens = {
        token
        for label in issue_labels
        for token in re.findall(r"[a-z]{4,}", label.lower())
        if token not in {"issue", "coverage", "denial", "law"}
    }
    state_tokens = {
        intake.state.lower(),
        "florida" if intake.state == "FL" else intake.state.lower(),
        intake.county.lower(),
        *[token for token in re.findall(r"[a-z]{4,}", intake.carrier.lower()) if token not in {"property", "insurance"}],
        *[token for token in re.findall(r"[a-z]{4,}", intake.event_name.lower())],
    }
    relevant_tokens = issue_tokens | state_tokens
    return any(token in haystack for token in relevant_tokens)


def _thin_case_metadata_penalty(case_info: dict[str, Any]) -> int:
    penalty = 0
    if not case_info.get("citation"):
        penalty += 2
    if not case_info.get("court"):
        penalty += 1
    if not case_info.get("year"):
        penalty += 1
    return penalty


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
