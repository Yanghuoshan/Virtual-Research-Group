# Variance, Statistics and Reporting

One run is not an estimate. Report spread, and compare models with paired evidence.

## Sources of Variance

| Source | Handling |
|---|---|
| Sampling (temperature/top-p) | Fix n and report per-run scores; use intervals, not a single number |
| Greedy nondeterminism | Batching, kernels and hardware can change results; repeat and record |
| Model/API version drift | Record endpoints, versions, dates; re-run if versions changed |
| Prompt/extraction variance | See [prompt sensitivity](prompt-sensitivity.md) |
| Task/item sampling | Treat tasks or domains as clusters; item counts overstate independence |

## Reporting Intervals

- Use the correct unit: cluster by task, domain or prompt family when items are not independent.
- For paired comparisons (same items, same prompts, same seeds), report the paired difference distribution or a paired bootstrap interval, not two separate intervals compared by eye.
- State what the interval covers: seed/run variability, task sampling, or both.
- Correct for multiple comparisons across tasks, metrics or variants; record how many were tested.

## Minimal Reporting Set

| Field | Why |
|---|---|
| Benchmark/task names and versions | Scores are version-specific |
| Model identity, endpoint/version, date | Prevents silent drift |
| Prompt template identifier and shot count | Makes the score reproducible |
| Decoding settings and number of runs | Enables variance interpretation |
| Scoring code version and normalization rules | Scores are implementation-specific |
| Item counts and independent cluster counts | Supports interval validity |
| Intervals or per-run distributions | Shows stability |
| Failure, timeout, refusal, truncation rates | Accuracy alone hides these |
| Compute/cost budget | Needed for matched comparison claims |
| Contamination status and method | See [contamination checks](contamination-checks.md) |

## Comparison Checklist

1. Same prompt template, extraction and scoring code across models.
2. Same shot counts, context limits, tools and safety filters.
3. Matched sampling and compute budgets, or an explicitly declared mismatch.
4. Paired comparison over tasks/seeds with an interval for the difference.
5. Negative, null and unstable results reported alongside improvements.

Do not convert a small unstable difference into a capability claim, and do not present "no statistically significant difference" as evidence of equivalence without an equivalence criterion.
