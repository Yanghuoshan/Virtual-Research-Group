# Issue Severity Rubric

Rank issues by what they do to the claim, not by how hard they are to fix.

## Levels

| Level | Definition | Effect on recommendation |
|---|---|---|
| Blocking | The claim, method or evidence does not support a stated conclusion; a required artifact or control is missing | Recommendation is blocked or revision required before any acceptance |
| Major | Substantial gap that weakens a central claim or its generality | Revision required; the claim should be narrowed or supported |
| Minor | Presentation, clarity, or completeness issue that does not change the claim's support | Improves the manuscript; does not gate acceptance |

## Criteria

| Dimension | Blocking example | Major example | Minor example |
|---|---|---|---|
| Evidence | Claimed result has no supplied raw measurement | Variance reported for only one seed | Figure caption lacks units |
| Method | Evaluation split leaks held-out data | Baseline not resource-matched | Hyperparameter table incomplete |
| Claims | Abstract states superiority not supported by intervals | Scope stated more broadly than the data | Related work omits a supplied citation |
| Reproducibility | Code/data unavailable with no description | Environment versions missing | Script paths undocumented |
| Presentation | — | Key limitation only in an appendix | Typos, inconsistent notation |

## Rules

- One blocking issue is enough to block; do not average severities.
- Attach every issue to a specific claim and location; unlocated issues are not review findings.
- Missing evidence is blocking for the claim that depends on it, even when the rest of the manuscript is sound; it is not proof the result is wrong.
- Restate resolved issues from prior rounds with their new status rather than silently dropping them.
- Do not inflate severity to force a preferred outcome, and do not downgrade a validity defect to "minor" because a deadline is near.

## Reporting Row

| ID | Severity | Location | Affected claim | Evidence | Impact | Resolution criterion |
|---|---|---|---|---|---|---|
| I1 | Blocking | Table 2, §4.1 | C2: superiority over baseline | Intervals overlap in supplied results | Claim unsupported as stated | Report paired interval or narrow the claim |
