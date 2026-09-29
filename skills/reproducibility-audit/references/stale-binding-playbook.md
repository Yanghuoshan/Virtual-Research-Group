# Stale and Unverifiable Bindings

A prior approval binds specific versions. When those versions change, the approval no longer covers the current artifacts.

## Decision Table

| Observed | Status of prior approval | Action |
|---|---|---|
| All subject hashes unchanged | Still bound | Report as current; no new verification implied |
| Manuscript or findings hash changed | Stale for affected claims | Mark stale, inspect the change, propose a new binding |
| Raw evidence hash changed | Stale for dependent claims | Mark stale; recompute or request the affected outputs |
| Protocol changed | Stale; comparison to the frozen protocol invalid | Report the mismatch; the core decides |
| Listed file missing | Unverifiable | Blocker; do not substitute another file |
| New dependency discovered | Coverage gap | Add to the manifest and re-assess affected claims |
| Only formatting/comments changed | Still substantively bound | State the assessment and the evidence for it |

## What Never to Do

- Refresh a hash so the audit "passes" again.
- Delete or overwrite the prior audit to remove the conflict.
- Declare the project verified because the remaining listed files match.
- Treat an unchanged hash as proof the science is correct.
- Change approval state in project files; that is a core operation.

## Handling the Prior Audit

1. Preserve the old audit file and record its identifier and subjects.
2. Diff its subjects against current artifacts; list changed, missing and added items.
3. Map each change to the claims that depend on it; some claims may remain unaffected.
4. Issue a new, version-bound proposal only after substantive reassessment of the affected claims.
5. Keep both audits as history, with the reason for the new one.

## Rerun Proposals

When inspection cannot settle the question, return a proposal containing: procedure identifier, inputs and outputs, environment/dependencies needed, tolerances, resource bounds, safety constraints for any untrusted code, and existing job identifiers that must be reconciled first. Do not start the rerun: execution belongs to a separate authorized experiment task.
