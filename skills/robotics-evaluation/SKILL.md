---
name: robotics-evaluation
description: Use when supplied control or embodied-policy rollouts need success, safety-constraint, and reproducibility analysis.
---

# Rollout and Control Evaluation

Analyze a fixed control-policy evaluation protocol and its recorded rollouts. This is not a robot controller or a training scheduler.

## Inputs

Environment and simulator versions, task/initial-state distribution, action and observation definitions, episode logs, termination flags, rewards and success criteria, policy identifiers, resource budgets, and assigned outputs.

## Method

1. Separate environment termination from time-limit truncation; check return computation and bootstrapping conventions. State whether an incomplete episode counts as failure, censoring, or exclusion.
2. Verify reset procedures, initial conditions, seeds, action rates, observation delays, normalization and policy stochasticity, using the [rollout protocol](references/rollout-protocol.md). Distinguish training seeds from evaluation episodes.
3. Report success rate and its sampling uncertainty alongside return, constraint violations, time to completion, and control effort where relevant, per [safety and metrics](references/safety-and-metrics.md). High return is not proof of safe operation.
4. Compare baselines under matched interaction budgets, sensors, actuation and initial-state distributions. Identify privileged simulator information absent in deployment.
5. Group results by task and environment conditions. Retain failed trajectories and denominator counts; repeated resets are not independent training runs.
6. Separate simulation evidence from real-device evidence and record any gap in dynamics, latency, contact or sensing. Never claim physical validation from simulated success.

## Outputs

A rollout audit, per-condition summary, failure taxonomy, and reproducibility checklist. Compute metrics only from the provided logs and approved local tools.

## Checks

Success definitions are fixed before comparison. Timeouts are visible. Constraints are measured, not inferred from reward. A real-device conclusion requires actual authorized device evidence.

Example: a policy that maximizes reward by exhausting the episode horizon may fail the declared completion criterion despite a high average return.

## Local References

- [Rollout protocol and reproducibility](references/rollout-protocol.md)
- [Safety metrics and failure taxonomy](references/safety-and-metrics.md)

These define procedures for this skill only. They do not authorize actuating hardware or starting simulations.

## Boundary

Return to the core with results or missing logs. Do not dispatch other skills or agents, select policies or models, actuate hardware, start simulations, schedule training, alter global state, or advance phases. Device execution requires a separate core-controlled assignment and authorization.
