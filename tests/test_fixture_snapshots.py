"""Golden snapshot tests for committed offline fixture scenarios."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from war_room.fixture_snapshots import (
    DEFAULT_SNAPSHOT_PATH,
    EXPECTED_FIXTURE_STATES,
    build_offline_fixture_snapshot,
    compare_snapshot_file,
    fixture_snapshot_quality_failures,
    main as fixture_snapshot_main,
)

ROOT = Path(__file__).resolve().parent.parent


def test_offline_fixture_golden_snapshot_matches_committed_file():
    snapshot = build_offline_fixture_snapshot(repo_root=ROOT)
    comparison = compare_snapshot_file(snapshot, snapshot_path=ROOT / DEFAULT_SNAPSHOT_PATH)

    assert comparison.matches, comparison.diff
    assert fixture_snapshot_quality_failures(snapshot) == []


def test_offline_fixture_snapshot_quality_assertions_cover_current_scenarios():
    snapshot = build_offline_fixture_snapshot(repo_root=ROOT)

    assert snapshot["schema_version"] == "offline-fixture-snapshots.v1"
    assert snapshot["scenario_count"] == 4
    assert set(snapshot["fixture_states"]) == set(EXPECTED_FIXTURE_STATES)
    assert snapshot["registry_backed_fixture_slugs"] == [
        "ida_orleans_lloyds_ho3",
        "milton_pinellas_citizens_ho3",
        "texas_hail_tarrant_allstate_dp3",
        "texas_hail_tarrant_allstate_hob",
    ]
    assert snapshot["offline_ready_registry_fixture_slugs"] == [
        "ida_orleans_lloyds_ho3",
        "milton_pinellas_citizens_ho3",
        "texas_hail_tarrant_allstate_dp3",
        "texas_hail_tarrant_allstate_hob",
    ]

    for scenario in snapshot["scenarios"]:
        assert scenario["weather_source_count"] >= 3
        assert scenario["carrier_document_count"] >= 3
        assert scenario["caselaw_issue_count"] >= 2
        assert scenario["caselaw_case_count"] >= 3
        assert scenario["citation_summary"]["total"] >= 3
        assert scenario["citation_summary"]["verified"] >= 1
        assert scenario["source_badge_counts"]["official"] >= 1
        assert scenario["source_badge_counts"]["professional"] >= 1
        assert len(scenario["memo_sections"]) == 10
        assert scenario["workflow_status"] == "completed"
        assert scenario["evidence_cluster_count"] >= 1
        assert scenario["issue_workspace_issue_count"] >= 1
        assert scenario["export_eligibility"] == "review_required_export"


def test_offline_fixture_snapshot_cli_check_passes(capsys):
    exit_code = fixture_snapshot_main(
        [
            "--check",
            "--snapshot-path",
            str(DEFAULT_SNAPSHOT_PATH),
        ]
    )

    assert exit_code == 0
    assert "Offline fixture snapshot matches" in capsys.readouterr().out


def test_offline_fixture_snapshot_quality_failures_are_actionable():
    snapshot = build_offline_fixture_snapshot(repo_root=ROOT)
    broken = deepcopy(snapshot)
    broken["scenarios"][0]["citation_summary"]["verified"] = 0
    broken["scenarios"][0]["source_badge_counts"].pop("official", None)

    failures = fixture_snapshot_quality_failures(broken)

    assert any("expected at least one verified citation check" in failure for failure in failures)
    assert any("expected at least one official source badge" in failure for failure in failures)
    assert all(broken["scenarios"][0]["case_key"] in failure for failure in failures)
