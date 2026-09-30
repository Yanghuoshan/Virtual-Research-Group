---
name: manuscript-review
description: Use when a versioned research manuscript needs a bounded scientific critique or final-review proposal, especially where claims, evidence, limitations, or reviewer independence are disputed.
---

# Evidence-Based Manuscript Review

Assess the argument and its evidential support, not just prose quality. Return a review proposal; neither a reviewer role nor a convincing manuscript authorizes final acceptance.

## Inputs

Exact manuscript version, review scope and venue/audience criteria, claim-to-evidence map, current findings, protocol and supporting results where available, known limitations, prior review issues, task independence requirement, permitted tools and output paths. Missing evidence limits the review; it is not presumed favorable.

## Method

1. Check scope and independence against the [independence checklist](references/independence-checklist.md) before assessment. If `independent_review=true`, require a core-verified fresh session without the author's drafting history or self-justification; retain neutral criteria, artifacts and known limitations. If unavailable, return a blocker, not an independent-review claim. A non-independent editorial assessment must be labeled as such and cannot replace a required independent review.
2. Reconstruct the thesis and enumerate substantive claims, assumptions and scope. Map each claim to specific manuscript locations and supplied sources/results. Distinguish observed results, interpretation, conjecture and proposed future work. Assess novelty only against available literature; do not assert priority from memory.
3. Examine method/evidence alignment: controls, leakage, comparison budgets, statistical units, uncertainty, exclusions, baseline strength, causal identification and external validity. For theoretical papers inspect stated assumptions, proof obligations and gaps without claiming execution of a proof checker. Mark unavailable data/code/proofs as not assessed rather than infer their correctness.
4. Cross-check abstract, figures, tables and conclusions against supplied measurements and limitations. Separate scientific defects from presentation issues. Check citation-to-claim support only within supplied material and authorized channels; unresolved identities or wider searches return to the core.
5. Record each issue using the [severity rubric](references/severity-rubric.md) and the [review report structure](references/review-report-template.md): severity, location, affected claim, supporting evidence, impact, and a testable resolution criterion. Distinguish blocking validity defects, major gaps and minor clarifications. Include strengths and confidence/coverage limits. Suggest necessary evidence or narrower wording rather than demand unrelated research or rewrite the manuscript unasked.
6. For revisions, verify each resolution against the new manuscript/evidence versions. Preserve earlier reviews and reopen affected issues when dependencies change. Recommend ready within scope, revision needed, or blocked with reasons; do not imply a venue acceptance probability or final approval.

## Outputs

A new task-local report at a new assigned path, containing the claim/evidence map, severity-ranked issue list, unresolved questions and recommendation. When requested, propose final-review JSON with `schema_version: 2`, actual `reviewer`, `reviewed_at`, `summary`, a nonempty `claims` list of `claim` / `support` pairs, and `subjects` as project-relative `path` / actual `sha256` pairs. Bind current `findings.md`, the manuscript under `paper/`, and inspected dependencies. Missing required artifacts prevent a complete proposal. Core-owned `review.status=passed` is separate from the audit file; this review does not replace the evidence audit or completion gates.

## Checks

Can every criticism be located and justified? Are absent artifacts recorded as missing evidence, not confirmed errors or imagined supporting results? Are revised subjects rechecked, and identity hashes distinguished from scientific validation? Do not approve publication or research completion, invent measurements/citations, or mark unperformed checks as passed.

Example: a request for independent final approval in the author's current session, with a performance table but no raw measurements, is blocked by both isolation and evidence gaps. A deadline removes neither requirement.

## Local References

- [Issue severity rubric](references/severity-rubric.md)
- [Review report structure](references/review-report-template.md)
- [Reviewer independence checklist](references/independence-checklist.md)

These define procedures for this skill only. They do not authorize setting approval state, running experiments, or rewriting the manuscript.

## Boundary

Return to the core with the review or exact blockers. Do not dispatch other skills or agents, select models, run experiments, schedule reviews, submit papers, edit the manuscript or global findings/state, or advance phases. Recommendations do not set approval status; only the core accepts results and decides follow-up tasks.
