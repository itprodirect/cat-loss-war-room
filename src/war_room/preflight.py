"""Deterministic offline demo preflight checks."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, UTC
from pathlib import Path
from typing import Any

from war_room.bootstrap import BootstrapContext
from war_room.caselaw_module import build_caselaw_pack
from war_room.carrier_module import build_carrier_doc_pack
from war_room.citation_verify import spot_check_citations
from war_room.export_md import render_markdown_memo
from war_room.models import CaseIntake
from war_room.query_plan import build_research_plan, load_case_intake
from war_room.scenarios import (
    ScenarioAvailabilitySummary,
    fixture_case_availability_summary,
    load_scenario_for_fixture_case,
)
from war_room.weather_module import build_weather_brief
from war_room.evidence_board import build_evidence_board_from_parts
from war_room.issue_workspace import build_issue_workspace_from_parts
from war_room.memo_composer import build_memo_composer_from_parts
from war_room.workflow_summary import build_run_timeline

_REQUIRED_FIXTURE_FILES = ("weather.json", "carrier.json", "caselaw.json", "citation_verify.json")
_EXPECTED_MEMO_SECTIONS = (
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
_REQUIRED_DISCLAIMERS = (
    "DRAFT - ATTORNEY WORK PRODUCT",
    "DEMO RESEARCH MEMO - VERIFY CITATIONS - NOT LEGAL ADVICE",
    "DRAFT - ATTORNEY WORK PRODUCT - VERIFY ALL CITATIONS",
)


@dataclass(frozen=True)
class PreflightCheck:
    """One deterministic offline smoke assertion."""

    name: str
    passed: bool
    evidence: str


@dataclass(frozen=True)
class PreflightScenarioReport:
    """Smoke results for a single committed fixture scenario."""

    case_key: str
    intake_path: str
    availability: ScenarioAvailabilitySummary
    checks: list[PreflightCheck] = field(default_factory=list)
    memo_length: int = 0
    memo_sections: list[str] = field(default_factory=list)
    workflow_status: str = ""
    workflow_review_required: bool = False
    workflow_stage_statuses: list[str] = field(default_factory=list)
    evidence_cluster_count: int = 0
    evidence_review_required_cluster_count: int = 0
    issue_count: int = 0
    review_required_issue_count: int = 0
    memo_section_count: int = 0
    review_required_memo_section_count: int = 0
    export_eligibility: str = ""


@dataclass(frozen=True)
class DemoPreflightReport:
    """Aggregate offline demo preflight report."""

    created_at: str
    repo_root: str
    cache_samples_dir: str
    scenario_count: int
    scenarios: list[PreflightScenarioReport]

    @property
    def passed(self) -> bool:
        return all(check.passed for scenario in self.scenarios for check in scenario.checks)


def run_demo_preflight(context: BootstrapContext) -> DemoPreflightReport:
    """Run the deterministic offline demo smoke against committed fixtures."""

    scenario_reports: list[PreflightScenarioReport] = []
    for scenario_dir in _discover_scenario_dirs(context.settings.cache_samples_dir):
        case_key = scenario_dir.name
        intake_path = context.repo_root / "eval" / "intakes" / f"{case_key}.json"
        registry_scenario = load_scenario_for_fixture_case(case_key, repo_root=context.repo_root)
        checks: list[PreflightCheck] = []
        intake_evidence = str(intake_path)
        availability = fixture_case_availability_summary(
            case_key=case_key,
            title=case_key,
            registry_slug=registry_scenario.slug if registry_scenario is not None else None,
            registry_offline_ready=(
                registry_scenario.offline_demo_ready if registry_scenario is not None else None
            ),
        )
        memo_length = 0
        memo_sections: list[str] = []
        workflow_status = ""
        workflow_review_required = False
        workflow_stage_statuses: list[str] = []
        evidence_cluster_count = 0
        evidence_review_required_cluster_count = 0
        issue_count = 0
        review_required_issue_count = 0
        memo_section_count = 0
        review_required_memo_section_count = 0
        export_eligibility = ""

        try:
            intake, intake_evidence = _load_intake(case_key, intake_path, repo_root=context.repo_root)
            checks.append(PreflightCheck("intake payload loads", True, intake_evidence))
            availability = fixture_case_availability_summary(
                case_key=case_key,
                title=registry_scenario.title if registry_scenario is not None else intake.event_name,
                registry_slug=registry_scenario.slug if registry_scenario is not None else None,
                registry_offline_ready=(
                    registry_scenario.offline_demo_ready if registry_scenario is not None else None
                ),
            )
            research_plan = build_research_plan(intake)
            query_plan = research_plan.query_plan

            weather = build_weather_brief(
                intake,
                None,
                query_plan=query_plan,
                cache_samples_dir=str(context.settings.cache_samples_dir),
            )
            checks.extend(_module_checks("weather", weather))

            carrier = build_carrier_doc_pack(
                intake,
                None,
                query_plan=query_plan,
                cache_samples_dir=str(context.settings.cache_samples_dir),
            )
            checks.extend(_module_checks("carrier", carrier))

            caselaw = build_caselaw_pack(
                intake,
                None,
                query_plan=query_plan,
                cache_samples_dir=str(context.settings.cache_samples_dir),
            )
            checks.extend(_module_checks("caselaw", caselaw))

            citecheck = _load_json(scenario_dir / "citation_verify.json")
            checks.extend(_citation_checks(citecheck))

            memo = render_markdown_memo(
                intake,
                weather,
                carrier,
                caselaw,
                citecheck,
                query_plan,
            )
            memo_length = len(memo)
            memo_sections = [section for section in _EXPECTED_MEMO_SECTIONS if section in memo]
            checks.extend(_memo_checks(memo, memo_sections))
            run_record, run_stages = build_run_timeline(
                intake,
                research_plan,
                weather,
                carrier,
                caselaw,
                citecheck,
                environment="preflight",
                export_written=False,
            )
            workflow_status = run_record.status
            workflow_review_required = run_record.review_required
            workflow_stage_statuses = [
                f"{stage.stage_key}={stage.status}"
                for stage in run_stages
            ]
            evidence_board = build_evidence_board_from_parts(
                intake,
                weather,
                carrier,
                caselaw,
                citecheck,
                query_plan,
            )
            evidence_cluster_count = evidence_board.total_clusters
            evidence_review_required_cluster_count = evidence_board.review_required_clusters
            issue_workspace = build_issue_workspace_from_parts(
                intake,
                weather,
                carrier,
                caselaw,
                citecheck,
                query_plan,
            )
            issue_count = len(issue_workspace.issue_cards)
            review_required_issue_count = issue_workspace.review_required_issue_count
            memo_composer = build_memo_composer_from_parts(
                intake,
                weather,
                carrier,
                caselaw,
                citecheck,
                query_plan,
            )
            memo_section_count = len(memo_composer.section_cards)
            review_required_memo_section_count = memo_composer.review_required_section_count
            export_eligibility = memo_composer.export_eligibility
        except Exception as exc:
            checks.append(
                PreflightCheck(
                    name="offline smoke execution",
                    passed=False,
                    evidence=f"{type(exc).__name__}: {exc}",
                )
            )

        scenario_reports.append(
            PreflightScenarioReport(
                case_key=case_key,
                intake_path=intake_evidence,
                availability=availability,
                checks=checks,
                memo_length=memo_length,
                memo_sections=memo_sections,
                workflow_status=workflow_status,
                workflow_review_required=workflow_review_required,
                workflow_stage_statuses=workflow_stage_statuses,
                evidence_cluster_count=evidence_cluster_count,
                evidence_review_required_cluster_count=evidence_review_required_cluster_count,
                issue_count=issue_count,
                review_required_issue_count=review_required_issue_count,
                memo_section_count=memo_section_count,
                review_required_memo_section_count=review_required_memo_section_count,
                export_eligibility=export_eligibility,
            )
        )

    return DemoPreflightReport(
        created_at=datetime.now(UTC).isoformat(),
        repo_root=str(context.repo_root),
        cache_samples_dir=str(context.settings.cache_samples_dir),
        scenario_count=len(scenario_reports),
        scenarios=scenario_reports,
    )


def render_demo_preflight_report(report: DemoPreflightReport) -> str:
    """Render the offline demo smoke report as Markdown-like text."""

    lines = [
        "# Demo Preflight",
        "",
        f"- Created at: {report.created_at}",
        f"- Repo root: {report.repo_root}",
        f"- Cache samples dir: {report.cache_samples_dir}",
        f"- Scenario count: {report.scenario_count}",
        f"- Passed: {'Yes' if report.passed else 'No'}",
        "",
    ]

    for scenario in report.scenarios:
        lines.append(f"## {scenario.case_key}")
        lines.append(f"- Intake: {scenario.intake_path}")
        lines.append(
            f"- Availability: {scenario.availability.status} | {scenario.availability.detail}"
        )
        if scenario.workflow_status:
            lines.append(
                f"- Workflow: {scenario.workflow_status} | review_required="
                f"{'yes' if scenario.workflow_review_required else 'no'}"
            )
        if scenario.workflow_stage_statuses:
            lines.append(
                "- Workflow stages: " + ", ".join(scenario.workflow_stage_statuses)
            )
        if scenario.evidence_cluster_count:
            lines.append(
                f"- Evidence board: {scenario.evidence_cluster_count} clusters | "
                f"{scenario.evidence_review_required_cluster_count} review_required"
            )
        if scenario.issue_count:
            lines.append(
                f"- Issue workspace: {scenario.issue_count} issues | "
                f"{scenario.review_required_issue_count} review_required"
            )
        if scenario.memo_section_count:
            lines.append(
                f"- Memo composer: {scenario.memo_section_count} sections | "
                f"{scenario.review_required_memo_section_count} review_required | "
                f"{scenario.export_eligibility}"
            )
        lines.append(f"- Memo length: {scenario.memo_length}")
        if scenario.memo_sections:
            lines.append(f"- Memo sections: {', '.join(scenario.memo_sections)}")
        for check in scenario.checks:
            marker = "x" if check.passed else " "
            lines.append(f"- [{marker}] {check.name} - {check.evidence}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def report_to_payload(report: DemoPreflightReport) -> dict[str, Any]:
    """Return a JSON-serializable preflight payload."""

    return {
        "created_at": report.created_at,
        "repo_root": report.repo_root,
        "cache_samples_dir": report.cache_samples_dir,
        "scenario_count": report.scenario_count,
        "passed": report.passed,
        "scenarios": [
            {
                "case_key": scenario.case_key,
                "intake_path": scenario.intake_path,
                "availability": asdict(scenario.availability),
                "memo_length": scenario.memo_length,
                "memo_sections": scenario.memo_sections,
                "workflow_status": scenario.workflow_status,
                "workflow_review_required": scenario.workflow_review_required,
                "workflow_stage_statuses": scenario.workflow_stage_statuses,
                "evidence_cluster_count": scenario.evidence_cluster_count,
                "evidence_review_required_cluster_count": scenario.evidence_review_required_cluster_count,
                "issue_count": scenario.issue_count,
                "review_required_issue_count": scenario.review_required_issue_count,
                "memo_section_count": scenario.memo_section_count,
                "review_required_memo_section_count": scenario.review_required_memo_section_count,
                "export_eligibility": scenario.export_eligibility,
                "checks": [asdict(check) for check in scenario.checks],
            }
            for scenario in report.scenarios
        ],
    }


def _discover_scenario_dirs(cache_samples_dir: Path) -> list[Path]:
    if not cache_samples_dir.exists():
        return []

    scenario_dirs = []
    for candidate in sorted(path for path in cache_samples_dir.iterdir() if path.is_dir()):
        if all((candidate / filename).exists() for filename in _REQUIRED_FIXTURE_FILES):
            scenario_dirs.append(candidate)
    return scenario_dirs


def _load_intake(case_key: str, intake_path: Path, *, repo_root: Path) -> tuple[CaseIntake, str]:
    scenario = load_scenario_for_fixture_case(case_key, repo_root=repo_root)
    if scenario is not None:
        return scenario.to_case_intake(), f"scenario:{scenario.slug}"

    if intake_path.exists():
        return load_case_intake(intake_path), str(intake_path)
    raise FileNotFoundError(f"Intake file not found: {intake_path}")


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _module_checks(module: str, payload: dict[str, Any]) -> list[PreflightCheck]:
    checks = [
        PreflightCheck(
            name=f"{module} module loaded from cache",
            passed=payload.get("module") == module,
            evidence=f"module={payload.get('module', '')}",
        ),
    ]
    if module == "weather":
        checks.append(
            PreflightCheck(
                name="weather sources present",
                passed=bool(payload.get("sources")),
                evidence=f"sources={len(payload.get('sources', []))}",
            )
        )
    elif module == "carrier":
        checks.append(
            PreflightCheck(
                name="carrier documents present",
                passed=bool(payload.get("document_pack")),
                evidence=f"documents={len(payload.get('document_pack', []))}",
            )
        )
    elif module == "caselaw":
        checks.append(
            PreflightCheck(
                name="caselaw issues present",
                passed=bool(payload.get("issues")),
                evidence=f"issues={len(payload.get('issues', []))}",
            )
        )
    return checks


def _citation_checks(payload: dict[str, Any]) -> list[PreflightCheck]:
    summary = payload.get("summary", {})
    total = int(summary.get("total", 0))
    return [
        PreflightCheck(
            name="citation verify module loaded from cache",
            passed=payload.get("module") == "citation_verify",
            evidence=f"module={payload.get('module', '')}",
        ),
        PreflightCheck(
            name="citation checks present",
            passed=total > 0,
            evidence=f"checks={total}",
        ),
        PreflightCheck(
            name="citation summary is internally consistent",
            passed=total == int(summary.get("verified", 0)) + int(summary.get("uncertain", 0)) + int(summary.get("not_found", 0)),
            evidence=(
                f"total={total}, verified={summary.get('verified', 0)}, "
                f"uncertain={summary.get('uncertain', 0)}, not_found={summary.get('not_found', 0)}"
            ),
        ),
    ]


def _memo_checks(memo: str, memo_sections: list[str]) -> list[PreflightCheck]:
    checks = [
        PreflightCheck(
            name="memo includes disclaimer language",
            passed=all(marker in memo for marker in _REQUIRED_DISCLAIMERS),
            evidence="; ".join(_REQUIRED_DISCLAIMERS),
        ),
        PreflightCheck(
            name="memo includes expected major sections",
            passed=len(memo_sections) == len(_EXPECTED_MEMO_SECTIONS),
            evidence=f"{len(memo_sections)}/{len(_EXPECTED_MEMO_SECTIONS)} sections present",
        ),
    ]
    return checks
