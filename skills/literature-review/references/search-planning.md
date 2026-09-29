# Search Planning and Query Logging

Plan and record a reproducible search before screening. A plan is not an executed search; label unexecuted work as such.

## Frame the Question as Eligibility Criteria

Translate the assigned question into explicit eligibility blocks before writing queries. Adapt the PICO pattern:

| Block | Question | ML/AI example |
|---|---|---|
| Population / material | Which tasks, datasets, systems or subjects? | Inductive node classification on citation graphs |
| Index concept | Which method, intervention or exposure? | Message-passing with edge dropout |
| Comparison | Compared with what? | Matched GNN without dropout, or non-graph baseline |
| Outcome | Which measured result and metric? | Macro-F1 under a declared split, with seed variance |
| Study design | Which designs are eligible? | Empirical benchmark study; proofs excluded unless assigned |

Record exclusions explicitly (designs, languages, date ranges, document types). Vague criteria produce unstable screening and unreproducible counts.

## Decompose Concepts and Control Vocabulary

For each block, list natural-language synonyms, acronyms and expansions, spelling variants, singular/plural forms and stemming limits. Vendors differ on truncation and proximity operators, so keep a vendor-neutral master expression and a per-source translation:

```text
block_method: ("graph neural network*" OR GNN OR "message passing" OR "graph convolution*")
block_task:   ("node classification" OR "node labeling")
block_outcome:(generalization OR "inductive" OR "unseen graph*")
query:        block_method AND block_task AND block_outcome
```

Combine blocks with Boolean operators: AND between blocks, OR within a block. Keep the vendor translation next to the master expression so the search can be rerun.

Common failures to avoid:

- One spelling or acronym only, silently dropping relevant work.
- Over-narrow proximity or phrase requirements that exclude equivalent phrasing.
- Concept blocks joined with OR instead of AND, which inflates hits without improving recall.
- Reusing a query copied from another review without checking that its scope matches the assigned question.

## Select Sources and Declare Their Bias

Choose sources by coverage, not convenience, and record what each source does not cover:

| Source type | Typical use | Coverage limitation |
|---|---|---|
| General scholarly indexes | Broad cross-disciplinary recall | Vendor-dependent indexing and lag |
| Preprint servers (arXiv and similar) | Recent ML work | Not peer reviewed; versions supersede each other |
| Community indexes (DBLP, ACL Anthology, IEEE/ACM) | Venue-complete ML/NLP coverage | Weak for non-English or grey literature |
| Domain-specific bibliographic databases | Clinical, social or scientific domains | Terminology differs from ML vocabulary |
| Grey literature and registries | Unpublished or negative results | Hard to search systematically |
| Citation chaining | Supplementary recall | Inherits the seed set's selection bias |

Overlap between sources is expected; count duplicates once in the ledger, not once per source.

## Apply Limits Deliberately

Every filter narrows coverage and must be justified by the assignment: date range, language, document type, peer-review status, availability, and citation-count thresholds. A citation-count or venue filter is a coverage limit, not a quality signal. Record the filter and, where possible, the number of records removed. A limit introduced to keep screening feasible is still a coverage limitation.

## Run Only Within Assigned Channels

Execute searches only through core-assigned servers/tools with `external_services` authorization. For each run, save the raw response at an assigned path and log:

| Field | Example |
|---|---|
| Source and interface/version | Vendor web UI, API v2, 2026-09-29 |
| Exact query string | Full translated string, not a paraphrase |
| Filters and limits | 2018-2026; English; article/inproceedings |
| Result count and export count | 1,240 hits; 1,240 exported |
| Pagination or truncation | First 500 only: truncated |
| Raw response path | `literature/raw/<source>-<run-id>.json` |

A truncated or failed run is a coverage limitation and a blocker candidate, never a zero result.

## Amendments

Version the plan. When the question, criteria or sources change, record the amendment rationale and re-run the affected searches; re-screen records that the change could affect. Do not silently mix records retrieved under different criteria.

## Coverage Labels

Use exact wording in the final report:

Canonical wording lives in [extraction and reporting](extraction-and-reporting.md); use it verbatim so units do not drift. Typical forms:

- "Supplied-corpus review of 33 studies; no database search performed."
- "Single-index search with documented query log; other sources not covered."
- "Search planned but not executed: no authorized retrieval channel."

Do not use "systematic", "comprehensive" or "exhaustive" unless the corresponding multi-source search was actually performed and logged.
