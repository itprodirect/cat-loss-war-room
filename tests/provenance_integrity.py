"""Shared provenance-integrity assertions for audit snapshots and read models."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Mapping

from war_room.carrier_module import build_carrier_doc_pack
from war_room.caselaw_module import build_caselaw_pack
from war_room.export_md import render_markdown_memo
from war_room.evidence_board import build_evidence_board
from war_room.issue_workspace import build_issue_workspace
from war_room.memo_composer import build_memo_composer
from war_room.models import (
    EvidenceBoardReadModel,
    IssueWorkspaceReadModel,
    MemoComposerReadModel,
    QuerySpec,
    RunAuditSnapshot,
    adapt_evidence_board,
    adapt_issue_workspace,
    adapt_memo_composer,
    adapt_run_audit_snapshot,
    run_audit_snapshot_from_parts,
)
from war_room.query_plan import generate_query_plan, load_case_intake
from war_room.scenarios import load_scenario_for_fixture_case
from war_room.weather_module import build_weather_brief

_REQUIRED_FIXTURE_FILES = ("weather.json", "carrier.json", "caselaw.json", "citation_verify.json")
_CLUSTER_ID_RE = re.compile(r"\bcluster-\d+\b")


def committed_fixture_case_keys(repo_root: Path) -> list[str]:
    """Return fixture case keys that have the complete offline module bundle."""

    cache_samples_dir = repo_root / "cache_samples"
    return [
        scenario_dir.name
        for scenario_dir in sorted(path for path in cache_samples_dir.iterdir() if path.is_dir())
        if all((scenario_dir / name).exists() for name in _REQUIRED_FIXTURE_FILES)
    ]


def fixture_parts(repo_root: Path, case_key: str) -> tuple[Any, Any, Any, Any, Any, list[QuerySpec]]:
    """Build current notebook-era module outputs from committed fixtures only."""

    cache_samples_dir = repo_root / "cache_samples"
    scenario = load_scenario_for_fixture_case(case_key, repo_root=repo_root)
    intake = (
        scenario.to_case_intake()
        if scenario is not None
        else load_case_intake(repo_root / "eval" / "intakes" / f"{case_key}.json")
    )
    query_plan = generate_query_plan(intake)
    weather = build_weather_brief(
        intake,
        None,
        query_plan=query_plan,
        cache_samples_dir=str(cache_samples_dir),
    )
    carrier = build_carrier_doc_pack(
        intake,
        None,
        query_plan=query_plan,
        cache_samples_dir=str(cache_samples_dir),
    )
    caselaw = build_caselaw_pack(
        intake,
        None,
        query_plan=query_plan,
        cache_samples_dir=str(cache_samples_dir),
    )
    citecheck = json.loads(
        (cache_samples_dir / case_key / "citation_verify.json").read_text(encoding="utf-8")
    )
    return intake, weather, carrier, caselaw, citecheck, query_plan


def fixture_audit_snapshot(repo_root: Path, case_key: str) -> RunAuditSnapshot:
    """Build the fixture-backed audit snapshot used by the current read models."""

    return run_audit_snapshot_from_parts(*fixture_parts(repo_root, case_key))


def fixture_markdown(repo_root: Path, case_key: str) -> str:
    """Render fixture-backed markdown through the current export path."""

    return render_markdown_memo(*fixture_parts(repo_root, case_key))


def fixture_snapshot_and_markdown(repo_root: Path, case_key: str) -> tuple[RunAuditSnapshot, str]:
    """Build the fixture-backed audit snapshot and markdown from one payload set."""

    parts = fixture_parts(repo_root, case_key)
    return run_audit_snapshot_from_parts(*parts), render_markdown_memo(*parts)


def assert_audit_snapshot_provenance_integrity(
    snapshot: Mapping[str, Any] | RunAuditSnapshot,
) -> None:
    """Assert audit snapshot evidence and cluster references resolve."""

    snapshot = adapt_run_audit_snapshot(snapshot)
    evidence_ids = [item.evidence_id for item in snapshot.evidence_items]
    cluster_ids = [cluster.cluster_id for cluster in snapshot.evidence_clusters]
    evidence_id_set = set(evidence_ids)
    cluster_id_set = set(cluster_ids)

    assert len(evidence_ids) == len(evidence_id_set), "duplicate evidence IDs in audit snapshot"
    assert len(cluster_ids) == len(cluster_id_set), "duplicate cluster IDs in audit snapshot"

    for cluster in snapshot.evidence_clusters:
        _assert_known_ids(
            f"cluster {cluster.cluster_id} evidence_ids",
            cluster.evidence_ids,
            evidence_id_set,
        )
        assert cluster.member_count == len(cluster.evidence_ids), (
            f"cluster {cluster.cluster_id} member_count does not match evidence_ids"
        )

    for claim in snapshot.memo_claims:
        _assert_known_ids(
            f"memo claim {claim.claim_id} evidence_ids",
            claim.evidence_ids,
            evidence_id_set,
        )
        _assert_known_ids(
            f"memo claim {claim.claim_id} cluster_ids",
            claim.cluster_ids,
            cluster_id_set,
        )

    for event in snapshot.review_events:
        _assert_known_ids(
            f"review event {event.event_id} related_evidence_ids",
            event.related_evidence_ids,
            evidence_id_set,
        )
        _assert_known_ids(
            f"review event {event.event_id} related_cluster_ids",
            event.related_cluster_ids,
            cluster_id_set,
        )

    quality = snapshot.quality_snapshot
    assert quality.evidence_item_count == len(snapshot.evidence_items)
    assert quality.evidence_cluster_count == len(snapshot.evidence_clusters)
    assert quality.provenance_link_count == sum(
        len(cluster.provenance_urls) for cluster in snapshot.evidence_clusters
    )


def assert_evidence_board_provenance_integrity(
    board: Mapping[str, Any] | EvidenceBoardReadModel,
    snapshot: Mapping[str, Any] | RunAuditSnapshot,
) -> None:
    """Assert Evidence Board read-model references resolve to the snapshot."""

    board = adapt_evidence_board(board)
    evidence_ids, cluster_ids = _snapshot_id_sets(snapshot)
    _assert_known_ids(
        "Evidence Board cluster cards",
        (card.cluster_id for card in board.cluster_cards),
        cluster_ids,
    )
    _assert_known_ids(
        "Evidence Board preview evidence IDs",
        (
            preview.evidence_id
            for card in board.cluster_cards
            for preview in card.evidence_previews
        ),
        evidence_ids,
    )
    _assert_known_ids(
        "Evidence Board ungrouped evidence IDs",
        (preview.evidence_id for preview in board.ungrouped_items),
        evidence_ids,
    )


def assert_issue_workspace_provenance_integrity(
    workspace: Mapping[str, Any] | IssueWorkspaceReadModel,
    snapshot: Mapping[str, Any] | RunAuditSnapshot,
) -> None:
    """Assert Issue Workspace read-model references resolve to the snapshot."""

    workspace = adapt_issue_workspace(workspace)
    evidence_ids, cluster_ids = _snapshot_id_sets(snapshot)
    _assert_known_ids(
        "Issue Workspace evidence cluster IDs",
        (
            cluster_id
            for card in workspace.issue_cards
            for cluster_id in card.evidence_cluster_ids
        ),
        cluster_ids,
    )
    _assert_known_ids(
        "Issue Workspace case-candidate evidence IDs",
        (
            candidate.evidence_id
            for card in workspace.issue_cards
            for candidate in card.case_candidates
        ),
        evidence_ids,
    )
    _assert_known_ids(
        "Issue Workspace citation-outcome evidence IDs",
        (
            outcome.evidence_id
            for card in workspace.issue_cards
            for outcome in card.citation_outcomes
        ),
        evidence_ids,
    )


def assert_memo_composer_provenance_integrity(
    composer: Mapping[str, Any] | MemoComposerReadModel,
    snapshot: Mapping[str, Any] | RunAuditSnapshot,
) -> None:
    """Assert Memo Composer read-model claim links resolve to the snapshot."""

    composer = adapt_memo_composer(composer)
    evidence_ids, cluster_ids = _snapshot_id_sets(snapshot)
    _assert_known_ids(
        "Memo Composer claim-link evidence IDs",
        (
            evidence_id
            for section in composer.section_cards
            for claim in section.claim_links
            for evidence_id in claim.evidence_ids
        ),
        evidence_ids,
    )
    _assert_known_ids(
        "Memo Composer claim-link cluster IDs",
        (
            cluster_id
            for section in composer.section_cards
            for claim in section.claim_links
            for cluster_id in claim.cluster_ids
        ),
        cluster_ids,
    )


def assert_markdown_provenance_integrity(
    markdown: str,
    snapshot: Mapping[str, Any] | RunAuditSnapshot,
) -> None:
    """Assert rendered markdown contains only current snapshot IDs."""

    snapshot = adapt_run_audit_snapshot(snapshot)
    evidence_ids, cluster_ids = _snapshot_id_sets(snapshot)
    evidence_refs = set(_markdown_evidence_index_ids(markdown))
    cluster_refs = set(_CLUSTER_ID_RE.findall(markdown))

    _assert_known_ids("Markdown evidence references", evidence_refs, evidence_ids)
    _assert_known_ids("Markdown cluster references", cluster_refs, cluster_ids)

    _assert_known_ids(
        "Markdown Evidence Index rows",
        (item.evidence_id for item in snapshot.evidence_items),
        evidence_refs,
    )
    _assert_known_ids(
        "Markdown cluster rows",
        (cluster.cluster_id for cluster in snapshot.evidence_clusters),
        cluster_refs,
    )


def assert_all_current_provenance_surfaces(
    snapshot: Mapping[str, Any] | RunAuditSnapshot,
    markdown: str,
) -> None:
    """Assert the current audit, read-model, and markdown provenance surfaces."""

    snapshot = adapt_run_audit_snapshot(snapshot)
    assert_audit_snapshot_provenance_integrity(snapshot)
    assert_evidence_board_provenance_integrity(build_evidence_board(snapshot), snapshot)
    assert_issue_workspace_provenance_integrity(build_issue_workspace(snapshot), snapshot)
    assert_memo_composer_provenance_integrity(build_memo_composer(snapshot), snapshot)
    assert_markdown_provenance_integrity(markdown, snapshot)


def _snapshot_id_sets(snapshot: Mapping[str, Any] | RunAuditSnapshot) -> tuple[set[str], set[str]]:
    snapshot = adapt_run_audit_snapshot(snapshot)
    evidence_ids = {item.evidence_id for item in snapshot.evidence_items}
    cluster_ids = {cluster.cluster_id for cluster in snapshot.evidence_clusters}
    return evidence_ids, cluster_ids


def _markdown_evidence_index_ids(markdown: str) -> list[str]:
    if "## Appendix: Evidence Index" not in markdown:
        return []
    section = markdown.split("## Appendix: Evidence Index", 1)[1]
    next_section = section.find("\n## ")
    if next_section != -1:
        section = section[:next_section]

    evidence_ids: list[str] = []
    for line in section.splitlines():
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if not cells or cells[0] == "ID" or set(cells[0]) <= {"-"}:
            continue
        evidence_ids.append(cells[0])
    return evidence_ids


def _assert_known_ids(label: str, refs: Any, known_ids: set[str]) -> None:
    ref_set = {ref for ref in refs if ref}
    missing = sorted(ref_set - known_ids)
    assert not missing, f"{label} reference missing IDs: {', '.join(missing)}"
