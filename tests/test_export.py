"""Tests for export_md module - no network calls."""

import tempfile
from pathlib import Path

from war_room.carrier_module import build_carrier_doc_pack
from war_room.caselaw_module import build_caselaw_pack
from war_room.citation_verify import spot_check_citations
from war_room.export_md import _append_review_log, render_markdown_memo, write_markdown
from war_room.models import (
    CaseIntake,
    QuerySpec,
    ReviewEvent,
    citation_verify_pack_to_evidence_items,
)
from war_room.query_plan import generate_query_plan
from war_room.weather_module import build_weather_brief


ROOT = Path(__file__).resolve().parent.parent
CACHE_SAMPLES_ROOT = ROOT / "cache_samples"

_MILTON_EXPORT_NOISE_MARKERS = (
    "\u00e2\u20ac",  # Common UTF-8 mojibake prefix: â€...
    "\u00f0\u0178",  # Common emoji mojibake prefix: ðŸ...
    "CONTINUE TO SITE",
    "Skip Navigation",
    "Mobile Site",
    "Text Version",
    "| Casetext Search + Citator",
    "Citing Cases",
    "[![Skip Navigation Links]]",
    "Hurricane Costs",
    "News and Media: Disaster 4834",
    "DR-4834 Public Notice 001",
    "Potentially relevant carrier document",
)


class _FixtureProvider:
    provider_name = "fixture"


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


def _milton_fixture_memo() -> str:
    intake = CaseIntake(
        event_name="Hurricane Milton",
        event_date="2024-10-09",
        state="FL",
        county="Pinellas",
        carrier="Citizens Property Insurance",
        policy_type="HO-3 Dwelling",
        posture=["denial", "bad_faith"],
        key_facts=[
            "Category 3 at landfall near Siesta Key",
            "Roof damage and water intrusion reported within 48 hours",
            "Claim denied citing pre-existing conditions",
        ],
        coverage_issues=[
            "wind vs water causation",
            "anti-concurrent causation clause",
            "duty to investigate",
        ],
    )
    cache_samples_dir = str(CACHE_SAMPLES_ROOT)
    query_plan = generate_query_plan(intake)
    weather = build_weather_brief(
        intake,
        None,
        query_plan=query_plan,
        cache_samples_dir=cache_samples_dir,
    )
    carrier = build_carrier_doc_pack(
        intake,
        None,
        query_plan=query_plan,
        cache_samples_dir=cache_samples_dir,
    )
    caselaw = build_caselaw_pack(
        intake,
        None,
        query_plan=query_plan,
        cache_samples_dir=cache_samples_dir,
    )
    citecheck = spot_check_citations(
        caselaw,
        _FixtureProvider(),
        cache_samples_dir=cache_samples_dir,
    )

    return render_markdown_memo(intake, weather, carrier, caselaw, citecheck, query_plan)


def _markdown_table_blocks(markdown: str) -> list[list[str]]:
    blocks: list[list[str]] = []
    current: list[str] = []
    for line in markdown.splitlines():
        if line.startswith("|"):
            current.append(line)
            continue
        if current:
            blocks.append(current)
            current = []
    if current:
        blocks.append(current)
    return blocks


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
    assert "Quality Snapshot" in md
    assert "Evidence Clusters" in md
    assert "Evidence Index" in md
    assert "All Sources" in md
    assert "Methodology" in md


def test_milton_fixture_render_is_demo_readable():
    md = _milton_fixture_memo()

    assert "DEMO RESEARCH MEMO - VERIFY CITATIONS - NOT LEGAL ADVICE" in md
    assert "Hurricane Milton" in md
    assert "Pinellas County, FL" in md
    assert "Citizens Property Insurance" in md
    assert "## Weather Corroboration" in md
    assert "## Carrier Document Pack" in md
    assert "## Case Law" in md
    assert "### Citation Spot-Check" in md

    for marker in _MILTON_EXPORT_NOISE_MARKERS:
        assert marker not in md


def test_milton_fixture_render_keeps_markdown_tables_aligned():
    md = _milton_fixture_memo()

    for block in _markdown_table_blocks(md):
        pipe_counts = {line.count("|") for line in block}
        assert len(pipe_counts) == 1, block


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
    assert "Sources by class:" in md
    assert "Primary vs secondary:" in md
    assert "Canonical authorities:" in md
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


def test_render_escapes_markdown_in_review_flags_warnings_and_source_reasons():
    intake, weather, carrier, caselaw, citecheck, queries = _sample_data()
    weather["warnings"] = ["## Injected heading <script>alert(1)</script> [click](https://evil)"]
    weather["sources"][0]["reason"] = "![img](x) <img src=x onerror=alert(1)>"

    md = render_markdown_memo(intake, weather, carrier, caselaw, citecheck, queries)

    assert (
        "- Weather: \\#\\# Injected heading &lt;script&gt;alert\\(1\\)&lt;/script&gt; "
        "click\\(https://evil\\)"
    ) in md
    assert (
        "- \\#\\# Injected heading &lt;script&gt;alert\\(1\\)&lt;/script&gt; "
        "click\\(https://evil\\)"
    ) in md
    assert "\\!img\\(x\\) &lt;img src=x onerror=alert\\(1\\)&gt;" in md
    assert "<script>" not in md
    assert "<img src=x onerror=alert(1)>" not in md


def test_render_includes_evidence_clusters():
    md = render_markdown_memo(*_sample_data())

    assert "cluster-1" in md
    assert "cluster-2" in md
    assert "cluster-3" in md
    assert "Members" in md
    assert "Provenance URLs" in md
    assert "citation | 123 so. 3d 456" in md


def test_render_shows_citation_confidence_and_source_type_columns():
    md = render_markdown_memo(*_sample_data())

    assert "| Badge | Case | Citation | Confidence | Source Type | Note |" in md
    assert "unknown" in md


def test_render_shows_canonical_authority_and_alternate_counts():
    intake, weather, carrier, caselaw, citecheck, queries = _sample_data()
    citecheck["checks"][0]["alternate_candidate_count"] = 2

    md = render_markdown_memo(intake, weather, carrier, caselaw, citecheck, queries)

    assert "duplicates collapsed 1" in md
    assert "Alternate aligned candidates: 2" in md


def test_render_sanitizes_multiline_export_text_and_backfills_citation_reasoning():
    intake, weather, carrier, caselaw, citecheck, queries = _sample_data()
    weather["key_observations"] = ["Line one\nLine two [Home] | extra"]
    carrier["document_pack"][0]["title"] = "Doc line 1\nDoc line 2"
    carrier["document_pack"][0]["why_it_matters"] = "Relevant |\nwith break"
    caselaw["issues"][0]["cases"][0]["court"] = "Fla. App.\nSecond DCA"
    caselaw["issues"][0]["cases"][0]["one_liner"] = "Coverage upheld\nwith note"
    citecheck["checks"][0]["status"] = "uncertain"
    citecheck["checks"][0]["badge"] = "warning"
    citecheck["checks"][0]["source_url"] = "https://casetext.com/case/doe-v-ins"
    citecheck["checks"][0]["note"] = "Found on professional source: casetext.com - verify independently"
    citecheck["summary"] = {"total": 1, "verified": 0, "uncertain": 1, "not_found": 0}

    md = render_markdown_memo(intake, weather, carrier, caselaw, citecheck, queries)

    assert "- Line one Line two Home | extra" in md
    assert "| 1 | Denial | [Doc line 1 Doc line 2](https://example.com) | professional | Relevant / with break |" in md
    assert "- professional **Doe v. Ins** - 123 So.3d 456 (Fla. App. Second DCA, 2023)" in md
    assert "  - Coverage upheld with note" in md
    assert "- Reasons: secondary authority match 1" in md
    assert "| warning | Doe v. Ins | 123 So.3d 456 | medium | court opinion |" in md


def test_render_surfaces_claim_cluster_references():
    md = render_markdown_memo(*_sample_data())

    assert "> Claim status: supported | Evidence clusters: cluster-1" in md
    assert "> Claim status: supported | Evidence clusters: cluster-3" in md


def test_render_includes_canonical_evidence_index_rows():
    sample_data = _sample_data()
    citation_evidence_id = (
        citation_verify_pack_to_evidence_items(sample_data[4])[0].evidence_id
    )
    md = render_markdown_memo(*sample_data)

    assert "weather-source-nws-report-" in md
    assert "carrier-document-denial-" in md
    assert "caselaw-case-123-so-3d-456-" in md
    assert citation_evidence_id in md
    assert "| citation-check-1 |" not in md


def test_render_sanitizes_evidence_index_review_log_and_unsafe_urls():
    intake, weather, carrier, caselaw, citecheck, queries = _sample_data()
    weather["warnings"] = ["## Needs review [link](javascript:alert(2)) <b>"]
    citecheck["checks"][0]["case_name"] = "Legit *Case* <b>"
    citecheck["checks"][0]["badge"] = "verified|<script>"
    citecheck["checks"][0]["source_url"] = "javascript:alert(1)"
    citecheck["checks"][0]["status"] = "uncertain"
    citecheck["summary"] = {"total": 1, "verified": 0, "uncertain": 1, "not_found": 0}
    citation_evidence_id = citation_verify_pack_to_evidence_items(citecheck)[0].evidence_id

    md = render_markdown_memo(intake, weather, carrier, caselaw, citecheck, queries)
    evidence_index = md.split("## Appendix: Evidence Index", 1)[1].split(
        "## Appendix: Review Log", 1
    )[0]

    assert (
        f"| {citation_evidence_id} | citation_verify | citation_check | "
        "Legit \\*Case\\* &lt;b&gt; | verified/&lt;script&gt; |  |"
    ) in evidence_index
    assert (
        "**Weather review required:** \\#\\# Needs review "
        "link\\(javascript:alert\\(2\\)\\) &lt;b&gt;"
    ) in md
    assert "javascript:alert(1)" not in evidence_index
    assert "<script>" not in evidence_index
    assert "<b>" not in md


def test_append_review_log_escapes_label_and_detail_fields():
    lines: list[str] = []
    _append_review_log(
        lines,
        [
            ReviewEvent(
                event_id="review-injection",
                event_type="warning",
                label="**Injected** <b>",
                detail="[link](javascript:alert(1)) <img>",
                related_cluster_ids=["cluster-1"],
            )
        ],
    )

    rendered = "\n".join(lines)

    assert (
        "- **\\*\\*Injected\\*\\* &lt;b&gt;:** "
        "link\\(javascript:alert\\(1\\)\\) &lt;img&gt; "
        "| Evidence clusters: cluster-1"
    ) in rendered


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


def test_render_escapes_entity_decoded_html_payloads():
    intake, weather, carrier, caselaw, citecheck, queries = _sample_data()
    payload = "&lt;img src=x onerror=alert(1)&gt;"
    weather["sources"][0]["title"] = payload
    carrier["document_pack"][0]["title"] = payload
    caselaw["issues"][0]["cases"][0]["name"] = payload

    md = render_markdown_memo(intake, weather, carrier, caselaw, citecheck, queries)

    assert "&lt;img src=x onerror=alert(1)&gt;" in md
    assert "<img src=x onerror=alert(1)>" not in md


def test_write_markdown_creates_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = write_markdown(tmpdir, "test_case", "# Test Memo\nContent here")
        assert path.exists()
        assert path.read_text(encoding="utf-8").startswith("# Test Memo")
        assert "test_case" in path.name
