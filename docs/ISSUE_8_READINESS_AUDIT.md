# Issue 8 Readiness Audit

Date: 2026-05-14

## Decision

Issue `#8` should remain open through this fixture-seeding PR.

The prior four-lane breadth blocker is addressed by the new manually source-reviewed `ian_citizens_lee` fixture lane. The repo now has five complete committed fixture lanes, all registry-backed and offline-ready. This PR intentionally leaves issue disposition to maintainer review instead of using auto-close keywords.

This audit intentionally avoids auto-close keywords.

## Scope Reviewed

- GitHub issue `#8`
- `docs/FIXTURE_SEEDING.md`
- `docs/ISSUE_8_NEXT_SCENARIO_AUDIT.md`
- `scenarios/` and `scenarios/index.json`
- `cache_samples/`
- `eval/intakes/`
- `tests/golden/offline_fixture_snapshots.json`
- `src/war_room/fixture_snapshots.py`
- `src/war_room/offline_e2e.py`
- `docs/V2_RELEASE_RUBRIC.md`
- `docs/V2_ISSUE_MAP.md`
- `docs/ROADMAP.md`
- `README.md`
- `CLAUDE.md`
- `docs/HANDOFF.md`

No fixture data was invented, no live retrieval was run in tests, no dependencies were added, no notebooks were changed, and no `#10` orchestration work was started.

## Deliverable Audit

| Issue `#8` item | Current status | Evidence |
|---|---|---|
| Broaden the canonical scenario fixture set beyond the prior four committed directories | Complete for this PR's requested slice | `cache_samples/` now has five complete fixture directories: `milton_citizens_pinellas`, `ian_citizens_lee`, `ida_lloyds_orleans`, `tx_hail_allstate_tarrant`, and `tx_hail_allstate_tarrant_dp3`. All five are promoted to offline-ready registry scenarios. |
| Define golden snapshots for key memo sections | Complete for the current five-lane fixture set | `tests/golden/offline_fixture_snapshots.json` records the five scenarios, memo section structure, workflow/export posture, evidence counts, source badges, and citation summaries. `python -m war_room.fixture_snapshots --check` is the deterministic diff gate. |
| Add quality assertions for source mix, case count, citation-check summaries, and output structure | Complete for the current five-lane fixture set | `src/war_room/fixture_snapshots.py` enforces module completeness, FL/TX/LA state coverage, source badge minimums, case-law issue/case counts, citation summary consistency, at least one verified citation, memo sections, workflow status, evidence/issue counts, export posture, and at least five complete committed scenarios. |

## Acceptance Criteria Audit

| Acceptance criterion | Current status | Evidence |
|---|---|---|
| Scenario suite runs offline and in CI | Satisfied for the committed five-lane suite | `src/war_room/offline_e2e.py` requires at least five committed scenarios, all offline-ready, complete workflow stages, populated memo/review surfaces, structured export posture, and linked preflight artifacts. |
| Snapshot diffs are reviewable and intentional | Satisfied | `python -m war_room.fixture_snapshots --check` fails on drift and points maintainers to `--write` only for intentional refreshes. |
| Failing quality thresholds block merges | Satisfied for the current gates | The golden snapshot and fixture-quality assertions are covered by tests and the completed `#9` CI quality-gate stack. |

## Current Fixture Breadth

| Fixture lane | Registry slug | State | Peril / event | Carrier | Policy type | Offline status |
|---|---|---|---|---|---|---|
| `milton_citizens_pinellas` | `milton_pinellas_citizens_ho3` | FL | Hurricane Milton | Citizens Property Insurance | HO-3 Dwelling | Registry-backed and offline-ready |
| `ian_citizens_lee` | `ian_lee_citizens_ho3` | FL | Hurricane Ian | Citizens Property Insurance | HO-3 Dwelling | Registry-backed and offline-ready |
| `ida_lloyds_orleans` | `ida_orleans_lloyds_ho3` | LA | Hurricane Ida | Certain Underwriters at Lloyd's, London | HO-3 Dwelling | Registry-backed and offline-ready |
| `tx_hail_allstate_tarrant` | `texas_hail_tarrant_allstate_hob` | TX | Texas hailstorm | Allstate Texas Lloyds | HO-B Homeowners | Registry-backed and offline-ready |
| `tx_hail_allstate_tarrant_dp3` | `texas_hail_tarrant_allstate_dp3` | TX | Texas hailstorm matching dispute | Allstate Texas Lloyds | DP-3 Dwelling | Registry-backed and offline-ready |

Represented breadth:

- States: `FL`, `LA`, `TX`
- Perils/events: hurricanes and hailstorm/matching disputes
- Carriers: Citizens Property Insurance, Certain Underwriters at Lloyd's, London, Allstate Texas Lloyds
- Policy types: HO-3 Dwelling, HO-B Homeowners, DP-3 Dwelling
- Postures: denial, underpayment, bad faith

## Remaining Candidates

Live-only registry scenarios that still need manual fixture seeding only if maintainers want broader Florida coverage beyond this PR:

| Scenario | State / county | Carrier | Policy type | Current status |
|---|---|---|---|---|
| `irma_monroe_citizens_ho3` | FL / Monroe | Citizens Property Insurance | HO-3 Dwelling | `offline_demo_ready: false`, `fixture_case_key: null` |
| `michael_bay_default_ho3` | FL / Bay | Florida Peninsula Insurance Company | HO-3 Dwelling | `offline_demo_ready: false`, `fixture_case_key: null` |
| `idalia_taylor_default_ho3` | FL / Taylor | Florida Peninsula Insurance Company | HO-3 Dwelling | `offline_demo_ready: false`, `fixture_case_key: null` |

Intake-only candidates:

- No unpromoted standalone intake candidate exists in `eval/intakes/`.
- `eval/intakes/_template_case_intake.json` is a template, not a fact pattern, and must not be promoted.
- `eval/intakes/ida_lloyds_orleans.json`, `eval/intakes/tx_hail_allstate_tarrant.json`, and `eval/intakes/tx_hail_allstate_tarrant_dp3.json` already correspond to promoted fixture lanes.

## Recommended Disposition

Keep `#8` open for review of this fifth-lane fixture-seeding PR.

After review, maintainers should decide whether the current five registry-backed fixture lanes satisfy `#8`:

- If yes, perform closeout separately after this PR is reviewed and merged.
- If no, create a follow-up issue titled `Manually seed remaining live-only Florida fixture scenarios` and move any additional Florida seeding work there.

The remaining live-only Florida scenarios should not be treated as offline-ready until they receive their own reviewed fixture bundles under `docs/FIXTURE_SEEDING.md`.
