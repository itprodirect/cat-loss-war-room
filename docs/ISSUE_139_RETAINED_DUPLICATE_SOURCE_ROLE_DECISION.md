# Issue 139 Retained Duplicate and Source-Role Metadata Decision

Date: 2026-05-28

## Purpose

Issue [#139](https://github.com/itprodirect/cat-loss-war-room/issues/139)
exists to prevent future issue `#12` work from moving from same-module
dedupe into cross-module evidence collapse before the audit model can preserve
the meaning of removed rows.

This is a decision record only. It does not change runtime behavior, exported
fields, markdown output, tests, fixtures, persistence, API, UI, dashboard,
auth, queues, workers, fuzzy matching, ML clustering, AI scoring, or citation
verification behavior.

## Decision

Cross-module evidence behavior stops at clustering-only relatedness.

`EvidenceItem` continues to preserve module-specific meaning. `EvidenceCluster`
continues to express relatedness across modules by citation, URL, or derived
authority grouping. Future work should improve grouping and reviewer visibility
before considering any row removal, but cross-module collapse is not a planned
next step under issue `#12`.

The current same-module dedupe behavior remains valid:

- same-module duplicate rows may collapse when deterministic compatibility
  checks prove the retained row preserves the removed row's audit meaning;
- every removed ID must map to a retained ID before downstream surfaces are
  finalized;
- caselaw and citation-verification rows that share a citation or URL remain
  separate `EvidenceItem` rows and may share an `EvidenceCluster`;
- raw/pre-dedupe and retained/exported counts must remain distinguishable.

## Metadata Home

If retained duplicate/source-role metadata is implemented later, it should live
as an audit-snapshot or audit-bundle trace object, not on `EvidenceItem` and
not on `EvidenceCluster`.

Recommended future shape:

- add a separate `EvidenceDedupeTrace` or `EvidenceAlias` style record attached
  to `RunAuditSnapshot` or the audit/export bundle;
- create trace records only for removed same-module duplicates in the first
  implementation;
- keep `EvidenceItem` focused on retained evidence meaning;
- keep `EvidenceCluster` focused on relatedness, not row-removal audit history;
- keep the trace object out of persistence/API/UI contracts until those
  contracts are explicitly scoped.

Reasoning:

- putting removed-row aliases on `EvidenceItem` would make each retained row
  carry audit-process history that is not itself evidence;
- putting aliases on `EvidenceCluster` would confuse relatedness with removal
  semantics and would be especially risky for cross-module clusters;
- a separate trace object can preserve reviewer auditability without implying
  cross-module dedupe is allowed.

## Fields To Preserve

A future same-module dedupe trace must preserve enough information for a
reviewer to understand what was removed, what retained it, and why.

For the removed duplicate row, preserve:

- old evidence ID;
- module;
- evidence type;
- source role, defined as module plus evidence type unless a future schema adds
  a narrower role vocabulary;
- title;
- summary or a deterministic summary excerpt;
- URL;
- citation;
- authority key;
- badge;
- source reason;
- source class;
- source tier;
- issue;
- primary-authority flag;
- review-required flag.

For the retained row, preserve:

- retained evidence ID;
- module;
- evidence type;
- source role;
- title;
- URL;
- citation;
- authority key;
- badge;
- source reason;
- source class;
- source tier;
- issue;
- primary-authority flag;
- review-required flag.

For the dedupe decision, preserve:

- dedupe scope, initially `same_module`;
- dedupe key type, such as normalized URL, normalized citation, authority key,
  or module-scoped title fallback;
- normalized dedupe key value or a deterministic digest if the value is too
  long for review output;
- reason for dedupe, including first-row-wins retained-row behavior;
- pre-dedupe order or enough ordering context to explain why one row was
  retained.

## Why Cross-Module Collapse Is Not Implemented Now

Cross-module collapse would remove evidence rows that may have different legal
or review roles even when they point at the same authority.

The sharpest example is caselaw plus citation verification:

- a caselaw row represents an authority candidate or legal support item;
- a citation-verification row represents the result of a spot-check against a
  citation or authority;
- the citation-verification row carries status, badge, note, review-required
  state, and review-event meaning that should not be buried inside a caselaw
  row;
- current read models and markdown surfaces do not yet expose removed-row
  aliases as reviewer-facing audit history.

The safer policy is therefore:

- do not dedupe or collapse across modules;
- let cross-module rows share an `EvidenceCluster`;
- require a separate, test-covered trace implementation before any future
  cross-module collapse proposal can even be evaluated.

## Implementation Decision

This issue is closed by docs only.

The existing code already has a runtime-local same-module remap for audit
snapshot assembly, but adding retained duplicate/source-role metadata in code
now would either be internal-only or would expand the public audit/export
contract. Internal-only metadata would not satisfy reviewer traceability, while
public metadata belongs in a separately scoped schema and export/read-model
slice.

## Issue 139 Closure Checklist

- [x] Chose clustering-only cross-module relatedness as the durable current
  policy.
- [x] Confirmed cross-module dedupe/collapse is not planned as the next issue
  `#12` step.
- [x] Chose the future metadata home: a separate audit-snapshot or audit-bundle
  trace object.
- [x] Defined fields that must be preserved for removed and retained duplicate
  evidence.
- [x] Explained why cross-module collapse is not implemented now.
- [x] Kept the change docs-only with no runtime, schema, export, fixture, API,
  UI, dependency, or citation-behavior changes.
- [x] Opened follow-up issue
  [#142](https://github.com/itprodirect/cat-loss-war-room/issues/142) for
  same-module `EvidenceDedupeTrace` / `EvidenceAlias` implementation if
  maintainers want reviewer-visible retained duplicate metadata next.

## Recommended Follow-Up Issue

Title:

`Add same-module evidence dedupe trace metadata to audit snapshots`

Tracking issue: [#142](https://github.com/itprodirect/cat-loss-war-room/issues/142)

Suggested scope:

- add a separate trace object for removed same-module duplicates;
- preserve old ID, retained ID, source role, module, evidence type, key reason,
  URL/citation/authority fields, source tiering fields, and review flags;
- prove no cross-module trace or collapse occurs;
- keep markdown/read-model exposure minimal and explicit;
- do not add persistence, API, UI/dashboard, auth, queues, workers, fuzzy/ML
  clustering, AI scoring, live retrieval, or citation behavior changes.
