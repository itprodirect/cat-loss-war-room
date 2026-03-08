# CAT-Loss War Room V2 Blueprint

## 1) Executive Read

The repo is a good v0 demo and a weak v1 product.

That is not a criticism of the first build. It is the right result for a fast prototype:

- the core workflow is real,
- the legal framing is disciplined,
- the cache-first demo lane works,
- and the codebase is small enough to reason about.

What it does **not** yet prove is that attorneys or paralegals can use it alone, that evidence quality is strong across many fact patterns, or that the system can be operated like a product instead of a narrated notebook.

V2 should preserve the best parts of v0 and rebuild the rest around:

- a product-grade web experience,
- a modular-monolith backend,
- a canonical evidence and provenance model,
- explicit review workflow,
- and measured AI usage only where it increases quality.

Do **not** rebuild this as a distributed microservice maze. The right V2 is a disciplined product platform, not a prematurely complex systems demo.

## 2) Current-State Scorecard

| Dimension | Verdict | Why |
|---|---|---|
| Demo reliability | Strong | Offline cache lane, committed fixtures, and `151` passing tests make the demo dependable. |
| End-user usability | Weak | The primary interface is still Jupyter plus environment setup and kernel selection. |
| Evidence quality | Mixed | Good source gathering intent, but normalization and extraction are still brittle. |
| Legal trust posture | Promising | Guardrails and disclaimers are strong; provenance and review workflow are not yet product-grade. |
| Architecture | Good prototype | Modules are understandable, but orchestration, contracts, storage, and runtime boundaries are still early. |
| Security and operations | Early | Repo hygiene is fine; product controls, auditability, and observability are mostly roadmap work. |

## 3) Deep-Dive Assessment

### What Works Well

- The product thesis is good.
  - Weather corroboration + carrier intelligence + case law + memo export is a compelling legal workflow.
- Cache-first design is the best decision in the repo.
  - `cache_samples -> cache -> live` makes the demo reliable and preserves an offline regression lane.
- Legal safety posture is unusually clear for an early prototype.
  - Disclaimers, citation warnings, and source badges are consistent.
- Module boundaries are understandable.
  - Weather, carrier, case law, citation checks, and export are separated in a way a new engineer can follow.
- Test coverage is respectable for a prototype.
  - `151` tests is enough to trust refactors more than usual at this stage.
- Documentation is better than the average internal prototype.
  - Handoff, method, safety, demo script, and roadmap docs reduce tribal knowledge.

### What Is OK, But Will Limit V2 If Left Alone

- Typed contracts are landing, but they are not yet the real internal architecture.
  - Pydantic currently validates payloads, but the core still leans on dict-shaped module outputs.
- Deterministic source scoring is the right default.
  - It is explainable, but it needs governance and more nuanced evidence handling around edge domains.
- The query-plan approach is directionally right.
  - It is still static, heuristic-heavy, and not yet editable, auditable, or quality-scored.
- The notebook is fine for guided demos.
  - It is a demo surface, not a product surface.

### What Is Bad Or High-Risk

- The UI/UX is effectively nonexistent for real users.
  - The current "app" requires Python setup, Jupyter, kernel selection, and a run-cell mental model.
  - That is acceptable for engineers and demos, not for attorneys.
- The canonical data model is improving, but still stops too early.
  - The system now knows about evidence clusters, memo claims, review events, and audit links, but it still lacks full run/stage/research-plan persistence and product-grade issue/memo-section entities across the runtime.
- Evidence normalization is too weak for trust-critical output.
  - Duplicate sources, generic regulatory pages, and noisy snippets still leak into output.
- Legal extraction is still brittle.
  - Case names, courts, years, and citations are regex-first and can be noisy or incomplete.
- Current sample output still shows relevance problems.
  - Weather extracts storm-wide metrics without strong county anchoring.
  - Carrier results include generic `floir.com` pages that are structurally valid but not very useful.
  - Case-law output still includes commentary-like entries such as "Wind vs. Water Damage: What Homeowners Must Know".
- Validation and orchestration logic are duplicated.
  - `CaseIntake` rules exist in both `models.py` and `query_plan.py`.
  - Each module regenerates its own query slice instead of operating from one canonical run plan.
- Packaging and runtime ergonomics are improving but still early.
  - The editable package/bootstrap layer is now in place.
  - The broader V2 repo split (`apps/`, `workers/`, `packages/`) is still planned rather than implemented.
- CI is still shallow for a V2 target.
  - Today it is essentially `pytest -q` plus an `exa-py` compatibility matrix.

### What Is Unknown

- Real usefulness across multiple jurisdictions, perils, and carriers.
- Precision and recall for case-law retrieval.
- How much AI improves extraction and drafting versus how much noise it introduces.
- How long it takes a new legal user to complete intake-to-memo without help.
- Live cost and latency under repeated use.
- Which outputs attorneys actually keep, edit, or discard.

## 4) If Starting From Scratch Today

### Keep

- The legal problem framing.
- Cache-first fixtures and offline demo lane.
- The module decomposition as a learning scaffold.
- Deterministic source-tiering as a policy layer.
- The safety posture and disclaimer language.
- The existing tests and sample outputs as regression assets.

### Kill

- Jupyter as the primary user interface.
- Dict-shaped payloads as the long-term internal contract.
- Provider SDK types leaking across module boundaries.
- Regex-only extraction as the main trust mechanism.
- "One-shot memo generation" as the core experience.

### Rewrite

- The runtime architecture.
- The canonical domain model.
- Evidence normalization and provenance tracking.
- Case-law resolution and citation handling.
- Export and memo workflow.
- User experience from intake through review.

### Delay

- Multi-tenant SaaS complexity.
- Fancy autonomous-agent behavior.
- Firm memory as a major feature before provenance and review are solid.
- Vector search as a default storage strategy.
  - Start with explicit relational entities and good retrieval metadata first.

## 5) Product Thesis For V2

### Primary Users

- Partner
  - Wants a fast, trustworthy first-pass research package and clear uncertainty markers.
- Associate
  - Wants issue-level evidence, citations, and a strong drafting starting point.
- Paralegal
  - Wants guided intake, progress visibility, and a repeatable way to gather material fast.
- Operator or litigation support lead
  - Wants reliability, audit trails, benchmark quality, and release confidence.

### V2 Outcome Targets

- A new legal user can complete intake and launch a run without engineering help.
- Every important statement in the memo can be traced back to evidence.
- Partial failures do not collapse the workflow.
- Citation ambiguity is visible, reviewable, and exportable.
- The system is measurably better than the notebook on speed, trust, and clarity.

## 6) UX Verdict And Experience Blueprint

### Current UX Verdict

Helpful as a narrated demo.

Nearly nonexistent as a standalone product.

The notebook explains the flow if an engineer is driving. It does not give non-technical users:

- safe input handling,
- clear progress,
- error recovery,
- evidence review,
- or a human approval workflow.

### V2 Workflow

1. **Intake**
   - Guided form with validation, redaction cues, defaults, and matter templates.
2. **Research Plan**
   - Preview planned modules, domains, questions, and estimated cost/time before run.
3. **Run Timeline**
   - Show module-by-module progress, retries, partial failures, and budget use.
4. **Evidence Board**
   - Deduplicated evidence cards with source tier, provenance, confidence, and exclusions.
5. **Issue Workspace**
   - Cluster facts and cases by legal issue with clear "why this matters" summaries.
6. **Memo Composer**
   - Section-based drafting with evidence links and review-required flags.
7. **Export And Audit Bundle**
   - Clean memo export plus appendix, evidence index, and run audit snapshot.

### UX Principles

- Show evidence before prose.
- Make uncertainty visible in the main flow, not hidden in footnotes.
- Prefer partial output over hard failure.
- Use review-required states instead of pretending low-confidence output is complete.
- Keep the interface calm, dense, and serious.
  - This should feel like a premium legal workbench, not a startup analytics dashboard.

### Visual Direction

- Editorial rather than "dashboard-first".
- High-contrast, document-like layout with strong information hierarchy.
- Confidence should use both color and text.
  - Never rely on badge color alone.
- Motion should be minimal and purposeful.
  - Progress and transitions, not decorative animation.
- Typography should support long-form reading and evidence comparison.

## 7) Recommended V2 Architecture

### 7.1 Build A Modular Monolith First

Do not begin with independent services for every module.

Recommended repo shape:

```text
apps/
  web/            # end-user UI
  api/            # HTTP API, auth, run state, orchestration endpoints
workers/
  research/       # background execution of runs
packages/
  domain/         # typed models, schemas, policy rules
  retrieval/      # provider interfaces and adapters
  pipeline/       # normalization, analysis, drafting orchestration
  export/         # markdown/docx/pdf generation
  evals/          # benchmark fixtures, scorecards, release gates
```

One backend codebase, one worker runtime, one frontend. Separate later only when operational data proves the need.

### 7.2 Runtime Model

- **Web app**
  - Intake, run status, evidence workspace, memo composer, export history.
- **API**
  - Owns run creation, read models, permissions, and orchestration commands.
- **Worker**
  - Executes retrieval, normalization, legal analysis, citation checks, and draft assembly.
- **Relational store**
  - Canonical run, evidence, issue, memo, review, and audit entities.
- **Object store**
  - Raw retrieval payloads, fetched content, PDFs, rendered exports.
- **Queue**
  - Background execution and retries.
- **Fixture lane**
  - Offline sample bundles remain first-class for demo and regression use.

### 7.3 Canonical Domain Model

Core V2 entities should include:

- `CaseIntake`
- `ResearchPlan`
- `Run`
- `RunEvent`
- `RetrievalTask`
- `EvidenceItem`
- `EvidenceCluster`
- `LegalIssue`
- `CaseCandidate`
- `CitationCheck`
- `MemoSection`
- `MemoClaim`
- `ReviewEvent`
- `ExportArtifact`

The key missing V0 idea is this:

> The memo is not the primary object. The memo is a view over evidence, issues, claims, and review state.

That is the architecture shift that makes V2 trustworthy.

### 7.4 Pipeline Stages

1. Intake validation and PII sanitization.
2. Research-plan generation with explicit rationale.
3. Retrieval through provider abstraction.
4. Evidence normalization, dedupe, and provenance attachment.
5. Module analysis:
   - weather,
   - carrier,
   - case law,
   - citation resolution.
6. Evidence-linked drafting and summary generation.
7. Human review and approval flow.
8. Export and immutable audit snapshot.

### 7.5 Storage Strategy

- Use relational storage for canonical state and auditability.
- Store raw retrieval content separately from normalized evidence.
- Version schemas and fixture outputs explicitly.
- Preserve a deterministic fixture lane for smoke tests and demos.
- Do not default to vector infrastructure until there is a measured need.
  - V2 should win on provenance and workflow before semantic memory becomes a platform concern.

### 7.6 Operational Boundaries

- Every run has explicit state transitions:
  - `queued`, `running`, `partial_success`, `failed`, `completed`, `cancelled`.
- Every stage emits structured events with trace IDs.
- Provider adapters return normalized errors and retry metadata.
- Cache entries and fixtures carry schema version information.
- No user-facing claim is emitted without a provenance path.

## 8) AI Integration Plan

### Use AI For

- Structured extraction from noisy text.
- Evidence summarization.
- Drafting alternative argument formulations from already-linked evidence.
- Highlighting contradictions or missing support in a draft.

### Do Not Use AI For

- Source credibility tiering.
- Final citation truth decisions without evidence.
- Unbounded legal recommendations.
- Silent rewriting that breaks evidence links.

### Guardrails

- Every generated statement must reference evidence IDs or citation anchors.
- Unsupported text is rejected, downgraded, or sent for review.
- Redaction happens before any external model call.
- Model/provider choice is environment-configurable and logged.
- The product must degrade gracefully to extractive or rule-based output if AI gates fail.

### Product Rule

AI should be an accelerator inside a trustworthy system, not the center of the trust model.

## 9) Security, Compliance, And Trust Baseline

- Redact or block sensitive intake details before external retrieval.
- Treat caches, raw retrieval payloads, and exports as controlled artifacts.
- Add retention rules for demo, staging, and production environments.
- Log review events, citation decisions, and export actions.
- Use role-aware access for editing, approving, and exporting.
- Keep legal disclaimers and confidence messaging intact across all surfaces.

## 10) Quality And Evaluation Strategy

### Test Pyramid

- Unit:
  - validation, scoring, parsing, formatting, policy rules.
- Component:
  - provider adapters, normalization pipeline, citation resolver.
- Integration:
  - intake -> run -> evidence -> memo using fixture bundles.
- E2E:
  - guided UI flows and error states.
- Human evaluation:
  - attorney and paralegal usability reviews using benchmark matters.

### V2 Scorecard

Measure at least:

- retrieval relevance,
- evidence cleanliness,
- citation confidence,
- memo usefulness,
- run reliability,
- latency,
- cost per run,
- and time-to-completion for a new user.

### Release Gates

- **Demo-ready**
  - stable fixture lane, no hard crashes, readable output.
- **Beta-ready**
  - canonical evidence graph, web UX, partial-failure handling, measurable scorecard.
- **Pilot-ready**
  - review workflow, observability, security baseline, benchmark and usability thresholds.

## 11) Phased Roadmap

### Phase 0: Rebuild Framing And Product Foundation

Goal: lock the shape of V2 before heavy implementation.

- [#22](https://github.com/itprodirect/cat-loss-war-room-demo/issues/22) product foundation
- [#23](https://github.com/itprodirect/cat-loss-war-room-demo/issues/23) workflow + design system
- [#24](https://github.com/itprodirect/cat-loss-war-room-demo/issues/24) canonical evidence graph + audit schema
- [#27](https://github.com/itprodirect/cat-loss-war-room-demo/issues/27) quality rubric + release scorecard

Exit criteria:

- repo shape is decided,
- product workflow is explicit,
- canonical data model is defined,
- and V2 has measurable success gates.

### Phase 1: Foundation Hardening

Goal: make the existing engine safe to build on.

- [#6](https://github.com/itprodirect/cat-loss-war-room-demo/issues/6) typed domain models
- [#7](https://github.com/itprodirect/cat-loss-war-room-demo/issues/7) retrieval contracts
- [#8](https://github.com/itprodirect/cat-loss-war-room-demo/issues/8) scenario fixtures
- [#9](https://github.com/itprodirect/cat-loss-war-room-demo/issues/9) CI quality gates

Exit criteria:

- typed contracts are real,
- provider boundaries are stable,
- scenario coverage is broader than one demo matter,
- and CI enforces more than unit success.

### Phase 2: Product Core

Goal: turn the prototype engine into a usable product workflow.

- [#10](https://github.com/itprodirect/cat-loss-war-room-demo/issues/10) orchestration API
- [#11](https://github.com/itprodirect/cat-loss-war-room-demo/issues/11) web intake + run status UX
- [#12](https://github.com/itprodirect/cat-loss-war-room-demo/issues/12) evidence normalization
- [#13](https://github.com/itprodirect/cat-loss-war-room-demo/issues/13) case-law quality v2
- [#25](https://github.com/itprodirect/cat-loss-war-room-demo/issues/25) AI guardrails + eval harness
- [#26](https://github.com/itprodirect/cat-loss-war-room-demo/issues/26) human review workflow

Exit criteria:

- a non-technical user can complete a guided run,
- evidence is normalized and reviewable,
- AI behavior is constrained,
- and humans can edit without losing provenance.

### Phase 3: Trust, Operations, And Adoption

Goal: make V2 pilotable in a serious legal environment.

- [#14](https://github.com/itprodirect/cat-loss-war-room-demo/issues/14) citation verification v2
- [#15](https://github.com/itprodirect/cat-loss-war-room-demo/issues/15) memo workspace/export v2
- [#16](https://github.com/itprodirect/cat-loss-war-room-demo/issues/16) firm memory v1
- [#17](https://github.com/itprodirect/cat-loss-war-room-demo/issues/17) observability + cost controls
- [#18](https://github.com/itprodirect/cat-loss-war-room-demo/issues/18) security baseline
- [#19](https://github.com/itprodirect/cat-loss-war-room-demo/issues/19) attorney pilot validation

Exit criteria:

- trust signals are operationalized,
- the memo workflow is clean enough for repeated use,
- operations and security are measurable,
- and pilot learnings feed the next backlog.

## 12) Hard Recommendations

- Build V2 as a modular monolith, not a fleet of services.
- Keep the notebook, but demote it to diagnostic/demo status.
- Treat provenance as a first-order product feature, not an appendix detail.
- Keep the canonical evidence graph clustered by durable identifiers such as normalized URLs and case citations, not only flat memo rows.
- Carry those cluster identifiers through memo claims so review, export, and later UI surfaces can address grouped support directly.
- Carry those same cluster identifiers through review events so the audit trail does not fall back to module-only warning context.
- Do not ship "AI magic" before scorecards, evidence links, and human review are real.
- Do not start firm memory until review workflow, provenance, and security baseline are underway.

## 13) Immediate Next Actions

1. Finish the remaining typed-domain work in [#6](https://github.com/itprodirect/cat-loss-war-room-demo/issues/6) with explicit schema-versioning rules.
2. Use completed [#22](https://github.com/itprodirect/cat-loss-war-room-demo/issues/22) as the bootstrap baseline, then push [#23](https://github.com/itprodirect/cat-loss-war-room-demo/issues/23), [#24](https://github.com/itprodirect/cat-loss-war-room-demo/issues/24), and [#27](https://github.com/itprodirect/cat-loss-war-room-demo/issues/27) before major V2 implementation.
3. Use the current notebook plus fixture lane as the regression harness while API and web surfaces come online.
4. Only introduce AI into V2 through the guardrailed path defined in [#25](https://github.com/itprodirect/cat-loss-war-room-demo/issues/25).
