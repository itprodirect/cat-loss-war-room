"""Project bootstrap helpers for scripts, notebooks, and tests."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

from war_room.settings import WarRoomSettings, load_settings


@dataclass(frozen=True)
class BootstrapContext:
    """Resolved bootstrap context for the current repo checkout."""

    repo_root: Path
    settings: WarRoomSettings


@dataclass(frozen=True)
class VerifyRunManifest:
    """One verify-run manifest tying generated evidence artifacts together."""

    run_id: str
    created_at: str
    candidate: str
    verification_command: str
    verification_summary: str
    repo_root: str
    preflight_artifact_path: str
    release_scorecard_json_path: str
    release_scorecard_markdown_path: str


@dataclass(frozen=True)
class LatestVerifyPointer:
    """Stable pointer to the newest successful verify-run manifest."""

    run_id: str
    created_at: str
    candidate: str
    verify_manifest_path: str


def discover_repo_root(start_path: Path | None = None) -> Path:
    """Find the repo root by walking upward until pyproject.toml is found."""
    current = (start_path or Path.cwd()).resolve()

    if current.is_file():
        current = current.parent

    for candidate in (current, *current.parents):
        if (candidate / "pyproject.toml").exists():
            return candidate

    raise FileNotFoundError("Could not locate repo root from current path")


def bootstrap_runtime(
    *,
    start_path: Path | None = None,
    env_file: Path | None = None,
    ensure_dirs: bool = True,
) -> BootstrapContext:
    """Resolve repo root, load settings, and optionally ensure runtime dirs exist."""
    repo_root = discover_repo_root(start_path)
    settings = load_settings(repo_root=repo_root, env_file=env_file)

    if ensure_dirs:
        for path in (settings.cache_dir, settings.cache_samples_dir, settings.output_dir, settings.runs_dir):
            path.mkdir(parents=True, exist_ok=True)

    return BootstrapContext(repo_root=repo_root, settings=settings)


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for bootstrap status, demo preflight, or supported local verification."""
    parser = argparse.ArgumentParser(description="Resolve CAT-Loss War Room runtime settings")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--preflight",
        action="store_true",
        help="Run the deterministic offline demo smoke instead of printing bootstrap settings",
    )
    mode.add_argument(
        "--verify",
        action="store_true",
        help="Run the supported local verification path (preflight + pytest -q)",
    )
    parser.add_argument(
        "--release-candidate",
        help="Optional release-scorecard candidate label for --verify. Defaults to the current branch when available.",
    )
    parser.add_argument("--json", action="store_true", help="Print the resolved settings as JSON")
    args = parser.parse_args(argv)

    context = bootstrap_runtime()
    summary = context.settings.display_summary() | {"repo_root": str(context.repo_root)}

    if args.preflight:
        from war_room.preflight import render_demo_preflight_report, report_to_payload, run_demo_preflight

        report = run_demo_preflight(context)
        if args.json:
            print(json.dumps(report_to_payload(report), indent=2))
        else:
            print(render_demo_preflight_report(report), end="")
        return 0 if report.passed else 1

    if args.verify:
        return _run_supported_verification(context, release_candidate=args.release_candidate)

    if args.json:
        print(json.dumps(summary, indent=2))
        return 0

    print("CAT-Loss War Room Bootstrap")
    print("=" * 32)
    for key, value in summary.items():
        print(f"{key}: {value}")
    return 0


def _run_supported_verification(
    context: BootstrapContext,
    *,
    release_candidate: str | None = None,
) -> int:
    """Run the deterministic offline preflight plus the supported pytest command."""
    from war_room.preflight import render_demo_preflight_report, run_demo_preflight

    print("CAT-Loss War Room Verification")
    print("=" * 32)

    report = run_demo_preflight(context)
    print(render_demo_preflight_report(report), end="")
    if not report.passed:
        print("Verification failed: offline demo preflight did not pass.")
        return 1

    print("## Test Suite")
    print("- Command: pytest -q")
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q"],
        cwd=context.repo_root,
        capture_output=True,
        check=False,
        text=True,
    )
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)

    verification_summary = _extract_pytest_summary(result.stdout, result.stderr)
    if not verification_summary:
        verification_summary = f"pytest exited with code {result.returncode}"
    if result.returncode:
        print(f"Verification failed: pytest exited with code {result.returncode}.")
        return result.returncode

    candidate = _resolve_release_candidate(context, override=release_candidate)
    run_id = _resolve_verify_run_id(report)
    try:
        preflight_artifact_path = _write_verify_preflight_artifact(
            context,
            candidate=candidate,
            preflight_report=report,
            run_id=run_id,
        )
        scorecard_json_path, scorecard_markdown_path = _write_verify_release_scorecard(
            context,
            candidate=candidate,
            run_id=run_id,
            verification_summary=verification_summary,
            preflight_report=report,
            preflight_artifact_path=preflight_artifact_path,
        )
        verify_manifest_path = _write_verify_manifest(
            context,
            run_id=run_id,
            created_at=report.created_at,
            candidate=candidate,
            verification_summary=verification_summary,
            preflight_artifact_path=preflight_artifact_path,
            release_scorecard_json_path=scorecard_json_path,
            release_scorecard_markdown_path=scorecard_markdown_path,
        )
        latest_verify_pointer_path = _write_latest_verify_pointer(
            context,
            run_id=run_id,
            created_at=report.created_at,
            candidate=candidate,
            verify_manifest_path=verify_manifest_path,
        )
    except Exception as exc:  # pragma: no cover - defensive failure path
        print(f"Verification failed: could not write verification artifacts ({type(exc).__name__}: {exc}).")
        return 1

    print("## Verify Manifest")
    print(f"- JSON: {verify_manifest_path}")
    print(f"- Latest: {latest_verify_pointer_path}")
    print("## Preflight Artifact")
    print(f"- Run id: {run_id}")
    print(f"- JSON: {preflight_artifact_path}")
    print("## Release Scorecard")
    print(f"- Candidate: {candidate}")
    print(f"- JSON: {scorecard_json_path}")
    print(f"- Markdown: {scorecard_markdown_path}")
    print("Verification passed.")
    return 0


def _resolve_release_candidate(
    context: BootstrapContext,
    *,
    override: str | None = None,
) -> str:
    """Resolve the release-scorecard candidate label for a local verify run."""

    if override:
        return override.strip() or "local-verify"

    result = subprocess.run(
        [
            "git",
            f"-c",
            f"safe.directory={context.repo_root}",
            "rev-parse",
            "--abbrev-ref",
            "HEAD",
        ],
        cwd=context.repo_root,
        capture_output=True,
        check=False,
        text=True,
    )
    branch = result.stdout.strip()
    if result.returncode == 0 and branch and branch.upper() != "HEAD":
        return branch
    return "local-verify"


def _write_verify_release_scorecard(
    context: BootstrapContext,
    *,
    candidate: str,
    run_id: str,
    verification_summary: str,
    preflight_report,
    preflight_artifact_path: Path,
) -> tuple[Path, Path]:
    """Write the release-scorecard artifact paired with a successful verify run."""

    from war_room.release_scorecard import (
        build_demo_release_scorecard,
        collect_fixture_coverage,
        collect_scenario_registry_coverage,
        summarize_preflight_report,
        write_release_scorecard_artifacts,
    )

    fixture_coverage = collect_fixture_coverage(context.settings.cache_samples_dir)
    scenario_registry = collect_scenario_registry_coverage(context.repo_root, context.settings.cache_samples_dir)
    scorecard = build_demo_release_scorecard(
        run_id=run_id,
        candidate=candidate,
        verification_summary=verification_summary,
        preflight_artifact_path=str(preflight_artifact_path),
        preflight_summary=summarize_preflight_report(preflight_report),
        fixture_coverage=fixture_coverage,
        scenario_registry=scenario_registry,
    )
    output_dir = context.settings.runs_dir / "release_scorecards"
    return write_release_scorecard_artifacts(scorecard, output_dir=output_dir)


def _write_verify_preflight_artifact(
    context: BootstrapContext,
    *,
    candidate: str,
    preflight_report,
    run_id: str,
) -> Path:
    """Persist the live preflight report for the verify run."""

    from war_room.preflight import write_preflight_artifact

    output_dir = context.settings.runs_dir / "preflight"
    return write_preflight_artifact(
        preflight_report,
        output_dir=output_dir,
        artifact_label=candidate,
        run_id=run_id,
    )


def _resolve_verify_run_id(preflight_report) -> str:
    """Return the shared run id for verify-generated artifacts."""

    from war_room.preflight import preflight_run_id

    return preflight_run_id(preflight_report)


def _write_verify_manifest(
    context: BootstrapContext,
    *,
    run_id: str,
    created_at: str,
    candidate: str,
    verification_summary: str,
    preflight_artifact_path: Path,
    release_scorecard_json_path: Path,
    release_scorecard_markdown_path: Path,
) -> Path:
    """Persist one machine-readable manifest for the verify run."""

    manifest = VerifyRunManifest(
        run_id=run_id,
        created_at=created_at,
        candidate=candidate,
        verification_command="pytest -q",
        verification_summary=verification_summary,
        repo_root=str(context.repo_root),
        preflight_artifact_path=str(preflight_artifact_path),
        release_scorecard_json_path=str(release_scorecard_json_path),
        release_scorecard_markdown_path=str(release_scorecard_markdown_path),
    )
    output_dir = context.settings.runs_dir / "verify"
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{created_at[:10]}_{_slugify_verify_label(candidate)}_{run_id.lower()}"
    output_path = output_dir / f"{stem}.json"
    output_path.write_text(json.dumps(asdict(manifest), indent=2), encoding="utf-8")
    return output_path


def _write_latest_verify_pointer(
    context: BootstrapContext,
    *,
    run_id: str,
    created_at: str,
    candidate: str,
    verify_manifest_path: Path,
) -> Path:
    """Persist a stable pointer to the newest successful verify-run manifest."""

    latest_pointer = LatestVerifyPointer(
        run_id=run_id,
        created_at=created_at,
        candidate=candidate,
        verify_manifest_path=str(verify_manifest_path),
    )
    output_dir = context.settings.runs_dir / "verify"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "latest.json"
    output_path.write_text(json.dumps(asdict(latest_pointer), indent=2), encoding="utf-8")
    return output_path


def _extract_pytest_summary(stdout: str, stderr: str) -> str:
    """Extract the final pytest result summary from captured command output."""

    summary_tokens = ("passed", "failed", "error", "errors", "skipped", "warning", "warnings", "xfailed", "xpassed")
    lines = [line.strip() for line in f"{stdout}\n{stderr}".splitlines() if line.strip()]
    for line in reversed(lines):
        normalized = line.lower()
        if any(token in normalized for token in summary_tokens):
            return line
    return ""


def _slugify_verify_label(value: str) -> str:
    normalized = "".join(char.lower() if char.isalnum() else "-" for char in value.strip())
    collapsed = "-".join(part for part in normalized.split("-") if part)
    return collapsed or "verify"


if __name__ == "__main__":
    raise SystemExit(main())
