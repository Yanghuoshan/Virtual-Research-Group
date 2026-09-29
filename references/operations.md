# Offline Core Operations

Python 3.10+ and standard library only. Run from `research-framework/`. The [core contract](../SKILL.md) is authoritative. These commands implement explicit core decisions; specialists must not invoke state-changing operations.

## Commands and Side Effects

| Command | Purpose | Changes project state? |
|---|---|---|
| `validate`, `skills` | Check the bundle or discover direct skills | No |
| `init` | Create four planning documents in a new directory | Creates a project; never overwrites |
| `task` | Register a stable task contract | Yes, not phase |
| `handoff` | Print an assignment for a registered task | No |
| `accept` | Validate and record an actual host receipt | Yes, starts the task; not phase |
| `task-status` | Record submission, blocking, rework, completion or cancellation | Yes, not phase |
| `phase` | Record a separate core phase decision | Yes, only this changes phase |

State-changing commands atomically replace `research-state.json`, increment revision and append decision history. They require one core writer; revision checks are not distributed locking. No command spawns a model, resumes a host session, starts an experiment or enforces resource budgets. `research-log.md` remains the core's human-readable scientific narrative.

## Initialize and Register Multiple Tasks

```bash
python3 scripts/research.py validate
python3 -m unittest discover -s tests -v
python3 scripts/research.py init --project ./projects/study --question "What explains graph sensitivity?"
python3 scripts/research.py task --project ./projects/study --task scope-1 --objective "Identify assumptions in the question" --activity analysis --skill creative-thinking-for-research --role strategist --acceptance "List assumptions, alternatives and scope limits"
python3 scripts/research.py task --project ./projects/study --task scope-2 --objective "Verify the supplied foundational references" --activity analysis --skill citation-verification --role reader --acceptance "Resolve source identities and mark unsupported claims"
```

Both tasks are planned in `scope`; no phase change occurs. Likewise create as many ideation tasks as needed after a separate phase decision. A task's objective, activity, skill, role and acceptance criteria are its fixed contract. New objectives require new IDs; local rework keeps the existing ID.

Activity is mandatory: `analysis` permits bounded preparatory/exploratory work, not new experiments or verified-result claims; `experiment` requires authorization, research mode, evaluation and frozen protocol; `conclusions` requires reviewed evidence. These gates apply in every project phase. The core is responsible for honest classification and all additional tool/service permissions.

External channels such as MCP servers are assigned per task. Name the permitted server and tool in the objective, for example "use the literature search server, `search` and `fetch` only", and record stable project-wide channels in `allowed_tools`. Leaving the project network or using paid access requires `external_services` authorization; the helper does not enforce this flag. Preserve raw responses with source URI and retrieval date rather than only a summary.

## Assign Without Changing Phase

```bash
python3 scripts/research.py handoff --project ./projects/study --task scope-1 --model current --summary "Reformulate the supplied question without running experiments" --evidence research-brief.md --outputs hypotheses/scope-1-v1.md --session fresh
```

`--task` selects a stable task, not a phase. The packet includes a new `packet_id`, current `project_phase`, task contract and evidence fingerprints. `handoff` no longer accepts `--to`, skill, role or acceptance overrides. Save the printed packet at a new path under `handoffs/` if it is to be accepted. Avoid overwriting earlier attempts.

All output targets must be new artifacts below `literature/`, `hypotheses/`, `experiments/`, `src/`, `data/`, `paper/`, `reports/` or `reviews/`. Whole roots, existing targets (including empty directories), input overlap, global records and `handoffs/` are forbidden. Use trailing `/` for a directory scope; submitted files must be within an assigned scope. Rework uses new output paths and may read previous outputs as evidence.

## Select a Session and Accept the Actual Executor

- `--session fresh`: default. Request new isolated working history, not a full-history fork.
- `--session reuse --session-reason "Compatible local continuation" --resume-session "host/session:123"`: request an already recorded idle host session. Core checks its latest accepted assignment, matching skill/role/actual model and valid assumptions. Related tasks may reuse a session.
- `--session current --session-reason "Small task without an independence requirement"`: explicitly use the current session.

Set `--independent-review` on **task creation** when independent assessment is required. It cannot be removed by retrying in a different session mode. Independent tasks require fresh execution; no silent fallback.

The core invokes the host facility with a minimal brief and one skill. The recipient verifies the task, evidence and requested limits. Complete `templates/handoff-receipt.json` with the actual session/mode/model, matching task/packet IDs and checks. `packet_sha256` is SHA-256 of the complete packet serialized with Python `json.dumps(packet, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode('utf-8')`; it is not the saved file's whitespace-sensitive hash. Verify the receipt came from the intended executor: this digest binds content, not signer identity. Three contract details the helper relies on: `project_phase` inside a packet is a snapshot of the current phase, never a target phase, so a packet cannot move the project forward; a `reuse` receipt must match the requested session ID and the latest accepted assignment recorded for that session, ordered by global acceptance revision rather than task order; and fingerprints cover the selected skill entry plus the core contract, not every reference file, so freeze the framework during an assignment or record a bundle revision.

After saving both files, the core can record acceptance:

```bash
python3 scripts/research.py accept --project ./projects/study --packet handoffs/scope-1-request.json --receipt handoffs/scope-1-receipt.json
```

This requires real receipt values; a copied blank template fails. The task becomes running, `active_task` becomes its ID, and phase stays `scope`. The packet/receipt are retained inside that task's assignment history. Changed state, input evidence, contract or packet content invalidates acceptance. Only one task may run at a time. Host IDs are not invented; absent IDs require an explicit limitation and cannot be resumed. No helper can prove host isolation or the truth of a receipt.

## Submit, Accept, or Continue the Same Task

After actual work and executor termination, record submission and then a separate core acceptance:

```bash
python3 scripts/research.py task-status --project ./projects/study --task scope-1 --status submitted --executor-stopped --reason "Executor returned the assumption analysis" --evidence hypotheses/scope-1-v1.md
python3 scripts/research.py task-status --project ./projects/study --task scope-1 --status completed --reason "Core verified the acceptance criteria and evidence limits"
```

Submission is not completion. The core must inspect the actual artifact, not merely rely on file existence. Completion rechecks submitted artifact hashes, task inputs and activity gates. `--executor-stopped` is a core assertion after checking host/job status, not a command that kills processes.

For overload or missing prerequisites: move `running → blocked` with `--executor-stopped`, preserving diagnostics as evidence. After resolving the blocker, move `blocked → planned`, then issue a new packet under the same task ID with new outputs and a fresh or compatible reused session. Rejected submissions can move `submitted → planned`. Neither requires falsely completing the task. Other tasks may work on prerequisites while one is blocked. Global blockers still prevent execution acceptance.

Allowed states: `planned → running` only through `accept`; `running → submitted/blocked/cancelled` only after executor termination; `submitted → completed/planned/cancelled`; `blocked → planned/cancelled`; `planned → cancelled`. Completed/cancelled tasks are terminal and remain in history.

## Decide Phase Separately

```bash
python3 scripts/research.py phase --project ./projects/study --to ideation --reason "Core checked scope exit criteria; remaining reference checks can continue as tasks" --evidence research-brief.md
```

Run this only when the cited evidence actually warrants the decision, not automatically after one task finishes. It requires no running executor, no global blockers, a legal core-table transition, rationale and nonempty evidence. Planned/blocked tasks may carry over; their creation phase does not bind execution. Exit criteria are scientific judgments the core must check, not machine-inferred truth.

`review → complete` additionally requires all tasks completed/cancelled and valid evidence and final-review audits. A protocol cannot substitute for raw evidence. Planning-only work may instead be paused/stopped by the core without claiming verified research completion.

## Compatibility

State, packet and receipt schema are now 3. Schema 1/2 is rejected; do not just change the version number. `--session` replaces `--context`; `--to` belongs only to `phase`. See [migration](architecture.md). No original library, external project, host configuration, schedule or experiment is modified by the framework refactor.
