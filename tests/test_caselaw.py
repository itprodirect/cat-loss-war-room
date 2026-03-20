"""Tests for caselaw_module - no network calls."""

import tempfile

from war_room.models import CaseIntake
from war_room.query_plan import generate_query_plan
from war_room.caselaw_module import _assemble_pack, _extract_case_info, build_caselaw_pack


def _sample_intake() -> CaseIntake:
    return CaseIntake(
        event_name="Hurricane Milton",
        event_date="2024-10-09",
        state="FL",
        county="Pinellas",
        carrier="Citizens Property Insurance",
        policy_type="HO-3 Dwelling",
        posture=["denial"],
    )


def test_assemble_pack_structure() -> None:
    results = [
        {
            "url": "https://scholar.google.com/case1",
            "title": "Citizens v. Homeowner",
            "snippet": "Coverage dispute involving wind damage",
            "text": "Citizens Property Insurance Corp v. Homeowner, 123 So. 3d 456 (Fla. App. 2023). The court held that...",
            "category": "carrier_precedent",
        },
    ]
    pack = _assemble_pack(_sample_intake(), results)
    assert pack["module"] == "caselaw"
    assert isinstance(pack["issues"], list)
    assert isinstance(pack["sources"], list)


def test_extract_case_info() -> None:
    result = {
        "url": "https://scholar.google.com/case",
        "title": "Smith v. Insurance Co",
        "snippet": "Wind damage coverage case",
        "text": "Smith v. Insurance Co, 234 So. 3d 789 (Fla. App. 2022). The court found coverage...",
        "_score": {
            "tier": "professional",
            "badge": "X",
            "source_class": "court_opinion",
            "is_primary_authority": True,
        },
    }
    info = _extract_case_info(result)
    assert info["name"] == "Smith v. Insurance Co"
    assert info["url"] == "https://scholar.google.com/case"
    assert info["badge"] == "X"
    assert "citation" in info
    assert "year" in info
    assert info["source_tier"] == "professional"


def test_pack_limits_cases() -> None:
    """Pack should return at most 12 cases total."""
    results = [
        {
            "url": f"https://scholar.google.com/case{i}",
            "title": f"Carrier v. Insured {i}",
            "snippet": f"Case {i} snippet",
            "text": f"Carrier v. Insured {i}, 123 So. 3d {400 + i} (Fla. App. 2024).",
            "category": "coverage_law",
        }
        for i in range(30)
    ]
    pack = _assemble_pack(_sample_intake(), results)
    total = sum(len(issue["cases"]) for issue in pack["issues"])
    assert total <= 12


def test_pack_excludes_commentary_titles_from_cases() -> None:
    results = [
        {
            "url": "https://www.jdsupra.com/legalnews/hurricane-irma-the-state-of-concurrent-52284",
            "title": "Hurricane Irma - The State of Concurrent Causation and ACC Clauses in Florida | JD Supra",
            "snippet": "Commentary article citing Sebo",
            "text": "Discusses Sebo, 208 So. 3d 694, and policy clauses.",
            "category": "concurrent_causation",
        },
        {
            "url": "https://casetext.com/case/sebo-v-am-home-assur-co",
            "title": "Sebo v. American Home Assurance Co.",
            "snippet": "Florida concurrent causation case",
            "text": "Sebo v. American Home Assurance Co., 208 So. 3d 694 (Fla. 2016).",
            "category": "concurrent_causation",
        },
    ]

    pack = _assemble_pack(_sample_intake(), results)
    case_names = [case["name"] for issue in pack["issues"] for case in issue["cases"]]

    assert "Sebo v. American Home Assurance Co." in case_names
    assert all("JD Supra" not in name for name in case_names)


def test_pack_dedupes_duplicate_citations_and_prefers_primary_authority() -> None:
    results = [
        {
            "url": "https://casetext.com/case/sebo-v-american-home-assurance-co",
            "title": "Sebo v. American Home Assurance Co.",
            "snippet": "Florida concurrent causation case",
            "text": "Sebo v. American Home Assurance Co., 208 So. 3d 694 (Fla. 2016).",
            "category": "concurrent_causation",
        },
        {
            "url": "https://www.courtlistener.com/opinion/4296801/sebo-v-american-home-assurance-company-inc/",
            "title": "Sebo v. American Home Assurance Company, Inc.",
            "snippet": "Florida concurrent causation case",
            "text": "Sebo v. American Home Assurance Co., 208 So. 3d 694 (Fla. 2016).",
            "category": "concurrent_causation",
        },
    ]

    pack = _assemble_pack(_sample_intake(), results)
    cases = [case for issue in pack["issues"] for case in issue["cases"]]

    assert len(cases) == 1
    assert cases[0]["is_primary_authority"] is True
    assert cases[0]["source_class"] == "court_opinion"
    assert "courtlistener.com" in cases[0]["url"]


def test_pack_prefers_richer_case_metadata_when_authority_class_is_equal() -> None:
    results = [
        {
            "url": "https://www.courtlistener.com/opinion/111/example-v-carrier/",
            "title": "Example v. Carrier",
            "snippet": "thin result",
            "text": "Example v. Carrier.",
            "category": "coverage_law",
        },
        {
            "url": "https://www.courtlistener.com/opinion/222/example-v-carrier-full/",
            "title": "Example v. Carrier",
            "snippet": "full result",
            "text": "Example v. Carrier, 123 So. 3d 456 (Fla. App. 2022).",
            "category": "coverage_law",
        },
    ]

    pack = _assemble_pack(_sample_intake(), results)
    case = pack["issues"][0]["cases"][0]

    assert case["citation"] == "123 So. 3d 456"
    assert case["year"] == "2022"




class _CaselawProvider:
    provider_name = "exa"

    def __init__(self) -> None:
        self.calls = 0

    def search(self, query: str, **kwargs: object) -> list[dict[str, object]]:
        self.calls += 1
        return [{
            "url": f"https://scholar.google.com/case{self.calls}",
            "title": f"Carrier v. Insured {self.calls}",
            "snippet": "Coverage dispute involving wind damage.",
            "text": f"Carrier v. Insured {self.calls}, 123 So. 3d {450 + self.calls} (Fla. App. 2024).",
        }]

    def get_contents(self, urls: list[str], **kwargs: object) -> list[dict[str, object]]:
        return []


def test_build_caselaw_pack_emits_retrieval_state() -> None:
    pack = build_caselaw_pack(
        _sample_intake(),
        client=_CaselawProvider(),
        use_cache=False,
    )

    assert pack["retrieval_tasks"]
    assert all(task["status"] == "completed" for task in pack["retrieval_tasks"])
    assert all(task["stage_id"].endswith(":caselaw") for task in pack["retrieval_tasks"])
    assert len(pack["run_events"]) == len(pack["retrieval_tasks"]) * 2
    assert {event["event_type"] for event in pack["run_events"]} == {"retrieval_started", "retrieval_completed"}


def test_build_caselaw_pack_uses_shared_query_plan(monkeypatch) -> None:
    shared_plan = generate_query_plan(_sample_intake())

    def _unexpected_regeneration(*args: object, **kwargs: object) -> list[object]:
        raise AssertionError("caselaw module regenerated the query plan")

    monkeypatch.setattr("war_room.caselaw_module.generate_query_plan", _unexpected_regeneration)

    provider = _CaselawProvider()
    pack = build_caselaw_pack(
        _sample_intake(),
        client=provider,
        use_cache=False,
        query_plan=shared_plan,
    )

    expected_queries = [query for query in shared_plan if query.module == "caselaw"]
    assert provider.calls == len(expected_queries)
    assert len(pack["retrieval_tasks"]) == len(expected_queries)
    assert all(task["query_text"] in {query.query for query in expected_queries} for task in pack["retrieval_tasks"])

def test_build_caselaw_pack_without_client_returns_structured_fallback() -> None:
    intake = _sample_intake()
    with tempfile.TemporaryDirectory() as cache_dir, tempfile.TemporaryDirectory() as samples_dir:
        pack = build_caselaw_pack(
            intake,
            client=None,
            use_cache=False,
            cache_dir=cache_dir,
            cache_samples_dir=samples_dir,
        )

    assert pack["module"] == "caselaw"
    assert pack["issues"] == []
    assert pack["sources"] == []
    assert "warnings" in pack
    assert any("No Exa client available" in warning for warning in pack["warnings"])
