# Obligation Mapping and Bounded Search

Map the claimed result onto explicit obligations, then report which are discharged. Every claim should be mapped to soundness, completeness and termination obligations before any verdict is given, even when only one is claimed.

## Obligation Types

| Obligation | Question | Typical evidence |
|---|---|---|
| Soundness | Does every derived/claimed result follow from the assumptions? | Checked proof or certificate |
| Completeness | Does the method find every instance/solution it claims to? | Coverage argument, checked certificate |
| Termination | Does it always halt? | Ranking function, measure, or bounded proof |
| Correctness for instances | Holds for a finite instance family | Exhaustive or bounded check with reported bounds |
| Complexity claim | Cost under a stated model | Analysis with stated model and input size |

Record which obligations are claimed and which the submitted argument actually establishes; a result can be sound without being complete.

## Assumption Ledger

| Item | Content |
|---|---|
| Axioms and definitions | Exact statements |
| Domain restrictions | Types, finiteness, non-emptiness, side conditions |
| Quantifier scope | Universal vs existential, and over what domain |
| Boundary cases | Empty structure, zero, identity, degenerate inputs |
| Translated statement | The form actually checked, if different |

## Bounded Search as Evidence

- State the search bounds (size, depth, variable count, time).
- Report found counterexamples with the witness and the bound at which they appear.
- Bounded testing supports "holds for all checked instances up to N", not the universal claim.
- Record whether the search space was exhausted for those bounds.

## Complexity and Empirics

- Distinguish worst case, average case under a stated distribution, and observed runtime.
- State the computational model and input size parameter.
- Do not convert measured solver speed into an asymptotic claim.

## Reporting Table

| Obligation | Claimed | Evidence | Status |
|---|---|---|---|
| Soundness | Yes | Checked certificate, version 2.1 | Discharged |
| Completeness | Yes | Not addressed | Unresolved |
| Termination | No | — | Not claimed |
