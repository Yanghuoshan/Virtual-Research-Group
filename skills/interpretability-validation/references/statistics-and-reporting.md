# Statistics, Labeling and Reporting

Interpretability studies search over many features, layers and examples. Multiplicity and labeling quality decide whether findings survive.

## Multiplicity and Search Reporting

The dominant threat in feature studies is usually multiplicity: report the search size and account for it before interpreting any selected finding.

| Field | Why |
|---|---|
| Features/layers/sites searched | Denominator for selection effects |
| Selection rule | Threshold, top-k, or manual selection |
| Held-out features and examples | Whether the finding generalizes |
| Correction method | How the search was accounted for |
| Effect sizes and intervals | Distinguishes large effects from marginal ones |

Selecting the best of thousands of features by top activation and then reporting it as a discovery is a selection effect: record the search size and confirm on held-out features and examples.

## Per-Example Variance

- Report the distribution across examples, not only the mean effect.
- Report how many examples support and contradict the claim.
- Avoid conclusions resting on a handful of demonstrations; cherry-picked examples are illustrations, not evidence.

## Labeling Quality

| Aspect | Requirement |
|---|---|
| Rubric | Written before labeling; what counts as an instance of the concept |
| Annotators | Number and independence; report agreement |
| Agreement | Report the statistic used and its value; low agreement weakens descriptive claims |
| Blinding | Labelers blinded to the hypothesis where feasible |
| Automated judges | Report judge identity/version, prompt and known biases (verbosity, position, self-preference) |

Treat automated judge scores as measurements with their own validity limits, not as ground truth.

## Replication

- Cross-model: does the feature or circuit appear in another model or seed?
- Cross-dataset: does it hold on inputs outside the original distribution?
- Cross-metric: does the conclusion survive an alternative behavioral metric?

## Minimal Report

Claim type; artifacts and versions inspected; baselines/controls and their results; searched features/layers with correction; per-example distribution; labeling agreement or judge setup; replication status; and the strongest claim actually supported.
