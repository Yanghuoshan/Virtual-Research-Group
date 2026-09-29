---
name: interpretability-validation
description: Use when claims about model internals, such as SAE features, circuits, probes, or activation patching results, need validity, baseline, and control checks.
---

# Interpretability Claim Validation

Check whether supplied interpretability evidence supports the stated claim. Training probes or autoencoders and running interventions are not part of this task.

## Inputs

Claim statement (feature identity, causal role, localization, or completeness), model/version and layer/site, artifacts such as feature activations, dashboards, activation patching results, probe weights and labeled examples, dataset and split used for examples, baselines/controls, metric definitions, statistics, and assigned outputs. Missing controls are gaps.

## Method

1. Classify the claim precisely: descriptive (this direction or SAE feature responds to X), causal (this component is necessary/sufficient for behavior Y), localization, or completeness (this set explains the computation). Require evidence matched to that type. Description accuracy does not establish causal role; causal evidence on one prompt set does not establish a general mechanism.
2. Demand baselines and controls from the [baselines and controls](references/baselines-and-controls.md) catalog: random or untrained directions/SAEs, shuffled/permuted or resampled activations, control tasks for probe selectivity, corrupted-run patching controls, and simpler alternative explanations such as lexical, positional or n-gram features. A result without a matched baseline is not interpretable evidence.
3. Audit sampling and selection: how examples, features, prompts and layers were chosen; top-activating example selection; cherry-picked or hand-picked demonstrations; counts of examples/prompts; holdout features and holdout examples; dataset coverage and label provenance. Require held-out confirmation before generalization claims.
4. Audit measurement: activation thresholds, sparsity/L0, dead features and feature splitting/absorption for SAEs, reconstruction-fidelity versus interpretability tradeoff, dictionary size and training data, probe accuracy versus control-task accuracy, patch scope and side effects, resample versus zero ablation, and metric normalization.
5. Audit causal claims with [causal claims](references/causal-claims.md): distinguish necessity from sufficiency; check patching site, direction (restore/corrupt), magnitude, counterfactual metric, and whether effects survive controls and alternative sites. Confirm the behavioral metric actually measures the claimed behavior.
6. Audit human and automated labeling using [statistics and reporting](references/statistics-and-reporting.md): rubric, annotator count, inter-annotator agreement, blinding to the hypothesis, and judge-based scoring with its known biases. Treat judge scores as measurements with their own validity limits, not as ground truth.
7. Audit statistics with the same reference: counts of features/examples/prompts, per-example variance, multiple comparisons across features or layers, intervals and effect sizes, correction for searching many features, and cross-model or cross-dataset replication. Record how many features, layers or sites were searched before selection, and report negative results.

## Outputs

A claim-by-claim audit at assigned paths: claim type, evidence required, what was supplied, baseline/control status, defect list with severity and affected claim, replication status and unresolved gaps. No training or intervention execution.

## Checks

Do not train probes, sparse autoencoders, or run patching experiments; recommend a separate authorized execution task. Do not accept cherry-picked demonstrations as population evidence. Do not treat attention weights, probe accuracy or a plausible narrative as a causal mechanism. Correct for multiplicity across searched features.

Example: a feature whose top-activating examples all match a concept, without random-direction baselines, holdout examples or selectivity controls, supports a descriptive hypothesis, not a validated feature identity or causal role.

## Local References

- [Baselines and controls catalog](references/baselines-and-controls.md)
- [Causal claims in interpretability](references/causal-claims.md)
- [Statistics, labeling and reporting](references/statistics-and-reporting.md)

These define procedures for this skill only. They do not authorize training probes or autoencoders, or running interventions.

## Boundary

Return to the core with the report or blockers. Do not dispatch other skills or agents, select models, train interpretation artifacts, run interventions, schedule experiments, edit global findings/state, or advance phases.
