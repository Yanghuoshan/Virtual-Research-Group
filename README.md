# General AI Research: Flat, Core-Controlled Architecture

One core decision maker directly assigns bounded tasks to professional skills. There is no domain configuration layer, capability registry, role-to-skill preset, or automatic skill pipeline. All maintained text is English. The original `.claude/` library remains untouched.

## Source Layout

| Entry | Responsibility |
|---|---|
| [SKILL.md](SKILL.md) | Authoritative core decisions, research phases, runtime workspace, evidence gates, and role/model handoffs |
| [skills/](skills/) | One flat namespace of specialist skills; each has inputs, method, outputs, checks, and a no-delegation boundary |
| [references/](references/) | Supporting explanations and operator instructions, not another decision layer |
| [templates/](templates/) | Runtime state, findings, log, audit and acceptance receipt |
| [scripts/research.py](scripts/research.py) | Optional deterministic helpers; no research decisions or model dispatch |
| [tests/](tests/) | Flat architecture, task lifecycle, session policy, evidence integrity, input/output boundaries, and English coverage |
| [provenance.json](provenance.json) | Original hashes and adapted locations for reused source files; never used for routing |

The core owns the question, hypothesis priority, phase, selected skill, role, model, permissions, resources, output scope and acceptance decision. Specialists perform only their assigned technical task and return results or blockers. Only the core updates global findings and state.

## Specialist Skills

The 23 direct entries cover:

- Hypothesis generation and ranking ([brainstorming](skills/brainstorming-research-ideas/SKILL.md)) and [problem reformulation](skills/creative-thinking-for-research/SKILL.md).
- [Literature review](skills/literature-review/SKILL.md): bounded search, screening and synthesis with traceable coverage limits; external retrieval needs authorization.
- [Experimental design](skills/experimental-design/SKILL.md): draft controls, statistical units, power/precision assumptions and validation plans; no protocol freezing or execution.
- [Experiment execution](skills/experiment-execution/SKILL.md), [data processing](skills/data-processing/SKILL.md) and [statistical analysis](skills/statistical-analysis/SKILL.md): run frozen protocols in an assigned sandbox, manifest the data, and run only pre-specified tests.
- [Reproducibility audit](skills/reproducibility-audit/SKILL.md): version-bound artifact and dependency checks; inspection is not an experimental rerun.
- [Manuscript review](skills/manuscript-review/SKILL.md): evidence-linked critique and final-review proposals; recommendations do not grant approval.
- [ML manuscript writing](skills/ml-paper-writing/SKILL.md) and [systems writing](skills/systems-paper-writing/SKILL.md).
- [Quantitative plotting](skills/academic-plotting/SKILL.md), [diagram design](skills/research-diagram-design/SKILL.md), and [conference talks](skills/presenting-conference-talks/SKILL.md).
- [Citation identity and claim verification](skills/citation-verification/SKILL.md).
- [Graph](skills/graph-evaluation/SKILL.md), [vision](skills/vision-evaluation/SKILL.md), [rollout/control](skills/robotics-evaluation/SKILL.md), [symbolic](skills/symbolic-verification/SKILL.md) and [surrogate](skills/scientific-surrogate-validation/SKILL.md) evaluation.
- [LLM evaluation](skills/llm-evaluation/SKILL.md): benchmark contamination, prompt/decoding sensitivity, variance and reporting audits; no benchmark runs.
- [Code model evaluation](skills/code-model-evaluation/SKILL.md): pass@k estimator, sandbox and oracle auditing; never executes generated code.
- [Interpretability validation](skills/interpretability-validation/SKILL.md): baseline, control and replication checks for internal-mechanism claims; no training or interventions.

These are focused methods, not universal training pipelines or a mandatory sequence. A graph evaluator does not choose or train graph models. A writer does not commission experiments. Only the core accepts protocols, approves audits, and selects follow-up tasks. Missing capabilities return to the core. Detailed methodological references remain inside their owning skill.

## Host Bridge and Watchdog

A host agent executes each packet in an isolated session and fills the receipt from actual execution facts; a scheduled read-only watchdog reports loop anomalies (silent tasks, receipt stalls, aging blockers, brief drift, project silence) to the human without changing state. Contracts and thresholds: [host bridge](references/host-bridge.md); visual map: [framework diagrams](references/architecture-diagrams.md).

## Install

This repository is a directory of skill documents, not a Python package. Install it by cloning it into the skills directory of the agent you use.

### Manual install

| Target | Command |
|---|---|
| Claude Code, user level | `git clone <repo-url> ~/.claude/skills/general-ai-research` |
| Claude Code, project level | `mkdir -p .claude/skills && git clone <repo-url> .claude/skills/general-ai-research` |
| CodeBuddy, user level | `git clone <repo-url> ~/.codebuddy/skills/general-ai-research` |
| Any other agent | clone into whatever directory that agent documents for user skills |

Requirements: Python 3.10+, standard library only, no build step.

Verify the install:

```bash
python3 <install-path>/scripts/research.py validate
python3 -m unittest discover -s <install-path>/tests
```

The directory name does not have to match the `name` in `SKILL.md`, but keep it stable so updating is just `git pull`. Updating never touches a research project directory.

### Agent-assisted install

Ask the agent to: clone `https://github.com/<your-org>/general-ai-research.git` into its user-level skills directory (`~/.claude/skills/` for Claude Code, `~/.codebuddy/skills/` for CodeBuddy; project level only on request; `git pull` if already present), confirm `SKILL.md` frontmatter `name general-ai-research`, then run `python3 <install-path>/scripts/research.py validate` and report the output verbatim. It must not create projects, run skills, start experiments, install packages or change agent configuration.

## Quick Start

Python 3.10+; standard library only for the helpers. From this directory:

```bash
python3 scripts/research.py validate
python3 -m unittest discover -s tests -v
python3 scripts/research.py skills
python3 scripts/research.py init --project ./projects/graph-study --question "How do graph perturbations affect inductive generalization?"
python3 scripts/research.py task --project ./projects/graph-study --task t1 --objective "Compare explanations for graph sensitivity" --activity analysis --skill brainstorming-research-ideas --role strategist --acceptance "Each candidate names a mechanism and falsifier"
python3 scripts/research.py handoff --project ./projects/graph-study --task t1 --model current --summary "Develop candidates" --evidence research-brief.md --outputs hypotheses/candidates-v1.md --session fresh
```

Initialization creates only `research-state.json`, `research-brief.md`, `research-log.md` and `findings.md`. The full runtime directory contract is in the [core skill](SKILL.md).

`handoff` prints one explicit task request; it saves nothing, runs nothing and changes no state. The host executes; the core owns acceptance and the next decision. See [operations](references/operations.md).

## Phase, Task, and Session

- **Phase:** a project-level research goal and exit criteria; working phases contain multiple tasks, not single executable steps.
- **Task:** a stable `task_id` with objective, activity, skill, role and acceptance criteria. It can be blocked, submitted, retried or completed without changing phase. New goals require new tasks.
- **Assignment packet:** one request to work on an existing task; its `packet_id` changes per attempt and never replaces the task ID.
- **Session:** a host execution resource. A task may continue in another session; related tasks may reuse a compatible session.

Each `handoff` generates a new `packet_id`. `accept` validates and records a real receipt and starts the task; `task-status` records submission, blocking, acceptance or cancellation. Neither changes phase; only `phase --to ... --reason ... --evidence ...` does.

Task activity controls safety in every phase: `experiment` requires research mode, all four evaluation fields and a frozen protocol; `conclusions` requires a verified evidence audit; `analysis` cannot silently perform either. Activities are declarations, not skill-routing presets. Those gates are set by explicit core commands, never by hand; see [operations](references/operations.md).

## Reading Project State

To see where an agent stands, read `research-state.json` in order: `status` (`active`/`stopped`; stopped is terminal), `blockers` (open blockers stop task creation, assignment, completion and phase decisions), `phase` (the research goal; only `phase` changes it), `active_task` (the sole running task), and `history` newest-last, recording every decision with action, reason, task id where applicable and cited evidence. `mode` (`planning`/`research`) is the single experiment gate. `research-log.md` opens with the current brief the core rewrites at every decision, so one file shows where the agent stands; roles are stored as `{id, prompt}` so the injected standpoint is inspectable.

Use `--session fresh` for substantial new work, changed models or independent review; `reuse` requires `--session-reason` and `--resume-session`, and `current` a reason. Specify `--independent-review` at task creation so retries cannot drop it. Reuse checks the latest recorded skill, role and actual model. See [session policy](SKILL.md#session-lifecycle) and [operations](references/operations.md).

Fresh sessions receive one skill and bounded evidence, not the entire conversation; no helper command creates or resumes a session, so the core invokes the host's facility and checks isolation and receipt authenticity itself. No silent fallback is permitted.

## Extend Without Adding a Routing Layer

Add `skills/<name>/SKILL.md` with single-line `name` and `description` frontmatter and the specialist sections. It is immediately discoverable from disk; no registry edits are required. Add local references or scripts only when the task needs them. Test applicability, missing inputs, technical correctness, and refusal to delegate. See [specialist development](references/domain-development.md).

## Migration and Limits

This version replaces the earlier domain/capability configuration architecture. State, packet and receipt schemas are now 4; older schemas are rejected rather than silently reinterpreted. Schema 4 drops the authorization flags (research mode is the single experiment gate), the `paused` status (open blockers now also stop task creation) and the unused `project_id`, `allowed_tools`, `budget` and `next_action` fields; see [migration notes](references/architecture.md) for the mapping. Audit records keep `schema_version` 1. No existing user research runs were found in the workspace; preserve external projects' evidence before manual migration.

Automatic model execution, automatic state transitions and a permissions sandbox are not implemented. The core contract remains authoritative; structural validation cannot prove scientific truth or enforce a model's obedience.

Reused skill entries were rewritten as specialists; do not claim they are unchanged upstream copies. No conference LaTeX templates are bundled; download author kits from the venues' official sources. Historical examples and license limitations remain; see [third-party notices](THIRD_PARTY_NOTICES.md). No experiment, schedule, git commit or host installation is part of this refactor.

## License

First-party content is MIT licensed; see [LICENSE](LICENSE). Adapted upstream material keeps its own attribution and terms; see [third-party notices](THIRD_PARTY_NOTICES.md).
