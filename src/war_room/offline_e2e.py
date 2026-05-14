"""Offline end-to-end demo gate for committed fixture scenarios."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Sequence

from war_room.bootstrap import BootstrapContext, bootstrap_runtime, discover_repo_root
from war_room.preflight import (
    DemoPreflightReport,
    preflight_run_id,
    run_demo_preflight,
    write_preflight_artifact,
)

SCHEMA_VERSION = "offline-demo-e2e.v1"
DEFAULT_OUTPUT_DIR = Path("runs/offline_e2e")
MIN_SCENARIO_COUNT = 5
EXPECTED_WORKFLOW_STAGES = (
    "intake_validation",
    "research_plan",
    "weather",
    "carrier",
    "caselaw",
    "citation_verify",
    "memo_assembly",
    "export",
)
EXPECTED_MEMO_SECTION_COUNT = 10


@dataclass(frozen=True)
class OfflineE2EScenario:
    """One committed fixture scenario exercised by the offline e2e gate."""

    case_key: str
    intake_path: str
    availability_status: str
    passed: bool
    workflow_status: str
    workflow_review_required: bool
    workflow_stage_statuses: list[str]
    evidence_cluster_count: int
    issue_count: int
    memo_section_count: int
    memo_length: int
    export_eligibility: str
    export_artifact_count: int
    export_delivery_state: str
    failed_checks: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class OfflineE2EAssertion:
    """One aggregate offline e2e assertion."""

    name: str
    passed: bool
    evidence: str


@dataclass(frozen=True)
class OfflineE2EResult:
    """Structured result for the offline e2e demo gate."""

    schema_version: str
    run_id: str
    created_at: str
    repo_root: str
    preflight_artifact_path: str
    json_path: str
    markdown_path: str
    scenario_count: int
    passed_scenario_count: int
    passed: bool
    assertions: list[OfflineE2EAssertion]
    scenarios: list[OfflineE2EScenario]


def run_offline_demo_e2e(
    context: BootstrapContext | None = None,
    *,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
) -> OfflineE2EResult:
    """Run the offline demo path and write e2e artifacts."""

    resolved_context = context or bootstrap_runtime(ensure_dirs=True)
    resolved_output_dir = _resolve_output_dir(resolved_context.repo_root, output_dir)
    report = run_demo_preflight(resolved_context)
    run_id = preflight_run_id(report)
    preflight_artifact_path = write_preflight_artifact(
        report,
        output_dir=resolved_output_dir / "preflight",
        artifact_label="offline-e2e",
        run_id=run_id,
    )
    json_path = resolved_output_dir / f"{_artifact_stem(report, run_id=run_id)}.json"
    markdown_path = resolved_output_dir / f"{_artifact_stem(report, run_id=run_id)}.md"
    result = build_offline_demo_e2e_result(
        report,
        preflight_artifact_path=preflight_artifact_path,
        json_path=json_path,
        markdown_path=markdown_path,
    )
    write_offline_demo_e2e_artifacts(result)
    return result


def build_offline_demo_e2e_result(
    report: DemoPreflightReport,
    *,
    preflight_artifact_path: Path,
    json_path: Path,
    markdown_path: Path,
) -> OfflineE2EResult:
    """Build a structured e2e result from a live preflight report."""

    scenarios = [_scenario_result(scenario) for scenario in report.scenarios]
    assertions = offline_demo_e2e_assertions(
        report,
        scenarios=scenarios,
        preflight_artifact_path=preflight_artifact_path,
    )
    passed = all(assertion.passed for assertion in assertions)
    return OfflineE2EResult(
        schema_version=SCHEMA_VERSION,
        run_id=preflight_run_id(report),
        created_at=report.created_at,
        repo_root=report.repo_root,
        preflight_artifact_path=str(preflight_artifact_path),
        json_path=str(json_path),
        markdown_path=str(markdown_path),
        scenario_count=report.scenario_count,
        passed_scenario_count=sum(1 for scenario in scenarios if scenario.passed),
        passed=passed,
        assertions=assertions,
        scenarios=scenarios,
    )


def offline_demo_e2e_assertions(
    report: DemoPreflightReport,
    *,
    scenarios: Sequence[OfflineE2EScenario],
    preflight_artifact_path: Path,
) -> list[OfflineE2EAssertion]:
    """Return aggregate assertions for the offline e2e gate."""

    preflight_payload = _read_preflight_payload(preflight_artifact_path)
    expected_stages = set(EXPECTED_WORKFLOW_STAGES)
    actual_stage_sets = [
        {stage.split("=", 1)[0] for stage in scenario.workflow_stage_statuses}
        for scenario in scenarios
    ]
    return [
        OfflineE2EAssertion(
            name="offline preflight passed",
            passed=report.passed,
            evidence=f"{sum(1 for scenario in scenarios if scenario.passed)}/{report.scenario_count} scenarios passed",
        ),
        OfflineE2EAssertion(
            name="committed fixture scenario coverage",
            passed=report.scenario_count >= MIN_SCENARIO_COUNT,
            evidence=f"{report.scenario_count} scenarios discovered",
        ),
        OfflineE2EAssertion(
            name="all scenarios are offline-ready",
            passed=all(scenario.availability_status == "offline-ready" for scenario in scenarios),
            evidence=", ".join(f"{scenario.case_key}:{scenario.availability_status}" for scenario in scenarios),
        ),
        OfflineE2EAssertion(
            name="workflow stages are complete enough for demo review",
            passed=all(expected_stages.issubset(stage_set) for stage_set in actual_stage_sets),
            evidence=f"expected stages: {', '.join(EXPECTED_WORKFLOW_STAGES)}",
        ),
        OfflineE2EAssertion(
            name="memo and review surfaces are populated",
            passed=all(
                scenario.memo_length > 0
                and scenario.memo_section_count >= EXPECTED_MEMO_SECTION_COUNT
                and scenario.evidence_cluster_count > 0
                and scenario.issue_count > 0
                for scenario in scenarios
            ),
            evidence="memo, evidence-board, and issue-workspace counts are non-empty",
        ),
        OfflineE2EAssertion(
            name="export posture is structured",
            passed=all(
                scenario.export_eligibility == "review_required_export"
                and scenario.export_artifact_count == 1
                and scenario.export_delivery_state == "not_written"
                for scenario in scenarios
            ),
            evidence="all scenarios expose review-required export history without writing final output",
        ),
        OfflineE2EAssertion(
            name="preflight artifact is linked and structured",
            passed=(
                preflight_artifact_path.exists()
                and preflight_payload.get("schema_like_payload", False)
                and preflight_payload.get("run_id") == preflight_run_id(report)
                and preflight_payload.get("passed") is True
                and preflight_payload.get("scenario_count") == report.scenario_count
            ),
            evidence=str(preflight_artifact_path),
        ),
    ]


def write_offline_demo_e2e_artifacts(result: OfflineE2EResult) -> tuple[Path, Path]:
    """Write JSON and Markdown artifacts for the offline e2e result."""

    json_path = Path(result.json_path)
    markdown_path = Path(result.markdown_path)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(asdict(result), indent=2), encoding="utf-8")
    markdown_path.write_text(render_offline_demo_e2e_markdown(result), encoding="utf-8")
    return json_path, markdown_path


def render_offline_demo_e2e_markdown(result: OfflineE2EResult) -> str:
    """Render the offline e2e result as Markdown."""

    lines = [
        "# Offline Demo E2E",
        "",
        f"- Run id: {result.run_id}",
        f"- Created at: {result.created_at}",
        f"- Status: {'passed' if result.passed else 'failed'}",
        f"- Scenario coverage: {result.passed_scenario_count}/{result.scenario_count}",
        f"- Preflight artifact: `{result.preflight_artifact_path}`",
        "",
        "## Assertions",
    ]
    for assertion in result.assertions:
        marker = "x" if assertion.passed else " "
        lines.append(f"- [{marker}] {assertion.name} - {assertion.evidence}")

    lines.extend(
        [
            "",
            "## Scenarios",
            "| Scenario | Passed | Workflow | Memo sections | Evidence clusters | Issues | Export | Failed checks |",
            "|---|---|---|---:|---:|---:|---|---|",
        ]
    )
    for scenario in result.scenarios:
        failed_checks = ", ".join(scenario.failed_checks) if scenario.failed_checks else "none"
        lines.append(
            "| "
            f"{scenario.case_key} | "
            f"{'Yes' if scenario.passed else 'No'} | "
            f"{scenario.workflow_status} | "
            f"{scenario.memo_section_count} | "
            f"{scenario.evidence_cluster_count} | "
            f"{scenario.issue_count} | "
            f"{scenario.export_eligibility}/{scenario.export_delivery_state} | "
            f"{failed_checks} |"
        )
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for the offline e2e demo gate."""

    parser = argparse.ArgumentParser(description="Run the offline demo e2e gate")
    parser.add_argument("--repo-root", type=Path, help="Repository root to inspect. Defaults to discovery from cwd.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--check", action="store_true", help="Run the e2e gate and fail if assertions fail.")
    parser.add_argument("--json", action="store_true", help="Emit the e2e result JSON to stdout.")
    args = parser.parse_args(argv)

    context = bootstrap_runtime(start_path=args.repo_root or discover_repo_root(), ensure_dirs=True)
    result = run_offline_demo_e2e(context, output_dir=Path(args.output_dir))
    if args.json:
        print(json.dumps(asdict(result), indent=2))
    else:
        print(render_offline_demo_e2e_markdown(result), end="")
        print(
            "Offline e2e "
            f"{'passed' if result.passed else 'failed'}: "
            f"{result.passed_scenario_count}/{result.scenario_count} scenarios passed; "
            f"artifacts: {result.json_path}"
        )
    return 0 if result.passed else 1


def _scenario_result(scenario) -> OfflineE2EScenario:
    failed_checks = [check.name for check in scenario.checks if not check.passed]
    return OfflineE2EScenario(
        case_key=scenario.case_key,
        intake_path=scenario.intake_path,
        availability_status=scenario.availability.status,
        passed=not failed_checks,
        workflow_status=scenario.workflow_status,
        workflow_review_required=scenario.workflow_review_required,
        workflow_stage_statuses=list(scenario.workflow_stage_statuses),
        evidence_cluster_count=scenario.evidence_cluster_count,
        issue_count=scenario.issue_count,
        memo_section_count=scenario.memo_section_count,
        memo_length=scenario.memo_length,
        export_eligibility=scenario.export_eligibility,
        export_artifact_count=scenario.export_artifact_count,
        export_delivery_state=scenario.export_delivery_state,
        failed_checks=failed_checks,
    )


def _read_preflight_payload(path: Path) -> dict:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload | {
        "schema_like_payload": all(
            key in payload
            for key in ("run_id", "passed", "scenario_count", "scenarios")
        )
    }


def _resolve_output_dir(repo_root: Path, output_dir: Path) -> Path:
    return output_dir if output_dir.is_absolute() else (repo_root / output_dir).resolve()


def _artifact_stem(report: DemoPreflightReport, *, run_id: str) -> str:
    return f"{report.created_at[:10]}_offline-e2e_{_slugify(run_id.lower())}"


def _slugify(value: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9]+", "-", value.strip().lower()).strip("-")
    return normalized or "offline-e2e"


if __name__ == "__main__":
    raise SystemExit(main())
