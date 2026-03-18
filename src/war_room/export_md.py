"""Markdown export module.

Compiles all module outputs into a structured research memo.
"""

from __future__ import annotations

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
    lines.append(f"- **Posture:** {', '.join(intake.posture)}")
    if intake.key_facts:
        lines.append(f"- **Key Facts:** {'; '.join(intake.key_facts)}")
    if intake.coverage_issues:
        lines.append(f"- **Coverage Issues:** {'; '.join(intake.coverage_issues)}")
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
            lines.append(f"- {obs[:250]}")
        lines.append("")

    _append_sources(lines, weather_payload.get("sources", []), "Weather")

    # --- 4. Carrier Document Pack ---
    lines.append("## Carrier Document Pack")
    lines.append("")
    snap = carrier_payload.get("carrier_snapshot", {})
    lines.append(
        f"**{snap.get('name', '')}** - {snap.get('event', '')} - "
        f"{snap.get('state', '')} - {snap.get('policy_type', '')}"
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
            title = document.get("title", "")[:60]
            lines.append(
                f"| {i} | {document.get('doc_type', '')} | "
                f"[{title}]({document.get('url', '')}) | "
                f"{document.get('badge', '')} | {document.get('why_it_matters', '')[:80]} |"
            )
        lines.append("")

    defenses = carrier_payload.get("common_defenses", [])
    if defenses:
        lines.append("### Common Carrier Defenses")
        lines.append("")
        for defense in defenses:
            lines.append(f"- {defense}")
        lines.append("")

    rebuttals = carrier_payload.get("rebuttal_angles", [])
    if rebuttals:
        lines.append("### Rebuttal Angles")
        lines.append("")
        for rebuttal in rebuttals:
            lines.append(f"- {rebuttal}")
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
        lines.append(f"### {issue.get('issue', '')}")
        lines.append("")
        for case in issue.get("cases", []):
            cite_str = f" - {case['citation']}" if case.get("citation") else ""
            court_str = f" ({case.get('court', '')}" if case.get("court") else ""
            year_str = f", {case['year']})" if case.get("year") else ")"
            if not court_str:
                year_str = f" ({case['year']})" if case.get("year") else ""
            lines.append(
                f"- {case.get('badge', '')} **{case.get('name', '')}**"
                f"{cite_str}{court_str}{year_str}"
            )
            if case.get("one_liner"):
                lines.append(f"  - {case['one_liner'][:200]}")
        lines.append("")
        for note in issue.get("notes", []):
            lines.append(f"  > {note}")
        lines.append("")

    checks = citecheck_payload.get("checks", [])
    if checks:
        lines.append("### Citation Spot-Check")
        lines.append("")
        lines.append(f"> {citecheck_payload.get('disclaimer', '')}")
        lines.append("> Use this as a routing signal for review, not as verification.")
        lines.append("")
        _append_claim_trace(lines, audit_snapshot.memo_claims, "citation-check-status")
        lines.append("| Badge | Case | Citation | Note |")
        lines.append("|-------|------|----------|------|")
        for check in checks:
            lines.append(
                f"| {check.get('badge', '')} | {check.get('case_name', '')[:40]} | "
                f"{check.get('citation', '')} | {check.get('note', '')[:60]} |"
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
        lines.append(f"| {query.module} | {query.category} | {query.query[:80]} |")
    lines.append("")

    # --- 7. Evidence Appendix ---
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
            f"| {i} | {src.get('badge', '')} | {src.get('module', '')} | "
            f"{src.get('title', '')[:50]} | {src.get('url', '')} |"
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

    lines.append("| Cluster | Type | Label | Modules | Evidence IDs |")
    lines.append("|---------|------|-------|---------|--------------|")
    for cluster in evidence_clusters:
        lines.append(
            f"| {cluster.cluster_id} | {cluster.cluster_type} | {cluster.label[:50]} | "
            f"{', '.join(cluster.modules)} | {', '.join(cluster.evidence_ids)} |"
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
            f"{title[:50]} | {item.badge} | {url} |"
        )
    lines.append("")


def _append_review_log(lines: list[str], review_events: list[Any]) -> None:
    """Append review-required audit events when present."""
    for event in review_events:
        cluster_ids = ", ".join(event.related_cluster_ids) if event.related_cluster_ids else "none"
        lines.append(
            f"- **{event.label}:** {event.detail} "
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
            f"- {src.get('badge', '')} [{src.get('title', '')[:60]}]({src.get('url', '')})"
            f" - {src.get('reason', '')}"
        )
    lines.append("")


def _append_warnings(lines: list[str], warnings: list[str] | None, heading: str) -> None:
    """Append a compact warning block when a module emitted warnings."""
    if not warnings:
        return
    lines.append(f"### {heading}")
    lines.append("")
    for warning in warnings:
        lines.append(f"- {warning}")
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
    lines.append("")


def _trust_snapshot_lines(
    *,
    weather_payload: dict[str, Any],
    carrier_payload: dict[str, Any],
    caselaw_payload: dict[str, Any],
    citecheck_payload: dict[str, Any],
) -> list[str]:
    """Build the top-of-memo trust snapshot."""
    total_cases = sum(len(issue.get("cases", [])) for issue in caselaw_payload.get("issues", []))
    citation_summary = citecheck_payload.get("summary", {})
    return [
        f"Weather sources: {len(weather_payload.get('sources', []))}",
        f"Carrier documents: {len(carrier_payload.get('document_pack', []))}",
        f"Case authorities: {total_cases}",
        (
            "Citation spot-checks: "
            f"{citation_summary.get('verified', 0)} verified / "
            f"{citation_summary.get('uncertain', 0)} uncertain / "
            f"{citation_summary.get('not_found', 0)} not found"
        ),
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
