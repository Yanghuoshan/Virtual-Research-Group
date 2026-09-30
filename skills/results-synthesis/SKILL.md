---
name: results-synthesis
description: Use when experiment outputs or failure diagnostics must be compared across runs or hypotheses, including contradictory results and post-run reflection, without promoting proposed claims to accepted findings.
---

# Cross-Run Results Synthesis

Assemble what the evidence currently supports across runs, hypotheses, and analyses. This skill organizes claims against their evidence; it never promotes a claim into `findings.md` and never authorizes new experiments.

## Inputs

Run analyses and result manifests with hashes, the frozen protocols they executed, current findings, known failures, the synthesis question from the core, and fresh output paths. Missing raw evidence for a cited result is a blocker, not a gap to paper over.

## Method

1. Inventory the evidence: every run, its protocol version, status, and the exact result artifacts, following [synthesis rules](references/synthesis-rules.md). Failed and null runs are first-class evidence.
2. Build the claim-evidence map: for each candidate claim, list supporting results, contradicting results, and the conditions under which each was observed. Use one row per claim; cite artifacts by path.
3. Separate convergence from divergence: claims supported under all tested conditions, claims that flip under specified conditions, and claims resting on a single run. Name the condition that flips each contested claim.
4. Test rival explanations against the same map: for each preferred mechanism, state at least one alternative the evidence does not yet exclude, and what observation would separate them.
5. Quantify where the artifacts allow it and refuse where they do not; a synthesis without intervals is labeled as such, never smoothed into false precision.
6. Return the map with open questions ranked by decision impact: which unresolved question, if answered, would most change the next direction decision. When the core requests post-run reflection, compare observed outcomes with the predeclared primary measure and baseline, name protocol deviations and failed/null runs, then offer bounded next-step alternatives with resource costs and a falsifiable prediction for each; do not edit a frozen protocol or cherry-pick favorable runs.

## Outputs

At the assigned path: the claim-evidence map with per-claim status (supported / contested / single-run / contradicted), condition tables, rival-explanation notes, and ranked open questions. If asked to prepare a reflection artifact, additionally propose a JSON file under the assigned `reports/` scope with `observation`, `protocol_check`, `counterevidence`, `alternatives`, `next_options`, `prediction`, `decision` and an `evidence` array of project-relative `path`/actual `sha256` pairs. Include an unchanged original run output or blocked-run diagnostic, and distinguish the specialist's proposed decision from the core's later acceptance. Everything is a proposal; the core alone promotes accepted claims.

## Checks

Every claim row cites at least one raw artifact; contradicting evidence is listed, not averaged away; no claim is labeled verified; extrapolation beyond tested conditions is marked explicitly.

Example: two runs improving accuracy only under low-degree graphs support "condition-specific improvement", not "general improvement", and the map must say which condition flips it.

## Boundary

Return to the core with the map and open questions. Do not dispatch other skills or agents, select models, commission or run experiments, update findings.md or global state, or advance phases. Promoting claims and choosing the next direction are core decisions.

## Local References

- [Synthesis rules](references/synthesis-rules.md)
