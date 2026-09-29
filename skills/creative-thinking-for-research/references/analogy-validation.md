# Analogy Validation

An analogy is only useful if its mechanism transfers. Most weak reformulations are verbal relabeling.

## Depth Ladder

| Level | Description | Value | Example |
|---|---|---|---|
| Surface | Things look similar | Low | "A neural network is like a brain" |
| Relational | Relationships between entities match | Medium | Attention allocation parallels economic resource allocation |
| Structural | Deep causal mechanisms map | High | Diffusion reverses a thermodynamic process, so non-equilibrium statistical mechanics applies directly |

Research value rises with depth and distance: nearby analogies refine ideas, distant analogies generate them, but distant analogies require more validation.

## Structure-Mapping Procedure

1. Strip domain nouns: restate the problem in relational and causal terms only.
   - Weak: "improve transformer attention efficiency".
   - Better: "a system must selectively aggregate from a large set where relevance is context-dependent and cost scales quadratically with set size".
2. Search for structural matches to that relational description.
3. Prefer the most distant match with genuine fidelity.
4. Map the source mechanism; state the invariants it preserves.
5. Transfer it and record what changes in the target domain.
6. Derive at least one prediction the source domain supplies that the original formulation did not.

## Validation Checklist

| Check | Requirement |
|---|---|
| Structural fidelity | Mechanisms and relations map, not labels |
| Invariants | Which properties are preserved, and which are known to break |
| Broken assumptions | Which target-domain assumptions the mapping violates |
| New prediction | At least one consequence not already encoded in the original wording |
| Source correctness | Would an expert in the source domain confirm the mechanism as stated? |
| Non-obviousness | Is the mapping non-obvious to the target audience? |
| Falsifier | What observation would show the analogy fails? |

## Labeling

| Situation | Label |
|---|---|
| Structural mapping with a derived prediction | Supported reformulation |
| Relational mapping, prediction unclear | Plausible; needs a discriminating prediction |
| Surface similarity only | Speculative; not a method |
| Mapping requires changing assigned constraints | Rejected: scope violation, not reformulation |

Renaming components is not a new method: if the reformulation only relabels the original statement, the mapping is surface similarity, not a mechanism transfer. Record it as rejected with that reason.

## Reporting Row

| Reformulation | Source domain | Mapped mechanism | Invariants preserved | Assumptions broken | Prediction | Label |
|---|---|---|---|---|---|---|
| Oversmoothing as spectral attenuation | Spectral graph theory | Repeated operator application attenuates high frequencies | Linearity, fixed operator | Nonlinearity of the learned update | Depth-dependent loss of high-frequency signal | Supported under stated assumptions |

## Boundary Notes

- Validate the source mechanism against supplied material when available; do not assert expertise from memory.
- Where validation needs literature or domain evidence that was not supplied, return a blocker naming the missing item.
- This skill returns reformulations; testing one is a separate authorized task decided by the core.
