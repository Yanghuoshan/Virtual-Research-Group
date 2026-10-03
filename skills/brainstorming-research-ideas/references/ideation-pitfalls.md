# Ideation Pitfalls and Anti-Patterns

## Common Pitfalls

| Pitfall | Symptom | Fix |
|---|---|---|
| Novelty without impact | "No one has done X" and no one needs X | Problem-first check: name the beneficiary |
| Incremental by default | Idea is +2% on a benchmark | Abstraction ladder: move up or sideways |
| Complexity worship | Eight components, each marginally helpful | Simplicity test with a matched baseline |
| echo chamber | All ideas derive from the same handful of papers | Cross-pollination from an adjacent field |
| Stale assumptions | "This was tried and failed" (years ago) | What changed: test the rejection assumptions |
| Single-perspective bias | Only the engineer's view | Stakeholder rotation |
| premature convergence | First idea adopted before alternatives exist | Complete the diverge phase before ranking |
| Unfalsifiable framing | "Better understanding of X" | Require an observable prediction and a falsifier |
| Novelty by absence | Claimed gap because a search found nothing | Require reviewed sources; mark unknown |
| Rename as novelty | New term or notation for an existing mechanism | State the mechanism-level difference and its unique prediction |
| Module stacking as contribution | Contribution is "A + B + C" with no necessary part | Show the emergent capability and remove parts to test necessity |
| Breakthrough theatre | Grand claim with no falsifier or discriminating evidence | Demand a prediction, a nearest-work difference and a decisive test |
| Cost-driven elimination | The cheapest idea wins because expensive ones were filtered out early | Judge potential and cost on separate axes; defer, do not delete |

## Anti-Patterns of Over-Conservatism

A loop optimized for safety and speed drifts into these, which lower contribution without raising rigor:

- Ranking purely by near-term feasibility, then reporting the convenient candidate as the best one. Fix: rank potential and cost separately, and defer high-potential/high-cost candidates instead of dropping them.
- Requiring a fully evidenced gap before allowing a question to be posed. Fix: a pending opportunity may guide bounded exploration while its evidence is still being gathered, labeled as unverified.
- Rewarding agreement with the nearest work and penalizing tension with it. Fix: treat a well-argued conflict with prior evidence as a candidate, not a defect.
- Treating "already studied" as "fully explained". Fix: check whether the mechanism, boundary and failure mode were actually explained, not just reported.
- Declaring success as "found some novel work to build on". Fix: require a specific gap, a real mechanism difference, and a claim that a matched baseline cannot explain.

## Contract-Specific Anti-Patterns

- Treating a generated candidate as an accepted hypothesis: selection belongs to the core.
- Turning "cheapest discriminating test" into a plan to run it: tests are designs; execution is a separate authorized task.
- Ranking with invented numeric scores: see [candidate schema](candidate-schema.md); use ordinal judgments with reasons.
- Expanding the question to find better ideas: scope changes return to the core.
- Citing from memory to support novelty: unresolved identities are gaps; verify against supplied material or return a blocker.
- Using a lens that contradicts supplied evidence because it is more interesting: evidence constrains the lens, not the reverse.
- Presenting unverified novelty or impact as established: label it unknown, or as source-based inference at most.

## Quality Signals Before Returning

1. Every ranked candidate has a mechanism, a prediction, a main alternative and a falsifier.
2. Each candidate states its contribution type, its real difference from the nearest work, and its decisive evidence.
3. Potential and cost are recorded separately, and costly high-potential candidates are deferred with a next step rather than removed.
4. Rejected candidates are recorded with reasons and the condition that would revive them.
5. Novelty and impact claims trace to reviewed sources or are marked unknown.
6. Validation costs are stated against the declared budget; infeasible candidates are labeled, not silently dropped.
7. Coverage limits are stated explicitly.
