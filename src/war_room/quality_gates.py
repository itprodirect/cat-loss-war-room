"""Run and summarize CI quality gates with categorized artifacts."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Sequence

from war_room.bootstrap import discover_repo_root

SCHEMA_VERSION = "ci-quality-gate.v1"
DEFAULT_OUTPUT_DIR = Path("runs/quality_gates")


@dataclass(frozen=True)
class QualityGateDefinition:
    """Stable metadata for one CI quality gate."""

    gate_id: str
    name: str
    category: str
    description: str


@dataclass(frozen=True)
class QualityGateResult:
    """Structured outcome for one quality-gate command."""

    schema_version: str
    gate_id: str
    name: str
    category: str
    description: str
    label: str | None
    status: str
    exit_code: int
    command: list[str]
    summary: str
    started_at: str
    finished_at: str
    duration_seconds: float
    log_path: str
    json_path: str
    markdown_path: str


GATE_DEFINITIONS: dict[str, QualityGateDefinition] = {
    "unit-tests": QualityGateDefinition(
        gate_id="unit-tests",
        name="Unit Test Gate",
        category="unit",
        description="Full pytest suite in a fresh editable-package environment.",
    ),
    "offline-fixture-tests": QualityGateDefinition(
        gate_id="offline-fixture-tests",
        name="Offline Fixture Gate",
        category="offline_fixture",
        description="Offline fixture smoke and intake validation tests.",
    ),
    "e2e-offline-demo": QualityGateDefinition(
        gate_id="e2e-offline-demo",
        name="Offline E2E Demo Gate",
        category="e2e_offline",
        description="End-to-end offline demo preflight and artifact validation.",
    ),
    "golden-snapshot-tests": QualityGateDefinition(
        gate_id="golden-snapshot-tests",
        name="Golden Snapshot Test Gate",
        category="golden_snapshot",
        description="Pytest coverage for committed offline fixture snapshots and quality assertions.",
    ),
    "golden-snapshot-check": QualityGateDefinition(
        gate_id="golden-snapshot-check",
        name="Golden Snapshot Check Gate",
        category="golden_snapshot",
        description="Direct committed golden snapshot comparison.",
    ),
    "exa-compat-tests": QualityGateDefinition(
        gate_id="exa-compat-tests",
        name="Exa Compatibility Gate",
        category="exa_compat",
        description="Test suite under the selected exa-py dependency constraint.",
    ),
    "release-scorecard-generate": QualityGateDefinition(
        gate_id="release-scorecard-generate",
        name="Release Scorecard Generation Gate",
        category="release_scorecard",
        description="Release-scorecard artifact generation.",
    ),
    "release-scorecard-validate": QualityGateDefinition(
        gate_id="release-scorecard-validate",
        name="Release Scorecard Validation Gate",
        category="release_scorecard",
        description="Release-scorecard threshold and must-pass gate validation.",
    ),
    "security-hygiene-check": QualityGateDefinition(
        gate_id="security-hygiene-check",
        name="Security Hygiene Gate",
        category="security_hygiene",
        description="Offline repository hygiene scan for secrets, env policy, and unsafe runtime artifacts.",
    ),
    "dependency-hygiene-check": QualityGateDefinition(
        gate_id="dependency-hygiene-check",
        name="Dependency Hygiene Gate",
        category="dependency_hygiene",
        description="Offline dependency manifest hygiene scan for pinning and dependency-file drift.",
    ),
}


def run_quality_gate(
    *,
    gate_id: str,
    command: Sequence[str],
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    repo_root: Path | None = None,
    label: str | None = None,
) -> QualityGateResult:
    """Run one quality-gate command, write artifacts, and return its result."""

    if gate_id not in GATE_DEFINITIONS:
        known = ", ".join(sorted(GATE_DEFINITIONS))
        raise ValueError(f"Unknown quality gate {gate_id!r}. Known gates: {known}")
    if not command:
        raise ValueError("Quality gate command cannot be empty.")

    definition = GATE_DEFINITIONS[gate_id]
    resolved_repo_root = repo_root or discover_repo_root()
    resolved_output_dir = (resolved_repo_root / output_dir).resolve() if not output_dir.is_absolute() else output_dir
    resolved_output_dir.mkdir(parents=True, exist_ok=True)

    artifact_stem = _artifact_stem(gate_id, label)
    log_path = resolved_output_dir / f"{artifact_stem}.log"
    json_path = resolved_output_dir / f"{artifact_stem}.json"
    markdown_path = resolved_output_dir / f"{artifact_stem}.md"

    started = datetime.now(UTC)
    process = subprocess.run(
        list(command),
        cwd=resolved_repo_root,
        capture_output=True,
        check=False,
        text=True,
    )
    finished = datetime.now(UTC)
    summary = _extract_command_summary(process.stdout, process.stderr)
    if not summary:
        summary = f"command exited with code {process.returncode}"

    _write_command_log(
        log_path,
        command=command,
        stdout=process.stdout,
        stderr=process.stderr,
    )
    result = QualityGateResult(
        schema_version=SCHEMA_VERSION,
        gate_id=definition.gate_id,
        name=definition.name,
        category=definition.category,
        description=definition.description,
        label=label,
        status="passed" if process.returncode == 0 else "failed",
        exit_code=process.returncode,
        command=list(command),
        summary=summary,
        started_at=started.isoformat(),
        finished_at=finished.isoformat(),
        duration_seconds=round((finished - started).total_seconds(), 3),
        log_path=str(log_path),
        json_path=str(json_path),
        markdown_path=str(markdown_path),
    )
    json_path.write_text(json.dumps(asdict(result), indent=2), encoding="utf-8")
    markdown_path.write_text(render_quality_gate_result_markdown(result), encoding="utf-8")

    if process.stdout:
        print(process.stdout, end="")
    if process.stderr:
        print(process.stderr, end="", file=sys.stderr)
    print(
        f"Quality gate {result.status}: {result.name}"
        f"{f' ({label})' if label else ''} - {result.summary}"
    )
    print(f"Quality gate artifacts: {json_path}")
    _append_github_step_summary(render_quality_gate_result_markdown(result))
    return result


def collect_quality_gate_results(output_dir: Path) -> list[QualityGateResult]:
    """Load quality-gate result JSON files from an artifact directory."""

    results: list[QualityGateResult] = []
    if not output_dir.exists():
        return results
    for path in sorted(output_dir.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("schema_version") != SCHEMA_VERSION:
            continue
        results.append(QualityGateResult(**payload))
    return results


def render_quality_gate_result_markdown(result: QualityGateResult) -> str:
    """Render one gate result for GitHub step summaries and artifacts."""

    return "\n".join(
        [
            f"## {result.name}",
            "",
            f"- Category: `{result.category}`",
            f"- Gate id: `{result.gate_id}`",
            f"- Label: `{result.label or ''}`",
            f"- Status: `{result.status}`",
            f"- Exit code: `{result.exit_code}`",
            f"- Summary: {result.summary}",
            f"- Log: `{result.log_path}`",
            f"- Command: `{' '.join(result.command)}`",
            "",
        ]
    )


def render_quality_gate_summary(results: Sequence[QualityGateResult]) -> str:
    """Render an aggregate Markdown summary for one CI job."""

    passed = sum(1 for result in results if result.status == "passed")
    failed = sum(1 for result in results if result.status != "passed")
    lines = [
        "# CI Quality Gate Summary",
        "",
        f"- Total gates: {len(results)}",
        f"- Passed: {passed}",
        f"- Failed: {failed}",
        "",
        "| Category | Gate | Label | Status | Summary |",
        "|---|---|---|---|---|",
    ]
    for result in results:
        lines.append(
            "| "
            f"{result.category} | "
            f"{result.name} | "
            f"{result.label or ''} | "
            f"{result.status} | "
            f"{_escape_table_cell(result.summary)} |"
        )

    failed_results = [result for result in results if result.status != "passed"]
    if failed_results:
        lines.extend(["", "## Failed Gates"])
        for result in failed_results:
            lines.append(f"- {result.name}: {result.summary} (log: `{result.log_path}`)")
    lines.append("")
    return "\n".join(lines)


def write_quality_gate_summary(
    *,
    output_dir: Path,
    summary_path: Path,
) -> tuple[Path, list[QualityGateResult]]:
    """Write an aggregate quality-gate summary file."""

    results = collect_quality_gate_results(output_dir)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    markdown = render_quality_gate_summary(results)
    summary_path.write_text(markdown, encoding="utf-8")
    _append_github_step_summary(markdown)
    return summary_path, results


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for running and summarizing quality gates."""

    parser = argparse.ArgumentParser(description="Run categorized CI quality gates")
    subparsers = parser.add_subparsers(dest="command_name", required=True)

    run_parser = subparsers.add_parser("run", help="Run a quality gate command")
    run_parser.add_argument("--gate", required=True, choices=sorted(GATE_DEFINITIONS))
    run_parser.add_argument("--label", help="Optional matrix or variant label")
    run_parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    run_parser.add_argument(
        "--github-output-key",
        help="Optional GitHub Actions output key that receives the gate summary.",
    )
    run_parser.add_argument("gate_command", nargs=argparse.REMAINDER)

    summarize_parser = subparsers.add_parser("summarize", help="Summarize gate artifacts")
    summarize_parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    summarize_parser.add_argument("--summary-path")
    summarize_parser.add_argument("--fail-on-failed", action="store_true")

    args = parser.parse_args(argv)
    repo_root = discover_repo_root()
    output_dir = _resolve_path(repo_root, Path(args.output_dir))

    if args.command_name == "run":
        gate_command = _strip_remainder_separator(args.gate_command)
        if not gate_command:
            parser.error("quality gate run requires a command after --")
        result = run_quality_gate(
            gate_id=args.gate,
            label=args.label,
            command=gate_command,
            output_dir=output_dir,
            repo_root=repo_root,
        )
        if args.github_output_key:
            _append_github_output(args.github_output_key, result.summary)
        return result.exit_code

    summary_path = (
        _resolve_path(repo_root, Path(args.summary_path))
        if args.summary_path
        else output_dir / "summary.md"
    )
    written_path, results = write_quality_gate_summary(output_dir=output_dir, summary_path=summary_path)
    failed = [result for result in results if result.status != "passed"]
    print(f"Wrote quality gate summary: {written_path}")
    print(f"Quality gates passed: {len(results) - len(failed)}/{len(results)}")
    return 1 if args.fail_on_failed and (failed or not results) else 0


def _write_command_log(
    path: Path,
    *,
    command: Sequence[str],
    stdout: str,
    stderr: str,
) -> None:
    path.write_text(
        "\n".join(
            [
                "# Command",
                " ".join(command),
                "",
                "# stdout",
                stdout.rstrip(),
                "",
                "# stderr",
                stderr.rstrip(),
                "",
            ]
        ),
        encoding="utf-8",
    )


def _extract_command_summary(stdout: str, stderr: str) -> str:
    summary_tokens = (
        "passed",
        "failed",
        "error",
        "errors",
        "skipped",
        "warning",
        "warnings",
        "snapshot",
        "scorecard",
        "verification",
    )
    lines = [line.strip() for line in f"{stdout}\n{stderr}".splitlines() if line.strip()]
    for line in reversed(lines):
        normalized = line.lower()
        if any(token in normalized for token in summary_tokens):
            return line
    return lines[-1] if lines else ""


def _append_github_step_summary(markdown: str) -> None:
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not summary_path:
        return
    with Path(summary_path).open("a", encoding="utf-8") as handle:
        handle.write(markdown)
        if not markdown.endswith("\n"):
            handle.write("\n")


def _append_github_output(key: str, value: str) -> None:
    output_path = os.environ.get("GITHUB_OUTPUT")
    if not output_path:
        return
    with Path(output_path).open("a", encoding="utf-8") as handle:
        handle.write(f"{key}<<EOF\n{value}\nEOF\n")


def _resolve_path(repo_root: Path, path: Path) -> Path:
    return path if path.is_absolute() else (repo_root / path).resolve()


def _strip_remainder_separator(values: Sequence[str]) -> list[str]:
    if values and values[0] == "--":
        return list(values[1:])
    return list(values)


def _artifact_stem(gate_id: str, label: str | None) -> str:
    if not label:
        return gate_id
    return f"{gate_id}-{_slugify(label)}"


def _slugify(value: str) -> str:
    normalized = "".join(char.lower() if char.isalnum() else "-" for char in value.strip())
    collapsed = "-".join(part for part in normalized.split("-") if part)
    return collapsed or "gate"


def _escape_table_cell(value: str) -> str:
    return value.replace("|", "\\|")


if __name__ == "__main__":
    raise SystemExit(main())
