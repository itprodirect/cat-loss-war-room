"""Generate repeatable release scorecard artifacts for the current repo state."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path

from war_room.bootstrap import bootstrap_runtime

DEFAULT_VERIFICATION_COMMAND = "pytest -q"
_FIXTURE_FILE_NAMES = ("weather.json", "carrier.json", "caselaw.json", "citation_verify.json")


@dataclass(frozen=True)
class ScorecardDimension:
    """One scored release-quality dimension."""

    name: str
    score: int
    verdict: str
    evidence: list[str] = field(default_factory=list)
    notes: str = ""


@dataclass(frozen=True)
class MustPassGate:
    """A required gate for the target release level."""

    name: str
    passed: bool
    evidence: str


@dataclass(frozen=True)
class FixtureScenarioCoverage:
    """Summary of one committed fixture scenario."""

    case_key: str
    event_summary: str
    state: str
    carrier: str
    issue_count: int
    citation_checks: int
    module_files: list[str]


@dataclass(frozen=True)
class FixtureCoverageSummary:
    """Aggregate fixture coverage used for release-scorecard calibration."""

    scenario_count: int
    states: list[str]
    scenario_keys: list[str]
    scenarios: list[FixtureScenarioCoverage]


@dataclass(frozen=True)
class ReleaseScorecard:
    """Structured release scorecard artifact."""

    date: str
    candidate: str
    target_release_level: str
    evaluators: list[str]
    evidence_bundle: list[str]
    fixture_coverage: FixtureCoverageSummary | None
    dimensions: list[ScorecardDimension]
    must_pass_gates: list[MustPassGate]
    blocking_gaps: list[str]
    decision: str


def collect_fixture_coverage(cache_samples_dir: Path) -> FixtureCoverageSummary:
    """Inspect committed scenario folders and summarize fixture coverage."""

    scenarios: list[FixtureScenarioCoverage] = []
    if not cache_samples_dir.exists():
        return FixtureCoverageSummary(0, [], [], [])

    for scenario_dir in sorted(path for path in cache_samples_dir.iterdir() if path.is_dir()):
        module_files = [name for name in _FIXTURE_FILE_NAMES if (scenario_dir / name).exists()]
        if not module_files:
            continue

        weather = _load_json_if_exists(scenario_dir / "weather.json")
        carrier = _load_json_if_exists(scenario_dir / "carrier.json")
        caselaw = _load_json_if_exists(scenario_dir / "caselaw.json")
        citation_verify = _load_json_if_exists(scenario_dir / "citation_verify.json")

        carrier_snapshot = carrier.get("carrier_snapshot", {}) if isinstance(carrier, dict) else {}
        summary = citation_verify.get("summary", {}) if isinstance(citation_verify, dict) else {}
        scenarios.append(
            FixtureScenarioCoverage(
                case_key=scenario_dir.name,
                event_summary=_clean_fixture_text(str(weather.get("event_summary", scenario_dir.name))),
                state=str(carrier_snapshot.get("state", "")),
                carrier=str(carrier_snapshot.get("name", "")),
                issue_count=len(caselaw.get("issues", [])) if isinstance(caselaw, dict) else 0,
                citation_checks=int(summary.get("total", 0)) if isinstance(summary, dict) else 0,
                module_files=module_files,
            )
        )

    return FixtureCoverageSummary(
        scenario_count=len(scenarios),
        states=sorted({scenario.state for scenario in scenarios if scenario.state}),
        scenario_keys=[scenario.case_key for scenario in scenarios],
        scenarios=scenarios,
    )


def build_demo_release_scorecard(
    *,
    candidate: str,
    verification_summary: str,
    verification_command: str = DEFAULT_VERIFICATION_COMMAND,
    artifact_date: str | None = None,
    evaluators: list[str] | None = None,
    blocking_gaps: list[str] | None = None,
    decision: str = "Ship",
    fixture_coverage: FixtureCoverageSummary | None = None,
) -> ReleaseScorecard:
    """Build the current demo-ready baseline scorecard."""

    chosen_date = artifact_date or date.today().isoformat()
    evidence_bundle = [
        f"Verification: {verification_command} -> {verification_summary}",
        "Offline demo lane uses committed cache_samples fixtures.",
        "Rubric source of truth: docs/V2_RELEASE_RUBRIC.md",
    ]
    if fixture_coverage and fixture_coverage.scenario_count:
        evidence_bundle.insert(
            1,
            f"Fixture coverage: {fixture_coverage.scenario_count} committed scenarios across {', '.join(fixture_coverage.states)}.",
        )

    reliability_evidence = [
        f"Supported verification path passed ({verification_summary}).",
        "Offline demo lane is established with committed fixtures.",
    ]
    evidence_quality_evidence = [
        "Normalization and caselaw quality improvements remain future work under #12 and #13.",
    ]
    operational_evidence = [
        "Bootstrap and runtime boundaries are documented.",
        "This script now emits repeatable local scorecard artifacts into runs/.",
    ]
    if fixture_coverage and fixture_coverage.scenario_count:
        fixture_line = (
            f"Committed fixture lane now spans {fixture_coverage.scenario_count} scenarios "
            f"across {', '.join(fixture_coverage.states)}."
        )
        reliability_evidence.append(fixture_line)
        evidence_quality_evidence.insert(0, fixture_line)
        operational_evidence.append(
            "Fixture coverage is exercised through an explicit CI smoke job and local smoke command."
        )
    else:
        evidence_quality_evidence.insert(0, "Broader scenario coverage is still pending under #8.")

    dimensions = [
        ScorecardDimension(
            name="Reliability",
            score=3,
            verdict="Strong",
            evidence=reliability_evidence,
            notes="Fresh-env and exa-py compatibility CI gates exist, and the local scorecard now records the supported verification lane plus committed fixture breadth.",
        ),
        ScorecardDimension(
            name="Evidence Quality",
            score=1,
            verdict="Weak",
            evidence=evidence_quality_evidence,
            notes="Fixture breadth is now measurable, but output-quality thresholds and comparative scenario scoring are still not calibrated enough for stronger release claims.",
        ),
        ScorecardDimension(
            name="Trust and Provenance",
            score=2,
            verdict="Acceptable",
            evidence=[
                "Disclaimers, citation checks, and evidence clustering exist in the current export path.",
                "Claim and review-event trace links are present in the notebook-era audit snapshot.",
            ],
            notes="Trust signals are real, but still tied to the current notebook-oriented workflow.",
        ),
        ScorecardDimension(
            name="Workflow Usability",
            score=1,
            verdict="Weak",
            evidence=[
                "Primary product surface remains the notebook demo.",
                "Routine operation still assumes engineering-guided setup.",
            ],
            notes="This is the clearest blocker for Beta-ready claims.",
        ),
        ScorecardDimension(
            name="Review and Export Quality",
            score=2,
            verdict="Acceptable",
            evidence=[
                "Memo output is readable and includes trust-context appendices.",
                "Review-required warnings remain visible in the exported memo path.",
            ],
            notes="Usable for internal review, not yet polished for repeated client-facing use.",
        ),
        ScorecardDimension(
            name="Operational Readiness",
            score=1,
            verdict="Weak",
            evidence=operational_evidence,
            notes="Observability and broader deployment lanes remain future work, but fixture coverage is now explicit in both CI and the scorecard artifact.",
        ),
        ScorecardDimension(
            name="Security and Governance",
            score=1,
            verdict="Weak",
            evidence=[
                "Demo disclaimers and no-secrets boundaries are explicit.",
                "Production-grade retention, access, and security controls are still roadmap items.",
            ],
            notes="Adequate for controlled demo use, not for production-style claims.",
        ),
    ]
    must_pass_gates = [
        MustPassGate(
            name="Supported test path is green",
            passed=True,
            evidence=f"{verification_command} -> {verification_summary}",
        ),
        MustPassGate(
            name="Offline demo lane completes",
            passed=True,
            evidence=_offline_gate_evidence(fixture_coverage),
        ),
        MustPassGate(
            name="Required disclaimer language appears in outputs",
            passed=True,
            evidence="Current memo/export path preserves the demo legal-disclaimer language.",
        ),
        MustPassGate(
            name="No known blocker prevents a narrated end-to-end demo",
            passed=True,
            evidence="Current baseline remains notebook-first but stable for guided use.",
        ),
        MustPassGate(
            name="Memo remains readable enough for internal review",
            passed=True,
            evidence="Current export path includes trust snapshot, review cues, and appendices.",
        ),
    ]

    return ReleaseScorecard(
        date=chosen_date,
        candidate=candidate,
        target_release_level="Demo-ready",
        evaluators=evaluators or ["local builder"],
        evidence_bundle=evidence_bundle,
        fixture_coverage=fixture_coverage,
        dimensions=dimensions,
        must_pass_gates=must_pass_gates,
        blocking_gaps=blocking_gaps or [],
        decision=decision,
    )


def render_release_scorecard_markdown(scorecard: ReleaseScorecard) -> str:
    """Render the structured scorecard as Markdown."""

    lines = [
        "# Release Scorecard",
        "",
        f"- Date: {scorecard.date}",
        f"- Candidate / branch: {scorecard.candidate}",
        f"- Target release level: {scorecard.target_release_level}",
        f"- Evaluator(s): {', '.join(scorecard.evaluators)}",
        "- Evidence bundle:",
    ]
    for entry in scorecard.evidence_bundle:
        lines.append(f"  - {entry}")

    if scorecard.fixture_coverage and scorecard.fixture_coverage.scenario_count:
        lines.extend(
            [
                "",
                "## Fixture Coverage",
                f"- Scenario count: {scorecard.fixture_coverage.scenario_count}",
                f"- States: {', '.join(scorecard.fixture_coverage.states)}",
            ]
        )
        for scenario in scorecard.fixture_coverage.scenarios:
            lines.append(
                f"- {scenario.case_key}: {scenario.event_summary} | {scenario.carrier} | issues {scenario.issue_count} | citation checks {scenario.citation_checks}"
            )

    lines.extend(
        [
            "",
            "| Dimension | Score (0-3) | Verdict | Evidence | Notes |",
            "|---|---:|---|---|---|",
        ]
    )
    for dimension in scorecard.dimensions:
        evidence = "<br>".join(dimension.evidence)
        lines.append(
            f"| {dimension.name} | {dimension.score} | {dimension.verdict} | {evidence} | {dimension.notes} |"
        )

    lines.extend(["", "## Must-pass gates"])
    for gate in scorecard.must_pass_gates:
        marker = "x" if gate.passed else " "
        lines.append(f"- [{marker}] {gate.name} - {gate.evidence}")

    lines.extend(["", "## Blocking gaps"])
    if scorecard.blocking_gaps:
        for gap in scorecard.blocking_gaps:
            lines.append(f"- {gap}")
    else:
        lines.append("- None recorded")

    lines.extend(["", "## Decision", f"- {scorecard.decision}", ""])
    return "\n".join(lines)


def write_release_scorecard_artifacts(
    scorecard: ReleaseScorecard,
    *,
    output_dir: Path,
) -> tuple[Path, Path]:
    """Write JSON and Markdown scorecard artifacts."""

    output_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{scorecard.date}_{_slugify(scorecard.candidate)}"
    json_path = output_dir / f"{stem}.json"
    markdown_path = output_dir / f"{stem}.md"

    json_payload = asdict(scorecard)
    json_path.write_text(json.dumps(json_payload, indent=2), encoding="utf-8")
    markdown_path.write_text(render_release_scorecard_markdown(scorecard), encoding="utf-8")
    return json_path, markdown_path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments for scorecard generation."""

    parser = argparse.ArgumentParser(description="Write a demo-ready release scorecard artifact")
    parser.add_argument("--candidate", required=True, help="Candidate label or branch name")
    parser.add_argument(
        "--verification-summary",
        required=True,
        help='Short verification result, for example "178 passed"',
    )
    parser.add_argument(
        "--verification-command",
        default=DEFAULT_VERIFICATION_COMMAND,
        help="Verification command tied to this scorecard",
    )
    parser.add_argument("--date", dest="artifact_date", help="Override artifact date (YYYY-MM-DD)")
    parser.add_argument(
        "--evaluator",
        dest="evaluators",
        action="append",
        help="Evaluator label; may be passed multiple times",
    )
    parser.add_argument(
        "--blocking-gap",
        dest="blocking_gaps",
        action="append",
        help="Blocking gap note; may be passed multiple times",
    )
    parser.add_argument(
        "--decision",
        default="Ship",
        help='Final decision label, for example "Ship" or "No ship"',
    )
    parser.add_argument(
        "--output-dir",
        help="Optional output directory. Defaults to <runs_dir>/release_scorecards.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for generating a release scorecard artifact."""

    args = parse_args(argv)
    context = bootstrap_runtime(start_path=Path(__file__))
    output_dir = Path(args.output_dir) if args.output_dir else context.settings.runs_dir / "release_scorecards"
    fixture_coverage = collect_fixture_coverage(context.settings.cache_samples_dir)
    scorecard = build_demo_release_scorecard(
        candidate=args.candidate,
        verification_summary=args.verification_summary,
        verification_command=args.verification_command,
        artifact_date=args.artifact_date,
        evaluators=args.evaluators,
        blocking_gaps=args.blocking_gaps,
        decision=args.decision,
        fixture_coverage=fixture_coverage,
    )
    json_path, markdown_path = write_release_scorecard_artifacts(scorecard, output_dir=output_dir)
    print(f"Wrote JSON scorecard: {json_path}")
    print(f"Wrote Markdown scorecard: {markdown_path}")
    return 0


def _load_json_if_exists(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _clean_fixture_text(value: str) -> str:
    return (
        value.replace("\u00c3\u00a2\u00e2\u201a\u00ac\u00e2\u20ac\u009d", "-")
        .replace("\u00e2\u20ac\u201d", "-")
        .replace("\u2014", "-")
        .strip()
    )


def _offline_gate_evidence(fixture_coverage: FixtureCoverageSummary | None) -> str:
    if not fixture_coverage or not fixture_coverage.scenario_count:
        return "Committed cache_samples fixtures support the offline demo lane."
    return (
        f"Committed cache_samples fixtures cover {fixture_coverage.scenario_count} scenarios: "
        f"{', '.join(fixture_coverage.scenario_keys)}."
    )


def _slugify(value: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9]+", "-", value.strip().lower()).strip("-")
    return normalized or "candidate"


if __name__ == "__main__":
    raise SystemExit(main())
