# Prompt and Formatting Sensitivity

A benchmark score is a property of the model **and** the prompt pipeline. Report variation across variants, not the best template found.

## Variant Matrix

| Factor | Variants to compare |
|---|---|
| Instruction format | Zero-shot instruction, few-shot, chat template, completion-style |
| Shot count and order | 0, 1, 2, 5 shots; permuted exemplar order |
| Exemplar provenance | From a permitted pool; never from the evaluated split |
| Answer extraction | Regex, normalized match, JSON field, verbalized answer, logprob choice |
| Normalization | Case, whitespace, punctuation, units, stopword handling |
| Option/position order | Permuted multiple-choice options; rotated candidate order |
| Context and truncation | Long inputs, truncation policy, retrieved-context placement |
| System prompt and safety filters | Present/absent; identical across compared models |

## Running the Check

1. Pre-specify the variants and the number of runs per variant before looking at results.
2. Hold decoding fixed while varying the prompt; hold the prompt fixed while varying decoding.
3. Record the score for every variant, plus failure/parse rates, not just accuracy.
4. Report the range or distribution across variants and identify the claims that survive the worst variant.
5. If the ranking between models flips across variants, report that as instability of the comparison rather than a winner.

## Anti-Patterns

- Selecting or editing prompts while looking at test items: this is evaluation-set overfitting, not capability.
- Reporting only the best template, or a template tuned per model.
- Using exemplars drawn from the evaluated split.
- Comparing models with different templates, chat formats or extraction code and attributing the difference to the model.
- Treating a parse-failure rate that differs across models as a neutral detail.

## Minimal Report

| Field | Content |
|---|---|
| Variants | List with identifiers |
| Decoding | Fixed settings held during the prompt sweep |
| Scores | Per-variant score, parse/failure rate |
| Spread | Range or interval across variants |
| Affected claims | Which claims hold under all variants, and which do not |
