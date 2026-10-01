"""Gate refusals carry the command that clears them, and malformed input names the expected shape."""

from pathlib import Path
import tempfile
import unittest

from test_framework import ROOT, load_tool

# Repair steps may name commands that are not registered yet: `next` (task
# sequencing) and `amend` (grant and channel revision) arrive in later tasks.
PENDING_COMMANDS = {'next', 'amend'}


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

    def create(self, task_id='t1'):
        return self.tool.create_task(ROOT, self.project, task_id, 'Compare explanations', activity='analysis',
                                     skill='brainstorming-research-ideas', role='strategist',
                                     acceptance='Each explanation has a falsifier')

    def handoff(self, task_id='t1'):
        return self.tool.handoff(ROOT, self.project, task_id, 'Work the evidence', ['research-brief.md'],
                                 model='current', outputs=['hypotheses/t1-v1.md'])

    def check(self, scope='study', packet_id='ghost', server='da-data', operation='search_content'):
        return self.tool.check_tool(ROOT, self.project, task_id='t1', packet_id=packet_id, server=server,
                                    operation=operation, scope=scope)

    def authorize(self, max_runs=3):
        return self.tool.authorize(ROOT, self.project, mode='research', reason='Bounded channel',
                                   evidence=['reports/user-approval-v1.md'], services=['da-data'],
                                   operations=['search_content'], scope='study', max_runs=max_runs,
                                   expires_at='2099-01-01T00:00:00Z')

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

    def test_a_refusal_names_a_repair_only_when_the_gate_has_one(self):
        refusal = self.tool.Refusal('Project is stopped')
        self.assertIsInstance(refusal, ValueError)
        self.assertEqual(str(refusal), 'Project is stopped')
        self.assertNotIn('Next:', str(refusal))
        self.assertEqual(refusal.next_steps, [])
        self.assertIsNone(self.tool.refuse(True, 'Project is stopped'))
        # A malformed argument is not a gate: it names the expected shape and must
        # not promise a repair that does not exist.
        with self.assertRaisesRegex(ValueError, 'ISO 8601') as raised:
            self.tool.iso_timestamp('tomorrow', 'Grant expiry')
        self.assertNotIn('Next:', str(raised.exception))
        self.assertIn('2099-01-01T00:00:00Z', str(raised.exception))

    def steps(self, call):
        """The repair commands one refusal carries, each stripped of its sentence stop."""
        with self.assertRaises(ValueError) as raised:
            call()
        text = str(raised.exception)
        self.assertIn('Next:', text, f'No repair offered: {text}')
        return [step.rstrip('.') for step in text.split(' Next: ')[1:]]

    def test_every_repair_step_names_a_real_command_and_real_flags(self):
        commands = {name: dict(options) for name, _, options in self.tool.CLI}
        steps = []
        # A stopped project: every gate that opens a project now names the reactivation.
        self.tool.set_project_status(ROOT, self.project, status='stopped', reason='Planning only')
        steps += self.steps(lambda: self.create('t2'))
        steps += self.steps(lambda: self.handoff())
        steps += self.steps(lambda: self.tool.accept_assignment(ROOT, self.project, {}, {}))
        steps += self.steps(lambda: self.tool.authorize(ROOT, self.project, mode='research', reason='Bounded',
                                                        evidence=[], services=[], operations=[], scope='study',
                                                        max_runs=3, expires_at='tomorrow'))
        self.tool.set_project_status(ROOT, self.project, status='active', reason='Planning resumed')
        # A planned task: check_tool stops at the assignment gate.
        steps += self.steps(lambda: self.check())
        # A granted, running task: the packet, grant, scope and channel gates.
        self.authorize()
        packet = self.handoff()
        self.tool.accept_assignment(ROOT, self.project, packet, self.receipt(packet))
        steps += self.steps(lambda: self.check())
        steps += self.steps(lambda: self.handoff())
        steps += self.steps(lambda: self.check(scope='study', packet_id=packet['packet_id']))
        steps += self.steps(lambda: self.check(scope='outside-the-grant', packet_id=packet['packet_id']))
        self.authorize(max_runs=5)
        steps += self.steps(lambda: self.check(scope='study', packet_id=packet['packet_id']))
        for step in steps:
            name = step.split()[0]
            if name in PENDING_COMMANDS:
                continue
            with self.subTest(step=step):
                self.assertIn(name, commands, f'{name} is not a registered command')
                for flag in [word for word in step.split() if word.startswith('--')]:
                    self.assertIn(flag[2:], commands[name], f'{name} has no {flag}')
