"""Golden snapshots for committed offline fixture scenarios."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from dataclasses import dataclass
from difflib import unified_diff
from pathlib import Path
from typing import Any

from war_room.bootstrap import BootstrapContext, bootstrap_runtime, discover_repo_root
from war_room.preflight import run_demo_preflight
from war_room.query_plan import load_case_intake
from war_room.scenarios import (
    load_scenario_for_fixture_case,
)

SNAPSHOT_SCHEMA_VERSION = "offline-fixture-snapshots.v1"
DEFAULT_SNAPSHOT_PATH = Path("tests/golden/offline_fixture_snapshots.json")
REQUIRED_FIXTURE_FILES = ("weather.json", "carrier.json", "caselaw.json", "citation_verify.json")
EXPECTED_FIXTURE_STATES = ("FL", "TX", "LA")
EXPECTED_MEMO_SECTIONS = (
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


@dataclass(frozen=True)
class SnapshotComparison:
    """Result of comparing a generated snapshot to a committed golden file."""

    matches: bool
    diff: str = ""


def build_offline_fixture_snapshot(
    context: BootstrapContext | None = None,
    *,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    """Build a deterministic snapshot for every committed offline fixture scenario."""

    resolved_context = context or bootstrap_runtime(
        start_path=repo_root or discover_repo_root(),
        ensure_dirs=False,
    )
    preflight_report = run_demo_preflight(resolved_context)
    preflight_by_case_key = {
        scenario.case_key: scenario
        for scenario in preflight_report.scenarios
    }
    scenarios = [
        _scenario_snapshot(resolved_context, scenario_dir, preflight_by_case_key.get(scenario_dir.name))
        for scenario_dir in _discover_fixture_dirs(resolved_context.settings.cache_samples_dir)
    ]
    registry_backed = [
        scenario["registry_slug"]
        for scenario in scenarios
        if scenario["registry_slug"]
    ]
    offline_ready_registry = [
        scenario["registry_slug"]
        for scenario in scenarios
        if scenario["registry_offline_ready"]
    ]
    return {
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "scenario_count": len(scenarios),
        "fixture_states": sorted({scenario["state"] for scenario in scenarios if scenario["state"]}),
        "registry_backed_fixture_count": len(registry_backed),
        "registry_backed_fixture_slugs": sorted(registry_backed),
        "offline_ready_registry_fixture_count": len(offline_ready_registry),
        "offline_ready_registry_fixture_slugs": sorted(offline_ready_registry),
        "scenarios": scenarios,
    }


def fixture_snapshot_quality_failures(snapshot: dict[str, Any]) -> list[str]:
    """Return human-readable failures for #8 fixture quality thresholds."""

    failures: list[str] = []
    scenarios = list(snapshot.get("scenarios") or [])
    scenario_count = int(snapshot.get("scenario_count") or 0)
    fixture_states = set(snapshot.get("fixture_states") or [])
    if scenario_count < 5:
        failures.append(f"scenario_count expected >= 5, got {scenario_count}")
    missing_states = sorted(set(EXPECTED_FIXTURE_STATES) - fixture_states)
    if missing_states:
        failures.append(f"fixture_states missing {', '.join(missing_states)}")
    if int(snapshot.get("registry_backed_fixture_count") or 0) < 1:
        failures.append("expected at least one registry-backed fixture scenario")
    if int(snapshot.get("offline_ready_registry_fixture_count") or 0) < 1:
        failures.append("expected at least one offline-ready registry fixture scenario")

    for scenario in scenarios:
        case_key = str(scenario.get("case_key") or "unknown")
        module_files = scenario.get("module_files") or []
        if module_files != list(REQUIRED_FIXTURE_FILES):
            failures.append(f"{case_key}: module_files must be {', '.join(REQUIRED_FIXTURE_FILES)}")
        if int(scenario.get("weather_source_count") or 0) < 3:
            failures.append(f"{case_key}: expected at least 3 weather sources")
        if int(scenario.get("carrier_document_count") or 0) < 3:
            failures.append(f"{case_key}: expected at least 3 carrier documents")
        if int(scenario.get("caselaw_issue_count") or 0) < 2:
            failures.append(f"{case_key}: expected at least 2 case-law issue buckets")
        if int(scenario.get("caselaw_case_count") or 0) < 3:
            failures.append(f"{case_key}: expected at least 3 case-law cases")

        citation_summary = scenario.get("citation_summary") or {}
        citation_total = int(citation_summary.get("total") or 0)
        verified = int(citation_summary.get("verified") or 0)
        uncertain = int(citation_summary.get("uncertain") or 0)
        not_found = int(citation_summary.get("not_found") or 0)
        if citation_total < 3:
            failures.append(f"{case_key}: expected at least 3 citation checks")
        if citation_total != verified + uncertain + not_found:
            failures.append(f"{case_key}: citation summary is not internally consistent")
        if verified < 1:
            failures.append(f"{case_key}: expected at least one verified citation check")

        source_badges = scenario.get("source_badge_counts") or {}
        if int(source_badges.get("official") or 0) < 1:
            failures.append(f"{case_key}: expected at least one official source badge")
        if int(source_badges.get("professional") or 0) < 1:
            failures.append(f"{case_key}: expected at least one professional source badge")

        memo_sections = scenario.get("memo_sections") or []
        if memo_sections != list(EXPECTED_MEMO_SECTIONS):
            failures.append(f"{case_key}: memo section snapshot changed")
        if scenario.get("workflow_status") != "completed":
            failures.append(f"{case_key}: workflow_status expected completed")
        if int(scenario.get("evidence_cluster_count") or 0) < 1:
            failures.append(f"{case_key}: expected evidence clusters")
        if int(scenario.get("issue_workspace_issue_count") or 0) < 1:
            failures.append(f"{case_key}: expected issue workspace issues")
        if scenario.get("export_eligibility") != "review_required_export":
            failures.append(f"{case_key}: export_eligibility expected review_required_export")

    return failures


def compare_snapshot_file(
    snapshot: dict[str, Any],
    *,
    snapshot_path: Path,
) -> SnapshotComparison:
    """Compare a generated snapshot to a committed golden JSON file."""

    expected_text = snapshot_path.read_text(encoding="utf-8")
    actual_text = snapshot_to_json(snapshot)
    if expected_text == actual_text:
        return SnapshotComparison(matches=True)
    diff = "".join(
        unified_diff(
            expected_text.splitlines(keepends=True),
            actual_text.splitlines(keepends=True),
            fromfile=str(snapshot_path),
            tofile="generated offline fixture snapshot",
        )
    )
    return SnapshotComparison(matches=False, diff=diff)


def write_snapshot_file(
    snapshot: dict[str, Any],
    *,
    snapshot_path: Path,
) -> Path:
    """Write a deterministic golden snapshot JSON file."""

    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    snapshot_path.write_text(snapshot_to_json(snapshot), encoding="utf-8")
    return snapshot_path


def snapshot_to_json(snapshot: dict[str, Any]) -> str:
    """Serialize a snapshot with stable formatting."""

    return json.dumps(snapshot, indent=2, sort_keys=True) + "\n"


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for checking or refreshing offline fixture snapshots."""

    parser = argparse.ArgumentParser(description="Check committed offline fixture golden snapshots")
    parser.add_argument(
        "--snapshot-path",
        default=str(DEFAULT_SNAPSHOT_PATH),
        help="Path to the committed golden snapshot JSON file.",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--write",
        action="store_true",
        help="Refresh the golden snapshot file instead of checking it.",
    )
    mode.add_argument(
        "--check",
        action="store_true",
        help="Check the committed snapshot. This is the default when --write is omitted.",
    )
    args = parser.parse_args(argv)

    context = bootstrap_runtime(ensure_dirs=False)
    snapshot_path = (context.repo_root / args.snapshot_path).resolve()
    snapshot = build_offline_fixture_snapshot(context)
    failures = fixture_snapshot_quality_failures(snapshot)
    if failures:
        print("Offline fixture snapshot quality checks failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    if args.write:
        write_snapshot_file(snapshot, snapshot_path=snapshot_path)
        print(f"Wrote offline fixture snapshot: {snapshot_path}")
        return 0

    comparison = compare_snapshot_file(snapshot, snapshot_path=snapshot_path)
    if not comparison.matches:
        print("Offline fixture snapshot differs from committed golden file.")
        print(comparison.diff, end="")
        print("Refresh intentionally with: python -m war_room.fixture_snapshots --write")
        return 1

    print(f"Offline fixture snapshot matches: {snapshot_path}")
    return 0


def _discover_fixture_dirs(cache_samples_dir: Path) -> list[Path]:
    if not cache_samples_dir.exists():
        return []
    return [
        candidate
        for candidate in sorted(path for path in cache_samples_dir.iterdir() if path.is_dir())
        if all((candidate / filename).exists() for filename in REQUIRED_FIXTURE_FILES)
    ]


def _scenario_snapshot(
    context: BootstrapContext,
    scenario_dir: Path,
    preflight_scenario,
) -> dict[str, Any]:
    case_key = scenario_dir.name
    registry_scenario = load_scenario_for_fixture_case(case_key, repo_root=context.repo_root)
    if registry_scenario is not None:
        intake = registry_scenario.to_case_intake()
        intake_ref = f"scenario:{registry_scenario.slug}"
        registry_slug = registry_scenario.slug
        registry_offline_ready = registry_scenario.offline_demo_ready
    else:
        intake_path = context.repo_root / "eval" / "intakes" / f"{case_key}.json"
        intake = load_case_intake(intake_path)
        intake_ref = intake_path.relative_to(context.repo_root).as_posix()
        registry_slug = None
        registry_offline_ready = False

    weather = _load_json(scenario_dir / "weather.json")
    carrier = _load_json(scenario_dir / "carrier.json")
    caselaw = _load_json(scenario_dir / "caselaw.json")
    citation_verify = _load_json(scenario_dir / "citation_verify.json")

    citation_summary = citation_verify.get("summary", {}) if isinstance(citation_verify, dict) else {}
    return {
        "case_key": case_key,
        "registry_slug": registry_slug,
        "registry_offline_ready": registry_offline_ready,
        "intake_ref": intake_ref,
        "event_name": intake.event_name,
        "state": intake.state,
        "county": intake.county,
        "carrier": intake.carrier,
        "policy_type": intake.policy_type,
        "coverage_issue_count": len(intake.coverage_issues),
        "module_files": _module_files(scenario_dir),
        "weather_source_count": len(weather.get("sources", [])),
        "carrier_document_count": len(carrier.get("document_pack", [])),
        "carrier_source_count": len(carrier.get("sources", [])),
        "caselaw_issue_count": len(caselaw.get("issues", [])),
        "caselaw_case_count": _caselaw_case_count(caselaw),
        "caselaw_source_count": len(caselaw.get("sources", [])),
        "citation_summary": {
            "not_found": int(citation_summary.get("not_found", 0)),
            "total": int(citation_summary.get("total", 0)),
            "uncertain": int(citation_summary.get("uncertain", 0)),
            "verified": int(citation_summary.get("verified", 0)),
        },
        "source_badge_counts": _source_badge_counts(weather, carrier, caselaw),
        "citation_badge_counts": _citation_badge_counts(citation_verify),
        "memo_sections": list(preflight_scenario.memo_sections) if preflight_scenario else [],
        "workflow_status": preflight_scenario.workflow_status if preflight_scenario else "",
        "workflow_review_required": bool(preflight_scenario.workflow_review_required) if preflight_scenario else False,
        "evidence_cluster_count": int(preflight_scenario.evidence_cluster_count) if preflight_scenario else 0,
        "evidence_review_required_cluster_count": (
            int(preflight_scenario.evidence_review_required_cluster_count) if preflight_scenario else 0
        ),
        "issue_workspace_issue_count": int(preflight_scenario.issue_count) if preflight_scenario else 0,
        "review_required_issue_count": int(preflight_scenario.review_required_issue_count) if preflight_scenario else 0,
        "memo_composer_section_count": int(preflight_scenario.memo_section_count) if preflight_scenario else 0,
        "review_required_memo_section_count": (
            int(preflight_scenario.review_required_memo_section_count) if preflight_scenario else 0
        ),
        "export_eligibility": preflight_scenario.export_eligibility if preflight_scenario else "",
        "export_delivery_state": preflight_scenario.export_delivery_state if preflight_scenario else "",
    }


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _module_files(scenario_dir: Path) -> list[str]:
    actual = {path.name for path in scenario_dir.glob("*.json")}
    required = [filename for filename in REQUIRED_FIXTURE_FILES if filename in actual]
    extras = sorted(actual - set(REQUIRED_FIXTURE_FILES))
    return required + extras


def _caselaw_case_count(caselaw: dict[str, Any]) -> int:
    return sum(len(issue.get("cases", [])) for issue in caselaw.get("issues", []))


def _source_badge_counts(
    weather: dict[str, Any],
    carrier: dict[str, Any],
    caselaw: dict[str, Any],
) -> dict[str, int]:
    badges: Counter[str] = Counter()
    _count_badges(badges, weather.get("sources", []))
    _count_badges(badges, carrier.get("document_pack", []))
    _count_badges(badges, carrier.get("sources", []))
    _count_badges(badges, caselaw.get("sources", []))
    for issue in caselaw.get("issues", []):
        _count_badges(badges, issue.get("cases", []))
    return dict(sorted(badges.items()))


def _citation_badge_counts(citation_verify: dict[str, Any]) -> dict[str, int]:
    badges: Counter[str] = Counter()
    _count_badges(badges, citation_verify.get("checks", []))
    return dict(sorted(badges.items()))


def _count_badges(counter: Counter[str], rows: list[dict[str, Any]]) -> None:
    for row in rows:
        badge = str(row.get("badge") or "").strip()
        if badge:
            counter[badge] += 1


if __name__ == "__main__":
    raise SystemExit(main())
