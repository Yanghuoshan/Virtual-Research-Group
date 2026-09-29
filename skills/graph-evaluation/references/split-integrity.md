# Graph Split Integrity

Split validity decides whether a graph result means anything. Check the split before interpreting any metric.

## Setting

| Setting | Permitted access | Common violation |
|---|---|---|
| Transductive node classification | Unlabeled test structure and features | Test labels or validation-selected thresholds entering training |
| Inductive / unseen-graph | No test graph structure at all | Test graphs present during message passing or normalization |
| Link prediction | Train edges plus masks | Reverse edges, filtered positives or temporal order leaking targets |
| Temporal graphs | Past only | Future edges or timestamps used for past predictions |

Name the setting explicitly as transductive, inductive or temporal; accuracy numbers are not comparable across settings.

## Checks

1. **Entity grouping:** split correlated graphs by source entity (protein family, site, patient, molecule scaffold) when the claim is about unseen groups.
2. **Duplicates:** detect isomorphic or duplicated graphs and shared subgraphs across splits.
3. **Reverse-edge leakage:** for undirected link prediction, removing a held-out positive edge while retaining its reverse edge invalidates the split.
4. **Negative sampling:** document the sampler, ratio, hard-negative policy and whether candidate sets are matched across compared methods.
5. **Temporal ordering:** ensure train edges precede validation and test edges; no random split of a temporal graph.
6. **Preprocessing fit:** normalization, feature scaling, graph construction and label-derived features must be fit only on permitted data.
7. **Model selection:** thresholds, hyperparameters and early stopping may use validation only; report test once.

## Reporting

| Item | Content |
|---|---|
| Split method | Rule, grouping key, seed, version |
| Leakage checks performed | Each check with result |
| Violations found | Location, mechanism, affected claim, severity |
| Unresolved | What could not be checked from supplied artifacts |

An unchecked split is a limitation, not a passed check.
