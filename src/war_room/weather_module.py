"""Weather data gathering module.

Runs weather queries from the query plan via Exa, preferring .gov sources.
Extracts metrics only when present in retrieved content.
"""

from __future__ import annotations

import html
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
from war_room.models import CaseIntake, QuerySpec, weather_brief_to_payload
from war_room.query_plan import generate_query_plan, query_plan_for_module
from war_room.source_scoring import score_url

GOV_WEATHER_DOMAINS = [
    "noaa.gov", "weather.gov", "nhc.noaa.gov",
    "fema.gov", "usgs.gov", "nasa.gov",
]

_HIGH_VALUE_WEATHER_TERMS = (
    "advisory",
    "damage",
    "declaration",
    "event details",
    "pdf",
    "post tropical cyclone report",
    "report",
    "storm events",
    "summary",
)

_LOW_VALUE_WEATHER_TERMS = (
    "costs",
    "fast facts",
    "historic events",
    "lessons from",
    "news-media",
    "news and media",
    "public notice",
)

_NAVIGATION_MARKERS = (
    "[home]",
    "[mobile site]",
    "[text version]",
    "![skip navigation links]",
    "mobile site",
    "text version",
    "skip navigation",
    "storm events database - event details",
)


def build_weather_brief(
    intake: CaseIntake,
    client: RetrievalProvider | None,
    *,
    query_plan: Sequence[Mapping[str, Any] | QuerySpec] | None = None,
    use_cache: bool = True,
    cache_dir: str = "cache",
    cache_samples_dir: str = "cache_samples",
) -> dict[str, Any]:
    """Build a structured weather brief for the case.

    Returns dict with: module, event_summary, key_observations, metrics, sources.
    """
    case_key = f"weather__{intake.event_name}__{intake.county}_{intake.state}"

    # Graceful fallback: no client available. Prefer cache, then return a safe empty payload.
    if client is None:
        if use_cache:
            cached = cache_get(case_key, cache_samples_dir)
            if cached is None:
                cached = cache_get(case_key, cache_dir)
            if cached is not None:
                return _normalize_weather_brief(cached, intake)
        return _empty_weather_brief(
            intake,
            "No Exa client available and no cached weather brief found.",
        )

    def _fetch() -> dict[str, Any]:
        queries = _weather_queries(intake, query_plan)
        all_results: list[dict] = []
        retrieval_tasks = []
        run_events = []
        warnings: list[str] = []
        run_id = notebook_run_id_from_intake(intake)
        stage_id = f"{run_id}:weather"

        for index, q in enumerate(queries, 1):
            task = query_spec_to_retrieval_task(
                q,
                run_id=run_id,
                stage_id=stage_id,
                provider=client.provider_name,
                retrieval_task_id=f"{stage_id}:{q.category}:{index}",
            )
            execution = execute_retrieval_task(
                client,
                RetrievalSearchRequest(
                    task=task,
                    k=5,
                    include_domains=q.preferred_domains,
                ),
            )
            retrieval_tasks.append(execution.task)
            run_events.extend(execution.run_events)
            if execution.warning:
                warnings.append(execution.warning)
            for hit in execution.hits:
                hit["category"] = q.category
            all_results.extend(execution.hits)

        payload = _assemble_brief(intake, all_results)
        if warnings:
            payload["warnings"] = list(dict.fromkeys((payload.get("warnings") or []) + warnings))
        payload["retrieval_tasks"] = retrieval_tasks
        payload["run_events"] = run_events
        return weather_brief_to_payload(payload)

    return _normalize_weather_brief(
        cached_call(
            case_key,
            _fetch,
            cache_samples_dir=cache_samples_dir,
            cache_dir=cache_dir,
            use_cache=use_cache,
        ),
        intake,
    )


def _weather_queries(
    intake: CaseIntake,
    query_plan: Sequence[Mapping[str, Any] | QuerySpec] | None,
) -> list[QuerySpec]:
    if query_plan is not None:
        return query_plan_for_module(query_plan, "weather")
    return [query for query in generate_query_plan(intake) if query.module == "weather"]


def _empty_weather_brief(intake: CaseIntake, reason: str) -> dict[str, Any]:
    """Return a structured empty weather payload when live retrieval is unavailable."""
    return weather_brief_to_payload({
        "module": "weather",
        "event_summary": (
            f"{intake.event_name} - {intake.county} County, {intake.state} "
            f"({intake.event_date})"
        ),
        "key_observations": [],
        "metrics": {
            "max_wind_mph": None,
            "storm_surge_ft": None,
            "rain_in": None,
        },
        "sources": [],
        "warnings": [reason],
    })


def _normalize_weather_brief(
    payload: Mapping[str, Any],
    intake: CaseIntake,
) -> dict[str, Any]:
    """Clean cached/live weather payloads before memo and workflow rendering."""
    brief = weather_brief_to_payload(payload)

    observations = []
    for observation in brief["key_observations"]:
        cleaned = _clean_weather_text(observation)
        if not cleaned:
            continue
        if _is_navigation_heavy_text(cleaned) or _is_low_value_weather_text(cleaned):
            continue
        if cleaned not in observations:
            observations.append(cleaned)

    sources = []
    seen_source_urls: set[str] = set()
    for source in brief["sources"]:
        title = _clean_weather_text(source.get("title", ""))
        url = source.get("url", "")
        if url and url in seen_source_urls:
            continue
        candidate = {
            **source,
            "title": title,
            "reason": _clean_weather_text(source.get("reason", "")),
        }
        if _is_low_value_weather_result(candidate):
            continue
        if _is_navigation_heavy_text(f"{title} {candidate.get('reason', '')}"):
            continue
        if url:
            seen_source_urls.add(url)
        score = score_url(url, title)
        sources.append(
            {
                **candidate,
                "badge": score["badge"],
                "reason": candidate.get("reason") or score["label"],
            }
        )

    return weather_brief_to_payload(
        {
            **brief,
            "event_summary": _clean_weather_text(brief.get("event_summary", "")),
            "key_observations": observations,
            "sources": sources,
            "warnings": [
                cleaned
                for warning in brief.get("warnings", [])
                if (cleaned := _clean_weather_text(warning))
            ],
        }
    )


def _assemble_brief(
    intake: CaseIntake,
    results: list[dict],
) -> dict[str, Any]:
    """Assemble structured brief from raw search results."""
    # Deduplicate by URL
    seen_urls: set[str] = set()
    unique: list[dict] = []
    for result in results:
        if result["url"] and result["url"] not in seen_urls:
            seen_urls.add(result["url"])
            unique.append(result)

    # Score and sort: official first, then relevance to the matter.
    scored: list[dict[str, Any]] = []
    for result in unique:
        score = score_url(result["url"])
        enriched = {**result, "_score": score}
        if _is_low_value_weather_result(enriched):
            continue
        scored.append(enriched)
    scored.sort(key=lambda item: _weather_result_priority(item, intake))

    # Build observations from top, matter-relevant results.
    observations = []
    for result in scored[:10]:
        observation = _extract_observation(result, intake)
        if observation and observation not in observations:
            observations.append(observation)

    # Extract metrics, preferring county-anchored texts when available.
    metric_candidates = [result for result in scored if _has_location_signal(result, intake)]
    metric_pool = metric_candidates or scored[:8]
    all_text = " ".join(result.get("text", "") for result in metric_pool)
    metrics = _extract_metrics(all_text)

    # Build source list
    sources = []
    for result in scored[:12]:
        score = result["_score"]
        sources.append({
            "title": result.get("title", ""),
            "url": result["url"],
            "badge": score["badge"],
            "reason": score["label"],
        })

    return weather_brief_to_payload({
        "module": "weather",
        "event_summary": (
            f"{intake.event_name} - {intake.county} County, {intake.state} "
            f"({intake.event_date})"
        ),
        "key_observations": observations[:6],
        "metrics": metrics,
        "sources": sources,
    })


def _weather_result_priority(result: dict[str, Any], intake: CaseIntake) -> tuple[int, int, int, int, str]:
    """Prefer official, county-specific, report-like weather evidence."""
    tier_order = {"official": 0, "professional": 1, "unvetted": 2, "paywalled": 3}
    title = (result.get("title", "") or "").lower()
    url = (result.get("url", "") or "").lower()

    county_bonus = 0 if _has_location_signal(result, intake) else 1
    doc_bonus = 0 if _contains_any(title, _HIGH_VALUE_WEATHER_TERMS) or _contains_any(url, _HIGH_VALUE_WEATHER_TERMS) or url.endswith(".pdf") else 1
    generic_penalty = 1 if _contains_any(title, _LOW_VALUE_WEATHER_TERMS) or _contains_any(url, _LOW_VALUE_WEATHER_TERMS) else 0

    return (
        tier_order.get(result["_score"]["tier"], 9),
        county_bonus,
        doc_bonus,
        generic_penalty,
        title,
    )


def _is_low_value_weather_result(result: dict[str, Any]) -> bool:
    """Reject generic official pages that do not advance county-level corroboration."""
    title = (result.get("title", "") or "").lower()
    url = (result.get("url", "") or "").lower()
    return _contains_any(title, _LOW_VALUE_WEATHER_TERMS) or _contains_any(url, _LOW_VALUE_WEATHER_TERMS)


def _has_location_signal(result: dict[str, Any], intake: CaseIntake) -> bool:
    text = " ".join(
        [
            result.get("title", "") or "",
            result.get("snippet", "") or "",
            (result.get("text", "") or "")[:800],
        ]
    ).lower()
    county_token = intake.county.lower()
    office_token = "tampa bay" if county_token == "pinellas" else ""
    return county_token in text or (office_token and office_token in text)


def _extract_observation(result: dict[str, Any], intake: CaseIntake) -> str | None:
    snippet = _clean_weather_text(result.get("snippet", ""))
    if not snippet:
        return None

    if _is_navigation_heavy_text(snippet):
        return None
    if not (_has_location_signal(result, intake) or _is_report_like(result)):
        return None
    return snippet[:300]


def _is_report_like(result: dict[str, Any]) -> bool:
    title = (result.get("title", "") or "").lower()
    url = (result.get("url", "") or "").lower()
    return _contains_any(title, _HIGH_VALUE_WEATHER_TERMS) or _contains_any(url, _HIGH_VALUE_WEATHER_TERMS) or url.endswith(".pdf")


def _contains_any(text: str, needles: tuple[str, ...]) -> bool:
    return any(needle in text for needle in needles)


def _clean_weather_text(value: Any) -> str:
    text = html.unescape(str(value or ""))
    text = text.replace("\r", " ").replace("\n", " ")
    text = re.sub(r"!\[([^\]]*)\](?:\([^)]*\))?", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]", r"\1", text)
    text = re.sub(r"[#*`]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _is_navigation_heavy_text(text: str) -> bool:
    return _contains_any(text.lower(), _NAVIGATION_MARKERS)


def _is_low_value_weather_text(text: str) -> bool:
    return _contains_any(text.lower(), _LOW_VALUE_WEATHER_TERMS)


def _extract_metrics(text: str) -> dict[str, Any]:
    """Extract weather metrics from text. Returns only what's found."""
    metrics: dict[str, Any] = {
        "max_wind_mph": None,
        "storm_surge_ft": None,
        "rain_in": None,
    }

    # Wind speed (mph)
    wind_matches = re.findall(
        r"(\d{2,3})\s*(?:mph|miles?\s*per\s*hour)",
        text,
        re.IGNORECASE,
    )
    if wind_matches:
        metrics["max_wind_mph"] = max(int(wind) for wind in wind_matches)

    # Storm surge (feet)
    surge_matches = re.findall(
        r"(?:storm\s*surge|surge)[^\d]{0,30}(\d+(?:\.\d+)?)\s*(?:feet|ft|foot)",
        text,
        re.IGNORECASE,
    )
    surge_matches.extend(
        re.findall(
            r"(\d+(?:\.\d+)?)\s*(?:feet|ft|foot)[^\d]{0,20}(?:storm\s*surge|surge)",
            text,
            re.IGNORECASE,
        )
    )
    if surge_matches:
        metrics["storm_surge_ft"] = max(float(surge) for surge in surge_matches)

    # Rainfall (inches)
    rain_matches = re.findall(
        r"(\d+(?:\.\d+)?)\s*(?:inches?\s*of\s*rain|inches?\s*rainfall)",
        text,
        re.IGNORECASE,
    )
    if rain_matches:
        metrics["rain_in"] = max(float(rain) for rain in rain_matches)

    return metrics
