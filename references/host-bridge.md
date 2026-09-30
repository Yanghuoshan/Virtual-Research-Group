# Host Bridge: Executing Packets and Watching the Loop

The framework's helpers record decisions; they do not dispatch work. This document defines how a host agent (CodeBuddy's subagent/task facility is the reference implementation; any host with isolated sessions works) bridges that gap while keeping every state change an explicit core decision, every step readable by a human, and every point intervenable.

Nothing here overrides the [core contract](../SKILL.md) or the [operations manual](operations.md). Where the bridge conflicts with them, the core contract wins and the bridge is wrong.

## A. The Execution Loop

One iteration per assignment attempt:

```text
core decision          host facility                    back to core
--------------         ----------------------------     --------------------
1. handoff packet  --> 2. host selects session  --> 3. accept receipt
   saved under          verifies packet + creates       (validates digest;
   handoffs/, brief     receipt before tool calls        task becomes running)
   updated              4. execute approved work; write task-local artifacts
                        5. reconcile host jobs; submit to core
```

1. **Issue.** The core runs `handoff`, saves the printed packet under `handoffs/` at a new path, and rewrites the current brief in `research-log.md`. No host interaction yet.
2. **Prepare.** The host selects the requested `fresh`, `reuse` or `current` session and checks the packet with only its selected skill, evidence hashes, contract and output boundaries. A fork inheriting the core's full conversation is not fresh isolation. Fill `templates/handoff-receipt.json` from observed session and model facts before any external call.
3. **Accept.** The core validates the receipt and invokes `accept`, moving the task to `running`. If acceptance fails, do not run external tools; reconcile any accidentally started executor first. The helper tolerates already existing scoped outputs for compatibility, but that is not permission to bypass the pre-call gate.
4. **Execute.** Before each external call the host runs `check-tool` with the active task ID and packet ID, approved server, operation and exact scope; refuse a mismatch. An `unknown` classification returns `needs_confirmation`: the agent asks the user once and records the answer with `tools --confirm`, which is cached until the catalog changes. Catalog declarations are hints, not proofs: the host must still inspect parameters and prohibit writes in planning/analysis. Keep call provenance; record job IDs with `host-event`. The helper cannot intercept an uncooperative host.
5. **Submit.** Reconcile job status and executor termination before `task-status submitted` or `blocked`, then let the core accept or replan the work.

The loop then continues with `task-status` (submitted after the executor stops, completed after core acceptance), each step rewriting the brief. Record any external job ID and actual running/terminal state with `host-event` after acceptance; a recorded running job blocks submission even when the executor claims to have stopped. `watch` reports silent active tasks and recorded jobs but does not implement the host-level watchdog's receipt-stall, blocker-age, brief-drift or project-silence checks, nor dispatch, stop or query real jobs. The host must reconcile external status before terminal events. The core then considers a fresh bounded task, a justified phase decision or stopping; neither the helper nor a watchdog chooses the next scientific action. Every arrow is a human intervention point.

## Receipt auto-generation rules

The executing subagent fills the receipt template from observed facts, never from the request:

| Field | Rule |
|---|---|
| `accepted_at` | Actual wall-clock time the executor accepted the assignment |
| `actual_model` | The model actually running, as the host reports it; `current` is an alias, not a proof |
| `actual_session_id` | The host-provided session ID; `null` with an explanation if the host provides none |
| four `*_checked` flags | True only for checks actually performed; isolation verified only for genuinely fresh sessions |

The helper's digest and consistency rules (including `packet_sha256` and reuse ordering) are unchanged and are documented in [operations](operations.md). The bridge fills the receipt faster than a human would; it does not weaken what the receipt asserts. A host that cannot verify isolation must say so - a false `session_isolation_verified` is the single worst lie this protocol can record.

## Human intervention points

Automation is the default for mechanics; judgment points stay with the core, and each can be escalated to require explicit human confirmation:

| Point | Default | Escalation |
|---|---|---|
| Packet issuance (before `handoff`) | Core decides | Human reviews objective, skill, channel permissions |
| Receipt acceptance (before `accept`) | Core verifies | Human inspects packet + receipt digest match |
| Completion (before `task-status completed`) | Core inspects artifacts | Human spot-checks acceptance criteria |
| Any time | - | `blockers` pauses task creation/assignment/completion/phase (a task created with `--resolves` may still work on its blocker); `project-status --to stopped` halts everything (terminal until reactivated); rejected submissions return `submitted → planned` |

The current brief in `research-log.md` is the primary human window: it states where the project is, what was just decided and why, and what the core intends next. A human who reads only the brief and the open blockers list always knows enough to choose an intervention.

## B. The Watchdog

The loop can stall silently: a running task with no submission, a packet issued but never accepted, a blocker no one resolves. A host-level scheduled task - the watchdog - monitors for exactly these failures. CodeBuddy automations (recurring) are the reference implementation; a cron-driven agent session works identically.

### Contract

- **Read-only.** The watchdog reads `research-state.json`, `research-log.md`, and `handoffs/` filenames. It never runs a state-changing command, never dispatches subagents, and never edits any file. If it could change something, it would be a second core, which the architecture forbids.
- **Reports to a human, not to the loop.** Output goes to the notification channel the host provides. Normal runs produce a one-line heartbeat; anomalies produce a report.
- **Owned by the user.** The user starts, stops, and re-tunes the watchdog. It is host configuration, not project state.

### Checks and default thresholds

| Check | Default threshold | Report |
|---|---|---|
| Running task silent | No history event for each task in `active_tasks` while `running` for 2 hours | Task id, last event, last brief update, suggested action: inspect executor or move to blocked |
| Receipt stall | Packet file under `handoffs/` with no matching acceptance for 6 hours | Packet path, task id, whether an executor was ever accepted |
| Blocker age | Any open blocker older than 24 hours | Blocker ID and text, age from `opened_at` (preserved across edits), tasks waiting on it |
| Brief drift | Brief missing, older than the newest history event, or contradicting `research-state.json` (phase, active task, blockers) | Both readings side by side; the core skipped its brief duty |
| Project silence | Active project with no decision recorded for 48 hours | Phase, last decision, whether this is expected dormancy or a dead loop |

Thresholds are defaults for the user to tune per project; the watchdog never invents stricter ones at runtime.

### Report format

```text
[watchdog 2026-09-30T14:05+08:00] project ./projects/graph-study
ANOMALY running-task-silent: t17 running, no event since 2026-09-30T09:40Z (4h25m)
  last brief: "Waiting on sandbox run for h1 run-b"
  suggested: inspect the executor session, or record blocked via task-status
```

A heartbeat, when nothing is wrong:

```text
[watchdog 2026-09-30T14:05+08:00] project ./projects/graph-study OK
  phase=execute active_tasks=t17 blockers=0 last_decision=assignment-accepted brief_age=12m
```

### What the watchdog is not

It is not an evaluator: it cannot judge whether the core's decisions are scientifically sound, only whether the loop is mechanically alive and self-consistent. It is not a recovery mechanism: after it reports, the human or the core chooses the intervention. And it is not required for small projects - a human reading the brief after each decision performs the same supervision synchronously.
