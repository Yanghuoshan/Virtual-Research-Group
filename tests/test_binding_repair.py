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
        self.tool.authorize(ROOT, self.project, mode='research', reason='Bounded retrieval',
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
