"""Carrier playbook intel module.

Runs carrier_docs queries via Exa. Builds a document pack with
denial patterns, regulatory signals, and rebuttal angles.
"""

from __future__ import annotations

from typing import Any

from war_room.cache_io import cache_get, cached_call
from war_room.retrieval import (
    RetrievalProvider,
    RetrievalSearchRequest,
    execute_retrieval_task,
    notebook_run_id_from_intake,
    query_spec_to_retrieval_task,
)
from war_room.models import CaseIntake, carrier_doc_pack_to_payload
from war_room.query_plan import generate_query_plan
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

_LOW_VALUE_PAGE_TERMS = (
    "about us",
    "brochure",
    "contact us",
    "consumer",
    "faq",
    "home",
    "organization and operation",
)


def build_carrier_doc_pack(
    intake: CaseIntake,
    client: RetrievalProvider | None,
    *,
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
                return cached
        return _empty_carrier_pack(
            intake,
            "No Exa client available and no cached carrier pack found.",
        )

    def _fetch() -> dict[str, Any]:
        queries = [q for q in generate_query_plan(intake) if q.module == "carrier_docs"]
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

    return cached_call(
        case_key,
        _fetch,
        cache_samples_dir=cache_samples_dir,
        cache_dir=cache_dir,
        use_cache=use_cache,
    )


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
        if _contains_any(title, _LOW_VALUE_PAGE_TERMS) or _contains_any(url, _LOW_VALUE_PAGE_TERMS):
            return True

    if category == "claims_manual" and _contains_any(title, ("brochure", "faq")):
        return True

    return False


def _contains_any(text: str, needles: tuple[str, ...]) -> bool:
    return any(needle in text for needle in needles)


def _why_it_matters(category: str, result: dict, intake: CaseIntake) -> str:
    """Generate a short 'why it matters' note for a document."""
    snippet = (result.get("snippet", "") or "")[:200].strip()
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
