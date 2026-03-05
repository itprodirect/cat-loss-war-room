# CAT-Loss War Room - Session Log

This is the concise, current session timeline.

## Session 1 - Foundation
Date: 2026-02-25
Status: Complete

- Established repo structure, core modules, and initial docs.
- Built notebook baseline (cells 0-3).
- Added initial tests.

## Session 2 - Exa Integration
Date: 2026-02-25
Status: Complete

- Added weather, carrier, caselaw, citation verification, and export flow.
- Seeded cache samples for offline demo behavior.
- Expanded tests.

## Session 3 - Reliability Patch Pass
Date: 2026-02-25
Status: Complete

- Improved caselaw filtering.
- Hardened citation-check behavior and search-budget handling.
- Fixed hostname normalization bug.
- Brought test suite to 75 passing.

## Session 4 - V2 Planning and Issue Setup
Date: 2026-03-04
Status: Complete

- Added V2 blueprint and issue map docs.
- Created GitHub roadmap issues #3 through #19.

## Session 5 - V2 Issue #4 Execution
Date: 2026-03-04
Status: Complete

- Implemented exa-py compatibility support in `exa_client.py`.
- Pinned tested dependencies for reproducible setup.
- Added adapter regression tests.
- Added CI fresh-env test gate and exa-py compatibility matrix.
- Expanded test suite to 81 passing.

## Session 6 - PR and Merge
Date: 2026-03-04
Status: Complete

- Opened PR #20 for issue #4 work.
- Verified all CI checks passed.
- Merged to `main`.

## Current Snapshot
Date: 2026-03-04

- Branch baseline: `main` contains PR #20 changes.
- Test status: 81 passing.
- Roadmap source of truth: `docs/ROADMAP.md` and `docs/V2_ISSUE_MAP.md`.
- Next priority: issue #5 (schema alignment), then #6 (typed contracts).

## Session 7 - Documentation Refresh and Roadmap Simplification
Date: 2026-03-04
Status: Complete

- Updated canonical docs to match current state (81 tests, CI gates, issue #4 closed).
- Rewrote `docs/HANDOFF.md` for cleaner onboarding.
- Added `docs/ROADMAP.md` for a plain-language, issue-linked plan.
- Updated `docs/V2_BLUEPRINT.md` and `docs/V2_ISSUE_MAP.md` to reflect completed #4 and next priorities.
- Replaced legacy prompt/checklist docs with current, execution-focused versions.
- Verified repository test suite remains green (`81 passed`).

## Session 8 - Eval Lane Formalization
Date: 2026-03-04
Status: Complete

- Formalized the `eval/` workspace as a tracked project surface.
- Added `eval/README.md` with clear usage and data rules.
- Added a CaseIntake-aligned starter template at `eval/intakes/_template_case_intake.json`.
- Updated `eval/results/README.md` and `.gitignore` behavior for local eval artifacts.
- Linked the live eval lane from README and HANDOFF docs.
- Verification: `pytest -q` -> 81 passed.

## Session 9 - Hardening Pass: Null-Client Safety + Caselaw Precision
Date: 2026-03-05
Status: Complete

- Added graceful null-client fallbacks in weather/carrier/caselaw module entrypoints.
- Modules now prefer cache when available and return structured empty payloads when live retrieval is unavailable.
- Tightened caselaw case-like filtering:
  - citation-only items now require a trusted legal/court host,
  - case-name patterns still pass.
- Softened assertive carrier phrasing to evidence-oriented language.
- Added regression tests for all fallback and filter hardening behavior.
- Updated V2 blueprint note to reference `_template_case_intake.json`.
- Verification: `pytest -q` -> 85 passed.

## Session 10 - Issue #5 Intake Validation and Schema Lock
Date: 2026-03-05
Status: Complete

- Added strict intake ingestion helpers in `src/war_room/query_plan.py`:
  - `validate_case_intake_payload(payload)`
  - `load_case_intake(path)`
  - `IntakeValidationError`
- Enforced canonical schema boundaries:
  - required fields must exist,
  - unknown fields are rejected,
  - no type coercion,
  - `event_date` must be valid `YYYY-MM-DD`,
  - `posture` must be a non-empty list of snake_case tokens.
- Exported intake validation API and schema constants from `war_room.__init__`.
- Added coverage in `tests/test_intake_validation.py` for valid/invalid payloads and JSON ingest errors.
- Updated `eval/README.md` with explicit required/optional fields for both demo and live-eval lanes plus strict validation behavior.
- Updated build checklist to reflect issue #5 completion.
- Verification: `pytest -q` -> 96 passed.
