---
name: citation-verification
description: Use when specific paper identities, bibliographic entries, or attributed claims need verification against supplied sources or authorized scholarly retrieval.
---

# Citation Identity and Claim Verification

Verify specific references and what they support. Do not infer correctness from a plausible title or citation count.

## Inputs

Candidate references, claims attributed to them, source documents or identifiers, permitted retrieval channels, output paths, and the required verification scope.

## Method

1. Resolve identity using title, authors, year, DOI/arXiv ID and version. Distinguish preprint, accepted and corrected versions; do not merge distinct papers by similar titles.
2. Check authoritative metadata from supplied source material or the authorized retrieval channel. Cross-check discrepancies and preserve the source URL and verification date.
3. Read the relevant passage, theorem, figure or experiment. Record a locator and whether the attributed claim is explicit, inferred, contradicted, or not found.
4. Retrieve bibliographic metadata rather than synthesizing it from memory. Preserve title capitalization, author order, venue and version; use stable identifiers.
5. Classify unresolved cases separately: inaccessible full text, ambiguous identity, missing metadata, or unsupported claim. Use `[CITATION NEEDED]` instead of fabricating a substitute.
6. Return a verified bibliography and claim-source table, marking the precise verification level. Metadata existence alone does not establish claim support.

## Outputs

Bibliography records with provenance, per-claim source locations and verification status, and a list of unresolved references at assigned paths.

## Checks

No invented DOI, author, venue or year. No abstract-only assertion disguised as full-text verification. An API response is metadata evidence, not a scientific endorsement.

Example: a paper demonstrating a method on one benchmark does not support a citation claiming general superiority across tasks.

## Local Reference

[Historical retrieval and bibliography examples](references/citation-workflow.md) illustrate technical operations within the channels already assigned by the core. Missing dependencies or coverage are blockers, not permission to install or choose a replacement service.

## Boundary

Return to the core with verified entries and unresolved cases. Do not dispatch other skills or agents, choose models, install retrieval services, broaden the literature assignment, schedule follow-up searches, or modify global state. Use only retrieval explicitly permitted by the core's task.
