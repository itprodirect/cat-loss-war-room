"""Carrier playbook intel module.

Runs carrier_docs queries via Exa. Builds a document pack with
denial patterns, regulatory signals, and rebuttal angles.
"""

from __future__ import annotations

import re
from typing import Any, Mapping, Sequence

from war_room.cache_io import cache_get, cached_call
from war_room.retrieval import (
    RetrievalProvider,
    RetrievalSearchRequest,
    execute_retrieval_task,
    notebook_run_id_from_intake,
    query_spec_to_retrieval_task,
)
from war_room.models import CaseIntake, QuerySpec, carrier_doc_pack_to_payload
from war_room.query_plan import generate_query_plan, query_plan_for_module
from war_room.source_scoring import score_url

_HIGH_VALUE_DOC_TERMS = (
    "complaint",
    "consent",
    "exam",
    "final report",
    "guideline",
    "handbook",
    "manual",
    "market conduct",
    "memorandum",
    "order",
    "report",
    "settlement",
)

_LOW_VALUE_PAGE_TITLES = (
    "about us",
    "consumers",
    "consumers - floir",
    "contact us",
    "contact us - floir",
    "organization and operation",
    "organization and operation - floir",
)

_LOW_VALUE_PAGE_URL_TERMS = (
    "/about-us/contact-us",
    "/about-us/organization-and-operation",
    "/consumers",
)

_LOW_SIGNAL_SNIPPET_TERMS = (
    "continue to site",
    "skip to content",
)

_LOW_VALUE_SUPPORT_TITLES = (
    "what to expect after reporting your claim",
)

_CARRIER_DOC_TYPE_RANK = {
    "DOI/Regulatory Complaint": 0,
    "Claims Handling Guideline": 1,
    "Regulatory Action": 2,
    "Bad Faith Signal": 3,
    "Denial Pattern Analysis": 4,
    "General": 5,
}


def build_carrier_doc_pack(
    intake: CaseIntake,
    client: RetrievalProvider | None,
    *,
    query_plan: Sequence[Mapping[str, Any] | QuerySpec] | None = None,
    use_cache: bool = True,
    cache_dir: str = "cache",
    cache_samples_dir: str = "cache_samples",
) -> dict[str, Any]:
    """Build a carrier document pack for the case."""
    case_key = f"carrier__{intake.carrier}__{intake.event_name}__{intake.state}"

    # Graceful fallback: no client available. Prefer cache, then return safe empty payload.
    if client is None:
        if use_cache:
            cached = cache_get(case_key, cache_samples_dir)
            if cached is None:
                cached = cache_get(case_key, cache_dir)
            if cached is not None:
                return _normalize_carrier_pack(cached, intake)
        return _normalize_carrier_pack(
            _empty_carrier_pack(
                intake,
                "No Exa client available and no cached carrier pack found.",
            ),
            intake,
        )

    def _fetch() -> dict[str, Any]:
        queries = _carrier_queries(intake, query_plan)
        all_results: list[dict] = []
        retrieval_tasks = []
        run_events = []
        warnings: list[str] = []
        run_id = notebook_run_id_from_intake(intake)
        stage_id = f"{run_id}:carrier"

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
        return carrier_doc_pack_to_payload(payload)

    pack = cached_call(
        case_key,
        _fetch,
        cache_samples_dir=cache_samples_dir,
        cache_dir=cache_dir,
        use_cache=use_cache,
    )
    return _normalize_carrier_pack(pack, intake)


def _carrier_queries(
    intake: CaseIntake,
    query_plan: Sequence[Mapping[str, Any] | QuerySpec] | None,
) -> list[QuerySpec]:
    if query_plan is not None:
        return query_plan_for_module(query_plan, "carrier_docs")
    return [query for query in generate_query_plan(intake) if query.module == "carrier_docs"]


def _empty_carrier_pack(intake: CaseIntake, reason: str) -> dict[str, Any]:
    """Return a structured empty carrier payload when live retrieval is unavailable."""
    return carrier_doc_pack_to_payload({
        "module": "carrier",
        "carrier_snapshot": {
            "name": intake.carrier,
            "state": intake.state,
            "event": intake.event_name,
            "policy_type": intake.policy_type,
        },
        "document_pack": [],
        "common_defenses": [],
        "rebuttal_angles": [],
        "sources": [],
        "warnings": [reason],
    })


def _assemble_pack(
    intake: CaseIntake,
    results: list[dict],
) -> dict[str, Any]:
    """Assemble carrier doc pack from raw results."""
    # Deduplicate
    seen: set[str] = set()
    unique: list[dict] = []
    for result in results:
        if result["url"] and result["url"] not in seen:
            seen.add(result["url"])
            unique.append(result)

    # Score, filter, and rank for evidence quality.
    scored = []
    for result in unique:
        score = score_url(result["url"])
        enriched = {**result, "_score": score}
        if _is_low_value_carrier_result(enriched):
            continue
        scored.append(enriched)

    scored.sort(key=_carrier_result_priority)

    # Categorize into document types
    doc_type_map = {
        "denial_patterns": "Denial Pattern Analysis",
        "doi_complaints": "DOI/Regulatory Complaint",
        "regulatory_action": "Regulatory Action",
        "claims_manual": "Claims Handling Guideline",
        "bad_faith_history": "Bad Faith Signal",
    }

    document_pack = []
    for result in scored[:15]:
        category = result.get("category", "general")
        score = result["_score"]
        document_pack.append({
            "doc_type": doc_type_map.get(category, "General"),
            "title": result.get("title", ""),
            "url": result["url"],
            "badge": score["badge"],
            "why_it_matters": _why_it_matters(category, result, intake),
        })

    # Build common defenses from denial_patterns results
    common_defenses = _extract_defenses(
        [result for result in scored if result.get("category") == "denial_patterns"],
        intake,
    )

    # Build rebuttal angles
    rebuttal_angles = _build_rebuttals(intake, common_defenses, scored)

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

    return carrier_doc_pack_to_payload({
        "module": "carrier",
        "carrier_snapshot": {
            "name": intake.carrier,
            "state": intake.state,
            "event": intake.event_name,
            "policy_type": intake.policy_type,
        },
        "document_pack": document_pack[:12],
        "common_defenses": common_defenses,
        "rebuttal_angles": rebuttal_angles,
        "sources": sources,
    })


def _normalize_carrier_pack(
    payload: Mapping[str, Any],
    intake: CaseIntake,
) -> dict[str, Any]:
    """Clean cached/live carrier payloads before downstream read models consume them."""
    pack = carrier_doc_pack_to_payload(payload)
    document_pack = []
    seen_doc_urls: set[str] = set()
    for document in pack["document_pack"]:
        entry = {
            **document,
            "why_it_matters": _clean_carrier_text(document.get("why_it_matters", "")),
        }
        if _is_low_value_carrier_payload_entry(entry, doc_type=document.get("doc_type", "")):
            continue
        url = entry.get("url", "")
        if url and url in seen_doc_urls:
            continue
        if url:
            seen_doc_urls.add(url)
        document_pack.append(entry)
    document_pack.sort(key=lambda document: _carrier_payload_priority(document, doc_type=document.get("doc_type", "")))
    if _strong_carrier_entry_count(document_pack, use_doc_type=True) >= 3:
        document_pack = [document for document in document_pack if not _is_unvetted_carrier_entry(document)]

    sources = []
    seen_source_urls: set[str] = set()
    for source in pack["sources"]:
        if _is_low_value_carrier_payload_entry(source):
            continue
        url = source.get("url", "")
        if url and url in seen_source_urls:
            continue
        if url:
            seen_source_urls.add(url)
        sources.append(source)
    sources.sort(key=_carrier_payload_priority)
    if _strong_carrier_entry_count(sources) >= 3:
        sources = [source for source in sources if not _is_unvetted_carrier_entry(source)]

    return carrier_doc_pack_to_payload(
        {
            **pack,
            "carrier_snapshot": pack["carrier_snapshot"] or {
                "name": intake.carrier,
                "state": intake.state,
                "event": intake.event_name,
                "policy_type": intake.policy_type,
            },
            "document_pack": document_pack,
            "sources": sources,
        }
    )


def _carrier_result_priority(result: dict[str, Any]) -> tuple[int, int, int, str]:
    """Prefer official, document-like sources over general navigation pages."""
    tier_rank = {"official": 0, "professional": 1, "unvetted": 2, "paywalled": 3}
    title = (result.get("title", "") or "").lower()
    url = (result.get("url", "") or "").lower()

    high_value_bonus = 0 if _contains_any(title, _HIGH_VALUE_DOC_TERMS) or _contains_any(
        url,
        _HIGH_VALUE_DOC_TERMS,
    ) or url.endswith(".pdf") else 1
    category_bonus = 0 if result.get("category") in {"doi_complaints", "regulatory_action"} else 1

    return (
        tier_rank.get(result["_score"]["tier"], 9),
        high_value_bonus,
        category_bonus,
        title,
    )


def _is_low_value_carrier_result(result: dict[str, Any]) -> bool:
    """Reject generic navigation pages that do not add carrier evidence."""
    title = (result.get("title", "") or "").lower()
    url = (result.get("url", "") or "").lower()
    category = result.get("category", "")

    if category in {"doi_complaints", "regulatory_action"}:
        if _is_low_value_carrier_page(title, url):
            return True

    if category == "claims_manual" and _contains_any(title, ("brochure", "faq")):
        return True

    return False


def _is_low_value_carrier_payload_entry(
    entry: Mapping[str, Any],
    *,
    doc_type: str = "",
) -> bool:
    title = (entry.get("title", "") or "").lower()
    url = (entry.get("url", "") or "").lower()
    normalized_doc_type = doc_type.lower()

    if _is_low_value_carrier_page(title, url):
        return True
    if _contains_any(title, _LOW_VALUE_SUPPORT_TITLES):
        return True
    if "claims handling guideline" in normalized_doc_type and _contains_any(
        title,
        ("brochure", "what to expect after reporting your claim"),
    ):
        return True
    return False


def _carrier_payload_priority(
    entry: Mapping[str, Any],
    *,
    doc_type: str = "",
) -> tuple[int, int, int, int, int, str]:
    title = entry.get("title", "") or ""
    url = entry.get("url", "") or ""
    score = score_url(url, title)
    hostname = score.get("hostname", "").removeprefix("www.")
    tier_rank = {"official": 0, "professional": 1, "unvetted": 2, "paywalled": 3}
    source_class_rank = {
        "government_guidance": 0,
        "other": 1,
        "commentary": 2,
        "news": 3,
    }
    title_lower = title.lower()
    url_lower = url.lower()
    doc_rank = _CARRIER_DOC_TYPE_RANK.get(doc_type or "General", 9)
    high_value_bonus = 0 if (
        _contains_any(title_lower, _HIGH_VALUE_DOC_TERMS)
        or _contains_any(url_lower, _HIGH_VALUE_DOC_TERMS)
        or url_lower.endswith(".pdf")
    ) else 1
    carrier_specific_bonus = 0 if (
        hostname.endswith("floir.com")
        or hostname.endswith("floir.gov")
        or hostname.endswith("citizensfla.com")
    ) else 1
    return (
        doc_rank,
        tier_rank.get(score["tier"], 9),
        high_value_bonus,
        carrier_specific_bonus,
        source_class_rank.get(score.get("source_class"), 9),
        title_lower,
    )


def _strong_carrier_entry_count(
    entries: Sequence[Mapping[str, Any]],
    *,
    use_doc_type: bool = False,
) -> int:
    return sum(
        1
        for entry in entries
        if _is_strong_carrier_entry(
            entry,
            doc_type=(entry.get("doc_type", "") if use_doc_type else ""),
        )
    )


def _is_strong_carrier_entry(
    entry: Mapping[str, Any],
    *,
    doc_type: str = "",
) -> bool:
    title = entry.get("title", "") or ""
    url = entry.get("url", "") or ""
    score = score_url(url, title)
    hostname = score.get("hostname", "").removeprefix("www.")
    title_lower = title.lower()
    url_lower = url.lower()
    normalized_doc_type = doc_type.lower()

    if score["tier"] == "official":
        return True
    if score["tier"] != "professional":
        return False
    if hostname.endswith("citizensfla.com"):
        return True
    if normalized_doc_type in {
        "doi/regulatory complaint",
        "claims handling guideline",
        "regulatory action",
    }:
        return True
    return (
        _contains_any(title_lower, _HIGH_VALUE_DOC_TERMS)
        or _contains_any(url_lower, _HIGH_VALUE_DOC_TERMS)
        or url_lower.endswith(".pdf")
    )


def _is_unvetted_carrier_entry(entry: Mapping[str, Any]) -> bool:
    score = score_url(entry.get("url", "") or "", entry.get("title", "") or "")
    return score["tier"] == "unvetted"


def _contains_any(text: str, needles: tuple[str, ...]) -> bool:
    return any(needle in text for needle in needles)


def _is_low_value_carrier_page(title: str, url: str) -> bool:
    normalized_title = title.strip().lower()
    return normalized_title in _LOW_VALUE_PAGE_TITLES or _contains_any(url, _LOW_VALUE_PAGE_URL_TERMS)


def _why_it_matters(category: str, result: dict, intake: CaseIntake) -> str:
    """Generate a short 'why it matters' note for a document."""
    snippet = _clean_carrier_text((result.get("snippet", "") or "")[:200].strip())
    if category == "denial_patterns":
        return f"Documents {intake.carrier} denial patterns - {snippet[:100]}"
    if category == "doi_complaints":
        return "Regulatory complaint record - may signal systemic issues"
    if category == "regulatory_action":
        return (
            f"Regulatory action context for {intake.carrier} - "
            "may inform bad-faith analysis pending legal review"
        )
    if category == "claims_manual":
        return "Internal claims handling standards - compare to actual handling"
    if category == "bad_faith_history":
        return f"Prior bad faith signals for {intake.carrier} in {intake.state}"
    return snippet[:150] if snippet else "Potentially relevant carrier document"


def _clean_carrier_text(text: str) -> str:
    normalized = text.replace("\r", " ").replace("\n", " ")
    normalized = re.sub(r"[#*]+", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    lowered = normalized.lower()
    for marker in _LOW_SIGNAL_SNIPPET_TERMS:
        lowered = lowered.replace(marker, " ")
        normalized = re.sub(marker, " ", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"\s+", " ", normalized).strip(" -")
    return normalized


def _extract_defenses(denial_results: list[dict], intake: CaseIntake) -> list[str]:
    """Extract common carrier defenses from denial pattern results."""
    defenses = []
    all_text = " ".join(result.get("text", "") for result in denial_results).lower()

    defense_patterns = [
        ("pre-existing", f"{intake.carrier} may argue damage was pre-existing"),
        ("wear and tear", "Wear and tear / maintenance exclusion defense"),
        ("flood exclu", "Flood exclusion - wind vs. water causation dispute"),
        ("concurrent caus", "Anti-concurrent causation clause defense"),
        ("late notice", "Late notice / failure to mitigate defense"),
        ("policy exclu", "Policy exclusion defense"),
    ]
    for pattern, defense in defense_patterns:
        if pattern in all_text:
            defenses.append(defense)

    if not defenses:
        defenses.append(f"Standard denial defenses for {intake.policy_type} claims")

    return defenses


def _build_rebuttals(
    intake: CaseIntake,
    defenses: list[str],
    scored_results: list[dict],
) -> list[str]:
    """Generate rebuttal angles from case facts and carrier data."""
    rebuttals = []

    for fact in intake.key_facts:
        rebuttals.append(f"Key fact undermines carrier position: {fact}")

    if any("pre-existing" in defense.lower() for defense in defenses):
        rebuttals.append(
            "Counter pre-existing defense: damage timeline correlates with event date"
        )
    if any("concurrent" in defense.lower() for defense in defenses):
        rebuttals.append(
            "Counter ACC clause: efficient proximate cause doctrine may apply in "
            f"{intake.state}"
        )
    if "bad_faith" in intake.posture:
        rebuttals.append(
            f"Potential bad-faith signal: investigate {intake.carrier}'s claims handling "
            "timeline and investigation adequacy"
        )

    # Add regulatory angle if DOI results found
    doi_results = [result for result in scored_results if result.get("category") == "doi_complaints"]
    if doi_results:
        rebuttals.append(
            f"Regulatory record: {len(doi_results)} DOI/regulatory results found - "
            "may warrant further pattern-of-conduct review"
        )

    return rebuttals
