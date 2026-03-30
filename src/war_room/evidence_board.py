"""Evidence-board read model helpers derived from the audit snapshot."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from war_room.models import (
    CaseIntake,
    CaseLawPack,
    CarrierDocPack,
    CitationVerifyPack,
    QuerySpec,
    RunAuditSnapshot,
    WeatherBrief,
    adapt_run_audit_snapshot,
    run_audit_snapshot_from_parts,
)


@dataclass(frozen=True)
class EvidenceBoardItemPreview:
    """Compact evidence-item preview for board rendering."""

    evidence_id: str
    module: str
    title: str
    summary: str
    badge: str
    source_tier: str
    url: str | None = None


@dataclass(frozen=True)
class EvidenceBoardClusterCard:
    """Cluster-first evidence card for the transitional read model."""

    cluster_id: str
    cluster_type: str
    label: str
    member_count: int
    modules: list[str] = field(default_factory=list)
    source_tier_summary: str = ""
    issue_labels: list[str] = field(default_factory=list)
    claim_ids: list[str] = field(default_factory=list)
    review_event_ids: list[str] = field(default_factory=list)
    provenance_urls: list[str] = field(default_factory=list)
    review_required: bool = False
    evidence_previews: list[EvidenceBoardItemPreview] = field(default_factory=list)


@dataclass(frozen=True)
class EvidenceBoardReadModel:
    """Cluster-first evidence-board read model for current notebook-era flows."""

    run_id: str
    total_clusters: int
    total_evidence_items: int
    review_required_clusters: int
    primary_source_count: int
    secondary_source_count: int
    fallback_to_item_view: bool = False
    cluster_cards: list[EvidenceBoardClusterCard] = field(default_factory=list)
    ungrouped_items: list[EvidenceBoardItemPreview] = field(default_factory=list)


def build_evidence_board(
    snapshot: Mapping[str, Any] | RunAuditSnapshot,
) -> EvidenceBoardReadModel:
    """Build a cluster-first evidence-board read model from the audit snapshot."""

    typed_snapshot = adapt_run_audit_snapshot(snapshot)
    evidence_by_id = {
        item.evidence_id: item
        for item in typed_snapshot.evidence_items
    }
    claims_by_cluster: dict[str, list[Any]] = {}
    for claim in typed_snapshot.memo_claims:
        for cluster_id in claim.cluster_ids:
            claims_by_cluster.setdefault(cluster_id, []).append(claim)

    review_events_by_cluster: dict[str, list[Any]] = {}
    for event in typed_snapshot.review_events:
        for cluster_id in event.related_cluster_ids:
            review_events_by_cluster.setdefault(cluster_id, []).append(event)

    cards: list[EvidenceBoardClusterCard] = []
    for cluster in typed_snapshot.evidence_clusters:
        items = [
            evidence_by_id[evidence_id]
            for evidence_id in cluster.evidence_ids
            if evidence_id in evidence_by_id
        ]
        linked_claims = claims_by_cluster.get(cluster.cluster_id, [])
        linked_events = review_events_by_cluster.get(cluster.cluster_id, [])
        issue_labels = _unique_strings(
            item.issue.strip()
            for item in items
            if item.issue and item.issue.strip()
        )
        claim_ids = _unique_strings(claim.claim_id for claim in linked_claims)
        review_event_ids = _unique_strings(event.event_id for event in linked_events)
        review_required = (
            cluster.review_required
            or bool(linked_events)
        )
        cards.append(
            EvidenceBoardClusterCard(
                cluster_id=cluster.cluster_id,
                cluster_type=cluster.cluster_type,
                label=cluster.label,
                member_count=cluster.member_count,
                modules=list(cluster.modules),
                source_tier_summary=_format_count_summary(
                    _count_values(item.source_tier or "unknown" for item in items)
                ),
                issue_labels=issue_labels,
                claim_ids=claim_ids,
                review_event_ids=review_event_ids,
                provenance_urls=list(cluster.provenance_urls),
                review_required=review_required,
                evidence_previews=[
                    EvidenceBoardItemPreview(
                        evidence_id=item.evidence_id,
                        module=item.module,
                        title=item.title or item.evidence_type,
                        summary=item.summary,
                        badge=item.badge,
                        source_tier=item.source_tier or "unknown",
                        url=item.url,
                    )
                    for item in items[:3]
                ],
            )
        )

    cards.sort(
        key=lambda card: (
            0 if card.review_required else 1,
            -card.member_count,
            card.label.lower(),
        )
    )

    ungrouped_items: list[EvidenceBoardItemPreview] = []
    fallback_to_item_view = False
    if not cards and typed_snapshot.evidence_items:
        fallback_to_item_view = True
        ungrouped_items = [
            EvidenceBoardItemPreview(
                evidence_id=item.evidence_id,
                module=item.module,
                title=item.title or item.evidence_type,
                summary=item.summary,
                badge=item.badge,
                source_tier=item.source_tier or "unknown",
                url=item.url,
            )
            for item in typed_snapshot.evidence_items[:8]
        ]

    quality = typed_snapshot.quality_snapshot
    return EvidenceBoardReadModel(
        run_id=typed_snapshot.export_artifact.run_id,
        total_clusters=len(typed_snapshot.evidence_clusters),
        total_evidence_items=len(typed_snapshot.evidence_items),
        review_required_clusters=sum(1 for card in cards if card.review_required),
        primary_source_count=quality.primary_source_count,
        secondary_source_count=quality.secondary_source_count,
        fallback_to_item_view=fallback_to_item_view,
        cluster_cards=cards,
        ungrouped_items=ungrouped_items,
    )


def build_evidence_board_from_parts(
    intake: Mapping[str, Any] | CaseIntake,
    weather: Mapping[str, Any] | WeatherBrief,
    carrier: Mapping[str, Any] | CarrierDocPack,
    caselaw: Mapping[str, Any] | CaseLawPack,
    citecheck: Mapping[str, Any] | CitationVerifyPack,
    query_plan: list[Mapping[str, Any] | QuerySpec],
) -> EvidenceBoardReadModel:
    """Build the read model directly from current notebook-era module outputs."""

    return build_evidence_board(
        run_audit_snapshot_from_parts(
            intake,
            weather,
            carrier,
            caselaw,
            citecheck,
            query_plan,
        )
    )


def format_evidence_board(board: EvidenceBoardReadModel) -> str:
    """Render the evidence-board read model as a notebook-friendly text block."""

    lines = [
        "=" * 60,
        "EVIDENCE BOARD",
        "=" * 60,
        f"  Run ID:            {board.run_id}",
        f"  Clusters:          {board.total_clusters}",
        f"  Evidence Items:    {board.total_evidence_items}",
        f"  Review Required:   {board.review_required_clusters} clusters",
        (
            "  Source Balance:    "
            f"{board.primary_source_count} primary / {board.secondary_source_count} secondary"
        ),
        (
            "  Next Step:         "
            + (
                "Inspect review-required clusters before relying on memo language."
                if board.review_required_clusters
                else "Evidence clusters are ready for issue-level review."
            )
        ),
        "",
    ]

    if board.fallback_to_item_view:
        lines.append("  Clustering unavailable. Falling back to item view.")
        for item in board.ungrouped_items:
            lines.append(
                f"  - {item.evidence_id} | {item.module} | {item.source_tier} | {item.title[:60]}"
            )
        lines.append("=" * 60)
        return "\n".join(lines)

    for card in board.cluster_cards:
        state = "review_required" if card.review_required else "ready"
        lines.append(
            f"  [{state}] {card.cluster_id} | {card.cluster_type} | {card.member_count} items"
        )
        lines.append(f"    Label: {card.label}")
        lines.append(f"    Modules: {', '.join(card.modules) or 'none'}")
        lines.append(f"    Source tiers: {card.source_tier_summary or 'unknown'}")
        if card.issue_labels:
            lines.append(f"    Issues: {', '.join(card.issue_labels)}")
        if card.claim_ids:
            lines.append(f"    Claims: {', '.join(card.claim_ids)}")
        if card.review_event_ids:
            lines.append(f"    Review events: {', '.join(card.review_event_ids)}")
        if card.provenance_urls:
            lines.append(f"    Provenance URLs: {len(card.provenance_urls)}")
        lines.append("    Evidence:")
        for item in card.evidence_previews:
            title = item.title[:56]
            lines.append(
                f"      - {item.evidence_id} | {item.module} | {item.source_tier} | {title}"
            )
        lines.append("")

    lines.append("=" * 60)
    return "\n".join(lines)


def _count_values(values: Any) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    return counts


def _format_count_summary(counts: Mapping[str, int]) -> str:
    ordered = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    return ", ".join(f"{label} {count}" for label, count in ordered)


def _unique_strings(values: Any) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result
