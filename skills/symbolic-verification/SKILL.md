---
name: symbolic-verification
description: Use when a concrete logical claim, proof certificate, or solver result requires soundness, completeness, or counterexample checking.
---

# Proof and Solver Result Verification

Check a bounded formal claim under explicit assumptions. Neural networks, GPUs, and language-model benchmarks are not required.

## Inputs

Formal or precise informal statement, axioms, domain restrictions, proof or solver certificate, checker/version if available, resource limit, reference results, and assigned outputs. A missing proof is a gap, not permission to invent a verified theorem.

## Method

1. Normalize quantifiers, types, boundary cases and assumptions. Distinguish a universal theorem from a result about a finite instance family.
2. Separate soundness, completeness and termination obligations. Record exactly which are claimed and which the submitted argument establishes.
3. Inspect inference steps and side conditions. For certificates, run only the assigned checker within authorized limits and retain version, command, exit status and diagnostics.
4. For SAT/SMT results, distinguish satisfiable, unsatisfiable, unknown, timeout and crash. Validate a model against the original formula or a refutation certificate where supported.
5. Seek small counterexamples to assumptions or unsupported generalization, without mistaking bounded testing for proof. Record the searched bounds explicitly.
6. Analyze complexity with stated input size, computational model and worst-case/average-case distinction. Do not turn empirical solver speed into an asymptotic proof.
7. Report proved, refuted, conditionally supported, or unresolved obligations separately.

## Outputs

An obligation-by-obligation verification report, certificate/checker evidence when actually available, counterexamples, and remaining assumptions. Store at assigned paths.

## Checks

A timeout never establishes unsatisfiability. Successful tests do not prove universal correctness. A certificate not checked is not a formal verification result. Independent checking replaces statistical intervals for deterministic proofs when appropriate.

Example: exhaustive Boolean search over n variables may establish correctness for each checked instance, while a general termination proof must justify finite enumeration for arbitrary finite n.

## Boundary

Return to the core with the report or missing proof/checker evidence. Do not dispatch other skills or agents, choose models, schedule searches, change project goals, promote claims to global findings, or edit global state.
