---
name: experimental-design
description: Use when a specified hypothesis needs a discriminating validation protocol, or a proposed study has unresolved controls, sampling units, statistical power, or stopping criteria before execution.
---

# Discriminating Experimental Design

Produce a draft protocol for the core to assess. Design evidence that could distinguish a hypothesis from plausible alternatives, not a procedure optimized to obtain significance.

## Inputs

Question and candidate hypothesis, competing explanations, target population/task, available data and resources, meaningful effect or success criterion, prior measurements if available, constraints, permitted tools, and new output paths. State missing assumptions rather than inventing variance, sample size or causal identification.

## Method

1. Define the estimand or proof obligation and its falsifiers; distinguish exploratory from confirmatory questions, and select a design from the [design catalog](references/design-catalog.md). For proof-only work, skip inapplicable empirical steps 2-5 and specify assumptions, counterexamples and independent checking in step 6. For causal claims, specify intervention, confounders and identification assumptions; predictive gains alone do not establish causation.
2. Work through the [units and power](references/units-and-power.md) worksheet: separate sampling, assignment/randomization, measurement and analysis units. Account for clusters, repeated measures, temporal dependence and shared datasets; avoid pseudoreplication. Repeated seeds measure training variability, not independent population samples. Propose randomization, blocking, pairing or blinding where feasible; document remaining confounding.
3. Specify controls, baselines, ablations and resource-matched tuning. Preserve held-out evaluation; propose preprocessing and model-selection rules limited to training/validation data, without fitting or selecting a model. Define leakage checks and inclusion/exclusion rules before results are seen.
4. Pre-specify primary and secondary outcomes, units, metric direction, effect sizes, uncertainty intervals and analysis assumptions. Plan handling of missing values, failed runs and outliers. Address multiple comparisons and optional stopping; do not choose favorable metrics or stopping rules after inspecting results.
5. Justify sample/cluster/run counts using a meaningful effect, variance/dependence assumptions and target power or precision. Record sensitivity to uncertain assumptions and feasibility under budget. Without these inputs, return a conditional calculation plan or explicitly limited pilot design, not an invented power claim. No fixed number of seeds guarantees adequacy.
6. Map the draft to `primary_measure`, `baseline`, `validation_plan` and `uncertainty_plan` using [evaluation plan mapping](references/evaluation-plan-mapping.md). Include data/code versions, seeds, measurement procedure, resource bounds, stopping/failure criteria and planned raw artifacts. For theoretical work, substitute proof obligations, assumptions, counterexample strategy and independent checking for inappropriate statistical fields; do not force GPUs or empirical power onto a proof.
7. Enumerate threats, alternatives, unresolved decisions and acceptance criteria. A revision to an already frozen protocol is a new proposal with a rationale, not an overwrite. Simulations or pilot experiments need a separate authorized execution task.

## Outputs

A versioned draft protocol at the assigned path, evaluation-field proposals, comparison/analysis plan, feasibility assessment, assumption ledger and blockers. Never overwrite an existing artifact; request a new path on collision. Label proposed quantities separately from observations. The core alone accepts and freezes the protocol or updates project state.

## Checks

Could a plausible result falsify the claim? Do uncertainty calculations use the correct independent unit? Are causal assumptions defensible and analyses fixed before outcomes? Do not freeze or execute the design, manufacture a pilot estimate, or turn absence of significance into proof of equivalence.

Example: 1,000 images from ten subjects and three seeds do not provide 3,000 independent subjects. Plan subject-level splitting and dependence-aware uncertainty; missing variance assumptions prevent a power guarantee.

## Local References

- [Design catalog and selection rules](references/design-catalog.md)
- [Units, dependence and precision](references/units-and-power.md)
- [Mapping the draft to evaluation fields](references/evaluation-plan-mapping.md)

These define procedures for this skill only. They do not authorize freezing the protocol, running experiments, or recording evaluation fields.

## Boundary

Return to the core with the draft or specific blockers. Do not dispatch other skills or agents, select models, run training/simulations/proof checks, schedule experiments, spend resources, change global findings/state, or advance phases. Protocol approval and execution authorization are separate core decisions.
