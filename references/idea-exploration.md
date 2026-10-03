# IDEA Exploration and Formulation

[The core contract](../SKILL.md) keeps the authoritative phase table and the rule that only a separate core decision changes phase. This reference explains how to pursue the four judgments below inside the existing `scope`, `ideation` and `design` phases. It adds no phase, no mandatory sequence and no permission; it does not promise publication.

## Why the default posture is too conservative

A loop that ranks candidates mainly by near-term cost will mechanically discard anything expensive, then report that the most convenient candidate won. Cost and risk are real, but they are a different axis from research value. A strong contribution asks a harder question first: is there a gap a capable reviewer would agree is real, and does answering it change what the community can do, explain or predict? Judge value and cost separately, and keep a costly candidate alive when its potential is high and its next discriminating step is affordable.

## Judgment 1: Opportunity — find a gap worth attention

Do not treat a search miss as a gap. Build an opportunity map before proposing solutions:

- **Affected setting and stakes.** Name the task, population or capability affected, and the concrete consequence if the problem stays open.
- **Assumption-and-boundary map.** For the two or three strongest current methods, record in parallel: core assumption, stated capability boundary, evaluation setting, known failure mode and source. A gap usually lives where an assumption is load-bearing yet untested.
- **Four evidenced entry points.** (a) results that conflict and are not explained by ordinary confounds; (b) a widely used method that depends on an unexamined premise or evaluation choice; (c) an important distribution, scale, composition or temporal boundary whose failure mechanism is unexplained; (d) a change in data, compute, tooling or theory that invalidates the premise behind an earlier negative result. A performance-versus-efficiency or generality-versus-specialization tension is a further entry point: ask whether the trade-off is a fundamental frontier or an artifact of current representations and objectives.
- **Nearest-neighbor audit.** For the closest work, state what it actually solved, under which assumptions, over which range, and what it left untested. Classify each area as solved, contradicted, documented limitation, or insufficient evidence. Record reverse evidence and coverage limits; where retrieval is authorized, log the query and sources, and where it is not, return the open verification question with novelty marked unknown.

Separate potential impact from evidence maturity from resource reachability. A direction with weak evidence but high potential is a **pending opportunity**, not an automatic selection and not an automatic rejection. Output: an opportunity map plus a nearest-neighbor and coverage-limits list.

## Judgment 2: Question — raise a gap to a breakthrough-potential question

Restate the gap so it can fail. Replace "improve a benchmark" with: *which mechanism or assumption produces the capability boundary, and what new observable must appear if it changes?* A usable question names the object, the condition, the target and a falsifiable comparison.

Generate candidates along different contribution paths rather than within one familiar framing: theoretical (bounds, impossibility, provable conditions), methodological (new representation, objective, inference or learning mechanism), empirical/evaluative (revealing a hidden regularity or failure mechanism), and capability (a combination or scale previously impossible). A question need not carry every path.

Force a real conceptual move rather than a rename:

- Change an implicit assumption or the level of abstraction, or move between representations, and state what becomes expressible and what is lost.
- Test cross-domain mappings for structural fidelity at the mechanism level, not shared vocabulary.
- Ask what transfers once the model name and implementation details are stripped away, and what remains if the simplest strong baseline already explains the effect.

For each serious question, write the core claim, necessary assumptions, the strongest rival explanation, a unique prediction or proof obligation, the observation that would overturn it, and what a negative result would still clarify. A framing with no falsifier stays a topic or conjecture; it may be reformulated, but it is not yet a mature hypothesis. Output: problem cards and competing-explanation cards.

## Judgment 3: Route — design mechanisms with a distinctive contribution

Compare a candidate family, not the first familiar plan: a minimal-mechanism route, an ambitious high-reward route, and a strong simple baseline or counter-route. For each, state the key primitive, the mechanism chain, its preconditions and its expected failure boundary.

Then make the "nearest-neighbor versus real increment" contrast explicit: what is shared, what differs, and why the difference cannot be reproduced by parameter scale, more data, tuning, or swapping an existing component. A combination must explain the emergent capability and why each part is necessary, not just list names.

Judge two axes separately and only with reasons; never invent precise novelty or impact scores:

| Axis | Dimensions |
|---|---|
| Potential | potential scientific contribution, breadth of beneficiaries, strength of the unique prediction, expected impact |
| Cost and risk | evidence maturity, confounding and rival explanations, implementation difficulty, resource dependence, risk of being absorbed by a strong baseline |

A high-potential but currently expensive route may be kept as a **conditional candidate**. Record the minimum conceptual or analytic step that would discriminate it, the condition to continue, and the condition to stop. If it exceeds the approved resources or permissions, mark it blocked instead of pretending it is executable.

Match validation to the contribution type: theoretical routes state formal assumptions, the theorem or bound, the key proof obligations and a counterexample search; empirical routes state a fairly tuned strong baseline, decisive controls, ablations, out-of-distribution and boundary tests, and confound control. This is design only and never authorizes execution. Output: route cards, a comparison matrix, and keep/reject/refute-reason notes.

## Judgment 4: Contribution — pre-build the originality and impact argument

Turn each serious route into an auditable chain and label every part as checked fact, source-based inference, or untested claim:

| Contribution claim | Nearest work | Real difference | New capability or explanation | Required evidence | Falsifier | Applicability |
|---|---|---|---|---|---|---|

Keep theoretical, methodological, empirical and community-resource contributions distinct, and do not repackage one effect as several contributions.

Run the reviewer's counterfactual before committing:

- If the new mechanism is removed, can the strong baseline reproduce the gain?
- If only data, scale or tuning changed, does the contribution still hold?
- If the conclusion holds in only one setting, what mechanism explains that, and is the bounded claim still meaningful?
- If a nearest paper already expresses the core idea, narrow or reformulate the claim instead of asserting prior work by wording.

Describe expected impact as specific and observable: which assumptions, methods, capabilities or evaluation practices it may change, what evidence would support that, and where the claim stops. Venue fit is the combination of a clear problem, a non-trivial mechanism, strict evidence and transferable insight, not keyword or score optimization.

## Decision states and returning

Keep four states distinct: pending opportunity, conditional high-potential candidate, evidence-supported route proposal, and verified conclusion. Only the core promotes among them. Weak contribution logic returns to route comparison; a failed route returns to question reformulation; contradicting literature returns to the opportunity map. The core decides, under the existing contract, whether to gather more evidence, continue in the current phase, or take a legal transition.

## Worked illustration (structure only; claims are unverified)

Suppose a method appears to fail under composition. Do not jump to "add a module for a few points". First check whether the nearest work already studied that boundary. Then hypothesize that the failure comes from an objective that does not preserve a composition invariant. Compare, in parallel, changing the objective, changing the representation, and proving the two goals incompatible under the stated assumptions. For each route write the mechanism difference, the unique prediction or proof obligation, and how a strong simple baseline would explain the same result. Without literature or experiments, these remain candidates to be checked, not findings.

## Boundaries

This reference guides judgment only. It does not authorize retrieval, experiments or proof checks, does not change the question or phase, and does not select a candidate; those remain core decisions under the existing gates.
