# Role Selection Guidance

[The core contract](../SKILL.md) chooses the role for each task. This reference explains how to choose it. Roles are judgment perspectives, not agents, managers or skill bundles.

## Candidate Roles

| Role | Choose when the task needs someone to | Typical output perspective |
|---|---|---|
| `strategist` | Bound the question, survey alternatives, generate or rank hypotheses | What is worth studying and why |
| `methodologist` | Design validation, measures, baselines, uncertainty or failure criteria | What would count as a disconfirming result |
| `experimenter` | Execute a frozen protocol or proof check and preserve raw outputs | What actually happened under the protocol |
| `analyst` | Synthesize results, test explanations, inspect leakage or counterevidence | What the results explain and where they fail |
| `writer` | Produce a manuscript, report or talk from verified material | How to communicate established findings |
| `reviewer` | Critically assess claims, artifacts and reproducibility | Where the argument or evidence is weak |
| `critic` | Actively seek counterexamples or competing explanations | What would overturn the current claim |

These names are conventional defaults, not a registry. Any lowercase hyphenated label is technically accepted; prefer established names so history stays comparable, and state the reason when using another label.

## How to Choose

1. **Name the judgment the task requires.** Ask which perspective must decide: what to study, how to test, what happened, what it means, how to present it, or where it fails.
2. **Match the role to that perspective, not to the skill.** A `graph-evaluation` skill can serve a `methodologist` reviewing a split design or an `analyst` auditing leakage. The skill supplies method; the role supplies standpoint.
3. **Check for conflicts of interest.** Do not assign the author's own drafting role to assess its own output. Mark such tasks with `independent_review` at creation.
4. **Record why the role fits.** Include the rationale with the task objective so later sessions can audit the choice.

## Rules

- **A role carries no skill list.** The core selects exactly one skill per task, independent of the role.
- **A role carries no permissions or model.** Authorization and budget come from the project state; the model is requested per assignment.
- **A role label does not prove independence.** `reviewer` or `critic` only describes perspective. Independent assessment requires the task-level `independent_review` flag, which forces a fresh session and cannot be dropped on retry.
- **Roles do not persist across tasks.** Each task gets its own explicit role; a later task in the same phase may use a different role.
- **One executor, one role at a time.** The same model may perform different roles in different tasks; that is acceptable and must still be recorded per assignment.

## Worked Examples

- Scope clarification → `strategist` with `creative-thinking-for-research`.
- Bounded cross-study synthesis → `analyst` with `literature-review`; retrieval permissions remain explicit.
- General protocol design → `methodologist` with `experimental-design`; graph-specific split auditing may instead call for `graph-evaluation`.
- Running a frozen experiment → `experimenter` with a skill whose actual contract permits that execution. If none fits, report the gap; an evaluator or designer is not automatically an executor.
- Explaining an unexpected gain → `analyst` with `graph-evaluation`; any later review is a separate core-selected task.
- Version-bound artifact assessment → `reviewer` with `reproducibility-audit`, with `independent_review=true` when independent assessment is required.
- Auditing an LLM benchmark claim → `analyst` with `llm-evaluation`, using supplied logs; a rerun is a separate authorized task.
- Auditing code-generation results → `analyst` with `code-model-evaluation`; executing generated code stays an explicitly authorized execution task.
- Checking internal-mechanism claims → `critic` with `interpretability-validation`; baselines and controls decide whether the claim is descriptively or causally supported.
- Writing from verified findings → `writer` with `ml-paper-writing`.
- Independent pre-submission critique → `critic` with `manuscript-review` and `independent_review=true`.

Examples are not a pipeline. Each task is a separate core decision, and a task's role does not bind the next task.
