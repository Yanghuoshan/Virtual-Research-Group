# Estimators, Sample Budgets and Intervals

Use the estimator that matches the claim. The most common error is reporting a per-sample or any-correct quantity and calling it pass@k.

## Unbiased pass@k

With `n` samples per task of which `c` pass:

```text
pass@k = 1 - C(n - c, k) / C(n, k)
```

Report `n`, `k`, `c` per task, and aggregate across tasks as the acceptance criteria require (usually the mean over tasks).

## Worked Numbers

| n | c | k | Unbiased pass@k | Naive any-correct | Reading |
|---|---|---|---|---|---|
| 20 | 7 | 1 | 0.35 | 1.0 | Any-correct massively overstates single-attempt success |
| 20 | 7 | 10 | ≈0.998 | 1.0 | Large k with small n is nearly uninformative |
| 100 | 40 | 10 | ≈0.998 | 1.0 | Still dominated by the sample budget |
| 100 | 40 | 1 | 0.40 | 1.0 | Stable and interpretable |

Interpretation: the unbiased estimator rises mechanically with `k`. It answers "is at least one of k samples correct", not "how good is the model". Prefer small `k` with a large `n`, and always report the interval.

## Other Estimators

| Quantity | Definition | Use |
|---|---|---|
| pass@1 | Unbiased estimator with k=1, or the fraction of passing samples | Single-attempt quality |
| Average/strict accuracy | Fraction of samples correct, averaged per task | Sample-level quality; do not label it pass@k |
| Success rate per task | Fraction of tasks with at least one correct sample | Any-correct; state it explicitly |
| Bootstrap interval | Resample tasks (or samples within task) for a task-level interval | Stability of the estimate |

## Sample Budget Guidance

Report variance across tasks, not only across samples: task-level clustering usually dominates the interval width.

- Choose `k` from the claim; report `n` and the resulting interval.
- Deduplicate identical samples before counting; duplicated samples inflate `c`.
- Small task sets (tens of tasks) give wide intervals even with many samples per task.
- Task-level clustering means the number of tasks, not samples, dominates the interval width.
- Report negative results and unstable estimates rather than rounding them into a headline number.
