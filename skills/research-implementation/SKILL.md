---
name: research-implementation
description: Use when a frozen design or accepted specification must be turned into working project code under src/ or run directories: writing modules, tests, and smoke checks, recording environments, without running experiments or interpreting results.
---

# Specification-Bound Research Implementation

Turn an accepted design into runnable, reviewable project code. This skill produces code and evidence of correctness; it does not run experiments, tune toward results, or decide what outcomes mean.

## Inputs

The frozen design, protocol draft, or specification with its recorded version, target interfaces or module boundaries, the required language and dependency constraints, the assigned output paths under `src/` or `experiments/{hypothesis-id}/runs/{run-id}/code/`, and acceptance criteria. A design that is still contested is a blocker, not an invitation to pick a side.

## Method

1. Restate the contract being implemented in one paragraph: inputs, outputs, invariants, and the acceptance checks the code must satisfy. Follow [implementation standards](references/implementation-standards.md).
2. Place reusable code under `src/` with a pinned version note, and run-specific code only under the assigned run directory. Never mix the two in one commit of code.
3. Write the module skeleton with explicit interfaces first; record assumptions the design leaves open as comments flagged `ASSUMPTION`, and return them in the output summary.
4. Implement in the smallest verifiable increments; each increment gets a smoke check that can fail. A step whose check cannot fail is decoration, not verification.
5. Record the environment manifest: language version, dependency versions, seeds, and platform notes. Code without a reproducible environment record is not evidence.
6. On any failure to meet the contract, stop and return a blocker with the failing check; do not silently broaden the design or substitute a different mechanism.

## Outputs

At the assigned paths: source modules, a test or smoke-check file with runnable commands, an environment manifest, and an implementation summary mapping each design requirement to the code and check that satisfies it, plus open assumptions.

## Checks

Every design requirement maps to code and to a check that ran; smoke checks fail deliberately on a broken build rather than passing vacuously; no hidden network calls or installs beyond the assigned channel; no result values are computed or reported - implementation stops at verified executability.

Example: a protocol requiring group-level splits must surface the split function with a test on a synthetic fixture, not an untested utility buried in a training loop.

## Boundary

Return to the core with code, checks, or exact blockers. Do not dispatch other skills or agents, select models, run experiments or training, tune toward observed results, update global findings/state, or advance phases. Executing the implemented code as an experiment is a separate core decision.

## Local References

- [Implementation standards](references/implementation-standards.md)
