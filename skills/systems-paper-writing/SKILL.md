---
name: systems-paper-writing
description: Use when verified systems measurements and design decisions need a paragraph-level manuscript structure for a specified systems venue.
---

# Systems Manuscript Structure

Explain why a concrete system is appropriate for a stated workload and environment. Adapted from Orchestra Research's systems-writing guidance, including the attributed Levin/Redell, Zhang, Heiser, and Roscoe sources in local references.

## Inputs

The approved thesis, implementation facts, workload and environment definitions, verified end-to-end and component measurements, design alternatives, supplied citations, venue constraints, and assigned output scope.

## Method

1. State the thesis as "design X improves property P for workload Y in environment Z." Specify where it does not apply.
2. Construct the introduction from an evidenced problem, concrete gaps, the key mechanism, and contributions that each map to evidence. Do not invent production observations to motivate the system.
3. Explain background only as needed. Distinguish measured workload properties from assumptions or illustrative examples.
4. Organize design by mechanism: responsibilities, data/control flow, invariants, alternatives considered, and reasons for the chosen trade-off. Separate design from implementation detail.
5. Structure evaluation as setup → end-to-end comparison → component isolation → scaling and failures. Match hardware, workload, concurrency, tuning effort, and resource accounting. Distinguish throughput at fixed latency from incomparable peak-throughput numbers.
6. Give each result a question, method, observation, and bounded conclusion. Microbenchmarks cannot alone establish end-to-end utility; unsupported deployment claims remain gaps.
7. Use [section blueprints](references/section-blueprints.md) and [writing patterns](references/writing-patterns.md) within the supplied page budget. Historical venue tables are examples, not current rules.
8. Return the requested draft with its claim coverage and missing-evidence list. Do not commission the missing measurements.

## Outputs

Paragraph-level outline or manuscript, design-to-evidence map, limitations, and explicit gaps at assigned paths. Report compilation status honestly when source output is requested.

## Checks

Can a reader distinguish the implemented prototype from proposed features? Is every design advantage supported under a named workload? Are latency percentiles, warm-up, saturation, repetitions, and measurement units explicit? Are trade-offs and failure cases reported?

Example: a cache hit-path microbenchmark is not evidence for whole-system speedup without hit-rate and miss-path measurements.

## Boundary

Return to the core with the artifact and gaps. Do not dispatch other skills or agents, select models, schedule benchmarks or revisions, change global state, or submit papers. Missing citation verification or another writing specialty is a blocker for the core, not a handoff owned by this skill.

## Local References

- [Section blueprints](references/section-blueprints.md)
- [Writing patterns](references/writing-patterns.md)
- [Checklist](references/checklist.md)
- [Reviewer guidance](references/reviewer-guidelines.md)
- [Historical venue details](references/systems-conferences.md)

## Venue Templates (External)

No LaTeX templates are bundled. Download the current author kit from the venue's official source and verify the year's page limit and formatting rules before drafting; bundled copies would be stale and are not redistributable here.

- ASPLOS: https://www.asplos-conference.org/
- NSDI and OSDI (USENIX): https://www.usenix.org/conferences/
- SOSP (ACM SIGOPS): https://www.sigops.org/

A missing template or toolchain is a blocker returned to the core. Do not install TeX packages, choose a different venue, or redirect the task to another skill.

Apply local technical advice only within the supplied task, tools, and evidence scope.
