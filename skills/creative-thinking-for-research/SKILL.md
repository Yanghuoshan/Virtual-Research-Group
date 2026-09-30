---
name: creative-thinking-for-research
description: Use when a specified research problem is stuck in one representation and needs structurally grounded alternative formulations.
---

# Research Problem Reformulation

Produce alternative representations and mechanistic analogies for one assigned problem. This is a local reasoning technique, not a project-level ideation pipeline. Adapted from Orchestra Research's creative-thinking guidance.

## Inputs

The current formulation, fixed scientific or physical constraints, suspected conventional constraints, known counterexamples, supplied source material, and an assigned output path.

## Method

1. Separate hard constraints from conventions and hidden assumptions. Do not relax correctness, user permissions, or resource limits while exploring a representation.
2. Express the problem in relational terms: entities, interactions, information available, objective, and cost. Remove incidental terminology without losing essential assumptions.
3. Apply selected transformations from the [reformulation frameworks](references/reformulation-frameworks.md) (eight frameworks in total; the common ones are summarized below), matching them to the diagnosed block in [creative blocks](references/creative-blocks.md):
   - **Bisociation:** pair primitives from two supplied fields; retain only mappings that preserve mechanism, not similar words.
   - **Representation change:** move between graph, algebraic, probabilistic, or optimization formulations; state what becomes easier and what is lost.
   - **Constraint manipulation:** relax or tighten one scientific assumption and derive its consequences.
   - **Inversion:** negate a conventional assumption and seek a coherent countermodel.
   - **Abstraction:** specialize a broad claim to an informative boundary case, or generalize only after enumerating required conditions.
   - **Contradiction:** express a trade-off as a joint objective and identify whether a new abstraction could satisfy both sides.
4. For each proposal, specify source relation, target relation, preserved invariants, broken assumptions, and a discriminating prediction, validated with [analogy validation](references/analogy-validation.md). Label unsupported analogies as speculative.
5. Compare the formulations without committing the project to a new direction. Return both plausible and rejected reformulations with reasons.

## Outputs

A reformulation memo at a new assigned path, containing the original formulation, assumption map, alternative formulations, structural mappings, counterexamples, and questions requiring domain evidence.

## Checks

A valid analogy must predict something not already encoded in the original wording. Renaming components is not a new method. A relaxed constraint must be scientifically meaningful, not an unauthorized change to the task.

Example: reformulate local message passing as repeated graph-operator application, then ask whether spectral attenuation explains observed oversmoothing. State the linearity assumptions before transferring the analogy to nonlinear models.

## Local References

- [Reformulation frameworks](references/reformulation-frameworks.md)
- [Analogy validation](references/analogy-validation.md)
- [Creative blocks and unblocking](references/creative-blocks.md)

These define procedures for this skill only. They do not authorize testing a reformulation, relaxing assigned constraints, or changing the question.

## Boundary

Return to the core with the memo or blockers. Do not dispatch other skills or agents, select models, schedule validation, change the research question globally, advance phases, or edit global state. Selecting or testing a new direction belongs to the core.
