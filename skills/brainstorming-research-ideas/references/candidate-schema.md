# Candidate Schema, Ranking and Rejection Log

Structure the output so the core can judge it. Diversity first, evaluation second: generate candidates before ranking, and do not filter prematurely. The gap, question, route and contribution judgments are described in the framework reference `references/idea-exploration.md`.

## Diverge

Aim for a broad candidate set before any filtering. Practical sources of breadth: scan for tensions, check what changed, probe two popular methods for failure modes, import one idea from an adjacent field, compose two existing techniques, and move each candidate up and down the abstraction ladder (see [ideation lenses](ideation-lenses.md)). Include at least one theory-oriented and one strong-simple-baseline candidate so that non-incremental and deflationary explanations are both represented.

Record every candidate, including the ones that look weak. Rejected candidates are evidence of coverage and often recombine later.

## Candidate Row

| Field | Content |
|---|---|
| `id` | Stable identifier (for example `h7`) |
| Statement | One or two sentences, mechanism included |
| Contribution type | Theoretical, methodological, empirical/evaluative, capability, or community resource |
| Gap evidence | Documented limitation, contradiction, or boundary failure with a source; not a search absence |
| Mechanism | Why it should work, at the mechanism level |
| New capability or explanation | What becomes possible or explicable that is not possible today |
| Prediction | Observable consequence that follows from the mechanism |
| Main alternative | Strongest competing explanation |
| Falsifier | Observation that would disconfirm this candidate |
| Nearest prior work | Closest supplied source |
| Real difference from nearest work | Why the difference cannot be reproduced by scale, data, tuning, or swapping an existing component |
| Decisive evidence | The single comparison, proof obligation or counterexample that would most discriminate this candidate |
| Expected impact | Which assumptions, methods, capabilities or evaluation practices could change, on what evidence |
| Confounds | What could produce the same observation for other reasons |
| Validation cost | Resources the test would need at a stated precision |
| Novelty status | Supported by reviewed sources, or unknown |

A candidate without a falsifier is not a research candidate; mark it as a topic and exclude it from ranking. A candidate may lack evidence for its novelty or impact as long as those are labeled unknown rather than asserted.

## Converge and Rank

Rank on two separate axes with ordinal judgments and reasons. Keep them separate so that cost never silently stands in for value.

| Axis | Dimension | Question |
|---|---|---|
| Potential | Significance | Who is affected and how much, per supplied evidence |
| Potential | Evidence of a gap | Is the gap documented, or inferred from search absence? |
| Potential | Discriminability | Does the predicted observation differ from the main alternative? |
| Potential | Unique-claim strength | Does the new capability or explanation exceed what a matched baseline or nearest work already gives? |
| Cost and risk | Feasibility | Is the cheapest discriminating test affordable with stated resources? |
| Cost and risk | Confounding risk | How easily could the result be explained away? |
| Cost and risk | Absorption risk | Could a stronger simple baseline or more scale reproduce the claimed contribution? |

Use ordinal ordering with written justifications. Do not invent precise novelty or impact scores; a fabricated numeric score is worse than an explicit qualitative ordering because it looks comparable across candidates. State the potential and cost judgments separately even when they disagree.

Filters that remove a candidate: cannot be stated in the two-sentence form; no identifiable beneficiary; a simpler matched baseline would produce the same result; the claim reduces to a rename or a stack of components with no necessary part. **High validation cost is not by itself a removal filter**: move the candidate to a conditional tier, record the minimum discriminating step, the condition to continue and the condition to stop, and leave the decision to the core.

## Rejection Log

| id | Rejected because | Would change the verdict if |
|---|---|---|
| h4 | Simpler matched baseline predicts the same effect | A baseline-comparison result is supplied |
| h9 | Falsifier depends on unavailable measurements | The measurement source is supplied |
| h12 | Contribution is a rename of prior work | A mechanism-level difference from the prior work is shown |

A conditional candidate is not a rejected candidate: record why it was deferred and what would promote it.

## Coverage and Limits

- Missing literature is a limitation, not evidence of novelty; state what was not available.
- Unverified novelty and impact: mark explicitly rather than asserting priority or significance.
- Proposed tests are designs; execution requires a separate authorized task decided by the core.
- Return the shortlist plus rejected and deferred candidates with reasons. The core selects which candidate to pursue.
