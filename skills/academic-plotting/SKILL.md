---
name: academic-plotting
description: Use when supplied quantitative research results need accurate, reproducible publication-quality charts with explicit uncertainty and provenance.
---

# Quantitative Research Plotting

Transform measured data into readable charts without changing the scientific claims. Adapted from Orchestra Research's quantitative plotting guidance. Architecture illustration and model-based image generation are outside this skill.

## Inputs

Data files and their provenance, metric definitions and units, grouping variables, uncertainty semantics, requested comparison, target dimensions, allowed local plotting tools, and output paths.

## Method

1. Inspect schema, missingness, units, repeated runs, and aggregation level. Distinguish samples from seeds and independent experiments. Do not pool dependent observations as independent repetitions.
2. Match representation to the question: line for ordered progression, paired points for matched comparisons, distribution plots for variability, heatmaps for matrices, and grouped bars for category comparisons. Prefer actual run points when a mean hides variation.
3. Use declared aggregation and error intervals only. Do not smooth away failures or fabricate missing values. Annotate exclusions, truncation, normalization, and log scales.
4. Use consistent semantic colors, colorblind-safe palettes, readable labels at final size, and explicit metric directions. Do not highlight a preferred method by distorting axes.
5. Generate deterministic local plotting code with input paths and processing decisions recorded. Export vector figures for charts and raster previews if requested, using only tools permitted in the assignment.
6. Check values against raw data and inspect the rendered figure. Return failed checks instead of altering the data to improve appearance.

## Outputs

Figure files, plotting source, captions, data-to-figure provenance, and a validation note at assigned paths. State whether rendering was actually performed.

## Checks

- Confidence intervals, standard errors, and standard deviations are labeled distinctly.
- Axis limits and baselines do not hide meaningful variation.
- Units and averaging definitions match the supplied protocol.
- No claim, run, or uncertainty estimate is invented.

Example: paired seed comparisons should retain pair identity; independently sorting two method vectors destroys the comparison.

## Boundary

Return to the core with figures or missing-data/tool blockers. Do not dispatch other skills or agents, choose models, call image-generation services, schedule new experiments, change global findings/state, advance phases, or redefine evaluation. Use only the assigned artifact paths.

## Local References

- [Quantitative plot patterns](references/data-visualization.md)
- [Publication styling](references/style-guide.md)
