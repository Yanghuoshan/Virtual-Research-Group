# Dependency and Provenance Manifest

A reproduction claim is only as complete as its dependency inventory. Listed artifacts that match their hashes can still hide missing dependencies.

## Inventory Fields

| Field | Content |
|---|---|
| Path | Project-relative path |
| `sha256` | Actual hash of the current file |
| Role | Claim source, protocol, raw result, derived table, figure, manuscript |
| Versions | Data/code/environment identifiers, model or service version |
| Seeds and configuration | Values that affect the result |
| Acquisition | How the artifact was produced or obtained |
| Status | Present, changed, missing, or unhashed |

## Chains to Trace

1. Claim → manuscript statement → table/figure → derived result file → raw run outputs.
2. Raw outputs → run code/config → environment → data/splits → source data.
3. Each link: is the dependency listed, hashed and present?

Break the chain at any unlisted or missing link, and mark every downstream claim as unverifiable at that link.

## Missing or Unlisted Dependencies

| Situation | Treatment |
|---|---|
| Listed but hash changed | Changed subject; the binding is stale |
| Listed but file absent | Missing evidence; blocker |
| Not listed but inferable | Coverage gap; add to the manifest proposal |
| Not listed and unknown | Unresolved dependency: report as a limitation, never as satisfied |

Do not create replacement files, and do not infer content from narrative description. Absence is a finding.

## Environment and Services

Record language/runtime versions, package manifests, container digests, hardware assumptions, external services/APIs and their access dates, and any network-dependent step. A result depending on an unavailable service is not reproducible from the artifacts alone; state that as a limitation.

## Minimal Manifest

Every inspected artifact with `path` and `sha256`, the claim-to-artifact map, the environment summary, and an explicit list of unresolved dependencies.
