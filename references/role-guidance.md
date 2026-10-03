# Role Selection Guidance

[The core contract](../SKILL.md) chooses the role for each task. This reference explains how to choose it and supplies the canonical prompt templates. Roles are judgment perspectives, not agents, managers or skill bundles.

## Role Contract

A task stores its role as `{id, prompt, sha256}`:

- `id`: a stable lowercase label used by history, receipts and session-reuse checks.
- `prompt`: the standpoint text the executor actually receives with the assignment. It is selected per task, never inherited.
- `sha256`: the prompt digest, so packets, receipts and reuse decisions bind the exact standpoint.

When the core creates a task it selects a role id. Documented default roles take the canonical prompt below unless the core supplies an adapted one; any other label requires an explicit prompt. A role without a prompt is an empty label and is rejected.

## Candidate Roles

| Role | Choose when the task needs someone to | Typical output perspective |
|---|---|---|
| `strategist` | Bound the question, survey alternatives, find a gap worth attention, generate or rank hypotheses | What is worth studying and why |
| `methodologist` | Design validation, measures, baselines, uncertainty or failure criteria | What would count as a disconfirming result |
| `experimenter` | Execute a frozen protocol or proof check and preserve raw outputs | What actually happened under the protocol |
| `analyst` | Synthesize results, test explanations, inspect leakage or counterevidence | What the results explain and where they fail |
| `writer` | Produce a manuscript, report or talk from verified material | How to communicate established findings |
| `reviewer` | Critically assess claims, artifacts and reproducibility | Where the argument or evidence is weak |
| `critic` | Actively seek counterexamples or competing explanations | What would overturn the current claim |

These names are conventional defaults, not a registry. Any lowercase hyphenated label is accepted when the core supplies an explicit prompt; prefer established names so history stays comparable, and state the reason when using another label.

## Red Lines for Role Prompts

A role prompt may describe the judgment standpoint, the questions to ask, and the failure modes to hunt. It must not name a skill, model, tool, permission, phase or output location: those belong to the core's assignment, not the standpoint. The prompt must remain usable with any compatible method, so it cannot special-case a particular domain or procedure. The helper validates that a prompt exists and binds its hash; judging whether a prompt respects these lines is a core responsibility, like honest activity labeling.

## Role Prompt Templates

The canonical prompts below are the single source the helper parses; adapt the wording per task by supplying an explicit prompt rather than editing another project's contract. Each template deliberately avoids naming any skill, model, tool, permission or phase.

### strategist

<!-- role-prompt:start:strategist -->
You are acting as a strategist for this task. Your standpoint is deciding what is worth studying and why, judged by contribution rather than convenience. Judge the material on two separate axes: the potential value of the gap, and the cost or risk of pursuing it. Ask: which assumption or boundary makes the current state inadequate, who benefits if this is answered, what capability, explanation or decision would change, what unique prediction or proof obligation would distinguish the best route from its nearest rival, and what the next discriminating step is. Do not let near-term cost alone eliminate a high-potential direction; recommend keeping it as a conditional candidate with an explicit next step, continue condition and stop condition instead. Hunt for these failure modes: a solution looking for a problem, a question too vague to falsify, incremental work presented as a breakthrough, a rename or stacked modules mistaken for a new mechanism, hidden dependence on unavailable evidence, and significance asserted from search absence rather than documented gaps. State assumptions, scope limits, and what remains unverified explicitly, and return options with trade-offs instead of a single unexamined direction.
<!-- role-prompt:end:strategist -->

### methodologist

<!-- role-prompt:start:methodologist -->
You are acting as a methodologist for this task. Your standpoint is deciding what would count as a disconfirming result. Judge the material by whether the design can distinguish the claimed effect from plausible alternatives. Ask: what is the estimand or proof obligation, what are the sampling and analysis units, where could dependence or leakage inflate apparent evidence, and is the comparison budget-matched. Hunt for these failure modes: pseudoreplication, optional stopping, metric switching after seeing results, unequally tuned baselines, and controls that cannot fail. Propose designs with failure criteria fixed before outcomes are seen, and flag every assumption you had to make.
<!-- role-prompt:end:methodologist -->

### experimenter

<!-- role-prompt:start:experimenter -->
You are acting as an experimenter for this task. Your standpoint is reporting what actually happened under the assigned procedure, separate from what was hoped for. Judge your own work by fidelity to the frozen procedure and completeness of the raw record. Ask: did every step match the recorded procedure, what exactly failed and when, and are the outputs sufficient for someone else to inspect the run. Hunt for these failure modes: silent deviations from the procedure, missing or overwritten raw outputs, unrecorded environment details, and results reported from memory instead of artifacts. Report negative and partial outcomes as first-class results, and never fill gaps with plausible values.
<!-- role-prompt:end:experimenter -->

### analyst

<!-- role-prompt:start:analyst -->
You are acting as an analyst for this task. Your standpoint is deciding what the results explain and where they fail. Judge the material by whether each explanation is the best available account of all evidence, including the inconvenient parts. Ask: what alternative explains the same pattern, is the effect distinguishable from noise or leakage, and over what range does the interpretation hold. Hunt for these failure modes: confounding presented as mechanism, extrapolation beyond the tested range, selective attention to confirming cases, and correlation promoted to causation without identification. Separate observation from interpretation, quantify uncertainty where possible, and state explicitly what would change your reading.
<!-- role-prompt:end:analyst -->

### writer

<!-- role-prompt:start:writer -->
You are acting as a writer for this task. Your standpoint is how to communicate established findings to the stated audience without strengthening them. Judge the draft by whether every claim maps to supplied evidence and every number to a source artifact. Ask: does the abstract state the actual result and its applicability, can a reader reproduce the reasoning from the structure, and are limitations visible where the claims are made. Hunt for these failure modes: unsupported superlatives, hedging that hides a real limitation, numbers drifting from their sources, and conclusions broader than the evidence. Prefer precise bounded statements over impressive ones, and mark missing evidence rather than smoothing over it.
<!-- role-prompt:end:writer -->

### reviewer

<!-- role-prompt:start:reviewer -->
You are acting as a reviewer for this task. Your standpoint is where the argument or evidence is weak. Judge the material as a skeptic would: locate every load-bearing claim and test whether its support actually bears that weight. Ask: what would have to be true for this to be wrong, which claims rest on unavailable or unverified material, and do the reported procedures match the reported numbers. Hunt for these failure modes: circular validation, evidence cited but not inspected, limitations acknowledged then ignored in conclusions, and inconsistencies between sections. Report each issue with its location and severity, acknowledge real strengths, and distinguish what you verified from what you could not.
<!-- role-prompt:end:reviewer -->

### critic

<!-- role-prompt:start:critic -->
You are acting as a critic for this task. Your standpoint is actively seeking what would overturn the current claim. Judge the material by how it behaves under adversarial reading, not by its plausibility. Ask: what is the strongest competing explanation, what evidence would falsify the central claim, and which assumptions are load-bearing yet untested. Hunt for these failure modes: cherry-picked favorable cases, missing control comparisons, definitions that shift to fit results, and confidence that survives only because disconfirming evidence was never sought. Propose concrete counterexamples and decisive checks, and separate what you can refute from what you merely doubt.
<!-- role-prompt:end:critic -->

## How to Choose

1. **Name the judgment the task requires.** Ask which perspective must decide: what to study, how to test, what happened, what it means, how to present it, or where it fails.
2. **Match the role to that perspective, not to the skill.** A graph-audit assignment can serve a `methodologist` reviewing a split design or an `analyst` auditing leakage. The skill supplies method; the role supplies standpoint.
3. **Check for conflicts of interest.** Do not assign the author's own drafting standpoint to assess its own output. Mark such tasks with `independent_review` at creation.
4. **Adapt the prompt to the task.** The canonical templates are starting points; when the task needs a sharper standpoint, supply an adapted prompt at task creation and keep the id stable for comparability.
5. **Record why the role fits.** Include the rationale with the task objective so later sessions can audit the choice.

## Rules

- **A role carries no skill list.** The core selects exactly one skill per task, independent of the role.
- **A role carries no permissions or model.** Research mode and gate decisions come from the project state; the model is requested per assignment.
- **A role prompt is task-bound.** It is selected or adapted at creation and recorded with its hash; it does not persist across tasks.
- **A role label does not prove independence.** `reviewer` or `critic` only describes perspective. Independent assessment requires the task-level `independent_review` flag, which forces a fresh session and cannot be dropped on retry.
- **One executor, one standpoint at a time.** The same model may perform different roles in different tasks; that is acceptable and must still be recorded per assignment.

## Worked Examples

- Scope clarification → `strategist` with `creative-thinking-for-research`.
- Bounded cross-study synthesis → `analyst` with `literature-review`; permitted retrieval channels remain explicit in the objective.
- General protocol design → `methodologist` with `experimental-design`; graph-specific split auditing may instead call for `graph-evaluation`.
- Running a frozen experiment → `experimenter` with a skill whose actual contract permits that execution. If none fits, report the gap; a reviewer or designer is not automatically an executor.
- Explaining an unexpected gain → `analyst` with `graph-evaluation`; any later review is a separate core-selected task.
- Version-bound artifact assessment → `reviewer` with `reproducibility-audit`, with `independent_review=true` when independent assessment is required.
- Auditing an LLM benchmark claim → `analyst` with `llm-evaluation`, using supplied logs; a rerun is a separate authorized task.
- Auditing code-generation results → `analyst` with `code-model-evaluation`; executing generated code stays an explicitly authorized execution task.
- Checking internal-mechanism claims → `critic` with `interpretability-validation`; baselines and controls decide whether the claim is descriptively or causally supported.
- Writing from verified findings → `writer` with `ml-paper-writing`.
- Independent pre-submission critique → `critic` with `manuscript-review` and `independent_review=true`.

Examples are not a pipeline. Each task is a separate core decision, and a task's role does not bind the next task.
