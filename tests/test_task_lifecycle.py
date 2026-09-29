import contextlib
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest

from test_framework import ROOT, load_tool


class TaskLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.tool = load_tool()
        self.temp = tempfile.TemporaryDirectory(dir=ROOT)
        self.addCleanup(self.temp.cleanup)
        self.project = Path(self.temp.name) / 'project'
        self.tool.initialize(ROOT, self.project, 'Investigate graph sensitivity')

    def state(self):
        return json.loads((self.project / 'research-state.json').read_text())

    def save(self, state):
        (self.project / 'research-state.json').write_text(json.dumps(state))

    def create(self, task_id='t1', **changes):
        self.assertTrue(callable(getattr(self.tool, 'create_task', None)), 'Stable task creation is missing')
        options = dict(activity='analysis', skill='brainstorming-research-ideas', role='strategist',
                       acceptance='Each explanation has a falsifier', independent_review=False)
        options.update(changes)
        return self.tool.create_task(ROOT, self.project, task_id, 'Compare explanations', **options)

    def packet(self, task_id='t1', **changes):
        options = dict(model='current', outputs=['hypotheses/t1-v1.md'])
        options.update(changes)
        return self.tool.handoff(ROOT, self.project, task_id, 'Work from the current evidence',
                                 ['research-brief.md'], **options)

    def receipt(self, packet, session_id='host:s1', **changes):
        result = dict(schema_version=3, packet_id=packet['packet_id'], task_id=packet['task_id'],
                      source_revision=packet['source_revision'], accepted=True,
                      actual_role=packet['target_role'], actual_model='provider/model-a',
                      actual_session_mode=packet['session']['mode'], actual_session_id=session_id,
                      session_isolation_verified=packet['session']['mode'] == 'fresh',
                      session_notes='Host execution identity and history verified',
                      state_hash_checked=True, core_hash_checked=True, skill_hash_checked=True,
                      evidence_hashes_checked=True)
        result['packet_sha256'] = hashlib.sha256(json.dumps(packet, sort_keys=True, ensure_ascii=False,
                                                          separators=(',', ':'), allow_nan=False).encode('utf-8')).hexdigest()
        result.update(changes)
        return result

    def accept(self, packet, **changes):
        return self.tool.accept_assignment(ROOT, self.project, packet, self.receipt(packet, **changes))

    def output(self, path='hypotheses/t1-v1.md'):
        target = self.project / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text('Mechanism, supporting evidence, alternative and falsifier')
        return path

    def update(self, status, task_id='t1', evidence=None, **changes):
        return self.tool.update_task(ROOT, self.project, task_id, status, 'Core checked the task state',
                                     evidence or [], **changes)

    def test_core_separates_phase_task_and_session(self):
        text = (ROOT / 'SKILL.md').read_text()
        for phrase in ('## Phase, Task, and Session', 'task_id', 'packet_id', '## Task Lifecycle',
                       'scope', 'ideation', 'Exit criteria', 'Session changes do not change task identity'):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)

    def test_multiple_scope_and_ideation_tasks_do_not_advance_phase(self):
        self.create('t1')
        self.create('t2')
        self.assertEqual(self.state()['phase'], 'scope')
        self.assertEqual(set(self.state()['tasks']), {'t1', 't2'})
        self.tool.transition_phase(ROOT, self.project, 'ideation', 'Scope is sufficiently defined', ['research-brief.md'])
        self.create('t3')
        self.create('t4')
        self.assertEqual(self.state()['phase'], 'ideation')
        self.assertEqual(len(self.state()['tasks']), 4)

    def test_duplicate_task_id_cannot_replace_contract(self):
        self.create()
        before = (self.project / 'research-state.json').read_bytes()
        with self.assertRaises(ValueError):
            self.create(activity='experiment')
        self.assertEqual(before, (self.project / 'research-state.json').read_bytes())

    def test_task_creation_requires_explicit_activity(self):
        self.create()
        for activity in ('scope', 'write', '', None):
            with self.subTest(activity=activity), self.assertRaises(ValueError):
                self.create('t2', activity=activity)

    def test_packet_has_stable_task_id_not_target_phase(self):
        self.create()
        first, second = self.packet(), self.packet()
        self.assertEqual(first['task_id'], second['task_id'])
        self.assertNotEqual(first['packet_id'], second['packet_id'])
        self.assertEqual(first['project_phase'], 'scope')
        self.assertNotIn('to_phase', first)
        self.assertNotIn('from_phase', first)
        self.assertEqual(self.state()['tasks']['t1']['status'], 'planned')

    def test_experiments_require_authorization_even_in_scope(self):
        self.create(activity='experiment')
        with self.assertRaisesRegex(ValueError, 'authorization'):
            self.packet()

    def test_conclusions_require_audit_even_in_ideation(self):
        self.create(activity='conclusions')
        state = self.state()
        state['phase'] = 'ideation'
        self.save(state)
        with self.assertRaisesRegex(ValueError, 'Verified findings'):
            self.packet()

    def test_analysis_tasks_allowed_in_execute_and_write_without_result_claims(self):
        self.create()
        for phase in ('execute', 'write'):
            state = self.state()
            state['phase'] = phase
            self.save(state)
            self.assertEqual(self.packet()['activity'], 'analysis')

    def test_assignment_acceptance_does_not_advance_phase(self):
        self.create()
        self.accept(self.packet())
        state = self.state()
        self.assertEqual(state['phase'], 'scope')
        self.assertEqual(state['active_task'], 't1')
        self.assertEqual(state['tasks']['t1']['status'], 'running')

    def test_same_task_can_continue_in_new_session_and_model(self):
        self.create()
        packet = self.packet()
        self.accept(packet)
        with self.assertRaises(ValueError):
            self.packet()
        self.update('blocked', executor_stopped=True)
        self.update('planned')
        next_packet = self.packet(outputs=['hypotheses/t1-v2.md'], model='provider/model-b')
        self.accept(next_packet, session_id='host:s2', actual_model='provider/model-b')
        state = self.state()
        self.assertEqual(state['active_task'], 't1')
        self.assertEqual(state['phase'], 'scope')
        self.assertEqual(len(state['tasks']['t1']['assignments']), 2)

    def test_running_task_cannot_be_replaced_without_stopping_executor(self):
        self.create()
        self.accept(self.packet())
        with self.assertRaises(ValueError):
            self.update('blocked')
        with self.assertRaises(ValueError):
            self.update('planned')
        self.assertEqual(self.state()['active_task'], 't1')

    def test_two_tasks_cannot_run_at_once(self):
        self.create('t1')
        self.create('t2')
        self.accept(self.packet())
        with self.assertRaises(ValueError):
            self.packet('t2')

    def test_submitted_is_not_completed_or_phase_complete(self):
        self.create()
        self.accept(self.packet())
        output = self.output()
        self.update('submitted', evidence=[output], executor_stopped=True)
        self.assertEqual(self.state()['tasks']['t1']['status'], 'submitted')
        self.assertEqual(self.state()['phase'], 'scope')
        self.update('completed')
        self.assertEqual(self.state()['tasks']['t1']['status'], 'completed')
        self.assertEqual(self.state()['phase'], 'scope')
        with self.assertRaises(ValueError):
            self.packet()

    def test_completion_rechecks_submitted_artifacts(self):
        self.create()
        self.accept(self.packet())
        output = self.output()
        self.update('submitted', evidence=[output], executor_stopped=True)
        (self.project / output).write_text('Changed after submission')
        with self.assertRaisesRegex(ValueError, 'hash mismatch'):
            self.update('completed')

    def test_submission_cannot_use_unassigned_output(self):
        self.create()
        self.accept(self.packet())
        output = self.output('reports/unassigned.md')
        with self.assertRaises(ValueError):
            self.update('submitted', evidence=[output], executor_stopped=True)

    def test_closed_task_cannot_be_reopened_with_same_id(self):
        self.create()
        self.update('cancelled')
        with self.assertRaises(ValueError):
            self.update('planned')
        with self.assertRaises(ValueError):
            self.create()

    def test_phase_transition_requires_separate_evidence_and_decision(self):
        self.create()
        with self.assertRaises(ValueError):
            self.tool.transition_phase(ROOT, self.project, 'ideation', '', ['research-brief.md'])
        with self.assertRaises(ValueError):
            self.tool.transition_phase(ROOT, self.project, 'ideation', 'Ready', [])
        with self.assertRaises(ValueError):
            self.tool.transition_phase(ROOT, self.project, 'write', 'Skip', ['research-brief.md'])
        self.accept(self.packet())
        with self.assertRaises(ValueError):
            self.tool.transition_phase(ROOT, self.project, 'ideation', 'Ready', ['research-brief.md'])

    def test_completion_phase_cannot_ignore_open_tasks(self):
        self.create()
        state = self.state()
        state['phase'] = 'review'
        self.save(state)
        with self.assertRaisesRegex(ValueError, 'open tasks'):
            self.tool.transition_phase(ROOT, self.project, 'complete', 'Conclude', ['research-brief.md'])

    def test_stale_assignment_packet_is_rejected(self):
        self.create()
        packet = self.packet()
        self.create('t2')
        with self.assertRaisesRegex(ValueError, 'stale|State|state'):
            self.accept(packet)

    def test_changed_input_blocks_acceptance(self):
        self.create()
        packet = self.packet()
        (self.project / 'research-brief.md').write_text('Different question')
        with self.assertRaisesRegex(ValueError, 'hash mismatch'):
            self.accept(packet)

    def test_receipt_must_match_task_packet_and_session(self):
        self.create()
        packet = self.packet()
        for change in ({'task_id': 't2'}, {'packet_id': 'wrong'}, {'accepted': False},
                       {'actual_session_mode': 'current'}, {'session_isolation_verified': False},
                       {'actual_role': 'other'}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.accept(packet, **change)

    def test_independence_is_part_of_task_not_optional_on_retry(self):
        self.create(independent_review=True)
        with self.assertRaises(ValueError):
            self.packet(session_mode='current', session_reason='Convenience')
        self.assertTrue(self.packet()['session']['independent_review'])

    def test_compatible_related_tasks_may_reuse_session(self):
        self.create()
        self.accept(self.packet())
        self.update('submitted', evidence=[self.output()], executor_stopped=True)
        self.update('completed')
        self.create('t2')
        packet = self.packet('t2', outputs=['hypotheses/t2.md'], session_mode='reuse',
                             session_reason='Related task with compatible history', resume_session_id='host:s1')
        self.accept(packet)
        self.assertEqual(self.state()['active_task'], 't2')
        self.assertEqual(self.state()['tasks']['t2']['assignments'][0]['receipt']['actual_session_id'], 'host:s1')

    def test_receipt_cannot_authorize_a_changed_packet(self):
        self.create()
        packet = self.packet()
        receipt = self.receipt(packet)
        for change in ({'allowed_outputs': ['data/new-scope/']}, {'summary': 'A different execution instruction'}):
            changed = dict(packet, **change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.tool.accept_assignment(ROOT, self.project, changed, receipt)

    def test_reuse_checks_latest_execution_not_task_creation_order(self):
        self.create('t1', role='critic')
        self.create('t2')
        self.accept(self.packet('t2'))
        self.update('cancelled', task_id='t2', executor_stopped=True)
        self.accept(self.packet('t1', session_mode='current', session_reason='Small critical check'))
        self.update('cancelled', executor_stopped=True)
        self.create('t3')
        packet = self.packet('t3', session_mode='reuse', session_reason='Continue strategy', resume_session_id='host:s1')
        with self.assertRaisesRegex(ValueError, 'incompatible'):
            self.accept(packet)

    def test_reused_session_cannot_claim_fresh_isolation(self):
        self.create()
        self.accept(self.packet())
        self.update('submitted', evidence=[self.output()], executor_stopped=True)
        self.update('completed')
        self.create('t2')
        packet = self.packet('t2', outputs=['hypotheses/t2.md'], session_mode='reuse',
                             session_reason='Related task with compatible history', resume_session_id='host:s1')
        with self.assertRaises(ValueError):
            self.accept(packet, session_isolation_verified=True)

    def test_legacy_state_is_not_silently_reinterpreted(self):
        self.create()
        state = self.state()
        state['schema_version'] = 2
        self.save(state)
        with self.assertRaisesRegex(ValueError, 'schema|migration'):
            self.packet()

    def test_cli_two_completed_tasks_keep_scope_until_explicit_phase_change(self):
        self.create('t1')
        self.create('t2')
        (self.project / 'handoffs').mkdir()
        for task_id in ('t1', 't2'):
            output_path = f'hypotheses/{task_id}.md'
            packet = self.packet(task_id, outputs=[output_path])
            receipt = self.receipt(packet, session_id=f'host:{task_id}')
            packet_path = f'handoffs/{task_id}.json'
            receipt_path = f'handoffs/{task_id}-receipt.json'
            (self.project / packet_path).write_text(json.dumps(packet))
            (self.project / receipt_path).write_text(json.dumps(receipt))
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(self.tool.main(['accept', '--project', str(self.project),
                                                '--packet', packet_path, '--receipt', receipt_path]), 0)
            self.output(output_path)
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(self.tool.main(['task-status', '--project', str(self.project), '--task', task_id,
                                                '--status', 'submitted', '--reason', 'Worker stopped',
                                                '--executor-stopped', '--evidence', output_path]), 0)
                self.assertEqual(self.tool.main(['task-status', '--project', str(self.project), '--task', task_id,
                                                '--status', 'completed', '--reason', 'Core accepted artifacts']), 0)
            self.assertEqual(self.state()['phase'], 'scope')
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(self.tool.main(['phase', '--project', str(self.project), '--to', 'ideation',
                                            '--reason', 'Scope exit criteria checked', '--evidence', 'research-brief.md']), 0)
        state = self.state()
        self.assertEqual(state['phase'], 'ideation')
        self.assertIsNone(state['active_task'])
        self.assertTrue(all(t['status'] == 'completed' for t in state['tasks'].values()))

    def test_cli_separates_task_creation_handoff_and_phase(self):
        with contextlib.redirect_stdout(io.StringIO()):
            code = self.tool.main(['task', '--project', str(self.project), '--task', 't1',
                                  '--objective', 'Bound the question', '--activity', 'analysis',
                                  '--skill', 'brainstorming-research-ideas', '--role', 'strategist',
                                  '--acceptance', 'Clear scope'])
        self.assertEqual(code, 0)
        with contextlib.redirect_stdout(io.StringIO()) as output:
            code = self.tool.main(['handoff', '--project', str(self.project), '--task', 't1',
                                  '--summary', 'Inspect scope', '--evidence', 'research-brief.md',
                                  '--outputs', 'reports/scope.md', '--model', 'current'])
        self.assertEqual(code, 0)
        self.assertNotIn('to_phase', json.loads(output.getvalue()))
        self.assertEqual(self.state()['phase'], 'scope')


if __name__ == '__main__':
    unittest.main()
