---
name: code-model-evaluation
description: Use when code generation or program-repair results need pass@k estimator, execution-sandbox, oracle-quality, or contamination auditing.
---

# Code Model Evaluation Audit

Check functional-correctness evaluation of generated code: estimator, execution environment, tests and provenance. Executing model-generated code is not part of this task.

## Inputs

Model outputs with samples per task, benchmark/task definitions and versions, unit tests or other oracles, execution environment description, sampling parameters (k, temperature), scoring scripts, language/runtime versions, baseline numbers, resource limits, and assigned outputs. Absent predictions or tests are gaps, not permission to generate replacements.

## Method

1. Identify the claim: pass@1, pass@k, strict/average accuracy, repair success, or security/safety behavior. Different estimators and sample budgets support different claims.
2. Verify the estimator with [estimators](references/estimators.md): use the unbiased estimator for pass@k over n samples with c correct, `1 - C(n-c, k)/C(n, k)`, not "any correct sample" or averaged per-sample accuracy. Report n, k, temperature and deduplicated identical samples. Small n with large k produces wide, unstable intervals.
3. Audit the execution sandbox against the [sandbox checklist](references/sandbox-checklist.md): runtime/language/package versions, deterministic environment, timeouts, memory/CPU limits, network and filesystem isolation, cleanup, flaky or nondeterministic tests, and crash/timeout versus wrong-answer classification. Record the execution policy actually used; unverified execution supports no correctness claim.
4. Audit the oracle and provenance with [oracle and provenance](references/oracle-and-provenance.md): test coverage and edge cases, weak or tautological tests, oracle leakage into prompts, dependence on reference solutions, hidden versus visible tests, and validity of cross-language translation. Weak tests can make incorrect code pass; report that as an oracle limitation, not model success.
5. Audit contamination and provenance: benchmark repositories/solutions likely present in training data, licenses and attribution, duplicate or near-duplicate tasks across splits, prompt context differences (signature, docstring, imports), and benchmark version drift.
6. Check comparison validity: matched k, temperature, sample budget, prompt template, context, tool/compiler availability and scoring scripts. Report compile/runtime error breakdowns and cost alongside pass rates.
7. Check statistics: task counts (often small), per-task clustering, bootstrap or exact intervals for pass@k, paired comparison across tasks, and effect sizes. Report negative results and unstable estimates explicitly.

## Outputs

An estimator and sandbox audit, oracle/leakage findings, a task-level defect list with severity and affected claim, and pass@k computed only from supplied samples/tests. Include n, k, intervals, environment versions and unresolved limitations at assigned paths.

## Checks

Do not execute generated code, install packages, or run test suites; recommend a separate authorized execution assignment in an isolated sandbox. Do not report averaged per-sample accuracy as pass@k. Do not compare pass rates computed with different k, budgets, prompts or environments.

Example: 20 samples with 7 correct gives unbiased pass@10 of `1 - C(13,10)/C(20,10)` ≈ 0.998, which is nearly uninformative and unstable; report n, k, the interval and the oracle limits instead of treating it as a precise success rate.

## Local References

- [Estimators, sample budgets and intervals](references/estimators.md)
- [Execution sandbox checklist](references/sandbox-checklist.md)
- [Test oracle quality and provenance](references/oracle-and-provenance.md)

These define procedures for this skill only. They do not authorize executing generated code, installing packages or running test suites.

## Boundary

Return to the core with the report or blockers. Do not dispatch other skills or agents, select models, run inference or test suites, schedule evaluations, acquire compute or repositories, edit global findings/state, or advance phases.
