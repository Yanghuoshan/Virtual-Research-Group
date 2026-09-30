# General AI Research: Flat, Core-Controlled Architecture

One core decision maker directly assigns bounded tasks to professional skills; several tasks may run in parallel under mutually exclusive output scopes. There is no domain configuration layer, capability registry, role-to-skill preset, or automatic skill pipeline. All maintained text is English. The original `.claude/` library remains untouched.

## Source Layout

| Entry | Responsibility |
|---|---|
| [SKILL.md](SKILL.md) | Authoritative core decisions, research phases, runtime workspace, evidence gates, and role/model handoffs |
| [skills/](skills/) | One flat namespace of specialist skills; each has inputs, method, outputs, checks, and a no-delegation boundary |
| [extensions/](extensions/) | Optional third-party skills, held to the same contract; broken entries degrade to warnings |
| [references/](references/) | Supporting explanations and operator instructions, not another decision layer |
| [templates/](templates/) | Runtime state, findings, log, audit and acceptance receipt |
| [scripts/research.py](scripts/research.py) | Optional deterministic helpers; no research decisions or model dispatch |
| [tests/](tests/) | Flat architecture, task lifecycle, session policy, evidence integrity, input/output boundaries, and English coverage |
| [provenance.json](provenance.json) | Original hashes and adapted locations for reused source files; never used for routing |

The core owns the question, hypothesis priority, phase, selected skill, role, model, permissions, resources, output scope and acceptance decision. Specialists perform only their assigned technical task and return results or blockers. Only the core updates global findings and state.

## Specialist Skills

The 26 direct entries cover:

- Hypothesis generation and ranking ([brainstorming](skills/brainstorming-research-ideas/SKILL.md)) and [problem reformulation](skills/creative-thinking-for-research/SKILL.md).
- [Literature review](skills/literature-review/SKILL.md): bounded search, screening and synthesis with traceable coverage limits; external retrieval needs authorization.
- [Experimental design](skills/experimental-design/SKILL.md): controls, statistical units, power/precision assumptions and validation plans; no protocol freezing or execution.
- [Research implementation](skills/research-implementation/SKILL.md): accepted designs become tested project code; no experiments, no tuning toward results.
- [Experiment execution](skills/experiment-execution/SKILL.md), [data processing](skills/data-processing/SKILL.md) and [statistical analysis](skills/statistical-analysis/SKILL.md): run frozen protocols in an assigned sandbox, manifest the data, and run only pre-specified tests.
- [Results synthesis](skills/results-synthesis/SKILL.md): claim-evidence maps across runs and hypotheses; never promotes claims into findings.
- [Reproducibility audit](skills/reproducibility-audit/SKILL.md) and [manuscript review](skills/manuscript-review/SKILL.md): version-bound artifact checks and evidence-linked critique; recommendations do not grant approval.
- [ML manuscript writing](skills/ml-paper-writing/SKILL.md), [systems writing](skills/systems-paper-writing/SKILL.md) and [survey writing](skills/survey-writing/SKILL.md).
- [Quantitative plotting](skills/academic-plotting/SKILL.md), [diagram design](skills/research-diagram-design/SKILL.md), and [conference talks](skills/presenting-conference-talks/SKILL.md).
- [Citation identity and claim verification](skills/citation-verification/SKILL.md).
- [Graph](skills/graph-evaluation/SKILL.md), [vision](skills/vision-evaluation/SKILL.md), [rollout/control](skills/robotics-evaluation/SKILL.md), [symbolic](skills/symbolic-verification/SKILL.md) and [surrogate](skills/scientific-surrogate-validation/SKILL.md) evaluation.
- [LLM evaluation](skills/llm-evaluation/SKILL.md), [code model evaluation](skills/code-model-evaluation/SKILL.md) and [interpretability validation](skills/interpretability-validation/SKILL.md): audit supplied artifacts; never run benchmarks, execute generated code, or train models.

These are focused methods, not a mandatory sequence. A graph evaluator does not choose or train graph models. A writer does not commission experiments. Only the core accepts protocols, approves audits, and selects follow-up tasks.

## Host Bridge and Watchdog

A cooperating host agent executes each packet in the requested fresh, reused or current session and fills the receipt from actual execution facts; an optional host-level scheduled watchdog may report loop anomalies to the human without changing state. Contracts and thresholds: [host bridge](references/host-bridge.md); visual map: [framework diagrams](references/architecture-diagrams.md).

## Install

This repository is a directory of skill documents, not a Python package. Install by cloning it into the skills directory of the agent you use.

| Target | Command |
|---|---|
| Claude Code, user level | `git clone <repo-url> ~/.claude/skills/general-ai-research` |
| Claude Code, project level | `mkdir -p .claude/skills && git clone <repo-url> .claude/skills/general-ai-research` |
| CodeBuddy, user level | `git clone <repo-url> ~/.codebuddy/skills/general-ai-research` |
| Any other agent | clone into whatever directory that agent documents for user skills |

Requirements: Python 3.10+, standard library only, no build step. Verify the install:

```bash
python3 <install-path>/scripts/research.py validate
python3 -m unittest discover -s <install-path>/tests
```

The directory name does not have to match the `name` in `SKILL.md`, but keep it stable so updating is just `git pull`. Updating never touches a research project directory. An agent asked to install must not create projects, run skills, start experiments, install packages or change agent configuration.

## Quick Start

```bash
python3 scripts/research.py validate
python3 -m unittest discover -s tests -v
python3 scripts/research.py init --project ./projects/graph-study --question "How do graph perturbations affect inductive generalization?"
python3 scripts/research.py task --project ./projects/graph-study --task t1 --objective "Compare explanations" --activity analysis --skill brainstorming-research-ideas --role strategist --acceptance "Each candidate names a mechanism and falsifier"
python3 scripts/research.py handoff --project ./projects/graph-study --task t1 --model current --summary "Develop candidates" --evidence research-brief.md --outputs hypotheses/candidates-v1.md --session fresh
python3 scripts/research.py status --project ./projects/graph-study
```

Initialization creates only `research-state.json`, `research-brief.md`, `research-log.md` and `findings.md`. `handoff` prints one explicit task request; it saves nothing, runs nothing and changes no state. The host executes; the core owns acceptance and the next decision. See [operations](references/operations.md).

## Planning, Execution, and Feedback

In planning mode the core may explore several bounded candidate directions, select a versioned goal dossier with `set-goal`, and hold a separately approved retrieval grant without authorizing experiments. Research mode requires an explicit scoped user grant, expiry, attempt limit, frozen protocol and evaluation fields. Packets snapshot the execution contract; `check-tool` offers a read-only host preflight that returns a preflight token, `tool-call` records each external call against that token, `host-event` records job statuses, and `watch` reports active-task anomalies without taking action. After a completed or blocked task of any activity, `reflect` binds a raw-evidence-backed proposal and prediction; `review-reflection` connects a later result. None of these commands launches a model, enforces host calls without host cooperation, decides scientific truth or authorizes new work by itself. See [operations](references/operations.md) and [host bridge](references/host-bridge.md).

## Phase, Task, and Session

- **Phase:** a project-level research goal and exit criteria; working phases contain multiple tasks, not single executable steps.
- **Task:** a stable `task_id` with objective, activity, skill, role and acceptance criteria. It can be blocked, submitted, retried or completed without changing phase. A task created with `--resolves` names the blockers it exists to fix; completing it removes them.
- **Assignment packet:** one request to work on an existing task; its `packet_id` changes per attempt and never replaces the task ID.
- **Session:** a host execution resource. A task may continue in another session; related tasks may reuse a compatible session.

Several tasks may run in parallel under mutually exclusive output scopes. `accept` validates and records a real receipt and starts the task; `task-status` records submission, blocking, acceptance or cancellation. Neither changes phase; only `phase --to ... --reason ... --evidence ...` does.

## Reading Project State

Read `research-state.json` in order: `status`, `blockers` (only the task explicitly resolving a blocker may proceed while it remains open), `phase`, `goal`, `grant`, `active_tasks`, `reflections`, and `history` newest-last. `mode` (`planning`/`research`) is the single experiment gate. `research-log.md` opens with the current brief the core rewrites at every decision, and `scripts/research.py status --project ...` renders the same state as a one-page board. See [session policy](SKILL.md#session-lifecycle) and [operations](references/operations.md).

## Extend Without Adding a Routing Layer

Add `skills/<name>/SKILL.md` with single-line `name` and `description` frontmatter and the specialist sections; it is immediately discoverable from disk. Third-party skills go into `extensions/<name>/` under the same contract; a broken extension degrades to a warning and never breaks the bundle. See [extending skills](references/extending-skills.md) and [specialist development](references/domain-development.md).

## Migration and Limits

State, packet and receipt schemas are now 8; older schemas are rejected rather than silently reinterpreted. `migrate` explicitly upgrades only idle schema-5, schema-6 or schema-7 projects in planning mode; preserve a backup and reissue old packets. Schema 7 gave blockers stable IDs (`b1`, `b2`, ...), a resolution history, identity-preserving `--edit`, an explicit `--freeze-all` emergency stop, and completion of finished work that no longer freezes on foreign blockers; schema 8 makes per-task tool channels structured `--tool` assignments checked exactly, replacing objective substring matching. Schema 4 dropped the authorization flags, the `paused` status and the unused `project_id`, `allowed_tools`, `budget` and `next_action` fields; see [migration notes](references/architecture.md). Schema 5 adds parallel tasks with exclusive output scopes (`active_tasks` replaces `active_task`), task-level `resolves` declarations, acceptance that tolerates artifacts written during execution, compact assignment records, and audit schema 2 (reviewer, reviewed_at, verified claims). Audit records keep `schema_version` 2. No existing user research runs were found in the workspace; preserve external projects' evidence before manual migration.

Automatic model execution, automatic state transitions, a host tool-call enforcement gateway and a permissions sandbox are not implemented. `check-tool` and `watch` are read-only interfaces for a cooperating host, not deployed services. The core contract remains authoritative; structural validation cannot prove scientific truth or enforce a model's obedience. Reused skill entries were rewritten as specialists; do not claim they are unchanged upstream copies. No conference LaTeX templates are bundled; download author kits from the venues' official sources. Historical examples and license limitations remain; see [third-party notices](THIRD_PARTY_NOTICES.md). No experiment, schedule, git commit or host installation is part of this refactor.

## License

First-party content is MIT licensed; see [LICENSE](LICENSE). Adapted upstream material keeps its own attribution and terms; see [third-party notices](THIRD_PARTY_NOTICES.md).
