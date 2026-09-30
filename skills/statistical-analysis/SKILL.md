---
name: statistical-analysis
description: Use when manifested, analysis-ready data must be tested against a pre-specified analysis plan: point estimates, uncertainty intervals, multiplicity control, effect sizes, and machine-checkable summary tables that distinguish confirmatory from exploratory results.
---

# Pre-Specified Statistical Testing

Execute the analysis a protocol already specified. This skill computes and reports quantities with their assumptions; it does not choose hypotheses after seeing results, and it does not announce scientific conclusions.

## Inputs

A data manifest with its analysis-ready tables, the protocol's analysis plan (primary and secondary comparisons, declared unit of analysis, `primary_measure`, `baseline`, `validation_plan`, `uncertainty_plan`), the computation channel assigned by the core, and fresh output paths. A manifest without a matching analysis plan is a blocker; testing whatever the data happens to support is out of contract.

## Method

1. Read the declared unit of analysis from the manifest and verify the table shape honors it; dependence between rows (shared seeds, clusters, repeated measures) changes the test, not just the arithmetic.
2. Execute each planned comparison following the [test selection](references/test-selection.md) rules: estimand first, then estimator, then test, then interval - in that order, matching the protocol's `uncertainty_plan`. Report every planned comparison including nulls and negatives.
3. Apply multiplicity control exactly as pre-specified across the planned family; a family with no declared correction is reported as uncorrected plus a limitation, never silently corrected or silently uncorrected.
4. Quantify what the data supports using [uncertainty and reporting](references/uncertainty-and-reporting.md) rules: effect sizes with intervals, not bare p-values; distinguish "no evidence of effect" from "evidence of no effect"; state assumptions that survived and assumptions that the data violated.
5. Label every output `confirmatory` (pre-specified in the plan) or `exploratory` (computed because the data suggested it). Exploratory results may appear, clearly fenced, but never enter the confirmatory summary table.
6. Separate author-reported numbers (baseline values cited from runs or literature with locators) from reviewer-computed numbers in every table; they are never averaged or blended.
7. When an assumption fails badly enough that no test is defensible, stop and return a blocker with the diagnostic - a broken test reported as passed is worse than no test.

## Outputs

At the assigned paths: a machine-readable summary table (one row per planned comparison: estimand, estimator, effect, interval, multiplicity status, label), an analysis report with assumptions and their checks, diagnostics for violated assumptions, and explicit limitations or blockers.

## Checks

Every number in the summary table is recomputable from the cited manifest tables with the stated method. The set of confirmatory comparisons matches the protocol's plan exactly - nothing added, nothing dropped. Exploratory work is fenced and cannot contaminate the confirmatory table. Distinguish underpowered results from null results. Do not round, trim, or select toward significance.

Example: with three seeds and a declared subject-level unit, a seed-level t-test is a unit error even if it reaches significance; the correct output reports the dependence problem and the planned but underpowered comparison, not a borrowed significance.

## Local References

- [Test selection rules](references/test-selection.md)
- [Uncertainty, multiplicity and reporting](references/uncertainty-and-reporting.md)

They define procedures for this skill only. They do not authorize new hypotheses, extra comparisons as confirmatory, or conclusions.

## Boundary

Return to the core with tables, diagnostics and blockers. Do not dispatch other skills or agents, select models, run experiments, process raw data, make figures, update global findings/state, or advance phases. Plotting belongs to quantitative plotting; accepting what results mean belongs to the core.
