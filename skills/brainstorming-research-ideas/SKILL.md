---
name: brainstorming-research-ideas
description: Use when a bounded research question and literature evidence need ranked, falsifiable candidate hypotheses that reach beyond incremental fixes.
---

# Research Hypothesis Generation and Ranking

Generate defensible candidates with real contribution potential, not a project schedule. Adapted from Orchestra Research's ideation guidance; original attribution is recorded in the bundle provenance manifest. The opportunity, question, route and contribution judgments behind these steps are described in the framework reference `references/idea-exploration.md`, which the core can supply with the assignment.

## Inputs

An assigned question, literature evidence with provenance, known failures, resource constraints, requested candidate count, output paths, and acceptance criteria. Missing literature is a limitation, not evidence of novelty.

## Method

1. Establish the gap before proposing a fix: name the affected setting and stakes, the load-bearing assumption or boundary, and the nearest work's actual coverage. Distinguish a documented gap from a search miss and from a solution looking for an application.
2. Choose two or three lenses relevant to the supplied evidence from the [ideation lenses](references/ideation-lenses.md) catalog (ten lenses in total; the most frequently useful are summarized below):
   - **Tension:** identify competing objectives and ask whether the trade-off is fundamental or an artifact of current representations or objectives.
   - **Abstraction:** generalize, specialize, or transfer a structural relation; state what assumptions change and what becomes expressible.
   - **Boundary:** vary an assumption about scale, distribution, composition, or time; predict a failure signature and its mechanism.
   - **What changed:** identify an evidenced change in available data, compute, or theory that invalidates the premise behind a prior negative result.
   - **Simplicity:** propose a capacity- and tuning-matched simple baseline to isolate unnecessary complexity.
   - **Composition/decomposition:** identify complementary mechanisms or a component whose removal distinguishes explanations.
3. Generate diverse candidates before ranking, using the [candidate schema](references/candidate-schema.md). For each, specify contribution type, mechanism, the new capability or explanation, prediction, strongest alternative explanation, falsifying observation, nearest prior work and the real difference from it, and cheapest discriminating test. Proposed tests are designs, not authorization to execute.
4. Rank on two separate axes with ordinal judgments and reasons, never invented numeric scores: **potential** (significance, evidence of a gap, discriminability, strength of the unique prediction) and **cost and risk** (feasibility, confounding, resource dependence, risk of being absorbed by a strong baseline). A costly but high-potential candidate is kept as a conditional candidate with a next discriminating step, continue condition and stop condition, not removed for cost alone.
5. Check the result against [ideation pitfalls](references/ideation-pitfalls.md). Return the requested shortlist plus rejected candidates and reasons. Leave selection of the pursued hypothesis to the core.

## Outputs

A candidate table and rationale at the assigned path. Each row includes hypothesis ID, contribution type, mechanism, nearest-prior difference, falsifier, evidence citations, confounds, potential and cost judgments, and proposed validation cost. Mark unknowns and unverified novelty explicitly.

## Checks

- Does every candidate have an observable prediction that differs from its main alternative?
- Is the gap documented rather than inferred from search absence?
- Could a rename, a stacked module, or a strong matched baseline explain the same claimed contribution?
- Are negative results useful for distinguishing explanations?
- Are claims of novelty backed by reviewed sources rather than search absence?

Example: rather than "improve graph accuracy," propose "degree-normalized aggregation reduces high-degree sensitivity; an improvement only on low-degree graphs contradicts this mechanism." Record that prediction without running training.

## Local References

- [Ideation lenses](references/ideation-lenses.md)
- [Candidate schema, ranking and rejection log](references/candidate-schema.md)
- [Ideation pitfalls and anti-patterns](references/ideation-pitfalls.md)

These define procedures for this skill only. They do not authorize executing proposed tests, expanding the question, or selecting a hypothesis.

## Boundary

Return to the core with candidates, limitations, or missing evidence. Do not dispatch other skills or agents, select models, schedule experiments, advance phases, or edit global research state. Work only within the assigned output scope; the core decides which candidate to pursue.
