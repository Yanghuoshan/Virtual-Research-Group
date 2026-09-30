---
name: reproducibility-audit
description: Use when research claims need a version-bound reproducibility assessment, or an existing audit has stale artifacts, missing dependencies, or unclear verification coverage.
---

# Version-Bound Reproducibility Audit

Inspect whether supplied artifacts support a reproducible claim. Distinguish artifact inspection, recomputation from saved outputs, rerunning the original procedure, and independent replication. None substitutes for the others or proves scientific truth.

## Inputs

Claim-to-evidence map, findings, protocol, raw evidence, code/data/environment manifests, prior audits if any, intended verification level and tolerances, independence requirement, permitted checks, and new output paths. Missing artifacts are audit findings, never grounds to fabricate replacements. Independent review requires core-verified fresh isolation without author working history; report a mismatch before reviewing.

## Method

1. Build the [dependency manifest](references/dependency-manifest.md): project-relative paths, actual hashes, source revisions, dataset/split identities, seeds, configuration, environment and hardware assumptions. Map each claim through its dependency chain from raw inputs to tables/figures and manuscript. Treat unlisted dependencies as a coverage gap even when listed hashes match.
2. Compare prior audit subjects with current artifacts using the [stale binding playbook](references/stale-binding-playbook.md). Changed, absent or unhashed dependencies make the affected approval stale or unverifiable. Preserve prior audits; replacing old hashes alone is not renewed verification.
3. Trace whether the protocol and implementation agree: preprocessing/splits, metric definitions, baseline and tuning budgets, stopping rules, uncertainty and exclusions. Check missing/failed runs, manual transformations, nondeterminism, unavailable services and undocumented steps. A protocol is not raw evidence; a polished table is not a substitute for underlying measurements or proof artifacts.
4. Inspect supplied artifacts with assigned read-only tools. Recompute summaries only within explicitly authorized analysis scope and available tools; save diagnostics at new paths. Do not rerun experiments, training, benchmarks, simulations or proof checkers, install dependencies, fetch missing data, or start background jobs. Return a rerun proposal to the core for a separate authorized execution task, including reconciliation of existing job IDs.
5. Report each claim/check with the [audit report structure](references/audit-report-template.md): supported within the inspected scope, failed, blocked, or not checked. Separate the verification level actually performed from the level requested. Record procedure, inputs, expected tolerance, observed discrepancy and limitation; no execution means no claim of successful reproduction.
6. Return a coverage matrix, dependency gaps, discrepancies and proposed remedies. Do not silently alter evidence, protocol, analysis code or prior approvals. Missing evidence prevents a complete verification recommendation even if other checks pass.

## Outputs

A task-local report at a new assigned path. When requested, propose an evidence-audit JSON with `schema_version: 2`, actual `reviewer`, `reviewed_at`, `summary`, a nonempty `claims` list of `claim` / `support` pairs, and `subjects` containing project-relative `path` / actual `sha256` pairs. For an evidence gate, bind current `findings.md`, any frozen protocol and separate primary evidence under `experiments/`, `data/`, `literature/` or `reports/`, plus inspected dependencies. Missing required subjects remain blockers; never invent hashes. Approval status is not an audit-file field: only the core can set `evidence_review.status=verified` after checking reasoning and coverage.

## Checks

Can each checked claim be traced to its actual inputs and environment? Are changes and omissions explicit? Hash agreement establishes identity only, not correctness, dependency completeness or reviewer independence.

Example: a passed audit for yesterday's metrics cannot certify today's modified file. Report the stale binding and inspect the change; do not refresh the hash and announce success.

## Local References

- [Dependency and provenance manifest](references/dependency-manifest.md)
- [Audit report structure](references/audit-report-template.md)
- [Stale and unverifiable bindings](references/stale-binding-playbook.md)

These define procedures for this skill only. They do not authorize reruns, dependency installation or approval-state changes.

## Boundary

Return to the core with an audit proposal and blockers. Do not dispatch other skills or agents, select models, schedule reruns, acquire permissions, edit global findings/state, approve the project, or advance phases. This skill audits supplied research artifacts; it is not an experiment executor or final manuscript acceptance authority.
