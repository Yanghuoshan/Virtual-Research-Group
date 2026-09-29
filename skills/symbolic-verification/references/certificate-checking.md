# Certificate and Checker Evidence

A certificate that was not checked is not a verification result. Record the checker, the invocation and the outcome.

## Result Vocabulary

| Outcome | Meaning | Reporting |
|---|---|---|
| Proved | Checker accepted the proof/obligation | Record version, command and exit status |
| Refuted | Counterexample or contradiction found | Include the witness and validate it |
| satisfiable / model | Witness for an existential claim | Validate the witness against the original formula |
| unsatisfiable | Refutation derived | Report whether a proof certificate was produced and checked |
| unknown | Resource or logic limitation | Not a refutation; state the limit |
| timeout | Limit reached | Report the limit; never read it as unsatisfiability |
| crash / error | Tool failure | Record diagnostics; no conclusion |

## Checker Record

| Field | Content |
|---|---|
| Checker/solver name and version | Exact version, build, and logic/theory |
| Command and options | Full invocation, including time/memory limits |
| Environment | OS, runtime, hardware limits |
| Input files | Hashes and paths of formula/proof/certificate |
| Output | Exit status, stdout/stderr, diagnostics |
| Resource use | Time, memory, limits reached |

## Validation Rules

1. Prefer independently checkable certificates over trusting a solver's printout.
2. Validate a model/witness against the original statement; a witness for a transformed formula may not satisfy the original.
3. Re-run with a different checker version or a second checker when the acceptance criteria demand independent checking.
4. Distinguish "no counterexample found within bounds" from "no counterexample exists".
5. Record translated or normalized formulas; the checked statement may differ from the claimed one.

Run checkers only within the authorized assignment and resource limits; this skill does not launch long searches.
