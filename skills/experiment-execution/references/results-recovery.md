# Results, Logs and Failure Recovery

## What to recover

Everything the protocol declares as an output, plus everything needed to diagnose why the run behaved as it did:

- Raw measurements before any aggregation; per-step logs with timestamps.
- Certificates, solver outputs, or channel-generated attestations where the protocol asks for them.
- The run summary binding each number to a protocol step and an evaluation field (`primary_measure`, `baseline`, `validation_plan`, `uncertainty_plan`).

Raw means raw: no smoothing, filtering, unit conversion, or dropping of "bad" rows. Transformations belong to later data-processing tasks on recorded manifests, not to the executor.

## Failure handling

On failure, timeout, or interruption:

1. Stop executing further protocol steps.
2. Preserve partial outputs in place; never delete a failed run's artifacts.
3. Write `analysis.md` with: the failing protocol step, the exact error or symptom, the last successful step, and a factual diagnosis clearly separated from speculation.
4. Return a blocker to the core describing what is missing for acceptance.

A failure is evidence. A run that fails cleanly and is fully diagnosed satisfies this skill's contract; a run that "mostly worked" with silent patches does not.

## Timeouts and bounds

- Time, memory, and attempt bounds come from the protocol or the task objective. A bound is a stop condition, not a negotiating position.
- Exceeding a bound is recorded as a bounded-failure with the observed usage; requesting more resources is a core decision made through the blocker, not a unilateral rerun.

## What results are not

- Results are not conclusions. No statement in a run artifact claims a hypothesis is supported or refuted.
- Numbers outside the protocol's declared measurements are logged as raw artifacts only, never promoted into the run summary as findings.
- Author-reported numbers from upstream baselines are copied with their source locator; they are never blended with this run's measurements.
