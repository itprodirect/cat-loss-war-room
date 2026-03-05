"""Markdown export module.

Compiles all module outputs into a structured research memo.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from war_room.models import (
    carrier_doc_pack_to_payload,
    caselaw_pack_to_payload,
    citation_verify_pack_to_payload,
    memo_render_input_from_parts,
    weather_brief_to_payload,
)
from war_room.query_plan import CaseIntake, QuerySpec


def render_markdown_memo(
    intake: CaseIntake,
    weather: dict[str, Any],
    carrier: dict[str, Any],
    caselaw: dict[str, Any],
    citecheck: dict[str, Any],
    query_plan: list[QuerySpec],
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

    docs = carrier_payload.get("document_pack", [])
    if docs:
        lines.append("### Documents")
        lines.append("")
        lines.append("| # | Type | Title | Badge | Why It Matters |")
        lines.append("|---|------|-------|-------|----------------|")
        for i, document in enumerate(docs[:10], 1):
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
        lines.append("")
        lines.append("| Badge | Case | Citation | Note |")
        lines.append("|-------|------|----------|------|")
        for check in checks:
            lines.append(
                f"| {check.get('badge', '')} | {check.get('case_name', '')[:40]} | "
                f"{check.get('citation', '')} | {check.get('note', '')[:60]} |"
            )
        lines.append("")
        summary = citecheck_payload.get("summary", {})
        lines.append(
            f"**Summary:** {summary.get('verified', 0)} verified, "
            f"{summary.get('uncertain', 0)} uncertain, "
            f"{summary.get('not_found', 0)} not found"
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

    # --- 7. Source Appendix (deduplicated) ---
    lines.append("## Appendix: All Sources")
    lines.append("")
    all_sources: list[dict] = []
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


def _append_sources(lines: list[str], sources: list[dict], label: str) -> None:
    """Append a sources sub-section."""
    if not sources:
        return
    lines.append(f"#### {label} Sources")
    lines.append("")
    for src in sources[:8]:
        lines.append(
            f"- {src.get('badge', '')} [{src.get('title', '')[:60]}]({src.get('url', '')})"
        )
    lines.append("")
