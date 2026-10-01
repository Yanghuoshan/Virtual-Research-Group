# Review Report Structure

Return a task-local report at a new assigned path. Recommendations inform the core; they do not set approval state.

## Sections

1. **Scope and versions:** manuscript version, artifacts inspected with `path` and `sha256`, criteria applied, independence status.
2. **Summary judgment:** what the manuscript claims, what the supplied evidence supports, and the recommendation.
3. **Claim/evidence map:** one row per substantive claim.
4. **Issue list:** severity-ranked rows using the [severity rubric](severity-rubric.md).
5. **Strengths:** what is well supported, with evidence.
6. **Unassessed areas and limitations:** what could not be checked and why.
7. **Recommendation:** ready within scope, revision needed, or blocked, with reasons.

## Claim/Evidence Map

| Claim ID | Location | Evidence inspected | Support | Notes |
|---|---|---|---|---|
| C1 | §3.2, Figure 3 | `experiments/H1/runs/run-001/results/metrics.json` | Supported within supplied artifacts | Single seed reported |
| C2 | Abstract, Table 2 | Table 2 only; raw measurements absent | Not assessable | Missing raw evidence |

## Issue Row

| ID | Severity | Location | Affected claim | Evidence | Impact | Resolution criterion |
|---|---|---|---|---|---|---|
| I2 | Major | §5.1 | C3: generalizes to unseen domains | Only one domain in supplied data | Scope overstated | Add domain evidence or restrict the claim |

## Recommendation Vocabulary

| Recommendation | Use when |
|---|---|
| Ready within scope | No blocking or major issues for the assigned criteria and supplied evidence |
| Revision needed | Major issues or minor issues that the core asked to be resolved |
| Blocked | Missing evidence, missing independence, or scope mismatch prevents the review |

## Rules

- Every issue is located and justified; "the writing is unclear" without a location is not a finding.
- Distinguish missing evidence from demonstrated error.
- State novelty only against supplied literature; do not assert priority from memory.
- For revisions, re-check the affected rows against the new versions and record prior statuses.
- If a final-review JSON is requested, use `schema_version: 2` with actual `reviewer`, `reviewed_at`, `summary`, a nonempty `claims` list of `claim` / `support` pairs, and `subjects` of project-relative `path` plus actual `sha256`, binding `findings.md`, the manuscript under `paper/`, and inspected dependencies. Produce each `path` / `sha256` pair with `python3 scripts/research.py bind --project <project> --path <path> ...`; a copied or invented hash is a falsified binding.
