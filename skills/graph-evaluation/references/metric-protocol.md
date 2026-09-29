# Graph Metric Protocol

Metric definitions differ across papers; comparing numbers without matching definitions is a category error.

## Aggregation

| Choice | Meaning | Pitfall |
|---|---|---|
| macro averaging | Mean over classes | Sensitive to rare or absent classes |
| micro averaging | Pooled over instances | Dominated by frequent classes |
| per-class reporting | One number per class | Needed when class balance is extreme |

State which averaging is used. AUROC requires both classes present in the evaluated slice; record undefined metrics rather than substituting zero.

## Task-Specific Definitions

| Task | Definition to pin down |
|---|---|
| Node classification | Label space, masked nodes, class balance, per-class support |
| Link prediction | Ranking metric (MRR, Hits@K), filtered vs raw ranks, tie handling, K value, candidate set |
| Graph classification | Pooling/aggregation, cross-validation folds vs a single split, fold-level variance |
| Regression | Units, transformation, inverse-transformation bias in averaged metrics |

## Comparison Protocol

1. Match data version, splits, feature construction, parameter budget and tuning budget across methods.
2. Pair comparisons by split and seed; report the distribution of differences, not the best run.
3. Report the number of independent graphs/groups, not just instances.
4. Include failed runs, OOM cases and timeouts with denominators; selective reporting of successful runs biases results.

## Reporting Table

| Metric | Definition | Aggregation | Undefined handling | Notes |
|---|---|---|---|---|
| Hits@10 | Filtered rank ≤ 10 | Mean over test edges | — | Candidate set fixed to 1000 negatives |

Document versions of the graph library, sampler and metric implementation: scores are implementation-specific.
