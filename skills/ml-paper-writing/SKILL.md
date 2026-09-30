---
name: ml-paper-writing
description: Use when verified AI or machine-learning claims, results, and source material need a manuscript or section for a specified audience and venue.
---

# Evidence-Based ML Manuscript Writing

Write the assigned manuscript artifact from supplied, verified material. Adapted from Orchestra Research; retained writing references remain attributed resources, not authority to expand the task.

## Inputs

The approved contribution, claim-to-evidence map, protocols and result references, verified bibliography, target venue/year or audience, scope (section or full draft), format, output path, and acceptance criteria. For an outline-only assignment, require explicit labeling of all missing evidence.

## Method

1. Build an argument outline: problem and gap → specific contribution → mechanism → evidence → scope and limitations. Do not decide a new research contribution to make writing easier.
2. Map every substantive claim to supplied evidence. Keep observed, inferred, and conjectured statements distinct. Report contradictory or missing results rather than filling them with plausible values.
3. Draft the requested scope. A concise abstract states the result, difficulty, approach, evidence, and applicability. An introduction defines the gap and measurable contributions. Methods expose assumptions and reproduction details. Results identify which claim each comparison tests.
4. Report the actual validation design, number of runs, meaning of uncertainty intervals, baseline tuning budget, and negative results. Do not replace standard deviation with standard error without explanation.
5. Organize related work by assumptions and mechanisms, using supplied verified citations. Mark unsupported citations as `[CITATION NEEDED]` and return the gap; bibliography discovery is not part of this writing assignment.
6. Apply [writing guidance](references/writing-guide.md) and the relevant [checklist](references/checklists.md). No LaTeX template is bundled; obtain the current author kit from the venue's official source listed below and copy it only to the assigned artifact location. Do not edit its style files to evade limits. Compile only if the task permits the required local toolchain; otherwise return source and a clear uncompiled status.
7. Return the draft, claim coverage, unresolved issues, and actual validation/compilation status. Never submit it to a venue automatically.

## Outputs

A versioned manuscript or section, bibliography references, a claim-to-section map, and a list of evidence/formatting gaps within the assigned output scope.

## Checks

Every number matches a source artifact; metric direction and units are explicit; figure captions stand alone; limitations do not contradict headline claims; bibliography entries are verified; current venue requirements come from supplied or authorized authoritative material, not historical templates alone.

Example: a mean improvement with overlapping intervals supports a bounded observed difference, not an unconditional superiority claim.

## Boundary

Return to the core with the draft or a blocked status. Do not dispatch other skills or agents, select models, run new experiments, schedule revisions, submit manuscripts, advance phases, or modify global findings/state. A systems-specific task outside this contract is returned, not redirected by this skill.

## Local References

- [Writing principles](references/writing-guide.md)
- [Venue checklists](references/checklists.md)
- [Reviewer criteria](references/reviewer-guidelines.md)
- [Source attribution](references/sources.md)

## Venue Templates (External)

Download the current author kit from the official source before formatting; page limits and style files change every year, and no template is redistributed with this skill.

- ICML: https://icml.cc/Conferences/2026/AuthorInstructions
- ICLR: https://github.com/ICLR/Master-Template
- NeurIPS: https://neurips.cc/
- ACL: https://github.com/acl-org/acl-style-files
- AAAI: https://aaai.org/authorkit26/
- COLM: https://github.com/COLM-org/Template

Retrieving a template requires the core's authorization for external access. A missing template or toolchain is a blocker returned to the core, not a reason to install packages, pick another venue, or redirect the task.

These documents refine writing technique only. Their historical examples do not authorize external setup, extra research, or changes to the assignment.
