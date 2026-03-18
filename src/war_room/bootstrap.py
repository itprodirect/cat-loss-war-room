"""Project bootstrap helpers for scripts, notebooks, and tests."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from war_room.settings import WarRoomSettings, load_settings


@dataclass(frozen=True)
class BootstrapContext:
    """Resolved bootstrap context for the current repo checkout."""

    repo_root: Path
    settings: WarRoomSettings


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
        return _run_supported_verification(context)

    if args.json:
        print(json.dumps(summary, indent=2))
        return 0

    print("CAT-Loss War Room Bootstrap")
    print("=" * 32)
    for key, value in summary.items():
        print(f"{key}: {value}")
    return 0


def _run_supported_verification(context: BootstrapContext) -> int:
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
        check=False,
    )
    if result.returncode:
        print(f"Verification failed: pytest exited with code {result.returncode}.")
        return result.returncode

    print("Verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
