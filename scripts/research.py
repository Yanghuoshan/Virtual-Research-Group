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
GOAL_FIELDS = ('Question:', 'Value:', 'Boundary:', 'Alternatives:', 'Evidence:', 'Falsifier:',
               'Success:', 'Feasibility:', 'Resources:', 'Stop:', 'Unknown:')
ACTIVITIES = ('analysis', 'experiment', 'conclusions')
OUTPUT_ROOTS = {'literature', 'hypotheses', 'experiments', 'src', 'data', 'paper', 'reports', 'reviews'}
PROJECT_STATUS = ('active', 'stopped')
ROLE_IDS = ('strategist', 'methodologist', 'experimenter', 'analyst', 'writer', 'reviewer', 'critic')
ADVISORY_PREFIX = 'NOTE: '
ASSIGNMENT_BOUNDARY = 'One skill assignment only. Return to the core; no delegation, session creation, or global state edits.'
SKILL_BUDGET = 20000
ENTRY_BUDGETS = (('SKILL.md', 40000), ('README.md', 16000))
PRIMARY_PREFIXES = ('experiments/', 'data/', 'literature/', 'reports/')
FINAL_PREFIXES = ('paper/', 'reports/')
ISO_TIMESTAMP = re.compile(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})\Z')
# Tool semantics come from the server's own catalog declarations (annotations,
# description, argument names), never from the operation name alone at call time.
OPERATION_ID = re.compile(r'[a-z0-9]+(?:[-_][a-z0-9]+)*\Z')
WRITE_WORDS = re.compile(r'\b(create|insert|update|delete|remove|drop|write|send|submit|execute|'
                         r'deploy|patch|modify|alter|truncate|replace|rename|append|upload|publish|'
                         r'cancel|stop|install|grant|revoke|reset|clear|purge)\b')
READ_WORDS = re.compile(r'\b(read|get|search|fetch|list|query|select|lookup|describe|analyse|analyze|'
                        r'inspect|check|preview|view|find|obtain|stat|head|diff|show)\b')
FREE_TEXT_ARGS = {'sql', 'query', 'command', 'commands', 'cmd', 'body', 'script', 'code',
                  'statement', 'payload', 'request', 'prompt', 'expression'}
SEMANTICS = ('read', 'write', 'unknown')
COMPLETION_VERDICTS = ('met', 'partially-met')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def iso_timestamp(value, label):
    require(isinstance(value, str) and ISO_TIMESTAMP.fullmatch(value), f'{label} must be an ISO 8601 timestamp')
    return value


def packet_digest(packet):
    return hashlib.sha256(json.dumps(packet, sort_keys=True, ensure_ascii=False,
                                      separators=(',', ':'), allow_nan=False).encode('utf-8')).hexdigest()


def preflight_token(task_id, packet_id, server, operation, scope, classification):
    """Deterministic digest binding one checked external call request.

    The host must carry the token check-tool returned and record it with
    tool-call, so a logged call can be reconciled against the exact facts that
    were checked. It binds the checked facts to each other; it cannot prove the
    host's honesty, only make the audit trail consistent.
    """
    payload = json.dumps({'task_id': task_id, 'packet_id': packet_id, 'server': server,
                          'operation': operation, 'scope': scope, 'classification': classification},
                         sort_keys=True, ensure_ascii=False, separators=(',', ':'),
                         allow_nan=False).encode('utf-8')
    return hashlib.sha256(b'research-preflight:' + payload).hexdigest()


def classify_operation(name, description, annotations, args):
    """Classify an operation from the server's own catalog evidence.

    Write signals dominate (fail closed), free-text arguments defer to the user,
    and a read classification needs positive evidence: an explicit readOnlyHint
    or a read verb in the catalog, with no write signal and no free-text argument.
    """
    # Snake and kebab case must be tokenized first: '_' and '-' are word characters,
    # so \bcreate\b would otherwise never match inside create_query_job.
    text = f'{name} {description}'.lower().replace('_', ' ').replace('-', ' ')
    if annotations.get('destructiveHint') is True or WRITE_WORDS.search(text):
        return 'write'
    if FREE_TEXT_ARGS.intersection(args):
        return 'unknown'
    if annotations.get('readOnlyHint') is True or READ_WORDS.search(text):
        return 'read'
    return 'unknown'


def registry_path(project, server):
    require(isinstance(server, str) and OPERATION_ID.fullmatch(server), f'Invalid server ID: {server}')
    return Path(project).resolve() / 'tools' / f'{server}.json'


def write_registry(project, server, registry):
    """Atomically replace one server's tool registry; the core owns this file."""
    path = registry_path(project, server)
    require(not path.is_symlink(), f'Tool registry must not be a symlink: tools/{server}.json')
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent, delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(registry, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
        os.replace(temporary, path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def operation_semantics(project, server, operation):
    """The recorded classification of one operation; uncataloged means unknown."""
    path = registry_path(project, server)
    if not path.is_file():
        return {'server': server, 'operation': operation, 'classification': 'unknown',
                'basis': 'not-cataloged'}
    registry = read_json(path)
    entry = (registry.get('operations') or {}).get(operation)
    require(isinstance(entry, dict) and entry.get('classification') in SEMANTICS,
            f'Invalid registry entry: {server}/{operation}')
    return {'server': server, 'operation': operation, 'classification': entry['classification'],
            'basis': entry.get('basis', 'auto')}


def planning_semantics(project, services, operation):
    """Classification a planning grant may rely on: read in a granted registry, never write."""
    readings = [operation_semantics(project, service, operation) for service in services]
    if any(reading['classification'] == 'write' for reading in readings):
        return {'classification': 'write', 'basis': 'registry'}
    if any(reading['classification'] == 'read' for reading in readings):
        return {'classification': 'read', 'basis': 'registry'}
    return {'classification': 'unknown', 'basis': 'not-cataloged'}


def freeze_active(state):
    """A freeze-all blocker is an explicit emergency stop for all task work."""
    return any(blocker.get('freeze_all') for blocker in state['blockers'])


def open_blocker_ids(state):
    return [blocker['blocker_id'] for blocker in state['blockers']]


def blocker_summary(state):
    """One readable line per open blocker, for error messages and boards."""
    return '; '.join(f"{blocker['blocker_id']} - {blocker['text']}" for blocker in state['blockers']) or 'none'


def task_may_proceed(state, resolves):
    """With open blockers, only a task resolving an open blocker may proceed."""
    if not state['blockers']:
        return True
    if freeze_active(state):
        return False
    return any(blocker_id in open_blocker_ids(state) for blocker_id in (resolves or []))


def gate_task(state, resolves, label):
    """Return the reason a task may not proceed right now, or None when it may."""
    if task_may_proceed(state, resolves):
        return None
    blockers = blocker_summary(state)
    if freeze_active(state):
        return f'Project is frozen by a freeze-all blocker ({blockers}); resolve or edit it before any task work'
    if resolves:
        return (f'{label} declares to resolve {", ".join(resolves)}, all now closed, while these blockers '
                f'are open ({blockers}); cancel or replan the task, or resolve them explicitly')
    return f'Open blockers halt unrelated work ({blockers}); declare --resolves naming one of them'


def task_resolves_open(state, resolves):
    """The open blockers a task declared it would resolve."""
    declared = set(resolves or [])
    return [blocker for blocker in state['blockers'] if blocker['blocker_id'] in declared]


def find_open_blocker(state, blocker_id):
    require(isinstance(blocker_id, str) and ID.fullmatch(blocker_id), f'Invalid blocker ID: {blocker_id}')
    for blocker in state['blockers']:
        if blocker['blocker_id'] == blocker_id:
            return blocker
    raise ValueError(f'Unknown blocker (or already resolved): {blocker_id}; open: {blocker_summary(state)}')


def close_blocker(state, blocker_id, resolved_by):
    """Move an open blocker into history, preserving its identity and age."""
    blocker = find_open_blocker(state, blocker_id)
    state['blockers'].remove(blocker)
    entry = dict(blocker)
    entry.update(resolved_at=datetime.now(timezone.utc).isoformat(), resolved_by=resolved_by)
    state['blocker_history'].append(entry)
    return entry


def scopes_overlap(first, second):
    """Two output scopes collide when one contains the other (file or directory)."""
    def inside(x, y):
        x, y = x.rstrip('/'), y.rstrip('/')
        return x == y or y.startswith(x + '/') or x.startswith(y + '/')
    return any(inside(x, y) for x in first for y in second)


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


def external_skill_entry(root, name):
    """An extension skill is held to the same contract as a built-in entry."""
    require(isinstance(name, str) and ID.fullmatch(name), 'Invalid skill ID')
    root = Path(root).resolve()
    directory = root / 'extensions' / name
    path = local_path(root, f'extensions/{name}/SKILL.md')
    require(path == directory / 'SKILL.md' and path.is_file(), f'Missing extension skill: {name}')
    text = path.read_text(encoding='utf-8')
    parts = text.split('---\n', 2)
    require(len(parts) == 3 and not parts[0], f'Missing frontmatter: {name}')
    fields = {}
    for line in parts[1].splitlines():
        key, separator, value = line.partition(':')
        require(separator and key in ('name', 'description') and key not in fields, f'Invalid skill metadata: {name}')
        fields[key] = value.strip()
    require(fields.get('name') == name and nonempty(fields.get('description')), f'Invalid skill identity: {name}')
    for heading in ('Inputs', 'Method', 'Outputs', 'Checks', 'Boundary'):
        require(f'## {heading}' in text, f'Missing {heading}: {name}')
    require('Return to the core' in text and 'Do not dispatch' in text, f'Missing specialist boundary: {name}')
    check_links(path, path.parent)
    return {'name': name, 'description': fields['description'], 'path': str(path.relative_to(root)),
            'sha256': digest(path)}


def discover_extensions(root):
    """Tolerant loader: a broken extension degrades to a warning, never a failure."""
    entries, warnings = {}, []
    base = Path(root).resolve() / 'extensions'
    if not base.is_dir():
        return entries, warnings
    for directory in sorted(base.iterdir()):
        if directory.name.startswith('.') or directory.name == 'README.md':
            continue
        if not directory.is_dir():
            warnings.append(f'{ADVISORY_PREFIX}extensions/{directory.name} is not a skill directory')
            continue
        try:
            if directory.name in discover_skills(root):
                warnings.append(f'{ADVISORY_PREFIX}extensions/{directory.name} is shadowed by the '
                                'built-in skill with the same name and stays unused')
                continue
            entries[directory.name] = external_skill_entry(root, directory.name)
        except (ValueError, OSError) as error:
            warnings.append(f'{ADVISORY_PREFIX}extensions/{directory.name}: {error}')
    return entries, warnings


def resolve_skill(root, name):
    """A skill is selected by name; a built-in entry wins over an extension with the same name."""
    require(isinstance(name, str) and ID.fullmatch(name), 'Invalid skill ID')
    if (Path(root).resolve() / 'skills' / name).exists() or (Path(root).resolve() / 'skills' / name).is_symlink():
        return skill_entry(root, name)
    return external_skill_entry(root, name)


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

    Thresholds are guidance, not gates: exceeding one only produces an
    ADVISORY_PREFIX note that callers filter out, and never a hard failure. They
    are kept deliberately loose so ordinary document growth does not turn into a
    warning; a note means an entry point has drifted well past its role as a
    readable entry, and reference-like detail belongs in references/ instead.

    Every returned note is prefixed with ADVISORY_PREFIX so callers can separate
    advice from hard validation errors without matching message text.
    """
    notes = []
    for name, limit in ENTRY_BUDGETS:
        path = Path(root) / name
        size = path.stat().st_size if path.is_file() else 0
        if size > limit:
            notes.append(f'{ADVISORY_PREFIX}{name} is {size} bytes (advisory budget {limit}); '
                         'consider moving reference-like detail out of the entry point')
    for base_name in ('skills', 'extensions'):
        base = Path(root) / base_name
        if not base.is_dir():
            continue
        for path in sorted(base.glob('*/SKILL.md')):
            size = path.stat().st_size
            if size > SKILL_BUDGET:
                notes.append(f'{ADVISORY_PREFIX}{base_name}/{path.parent.name}/SKILL.md is {size} bytes '
                             f'(advisory budget {SKILL_BUDGET}); consider moving reference-like detail '
                             'into its references/ directory')
    return notes


def validate(root):
    root = Path(root).resolve()
    try:
        phases = core_phases(root)
        config = read_json(root / 'framework.json')
        expected_fields = {'schema_version', 'note', 'phases', 'activities', 'output_roots',
                           'roles', 'evaluation_fields'}
        require(set(config) == expected_fields and config['schema_version'] == 8,
                'framework.json fields or schema differ from the implemented contract')
        require(isinstance(config['note'], str) and config['note'].strip(), 'framework.json note is required')
        require(config['phases'] == [dict(name=name, **phase) for name, phase in phases.items()],
                'framework.json phases differ from SKILL.md')
        require(config['activities'] == list(ACTIVITIES), 'framework.json activities differ from runtime')
        require(isinstance(config['output_roots'], list) and len(config['output_roots']) == len(OUTPUT_ROOTS)
                and set(config['output_roots']) == OUTPUT_ROOTS, 'framework.json output roots differ from runtime')
        require(config['roles'] == list(ROLE_IDS), 'framework.json roles differ from runtime')
        require(config['evaluation_fields'] == list(MEASURES), 'framework.json evaluation fields differ from runtime')
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
        require(state['schema_version'] == 8 and state['mode'] == 'planning', 'Invalid planning defaults')
        log_template = (root / 'templates/research-log.md').read_text(encoding='utf-8')
        require(log_template.count('<!-- brief:start -->') == log_template.count('<!-- brief:end -->') == 1,
                'Research log template must contain exactly one current-brief marker block')
        manifest = read_json(root / 'provenance.json')
        for item in manifest['files'].values():
            path = local_path(root, item['path'])
            require(path.is_file() and digest(path) == item['sha256'], f'Adapted source changed: {item["path"]}')
    except (ValueError, OSError, KeyError, TypeError, AttributeError) as error:
        return [str(error)]
    return budget_notes(root) + discover_extensions(root)[1]


def initialize(root, project, question):
    root, project = Path(root).resolve(), Path(project).absolute()
    require(nonempty(question), 'Research question cannot be blank')
    require(not project.exists() and not project.is_symlink(), 'Project destination already exists; refusing to overwrite')
    state = read_json(root / 'templates/research-state.json')
    require(state.get('schema_version') == 8 and state.get('mode') == 'planning', 'Unsupported state defaults')
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


def verify_audit(project, reference, label, required_paths, required_prefixes):
    record = verify_reference(project, reference, label)
    audit = read_json(local_path(project, record['path']))
    require(audit.get('schema_version') == 2, f'Unknown {label} schema version')
    subjects = audit.get('subjects')
    require(isinstance(subjects, list) and subjects, f'{label} must bind reviewed subjects')
    require(nonempty(audit.get('reviewer')), f'{label} reviewer is required')
    iso_timestamp(audit.get('reviewed_at'), f'{label} reviewed_at')
    claims = audit.get('claims')
    require(isinstance(claims, list) and claims, f'{label} must record the verified claims')
    for claim in claims:
        require(isinstance(claim, dict) and nonempty(claim.get('claim')) and nonempty(claim.get('support')),
                'Each audit claim needs its text and the support it was given')
    checked = [verify_reference(project, subject, label + ' subject') for subject in subjects]
    paths = {subject['path'] for subject in checked}
    require(set(required_paths).issubset(paths), f'{label} lacks required subject versions')
    primary_paths = paths - set(required_paths) - {record['path']}
    require(any(path.startswith(required_prefixes) for path in primary_paths), f'{label} lacks primary artifacts')
    return [record] + checked


def check_outputs(project, outputs, inputs, *, require_new=True):
    require(isinstance(outputs, list) and outputs, 'Explicit output paths are required')
    checked = []
    for value in outputs:
        path = local_path(project, value)
        relative = path.relative_to(project)
        require(relative.parts and relative.parts[0] in OUTPUT_ROOTS and len(relative.parts) > 1,
                f'Output must be a bounded task artifact, not global state or a root directory: {value}')
        require(not (project / value).is_symlink() and (not require_new or not path.exists()),
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


def migrate_project(root, project):
    path = Path(project).resolve() / 'research-state.json'
    require(not path.is_symlink(), 'Project state must not be a symlink')
    original = path.read_bytes()
    state = json.loads(original)
    version = state.get('schema_version')
    require(version in (5, 6, 7), 'Only schema 5, 6 or 7 projects can be migrated to schema 8')
    require(state.get('mode') == 'planning' and state.get('status') in PROJECT_STATUS,
            'Return to planning before migration')
    require(isinstance(state.get('tasks'), dict) and isinstance(state.get('history'), list)
            and isinstance(state.get('active_tasks'), list), 'Invalid legacy state')
    require(not state['active_tasks'] and all(task.get('status') != 'running'
                                              and not any(v == 'running' for v in task.get('jobs', {}).values())
                                              for task in state['tasks'].values()),
            'Reconcile active executors and jobs before migration')
    require(state.get('phase') in core_phases(root) and isinstance(state.get('blockers'), list)
            and type(state.get('revision')) is int and state['revision'] >= 0,
            'Invalid legacy state invariants')
    if version == 5:
        state.update(goal=None, grant=None, reflections=[])
    if version in (5, 6):
        # Schema 6 to 7: free-text blockers become stable, auditable blocker records.
        now = datetime.now(timezone.utc).isoformat()
        add_events = {event.get('add'): event for event in state['history']
                      if event.get('action') == 'blockers-changed' and event.get('add')}
        close_events = {event.get('resolve'): event for event in state['history']
                        if event.get('action') == 'blockers-changed' and event.get('resolve')}
        id_map, recovered, open_records, history_records = {}, {}, [], []
        seq = 0
        for text in state['blockers']:
            seq += 1
            id_map[text] = f'b{seq}'
            event = add_events.get(text)
            open_records.append({'blocker_id': id_map[text], 'text': text,
                                  'opened_at': event.get('at') if event else now,
                                  'opened_revision': event.get('revision') if event else state['revision'],
                                  'freeze_all': False})
        # A resolves declaration may name a blocker resolved earlier; recover those from
        # decision history instead of guessing or silently dropping the reference.
        declared = {text for task in state['tasks'].values() for text in (task.get('resolves') or [])}
        for text in sorted(declared - set(id_map)):
            add_event, close_event = add_events.get(text), close_events.get(text)
            require(add_event is not None or close_event is not None,
                    f'Cannot identify the blocker named by a resolves declaration: "{text}"; '
                    'fix the reference manually before migration')
            seq += 1
            recovered[text] = f'b{seq}'
            history_records.append({'blocker_id': recovered[text], 'text': text,
                                    'opened_at': (add_event or close_event)['at'],
                                    'opened_revision': (add_event or close_event).get('revision', state['revision']),
                                    'freeze_all': False,
                                    'resolved_at': close_event['at'] if close_event else now,
                                    'resolved_by': {'kind': 'migration', 'revision': state['revision']}})
        for task in state['tasks'].values():
            task['resolves'] = [id_map.get(text, recovered.get(text)) for text in (task.get('resolves') or [])]
        state.update(blockers=open_records, blocker_history=history_records, blocker_seq=seq)
    # Schema 7 to 8: per-task tool assignments become a structured contract field.
    # Prose objectives are never parsed back into assignments; redeclare channels
    # with --tool on any task that must keep external access.
    for task in state['tasks'].values():
        task.setdefault('tools', [])
    state['schema_version'] = 8
    return save_decision(project, state, hashlib.sha256(original).hexdigest(),
                         {'action': 'schema-migrated',
                          'reason': 'Explicit migration to schema 8; tool assignments are structured fields'})


def project_state(root, project):
    path = Path(project).resolve() / 'research-state.json'
    require(not path.is_symlink(), 'Project state must not be a symlink')
    content = path.read_bytes()
    state = json.loads(content)
    require(isinstance(state, dict) and state.get('schema_version') == 8,
            'Unsupported state schema version; manual migration required')
    require(state.get('phase') in core_phases(root), 'Unknown project phase')
    require(state.get('status') in PROJECT_STATUS, 'Unknown project status')
    require(state.get('mode') in ('planning', 'research'), 'Unknown mode')
    require(type(state.get('revision')) is int and state['revision'] >= 0, 'Invalid revision')
    require(isinstance(state.get('tasks'), dict) and isinstance(state.get('history'), list), 'Missing task records')
    require(isinstance(state.get('blockers'), list), 'Invalid project blockers')
    require(isinstance(state.get('blocker_history'), list), 'Invalid blocker history')
    require(type(state.get('blocker_seq')) is int and state['blocker_seq'] >= 0, 'Invalid blocker sequence')
    for blocker in state['blockers'] + state['blocker_history']:
        require(isinstance(blocker, dict) and isinstance(blocker.get('blocker_id'), str)
                and ID.fullmatch(blocker['blocker_id']) and nonempty(blocker.get('text'))
                and iso_timestamp(blocker.get('opened_at'), 'Blocker opened_at')
                and type(blocker.get('freeze_all')) is bool,
                f'Invalid blocker record: {blocker.get("blocker_id") if isinstance(blocker, dict) else blocker}')
    for blocker in state['blocker_history']:
        iso_timestamp(blocker.get('resolved_at'), 'Blocker resolved_at')
    blocker_ids = [blocker['blocker_id'] for blocker in state['blockers'] + state['blocker_history']]
    require(len(blocker_ids) == len(set(blocker_ids)), 'Duplicate blocker ID')
    require(state.get('goal') is None or isinstance(state['goal'], dict), 'Invalid goal reference')
    require(state.get('grant') is None or isinstance(state['grant'], dict), 'Invalid grant')
    require(isinstance(state.get('reflections'), list), 'Invalid reflection history')
    active = state.get('active_tasks')
    require(isinstance(active, list), 'active_tasks must be a list of running task IDs')
    running = sorted(name for name, task in state['tasks'].items() if task['status'] == 'running')
    require(running == sorted(active), 'Active tasks do not match running task records')
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
                role_prompt_text=None, resolves=None, tools=None):
    state, fingerprint = project_state(root, project)
    require(state['status'] == 'active', 'Project is stopped; reactivate it before creating tasks')
    require(state['phase'] != 'complete', 'Completed research reopens only through a new scope decision')
    resolves = list(resolves or [])
    open_ids = open_blocker_ids(state)
    for blocker_id in resolves:
        require(blocker_id in open_ids,
                f'Unknown blocker (or already resolved): {blocker_id}; open: {blocker_summary(state)}')
    message = gate_task(state, resolves, f'Task {task_id}')
    require(message is None, message)
    require(isinstance(task_id, str) and ID.fullmatch(task_id), 'Invalid task ID; use lowercase letters, digits and hyphens')
    require(task_id not in state['tasks'], 'Task ID already exists; never overwrite its contract')
    require(nonempty(objective) and nonempty(acceptance), 'Objective and acceptance criteria are required')
    require(isinstance(activity, str) and activity in ACTIVITIES, 'Unknown task activity')
    require(type(independent_review) is bool, 'independent_review must be a boolean')
    # External channels are structured assignments, never inferred from prose.
    assigned_tools, seen = [], set()
    for tool in list(tools or []):
        require(isinstance(tool, str) and nonempty(tool), f'Invalid tool assignment: {tool}')
        server, separator, operation = tool.partition(':')
        require(separator and OPERATION_ID.fullmatch(server) and OPERATION_ID.fullmatch(operation),
                f'Invalid tool assignment (expected server:operation): {tool}')
        require((server, operation) not in seen, f'Duplicate tool assignment: {tool}')
        seen.add((server, operation))
        assigned_tools.append({'server': server, 'operation': operation})
    selected_role = role_contract(root, role, role_prompt_text)
    selected = resolve_skill(root, skill)
    state['tasks'][task_id] = {'task_id': task_id, 'created_phase': state['phase'], 'objective': objective.strip(),
                              'activity': activity, 'skill': skill, 'role': selected_role,
                              'acceptance_criteria': acceptance.strip(), 'independent_review': independent_review,
                              'resolves': resolves, 'tools': assigned_tools,
                              'status': 'planned', 'assignments': [], 'submission': []}
    save_decision(project, state, fingerprint, {'action': 'task-created', 'task_id': task_id,
                                                'activity': activity, 'skill': skill,
                                                'role': selected_role['id'], 'resolves': resolves,
                                                'tools': assigned_tools,
                                                'reason': objective.strip()})
    return state['tasks'][task_id]


def execution_contract(state):
    return {'mode': state['mode'], 'protocol': state['protocol'], 'evaluation': state['evaluation'],
            'grant': state.get('grant'), 'goal': state.get('goal')}


def verify_grant(project, state, *, check_expiry=True):
    grant = state.get('grant')
    require(isinstance(grant, dict), 'Research requires a scoped user grant')
    verify_reference(project, grant.get('evidence'), 'User grant')
    require(grant.get('scope') and grant.get('services') and grant.get('operations'), 'Incomplete user grant')
    require(type(grant.get('max_runs')) is int and grant['max_runs'] > 0, 'Invalid run limit')
    iso_timestamp(grant.get('expires_at'), 'Grant expiry')
    if check_expiry:
        require(datetime.fromisoformat(grant['expires_at'].replace('Z', '+00:00')) > datetime.now(timezone.utc),
                'User grant expired')
    return grant


def activity_evidence(project, state, activity, records, final=False, *, check_expiry=True):
    require(activity in ACTIVITIES, 'Unknown task activity')
    if activity == 'experiment':
        require(state['mode'] == 'research',
                'Execution requires research mode set through an explicit core decision')
        verify_grant(project, state, check_expiry=check_expiry)
        require(isinstance(state.get('evaluation'), dict), 'Evaluation plan missing')
        for field in MEASURES:
            require(nonempty(state['evaluation'].get(field)), f'Evaluation {field} is required')
        records.append(verify_reference(project, state.get('protocol'), 'Protocol'))
    elif activity == 'conclusions':
        require(state.get('evidence_review', {}).get('status') == 'verified', 'Verified findings required')
        protocol_reference = state.get('protocol')
        required = ['findings.md']
        if isinstance(protocol_reference, dict) and nonempty(protocol_reference.get('path')):
            required.append(verify_reference(project, protocol_reference, 'Protocol')['path'])
        audited = verify_audit(project, state.get('evidence_review'), 'Evidence review',
                               required, PRIMARY_PREFIXES)
        if final:
            require(state.get('review', {}).get('status') == 'passed', 'Passed review required')
            audited += verify_audit(project, state.get('review'), 'Final review', ['findings.md'], FINAL_PREFIXES)
        require({x['path'] for x in records}.issubset({x['path'] for x in audited}), 'Unreviewed evidence in conclusions request')
        records.extend(audited)
    return list({x['path']: x for x in records}.values())


def handoff(root, project, task_id, summary, evidence, *, model, outputs,
            session_mode='fresh', session_reason=None, resume_session_id=None):
    root, project = Path(root).resolve(), Path(project).resolve()
    state, fingerprint = project_state(root, project)
    require(state['status'] == 'active' and state['phase'] != 'complete', 'Project is not active')
    require(isinstance(task_id, str) and task_id in state['tasks'], 'Unknown task ID')
    task = state['tasks'][task_id]
    message = gate_task(state, task.get('resolves') or [], f'Task {task_id}')
    require(message is None, message)
    require(task['status'] == 'planned', 'Task must be planned before assignment')
    require(nonempty(summary) and nonempty(model), 'Assignment rationale and model are required')
    require(isinstance(evidence, list) and evidence, 'At least one evidence file is required')
    session = session_request(session_mode, session_reason, resume_session_id, task['independent_review'])
    selected = resolve_skill(root, task['skill'])
    records = activity_evidence(project, state, task['activity'], [evidence_record(project, p) for p in evidence])
    if task['activity'] == 'experiment':
        grant = verify_grant(project, state)
        attempts = sum(len(t['assignments']) for t in state['tasks'].values() if t['activity'] == 'experiment')
        require(attempts < grant['max_runs'], 'Research run limit exhausted')
    protected = list(records)
    for field in ('protocol', 'evidence_review', 'review'):
        reference = state.get(field)
        if isinstance(reference, dict) and nonempty(reference.get('path')):
            protected.append({'path': reference['path']})
    allowed = check_outputs(project, outputs, protected)
    # Parallel execution is bounded by mutually exclusive output scopes: a running
    # task holds its assigned scopes until it leaves the running state.
    for other_id, other in state['tasks'].items():
        if other_id != task_id and other['status'] == 'running':
            require(other['assignments'], f'Running task {other_id} has no recorded output scope')
            held = other['assignments'][-1]['allowed_outputs']
            require(not scopes_overlap(allowed, held),
                    f'Output scope conflicts with the running task {other_id}; pick disjoint versioned paths')
    return {'schema_version': 8, 'packet_id': str(uuid4()), 'task_id': task_id,
            'created_at': datetime.now(timezone.utc).isoformat(), 'source_revision': state['revision'],
            'state_sha256': fingerprint, 'core_sha256': digest(root / 'SKILL.md'), 'project_phase': state['phase'],
            'objective': task['objective'], 'activity': task['activity'], 'skill': selected,
            'target_role': task['role'], 'requested_model': model, 'session': session, 'summary': summary.strip(),
            'acceptance_criteria': task['acceptance_criteria'], 'evidence': records,
            'declared_blockers': task_resolves_open(state, task.get('resolves') or []),
            'assigned_tools': task['tools'],
            'execution_contract': execution_contract(state), 'allowed_outputs': allowed, 'dispatch_status': 'not_dispatched', 'receipt_required': True,
            'framework_root': str(root), 'project_root': str(project),
            'boundary': ASSIGNMENT_BOUNDARY}


def accept_assignment(root, project, packet, receipt, packet_file=None, receipt_file=None):
    root, project = Path(root).resolve(), Path(project).resolve()
    state, fingerprint = project_state(root, project)
    require(state['status'] == 'active' and state['phase'] != 'complete', 'Project is not active')
    require(packet.get('schema_version') == 8 and receipt.get('schema_version') == 8, 'Unknown packet or receipt schema')
    require(receipt.get('packet_sha256') == packet_digest(packet), 'Receipt packet hash mismatch')
    require(packet.get('source_revision') == state['revision'] and packet.get('state_sha256') == fingerprint,
            'Packet is stale: state revision or hash changed')
    task_id = packet.get('task_id')
    require(isinstance(task_id, str) and task_id in state['tasks'], 'Unknown task ID')
    task = state['tasks'][task_id]
    require(task['status'] == 'planned', 'Task must be planned before assignment')
    message = gate_task(state, task.get('resolves') or [], f'Task {task_id}')
    require(message is None, message)
    require(packet.get('core_sha256') == digest(root / 'SKILL.md'), 'Packet core binding changed')
    require(packet.get('framework_root') == str(root) and packet.get('project_root') == str(project),
            'Packet root binding changed')
    require(packet.get('dispatch_status') == 'not_dispatched' and packet.get('receipt_required') is True
            and packet.get('boundary') == ASSIGNMENT_BOUNDARY, 'Packet dispatch contract changed')
    require(nonempty(packet.get('summary')) and nonempty(packet.get('requested_model')),
            'Packet rationale and model are required')
    session = packet['session']
    require(session == session_request(session.get('mode'), session.get('reason'),
                                       session.get('resume_session_id'), task['independent_review']),
            'Packet session contract changed')
    # The packet cannot rewrite the live task contract: every state-derived field
    # is rechecked directly against the current task and state.
    require(packet.get('objective') == task['objective'] and packet.get('activity') == task['activity'],
            'Packet contract changed: objective')
    require(packet.get('acceptance_criteria') == task['acceptance_criteria'], 'Packet contract changed: acceptance')
    selected = resolve_skill(root, task['skill'])
    require(packet.get('skill') == selected, 'Packet skill binding changed')
    require(packet.get('target_role') == task['role'], 'Packet role binding changed')
    require(packet.get('assigned_tools') == task['tools'], 'Packet tool assignments changed')
    require(packet.get('project_phase') == state['phase'], 'Packet phase snapshot changed')
    require(packet.get('execution_contract') == execution_contract(state), 'Execution contract changed')
    if task['activity'] == 'experiment':
        grant = verify_grant(project, state)
        attempts = sum(len(t['assignments']) for t in state['tasks'].values() if t['activity'] == 'experiment')
        require(attempts < grant['max_runs'], 'Research run limit exhausted')
    require(isinstance(packet.get('evidence'), list) and packet['evidence'], 'Assignment input is required')
    for record in packet['evidence']:
        verify_reference(project, record, 'Assignment input')
    activity_evidence(project, state, task['activity'], list(packet['evidence']))
    for key in ('packet_id', 'task_id', 'source_revision'):
        require(receipt.get(key) == packet[key], f'Receipt mismatch: {key}')
    require(nonempty(packet.get('packet_id')), 'Missing packet ID')
    require(receipt.get('accepted') is True, 'Executor has not accepted assignment')
    iso_timestamp(receipt.get('accepted_at'), 'Receipt accepted_at')
    for key in ('state_hash_checked', 'core_hash_checked', 'skill_hash_checked', 'evidence_hashes_checked'):
        require(receipt.get(key) is True, f'Receipt check missing: {key}')
    require(receipt.get('actual_role') == packet['target_role']['id'], 'Actual role mismatch')
    require(nonempty(receipt.get('actual_model')), 'Actual model is required')
    require(packet['requested_model'] == 'current' or receipt['actual_model'] == packet['requested_model'],
            'Actual model mismatch')
    require(receipt.get('actual_session_mode') == session['mode'], 'Actual session mode mismatch')
    actual_id = receipt.get('actual_session_id')
    require(nonempty(actual_id) or (actual_id is None and nonempty(receipt.get('session_notes'))),
            'Missing host session identity or limitation')
    require(type(receipt.get('session_isolation_verified')) is bool, 'Session isolation check is required')
    history = [a for t in state['tasks'].values() for a in t['assignments']]
    require(all(a['packet_id'] != packet['packet_id'] for a in history), 'Packet already accepted')
    require(actual_id is not None or session['mode'] != 'current' or not state['active_tasks'],
            'Current session without identity cannot be shared with a running task')
    require(actual_id is None or not any(other['status'] == 'running' and other['assignments']
                                        and other['assignments'][-1]['actual_session_id'] == actual_id
                                        for other in state['tasks'].values()),
            'Host session is occupied by a running task')
    if session['mode'] == 'fresh':
        require(receipt['session_isolation_verified'], 'Fresh session isolation must be verified by the core')
        require(actual_id is None or all(a['actual_session_id'] != actual_id for a in history),
                'Fresh session reuses a recorded ID')
    elif session['mode'] == 'current':
        require(not receipt['session_isolation_verified'], 'Current session cannot claim fresh isolation')
    else:
        require(not receipt['session_isolation_verified'], 'A reused session cannot claim fresh isolation')
        require(actual_id == session['resume_session_id'], 'Resume session identity mismatch')
        previous = [a for a in history if a['actual_session_id'] == actual_id]
        require(previous, 'No accepted assignment records this host session')
        last = max(previous, key=lambda a: a['accepted_revision'])
        require(last['skill'] == packet['skill']['name']
                and last['role_id'] == receipt['actual_role']
                and last['role_sha256'] == packet['target_role']['sha256']
                and last['actual_model'] == receipt['actual_model'],
                'Resumed session has incompatible skill, role or model')
    # Recheck scope boundaries without requiring the executor's output to remain absent.
    protected = list(packet['evidence'])
    for field in ('protocol', 'evidence_review', 'review'):
        reference = state.get(field)
        if isinstance(reference, dict) and nonempty(reference.get('path')):
            protected.append({'path': reference['path']})
    allowed = check_outputs(project, packet.get('allowed_outputs'), protected, require_new=False)
    require(allowed == packet['allowed_outputs'], 'Packet output scope changed')
    for other_id, other in state['tasks'].items():
        if other_id != task_id and other['status'] == 'running':
            require(not scopes_overlap(allowed, other['assignments'][-1]['allowed_outputs']),
                    f'Output scope conflicts with the running task {other_id}')
    compact = {'packet_id': packet['packet_id'], 'source_revision': packet['source_revision'],
               'packet_sha256': packet_digest(packet), 'skill': packet['skill']['name'],
               'role_id': packet['target_role']['id'], 'role_sha256': packet['target_role']['sha256'],
               'actual_model': receipt['actual_model'], 'actual_session_id': actual_id,
               'session_mode': session['mode'], 'accepted_revision': state['revision'] + 1,
               'allowed_outputs': allowed, 'evidence': packet['evidence'],
               'execution_contract': packet['execution_contract'],
               'packet_file': packet_file, 'receipt_file': receipt_file}
    task['assignments'].append(compact)
    task['status'] = 'running'
    state['active_tasks'].append(task_id)
    return save_decision(project, state, fingerprint, {'action': 'assignment-accepted', 'task_id': task_id,
                                                      'packet_id': packet['packet_id'], 'reason': packet['summary']})


def host_event(root, project, task_id, job_id, status, reason):
    state, fingerprint = open_project(root, project)
    require(task_id in state['active_tasks'], 'Host events require an active task')
    require(nonempty(job_id) and nonempty(reason), 'Host job identity and reason required')
    require(status in ('running', 'succeeded', 'failed', 'cancelled'), 'Invalid host job status')
    jobs = state['tasks'][task_id].setdefault('jobs', {})
    old = jobs.get(job_id)
    require(old is None or (old == 'running' and status != 'running'), 'Invalid or duplicate job transition')
    jobs[job_id] = status
    return save_decision(project, state, fingerprint, {'action': 'host-job-' + status, 'task_id': task_id,
                                                      'job_id': job_id, 'reason': reason})


def watch(root, project, hours=2):
    state, _ = project_state(root, project)
    require(hours > 0, 'Positive silence threshold required')
    now = datetime.now(timezone.utc)
    problems = []
    for task_id in state['active_tasks']:
        events = [e for e in state['history'] if e.get('task_id') == task_id]
        if events and (now - datetime.fromisoformat(events[-1]['at'])).total_seconds() > hours * 3600:
            problems.append({'task_id': task_id, 'reason': 'silent-running-task'})
    return {'active_tasks': state['active_tasks'], 'anomalies': problems,
            'outstanding_jobs': {tid: [jid for jid, st in task.get('jobs', {}).items() if st == 'running']
                                 for tid, task in state['tasks'].items() if task.get('jobs')},
            'note': 'Read only; host and core must reconcile real job status'}


def update_task(root, project, task_id, status, reason, evidence, *, executor_stopped=False, verdict=None):
    state, fingerprint = open_project(root, project)
    require(isinstance(task_id, str) and task_id in state['tasks'], 'Unknown task ID')
    require(nonempty(reason), 'Core decision reason is required')
    if verdict is not None:
        require(status == 'completed' and verdict in COMPLETION_VERDICTS,
                f'Verdicts apply to completion only; use one of {", ".join(COMPLETION_VERDICTS)}')
    task = state['tasks'][task_id]
    transitions = {'planned': ('cancelled',), 'running': ('blocked', 'submitted', 'cancelled'),
                   'blocked': ('planned', 'cancelled'), 'submitted': ('planned', 'completed', 'cancelled')}
    require(status in transitions.get(task['status'], ()), 'Illegal task status transition')
    if task['status'] == 'running':
        require(executor_stopped is True, 'Confirm executor stopped and reconcile in-flight jobs first')
        require(not any(value == 'running' for value in task.get('jobs', {}).values()),
                'Reconcile outstanding host jobs before leaving running')
        if task_id in state['active_tasks']:
            state['active_tasks'].remove(task_id)
    require(isinstance(evidence, list), 'Evidence must be a list')
    records = [evidence_record(project, path) for path in evidence]
    auto_resolved, declared_already_closed = [], []
    if status in ('submitted', 'blocked') and task['status'] == 'running':
        if status == 'submitted':
            require(records, 'Submission requires output evidence')
        allowed = task['assignments'][-1]['allowed_outputs']
        for record in records:
            require(any(record['path'] == scope or (scope.endswith('/') and record['path'].startswith(scope))
                        for scope in allowed), f'Unassigned run artifact: {record["path"]}')
        if status == 'submitted':
            task['submission'] = records
    if status == 'completed':
        require(task['submission'], 'No submitted artifacts to accept')
        for record in task['submission']:
            verify_reference(project, record, 'Submitted artifact')
        assignment = task['assignments'][-1]
        if task['activity'] == 'experiment':
            require(assignment.get('execution_contract') == execution_contract(state),
                    'Execution contract changed; reconcile the old run before completing')
        for record in assignment['evidence']:
            verify_reference(project, record, 'Task input')
        activity_evidence(project, state, task['activity'], list(assignment['evidence']), check_expiry=False)
        # Completion records finished work: foreign open blockers never freeze it,
        # but an explicit freeze-all emergency stop does.
        require(not freeze_active(state),
                f'Project is frozen by a freeze-all blocker ({blocker_summary(state)}); resolve it before completion')
        # Completing the task closes the open blockers it declared; declared blockers
        # already closed elsewhere are recorded in the decision, never silently dropped.
        resolved_now = task_resolves_open(state, task.get('resolves') or [])
        auto_resolved = [blocker['blocker_id'] for blocker in resolved_now]
        declared_already_closed = [blocker_id for blocker_id in task.get('resolves', [])
                                   if blocker_id not in auto_resolved]
        for blocker in resolved_now:
            close_blocker(state, blocker['blocker_id'],
                          {'kind': 'task', 'task_id': task_id, 'revision': state['revision'] + 1})
    task['status'] = status
    return save_decision(project, state, fingerprint, {'action': 'task-' + status, 'task_id': task_id,
                                                      'reason': reason.strip(), 'evidence': records,
                                                      'auto_resolved': auto_resolved,
                                                      'declared_already_closed': declared_already_closed,
                                                      'verdict': verdict})


def set_goal(root, project, path, reason):
    state, fingerprint = open_project(root, project)
    require(nonempty(reason), 'Goal decision needs a reason')
    record = evidence_record(project, path)
    text = local_path(project, path).read_text(encoding='utf-8')
    require(all(len(re.findall(r'(?m)^' + re.escape(field) + r'[^\S\n]*\S[^\n]*$', text)) == 1
                for field in GOAL_FIELDS),
            'Goal dossier requires one populated line per question, value, boundary, alternatives, evidence, '
            'falsifier, success, feasibility, resources, stop conditions and unknowns')
    require(record['path'].startswith(('hypotheses/', 'reports/')),
            'Versioned goal dossier must be a task artifact')
    require(state.get('goal') != record, 'Goal version is already selected')
    state['goal'] = record
    return save_decision(project, state, fingerprint, {'action': 'goal-selected', 'reason': reason, 'evidence': [record]})


def goal_ready(project, state):
    record = verify_reference(project, state.get('goal'), 'Goal dossier')
    text = local_path(project, record['path']).read_text(encoding='utf-8')
    unknown = re.search(r'(?m)^Unknown:[^\S\n]*(\S[^\n]*)$', text)
    require(unknown and unknown.group(1).strip().lower() in ('none', 'resolved'),
            'Resolve or explicitly bound goal unknowns before leaving scope')
    return record


def transition_phase(root, project, target, reason, evidence):
    state, fingerprint = project_state(root, project)
    phases = core_phases(root)
    require(state['status'] == 'active' and not state['active_tasks'], 'Stop the running executors before changing phase')
    require(not state['blockers'],
            f'Resolve project blockers before changing phase ({blocker_summary(state)})')
    require(nonempty(reason) and isinstance(evidence, list) and evidence, 'Phase decision needs a rationale and evidence')
    require(target in phases[state['phase']]['next'], 'Illegal phase transition')
    records = [evidence_record(project, p) for p in evidence]
    if state['phase'] == 'scope' and target == 'ideation' and state.get('goal'):
        goal_ready(project, state)
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


def authorize(root, project, *, mode, reason, evidence=(), services=(), operations=(), scope=None,
              max_runs=None, expires_at=None):
    state, fingerprint = open_project(root, project)
    require(mode in ('planning', 'research'), 'Unknown mode')
    require(nonempty(reason), 'Research mode decisions need an explicit core reason')
    records = [evidence_record(project, path) for path in evidence]
    if mode == 'research' or services or operations or scope or max_runs or expires_at:
        require(len(records) == 1, 'Access requires one cited user approval artifact')
        require(isinstance(services, (tuple, list)) and services and all(nonempty(x) for x in services),
                'Approved services are required')
        require(isinstance(operations, (tuple, list)) and operations and all(nonempty(x) for x in operations),
                'Approved operations are required')
        if mode == 'planning':
            for operation in operations:
                semantics = planning_semantics(project, services, operation)
                require(semantics['classification'] == 'read',
                        f'Planning grants may only name read-classified operations; {operation} is '
                        f'{semantics["classification"]} ({semantics["basis"]}); confirm it with '
                        'tools --confirm, or request research mode')
        require(nonempty(scope) and type(max_runs) is int and max_runs > 0, 'Grant scope and run limit required')
        iso_timestamp(expires_at, 'Grant expiry')
        require(datetime.fromisoformat(expires_at.replace('Z', '+00:00')) > datetime.now(timezone.utc),
                'User grant expired')
        state['grant'] = {'evidence': records[0], 'services': list(services), 'operations': list(operations),
                          'scope': scope.strip(), 'max_runs': max_runs, 'expires_at': expires_at}
    else:
        state['grant'] = None
    state['mode'] = mode
    return save_decision(project, state, fingerprint, {'action': 'mode-set', 'mode': mode,
                                                      'reason': reason.strip(), 'evidence': records,
                                                      'grant': state['grant']})


def check_tool(root, project, *, task_id, packet_id, server, operation, scope):
    state, _ = project_state(root, project)
    require(state['status'] == 'active' and task_id in state['active_tasks'],
            'Tool access requires an active assignment')
    task = state['tasks'][task_id]
    message = gate_task(state, task.get('resolves') or [], f'Task {task_id}')
    require(message is None, message)
    assignment = task['assignments'][-1]
    require(packet_id == assignment['packet_id'], 'Tool request does not match the active packet')
    grant = verify_grant(project, state)
    require(assignment['execution_contract']['grant'] == grant, 'Assignment grant changed')
    require(server in grant['services'] and operation in grant['operations'] and scope == grant['scope'],
            'Tool request exceeds approved scope')
    require(any(assigned['server'] == server and assigned['operation'] == operation
                for assigned in task.get('tools') or []),
            f'Tool {server}:{operation} was not assigned to task {task_id}; '
            'assign channels at task creation with --tool server:operation')
    semantics = operation_semantics(project, server, operation)
    if semantics['classification'] != 'read':
        require(state['mode'] == 'research' and task['activity'] == 'experiment',
                f'Planning and analysis tasks may only use read-classified channels; '
                f'{server}/{operation} is {semantics["classification"]} ({semantics["basis"]}); '
                'confirm it with tools --confirm or run it under research mode')
        attempts = sum(len(t['assignments']) for t in state['tasks'].values() if t['activity'] == 'experiment')
        require(attempts <= grant['max_runs'], 'Research run limit exhausted')
    return {'allowed': True, 'task_id': task_id, 'packet_id': packet_id, 'grant': grant['evidence'],
            'operation_semantics': semantics,
            'needs_confirmation': semantics['classification'] == 'unknown',
            'preflight_token': preflight_token(task_id, packet_id, server, operation, scope,
                                               semantics['classification'])}


def record_tool_call(root, project, *, task_id, packet_id, server, operation, scope, token):
    """Record one external tool call against the preflight token check-tool issued.

    The call is re-validated exactly as at preflight; the recorded token binds the
    logged call to the checked facts, so the audit trail can be reconciled later.
    """
    result = check_tool(root, project, task_id=task_id, packet_id=packet_id,
                        server=server, operation=operation, scope=scope)
    expected = preflight_token(task_id, packet_id, server, operation, scope,
                               result['operation_semantics']['classification'])
    require(token == expected, 'Preflight token mismatch; run check-tool and carry the returned token')
    state, fingerprint = open_project(root, project)
    return save_decision(project, state, fingerprint,
                         {'action': 'tool-call-recorded', 'task_id': task_id, 'packet_id': packet_id,
                          'server': server, 'operation': operation, 'scope': scope, 'token': token,
                          'reason': f'{server}/{operation} recorded against its preflight token'})


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
            protocol_reference = state.get('protocol')
            required = ['findings.md']
            if isinstance(protocol_reference, dict) and nonempty(protocol_reference.get('path')):
                required.append(verify_reference(project, protocol_reference, 'Protocol')['path'])
            verify_audit(project, reference, label, required, PRIMARY_PREFIXES)
        else:
            verify_audit(project, reference, label, ['findings.md'], FINAL_PREFIXES)
    field = 'evidence_review' if kind == 'evidence' else 'review'
    state[field] = {'status': status, 'path': str(relative), 'sha256': reference['sha256']}
    return save_decision(project, state, fingerprint, {'action': f'{field}-set', field: dict(state[field]),
                                                      'reason': reason.strip()})


def update_blockers(root, project, *, add=None, resolve=None, reason, edit=None, text=None, freeze_all=False):
    state, fingerprint = open_project(root, project)
    require(nonempty(reason), 'Blocker decision needs an explicit core decision reason')
    require(bool(add) or bool(resolve) or bool(edit), 'Declare a blocker to add, resolve or edit')
    if edit is not None:
        require(nonempty(text), 'Editing a blocker requires the replacement text')
        blocker = find_open_blocker(state, edit)
        previous = blocker['text']
        blocker['text'] = text.strip()
        return save_decision(project, state, fingerprint, {'action': 'blocker-edited', 'blocker_id': edit,
                                                           'from_text': previous, 'to_text': blocker['text'],
                                                           'reason': reason.strip()})
    if add is not None:
        require(nonempty(add), 'Blocker text cannot be blank')
        require(not any(blocker['text'] == add.strip() for blocker in state['blockers']),
                'An open blocker with this text already exists '
                f'({blocker_summary(state)}); edit it or reword the new blocker')
        state['blocker_seq'] += 1
        state['blockers'].append({'blocker_id': f"b{state['blocker_seq']}", 'text': add.strip(),
                                  'opened_at': datetime.now(timezone.utc).isoformat(),
                                  'opened_revision': state['revision'] + 1, 'freeze_all': bool(freeze_all)})
    if resolve is not None:
        close_blocker(state, resolve, {'kind': 'manual', 'revision': state['revision'] + 1})
    return save_decision(project, state, fingerprint, {'action': 'blockers-changed', 'add': add, 'resolve': resolve,
                                                      'blockers': blocker_summary(state), 'reason': reason.strip()})


def list_blockers(root, project):
    """Read-only view of open and resolved blockers with their stable identities."""
    state, _ = project_state(root, project)
    return {'open': state['blockers'], 'history': state['blocker_history'],
            'note': 'Read only; change blockers with blockers --add, --resolve or --edit'}


def ingest_catalog(root, project, server, catalog, reason):
    """Classify a host-exported MCP tool catalog into the project tool registry.

    The host (which can see the server) exports the tool list to a project-relative
    file; the helper parses it, classifies each operation from the server's own
    declarations, and preserves confirmed answers whose tool signature is unchanged.
    """
    state, fingerprint = open_project(root, project)
    require(nonempty(reason), 'Catalog ingestion needs an explicit core reason')
    require(nonempty(server), 'A server name is required')
    dump = read_json(local_path(project, catalog))
    tools = dump.get('tools') if isinstance(dump, dict) else dump
    require(isinstance(tools, list) and tools, 'The catalog must be a nonempty tools list')
    previous = {}
    path = registry_path(project, server)
    if path.is_file():
        require(not path.is_symlink(), f'Tool registry must not be a symlink: tools/{server}.json')
        previous = read_json(path).get('operations') or {}
        require(isinstance(previous, dict), 'Invalid tool registry')
    now = datetime.now(timezone.utc).isoformat()
    entries, counts = {}, {'read': 0, 'write': 0, 'unknown': 0}
    for tool in tools:
        require(isinstance(tool, dict), 'Each catalog entry must be an object')
        name = tool.get('name')
        require(isinstance(name, str) and OPERATION_ID.fullmatch(name), f'Invalid operation name: {name}')
        description = tool.get('description') or ''
        require(isinstance(description, str), f'Invalid description: {name}')
        annotations = tool.get('annotations') or {}
        require(isinstance(annotations, dict), f'Invalid annotations: {name}')
        schema = tool.get('input_schema') or tool.get('inputSchema') or {}
        require(isinstance(schema, dict), f'Invalid input schema: {name}')
        args = sorted((schema.get('properties') or {}).keys())
        signature = hashlib.sha256(json.dumps([name, description, sorted(annotations.items()), args],
                                              sort_keys=True, ensure_ascii=False).encode('utf-8')).hexdigest()
        classification = classify_operation(name, description, annotations, args)
        entry = {'operation': name, 'description': description, 'annotations': annotations,
                 'input_args': args, 'classification': classification, 'basis': 'auto',
                 'classified_at': now, 'signature': signature}
        old = previous.get(name)
        if isinstance(old, dict) and old.get('basis') == 'confirmed' and old.get('signature') == signature:
            entry.update(classification=old['classification'], basis='confirmed',
                         confirmed_at=old.get('confirmed_at'), reason=old.get('reason'))
        else:
            counts[classification] += 1
        entries[name] = entry
    registry = {'server': server, 'schema_version': 1,
                'catalog_sha256': digest(local_path(project, catalog)), 'operations': entries}
    write_registry(project, server, registry)
    save_decision(project, state, fingerprint, {'action': 'tool-catalog-ingested', 'server': server,
                                                'auto_classified': counts,
                                                'preserved_confirmations': len(entries) - sum(counts.values()),
                                                'reason': reason.strip()})
    return registry


def confirm_semantics(root, project, server, operation, semantics, reason):
    """Record the user's answer for an ambiguous operation, with drift detection.

    A confirmation binds the tool signature it was given; a catalog re-ingest that
    changes the tool resets the entry to the automatic classification.
    """
    state, fingerprint = open_project(root, project)
    require(semantics in ('read', 'write'), 'Semantics must be read or write')
    require(nonempty(reason), 'Confirming tool semantics needs the user-decided reason')
    require(nonempty(server) and nonempty(operation), 'Server and operation are required')
    path = registry_path(project, server)
    require(path.is_file(), f'No tool registry for server {server}; ingest a catalog first')
    registry = read_json(path)
    entry = (registry.get('operations') or {}).get(operation)
    require(isinstance(entry, dict), f'Unknown operation for server {server}: {operation}')
    entry.update(classification=semantics, basis='confirmed',
                 confirmed_at=datetime.now(timezone.utc).isoformat(), reason=reason.strip())
    write_registry(project, server, registry)
    save_decision(project, state, fingerprint, {'action': 'tool-semantics-confirmed', 'server': server,
                                                'operation': operation, 'semantics': semantics,
                                                'reason': reason.strip()})
    return registry


def view_registry(root, project, server=None):
    """Read-only view of the ingested tool registries."""
    project_state(root, project)
    base = Path(project).resolve() / 'tools'
    servers = {}
    if base.is_dir():
        for path in sorted(base.glob('*.json')):
            if server and path.stem != server:
                continue
            servers[path.stem] = read_json(path)
    if server:
        require(server in servers, f'No tool registry for server {server}; ingest a catalog first')
    return {'servers': servers,
            'note': 'Read only; classify with tools --catalog and confirm with tools --confirm'}


def set_project_status(root, project, *, status, reason):
    state, fingerprint = project_state(root, project)
    require(status in PROJECT_STATUS, 'Unknown project status')
    require(nonempty(reason), 'Project status decision needs an explicit core reason')
    require(status != state['status'], f'Project already has status {status}; no decision to record')
    if status != 'active':
        require(not state['active_tasks'], 'Stop the running executors before stopping the project')
    previous = state['status']
    state['status'] = status
    return save_decision(project, state, fingerprint, {'action': 'project-status-changed', 'from_status': previous,
                                                      'to_status': status, 'reason': reason.strip()})


def record_reflection(root, project, task_id, path, reason):
    state, fingerprint = open_project(root, project)
    task = state['tasks'].get(task_id)
    require(task and task['status'] in ('completed', 'blocked'),
            'Reflection requires a finished or blocked task')
    require(nonempty(reason), 'Reflection needs a core decision reason')
    record = evidence_record(project, path)
    require(record['path'].startswith('reports/'), 'Reflection must be a versioned report')
    proposal = read_json(local_path(project, path))
    for field in ('observation', 'protocol_check', 'counterevidence', 'alternatives', 'next_options',
                  'prediction', 'decision', 'evidence'):
        require(proposal.get(field), f'Reflection needs {field}')
    require(isinstance(proposal['evidence'], list), 'Reflection evidence must be a list')
    sources = [verify_reference(project, ref, 'Reflection source') for ref in proposal['evidence']]
    original = {(x['path'], x['sha256']) for x in task['submission']}
    if task['status'] == 'blocked':
        original.update((x['path'], x['sha256']) for event in state['history']
                        if event.get('task_id') == task_id and event.get('action') == 'task-blocked'
                        for x in event.get('evidence', []))
    require(original.intersection((x['path'], x['sha256']) for x in sources),
            'Reflection must cite unchanged original run evidence')
    require(all(x['artifact']['path'] != path for x in state['reflections']), 'Reflection version already recorded')
    state['reflections'].append({'task_id': task_id, 'artifact': record, 'prediction': proposal['prediction'],
                                 'decision': proposal['decision'], 'recorded_revision': state['revision'] + 1,
                                 'followup': None})
    return save_decision(project, state, fingerprint, {'action': 'reflection-recorded', 'task_id': task_id,
                                                      'reason': reason, 'evidence': [record] + sources})


def review_reflection(root, project, path, followup_task, reason, *, assessment):
    state, fingerprint = open_project(root, project)
    require(nonempty(reason), 'Follow-up review needs a reason')
    require(assessment in ('supported', 'contradicted', 'inconclusive'), 'Invalid prediction assessment')
    ref = next((x for x in state['reflections'] if x['artifact']['path'] == path), None)
    require(ref and ref['followup'] is None, 'Unknown or reviewed reflection')
    verify_reference(project, ref['artifact'], 'Reflection')
    task = state['tasks'].get(followup_task)
    require(followup_task != ref['task_id'] and task and task['status'] == 'completed',
            'Follow-up must be a different completed task')
    require(any(event.get('action') == 'task-completed' and event.get('task_id') == followup_task
                and event['revision'] > ref['recorded_revision'] for event in state['history']),
            'Follow-up task must complete after the reflection')
    require(task['submission'], 'Follow-up requires raw evidence')
    for source in task['submission']:
        verify_reference(project, source, 'Follow-up result')
    ref['followup'] = {'task_id': followup_task, 'evidence': task['submission'],
                       'assessment': assessment, 'reason': reason}
    return save_decision(project, state, fingerprint, {'action': 'reflection-reviewed', 'task_id': followup_task,
                                                      'assessment': assessment, 'reason': reason,
                                                      'evidence': task['submission']})


def blocker_age(blocker):
    """Age of an open blocker in hours, from the identity-preserving opened_at."""
    opened = datetime.fromisoformat(blocker['opened_at'].replace('Z', '+00:00'))
    hours = (datetime.now(timezone.utc) - opened).total_seconds() / 3600
    return f'{hours:.1f}h'


def status(root, project):
    """Read-only progress board rendered as Markdown from the project state."""
    state, _ = project_state(root, project)
    resolving = {}
    for task in state['tasks'].values():
        if task.get('status') in ('planned', 'running', 'submitted'):
            for blocker in task.get('resolves') or []:
                resolving.setdefault(blocker, []).append(task['task_id'])
    lines = [f"# Research Status", '',
             f"- **Question:** {state['question']}",
             f"- **Status:** {state['status']}",
             f"- **Phase:** {state['phase']}",
             f"- **Mode:** {state['mode']}",
             f"- **Goal dossier:** {(state.get('goal') or {}).get('path', 'none')}",
             f"- **Scoped grant:** {(state.get('grant') or {}).get('scope', 'none')}",
             f"- **Reflections:** {len(state.get('reflections', []))}"]
    running = [name for name, task in state['tasks'].items() if task['status'] == 'running']
    lines.append(f"- **Active tasks:** {', '.join(running) or 'none'}")
    if state.get('reflections'):
        latest = state['reflections'][-1]
        assessment = latest['followup']['assessment'] if latest.get('followup') else 'awaiting follow-up'
        lines.append(f"- **Latest prediction:** {latest['prediction']} ({assessment})")
    if state['blockers']:
        lines.append(f"- **Blockers:** {len(state['blockers'])} open, {len(state['blocker_history'])} resolved")
        for blocker in state['blockers']:
            owners = resolving.get(blocker['blocker_id'])
            marker = ' [freeze-all]' if blocker.get('freeze_all') else ''
            suffix = f" (being resolved by {', '.join(owners)})" if owners else ' (unresolved)'
            lines.append(f"  - {blocker['blocker_id']}: {blocker['text']}{marker}, "
                         f"open for {blocker_age(blocker)}{suffix}")
    else:
        lines.append('- **Blockers:** none')
    lines += ['', '## Tasks', '',
              '| Task | Status | Activity | Skill | Role | Resolves |',
              '|---|---|---|---|---|---|']
    for task in state['tasks'].values():
        lines.append(f"| {task['task_id']} | {task['status']} | {task['activity']} | {task['skill']} "
                     f"| {task['role']['id']} | {', '.join(task.get('resolves') or []) or '-'} |")
    lines += ['', '## Recent Decisions', '']
    for event in state['history'][-5:]:
        marker = f" ({event['task_id']})" if event.get('task_id') else ''
        lines.append(f"- r{event['revision']} {event['at']}: {event['action']}{marker} - {event.get('reason', '')}")
    return '\n'.join(lines) + '\n'


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('validate', help='Validate core contract, flat skills, extensions and provenance')
    commands.add_parser('skills', help='List built-in and extension skills directly from disk')
    status_parser = commands.add_parser('status', help='Print a read-only progress board; no state change')
    status_parser.add_argument('--project', required=True, type=Path)
    watch_parser = commands.add_parser('watch', help='Read-only active task and job supervision')
    watch_parser.add_argument('--project', required=True, type=Path)
    watch_parser.add_argument('--hours', type=float, default=2)
    migrate = commands.add_parser('migrate', help='Explicit idle planning schema 5, 6 or 7 to 8 migration')
    migrate.add_argument('--project', required=True, type=Path)
    init = commands.add_parser('init', help='Create four planning documents')
    init.add_argument('--project', required=True, type=Path)
    init.add_argument('--question', required=True)
    goal = commands.add_parser('set-goal', help='Core only: select a versioned planning dossier')
    for option in ('project', 'path', 'reason'):
        goal.add_argument('--' + option, required=True)
    tool = commands.add_parser('check-tool', help='Read-only check before host tool invocation')
    for option in ('project', 'task', 'packet', 'server', 'operation', 'scope'):
        tool.add_argument('--' + option, required=True)
    tools = commands.add_parser('tools', help='Ingest a host tool catalog, confirm ambiguous semantics, or view registries')
    tools.add_argument('--project', required=True, type=Path)
    tools.add_argument('--server')
    tools.add_argument('--catalog')
    tools.add_argument('--confirm', action='store_true')
    tools.add_argument('--operation')
    tools.add_argument('--semantics', choices=('read', 'write'))
    tools.add_argument('--reason')
    call = commands.add_parser('tool-call', help='Core only: record an external call against its preflight token')
    for option in ('project', 'task', 'packet', 'server', 'operation', 'scope', 'token'):
        call.add_argument('--' + option, required=True)
    event = commands.add_parser('host-event', help='Core only: record host job state')
    for option in ('project', 'task', 'job', 'status', 'reason'):
        event.add_argument('--' + option, required=True)
    reflect = commands.add_parser('reflect', help='Core only: bind experiment reflection')
    for option in ('project', 'task', 'path', 'reason'):
        reflect.add_argument('--' + option, required=True)
    review_reflect = commands.add_parser('review-reflection', help='Core only: review follow-up result')
    for option in ('project', 'path', 'task', 'reason'):
        review_reflect.add_argument('--' + option, required=True)
    review_reflect.add_argument('--assessment', required=True,
                                choices=('supported', 'contradicted', 'inconclusive'))
    task = commands.add_parser('task', help='Core only: register a stable task without changing phase')
    for name in ('task', 'objective', 'activity', 'skill', 'role', 'acceptance'):
        task.add_argument('--' + name, required=True)
    task.add_argument('--project', required=True, type=Path)
    task.add_argument('--independent-review', action='store_true')
    task.add_argument('--resolves', nargs='+', default=[], help='Open blocker IDs this task is created to resolve')
    task.add_argument('--tool', action='append', default=[],
                      help='Assigned external channel as server:operation; repeatable')
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
    update.add_argument('--verdict', choices=COMPLETION_VERDICTS,
                        help='Structured acceptance verdict recorded with a completion')
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
    grant.add_argument('--services', nargs='+', default=[])
    grant.add_argument('--operations', nargs='+', default=[])
    grant.add_argument('--scope')
    grant.add_argument('--max-runs', type=int)
    grant.add_argument('--expires-at')
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
    blockers = commands.add_parser('blockers', help='Core only: add, resolve, edit or list project blockers')
    blockers.add_argument('--project', required=True, type=Path)
    blockers.add_argument('--add')
    blockers.add_argument('--resolve')
    blockers.add_argument('--edit')
    blockers.add_argument('--text')
    blockers.add_argument('--freeze-all', action='store_true')
    blockers.add_argument('--list', action='store_true')
    blockers.add_argument('--reason')
    project_status = commands.add_parser('project-status', help='Core only: activate or stop the project')
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
            for name, entry in discover_extensions(ROOT)[0].items():
                result.setdefault(name, entry)
        elif args.command == 'status':
            print(status(ROOT, args.project))
            return 0
        elif args.command == 'watch':
            result = watch(ROOT, args.project, hours=args.hours)
        elif args.command == 'migrate':
            result = migrate_project(ROOT, args.project)
        elif args.command == 'set-goal':
            result = set_goal(ROOT, args.project, args.path, args.reason)
        elif args.command == 'check-tool':
            result = check_tool(ROOT, args.project, task_id=args.task, packet_id=args.packet,
                                server=args.server, operation=args.operation, scope=args.scope)
        elif args.command == 'tool-call':
            result = record_tool_call(ROOT, args.project, task_id=args.task, packet_id=args.packet,
                                      server=args.server, operation=args.operation, scope=args.scope,
                                      token=args.token)
        elif args.command == 'tools':
            if args.catalog is not None:
                result = ingest_catalog(ROOT, args.project, args.server, args.catalog,
                                        args.reason or 'Host exported the server tool catalog')
            elif args.confirm:
                result = confirm_semantics(ROOT, args.project, args.server, args.operation,
                                           args.semantics, args.reason)
            else:
                result = view_registry(ROOT, args.project, args.server)
        elif args.command == 'host-event':
            result = host_event(ROOT, args.project, args.task, args.job, args.status, args.reason)
        elif args.command == 'reflect':
            result = record_reflection(ROOT, args.project, args.task, args.path, args.reason)
        elif args.command == 'review-reflection':
            result = review_reflection(ROOT, args.project, args.path, args.task, args.reason,
                                       assessment=args.assessment)
        elif args.command == 'init':
            result = initialize(ROOT, args.project, args.question)
        elif args.command == 'task':
            result = create_task(ROOT, args.project, args.task, args.objective, activity=args.activity,
                                 skill=args.skill, role=args.role, acceptance=args.acceptance,
                                 independent_review=args.independent_review,
                                 role_prompt_text=args.role_prompt, resolves=args.resolves, tools=args.tool)
        elif args.command == 'handoff':
            result = handoff(ROOT, args.project, args.task, args.summary, args.evidence,
                             model=args.model, outputs=args.outputs, session_mode=args.session,
                             session_reason=args.session_reason, resume_session_id=args.resume_session)
        elif args.command == 'accept':
            result = accept_assignment(ROOT, args.project, read_json(local_path(args.project, args.packet)),
                                       read_json(local_path(args.project, args.receipt)),
                                       packet_file=args.packet, receipt_file=args.receipt)
        elif args.command == 'task-status':
            result = update_task(ROOT, args.project, args.task, args.status, args.reason, args.evidence,
                                 executor_stopped=args.executor_stopped, verdict=args.verdict)
        elif args.command == 'authorize':
            result = authorize(ROOT, args.project, mode=args.mode, reason=args.reason, evidence=args.evidence,
                               services=args.services, operations=args.operations, scope=args.scope,
                               max_runs=args.max_runs, expires_at=args.expires_at)
        elif args.command == 'set-evaluation':
            result = set_evaluation(ROOT, args.project, **{field: getattr(args, field) for field in MEASURES},
                                    reason=args.reason)
        elif args.command == 'set-protocol':
            result = set_protocol(ROOT, args.project, path=args.path, reason=args.reason)
        elif args.command == 'set-audit':
            result = set_audit(ROOT, args.project, kind=args.kind, path=args.path, status=args.status,
                               reason=args.reason)
        elif args.command == 'blockers':
            if args.list:
                result = list_blockers(ROOT, args.project)
            else:
                result = update_blockers(ROOT, args.project, add=args.add, resolve=args.resolve,
                                         reason=args.reason, edit=args.edit, text=args.text,
                                         freeze_all=args.freeze_all)
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
