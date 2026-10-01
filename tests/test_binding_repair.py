"""Hash bindings are visible and repairable instead of silent."""

import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from test_framework import ROOT, load_tool

# A goal dossier is admitted only when every field appears on exactly one populated line.
GOAL_DOSSIER = '\n'.join((
    '# Goal dossier',
    'Question: how sensitive is the graph baseline to the metric choice?',
    'Value: fewer conclusions that rest on a single metric',
    'Boundary: the supplied graph datasets',
    'Alternatives: a data shift or a metric bias',
    'Evidence: dataset inventory and paired run results',
    'Falsifier: no difference under a matched split',
    'Success: a held-out effect above the matched baseline',
    'Feasibility: supplied data and one bounded sandbox run',
    'Resources: one paired run per seed',
    'Stop: abandon the direction after two failed replications',
    'Unknown: baseline availability'))


class BindingRepairTests(unittest.TestCase):
    def setUp(self):
        self.tool = load_tool()
        self.temp = tempfile.TemporaryDirectory(dir=ROOT)
        self.addCleanup(self.temp.cleanup)
        self.project = Path(self.temp.name) / 'project'
        self.tool.initialize(ROOT, self.project, 'Investigate graph sensitivity')
        self.approval = self.write('reports/user-approval-v1.md', 'Approved bounded channel')
        self.tool.authorize(ROOT, self.project, mode='research', reason='Bounded retrieval',
                            evidence=[self.approval], services=['da-data'], operations=['search_content'],
                            scope='study', max_runs=3, expires_at='2099-01-01T00:00:00Z')

    def write(self, name, text):
        path = self.project / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        return name

    def state(self):
        return json.loads((self.project / 'research-state.json').read_text())

    def row_for(self, path):
        rows = [row for row in self.tool.binding_report(ROOT, self.project)['bindings']
                if row['path'] == path]
        self.assertEqual(len(rows), 1, f'Exactly one binding must point at {path}')
        return rows[0]

    def drift_details(self):
        """The detail text of every binding-drift anomaly watch reports right now."""
        return [problem.get('detail') for problem in self.tool.watch(ROOT, self.project, silence_hours=1e9)
                ['anomalies'] if problem['reason'] == 'binding-drift']

    def audit(self, name, subjects, claim, support):
        """An audit JSON under reviews/, filled in from the shipped template."""
        payload = json.loads((ROOT / 'templates' / 'evidence-audit.json').read_text())
        payload.update(reviewer='core', reviewed_at='2026-01-01T00:00:00+00:00',
                       summary='Audit binds the listed subjects at the recorded versions',
                       claims=[{'claim': claim, 'support': support}],
                       subjects=[{'path': subject, 'sha256': self.tool.digest(self.project / subject)}
                                 for subject in subjects])
        return self.write(name, json.dumps(payload, ensure_ascii=False, indent=2))

    def build_every_binding(self):
        """A project holding one binding of every kind, so a row that is never listed is visible."""
        protocol = self.write('experiments/H1/protocol.md', 'Frozen protocol for the paired runs')
        self.tool.set_protocol(ROOT, self.project, path=protocol, reason='Core froze the protocol')
        goal = self.write('hypotheses/goal-v1.md', GOAL_DOSSIER)
        self.tool.set_goal(ROOT, self.project, goal, 'Scope selected from the dossier')
        findings = self.write('findings.md', 'Bounded finding with its matching raw result')
        raw = self.write('experiments/H1/runs/run-001/results/metrics.json', '{"score": 0.7}')
        self.audit('reviews/evidence-audit.json', [findings, protocol, raw],
                   'The reported gain is bound to raw evidence', 'Run artifacts under experiments/')
        self.tool.set_audit(ROOT, self.project, kind='evidence', path='reviews/evidence-audit.json',
                            status='verified', reason='Audit binds findings, protocol and raw evidence')
        paper = self.write('paper/summary-v1.md', 'Bounded summary of the verified finding')
        self.audit('reviews/final-review.json', [findings, paper],
                   'The summary states the bounded result', 'Manuscript under paper/')
        self.tool.set_audit(ROOT, self.project, kind='final', path='reviews/final-review.json',
                            status='passed', reason='Final review binds findings and the summary')
        self.create('run')
        _, artifact = self.submit_version('run', 1, [findings])
        self.tool.update_task(ROOT, self.project, 'run', 'completed', 'Core accepted the analysis', [])
        self.write('reports/reflection-v1.json', json.dumps({
            'observation': 'The measured gain is below the target',
            'protocol_check': 'No deviation from the frozen protocol',
            'counterevidence': 'The matched baseline remains competitive',
            'alternatives': 'Attribute the gap to a data shift',
            'next_options': ['Replicate on an independent split'],
            'prediction': 'The gap disappears on an independent split',
            'decision': 'Replicate before drawing conclusions',
            'evidence': [{'path': artifact, 'sha256': self.tool.digest(self.project / artifact)}]}))
        self.tool.record_reflection(ROOT, self.project, 'run', 'reports/reflection-v1.json',
                                    'Review before selecting a follow-up')

    def create(self, task_id):
        return self.tool.create_task(ROOT, self.project, task_id, 'Analyze the supplied evidence',
                                     activity='analysis', skill='brainstorming-research-ideas',
                                     role='strategist', acceptance='Report the bounded comparison')

    def submit_version(self, task_id, version, evidence=None):
        """Assign one version of a task and submit its artifact; returns input and artifact paths."""
        source = self.write(f'hypotheses/{task_id}-input-v{version}.md',
                            f'Supplied evidence for pass {version}')
        artifact = f'reports/{task_id}-analysis-v{version}.md'
        self.tool.assign(ROOT, self.project, task_id, f'Pass {version}', evidence or [source],
                         model='current', outputs=[artifact], session_mode='current',
                         session_reason='Small task without independence')
        self.write(artifact, f'Bounded analysis from pass {version}')
        self.tool.update_task(ROOT, self.project, task_id, 'submitted', 'Executor stopped', [artifact],
                              executor_stopped=True)
        return source, artifact

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

    def test_bindings_report_lists_one_row_per_binding_kind(self):
        self.build_every_binding()
        report = self.tool.binding_report(ROOT, self.project)
        self.assertEqual(report['broken'], [], 'Every binding in the fixture must still hold')
        self.assertEqual({row['binding'] for row in report['bindings']},
                         {'grant evidence', 'protocol', 'goal dossier', 'evidence review', 'final review',
                          'run assignment input', 'run submitted artifact', 'reflection artifact'})

    def test_watch_stops_reporting_drift_once_the_task_is_finished(self):
        # Completion re-verifies the submission and the newest assignment input, so the
        # drift that survives a legal completion is the superseded input of an earlier pass.
        for status in ('completed', 'cancelled'):
            with self.subTest(status=status):
                task_id = f'finished-{status}'
                self.create(task_id)
                stale, _ = self.submit_version(task_id, 1)
                self.tool.update_task(ROOT, self.project, task_id, 'planned', 'Rework requested', [])
                self.submit_version(task_id, 2)
                self.write(stale, 'Corrected after the rework')
                detail = (f'{task_id} assignment input: {stale} '
                          'no longer matches its recorded hash')
                self.assertIn(detail, self.drift_details())
                self.tool.update_task(ROOT, self.project, task_id, status, 'Core closed the task', [])
                self.assertEqual(self.state()['tasks'][task_id]['status'], status,
                                 f'{status} must be a legal transition from submitted')
                self.assertFalse(self.row_for(stale)['holds'], 'The superseded input still drifts')
                self.assertNotIn(detail, self.drift_details())

    def test_a_deleted_bound_file_is_reported_as_missing(self):
        protocol = self.write('experiments/H1/protocol.md', 'Frozen protocol for the paired runs')
        self.tool.set_protocol(ROOT, self.project, path=protocol, reason='Core froze the protocol')
        (self.project / protocol).unlink()
        row = self.row_for(protocol)
        self.assertEqual(row['binding'], 'protocol')
        self.assertIsNone(row['current_sha256'])
        self.assertFalse(row['holds'])
        self.assertEqual(row['detail'], 'file is missing')
