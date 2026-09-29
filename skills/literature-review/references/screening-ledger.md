# Deduplication, Screening and the Record Ledger

Screening decides which records enter the review. The ledger makes those decisions auditable and keeps counts honest.

## Normalize Identities Before Counting

Resolve records to studies, not files:

| Situation | Handling |
|---|---|
| Same DOI/ID from two sources | One study record; record both source IDs |
| Preprint and published version | One study; link versions, mark the version actually screened |
| Revision, erratum, retraction | Link to the study; mark status and screened version |
| Fuzzy match (title + authors + year) | Manual confirmation; do not auto-merge on title alone |
| Same study reported twice (paper + thesis) | One study, two reports; keep the richer report as primary |

Report counts by records retrieved, by unique studies, and by included studies. Mixing these numbers is the most common reporting error.

## Two-Stage Screening

1. **Calibrate:** pilot-screen a sample against the criteria; refine ambiguous wording and record the change.
2. **Title/abstract stage:** apply eligibility criteria conservatively; uncertainty is "uncertain", not "exclude".
3. **Full-text stage:** confirm population, design, outcome and reporting detail; record exclusion reason with the locator that justifies it.

If the acceptance criteria require duplicate independent screening, record both screeners' decisions and the reconciliation rule. With a single screener, state that as a limitation rather than implying dual review. A single screener cannot manufacture a second reviewer; do not report dual screening that did not occur.

## Decision Codes

| Code | Meaning | Reporting treatment |
|---|---|---|
| `included` | Passes all criteria at this stage | Counted at that stage |
| `excluded` | Fails a criterion; reason required | Counted with reason code |
| `uncertain` | Insufficient information | Held for full text or core clarification |
| `duplicate-of` | Same study as an existing record | Excluded from study counts, retained as a report link |
| `unobtainable` | Full text unavailable | Reported separately; never "excluded" or "negative" |
| `awaiting-access` | Requested through the core | Open item, not a decision |

## Exclusion Reason Taxonomy

Use a fixed vocabulary for true exclusions so counts aggregate: wrong population/task; wrong study design; wrong outcome or metric; wrong comparison or baseline; insufficient reporting detail; not peer reviewed (only when the criteria exclude it); language; out-of-date scope. `unobtainable` and `duplicate-of` are decision codes, not exclusion reasons: keep them out of exclusion counts and report them separately. Always store the specific justification alongside the code.

## Ledger Schema

| Column | Purpose |
|---|---|
| `record_id` | Stable local identifier |
| `source` and `source_ids` | Provenance (DOI, arXiv ID, Anthology ID) |
| `title`, `authors`, `year` | Display identity |
| `version_of` | Links duplicates/versions to one study |
| `stage` | Title/abstract or full text |
| `decision` | Code from the table above |
| `reason_code` and `reason_detail` | Why, with locator |
| `locator` | Page, section, table or file supporting the decision |
| `screened_by`, `date` | Audit trail |
| `notes` | Open questions for the core |

Keep the ledger at an assigned path together with the raw exports. The ledger is evidence, not scratch space.

## Counts and Flow

Reconcile counts across stages and sources. Report only stages actually performed:

```text
Records retrieved: 1,240 (source A 900, source B 340)
Duplicate reports removed from study counts: 190 (retained as report links)
After deduplication: 1,050 studies
Title/abstract screened: 1,050 → excluded 910, uncertain 40, advanced 100
Full texts assessed: 140 (100 advanced + 40 uncertain) → excluded 95
Unobtainable full texts: 12 (not treated as negative evidence)
Included studies: 33
Database registries searched: not performed
```

Rules: an unknown count stays "not performed" or "unknown"; never substitute zero. Duplicates excluded from study counts must still appear as report links. A flow diagram is optional; the numbers must reconcile with the ledger.

## Audit Trail

Preserve raw exports, screening tool/rubric version, criteria version and amendment dates. Re-screen affected records whenever criteria change after screening begins.
