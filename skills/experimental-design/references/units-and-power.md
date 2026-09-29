# Units, Dependence and Precision

Most invalid power claims come from counting the wrong units.

## Unit Worksheet

| Level | Questions |
|---|---|
| Sampling unit | What was drawn from the target population? |
| Assignment/randomization unit | What was randomized: item, subject, cluster, run? |
| Measurement unit | What is one observation in the raw data? |
| Analysis unit | What is treated as independent in the model? |
| Claim unit | What does the conclusion generalize to? |

Misalignment between claim unit and analysis unit invalidates the interval. Repeated seeds measure training variability, not population sampling.

## Dependence

| Pattern | Handling |
|---|---|
| Clusters (subjects, sites, devices) | Split at the cluster level; use cluster-aware intervals |
| Repeated measures | Model within-unit correlation; avoid pseudoreplication |
| Time series / temporal dependence | Block or account for autocorrelation; avoid random splits of adjacent records |
| Shared datasets or duplicates | Group correlated records; count distinct sources |
| Seeds/runs | Report as run variability, separate from sampling variability |

## Effect Size, Variance and Precision

1. State the smallest effect size that would matter for the claim, in the outcome's units.
2. State variance and dependence assumptions; mark each as assumed or measured.
3. Compute the implied sample/cluster count for the target power or interval width, and report sensitivity to uncertain assumptions.
4. Report feasibility against the budget: if the implied count exceeds resources, return a reduced-scope or pilot design with explicit limits.
5. Missing variance or dependence inputs: return a conditional calculation plan and a pilot design, not an invented power guarantee.

## Reporting Table

| Quantity | Source | Status |
|---|---|---|
| Meaningful effect | Assigned criterion | Stated |
| Variance assumption | Prior measurements | Assumed |
| Cluster ICC / dependence | Unknown | Assumption needed; sensitivity reported |
| Implied n (clusters) | Calculation | Conditional on assumptions above |
| Budget feasibility | Resource limits | Feasible / not feasible |

No fixed number of seeds or runs guarantees adequacy. Precision comes from independent units, not repetition of the same dependent ones.
