# Mapping the Draft to Evaluation Fields

The draft must be checkable against the project's evaluation fields. Propose values; the core records them.

## Field Mapping

| Field | Draft content |
|---|---|
| `primary_measure` | Single pre-specified outcome: name, direction, units, aggregation |
| `baseline` | Comparison conditions, including resource-matched baselines and ablations |
| `validation_plan` | Split/holdout construction, leakage checks, selection rules, inclusion/exclusion |
| `uncertainty_plan` | Runs/seeds, clustering, interval definition, multiplicity handling |

Secondary outcomes stay secondary: list them separately so a primary result cannot be swapped after the fact.

## Pre-Specification

| Item | Where it is fixed |
|---|---|
| Outcome and metric definition | Before any result is inspected |
| Stopping rule | Before the run; optional stopping needs correction |
| Subgroup analyses | Pre-specified, or explicitly exploratory |
| Exclusions and failure handling | Pre-specified with reasons |
| Analysis code version | Recorded with the protocol |

## Versions and Artifacts

Record data/version identifiers, code revision, environment, seeds, configuration, measurement procedure, resource bounds, stopping/failure criteria and the planned raw artifact paths. Include what will be preserved even when a run fails.

## Theoretical Variant

For proof-only work, do not fabricate empirical fields. Map instead to:

| Item | Content |
|---|---|
| Proposition | Exact statement and quantifiers |
| Assumptions | Axioms, domain restrictions, side conditions |
| Proof obligations | Soundness, completeness, termination as applicable |
| Counterexample strategy | Bounded search strategy and reported bounds |
| Independent checking | Who/what re-checks, and how disagreement is resolved |

Mark inapplicable empirical fields as not applicable rather than filling them with placeholders.
