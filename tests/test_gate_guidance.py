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
        # authorize resolves the cited approval artifact before it validates the
        # timestamp format, so the artifact has to exist for the ISO check to run.
        approval = self.project / 'reports/user-approval-v1.md'
        approval.parent.mkdir(parents=True, exist_ok=True)
        approval.write_text('User-approved scope: study; sandbox run; up to three attempts.')
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
