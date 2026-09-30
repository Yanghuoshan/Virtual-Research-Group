---
name: data-processing
description: Use when raw experiment outputs or supplied datasets must be cleaned, validated, and aligned into analysis-ready tables with a checksummed data manifest that downstream statistical analysis and evidence audits can bind to.
---

# Cleaning, Validation and Manifested Data Preparation

Turn raw results into trustworthy analysis inputs. This skill transforms recorded data and documents every transformation; it runs no experiments, performs no statistical tests, and draws no conclusions.

## Inputs

Raw result paths or supplied datasets with their provenance (run directories, external URIs with retrieval dates), the protocol's or packet's declared data schema and inclusion rules, the processing channel assigned by the core, and fresh output paths for the cleaned tables and manifest. Missing inclusion rules are a blocker; "clean it up" is not a specification.

## Method

1. Inventory inputs before touching them: record each source's identity, format, row counts and checksums. Reject inputs whose checksum fails against the cited provenance rather than quietly repairing them.
2. Apply the declared cleaning rules only - deduplication key, unit normalization, timezone alignment, missing-value policy. Every rule is applied or explicitly not applicable; no rule is invented because the data looks like it needs one.
3. Validate against the declared schema: type checks, range checks, referential integrity between joined tables. Validation failures are recorded per rule with counts, not silently coerced.
4. Align for analysis: join keys, shared units, one row per analysis unit as the protocol defines it. Record every dropped record with a machine-readable reason code and a one-line human explanation.
5. Emit the [data manifest](references/manifest-schema.md): source bindings with checksums, transformation log, row counts in and out, per-reason drop counts, and output checksums. The manifest is the contract between this skill and every downstream consumer.
6. Compute nothing interpretive: no aggregations beyond the declared cleaning rules, no filtering by outcome values, no reordering that hides rows. Aggregation and testing belong to statistical analysis under its own task.

## Outputs

At the assigned paths: the cleaned analysis-ready tables, the data manifest binding each table to its sources and transformations, and a short processing report listing deviations, validation failures and unresolved data quality questions as explicit limitations or blockers.

## Checks

Every output row is traceable to input rows through the transformation log. Row-count arithmetic reconciles: input rows equal kept plus dropped, with drops accounted per reason. No record is dropped for an undeclared reason; suspicious-but-declared drops are flagged, not deleted. The manifest checksums match the actual files.

Example: merging two runs where 137 of 40,000 rows fail a referential check yields a manifest entry with `dropped: 137, reason: orphan-key`, not a silent 39,863-row table. If the protocol never declared an orphan policy, that is a blocker returned to the core.

## Local References

- [Data manifest schema and reason codes](references/manifest-schema.md)

It defines the manifest contract for this skill only. It does not authorize statistical testing, plotting, or conclusions.

## Boundary

Return to the core with tables, manifests and blockers. Do not dispatch other skills or agents, select models, run experiments, perform statistical tests, make figures, update global findings/state, or advance phases. Statistical testing, plotting and interpretation are separate tasks for their own skills.
