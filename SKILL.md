---
name: general-ai-research
description: Use when managing an AI research project, deciding the next research action, or coordinating sequential specialist tasks across roles or models.
---

# General AI Research: Core Decision Maker

One decision layer, one flat collection of specialist skills. Read this document as the authoritative research and runtime contract. Supporting scripts check explicit decisions; they do not make research decisions.

## Core Decision Authority

Only the core selects hypotheses, phases, skills, roles, models, tool permissions, budgets, output paths, acceptance criteria, and the next task. Only the core initializes the project, freezes protocols, accepts results, updates global findings, and closes or pauses research.

- Maintain sole write ownership of `research-state.json`, `research-brief.md`, `research-log.md`, `findings.md`, and `handoffs/`. Specialists return proposed findings in task-local artifacts, never edit these global records.
- Delegate one bounded task to one skill at a time. A role describes responsibility, not a fixed skill bundle. Choose a model explicitly; never derive skills from a domain profile or merge role presets.
- Retain scientific judgment: decide whether evidence is relevant and sound, resolve contradictions, reject unsupported claims, and decide when to deepen, broaden, pivot, or stop.
- Default to planning only. User authorization is required for experiments, external services, spending, recurring operation, and git commits. Stronger core ownership does not grant authority beyond the user's request.
- Specialist skills may choose technical steps within their assignment. They must not select another skill, spawn agents, change models, schedule future work, advance research phases, or acquire new permissions. Missing inputs return to the core as blockers.

## Phase, Task, and Session

- **Phase:** the project's current research goal and exit criteria. It is not an executable assignment or a skill bundle.
- **Task:** a bounded work contract with a stable `task_id`, objective, activity, skill, role and acceptance criteria. A phase normally contains multiple tasks. A changed objective or acceptance contract requires a new task ID.
- **Session:** a host execution resource carrying working history. The core chooses a model and fresh/reuse/current session for an assignment. Context is the information inside a session, not a fourth workflow entity.
- **Assignment packet:** one request to work on an existing task. Its `packet_id` changes for each attempt; it is not the task ID, session ID, hypothesis ID or experiment run ID.

Session changes do not change task identity. A task can continue across several sessions; compatible related tasks may share an idle session when independence is unnecessary. Accepting a session receipt starts execution, not a new research phase. Completing a task does not complete its phase. Only the core can decide each of these events, independently.

## Task Lifecycle

Keep `tasks` and append-only decision `history` in `research-state.json`; no extra routing registry or manager is needed. `active_task` is the ID of the sole running task, not a packet or session object. Multiple planned, blocked and submitted tasks may coexist.

1. **Create:** the core registers a `planned` task with a unique lowercase ID, such as `t17`, and an immutable work contract. Its `created_phase` is informational. Specify whether independent review is required at creation, not per retry.
2. **Assign:** generate a packet for that task with current evidence, versioned output paths, requested model and session choice. Packet generation has no state side effects. The same task may receive multiple packets, but only one executor may run at a time.
3. **Accept execution:** after actual host selection and verification, the core records the matching receipt. Status becomes `running`; phase stays unchanged. Retain the packet and receipt under that task's assignment history.
4. **Submit or block:** an executor returns artifacts or diagnostics. After confirming the executor stopped and reconciling any in-flight jobs, the core records `submitted` or `blocked` and clears the running pointer. Submitted is not completed. Other tasks can now address prerequisites.
5. **Accept output or retry:** the core reviews a submission against its acceptance criteria. Only then mark it `completed`; reject stale artifacts or inputs. For bounded rework or resolved blockers, move back to `planned` with a reason and issue a new packet under the same task ID. Preserve previous submissions and attempts in history. Reuse old outputs as evidence but assign new output paths.
6. **Cancel:** the core may cancel unneeded tasks explicitly, retaining reasons and partial artifacts. Completed/cancelled IDs are never overwritten or reopened; create a new task for a new objective. Session termination alone cannot complete or cancel a task.

Helpers implement these explicit core operations, not an autonomous scheduler. Never let specialists call core state-changing commands. The core may plan further work while a task runs, but cannot accept concurrent execution. It separately evaluates the phase's exit criteria and invokes a phase decision when appropriate; no task or session operation advances phase automatically.

## Research Workspace

Keep the framework source separate from each research project's runtime directory:

```text
{project}/
├── research-brief.md                 # Core: question, scope, constraints
├── research-state.json               # Core: phase, revision, authorization, evidence status
├── research-log.md                   # Core: append-only decisions and actual execution records
├── findings.md                       # Core: accepted claim-to-evidence narrative
├── literature/                      # Sourced paper notes and verified bibliography
├── hypotheses/                      # Candidate hypotheses and ranking proposals
├── experiments/
│   └── {hypothesis-id}/
│       ├── protocol.md              # Frozen design accepted by the core
│       └── runs/
│           └── {run-id}/
│               ├── code/            # Run-specific code or references to versioned src/
│               ├── results/         # Raw measurements, proof certificates, logs
│               └── analysis.md      # Local interpretation, uncertainty, failures
├── src/                             # Reusable, versioned project code
├── data/                            # Data manifests, compact inputs and shared derived data
├── paper/                           # Versioned manuscripts, not fabricated results
├── reports/                         # Figures, talks, planning deliverables
├── reviews/                         # Version-bound audits and specialist review reports
└── handoffs/                        # Core: requests, receipts and acceptance records
```

Initialize only the four root documents; create other directories when needed. `scripts/research.py init` is an optional convenience implementing this contract, not a prerequisite to reasoning. It refuses existing targets. Resume an existing project instead of reinitializing it.

Use stable hypothesis IDs such as `H1` and unique run IDs such as `run-001`. Record the hypothesis ID, protocol path/hash, data version, code revision, configuration, seeds, resource usage, and result locations in each run. Distinguish a hypothesis from its repeated runs. Freeze `protocol.md` before execution; a changed design needs a new versioned hypothesis/protocol and re-review, never an overwritten history. The core may request a draft protocol, then accept and freeze it.

Keep reusable code in `src/` and run-specific code in `code/`; pin the actual code version used. Preserve negative runs, errors, and exploratory discoveries. Never overwrite raw evidence to match a manuscript. Put large datasets/checkpoints in user-approved external storage; record their URI, checksum, version and access conditions in `data/`, rather than copying them into the repository. Local audit manifests hash those references; the core must separately verify the external artifacts.

## Direct Skill Selection

1. Read the current question, state, accepted findings, last decision, and evidence.
2. Identify the smallest unresolved research question or artifact requirement. State why it matters now.
3. Inspect `skills/*/SKILL.md` descriptions, then read the candidate's full input, method, output, check, and boundary contract. Optional `scripts/research.py skills` lists entries directly from disk without a registration file.
4. Register a task with an objective, explicit activity, one applicable skill, role and acceptance criterion. Select an existing planned task instead when continuing the same contract. No suitable skill means report the gap; do not pretend an evaluator also trains models.
5. Prepare an assignment for that task: select model/session using the Session Lifecycle policy, provide evidence and fresh output paths, then invoke the host. Record the actual receipt before work. Inspect the returned submission and separately decide completion or rework. Neither assignment nor task completion advances phase.

Examples: source identity questions call for `citation-verification`; graph split validity calls for `graph-evaluation`; quantitative figures call for `academic-plotting`; a systems manuscript calls for `systems-paper-writing`. Read the actual files before selection. These examples are not a mandatory pipeline or a second registry.

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

Example scope tasks: clarify the question, check existing answers, assess data availability, and propose success criteria. Example ideation tasks: generate candidates, reformulate the problem, verify novelty evidence, critique mechanisms, and compare validation costs. These are optional examples, not a fixed checklist. Each has a distinct artifact and acceptance criterion; ordinary file reads or clarification turns are steps within a task.

A citation check during writing or a split audit during execution is another task, not a project-wide phase change. Tasks may remain planned or blocked across a justified phase change; their creation phase is provenance, not a routing restriction. Stop the active executor before changing phase. To close research, resolve or explicitly cancel all open tasks and recheck both evidence and final-review audits. Planning-only work may stop as paused/stopped without claiming completed research.

- **Scope and ideation:** identify the research question, verify literature, separate evidence from novelty conjectures, and rank falsifiable hypotheses. Do not assert novelty from search absence alone.
- **Design:** define the primary measure or proof obligation, baseline or known bound, validation design, uncertainty treatment, failure criteria, and budget. Evidence standards are common core rules; specialists contribute domain-specific checks.
- **Execution / inner loop:** accept a frozen protocol and required authorization, execute a bounded experiment or proof check, preserve raw outputs, and compare with the protocol. Missing executors are capability gaps, not permission to invent results.
- **Synthesis / outer loop:** inspect convergence or validity, leakage, baseline reproduction, uncertainty, and counterevidence. Ask what a result explains. The core alone promotes checked findings to `findings.md` and chooses deepen, broaden, pivot, or conclude.
- **Writing and review:** provide a verified claim set and target audience to the writer. Seek critical review without letting reviewers schedule revisions. The core decides whether more work is necessary.
- **Stop:** planning can end with a proposal or outline without passing through experimental writing gates. Set `status=paused` or `stopped` and document remaining gaps. Do not call an unverified draft a completed research result. No recurring loop is created by default.

## Evidence and Acceptance Gates

All assignments require existing nonempty input evidence, nonempty rationale and acceptance criteria, legal project-local output paths, active state, and no unresolved blockers. Do not permit specialists to overwrite inputs, existing outputs, global records, or the frozen protocol. Use new versioned outputs for revisions. Request new output targets, including directories; pre-existing directories or symlink targets are not an acceptable output scope.

At task creation, the core explicitly classifies the actual work, never inferring permission from phase, role, skill name or output directory:

- `analysis`: scoping, literature/citation checks, hypothesis generation, protocol design/audits, exploratory interpretation or clearly labeled outlines. No new experiment or presentation of unverified claims as established results is authorized.
- `experiment`: performing an experiment, simulation, benchmark, or computational proof check. Requires `mode=research`, experiment authorization, all four evaluation fields and the matching frozen protocol, even if the project is still in scope or ideation.
- `conclusions`: presenting research claims as verified, in writing, figures or talks. Requires the verified evidence audit below, even outside the write phase. Split combined experimental execution and verified-claim communication into separate tasks.

These three activity values are safety declarations, not new phases or a skill router. The helper cannot detect dishonest labeling; the core must inspect the objective, permitted tools and actual operations. Analysis that needs external retrieval still requires service authorization. Theoretical validation uses proof obligations and independent checking rather than assuming training or GPUs.

Writing research conclusions requires a verified audit JSON binding `findings.md`, the current protocol, and raw evidence under `experiments/` or `data/`. Completion additionally requires a passed final review binding current findings and the manuscript. Audit `subjects` are path/hash pairs. Changed subjects invalidate approval. Specialists may produce audit proposals; only the core sets approval state after checking their coverage and reasoning. Hash checks cannot prove truth or detect omitted dependencies.

## Session Lifecycle

Only the core creates, resumes, retires, or replaces sessions. Session choice is made per assignment, not automatically once per phase or once per task. Keep the core's decision history separate from specialist working history and allow only one running executor.

| Mode | Appropriate conditions | Required action |
|---|---|---|
| `fresh` | Substantial new work; changed model or responsibility; independent review; context overload or stale assumptions | Request a separate host session carrying only the task brief and relevant evidence |
| `reuse` | Local continuation or a compatible related task, with the same skill, role and actual model; useful valid history and no independence requirement | Verify the previous accepted assignment, explain why reuse helps, and resume its host-provided session ID |
| `current` | A small bounded task, or a core-approved fallback when isolation is not needed | Explain the exception; do not claim a role prompt creates an isolated session |

Detect context overload from actual symptoms: logs crowding out relevant inputs, repeatedly forgotten constraints, or invalidated hypotheses persisting. Do not invent token counts or a universal reset threshold. A phase label alone never forces session replacement. A changed task objective requires a new task contract, but does not necessarily require discarding a compatible idle session.

Independent review is a task-level requirement and always uses fresh execution, even on retry. Exclude the author's drafting conversation and self-justification; retain artifacts, raw evidence, known limitations and neutral criteria. A different session reduces carryover but does not prove scientific independence or truth. The same model may be appropriate in a new session.

### Minimal Context and Host Verification

Do not forward the full conversation, all skill documents, or large logs. Provide task ID, objective, one selected skill, role, current evidence paths/hashes, uncertainties, output boundaries, permissions and acceptance criteria. Each packet has a new packet ID and current state fingerprint, including for the same task. Retained history never overrides the current assignment. Fingerprint the core contract without asking specialists to become another research manager.

Use the host's actual create/resume facility. A fork inheriting the entire conversation is not fresh isolation. Record actual model, session mode and host-provided session ID in the receipt; never substitute task or packet IDs. If the host provides no ID, use null with an explanation, and do not claim that such a session is resumable. Verify history isolation for fresh execution and mark it false for current-session execution. The helper checks receipt consistency and recorded reuse identity; it cannot verify that host assertions are true.

No silent fallback: missing isolation, unavailable models or failed resume operations return to the core. Reissue a packet only if the revised request still satisfies the same task contract. Do not remove an independent-review requirement to use the author's current session. The `current` model alias alone cannot establish that the actual model is unchanged.

### Recovery Without Duplicate Work

Checkpoint artifacts and diagnostics, confirm the old executor has stopped, and reconcile job IDs, statuses and outputs before marking a running task blocked or submitted. A new session does not authorize rerunning an in-flight experiment or reset its budget. The core can then replan the same task and issue a fresh packet with new output paths, or cancel it explicitly. Preserve partial work and failures as evidence.

When the core itself changes session, transfer the state revision, tasks, active assignment/session, outstanding jobs and last decision through durable records. Reconcile in-flight work before continuing; never keep two decision owners or reset permissions/audit status because a session changed.

## Sequential Roles and Models

Roles describe responsibilities; skills provide methods; models and sessions are execution choices. None is a substitute for a task or phase. Specialists only return work, checks and blockers. Only the core accepts outputs, updates global findings, decides a retry, and judges phase exit criteria.

The optional helper now performs explicit core state operations (`task`, `accept`, `task-status`, `phase`), atomically recording each change and history in the project state. `handoff` remains read-only. No command creates a model session, starts experiments, enforces hard budgets, or provides a filesystem sandbox. Use a single state writer; atomic replacement and revision checks are not distributed locking. Keep a narrative log of scientific decisions separately. See [operations](references/operations.md) and [extension guidance](references/domain-development.md).
