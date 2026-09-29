---
name: scientific-surrogate-validation
description: Use when scientific surrogate predictions need unit, physical-consistency, extrapolation, and uncertainty checks against reference evidence.
---

# Scientific Surrogate Validation

Audit a specified surrogate model's predictions and scientific claims. Do not treat numerical fit as sufficient scientific validity.

## Inputs

Physical quantities and units, governing assumptions, boundary conditions, system identifiers, data provenance, train/evaluation parameter ranges, predictions, measurements or reference simulations, error definitions, and assigned outputs.

## Method

1. Check units, dimensional consistency, coordinate systems and nondimensionalization, using [units and consistency](references/units-and-consistency.md). Trace transformations back to physical quantities before computing errors.
2. Identify correlated observations from the same trajectory, specimen, simulation or system. Check splits at the unit relevant to the generalization claim.
3. Separate interpolation from extrapolation across time, parameters and physical regimes. Report each regime rather than averaging away an important failure region.
4. Compare against trusted numerical, analytic or statistical references. State their discretization error, measurement uncertainty or validity assumptions rather than calling them exact ground truth unconditionally.
5. Check conservation, positivity, symmetry or boundary conditions only where scientifically required. Report violations alongside fit error and identify whether constraints were imposed or merely observed.
6. Distinguish observation noise, model uncertainty and numerical error, using [uncertainty and baselines](references/uncertainty-and-baselines.md). Evaluate uncertainty calibration against held-out evidence and report undercoverage or sensitivity to distribution shift.
7. Record scientific conclusions at the scope warranted by reference evidence; proxy predictions are not physical measurements.

## Outputs

A unit/constraint audit, per-regime error and uncertainty analysis, source traceability, and limitations at assigned artifact paths. Missing scientific assumptions return as unresolved inputs.

## Checks

Good interpolation does not prove extrapolation. A reference solver's discretization bias is not necessarily model error. Related samples must not inflate effective sample size.

Example: low average trajectory error can hide systematic energy drift that invalidates long-horizon use.

## Local References

- [Units, consistency and regimes](references/units-and-consistency.md)
- [Uncertainty, calibration and baselines](references/uncertainty-and-baselines.md)

These define procedures for this skill only. They do not authorize new experiments or simulations.

## Boundary

Return to the core with the audit or blockers. Do not dispatch other skills or agents, select models, run new scientific experiments, schedule simulations, alter global hypotheses or state, or promote predictions to verified findings.
