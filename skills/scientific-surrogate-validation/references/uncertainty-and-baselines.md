# Uncertainty, Calibration and Baselines

Separate observation noise, model uncertainty and numerical error before claiming predictive quality.

## Error Decomposition

| Source | Handling |
|---|---|
| Observation noise | Estimate from repeated measurements or declared sensor uncertainty |
| Model uncertainty | Report predictive intervals or ensembles; state the method |
| Numerical error | Solver tolerance, discretization, mesh or step size |
| Reference error | Discretization or measurement uncertainty of the comparator |

Attributing all discrepancy to the surrogate is a common error: subtract or report the reference's own uncertainty first.

## Calibration

- Evaluate interval coverage on held-out evidence at the unit relevant to the claim (specimen, trajectory, system).
- Report undercoverage or overcoverage quantitatively, not qualitatively.
- Do not tune calibration on the evaluation data used for the final claim.
- Report sensitivity to distribution shift: coverage may hold in-distribution and fail out of regime.

## Baselines and Comparators

| Comparator | Report |
|---|---|
| Physics-based solver | Version, tolerance, cost per query |
| Analytic solution | Domain of validity |
| Statistical baseline | Fit procedure and training ranges |
| Prior surrogate | Version and training data overlap |

Compare under matched data ranges and matched evaluation regimes; a surrogate compared only in its training regime says nothing about extrapolation.

## Independent Units

Correlated observations from one trajectory, specimen or simulation must be grouped. Report the number of independent systems or trajectories alongside raw sample counts; raw counts inflate effective sample size.

## Reporting Table

| Regime | Metric | Interval coverage | Reference uncertainty | Verdict |
|---|---|---|---|---|
| Interpolation, t<10s | RMSE 0.02 (m/s) | 0.91 vs nominal 0.95 | 0.005 | Slight undercoverage |
| Extrapolation, Re>5000 | RMSE 0.31 (m/s) | 0.62 | 0.01 | Not supported |
