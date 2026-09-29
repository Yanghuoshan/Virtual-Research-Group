# General Research Framework Implementation Plan (Historical)

> Superseded by the flat architecture in the root `SKILL.md`. The configuration layers described below are historical and must not be recreated or used for routing. The current helper reads the core phase contract directly and receives one explicit skill, role, model, output scope, and acceptance criterion per assignment.

**Goal:** Build a domain-neutral research skill with sequential role and model handoffs in an independent `research-framework/` directory. Do not modify `.claude/`, install the bundle automatically, or start research.

**Architecture:** Separate research phases, role responsibilities, domain methodology, tool selection, and host models. Use JSON for checkable configuration and state, Markdown for methodology and handoff contracts, and Python standard-library helpers for offline operations rather than model execution.

**Technology:** Python 3.10+ standard library, JSON, and Markdown; no external Python dependencies.

## Alternatives

1. Copy and rename the old orchestrator: inexpensive, but retains domain routing, continuous-execution, and model assumptions.
2. Create a general core with the old library as optional knowledge: selected for clear boundaries and methodological reuse.
3. Introduce a full multi-agent service, queue, and database: deferred because sequential handoffs do not require a daemon.

## Files and Work Sequence

1. `tests/test_framework.py`: define acceptance tests first and observe failures while tools are missing. Cover configuration, domain routing, planning defaults, overwrite refusal, path boundaries, evidence, and model declarations.
2. `SKILL.md`, `core/*.json`, `references/*.md`: define phased roles, permissions, and evidence gates without making training loss or GPUs universal prerequisites.
3. `domains/*.json`, `adapters/manual.json`, `catalog.json`: provide general and cross-domain examples. Keep LLM tools optional rather than discarding entire transferable capability categories.
4. `library/`: initially copy six ideation and output skills byte for byte with source hashes. Do not execute their workflows. For the subsequent English edition, record language adaptations separately from original hashes.
5. `scripts/research.py`: implement `validate`, `init`, and `handoff`. Requests do not switch models or call APIs. Resolve paths against their declared roots.
6. `README.md`, `THIRD_PARTY_NOTICES.md`: explain use, extension, defaults, authorization, and license review required before redistribution.
7. Run unit tests, architecture checks, and cross-domain paper scenarios; compare `.claude/` hashes and library manifests. Do not commit or create automations.

## Baseline Before Implementation

Read-only evaluation of the original `0-autoresearch-skill/` found:

- No role-to-model binding, handoff packet, or acceptance receipt. Skill routing is not model switching.
- Continuous operation described as mandatory, without an internal planning-only mode.
- Textual metric and baseline requirements, but no structured split or evidence-trust gates.
- An approaching deadline, unverified inherited metrics, and planning-only authorization cannot justify proceeding to a results-based paper.

## Acceptance Criteria

- All new content stays under `research-framework/`; original source hashes remain unchanged.
- Default to planning only; no schedules, commits, remote API calls, training, or paid-resource actions.
- Graph learning, vision, robotics, and symbolic examples use appropriate data, methods, and evidence without mandatory training or GPUs.
- Packets contain target roles, model requests, input evidence, output boundaries, blockers, and receipt requirements.
- Reject execution handoffs without authorization or a frozen protocol; reject results writing without reviewed evidence.
- Track the six packages' provenance and license limitations. Do not present this local bundle as cleared for public redistribution.
- Deliver bundled documentation, descriptions, templates, examples, and generated scaffolding in English while preserving user-supplied inputs.

## Observed Verification History

- The initial 19 tests failed because the helper was missing, then passed after implementation.
- Review scenarios reproduced stale-audit reuse, inconsistent configuration validation, and unchecked handoff paths. Version binding and shared validation brought the suite to 34 passing tests.
- Three read-only scenarios exercised graph classification under planning-only authorization, symbolic proofs without GPUs, and extracting a domain skill from research. These assess contract application, not actual research performance.
- At initial delivery, all 417 original `.claude/` files and all 75 copied library files matched their source hashes.
- The English edition adds language regression checks, translates first-party content, and adapts three library documents while retaining original hashes for provenance.
- Model API dispatch, automatic state transitions, enforced budgets, and research executors remain unimplemented and are not claimed as completed capabilities.

## Flat Architecture Delivery (2026-09-29)

The current core entry owns runtime directories, phases, hypothesis decisions, skill/role/model choices, acceptance, and all global state. Thirteen specialists are directly discoverable under `skills/`; each returns artifacts or blockers instead of delegating, scheduling, or selecting models.

The domain, role-preset, adapter and capability-registry layers have been removed. Reused source files are mapped through `provenance.json` for attribution only. Runtime schema is 2, and legacy projects require explicit manual migration.

Regression tests cover direct discovery, explicit assignments, English text, source-independent initialization, protected global state, stale audits, existing output directories and raw evidence separate from protocols. The last two defects were reproduced with four failing tests before repair. Application scenarios checked graph leakage without retraining, missing citations without delegation, and missing renderers without autonomous backend selection. These are contract tests, not real research experiments.
