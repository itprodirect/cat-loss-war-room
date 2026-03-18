"""Tests for weather_module - no network calls, uses mock/cache."""

import tempfile

from war_room.models import CaseIntake
from war_room.weather_module import _assemble_brief, _extract_metrics, build_weather_brief


def _sample_intake() -> CaseIntake:
    return CaseIntake(
        event_name="Hurricane Milton",
        event_date="2024-10-09",
        state="FL",
        county="Pinellas",
        carrier="Citizens Property Insurance",
        policy_type="HO-3 Dwelling",
    )


def test_extract_metrics_wind() -> None:
    text = "Maximum sustained winds of 120 mph were recorded near landfall."
    metrics = _extract_metrics(text)
    assert metrics["max_wind_mph"] == 120


def test_extract_metrics_surge() -> None:
    text = "Storm surge of 8.5 feet was observed along the coast."
    metrics = _extract_metrics(text)
    assert metrics["storm_surge_ft"] == 8.5


def test_extract_metrics_rain() -> None:
    text = "The area received 12.3 inches of rainfall over 24 hours."
    metrics = _extract_metrics(text)
    assert metrics["rain_in"] == 12.3


def test_extract_metrics_none() -> None:
    text = "The storm caused significant damage to the region."
    metrics = _extract_metrics(text)
    assert metrics["max_wind_mph"] is None
    assert metrics["storm_surge_ft"] is None
    assert metrics["rain_in"] is None


def test_assemble_brief_structure() -> None:
    results = [
        {
            "url": "https://weather.gov/report",
            "title": "NWS Report",
            "snippet": "Winds reached 110 mph in Pinellas County",
            "text": "Winds reached 110 mph in Pinellas County during Milton.",
            "category": "wind_data",
        },
        {
            "url": "https://fema.gov/disaster",
            "title": "FEMA Declaration",
            "snippet": "Major disaster declared for FL",
            "text": "FEMA major disaster declaration for Hurricane Milton FL.",
            "category": "fema_declaration",
        },
    ]
    brief = _assemble_brief(_sample_intake(), results)
    assert brief["module"] == "weather"
    assert "event_summary" in brief
    assert isinstance(brief["key_observations"], list)
    assert isinstance(brief["metrics"], dict)
    assert isinstance(brief["sources"], list)
    assert len(brief["sources"]) == 2


def test_weather_excludes_generic_reference_pages() -> None:
    results = [
        {
            "url": "https://coast.noaa.gov/states/fast-facts/hurricane-costs.html",
            "title": "Hurricane Costs",
            "snippet": "Generic costs page",
            "text": "Historic costs.",
            "category": "loss_estimate",
        },
        {
            "url": "https://www.weather.gov/media/tbw/TropicalEventSummary/PSHTBW_2024AL14_Milton_Summary.pdf",
            "title": "POST TROPICAL CYCLONE REPORT",
            "snippet": "Pinellas County saw hurricane-force wind gusts during Milton.",
            "text": "Pinellas County saw hurricane-force wind gusts of 105 mph.",
            "category": "damage_report",
        },
    ]

    brief = _assemble_brief(_sample_intake(), results)
    titles = [source["title"] for source in brief["sources"]]

    assert "Hurricane Costs" not in titles
    assert "POST TROPICAL CYCLONE REPORT" in titles


def test_weather_prefers_county_specific_metrics() -> None:
    results = [
        {
            "url": "https://www.nhc.noaa.gov/data/tcr/AL142024_Milton.pdf",
            "title": "Hurricane Milton",
            "snippet": "Storm report",
            "text": "Milton reached 180 mph over open water before landfall.",
            "category": "wind_data",
        },
        {
            "url": "https://www.weather.gov/media/tbw/TropicalEventSummary/PSHTBW_2024AL14_Milton_Summary.pdf",
            "title": "POST TROPICAL CYCLONE REPORT",
            "snippet": "Pinellas County observed 105 mph wind gusts.",
            "text": "Pinellas County observed 105 mph wind gusts and 8 ft storm surge.",
            "category": "damage_report",
        },
    ]

    brief = _assemble_brief(_sample_intake(), results)

    assert brief["metrics"]["max_wind_mph"] == 105
    assert brief["metrics"]["storm_surge_ft"] == 8.0


def test_weather_drops_navigation_heavy_observations() -> None:
    results = [
        {
            "url": "https://www.nhc.noaa.gov/archive/2024/al14/al142024.public.019.shtml",
            "title": "Hurricane MILTON",
            "snippet": "[Home] [Mobile Site] [Text Version] Skip Navigation Links",
            "text": "Navigation-heavy content without substance.",
            "category": "wind_data",
        },
        {
            "url": "https://www.weather.gov/media/tbw/TropicalEventSummary/PSHTBW_2024AL14_Milton_Summary.pdf",
            "title": "POST TROPICAL CYCLONE REPORT",
            "snippet": "Pinellas County reported roof damage and widespread water intrusion.",
            "text": "Pinellas County reported roof damage and widespread water intrusion.",
            "category": "damage_report",
        },
    ]

    brief = _assemble_brief(_sample_intake(), results)

    assert all("Skip Navigation" not in observation for observation in brief["key_observations"])
    assert any("Pinellas County" in observation for observation in brief["key_observations"])




class _WeatherProvider:
    provider_name = "exa"

    def __init__(self) -> None:
        self.calls = 0

    def search(self, query: str, **kwargs: object) -> list[dict[str, object]]:
        self.calls += 1
        return [{
            "url": f"https://weather.gov/report/{self.calls}",
            "title": "NWS Report",
            "snippet": "Pinellas County observed 105 mph wind gusts.",
            "text": "Pinellas County observed 105 mph wind gusts and 8 ft storm surge.",
        }]

    def get_contents(self, urls: list[str], **kwargs: object) -> list[dict[str, object]]:
        return []


def test_build_weather_brief_emits_retrieval_state() -> None:
    brief = build_weather_brief(
        _sample_intake(),
        client=_WeatherProvider(),
        use_cache=False,
    )

    assert brief["retrieval_tasks"]
    assert all(task["status"] == "completed" for task in brief["retrieval_tasks"])
    assert all(task["stage_id"].endswith(":weather") for task in brief["retrieval_tasks"])
    assert len(brief["run_events"]) == len(brief["retrieval_tasks"]) * 2
    assert {event["event_type"] for event in brief["run_events"]} == {"retrieval_started", "retrieval_completed"}

def test_build_weather_brief_without_client_returns_structured_fallback() -> None:
    intake = _sample_intake()
    with tempfile.TemporaryDirectory() as cache_dir, tempfile.TemporaryDirectory() as samples_dir:
        brief = build_weather_brief(
            intake,
            client=None,
            use_cache=False,
            cache_dir=cache_dir,
            cache_samples_dir=samples_dir,
        )

    assert brief["module"] == "weather"
    assert brief["sources"] == []
    assert brief["key_observations"] == []
    assert "warnings" in brief
    assert any("No Exa client available" in warning for warning in brief["warnings"])
