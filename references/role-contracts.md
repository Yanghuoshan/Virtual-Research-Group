# Task Assignments and Execution Receipts

[The core contract](../SKILL.md) defines the lifecycle. There is no role manager, phase-specific executor registry or session scheduler between the core and a skill.

## Separate Identities

| Identity | Meaning | Lifetime |
|---|---|---|
| `phase` | Current project-level research goal | Until the core separately decides a transition |
| `task_id` | Stable objective, activity, skill, role and acceptance contract | Across attempts and sessions, until completed/cancelled |
| `packet_id` | One assignment of a task | One request and its matching acceptance receipt |
| `actual_session_id` | Opaque host execution session | May span compatible tasks or be replaced within a task |

`created_phase` is task provenance. `project_phase` in a packet is a snapshot, not a target phase. Neither chooses a skill. `active_task` references the sole running task ID; planned, blocked or submitted tasks are not active executors.

## Assignment Contract

A packet binds the stored task contract, current evidence paths/hashes, new output scopes, requested model/session, core/state/skill fingerprints, authorization and budget. Its summary specifies this attempt's work, including relevant checkpoint facts, without changing the task objective. Different objectives or acceptance standards need new tasks.

The session field requests `fresh`, `reuse` or `current`. Its status is only `requested`. Context is the bounded information loaded into a session, not a separate identity. The task-level independence requirement constrains every assignment, including retries.

## Acceptance Protocol

1. The core selects a planned task and generates/saves a packet without changing state.
2. The host creates or resumes the requested session and selects the actual model. The recipient reads a minimal task brief and selected skill, verifies inputs and returns a receipt before executing task work. If the host cannot support this handshake, report the limitation; do not retroactively claim a receipt prevented already executed work.
3. The receipt matches `task_id`, `packet_id`, state revision and **full packet digest**. Compute `packet_sha256` as SHA-256 of UTF-8 `json.dumps(packet, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False)`. Any packet edit requires a new receipt, including changed outputs, evidence or attempt instructions.
4. The core verifies actual model/role/session, host isolation and receipt origin. A fresh receipt must assert verified isolated history and not reuse a recorded session ID. A reuse receipt must match the requested ID and the latest accepted assignment for that session, ordered by global acceptance revision rather than task order. The helper rejects inconsistent assertions; it cannot authenticate the executor or inspect host memory.
5. The core invokes `accept` to record the packet/receipt, mark the task running and update `active_task`. **Phase is unchanged.** Task work then begins.
6. After executor termination and job reconciliation, the core records a submission or blocker. It independently accepts the task output, requests rework, or cancels. A session finishing is not scientific acceptance, and a task completing is not a phase transition.

No two tasks run concurrently. An idle compatible session may be reused for a related task; same-session history must still be appropriate to its new objective. A required independent review must not reuse the author's session. Model `current` is an alias, not proof of the same actual model.

## Evidence and Limits

Experiment tasks require authorization, research mode, actual evaluation fields and the frozen protocol in every phase. Conclusions tasks require current verified evidence. Analysis tasks cannot quietly run experiments or present unsupported conclusions. Split mixed work; labels alone are not a sandbox.

The core inspects actual content and complete dependencies. Hashes cannot establish scientific truth, detect omitted sources, or prove a receipt's origin. Freeze the framework during an assignment or record a bundle revision: only the selected entry and core contract are fingerprinted, not every reference file.

State history contains explicit lifecycle events; the core maintains scientific interpretation in the narrative log and accepted findings. Review and permission facts are not reset on session replacement. No command installs tools, changes host settings or dispatches model calls.
