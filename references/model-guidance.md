# Model Selection Guidance

[The core contract](../SKILL.md) requests the model for each assignment; the host selects the actual executor. This reference explains how to choose. A model is an execution resource, not a role, skill or phase.

## Match Capability to the Task

| Task character | Prefer a model strong in | Typical examples |
|---|---|---|
| Literature synthesis, long evidence sets | Long context and integration | Scoping reviews, cross-paper comparison |
| Synthesis, critique, independence checks | Reasoning depth and calibration | Explaining results, finding counterexamples |
| Protocol execution, scripted checks | Reliable tool use and instruction following | Running a frozen protocol, metric computation |
| Manuscripts, reports, talks | Sustained long-form coherence and formatting | Drafting sections, LaTeX-heavy output |
| Diagrams and figures | Faithful structured output | Diagram specs, plotting instructions |

Choose by the judgment density of the task, not by its phase. A routine check inside `execute` may need less reasoning than a scoping decision inside `scope`.

## Spend Where Judgment Is Concentrated

- Use the strongest available model where errors are expensive and hard to detect: synthesis, critique, evaluation design and conclusion writing.
- Use cost-efficient models for bounded, mechanical, easily verified work: executing a frozen protocol, formatting, re-checking a fixed procedure.
- Reuse a verified session with the same actual model for compatible follow-up tasks to avoid repeated bootstrap cost, when independence is not required.
- Model choice does not change authorization or budget limits; it only affects how the permitted budget is used.

## Using the `current` Alias

`current` means "retain the host's current model". It is appropriate when:

- the task is low-risk and its output will be verified by the core,
- no independence requirement applies,
- the actual model identity is either known or genuinely irrelevant to the result.

It is not appropriate when a specific capability is required, when comparing outputs across models, or when model identity must be traceable across runs. **`current` is an alias, not evidence that the actual model is unchanged.** The receipt records the actual model; for `current`, the core cannot assert that it matches a previous run.

Independence is established by session isolation, not by the model choice: an independent review requires a core-verified fresh session that excludes the author's drafting history. The `current` alias does not by itself break that isolation, but it does remove model traceability, so pair it with explicit recording of the actual model whenever the result will be compared or audited.

## When the Requested Model Is Unavailable

No silent substitution. If the host cannot provide the requested model:

1. Return the limitation to the core with the reason.
2. Decide explicitly whether another model is acceptable for this task contract.
3. If accepted, issue a **new packet** with the changed model and obtain a **fresh matching receipt**; never reuse the old receipt.
4. If the required model or capability is essential and unavailable, mark the task `blocked` and record the gap instead of downgrading silently.

Changing the model invalidates session-reuse compatibility: `reuse` requires the same skill, role and actual model as the session's latest accepted assignment.

## Independence Is Not Model Switching

Using a different model does not by itself produce an independent review. Independence requires:

- the task-level `independent_review` flag set at creation,
- a `fresh` session,
- excluding the author's drafting history and self-justification.

The same model may be acceptable in a fresh session for an independent review if the core judges it suitable; conversely, a different model in a reused session is not independent.

## Rules

- **Request explicitly per assignment.** The model is not inherited from a role, skill, phase or previous task.
- **Never let a specialist choose or switch models.** Model changes are core decisions recorded in a new packet and receipt.
- **Record the actual model.** `actual_model` in the receipt is what matters; `requested_model` is only a request. For `current`, the recorded actual model is authoritative.
- **No model registry is enforced.** The helper only requires a nonempty request and a matching actual model; it cannot verify provider identity, availability or true capability.
