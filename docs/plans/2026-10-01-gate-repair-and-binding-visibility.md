# Gate Repair and Binding Visibility Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make the framework's gates cheap to clear instead of merely correct: every refusal names the command that clears it, hash bindings are visible and repairable, and frozen task channels have an explicit amendment path.

**Architecture:** Three additions to `scripts/research.py`, all additive to schema 8 (no new state fields, no migration). (1) A `Refusal` exception carrying executable repair steps, raised at every order-sensitive gate. (2) Two read-only commands — `next` (what is legal right now) and `bindings` (which hash bindings hold) — so locating state costs zero round trips. (3) One explicit write command `amend` that re-binds a gate artifact or a planned task's channels, records old/new hashes, and reports every downstream binding it breaks. Docs updated last.

**Tech Stack:** Python 3.10+ standard library only, `unittest`, no build step. Validation: `python3 scripts/research.py validate` and `python3 -m unittest discover -s tests`.

**Evidence this plan responds to** (40 refusals observed in one live project): ~12 state-machine timing, ~9 channel/registry/scope, ~6 artifact routing, ~6 hash/normalization, ~3 format. Two failures had real cost: three tasks destroyed by a registry rewrite with no channel repair path, and one task that became structurally uncompletable because `findings.md` was frozen as its own input.

---

### Task 1: Refusals that name the repair

**Files:**
- Modify: `scripts/research.py:46-48` (`require`), add `Refusal` and `refuse` beside it
- Modify: `scripts/research.py:1200-1208` (`open_project`)
- Modify: `scripts/research.py:730-741` (`create_task` gates)
- Modify: `scripts/research.py:826-831` (`handoff`)
- Modify: `scripts/research.py:868-874` (`accept_assignment`)
- Modify: `scripts/research.py:1246-1260` (`check_tool`)
- Create: `tests/test_gate_guidance.py`

**Step 1: Write the failing test**

```python
"""Gate refusals carry the command that clears them, and format/routing errors name the shape."""

import json
from pathlib import Path
import tempfile
import unittest

from test_framework import ROOT, load_tool


class GateGuidanceTests(unittest.TestCase):
    def setUp(self):
        self.tool = load_tool()
        self.temp = tempfile.TemporaryDirectory(dir=ROOT)
        self.addCleanup(self.temp.cleanup)
        self.project = Path(self.temp.name) / 'project'
        self.tool.initialize(ROOT, self.project, 'Study structural inductive biases')
        self.tool.create_task(ROOT, self.project, 't1', 'Compare explanations', activity='analysis',
                              skill='brainstorming-research-ideas', role='strategist',
                              acceptance='Each explanation has a falsifier')

    def test_stopped_project_refusal_names_the_reactivation_command(self):
        self.tool.set_project_status(ROOT, self.project, status='stopped', reason='Planning only')
        with self.assertRaisesRegex(ValueError, 'project-status .* --to active') as raised:
            self.tool.create_task(ROOT, self.project, 't2', 'More work', activity='analysis',
                                  skill='brainstorming-research-ideas', role='strategist',
                                  acceptance='Bounded')
        self.assertIn('Next:', str(raised.exception))

    def test_tool_gate_refusals_name_the_missing_step(self):
        for message in ('active assignment', 'does not match the active packet'):
            with self.subTest(message=message), self.assertRaisesRegex(ValueError, 'Next:'):
                self.tool.check_tool(ROOT, self.project, task_id='t1', packet_id='ghost',
                                     server='da-data', operation='search', scope='study')

    def test_iso_timestamp_refusal_names_the_expected_shape(self):
        with self.assertRaisesRegex(ValueError, 'ISO 8601') as raised:
            self.tool.authorize(ROOT, self.project, mode='research', reason='Bounded',
                                evidence=['reports/user-approval-v1.md'], services=['sandbox'],
                                operations=['run'], scope='study', max_runs=3, expires_at='tomorrow')
        self.assertIn('2099-01-01T00:00:00Z', str(raised.exception))
```

**Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_gate_guidance -v`
Expected: FAIL — refusals are bare rule statements, `Next:` never appears.

**Step 3: Write minimal implementation**

Insert after `require` (`scripts/research.py:48`):

```python
class Refusal(ValueError):
    """A gate refusal that names the repair, not only the rule that was hit.

    The gates are stateful and order sensitive, so a bare rule statement costs a
    round trip to locate the state the command was actually issued in. Steps are
    executable commands, never prose advice.
    """

    def __init__(self, message, *next_steps):
        self.message = message
        self.next_steps = [step for step in next_steps if step]
        super().__init__(message + ''.join(f' Next: {step}.' for step in self.next_steps))


def refuse(condition, message, *next_steps):
    """Like require, but the refusal carries the commands that clear the gate."""
    if not condition:
        raise Refusal(message, *next_steps)


def reactivate(project):
    """The one command that reopens every gate of a stopped project."""
    return (f'project-status --project {project} --to active '
            '--reason "<why the project resumes>"')
```

Replace the gate `require`s (keep `require` for programmer errors such as malformed IDs):

```python
# open_project, line 1207
    refuse(state['status'] == 'active',
           'Project is stopped; reactivate it before recording further decisions', reactivate(project))

# create_task, line 733
    refuse(state['status'] == 'active', 'Project is stopped; reactivate it before creating tasks',
           reactivate(project))

# handoff, line 831
    refuse(task['status'] == 'planned', 'Task must be planned before assignment',
           f'status --project {project}', f'next --project {project} --task {task_id}')

# accept_assignment, line 868
    refuse(receipt.get('packet_sha256') == packet_digest(packet), 'Receipt packet hash mismatch',
           f'handoff --project {project} --task {packet.get("task_id")} ... and save the new packet')
    refuse(packet.get('source_revision') == state['revision'] and packet.get('state_sha256') == fingerprint,
           'Packet is stale: state revision or hash changed',
           f'handoff --project {project} --task {packet.get("task_id")} ... and save the new packet')

# check_tool, lines 1246-1260
    refuse(state['status'] == 'active' and task_id in state['active_tasks'],
           'Tool access requires an active assignment',
           f'handoff --project {project} --task {task_id} --summary <summary> --model <model> '
           '--evidence <path> --outputs <path>',
           f'accept --project {project} --packet <packet> --receipt <receipt>',
           f'next --project {project} --task {task_id}')
    refuse(packet_id == assignment['packet_id'], 'Tool request does not match the active packet',
           f'handoff --project {project} --task {task_id} ... and accept the new packet')
    refuse(assignment['execution_contract']['grant'] == grant, 'Assignment grant changed',
           f'amend --project {project} --kind grant --reason "<why the approval artifact changed>"',
           f'task-status --project {project} --task {task_id} --status planned --reason "reissue packet"')
    refuse(server in grant['services'] and operation in grant['operations'] and scope == grant['scope'],
           'Tool request exceeds approved scope',
           f'authorize --project {project} --mode <planning|research> --reason <reason> '
           f'--evidence <approval-path> --services {" ".join(grant["services"])} '
           f'--operations {" ".join(grant["operations"])} --scope "{grant["scope"]}" '
           f'--max-runs <n> --expires-at <iso>')
    refuse(any(...), f'Tool {server}:{operation} was not assigned to task {task_id}; '
                     'assign channels at task creation with --tool server:operation',
           f'amend --project {project} --kind tools --task {task_id} --tool {server}:{operation} '
           '--reason "..." while the task is planned',
           f'task --project {project} --task <new-id> ... --tool {server}:{operation}')
```

Enrich `iso_timestamp` (`scripts/research.py:55-57`):

```python
def iso_timestamp(value, label):
    refuse(isinstance(value, str) and ISO_TIMESTAMP.fullmatch(value),
           f'{label} must be an ISO 8601 timestamp, for example 2099-01-01T00:00:00Z')
    return value
```

**Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.test_gate_guidance -v`
Expected: PASS.

**Step 5: Run the full suite** — `python3 -m unittest discover -s tests` — because `require` and `Refusal` must stay interchangeable for `assertRaisesRegex(ValueError, ...)`.

**Step 6: Commit**

```bash
git add scripts/research.py tests/test_gate_guidance.py
git commit -m "feat: gate refusals carry the command that clears them"
```

---

### Task 2: `next` — read-only "what is legal right now"

**Files:**
- Modify: `scripts/research.py` — add `next_steps_for`, register in `CLI` (near `scripts/research.py:1698`) and `RUNNERS` (`scripts/research.py:1773`)
- Modify: `scripts/research.py:1551-1580` (`render_brief`) and `1623-1665` (`status`) — add a "waiting on" line
- Modify: `tests/test_gate_guidance.py` — append tests

**Step 1: Write the failing test**

```python
    def test_next_lists_the_legal_moves_for_an_active_project(self):
        board = self.tool.next_steps_for(ROOT, self.project)
        self.assertEqual(board['status'], 'active')
        joined = ' '.join(entry['command'] for entry in board['legal'])
        self.assertIn('--task t1', joined, 'a planned task must offer handoff and cancellation')
        self.assertIn('phase ', joined)

    def test_next_gives_a_stopped_project_exactly_one_move(self):
        self.tool.set_project_status(ROOT, self.project, status='stopped', reason='Awaiting approval')
        board = self.tool.next_steps_for(ROOT, self.project)
        self.assertEqual(board['legal'], [])
        self.assertEqual(len(board['blocked']), 1)
        self.assertIn('--to active', board['blocked'][0]['next'][0])

    def test_next_explains_why_a_running_task_refuses_a_new_packet(self):
        packet = self.tool.handoff(ROOT, self.project, 't1', 'Work the evidence', ['research-brief.md'],
                                   model='current', outputs=['hypotheses/t1-v1.md'])
        self.tool.accept_assignment(ROOT, self.project, packet, self.receipt(packet))
        board = self.tool.next_steps_for(ROOT, self.project, task_id='t1')
        blocked = ' '.join(entry['reason'] for entry in board['blocked'])
        self.assertIn('running', blocked)
        self.assertIn('phase', ' '.join(entry['command'] for entry in board['blocked']))

    def test_status_and_brief_name_the_human_action_the_project_waits_on(self):
        self.tool.set_project_status(ROOT, self.project, status='stopped', reason='Awaiting approval')
        self.assertIn('Waiting on', self.tool.status(ROOT, self.project))
        self.assertIn('Waiting on', self.tool.render_brief(self.tool.project_state(ROOT, self.project)[0]))

    def receipt(self, packet, session_id='host:s1'):
        import hashlib
        digest = hashlib.sha256(json.dumps(packet, sort_keys=True, ensure_ascii=False,
                                           separators=(',', ':'), allow_nan=False).encode('utf-8')).hexdigest()
        return {'schema_version': 8, 'task_id': packet['task_id'], 'packet_id': packet['packet_id'],
                'source_revision': packet['source_revision'], 'packet_sha256': digest, 'accepted': True,
                'accepted_at': '2026-01-01T00:00:00+00:00', 'actual_role': packet['target_role']['id'],
                'actual_model': 'provider/model-a', 'actual_session_mode': packet['session']['mode'],
                'actual_session_id': session_id, 'session_isolation_verified': False,
                'session_notes': 'Host identity', 'state_hash_checked': True, 'core_hash_checked': True,
                'skill_hash_checked': True, 'evidence_hashes_checked': True}
```

**Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_gate_guidance -v`
Expected: FAIL with `AttributeError: module has no attribute 'next_steps_for'`.

**Step 3: Write minimal implementation**

Add near `watch` (`scripts/research.py:1080`):

```python
def next_steps_for(root, project, task_id=None):
    """Read-only: the commands legal right now, and the repair for everything else.

    Every gate is stateful and order sensitive, and a refusal by itself only says
    which rule was hit. This evaluates the gates against the current state so the
    core can see the legal move without spending a round trip discovering it.
    """
    state, _ = project_state(root, project)
    option = f'--project {project}'
    legal, blocked = [], []

    def allow(command, why):
        legal.append({'command': command, 'why': why})

    def block(command, reason, *steps):
        blocked.append({'command': command, 'reason': reason, 'next': list(steps)})

    if state['status'] == 'stopped':
        block('task, handoff, accept, task-status, phase, authorize, amend, blockers',
              'Project is stopped; task creation, handoffs, acceptance, task-status, phase and gate '
              'decisions are all closed', reactivate(project))
        return {'status': state['status'], 'phase': state['phase'], 'legal': legal, 'blocked': blocked}

    allow(f'status {option}', 'Read the current progress board')
    allow(f'next {option} [--task ID]', 'Re-read the legal moves after any decision')
    blockers = blocker_summary(state)
    if freeze_active(state):
        block('task, handoff, accept, task-status --status completed',
              f'A freeze-all blocker halts all task work ({blockers})',
              f'blockers {option} --resolve <blocker-id> --reason "..."')
    elif state['blockers']:
        allow(f'task {option} --task <id> --objective "..." --activity analysis --skill <name> '
              '--role <id> --acceptance "..." --resolves <blocker-id>',
              f'Only a task resolving an open blocker may proceed ({blockers})')
        block('task, handoff, accept for unrelated work',
              f'Open blockers halt unrelated work ({blockers})',
              f'blockers {option} --resolve <blocker-id> --reason "..."',
              f'blockers {option} --edit <blocker-id> --text "..." --reason "..."')
    else:
        allow(f'task {option} --task <id> --objective "..." --activity analysis --skill <name> '
              '--role <id> --acceptance "..."', 'Register a bounded task')

    selected = state['tasks'] if task_id is None else {k: v for k, v in state['tasks'].items() if k == task_id}
    if task_id is not None and not selected:
        block(f'next {option} --task {task_id}', f'Unknown task {task_id}', f'status {option}')
    for name, task in selected.items():
        if task['status'] == 'planned':
            allow(f'handoff {option} --task {name} --summary "..." --model <model> --evidence <paths> '
                  '--outputs <new-paths>', f'{name} is planned; issue an assignment')
            allow(f'task-status {option} --task {name} --status cancelled --reason "..."',
                  f'{name} is no longer needed')
        elif task['status'] == 'running':
            allow(f'task-status {option} --task {name} --status submitted --executor-stopped '
                  '--reason "..." --evidence <paths>', f'{name} is running; record its returned artifacts')
            block(f'handoff {option} --task {name}',
                  f'{name} is running; one task has at most one executor',
                  f'task-status {option} --task {name} --status blocked --executor-stopped --reason "..."')
        elif task['status'] == 'submitted':
            allow(f'task-status {option} --task {name} --status completed --reason "..."',
                  f'{name} is submitted; complete it after inspecting the artifacts')
            allow(f'task-status {option} --task {name} --status planned --reason "..."',
                  f'{name} needs bounded rework; issue a new packet with new output paths')
        elif task['status'] == 'blocked':
            allow(f'task-status {option} --task {name} --status planned --reason "..."',
                  f'{name} is blocked; move it back to planned once the blocker is resolved')
    if state['active_tasks']:
        block(f'phase {option} --to <phase>', 'A running executor holds the phase decision',
              f'task-status {option} --task {state["active_tasks"][0]} --status submitted '
              '--executor-stopped --reason "..." --evidence <paths>')
    else:
        allow(f'phase {option} --to {"|".join(core_phases(root)[state["phase"]]["next"])} '
              '--reason "..." --evidence <paths>', 'A separate core phase decision')
    return {'status': state['status'], 'phase': state['phase'], 'mode': state['mode'],
            'legal': legal, 'blocked': blocked,
            'note': 'Read only; every listed command is still checked when it runs'}


def waiting_on(state):
    """The human action the project is waiting for, or None when nothing blocks it.

    Most wall-clock time in a governed loop is deliberate waiting on a person.
    Naming it in the board and the brief is what makes that waiting visible
    instead of indistinguishable from a stalled loop.
    """
    if state['status'] == 'stopped':
        return 'human decision: reactivate the project (project-status --to active)'
    grant = state.get('grant')
    if isinstance(grant, dict) and nonempty(grant.get('expires_at')):
        expiry = datetime.fromisoformat(grant['expires_at'].replace('Z', '+00:00'))
        if expiry <= datetime.now(timezone.utc):
            return 'human approval: the grant expired; re-authorize with a cited approval artifact'
    if state['blockers']:
        return f'human or task action: {len(state["blockers"])} open blocker(s)'
    if state['mode'] == 'planning':
        return 'human approval: experiments and external access need a cited grant (authorize)'
    return None
```

Wire it into `render_brief` (append before the `Next:` line) and `status`:

```python
    waiting = waiting_on(state)
    if waiting:
        lines.append(f'- **Waiting on:** {waiting}')
```

Register the command (CLI entry next to `status`, runner next to `'status'`):

```python
    ('next', 'Read-only: the commands legal right now and the repair for the rest',
     (('project', PROJECT), ('task', {}))),
```

```python
    'next': lambda a: next_steps_for(ROOT, a.project, task_id=a.task),
```

**Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.test_gate_guidance -v`
Expected: PASS. Also run `python3 -m unittest tests.test_brief_watch -v`: adding a brief line must not break the drift check, because `watch` compares `render_brief` against itself.

**Step 5: Commit**

```bash
git add scripts/research.py tests/test_gate_guidance.py
git commit -m "feat: next command lists the moves legal in the current state"
```

---

### Task 3: `bindings` — every hash binding, visible

**Files:**
- Modify: `scripts/research.py` — add `binding_report`, register `bindings` in `CLI`/`RUNNERS`
- Modify: `scripts/research.py:1028-1080` (`watch`) — add a `binding-drift` anomaly
- Create: `tests/test_binding_repair.py`

**Step 1: Write the failing test**

```python
"""Hash bindings are visible and repairable instead of silent."""

import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from test_framework import ROOT, load_tool


class BindingRepairTests(unittest.TestCase):
    def setUp(self):
        self.tool = load_tool()
        self.temp = tempfile.TemporaryDirectory(dir=ROOT)
        self.addCleanup(self.temp.cleanup)
        self.project = Path(self.temp.name) / 'project'
        self.tool.initialize(ROOT, self.project, 'Investigate graph sensitivity')
        self.approval = self.write('reports/user-approval-v1.md', 'Approved bounded channel')
        self.tool.authorize(ROOT, self.project, mode='planning', reason='Bounded retrieval',
                            evidence=[self.approval], services=['da-data'], operations=['search_content'],
                            scope='study', max_runs=3, expires_at='2099-01-01T00:00:00Z')

    def write(self, name, text):
        path = self.project / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        return name

    def test_bindings_report_flags_a_broken_grant_binding(self):
        report = self.tool.binding_report(ROOT, self.project)
        self.assertEqual(report['broken'], [])
        self.write(self.approval, 'Approved bounded channel; corrected arXiv title')
        report = self.tool.binding_report(ROOT, self.project)
        self.assertEqual([row['binding'] for row in report['broken']], ['grant evidence'])
        self.assertIn('amend', report['broken'][0]['fix'])

    def test_watch_reports_binding_drift(self):
        self.write(self.approval, 'Corrected title')
        reasons = {problem['reason'] for problem in self.tool.watch(ROOT, self.project)['anomalies']}
        self.assertIn('binding-drift', reasons)
```

**Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_binding_repair -v`
Expected: FAIL with `AttributeError: module has no attribute 'binding_report'`.

**Step 3: Write minimal implementation**

```python
GATE_FIXES = {'grant evidence': 'amend --kind grant', 'protocol': 'amend --kind protocol',
              'goal dossier': 'amend --kind goal', 'evidence review': 'set-audit --kind evidence',
              'final review': 'set-audit --kind final'}


def binding_report(root, project):
    """Read-only: every hash binding in the project and whether it still holds.

    Bindings are global and silent: one edit breaks several gates at once and
    nothing reports it until the next refusal, which is why a correction costs
    three round trips. This lists them all so one command follows the edit.
    """
    state, _ = project_state(root, project)
    rows = []

    def add(binding, reference, task_status=None):
        if not isinstance(reference, dict) or not nonempty(reference.get('path')):
            return
        row = {'binding': binding, 'path': reference['path'], 'recorded_sha256': reference.get('sha256'),
               'task_status': task_status, 'fix': GATE_FIXES.get(binding, 'replan the task and reissue its packet')}
        target = Path(project).resolve() / reference['path']
        if target.is_file():
            row['current_sha256'] = digest(target)
            row['holds'] = row['current_sha256'] == reference.get('sha256')
        else:
            row.update(current_sha256=None, holds=False, detail='file is missing')
        rows.append(row)

    add('grant evidence', (state.get('grant') or {}).get('evidence'))
    add('protocol', state.get('protocol'))
    add('goal dossier', state.get('goal'))
    add('evidence review', state.get('evidence_review'))
    add('final review', state.get('review'))
    for task_id, task in state['tasks'].items():
        for assignment in task['assignments']:
            for record in assignment['evidence']:
                add(f'{task_id} assignment input', record, task['status'])
        for record in task['submission']:
            add(f'{task_id} submitted artifact', record, task['status'])
    for reflection in state.get('reflections', []):
        add('reflection artifact', reflection.get('artifact'))
    return {'bindings': rows, 'broken': [row for row in rows if not row['holds']],
            'note': 'Read only; amend rebinds one gate artifact and records old and new hashes'}
```

In `watch`, after the blocker-age loop:

```python
    for row in binding_report(root, project)['bindings']:
        if row['holds'] or row.get('task_status') in ('completed', 'cancelled'):
            continue
        problems.append({'reason': 'binding-drift',
                         'detail': f"{row['binding']}: {row['path']} no longer matches its recorded hash"})
```

Register: `('bindings', 'Read-only: every hash binding and whether it still holds', (('project', PROJECT),))` and `'bindings': lambda a: binding_report(ROOT, a.project)`.

**Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.test_binding_repair tests.test_brief_watch -v`
Expected: PASS. `test_watch_accepts_a_clean_project_without_anomalies` must still pass: an unchanged evidence file holds.

**Step 5: Commit**

```bash
git add scripts/research.py tests/test_binding_repair.py
git commit -m "feat: bindings report makes hash drift visible before a gate refuses"
```

---

### Task 4: Stop constructing an uncompletable task

**Files:**
- Modify: `scripts/research.py:1112-1122` (completion input recheck in `update_task`)
- Modify: `scripts/research.py:1107-1109` (`Unassigned run artifact`) and `1336` (audit routing)
- Modify: `tests/test_binding_repair.py` — append tests

**Step 1: Write the failing test**

```python
    def run_task(self):
        self.tool.create_task(ROOT, self.project, 't1', 'Compare explanations', activity='analysis',
                              skill='brainstorming-research-ideas', role='strategist',
                              acceptance='Each explanation has a falsifier')
        packet = self.tool.handoff(ROOT, self.project, 't1', 'Work the evidence', ['research-brief.md'],
                                   model='current', outputs=['hypotheses/t1-v1.md'])
        self.tool.accept_assignment(ROOT, self.project, packet,
                                    self.receipt(packet, session_id='host:s1'))
        return packet

    def test_core_record_input_drift_is_recorded_not_refused(self):
        # findings.md is the sink the core writes when it accepts results, so a
        # completion check demanding it stay byte-identical is unsatisfiable.
        self.tool.create_task(ROOT, self.project, 't9', 'Synthesize accepted findings',
                              activity='analysis', skill='results-synthesis', role='analyst',
                              acceptance='Bounded synthesis')
        packet = self.tool.handoff(ROOT, self.project, 't9', 'Synthesize', ['findings.md'],
                                   model='current', outputs=['reports/synthesis-v1.md'])
        self.tool.accept_assignment(ROOT, self.project, packet, self.receipt(packet, session_id='host:s9'))
        self.write('reports/synthesis-v1.md', 'Synthesis with limits')
        self.write('findings.md', 'Accepted finding recorded by the core')
        state = self.tool.update_task(ROOT, self.project, 't9', 'submitted', 'Returned synthesis',
                                      ['reports/synthesis-v1.md'], executor_stopped=True)
        state = self.tool.update_task(ROOT, self.project, 't9', 'completed', 'Core inspected it', [])
        self.assertEqual(state['tasks']['t9']['status'], 'completed')
        self.assertIn('findings.md', state['history'][-1].get('input_drift', []))

    def test_changed_versioned_input_is_refused_with_a_repair(self):
        self.run_task()
        evidence = self.write('literature/review-v1.md', 'Sourced notes')
        packet = self.tool.handoff(ROOT, self.project, 't1', 'Work the evidence', [evidence],
                                   model='current', outputs=['hypotheses/t1-v2.md'])
        self.tool.accept_assignment(ROOT, self.project, packet, self.receipt(packet, session_id='host:s2'))
        self.write(evidence, 'Sourced notes, revised')
        self.write('hypotheses/t1-v2.md', 'Mechanism and falsifier')
        self.tool.update_task(ROOT, self.project, 't1', 'submitted', 'Returned', ['hypotheses/t1-v2.md'],
                              executor_stopped=True)
        with self.assertRaisesRegex(ValueError, 'Next:') as raised:
            self.tool.update_task(ROOT, self.project, 't1', 'completed', 'Core inspected it', [])
        self.assertIn('task-status', str(raised.exception))
```

**Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_binding_repair -v`
Expected: the first test FAILS with `Task input hash mismatch`.

**Step 3: Write minimal implementation**

Above `update_task`:

```python
# The core rewrites these root documents as a direct consequence of deciding: the
# brief on every decision, findings on every acceptance. Binding one as a frozen
# contract input made completion unsatisfiable by construction, because recording
# the result is exactly what invalidated the input. They are snapshot inputs: the
# hash is taken at assignment and drift is recorded at completion, never refused.
CORE_MUTABLE_RECORDS = ('findings.md', 'research-log.md', 'research-brief.md')
```

In `update_task`, replace `for record in assignment['evidence']: verify_reference(project, record, 'Task input')`:

```python
        drift = []
        for record in assignment['evidence']:
            if record['path'] in CORE_MUTABLE_RECORDS:
                target = local_path(project, record['path'])
                if not target.is_file() or digest(target, cached=False) != record['sha256']:
                    drift.append(record['path'])
                continue
            try:
                verify_reference(project, record, 'Task input')
            except ValueError:
                current = digest(local_path(project, record['path']), cached=False)
                raise Refusal(f'Task input {record["path"]} changed since this assignment was accepted '
                              f'({str(record["sha256"])[:12]} -> {current[:12]})',
                              f'task-status --project {project} --task {task_id} --status planned '
                              '--reason "reissue the packet"',
                              f'task-status --project {project} --task {task_id} --status cancelled '
                              '--reason "..." and create a new task when the objective changed') from None
```

Add `input_drift` to the completion event alongside `auto_resolved`.

Enrich routing refusals:

```python
# update_task, line 1109
            refuse(any(...), f'Unassigned run artifact: {record["path"]}',
                   f'assign an output scope containing it at handoff time; this attempt holds '
                   f'{", ".join(allowed)}')

# set_audit, line 1336
    refuse(relative.parts[0] == 'reviews', 'Audit records belong under reviews/',
           f'write it from templates/evidence-audit.json to reviews/evidence-audit-v1.json, then '
           f'bind --project {project} --path findings.md <primary artifacts> for its subjects')
```

**Step 4: Run test to verify it passes**

Run: `python3 -m unittest discover -s tests`
Expected: PASS, including `test_task_lifecycle` (submitted-artifact and accept-time input checks are untouched).

**Step 5: Commit**

```bash
git add scripts/research.py tests/test_binding_repair.py
git commit -m "fix: core-owned records are snapshot inputs, so completion stays satisfiable"
```

---

### Task 5: `amend` — rebind a gate artifact with a record

**Files:**
- Modify: `scripts/research.py` — add `amend_binding` and `invalidated_bindings`, register `amend` in `CLI`/`RUNNERS`
- Modify: `scripts/research.py:1254` (`Assignment grant changed` already carries `amend` after Task 1)
- Modify: `tests/test_binding_repair.py` — append tests

**Step 1: Write the failing test**

```python
    def test_amend_rebinds_the_grant_and_reports_invalidated_assignments(self):
        self.write('tools/da-data.json', json.dumps({'server': 'da-data', 'schema_version': 1,
                                                     'operations': {'search_content': {'classification': 'read',
                                                                                       'basis': 'auto'}}}))
        self.tool.create_task(ROOT, self.project, 't1', 'Retrieve sources', activity='analysis',
                              skill='literature-review', role='analyst', acceptance='Bounded coverage',
                              tools=['da-data:search_content'])
        packet = self.tool.handoff(ROOT, self.project, 't1', 'Retrieve', ['research-brief.md'],
                                   model='current', outputs=['literature/review-v1.md'])
        self.tool.accept_assignment(ROOT, self.project, packet, self.receipt(packet, session_id='host:s1'))
        self.write(self.approval, 'Approved bounded channel; corrected arXiv title')
        result = self.tool.amend_binding(ROOT, self.project, 'grant', 'Corrected a false title in the approval')
        self.assertNotEqual(result['from_sha256'], result['to_sha256'])
        self.assertEqual([row['task_id'] for row in result['invalidated']], ['t1'])
        state = json.loads((self.project / 'research-state.json').read_text())
        event = state['history'][-1]
        self.assertEqual(event['action'], 'grant-rebound')
        self.assertEqual(event['from_sha256'], result['from_sha256'])

    def test_amend_refuses_to_rewrite_a_contract_field(self):
        with self.assertRaisesRegex(ValueError, 'grant, protocol, goal'):
            self.tool.amend_binding(ROOT, self.project, 'objective', 'Not a rebinding')
```

**Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_binding_repair -v`
Expected: FAIL with `AttributeError: module has no attribute 'amend_binding'`.

**Step 3: Write minimal implementation**

```python
AMEND_KINDS = ('grant', 'protocol', 'goal')


def invalidated_bindings(state):
    """Assignments whose frozen snapshot no longer matches the current contract.

    Rebinding is legal and often correct; what costs the project is discovering
    afterwards which work the change invalidated. This names them.
    """
    current = execution_contract(state)
    affected = []
    for task_id, task in state['tasks'].items():
        if task['status'] in ('completed', 'cancelled'):
            continue
        for assignment in task['assignments']:
            if assignment.get('execution_contract') != current:
                affected.append({'task_id': task_id, 'packet_id': assignment['packet_id'],
                                 'status': task['status']})
    return affected


def amend_binding(root, project, kind, reason):
    """Re-bind one gate artifact to the bytes now on disk, recording old and new.

    Correcting a known-false artifact is the right action; what made it damaging
    was that every gate depended on the old hash silently. The change is a core
    decision, and the assignments it invalidates are returned, never auto-repaired.
    """
    state, fingerprint = open_project(root, project)
    refuse(kind in AMEND_KINDS, 'Amendable bindings are grant, protocol, goal or tools')
    require(nonempty(reason), 'Re-binding needs an explicit core reason')
    if kind == 'grant':
        grant = state.get('grant')
        require(isinstance(grant, dict), 'No grant to re-bind; use authorize')
        reference = dict(grant['evidence'])
        record = evidence_record(project, reference['path'])
        grant['evidence'] = record
    elif kind == 'protocol':
        reference = state.get('protocol') or {}
        refuse(nonempty(reference.get('path')) and nonempty(reference.get('sha256')),
               'No frozen protocol to re-bind; use set-protocol',
               f'set-protocol --project {project} --path experiments/<id>/protocol.md --reason "..."')
        record = evidence_record(project, reference['path'])
        state['protocol'] = record
    else:
        reference = state.get('goal') or {}
        refuse(isinstance(reference, dict) and nonempty(reference.get('path')),
               'No selected goal dossier to re-bind; use set-goal',
               f'set-goal --project {project} --path hypotheses/goal-v1.md --reason "..."')
        record = evidence_record(project, reference['path'])
        state['goal'] = record
    affected = invalidated_bindings(state)
    state = save_decision(project, state, fingerprint,
                          {'action': f'{kind}-rebound', 'path': record['path'],
                           'from_sha256': reference.get('sha256'), 'to_sha256': record['sha256'],
                           'invalidated': affected, 'reason': reason.strip()})
    return {'kind': kind, 'path': record['path'], 'from_sha256': reference.get('sha256'),
            'to_sha256': record['sha256'], 'invalidated': affected, 'revision': state['revision'],
            'next': [f'task-status --project {project} --task {row["task_id"]} --status planned '
                     '--reason "reissue the packet"' for row in affected]}
```

Register: `('amend', 'Core only: rebind a gate artifact or a planned task channel', (('project', PROJECT), ('kind', {'required': True, 'choices': ('grant', 'protocol', 'goal', 'tools')}), ('task', {}), ('tool', {'action': 'append', 'default': []}), ('reason', TEXT)))`.

**Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.test_binding_repair -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add scripts/research.py tests/test_binding_repair.py
git commit -m "feat: amend rebinds a gate artifact and names the work it invalidates"
```

---

### Task 6: Channels that survive a registry rewrite

**Files:**
- Modify: `scripts/research.py:748-756` — extract `parse_tools`
- Modify: `scripts/research.py:127-138` — add `registry_operation`
- Modify: `scripts/research.py:1384-1436` (`ingest_catalog`) — report orphaned channels
- Modify: `scripts/research.py:1439-1460` (`confirm_semantics`) — allow a core-authored entry with no catalog
- Modify: `scripts/research.py:1463-1476` (`view_registry`) — add `used_by`
- Modify: `scripts/research.py` (`amend_binding`) — handle `kind == 'tools'`
- Modify: `tests/test_tool_semantics.py` — append tests

**Step 1: Write the failing test**

```python
    def test_ingest_reports_tasks_whose_frozen_channels_disappeared(self):
        self.ingest([{'name': 'search_content', 'description': 'Search indexed documents'},
                     {'name': 'fetch', 'description': 'Fetch a document'}])
        self.tool.create_task(ROOT, self.project, 't1', 'Retrieve sources', activity='analysis',
                              skill='literature-review', role='analyst', acceptance='Bounded coverage',
                              tools=['da-data:search_content', 'da-data:fetch'])
        registry = self.ingest([{'name': 'search_content', 'description': 'Search indexed documents'}],
                               name='tools/catalog-dump-2.json')
        self.assertEqual([row['operation'] for row in registry['orphaned_channels']], ['fetch'])
        self.assertEqual(registry['orphaned_channels'][0]['task_id'], 't1')

    def test_amend_tools_repairs_a_planned_task_after_a_registry_rewrite(self):
        self.ingest([{'name': 'search_content', 'description': 'Search indexed documents'}])
        self.tool.create_task(ROOT, self.project, 't1', 'Retrieve sources', activity='analysis',
                              skill='literature-review', role='analyst', acceptance='Bounded coverage',
                              tools=['da-data:fetch'])
        result = self.tool.amend_binding(ROOT, self.project, 'tools', 'Registry merged into retrieval',
                                         task_id='t1', tools=['da-data:search_content'])
        self.assertEqual(result['to'], [{'server': 'da-data', 'operation': 'search_content'}])
        state = json.loads((self.project / 'research-state.json').read_text())
        self.assertEqual(state['tasks']['t1']['tools'], [{'server': 'da-data', 'operation': 'search_content'}])

    def test_amend_tools_refuses_a_running_task(self):
        self.ingest([{'name': 'search_content', 'description': 'Search indexed documents'}])
        self.tool.create_task(ROOT, self.project, 't1', 'Retrieve sources', activity='analysis',
                              skill='literature-review', role='analyst', acceptance='Bounded coverage',
                              tools=['da-data:search_content'])
        packet = self.tool.handoff(ROOT, self.project, 't1', 'Retrieve', ['research-brief.md'],
                                  model='current', outputs=['literature/review-v1.md'])
        self.tool.accept_assignment(ROOT, self.project, packet, self.receipt(packet))
        with self.assertRaisesRegex(ValueError, 'planned'):
            self.tool.amend_binding(ROOT, self.project, 'tools', 'Too late', task_id='t1',
                                    tools=['da-data:search_content'])

    def test_confirmation_works_when_the_host_exports_no_catalog(self):
        # This host does not export an MCP catalog, so the core authors the entry.
        # The record must say so: a classification without server evidence is a
        # documented boundary, not an enforced one.
        registry = self.tool.confirm_semantics(ROOT, self.project, 'host-web', 'fetch', 'read',
                                               'Core-authored entry; the host exports no catalog')
        self.assertEqual(registry['operations']['fetch']['classification'], 'read')
        self.assertEqual(registry['provenance'], 'core-authored')
        self.assertIsNone(registry['catalog_sha256'])
```

**Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_tool_semantics -v`
Expected: FAIL — `ingest_catalog` returns no `orphaned_channels`; `amend_binding` has no `tools` kind; `confirm_semantics` rejects a missing registry.

**Step 3: Write minimal implementation**

```python
def registry_operation(project, server, operation):
    """The registry entry for one operation, or None when the host never exported it."""
    path = registry_path(project, server)
    if not path.is_file():
        return None
    entry = (read_json(path).get('operations') or {}).get(operation)
    return entry if isinstance(entry, dict) else None


def orphaned_channels(project, state):
    """Frozen channels no registry can satisfy: these tasks can never pass check-tool."""
    orphaned = []
    for task_id, task in state['tasks'].items():
        if task['status'] in ('completed', 'cancelled'):
            continue
        for channel in task.get('tools') or []:
            if registry_operation(project, channel['server'], channel['operation']) is None:
                orphaned.append({'task_id': task_id, 'status': task['status'],
                                 'server': channel['server'], 'operation': channel['operation']})
    return orphaned


def parse_tools(tools):
    """Structured server:operation channels; prose objectives never assign one."""
    assigned, seen = [], set()
    for tool in list(tools or []):
        require(isinstance(tool, str) and nonempty(tool), f'Invalid tool assignment: {tool}')
        server, separator, operation = tool.partition(':')
        refuse(separator and OPERATION_ID.fullmatch(server) and OPERATION_ID.fullmatch(operation),
               f'Invalid tool assignment (expected server:operation): {tool}')
        require((server, operation) not in seen, f'Duplicate tool assignment: {tool}')
        seen.add((server, operation))
        assigned.append({'server': server, 'operation': operation})
    return assigned
```

In `ingest_catalog`, after `write_registry(project, server, registry)`:

```python
    orphaned = orphaned_channels(project, state)
    save_decision(project, state, fingerprint, {'action': 'tool-catalog-ingested', 'server': server,
                                                'auto_classified': counts, 'orphaned_channels': orphaned, ...})
    # Returned, never persisted: the registry file describes the server, while the
    # collateral belongs to the decision that caused it.
    registry['orphaned_channels'] = orphaned
    registry['next'] = [f'amend --project {project} --kind tools --task {row["task_id"]} '
                        f'--tool <server:operation> --reason "..."' for row in orphaned]
    return registry
```

In `confirm_semantics`, replace the `require(path.is_file(), ...)` gate with creation of a core-authored registry:

```python
    path = registry_path(project, server)
    if path.is_file():
        registry = read_json(path)
    else:
        # A host that exports no catalog leaves one option: the core authors the
        # entry, and the missing catalog_sha256 records that the classification
        # has no server evidence behind it.
        registry = {'server': server, 'schema_version': 1, 'catalog_sha256': None,
                    'provenance': 'core-authored', 'operations': {}}
    entry = (registry.get('operations') or {}).get(operation)
    if not isinstance(entry, dict):
        entry = {'operation': operation, 'description': '', 'annotations': {}, 'input_args': [],
                 'classified_at': now, 'signature': None}
    entry.update(classification=semantics, basis='confirmed', confirmed_at=now, reason=reason.strip())
    registry.setdefault('operations', {})[operation] = entry
    write_registry(project, server, registry)
```

In `view_registry`, add per-operation `used_by`:

```python
        for name, table in servers.items():
            for operation in table.get('operations', {}):
                table['operations'][operation]['used_by'] = sorted(
                    task_id for task_id, task in state['tasks'].items()
                    if any(c['server'] == name and c['operation'] == operation
                           for c in task.get('tools') or []))
```

(load `state` via `project_state(root, project)` at the top of `view_registry`.)

Extend `amend_binding` with the `tools` kind:

```python
def amend_binding(root, project, kind, reason, task_id=None, tools=None):
    ...
    if kind == 'tools':
        require(isinstance(task_id, str) and task_id in state['tasks'], 'Unknown task ID')
        task = state['tasks'][task_id]
        refuse(task['status'] == 'planned',
               f'Frozen channels can be amended only while {task_id} is planned; a running or '
               'submitted task keeps the packet it was assigned',
               f'task-status --project {project} --task {task_id} --status planned --reason "reissue packet"')
        assigned = parse_tools(tools)
        for channel in assigned:
            refuse(registry_operation(project, channel['server'], channel['operation']) is not None,
                   f'No registry entry for {channel["server"]}:{channel["operation"]}; ingest a catalog '
                   'or confirm its semantics first',
                   f'tools --project {project} --server {channel["server"]} --operation '
                   f'{channel["operation"]} --confirm --semantics read|write --reason "..."')
        previous, reference, record = task['tools'], {'tools': task['tools']}, {'tools': assigned}
        task['tools'] = assigned
    ...
```

Adjust the shared tail so `from_sha256`/`to_sha256` are omitted for `kind == 'tools'` (use `from`/`to` channel lists) and the event action becomes `task-tools-amended`.

**Step 4: Run test to verify it passes**

Run: `python3 -m unittest discover -s tests`
Expected: PASS.

**Step 5: Commit**

```bash
git add scripts/research.py tests/test_tool_semantics.py
git commit -m "feat: channels survive a registry rewrite; core-authored registries are recorded"
```

---

### Task 7: Document the repair paths

**Files:**
- Modify: `references/operations.md` — command table rows for `next`, `bindings`, `amend`; new "Gate refusals and the repair" section
- Modify: `SKILL.md:138-154` — state controls note that `next` is the map and `amend` is the repair; `references/host-bridge.md:22-27` — "when a gate refuses, run `next`"
- Modify: `README.md:173-179` — limitations: state that a core-authored registry is recorded with `catalog_sha256: null` and is a documented boundary

**Step 1: Write the failing test**

Add to `tests/test_gate_guidance.py`:

```python
    def test_operations_documents_every_refusal_repair(self):
        text = (ROOT / 'references' / 'operations.md').read_text()
        for command in ('next', 'bindings', 'amend'):
            with self.subTest(command=command):
                self.assertIn(f'`{command}`', text)
        for refusal in ('Project is stopped', 'Tool access requires an active assignment',
                        'Task input', 'Unassigned run artifact', 'hash mismatch'):
            with self.subTest(refusal=refusal):
                self.assertIn(refusal, text)
```

**Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_gate_guidance -v`
Expected: FAIL.

**Step 3: Write the documentation**

Add to `references/operations.md`:

| Command | Purpose | Changes project state? |
|---|---|---|
| `next` | Read-only: the commands legal right now and the repair for the rest | No |
| `bindings` | Read-only: every hash binding and whether it still holds | No |
| `amend` | Rebind `grant`, `protocol`, `goal` or a planned task's channels, recording old and new | Yes, not phase |

```markdown
## Gate Refusals and the Repair

The gates are stateful and order sensitive, so a legal command issued in the wrong
state is refused. Every refusal ends with `Next:` and the command that clears it;
when a refusal has no `Next:`, it is a malformed argument, not a gate. Run
`next --project ... [--task <id>]` to see the legal moves without spending a round
trip discovering the state.

| Refusal | Cause | Repair |
|---|---|---|
| `Project is stopped; reactivate it before ...` | `project-status --to stopped` closed every decision | `project-status --to active` |
| `Tool access requires an active assignment` | no accepted packet for this task | `handoff`, then `accept` |
| `Tool request does not match the active packet` | a new packet superseded the one being used | reissue `handoff` and accept it |
| `Assignment grant changed` | the approval artifact was corrected after acceptance | `amend --kind grant`, then replan and reissue the packet |
| `Tool ... was not assigned to task` | channels are frozen at creation | `amend --kind tools --task <id>` while planned, else a new task |
| `Receipt packet hash mismatch` / `Packet is stale` | state or packet changed after `handoff` | reissue the packet |
| `hash mismatch` on completion | a versioned input changed | replan, or cancel and create a new task |
| `Unassigned run artifact` | the artifact is outside the assigned output scope | reuse the scope printed in the refusal |
| `Audit records belong under reviews/` | audits are read from `reviews/` | write it from `templates/evidence-audit.json` |

Hash bindings are global and silent: one edit can break the grant, the frozen
execution contract and a task's frozen inputs at once. Run `bindings` after any
edit to a bound artifact; `watch` reports `binding-drift` for the same reason.
Correcting a known-false artifact is correct behaviour — `amend` rebinds it and
names every assignment the change invalidated.

`findings.md`, `research-log.md` and `research-brief.md` are snapshot inputs: the
core rewrites them as a consequence of deciding, so their drift is recorded at
completion (`input_drift`) rather than refused. Versioned artifacts stay frozen.

A host that exports no MCP catalog leaves the core to author the registry entry
with `tools --confirm`; that entry carries `catalog_sha256: null` and
`provenance: core-authored`, so the audit trail records that the classification
has no server evidence behind it.
```

**Step 4: Run the full check**

Run: `python3 scripts/research.py validate && python3 -m unittest discover -s tests`
Expected: both pass. `validate` checks links in `SKILL.md`, `README.md` and `references/*.md`, so any new link must resolve.

**Step 5: Commit**

```bash
git add SKILL.md README.md references/operations.md references/host-bridge.md tests/test_gate_guidance.py
git commit -m "docs: document the repair for every gate refusal"
```

---

## Out of scope

- **Waiting on the human (77% of wall clock).** `next` and the `Waiting on:` board line make the wait legible; shortening it is a user-side decision, not a framework change.
- **Schema change.** Every addition reuses schema-8 fields; no migration is needed and `framework.json` is unchanged.
- **Enforcing tool calls.** `check-tool` remains a documented boundary on a cooperating host; this plan does not attempt to sandbox it.
- **`research-brief.md` as frozen evidence.** It stays bindable; its drift is now recorded rather than fatal, which removes the trap without churning fixtures.
