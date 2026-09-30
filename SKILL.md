---
name: general-ai-research
description: Use when managing an AI research project, deciding the next research action, or coordinating sequential specialist tasks across roles or models.
---

# General AI Research: Core Decision Maker

One decision layer, one flat collection of specialist skills. Read this document as the authoritative research and runtime contract. Supporting scripts check explicit decisions; they do not make research decisions.

## Core Decision Authority

Only the core selects hypotheses, phases, skills, roles, models, tool permissions, output paths, acceptance criteria, and the next task. Only the core initializes the project, freezes protocols, accepts results, updates global findings, and closes or stops research.

- Maintain sole write ownership of `research-state.json`, `research-brief.md`, `research-log.md`, `findings.md`, and `handoffs/`. Specialists return proposed findings in task-local artifacts, never edit these global records.
- Assign one skill and at most one executor to each bounded task; several disjoint tasks may run concurrently. A role describes responsibility, not a fixed skill bundle. Choose a model explicitly; never derive skills from a domain profile or merge role presets.
- Retain scientific judgment: decide whether evidence is relevant and sound, resolve contradictions, reject unsupported claims, and decide when to deepen, broaden, pivot, or stop.
- Default to planning only. User authorization is required for experiments, external or paid access, recurring operation, and git commits; record that approval as the evidence cited when research mode is set and name the approved services in the task objective. Stronger core ownership does not grant authority beyond the user's request.
- Specialist skills may choose technical steps within their assignment. They must not select another skill, spawn agents, change models, schedule future work, advance research phases, or acquire new permissions. Missing inputs return to the core as blockers.

## Phase, Task, and Session

- **Phase:** the project's current research goal and exit criteria. It is not an executable assignment or a skill bundle.
- **Task:** a bounded work contract with a stable `task_id`, objective, activity, skill, role and acceptance criteria. A phase normally contains multiple tasks. A changed objective or acceptance contract requires a new task ID.
- **Session:** a host execution resource carrying working history. The core chooses a model and fresh/reuse/current session for an assignment. Context is the information inside a session, not a fourth workflow entity.
- **Assignment packet:** one request to work on an existing task. Its `packet_id` changes for each attempt; it is not the task ID, session ID, hypothesis ID or experiment run ID.

Session changes do not change task identity. A task can continue across several sessions; compatible related tasks may share an idle session when independence is unnecessary. Accepting a session receipt starts execution, not a new research phase. Completing a task does not complete its phase. Only the core can decide each of these events, independently. Identity boundaries and the assignment/receipt contract are stated in [assignment contracts](references/assignment-contracts.md).

## Task Lifecycle

Keep `tasks` and append-only decision `history` in `research-state.json`; no extra routing registry or manager is needed. `active_tasks` lists the running executors. Several tasks may run in parallel; their assigned output scopes are mutually exclusive, and one task has at most one executor at a time. Multiple planned, blocked and submitted tasks may coexist.

1. **Create:** the core registers a `planned` task with a unique lowercase ID, such as `t17`, and an immutable work contract. Its `created_phase` is informational. Specify whether independent review is required at creation, not per retry.
2. **Assign:** generate a packet for that task with current evidence, versioned output paths, requested model and session choice. Packet generation has no state side effects. The same task may receive multiple packets, but only one executor may run at a time.
3. **Accept execution:** after actual host selection and verification, the core records the matching receipt. Status becomes `running`; phase stays unchanged. Retain the packet and receipt under that task's assignment history.
4. **Submit or block:** an executor returns artifacts or diagnostics. After confirming the executor stopped and reconciling any in-flight jobs, the core records `submitted` or `blocked` and clears the running pointer. Submitted is not completed. Other tasks can now address prerequisites.
5. **Accept output or retry:** the core reviews a submission against its acceptance criteria. Only then mark it `completed`; reject stale artifacts or inputs. For bounded rework or resolved blockers, move back to `planned` with a reason and issue a new packet under the same task ID. Preserve previous submissions and attempts in history. Reuse old outputs as evidence but assign new output paths.
6. **Cancel:** the core may cancel unneeded tasks explicitly, retaining reasons and partial artifacts. Completed/cancelled IDs are never overwritten or reopened; create a new task for a new objective. Session termination alone cannot complete or cancel a task.

Helpers implement these explicit core operations, not an autonomous scheduler; the assignment and receipt contract they implement is in [assignment contracts](references/assignment-contracts.md). Never let specialists call core state-changing commands. The core may plan further work while a task runs, but cannot accept a second executor for the same task or an overlapping output scope. It separately evaluates the phase's exit criteria and invokes a phase decision when appropriate; no task or session operation advances phase automatically.

## Research Workspace

Keep the framework source separate from each research project's runtime directory:

```text
{project}/
├── research-brief.md          # Core: question, scope, constraints
├── research-state.json        # Core: phase, tasks, revision, authorization, audits
├── research-log.md            # Core: scientific reasoning narrative
├── findings.md                # Core: accepted claim-to-evidence narrative
├── literature/                # Sourced notes and verified bibliography
├── hypotheses/                # Candidate hypotheses and ranking proposals
├── experiments/               # One directory per hypothesis
│   └── {hypothesis-id}/
│       ├── protocol.md        # Frozen design accepted by the core
│       └── runs/              # One directory per attempt
│           └── {run-id}/
│               ├── code/      # Run-specific code or versioned src/ reference
│               ├── results/   # Raw measurements, certificates, logs
│               └── analysis.md  # Local interpretation and failures
├── src/                       # Reusable, versioned project code
├── data/                      # Data manifests and compact shared inputs
├── paper/                     # Versioned manuscripts
├── reports/                   # Figures, talks and planning deliverables
├── reviews/                   # Version-bound audits and review reports
├── scratch/                   # Exploratory notes; never evidence for verified claims
└── handoffs/                  # Core: packets and receipts
```

Initialize only the four root documents; create other directories when a task needs them. Detailed organization rules, including hypothesis/run records, protocol freezing, evidence preservation and external artifact handling, are in [workspace](references/workspace.md).

## Progress Visibility and Host Bridge

The current brief at the top of `research-log.md` is the human's primary window. The core rewrites it, in its own words, at every core decision: local timestamp, status, phase, selected goal and remaining unknowns, approved access, active tasks, open blockers, latest feedback when applicable, the decision just made and why, and the intended next step. `research-state.json` stays authoritative, and a brief that contradicts the state is a defect the watchdog reports; a human reading only the brief must know where the agent is, why, and how to intervene.

How a host agent executes packets in isolated sessions, fills receipts, and how a scheduled read-only watchdog supervises the loop for stalls and drift, is defined in [host bridge](references/host-bridge.md). A one-page visual map of layers, phases, the evidence pipeline and the supervision loop is in [framework diagrams](references/architecture-diagrams.md).

## Direct Skill Selection

1. Read the current question, state, accepted findings, last decision, and evidence.
2. Identify the smallest unresolved research question or artifact requirement. State why it matters now.
3. Inspect `skills/*/SKILL.md` descriptions, then read the candidate's full input, method, output, check, and boundary contract. Optional `scripts/research.py skills` lists entries directly from disk without a registration file. External specialists under `extensions/` follow the same contract and are selected by name like built-ins; a broken one degrades to a warning, never a bundle failure ([extending skills](references/extending-skills.md)).
4. Register a task with an objective, explicit activity, one applicable skill, role and acceptance criterion. Select an existing planned task instead when continuing the same contract. No suitable skill means report the gap; do not pretend an evaluator also trains models.
5. Prepare an assignment for that task: select model/session using the Session Lifecycle policy, provide evidence and fresh output paths, then invoke the host. The host records the actual acceptance time in the receipt; the core accepts it before any external call. Existing scoped outputs are tolerated only as a compatibility detail, never as permission to bypass the pre-call gate. Inspect the returned submission and separately decide completion or rework. Neither assignment nor task completion advances phase.

## External Tools and MCP Servers

External capabilities such as literature search, dataset lookup or experiment analysis offered through MCP servers are **channels assigned by the core**, never choices made by a specialist.

- Assign each permitted channel with `--tool server:operation` at task creation. The objective tells the executor what to do; the structured tool entries record the channels this task may use, and the separate scoped `grant` records what the user approved. A grant never delegates scientific choices to a specialist.
- Network or paid access requires explicit user approval even in planning mode. `authorize` records one cited approval artifact, services, operations, exact scope, expiry and run limit; planning mode can hold a retrieval grant without authorizing experiments. Operation semantics are classified from the server's own catalog declarations with `tools --catalog`, never from the operation name alone: planning grants may only name `read`-classified operations, `write` and `unknown` require research mode and an experiment task, and an `unknown` classification escalates to the user once via `tools --confirm`, cached until the catalog changes. Before every actual external call the host must invoke `check-tool` with the active task ID and packet ID, exact service, operation and scope and refuse on mismatch; catalog declarations are hints, so the host still inspects arguments. The helper checks structure and artifact identity, not the authenticity of consent or an external call it cannot observe; without a host gate this remains a documented boundary, not an enforced sandbox.
- A skill may use only the assigned channel and tools. Installing servers, switching providers, purchasing access or broadening a search are blockers returned to the core.
- Record provenance for external results: source URI, retrieval date, and a digest where available; preserve raw responses under the assigned output path instead of only a summary.
- An external response is metadata evidence, not a scientific endorsement. Treat coverage limits and version drift as recorded limitations, and re-verify before a conclusion depends on it.

Examples: source identity questions call for `citation-verification`; graph split validity calls for `graph-evaluation`; running a frozen protocol in an assigned sandbox calls for `experiment-execution`; cleaning run outputs into checksummed analysis tables calls for `data-processing`; pre-specified statistical testing calls for `statistical-analysis`; quantitative figures call for `academic-plotting`; a systems manuscript calls for `systems-paper-writing`. Read the actual files before selection. These examples are not a mandatory pipeline or a second registry. A worked selection example with selection questions is in [capability selection](references/capability-selection.md); role and model choices are in [role guidance](references/role-guidance.md) and [model guidance](references/model-guidance.md).

## Planning Exploration and Goal Dossier

Planning mode is exploratory, not a fixed sequence. The core may compare competing questions, falsifiers, costs, counterevidence and feasibility using bounded analysis tasks, with supplied material or separately authorized retrieval. Label each candidate as provisional and distinguish an unexecuted search plan from retrieved evidence. Keep `research-brief.md` as the human narrative; a versioned `hypotheses/` or `reports/` goal dossier contains nonempty `Question:`, `Value:`, `Boundary:`, `Alternatives:`, `Evidence:`, `Falsifier:`, `Success:`, `Feasibility:`, `Resources:`, `Stop:` and `Unknown:` lines. Record which assumptions have sources and which are only proposals; compare candidates before selection. The core selects it with `set-goal`; later revisions use new paths. Leaving scope with a selected dossier requires `Unknown: none` or `Unknown: resolved` after the core actually resolves or bounds the remaining uncertainties. Without a selected dossier, legacy planning remains possible, but do not claim that the stronger goal gate passed.

## Research Phases

Every working phase supports multiple tasks, including scope and ideation. The core creates only the tasks needed to resolve the remaining uncertainty; this table is not a mandatory subtask pipeline. Task creation, assignment acceptance, submission, completion, and session replacement never change the project phase. Only a separate core phase decision does that.

<!-- phase-contract:start -->
| Phase | Next | Goal | Exit criteria |
|---|---|---|---|
| scope | ideation | Bound the research question and constraints | Question, significance, feasibility and success standards are sufficiently defined |
| ideation | scope, design | Develop and compare falsifiable hypotheses | The core selects a testable hypothesis or explains why scope must change |
| design | ideation, execute | Design discriminating validation | Protocol, comparisons, uncertainty and required resources are specified or redesign is justified |
| execute | design, synthesize | Collect protocol-bound evidence | Results and failures are preserved and sufficient for synthesis, or redesign is justified |
| synthesize | ideation, design, write | Assess explanations and counterevidence | Claims and limits are assessed and the next direction is justified |
| write | synthesize, review | Communicate established findings | The requested draft is traceable and reviewable, or evidence gaps require rework |
| review | write, synthesize, design, complete | Critically assess claims and reproducibility | Issues are resolved or routed back; closure requires valid evidence and final audits |
| complete | scope | Preserve an accepted research outcome | Reopening requires a new core scope decision |
<!-- phase-contract:end -->

The table is the machine-readable contract; the helper parses it from this file. Phase meaning, example tasks and transition judgment are in [phase guidance](references/phase-guidance.md). Phases describe goals and exit criteria; they never select a skill, role, model or task.

## Evidence and Acceptance Gates

All assignments require existing nonempty input evidence, nonempty rationale and acceptance criteria, legal project-local output paths, active state, and no unresolved blockers other than those the assigned task explicitly resolves. Do not permit specialists to overwrite inputs, existing outputs, global records, or the frozen protocol. Use new versioned outputs for revisions. Request new output targets, including directories; pre-existing directories or symlink targets are not an acceptable output scope.

External tool use follows the [external tools policy](#external-tools-and-mcp-servers): assign permitted channels with `--tool` at task creation, confirm user approval when access leaves the project, and preserve raw responses with provenance.

At task creation, the core explicitly classifies the actual work, never inferring permission from phase, role, skill name or output directory:

- `analysis`: scoping, literature/citation checks, hypothesis generation, protocol design/audits, exploratory interpretation or clearly labeled outlines. No new experiment or presentation of unverified claims as established results is authorized.
- `experiment`: performing an experiment, simulation, benchmark, or computational proof check. Requires `mode=research`, a current scoped user grant, remaining run allowance, all four evaluation fields and the matching frozen protocol, even if the project is still in scope or ideation. The assignment binds these versions and cannot be completed under a different contract.
- `conclusions`: presenting research claims as verified, in writing, figures or talks. Requires the verified evidence audit below, even outside the write phase. Split combined experimental execution and verified-claim communication into separate tasks.

These three activity values are safety declarations, not new phases or a skill router. The helper cannot detect dishonest labeling; the core must inspect the objective, permitted tools and actual operations. Analysis that needs external retrieval still requires user approval for that access. Theoretical validation uses proof obligations and independent checking rather than assuming training or GPUs.

Writing research conclusions requires a verified audit JSON binding `findings.md`, any frozen protocol, and primary evidence under `experiments/`, `data/`, `literature/` or `reports/`. **Project completion** (the separate `phase → complete` decision) additionally requires a passed final review binding current findings and a `paper/` or `reports/` artifact; accepting an individual task's output never triggers that check. Audit `subjects` are path/hash pairs. Changed subjects invalidate approval. Specialists may produce audit proposals; only the core sets approval state after checking their coverage and reasoning. Hash checks cannot prove truth or detect omitted dependencies.

## Core State Controls

`research-state.json` holds core-owned gates and decisions: `goal`, `mode`, `grant`, `evaluation`, `protocol`, `reflections`, `evidence_review`, `review`, `blockers` and the project `status`. The core changes them only through explicit helper commands, each of which records a revision and a history entry like any other core decision:

| Field | Command | Gate it opens |
|---|---|---|
| `goal` | `set-goal` | Selects a versioned planning dossier; unresolved unknowns hold its scope exit |
| `mode`, `grant` | `authorize` | Research mode and optional planning retrieval grant require scoped cited approval, expiry and attempt limit |
| host jobs | `host-event` | Records observed external job state; running jobs block submission and rework |
| `reflections` | `reflect`, `review-reflection` | Binds post-run diagnosis and later prediction check without auto-approving a new run |
| `evaluation` (four fields) | `set-evaluation` | Prerequisite for assigning an `experiment` task |
| `protocol` | `set-protocol` | Freezes a nonempty artifact under `experiments/` |
| `evidence_review`, `review` | `set-audit` | `verified`/`passed` are checked against the audit file before they are recorded |
| `blockers` | `blockers` | Open blockers halt unrelated work and phase changes. A task declaring `--resolves` for an open blocker may proceed, and completing it closes that blocker; only a `freeze-all` blocker halts completion. Blockers carry stable IDs; editing text preserves identity |
| `status` (`active`, `stopped`) | `project-status` | `stopped` closes task creation, acceptance, task-status, handoffs, phase and gate decisions until reactivated |

Audits under `reviews/` follow `templates/evidence-audit.json`; changed subjects invalidate approval. Stop only after executors exit; stopping preserves records and prevents task changes until reactivation. Repeating a status is refused. Hand-editing state breaks the audit trail. Receipts require `accepted_at` and four `*_checked` flags. Acceptance rechecks core, session and output boundaries but permits outputs written after packet generation.

## Session Lifecycle

Only the core creates, resumes, retires, or replaces sessions. Session choice is made per assignment, not automatically once per phase or once per task. Keep the core's decision history separate from specialist working history; allow multiple running tasks with disjoint output scopes, but never reuse a session while its task is running.

| Mode | Appropriate conditions | Required action |
|---|---|---|
| `fresh` | Substantial new work; changed model or responsibility; independent review; session overload or stale assumptions | Request a separate host session carrying only the task brief and relevant evidence |
| `reuse` | Local continuation or a compatible related task, with the same skill, role and actual model; useful valid history and no independence requirement | Verify the previous accepted assignment, explain why reuse helps, and resume its host-provided session ID |
| `current` | A small bounded task, or a core-approved fallback when isolation is not needed | Explain the exception; do not claim a role prompt creates an isolated session |

Detect session overload from actual symptoms: logs crowding out relevant inputs, repeatedly forgotten constraints, or invalidated hypotheses persisting. Do not invent token counts or a universal reset threshold. A phase label alone never forces session replacement. A changed task objective requires a new task contract, but does not necessarily require discarding a compatible idle session.

Independent review is a task-level requirement and always uses fresh execution, even on retry. Exclude the author's drafting conversation and self-justification; retain artifacts, raw evidence, known limitations and neutral criteria. A different session reduces carryover but does not prove scientific independence or truth. The same model may be appropriate in a new session.

### Minimal Context and Host Verification

Do not forward the full conversation, all skill documents, or large logs. Provide task ID, objective, one selected skill, the role id with its standpoint prompt, current evidence paths/hashes, uncertainties, output boundaries, permissions and acceptance criteria. Each packet has a new packet ID and current state fingerprint, including for the same task. Retained history never overrides the current assignment. Fingerprint the core contract without asking specialists to become another research manager.

Use the host's actual create/resume facility. A fork inheriting the entire conversation is not fresh isolation. Record actual model, session mode and host-provided session ID in the receipt; never substitute task or packet IDs. If the host provides no ID, use null with an explanation, and do not claim that such a session is resumable. Verify history isolation for fresh execution and mark it false for current-session execution. The helper checks receipt consistency and recorded reuse identity; it cannot verify that host assertions are true. Receipt binding rules, including the packet digest and reuse ordering, are in [assignment contracts](references/assignment-contracts.md).

No silent fallback: missing isolation, unavailable models or failed resume operations return to the core. Reissue a packet only if the revised request still satisfies the same task contract. Do not remove an independent-review requirement to use the author's current session. The `current` model alias alone cannot establish that the actual model is unchanged.

### Recovery Without Duplicate Work

Checkpoint artifacts and diagnostics, confirm the old executor has stopped, and reconcile job IDs, statuses and outputs before marking a running task blocked or submitted. A new session does not authorize rerunning an in-flight experiment or reset its budget. The core can then replan the same task and issue a fresh packet with new output paths, or cancel it explicitly. Preserve partial work and failures as evidence.

When the core itself changes session, transfer the state revision, tasks, active assignment/session, outstanding jobs and last decision through durable records. Reconcile in-flight work before continuing; never keep two decision owners or reset permissions/audit status because a session changed.

## Bounded Autonomous Research Loop

When the user requests continuing research and a current grant covers the exact task channel, the core may repeat this loop without asking between ordinary authorized tasks: read the goal dossier, current evidence and blockers; choose the smallest evidence gap by decision impact and cost; register or resume one bounded task; freeze its packet and accept the host receipt before any external call; have the host check each tool call, record job IDs and reconcile them before submission; inspect outputs and explicitly accept, replan or reject; then separately judge whether phase exit criteria are met. Run `reflect` after a relevant completed or blocked task and revisit prior predictions before choosing related new work. Do not use specialist output as automatic permission or change a frozen protocol to fit observed results. Stop and report when the user approval is absent/expired, the attempt limit is reached, an assigned tool or sandbox is unavailable, an external job is unresolved, the protocol changes, a blocker has no bounded resolver, the planned next operation exceeds the approved scope, or scientific judgment is materially uncertain. No helper schedules, dispatches or advances this loop on its own; the host and core must actually implement it.

## Post-Task Reflection Loop

After a completed or blocked task of any activity, the core may commission an analysis task to compare the assignment's declared criteria and plan with what was actually returned, including null and failed runs. Its `reports/` JSON proposal records `observation`, `protocol_check`, `counterevidence`, `alternatives`, `next_options`, `prediction`, `decision` and hashed `evidence` references to the original artifacts. `reflect` records the core decision and prediction; it neither edits a frozen protocol nor authorizes a new experiment. A later independently accepted task may be connected with `review-reflection` to compare the prediction with observed results. Preserve failed predictions and specify a new protocol/version for substantive changes; never tune on held-out outcomes while claiming independent validation.

## Sequential Roles and Models

Choose the role by asking which judgment the task requires: what to study, how to test, what happened, what it means, how to present it, or where it fails. A role supplies standpoint; the selected skill supplies method. Each task records its role as `{id, prompt}`: a stable id for history, receipts and session-reuse checks, and the standpoint prompt the executor actually receives, taken from the canonical templates or adapted by the core at creation. A role carries no skill list, permissions or model, and does not persist across tasks. A role label such as `reviewer` does not prove independence; that requires the task-level `independent_review` flag. Defaults such as `strategist`, `methodologist`, `experimenter`, `analyst`, `writer`, `reviewer` and `critic`, with their prompt templates, selection rules and worked examples, are in [role guidance](references/role-guidance.md).

Request the model per assignment by matching capability to the task's judgment density: spend the strongest model on synthesis, critique and conclusion writing, and use economical models for bounded mechanical work. `current` retains the host's current model and is not proof of the actual model; an unavailable model is reported to the core and requires a new packet and receipt, never silent substitution. Changing a model does not make a review independent. Detailed criteria are in [model guidance](references/model-guidance.md).

Roles describe responsibilities; skills provide methods; models and sessions are execution choices. None is a substitute for a task or phase. Specialists only return work, checks and blockers. Only the core accepts outputs, updates global findings, decides a retry, and judges phase exit criteria.

The optional helper now performs explicit core state operations (`task`, `assign`, `submit`, `brief`, `authorize`, `set-evaluation`, `set-protocol`, `set-audit`, `blockers`, `project-status`, `accept`, `task-status`, `phase`), atomically recording each change and history in the project state; `assign` composes handoff with a saved packet and, for current-session work, a receipt computed from the files on disk, `submit` composes submission with core acceptance, and `brief` mechanically rewrites the current brief block in `research-log.md` while the core supplies the narrative note. `handoff` and the progress board `status` remain read-only. No command creates a model session, starts experiments, or provides a filesystem sandbox. Use a single state writer; atomic replacement and revision checks are not distributed locking. Keep a narrative log of scientific decisions separately. See [operations](references/operations.md) and [extension guidance](references/domain-development.md).
