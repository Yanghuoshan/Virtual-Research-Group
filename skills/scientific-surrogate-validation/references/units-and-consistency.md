# Units, Consistency and Regimes

Numerical fit does not establish scientific validity. Check units, consistency and regime coverage first.

## Units and Dimensional Analysis

| Check | Method |
|---|---|
| Unit traceability | Map every model input/output back to physical quantities |
| Dimensional consistency | Verify terms and losses are dimensionally consistent |
| Nondimensionalization | Record reference scales and whether they are constant |
| Coordinate systems | Record frame, orientation and transformations |
| Derived metrics | Report the formula; note inverse-transform bias when averaging in transformed space |

## Consistency Constraints

Check only where physics requires them, and report whether they were imposed or merely observed:

| Constraint | Typical test |
|---|---|
| Conservation | Mass, energy or momentum balance over the predicted trajectory |
| Positivity | Non-negative quantities (density, concentration, temperature in K) |
| Symmetry/equivariance | Invariance under declared transformations |
| Boundary conditions | Prescribed values at domain boundaries |
| Monotonicity | Where the governing relation requires it |

Report violations alongside fit error; a small error with systematic drift can still invalidate long-horizon use.

## Regime Separation

| Dimension | Report |
|---|---|
| Interpolation vs extrapolation | Which parameter/time ranges were covered by training data |
| Parameter regimes | Error per regime, not only the global mean |
| Time horizon | Error versus rollout length; drift accumulation |
| Physical regime | Phase, Reynolds number, temperature band as applicable |

Never average away a failing regime; report it explicitly. Good interpolation does not support extrapolation claims.

## Reference Evidence

State the reference solver's discretization error, measurement uncertainty or validity assumptions. A reference is not exact ground truth; discrepancies may originate in the reference rather than the surrogate.
