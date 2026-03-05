"""Weather data gathering module.

Runs weather queries from the query plan via Exa, preferring .gov sources.
Extracts metrics only when present in retrieved content.
"""

from __future__ import annotations

import re
from typing import Any

from war_room.cache_io import cache_get, cached_call
from war_room.exa_client import ExaClient
from war_room.models import weather_brief_to_payload
from war_room.query_plan import CaseIntake, generate_query_plan
from war_room.source_scoring import score_url

GOV_WEATHER_DOMAINS = [
    "noaa.gov", "weather.gov", "nhc.noaa.gov",
    "fema.gov", "usgs.gov", "nasa.gov",
]


def build_weather_brief(
    intake: CaseIntake,
    client: ExaClient | None,
    *,
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
                return cached
        return _empty_weather_brief(
            intake,
            "No Exa client available and no cached weather brief found.",
        )

    def _fetch() -> dict[str, Any]:
        queries = [q for q in generate_query_plan(intake) if q.module == "weather"]
        all_results: list[dict] = []

        for q in queries:
            hits = client.search(
                q.query,
                k=5,
                include_domains=q.preferred_domains or None,
            )
            for h in hits:
                h["category"] = q.category
            all_results.extend(hits)

        return _assemble_brief(intake, all_results)

    return cached_call(
        case_key,
        _fetch,
        cache_samples_dir=cache_samples_dir,
        cache_dir=cache_dir,
        use_cache=use_cache,
    )


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

    # Score and sort: official first, then professional, then unvetted
    tier_order = {"official": 0, "professional": 1, "unvetted": 2, "paywalled": 3}
    scored: list[dict[str, Any]] = []
    for result in unique:
        score = score_url(result["url"])
        scored.append({**result, "_score": score})
    scored.sort(key=lambda item: tier_order.get(item["_score"]["tier"], 9))

    # Build observations from top results
    observations = []
    for result in scored[:10]:
        snippet = result.get("snippet", "").strip()
        if snippet:
            observations.append(snippet[:300])

    # Extract metrics defensively from all text
    all_text = " ".join(result.get("text", "") for result in scored[:15])
    metrics = _extract_metrics(all_text)

    # Build source list
    sources = []
    for result in scored[:15]:
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
        "key_observations": observations[:8],
        "metrics": metrics,
        "sources": sources,
    })


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
