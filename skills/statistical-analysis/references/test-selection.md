# Test Selection Rules

Selection is driven by the protocol's estimand and design, never by which test would reach significance.

## Order of decisions

1. **Estimand**: what quantity is the comparison about (difference in means, ratio, probability of superiority, rank correlation)? It comes from `primary_measure` and the design.
2. **Unit and dependence**: the manifest's `analysis_unit` governs. Shared seeds, clusters, paired designs, or repeated measures demand dependence-aware methods or aggregation to the declared unit first.
3. **Estimator**: unbiased (or explicitly biased-but-preferred, with the protocol saying so) for that estimand at that unit.
4. **Test and interval**: matched to the estimator and sample structure, with the `uncertainty_plan` naming the interval method (bootstrap, analytic, permutation). A conflict between the plan and the data's structure is a blocker, not a vote.

## Selection table

| Structure | Prefer | Notes |
|---|---|---|
| Two conditions, subject-level unit, paired | Paired test or permutation on differences | Pairing declared by design, not discovered in data |
| Two conditions, unpaired | Permutation/bootstrap or t-with-checks | Report effect size with interval regardless |
| Multiple conditions | Family-wise or FDR control as pre-specified | Family = the declared set, not the reported subset |
| Many seeds, few subjects | Aggregate to subject level; report training variance separately | Seeds are not subjects |
| Count/proportion outcomes | Exact or bootstrap intervals | Normal approximations flagged at small counts |
| Ranked outcomes | Rank-based tests with the estimand stated | Rank transform changes the estimand; say so |

## Prohibitions

- No test chosen because its p-value is smaller across a menu of candidates.
- No switching to one-sided tests after seeing the direction of the effect.
- No peeking-based stopping: the protocol's stopping rule governs, and optional stopping is reported if it occurred.
- No "correction shopping" among Bonferroni, Holm and FDR after seeing which survives.

## Failed assumptions

Check assumptions the method requires (variance homogeneity, symmetry, independence), record the check result, and prefer robust or permutation alternatives **only when the protocol's `uncertainty_plan` anticipated them**. Otherwise record the violation and return it as a limitation or blocker for the core to resolve.
