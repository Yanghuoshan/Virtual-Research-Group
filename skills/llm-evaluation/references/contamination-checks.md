# Contamination and Held-Out Checks

Contamination means evaluation items, labels, statistics or exemplars reached training, fine-tuning, selection or prompting. Report the method actually used; an unresolved question stays a limitation.

## What to Check

| Check | Method | Typical limit |
|---|---|---|
| Exact and near overlap | Normalize text, compare n-gram overlap between evaluation items and training/fine-tuning data | Requires the training corpus or a documented proxy; often unavailable |
| Canary strings | Search training data for benchmark canaries or GUID markers | Only present in benchmarks published with canaries |
| Membership probing | Loss/perplexity or membership-inference style probes | Probabilistic; disagreement between methods is common |
| Paraphrase and translation | Check paraphrased or translated versions of items | Recall depends on the paraphrase generator |
| Temporal cutoff | Compare benchmark release date with the model's training cutoff | Cutoff dates are frequently approximate |
| Split integrity | Duplicates or near-duplicates across train/validation/test | Cheap and often decisive; always perform it |
| Exemplar provenance | Verify few-shot exemplars do not come from the evaluated split | Fully checkable from supplied prompts |
| Leaderboard or test-set tuning | Look for selection, threshold or prompt choices made on the reported split | Detectable from the protocol history |

## Procedure

1. Inventory what is actually available: training corpus, data sheet, cutoff date, benchmark canaries, prompt exemplars, split manifests.
2. Run the cheapest decisive checks first: split integrity, exemplar provenance, exact overlap.
3. Run probabilistic checks only with their assumptions stated, and report disagreement between methods as a limitation.
4. Record item counts examined, overlap counts, thresholds, tool versions and raw outputs at assigned paths.
5. Map findings to affected claims: a contaminated subset may invalidate one task's score and leave another intact.

## Reporting

| Situation | Wording |
|---|---|
| Checked, no overlap found | "Exact n-gram overlap checked against the supplied corpus: 0 of N items; method and thresholds recorded." |
| Probabilistic evidence | "Membership probing suggests exposure for an estimated subset; estimate and method limits recorded." |
| Not checkable | "Training data unavailable; pretraining exposure unknown and not claimed clean." |
| Subset affected | "Contamination confirmed for task X (k items); claims depending on X are unsupported." |

Never write "contamination-free" without naming the check that supports it. Unknown is not clean, and a clean canary check does not rule out paraphrase-level exposure.
