# Session 144 Closeout — May 20, 2026

## Purpose

This closeout captures what changed in the May 20 evidence/provenance session, why the choices were made, which tools were used, and where future maintainers or agents should start next.

The main goal was to advance issue `#12` without weakening the legal/audit trail. The session moved from same-module evidence dedupe integration to a small reviewer-visibility follow-up, then paused before any risky cross-module dedupe work.

## Tools and review flow used

- ChatGPT was used for repo triage, issue creation, PR review, and GitHub connector operations.
- Codex implemented the focused code/test/docs slices.
- Claude Code was used as a read-only second reviewer for the provenance-sensitive dedupe integration.
- GitHub Actions validated PRs through the repo CI and Exa Compatibility Matrix workflows.
- The supported local validation path reported by Codex was:
  - `git diff --check`
  - focused pytest targets
  - `python -m pytest -q`
  - `python -m war_room --verify`

## What landed today

### PR #136 — same-module audit-snapshot dedupe

PR `#136` integrated deterministic same-module evidence dedupe into audit snapshot assembly.

Key behavior:

- Dedupe runs after current weather, carrier, caselaw, and citation-verify adapters emit canonical `EvidenceItem` rows.
- Dedupe is same-module only.
- Cross-module caselaw and citation-verification rows do not collapse.
- An explicit runtime-local `old_id -> retained_id` remapping rewrites downstream evidence references.
- Clusters, memo claims, review events, quality counts, read models, and markdown/export-facing surfaces resolve to retained IDs.
- `raw_evidence_count` tracks pre-dedupe adapter rows.
- `evidence_item_count` tracks retained/exported evidence rows.

Reported validation:

- `python -m pytest -q` -> `491 passed`
- `python -m war_room --verify` -> passed; embedded pytest reported `491 passed`
- GitHub Actions CI and Exa Compatibility Matrix passed.

Review result:

- ChatGPT review: approve.
- Codex/Claude read-only review: approve, no blockers.
- Non-blocking follow-ups became issue `#137`.

### Issue #137 and PR #138 — citation `not_found` regression and markdown visibility

Issue `#137` was created to address the non-blocking review follow-ups from PR `#136`.

PR `#138` then landed:

- A focused duplicate `citation_verify` regression for `status="not_found"`.
- Proof that the `citation-not-found` review event rewrites removed evidence IDs to the retained citation evidence ID.
- Proof that related cluster IDs still resolve after the rewrite.
- A reviewer-facing Markdown Quality Snapshot line:

```text
Evidence retention: <raw> raw/pre-dedupe / <retained> retained/exported
```

Reported validation:

- `python -m pytest tests/test_memo_contracts.py tests/test_export.py -q` -> `63 passed`
- `python -m pytest -q` -> `493 passed`
- `python -m war_room --verify` -> passed; embedded pytest reported `493 passed`
- GitHub Actions CI and Exa Compatibility Matrix passed.

PR `#138` was marked ready and squash-merged. Issue `#137` auto-closed as completed.

### Issue #139 — planning issue for the next serious decision

Issue `#139` was created to prevent future agents from jumping directly into risky cross-module dedupe.

Title:

`Decide retained duplicate/source-role metadata before cross-module dedupe`

It captures these options:

- Option A: stop at same-module dedupe for now.
- Option B: design retained duplicate/source-role metadata before implementation.
- Option C: implement retained duplicate/source-role metadata for same-module dedupe only.
- Option D: enable cross-module dedupe without retained metadata — not recommended.
- Option E: never collapse cross-module rows; use clusters only.

Recommended next-session starting point:

Start with a docs-only decision record under issue `#139`. Do not enable cross-module dedupe yet.

## Decisions made

1. Same-module dedupe is safe enough to integrate when every removed ID maps to a retained ID and all downstream references are rewritten.
2. Cross-module dedupe is not safe yet.
3. Caselaw rows and citation-verification rows may share the same authority, citation, or URL, but they can represent different evidence roles.
4. `EvidenceCluster` is currently the safer way to express cross-module relatedness without deleting module-specific evidence meaning.
5. Raw/pre-dedupe counts and retained/exported counts should both remain visible because they answer different audit questions.
6. Future cross-module dedupe, if ever implemented, should wait for a retained duplicate/source-role metadata design.

## Current repo truth after this session

- Active runtime is still the notebook plus `src/war_room/`.
- The repo is not a production web app.
- The dev HTTP adapter remains dev-only and process-local.
- No persistence, auth, users, sessions, queue, worker, dashboard, production API, or frontend was added.
- Issue `#12` now has adapters, helper dedupe, same-module audit-snapshot dedupe, retained-ID remapping, provenance-integrity coverage, `not_found` citation regression coverage, and markdown raw-vs-retained evidence visibility.
- Issue `#12` is still not a full V2 evidence graph.
- Cross-module dedupe remains intentionally disabled.
- Current validation baseline after PR `#138`: `493 passed` under the full pytest path reported by Codex and `python -m war_room --verify`.

## Recommended next-session roadmap

### Recommended path — issue #139 docs-only decision record

Create a decision record that answers:

- Should cross-module rows ever collapse, or should clusters remain the only cross-module grouping mechanism?
- If retained duplicate/source-role metadata is needed, where should it live?
  - `EvidenceItem`
  - `EvidenceCluster`
  - a separate `DedupeTrace`
  - a separate `EvidenceAlias`
- What fields must be preserved?
  - old evidence ID
  - retained evidence ID
  - module
  - evidence type
  - source role
  - URL
  - citation
  - authority key
  - citation status
  - badge
  - review-required flag
  - collapse reason
- What, if anything, should markdown/read models expose before cross-module dedupe is reconsidered?

### Acceptable alternate path — same-module metadata implementation only

If implementation work is preferred next, keep it same-module only.

Possible scope:

- Give the existing `removed_duplicate_ids` and `retained_id_to_duplicate_ids` data a controlled downstream consumer.
- Preserve current no-cross-module-collapse behavior.
- Avoid markdown/read-model changes unless explicitly scoped.

### Avoid next

Do not implement cross-module dedupe next. That would optimize output neatness before the audit model is ready.

## Non-goals preserved today

- No cross-module evidence collapse.
- No retained-row duplicate/source metadata schema yet.
- No persistence.
- No API framework.
- No UI/dashboard.
- No auth/users/sessions.
- No queues/workers/background runtime.
- No fuzzy/ML clustering.
- No AI scoring.
- No live retrieval changes.
- No citation verification behavior changes.
- No broad golden snapshot refresh.
- No claim that the V2 evidence graph is complete.
- No Beta-ready, Pilot-ready, production-ready, or self-serve legal-product claim.

## Suggested restart prompt for the next session

```text
We are continuing cat-loss-war-room after the May 20 evidence/provenance session.

Current state:
- PR #136 merged same-module audit-snapshot dedupe with old_id -> retained_id remapping.
- PR #138 merged not_found citation regression coverage and markdown raw-vs-retained evidence visibility.
- Issue #137 is closed.
- Issue #139 is open and should be the next planning starting point.
- Current reported validation baseline after PR #138: 493 passing tests and `python -m war_room --verify` passed.

Goal:
Start with issue #139 and create a docs-only decision record deciding whether retained duplicate/source-role metadata is needed before any future cross-module dedupe. Do not implement cross-module dedupe.
```
