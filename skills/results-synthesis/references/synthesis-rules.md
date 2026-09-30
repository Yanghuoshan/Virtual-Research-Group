# Synthesis Rules

Procedures for the results-synthesis skill only. They organize evidence; they never authorize experiments, claim promotion, or global state writes.

## Evidence Inventory

- Record for each run: hypothesis, protocol version, run id, status (completed, failed, partial), and the result artifact paths with hashes.
- A result cited in the map must exist as an artifact; author-reported numbers carry a locator and are never blended with reviewer-computed ones.
- Absent evidence is recorded as absent; it is never counted as negative evidence.

## Claim-Evidence Map

- One row per claim: claim text, applicability conditions, supporting artifacts, contradicting artifacts, status.
- Statuses: `supported` (all available evidence agrees), `contested` (evidence splits by condition - name the condition), `single-run` (one observation), `contradicted` (evidence against dominates).
- Claims are about what was observed, not about what the mechanism "must" be.

## Rival Explanations

- For each preferred explanation, list at least one unexcluded alternative and the observation that would separate them.
- Correlation-flavored claims are marked as such unless the design supports identification.

## Open Questions

- Rank by decision impact: what would most change the next direction decision if answered.
- Each open question states what evidence would answer it, not merely that it is interesting.

## Refusals

- No intervals or precision beyond what artifacts support.
- No promotion language ("we show", "proven") in the map; use "observed under conditions".
- No new experiment proposals executed; proposing the next check is allowed only as an open question with its discriminating observation.
