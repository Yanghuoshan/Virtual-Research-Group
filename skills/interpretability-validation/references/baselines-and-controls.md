# Baselines and Controls Catalog

An interpretability result without a matched baseline is not evidence. Select the baseline that matches the claim, then ask whether the result beats it. The cheapest control for attribution claims is usually shuffled or permuted activation; try it before more elaborate baselines.

## Catalog

| Baseline / control | What it rules out | Typical use |
|---|---|---|
| Random directions or untrained SAE | Structure claimed to be special about the learned feature | Feature identity claims |
| Shuffled or permuted activations | Effects driven by activation magnitude or distribution, not content | Attribution and patching claims |
| Resampled activations from other inputs | Effects driven by generic activation statistics | Patching with resample ablation |
| Control tasks for probes | Probe accuracy reflecting task-relevant or trivial signal | Selectivity of linear probes |
| Corrupted-run controls | Patching effect caused by the corruption itself | Causal patching designs |
| Simpler lexical, positional or n-gram features | A complex mechanism claim explained by surface features | Circuit and feature claims |
| Alternative sites or layers | Effect unique to the claimed component | Localization claims |
| Held-out features and examples | Selection or overfitting to chosen examples | Generalization of a feature description |

## Matching Rules

1. The baseline must differ only in the property under test; otherwise the comparison is uninterpretable.
2. Report the baseline's own performance: if a random direction explains the same behavior, the claim fails.
3. Run the baseline on the same inputs, metric and number of examples as the claimed result.
4. Where several baselines apply (for example random directions and control tasks), report all of them; passing one does not satisfy the others.
5. An absent baseline is a blocker for the affected claim, not a minor limitation.

## Reporting Table

| Claim | Baseline used | Baseline result | Claimed result | Verdict |
|---|---|---|---|---|
| Feature F responds to concept X | Random direction + untrained SAE | Random: near zero activation alignment | F: high alignment on held-out examples | Descriptively supported |
| Component C necessary for behavior Y | Corrupted-run control | Control recovers behavior without patching C | Patching C restores 60% | Necessity weakened |

Report the verdict per claim, with the baseline numbers that produced it.
