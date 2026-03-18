"""Offline demo pack validation.

Loads cache_samples/<case_key>/*.json and validates
required keys exist and lists are non-empty.

No network calls - tests the committed fixture data.
"""

import json
from pathlib import Path

import pytest

from war_room.carrier_module import build_carrier_doc_pack
from war_room.caselaw_module import build_caselaw_pack
from war_room.citation_verify import spot_check_citations
from war_room.models import CaseIntake
from war_room.weather_module import build_weather_brief

ROOT = Path(__file__).resolve().parent.parent
CACHE_SAMPLES_ROOT = ROOT / "cache_samples"

SCENARIOS = {
    "milton_citizens_pinellas": {
        "event_name": "Hurricane Milton",
        "event_date": "2024-10-09",
        "state": "FL",
        "county": "Pinellas",
        "carrier": "Citizens Property Insurance",
        "policy_type": "HO-3 Dwelling",
        "posture": ["denial", "bad_faith"],
        "key_facts": [
            "Category 3 at landfall near Siesta Key",
            "Roof damage and water intrusion reported within 48 hours",
            "Claim denied citing pre-existing conditions",
        ],
        "coverage_issues": [
            "wind vs water causation",
            "anti-concurrent causation clause",
            "duty to investigate",
        ],
        "expected_checks": 6,
    },
    "tx_hail_allstate_tarrant": {
        "event_name": "Texas Hailstorm",
        "event_date": "2023-05-04",
        "state": "TX",
        "county": "Tarrant",
        "carrier": "Allstate Texas Lloyds",
        "policy_type": "HO-B Homeowners",
        "posture": ["denial", "underpayment"],
        "key_facts": [
            "Golf-ball-size hail was reported in Tarrant County on the reported date of loss",
            "Roof slope bruising and soft-metal damage were documented shortly after the storm",
            "Carrier estimate scoped only spot repairs despite full-slope damage indicators",
        ],
        "coverage_issues": [
            "hail causation",
            "matching",
            "actual cash value vs replacement cost",
        ],
        "expected_checks": 3,
    },
    "ida_lloyds_orleans": {
        "event_name": "Hurricane Ida",
        "event_date": "2021-08-29",
        "state": "LA",
        "county": "Orleans",
        "carrier": "Certain Underwriters at Lloyd's, London",
        "policy_type": "HO-3 Dwelling",
        "posture": ["denial", "bad_faith"],
        "key_facts": [
            "Hurricane-force winds were documented in Orleans Parish during Ida landfall",
            "Interior water intrusion was reported immediately after roof and window-envelope damage",
            "Carrier attributed the majority of loss to excluded flood and delayed portions of the adjustment",
        ],
        "coverage_issues": [
            "wind vs water causation",
            "concurrent causation",
            "duty to investigate",
        ],
        "expected_checks": 3,
    },
}

_GENERIC_CARRIER_TITLES = {
    "consumers - floir",
    "contact us - floir",
    "organization and operation - floir",
}

_GENERIC_WEATHER_TITLES = {
    "hurricane costs",
    "news and media: disaster 4834 - fema",
    "dr-4834 public notice 001 - fema.gov",
}

_CASE_COMMENTARY_MARKERS = (
    "jd supra",
    "what homeowners must know",
    "in the wake of hurricane",
)

_STABLE_SOURCE_BADGES = {"official", "professional", "unvetted", "paywalled"}
_STABLE_CITATION_BADGES = {"verified", "warning", "not_found"}


class _FixtureProvider:
    provider_name = "fixture"


def _scenario_dir(case_key: str) -> Path:
    return CACHE_SAMPLES_ROOT / case_key


def _load(case_key: str, name: str) -> dict:
    path = _scenario_dir(case_key) / f"{name}.json"
    if not path.exists():
        pytest.skip(f"Cache sample not seeded yet: {path}")
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _intake(case_key: str) -> CaseIntake:
    payload = {key: value for key, value in SCENARIOS[case_key].items() if key != "expected_checks"}
    return CaseIntake(**payload)


@pytest.mark.parametrize("case_key", sorted(SCENARIOS))
def test_scenario_folder_has_expected_module_files(case_key: str):
    scenario_dir = _scenario_dir(case_key)
    assert scenario_dir.exists()
    assert (scenario_dir / "weather.json").exists()
    assert (scenario_dir / "carrier.json").exists()
    assert (scenario_dir / "caselaw.json").exists()
    assert (scenario_dir / "citation_verify.json").exists()


@pytest.mark.parametrize("case_key", sorted(SCENARIOS))
def test_weather_sample_has_required_keys_and_content(case_key: str):
    data = _load(case_key, "weather")
    config = SCENARIOS[case_key]

    assert data["module"] == "weather"
    assert "event_summary" in data
    assert config["event_name"] in data["event_summary"]
    assert config["county"] in data["event_summary"]
    assert config["state"] in data["event_summary"]
    assert len(data["key_observations"]) > 0
    assert len(data["sources"]) > 0
    for source in data["sources"]:
        assert "url" in source
        assert "badge" in source


@pytest.mark.parametrize("case_key", sorted(SCENARIOS))
def test_carrier_sample_has_required_keys_and_content(case_key: str):
    data = _load(case_key, "carrier")
    config = SCENARIOS[case_key]

    assert data["module"] == "carrier"
    assert data["carrier_snapshot"]["name"] == config["carrier"]
    assert data["carrier_snapshot"]["state"] == config["state"]
    assert data["carrier_snapshot"]["event"] == config["event_name"]
    assert len(data["document_pack"]) > 0
    assert len(data["rebuttal_angles"]) > 0
    assert len(data["sources"]) > 0


@pytest.mark.parametrize("case_key", sorted(SCENARIOS))
def test_caselaw_sample_has_required_keys_and_cases(case_key: str):
    data = _load(case_key, "caselaw")

    assert data["module"] == "caselaw"
    assert len(data["issues"]) > 0
    total_cases = sum(len(issue["cases"]) for issue in data["issues"])
    assert total_cases >= 1
    assert len(data["sources"]) > 0


@pytest.mark.parametrize("case_key", sorted(SCENARIOS))
def test_citation_verify_sample_has_required_keys_and_summary(case_key: str):
    data = _load(case_key, "citation_verify")
    expected_checks = SCENARIOS[case_key]["expected_checks"]

    assert data["module"] == "citation_verify"
    assert "disclaimer" in data
    assert len(data["checks"]) == expected_checks
    assert data["summary"]["total"] == expected_checks
    assert data["summary"]["total"] == data["summary"]["verified"] + data["summary"]["uncertain"] + data["summary"]["not_found"]


@pytest.mark.parametrize("case_key", sorted(SCENARIOS))
def test_scenario_resolves_through_cache_first_runtime(case_key: str):
    intake = _intake(case_key)
    cache_samples_dir = str(CACHE_SAMPLES_ROOT)

    weather = build_weather_brief(intake, None, cache_samples_dir=cache_samples_dir)
    assert weather["event_summary"].startswith(SCENARIOS[case_key]["event_name"])

    carrier = build_carrier_doc_pack(intake, None, cache_samples_dir=cache_samples_dir)
    assert carrier["carrier_snapshot"]["name"] == SCENARIOS[case_key]["carrier"]

    caselaw = build_caselaw_pack(intake, None, cache_samples_dir=cache_samples_dir)
    assert len(caselaw["issues"]) > 0

    citecheck = spot_check_citations(caselaw, _FixtureProvider(), cache_samples_dir=cache_samples_dir)
    assert citecheck["summary"]["total"] == SCENARIOS[case_key]["expected_checks"]


def test_milton_weather_sample_excludes_generic_weather_reference_pages():
    data = _load("milton_citizens_pinellas", "weather")
    titles = {source["title"].strip().lower() for source in data["sources"]}
    assert not titles.intersection(_GENERIC_WEATHER_TITLES)


def test_milton_carrier_sample_excludes_generic_regulator_navigation_pages():
    data = _load("milton_citizens_pinellas", "carrier")
    titles = {document["title"].strip().lower() for document in data["document_pack"]}
    assert not titles.intersection(_GENERIC_CARRIER_TITLES)


def test_milton_caselaw_sample_excludes_commentary_titles_from_case_entries():
    data = _load("milton_citizens_pinellas", "caselaw")
    case_titles = [case["name"].lower() for issue in data["issues"] for case in issue["cases"]]
    for marker in _CASE_COMMENTARY_MARKERS:
        assert all(marker not in title for title in case_titles)


def test_milton_citation_checks_reference_case_titles_not_commentary():
    data = _load("milton_citizens_pinellas", "citation_verify")
    case_titles = [check["case_name"].lower() for check in data["checks"]]
    for marker in _CASE_COMMENTARY_MARKERS:
        assert all(marker not in title for title in case_titles)


@pytest.mark.parametrize("case_key", sorted(SCENARIOS))
def test_fixture_badges_use_stable_ascii_tokens(case_key: str):
    weather = _load(case_key, "weather")
    assert {source["badge"] for source in weather["sources"]}.issubset(_STABLE_SOURCE_BADGES)

    carrier = _load(case_key, "carrier")
    carrier_badges = {document["badge"] for document in carrier["document_pack"]}
    carrier_badges.update(source["badge"] for source in carrier["sources"])
    assert carrier_badges.issubset(_STABLE_SOURCE_BADGES)

    caselaw = _load(case_key, "caselaw")
    caselaw_badges = {source["badge"] for source in caselaw["sources"]}
    caselaw_badges.update(case["badge"] for issue in caselaw["issues"] for case in issue["cases"])
    assert caselaw_badges.issubset(_STABLE_SOURCE_BADGES)

    citecheck = _load(case_key, "citation_verify")
    assert {check["badge"] for check in citecheck["checks"]}.issubset(_STABLE_CITATION_BADGES)

