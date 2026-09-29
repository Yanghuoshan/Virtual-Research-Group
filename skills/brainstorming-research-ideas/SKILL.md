---
name: brainstorming-research-ideas
description: Use when a bounded research question and literature evidence need a ranked set of falsifiable candidate hypotheses.
---

# Research Hypothesis Generation and Ranking

Generate defensible candidates, not a project schedule. Adapted from Orchestra Research's ideation guidance; original attribution is recorded in the bundle provenance manifest.

## Inputs

An assigned question, literature evidence with provenance, known failures, resource constraints, requested candidate count, output paths, and acceptance criteria. Missing literature is a limitation, not evidence of novelty.

## Method

1. State the problem, affected setting, and unresolved mechanism in two sentences. Distinguish a real problem from a method looking for an application.
2. Choose two or three lenses relevant to the supplied evidence:
   - **Tension:** identify competing objectives and ask whether the trade-off is fundamental or implementation-dependent.
   - **Abstraction:** generalize, specialize, or transfer a structural relation; state what assumptions change.
   - **Boundary:** vary an assumption about scale, distribution, composition, or time; predict a failure signature.
   - **What changed:** identify an evidenced change in available data, compute, or theory that invalidates a prior negative result.
   - **Simplicity:** propose a capacity- and tuning-matched simple baseline to isolate unnecessary complexity.
   - **Composition/decomposition:** identify complementary mechanisms or a component whose removal distinguishes explanations.
3. Generate diverse candidates before ranking. For each, specify mechanism, prediction, strongest alternative explanation, falsifying observation, nearest prior work, and cheapest discriminating test. Proposed tests are designs, not authorization to execute.
4. Rank candidates on significance, evidence of a gap, discriminability, feasibility, and confounding risk. Use ordinal judgments with reasons; do not invent precise novelty scores.
5. Return the requested shortlist plus rejected candidates and reasons. Leave selection of the pursued hypothesis to the core.

## Outputs

A candidate table and rationale at the assigned path. Each row includes hypothesis ID, mechanism, falsifier, evidence citations, confounds, and proposed validation cost. Mark unknowns and unverified novelty explicitly.

## Checks

- Does every candidate have an observable prediction that differs from its main alternative?
- Are negative results useful for distinguishing explanations?
- Is the proposed baseline fair under the available resources?
- Are claims of novelty backed by reviewed sources rather than search absence?

Example: rather than "improve graph accuracy," propose "degree-normalized aggregation reduces high-degree sensitivity; an improvement only on low-degree graphs contradicts this mechanism." Record that prediction without running training.

## Boundary

Return to the core with candidates, limitations, or missing evidence. Do not dispatch other skills or agents, select models, schedule experiments, advance phases, or edit global research state. Work only within the assigned output scope; the core decides which candidate to pursue.
