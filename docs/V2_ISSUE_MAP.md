# V2 Roadmap Issue Map

This file maps V2 phases to GitHub issues so planning and execution stay aligned.

Written source-of-truth specs for `#23` and `#24` are complete and those definition issues should remain closed. Downstream implementation work continues in later issues; those docs should not be read as evidence that the V2 app/api/runtime already exists.

## Phase 0: Stabilize V0 Baseline

| Focus | Issue | Notes |
|---|---|---|
| Program epic | [#3](https://github.com/itprodirect/cat-loss-war-room/issues/3) | Master scope and success criteria |
| Exa adapter compatibility fix | [#4](https://github.com/itprodirect/cat-loss-war-room/issues/4) | Completed and closed (Mar 4, 2026) |
| Live-eval intake schema alignment | [#5](https://github.com/itprodirect/cat-loss-war-room/issues/5) | Completed and closed (Mar 5, 2026) |

## Phase 1: V2 Framing and Product Foundation

| Focus | Issue | Notes |
|---|---|---|
| Product foundation and repo shape | [#22](https://github.com/itprodirect/cat-loss-war-room/issues/22) | Completed and closed Mar 6, 2026: packaging/bootstrap landed; app boundaries, envs, local dev, fixture lane documented |
| Workflow IA and design system | [#23](https://github.com/itprodirect/cat-loss-war-room/issues/23) | Written spec complete and issue closed in `docs/V2_WORKFLOW_IA.md`; downstream implementation belongs to `#10` and `#11` |
| Canonical evidence graph and audit schema | [#24](https://github.com/itprodirect/cat-loss-war-room/issues/24) | Written spec complete and issue closed in `docs/V2_EVIDENCE_SCHEMA.md`; downstream implementation belongs to `#6`, `#10`, `#11`, and `#12` |
| Quality rubric and release scorecard | [#27](https://github.com/itprodirect/cat-loss-war-room/issues/27) | First-pass rubric plus fixture-calibrated local scorecard now live in `docs/V2_RELEASE_RUBRIC.md`; CI artifact emission and the linked local verify-evidence workflow are landed, and the next step is broader CI and pilot operationalization |

## Phase 2: Foundation and Quality Gates

| Focus | Issue | Notes |
|---|---|---|
| Typed domain models | [#6](https://github.com/itprodirect/cat-loss-war-room/issues/6) | In progress: intake/query, pack, citation/export, graph/version, issue/authority, run/retrieval, review/export graph-linkage, schema-versioned runtime cache-envelope, and typed Evidence Board / Issue Workspace read-model slices are landed against the canonical schema in `#24` |
| Retrieval adapter contract tests | [#7](https://github.com/itprodirect/cat-loss-war-room/issues/7) | In progress: provider seam, notebook retrieval-state emission, citation-verify tracking, deterministic retrieval-task timing, and Exa compatibility tests landed |
| Scenario fixture suite | [#8](https://github.com/itprodirect/cat-loss-war-room/issues/8) | Four committed scenario directories now cover Florida, Texas, and Louisiana and feed `#27`; the next step is broader breadth plus comparable thresholds |
| CI quality gate pipeline | [#9](https://github.com/itprodirect/cat-loss-war-room/issues/9) | Fresh-env + exa compatibility + offline fixture smoke now exist; release-scorecard artifact emission and validation plus the local verify-evidence workflow are wired, and the next step is broader CI layering, fixture breadth, and failure categorization |

## Phase 3: Product Core and Human Workflow

| Focus | Issue | Notes |
|---|---|---|
| API orchestrator service | [#10](https://github.com/itprodirect/cat-loss-war-room/issues/10) | Move orchestration out of notebook |
| Web intake and run status UI | [#11](https://github.com/itprodirect/cat-loss-war-room/issues/11) | Non-technical usability, shaped by `#23` |
| Evidence normalization engine | [#12](https://github.com/itprodirect/cat-loss-war-room/issues/12) | Dedupe, confidence, provenance, built on `#24` |
| Caselaw quality and filtering v2 | [#13](https://github.com/itprodirect/cat-loss-war-room/issues/13) | Reduce false positives |
| AI guardrails and eval harness | [#25](https://github.com/itprodirect/cat-loss-war-room/issues/25) | Evidence-linked generation only |
| Human review workflow | [#26](https://github.com/itprodirect/cat-loss-war-room/issues/26) | Approvals, revisions, provenance-preserving edits |

## Phase 4: Trust, Scale, and Adoption

| Focus | Issue | Notes |
|---|---|---|
| Citation verification hardening | [#14](https://github.com/itprodirect/cat-loss-war-room/issues/14) | Better official-source validation and ambiguity handling |
| Memo workspace and export v2 | [#15](https://github.com/itprodirect/cat-loss-war-room/issues/15) | Cleaner legal-ready output, paired with `#26` |
| Firm memory v1 | [#16](https://github.com/itprodirect/cat-loss-war-room/issues/16) | Governed memory after provenance, review, and security mature |
| Observability and run audit logs | [#17](https://github.com/itprodirect/cat-loss-war-room/issues/17) | Operability and trust |
| Security and PII controls | [#18](https://github.com/itprodirect/cat-loss-war-room/issues/18) | Production readiness baseline |
| Pilot validation with attorneys | [#19](https://github.com/itprodirect/cat-loss-war-room/issues/19) | Product-market fit feedback, scored through `#27` |

## Cross-Cutting Workstreams

| Focus | Issue | Notes |
|---|---|---|
| Product foundation | [#22](https://github.com/itprodirect/cat-loss-war-room/issues/22) | Unblocks clean implementation of nearly every V2 workstream |
| UX and design coherence | [#23](https://github.com/itprodirect/cat-loss-war-room/issues/23) | Keeps V2 from devolving into a backend-first tool with thin screens |
| Provenance and canonical contracts | [#24](https://github.com/itprodirect/cat-loss-war-room/issues/24) | Backbone for evidence trust, review, audit, and export |
| AI guardrails | [#25](https://github.com/itprodirect/cat-loss-war-room/issues/25) | Required for any serious AI-assisted extraction or drafting |
| Release scorecard | [#27](https://github.com/itprodirect/cat-loss-war-room/issues/27) | Shared benchmark language across CI, dashboards, and pilot work; local artifacts now record committed fixture coverage and the supported verify path emits a linked release-evidence bundle |
