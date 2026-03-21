"""Tests for the curated benchmark scenario registry."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from war_room.scenarios import (
    ScenarioValidationError,
    default_scenario_id,
    list_scenarios,
    load_scenario,
    load_scenario_for_fixture_case,
    scenarios_dir,
    validate_scenario,
)

ROOT = Path(__file__).resolve().parent.parent
NOTEBOOK_PATH = ROOT / "notebooks" / "01_case_war_room.ipynb"


def test_list_scenarios_returns_curated_registry_order():
    scenarios = list_scenarios(repo_root=ROOT)

    assert [scenario.slug for scenario in scenarios] == [
        "milton_pinellas_citizens_ho3",
        "ian_lee_citizens_ho3",
        "irma_monroe_citizens_ho3",
        "michael_bay_default_ho3",
        "idalia_taylor_default_ho3",
    ]
    assert default_scenario_id(repo_root=ROOT) == "milton_pinellas_citizens_ho3"


def test_load_scenario_returns_case_intake_compatible_payload():
    scenario = load_scenario("ian_lee_citizens_ho3", repo_root=ROOT)

    intake = scenario.to_case_intake()

    assert intake.event_name == "Hurricane Ian"
    assert intake.county == "Lee"
    assert intake.posture == ["denial", "underpayment"]
    assert "scope of repair" in intake.coverage_issues


def test_load_scenario_supports_case_intake_overrides():
    scenario = load_scenario("michael_bay_default_ho3", repo_root=ROOT)

    intake = scenario.to_case_intake({"coverage_issues": ["matching", "scope of repair"]})

    assert intake.coverage_issues == ["matching", "scope of repair"]


def test_validate_scenario_rejects_invalid_case_intake_fields():
    payload = load_scenario("milton_pinellas_citizens_ho3", repo_root=ROOT).model_dump()
    payload["posture"] = ["bad faith"]

    with pytest.raises(ScenarioValidationError, match="Invalid CaseIntake fields"):
        validate_scenario(payload)


def test_validate_scenario_rejects_unknown_metadata_fields():
    payload = load_scenario("milton_pinellas_citizens_ho3", repo_root=ROOT).model_dump()
    payload["claim_number"] = "12345"

    with pytest.raises(ScenarioValidationError, match="Invalid scenario payload"):
        validate_scenario(payload)


def test_load_scenario_for_fixture_case_returns_registry_backed_benchmark():
    scenario = load_scenario_for_fixture_case("milton_citizens_pinellas", repo_root=ROOT)

    assert scenario is not None
    assert scenario.slug == "milton_pinellas_citizens_ho3"
    assert scenario.offline_demo_ready is True


def test_all_committed_scenario_files_are_valid():
    scenario_paths = sorted(path for path in scenarios_dir(ROOT).glob("*.json") if path.name != "index.json")

    assert len(scenario_paths) == 5

    for path in scenario_paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        scenario = validate_scenario(payload, path=path)
        assert scenario.slug == path.stem
        assert scenario.tags
        assert scenario.notes


def test_notebook_default_scenario_exists_in_registry():
    notebook = json.loads(NOTEBOOK_PATH.read_text(encoding="utf-8"))
    cell_sources = ["".join(cell.get("source", [])) for cell in notebook["cells"] if cell.get("cell_type") == "code"]
    scenario_cell = next(source for source in cell_sources if "SCENARIO_ID" in source)

    assert 'SCENARIO_ID = "milton_pinellas_citizens_ho3"' in scenario_cell


def test_notebook_uses_helper_driven_scenario_prep_and_has_no_stale_hardcoded_intake():
    notebook = json.loads(NOTEBOOK_PATH.read_text(encoding="utf-8"))
    code_cells = ["".join(cell.get("source", [])) for cell in notebook["cells"] if cell.get("cell_type") == "code"]
    scenario_cells = [source for source in code_cells if "SCENARIO_ID" in source]
    query_cells = [source for source in code_cells if "Query Plan Generation" in source]

    assert len(scenario_cells) == 1
    assert len(query_cells) == 1
    assert "prepare_notebook_scenario" in scenario_cells[0]
    assert "SETTINGS.live_retrieval_enabled" not in scenario_cells[0]
    assert "build_research_plan" in query_cells[0]
    assert "format_research_plan_preview" in query_cells[0]
    assert "build_evidence_board_from_parts" in "".join(code_cells)
    assert "format_evidence_board" in "".join(code_cells)
    assert "build_issue_workspace_from_parts" in "".join(code_cells)
    assert "format_issue_workspace" in "".join(code_cells)
    assert "build_memo_composer_from_parts" in "".join(code_cells)
    assert "format_memo_composer" in "".join(code_cells)
    assert "build_run_timeline" in "".join(code_cells)
    assert "format_run_timeline" in "".join(code_cells)
    assert 'query_plan=queries' in "".join(code_cells)
    assert sum("CaseIntake(" in source for source in code_cells) == 0
    assert sum("write_markdown(" in source for source in code_cells) == 1
