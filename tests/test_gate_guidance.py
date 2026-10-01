"""Gate refusals carry the command that clears them, and malformed input names the expected shape."""

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

    def receipt(self, packet, session_id='host:gate'):
        return {'schema_version': 8, 'packet_id': packet['packet_id'], 'task_id': packet['task_id'],
                'source_revision': packet['source_revision'], 'accepted': True,
                'accepted_at': '2026-01-01T00:00:00+00:00', 'actual_role': packet['target_role']['id'],
                'actual_model': 'provider/model-a', 'actual_session_mode': packet['session']['mode'],
                'actual_session_id': session_id,
                'session_isolation_verified': packet['session']['mode'] == 'fresh',
                'session_notes': 'Host execution identity and history verified',
                'state_hash_checked': True, 'core_hash_checked': True, 'skill_hash_checked': True,
                'evidence_hashes_checked': True, 'packet_sha256': self.tool.packet_digest(packet)}

    def test_stopped_project_refusal_names_the_reactivation_command(self):
        self.tool.set_project_status(ROOT, self.project, status='stopped', reason='Planning only')
        with self.assertRaisesRegex(ValueError, 'project-status .* --to active') as raised:
            self.tool.create_task(ROOT, self.project, 't2', 'More work', activity='analysis',
                                  skill='brainstorming-research-ideas', role='strategist',
                                  acceptance='Bounded')
        self.assertIn('Next:', str(raised.exception))

    def test_tool_gate_refuses_a_task_without_an_active_assignment(self):
        # t1 is only planned here, so check_tool stops at the first gate.
        with self.assertRaisesRegex(ValueError, 'Tool access requires an active assignment') as raised:
            self.tool.check_tool(ROOT, self.project, task_id='t1', packet_id='ghost',
                                 server='da-data', operation='search', scope='study')
        self.assertIn('Next:', str(raised.exception))

    def test_tool_gate_refuses_a_packet_that_is_not_the_active_one(self):
        packet = self.tool.handoff(ROOT, self.project, 't1', 'Work the evidence', ['research-brief.md'],
                                   model='current', outputs=['hypotheses/t1-v1.md'])
        self.tool.accept_assignment(ROOT, self.project, packet, self.receipt(packet))
        # The task is running, so the same request now reaches the packet gate instead.
        with self.assertRaisesRegex(ValueError, 'Tool request does not match the active packet') as raised:
            self.tool.check_tool(ROOT, self.project, task_id='t1', packet_id='stale-packet',
                                 server='da-data', operation='search', scope='study')
        self.assertIn('Next:', str(raised.exception))

    def test_iso_timestamp_refusal_names_the_expected_shape(self):
        with self.assertRaisesRegex(ValueError, 'ISO 8601') as raised:
            self.tool.authorize(ROOT, self.project, mode='research', reason='Bounded',
                                evidence=['reports/user-approval-v1.md'], services=['sandbox'],
                                operations=['run'], scope='study', max_runs=3, expires_at='tomorrow')
        self.assertIn('2099-01-01T00:00:00Z', str(raised.exception))
