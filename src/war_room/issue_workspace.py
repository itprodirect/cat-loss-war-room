"""Issue-workspace read model helpers derived from the audit snapshot."""

from __future__ import annotations

from typing import Any, Mapping

from war_room.models import (
    CaseIntake,
    CaseLawPack,
    CarrierDocPack,
    CitationVerifyPack,
    IssueWorkspaceCard,
    IssueWorkspaceCaseCandidate,
    IssueWorkspaceCitationOutcome,
    IssueWorkspaceReadModel,
    QuerySpec,
    RunAuditSnapshot,
    WeatherBrief,
    adapt_issue_workspace,
    adapt_run_audit_snapshot,
    run_audit_snapshot_from_parts,
)

_TIER_RANK = {
    "primary": 0,
    "official": 0,
    "government": 0,
    "professional": 1,
    "secondary": 2,
    "unvetted": 3,
    "unknown": 4,
}


def build_issue_workspace(
    snapshot: Mapping[str, Any] | RunAuditSnapshot,
) -> IssueWorkspaceReadModel:
    """Build an issue-workspace read model from the canonical audit snapshot."""

    typed_snapshot = adapt_run_audit_snapshot(snapshot)
    evidence_by_id = {item.evidence_id: item for item in typed_snapshot.evidence_items}
    cluster_by_id = {cluster.cluster_id: cluster for cluster in typed_snapshot.evidence_clusters}
    claims_by_cluster: dict[str, list[Any]] = {}
    for claim in typed_snapshot.memo_claims:
        for cluster_id in claim.cluster_ids:
            claims_by_cluster.setdefault(cluster_id, []).append(claim)
    events_by_cluster: dict[str, list[Any]] = {}
    for event in typed_snapshot.review_events:
        for cluster_id in event.related_cluster_ids:
            events_by_cluster.setdefault(cluster_id, []).append(event)

    issue_labels = _ordered_issue_labels(typed_snapshot)
    cards: list[IssueWorkspaceCard] = []
    for issue_label in issue_labels:
        normalized_issue = _normalize_issue_label(issue_label)
        cluster_ids = [
            cluster.cluster_id
            for cluster in typed_snapshot.evidence_clusters
            if _cluster_matches_issue(cluster, evidence_by_id, normalized_issue)
        ]
        candidates = _case_candidates_for_clusters(cluster_ids, cluster_by_id, evidence_by_id)
        citation_outcomes = _citation_outcomes_for_clusters(cluster_ids, cluster_by_id, evidence_by_id)
        claim_ids = _unique_strings(
            claim.claim_id
            for cluster_id in cluster_ids
            for claim in claims_by_cluster.get(cluster_id, [])
        )
        review_event_ids = _unique_strings(
            event.event_id
            for cluster_id in cluster_ids
            for event in events_by_cluster.get(cluster_id, [])
        )
        review_required = bool(review_event_ids) or not candidates or any(
            outcome.status != "verified" for outcome in citation_outcomes
        )
        status = "review_required" if review_required else "ready"
        cards.append(
            IssueWorkspaceCard(
                issue_label=issue_label,
                summary=(
                    f"{len(cluster_ids)} clusters, {len(candidates)} authorities, "
                    f"{len(citation_outcomes)} citation outcomes."
                ),
                status=status,
                evidence_cluster_ids=cluster_ids,
                case_candidates=candidates,
                citation_outcomes=citation_outcomes,
                claim_ids=claim_ids,
                review_event_ids=review_event_ids,
                review_required=review_required,
            )
        )

    cards.sort(key=lambda card: (0 if card.review_required else 1, card.issue_label.lower()))
    return IssueWorkspaceReadModel(
        run_id=typed_snapshot.export_artifact.run_id,
        issue_cards=cards,
        review_required_issue_count=sum(1 for card in cards if card.review_required),
    )


def build_issue_workspace_from_parts(
    intake: Mapping[str, Any] | CaseIntake,
    weather: Mapping[str, Any] | WeatherBrief,
    carrier: Mapping[str, Any] | CarrierDocPack,
    caselaw: Mapping[str, Any] | CaseLawPack,
    citecheck: Mapping[str, Any] | CitationVerifyPack,
    query_plan: list[Mapping[str, Any] | QuerySpec],
) -> IssueWorkspaceReadModel:
    """Build the read model directly from current notebook-era module outputs."""

    return build_issue_workspace(
        run_audit_snapshot_from_parts(
            intake,
            weather,
            carrier,
            caselaw,
            citecheck,
            query_plan,
        )
    )


def format_issue_workspace(workspace: Mapping[str, Any] | IssueWorkspaceReadModel) -> str:
    """Render the issue-workspace read model as a notebook-friendly text block."""

    workspace = adapt_issue_workspace(workspace)
    lines = [
        "=" * 60,
        "ISSUE WORKSPACE",
        "=" * 60,
        f"  Run ID:            {workspace.run_id}",
        f"  Issues:            {len(workspace.issue_cards)}",
        f"  Review Required:   {workspace.review_required_issue_count} issues",
        (
            "  Next Step:         "
            + (
                "Resolve review-required issues before treating memo claims as settled."
                if workspace.review_required_issue_count
                else "Issue summaries are ready for memo composition."
            )
        ),
        "",
    ]

    for card in workspace.issue_cards:
        lines.append(f"  [{card.status}] {card.issue_label}")
        lines.append(f"    {card.summary}")
        lines.append(f"    Clusters: {', '.join(card.evidence_cluster_ids) or 'none'}")
        if card.case_candidates:
            lines.append("    Strongest authorities:")
            for candidate in card.case_candidates[:3]:
                cite_suffix = f" - {candidate.citation}" if candidate.citation else ""
                lines.append(
                    f"      - {candidate.source_tier} | {candidate.name[:52]}{cite_suffix}"
                )
        else:
            lines.append("    Strongest authorities: none")
        if card.citation_outcomes:
            lines.append("    Citation outcomes:")
            for outcome in card.citation_outcomes[:3]:
                citation = outcome.citation or outcome.evidence_id
                lines.append(
                    f"      - {outcome.status} | {citation[:52]} | {outcome.note[:50]}"
                )
        else:
            lines.append("    Citation outcomes: none")
        if card.claim_ids:
            lines.append(f"    Claims: {', '.join(card.claim_ids)}")
        if card.review_event_ids:
            lines.append(f"    Review events: {', '.join(card.review_event_ids)}")
        lines.append("")

    lines.append("=" * 60)
    return "\n".join(lines)


def _ordered_issue_labels(snapshot: RunAuditSnapshot) -> list[str]:
    labels: list[str] = []
    labels.extend(snapshot.intake.coverage_issues)
    labels.extend(
        item.issue
        for item in snapshot.evidence_items
        if item.issue
    )
    if not labels:
        labels.append("General coverage posture")
    return _unique_strings(label.strip() for label in labels if label and label.strip())


def _cluster_matches_issue(
    cluster: Any,
    evidence_by_id: Mapping[str, Any],
    normalized_issue: str,
) -> bool:
    if normalized_issue == _normalize_issue_label("General coverage posture"):
        return True
    for evidence_id in cluster.evidence_ids:
        item = evidence_by_id.get(evidence_id)
        if item is None or not item.issue:
            continue
        if _normalize_issue_label(item.issue) == normalized_issue:
            return True
    return False


def _case_candidates_for_clusters(
    cluster_ids: list[str],
    cluster_by_id: Mapping[str, Any],
    evidence_by_id: Mapping[str, Any],
) -> list[IssueWorkspaceCaseCandidate]:
    candidates: dict[str, IssueWorkspaceCaseCandidate] = {}
    for cluster_id in cluster_ids:
        cluster = cluster_by_id.get(cluster_id)
        if cluster is None:
            continue
        for evidence_id in cluster.evidence_ids:
            item = evidence_by_id.get(evidence_id)
            if item is None or item.module != "caselaw":
                continue
            candidates[evidence_id] = IssueWorkspaceCaseCandidate(
                evidence_id=evidence_id,
                name=item.title or item.evidence_type,
                citation=item.citation or "",
                source_tier=item.source_tier or "unknown",
                badge=item.badge,
                summary=item.summary,
                url=item.url,
            )
    return sorted(
        candidates.values(),
        key=lambda candidate: (
            _TIER_RANK.get(candidate.source_tier, _TIER_RANK["unknown"]),
            candidate.name.lower(),
        ),
    )


def _citation_outcomes_for_clusters(
    cluster_ids: list[str],
    cluster_by_id: Mapping[str, Any],
    evidence_by_id: Mapping[str, Any],
) -> list[IssueWorkspaceCitationOutcome]:
    outcomes: dict[str, IssueWorkspaceCitationOutcome] = {}
    for cluster_id in cluster_ids:
        cluster = cluster_by_id.get(cluster_id)
        if cluster is None:
            continue
        for evidence_id in cluster.evidence_ids:
            item = evidence_by_id.get(evidence_id)
            if item is None or item.module != "citation_verify":
                continue
            outcomes[evidence_id] = IssueWorkspaceCitationOutcome(
                evidence_id=evidence_id,
                status=(item.source_reason or "").strip() or "unknown",
                citation=item.citation or "",
                note=item.summary,
                source_tier=item.source_tier or "unknown",
                url=item.url,
            )
    return sorted(
        outcomes.values(),
        key=lambda outcome: (0 if outcome.status != "verified" else 1, outcome.citation.lower()),
    )


def _normalize_issue_label(label: str) -> str:
    return " ".join(label.lower().split())


def _unique_strings(values: Any) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result
