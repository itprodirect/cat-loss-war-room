"""Tests for export_md module - no network calls."""

import tempfile

from war_room.export_md import render_markdown_memo, write_markdown
from war_room.models import CaseIntake, QuerySpec


def _sample_data():
    intake = CaseIntake(
        event_name="Hurricane Milton",
        event_date="2024-10-09",
        state="FL",
        county="Pinellas",
        carrier="Citizens Property Insurance",
        policy_type="HO-3 Dwelling",
        posture=["denial"],
    )
    weather = {
        "module": "weather",
        "event_summary": "Hurricane Milton - Pinellas County, FL",
        "key_observations": ["Winds of 120 mph"],
        "metrics": {"max_wind_mph": 120, "storm_surge_ft": None, "rain_in": None},
        "sources": [
            {
                "title": "NWS Report",
                "url": "https://weather.gov/r",
                "badge": "official",
                "reason": "Official source",
            }
        ],
    }
    carrier = {
        "module": "carrier",
        "carrier_snapshot": {
            "name": "Citizens",
            "state": "FL",
            "event": "Milton",
            "policy_type": "HO-3",
        },
        "document_pack": [
            {
                "doc_type": "Denial",
                "title": "Doc",
                "url": "https://example.com",
                "badge": "professional",
                "why_it_matters": "Relevant",
            }
        ],
        "common_defenses": ["Pre-existing damage"],
        "rebuttal_angles": ["Timeline contradicts carrier position"],
        "sources": [
            {
                "title": "Article",
                "url": "https://example.com",
                "badge": "professional",
                "reason": "Professional source",
            }
        ],
    }
    caselaw = {
        "module": "caselaw",
        "issues": [
            {
                "issue": "Coverage",
                "cases": [
                    {
                        "name": "Doe v. Ins",
                        "citation": "123 So.3d 456",
                        "court": "Fla. App.",
                        "year": "2023",
                        "one_liner": "Coverage upheld",
                        "url": "https://example.com",
                        "badge": "professional",
                    }
                ],
                "notes": ["Relevant"],
            }
        ],
        "sources": [
            {
                "title": "Case",
                "url": "https://example.com/c",
                "badge": "professional",
                "reason": "Professional source",
            }
        ],
    }
    citecheck = {
        "module": "citation_verify",
        "disclaimer": "SPOT-CHECK ONLY",
        "checks": [
            {
                "badge": "verified",
                "case_name": "Doe v. Ins",
                "citation": "123 So.3d 456",
                "status": "verified",
                "note": "Found on official source",
            }
        ],
        "summary": {"total": 1, "verified": 1, "uncertain": 0, "not_found": 0},
    }
    queries = [QuerySpec(module="weather", query="test query", category="test")]
    return intake, weather, carrier, caselaw, citecheck, queries


def test_render_contains_all_sections():
    md = render_markdown_memo(*_sample_data())
    assert "DRAFT" in md
    assert "ATTORNEY WORK PRODUCT" in md
    assert "DEMO RESEARCH MEMO" in md
    assert "Trust Snapshot" in md
    assert "Case Intake" in md
    assert "Weather Corroboration" in md
    assert "Carrier Document Pack" in md
    assert "Case Law" in md
    assert "Citation Spot-Check" in md
    assert "Query Plan" in md
    assert "Evidence Clusters" in md
    assert "Evidence Index" in md
    assert "All Sources" in md
    assert "Methodology" in md


def test_render_contains_case_details():
    md = render_markdown_memo(*_sample_data())
    assert "Hurricane Milton" in md
    assert "Citizens" in md
    assert "Pinellas" in md


def test_render_includes_trust_snapshot_and_source_reasons():
    md = render_markdown_memo(*_sample_data())
    assert "Weather sources: 1" in md
    assert "Carrier documents: 1" in md
    assert "Case authorities: 1" in md
    assert "Professional source" in md


def test_render_surfaces_review_flags_when_present():
    intake, weather, carrier, caselaw, citecheck, queries = _sample_data()
    weather["warnings"] = ["County-specific weather corroboration is limited."]
    citecheck["summary"] = {"total": 1, "verified": 0, "uncertain": 1, "not_found": 0}

    md = render_markdown_memo(intake, weather, carrier, caselaw, citecheck, queries)

    assert "Review Required" in md
    assert "Weather: County-specific weather corroboration is limited." in md
    assert "Citation review: 1 uncertain and 0 not found entries require manual verification." in md
    assert "Appendix: Review Log" in md
    assert "Citation review required" in md
    assert "Evidence clusters: cluster-1" in md
    assert "Evidence clusters: cluster-3" in md


def test_render_includes_evidence_clusters():
    md = render_markdown_memo(*_sample_data())

    assert "cluster-1" in md
    assert "cluster-2" in md
    assert "cluster-3" in md
    assert "citation | 123 So.3d 456" in md


def test_render_surfaces_claim_cluster_references():
    md = render_markdown_memo(*_sample_data())

    assert "> Claim status: supported | Evidence clusters: cluster-1" in md
    assert "> Claim status: supported | Evidence clusters: cluster-3" in md


def test_render_includes_canonical_evidence_index_rows():
    md = render_markdown_memo(*_sample_data())

    assert "weather-source-1" in md
    assert "carrier-document-1" in md
    assert "caselaw-case-1-1" in md
    assert "citation-check-1" in md


def test_render_accepts_dict_intake_and_query_specs():
    intake, weather, carrier, caselaw, citecheck, queries = _sample_data()

    md = render_markdown_memo(
        intake.model_dump(),
        weather,
        carrier,
        caselaw,
        citecheck,
        [queries[0].model_dump()],
    )

    assert "Case Intake" in md
    assert "Total queries: 1" in md


def test_write_markdown_creates_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = write_markdown(tmpdir, "test_case", "# Test Memo\nContent here")
        assert path.exists()
        assert path.read_text(encoding="utf-8").startswith("# Test Memo")
        assert "test_case" in path.name
