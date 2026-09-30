import json
import os
from pathlib import Path
import tempfile
import unittest

from test_framework import ROOT, load_tool


class BriefWatchTests(unittest.TestCase):
    def setUp(self):
        self.tool = load_tool()
        self.temp = tempfile.TemporaryDirectory(dir=ROOT)
        self.addCleanup(self.temp.cleanup)
        self.project = Path(self.temp.name) / 'project'
        self.tool.initialize(ROOT, self.project, 'Watch the loop')

    def state(self):
        return json.loads((self.project / 'research-state.json').read_text())

    def save(self, state):
        (self.project / 'research-state.json').write_text(json.dumps(state))

    def anomalies(self, **changes):
        return {problem['reason'] for problem in self.tool.watch(ROOT, self.project, **changes)['anomalies']}

    def age_file(self, path, hours):
        old = os.stat(path).st_mtime - hours * 3600
        os.utime(path, (old, old))

    def create(self, task_id='t1'):
        return self.tool.create_task(ROOT, self.project, task_id, 'Compare explanations', activity='analysis',
                                     skill='brainstorming-research-ideas', role='strategist',
                                     acceptance='Each explanation has a falsifier')

    def test_brief_command_rewrites_the_mechanical_block(self):
        self.create()
        result = self.tool.write_brief(ROOT, self.project, note='Draft candidates next')
        self.assertEqual(result['brief'], 'rewritten')
        text = (self.project / 'research-log.md').read_text()
        block = text.split('<!-- brief:start -->', 1)[1].split('<!-- brief:end -->', 1)[0]
        self.assertIn('- **Phase:** scope', block)
        self.assertIn('Draft candidates next', block)
        # The narrative log below the block is untouched.
        self.assertIn('## Decision Narrative', text.split('<!-- brief:end -->', 1)[1])

    def test_brief_command_adds_the_block_to_a_pre_brief_log(self):
        (self.project / 'research-log.md').write_text('# Research Log\n\nOld narrative.\n')
        self.tool.write_brief(ROOT, self.project, note='Added the block')
        text = (self.project / 'research-log.md').read_text()
        self.assertIn('<!-- brief:start -->', text)
        self.assertIn('Old narrative.', text)

    def test_watch_reports_brief_drift_until_the_brief_is_written(self):
        self.assertIn('brief-drift', self.anomalies(silence_hours=1e9))
        self.tool.write_brief(ROOT, self.project, note='Planning')
        self.assertNotIn('brief-drift', self.anomalies(silence_hours=1e9))

    def test_watch_reports_receipt_stalls_only_for_unaccepted_packets(self):
        handoffs = self.project / 'handoffs'
        handoffs.mkdir()
        packet = handoffs / 't1-request-abc12345.json'
        packet.write_text(json.dumps({'packet_id': 'ghost'}))
        self.age_file(packet, 7)
        self.assertIn('receipt-stall', self.anomalies(silence_hours=1e9))
        state = self.state()
        state['history'].append({'action': 'assignment-accepted', 'packet_id': 'ghost',
                                 'revision': 1, 'at': '2026-01-01T00:00:00+00:00'})
        self.save(state)
        self.assertNotIn('receipt-stall', self.anomalies(silence_hours=1e9))

    def test_watch_reports_aged_blockers(self):
        self.tool.update_blockers(ROOT, self.project, add='Waiting on external data', reason='Blocked')
        state = self.state()
        state['blockers'][0]['opened_at'] = '2026-01-01T00:00:00+00:00'
        self.save(state)
        self.assertIn('blocker-age', self.anomalies())

    def test_watch_reports_project_silence(self):
        state = self.state()
        state['history'].append({'action': 'task-created', 'revision': 1, 'at': '2026-01-01T00:00:00+00:00'})
        self.save(state)
        self.assertIn('project-silence', self.anomalies())

    def test_watch_still_reports_silent_running_tasks(self):
        self.create()
        self.tool.assign(ROOT, self.project, 't1', 'Analyze the evidence', ['research-brief.md'],
                         model='current', outputs=['hypotheses/t1-v1.md'],
                         session_mode='current', session_reason='Small task without independence')
        state = self.state()
        for event in state['history']:
            event['at'] = '2026-01-01T00:00:00+00:00'
        self.save(state)
        self.assertIn('silent-running-task', self.anomalies(silence_hours=1e9, receipt_hours=1e9,
                                                            blocker_hours=1e9, hours=1e-6))

    def test_watch_accepts_a_clean_project_without_anomalies(self):
        self.create()
        self.tool.assign(ROOT, self.project, 't1', 'Analyze the evidence', ['research-brief.md'],
                         model='current', outputs=['hypotheses/t1-v1.md'],
                         session_mode='current', session_reason='Small task without independence')
        self.tool.write_brief(ROOT, self.project, note='Executing the small task')
        self.assertEqual(self.anomalies(silence_hours=1e9), set())


if __name__ == '__main__':
    unittest.main()
