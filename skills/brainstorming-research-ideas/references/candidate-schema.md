# Candidate Schema, Ranking and Rejection Log

Structure the output so the core can judge it. Diversity first, evaluation second: generate candidates before ranking, and do not filter prematurely.

## Diverge

Aim for a broad candidate set before any filtering. Practical sources of breadth: scan for tensions, check what changed, probe two popular methods for failure modes, import one idea from an adjacent field, compose two existing techniques, and move each candidate up and down the abstraction ladder (see [ideation lenses](ideation-lenses.md)).

Record every candidate, including the ones that look weak. Rejected candidates are evidence of coverage and often recombine later.

## Candidate Row

| Field | Content |
|---|---|
| `id` | Stable identifier (for example `h7`) |
| Statement | One or two sentences, mechanism included |
| Mechanism | Why it should work, at the mechanism level |
| Prediction | Observable consequence that follows from the mechanism |
| Main alternative | Strongest competing explanation |
| Falsifier | Observation that would disconfirm this candidate |
| Nearest prior work | Closest supplied source and the gap to it |
| Cheapest discriminating test | Design only; not an authorization to execute |
| Confounds | What could produce the same observation for other reasons |
| Validation cost | Resources the test would need at a stated precision |
| Novelty status | Supported by reviewed sources, or unknown |

A candidate without a falsifier is not a research candidate; mark it as a topic and exclude it from ranking.

## Converge and Rank

Rank on five dimensions with ordinal judgments and reasons:

| Dimension | Question |
|---|---|
| Significance | Who is affected and how much, per supplied evidence |
| Evidence of a gap | Is the gap documented, or inferred from search absence? |
| Discriminability | Does the predicted observation differ from the main alternative? |
| Feasibility | Is the cheapest discriminating test affordable with stated resources? |
| Confounding risk | How easily could the result be explained away? |

Use ordinal ordering with written justifications. Do not invent precise novelty or impact scores; a fabricated numeric score is worse than an explicit qualitative ordering because it looks comparable across candidates.

Filters that remove a candidate: cannot be stated in the two-sentence form; no identifiable beneficiary; a simpler matched baseline would produce the same result; clearly infeasible under the stated budget.

## Rejection Log

| id | Rejected because | Would change the verdict if |
|---|---|---|
| h4 | Simpler matched baseline predicts the same effect | A baseline-comparison result is supplied |
| h9 | Falsifier depends on unavailable measurements | The measurement source is supplied |

## Coverage and Limits

- Missing literature is a limitation, not evidence of novelty; state what was not available.
- Unverified novelty: mark explicitly rather than asserting priority.
- Proposed tests are designs; execution requires a separate authorized task decided by the core.
- Return the shortlist plus rejected candidates and reasons. The core selects which candidate to pursue.
