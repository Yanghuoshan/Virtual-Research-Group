# Run Directory and Identity Management

## Directory contract

One run directory per attempt, created before execution starts:

```text
experiments/{hypothesis-id}/runs/{run-id}/
├── code/          # Exact snapshot of executed code
├── results/       # Raw measurements, logs, certificates
└── analysis.md    # Diagnostics and failure report
```

The run id is chosen by the executor, lowercase and unique within the hypothesis, such as `run-2026-09-30-a`. It is neither the task id, the packet id, nor the session id: one task may legitimately produce several runs, and a retried packet must use a new run id rather than overwriting an old one.

## Rules

- Create the directory tree before the first execution step; never write results outside it.
- Never overwrite or delete a previous run. A superseded run stays on disk; the core decides what is discarded.
- The run summary at `results/run-summary.md` (or the assigned path) states: hypothesis id, task id, packet id, protocol path and hash, run id, and one line per protocol step with its outcome.
- Partial results from an interrupted run are preserved in place with a diagnostic note in `analysis.md`; an interrupted run is never silently completed by a later session.
- Storage-hungry artifacts (datasets, checkpoints) follow the workspace external-artifact rules: store a URI plus checksum, not a copy, unless the core assigned local paths.

## Relationship to identities

| Identity | Owner | Changes when |
|---|---|---|
| task id | Core | A new objective or acceptance contract is needed |
| packet id | Core | A new assignment attempt is issued |
| session id | Host | The execution session is replaced |
| run id | Executor | Every physical execution attempt |

A rerun under the same packet is a protocol deviation and must be reported as one. A new packet for the same task may legitimately produce a fresh run; record the lineage in the run summary.
