# Flat Architecture and Migration

## One Decision Layer

[The core SKILL.md](../SKILL.md) owns research goals, task selection, skill/role/model choices, sessions, permissions, evidence acceptance and phase decisions. Specialists only perform bounded technical work and return artifacts or blockers. Direct discovery remains `skills/<name>/SKILL.md`; no domain profiles, capability registry or fixed role bundles are reintroduced.

## Three Orthogonal Concepts

- **Phase:** project-level goal and exit criteria. Every working phase can involve several tasks, including scope and ideation. Phase changes are independent core decisions, not side effects of dispatch.
- **Task:** a stable bounded objective, activity, one skill, role and acceptance standard. It survives session replacement and retries. A changed contract gets a new task ID.
- **Assignment packet:** one request to work on an existing task. Its `packet_id` identifies an attempt and never substitutes for `task_id` or a host session ID.
- **Session:** a host resource carrying working history. It may serve compatible tasks serially, while one task may span multiple sessions. Context is its information, not an additional manager or state machine.

A packet is merely an assignment record linking a task to a requested execution. `packet_id` identifies an attempt; it cannot substitute for `task_id` or a real host session ID. Requests are read-only, acceptance records execution, submission records returned work, and completion records core acceptance. Only the separate `phase` operation advances research phase.

Core → select task → assign one skill in a session → inspect submission → complete or replan task. Separately: core assesses phase goals → records a justified phase decision.

## State and Safety

Schema-6 `research-state.json` contains `tasks`, a list of running `active_tasks` IDs, compact assignment records, and append-only decision `history`. Full assignment packets and actual receipts are saved separately under `handoffs/`. No new routing configuration or task/session service is needed. The four-root-document initialization and hypothesis/run artifact layout remain unchanged.

Explicit core commands atomically save state with revision checks. They do not run in the background, choose what to do next, or authorize specialists to edit state. Use one writer; no distributed lock or cost meter is implied. The narrative log is maintained separately and is not part of an atomic cross-file transaction.

Evidence gates follow actual task activity, not project phase. An experiment in scope still requires research mode and a frozen protocol; a citation check in write does not need to pretend the project changed phase. Verified conclusions require audits wherever they are produced. Labeling is a core judgment, not an automatic classifier or security sandbox. Closure additionally checks all tasks are closed and the final review remains valid.

## Migration from Schema 1, 2, 3, 4 or 5

No automatic migration is performed. Schema-5 projects may use `migrate --project ...` only while in planning mode, with no running task or recorded in-flight job. Back up state, audit artifacts and host records first, and reconcile external jobs outside the helper. The command retains prior tasks and decisions, adds `goal`, `grant` and `reflections`, increments revision and invalidates unaccepted schema-5 packets; reissue packets and receipts. It does not infer past approvals. Older versions require manual migration; do not merely replace the schema version.

Migrating schema 3 to schema 4 is a reduction: drop the removed fields (`project_id`, `authorization`, `allowed_tools`, `budget`, `next_action`); record any prior experiment authorization as the evidence cited in a fresh `authorize --mode research` decision; express a paused project as open blockers instead of a status value; and reissue current packets and receipts at schema 4, because their shapes lost the authorization and budget snapshots.

Migrating schema 4 to schema 5 is also a reduction plus one rename: replace the `active_task` single-running pointer with an `active_tasks` list (parallel tasks hold mutually exclusive output scopes); move each assignment's full packet/receipt JSON out of the state into `handoffs/`, keeping only the compact record the helper writes; rewrite audit records at schema 2 with a nonempty reviewer, an ISO 8601 `reviewed_at` and verified claims. Receipts recorded before acceptance-timing was relaxed stay valid; only the `accepted_at` format is now enforced as ISO 8601.

1. Back up the project and evidence. Reconcile all host sessions and external jobs; stop or safely checkpoint live work before transferring ownership.
2. Prepare schema-4 state from the template, preserving actual question, current project phase, protocol and valid audit references. A previous handoff target is not proof the phase goal was achieved.
3. Reconstruct durable tasks with unique IDs, explicit activities and acceptance contracts. Separate tasks from their old request/packet IDs. Preserve old requests as historical evidence, not fabricated schema-3 assignments.
4. Record incomplete work as planned/blocked with checkpoint evidence. Do not invent actual session IDs or acceptance revisions. Reissue current packets and obtain actual matching receipts. An empty `active_tasks` list is correct only when no executor is running.
5. Preserve evidence paths where possible. Relocation or changed dependencies require updated references and fresh scientific review, not blind hash replacement.
6. Log the migration and retain prior decisions. The old `--to` handoff argument is removed: create work with the `task` command, assign it with `handoff --task <id>`, and reserve `phase --to` for a separate phase decision. Session flags replace context flags. Independent review is specified at task creation.

No real project was found under the framework during this change; external projects have not been searched or migrated. Original `.claude/` content remains untouched and reused-file provenance remains independent of task state.

## Limits

No model dispatch, automatic scheduler, host-session implementation, enforced tool-call gateway or scientific-truth checker is provided. `check-tool` can validate a cooperating host request but does not intercept calls, inspect arbitrary tool arguments or authenticate user consent. The helper validates explicit recorded decisions, inputs and receipts. Host assertions and core judgments remain necessary; changing a role prompt is not creating a new session.
