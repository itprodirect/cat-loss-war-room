# Fixture Seeding Process

This checklist is the safe path for adding or promoting offline scenarios under issue `#8`.

The goal is reviewable fixture breadth, not synthetic coverage. Do not mark a scenario offline-ready until the committed evidence exists and has been reviewed.

## Scenario Terms

| Term | Location | Meaning |
|---|---|---|
| Curated registry scenario | `scenarios/*.json` plus `scenarios/index.json` | A named benchmark exposed to notebook/runtime scenario selection. It may be live-only or offline-ready. |
| Committed fixture lane | `cache_samples/<case_key>/` | A cache-backed offline lane containing `weather.json`, `carrier.json`, `caselaw.json`, and `citation_verify.json`. It is what preflight, snapshots, and offline e2e exercise. |
| Offline-demo-ready scenario | `scenarios/*.json` with `offline_demo_ready: true` | A curated registry scenario that points to a complete committed fixture lane through `fixture_case_key`. It is safe for cache-only notebook demos. |
| Live-eval/intake-only scenario | `eval/intakes/*.json` or a registry scenario with `offline_demo_ready: false` | A validated intake or benchmark definition that is not cache-only ready. It must not be treated as an offline demo scenario until reviewed fixture payloads are committed. |

## Promotion Requirements

Before setting `offline_demo_ready: true`, all of the following must be true:

- the scenario is public/redacted and contains no secrets, privileged claim material, or private client identifiers;
- the scenario JSON validates against the canonical `CaseIntake` fields;
- `fixture_case_key` is set and points to a committed `cache_samples/<case_key>/` directory;
- the fixture directory contains all four required module files: `weather.json`, `carrier.json`, `caselaw.json`, and `citation_verify.json`;
- fixture payloads are based on reviewed source material or reviewed live-retrieval output, not invented data;
- weather evidence includes meaningful official-source support for the event, date, and county;
- carrier evidence identifies the carrier, jurisdiction, policy type, and reviewable source links;
- case-law evidence has at least two issue buckets and reviewable authority rows;
- citation verification has at least three checks, an internally consistent summary, and at least one verified citation;
- generated memo/review surfaces keep demo disclaimers and review-required states intact;
- `python -m war_room.fixture_snapshots --check` either passes or the golden snapshot is refreshed intentionally with a small, explained diff.

## Seeding Checklist

1. Start from a public/redacted fact pattern.
2. Add or validate the intake in `eval/intakes/` if the scenario is not already in the curated registry.
3. Keep the scenario live-only while evidence is incomplete: `offline_demo_ready: false` and `fixture_case_key: null`.
4. Build fixture payloads outside tests. Live retrieval may be used only as a deliberate manual seeding step, never in tests or CI.
5. Review the four module payloads for source quality, source badges, citation summary consistency, disclaimers, and obvious scraped navigation or boilerplate.
6. Commit the fixture bundle under `cache_samples/<case_key>/` only after review.
7. Promote the registry scenario by setting `fixture_case_key` to the committed lane and `offline_demo_ready: true`.
8. Add the scenario slug to `scenarios/index.json` only when it should appear in the curated notebook/runtime catalog.
9. Refresh `tests/golden/offline_fixture_snapshots.json` with `python -m war_room.fixture_snapshots --write` only after inspecting the generated diff.
10. Run the required offline gates and include exact results in the PR.

## Validation Commands

Run these before requesting review:

```bash
python -m pytest tests/test_fixture_snapshots.py tests/test_offline_demo_pack.py tests/test_intake_validation.py tests/test_scenarios.py -q
python -m pytest -q
python -m war_room.fixture_snapshots --check
python -m war_room.offline_e2e --check
python -m war_room --verify --release-candidate issue-8-fixture-seeding-process
```

## PR Notes

Every fixture-seeding PR should say:

- whether it adds a new committed fixture lane, promotes an existing lane, or only documents/seeds an intake;
- whether any live retrieval happened during manual seeding, and that tests/CI do not make live calls;
- what golden snapshot changes were intentional;
- whether issue `#8` remains open.

## Do Not Promote When

- the scenario only has a registry file or intake file;
- fixture payloads are partial, generated from invented facts, or not reviewed;
- `fixture_case_key` is missing or points at a non-existent fixture directory;
- citation summaries do not reconcile;
- the memo/review surfaces drop disclaimer or review-required posture;
- the change starts product orchestration work from `#10`.
