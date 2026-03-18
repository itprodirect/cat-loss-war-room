# Project Health Audit

Date: March 10, 2026
Audience: Internal builders
Horizon: Next 2 weeks

## Status memo

### Implemented now

- The current product is a notebook-first V0 demo backed by `src/war_room/`.
- The offline demo lane is real: committed `cache_samples/` support cache-first runs without an API key across three public/redacted scenarios in Florida, Texas, and Louisiana.
- The supported test/bootstrap posture is real: `pip install -e . --no-deps --no-build-isolation` followed by `pytest -q`, or ad hoc local runs with `PYTHONPATH=src`.
- `178` tests pass under the supported bootstrap path.
- CI enforces a fresh-environment test gate, an explicit offline fixture smoke gate, and an `exa-py` compatibility matrix.
- Typed-domain and retrieval-contract work has landed substantial slices under `#6` and `#7`.
- Issue `#27` now has a fixture-calibrated local release-scorecard workflow tied to the committed scenario set.

### Specified but not built yet

- `docs/V2_WORKFLOW_IA.md` is the canonical written spec for the V2 workflow and IA (`#23`).
- `docs/V2_EVIDENCE_SCHEMA.md` is the canonical written spec for the V2 evidence graph and audit schema (`#24`).
- `apps/`, `workers/`, and `packages/` describe planned V2 runtime boundaries only. They currently contain placeholder READMEs, not active product code.
- The primary runnable surfaces remain the notebook, `python -m war_room`, and the Python package under `src/war_room/`.

### Main risks

- Documentation drift between "working now" V0 behavior and "planned V2" written specs.
- Contributor confusion around test/bootstrap expectations if they skip editable install.
- Roadmap drift if `#23` and `#24` are treated as active implementation tickets instead of completed source-of-truth specs.

## Files updated in this pass

- `README.md`: clarified supported bootstrap/test flow and the implemented-now versus planned-V2 boundary.
- `docs/HANDOFF.md`: updated status date, split completed V2 written specs from open implementation work, and added a clearer builder reading order.
- `docs/ROADMAP.md`: separated V0 baseline, completed V2 definition work, and active implementation priorities.
- `docs/FOUNDATION.md`: made bootstrap expectations explicit and clarified that placeholder V2 directories are not yet runnable surfaces.
- `docs/V2_ISSUE_MAP.md`: tightened the distinction between completed definition work and downstream implementation tickets.
- `docs/BUILD_CHECKLIST.md`: aligned the checklist with the audited next-2-weeks execution order.
- `docs/DECISION_LOG.md`: recorded the repo-wide rule that V2 written specs must not be read as shipped runtime surfaces.

## Canonical reading order

1. `README.md` for quickstart and current-state summary
2. `docs/HANDOFF.md` for builder orientation
3. `docs/FOUNDATION.md` for bootstrap, runtime, and repo-boundary rules
4. `docs/ROADMAP.md` for active execution order
5. `docs/V2_WORKFLOW_IA.md` for workflow and UX source of truth
6. `docs/V2_EVIDENCE_SCHEMA.md` for schema and provenance source of truth
7. `docs/V2_ISSUE_MAP.md` for issue-to-phase mapping
8. `docs/BUILD_CHECKLIST.md` for near-term execution tracking

## Contributor friction items

- Raw-checkout `pytest -q` is not a supported path. Contributors must either use editable install or set `PYTHONPATH=src`.
- The placeholder `apps/`, `workers/`, and `packages/` directories can look more implemented than they are unless docs call that out directly.
- The notebook is still the main demo surface. V2 app/api/workers are roadmap targets, not current runtime entrypoints.
- `#23` and `#24` are complete and closed as written specs. Downstream implementation belongs to `#10`, `#11`, and `#12`, plus remaining foundation work in `#6`, `#7`, `#8`, and `#9`.

## Next 2 weeks action plan

### Must fix

- Continue `#27` calibration now that the rubric, local artifact generator, and fixture-calibrated scorecard are in place.
  Artifact: threshold definitions tied to the committed fixture lane and future pilot evidence.
- Complete the remaining `#6` and `#7` scope with contract boundaries tied back to the written schema/workflow specs.
  Artifact: typed-model/retrieval work plus status updates in roadmap/handoff.
- Extend `#8` fixture breadth beyond the current FL/TX/LA trio and keep `#9` CI expansion aligned with those scenarios.
  Artifact: additional fixtures, stronger release-evidence automation, and refreshed build checklist.

### Should fix

- Keep README, HANDOFF, and FOUNDATION synchronized whenever bootstrap or contributor expectations change.
  Artifact: doc edits in the canonical set, not one-off notes elsewhere.
- Treat `#10`, `#11`, and `#12` as implementation tickets that consume `#23` and `#24`, not as places to re-decide workflow/schema.
  Artifact: roadmap wording and issue-scope discipline.

### Nice to have

- Add a small contributor-facing note wherever placeholders may be mistaken for active code.
  Artifact: repo-shape doc polish.
- Keep the session log and decision log current so future status reads do not depend on git archaeology.
  Artifact: routine log updates after each build session.
