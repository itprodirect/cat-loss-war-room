"""Markdown export module.

Compiles all module outputs into a structured research memo.
"""

from __future__ import annotations

import html
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

from war_room.models import (
    CaseIntake,
    CaseLawPack,
    CarrierDocPack,
    CitationVerifyPack,
    QuerySpec,
    WeatherBrief,
    carrier_doc_pack_to_payload,
    caselaw_pack_to_payload,
    citation_verify_pack_to_payload,
    memo_render_input_from_parts,
    run_audit_snapshot_from_memo_input,
    weather_brief_to_payload,
)


def render_markdown_memo(
    intake: Mapping[str, Any] | CaseIntake,
    weather: Mapping[str, Any] | WeatherBrief,
    carrier: Mapping[str, Any] | CarrierDocPack,
    caselaw: Mapping[str, Any] | CaseLawPack,
    citecheck: Mapping[str, Any] | CitationVerifyPack,
    query_plan: list[Mapping[str, Any] | QuerySpec],
) -> str:
    """Render the full research memo as markdown."""
    memo_input = memo_render_input_from_parts(
        intake,
        weather,
        carrier,
        caselaw,
        citecheck,
        query_plan,
    )

    intake = memo_input.intake
    weather_payload = weather_brief_to_payload(memo_input.weather)
    carrier_payload = carrier_doc_pack_to_payload(memo_input.carrier)
    caselaw_payload = caselaw_pack_to_payload(memo_input.caselaw)
    citecheck_payload = citation_verify_pack_to_payload(memo_input.citecheck)
    query_plan = memo_input.query_plan
    audit_snapshot = run_audit_snapshot_from_memo_input(memo_input)

    lines: list[str] = []

    # --- 1. Title + Disclaimer ---
    lines.append("# CAT-Loss War Room - Research Memo")
    lines.append("")
    lines.append("> **DRAFT - ATTORNEY WORK PRODUCT**")
    lines.append(">")
    lines.append("> **DEMO RESEARCH MEMO - VERIFY CITATIONS - NOT LEGAL ADVICE**")
    lines.append(">")
    lines.append(f"> Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("")
    lines.append("---")
    lines.append("")

    review_flags = _build_review_flags(
        weather_payload=weather_payload,
        carrier_payload=carrier_payload,
        caselaw_payload=caselaw_payload,
        citecheck_payload=citecheck_payload,
    )

    lines.append("## Trust Snapshot")
    lines.append("")
    for item in _trust_snapshot_lines(
        weather_payload=weather_payload,
        carrier_payload=carrier_payload,
        caselaw_payload=caselaw_payload,
        citecheck_payload=citecheck_payload,
        audit_snapshot=audit_snapshot,
    ):
        lines.append(f"- {item}")
    lines.append("")

    if review_flags:
        lines.append("### Review Required")
        lines.append("")
        for flag in review_flags:
            lines.append(f"- {flag}")
        lines.append("")

    lines.append("---")
    lines.append("")

    # --- 2. Case Intake ---
    lines.append("## Case Intake")
    lines.append("")
    lines.append(f"- **Event:** {intake.event_name} ({intake.event_date})")
    lines.append(f"- **Location:** {intake.county} County, {intake.state}")
    lines.append(f"- **Carrier:** {intake.carrier}")
    lines.append(f"- **Policy:** {intake.policy_type}")
    lines.append(f"- **Posture:** {', '.join(_humanize_token(item) for item in intake.posture)}")
    if intake.key_facts:
        lines.append(
            "- **Key Facts:** "
            + "; ".join(_clean_inline_text(item, limit=180) for item in intake.key_facts)
        )
    if intake.coverage_issues:
        lines.append(
            "- **Coverage Issues:** "
            + "; ".join(_clean_inline_text(item, limit=120) for item in intake.coverage_issues)
        )
    lines.append("")
    lines.append("---")
    lines.append("")

    # --- 3. Weather Corroboration ---
    lines.append("## Weather Corroboration")
    lines.append("")
    lines.append(f"**{weather_payload.get('event_summary', '')}**")
    lines.append("")
    _append_claim_trace(lines, audit_snapshot.memo_claims, "weather-corroboration")
    _append_warnings(lines, weather_payload.get("warnings", []), "Weather review flags")
    metrics = weather_payload.get("metrics", {})
    if any(value is not None for value in metrics.values()):
        lines.append("### Metrics Extracted")
        lines.append("")
        if metrics.get("max_wind_mph") is not None:
            lines.append(f"- Max Wind: **{metrics['max_wind_mph']} mph**")
        if metrics.get("storm_surge_ft") is not None:
            lines.append(f"- Storm Surge: **{metrics['storm_surge_ft']} ft**")
        if metrics.get("rain_in") is not None:
            lines.append(f"- Rainfall: **{metrics['rain_in']} in**")
        lines.append("")

    observations = weather_payload.get("key_observations", [])
    if observations:
        lines.append("### Key Observations")
        lines.append("")
        for obs in observations[:6]:
            lines.append(f"- {_clean_inline_text(obs, limit=250)}")
        lines.append("")

    _append_sources(lines, weather_payload.get("sources", []), "Weather")

    # --- 4. Carrier Document Pack ---
    lines.append("## Carrier Document Pack")
    lines.append("")
    snap = carrier_payload.get("carrier_snapshot", {})
    lines.append(
        f"**{_clean_inline_text(snap.get('name', ''), limit=80)}** - "
        f"{_clean_inline_text(snap.get('event', ''), limit=80)} - "
        f"{_clean_inline_text(snap.get('state', ''), limit=10)} - "
        f"{_clean_inline_text(snap.get('policy_type', ''), limit=40)}"
    )
    lines.append("")
    _append_claim_trace(lines, audit_snapshot.memo_claims, "carrier-positioning")
    _append_warnings(lines, carrier_payload.get("warnings", []), "Carrier review flags")

    docs = carrier_payload.get("document_pack", [])
    if docs:
        lines.append("### Highest-Value Documents")
        lines.append("")
        lines.append("| # | Type | Title | Badge | Why It Matters |")
        lines.append("|---|------|-------|-------|----------------|")
        for i, document in enumerate(docs[:8], 1):
            title = _clean_inline_text(document.get("title", ""), limit=60, table_safe=True)
            why_it_matters = _clean_inline_text(
                document.get("why_it_matters", ""),
                limit=80,
                table_safe=True,
            )
            lines.append(
                f"| {i} | {_clean_inline_text(document.get('doc_type', ''), limit=32, table_safe=True)} | "
                f"[{title}]({document.get('url', '')}) | "
                f"{document.get('badge', '')} | {why_it_matters} |"
            )
        lines.append("")

    defenses = carrier_payload.get("common_defenses", [])
    if defenses:
        lines.append("### Common Carrier Defenses")
        lines.append("")
        for defense in defenses:
            lines.append(f"- {_clean_inline_text(defense, limit=180)}")
        lines.append("")

    rebuttals = carrier_payload.get("rebuttal_angles", [])
    if rebuttals:
        lines.append("### Rebuttal Angles")
        lines.append("")
        for rebuttal in rebuttals:
            lines.append(f"- {_clean_inline_text(rebuttal, limit=180)}")
        lines.append("")

    _append_sources(lines, carrier_payload.get("sources", []), "Carrier")

    # --- 5. Case Law Pack + Citation Check ---
    lines.append("## Case Law")
    lines.append("")
    _append_claim_trace(lines, audit_snapshot.memo_claims, "case-law-support")
    _append_warnings(lines, caselaw_payload.get("warnings", []), "Case-law review flags")
    _append_citation_summary(lines, citecheck_payload)

    issues = caselaw_payload.get("issues", [])
    for issue in issues:
        lines.append(f"### {_clean_inline_text(issue.get('issue', ''), limit=120)}")
        lines.append("")
        for case in issue.get("cases", []):
            citation = _clean_inline_text(case.get("citation", ""), limit=80)
            court = _clean_inline_text(case.get("court", ""), limit=80)
            year = _clean_inline_text(case.get("year", ""), limit=16)
            cite_str = f" - {citation}" if citation else ""
            court_str = f" ({court}" if court else ""
            year_str = f", {year})" if year else ")"
            if not court_str:
                year_str = f" ({year})" if year else ""
            lines.append(
                f"- {case.get('badge', '')} **{_clean_inline_text(case.get('name', ''), limit=120)}**"
                f"{cite_str}{court_str}{year_str}"
            )
            if case.get("one_liner"):
                lines.append(f"  - {_clean_inline_text(case['one_liner'], limit=200)}")
        lines.append("")
        for note in issue.get("notes", []):
            lines.append(f"  > {_clean_inline_text(note, limit=200)}")
        lines.append("")

    checks = citecheck_payload.get("checks", [])
    if checks:
        lines.append("### Citation Spot-Check")
        lines.append("")
        lines.append(f"> {citecheck_payload.get('disclaimer', '')}")
        lines.append("> Use this as a routing signal for review, not as verification.")
        lines.append("")
        _append_claim_trace(lines, audit_snapshot.memo_claims, "citation-check-status")
        lines.append("| Badge | Case | Citation | Confidence | Source Type | Note |")
        lines.append("|-------|------|----------|------------|-------------|------|")
        for check in checks:
            source_type = _clean_inline_text(
                (check.get("source_class") or "unknown").replace("_", " "),
                limit=32,
                table_safe=True,
            )
            note = _clean_inline_text(check.get("note", ""), limit=60, table_safe=True)
            if check.get("alternate_candidate_count"):
                note = f"{note} ({check['alternate_candidate_count']} alternates)"
            lines.append(
                f"| {check.get('badge', '')} | {_clean_inline_text(check.get('case_name', ''), limit=40, table_safe=True)} | "
                f"{_clean_inline_text(check.get('citation', ''), limit=40, table_safe=True)} | "
                f"{_clean_inline_text(check.get('confidence', ''), limit=12, table_safe=True)} | "
                f"{source_type} | {note} |"
            )
        lines.append("")

    _append_sources(lines, caselaw_payload.get("sources", []), "Case Law")

    # --- 6. Query Plan Appendix ---
    lines.append("## Appendix: Query Plan")
    lines.append("")
    lines.append(f"Total queries: {len(query_plan)}")
    lines.append("")
    lines.append("| Module | Category | Query |")
    lines.append("|--------|----------|-------|")
    for query in query_plan:
        lines.append(
            f"| {_clean_inline_text(query.module, limit=24, table_safe=True)} | "
            f"{_clean_inline_text(query.category, limit=24, table_safe=True)} | "
            f"{_clean_inline_text(query.query, limit=80, table_safe=True)} |"
        )
    lines.append("")

    # --- 7. Evidence Appendix ---
    lines.append("## Appendix: Quality Snapshot")
    lines.append("")
    _append_quality_snapshot(lines, audit_snapshot.quality_snapshot)

    lines.append("## Appendix: Evidence Clusters")
    lines.append("")
    _append_evidence_clusters(lines, audit_snapshot.evidence_clusters)

    lines.append("## Appendix: Evidence Index")
    lines.append("")
    _append_evidence_index(lines, audit_snapshot.evidence_items)

    if audit_snapshot.review_events:
        lines.append("## Appendix: Review Log")
        lines.append("")
        _append_review_log(lines, audit_snapshot.review_events)

    # --- 8. Source Appendix (deduplicated) ---
    lines.append("## Appendix: All Sources")
    lines.append("")
    all_sources: list[dict[str, Any]] = []
    seen_urls: set[str] = set()
    for module_data in [weather_payload, carrier_payload, caselaw_payload]:
        for src in module_data.get("sources", []):
            if src["url"] not in seen_urls:
                seen_urls.add(src["url"])
                all_sources.append({**src, "module": module_data.get("module", "")})

    lines.append("| # | Badge | Module | Title | URL |")
    lines.append("|---|-------|--------|-------|-----|")
    for i, src in enumerate(all_sources, 1):
        lines.append(
            f"| {i} | {src.get('badge', '')} | {_clean_inline_text(src.get('module', ''), limit=20, table_safe=True)} | "
            f"{_clean_inline_text(src.get('title', ''), limit=50, table_safe=True)} | {src.get('url', '')} |"
        )
    lines.append("")

    # --- Methodology ---
    lines.append("---")
    lines.append("")
    lines.append("## Methodology & Limitations")
    lines.append("")
    lines.append("- Sources gathered via Exa search API")
    lines.append("- Source credibility scored by domain classification (not ML)")
    lines.append("- Citation spot-checks are confidence signals, not legal verification")
    lines.append("- Paywalled sources (Westlaw, LexisNexis) excluded from primary results")
    lines.append("- Weather metrics extracted via regex - verify against official records")
    lines.append("- This memo is generated research, not attorney analysis")
    lines.append("")
    lines.append("**DRAFT - ATTORNEY WORK PRODUCT - VERIFY ALL CITATIONS**")

    return "\n".join(lines)


def write_markdown(output_dir: str | Path, case_key: str, md: str) -> Path:
    """Write the markdown memo to a file. Returns the file path."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{case_key}_{ts}.md"
    path = out / filename
    path.write_text(md, encoding="utf-8")
    return path


def _append_claim_trace(lines: list[str], memo_claims: list[Any], claim_id: str) -> None:
    """Append stable claim-level trace metadata when available."""
    claim = next((item for item in memo_claims if item.claim_id == claim_id), None)
    if claim is None:
        return

    cluster_ids = ", ".join(claim.cluster_ids) if claim.cluster_ids else "none"
    lines.append(f"> Claim status: {claim.status} | Evidence clusters: {cluster_ids}")
    lines.append("")


def _append_evidence_clusters(lines: list[str], evidence_clusters: list[Any]) -> None:
    """Append normalized evidence clusters from the audit snapshot."""
    if not evidence_clusters:
        lines.append("No evidence clusters captured.")
        lines.append("")
        return

    lines.append("| Cluster | Type | Label | Members | Provenance URLs | Modules | Evidence IDs |")
    lines.append("|---------|------|-------|---------|-----------------|---------|--------------|")
    for cluster in evidence_clusters:
        lines.append(
            f"| {cluster.cluster_id} | {cluster.cluster_type} | {_clean_inline_text(cluster.label, limit=50, table_safe=True)} | "
            f"{cluster.member_count} | {len(cluster.provenance_urls)} | "
            f"{_clean_inline_text(', '.join(cluster.modules), limit=40, table_safe=True)} | "
            f"{_clean_inline_text(', '.join(cluster.evidence_ids), limit=120, table_safe=True)} |"
        )
    lines.append("")


def _append_quality_snapshot(lines: list[str], quality_snapshot: Any) -> None:
    """Append lightweight structured quality telemetry for the memo run."""
    if quality_snapshot is None:
        lines.append("No quality snapshot captured.")
        lines.append("")
        return

    source_class_counts = getattr(quality_snapshot, "source_class_counts", {}) or {}
    citation_status_counts = getattr(quality_snapshot, "citation_status_counts", {}) or {}
    citation_reason_counts = getattr(quality_snapshot, "citation_reason_counts", {}) or {}

    lines.append(f"- Sources by class: {_format_count_map(source_class_counts) or 'none'}")
    lines.append(
        f"- Primary vs secondary: {quality_snapshot.primary_source_count} primary / "
        f"{quality_snapshot.secondary_source_count} secondary"
    )
    lines.append(f"- Citation buckets: {_format_count_map(citation_status_counts) or 'none'}")
    if citation_reason_counts:
        lines.append(f"- Citation reasons: {_format_count_map(citation_reason_counts)}")
    lines.append(
        f"- Evidence normalization: {quality_snapshot.evidence_item_count} items -> "
        f"{quality_snapshot.evidence_cluster_count} clusters "
        f"({quality_snapshot.grouped_evidence_count} grouped)"
    )
    lines.append(
        f"- Canonical authorities: {quality_snapshot.normalized_authority_count} "
        f"({quality_snapshot.duplicate_authority_count} duplicates collapsed, "
        f"{quality_snapshot.provenance_link_count} provenance links)"
    )
    lines.append("")


def _append_evidence_index(lines: list[str], evidence_items: list[Any]) -> None:
    """Append the canonical evidence index derived from the audit snapshot."""
    if not evidence_items:
        lines.append("No evidence items captured.")
        lines.append("")
        return

    lines.append("| ID | Module | Type | Title | Badge | URL |")
    lines.append("|----|--------|------|-------|-------|-----|")
    for item in evidence_items:
        title = item.title or item.summary or item.evidence_type
        url = item.url or ""
        lines.append(
            f"| {item.evidence_id} | {item.module} | {item.evidence_type} | "
            f"{_clean_inline_text(title, limit=50, table_safe=True)} | {item.badge} | {url} |"
        )
    lines.append("")


def _append_review_log(lines: list[str], review_events: list[Any]) -> None:
    """Append review-required audit events when present."""
    for event in review_events:
        cluster_ids = ", ".join(event.related_cluster_ids) if event.related_cluster_ids else "none"
        lines.append(
            f"- **{_clean_inline_text(event.label, limit=80)}:** {_clean_inline_text(event.detail, limit=180)} "
            f"| Evidence clusters: {cluster_ids}"
        )
    lines.append("")


def _append_sources(lines: list[str], sources: list[dict[str, Any]], label: str) -> None:
    """Append a sources sub-section."""
    if not sources:
        return
    lines.append(f"#### {label} Sources")
    lines.append("")
    for src in sources[:8]:
        lines.append(
            f"- {src.get('badge', '')} "
            f"[{_clean_inline_text(src.get('title', ''), limit=60)}]({src.get('url', '')})"
            f" - {_clean_inline_text(src.get('reason', ''), limit=120)}"
        )
    lines.append("")


def _append_warnings(lines: list[str], warnings: list[str] | None, heading: str) -> None:
    """Append a compact warning block when a module emitted warnings."""
    if not warnings:
        return
    lines.append(f"### {heading}")
    lines.append("")
    for warning in warnings:
        lines.append(f"- {_clean_inline_text(warning, limit=180)}")
    lines.append("")


def _append_citation_summary(lines: list[str], citecheck_payload: dict[str, Any]) -> None:
    """Append a compact citation confidence summary ahead of case detail."""
    summary = citecheck_payload.get("summary", {})
    total = summary.get("total", 0)
    if total == 0:
        return

    lines.append("### Citation Confidence")
    lines.append("")
    lines.append(f"- Verified: {summary.get('verified', 0)}")
    lines.append(f"- Uncertain: {summary.get('uncertain', 0)}")
    lines.append(f"- Not Found: {summary.get('not_found', 0)}")
    reason_counts = {}
    for check in citecheck_payload.get("checks", []):
        reason = (check.get("status_reason") or "").strip()
        if reason:
            reason_counts[reason] = reason_counts.get(reason, 0) + 1
    if reason_counts:
        lines.append(f"- Reasons: {_format_count_map(reason_counts)}")
    alternate_candidates = sum(
        int(check.get("alternate_candidate_count", 0))
        for check in citecheck_payload.get("checks", [])
    )
    if alternate_candidates:
        lines.append(f"- Alternate aligned candidates: {alternate_candidates}")
    lines.append("")


def _trust_snapshot_lines(
    *,
    weather_payload: dict[str, Any],
    carrier_payload: dict[str, Any],
    caselaw_payload: dict[str, Any],
    citecheck_payload: dict[str, Any],
    audit_snapshot: Any,
) -> list[str]:
    """Build the top-of-memo trust snapshot."""
    total_cases = sum(len(issue.get("cases", [])) for issue in caselaw_payload.get("issues", []))
    citation_summary = citecheck_payload.get("summary", {})
    quality_snapshot = getattr(audit_snapshot, "quality_snapshot", None)
    source_class_line = "Sources by class: unavailable"
    evidence_line = "Evidence normalization: unavailable"
    primary_secondary_line = "Primary vs secondary: unavailable"
    if quality_snapshot is not None:
        source_class_line = (
            "Sources by class: "
            f"{_format_count_map(getattr(quality_snapshot, 'source_class_counts', {}) or {}) or 'none'}"
        )
        primary_secondary_line = (
            "Primary vs secondary: "
            f"{quality_snapshot.primary_source_count} primary / "
            f"{quality_snapshot.secondary_source_count} secondary"
        )
        evidence_line = (
            "Evidence normalization: "
            f"{quality_snapshot.evidence_item_count} items / "
            f"{quality_snapshot.evidence_cluster_count} clusters / "
            f"{quality_snapshot.grouped_evidence_count} grouped"
        )
        authority_line = (
            "Canonical authorities: "
            f"{quality_snapshot.normalized_authority_count} / "
            f"duplicates collapsed {quality_snapshot.duplicate_authority_count}"
        )
    else:
        authority_line = "Canonical authorities: unavailable"
    return [
        f"Weather sources: {len(weather_payload.get('sources', []))}",
        f"Carrier documents: {len(carrier_payload.get('document_pack', []))}",
        f"Case authorities: {total_cases}",
        source_class_line,
        primary_secondary_line,
        authority_line,
        (
            "Citation spot-checks: "
            f"{citation_summary.get('verified', 0)} verified / "
            f"{citation_summary.get('uncertain', 0)} uncertain / "
            f"{citation_summary.get('not_found', 0)} not found"
        ),
        evidence_line,
    ]


def _build_review_flags(
    *,
    weather_payload: dict[str, Any],
    carrier_payload: dict[str, Any],
    caselaw_payload: dict[str, Any],
    citecheck_payload: dict[str, Any],
) -> list[str]:
    """Collect top-level review flags from module warnings and citation status."""
    flags: list[str] = []
    for module_label, payload in (
        ("Weather", weather_payload),
        ("Carrier", carrier_payload),
        ("Case law", caselaw_payload),
    ):
        for warning in payload.get("warnings", []) or []:
            flags.append(f"{module_label}: {warning}")

    summary = citecheck_payload.get("summary", {})
    uncertain = summary.get("uncertain", 0)
    not_found = summary.get("not_found", 0)
    if uncertain or not_found:
        flags.append(
            "Citation review: "
            f"{uncertain} uncertain and {not_found} not found entries require manual verification."
        )

    return flags


def _format_count_map(values: dict[str, int]) -> str:
    parts = []
    for key, value in values.items():
        if value:
            parts.append(f"{key.replace('_', ' ')} {value}")
    return " / ".join(parts)


def _clean_inline_text(
    value: Any,
    *,
    limit: int | None = None,
    table_safe: bool = False,
) -> str:
    text = html.unescape(str(value or ""))
    text = text.replace("\r", " ").replace("\n", " ")
    text = re.sub(r"\[([^\]]+)\]", r"\1", text)
    text = re.sub(r"\s+", " ", text).strip()
    if table_safe:
        text = text.replace("|", "/")
    if limit is not None and len(text) > limit:
        return text[: max(0, limit - 3)].rstrip() + "..."
    return text


def _humanize_token(value: str) -> str:
    return _clean_inline_text(value.replace("_", " "), limit=40)
