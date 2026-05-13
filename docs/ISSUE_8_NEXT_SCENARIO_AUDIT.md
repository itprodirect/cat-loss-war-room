# Issue 8 Next Scenario Candidate Audit

Date: 2026-05-13

## Conclusion

The next best `#8` fixture-breadth candidate is `tx_hail_allstate_tarrant`.

It is ready to promote from an existing committed fixture lane because it already has:

- a validated intake at `eval/intakes/tx_hail_allstate_tarrant.json`;
- a complete four-file fixture bundle at `cache_samples/tx_hail_allstate_tarrant/`;
- official weather support, carrier evidence, two case-law issue buckets, three citation checks, and one verified citation in the committed golden snapshot;
- passing offline preflight/e2e behavior with disclaimer and review-required posture intact.

This PR promotes it as `texas_hail_tarrant_allstate_hob`, the first Texas hail homeowners benchmark in the curated registry.

## Candidate Classification

| Candidate | Classification | Audit Result |
|---|---|---|
| `tx_hail_allstate_tarrant` | Ready to promote from existing committed fixture lane | Promoted in this PR as `texas_hail_tarrant_allstate_hob`. It broadens the registry beyond hurricane and HO-3 fact patterns while using already committed reviewed fixture data. |
| `tx_hail_allstate_tarrant_dp3` | Ready to promote from existing committed fixture lane | Suitable follow-up candidate. It uses the same Tarrant hail event but focuses on the narrower DP-3 matching/scope dispute, so it should follow the broader HO-B benchmark. |
| `ian_lee_citizens_ho3` | Needs manual fixture seeding | Curated registry scenario exists, but no committed fixture lane exists yet. Keep live-only until reviewed weather/carrier/caselaw/citation fixtures are seeded. |
| `irma_monroe_citizens_ho3` | Needs manual fixture seeding | Curated registry scenario exists, but no committed fixture lane exists yet. Good future legal-depth candidate after reviewed fixture seeding. |
| `michael_bay_default_ho3` | Needs manual fixture seeding | Curated registry scenario exists, but no committed fixture lane exists yet. Good future wind/scope candidate after reviewed fixture seeding. |
| `idalia_taylor_default_ho3` | Needs manual fixture seeding | Curated registry scenario exists, but no committed fixture lane exists yet. Good future recent-source candidate after reviewed fixture seeding. |
| `milton_citizens_pinellas` | Already promoted | Already mapped to `milton_pinellas_citizens_ho3`. Not a next candidate. |
| `ida_lloyds_orleans` | Already promoted | Already mapped to `ida_orleans_lloyds_ho3`. Not a next candidate. |
| `_template_case_intake.json` | Not suitable yet | Template only. It is not a fact pattern and must not be promoted. |

## Evidence Needed Before Future Promotions

For live-only registry scenarios, promotion still requires the full `docs/FIXTURE_SEEDING.md` path:

- reviewed public/redacted fact pattern;
- complete committed fixture directory with `weather.json`, `carrier.json`, `caselaw.json`, and `citation_verify.json`;
- official weather support for event/date/county;
- carrier evidence tied to carrier/jurisdiction/policy type;
- at least two case-law issue buckets;
- at least three citation checks with an internally consistent summary and at least one verified citation;
- snapshot and offline e2e validation with disclaimers and review-required posture intact.

## Issue Status

Issue `#8` should remain open. This audit promotes one safe existing fixture-backed candidate, but broader fixture breadth and future manual seeding remain incomplete.
