# CAT-Loss War Room - Decision Log

Track key architecture and design decisions so future sessions (human or AI) understand *why*.

---

## D001: CLAUDE.md instead of AGENTS.md
**Date:** 2026-02-24
**Decision:** Use CLAUDE.md as the project conventions file, not AGENTS.md.
**Reason:** Claude Code automatically reads CLAUDE.md on session start. AGENTS.md is a ChatGPT/Codex convention that Claude Code ignores. Using CLAUDE.md means every Claude Code session inherits project rules automatically.
**Impact:** If using Codex for some prompts, you may want to also create an AGENTS.md that mirrors CLAUDE.md, or symlink them.

## D002: Posture as list[str], not nested dict
**Date:** 2026-02-24
**Decision:** `posture: list[str]` (e.g., `["denial", "bad_faith"]`) instead of `posture: dict[str, bool]`.
**Reason:** Simpler to iterate (`if "bad_faith" in case.posture`), fewer bugs, easier for AI agents to work with. The nested dict added no value - you never need `posture["bad_faith"] = False`.

## D003: Markdown export only in MVP (no PDF)
**Date:** 2026-02-24
**Decision:** Cell 6 exports markdown. No PDF generation in Phase 1-2.
**Reason:** PDF generation (weasyprint, wkhtmltopdf, fpdf2) adds dependency complexity and 3+ hours of debugging. Markdown is readable, editable, and converts to PDF in any tool. Ship markdown first, add PDF in Phase 3+.

## D004: Cache-first architecture with committed samples
**Date:** 2026-02-24
**Decision:** Two cache layers: `cache_samples/` (committed, demo fixtures) and `cache/` (gitignored, runtime).
**Reason:** The notebook must run without an API key on first clone. Committed sample data guarantees a working demo. Runtime cache avoids re-hitting the API during development. The USE_CACHE toggle lets you switch between cached and live mode.

## D005: Citation spot-check, not full verification
**Date:** 2026-02-24
**Decision:** Run one Exa search per citation to check if it exists on a court/legal site. Report `verified` / `warning` / `not_found`. Do not claim "verified" as a legal conclusion.
**Reason:** Full citation verification requires Westlaw/Lexis (paywalled). A spot-check gives attorneys confidence the citation is real without overclaiming. The mandatory disclaimer ("KeyCite before reliance") handles the gap.
**Cost:** ~$0.01 per citation, ~$0.10 per case run. Worth it for trust.

## D006: 7 cells, not 10
**Date:** 2026-02-24
**Decision:** MVP is 7 cells (setup, intake, query plan, weather, carrier, caselaw, export). Expert finder, depo questions, demand outline, and policy checklist are Phase 2+.
**Reason:** The 4 cells that actually impress attorneys are weather, carrier, caselaw, and export. The others are useful but do not create "wow" moments. Tight scope = faster ship = earlier feedback.

## D007: Firm Memory is a JSON file, not a database
**Date:** 2026-02-24
**Decision:** Firm memory is a single JSON file (firm_memory.json) with load/save functions.
**Reason:** No database, no server, no auth. About 30 lines of code. Creates the "platform" narrative in the demo ("it learns over time") without scope creep. Can migrate to SQLite or a real DB later if needed.

## D008: Source scoring via domain classification, not ML
**Date:** 2026-02-24
**Decision:** Hardcoded domain dicts (`GOV_COURT -> green`, `LEGAL_COMMENTARY -> yellow`, everything else -> red).
**Reason:** Deterministic, debuggable, explainable to attorneys. An ML classifier would be overkill for a demo and adds a "why did it rate this yellow?" trust problem. The hardcoded dict can be extended in 30 seconds.

## D009: Three demo fact patterns, one primary
**Date:** 2026-02-24
**Decision:** Primary: Hurricane Milton / Citizens / Pinellas FL. Backup: TX Hail / Allstate / Tarrant. Stretch: Hurricane Ida / Lloyd's / Orleans Parish LA.
**Reason:** Milton is Merlin's backyard - every attorney there has active Milton files. Citizens is their #1 opponent. The backup patterns prove jurisdiction flexibility. Cache all three, demo with Milton.

## D010: exa_py in requirements from day 1
**Date:** 2026-02-24
**Decision:** Include `exa_py` in requirements.txt even though Prompt #1 does not make API calls.
**Reason:** Stub modules import Exa types for type hints. Having it installed prevents import errors during development. Costs nothing, prevents a "why is this broken" moment between Prompt #1 and Prompt #2.

## D011: V2 workflow optimized for non-technical operator
**Date:** 2026-03-08
**Decision:** Treat the paralegal or other non-technical legal operator as the primary V2 workflow driver. Partners and associates are first-class reviewers, but not the default interaction model.
**Reason:** The core product gap is not raw research capability; it is self-serve usability without Python, Jupyter, or narrated setup. Optimizing for the first non-technical operator forces guided intake, visible trust states, and clearer handoffs.

## D012: Evidence-first V2 review model
**Date:** 2026-03-08
**Decision:** Make evidence review and issue analysis the primary V2 product surfaces. The memo remains a downstream artifact rather than the main object of the system.
**Reason:** Trust depends on showing support before prose. A memo-first workflow makes it too easy to hide uncertainty, flatten provenance, and overstate incomplete analysis.

## D013: Canonical V2 workflow and state vocabulary
**Date:** 2026-03-08
**Decision:** Standardize the V2 workflow as `Intake -> Research Plan Preview -> Run Timeline -> Evidence Board -> Issue Workspace -> Memo Composer -> Export/Audit Bundle`, with canonical run states `queued`, `running`, `partial_success`, `failed`, `completed`, and `cancelled`.
**Reason:** `#10`, `#11`, and later provenance/review work need one stable workflow contract and one state vocabulary. Locking the sequence now reduces downstream drift across API, UI, and schema work.

## D014: Run-scoped canonical graph
**Date:** 2026-03-08
**Decision:** Treat `Run` as the top-level canonical persistence boundary for V2, with intake, planning, evidence, issue, claim, review, and export records all attached to the run.
**Reason:** The product needs one stable graph for progress, review, export history, and partial-success handling. Making the memo or export the primary object would flatten provenance and make review state harder to preserve.

## D015: Evidence clusters are canonical, not presentational only
**Date:** 2026-03-08
**Decision:** Keep `EvidenceCluster` as a first-class canonical entity that links evidence, issues, claims, review events, and exports.
**Reason:** Grouped support is necessary for trustworthy issue review and export traceability. Flat evidence rows alone are not enough for the Evidence Board or Issue Workspace.

## D016: Schema versioning at canonical-envelope level
**Date:** 2026-03-08
**Decision:** Require `schema_version` on persisted or exported canonical graph envelopes, starting with `v2alpha1`.
**Reason:** Typed contracts, fixtures, exports, and future APIs need an explicit compatibility boundary. Versioning only in tribal knowledge would make `#6`, `#10`, and `#12` drift silently.

## D017: Distinguish shipped V0 surfaces from written V2 specs
**Date:** 2026-03-10
**Decision:** Treat the current notebook/package flow as the shipped product surface, and treat `docs/V2_WORKFLOW_IA.md`, `docs/V2_EVIDENCE_SCHEMA.md`, plus the placeholder `apps/`, `workers/`, and `packages/` directories as V2 planning artifacts unless implementation work explicitly lands in code.
**Reason:** The repo now has a stable V0 demo, completed written specs for `#23` and `#24`, and placeholder top-level directories for future runtime boundaries. Without an explicit rule, contributors can over-read roadmap/docs as if the V2 app/api/runtime already exists.
**Impact:** README, HANDOFF, FOUNDATION, and ROADMAP should always separate "implemented now" from "planned V2". Active execution work should start with `#27`, `#6`, `#7`, `#8`, and `#9`, then move into `#10` onward.

## D018: Release scorecards derive fixture coverage from committed scenarios
**Date:** 2026-03-11
**Decision:** Treat committed scenario folders under `cache_samples/` as the source of truth for local release-scorecard fixture coverage reporting.
**Reason:** The repo now has four public/redacted offline scenarios across Florida, Texas, and Louisiana. Scorecard artifacts should report real committed coverage instead of a hardcoded narrative so `#27` calibration stays aligned with `#8` fixture work and `#9` CI smoke evidence.
**Impact:** When fixture scenarios are added, removed, or materially changed, the release scorecard should reflect that automatically and the canonical docs should be updated with the new coverage and supported test count.
