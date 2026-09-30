#!/usr/bin/env python3
"""Offline helpers for explicit core decisions; no research routing or dispatch."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
ID = re.compile(r'[a-z0-9]+(?:-[a-z0-9]+)*\Z')
MEASURES = ('primary_measure', 'baseline', 'validation_plan', 'uncertainty_plan')
OUTPUT_ROOTS = {'literature', 'hypotheses', 'experiments', 'src', 'data', 'paper', 'reports', 'reviews'}
PROJECT_STATUS = ('active', 'stopped')
ROLE_IDS = ('strategist', 'methodologist', 'experimenter', 'analyst', 'writer', 'reviewer', 'critic')
ADVISORY_PREFIX = 'NOTE: '
SKILL_BUDGET = 20000


def require(condition, message):
    if not condition:
        raise ValueError(message)


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def read_json(path):
    value = json.loads(Path(path).read_text(encoding='utf-8'))
    require(isinstance(value, dict), f'Expected JSON object: {path}')
    return value


def write_json(path, value):
    with Path(path).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def local_path(base, relative):
    require(nonempty(relative), 'A nonempty relative path is required')
    path = Path(relative)
    require(not path.is_absolute() and '..' not in path.parts, f'Invalid relative path: {relative}')
    base = Path(base).resolve()
    resolved = (base / path).resolve()
    require(resolved.is_relative_to(base), f'Path escapes root: {relative}')
    return resolved


def core_phases(root):
    text = (Path(root) / 'SKILL.md').read_text(encoding='utf-8')
    start, end = '<!-- phase-contract:start -->', '<!-- phase-contract:end -->'
    require(text.count(start) == text.count(end) == 1, 'Missing unique core phase contract')
    table = text.split(start, 1)[1].split(end, 1)[0]
    phases = {}
    for line in table.splitlines():
        if not line.startswith('|'):
            continue
        columns = [x.strip() for x in line.strip('|').split('|')]
        if columns[0] == 'Phase' or columns[0].startswith('-'):
            continue
        require(len(columns) == 4, 'Invalid core phase row')
        name, next_names, goal, exit_criteria = columns
        require(ID.fullmatch(name) and name not in phases, 'Invalid or duplicate phase')
        require(nonempty(goal) and nonempty(exit_criteria), 'Missing phase goal or exit criteria')
        phases[name] = {'next': [x.strip() for x in next_names.split(',')],
                        'goal': goal, 'exit_criteria': exit_criteria}
    require('scope' in phases and 'complete' in phases, 'Missing scope or complete phase')
    require(all(n in phases for p in phases.values() for n in p['next']), 'Unknown transition')
    return phases


def skill_entry(root, name):
    require(isinstance(name, str) and ID.fullmatch(name), 'Invalid skill ID')
    root = Path(root).resolve()
    directory = root / 'skills' / name
    require(not (root / 'skills').is_symlink() and not directory.is_symlink(), 'Symlinked skill directories are forbidden')
    path = local_path(root, f'skills/{name}/SKILL.md')
    require(path == directory / 'SKILL.md' and path.is_file(), f'Missing direct skill: {name}')
    text = path.read_text(encoding='utf-8')
    parts = text.split('---\n', 2)
    require(len(parts) == 3 and not parts[0], f'Missing frontmatter: {name}')
    fields = {}
    for line in parts[1].splitlines():
        key, separator, value = line.partition(':')
        require(separator and key in ('name', 'description') and key not in fields, f'Invalid skill metadata: {name}')
        fields[key] = value.strip()
    require(fields.get('name') == name and nonempty(fields.get('description')), f'Invalid skill identity: {name}')
    return {'name': name, 'description': fields['description'], 'path': str(path.relative_to(root)), 'sha256': digest(path)}


def discover_skills(root):
    base = Path(root).resolve() / 'skills'
    require(base.is_dir() and not base.is_symlink(), 'Missing flat skills directory')
    entries = {}
    for directory in sorted(base.iterdir()):
        if directory.name.startswith('.'):
            continue
        require(directory.is_dir() and not directory.is_symlink(), f'Invalid skill directory: {directory.name}')
        entries[directory.name] = skill_entry(root, directory.name)
    require(entries, 'No specialist skills found')
    return entries


def role_prompt(root, role_id):
    """Canonical standpoint prompt parsed from the single source in role guidance."""
    require(isinstance(role_id, str) and ID.fullmatch(role_id), 'Invalid role ID')
    text = (Path(root) / 'references' / 'role-guidance.md').read_text(encoding='utf-8')
    start, end = f'<!-- role-prompt:start:{role_id} -->', f'<!-- role-prompt:end:{role_id} -->'
    require(text.count(start) == text.count(end) == 1, f'Missing unique canonical role prompt: {role_id}')
    prompt = text.split(start, 1)[1].split(end, 1)[0].strip()
    require(nonempty(prompt), f'Empty canonical role prompt: {role_id}')
    return prompt


def role_contract(root, role_id, prompt=None):
    """A role is a standpoint prompt bound to a task, never a bare label."""
    require(isinstance(role_id, str) and ID.fullmatch(role_id), 'Explicit role ID is required')
    if prompt is None:
        prompt = role_prompt(root, role_id)
    require(nonempty(prompt), f'Role {role_id} requires an explicit prompt')
    prompt = prompt.strip()
    return {'id': role_id, 'prompt': prompt,
            'sha256': hashlib.sha256(prompt.encode('utf-8')).hexdigest()}


def check_links(doc, boundary):
    boundary = Path(boundary).resolve()
    require(doc.resolve().is_relative_to(boundary), 'Document escapes its package')
    for target in re.findall(r'\[[^\]]*\]\(([^\s)]+)\)', doc.read_text(encoding='utf-8')):
        if '://' in target or target.startswith(('#', 'mailto:')):
            continue
        target = target.split('#', 1)[0]
        resolved = (doc.parent / target).resolve()
        require(resolved.is_relative_to(boundary) and resolved.exists(), f'Broken or cross-package link: {doc}: {target}')


def budget_notes(root):
    """Advisory reading budget for progressive disclosure; never fails validation.

    Every returned note is prefixed with ADVISORY_PREFIX so callers can separate
    advice from hard validation errors without matching message text.
    """
    notes = []
    for path, limit in ((Path(root) / 'SKILL.md', 25000), (Path(root) / 'README.md', 12000)):
        size = path.stat().st_size if path.is_file() else 0
        if size > limit:
            notes.append(f'{ADVISORY_PREFIX}{path.name} is {size} bytes (soft budget {limit}); '
                         'move reference-like detail out of the entry point')
    for path in sorted((Path(root) / 'skills').glob('*/SKILL.md')):
        size = path.stat().st_size
        if size > SKILL_BUDGET:
            notes.append(f'{ADVISORY_PREFIX}skills/{path.parent.name}/SKILL.md is {size} bytes '
                         f'(soft budget {SKILL_BUDGET}); move reference-like detail into its references/ directory')
    return notes


def validate(root):
    root = Path(root).resolve()
    try:
        core_phases(root)
        for role_id in ROLE_IDS:
            role_prompt(root, role_id)
        entries = discover_skills(root)
        for name, entry in entries.items():
            path = root / entry['path']
            text = path.read_text(encoding='utf-8')
            for heading in ('Inputs', 'Method', 'Outputs', 'Checks', 'Boundary'):
                require(f'## {heading}' in text, f'Missing {heading}: {name}')
            require('Return to the core' in text and 'Do not dispatch' in text, f'Missing specialist boundary: {name}')
            check_links(path, path.parent)
        for path in [root / 'SKILL.md', root / 'README.md'] + list((root / 'references').glob('*.md')):
            check_links(path, root)
        state = read_json(root / 'templates/research-state.json')
        require(state['schema_version'] == 4 and state['mode'] == 'planning', 'Invalid planning defaults')
        log_template = (root / 'templates/research-log.md').read_text(encoding='utf-8')
        require(log_template.count('<!-- brief:start -->') == log_template.count('<!-- brief:end -->') == 1,
                'Research log template must contain exactly one current-brief marker block')
        manifest = read_json(root / 'provenance.json')
        for item in manifest['files'].values():
            path = local_path(root, item['path'])
            require(path.is_file() and digest(path) == item['sha256'], f'Adapted source changed: {item["path"]}')
    except (ValueError, OSError, KeyError, TypeError, AttributeError) as error:
        return [str(error)]
    return budget_notes(root)


def initialize(root, project, question):
    root, project = Path(root).resolve(), Path(project).absolute()
    require(nonempty(question), 'Research question cannot be blank')
    require(not project.exists() and not project.is_symlink(), 'Project destination already exists; refusing to overwrite')
    state = read_json(root / 'templates/research-state.json')
    require(state.get('schema_version') == 4 and state.get('mode') == 'planning', 'Unsupported state defaults')
    texts = {name: (root / 'templates' / name).read_text(encoding='utf-8') for name in ('findings.md', 'research-log.md')}
    state.update(question=question.strip(), created_at=datetime.now(timezone.utc).isoformat())
    project.mkdir(parents=True, exist_ok=False)
    write_json(project / 'research-state.json', state)
    for name, text in texts.items():
        with (project / name).open('x', encoding='utf-8') as stream:
            stream.write(text)
    with (project / 'research-brief.md').open('x', encoding='utf-8') as stream:
        stream.write(f'# Research Scope\n\n{question.strip()}\n\nPlanning only; no experimental results yet.\n\n'
                     '## To Be Defined\n\nQuestion boundaries, evidence, evaluation, resources, and authorization.\n')
    return state


def evidence_record(project, path):
    resolved = local_path(project, path)
    require(resolved.is_file() and resolved.stat().st_size > 0, f'Missing or empty evidence: {path}')
    return {'path': str(resolved.relative_to(Path(project).resolve())), 'sha256': digest(resolved)}


def verify_reference(project, reference, label):
    require(isinstance(reference, dict), f'Missing {label} reference')
    record = evidence_record(project, reference.get('path'))
    require(record['sha256'] == reference.get('sha256'), f'{label} hash mismatch')
    return record


def verify_audit(project, reference, label, required_paths, required_prefix):
    record = verify_reference(project, reference, label)
    audit = read_json(local_path(project, record['path']))
    require(audit.get('schema_version') == 1, f'Unknown {label} schema version')
    subjects = audit.get('subjects')
    require(isinstance(subjects, list) and subjects, f'{label} must bind reviewed subjects')
    checked = [verify_reference(project, subject, label + ' subject') for subject in subjects]
    paths = {subject['path'] for subject in checked}
    require(set(required_paths).issubset(paths), f'{label} lacks required subject versions')
    primary_paths = paths - set(required_paths) - {record['path']}
    require(any(path.startswith(required_prefix) for path in primary_paths), f'{label} lacks primary artifacts')
    return [record] + checked


def check_outputs(project, outputs, inputs):
    require(isinstance(outputs, list) and outputs, 'Explicit output paths are required')
    checked = []
    for value in outputs:
        path = local_path(project, value)
        relative = path.relative_to(project)
        require(relative.parts and relative.parts[0] in OUTPUT_ROOTS and len(relative.parts) > 1,
                f'Output must be a bounded task artifact, not global state or a root directory: {value}')
        require(not (project / value).is_symlink() and not path.exists(),
                f'Output already exists or is a symlink; use a new version: {value}')
        for evidence in inputs:
            source = local_path(project, evidence['path'])
            require(path != source and not source.is_relative_to(path), f'Output overlaps protected input: {value}')
        checked.append(str(relative) + ('/' if value.endswith('/') else ''))
    return checked


def session_request(mode='fresh', reason=None, resume_session_id=None, independent_review=False):
    require(isinstance(mode, str) and mode in ('fresh', 'reuse', 'current'), 'Invalid session mode')
    require(type(independent_review) is bool, 'independent_review must be a boolean')
    if reason is None and mode == 'fresh':
        reason = 'Fresh specialist session is the default for a new assignment.'
    require(nonempty(reason), 'An explicit session reason is required')
    if mode == 'reuse':
        require(nonempty(resume_session_id), 'Reuse requires a host-provided session ID')
    else:
        require(resume_session_id is None, 'A resume session ID is valid only for reuse')
    require(not independent_review or mode == 'fresh', 'Independent review requires a fresh session')
    return {'mode': mode, 'reason': reason.strip(), 'resume_session_id': resume_session_id,
            'independent_review': independent_review, 'status': 'requested',
            'bootstrap_policy': 'selected-skill-and-task-evidence-only',
            'unavailable_policy': 'return-to-core-no-silent-fallback'}


def project_state(root, project):
    path = Path(project).resolve() / 'research-state.json'
    require(not path.is_symlink(), 'Project state must not be a symlink')
    content = path.read_bytes()
    state = json.loads(content)
    require(isinstance(state, dict) and state.get('schema_version') == 4,
            'Unsupported state schema version; manual migration required')
    require(state.get('phase') in core_phases(root), 'Unknown project phase')
    require(state.get('status') in PROJECT_STATUS, 'Unknown project status')
    require(state.get('mode') in ('planning', 'research'), 'Unknown mode')
    require(type(state.get('revision')) is int and state['revision'] >= 0, 'Invalid revision')
    require(isinstance(state.get('tasks'), dict) and isinstance(state.get('history'), list), 'Missing task records')
    require(isinstance(state.get('blockers'), list), 'Invalid project blockers')
    running = [name for name, task in state['tasks'].items() if task['status'] == 'running']
    require(running == ([] if state.get('active_task') is None else [state['active_task']]),
            'Active task does not match running task records')
    return state, hashlib.sha256(content).hexdigest()


def save_decision(project, state, expected_hash, event):
    path = Path(project).resolve() / 'research-state.json'
    require(not path.is_symlink() and digest(path) == expected_hash, 'State changed; retry the core decision')
    state['revision'] += 1
    state['history'].append(dict(event, revision=state['revision'], at=datetime.now(timezone.utc).isoformat()))
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent, delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(state, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
        require(not path.is_symlink() and digest(path) == expected_hash, 'State changed; retry the core decision')
        os.replace(temporary, path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()
    return state


def create_task(root, project, task_id, objective, *, activity, skill, role, acceptance, independent_review=False,
                role_prompt_text=None):
    state, fingerprint = project_state(root, project)
    require(state['status'] == 'active' and state['phase'] != 'complete', 'Project is not open for new tasks')
    require(not state['blockers'], 'Resolve project blockers before creating new tasks')
    require(isinstance(task_id, str) and ID.fullmatch(task_id), 'Invalid task ID; use lowercase letters, digits and hyphens')
    require(task_id not in state['tasks'], 'Task ID already exists; never overwrite its contract')
    require(nonempty(objective) and nonempty(acceptance), 'Objective and acceptance criteria are required')
    require(isinstance(activity, str) and activity in ('analysis', 'experiment', 'conclusions'), 'Unknown task activity')
    require(type(independent_review) is bool, 'independent_review must be a boolean')
    selected_role = role_contract(root, role, role_prompt_text)
    skill_entry(root, skill)
    state['tasks'][task_id] = {'task_id': task_id, 'created_phase': state['phase'], 'objective': objective.strip(),
                              'activity': activity, 'skill': skill, 'role': selected_role,
                              'acceptance_criteria': acceptance.strip(), 'independent_review': independent_review,
                              'status': 'planned', 'assignments': [], 'submission': []}
    save_decision(project, state, fingerprint, {'action': 'task-created', 'task_id': task_id,
                                                'activity': activity, 'skill': skill,
                                                'role': selected_role['id'], 'reason': objective.strip()})
    return state['tasks'][task_id]


def activity_evidence(project, state, activity, records, final=False):
    require(activity in ('analysis', 'experiment', 'conclusions'), 'Unknown task activity')
    if activity == 'experiment':
        require(state['mode'] == 'research',
                'Execution requires research mode set through an explicit core decision')
        require(isinstance(state.get('evaluation'), dict), 'Evaluation plan missing')
        for field in MEASURES:
            require(nonempty(state['evaluation'].get(field)), f'Evaluation {field} is required')
        records.append(verify_reference(project, state.get('protocol'), 'Protocol'))
    elif activity == 'conclusions':
        require(state.get('evidence_review', {}).get('status') == 'verified', 'Verified findings required')
        protocol = verify_reference(project, state.get('protocol'), 'Protocol')
        audited = verify_audit(project, state.get('evidence_review'), 'Evidence review',
                               ['findings.md', protocol['path']], ('experiments/', 'data/'))
        if final:
            require(state.get('review', {}).get('status') == 'passed', 'Passed review required')
            audited += verify_audit(project, state.get('review'), 'Final review', ['findings.md'], 'paper/')
        require({x['path'] for x in records}.issubset({x['path'] for x in audited}), 'Unreviewed evidence in conclusions request')
        records.extend(audited)
    return list({x['path']: x for x in records}.values())


def handoff(root, project, task_id, summary, evidence, *, model, outputs,
            session_mode='fresh', session_reason=None, resume_session_id=None):
    root, project = Path(root).resolve(), Path(project).resolve()
    state, fingerprint = project_state(root, project)
    require(state['status'] == 'active' and state['phase'] != 'complete', 'Project is not active')
    require(state['active_task'] is None, 'A task is already running; stop its executor before reassignment')
    require(not state['blockers'], 'Resolve blockers before handoff')
    require(isinstance(task_id, str) and task_id in state['tasks'], 'Unknown task ID')
    task = state['tasks'][task_id]
    require(task['status'] == 'planned', 'Task must be planned before assignment')
    require(nonempty(summary) and nonempty(model), 'Assignment rationale and model are required')
    require(isinstance(evidence, list) and evidence, 'At least one evidence file is required')
    session = session_request(session_mode, session_reason, resume_session_id, task['independent_review'])
    selected = skill_entry(root, task['skill'])
    records = activity_evidence(project, state, task['activity'], [evidence_record(project, p) for p in evidence])
    protected = list(records)
    for field in ('protocol', 'evidence_review', 'review'):
        reference = state.get(field)
        if isinstance(reference, dict) and nonempty(reference.get('path')):
            protected.append({'path': reference['path']})
    return {'schema_version': 4, 'packet_id': str(uuid4()), 'task_id': task_id,
            'created_at': datetime.now(timezone.utc).isoformat(), 'source_revision': state['revision'],
            'state_sha256': fingerprint, 'core_sha256': digest(root / 'SKILL.md'), 'project_phase': state['phase'],
            'objective': task['objective'], 'activity': task['activity'], 'skill': selected,
            'target_role': task['role'], 'requested_model': model, 'session': session, 'summary': summary.strip(),
            'acceptance_criteria': task['acceptance_criteria'], 'evidence': records,
            'allowed_outputs': check_outputs(project, outputs, protected),
            'dispatch_status': 'not_dispatched', 'receipt_required': True,
            'framework_root': str(root), 'project_root': str(project),
            'boundary': 'One skill assignment only. Return to the core; no delegation, session creation, or global state edits.'}


def accept_assignment(root, project, packet, receipt):
    state, fingerprint = project_state(root, project)
    require(packet.get('schema_version') == 4 and receipt.get('schema_version') == 4, 'Unknown packet or receipt schema')
    packet_hash = hashlib.sha256(json.dumps(packet, sort_keys=True, ensure_ascii=False,
                                           separators=(',', ':'), allow_nan=False).encode('utf-8')).hexdigest()
    require(receipt.get('packet_sha256') == packet_hash, 'Receipt packet hash mismatch')
    require(packet.get('source_revision') == state['revision'] and packet.get('state_sha256') == fingerprint,
            'Packet is stale: state revision or hash changed')
    session = packet['session']
    for record in packet['evidence']:
        verify_reference(project, record, 'Assignment input')
    expected = handoff(root, project, packet['task_id'], packet['summary'], [r['path'] for r in packet['evidence']],
                       model=packet['requested_model'], outputs=packet['allowed_outputs'], session_mode=session['mode'],
                       session_reason=session['reason'], resume_session_id=session['resume_session_id'])
    for key, value in expected.items():
        if key not in ('packet_id', 'created_at'):
            require(packet.get(key) == value, f'Packet contract changed: {key}')
    for key in ('packet_id', 'task_id', 'source_revision'):
        require(receipt.get(key) == packet[key], f'Receipt mismatch: {key}')
    require(nonempty(packet.get('packet_id')), 'Missing packet ID')
    require(receipt.get('accepted') is True, 'Executor has not accepted assignment')
    require(nonempty(receipt.get('accepted_at')), 'Receipt acceptance timestamp is required')
    for key in ('state_hash_checked', 'core_hash_checked', 'skill_hash_checked', 'evidence_hashes_checked'):
        require(receipt.get(key) is True, f'Receipt check missing: {key}')
    require(receipt.get('actual_role') == packet['target_role']['id'], 'Actual role mismatch')
    require(nonempty(receipt.get('actual_model')), 'Actual model is required')
    require(packet['requested_model'] == 'current' or receipt['actual_model'] == packet['requested_model'], 'Actual model mismatch')
    require(receipt.get('actual_session_mode') == session['mode'], 'Actual session mode mismatch')
    actual_id = receipt.get('actual_session_id')
    require(nonempty(actual_id) or (actual_id is None and nonempty(receipt.get('session_notes'))), 'Missing host session identity or limitation')
    require(type(receipt.get('session_isolation_verified')) is bool, 'Session isolation check is required')
    history = [a for t in state['tasks'].values() for a in t['assignments']]
    require(all(a['packet']['packet_id'] != packet['packet_id'] for a in history), 'Packet already accepted')
    if session['mode'] == 'fresh':
        require(receipt['session_isolation_verified'], 'Fresh session isolation must be verified by the core')
        require(actual_id is None or all(a['receipt']['actual_session_id'] != actual_id for a in history), 'Fresh session reuses a recorded ID')
    elif session['mode'] == 'current':
        require(not receipt['session_isolation_verified'], 'Current session cannot claim fresh isolation')
    else:
        require(not receipt['session_isolation_verified'], 'A reused session cannot claim fresh isolation')
        require(actual_id == session['resume_session_id'], 'Resume session identity mismatch')
        previous = [a for a in history if a['receipt']['actual_session_id'] == actual_id]
        require(previous, 'No accepted assignment records this host session')
        last = max(previous, key=lambda assignment: assignment['accepted_revision'])
        require(last['packet']['skill']['name'] == packet['skill']['name']
                and last['receipt']['actual_role'] == receipt['actual_role']
                and last['packet']['target_role']['sha256'] == packet['target_role']['sha256']
                and last['receipt']['actual_model'] == receipt['actual_model'], 'Resumed session has incompatible skill, role or model')
    task = state['tasks'][packet['task_id']]
    task['assignments'].append({'packet': packet, 'receipt': receipt, 'accepted_revision': state['revision'] + 1})
    task['status'] = 'running'
    state['active_task'] = packet['task_id']
    return save_decision(project, state, fingerprint, {'action': 'assignment-accepted', 'task_id': packet['task_id'],
                                                      'packet_id': packet['packet_id'], 'reason': packet['summary']})


def update_task(root, project, task_id, status, reason, evidence, *, executor_stopped=False):
    state, fingerprint = project_state(root, project)
    require(isinstance(task_id, str) and task_id in state['tasks'], 'Unknown task ID')
    require(nonempty(reason), 'Core decision reason is required')
    task = state['tasks'][task_id]
    transitions = {'planned': ('cancelled',), 'running': ('blocked', 'submitted', 'cancelled'),
                   'blocked': ('planned', 'cancelled'), 'submitted': ('planned', 'completed', 'cancelled')}
    require(status in transitions.get(task['status'], ()), 'Illegal task status transition')
    if task['status'] == 'running':
        require(executor_stopped is True, 'Confirm executor stopped and reconcile in-flight jobs first')
        state['active_task'] = None
    require(isinstance(evidence, list), 'Evidence must be a list')
    records = [evidence_record(project, path) for path in evidence]
    if status == 'submitted':
        require(records, 'Submission requires output evidence')
        allowed = task['assignments'][-1]['packet']['allowed_outputs']
        for record in records:
            require(any(record['path'] == scope or (scope.endswith('/') and record['path'].startswith(scope))
                        for scope in allowed), f'Unassigned submission artifact: {record["path"]}')
        task['submission'] = records
    if status == 'completed':
        require(not state['blockers'], 'Resolve project blockers before accepting task output')
        require(task['submission'], 'No submitted artifacts to accept')
        for record in task['submission']:
            verify_reference(project, record, 'Submitted artifact')
        packet = task['assignments'][-1]['packet']
        for record in packet['evidence']:
            verify_reference(project, record, 'Task input')
        activity_evidence(project, state, task['activity'], list(packet['evidence']))
    task['status'] = status
    return save_decision(project, state, fingerprint, {'action': 'task-' + status, 'task_id': task_id,
                                                      'reason': reason.strip(), 'evidence': records})


def transition_phase(root, project, target, reason, evidence):
    state, fingerprint = project_state(root, project)
    phases = core_phases(root)
    require(state['status'] == 'active' and state['active_task'] is None, 'Stop the active executor before changing phase')
    require(not state['blockers'], 'Resolve project blockers before changing phase')
    require(nonempty(reason) and isinstance(evidence, list) and evidence, 'Phase decision needs a rationale and evidence')
    require(target in phases[state['phase']]['next'], 'Illegal phase transition')
    records = [evidence_record(project, p) for p in evidence]
    if target == 'complete':
        require(all(t['status'] in ('completed', 'cancelled') for t in state['tasks'].values()), 'Resolve or cancel open tasks before completion')
        records = activity_evidence(project, state, 'conclusions', records, final=True)
    previous = state['phase']
    state['phase'] = target
    return save_decision(project, state, fingerprint, {'action': 'phase-changed', 'from_phase': previous,
                                                      'to_phase': target, 'reason': reason.strip(), 'evidence': records})


def open_project(root, project):
    """Guard for core management commands; a stopped project is terminal.

    Mode, evaluation, protocol, audit and blocker decisions require an active
    project. Only `project-status` can move a stopped project back to active.
    """
    state, fingerprint = project_state(root, project)
    require(state['status'] == 'active', 'Project is stopped; reactivate it before recording further decisions')
    return state, fingerprint


def authorize(root, project, *, mode, reason, evidence=()):
    state, fingerprint = open_project(root, project)
    require(mode in ('planning', 'research'), 'Unknown mode')
    require(nonempty(reason), 'Research mode decisions need an explicit core reason')
    records = [evidence_record(project, path) for path in evidence]
    require(mode != 'research' or records, 'Granting research mode requires cited authorization evidence')
    state['mode'] = mode
    return save_decision(project, state, fingerprint, {'action': 'mode-set', 'mode': state['mode'],
                                                      'reason': reason.strip(), 'evidence': records})


def set_evaluation(root, project, *, primary_measure, baseline, validation_plan, uncertainty_plan, reason):
    state, fingerprint = open_project(root, project)
    require(nonempty(reason), 'Evaluation plan needs an explicit core reason')
    values = {'primary_measure': primary_measure, 'baseline': baseline,
              'validation_plan': validation_plan, 'uncertainty_plan': uncertainty_plan}
    for field in MEASURES:
        require(nonempty(values[field]), f'Evaluation {field} is required')
    state['evaluation'] = {field: values[field].strip() for field in MEASURES}
    return save_decision(project, state, fingerprint, {'action': 'evaluation-set',
                                                      'evaluation': dict(state['evaluation']),
                                                      'reason': reason.strip()})


def set_protocol(root, project, *, path, reason):
    state, fingerprint = open_project(root, project)
    require(nonempty(reason), 'Protocol freeze needs an explicit core reason')
    resolved = local_path(project, path)
    relative = resolved.relative_to(Path(project).resolve())
    require(not resolved.is_symlink() and resolved.is_file() and resolved.stat().st_size > 0,
            f'Missing or empty protocol: {path}')
    require(relative.parts[0] == 'experiments', 'Protocol must be a frozen artifact under experiments/')
    state['protocol'] = {'path': str(relative), 'sha256': digest(resolved)}
    return save_decision(project, state, fingerprint, {'action': 'protocol-frozen',
                                                      'protocol': dict(state['protocol']),
                                                      'reason': reason.strip()})


def set_audit(root, project, *, kind, path, status, reason):
    state, fingerprint = open_project(root, project)
    require(kind in ('evidence', 'final'), 'Audit kind must be evidence or final')
    expected = ('verified', 'unverified') if kind == 'evidence' else ('passed', 'pending')
    require(status in expected, f'Unknown {kind} audit status: {status}')
    require(nonempty(reason), 'Audit decision needs an explicit core reason')
    resolved = local_path(project, path)
    relative = resolved.relative_to(Path(project).resolve())
    require(not resolved.is_symlink() and resolved.is_file() and resolved.stat().st_size > 0,
            f'Missing or empty audit record: {path}')
    require(relative.parts[0] == 'reviews', 'Audit records belong under reviews/')
    reference = {'path': str(relative), 'sha256': digest(resolved)}
    label = 'Evidence review' if kind == 'evidence' else 'Final review'
    if status in ('verified', 'passed'):
        if kind == 'evidence':
            protocol = verify_reference(project, state.get('protocol'), 'Protocol')
            verify_audit(project, reference, label, ['findings.md', protocol['path']], ('experiments/', 'data/'))
        else:
            verify_audit(project, reference, label, ['findings.md'], 'paper/')
    field = 'evidence_review' if kind == 'evidence' else 'review'
    state[field] = {'status': status, 'path': str(relative), 'sha256': reference['sha256']}
    return save_decision(project, state, fingerprint, {'action': f'{field}-set', field: dict(state[field]),
                                                      'reason': reason.strip()})


def update_blockers(root, project, *, add=None, resolve=None, reason):
    state, fingerprint = open_project(root, project)
    require(nonempty(reason), 'Blocker decision needs an explicit core reason')
    require(bool(add) or bool(resolve), 'Declare a blocker to add or resolve')
    if add is not None:
        require(nonempty(add), 'Blocker text cannot be blank')
        require(add not in state['blockers'], 'Blocker is already recorded')
        state['blockers'].append(add)
    if resolve is not None:
        require(resolve in state['blockers'], 'Unknown blocker')
        state['blockers'].remove(resolve)
    return save_decision(project, state, fingerprint, {'action': 'blockers-changed', 'add': add, 'resolve': resolve,
                                                      'blockers': list(state['blockers']), 'reason': reason.strip()})


def set_project_status(root, project, *, status, reason):
    state, fingerprint = project_state(root, project)
    require(status in PROJECT_STATUS, 'Unknown project status')
    require(nonempty(reason), 'Project status decision needs an explicit core reason')
    require(status != state['status'], f'Project already has status {status}; no decision to record')
    if status != 'active':
        require(state['active_task'] is None, 'Stop the active executor before pausing or stopping the project')
    previous = state['status']
    state['status'] = status
    return save_decision(project, state, fingerprint, {'action': 'project-status-changed', 'from_status': previous,
                                                      'to_status': status, 'reason': reason.strip()})


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('validate', help='Validate core contract, flat skills and provenance')
    commands.add_parser('skills', help='List skill entries directly from disk')
    init = commands.add_parser('init', help='Create four planning documents')
    init.add_argument('--project', required=True, type=Path)
    init.add_argument('--question', required=True)
    task = commands.add_parser('task', help='Core only: register a stable task without changing phase')
    for name in ('task', 'objective', 'activity', 'skill', 'role', 'acceptance'):
        task.add_argument('--' + name, required=True)
    task.add_argument('--project', required=True, type=Path)
    task.add_argument('--independent-review', action='store_true')
    task.add_argument('--role-prompt', help='Explicit standpoint prompt; required for role ids without a canonical template')
    transfer = commands.add_parser('handoff', help='Print one task assignment; no state change or dispatch')
    transfer.add_argument('--project', required=True, type=Path)
    for name in ('task', 'summary', 'model'):
        transfer.add_argument('--' + name, required=True)
    transfer.add_argument('--evidence', nargs='+', required=True)
    transfer.add_argument('--outputs', nargs='+', required=True)
    transfer.add_argument('--session', choices=('fresh', 'reuse', 'current'), default='fresh')
    transfer.add_argument('--session-reason')
    transfer.add_argument('--resume-session')
    accept = commands.add_parser('accept', help='Core only: validate and record an actual executor receipt')
    accept.add_argument('--project', required=True, type=Path)
    accept.add_argument('--packet', required=True, help='Project-relative saved packet path')
    accept.add_argument('--receipt', required=True, help='Project-relative saved receipt path')
    update = commands.add_parser('task-status', help='Core only: record submission, acceptance, blocking or cancellation')
    update.add_argument('--project', required=True, type=Path)
    for name in ('task', 'status', 'reason'):
        update.add_argument('--' + name, required=True)
    update.add_argument('--evidence', nargs='*', default=[])
    update.add_argument('--executor-stopped', action='store_true')
    phase = commands.add_parser('phase', help='Core only: explicitly change project phase')
    phase.add_argument('--project', required=True, type=Path)
    phase.add_argument('--to', required=True)
    phase.add_argument('--reason', required=True)
    phase.add_argument('--evidence', nargs='+', required=True)
    grant = commands.add_parser('authorize', help='Core only: set research mode')
    grant.add_argument('--project', required=True, type=Path)
    grant.add_argument('--mode', required=True, choices=('planning', 'research'))
    grant.add_argument('--reason', required=True)
    grant.add_argument('--evidence', nargs='*', default=[])
    evaluation = commands.add_parser('set-evaluation', help='Core only: record the four evaluation fields')
    evaluation.add_argument('--project', required=True, type=Path)
    for name in MEASURES:
        evaluation.add_argument('--' + name.replace('_', '-'), required=True)
    evaluation.add_argument('--reason', required=True)
    protocol = commands.add_parser('set-protocol', help='Core only: freeze the protocol under experiments/')
    protocol.add_argument('--project', required=True, type=Path)
    protocol.add_argument('--path', required=True)
    protocol.add_argument('--reason', required=True)
    audit = commands.add_parser('set-audit', help='Core only: record an evidence or final review audit')
    audit.add_argument('--project', required=True, type=Path)
    audit.add_argument('--kind', required=True, choices=('evidence', 'final'))
    audit.add_argument('--path', required=True)
    audit.add_argument('--status', required=True, choices=('verified', 'unverified', 'passed', 'pending'))
    audit.add_argument('--reason', required=True)
    blockers = commands.add_parser('blockers', help='Core only: add or resolve a project blocker')
    blockers.add_argument('--project', required=True, type=Path)
    blockers.add_argument('--add')
    blockers.add_argument('--resolve')
    blockers.add_argument('--reason', required=True)
    project_status = commands.add_parser('project-status', help='Core only: activate, pause or stop the project')
    project_status.add_argument('--project', required=True, type=Path)
    project_status.add_argument('--to', required=True, choices=PROJECT_STATUS)
    project_status.add_argument('--reason', required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == 'validate':
            errors = validate(ROOT)
            failures = [x for x in errors if not x.startswith(ADVISORY_PREFIX)]
            require(not failures, '; '.join(failures))
            print('OK: core contract, flat specialist skills, provenance')
            for note in errors:
                if note.startswith(ADVISORY_PREFIX):
                    print(note)
            return 0
        if args.command == 'skills':
            result = discover_skills(ROOT)
        elif args.command == 'init':
            result = initialize(ROOT, args.project, args.question)
        elif args.command == 'task':
            result = create_task(ROOT, args.project, args.task, args.objective, activity=args.activity,
                                 skill=args.skill, role=args.role, acceptance=args.acceptance,
                                 independent_review=args.independent_review,
                                 role_prompt_text=args.role_prompt)
        elif args.command == 'handoff':
            result = handoff(ROOT, args.project, args.task, args.summary, args.evidence,
                             model=args.model, outputs=args.outputs, session_mode=args.session,
                             session_reason=args.session_reason, resume_session_id=args.resume_session)
        elif args.command == 'accept':
            result = accept_assignment(ROOT, args.project, read_json(local_path(args.project, args.packet)),
                                       read_json(local_path(args.project, args.receipt)))
        elif args.command == 'task-status':
            result = update_task(ROOT, args.project, args.task, args.status, args.reason, args.evidence,
                                 executor_stopped=args.executor_stopped)
        elif args.command == 'authorize':
            result = authorize(ROOT, args.project, mode=args.mode, reason=args.reason, evidence=args.evidence)
        elif args.command == 'set-evaluation':
            result = set_evaluation(ROOT, args.project, **{field: getattr(args, field) for field in MEASURES},
                                    reason=args.reason)
        elif args.command == 'set-protocol':
            result = set_protocol(ROOT, args.project, path=args.path, reason=args.reason)
        elif args.command == 'set-audit':
            result = set_audit(ROOT, args.project, kind=args.kind, path=args.path, status=args.status,
                               reason=args.reason)
        elif args.command == 'blockers':
            result = update_blockers(ROOT, args.project, add=args.add, resolve=args.resolve, reason=args.reason)
        elif args.command == 'project-status':
            result = set_project_status(ROOT, args.project, status=args.to, reason=args.reason)
        else:
            result = transition_phase(ROOT, args.project, args.to, args.reason, args.evidence)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, OSError, KeyError, TypeError, AttributeError) as error:
        print(f'ERROR: {error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
