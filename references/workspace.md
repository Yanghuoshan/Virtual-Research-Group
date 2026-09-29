# Research Workspace Rules

[The core contract](../SKILL.md) keeps the minimal directory tree and the rule that only four root documents are initialized. This reference explains how to use that structure.

## Root Document Ownership

| Document | Owner | Contents |
|---|---|---|
| `research-brief.md` | Core | Question, scope, constraints and unresolved definitions |
| `research-state.json` | Core | Project phase, tasks, active task, revision, authorization, budget, evaluation and audit references |
| `research-log.md` | Core | Human-readable scientific reasoning; events themselves are in state history |
| `findings.md` | Core | Accepted claim-to-evidence narrative; only the core promotes findings |
| `handoffs/` | Core | Saved assignment packets and actual execution receipts |

Create these documents once. Never reinitialize over an existing project; resume it and reconcile any in-flight work. Other directories appear only when a task needs them.

## Hypothesis and Run Organization

Use stable hypothesis IDs such as `H1` under `experiments/{hypothesis-id}/`, and one directory per attempt as `runs/{run-id}/`, for example `run-001`. A hypothesis is distinct from its repeated runs. Each run records:

- hypothesis ID and frozen `protocol.md` path/hash,
- data version, manifest and preprocessing steps,
- code revision, configuration and seeds,
- resource usage, job IDs and result locations,
- raw outputs, failures and local interpretation.

Reusable code belongs in `src/` with a pinned version; run-specific code belongs in `code/`. `results/` keeps raw measurements, proof certificates and logs. `analysis.md` records only local interpretation and uncertainty; the core decides whether it becomes an accepted finding.

## Protocol Discipline

Freeze `protocol.md` before execution. A changed design requires a new versioned hypothesis/protocol and renewed review, never an overwritten history. The core may request a draft protocol, then accept and freeze it. Execution tasks compare against the frozen protocol's recorded hash; a mismatch is a blocker, not a detail to adjust later.

## Evidence Preservation

Preserve negative runs, errors, exploratory discoveries and superseded analyses. Never overwrite raw evidence to match a manuscript. New interpretations get new versioned artifacts; previous versions remain inspectable. Audit records bind subject paths and hashes, so modification invalidates approval until re-review.

## Large Artifacts

Keep large datasets, checkpoints and bulky outputs in user-approved external storage. Record URI, checksum, version and access conditions under `data/` rather than copying them into the project. Local manifests hash those references; the core must separately verify external artifacts when their integrity affects a conclusion.

## Per-Task Artifacts

Task outputs stay inside their assigned scope: `literature/`, `hypotheses/`, `experiments/`, `src/`, `data/`, `paper/`, `reports/` or `reviews/`. Specialists write only these artifacts and never global records. Rework uses new versioned paths; earlier outputs can serve as evidence for a later task.
