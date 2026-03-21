"""Tests for the deterministic offline demo preflight."""

from __future__ import annotations

import json
from pathlib import Path

from war_room.bootstrap import bootstrap_runtime, main as bootstrap_main
from war_room.preflight import render_demo_preflight_report, run_demo_preflight
from war_room.query_plan import build_research_plan, load_case_intake

ROOT = Path(__file__).resolve().parent.parent
REQUIRED_FIXTURE_FILES = ("weather.json", "carrier.json", "caselaw.json", "citation_verify.json")


def _expected_scenario_keys() -> list[str]:
    cache_samples_dir = ROOT / "cache_samples"
    return sorted(
        path.name
        for path in cache_samples_dir.iterdir()
        if path.is_dir() and all((path / filename).exists() for filename in REQUIRED_FIXTURE_FILES)
    )


def test_demo_preflight_smoke_covers_committed_scenarios():
    context = bootstrap_runtime(start_path=ROOT, ensure_dirs=False)

    report = run_demo_preflight(context)

    assert report.scenario_count == len(_expected_scenario_keys())
    assert report.passed is True

    scenario_keys = [scenario.case_key for scenario in report.scenarios]
    assert scenario_keys == _expected_scenario_keys()
    assert report.scenarios[scenario_keys.index("milton_citizens_pinellas")].intake_path == "scenario:milton_pinellas_citizens_ho3"

    for scenario in report.scenarios:
        assert scenario.availability.status == "offline-ready"
        assert scenario.workflow_status == "completed"
        assert scenario.workflow_review_required is True
        assert "citation_verify=degraded" in scenario.workflow_stage_statuses
        assert "memo_assembly=degraded" in scenario.workflow_stage_statuses
        assert scenario.evidence_cluster_count > 0
        assert scenario.evidence_review_required_cluster_count > 0
        check_names = {check.name for check in scenario.checks}
        assert "intake payload loads" in check_names
        assert "memo includes disclaimer language" in check_names
        assert "memo includes expected major sections" in check_names
        assert scenario.memo_length > 0
        assert len(scenario.memo_sections) == 10
    assert any("Registry scenario" in scenario.availability.detail for scenario in report.scenarios)
    assert any("No registry scenario maps" in scenario.availability.detail for scenario in report.scenarios)


def test_demo_preflight_rendering_includes_summary():
    context = bootstrap_runtime(start_path=ROOT, ensure_dirs=False)
    report = run_demo_preflight(context)

    rendered = render_demo_preflight_report(report)

    assert "# Demo Preflight" in rendered
    assert f"Scenario count: {len(_expected_scenario_keys())}" in rendered
    assert "ida_lloyds_orleans" in rendered
    assert "Passed: Yes" in rendered
    assert "Availability: offline-ready" in rendered
    assert "Workflow: completed | review_required=yes" in rendered
    assert "Evidence board:" in rendered
    assert "Registry scenario" in rendered


def test_bootstrap_cli_preflight_json_output(monkeypatch, capsys):
    monkeypatch.chdir(ROOT)

    exit_code = bootstrap_main(["--preflight", "--json"])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["passed"] is True
    assert payload["scenario_count"] == len(_expected_scenario_keys())
    assert len(payload["scenarios"]) == len(_expected_scenario_keys())
    assert payload["scenarios"][0]["availability"]["status"] == "offline-ready"
    assert payload["scenarios"][0]["workflow_status"] == "completed"
    assert payload["scenarios"][0]["evidence_cluster_count"] > 0


def test_demo_preflight_reuses_one_shared_query_plan(monkeypatch):
    context = bootstrap_runtime(start_path=ROOT, ensure_dirs=False)
    scenario_dir = ROOT / "cache_samples" / "milton_citizens_pinellas"
    intake = load_case_intake(ROOT / "eval" / "intakes" / "tx_hail_allstate_tarrant.json")
    research_plan = build_research_plan(intake)
    observed_query_plans: list[object] = []

    monkeypatch.setattr("war_room.preflight._discover_scenario_dirs", lambda cache_samples_dir: [scenario_dir])
    monkeypatch.setattr(
        "war_room.preflight._load_intake",
        lambda case_key, intake_path, repo_root: (intake, str(intake_path)),
    )
    monkeypatch.setattr(
        "war_room.preflight.build_research_plan",
        lambda payload: research_plan,
    )

    def _weather(intake_arg, client, **kwargs):
        observed_query_plans.append(kwargs.get("query_plan"))
        return {"module": "weather", "sources": [{"url": "https://example.com"}]}

    def _carrier(intake_arg, client, **kwargs):
        observed_query_plans.append(kwargs.get("query_plan"))
        return {"module": "carrier", "document_pack": [{"url": "https://example.com"}]}

    def _caselaw(intake_arg, client, **kwargs):
        observed_query_plans.append(kwargs.get("query_plan"))
        return {"module": "caselaw", "issues": [{"issue": "Coverage", "cases": []}]}

    monkeypatch.setattr("war_room.preflight.build_weather_brief", _weather)
    monkeypatch.setattr("war_room.preflight.build_carrier_doc_pack", _carrier)
    monkeypatch.setattr("war_room.preflight.build_caselaw_pack", _caselaw)
    monkeypatch.setattr(
        "war_room.preflight.render_markdown_memo",
        lambda intake_arg, weather, carrier, caselaw, citecheck, query_plan: "\n".join(
            [
                "DRAFT - ATTORNEY WORK PRODUCT",
                "DEMO RESEARCH MEMO - VERIFY CITATIONS - NOT LEGAL ADVICE",
                "DRAFT - ATTORNEY WORK PRODUCT - VERIFY ALL CITATIONS",
                *[
                    section
                    for section in (
                        "## Trust Snapshot",
                        "## Case Intake",
                        "## Weather Corroboration",
                        "## Carrier Document Pack",
                        "## Case Law",
                        "## Appendix: Query Plan",
                        "## Appendix: Evidence Clusters",
                        "## Appendix: Evidence Index",
                        "## Appendix: All Sources",
                        "## Methodology & Limitations",
                    )
                ],
            ]
        )
        if query_plan == research_plan.query_plan
        else "",
    )
    monkeypatch.setattr(
        "war_room.preflight.build_run_timeline",
        lambda *args, **kwargs: (
            type("RunRecord", (), {"status": "completed", "review_required": False})(),
            [type("RunStageRecord", (), {"stage_key": "memo_assembly", "status": "completed"})()],
        ),
    )
    monkeypatch.setattr(
        "war_room.preflight.build_evidence_board_from_parts",
        lambda *args, **kwargs: type(
            "EvidenceBoardRecord",
            (),
            {"total_clusters": 3, "review_required_clusters": 1},
        )(),
    )

    report = run_demo_preflight(context)

    assert report.passed is True
    assert len(observed_query_plans) == 3
    assert all(query_plan == research_plan.query_plan for query_plan in observed_query_plans)
    assert report.scenarios[0].workflow_status == "completed"
    assert report.scenarios[0].evidence_cluster_count == 3
