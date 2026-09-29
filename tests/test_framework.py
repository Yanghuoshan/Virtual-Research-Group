import contextlib
import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import re
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts/research.py'


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
        self.assertEqual(self.tool.validate(ROOT), [])

    def test_bundle_text_is_english(self):
        han = re.compile('[\u3400-\u9fff\uf900-\ufaff\U00020000-\U000323af]')
        violations = []
        for path in sorted(ROOT.rglob('*')):
            relative = path.relative_to(ROOT)
            if not path.is_file() or relative.parts[0] in ('projects', '.venv') or '__pycache__' in relative.parts:
                continue
            if path.is_relative_to(Path(self.temp.name)):
                continue
            try:
                text = path.read_text(encoding='utf-8')
            except UnicodeDecodeError:
                continue
            if path.suffix == '.json':
                text = json.dumps(json.loads(text), ensure_ascii=False)
            if han.search(text):
                violations.append(str(relative))
        self.assertEqual(violations, [], 'Non-English CJK text remains in the bundle')

    def test_generated_scaffolding_is_english_and_preserves_user_input(self):
        question = '\u56fe\u5206\u7c7b'
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
        register_task(self.tool, self.project, 'run', activity='experiment', skill='graph-evaluation', role='evaluator')
        state = self.state()
        state.update(phase='design', mode='research')
        state['authorization']['experiments'] = True
        state['evaluation'] = dict(primary_measure='macro F1', baseline='Matched graph baseline',
                                   validation_plan='Grouped train/validation/test split', uncertainty_plan='Five paired seeds')
        protocol = self.evidence('experiments/H1/protocol.md')
        state['protocol'] = {'path': protocol, 'sha256': self.tool.digest(self.project / protocol)}
        self.save(state)
        return state, protocol

    def execute_packet(self, protocol):
        return self.handoff(task_id='run', evidence=[protocol],
                            outputs=['experiments/H1/runs/run-001/analysis.md'])

    def test_execution_requires_authorization(self):
        state, protocol = self.prepare_execution()
        state['authorization']['experiments'] = False
        self.save(state)
        with self.assertRaises(ValueError):
            self.execute_packet(protocol)

    def test_planning_mode_blocks_execution(self):
        state, protocol = self.prepare_execution()
        state['mode'] = 'planning'
        self.save(state)
        with self.assertRaises(ValueError):
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
        self.assertEqual(self.execute_packet(protocol)['target_role'], 'evaluator')

    def test_paused_or_busy_project_cannot_handoff(self):
        self.initialize()
        original = self.state()
        busy = dict(original, active_task='t1')
        busy['tasks']['t1']['status'] = 'running'
        for changed in (dict(original, status='paused'), busy):
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
