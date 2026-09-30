---
name: experiment-execution
description: Use when a frozen protocol must actually be run to produce raw evidence: executing experiment runs under an assigned sandbox channel, snapshotting code and environment, and recovering logs, results and failure diagnostics without altering the protocol.
---

# Protocol-Bound Experiment Execution

Execute an already frozen protocol exactly as written. This skill produces raw evidence; it never designs, amends, or reinterprets the protocol, and it never decides what the results mean.

## Inputs

The frozen protocol path with its recorded hash, hypothesis id, the four evaluation fields (`primary_measure`, `baseline`, `validation_plan`, `uncertainty_plan`), the assigned execution channel (sandbox server and tool names named by the core in the task objective), run budget and stopping conditions, fresh output paths under `experiments/{hypothesis-id}/runs/{run-id}/`, and acceptance criteria. A missing protocol, mismatched hash, or unassigned execution channel is a blocker, not an invitation to improvise.

## Method

1. Verify the run contract before touching anything: the protocol file matches the frozen hash, the evaluation fields name what will be measured, and the assigned channel covers every execution step the protocol requires. Following [run management](references/run-management.md), create the run directory and fix the run id before execution starts.
2. Snapshot the exact code to execute into `runs/{run-id}/code/` and record the [environment and code](references/environment-and-code.md) manifest: dependency versions, random seeds, hardware or sandbox identity, and the source commit or `src/` versions the snapshot came from. A run without a reproducible snapshot is not evidence.
3. Execute only the protocol's steps, in the protocol's order, through the assigned sandbox channel only. Respect pre-declared time, memory and attempt bounds; a step that exceeds its bounds is a recorded failure, not a reason to request more resources silently. Deviations observed mid-run are logged, never patched around.
4. Recover artifacts following [results recovery](references/results-recovery.md): raw measurements, logs, certificates and the run summary go to `runs/{run-id}/results/`; failures, timeouts and diagnostics go to `runs/{run-id}/analysis.md` with the exact step and error. Preserve partial output from a failed run rather than deleting it.
5. Map every recovered number to the protocol step and evaluation field that produced it. Numbers the protocol does not ask for are not reported as findings; they may be logged as raw artifacts only.
6. On any failure, timeout, or channel unavailability: stop, write the diagnosis, and return a blocker to the core. Do not retry the run, do not switch channels, and do not rerun an in-flight experiment because a session changed.

## Outputs

At the assigned run paths: the code snapshot, environment manifest, raw results and logs, `analysis.md` with factual diagnostics and local interpretation clearly separated from speculation, and a run summary binding each result to a protocol step and evaluation field. Failed runs return the same structure with failure evidence. Nothing here is a scientific conclusion; meaning is assigned later by synthesis and the core.

## Checks

Every reported number traces to a raw artifact under `results/`. The executed steps match the frozen protocol step for step; any deviation is documented with cause and location. Seeds, versions and channel identity are recorded well enough that a competent stranger could attempt the same run. A run that produced no usable evidence is reported as such, not summarized into success.

Example: a training run that diverged on step 4 of the protocol is reported with its partial logs and a divergence diagnosis, and the core decides whether the protocol, the channel, or the hypothesis is at fault. Rerunning quietly with a different seed is forbidden.

## Local References

- [Run directory and identity management](references/run-management.md)
- [Environment, code snapshot and version rules](references/environment-and-code.md)
- [Results, logs and failure recovery](references/results-recovery.md)
- [Sandbox channel assignment and refusal rules](references/sandbox-assignment.md)

These define procedures for this skill only. They do not authorize protocol changes, resource expansion, channel switching, or retries.

## Boundary

Return to the core with artifacts or exact blockers. Do not dispatch other skills or agents, select models, modify or extend the frozen protocol, retry or rerun failed runs, install servers, expand the assigned channel, update global findings/state, or advance phases. Interpreting results, updating findings, and commissioning further runs are separate core decisions.
