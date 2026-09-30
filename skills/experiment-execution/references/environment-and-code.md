# Environment, Code Snapshot and Version Rules

## Code snapshot

Copy the exact files that will execute into `runs/{run-id}/code/` before starting. The snapshot is the definition of "what ran":

- Record where the code came from: a `src/` version, a commit hash, or an upstream release with its identifier.
- If the protocol names exact file versions, verify the snapshot matches them; a mismatch is a blocker.
- Do not modify code after execution starts. A required fix means stopping the run, reporting the defect, and letting the core decide whether a new run under a new packet is justified.

## Environment manifest

Write `runs/{run-id}/environment.json` (or the assigned path) before execution:

| Field | Content |
|---|---|
| `channel` | Assigned sandbox server and tool names, exactly as the task objective names them |
| `runtime` | Language and interpreter/library versions actually used |
| `dependencies` | Package list with versions, or a lock file hash |
| `seeds` | Every random seed the protocol declares, and where each was applied |
| `hardware` | Sandbox identity, CPU/GPU/memory class where the channel reports it |
| `inputs` | Data or model artifacts consumed, with path or URI and checksum |

## Rules

- Seeds come from the protocol. Inventing, re-rolling, or "fixing" a seed mid-run is a protocol deviation and must be reported.
- The manifest records what was actually used, discovered from the channel, not what was requested. Requested-versus-actual differences are noted.
- A channel that cannot report its runtime or hardware identity is recorded with `unknown` values plus an explanation; it is not a reason to refuse execution, but it is a reproducibility limitation the run summary must carry.
- Checksums use SHA-256 and cover the artifact as consumed, not as named.

## Failure modes to record

- Unpinned dependencies resolved at run time (version drift).
- Input artifacts whose checksum differs from the one the protocol or packet cited.
- Environment changes mid-run (preemption, restart) with timestamps.
