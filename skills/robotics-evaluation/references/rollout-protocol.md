# Rollout Protocol and Reproducibility

Robot results are sensitive to seeds, resets and environment versions. Record the protocol before interpreting success rates.

## Protocol Fields

| Field | Content |
|---|---|
| Environment/simulator version | Simulator build, physics version, asset versions |
| Task and initial-state distribution | Task IDs, randomization ranges, generator seed |
| Episode definition | Termination flags, time limit, truncation handling |
| Policy identity | Checkpoint, stochastic vs deterministic sampling, action rate |
| Observation and action spaces | Normalization, delays, control frequency |
| Trials | Number of episodes per condition, and the seed per episode |

Distinguish training seeds from evaluation episodes: many training seeds do not create independent evaluation episodes.

## Termination and Censoring

- Separate environment termination from time-limit truncation; bootstrap only when the declared return computation permits it.
- State whether an incomplete episode counts as failure, censored observation, or exclusion, and apply it consistently across compared policies.
- Report horizon exploitation: policies that exhaust the episode limit can inflate return while failing the completion criterion.

## Denominators and Failures

| Item | Rule |
|---|---|
| Failed episodes | Retained in denominators unless pre-specified otherwise |
| Crashes/resets | Counted and classified, not dropped |
| Partial logs | Marked incomplete; excluded only with a stated rule |
| Repeated resets of one condition | Not independent trials |

## Simulation vs Real Device

- Record dynamics, latency, contact and sensing gaps between simulation and hardware.
- Privileged simulator information (ground-truth state, perfect sensing) must be declared; it often does not exist in deployment.
- Simulated success is never physical validation; real-device claims require authorized device evidence.

## Reproducibility Checklist

Versions, seeds, episode counts, termination rules, success criteria, constraint measurements, artifact paths for logs, and any missing item as an explicit gap.
