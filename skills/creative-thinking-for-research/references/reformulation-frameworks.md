# Reformulation Frameworks

Eight frameworks adapted from Orchestra Research's creative-thinking guidance (Koestler's bisociation, Gestalt representational change, Gentner's structure-mapping, Boden's constraint taxonomy, TRIZ-style negation, Polya's laddering, Kauffman's adjacent possible, Rothenberg's Janusian thinking). Select two or three that target the actual block.

## 1. Combinatorial Creativity (Bisociation)

Connect two previously unrelated frames of reference; the combination itself is the creative act.

Workflow: select two domains → list five to ten core primitives in each → build a cross-product matrix (rows from A, columns from B) → for each cell ask what applying A's concept to B's problem would mean → keep combinations that yield a non-trivial testable question → validate that the connection is mechanistic, not metaphorical.

Illustrative cross-product (structure of the exercise, not a result):

| | Caching | Load balancing | Fault tolerance |
|---|---|---|---|
| Natural selection | Evict least-fit entries | Adaptive allocation via fitness | Population-level redundancy |
| Immune memory | Learned threat signatures | Distributed detection | Self/non-self discrimination |
| Symbiosis | Cooperative prefetching | Mutualistic resource sharing | Co-dependent resilience |

Self-check: is the connection structural or merely verbal? Does it generate testable predictions? Would an expert in both fields find it non-obvious but sound?

## 2. Problem Reformulation (Representational Change)

The key shift: from "how do I solve this?" to "am I representing this correctly?"

| Strategy | Example |
|---|---|
| Change the objective | "Make it faster" → "Eliminate the need for this computation" |
| Change the formalism | Graph problem → spectral/linear-algebra problem |
| Change the granularity | Per-token → per-span prediction |
| Change the agent | "How should the model learn?" → "How should the data teach?" |
| Change the timescale | Real-time optimization → amortized inference |
| Invert the direction | Forward simulation → inverse problem |

Workflow: state the problem in one sentence → identify hidden assumptions (formalism, objective, granularity, agent) → generate the opposite of each → ask whether the reformulation makes the problem easier, harder, or usefully different. Historical examples: PageRank (content analysis → graph eigenvalue), dropout (regularization → approximate ensemble), attention (remember everything → selective query).

## 3. Analogical Reasoning (Structure-Mapping)

Depth determines value; see [analogy validation](analogy-validation.md) for the depth ladder and validation checklist.

Workflow: describe the problem in relational and causal language only → search for structurally similar systems → prefer the most distant match with genuine fidelity → map the source mechanism → transfer it and note what changes → generate predictions the source did not provide.

## 4. Constraint Manipulation (Boden's Taxonomy)

| Type | Operation | Example |
|---|---|---|
| Exploratory | Search within the existing conceptual space | Architecture search within a fixed paradigm |
| Combinational | Combine elements from different spaces | Neuro-symbolic methods |
| Transformational | Change the rules of the space | Dropping "training requires labels" |

Transformational moves are rarest and highest impact. Workflow: list five to ten constraints (computational, methodological, architectural, evaluative) → classify each as hard (physically or logically necessary), soft (convention), or hidden (unstated but assumed) → for each soft or hidden constraint ask what relaxing, tightening, or replacing it produces.

Hard constraints include correctness requirements, assigned permissions and resource limits: those are never relaxed by a reformulation. A "relaxation" that removes an assigned constraint is a scope violation, not creativity.

Examples of legitimate constraint transformation: "data must fit in memory" → streaming algorithms; "training requires labels" → self-supervised learning; "inference is one pass" → iterative refinement.

## 5. Negation and Inversion

Negate a core assumption and ask what system you would build.

| Assumption | Negation | Consequence |
|---|---|---|
| Strong consistency is required | What if it is not? | Eventual consistency, CRDTs |
| Exact answers are required | What if approximate is fine? | Sketches, locality-sensitive hashing |
| Labels are necessary | What if we learn without them? | Self-supervised and contrastive methods |
| All parameters are used | What if only some are? | Mixture of experts, sparsity |
| Errors must be prevented | What if we correct them? | Speculative decoding, self-correction |

TRIZ-inspired moves: inversion, segmentation, merging, universality, nesting, dynamization. Evaluation: incoherent negations are discarded; already-explored ones should be re-checked against what changed; unexplored and coherent ones become candidates.

## 6. Abstraction and Generalization Laddering

Generalize when results exist without explanation; specialize when theory exists without grounding; analogize when stuck in either direction.

Generalization: replace each specific element with a variable → ask under what conditions the claim holds → if the general principle is novel, that is the contribution. Specialization: add extreme constraints (tiny data, huge dimension, adversarial input, real-time requirement) → ask whether it still works and why not → the failure case reveals true assumptions.

## 7. The Adjacent Possible

Innovation happens at the boundary of what has become reachable. Workflow: list recent enablers (hardware capability, datasets or benchmarks, open tooling, theoretical results, regulatory or social conditions) → for each ask what was previously impractical that it now permits → intersect enablers → note that widely visible adjacent possibles attract competition.

Timing heuristics: an idea requiring nonexistent technology is beyond the boundary; an idea feasible five years ago probably exists already — verify against supplied literature. Verify the currency of any claimed enabler; tables of "current" enablers age quickly and are examples, not facts.

## 8. Janusian and Dialectical Thinking

Hold the contradiction instead of choosing a side. Workflow: identify the binary treated as opposition → ask what a system achieving both would look like, and whether the trade-off is an artifact of the current formalization → seek a synthesis that reframes the relationship → test whether both goals are demonstrably achievable.

Self-check: is the contradiction held genuinely rather than prematurely resolved? Is the synthesis new rather than a compromise? Does it change how the problem is framed, not just which solution is chosen?

## Combining Frameworks

A deep session usually maps the space (constraints, adjacent possible), generates disruptions (negation, bisociation, reformulation), deepens leads (structure-mapping, laddering, Janusian synthesis), then evaluates with the two-sentence test:

> "[Domain] currently struggles with [problem] because [reason]. We [approach] by [mechanism], which works because [insight]."

Anything surviving all phases and passing the test is a candidate to return. Selection remains the core's decision.
