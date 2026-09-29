import contextlib
import importlib.util
import io
import json
from pathlib import Path
import re
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('flat_research', ROOT / 'scripts/research.py')
TOOL = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(TOOL)


class FlatArchitectureTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=ROOT)
        self.addCleanup(self.temp.cleanup)
        self.project = Path(self.temp.name) / 'project'

    def initialize(self, role='strategist'):
        TOOL.initialize(ROOT, self.project, 'Study graph classification')
        TOOL.create_task(ROOT, self.project, 't1', 'Compare explanations', activity='analysis',
                         skill='brainstorming-research-ideas', role=role, acceptance='Every hypothesis has a falsifier')

    def evidence(self, name='literature/evidence.md', text='Sourced evidence'):
        path = self.project / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')
        return {'path': name, 'sha256': TOOL.digest(path)}

    def state(self):
        return json.loads((self.project / 'research-state.json').read_text())

    def save(self, state):
        (self.project / 'research-state.json').write_text(json.dumps(state))

    def packet(self, **changes):
        options = dict(model='current', outputs=['hypotheses/candidates.md'])
        options.update(changes)
        return TOOL.handoff(ROOT, self.project, 't1', 'Compare plausible explanations',
                            ['research-brief.md'], **options)

    def test_intermediate_routing_layers_are_removed(self):
        for name in ('domains', 'core', 'adapters', 'catalog.json', 'library', 'extensions'):
            with self.subTest(name=name):
                self.assertFalse((ROOT / name).exists(), f'Redundant layer remains: {name}')

    def test_core_defines_workspace_and_decision_authority(self):
        text = (ROOT / 'SKILL.md').read_text()
        for fragment in ('## Research Workspace', '## Core Decision Authority',
                         '## Direct Skill Selection', '{hypothesis-id}', '{run-id}',
                         'protocol.md', 'results/', 'analysis.md', 'Only the core'):
            self.assertIn(fragment, text)

    def test_entry_point_stays_within_reading_budget(self):
        notes = TOOL.budget_notes(ROOT)
        self.assertEqual(notes, [], 'Entry documents exceeded the progressive-disclosure budget')
        skill = max((p for p in (ROOT / 'skills').glob('*/SKILL.md')), key=lambda p: p.stat().st_size)
        self.assertLess(skill.stat().st_size, 20000, f'Specialist entry too large: {skill.parent.name}')

    def test_skills_are_directly_discoverable(self):
        self.assertTrue(callable(getattr(TOOL, 'discover_skills', None)), 'Direct skill discovery is missing')
        skills = TOOL.discover_skills(ROOT)
        self.assertIn('graph-evaluation', skills)
        for name, entry in skills.items():
            self.assertEqual(entry['path'], f'skills/{name}/SKILL.md')
            self.assertNotIn('optional_capabilities', entry)

    def test_each_specialist_has_vertical_contract(self):
        entries = list((ROOT / 'skills').glob('*/SKILL.md'))
        self.assertGreaterEqual(len(entries), 12)
        for path in entries:
            text = path.read_text()
            with self.subTest(skill=path.parent.name):
                for section in ('## Inputs', '## Method', '## Outputs', '## Checks', '## Boundary'):
                    self.assertIn(section, text)
                self.assertIn('Return to the core', text)
                self.assertIn('Do not dispatch', text)
                self.assertNotRegex(text, r'\]\(\.\./')

    def test_discovery_requires_no_registration(self):
        self.assertTrue(callable(getattr(TOOL, 'discover_skills', None)))
        bundle = Path(self.temp.name) / 'bundle'
        entry = bundle / 'skills/example/SKILL.md'
        entry.parent.mkdir(parents=True)
        entry.write_text('---\nname: example\ndescription: Use when examining examples.\n---\n# Example\n')
        self.assertIn('example', TOOL.discover_skills(bundle))

    def test_initialize_needs_no_domain_or_model_configuration(self):
        self.initialize()
        self.assertEqual({p.name for p in self.project.iterdir()},
                         {'research-state.json', 'research-brief.md', 'research-log.md', 'findings.md'})
        state = self.state()
        self.assertEqual(state['schema_version'], 3)
        self.assertEqual(state['mode'], 'planning')
        self.assertNotIn('domain', state)
        self.assertFalse(any(state['authorization'].values()))

    def test_explicit_single_skill_role_model_not_inferred(self):
        self.initialize(role='critical-reader')
        before = (self.project / 'research-state.json').read_bytes()
        packet = self.packet(model='provider/selected-model')
        self.assertEqual(packet['skill']['name'], 'brainstorming-research-ideas')
        self.assertEqual(packet['target_role'], 'critical-reader')
        self.assertEqual(packet['requested_model'], 'provider/selected-model')
        self.assertEqual(packet['dispatch_status'], 'not_dispatched')
        self.assertNotIn('knowledge_sources', packet)
        self.assertNotIn('domain_profile', packet)
        self.assertEqual(before, (self.project / 'research-state.json').read_bytes())

    def test_outputs_cannot_touch_global_state(self):
        self.initialize()
        for path in ('research-state.json', 'findings.md', 'research-log.md', 'research-brief.md', '.', 'handoffs/', '../escape'):
            with self.subTest(path=path), self.assertRaises(ValueError):
                self.packet(outputs=[path])

    def test_explicit_task_contract_is_required(self):
        self.initialize()
        for change in ({'model': ''}, {'outputs': []}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.packet(**change)
        for change in ({'role': ''}, {'skill': '../escape'}, {'acceptance': ''}):
            options = dict(activity='analysis', skill='brainstorming-research-ideas', role='strategist', acceptance='Falsifier')
            options.update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                TOOL.create_task(ROOT, self.project, 't2', 'Compare', **options)

    def test_outputs_cannot_overwrite_inputs(self):
        self.initialize()
        with self.assertRaises(ValueError):
            self.packet(outputs=['research-brief.md'])

    def test_skill_selection_cannot_escape_flat_directory(self):
        self.assertTrue(callable(getattr(TOOL, 'discover_skills', None)))
        bundle = Path(self.temp.name) / 'bundle'
        (bundle / 'skills').mkdir(parents=True)
        external = Path(self.temp.name) / 'external'
        external.mkdir()
        (external / 'SKILL.md').write_text('---\nname: linked\ndescription: Use when testing.\n---\n')
        (bundle / 'skills/linked').symlink_to(external)
        with self.assertRaises(ValueError):
            TOOL.discover_skills(bundle)

    def test_frozen_protocol_and_authorization_gate_remain(self):
        self.initialize()
        TOOL.create_task(ROOT, self.project, 'run', 'Evaluate frozen outputs', activity='experiment',
                         skill='graph-evaluation', role='evaluator', acceptance='Report per-seed metrics')
        protocol = self.evidence('experiments/H1/protocol.md')
        state = self.state()
        state.update(phase='design', mode='research', protocol=protocol)
        state['evaluation'] = dict(primary_measure='Macro F1', baseline='Graph kernel',
                                   validation_plan='Grouped graph splits', uncertainty_plan='Five seeds')
        self.save(state)
        args = dict(model='current', outputs=['experiments/H1/runs/run-001/results/'])
        with self.assertRaises(ValueError):
            TOOL.handoff(ROOT, self.project, 'run', 'Evaluate frozen outputs', [protocol['path']], **args)
        state['authorization']['experiments'] = True
        self.save(state)
        packet = TOOL.handoff(ROOT, self.project, 'run', 'Evaluate frozen outputs', [protocol['path']], **args)
        self.assertEqual(packet['skill']['name'], 'graph-evaluation')
        self.evidence(protocol['path'], 'Changed protocol')
        with self.assertRaises(ValueError):
            TOOL.handoff(ROOT, self.project, 'run', 'Evaluate frozen outputs', [protocol['path']], **args)

    def test_packet_rejects_legacy_state_explicitly(self):
        self.initialize()
        state = self.state()
        state['schema_version'] = 1
        self.save(state)
        with self.assertRaisesRegex(ValueError, 'schema|version|migration'):
            self.packet()

    def test_primary_docs_do_not_prescribe_old_routing(self):
        for path in [ROOT / 'SKILL.md', ROOT / 'README.md']:
            self.assertNotIn('--domain', path.read_text())
        text = (ROOT / 'scripts/research.py').read_text()
        for name in ('optional_capabilities', 'catalog.json', 'domain-profile.json', 'model-routing.json'):
            self.assertNotIn(name, text)

    def test_cli_requires_explicit_decisions(self):
        self.initialize()
        args = ['handoff', '--project', str(self.project), '--task', 't1', '--summary', 'Explore',
                '--evidence', 'research-brief.md', '--model', 'current', '--outputs', 'hypotheses/ideas.md']
        with contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(TOOL.main(args), 0)
        self.assertEqual(json.loads(output.getvalue())['skill']['name'], 'brainstorming-research-ideas')


if __name__ == '__main__':
    unittest.main()
