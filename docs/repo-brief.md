# Repo Brief

## Purpose

CAT-Loss War Room is a notebook-first catastrophic-loss litigation research demo. It turns a case intake into weather corroboration, carrier intelligence, issue-organized case law, citation spot-checks, and a markdown memo.

## User / buyer

- Primary buyer/user: Merlin Law Group demo stakeholders.
- Primary operator today: a technical or semi-technical builder running the notebook and offline cache-backed demo flow.

## Strategic role

This repo is the current execution surface for attorney-demo research acceleration and the proving ground for V2 contracts, workflow read models, and release-quality gates. It is not yet the future web product.

## Current milestone

Preserve the stable V0 notebook demo while finishing the active foundation tranche: issue `#27` plus the remaining work in `#6`, `#7`, `#8`, and `#9`.

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
- Run-scoped preflight, scorecard, and verify-manifest artifacts for the supported local release-evidence path.

## Quality bar

- Attorney-demo credible and easy to run.
- Offline cache-backed demo path remains reliable.
- Outputs keep disclaimers, traceability, and review-required markers.
- Validation uses the supported path (`python -m war_room --verify`) rather than unsupported raw-checkout shortcuts.
- Docs stay aligned with the actual branch state and open milestone.

## Known risks

- The primary UX is still notebook-first, which is less approachable for non-technical users.
- Offline readiness is uneven: committed fixtures exist, but the broader scenario registry is not fully fixture-backed.
- Case-law precision and citation confidence still need ongoing hardening in edge cases.
- Status can drift quickly because roadmap, handoff, and session history are dense and frequently updated.

## Next 3 tasks

1. Continue issue `#27` by operationalizing the release scorecard in CI and pilot evidence without changing the current demo surface.
2. Finish the remaining `#6` and `#7` foundation seams so the notebook-era runtime keeps one clear contract path.
3. Expand `#8` and `#9` with broader fixture coverage and CI quality gates that match the supported offline-demo lane.

## Ownership

Named ownership is not explicit in the repo. Functional ownership is the current maintainer group shipping a Merlin Law Group demo; buyer/user ownership sits with Merlin Law Group stakeholders.
