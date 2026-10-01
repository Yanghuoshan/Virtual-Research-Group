import contextlib
import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts/research.py'
# Directories that are not maintained bundle text: user projects, tooling and git internals.
SKIP_DIRECTORIES = ('projects', '.venv', '.git')
# Unicode ranges for scripts that would violate the English-only rule. Written as
# code points so this file stays pure ASCII and passes its own bundle check.
NON_LATIN_RANGES = ((0x1100, 0x11FF), (0x2E80, 0x2FDF), (0x3040, 0x30FF), (0x3130, 0x318F),
                    (0x3400, 0x9FFF), (0xA960, 0xA97F), (0xAC00, 0xD7AF), (0xF900, 0xFAFF),
                    (0x0400, 0x052F), (0x0590, 0x05FF), (0x0600, 0x06FF),
                    (0x0E00, 0x0E7F), (0x20000, 0x323AF))


def non_latin_characters(text):
    """Every distinct non-Latin script character in text, for the English-only check."""
    return sorted({ch for ch in text if any(low <= ord(ch) <= high for low, high in NON_LATIN_RANGES)})


def load_tool():
    spec = importlib.util.spec_from_file_location('research', SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def register_task(tool, project, task_id='t1', **changes):
    options = dict(activity='analysis', skill='brainstorming-research-ideas', role='strategist',
                   acceptance='State falsifiable predictions', independent_review=False)
    options.update(changes)
    return tool.create_task(ROOT, project, task_id, 'Analyze supplied evidence', **options)


class FrameworkTests(unittest.TestCase):
    def setUp(self):
        self.tool = load_tool()
        self.temp = tempfile.TemporaryDirectory(dir=ROOT)
        self.addCleanup(self.temp.cleanup)
        self.project = Path(self.temp.name) / 'project'

    def initialize(self):
        self.tool.initialize(ROOT, self.project, 'Study structural inductive biases')
        register_task(self.tool, self.project)

    def state(self):
        return json.loads((self.project / 'research-state.json').read_text())

    def save(self, state):
        (self.project / 'research-state.json').write_text(json.dumps(state))

    def evidence(self, name='literature/review.md'):
        path = self.project / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('Evidence with provenance, limitations and unresolved questions.')
        return name

    def handoff(self, task_id='t1', summary='Analyze the evidence', evidence=None, **changes):
        options = dict(model='current', outputs=['hypotheses/candidates.md'])
        options.update(changes)
        return self.tool.handoff(ROOT, self.project, task_id, summary,
                                 ['research-brief.md'] if evidence is None else evidence, **options)

    def test_architecture_and_provenance_validate(self):
        # Advisory notes are guidance, not failures: only hard errors count here.
        failures = [error for error in self.tool.validate(ROOT)
                    if not error.startswith(self.tool.ADVISORY_PREFIX)]
        self.assertEqual(failures, [])

    def test_bundle_text_is_english(self):
        violations = []
        for path in sorted(ROOT.rglob('*')):
            relative = path.relative_to(ROOT)
            if not path.is_file() or relative.parts[0] in SKIP_DIRECTORIES or '__pycache__' in relative.parts:
                continue
            if path.is_relative_to(Path(self.temp.name)):
                continue
            try:
                text = path.read_text(encoding='utf-8')
            except UnicodeDecodeError:
                continue
            if path.suffix == '.json':
                text = json.dumps(json.loads(text), ensure_ascii=False)
            found = non_latin_characters(text)
            if found:
                violations.append(f'{relative}: {found[:5]}')
        self.assertEqual(violations, [], 'Non-English script text remains in the bundle')

    def test_english_check_covers_more_than_han_characters(self):
        samples = {'kana': chr(0x30C7), 'hangul': chr(0xD55C), 'cyrillic': chr(0x041F),
                   'arabic': chr(0x0645), 'thai': chr(0x0E01)}
        for name, sample in samples.items():
            with self.subTest(script=name):
                self.assertTrue(non_latin_characters(sample), f'English check must flag {name} text')
        self.assertEqual(non_latin_characters('Mechanism, evidence and falsifier'), [])

    def test_generated_scaffolding_is_english_and_preserves_user_input(self):
        question = chr(0x56FE) + chr(0x5206) + chr(0x7C7B)
        self.tool.initialize(ROOT, self.project, question)
        brief = (self.project / 'research-brief.md').read_text()
        self.assertIn('# Research Scope', brief)
        self.assertIn('Planning only; no experimental results yet.', brief)
        self.assertIn(question, brief)
        self.assertEqual(self.state()['question'], question)

    def test_init_does_not_overwrite_existing_directory(self):
        self.project.mkdir()
        marker = self.project / 'keep.txt'
        marker.write_text('keep')
        with self.assertRaises(ValueError):
            self.initialize()
        self.assertEqual(marker.read_text(), 'keep')
        self.assertFalse((self.project / 'research-state.json').exists())

    def test_blank_question_rejected(self):
        with self.assertRaises(ValueError):
            self.tool.initialize(ROOT, self.project, '  ')
        self.assertFalse(self.project.exists())

    def test_handoff_records_explicit_model_and_fingerprints_without_state_change(self):
        self.initialize()
        before = (self.project / 'research-state.json').read_bytes()
        packet = self.handoff(model='provider/custom-model')
        self.assertEqual(packet['requested_model'], 'provider/custom-model')
        self.assertEqual(packet['dispatch_status'], 'not_dispatched')
        self.assertEqual(packet['state_sha256'], hashlib.sha256(before).hexdigest())
        self.assertEqual(packet['core_sha256'], self.tool.digest(ROOT / 'SKILL.md'))
        self.assertEqual(packet['skill']['sha256'], self.tool.digest(ROOT / packet['skill']['path']))
        self.assertEqual(before, (self.project / 'research-state.json').read_bytes())

    def test_bind_emits_real_subject_hashes_without_state_change(self):
        # A specialist writing an audit, manifest or reflection must record real
        # hashes; bind computes them, so transcription is never the only option.
        self.initialize()
        before = (self.project / 'research-state.json').read_bytes()
        name = self.evidence()
        bound = self.tool.bind(self.project, ['research-brief.md', name])
        self.assertEqual([record['path'] for record in bound], ['research-brief.md', name])
        for record in bound:
            self.assertEqual(record['sha256'],
                             hashlib.sha256((self.project / record['path']).read_bytes()).hexdigest())
        self.assertEqual(before, (self.project / 'research-state.json').read_bytes())
        with self.assertRaisesRegex(ValueError, 'Missing or empty'):
            self.tool.bind(self.project, ['missing.md'])

    def test_digest_streams_large_files_and_never_serves_a_stale_hash(self):
        self.initialize()
        path = self.project / 'data/measurements.bin'
        path.parent.mkdir(parents=True, exist_ok=True)
        body = bytes(range(256)) * (self.tool.HASH_CHUNK // 256 + 500)
        path.write_bytes(body)
        expected = hashlib.sha256(body).hexdigest()
        self.assertGreater(len(body), self.tool.HASH_CHUNK, 'The sample must span several chunks')
        self.assertEqual(self.tool.digest(path), expected)
        self.assertEqual(self.tool.digest(path), expected)
        self.assertEqual(self.tool.digest(path, cached=False), expected)
        path.write_bytes(body + b'appended row')
        self.assertNotEqual(self.tool.digest(path), expected)

    def test_missing_evidence_and_blank_summary_rejected(self):
        self.initialize()
        for summary, evidence in [(' ', []), ('Hypotheses', []), ('Hypotheses', ['missing.md'])]:
            with self.subTest(summary=summary, evidence=evidence), self.assertRaises(ValueError):
                self.handoff(summary=summary, evidence=evidence)

    def test_evidence_cannot_escape_project_even_through_symlink(self):
        self.initialize()
        outside = Path(self.temp.name) / 'outside.md'
        outside.write_text('private')
        (self.project / 'linked.md').symlink_to(outside)
        for value in ['../outside.md', str(outside), 'linked.md']:
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.handoff(evidence=[value])

    def test_unexpected_phase_jump_rejected(self):
        self.initialize()
        with self.assertRaises(ValueError):
            self.tool.transition_phase(ROOT, self.project, 'write', 'Skip phases', ['research-brief.md'])

    def prepare_execution(self):
        self.initialize()
        register_task(self.tool, self.project, 'run', activity='experiment', skill='graph-evaluation', role='experimenter')
        state = self.state()
        state.update(phase='design', mode='research')
        approval = self.evidence('reports/user-approval-v1.md')
        state['grant'] = {'evidence': {'path': approval,
                                       'sha256': self.tool.digest(self.project / approval)},
                          'services': ['sandbox'], 'operations': ['run'], 'scope': 'graph-study',
                          'max_runs': 10, 'expires_at': '2099-01-01T00:00:00Z'}
        state['evaluation'] = dict(primary_measure='macro F1', baseline='Matched graph baseline',
                                   validation_plan='Grouped train/validation/test split', uncertainty_plan='Five paired seeds')
        protocol = self.evidence('experiments/H1/protocol.md')
        state['protocol'] = {'path': protocol, 'sha256': self.tool.digest(self.project / protocol)}
        self.save(state)
        return state, protocol

    def execute_packet(self, protocol):
        return self.handoff(task_id='run', evidence=[protocol],
                            outputs=['experiments/H1/runs/run-001/analysis.md'])

    def test_execution_requires_research_mode(self):
        state, protocol = self.prepare_execution()
        state['mode'] = 'planning'
        self.save(state)
        with self.assertRaisesRegex(ValueError, 'research mode'):
            self.execute_packet(protocol)

    def test_execution_requires_all_evaluation_fields(self):
        state, protocol = self.prepare_execution()
        for key in state['evaluation']:
            changed = copy.deepcopy(state)
            changed['evaluation'][key] = None
            self.save(changed)
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.execute_packet(protocol)

    def test_protocol_hash_detects_changes(self):
        _, protocol = self.prepare_execution()
        (self.project / protocol).write_text('Changed after freezing')
        with self.assertRaises(ValueError):
            self.execute_packet(protocol)

    def test_valid_execution_packet(self):
        _, protocol = self.prepare_execution()
        self.assertEqual(self.execute_packet(protocol)['target_role']['id'], 'experimenter')

    def test_stopped_or_busy_project_cannot_handoff(self):
        self.initialize()
        original = self.state()
        busy = dict(original, active_tasks=['t1'])
        busy['tasks']['t1']['status'] = 'running'
        for changed in (dict(original, status='stopped'), busy):
            self.save(changed)
            with self.assertRaises(ValueError):
                self.handoff()

    def test_writing_requires_reviewed_evidence(self):
        self.initialize()
        register_task(self.tool, self.project, 'draft', activity='conclusions', skill='ml-paper-writing', role='writer')
        state = self.state()
        state['phase'] = 'synthesize'
        self.save(state)
        with self.assertRaises(ValueError):
            self.handoff(task_id='draft', outputs=['paper/draft.md'])

    def test_existing_outputs_are_not_reused(self):
        self.initialize()
        self.evidence('hypotheses/candidates.md')
        with self.assertRaises(ValueError):
            self.handoff()

    def test_same_phase_can_use_another_explicit_skill(self):
        self.initialize()
        state = self.state()
        state['phase'] = 'ideation'
        self.save(state)
        register_task(self.tool, self.project, 'reformulate', skill='creative-thinking-for-research')
        packet = self.handoff(task_id='reformulate')
        self.assertEqual(packet['project_phase'], 'ideation')
        self.assertEqual(packet['skill']['name'], 'creative-thinking-for-research')

    def test_cli_validation(self):
        with contextlib.redirect_stdout(io.StringIO()) as captured:
            self.assertEqual(self.tool.main(['validate']), 0)
        self.assertIn('OK', captured.getvalue())


if __name__ == '__main__':
    unittest.main()
