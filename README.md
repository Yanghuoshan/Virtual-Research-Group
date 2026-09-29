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
| [tests/](tests/) | Flat architecture, evidence integrity, input/output boundaries, and English coverage |
| [provenance.json](provenance.json) | Original hashes and adapted locations for reused source files; never used for routing |

The core owns the question, hypothesis priority, phase, selected skill, role, model, permissions, resources, output scope and acceptance decision. Specialists perform only their assigned technical task and return results or blockers. Only the core updates global findings and state.

## Specialist Skills

The 13 direct entries cover:

- Hypothesis generation/ranking and problem reformulation.
- ML manuscript writing and systems manuscript structure.
- Quantitative plotting, research diagram design, and conference talks.
- Citation identity and claim verification.
- Graph evaluation, vision evaluation, rollout/control evaluation, symbolic verification, and scientific surrogate validation.

These are focused methods, not universal training pipelines. A graph evaluator does not choose or train graph models. A writer does not commission experiments. Missing capabilities return to the core. Detailed references and templates remain inside their owning skill.

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

Paste the block below into the agent you want to install into; it finds its own skills directory, clones, and verifies.

```text
Install the "general-ai-research" skill bundle into this agent.

1. Determine this agent's user-level skills directory. For Claude Code it is
   ~/.claude/skills/; for CodeBuddy it is ~/.codebuddy/skills/; for any other
   agent use the directory that agent documents for user skills. Ask me before
   installing at project level instead.
2. Clone https://github.com/<your-org>/general-ai-research.git into
   <skills-dir>/general-ai-research. If that directory already exists, run
   git pull inside it instead. Do not clone anywhere else and do not copy files
   by hand.
3. Confirm <skills-dir>/general-ai-research/SKILL.md exists and that its YAML
   frontmatter name is general-ai-research. Stop and report the path if not.
4. Run: python3 <skills-dir>/general-ai-research/scripts/research.py validate
   and report the output verbatim.
5. Report the installed path and the validate result. Do not create a research
   project, run a skill, start experiments, modify other skills, install
   packages, or change agent configuration.
```

Replace `<your-org>/general-ai-research` with your repository before use.

## Quick Start

Python 3.10+; standard library only for the helpers. From this directory:

```bash
python3 scripts/research.py validate
python3 -m unittest discover -s tests -v
python3 scripts/research.py skills
python3 scripts/research.py init --project ./projects/graph-study --question "How do graph perturbations affect inductive generalization?"
python3 scripts/research.py task --project ./projects/graph-study --task t1 --objective "Compare explanations for graph sensitivity" --activity analysis --skill brainstorming-research-ideas --role strategist --acceptance "Every candidate includes a mechanism, falsifier and evidence limits"
python3 scripts/research.py handoff --project ./projects/graph-study --task t1 --model current --summary "Develop candidates from the supplied question" --evidence research-brief.md --outputs hypotheses/candidates-v1.md --session fresh
```

Initialization creates only `research-state.json`, `research-brief.md`, `research-log.md`, and `findings.md`. The full runtime directory contract, including `experiments/{hypothesis-id}/runs/{run-id}/`, is defined directly in the [core skill](SKILL.md). Other directories are created when a task needs them.

`handoff` prints a single explicit task request. It does not save the packet, switch models, run a skill, or change state. The host performs actual execution; the core owns acceptance and the next decision. See [operations](references/operations.md).

## Phase, Task, and Session

- **Phase:** a project-level research goal and exit criteria. Scope and ideation, like other working phases, can contain multiple tasks; they are not single executable steps.
- **Task:** a stable `task_id` with objective, activity, skill, role and acceptance criteria. It can be blocked, submitted, retried or completed without changing phase. New goals require new tasks.
- **Session:** a host execution resource. A task may continue in another session; related tasks may reuse a compatible session. Context is the information carried by the session, not another workflow entity.

Each `handoff` generates a new `packet_id` for an existing task. The core's explicit `accept` command validates and records a real receipt and starts that task; `task-status` separately records submission, blocking, output acceptance or cancellation. Neither changes phase. Only `phase --to ... --reason ... --evidence ...` records a phase decision.

Task activity controls safety in every phase: `experiment` requires authorization and a frozen protocol; `conclusions` requires verified evidence; `analysis` cannot silently perform either. Activities are declarations, not skill-routing presets. Phase goals and scientific acceptance remain core judgments.

Use `--session fresh` for substantial new work, changed models or independent review. `reuse` requires `--session-reason` and `--resume-session`; `current` requires a reason. Specify `--independent-review` when creating the task so retries cannot drop it. Reuse checks the latest recorded skill/role/actual model for the host session. See [session policy](SKILL.md#session-lifecycle) and [operations](references/operations.md).

Fresh sessions receive one skill and bounded evidence, not the entire conversation. The core still invokes the host's actual subagent/session facility; no helper command creates or resumes a session. Receipts bind the full packet digest and actual session identity, but host isolation and receipt authenticity must be checked by the core. No silent fallback is permitted.

## Extend Without Adding a Routing Layer

Add `skills/<name>/SKILL.md` with single-line `name` and `description` frontmatter and the specialist sections. It is immediately discoverable from disk; no registry edits are required. Add local references or scripts only when the task needs them. Test applicability, missing inputs, technical correctness, and refusal to delegate. See [specialist development](references/domain-development.md).

## Migration and Limits

This version replaces the earlier domain/capability configuration architecture. State, assignment packet and receipt schemas are now 3; older schemas are rejected rather than silently reinterpreted. No existing user research runs were found in the workspace. For external older projects, see [migration notes](references/architecture.md) and preserve their evidence before manual migration.

Automatic model execution, automatic state transitions, budget enforcement and a permissions sandbox are not implemented. The core contract remains authoritative even without helper scripts; structural validation cannot prove scientific truth or enforce a model's obedience.

Reused skill entries have been rewritten as specialists; references retain provenance. Do not claim the adapted entries are unchanged upstream copies. No conference LaTeX templates are bundled any more; download the current author kit from the venue's official source listed in the writing skills. Historical examples and license limitations remain; see [third-party notices](THIRD_PARTY_NOTICES.md). No experiment, schedule, git commit, or host installation is part of this refactor.

## License

First-party content is MIT licensed; see [LICENSE](LICENSE). Adapted upstream material keeps its own attribution and terms; see [third-party notices](THIRD_PARTY_NOTICES.md).
