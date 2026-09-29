# Identity and Packet Quick Reference

[The core contract](../SKILL.md) defines the lifecycle. There is no role manager, phase-specific executor registry or session scheduler between the core and a skill. Command usage and the step-by-step acceptance protocol are in [operations](operations.md); role selection is in [role guidance](role-guidance.md).

## Separate Identities

| Identity | Meaning | Lifetime |
|---|---|---|
| `phase` | Current project-level research goal | Until the core separately decides a transition |
| `task_id` | Stable objective, activity, skill, role and acceptance contract | Across attempts and sessions, until completed/cancelled |
| `packet_id` | One assignment of a task | One request and its matching acceptance receipt |
| `actual_session_id` | Opaque host execution session | May span compatible tasks or be replaced within a task |

`created_phase` is task provenance. `project_phase` in a packet is a snapshot, not a target phase. Neither chooses a skill. `active_task` references the sole running task ID; planned, blocked or submitted tasks are not active executors.

## What a Packet Binds

The stored task contract, current evidence paths/hashes, new output scopes, requested model/session, core/state/skill fingerprints, authorization and budget. Its `summary` scopes this attempt only and never rewrites the task objective. The session field is only `requested`; context is bounded information in a session, not an identity. Different objectives or acceptance standards require a new task, not an edited packet.
