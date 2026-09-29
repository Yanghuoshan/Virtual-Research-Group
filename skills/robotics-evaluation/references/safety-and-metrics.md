# Safety Metrics and Failure Taxonomy

A high return does not imply safe operation. Measure constraints directly.

## Metric Set

| Metric | Notes |
|---|---|
| Success rate | With the number of episodes and an interval; a fixed success criterion declared before comparison |

Report the success rate with its denominator and interval; a bare percentage is not interpretable.
| Constraint violations | Count, rate and severity, measured from logs rather than inferred from reward |
| Time to completion | Distinguishes efficiency from horizon exploitation |
| Control effort / smoothness | Energy, jerk, or actuation saturation where relevant |
| Return | Report alongside the metrics above, never as a proxy for safety |
| Recovery behavior | Whether violations are recovered or terminal |

## Failure Taxonomy

| Class | Example |
|---|---|
| Task failure | Object dropped, goal not reached |
| Constraint violation | Collision, joint limit exceeded, forbidden contact |
| Timeout | Episode truncated at the horizon |
| Sensing failure | Lost tracking, occluded target |
| Controller instability | Oscillation, saturation |
| Environment artifact | Simulator crash, reset anomaly |

Keep classes separate: merging them hides whether failures are policy or environment issues.

## Safety Reporting Rules

- Fixed success and violation criteria before comparison; no post-hoc adjustment.
- Report violation rates per condition, with denominators.
- Weight violations by severity only when the weighting was pre-specified.
- A policy with fewer violations but lower success is a trade-off to report, not a winner by default.
- Reward shaping that penalizes violations is not a measurement of constraint satisfaction.

## Comparison Conditions

Match interaction budgets, sensors, actuation, initial-state distributions and episode counts. Report paired differences across conditions and seeds; a single-condition improvement does not establish a general result.
