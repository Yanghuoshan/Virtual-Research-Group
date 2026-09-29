---
name: vision-evaluation
description: Use when image classification, detection, or segmentation results need split-integrity and metric-protocol auditing.
---

# Vision Evaluation Protocol Audit

Check the validity of a supplied visual benchmark or result set, not an entire vision research project.

## Inputs

Task type, image/subject/source identifiers, annotation schema and version, split manifests, prediction files, preprocessing and augmentation definitions, metric implementation, and assigned artifact paths.

## Method

1. Check image duplicates, near-duplicates, shared subjects, and adjacent video frames across splits. Group correlated observations by subject, scene, or acquisition session when required by the target claim.
2. Verify label mapping, missing labels, ignored regions, image resizing, mask interpolation, and coordinate conventions. Mismatched label spaces can masquerade as model errors.
3. For detection, specify IoU thresholds, confidence handling, nonmaximum suppression, maximum detections and averaging. Do not compare different AP definitions as one number.
4. For segmentation, specify class averaging, background/void handling and absent-class conventions. Aggregate per-image and global intersection/union only as declared.
5. For classification, check class balance, macro/micro metrics, calibration where claimed, and validation-only threshold or checkpoint selection.
6. Compare models with matched pretraining exposure, input resolution and evaluation transforms. Identify potential test contamination from pretrained data as a limitation when it cannot be resolved.
7. Report multiple seeds or appropriately grouped uncertainty, subgroup errors and traceable failure cases. Do not tune on inspected test failures during this audit.

## Outputs

A split and metric audit, task-specific defect list, and computed measurements only if valid predictions are supplied. Include source paths and unresolved assumptions.

## Checks

Training augmentations must not alter held-out labels or leak statistics. Near-duplicate checks are documented procedures, not assumed to have passed. Metrics use the same units, thresholds, and denominator across comparisons.

Example: interpolation that creates fractional class IDs in a segmentation mask requires checking preprocessing before blaming the model.

## Boundary

Return to the core with the report or blockers. Do not dispatch other skills or agents, choose models, schedule retraining, revise global benchmarks, advance phases, or modify global state. Use only the assigned inputs, tools, and output paths.
