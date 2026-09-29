# Developing a Vertical Specialist Skill

## One Technical Responsibility

Add a direct directory under `skills/`. No domain manifest, capability menu, registry or role preset is necessary. Use a task name such as `graph-evaluation`, not a broad dispatcher such as `graph-research-manager`.

Each entry has only `name` and `description` frontmatter, both single-line values. The name matches the directory and uses lowercase letters, numbers and hyphens. Describe when the skill applies, not a pipeline that invokes other skills.

## Required Sections

- **Inputs:** exact scientific material, assumptions, assigned outputs and tool limits needed to perform the task.
- **Method:** professional steps and decision rules internal to that task, including domain-specific failure modes.
- **Outputs:** artifacts and evidence the core can inspect, including uncertainties and blockers.
- **Checks:** technical validity tests, counterexamples, and conditions under which no conclusion is justified.
- **Boundary:** return to the core; no other skill dispatch, agent creation, model selection, scheduling, phase transitions or global state writes.

Keep common research orchestration in the core. Keep local references and scripts inside the skill's directory. Reading a local methodological reference is not delegation. References must not quietly reintroduce cross-skill dispatch or model-selection instructions.

## Examples of Appropriate Scope

A graph evaluator can distinguish transductive and inductive splits, audit reverse-edge leakage and check ranking metrics. It cannot choose a new model family or commission training. A citation verifier resolves specific identities and claims; it does not run an open-ended literature project. A diagram designer can choose layout and visual encodings but only uses the backend assigned by the core.

A missing prerequisite produces a blocked result with the exact gap. It must not trigger a chain of helper agents or silently expand the task.

## Derive from Research Evidence

1. Extract reusable methods, conditions, failure cases and provenance from completed work; do not turn one project narrative into a universal rule.
2. Write a narrow skill and keep examples in English. Preserve user data and authoritative identifiers without forced translation.
3. Test on a valid input, an out-of-scope input and an incomplete input. Compare behavior with and without the skill.
4. Inspect actual artifacts and tool actions: does the skill return to the core, or try to solve missing prerequisites by dispatching work?
5. Run bundle validation. Add deterministic scripts only for repeated operations and test their technical correctness separately.

Static section and boundary checks are not proof of specialist quality. Record application evidence and remaining limitations. New first-party skills do not require entries in `provenance.json`; that manifest records reused upstream files only.
