"""Parallel execution, blocker resolution, receipt timing, audits and extensions."""

import contextlib
import hashlib
import io
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from test_framework import ROOT, load_tool


def write_valid_skill(base, name, description='Use when bounded testing is needed.'):
    directory = base / name
    directory.mkdir(parents=True)
    (directory / 'SKILL.md').write_text(
        '---\n'
        f'name: {name}\n'
        f'description: {description}\n'
        '---\n'
        f'# {name}\n\n'
        '## Inputs\n\nSupplied material and output paths.\n\n'
        '## Method\n\nInspect and report within the assignment.\n\n'
        '## Outputs\n\nA report at the assigned path.\n\n'
        '## Checks\n\nNothing is fabricated; gaps are returned as blockers.\n\n'
        '## Boundary\n\nReturn to the core with the report. Do not dispatch other skills '
        'or agents, select models, or advance phases.\n')
    return directory


class AssignmentTests(unittest.TestCase):
    """Receipt timing, parallel scopes and blocker resolution through the real lifecycle."""

    def setUp(self):
        self.tool = load_tool()
        self.temp = tempfile.TemporaryDirectory(dir=ROOT)
        self.addCleanup(self.temp.cleanup)
        self.project = Path(self.temp.name) / 'project'
        self.tool.initialize(ROOT, self.project, 'Study graph sensitivity')

    def state(self):
        return json.loads((self.project / 'research-state.json').read_text())

    def create(self, task_id='t1', **changes):
        options = dict(activity='analysis', skill='brainstorming-research-ideas', role='strategist',
                       acceptance='Falsifier per hypothesis')
        options.update(changes)
        return self.tool.create_task(ROOT, self.project, task_id, 'Bounded work', **options)

    def packet(self, task_id='t1', **changes):
        options = dict(model='current', outputs=['hypotheses/out-v1.md'])
        options.update(changes)
        return self.tool.handoff(ROOT, self.project, task_id, 'Work from the brief',
                                 ['research-brief.md'], **options)

    def receipt(self, packet, session_id='host:r1', **changes):
        digest = hashlib.sha256(json.dumps(packet, sort_keys=True, ensure_ascii=False,
                                           separators=(',', ':'), allow_nan=False).encode('utf-8')).hexdigest()
        result = dict(schema_version=5, packet_id=packet['packet_id'], task_id=packet['task_id'],
                      source_revision=packet['source_revision'], packet_sha256=digest, accepted=True,
                      accepted_at='2026-01-01T00:00:00+00:00', actual_role=packet['target_role']['id'],
                      actual_model='provider/model-a', actual_session_mode=packet['session']['mode'],
                      actual_session_id=session_id,
                      session_isolation_verified=packet['session']['mode'] == 'fresh',
                      state_hash_checked=True, core_hash_checked=True,
                      skill_hash_checked=True, evidence_hashes_checked=True)
        result.update(changes)
        return result

    def accept(self, packet, **changes):
        return self.tool.accept_assignment(ROOT, self.project, packet, self.receipt(packet, **changes))

    def write(self, name, text='Artifact body'):
        path = self.project / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        return name

    def digest(self, name):
        return hashlib.sha256((self.project / name).read_bytes()).hexdigest()

    def audit_json(self, name, subjects, path, claims=None, reviewer='core'):
        payload = {'schema_version': 2, 'reviewer': reviewer,
                   'reviewed_at': '2026-01-01T00:00:00+00:00',
                   'summary': 'Schema-2 audit', 'subjects': subjects,
                   'claims': claims if claims is not None else
                   [{'claim': 'A verified claim', 'support': 'Primary artifacts'}]}
        return self.write(name, json.dumps(payload))

    def test_artifacts_written_before_acceptance_are_tolerated(self):
        # The documented loop is receipt-then-artifacts, but a host whose executor has
        # already produced output must not be rejected for it at accept time.
        self.create('t1')
        packet = self.packet()
        self.write('hypotheses/out-v1.md')
        self.accept(packet)
        self.assertEqual(self.state()['tasks']['t1']['status'], 'running')

    def test_non_iso_accepted_at_is_rejected(self):
        self.create('t1')
        packet = self.packet()
        for value in ('x', 'yesterday', '2026-01-01', None):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, 'ISO 8601'):
                self.accept(packet, accepted_at=value)

    def test_blocker_being_resolved_no_longer_freezes_the_project(self):
        self.tool.update_blockers(ROOT, self.project, add='Missing baseline', reason='Baseline not reproduced')
        # Creating the fixing task is possible while the blocker is open.
        task = self.create('t1', resolves=['Missing baseline'])
        self.assertEqual(task['resolves'], ['Missing baseline'])
        # It can be assigned and run.
        self.accept(self.packet())
        # An unrelated new task is fine while the fix is in flight.
        self.create('t2')
        # Completing the fixing task removes the blocker automatically.
        self.write('hypotheses/out-v1.md')
        self.tool.update_task(ROOT, self.project, 't1', 'submitted', 'Executor stopped',
                              ['hypotheses/out-v1.md'], executor_stopped=True)
        self.tool.update_task(ROOT, self.project, 't1', 'completed', 'Core accepted the reproduction', [])
        self.assertEqual(self.state()['blockers'], [])
        self.assertIn('auto_resolved', self.state()['history'][-1])

    def test_unresolved_blockers_still_stop_new_work(self):
        self.tool.update_blockers(ROOT, self.project, add='Data access denied', reason='No channel approved')
        with self.assertRaisesRegex(ValueError, 'blockers'):
            self.create('t1')
        with self.assertRaises(ValueError):
            self.packet('t1')
        self.tool.update_blockers(ROOT, self.project, resolve='Data access denied', reason='Channel approved')
        self.create('t1')
        self.accept(self.packet())
        self.assertEqual(self.state()['active_tasks'], ['t1'])

    def test_resolves_must_name_a_real_blocker(self):
        with self.assertRaisesRegex(ValueError, 'Unknown blocker'):
            self.create('t1', resolves=['Not a recorded blocker'])

    def test_compact_assignment_records(self):
        self.create('t1')
        packet = self.packet()
        (self.project / 'handoffs').mkdir()
        packet_file, receipt_file = 'handoffs/p1.json', 'handoffs/r1.json'
        (self.project / packet_file).write_text(json.dumps(packet))
        (self.project / receipt_file).write_text(json.dumps(self.receipt(packet)))
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(self.tool.main(['accept', '--project', str(self.project),
                                             '--packet', packet_file, '--receipt', receipt_file]), 0)
        assignment = self.state()['tasks']['t1']['assignments'][0]
        self.assertIn('packet_id', assignment)
        self.assertIn('allowed_outputs', assignment)
        self.assertEqual(assignment['packet_file'], packet_file)
        # The full packet text never enters the state file.
        self.assertNotIn('One skill assignment only', (self.project / 'research-state.json').read_text())

    def test_status_board_renders_the_project(self):
        self.create('t1')
        self.accept(self.packet())
        with contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(self.tool.main(['status', '--project', str(self.project)]), 0)
        board = output.getvalue()
        for fragment in ('Research Status', 'Phase', 'Active tasks', '## Tasks', 't1', '## Recent Decisions'):
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, board)

    def test_survey_project_completes_without_protocol(self):
        self.write('findings.md', 'Verified survey findings with literature evidence')
        self.write('literature/screening-ledger.md', 'Ledger: 40 identified, 31 included')
        self.write('literature/evidence-table.md', 'Evidence table with locators')
        subjects = [{'path': name, 'sha256': self.digest(name)}
                    for name in ('findings.md', 'literature/evidence-table.md', 'literature/screening-ledger.md')]
        self.audit_json('reviews/evidence-audit.json', subjects, 'reviews/evidence-audit.json')
        self.tool.set_audit(ROOT, self.project, kind='evidence', path='reviews/evidence-audit.json',
                            status='verified', reason='Audit binds findings and literature evidence')
        # No protocol was ever frozen; conclusions must still be assignable.
        self.create('draft', activity='conclusions', skill='survey-writing', role='writer',
                    acceptance='Survey states only ledger-supported claims')
        packet = self.tool.handoff(ROOT, self.project, 'draft', 'Write from verified literature',
                                   ['reviews/evidence-audit.json'], model='current', outputs=['paper/survey-v1.md'])
        self.assertEqual(packet['skill']['name'], 'survey-writing')
        self.accept(packet)
        self.write('paper/survey-v1.md')
        self.tool.update_task(ROOT, self.project, 'draft', 'submitted', 'Executor stopped',
                              ['paper/survey-v1.md'], executor_stopped=True)
        self.tool.update_task(ROOT, self.project, 'draft', 'completed', 'Core accepted the survey', [])
        # Final review binds findings and a reports/ primary artifact.
        paper = {'path': 'paper/survey-v1.md', 'sha256': self.digest('paper/survey-v1.md')}
        report = {'path': 'reports/survey-summary.md', 'sha256': self.digest(self.write('reports/survey-summary.md'))}
        findings = {'path': 'findings.md', 'sha256': self.digest('findings.md')}
        self.audit_json('reviews/final.json', [findings, paper, report], 'reviews/final.json',
                        claims=[{'claim': 'The survey states bounded claims', 'support': 'Ledger counts'}])
        self.tool.set_audit(ROOT, self.project, kind='final', path='reviews/final.json',
                             status='passed', reason='Final review binds findings, paper and report')
        state = self.state()
        state['phase'] = 'review'
        (self.project / 'research-state.json').write_text(json.dumps(state))
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(self.tool.main(['phase', '--project', str(self.project), '--to', 'complete',
                                             '--reason', 'Survey closed', '--evidence', 'reviews/final.json']), 0)
        self.assertEqual(self.state()['phase'], 'complete')

    def test_audit_schema_two_requires_claims_and_reviewer(self):
        self.write('findings.md', 'Findings')
        self.write('experiments/H1/runs/run-001/results/metrics.json', '{"value": 0.6}')
        subjects = [{'path': name, 'sha256': self.digest(name)}
                    for name in ('findings.md', 'experiments/H1/runs/run-001/results/metrics.json')]
        # Missing claims entirely.
        self.audit_json('reviews/no-claims.json', subjects, 'reviews/no-claims.json', claims=[])
        with self.assertRaisesRegex(ValueError, 'claims'):
            self.tool.set_audit(ROOT, self.project, kind='evidence', path='reviews/no-claims.json',
                                 status='verified', reason='Try to record')
        # Missing reviewer.
        self.audit_json('reviews/no-reviewer.json', subjects, 'reviews/no-reviewer.json', reviewer=None)
        with self.assertRaisesRegex(ValueError, 'reviewer'):
            self.tool.set_audit(ROOT, self.project, kind='evidence', path='reviews/no-reviewer.json',
                                 status='verified', reason='Try to record')
        # Bad reviewed_at.
        payload_path = self.audit_json('reviews/bad-time.json', subjects, 'reviews/bad-time.json')
        data = json.loads((self.project / payload_path).read_text())
        data['reviewed_at'] = 'not a timestamp'
        (self.project / payload_path).write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, 'reviewed_at'):
            self.tool.set_audit(ROOT, self.project, kind='evidence', path='reviews/bad-time.json',
                                 status='verified', reason='Try to record')


class ExtensionTests(unittest.TestCase):
    """External skills load tolerantly and never break the bundle."""

    def setUp(self):
        self.tool = load_tool()
        self.temp = tempfile.TemporaryDirectory(dir=ROOT)
        self.addCleanup(self.temp.cleanup)
        self.bundle = Path(self.temp.name) / 'bundle'
        self.bundle.mkdir()
        shutil.copy(ROOT / 'SKILL.md', self.bundle / 'SKILL.md')
        (self.bundle / 'references').mkdir()
        shutil.copy(ROOT / 'references' / 'role-guidance.md', self.bundle / 'references' / 'role-guidance.md')
        self.extensions = self.bundle / 'extensions'
        self.extensions.mkdir()
        (self.extensions / 'README.md').write_text('usage note')
        # A minimal built-in baseline so shadowing and resolution behave like the real bundle.
        write_valid_skill(self.bundle / 'skills', 'graph-evaluation')
        self.project = Path(self.temp.name) / 'project'
        self.tool.initialize(ROOT, self.project, 'Use an extension skill')

    def test_valid_extension_is_discovered_and_usable(self):
        write_valid_skill(self.extensions, 'domain-tool')
        entries, warnings = self.tool.discover_extensions(self.bundle)
        self.assertEqual(entries['domain-tool']['path'], 'extensions/domain-tool/SKILL.md')
        self.assertEqual(warnings, [])
        # It is selectable by name exactly like a built-in entry.
        task = self.tool.create_task(self.bundle, self.project, 't1', 'Bounded work',
                                     activity='analysis', skill='domain-tool', role='strategist',
                                     acceptance='Report the scoped findings')
        self.assertEqual(task['skill'], 'domain-tool')
        packet = self.tool.handoff(self.bundle, self.project, 't1', 'Use the extension',
                                   ['research-brief.md'], model='current', outputs=['reports/ext-v1.md'])
        self.assertEqual(packet['skill']['name'], 'domain-tool')
        self.assertTrue(packet['skill']['path'].startswith('extensions/'))

    def test_broken_extension_degrades_to_a_warning(self):
        (self.extensions / 'broken').mkdir()
        (self.extensions / 'broken' / 'SKILL.md').write_text('---\nname: broken\n---\n# No sections')
        (self.extensions / 'not-a-dir.md').write_text('stray file')
        entries, warnings = self.tool.discover_extensions(self.bundle)
        self.assertNotIn('broken', entries)
        self.assertTrue(any('extensions/broken' in warning for warning in warnings), warnings)
        self.assertTrue(any('not-a-dir' in warning for warning in warnings), warnings)
        # Selecting a broken extension fails loudly, it never impersonates another skill.
        with self.assertRaisesRegex(ValueError, 'broken'):
            self.tool.create_task(self.bundle, self.project, 't1', 'Bounded work',
                                   activity='analysis', skill='broken', role='strategist',
                                   acceptance='Report')

    def test_built_in_shadows_extension_of_the_same_name(self):
        write_valid_skill(self.extensions, 'graph-evaluation')
        entries, warnings = self.tool.discover_extensions(self.bundle)
        self.assertNotIn('graph-evaluation', entries)
        self.assertTrue(any('shadowed' in warning for warning in warnings), warnings)
        selected = self.tool.resolve_skill(self.bundle, 'graph-evaluation')
        self.assertEqual(selected['path'], 'skills/graph-evaluation/SKILL.md')

    def test_missing_extensions_directory_is_normal(self):
        empty = self.bundle / 'only-bundle'
        empty.mkdir()
        shutil.copy(ROOT / 'SKILL.md', empty / 'SKILL.md')
        entries, warnings = self.tool.discover_extensions(empty)
        self.assertEqual((entries, warnings), ({}, []))


if __name__ == '__main__':
    unittest.main()
