# Implementation Standards

Procedures for the research-implementation skill only. They refine code quality; they never authorize running experiments, installing unassigned packages, or changing the design.

## Contract Restatement

- List every requirement from the design as a numbered check before writing code.
- Mark requirements that cannot be tested mechanically; propose the human check the core must perform.
- Distinguish "the design says" from "the implementer prefers"; the second class is returned as a suggestion, never silently applied.

## Code Placement

- Reusable, versioned code belongs in `src/` with a note of the version it serves.
- One run's snapshot belongs in `runs/{run-id}/code/`; it is copied or pinned there, never imported from a mutable location.
- No file outside the assigned output scope is created or modified.

## Verification Discipline

- Every increment ships with a check that can fail: a unit test, an assertion script, or a documented manual probe with expected output.
- Deterministic fixtures over live data; fixed seeds; no timing-dependent assertions.
- A check that cannot fail is reported as such and does not count toward acceptance.

## Environment Recording

- Record interpreter version, dependency versions with lock references, platform, and seeds in the manifest.
- Any dependency added beyond the design is a blocker returned to the core, not a silent `install`.

## Failure Reporting

- On contract violation, report the failing check, the smallest reproducing input, and the step that failed. Do not patch around the design or "fix" the protocol.
