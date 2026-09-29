# Design Catalog and Selection Rules

Choose the design that can answer the question, then state what it cannot answer. Drafts are proposals; the core approves and freezes them. A factorial design costs power for every added factor, so use it only when interactions are part of the question.

## Catalog

| Design | Answers | Limits |
|---|---|---|
| Parallel randomized comparison | Average effect under randomization | Requires feasible randomization and adequate units |
| Paired/blocked design | Effect with nuisance variation removed | Requires defensible pairing and no carryover |
| Factorial design | Main effects and interactions | Combinatorial cost; interactions need power |
| Ablation sequence | Contribution of components | Order-dependent; does not prove sufficiency |
| Held-out/holdout-family validation | Generalization to unseen groups | Requires group identifiers and honest separation |
| Cross-validation | Model selection stability | Repeated reuse of data; not an unbiased final estimate |
| Dose-response or scaling sweep | Shape of the relationship | Confounded with resource or time |
| Quasi-experimental / observational comparison | Association under stated assumptions | Confounding remains; causal language limited |
| Pilot or feasibility study | Variance estimates, procedure checks | Not evidence for the main effect |
| Proof obligation (theoretical) | Soundness/completeness under axioms | Requires checking, not empirical runs |

## Selection Rules

1. Start from the falsifier: which result would disconfirm the hypothesis under this design?
2. Match the design to the estimand, not to convenience or available tooling.
3. Prefer the simplest design that can answer the question; added factors cost power and clarity.
4. Pre-specify what will be treated as confirmatory versus exploratory.
5. State the design's blind spots in the draft; a design that cannot fail is not a test.

## Anti-Patterns

- Using cross-validation results as the final generalization estimate.
- Ablations ordered by expected outcome, then reported as independent contributions.
- Adding comparisons after seeing results without marking them exploratory.
- Substituting a benchmark score for the construct the hypothesis is about.
- Mapping an empirical design onto a theoretical claim without proof obligations.

## Minimal Record

Design identifier, estimand, randomization/assignment mechanism, unit definitions, controls/ablations, primary outcome, exploratory items, and known blind spots.
