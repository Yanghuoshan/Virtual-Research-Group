# Uncertainty, Multiplicity and Reporting

## Intervals before p-values

Every confirmatory comparison reports an effect size with an uncertainty interval at the pre-specified confidence level. p-values may appear but never stand alone; a p-value without an interval is an incomplete row.

- Interval method comes from `uncertainty_plan`: bootstrap (state resampling unit - it must match the analysis unit), analytic (state the distributional assumption), or permutation (state the exchangeability scope).
- Bootstrap resampling that ignores clusters inflates precision; resample the highest declared dependent unit.
- Report interval width honestly; an interval spanning the entire plausible range is a finding about power, not a failure to hide.

## Multiplicity

- The family is the declared set of confirmatory comparisons in the plan, whether or not all were reported interesting.
- Apply the pre-specified correction (none, Bonferroni, Holm, FDR) to that family. "None declared" is reported as uncorrected with a limitation line, so a reader can see the exposure.
- Selective reporting does not shrink the family: dropping a null comparison after seeing it still counts it in the denominator of whatever correction was declared.

## Effect sizes

- Report the estimand's natural scale first (accuracy points, milliseconds, dollars), then standardized measures where convention demands them.
- State the direction convention (higher is better?) once per table; ambiguity here has flipped conclusions in print.
- A tiny but significant effect with a huge n is reported as tiny; significance is not importance.

## Distinguish evidence states

| State | Correct phrasing |
|---|---|
| Interval excludes null | "Data are inconsistent with the null under these assumptions" |
| Interval includes null, wide | "Underpowered for this effect size; no claim either way" |
| Interval includes null, narrow | "Effect, if present, is smaller than X" |
| Assumptions violated | "No defensible test; diagnostics returned" |

## Summary table shape

One row per planned comparison, machine-readable:

```json
{"comparison": "cond-a vs cond-b", "estimand": "mean difference",
 "effect": 1.3, "interval": [0.2, 2.4], "level": 0.95,
 "multiplicity": "Holm, family of 4", "label": "confirmatory"}
```

Rows never blend author-reported and reviewer-computed values; author-reported numbers appear in separate rows with source locators. Exploratory computations live in a fenced section and never in this table.

## Reporting integrity

- No rounding that changes comparisons (report enough digits to reproduce the ordering).
- No trimming of "outlier" comparisons; outliers are data plus a declared policy or a limitation.
- Every table row cites the manifest tables and method well enough to be recomputed independently.
