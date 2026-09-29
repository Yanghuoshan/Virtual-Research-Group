---
name: graph-evaluation
description: Use when graph, node, or link prediction protocols and outputs require task-specific leakage checks and valid metric interpretation.
---

# Graph Evaluation and Leakage Audit

Evaluate one specified graph-learning protocol or result set. Do not train or select a new model family.

## Inputs

Task level, graph construction rules, split/entity identifiers, label availability, transductive or inductive setting, prediction files if available, metrics, baseline budgets, and output scope. Without predictions, return a protocol audit, not measured performance.

## Method

1. Establish the statistical unit: node, edge, graph, or graph family. Check duplicates and source-related graph groups before interpreting independent samples.
2. Trace graph construction, normalization, features, and message-passing access to labels and held-out entities. Transductive access to unlabeled structure can be allowed by the protocol; held-out labels or future information cannot silently enter it.
3. For link prediction, document negative sampling, filtered positives, temporal ordering, and whether reverse edges leak targets. Match candidate sets across methods.
4. For graph classification, split correlated graphs by source entity where appropriate. Fit preprocessing only on permitted data. Verify validation-only model selection and untouched test reporting.
5. Compute or check the metric exactly as specified: macro versus micro aggregation, multilabel handling, AUROC class availability, or ranking tie conventions. Record undefined metrics rather than substituting zero.
6. Compare matched data, parameter/tuning budgets, seeds, and splits. Pair comparisons by split/seed and report the distribution, not the best run.
7. Return a finding for each defect: location, leakage mechanism, affected claim, severity, and proposed correction for the core to consider.

## Outputs

A protocol/evidence audit and, only when supplied predictions permit it, per-run metric tables with definitions and provenance. All artifacts go to assigned paths.

## Checks

Do not present node accuracy as graph accuracy. Do not infer unseen-graph generalization from a transductive node split. Distinguish confidence from additional dependent samples. Document graph-builder and sampler versions.

Example: removing a held-out positive edge while retaining its reverse edge may invalidate an undirected link-prediction split.

## Boundary

Return to the core with findings or missing-input blockers. Do not dispatch other skills or agents, select models, schedule training, change splits globally, advance phases, or edit global state. Corrections are recommendations, not automatically applied research decisions.
