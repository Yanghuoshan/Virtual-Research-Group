# Research Phase Guidance

[The core contract](../SKILL.md) keeps the authoritative phase table and the rule that only a separate core decision changes phase. This reference explains how to work within those phases.

## What Each Phase Is For

The eight phases below are the authoritative names in the [core contract](../SKILL.md) phase table; a phase is a goal with exit criteria, never a skill, role, model or task bundle.

- **scope:** bound the research question and constraints; verify what is already known; separate evidence from conjecture. Do not assert novelty from search absence alone.
- **ideation:** develop, compare and rank falsifiable hypotheses with mechanisms, falsifiers and evidence limits.
- **design:** define the primary measure or proof obligation, baseline or known bound, validation design, uncertainty treatment, failure criteria and budget. Evidence standards are common core rules; specialists contribute domain-specific checks.
- **execute:** accept a frozen protocol and the required authorization, run the bounded experiment or proof check, preserve raw outputs, and compare with the protocol. Missing executors are capability gaps, not permission to invent results.
- **synthesize:** inspect convergence or validity, leakage, baseline reproduction, uncertainty and counterevidence. Ask what a result explains. The core alone promotes checked findings to `findings.md` and chooses whether to deepen, broaden, pivot or conclude.
- **write:** communicate established findings to the stated audience with a traceable, reviewable draft.
- **review:** critically assess claims and reproducibility; route unresolved issues back rather than silently accepting them.
- **complete:** preserve an accepted research outcome with its evidence and audits. Reopening requires a new core scope decision.

Working phases may be grouped when planning: scope and ideation form one question-shaping loop, design and execute form the inner loop, and write and review form the communication loop. The grouping is a planning convenience; the recorded phase is always one of the eight names above.

## Allowed Transitions

| From | To |
|---|---|
| scope | ideation |
| ideation | scope, design |
| design | ideation, execute |
| execute | design, synthesize |
| synthesize | ideation, design, write |
| write | synthesize, review |
| review | write, synthesize, design, complete |
| complete | scope |

No other transition is legal. `complete → scope` is the only way to reopen finished work, and it takes a fresh scope decision rather than a continuation.

## Example Tasks per Phase

Example scope tasks: clarify the question, check existing answers, assess data availability, and propose success criteria. Example ideation tasks: generate candidates, reformulate the problem, verify novelty evidence, critique mechanisms, and compare validation costs.

These are optional examples, not a fixed checklist. Each task has a distinct artifact and acceptance criterion; ordinary file reads or clarification turns are steps within a task, not separate tasks.

## Using the Exploration Framework

[IDEA exploration and formulation](idea-exploration.md) describes four judgments — opportunity, question, route and contribution — for the question-shaping loop. They are reusable views, not extra phases or a mandatory sequence, and the core decides which one a task needs:

- **scope** uses opportunity and nearest-neighbor analysis to separate a documented gap from a search miss. A pending opportunity may stay labeled as unverified while the question is still being bounded; reaching `ideation` does not require pretending the unknowns are resolved.
- **ideation** uses the question and route judgments to develop competing mechanisms, judge potential and cost on separate axes, and keep a high-potential but expensive route as a conditional candidate with an explicit next discriminating step. Contribution framing may begin here so that weak claims are caught before design.
- **design** uses the contribution judgment to map each load-bearing claim to controls, a proof obligation or a counterexample strategy, so the planned evidence actually supports the claim rather than a nearby one.

Returning is expected, not a failure: a contradicted assumption sends work back to scope, a candidate that cannot be discriminated sends it back to ideation, and a claim whose evidence does not exist yet returns to design or ideation. The recorded phase still changes only through a separate core decision.

## Cross-Phase Tasks

A citation check during writing or a split audit during execution is another task, not a project-wide phase change. Tasks may remain planned or blocked across a justified phase change; their creation phase is provenance, not a routing restriction.

Stop the running executors before changing phase, and keep the project status `active`; a stopped project records no phase decision, and all unresolved blockers stop phase decisions even when an open task declares it will resolve one. To close research, resolve or explicitly cancel all open tasks and recheck both evidence and final-review audits.

`stopped` is a project status value, not a phase, and is set by `project-status`. It closes new tasks, handoffs, phase and gate decisions while preserving tasks, audits and evidence. Planning-only work may stop this way without claiming completed research, and only `project-status --to active` reopens the project.

## Deciding a Transition

Check legality against the Allowed Transitions table above, then use the phase goal and exit criteria as scientific judgments, not as automatic consequences of finishing one task. Record rationale and the evidence that supports the decision. Reusing a phase for another bounded task is allowed except after completion; completion requires a new scope decision to reopen.
