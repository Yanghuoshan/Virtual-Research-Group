---
name: llm-evaluation
description: Use when language-model benchmark results, prompts, or evaluation protocols need contamination, prompt-sensitivity, variance, or reporting audits.
---

# LLM Benchmark Evaluation Audit

Check the validity of a supplied language-model evaluation: protocol, prompts, splits, decoding and reported numbers. Running a new benchmark or fine-tuning is not part of this task.

## Inputs

Benchmark/task names and versions, split or held-out definitions and item counts, prompt templates and shot counts, exemplar sources, decoding parameters, model/API/harness versions, prediction or log files, scoring/normalization code, baseline/reference numbers, cost or resource limits, and assigned outputs. Missing items are gaps, not defaults to assume.

## Method

1. Classify the claim: capability, model comparison, scaling/efficiency, safety, or agentic outcome. Each has different validity conditions; one aggregate score cannot support all of them.
2. Audit contamination and held-out integrity with [contamination checks](references/contamination-checks.md): overlap with pretraining/fine-tuning data, benchmark membership and canary strings, near-duplicates or paraphrases across splits, reuse of items in validation or prompt exemplars, and public-leaderboard tuning. State unresolved exposure as a limitation; an unknown is not a clean result.
3. Audit prompt and formatting sensitivity with [prompt sensitivity](references/prompt-sensitivity.md): instruction versus completion format, chat template and tokenization, number and order of few-shot exemplars, exemplar provenance, answer extraction/normalization, stop criteria, truncation, and option/position bias. Report variation across template variants, not the best single prompt.
4. Audit decoding and seed variance with [variance and reporting](references/variance-and-reporting.md): greedy versus sampling, temperature/top-p, number of samples, batching or kernel nondeterminism, model/API version drift, retries and rate-limit truncation. Require repeated runs and report distributions or intervals; one run is not a stable estimate.
5. Check scoring and aggregation: exact match versus normalized/fuzzy match, logprob or likelihood scoring, per-task versus macro/micro aggregation, subgroup and length breakdowns, refusal/abstention and truncation handling, and judge-based scoring with its position/verbosity/self-preference biases. Do not compare scores from different scoring code or harness versions as equivalent.
6. Check comparison validity: matched prompt templates, shot counts, sampling budgets, token/compute budgets, context limits, tool availability, safety filters and model versions. Report cost, timeout and failure rates alongside accuracy.
7. Check statistics and reporting: item counts and independent task counts, clustering by task or domain, paired comparisons across tasks/seeds, multiple comparisons, intervals and effect sizes. Distinguish better-than-zero from better-than-baseline, and report negative or null results.

## Outputs

A protocol/evidence audit, a task-level defect list with severity and affected claim, and measurements only for supplied prediction/log files. Include versions, templates, item counts, intervals, unresolved contamination questions and coverage limits at assigned paths.

## Checks

Do not tune prompts, exemplars or models on evaluated items; that is evaluation-set overfitting, not capability. Do not claim contamination-free without a documented check. Do not mix harness versions, scoring implementations or budgets within one comparison.

Example: a 2-point gain from one greedy run on 500 items, with unmatched prompt templates and unknown pretraining overlap, supports a bounded observed difference, not a capability claim.

## Local References

- [Contamination and held-out checks](references/contamination-checks.md)
- [Prompt and formatting sensitivity](references/prompt-sensitivity.md)
- [Variance, statistics and reporting](references/variance-and-reporting.md)

These define procedures for this skill only. They do not authorize retrieval, benchmark execution or access to external services.

## Boundary

Return to the core with the report or blockers. Do not dispatch other skills or agents, select models, run benchmarks or inference, schedule evaluations, acquire API access or budget, edit global findings/state, or advance phases. Executing an evaluation requires a separate authorized experiment assignment.
