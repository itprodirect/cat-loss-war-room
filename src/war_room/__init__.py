"""CAT-Loss War Room - AI-powered catastrophic loss litigation research."""

from war_room.cache_io import cached_call
from war_room.models import (
    CaseLawPack,
    CaseIntake,
    CarrierDocPack,
    CitationVerifyPack,
    MemoRenderInput,
    QuerySpec,
    WeatherBrief,
    adapt_caselaw_pack,
    adapt_carrier_doc_pack,
    adapt_citation_verify_pack,
    adapt_weather_brief,
    caselaw_pack_to_payload,
    carrier_doc_pack_to_payload,
    citation_verify_pack_to_payload,
    memo_render_input_from_parts,
    weather_brief_to_payload,
)
from war_room.query_plan import (
    CASE_INTAKE_ALLOWED_FIELDS,
    CASE_INTAKE_OPTIONAL_FIELDS,
    CASE_INTAKE_REQUIRED_FIELDS,
    IntakeValidationError,
    generate_query_plan,
    load_case_intake,
    validate_case_intake_payload,
)
from war_room.source_scoring import score_url

__all__ = [
    "cached_call",
    "score_url",
    "CASE_INTAKE_REQUIRED_FIELDS",
    "CASE_INTAKE_OPTIONAL_FIELDS",
    "CASE_INTAKE_ALLOWED_FIELDS",
    "CaseIntake",
    "IntakeValidationError",
    "QuerySpec",
    "generate_query_plan",
    "validate_case_intake_payload",
    "load_case_intake",
    "WeatherBrief",
    "CarrierDocPack",
    "CaseLawPack",
    "CitationVerifyPack",
    "MemoRenderInput",
    "adapt_weather_brief",
    "adapt_carrier_doc_pack",
    "adapt_caselaw_pack",
    "adapt_citation_verify_pack",
    "weather_brief_to_payload",
    "carrier_doc_pack_to_payload",
    "caselaw_pack_to_payload",
    "citation_verify_pack_to_payload",
    "memo_render_input_from_parts",
]
