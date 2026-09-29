# Test Oracle Quality and Provenance

Functional correctness is only as strong as the tests that judge it. Audit the oracle and the data provenance before accepting pass rates.

## Oracle Quality Rubric

Strength, independence and coverage decide whether a pass rate means anything; judge all three before accepting the number.

| Dimension | Questions | Weak signal |
|---|---|---|
| Coverage | Do tests exercise branches, edge cases and error paths? | Only a happy-path example |
| Strength | Would a wrong-but-plausible implementation pass? | Assertions on type or non-emptiness only |
| Independence | Are tests derived from the reference solution? | Tests copied from the reference implementation |
| Determinism | Do tests pass reliably on the reference solution? | Flaky timing or ordering assertions |
| Visibility | Which tests are visible to the model? | Hidden/visible split undocumented |
| Oracle leakage | Do prompts or docstrings contain the assertions or solution? | Tests quoted in the prompt |
| Language validity | For translated benchmarks, are semantics preserved? | Literal translation breaking idioms |

Report weak oracles as a limitation that can inflate correctness, not as evidence of model capability.

## Failure Taxonomy

| Class | Meaning |
|---|---|
| Wrong answer | Runs and fails a meaningful assertion |
| Compile/build error | Does not build under the declared toolchain |
| Runtime error | Crashes or raises |
| Timeout | Exceeds the declared limit |
| Sandbox violation | Attempted disallowed access; treat as a safety-relevant finding |
| Non-deterministic | Result varies across repeated runs |

Keep these classes separate; merging them hides whether failures are capability or environment issues.

## Provenance and Contamination

| Check | Method |
|---|---|
| Benchmark in training data | Compare task sources and solutions against known training corpora; report as uncertain when unknown |
| Duplicate tasks across splits | Normalize and compare task statements and tests |
| Version drift | Record benchmark version and task-set hash; tasks change between releases |
| Licensing and attribution | Record dataset license, source repository and attribution requirements |
| Repository availability | Note archived or removed repositories that prevent verification |

## Minimal Report

Benchmark/version, task count, `n`/`k`/temperature, estimator and interval, environment identity, failure taxonomy counts, oracle limitations, contamination status, and unresolved verification gaps.
