# Offline Core Operations

Python 3.10+ and standard library only. Run from `research-framework/`. The [core contract](../SKILL.md) is authoritative. These commands implement explicit core decisions; specialists must not invoke state-changing operations.

## Commands and Side Effects

| Command | Purpose | Changes project state? |
|---|---|---|
| `validate`, `skills` | Check the bundle or discover direct and extension skills | No |
| `status` | Print a read-only progress board | No |
| `init` | Create four planning documents in a new directory | Creates a project; never overwrites |
| `migrate` | Explicitly upgrade an idle planning schema-5, schema-6 or schema-7 project to schema 8 | Yes, not phase |
| `set-goal` | Select a versioned goal dossier under `hypotheses/` or `reports/` | Yes, not phase |
| `authorize` | Set research mode and/or a scoped access grant | Yes, not phase |
| `check-tool` | Read-only host preflight that returns the preflight token the call must carry | No |
| `tools` | Ingest a host-exported tool catalog, confirm an ambiguous operation, or view the registry | Writes `tools/<server>.json`, records decisions |
| `tool-call` | Record one external call, or a burst of identical calls with `--count`, against its preflight token | Yes, not phase |
| `host-event` | Record the observed status of an external job for a running task | Yes, not phase |
| `watch` | Read-only report of silent active tasks and recorded outstanding jobs | No |
| `reflect`, `review-reflection` | Record raw-evidence-backed reflection and follow-up check | Yes, not phase |
| `set-evaluation` | Record the four evaluation fields | Yes, not phase |
| `set-protocol` | Freeze a nonempty protocol under `experiments/` | Yes, not phase |
| `set-audit` | Record an evidence or final review audit from `reviews/` | Yes, not phase |
| `blockers` | Add, resolve, edit or list project blockers (`--list` is read-only) | Yes for add/resolve/edit, not phase |
| `project-status` | Activate or stop the project | Yes, only this changes project status |
| `task` | Register a stable task contract, optionally with `--resolves` | Yes, not phase |
| `handoff` | Print an assignment for a registered task | No |
| `assign` | Composite: save the handoff packet under `handoffs/`; a current-session assignment also computes and records its receipt | Yes for current-session acceptance, not phase |
| `submit` | Composite: record submission and completion in one command | Yes, not phase |
| `brief` | Mechanically rewrite the current brief block in `research-log.md` | Writes the log brief block only, never state |
| `accept` | Validate and record an actual host receipt | Yes, starts the task; not phase |
| `task-status` | Record submission, blocking, rework, completion or cancellation | Yes, not phase |
| `phase` | Record a separate core phase decision | Yes, only this changes phase |

Every command marked "Yes" in the table above atomically replaces `research-state.json`, increments revision and appends decision history. `init` is the exception: it creates the project and leaves `revision` at 0 with an empty `history`, because there is no decision to record yet. They require one core writer; revision checks are not distributed locking. No command spawns a model, resumes a host session or starts an experiment. `research-log.md` remains the core's human-readable scientific narrative.

History events use one uniform shape: `action`, `reason` and `revision` with a timestamp on every event, `task_id` on task-level events, and evidence path/hash pairs on events that cite material. Reading `history` newest-last shows where the project stands: `task-created` commissions work, `assignment-accepted` records an executor starting, `task-submitted` records work returned, `task-completed` records core acceptance.

## Planning Goal and Research Feedback

In planning mode, compare candidate questions, evidence gaps, falsifiers and feasibility without treating hypotheses as verified results. Write a versioned dossier under `hypotheses/` or `reports/` containing populated `Question:`, `Value:`, `Boundary:`, `Alternatives:`, `Evidence:`, `Falsifier:`, `Success:`, `Feasibility:`, `Resources:`, `Stop:` and `Unknown:` lines; select it with `set-goal --project ... --path hypotheses/goal-v1.md --reason ...`. A selected goal must remain hash-valid; `scope → ideation` requires its `Unknown:` line to be `none` or `resolved` after the core has actually resolved/bounded material uncertainties. Legacy projects without a selected goal remain usable but do not satisfy this stronger gate.

For an accepted experimental assignment, keep the snapshot of protocol, evaluation, grant and goal in its packet. Grant expiry forbids *new* work or tool calls; it does not retroactively prevent acceptance of results already submitted under the same unchanged contract. Never change a protocol to relabel an earlier run; use new versioned paths and a new task if its contract changed. After a completed or blocked task of any activity, prepare a JSON report under `reports/` with nonempty `observation`, `protocol_check`, `counterevidence`, `alternatives`, `next_options`, `prediction`, `decision` and `evidence` (an array of project-relative `path`/`sha256` pairs including an original run output or returned artifact). `reflect --project ... --task ... --path reports/...json --reason ...` records its prediction without starting another run. When a different task completes *later*, `review-reflection --project ... --path reports/...json --task ... --assessment supported|contradicted|inconclusive --reason ...` links the new evidence and the core's prediction assessment. Rejected hypotheses, null results and incomplete replication remain in the record.

## Keep the Current Brief Current

Every state-changing command is preceded or immediately followed by the core rewriting the brief block at the top of `research-log.md`, in the core's own words. The block lives between `<!-- brief:start -->` and `<!-- brief:end -->`; nothing outside the block is rewritten. A compliant brief states, at minimum: the local-time ISO 8601 moment it was written, project status, phase, goal dossier and unknowns, approved access/scope/expiry, each active task (id, one-line objective, skill, role) or none, each open blocker, most recent reflection when applicable, the decision just made and why, and what the core believes should happen next. The `brief` command writes the mechanical lines of this block from `research-state.json` in one step; the core supplies the narrative through `--note` (the `Next:` line) and keeps the deeper reasoning in the narrative log below the block. `research-state.json` remains the authoritative record, and the brief is the core's human-readable narrative of it. A brief that contradicts the state file is a defect in itself - the `watch` command checks brief-state consistency, and a human reading only the brief must be able to tell where the agent is, why, and how to intervene. If the log file is missing the markers (for example a pre-brief project), the brief command adds the block on top rather than editing history.

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

A task created with `--resolves b3` declares that it exists to fix that open blocker, referenced by its stable ID. While blockers are open, only tasks resolving one of them may be created, assigned or run; unrelated tasks and phase changes stay blocked. Completing such a task closes the open blockers it declared; blockers it declared that were already closed elsewhere are recorded in the decision history, never silently dropped. Foreign open blockers never freeze the completion of finished work; only an explicit `--freeze-all` blocker halts everything, including completion, until resolved. `--resolve` and `--edit` take the blocker ID printed by `--add`; `--edit` rewords the text while keeping the ID and its age, and `--list` prints open and resolved blockers read-only.

Activity is mandatory: `analysis` permits bounded preparatory/exploratory work, not new experiments or verified-result claims; `experiment` requires research mode, all four evaluation fields and the matching frozen protocol; `conclusions` requires a verified evidence audit (`evidence_review.status == verified`) binding findings, the current protocol when one is frozen, and primary artifacts under `experiments/`, `data/`, `literature/` or `reports/`. These gates apply in every project phase, are opened by the gate commands below, and the core is responsible for honest classification and all additional tool/service permissions.

External channels such as MCP servers are assigned per task. Name the permitted server and tool in the objective and record a separate scoped grant from actual user approval. For planning retrieval, `authorize --mode planning` may include a grant without enabling experiments; `authorize --mode planning` without grant options revokes it. After `accept`, the host must call `check-tool --project ... --task ... --packet ... --server ... --operation ... --scope ...` before every external operation and enforce refusal on mismatch. Each check returns a `preflight_token` binding the checked facts; after the call, record it with `tool-call --project ... --task ... --packet ... --server ... --operation ... --scope ... --token ...`, which re-validates the request and appends the call to the decision history so the audit trail can be reconciled later. A burst of identical requests (same task, packet, server, operation and scope) shares one preflight token; record it once with `--count N` instead of N separate calls. Each permitted channel is assigned with `--tool server:operation` at task creation and verified exactly at call time; prose objectives never authorize channels. Operation semantics come from the server's own catalog, never from the operation name alone at call time: the host exports the tool list and `tools --project ... --server ... --catalog <file>` classifies each operation as `read`, `write` or `unknown` from its annotations, description and argument names. Planning grants may only name `read`-classified operations; `write` and `unknown` require research mode and an experiment task. An `unknown` result carries `needs_confirmation`: the agent asks the user once and records the answer with `tools --confirm --server ... --operation ... --semantics read|write --reason ...`; the answer is cached against the tool signature, and a changed catalog resets it. Catalog declarations are hints, so the host still inspects parameters to rule out writes. This check cannot intercept an uncooperative host or establish the authenticity of a cited approval artifact. Preserve raw responses with source URI and retrieval date.

## Set Gates Before Gated Work

Gates are core decisions, not specialist actions. Each command below requires `--reason`, appends one decision to `history`, and changes no phase:

```bash
python3 scripts/research.py authorize --project ./projects/study --mode research \
  --reason "User authorized the bounded protocol" --evidence reports/user-approval-v1.md \
  --services sandbox-server --operations run --scope "graph-study" --max-runs 3 --expires-at 2099-01-01T00:00:00Z
python3 scripts/research.py set-evaluation --project ./projects/study --primary-measure "mean accuracy" \
  --baseline "published baseline" --validation-plan "held-out split" --uncertainty-plan "bootstrap interval" \
  --reason "Core accepted the protocol's estimand and checks"
python3 scripts/research.py set-protocol --project ./projects/study --path experiments/h1/protocol.md \
  --reason "Core froze the accepted protocol"
python3 scripts/research.py blockers --project ./projects/study --resolve b1 --reason "Baseline reproduced"
python3 scripts/research.py project-status --project ./projects/study --to stopped --reason "Planning-only work stops here"
```

Granting research mode requires one cited user approval artifact, named services/operations, exact scope, a positive maximum number of experimental attempts across the project and a future ISO expiry. The helper checks the evidence file and fields, not the authenticity of user consent. Returning to planning mode without new grant arguments revokes access. `migrate --project ...` only accepts schema-5, schema-6 or schema-7 projects with no active tasks and planning mode; first back up and reconcile every host job, then issue new schema-8 packets and receipts. `set-protocol` accepts only a nonempty, nonsymlinked file under `experiments/`.

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

How a cooperating host prepares the requested fresh/reused/current session, records a receipt before external calls, and how an optional host-level read-only watchdog could supervise the loop, is defined in the [host bridge](host-bridge.md); the [framework diagrams](architecture-diagrams.md) map the layers and flows.

`assign` composes the same mechanics for small work: it runs `handoff`, saves the packet under `handoffs/{task}-request-{tag}.json`, and prints it. With `--session current` it also computes the four receipt checks from the files on disk, saves the receipt and records acceptance in one command, so a small bounded analysis no longer needs a hand-packed packet and receipt. The composite receipt records `session_isolation_verified: false` and the model as requested; fresh and reuse sessions still require a host-filled receipt, because isolation and resumed-session identity are host facts the helper cannot assert.

`--task` selects a stable task, not a phase. The packet includes a new `packet_id`, current `project_phase`, task contract and evidence fingerprints. `handoff` no longer accepts `--to`, skill, role or acceptance overrides. Save the printed packet at a new path under `handoffs/` if it is to be accepted. Avoid overwriting earlier attempts.

All output targets must be new artifacts below `literature/`, `hypotheses/`, `experiments/`, `src/`, `data/`, `paper/`, `reports/`, `reviews/` or `scratch/`. `scratch/` is the free exploration channel: its artifacts may inform later tasks as evidence but are rejected as audit subjects, so they can never support verified claims. Whole roots, existing targets (including empty directories), input overlap, global records and `handoffs/` are forbidden. Use trailing `/` for a directory scope; submitted files must be within an assigned scope. Rework uses new output paths and may read previous outputs as evidence.

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

This requires real receipt values; a copied blank template fails. Acceptance validates the receipt against the current state and the live task contract directly. Record acceptance before any external call; the helper tolerates scoped outputs already written before acceptance for compatibility, not as permission to bypass `check-tool`. Output freshness is enforced at `handoff` time, while artifact inspection happens at submission. The task becomes running and joins `active_tasks`; phase stays `scope`. A compact record of the attempt (packet id and digest, skill, role, model, session, output scopes, evidence hashes) is kept inside that task's assignment history; the full packet and receipt JSON stay saved under `handoffs/`. Changed state, input evidence or a drifted contract invalidates acceptance. Host IDs are not invented; absent IDs require an explicit limitation and cannot be resumed. No helper can prove host isolation or the truth of a receipt.

## Submit, Accept, or Continue the Same Task

After actual work and executor termination, record submission and then a separate core acceptance:

```bash
python3 scripts/research.py task-status --project ./projects/study --task scope-1 --status submitted --executor-stopped --reason "Executor returned the assumption analysis" --evidence hypotheses/scope-1-v1.md
python3 scripts/research.py task-status --project ./projects/study --task scope-1 --status completed --reason "Core verified the acceptance criteria and evidence limits"
```

Submission is not completion. The core must inspect the actual artifact, not merely rely on file existence. Completion rechecks submitted artifact hashes and task inputs; for experiments it compares the original execution contract to the current protocol, plan and grant without requiring an already-used grant to remain unexpired. An unrelated open blocker still prevents completion; the explicitly resolving task may complete and remove its blocker. `--executor-stopped` is a core assertion after checking host/job status, not a command that kills processes.

`submit` composes the two steps for ordinary acceptance: it records `submitted` with `--executor-stopped` semantics and then `completed`, running every check of both commands unchanged. If the completion step is refused, the task remains `submitted`, exactly like the manual flow; inspect the error, fix the cause and re-run `task-status --status completed` or replan.

For overload or missing prerequisites: move `running → blocked` with `--executor-stopped`, preserving diagnostics as evidence. After resolving the blocker, move `blocked → planned`, then issue a new packet under the same task ID with new outputs and a fresh or compatible reused session. Rejected submissions can move `submitted → planned`. Neither requires falsely completing the task. Other tasks may work on prerequisites while one is blocked, but only tasks explicitly declaring the matching open blocker under `--resolves` may bypass it. Unrelated work stays blocked.

Allowed states: `planned → running` only through `accept`; `running → submitted/blocked/cancelled` only after executor termination; `submitted → completed/planned/cancelled`; `blocked → planned/cancelled`; `planned → cancelled`. Completed/cancelled tasks are terminal and remain in history.

## Decide Phase Separately

```bash
python3 scripts/research.py phase --project ./projects/study --to ideation --reason "Core checked scope exit criteria; remaining reference checks can continue as tasks" --evidence research-brief.md
```

Run this only when the cited evidence actually warrants the decision, not automatically after one task finishes. It requires an active project status, no running executor, no global blockers, a legal core-table transition, rationale and nonempty evidence. Planned/blocked tasks may carry over; their creation phase does not bind execution. Exit criteria are scientific judgments the core must check, not machine-inferred truth.

`review → complete` additionally requires all tasks completed/cancelled and valid evidence and final-review audits. A protocol cannot substitute for raw evidence. Planning-only work may instead be stopped by the core without claiming verified research completion.

## Compatibility

State, packet and receipt schema are now 8. Older schemas are rejected; idle planning schema-5, schema-6 and schema-7 projects have an explicit `migrate` path. Schema 7 gave blockers stable IDs, a resolution history, identity-preserving `--edit`, an explicit `--freeze-all` emergency stop, and completion of finished work that no longer freezes on foreign blockers; schema 8 makes per-task tool channels structured `--tool` assignments checked exactly, replacing objective substring matching. Do not just change the version number. Schema 4 dropped the authorization flags (research mode is the single experiment gate), the `paused` status and the unused `project_id`, `allowed_tools`, `budget` and `next_action` fields; see [migration](architecture.md). Schema 5 introduces parallel tasks with mutually exclusive output scopes (`active_tasks` replaces `active_task`), task-level `resolves` declarations, acceptance that tolerates artifacts written during execution, compact assignment records, and audit schema 2 (reviewer, reviewed_at, verified claims). No original library, external project, host configuration, schedule or experiment is modified by the framework refactor.
