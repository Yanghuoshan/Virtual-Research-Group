# Risk of Bias and Study-Quality Assessment

Assess risk of bias domain by domain and justify every judgment with a locator. Do not collapse domains into a single numeric score; a total score hides which claim is actually threatened.

## Judgment Scale

| Judgment | Meaning |
|---|---|
| Low | The design and reporting make the threatened bias unlikely for the claim in question |
| Some concerns | Plausible bias or insufficient detail; state what would resolve it |
| High | The design or reporting could plausibly produce the observed result for other reasons |
| Unclear | Not reported or not assessable from supplied material |

"Unclear" is never "low". A high-risk domain does not automatically invalidate the study; report which claims depend on that domain and how.

## Common Domains

| Domain | Typical questions |
|---|---|
| Selection of units | Are splits, clusters or subjects defined so that the analysis unit matches the claim? Are correlated or duplicated units grouped? |
| Confounding and comparability | Are comparison conditions matched on data, preprocessing, compute, tuning and prompt budgets? |
| Protocol fidelity | Was the declared procedure followed; were deviations recorded? |
| Measurement of outcomes | Are metric definitions, units, thresholds and aggregation declared and consistent across comparisons? |
| Leakage and contamination | Did test items, labels, statistics or exemplars enter training, model selection or prompt selection? |
| Missing data and failures | Are failed runs, timeouts, truncations and dropped cases reported and handled consistently? |
| Selective reporting | Were outcomes, metrics or subsets switched after results were seen; are null results reported? |
| Analysis-unit errors | Pseudoreplication, clustering, repeated seeds counted as independent samples, multiple comparisons uncorrected |
| Optional stopping | Was stopping or extension decided after inspecting outcomes? |
| Generalizability | Do population, dataset, language, scale and environment match the claim's scope? |
| Reproducibility | Are code, data, environment, seeds and versions available; is the procedure runnable from supplied artifacts? |
| Independence | Are reported replications genuinely independent, or shared data/author groups/overlapping benchmarks? |
| Conflicts and provenance | Funding or conflicts if reported; licensing and provenance of data and models |

## ML/AI-Specific Failure Modes

- Train/test contamination or leakage: test items, labels, statistics or exemplars reaching training, model selection or prompt selection; benchmark items present in pretraining data; ignored canary strings.
- Hyperparameters, thresholds, prompts or checkpoints selected on the evaluated split.
- Weak or unmatched baselines; unequal tuning budgets or parameter counts.
- Single-seed or single-run results reported as stable estimates; unreported variance.
- Small benchmarks where item counts and task clustering make intervals wide.
- Metric implementation differences across papers compared as one number.
- Reported improvements that depend on preprocessing, tokenization or context length differences.
- Claims transferred across model families, scales or languages without evidence.

## Independence of Reports

Assess a study once, with its versions linked. Multiple reports of the same experiment are not independent confirmations. Shared benchmarks, datasets or author groups limit independence even when papers differ.

## Output Table

| Study/report | Domain | Judgment | Justification + locator | Claims affected |
|---|---|---|---|---|
| S1 (v2) | Selection of units | Some concerns | Splits by graph, not source; §3.2 | C1, C3 |
| S1 (v2) | Leakage | Low | Edge-level split verified; Table 2 | C1 |

Add an overall confidence per claim, not per study, using the certainty labels in [extraction and reporting](extraction-and-reporting.md), and list the domains that drive it. Where a bias judgment would change the synthesis decision (for example excluding a study from pooling), return that as a recommendation to the core rather than silently applying it.
