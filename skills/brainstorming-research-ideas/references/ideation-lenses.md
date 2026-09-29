# Ideation Lenses

Ten lenses adapted from Orchestra Research's ideation guidance. Select two or three that fit the supplied evidence; do not run all ten by default. Every lens produces candidates, not decisions.

## 1. Problem-First vs Solution-First

| Mode | Start | Risk |
|---|---|---|
| Problem-first | A concrete failure, bottleneck or unmet need | Converges on incremental fixes |
| Solution-first | A new capability seeking application | "Hammer looking for a nail" |

Workflow: write the idea in one sentence → classify the mode → if problem-first, establish who suffers and how much; if solution-first, identify at least two genuine problems it addresses → state the gap: what is impossible today that this would enable.

Self-check: can a specific community be named as beneficiary? Is the problem genuinely unsolved rather than under-marketed? In solution-first mode, does it create new capability or replicate existing ones?

## 2. The Abstraction Ladder

| Move | Action | Typical outcome |
|---|---|---|
| Up (generalize) | Turn a specific result into a broader principle | Framework or theory contribution |
| Down (instantiate) | Test a general paradigm under concrete constraints | Empirical paper, surprising failure analysis |
| Sideways (analogize) | Apply the same abstraction level to an adjacent domain | Transfer paper |

Workflow: state the current focus in one sentence → generate an up, a down and a sideways variant → for each, ask whether it is a contribution on its own. Record what assumptions change at each level.

## 3. Tension and Contradiction Hunting

Breakthroughs often come from reconciling goals treated as trade-offs. Common tensions: performance versus efficiency, privacy versus utility, generality versus specialization, safety versus capability, interpretability versus performance, scale versus accessibility.

Workflow: list the top three to five desiderata → identify pairs treated as trade-offs → ask whether each trade-off is fundamental or an artifact of current methods → if an artifact, the reconciliation is the contribution; if fundamental, characterizing the frontier is itself valuable.

Self-check: is the tension evidenced rather than assumed? Can each side be traced to supplied sources? Is the reconciliation technically plausible rather than aspirational? The tension lens is the one most often used without evidence; record the source for each claimed trade-off.

## 4. Cross-Pollination (Analogy Transfer)

A valid analogy requires structural fidelity (the mapping holds at the mechanism level), a non-obvious connection, and testable predictions. Frequently productive source fields: neuroscience (attention, memory consolidation), physics (energy-based models, phase transitions), economics (mechanism design, incentives), ecology (population dynamics, niche competition), linguistics (compositionality, pragmatics), control theory (feedback, stability, adaptive regulation).

Workflow: describe the problem in domain-agnostic language → ask what other field solves a structurally similar problem → study that solution at the mechanism level → map it back preserving relations → generate predictions. Validate depth with the mapping test: mechanisms must transfer, not labels. Deeper reformulation work is a separate core decision, not something this skill hands off by itself.

## 5. The "What Changed?" Principle

Revisit abandoned approaches under new conditions. Change categories to monitor: compute, scale, regulation, tooling, high-profile failures, and cultural shifts.

Workflow: pick a negative result or abandoned approach three to ten years old → list the assumptions behind its rejection → test whether each still holds → if one is invalidated, re-derive the idea and frame it as "X was impractical because Y, but Z changed". Verify the change with supplied evidence; a claimed change without evidence is a hypothesis, not a premise.

## 6. Failure Analysis and Boundary Probing

Boundary types worth probing: distributional, scale, adversarial, compositional, temporal.

Workflow: select a widely used method with strong reported results → identify implicit evaluation assumptions → systematically violate each → document where and how it breaks → diagnose why → propose a fix or argue the failure is fundamental. A boundary probe is most valuable when it yields a failure signature that discriminates between explanations.

## 7. The Simplicity Test

Warning signs of unnecessary complexity: many hyperparameters with narrow optima, ablations where most components contribute marginally, a simple baseline never properly tuned, improvements within noise on most benchmarks.

Workflow: identify the current strong method → strip it to its minimal core → compare with matched compute and tuning → if the gap is small, the simplicity is the contribution; if large, the complexity is now explained. Always specify a capacity- and tuning-matched baseline, otherwise the comparison is not evidence.

## 8. Stakeholder Rotation

| Perspective | Typical question |
|---|---|
| End user | Is it usable; what errors are unacceptable? |
| Developer | Is it debuggable and composable? |
| Theorist | Why does it work; what are the guarantees? |
| Adversary | How can it be exploited? |
| Ethicist | Who is harmed or excluded? |
| Regulator | Is it auditable and explainable? |
| Operator | What is the cost, scaling and failure mode? |

Workflow: describe the system in one paragraph → assume each stakeholder perspective in turn → list the top concerns → identify which are unaddressed by supplied evidence → the unaddressed concern with broadest impact becomes the question. A stakeholder perspective reveals questions; it does not by itself establish significance.

## 9. Composition and Decomposition

Composition: pick two methods solving complementary subproblems and ask what emergent capability arises. Decomposition: isolate components of a complex method and ask which is the actual bottleneck.

Workflow: list five to ten components in the area → compose pairs and decompose one complex method → ask whether combinations create new capability and whether isolation reveals a dominant or redundant component.

## 10. The Two-Sentence Test

> Sentence 1 (problem): "[Domain] currently struggles with [specific problem], which matters because [concrete consequence]."
> Sentence 2 (insight): "We [approach] by [key mechanism], which works because [reason]."

If the template cannot be filled, the problem is not well defined (return to lens 1), the insight is unclear (lens 7), or significance is unestablished (lens 3). Calibration: would a colleague outside the subfield understand why it matters? Does it stand without jargon? What would a skeptic's first objection be?

## Lens Selection Guide

| Situation | Start with |
|---|---|
| Unknown area | Tension hunting (3) → What changed (5) |
| Vague area, no specific idea | Abstraction ladder (2) → Boundary probing (6) |
| Existing idea, quality unclear | Two-sentence test (10) → Simplicity test (7) |
| Good idea, fresh angle wanted | Cross-pollination (4) → Stakeholder rotation (8) |
| Combining existing work | Composition/decomposition (9) |
| Challenging conventional wisdom | Boundary probing (6) → Simplicity test (7) |

Adaptation note: the source guidance also prescribed defining a pilot schedule and executing next steps. Here those become proposals returned to the core; this skill does not schedule or authorize work.
