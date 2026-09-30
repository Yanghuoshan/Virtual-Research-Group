# Data Manifest Schema

The manifest is a JSON file at the assigned output path binding cleaned tables to their sources. Downstream statistical analysis consumes it as its standard input; evidence audits may cite it and its outputs as subjects.

## Top-level shape

```json
{
  "schema_version": 1,
  "created_for": "task id the processing ran under",
  "protocol_reference": {"path": "experiments/h1/protocol.md", "sha256": "..."},
  "sources": [
    {"path": "experiments/h1/runs/run-a/results/metrics.jsonl", "sha256": "...",
     "rows": 40000, "format": "jsonl"}
  ],
  "transformations": [
    {"step": 1, "rule": "deduplicate on (unit,seed,epoch)", "rows_removed": 12}
  ],
  "tables": [
    {"path": "data/processed/h1-analysis-v1.parquet", "sha256": "...",
     "rows": 39863, "columns": ["unit", "seed", "condition", "metric", "value"],
     "analysis_unit": "(condition, seed)"}
  ],
  "drops": [
    {"reason": "orphan-key", "count": 137,
     "explanation": "rows referencing a condition absent from the run manifest"}
  ],
  "limitations": ["timezone of source logs was UTC per environment manifest"]
}
```

## Field rules

- `schema_version` is 1. Unknown versions are rejected by consumers, not guessed.
- `sources` entries carry the checksum of the artifact as consumed. A source that failed checksum verification never appears in a manifest; it appears in the processing report as a blocker.
- Every `drops` entry has a machine-readable `reason` code and a human explanation. The union of drop counts plus the table row count must reconcile against source rows for each transformation chain.
- `analysis_unit` states the protocol's unit of analysis for the table. Statistical analysis reads it rather than re-deriving it; a mismatch between declared unit and table shape is a defect.
- `limitations` records everything a careful reader would want flagged: unverifiable provenance, undeclared-but-observed anomalies kept in the data, format drift between sources.

## Reason codes

Use stable, lowercase reason codes so audits can count without parsing prose: `orphan-key`, `schema-violation`, `range-violation`, `duplicate`, `missing-value-policy`, `declared-exclusion`. A drop reason not derivable from the declared cleaning rules is not a valid code - that situation is a blocker, not a drop.

## Binding rules

- The manifest is append-only in spirit: correcting it means writing a new versioned manifest at a new path, not editing one a downstream task already consumed.
- Evidence audits bind manifests by path and checksum like any other subject; a changed table invalidates the recorded approval.
- The manifest contains no statistics beyond row counts. Means, intervals and tests live in statistical-analysis outputs.
