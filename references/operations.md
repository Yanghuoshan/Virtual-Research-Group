# Offline Core Operations

Python 3.10+ and standard library only. Run from `research-framework/`. The [core contract](../SKILL.md) is authoritative. These commands implement explicit core decisions; specialists must not invoke state-changing operations.

## Commands and Side Effects

| Command | Purpose | Changes project state? |
|---|---|---|
| `validate`, `skills` | Check the bundle or discover direct and extension skills | No |
| `status` | Print a read-only progress board | No |
| `init` | Create four planning documents in a new directory | Creates a project; never overwrites |
| `authorize` | Set research mode, the single experiment gate | Yes, not phase |
| `set-evaluation` | Record the four evaluation fields | Yes, not phase |
| `set-protocol` | Freeze a nonempty protocol under `experiments/` | Yes, not phase |
| `set-audit` | Record an evidence or final review audit from `reviews/` | Yes, not phase |
| `blockers` | Add or resolve a project blocker | Yes, not phase |
| `project-status` | Activate or stop the project | Yes, only this changes project status |
| `task` | Register a stable task contract, optionally with `--resolves` | Yes, not phase |
| `handoff` | Print an assignment for a registered task | No |
| `accept` | Validate and record an actual host receipt | Yes, starts the task; not phase |
| `task-status` | Record submission, blocking, rework, completion or cancellation | Yes, not phase |
| `phase` | Record a separate core phase decision | Yes, only this changes phase |

Every command marked "Yes" in the table above atomically replaces `research-state.json`, increments revision and appends decision history. `init` is the exception: it creates the project and leaves `revision` at 0 with an empty `history`, because there is no decision to record yet. They require one core writer; revision checks are not distributed locking. No command spawns a model, resumes a host session or starts an experiment. `research-log.md` remains the core's human-readable scientific narrative.

History events use one uniform shape: `action`, `reason` and `revision` with a timestamp on every event, `task_id` on task-level events, and evidence path/hash pairs on events that cite material. Reading `history` newest-last shows where the project stands: `task-created` commissions work, `assignment-accepted` records an executor starting, `task-submitted` records work returned, `task-completed` records core acceptance.

## Keep the Current Brief Current

Every state-changing command is preceded or immediately followed by the core rewriting the brief block at the top of `research-log.md`, in the core's own words. The block lives between `<!-- brief:start -->` and `<!-- brief:end -->`; nothing outside the block is rewritten. A compliant brief states, at minimum: the local-time ISO 8601 moment it was written, project status, phase, the active task (id, one-line objective, skill, role) or none, each open blocker, the decision just made and why, and what the core believes should happen next. The scripts never write this block: `research-state.json` remains the authoritative record, and the brief is the core's human-readable narrative of it. A brief that contradicts the state file is a defect in itself - the host watchdog checks brief-state consistency, and a human reading only the brief must be able to tell where the agent is, why, and how to intervene. If the log file is missing the markers (for example a pre-brief project), the core adds the block on its next decision rather than editing history.

## Initialize and Register Multiple Tasks

```bash
python3 scripts/research.py validate
python3 -m unittest discover -s tests -v
python3 scripts/research.py init --project ./projects/study --question "What explains graph sensitivity?"
python3 scripts/research.py task --project ./projects/study --task scope-1 --objective "Identify assumptions in the question" --activity analysis --skill creative-thinking-for-research --role strategist --acceptance "List assumptions, alternatives and scope limits"
python3 scripts/research.py task --project ./projects/study --task scope-2 --objective "Verify the supplied foundational references" --activity analysis --skill citation-verification --role analyst --acceptance "Resolve source identities and mark unsupported claims"
```

Both tasks are planned in `scope`; no phase change occurs. Likewise create as many ideation tasks as needed after a separate phase decision. A task's objective, activity, skill, role and acceptance criteria are its fixed contract. New objectives require new IDs; local rework keeps the existing ID.

Several tasks may run at the same time; a new assignment is refused only while another running task holds an overlapping output scope. One task still has at most one executor at a time.

A task created with `--resolves "Missing baseline"` declares that it exists to fix that blocker. Such a task may be created, assigned and completed while the blocker is open, so a missing prerequisite no longer freezes the whole project; completing the task removes the blocker automatically, and the core can re-add it if the accepted output does not actually fix it.

Activity is mandatory: `analysis` permits bounded preparatory/exploratory work, not new experiments or verified-result claims; `experiment` requires research mode, all four evaluation fields and the matching frozen protocol; `conclusions` requires a verified evidence audit (`evidence_review.status == verified`) binding findings, the current protocol when one is frozen, and primary artifacts under `experiments/`, `data/`, `literature/` or `reports/`. These gates apply in every project phase, are opened by the gate commands below, and the core is responsible for honest classification and all additional tool/service permissions.

External channels such as MCP servers are assigned per task. Name the permitted server and tool in the objective, for example "use the literature search server, `search` and `fetch` only". Leaving the project network or using paid access requires explicit user approval, recorded as the evidence cited when research mode is set and named in the task objective; the helper does not enforce it. Preserve raw responses with source URI and retrieval date rather than only a summary.

## Set Gates Before Gated Work

Gates are core decisions, not specialist actions. Each command below requires `--reason`, appends one decision to `history`, and changes no phase:

```bash
python3 scripts/research.py authorize --project ./projects/study --mode research \
  --reason "User authorized the bounded protocol" --evidence research-brief.md
python3 scripts/research.py set-evaluation --project ./projects/study --primary-measure "mean accuracy" \
  --baseline "published baseline" --validation-plan "held-out split" --uncertainty-plan "bootstrap interval" \
  --reason "Core accepted the protocol's estimand and checks"
python3 scripts/research.py set-protocol --project ./projects/study --path experiments/h1/protocol.md \
  --reason "Core froze the accepted protocol"
python3 scripts/research.py blockers --project ./projects/study --resolve "Missing baseline" --reason "Baseline reproduced"
python3 scripts/research.py project-status --project ./projects/study --to stopped --reason "Planning-only work stops here"
```

Granting research mode requires cited authorization evidence; returning to planning mode does not. `set-protocol` accepts only a nonempty, nonsymlinked file under `experiments/`.

Audits are written under `reviews/` from `templates/evidence-audit.json` and only then recorded, because the helper verifies the file before accepting `verified` or `passed`:

```bash
python3 scripts/research.py set-audit --project ./projects/study --kind evidence --path reviews/evidence-audit.json \
  --status verified --reason "Audit binds findings, protocol and raw evidence"
```

An evidence audit must bind `findings.md`, the frozen protocol when one is frozen, and primary artifacts under `experiments/`, `data/`, `literature/` or `reports/` (survey and report projects may close on `literature/` or `reports/` evidence); a final review must bind `findings.md` and primary artifacts under `paper/` or `reports/`. Audit records use schema 2: a nonempty reviewer, an ISO 8601 `reviewed_at`, and at least one verified claim with its support. Every evidence path cited by a conclusions task or by `phase --to complete` must already appear in the audited subjects, so an unaudited file cannot ride along with a verified claim.

`stopped` closes new tasks, handoffs, acceptance, task-status, phase decisions and gate commands alike; only `project-status --to active` reopens it. It requires the active executor to have stopped first, and setting the status the project already has is refused. While a project stays active, open blockers stop task creation, assignment, completion and phase decisions, so pausing work without closing the project is expressed as blockers rather than as a status value.

## Assign Without Changing Phase

```bash
python3 scripts/research.py handoff --project ./projects/study --task scope-1 --model current --summary "Reformulate the supplied question without running experiments" --evidence research-brief.md --outputs hypotheses/scope-1-v1.md --session fresh
```

How a host agent executes the printed packet in an isolated subagent session, fills the receipt from actual execution facts, and how a scheduled read-only watchdog supervises the loop, is defined in the [host bridge](host-bridge.md); the [framework diagrams](architecture-diagrams.md) map the layers and flows.

`--task` selects a stable task, not a phase. The packet includes a new `packet_id`, current `project_phase`, task contract and evidence fingerprints. `handoff` no longer accepts `--to`, skill, role or acceptance overrides. Save the printed packet at a new path under `handoffs/` if it is to be accepted. Avoid overwriting earlier attempts.

All output targets must be new artifacts below `literature/`, `hypotheses/`, `experiments/`, `src/`, `data/`, `paper/`, `reports/` or `reviews/`. Whole roots, existing targets (including empty directories), input overlap, global records and `handoffs/` are forbidden. Use trailing `/` for a directory scope; submitted files must be within an assigned scope. Rework uses new output paths and may read previous outputs as evidence.

## Select a Session and Accept the Actual Executor

- `--session fresh`: default. Request new isolated working history, not a full-history fork.
- `--session reuse --session-reason "Compatible local continuation" --resume-session "host/session:123"`: request an already recorded idle host session. The helper checks that the resumed host session ID is not held by a running task; the core confirms the previous assignment was submitted, completed or cancelled and that its assumptions still hold. It also checks the latest accepted assignment for that session, matching skill, role id and role prompt digest, and actual model. Related tasks may reuse a session.
- `--session current --session-reason "Small task without an independence requirement"`: explicitly use the current session.

Set `--independent-review` on **task creation** when independent assessment is required. It cannot be removed by retrying in a different session mode. Independent tasks require fresh execution; no silent fallback.

The core invokes the host facility with a minimal brief and one skill. The recipient verifies the task, evidence and requested limits. Complete `templates/handoff-receipt.json` with the actual session/mode/model, matching task/packet IDs, a nonempty `accepted_at`, and all four `*_checked` flags true. The helper rejects a receipt that accepts without an acceptance time, that omits a check flag, or whose actual role, model or session mode diverges from the request. A `fresh` receipt must verify isolation and must not repeat a session ID already recorded under any task; `reuse` and `current` receipts must set `session_isolation_verified` false, and `reuse` must match the requested resume session ID. `packet_sha256` is SHA-256 of the complete packet serialized with Python `json.dumps(packet, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode('utf-8')`; it is not the saved file's whitespace-sensitive hash. Verify the receipt came from the intended executor: this digest binds content, not signer identity. Three contract details the helper relies on: `project_phase` inside a packet is a snapshot of the current phase, never a target phase, so a packet cannot move the project forward; a `reuse` receipt must match the requested session ID and the latest accepted assignment recorded for that session, ordered by global acceptance revision rather than task order; and fingerprints cover the selected skill entry plus the core contract, not every reference file, so freeze the framework during an assignment or record a bundle revision.

After saving both files, the core can record acceptance:

```bash
python3 scripts/research.py accept --project ./projects/study --packet handoffs/scope-1-request.json --receipt handoffs/scope-1-receipt.json
```

This requires real receipt values; a copied blank template fails. Acceptance validates the receipt against the current state and the live task contract directly; the executor may already have written artifacts inside its assigned scope by the time the receipt is recorded, and that is not an error - output freshness is enforced at `handoff` time, artifact inspection happens at submission. The task becomes running and joins `active_tasks`; phase stays `scope`. A compact record of the attempt (packet id and digest, skill, role, model, session, output scopes, evidence hashes) is kept inside that task's assignment history; the full packet and receipt JSON stay saved under `handoffs/`. Changed state, input evidence or a drifted contract invalidates acceptance. Host IDs are not invented; absent IDs require an explicit limitation and cannot be resumed. No helper can prove host isolation or the truth of a receipt.

## Submit, Accept, or Continue the Same Task

After actual work and executor termination, record submission and then a separate core acceptance:

```bash
python3 scripts/research.py task-status --project ./projects/study --task scope-1 --status submitted --executor-stopped --reason "Executor returned the assumption analysis" --evidence hypotheses/scope-1-v1.md
python3 scripts/research.py task-status --project ./projects/study --task scope-1 --status completed --reason "Core verified the acceptance criteria and evidence limits"
```

Submission is not completion. The core must inspect the actual artifact, not merely rely on file existence. Completion rechecks submitted artifact hashes, task inputs and activity gates, and is refused while any project blocker remains open. `--executor-stopped` is a core assertion after checking host/job status, not a command that kills processes.

For overload or missing prerequisites: move `running → blocked` with `--executor-stopped`, preserving diagnostics as evidence. After resolving the blocker, move `blocked → planned`, then issue a new packet under the same task ID with new outputs and a fresh or compatible reused session. Rejected submissions can move `submitted → planned`. Neither requires falsely completing the task. Other tasks may work on prerequisites while one is blocked. Global blockers still prevent execution acceptance.

Allowed states: `planned → running` only through `accept`; `running → submitted/blocked/cancelled` only after executor termination; `submitted → completed/planned/cancelled`; `blocked → planned/cancelled`; `planned → cancelled`. Completed/cancelled tasks are terminal and remain in history.

## Decide Phase Separately

```bash
python3 scripts/research.py phase --project ./projects/study --to ideation --reason "Core checked scope exit criteria; remaining reference checks can continue as tasks" --evidence research-brief.md
```

Run this only when the cited evidence actually warrants the decision, not automatically after one task finishes. It requires an active project status, no running executor, no global blockers, a legal core-table transition, rationale and nonempty evidence. Planned/blocked tasks may carry over; their creation phase does not bind execution. Exit criteria are scientific judgments the core must check, not machine-inferred truth.

`review → complete` additionally requires all tasks completed/cancelled and valid evidence and final-review audits. A protocol cannot substitute for raw evidence. Planning-only work may instead be stopped by the core without claiming verified research completion.

## Compatibility

State, packet and receipt schema are now 5. Schema 4 and older are rejected; do not just change the version number. Schema 4 dropped the authorization flags (research mode is the single experiment gate), the `paused` status and the unused `project_id`, `allowed_tools`, `budget` and `next_action` fields; see [migration](architecture.md). Schema 5 introduces parallel tasks with mutually exclusive output scopes (`active_tasks` replaces `active_task`), task-level `resolves` declarations, acceptance that tolerates artifacts written during execution, compact assignment records, and audit schema 2 (reviewer, reviewed_at, verified claims). No original library, external project, host configuration, schedule or experiment is modified by the framework refactor.
