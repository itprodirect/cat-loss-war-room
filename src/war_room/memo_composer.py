"""Memo-composer read model helpers derived from the audit snapshot."""

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
class MemoComposerClaimLink:
    """Claim-level support row for a memo section."""

    claim_id: str
    text: str
    status: str
    cluster_ids: list[str] = field(default_factory=list)
    evidence_ids: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class MemoComposerSectionCard:
    """Section-first memo-composer card."""

    section_id: str
    title: str
    status: str
    claim_links: list[MemoComposerClaimLink] = field(default_factory=list)
    review_event_ids: list[str] = field(default_factory=list)
    review_required: bool = False


@dataclass(frozen=True)
class MemoComposerReadModel:
    """Memo-composer read model for notebook-era flows."""

    run_id: str
    export_eligibility: str
    review_required_section_count: int
    section_cards: list[MemoComposerSectionCard] = field(default_factory=list)


def build_memo_composer(
    snapshot: Mapping[str, Any] | RunAuditSnapshot,
) -> MemoComposerReadModel:
    """Build a section-first memo-composer read model from the audit snapshot."""

    typed_snapshot = adapt_run_audit_snapshot(snapshot)
    claims_by_section: dict[str, list[Any]] = {}
    claim_to_section: dict[str, str] = {}
    for claim in typed_snapshot.memo_claims:
        claims_by_section.setdefault(claim.section, []).append(claim)
        claim_to_section[claim.claim_id] = claim.section

    review_events_by_section: dict[str, list[Any]] = {}
    for event in typed_snapshot.review_events:
        target_sections = _unique_strings(
            claim_to_section[claim_id]
            for claim_id in event.related_claim_ids
            if claim_id in claim_to_section
        )
        for section in target_sections:
            review_events_by_section.setdefault(section, []).append(event)

    cards: list[MemoComposerSectionCard] = []
    for section_id, title in zip(
        typed_snapshot.export_artifact.section_ids,
        typed_snapshot.export_artifact.section_titles,
        strict=False,
    ):
        claims = claims_by_section.get(title, [])
        review_events = review_events_by_section.get(title, [])
        review_required = bool(review_events) or any(
            claim.status == "review_required" for claim in claims
        )
        status = _section_status(title, claims, review_required)
        cards.append(
            MemoComposerSectionCard(
                section_id=section_id,
                title=title,
                status=status,
                claim_links=[
                    MemoComposerClaimLink(
                        claim_id=claim.claim_id,
                        text=claim.text,
                        status=claim.status,
                        cluster_ids=list(claim.cluster_ids),
                        evidence_ids=list(claim.evidence_ids),
                    )
                    for claim in claims
                ],
                review_event_ids=_unique_strings(event.event_id for event in review_events),
                review_required=review_required,
            )
        )

    return MemoComposerReadModel(
        run_id=typed_snapshot.export_artifact.run_id,
        export_eligibility=(
            "review_required_export"
            if typed_snapshot.export_artifact.review_required
            else "ready_to_export"
        ),
        review_required_section_count=sum(1 for card in cards if card.review_required),
        section_cards=cards,
    )


def build_memo_composer_from_parts(
    intake: Mapping[str, Any] | CaseIntake,
    weather: Mapping[str, Any] | WeatherBrief,
    carrier: Mapping[str, Any] | CarrierDocPack,
    caselaw: Mapping[str, Any] | CaseLawPack,
    citecheck: Mapping[str, Any] | CitationVerifyPack,
    query_plan: list[Mapping[str, Any] | QuerySpec],
) -> MemoComposerReadModel:
    """Build the read model directly from current notebook-era module outputs."""

    return build_memo_composer(
        run_audit_snapshot_from_parts(
            intake,
            weather,
            carrier,
            caselaw,
            citecheck,
            query_plan,
        )
    )


def format_memo_composer(composer: MemoComposerReadModel) -> str:
    """Render the memo-composer read model as a notebook-friendly text block."""

    lines = [
        "=" * 60,
        "MEMO COMPOSER",
        "=" * 60,
        f"  Run ID:            {composer.run_id}",
        f"  Sections:          {len(composer.section_cards)}",
        f"  Review Required:   {composer.review_required_section_count} sections",
        f"  Export Eligibility:{' ' * 1}{composer.export_eligibility}",
        (
            "  Next Step:         "
            + (
                "Export is allowed, but the memo must stay marked review-required."
                if composer.export_eligibility == "review_required_export"
                else "Memo sections are ready for export."
            )
        ),
        "",
    ]

    for card in composer.section_cards:
        lines.append(f"  [{card.status}] {card.title}")
        if card.claim_links:
            lines.append("    Claims:")
            for claim in card.claim_links[:4]:
                cluster_ids = ", ".join(claim.cluster_ids) if claim.cluster_ids else "none"
                lines.append(
                    f"      - {claim.claim_id} | {claim.status} | clusters: {cluster_ids}"
                )
        else:
            lines.append("    Claims: none")
        if card.review_event_ids:
            lines.append(f"    Review events: {', '.join(card.review_event_ids)}")
        lines.append("")

    lines.append("=" * 60)
    return "\n".join(lines)


def _section_status(title: str, claims: list[Any], review_required: bool) -> str:
    if review_required:
        return "review_required"
    if claims:
        return "ready"
    if title == "Appendix: Review Log":
        return "review_required"
    return "ready"


def _unique_strings(values: Any) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result
