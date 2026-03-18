# Methodology

## Architecture

The war room follows a **cache-first, source-scored** pipeline:

```
CaseIntake -> QueryPlan -> [Weather | Carrier | CaseLaw] -> CitationVerify -> Export
```

## Cache System (`cache_io.py`)

Two-layer cache:

1. **`cache_samples/`** - Committed to the repo. Contains pre-cached demo results and guarantees the notebook runs without an API key on first clone.
2. **`cache/`** - Gitignored runtime cache populated by live API calls. Avoids re-hitting Exa during development.

Lookup order:

`cache_samples/` -> `cache/` -> live API call -> save to `cache/`

Cache keys are normalized: lowercased, stripped, and converted to filesystem-safe underscore tokens. Cache files are stored as JSON.

## Source Scoring (`source_scoring.py`)

Deterministic domain-based classification:

| Tier | Badge | Examples |
|------|-------|----------|
| Official | `official` | `.gov`, courts.*, NOAA, NWS, state DOI |
| Professional | `professional` | law firms, legal publishers, Reuters, AM Best |
| Unvetted | `unvetted` | blogs, forums, unknown domains |
| Paywalled | `paywalled` | Westlaw, LexisNexis, HeinOnline |

No ML - fully deterministic and debuggable.

## Query Plan (`query_plan.py`)

Given a `CaseIntake`, the system generates 12-18 search queries organized by module:

- **`weather`** - NOAA storm reports, NWS advisories, and damage surveys for the specific event and location
- **`carrier_docs`** - carrier denial patterns, DOI complaints, regulatory actions, and claims manuals
- **`caselaw`** - jurisdiction-specific precedent for the coverage type and litigation posture

Queries include date ranges, domain preferences, and category tags.

## Exa Search Wrapper (`exa_client.py`)

All network calls go through `ExaClient`, a thin wrapper around `exa-py`.

Assumptions about `exa-py`:

- `Exa(api_key)` constructor
- `Exa.search(query, num_results=, include_domains=, start_published_date=, contents=)` returns `SearchResponse`
- `contents=ContentsOptions(text={"max_characters": N})` inlines text in results
- result objects expose `url`, `title`, `score`, `published_date`, `text`, `summary`, and `highlights`
- `ContentsOptions` is a TypedDict from `exa_py.api`

Features:

- simple retry with exponential backoff (3 attempts)
- budget guard: `MAX_SEARCH_CALLS` (default 30), raises `BudgetExhausted` if exceeded
- result normalization to plain dicts: `{title, url, published_date, snippet, text, score}`

## Citation Verification (`citation_verify.py`)

Spot-check only: one Exa search per citation to verify it appears on a court or legal site. Results are recorded as `verified`, `uncertain`, or `not_found`. This is not a substitute for KeyCite or Shepardize.

## Weather Module (`weather_module.py`)

Runs weather queries with gov-first domain preference (`noaa.gov`, `weather.gov`, `fema.gov`, etc.). Extracts metrics such as wind mph, surge ft, and rain in via regex only when present in retrieved text. The module does not invent numbers.

## Carrier Module (`carrier_module.py`)

Runs `carrier_docs` queries. Categorizes results by type (denial patterns, DOI complaints, regulatory actions, claims manuals), extracts common defenses from text, and generates rebuttal angles from case facts. It avoids overclaiming bad faith and instead describes "signals" with citations.

## Case Law Module (`caselaw_module.py`)

Runs caselaw queries while excluding paywalled domains such as Westlaw and LexisNexis. Organizes results by legal issue and extracts case names, citations, court, and year via regex. Limits results to 6-12 cases total.

## Export (`export_md.py`)

Compiles all module outputs into a structured markdown memo with:

- DRAFT / ATTORNEY WORK PRODUCT watermark
- case intake, weather, carrier, and caselaw sections
- citation spot-check table
- query plan appendix
- deduplicated source appendix
- methodology and limitations section
