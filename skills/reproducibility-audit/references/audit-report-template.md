# Audit Report Structure

Return a task-local report. Approval belongs to the core; the report supports that decision, it does not make it.

## Sections

1. **Scope:** claim(s) audited, artifacts inspected with `path` and `sha256`, requested verification level, and independence status.
2. **Method:** procedures actually performed, tools used, limits, and what was deliberately not done.
3. **Claim/check matrix:** one row per claim and check.
4. **Dependency findings:** changed, missing or unlisted items from the [dependency manifest](dependency-manifest.md).
5. **Discrepancies:** expected versus observed, with tolerance and materiality.
6. **Blockers and recommendations:** what would resolve each one, including a separate authorized rerun proposal if needed.
7. **Limitations:** coverage limits and unverified areas.

## Claim/Check Matrix

| Claim | Check performed | Level | Result | Evidence | Blocker |
|---|---|---|---|---|---|
| C1: method beats baseline | Recomputed aggregate from supplied raw outputs | Recomputation | Matches within tolerance | `experiments/H1/runs/run-001/results/metrics.json` | None |
| C2: variance across seeds | Seed run files inspected | Inspection | Only 3 of 5 seed files present | — | Missing seed outputs |

## Verification Levels

| Level | Meaning |
|---|---|
| Inspection | Artifacts and versions examined; nothing executed |
| Recomputation | Derived values recomputed from supplied raw outputs within authorized analysis |
| Rerun | Procedure executed again; requires a separate authorized experiment task |
| Independent replication | Different team/setup reproduces; outside this skill's scope |

Record the level performed for each check. Never label a check at a level that was not performed.

## Result Vocabulary

| Result | Use when |
|---|---|
| Supported within inspected scope | Check passed under the stated level and limits |
| Failed | Observed discrepancy beyond tolerance |
| Blocked | Required artifact or authorization missing |
| Not checked | Check requested but not performed |

"Not checked" is a valid and necessary entry. Omitting it overstates coverage.

## Proposal JSON

When requested, propose an evidence-audit JSON with `schema_version: 2`, actual `reviewer`, `reviewed_at`, `summary`, a nonempty `claims` list of `claim` / `support` pairs, and `subjects` of project-relative `path` plus actual `sha256`. Bind `findings.md`, any frozen protocol, separate primary evidence under `experiments/`, `data/`, `literature/` or `reports/`, and inspected dependencies. Missing required subjects remain blockers; never invent hashes.
