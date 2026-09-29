# Causal Claims in Interpretability

Distinguish description from causation. Most overclaiming comes from merging them: necessity and sufficiency require intervention evidence, not activation alignment.

## Claim Types

| Claim | Required evidence |
|---|---|
| Descriptive: this direction/feature responds to X | Activation alignment on held-out examples, with baselines |
| Correlational: activation predicts behavior | Prediction with controls and held-out data |
| Necessity: removing the component degrades behavior | Intervention with corrupted-run and alternative-site controls |
| Sufficiency: restoring or inducing it produces behavior | Intervention that produces the behavior from a corrupted baseline |
| Localization: behavior lives at this site | Site comparison with matched patch scope |
| Completeness: this set explains the computation | Accounting for residual behavior after the full intervention |

## Intervention Designs

| Design | What it does | Main caveat |
|---|---|---|
| Zero ablation | Sets activations to zero | Introduces out-of-distribution inputs |
| Mean/resample ablation | Replaces with activations from other inputs | Resample source must be justified |
| Corrupt-then-restore (patching) | Runs corrupted input, restores the component, measures recovery | Requires the corruption to actually break behavior |
| Activation addition/steering | Adds a scaled direction | Scale choice can drive the effect |
| Path patching | Patches along a hypothesized path | Requires the path graph to be correct |

Report the design, site, direction, magnitude, corrupted-run control and the behavioral metric used.

## Failure Modes

- Necessity claimed from correlational or descriptive evidence.
- Sufficiency claimed from a steering result with an unmatched scale.
- Patching effects caused by distribution shift rather than the component.
- Behavioral metrics that do not measure the claimed behavior (for example a proxy task).
- Effects that vanish under alternative sites, reported as localization anyway.
- Single prompt families used to support a general mechanism claim.

## Reporting

| Claim | Design | Controls | Result | Verdict |
|---|---|---|---|---|
| C necessary for Y | Corrupt-and-restore at layer 8 | Corrupted-run control, layer 4 alternative site | Recovery 0.62 vs control 0.58 | Necessity not established |

When a control undermines the claim, report the weaker supported claim (often descriptive) rather than dropping the claim silently.
