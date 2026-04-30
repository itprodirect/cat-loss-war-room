"""Evidence-board read model helpers derived from the audit snapshot."""

from __future__ import annotations

import html
from typing import Any, Mapping

from war_room.models import (
    CaseIntake,
    CaseLawPack,
    CarrierDocPack,
    CitationVerifyPack,
    EvidenceBoardClusterCard,
    EvidenceBoardItemPreview,
    EvidenceBoardReadModel,
    QuerySpec,
    RunAuditSnapshot,
    WeatherBrief,
    adapt_evidence_board,
    adapt_run_audit_snapshot,
    run_audit_snapshot_from_parts,
)


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


def format_evidence_board(board: Mapping[str, Any] | EvidenceBoardReadModel) -> str:
    """Render the evidence-board read model as a notebook-friendly text block."""

    board = adapt_evidence_board(board)
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


def render_evidence_board_html(board: Mapping[str, Any] | EvidenceBoardReadModel) -> str:
    """Render the evidence-board read model as a styled notebook HTML panel."""

    board = adapt_evidence_board(board)
    review_state = (
        "review-required"
        if board.review_required_clusters
        else "ready"
    )
    next_step = (
        "Inspect review-required clusters before relying on memo language."
        if board.review_required_clusters
        else "Evidence clusters are ready for issue-level review."
    )

    parts = [
        '<section class="wr-evidence-board" aria-label="Evidence Board">',
        _evidence_board_css(),
        '<header class="wr-eb-header">',
        '<div>',
        '<p class="wr-eb-kicker">Evidence Board</p>',
        '<h2>Cluster-first evidence review</h2>',
        (
            '<p class="wr-eb-subtitle">'
            'Review source quality, linked claims, and attorney follow-up before using memo prose.'
            '</p>'
        ),
        '</div>',
        f'<span class="wr-eb-status wr-eb-status--{review_state}">{_state_text(review_state)}</span>',
        '</header>',
        '<div class="wr-eb-metrics">',
        _metric("Run ID", board.run_id),
        _metric("Clusters", str(board.total_clusters)),
        _metric("Evidence Items", str(board.total_evidence_items)),
        _metric("Review Required", f"{board.review_required_clusters} clusters"),
        _metric(
            "Source Balance",
            f"{board.primary_source_count} primary / {board.secondary_source_count} secondary",
        ),
        '</div>',
        f'<p class="wr-eb-next">{_escape(next_step)}</p>',
    ]

    if board.fallback_to_item_view:
        parts.append(
            '<div class="wr-eb-alert">Clustering is unavailable. Showing item-level evidence.</div>'
        )
        parts.append('<div class="wr-eb-list">')
        for item in board.ungrouped_items:
            parts.append(_render_item_preview(item))
        parts.append('</div>')
        parts.append('</section>')
        return "".join(parts)

    parts.append('<div class="wr-eb-grid">')
    for card in board.cluster_cards:
        parts.append(_render_cluster_card(card))
    parts.append('</div>')
    parts.append('</section>')
    return "".join(parts)


def _render_cluster_card(card: EvidenceBoardClusterCard) -> str:
    state = "review-required" if card.review_required else "ready"
    issue_text = ", ".join(card.issue_labels) if card.issue_labels else "none"
    claim_text = ", ".join(card.claim_ids) if card.claim_ids else "none"
    review_text = ", ".join(card.review_event_ids) if card.review_event_ids else "none"
    provenance_text = str(len(card.provenance_urls))
    parts = [
        f'<article class="wr-eb-card wr-eb-card--{state}">',
        '<div class="wr-eb-card-head">',
        f'<span class="wr-eb-status wr-eb-status--{state}">{_state_text(state)}</span>',
        f'<span class="wr-eb-count">{card.member_count} items</span>',
        '</div>',
        f'<h3>{_escape(card.label)}</h3>',
        (
            '<p class="wr-eb-card-meta">'
            f'{_escape(card.cluster_id)} | {_escape(card.cluster_type)}'
            '</p>'
        ),
        '<dl class="wr-eb-facts">',
        _fact("Modules", ", ".join(card.modules) or "none"),
        _fact("Source tiers", card.source_tier_summary or "unknown"),
        _fact("Issues", issue_text),
        _fact("Claims", claim_text),
        _fact("Review events", review_text),
        _fact("Provenance URLs", provenance_text),
        '</dl>',
    ]
    if card.evidence_previews:
        parts.append('<div class="wr-eb-preview-list">')
        for item in card.evidence_previews:
            parts.append(_render_item_preview(item))
        parts.append('</div>')
    parts.append('</article>')
    return "".join(parts)


def _render_item_preview(item: EvidenceBoardItemPreview) -> str:
    url = _safe_url(item.url)
    link = (
        f'<a href="{url}" target="_blank" rel="noopener noreferrer">Source</a>'
        if url
        else ""
    )
    summary = item.summary.strip()
    if len(summary) > 220:
        summary = summary[:217].rstrip() + "..."
    return "".join(
        [
            '<div class="wr-eb-preview">',
            '<div class="wr-eb-preview-top">',
            f'<span class="wr-eb-tier wr-eb-tier--{_token_class(item.source_tier)}">'
            f'{_escape(item.source_tier or "unknown")}</span>',
            f'<span>{_escape(item.module)}</span>',
            link,
            '</div>',
            f'<strong>{_escape(item.title)}</strong>',
            f'<p>{_escape(summary)}</p>' if summary else "",
            f'<code>{_escape(item.evidence_id)}</code>',
            '</div>',
        ]
    )


def _metric(label: str, value: str) -> str:
    return (
        '<div class="wr-eb-metric">'
        f'<span>{_escape(label)}</span>'
        f'<strong>{_escape(value)}</strong>'
        '</div>'
    )


def _fact(label: str, value: str) -> str:
    return f'<div><dt>{_escape(label)}</dt><dd>{_escape(value)}</dd></div>'


def _state_text(state: str) -> str:
    return "Review required" if state == "review-required" else "Ready"


def _escape(value: Any) -> str:
    return html.escape(str(value or ""), quote=True)


def _safe_url(value: str) -> str:
    url = str(value or "").strip()
    if not (url.startswith("https://") or url.startswith("http://")):
        return ""
    return _escape(url)


def _token_class(value: str) -> str:
    text = str(value or "unknown").lower()
    return "".join(ch if ch.isalnum() else "-" for ch in text).strip("-") or "unknown"


def _evidence_board_css() -> str:
    return """
<style>
.wr-evidence-board {
  --wr-bg: #f7f8f5;
  --wr-panel: #ffffff;
  --wr-ink: #18211f;
  --wr-muted: #5d6864;
  --wr-line: #d7ddd7;
  --wr-ready: #1f7a4d;
  --wr-review: #9b4d10;
  --wr-review-bg: #fff4e7;
  --wr-ready-bg: #edf8f1;
  color: var(--wr-ink);
  background: var(--wr-bg);
  border: 1px solid var(--wr-line);
  border-radius: 8px;
  font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  margin: 16px 0;
  padding: 18px;
}
.wr-eb-header {
  align-items: start;
  display: flex;
  gap: 16px;
  justify-content: space-between;
}
.wr-eb-kicker {
  color: var(--wr-muted);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: .06em;
  margin: 0 0 4px;
  text-transform: uppercase;
}
.wr-evidence-board h2 {
  font-size: 24px;
  line-height: 1.2;
  margin: 0;
}
.wr-eb-subtitle {
  color: var(--wr-muted);
  margin: 6px 0 0;
  max-width: 780px;
}
.wr-eb-status {
  border: 1px solid currentColor;
  border-radius: 999px;
  display: inline-block;
  flex: 0 0 auto;
  font-size: 12px;
  font-weight: 700;
  line-height: 1;
  padding: 7px 10px;
}
.wr-eb-status--ready {
  background: var(--wr-ready-bg);
  color: var(--wr-ready);
}
.wr-eb-status--review-required {
  background: var(--wr-review-bg);
  color: var(--wr-review);
}
.wr-eb-metrics {
  display: grid;
  gap: 10px;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  margin: 16px 0;
}
.wr-eb-metric {
  background: var(--wr-panel);
  border: 1px solid var(--wr-line);
  border-radius: 8px;
  padding: 10px 12px;
}
.wr-eb-metric span,
.wr-eb-facts dt {
  color: var(--wr-muted);
  display: block;
  font-size: 12px;
  font-weight: 700;
  margin-bottom: 3px;
  text-transform: uppercase;
}
.wr-eb-metric strong {
  display: block;
  font-size: 15px;
  overflow-wrap: anywhere;
}
.wr-eb-next,
.wr-eb-alert {
  background: #eef4f7;
  border: 1px solid #ccdae1;
  border-radius: 8px;
  margin: 0 0 16px;
  padding: 10px 12px;
}
.wr-eb-grid {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
}
.wr-eb-card {
  background: var(--wr-panel);
  border: 1px solid var(--wr-line);
  border-left: 5px solid var(--wr-ready);
  border-radius: 8px;
  padding: 14px;
}
.wr-eb-card--review-required {
  border-left-color: var(--wr-review);
}
.wr-eb-card-head,
.wr-eb-preview-top {
  align-items: center;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: space-between;
}
.wr-eb-count,
.wr-eb-preview-top span,
.wr-eb-preview-top a {
  color: var(--wr-muted);
  font-size: 12px;
}
.wr-eb-card h3 {
  font-size: 17px;
  line-height: 1.25;
  margin: 12px 0 4px;
  overflow-wrap: anywhere;
}
.wr-eb-card-meta {
  color: var(--wr-muted);
  font-size: 12px;
  margin: 0 0 12px;
  overflow-wrap: anywhere;
}
.wr-eb-facts {
  display: grid;
  gap: 8px 12px;
  grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
  margin: 0 0 12px;
}
.wr-eb-facts dd {
  margin: 0;
  overflow-wrap: anywhere;
}
.wr-eb-preview-list,
.wr-eb-list {
  display: grid;
  gap: 8px;
}
.wr-eb-preview {
  background: #fbfcfa;
  border: 1px solid var(--wr-line);
  border-radius: 8px;
  padding: 10px;
}
.wr-eb-preview strong {
  display: block;
  margin: 8px 0 3px;
  overflow-wrap: anywhere;
}
.wr-eb-preview p {
  color: var(--wr-muted);
  margin: 0 0 7px;
}
.wr-eb-preview code {
  background: transparent;
  color: var(--wr-muted);
  font-size: 11px;
  overflow-wrap: anywhere;
  white-space: normal;
}
.wr-eb-tier {
  border-radius: 999px;
  border: 1px solid var(--wr-line);
  padding: 3px 7px;
}
.wr-eb-tier--primary,
.wr-eb-tier--official,
.wr-eb-tier--government {
  background: var(--wr-ready-bg);
  color: var(--wr-ready);
}
.wr-eb-tier--secondary,
.wr-eb-tier--professional {
  background: #eef4f7;
  color: #29586a;
}
.wr-eb-tier--unknown,
.wr-eb-tier--unvetted {
  background: var(--wr-review-bg);
  color: var(--wr-review);
}
@media (max-width: 640px) {
  .wr-evidence-board {
    padding: 14px;
  }
  .wr-eb-header {
    display: block;
  }
  .wr-eb-header > .wr-eb-status {
    margin-top: 12px;
  }
  .wr-eb-grid {
    grid-template-columns: 1fr;
  }
}
</style>
"""


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
