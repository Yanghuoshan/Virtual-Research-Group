# Research Log

## Current Brief

<!-- brief:start -->

- **Updated:** (local time, ISO 8601, written when the core last made a decision)
- **Status:** active or stopped
- **Phase:** current research phase
- **Active task:** task id, one-line objective, selected skill, role; or none
- **Open blockers:** each open blocker in one line; or none
- **Last decision:** what the core decided and why, in its own words
- **Next:** what the core believes should happen next, and what it is waiting for

<!-- brief:end -->

The brief above is rewritten by the core model at every core decision (task registration, handoff, accept, task-status, phase, gate commands, blockers, project-status). It is the core's own narrative of where the project stands, not script output; the authoritative record remains `research-state.json`. A stale or inconsistent brief is itself a defect: the watchdog checks brief-state consistency, and a human reading only this block should know where the agent is, why, and how to intervene.

## Decision Narrative

Append only. Correct earlier conclusions by adding a correction that references the previous record; do not erase failures.

The state history records explicit lifecycle events automatically. This narrative log is maintained by the core for scientific reasoning; it is not the task queue or a session registry.

| Time | Project phase | Task ID | Packet ID | Host session ID | Role / actual model | State revision | Decision / rationale | Evidence |
|---|---|---|---|---|---|---|---|---|
| 2026-01-01T10:00Z | scope | t1 | 3f2a... | host:session-17 | strategist / provider/model-a | 4 | Accepted scope analysis; two assumptions need literature support | literature/scope-notes-v1.md |

Column guidance:

- **Time:** when the core made the decision, not when work started.
- **Project phase / State revision:** match `research-state.json` at the moment of the decision; together with `history` they answer "where did the agent stop".
- **Task ID / Packet ID / Host session ID:** the three identities of one attempt; a task may span several packets and sessions.
- **Role / actual model:** the role id whose standpoint prompt was injected, and the model that actually executed.
- **Decision / rationale:** the scientific judgment in one or two sentences; the raw event lives in state history.
- **Evidence:** the artifacts the decision relied on, as project-relative paths.
