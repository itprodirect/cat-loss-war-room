# Repo Brief

## Purpose

CAT-Loss War Room is a notebook-first catastrophic-loss litigation research demo. It turns a case intake into weather corroboration, carrier intelligence, issue-organized case law, citation spot-checks, and a markdown memo.

## User / buyer

- Primary buyer/user: Merlin Law Group demo stakeholders.
- Primary operator today: a technical or semi-technical builder running the notebook and offline cache-backed demo flow.

## Strategic role

This repo is the current execution surface for attorney-demo research acceleration and the proving ground for V2 contracts, workflow read models, and release-quality gates. It is not yet the future web product.

## Current milestone

Preserve the stable V0 notebook demo while finishing broader `#27` CI/pilot operationalization after the completed five-lane offline fixture baseline and landed issue `#88` reviewer-summary slice.

## Non-goals

- Broad refactors or repo reshaping.
- Renaming the repo or repositioning it as a SaaS product.
- Treating `apps/`, `workers/`, or `packages/` as live runtime entrypoints.
- New dependency adoption without approval.
- ML scoring or classification in place of deterministic domain rules.

## Inputs / dependencies

- Structured case intake and scenario registry data.
- Committed offline fixtures in `cache_samples/` for the demo lane.
- Exa-backed retrieval for live runs when enabled.
- Deterministic source scoring, typed contracts, and cache-first retrieval rules in `src/war_room/`.
- Editable package bootstrap, `.env` settings, and the project venv.
- Jupyter notebook surface plus preflight and verify CLI entrypoints.

## Outputs

- Research-plan preview and workflow summaries.
- Weather, carrier, and case-law research packs.
- Citation verification summaries.
- Markdown research memo exports with disclaimers and audit linkage.
- Preflight and verification results for demo readiness.
- Run-scoped preflight, scorecard, and verify-manifest artifacts for the supported local release-evidence path, including blocking/advisory readiness categories and the top-level `reviewer_summary` convenience layer for reviewer use.
- Golden offline fixture snapshots for reviewable scenario/output drift checks.
- Categorized CI quality-gate artifacts for unit, offline fixture, offline e2e, golden snapshot, Exa compatibility, release-scorecard, security-hygiene, and dependency-hygiene lanes.

## Quality bar

- Attorney-demo credible and easy to run.
- Offline cache-backed demo path remains reliable.
- Outputs keep disclaimers, traceability, and review-required markers.
- Validation uses the supported path (`python -m war_room --verify`) rather than unsupported raw-checkout shortcuts.
- Docs stay aligned with the actual branch state and open milestone.

## Known risks

- The primary UX is still notebook-first, which is less approachable for non-technical users.
- The issue `#10` run-state contract slice, issue `#73` API boundary contract slice, in-process offline service slice, operator-facing status presentation layer, dependency-free thin transport/request-handler wrapper, and dev-only standard-library HTTP adapter exist, but production API routing, persistence, queues, auth, retries, circuit breakers, dashboards, and UI remain unbuilt.
- Issue `#11` has guided-intake and run-status UX specs plus deterministic previews only; no web UI has shipped.
- Offline readiness is stronger but still demo-scoped: five committed fixture lanes now have a golden snapshot gate and fixture-backed registry scenarios, and issue `#8` is closed as completed after the five-lane baseline validation.
- Case-law precision and citation confidence still need ongoing hardening in edge cases.
- Status can drift quickly because roadmap, handoff, and session history are dense and frequently updated.

## Next 3 tasks

1. Continue issue `#27` by broadening CI/pilot release evidence beyond the merged local verify bundle without changing the current demo surface.
2. Map the remaining issue `#10` scope against the landed contracts/service/status/transport/dev-HTTP stack, keeping production routing, persistence, queues, auth, retries, circuit breakers, dashboards, and UI out unless explicitly authorized.
3. Split issue `#11` into a contract seam and future UI child issues before any implementation beyond the landed specs/previews.

## Ownership

Named ownership is not explicit in the repo. Functional ownership is the current maintainer group shipping a Merlin Law Group demo; buyer/user ownership sits with Merlin Law Group stakeholders.
