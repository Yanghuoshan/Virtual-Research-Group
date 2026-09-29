# Extraction Schema, Synthesis Rules and Reporting

Extraction turns screened studies into comparable evidence; reporting states what the review can and cannot support.

## Extraction Table Schema

| Field | Notes |
|---|---|
| Study/report ID and version | Which version was extracted |
| Source locator | Page, section, table, figure or file for each value |
| Value origin | `author-reported` or `reviewer-derived` for each substantive value |
| Design and setting | Empirical benchmark, observational study, proof, simulation |
| Population / data | Dataset name, version, split identity, size, cluster structure |
| Sample and cluster counts | Number of units at the analysis level, not raw rows |
| Method / intervention | Model or procedure, with configuration summary |
| Comparison / baseline | Baselines, ablations, tuning and compute budgets |
| Outcome definition | Metric name, direction, units, thresholds, aggregation |
| Effect and uncertainty | Point estimate, interval definition, number of seeds/runs |
| Missing data and failures | Dropouts, failed runs, truncations, handling rule |
| Assumptions and limitations | Author-stated limits plus assessor-observed limits |
| Provenance | Data/model licenses and sources, if reported |
| Extractor and date | Audit trail |

Store the extraction table at an assigned path. Every substantive value needs a locator; values without locators are gaps, not findings.

## Values, Units and Missing Data

- Keep original units and record any conversion formula; mark derived values as derived.
- Distinguish "not reported" from "not applicable"; do not impute from memory or from another paper's summary of the study.
- Intervals must state what they cover (confidence, prediction, seed variance, bootstrap) and the number of runs behind them.
- When a paper reports several variants, extract the variant matching the eligibility criteria and note the others.

## When Pooling Is and Is Not Defensible

Pool estimates only when all of the following hold; otherwise use structured or narrative synthesis:

1. The same estimand and outcome definition, in comparable units.
2. Comparable study designs and analysis units.
3. Risks of bias that do not threaten the pooled claim. Where they might, propose a sensitivity analysis to the core rather than applying the exclusion unilaterally.
4. Heterogeneity assessed and explained by pre-specified subgroups (dataset scale, domain, supervision, compute, language).
5. Enough studies to make the pooled interval meaningful; a pool of two heterogeneous studies is usually narrative evidence.

Report heterogeneity sources and direction of disagreement. Distinguish statistical heterogeneity from methodological incompatibility; the latter is not fixed by a random-effects model.

## Certainty Language per Claim

| Label | Use when |
|---|---|
| Supported | Multiple compatible studies, low/some-concern bias, consistent direction, adequate precision |
| Limited | Few studies, moderate concerns, or wide intervals |
| Conflicting | Compatible studies disagree and sources of disagreement are not resolved |
| Insufficient | Too few or too biased studies to support any direction |

Avoid "the literature shows" when the basis is a handful of studies or a single corpus. State absence of evidence separately from evidence of absence.

## Reporting Checklist

- Question, eligibility criteria and any amendments.
- Sources, interfaces, queries, run dates and raw-record paths (or the unexecuted-plan label).
- Counts: retrieved, deduplicated, screened, excluded with reasons, unobtainable, included; "not performed" where applicable.
- Extraction table with locators.
- Risk-of-bias table per study/domain.
- Synthesis method, pooling decision and heterogeneity assessment.
- Coverage limitations and conflicting findings.
- Unresolved gaps and blockers returned to the core.

## Coverage-Limit Phrasing

- "Supplied-corpus review of 33 studies; no database search was performed, so coverage is limited to the supplied material."
- "Two preprint-server searches were executed; venue-indexed literature and grey literature were not covered."
- "Twelve full texts were unobtainable; they are reported as unobtainable and are not treated as negative evidence."
- "Screening was performed by a single reviewer; dual independent screening was not performed."

Keep every claim's scope inside these statements. A review is a bounded argument, not a survey of everything published.
