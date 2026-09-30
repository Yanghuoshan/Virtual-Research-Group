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
        result = dict(schema_version=8, packet_id=packet['packet_id'], task_id=packet['task_id'],
                      source_revision=packet['source_revision'], accepted=True,
                      accepted_at='2026-01-01T00:00:00+00:00',
                      actual_role=packet['target_role']['id'], actual_model='provider/model-a',
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

    def test_migration_rejects_inconsistent_running_legacy_state(self):
        self.create()
        legacy = self.state()
        legacy['schema_version'] = 5
        for key in ('goal', 'grant', 'reflections'):
            legacy.pop(key)
        legacy['tasks']['t1']['status'] = 'running'
        self.save(legacy)
        with self.assertRaisesRegex(ValueError, 'executors'):
            self.tool.migrate_project(ROOT, self.project)
        self.assertEqual(self.state()['schema_version'], 5)
        legacy['tasks']['t1']['status'] = 'planned'
        self.save(legacy)
        self.tool.migrate_project(ROOT, self.project)
        self.assertEqual(self.state()['schema_version'], 8)

    def test_goal_versions_are_bound_and_unknowns_block_scope_exit(self):
        goal = self.output('hypotheses/goal-v1.md')
        with self.assertRaises(ValueError):
            self.tool.set_goal(ROOT, self.project, goal, 'Select scope')
        (self.project / goal).write_text('\n'.join((
            '# Goal', 'Question: graph sensitivity', 'Value: improve reliability',
            'Boundary: graph datasets', 'Alternatives: data shift or metric bias',
            'Evidence: supplied dataset inventory', 'Falsifier: no improvement',
            'Success: held-out effect', 'Feasibility: supplied data', 'Resources: bounded sandbox run',
            'Stop: abandon after failed matched baseline', 'Unknown: baseline availability')))
        self.tool.set_goal(ROOT, self.project, goal, 'Select scope')
        with self.assertRaisesRegex(ValueError, 'unknown'):
            self.tool.transition_phase(ROOT, self.project, 'ideation', 'Explore', [goal])

    def test_reflection_requires_evidence_and_followup_review(self):
        self.create('run', activity='experiment')
        self.create('followup', activity='experiment')
        self.output('reports/reflection-v1.json')
        with self.assertRaises(ValueError):
            self.tool.record_reflection(ROOT, self.project, 'run', 'reports/reflection-v1.json',
                                        'Compare with predeclared metric')

    def test_completion_records_a_structured_verdict(self):
        self.create('t1')
        self.accept(self.packet())
        self.update('submitted', evidence=[self.output()], executor_stopped=True)
        with self.assertRaisesRegex(ValueError, 'Verdicts apply to completion'):
            self.update('submitted', verdict='met')
        with self.assertRaises(ValueError):
            self.update('completed', verdict='exceeded')
        state = self.update('completed', verdict='partially-met')
        event = state['history'][-1]
        self.assertEqual(event['action'], 'task-completed')
        self.assertEqual(event['verdict'], 'partially-met')

    def test_reflection_covers_analysis_tasks(self):
        self.create('review')
        self.accept(self.packet('review', outputs=['literature/review-v1.md']))
        self.update('submitted', task_id='review', evidence=[self.output('literature/review-v1.md')],
                    executor_stopped=True)
        self.update('completed', task_id='review')
        record = {'observation': 'Coverage is thinner than expected for the stated question',
                  'protocol_check': 'Search plan followed as recorded',
                  'counterevidence': 'Nothing in the supplied corpus contradicts the map',
                  'alternatives': 'A different query formulation',
                  'next_options': ['Broaden the search terms'],
                  'prediction': 'A broader query formulation doubles the yield',
                  'decision': 'Test the broader formulation',
                  'evidence': [{'path': 'literature/review-v1.md',
                                'sha256': self.tool.digest(self.project / 'literature/review-v1.md')}]}
        (self.project / 'reports').mkdir(parents=True, exist_ok=True)
        (self.project / 'reports/reflection-v1.json').write_text(json.dumps(record))
        state = self.tool.record_reflection(ROOT, self.project, 'review', 'reports/reflection-v1.json',
                                            'Compare with the prediction before the follow-up')
        self.assertEqual(state['reflections'][0]['task_id'], 'review')
        # A later completed analysis task reviews the prediction.
        self.create('followup')
        self.accept(self.packet('followup', outputs=['literature/followup-v1.md']), session_id='host:s2')
        self.update('submitted', task_id='followup', evidence=[self.output('literature/followup-v1.md')],
                    executor_stopped=True)
        self.update('completed', task_id='followup')
        state = self.tool.review_reflection(ROOT, self.project, 'reports/reflection-v1.json', 'followup',
                                            'Prediction consistent with the broader search',
                                            assessment='supported')
        self.assertEqual(state['reflections'][0]['followup']['assessment'], 'supported')

    def test_host_job_must_be_reconciled_before_submission(self):
        self.create()
        self.accept(self.packet())
        self.tool.host_event(ROOT, self.project, 't1', 'host/job-1', 'running', 'Started')
        with self.assertRaisesRegex(ValueError, 'outstanding'):
            self.update('submitted', evidence=[self.output()], executor_stopped=True)
        self.tool.host_event(ROOT, self.project, 't1', 'host/job-1', 'succeeded', 'Reconciled')
        self.update('submitted', evidence=['hypotheses/t1-v1.md'], executor_stopped=True)

    def test_planned_resolver_does_not_unblock_unrelated_work(self):
        state = self.tool.update_blockers(ROOT, self.project, add='Missing baseline', reason='Need data')
        blocker_id = state['blockers'][0]['blocker_id']
        self.create('fix', resolves=[blocker_id])
        with self.assertRaises(ValueError):
            self.create('other')
        self.assertEqual(self.packet('fix')['task_id'], 'fix')

    def test_experiments_require_research_mode_even_in_scope(self):
        self.create(activity='experiment')
        with self.assertRaisesRegex(ValueError, 'research mode'):
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
        self.assertEqual(state['active_tasks'], ['t1'])
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
        self.assertEqual(state['active_tasks'], ['t1'])
        self.assertEqual(state['phase'], 'scope')
        self.assertEqual(len(state['tasks']['t1']['assignments']), 2)

    def test_running_task_cannot_be_replaced_without_stopping_executor(self):
        self.create()
        self.accept(self.packet())
        with self.assertRaises(ValueError):
            self.update('blocked')
        with self.assertRaises(ValueError):
            self.update('planned')
        self.assertEqual(self.state()['active_tasks'], ['t1'])

    def test_disjoint_tasks_run_in_parallel_until_completion(self):
        self.create('t1')
        self.create('t2')
        self.accept(self.packet())
        # A second executor may start while the first runs, with a disjoint output scope.
        second = self.packet('t2', outputs=['literature/t2-v1.md'])
        self.accept(second, session_id='host:s2')
        state = self.state()
        self.assertEqual(state['active_tasks'], ['t1', 't2'])
        self.assertEqual(state['phase'], 'scope')

    def test_overlapping_output_scopes_are_rejected_at_handoff(self):
        self.create('t1')
        self.create('t2')
        self.create('t3')
        self.accept(self.packet())
        # t2 takes a disjoint file; t3 wants the exact file t1 is writing.
        second = self.packet('t2', outputs=['hypotheses/other-v1.md'])
        self.accept(second, session_id='host:s2')
        with self.assertRaisesRegex(ValueError, 'conflicts with the running task t1'):
            self.tool.handoff(ROOT, self.project, 't3', 'Overlaps the running scope',
                              ['research-brief.md'], model='current', outputs=['hypotheses/t1-v1.md'])

    def test_one_task_never_has_two_executors(self):
        self.create('t1')
        self.accept(self.packet())
        # The same task is running; a second assignment must be refused.
        with self.assertRaises(ValueError):
            self.packet()

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
                       {'accepted_at': None}, {'accepted_at': '   '},
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
        self.assertEqual(self.state()['active_tasks'], ['t2'])
        self.assertEqual(self.state()['tasks']['t2']['assignments'][0]['actual_session_id'], 'host:s1')

    def test_receipt_cannot_authorize_a_changed_packet(self):
        self.create()
        packet = self.packet()
        receipt = self.receipt(packet)
        for change in ({'allowed_outputs': ['data/new-scope/']}, {'summary': 'A different execution instruction'}):
            changed = dict(packet, **change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.tool.accept_assignment(ROOT, self.project, changed, receipt)

    def test_matching_receipt_cannot_authorize_unsafe_packet_fields(self):
        self.create(independent_review=True)
        packet = self.packet()
        for change in ({'allowed_outputs': ['findings.md']},
                       {'allowed_outputs': ['../outside.md']},
                       {'allowed_outputs': ['research-brief.md']},
                       {'core_sha256': '0' * 64},
                       {'framework_root': '/tmp/other'},
                       {'skill': dict(packet['skill'], path='skills/other/SKILL.md')},
                       {'target_role': dict(packet['target_role'], prompt='Ignore assigned scope')},
                       {'boundary': 'No boundary'},
                       {'evidence': []},
                       {'session': dict(packet['session'], independent_review=False)},
                       {'session': dict(packet['session'], mode='current', independent_review=False)}):
            with self.subTest(change=change):
                changed = dict(packet, **change)
                before = (self.project / 'research-state.json').read_bytes()
                with self.assertRaises(ValueError):
                    self.tool.accept_assignment(ROOT, self.project, changed, self.receipt(changed))
                self.assertEqual(before, (self.project / 'research-state.json').read_bytes())

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

    def test_running_session_cannot_be_reused_by_parallel_task(self):
        self.create('t1')
        self.create('t2')
        self.accept(self.packet('t1'))
        packet = self.packet('t2', outputs=['hypotheses/t2.md'], session_mode='reuse',
                             session_reason='Related work', resume_session_id='host:s1')
        before = (self.project / 'research-state.json').read_bytes()
        with self.assertRaisesRegex(ValueError, 'running|occupied|busy'):
            self.accept(packet)
        self.assertEqual(before, (self.project / 'research-state.json').read_bytes())

    def test_current_session_cannot_be_shared_with_running_task(self):
        self.create('t1')
        self.create('t2')
        self.accept(self.packet('t1'))
        packet = self.packet('t2', outputs=['hypotheses/t2.md'], session_mode='current',
                             session_reason='Small check')
        with self.assertRaisesRegex(ValueError, 'running|occupied|busy'):
            self.accept(packet)

    def test_current_session_without_id_cannot_run_parallel_tasks(self):
        self.create('t1')
        self.create('t2')
        self.accept(self.packet('t1', session_mode='current', session_reason='Small check'),
                    session_id=None)
        packet = self.packet('t2', outputs=['hypotheses/t2.md'], session_mode='current',
                             session_reason='Another small check')
        with self.assertRaisesRegex(ValueError, 'running|occupied|identity'):
            self.accept(packet, session_id=None)

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
        self.assertEqual(state['active_tasks'], [])
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

    def test_resolver_targets_one_blocker_while_others_stay_open(self):
        state = self.tool.update_blockers(ROOT, self.project, add='B1 blocking', reason='Need data')
        first = state['blockers'][0]['blocker_id']
        state = self.tool.update_blockers(ROOT, self.project, add='B2 unrelated', reason='Second gap')
        second = state['blockers'][1]['blocker_id']
        self.create('fix', resolves=[first])
        self.assertEqual(self.packet('fix', outputs=['hypotheses/fix-v1.md'])['task_id'], 'fix')
        self.create('late', resolves=[second])
        with self.assertRaisesRegex(ValueError, 'unrelated work'):
            self.create('other')
        with self.assertRaisesRegex(ValueError, 'Unknown blocker'):
            self.create('phantom', resolves=['b99'])

    def test_editing_blocker_text_keeps_identity_and_resolver(self):
        state = self.tool.update_blockers(ROOT, self.project, add='Missing baseline', reason='Need data')
        blocker_id, opened_at = state['blockers'][0]['blocker_id'], state['blockers'][0]['opened_at']
        self.create('fix', resolves=[blocker_id])
        edited = self.tool.update_blockers(ROOT, self.project, edit=blocker_id,
                                           text='Missing baseline (clarified)', reason='Reword')
        self.assertEqual(edited['blockers'][0]['blocker_id'], blocker_id)
        self.assertEqual(edited['blockers'][0]['opened_at'], opened_at)
        self.assertEqual(self.packet('fix', outputs=['hypotheses/fix-v1.md'])['task_id'], 'fix')

    def test_reopened_blocker_survives_stale_task_completion(self):
        state = self.tool.update_blockers(ROOT, self.project, add='Missing data', reason='First round')
        first = state['blockers'][0]['blocker_id']
        self.create('fix', resolves=[first])
        self.accept(self.packet('fix', outputs=['hypotheses/fix-v1.md']))
        self.update('submitted', task_id='fix', evidence=[self.output('hypotheses/fix-v1.md')], executor_stopped=True)
        # The first round is closed manually, then the same text is reopened as a new round.
        self.tool.update_blockers(ROOT, self.project, resolve=first, reason='Closed early')
        state = self.tool.update_blockers(ROOT, self.project, add='Missing data', reason='Second round')
        reopened = state['blockers'][0]['blocker_id']
        self.assertNotEqual(reopened, first)
        # Completing the stale task neither clears the new round nor touches it silently.
        state = self.update('completed', task_id='fix')
        self.assertEqual([b['blocker_id'] for b in state['blockers']], [reopened])
        self.assertEqual([b['blocker_id'] for b in state['blocker_history']], [first])
        event = state['history'][-1]
        self.assertEqual(event['auto_resolved'], [])
        self.assertEqual(event['declared_already_closed'], [first])
        # A fresh task targeting the reopened round proceeds, and a task still pointing
        # at the closed round is refused loudly instead of matching by text.
        self.create('round2', resolves=[reopened])
        self.assertEqual(self.packet('round2', outputs=['hypotheses/round2-v1.md'])['task_id'], 'round2')
        self.tool.update_blockers(ROOT, self.project, resolve=reopened, reason='Second round closed')
        with self.assertRaisesRegex(ValueError, 'Unknown blocker'):
            self.create('stale', resolves=[first])

    def test_freeze_all_is_an_explicit_recoverable_emergency_stop(self):
        self.create('t1')
        state = self.tool.update_blockers(ROOT, self.project, add='Emergency stop', reason='Halt', freeze_all=True)
        blocker_id = state['blockers'][0]['blocker_id']
        with self.assertRaisesRegex(ValueError, 'freeze-all'):
            self.create('fix', resolves=[blocker_id])
        with self.assertRaisesRegex(ValueError, 'freeze-all'):
            self.packet()
        self.tool.update_blockers(ROOT, self.project, resolve=blocker_id, reason='Recovered')
        self.accept(self.packet())
        self.update('submitted', evidence=[self.output()], executor_stopped=True)
        state = self.tool.update_blockers(ROOT, self.project, add='Second stop', reason='Halt again', freeze_all=True)
        with self.assertRaisesRegex(ValueError, 'freeze-all'):
            self.update('completed')
        self.tool.update_blockers(ROOT, self.project, resolve=state['blockers'][0]['blocker_id'], reason='Recovered')
        self.assertEqual(self.update('completed')['tasks']['t1']['status'], 'completed')

    def test_status_board_shows_blocker_identity_and_resolver(self):
        state = self.tool.update_blockers(ROOT, self.project, add='Missing baseline', reason='Need data')
        blocker_id = state['blockers'][0]['blocker_id']
        self.create('fix', resolves=[blocker_id])
        board = self.tool.status(ROOT, self.project)
        self.assertIn(f'{blocker_id}: Missing baseline', board)
        self.assertIn('being resolved by fix', board)

    def test_migration_converts_blocker_text_to_stable_ids(self):
        self.create('fix')
        legacy = self.state()
        legacy['schema_version'] = 6
        legacy['blockers'] = ['Missing baseline']
        legacy['tasks']['fix']['resolves'] = ['Missing baseline']
        legacy.pop('blocker_history')
        legacy.pop('blocker_seq')
        self.save(legacy)
        state = self.tool.migrate_project(ROOT, self.project)
        self.assertEqual(state['schema_version'], 8)
        self.assertEqual(state['blockers'][0]['blocker_id'], 'b1')
        self.assertEqual(state['blockers'][0]['text'], 'Missing baseline')
        self.assertEqual(state['tasks']['fix']['resolves'], ['b1'])

    def test_migration_refuses_unidentifiable_resolves_references(self):
        self.create('fix')
        legacy = self.state()
        legacy['schema_version'] = 6
        legacy['blockers'] = ['Missing baseline']
        legacy['tasks']['fix']['resolves'] = ['Never recorded anywhere']
        legacy.pop('blocker_history')
        legacy.pop('blocker_seq')
        self.save(legacy)
        with self.assertRaisesRegex(ValueError, 'Cannot identify'):
            self.tool.migrate_project(ROOT, self.project)


class GateCommandTests(unittest.TestCase):
    """The gates that no specialist may set are opened only by explicit core commands."""

    def setUp(self):
        self.tool = load_tool()
        self.temp = tempfile.TemporaryDirectory(dir=ROOT)
        self.addCleanup(self.temp.cleanup)
        self.project = Path(self.temp.name) / 'project'
        self.tool.initialize(ROOT, self.project, 'Investigate graph sensitivity')

    def state(self):
        return json.loads((self.project / 'research-state.json').read_text())

    def write(self, name, text='Artifact body'):
        path = self.project / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        return name

    def digest(self, name):
        return hashlib.sha256((self.project / name).read_bytes()).hexdigest()

    def receipt(self, packet, session_id='host:gate'):
        digest = hashlib.sha256(json.dumps(packet, sort_keys=True, ensure_ascii=False,
                                           separators=(',', ':'), allow_nan=False).encode('utf-8')).hexdigest()
        return {'schema_version': 8, 'task_id': packet['task_id'], 'packet_id': packet['packet_id'],
                'source_revision': packet['source_revision'], 'packet_sha256': digest, 'accepted': True,
                'accepted_at': '2026-01-01T00:00:00+00:00', 'actual_role': packet['target_role']['id'],
                'actual_model': 'provider/model-a', 'actual_session_mode': packet['session']['mode'],
                'actual_session_id': session_id,
                'session_isolation_verified': packet['session']['mode'] == 'fresh',
                'session_notes': 'Host identity verified', 'state_hash_checked': True,
                'core_hash_checked': True, 'skill_hash_checked': True, 'evidence_hashes_checked': True}

    def create(self, task_id='run', **changes):
        options = dict(activity='experiment', skill='graph-evaluation', role='experimenter',
                       acceptance='Report protocol-bound measurements')
        options.update(changes)
        return self.tool.create_task(ROOT, self.project, task_id, 'Run the frozen protocol', **options)

    def grant(self, reason='User authorized the bounded protocol', evidence=('reports/user-approval-v1.md',)):
        self.write('reports/user-approval-v1.md', 'User-approved scope: graph-study; sandbox run; up to ten attempts.')
        return self.tool.authorize(ROOT, self.project, mode='research', reason=reason, evidence=list(evidence),
                                   services=['sandbox'], operations=['run'], scope='graph-study', max_runs=10,
                                   expires_at='2099-01-01T00:00:00Z')

    def evaluate(self):
        return self.tool.set_evaluation(ROOT, self.project, primary_measure='macro F1', baseline='Matched baseline',
                                        validation_plan='Grouped split', uncertainty_plan='Five seeds',
                                        reason='Core accepted the protocol')

    def protocol(self):
        path = self.write('experiments/H1/protocol.md', 'Frozen protocol')
        self.tool.set_protocol(ROOT, self.project, path=path, reason='Core froze the protocol')
        return path

    def audit(self, subjects, name='reviews/evidence-audit.json', status='verified', kind='evidence'):
        payload = {'schema_version': 2, 'reviewer': 'core',
                   'reviewed_at': '2026-01-01T00:00:00+00:00',
                   'summary': 'Audit binds findings, protocol and raw evidence',
                   'claims': [{'claim': 'The reported gain is bound to raw evidence',
                               'support': 'Run artifacts under experiments/'}],
                   'subjects': []}
        for subject in subjects:
            payload['subjects'].append({'path': subject, 'sha256': self.digest(subject)})
        target = self.project / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
        return self.tool.set_audit(ROOT, self.project, kind=kind, path=name, status=status,
                                   reason='Core recorded the audit')

    def test_authorize_requires_evidence_when_granting(self):
        for evidence in ([], ['missing.md']):
            with self.subTest(evidence=evidence), self.assertRaises(ValueError):
                self.grant(evidence=evidence)
        self.grant()
        state = self.state()
        self.assertEqual(state['mode'], 'research')

    def test_revoking_research_mode_needs_no_evidence(self):
        self.grant()
        state = self.tool.authorize(ROOT, self.project, mode='planning',
                                    reason='Mode withdrawn', evidence=[])
        self.assertEqual(state['mode'], 'planning')

    def test_planning_grant_rejects_execution_operation(self):
        approval = self.write('reports/planning-approval-v1.md', 'Approved search only')
        with self.assertRaisesRegex(ValueError, 'Planning grants'):
            self.tool.authorize(ROOT, self.project, mode='planning', reason='Search candidate directions',
                                evidence=[approval], services=['sandbox'], operations=['run'],
                                scope='graph-study', max_runs=1, expires_at='2099-01-01T00:00:00Z')
        # Uncataloged operations fail closed: the search channel must be classified
        # from an ingested catalog before a planning grant may name it.
        with self.assertRaisesRegex(ValueError, 'read-classified'):
            self.tool.authorize(ROOT, self.project, mode='planning', reason='Search candidate directions',
                                evidence=[approval], services=['catalog'], operations=['search'],
                                scope='graph-study', max_runs=1, expires_at='2099-01-01T00:00:00Z')
        self.write('tools/catalog-dump.json', json.dumps(
            {'tools': [{'name': 'search', 'description': 'Search the published catalog'}]}))
        self.tool.ingest_catalog(ROOT, self.project, 'catalog', 'tools/catalog-dump.json',
                                 'Host exported the catalog')
        state = self.tool.authorize(ROOT, self.project, mode='planning', reason='Search candidate directions',
                                    evidence=[approval], services=['catalog'], operations=['search'],
                                    scope='graph-study', max_runs=1, expires_at='2099-01-01T00:00:00Z')
        self.assertEqual(state['mode'], 'planning')
        self.assertEqual(state['grant']['operations'], ['search'])

    def test_authorize_rejects_unknown_mode_and_blank_reason(self):
        with self.assertRaises(ValueError):
            self.tool.authorize(ROOT, self.project, mode='curious', reason='Not a real mode')
        with self.assertRaises(ValueError):
            self.grant(reason='   ')

    def test_experiment_task_stays_closed_until_every_gate_is_set(self):
        self.create()
        with self.assertRaises(ValueError):
            self.packet_for('experiments/H1/runs/run-001/analysis.md')
        self.grant()
        with self.assertRaises(ValueError):
            self.packet_for('experiments/H1/runs/run-001/analysis.md')
        self.evaluate()
        with self.assertRaises(ValueError):
            self.packet_for('experiments/H1/runs/run-001/analysis.md')
        protocol = self.protocol()
        packet = self.packet_for('experiments/H1/runs/run-001/analysis.md', evidence=[protocol])
        self.assertEqual(packet['activity'], 'experiment')
        self.assertEqual(packet['skill']['name'], 'graph-evaluation')

    def packet_for(self, output, evidence=None):
        return self.tool.handoff(ROOT, self.project, 'run', 'Execute the frozen protocol',
                                 evidence or ['research-brief.md'], model='current', outputs=[output])

    def test_reflection_records_original_result_and_later_prediction_check(self):
        self.grant()
        self.evaluate()
        protocol = self.protocol()
        self.create('run')
        first = self.packet_for('experiments/H1/runs/first/results/metrics.json', evidence=[protocol])
        self.tool.accept_assignment(ROOT, self.project, first, self.receipt(first))
        raw = self.write('experiments/H1/runs/first/results/metrics.json', '{"score": 0.7}')
        self.tool.update_task(ROOT, self.project, 'run', 'submitted', 'Returned raw result', [raw], executor_stopped=True)
        self.tool.update_task(ROOT, self.project, 'run', 'completed', 'Accepted result', [])
        reflection = self.write('reports/reflection-v1.json', json.dumps({
            'observation': 'The result is below the target', 'protocol_check': 'No known deviation',
            'counterevidence': 'Baseline remains competitive', 'alternatives': 'Data shift',
            'next_options': ['Replicate on independent split'], 'prediction': 'Effect disappears on new split',
            'decision': 'Test the alternate split',
            'evidence': [{'path': raw, 'sha256': self.digest(raw)}]}))
        self.tool.record_reflection(ROOT, self.project, 'run', reflection, 'Review before selecting follow-up')
        with self.assertRaises(ValueError):
            self.tool.review_reflection(ROOT, self.project, reflection, 'run', 'Cannot reuse the same run',
                                        assessment='inconclusive')
        self.create('followup')
        second = self.tool.handoff(ROOT, self.project, 'followup', 'Run independent check', [protocol],
                                   model='current', outputs=['experiments/H1/runs/followup/results/metrics.json'])
        self.tool.accept_assignment(ROOT, self.project, second, self.receipt(second, session_id='host:followup'))
        new_raw = self.write('experiments/H1/runs/followup/results/metrics.json', '{"score": 0.68}')
        self.tool.update_task(ROOT, self.project, 'followup', 'submitted', 'Returned follow-up result',
                              [new_raw], executor_stopped=True)
        self.tool.update_task(ROOT, self.project, 'followup', 'completed', 'Checked follow-up', [])
        self.tool.review_reflection(ROOT, self.project, reflection, 'followup',
                                    'Prediction consistent with new run', assessment='supported')
        self.assertEqual(self.state()['reflections'][0]['followup']['task_id'], 'followup')
        self.assertEqual(self.state()['reflections'][0]['followup']['assessment'], 'supported')

    def test_scoped_tool_preflight_binds_active_packet_and_task(self):
        self.grant()
        self.evaluate()
        protocol = self.protocol()
        self.tool.create_task(ROOT, self.project, 'tool-run', 'Use sandbox run in graph-study',
                              activity='experiment', skill='experiment-execution', role='experimenter',
                              acceptance='Return protocol-bound measurements', tools=['sandbox:run'])
        packet = self.tool.handoff(ROOT, self.project, 'tool-run', 'Run bounded experiment', [protocol],
                                   model='current', outputs=['experiments/H1/runs/tool-run/results/'])
        args = dict(task_id='tool-run', packet_id=packet['packet_id'], server='sandbox',
                    operation='run', scope='graph-study')
        with self.assertRaisesRegex(ValueError, 'active assignment'):
            self.tool.check_tool(ROOT, self.project, **args)
        self.tool.accept_assignment(ROOT, self.project, packet, self.receipt(packet))
        self.assertTrue(self.tool.check_tool(ROOT, self.project, **args)['allowed'])
        for change in ({'packet_id': 'old'}, {'scope': 'another-study'}, {'operation': 'write'}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.tool.check_tool(ROOT, self.project, **dict(args, **change))

    def test_changed_protocol_does_not_relabel_submitted_experiment(self):
        self.grant()
        self.evaluate()
        protocol = self.protocol()
        self.create('run')
        packet = self.packet_for('experiments/H1/runs/exp-1/results/metrics.json', evidence=[protocol])
        self.tool.accept_assignment(ROOT, self.project, packet, self.receipt(packet))
        raw = self.write('experiments/H1/runs/exp-1/results/metrics.json', '{"score": 0.7}')
        self.tool.update_task(ROOT, self.project, 'run', 'submitted', 'Executor stopped', [raw],
                              executor_stopped=True)
        next_protocol = self.write('experiments/H1/protocol-v2.md', 'Different metric and split')
        self.tool.set_protocol(ROOT, self.project, path=next_protocol, reason='New version after execution')
        with self.assertRaisesRegex(ValueError, 'Execution contract changed'):
            self.tool.update_task(ROOT, self.project, 'run', 'completed', 'Incorrect relabel', [])

    def test_expired_grant_prevents_new_calls_but_not_existing_result_review(self):
        self.grant()
        self.evaluate()
        protocol = self.protocol()
        self.create('run')
        packet = self.packet_for('experiments/H1/runs/exp-1/results/metrics.json', evidence=[protocol])
        self.tool.accept_assignment(ROOT, self.project, packet, self.receipt(packet))
        self.write('experiments/H1/runs/exp-1/results/metrics.json', '{"score": 0.7}')
        self.tool.update_task(ROOT, self.project, 'run', 'submitted', 'Executor stopped',
                              ['experiments/H1/runs/exp-1/results/metrics.json'], executor_stopped=True)
        from datetime import datetime, timezone
        from unittest import mock

        class Later(datetime):
            @classmethod
            def now(cls, tz=None):
                return datetime(2100, 1, 1, tzinfo=tz or timezone.utc)

        with mock.patch.object(self.tool, 'datetime', Later):
            with self.assertRaisesRegex(ValueError, 'expired'):
                self.tool.verify_grant(self.project, self.state())
            self.tool.update_task(ROOT, self.project, 'run', 'completed', 'Reviewed recorded run', [])
        self.assertEqual(self.state()['tasks']['run']['status'], 'completed')

    def test_set_protocol_rejects_paths_outside_experiments(self):
        self.write('paper/protocol.md')
        for path in ('paper/protocol.md', 'experiments/missing.md', '../outside.md'):
            with self.subTest(path=path), self.assertRaises(ValueError):
                self.tool.set_protocol(ROOT, self.project, path=path, reason='Try to freeze')
        self.protocol()
        self.assertEqual(self.state()['protocol']['path'], 'experiments/H1/protocol.md')

    def test_audit_verified_only_with_complete_binding(self):
        self.grant()
        self.evaluate()
        protocol = self.protocol()
        self.write('experiments/H1/runs/run-001/results.json', '{"macro_f1": 0.71}')
        with self.assertRaises(ValueError):
            self.audit(['findings.md'])
        self.audit(['findings.md', protocol, 'experiments/H1/runs/run-001/results.json'])
        review = self.state()['evidence_review']
        self.assertEqual(review['status'], 'verified')
        self.assertEqual(review['path'], 'reviews/evidence-audit.json')

    def test_audit_outside_reviews_and_unknown_status_rejected(self):
        self.write('data/audit.json', '{}')
        with self.assertRaises(ValueError):
            self.tool.set_audit(ROOT, self.project, kind='evidence', path='data/audit.json', status='verified',
                                reason='Wrong directory')
        with self.assertRaises(ValueError):
            self.tool.set_audit(ROOT, self.project, kind='evidence', path='reviews/a.json', status='passed',
                                reason='Wrong status for an evidence audit')

    def test_foreign_blocker_freezes_phase_but_not_completion(self):
        self.create('t1', activity='analysis', skill='brainstorming-research-ideas', role='strategist',
                    acceptance='Falsifier per hypothesis')
        packet = self.tool.handoff(ROOT, self.project, 't1', 'Develop candidates', ['research-brief.md'],
                                   model='current', outputs=['hypotheses/t1.md'])
        self.tool.accept_assignment(ROOT, self.project, packet, self.receipt(packet))
        self.write_output('hypotheses/t1.md')
        self.tool.update_task(ROOT, self.project, 't1', 'submitted', 'Worker returned artifacts', ['hypotheses/t1.md'],
                              executor_stopped=True)
        state = self.tool.update_blockers(ROOT, self.project, add='Baseline unavailable', reason='Baseline missing')
        blocker_id = state['blockers'][0]['blocker_id']
        # Completion records finished work even while a foreign blocker is open.
        self.tool.update_task(ROOT, self.project, 't1', 'completed', 'Accept returned artifacts', [])
        event = self.state()['history'][-1]
        self.assertEqual(event['auto_resolved'], [])
        self.assertEqual(event['declared_already_closed'], [])
        # Phase decisions still wait for every open blocker.
        with self.assertRaisesRegex(ValueError, 'blockers'):
            self.tool.transition_phase(ROOT, self.project, 'ideation', 'Try to advance', ['research-brief.md'])
        with self.assertRaises(ValueError):
            self.tool.update_blockers(ROOT, self.project, resolve='b99', reason='Not recorded')
        self.tool.update_blockers(ROOT, self.project, resolve=blocker_id, reason='Baseline reproduced')
        self.assertEqual(self.state()['blockers'], [])
        self.tool.transition_phase(ROOT, self.project, 'ideation', 'Scope exit criteria checked', ['research-brief.md'])
        self.assertEqual(self.state()['phase'], 'ideation')

    def write_output(self, name, text='Artifact body'):
        path = self.project / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        return name

    def test_blockers_stop_new_tasks_and_stopped_closes_everything(self):
        # Blockers absorb the old paused semantics: no new task may be created while blocked,
        # but gate decisions and task bookkeeping continue on an active project.
        state = self.tool.update_blockers(ROOT, self.project, add='Waiting for data', reason='Data request open')
        with self.assertRaisesRegex(ValueError, 'blockers'):
            self.create('t1', activity='analysis', skill='brainstorming-research-ideas', role='strategist',
                        acceptance='Falsifier per hypothesis')
        self.tool.update_blockers(ROOT, self.project, resolve=state['blockers'][0]['blocker_id'],
                                 reason='Data received')
        self.create('t1', activity='analysis', skill='brainstorming-research-ideas', role='strategist',
                    acceptance='Falsifier per hypothesis')
        # A stopped project closes new tasks, handoffs, phase decisions and gate commands alike.
        self.tool.set_project_status(ROOT, self.project, status='stopped', reason='Study closed')
        with self.assertRaises(ValueError):
            self.create('t2', activity='analysis', skill='citation-verification', role='analyst', acceptance='Resolved')
        with self.assertRaises(ValueError):
            self.tool.handoff(ROOT, self.project, 't1', 'Work', ['research-brief.md'], model='current',
                              outputs=['reports/a.md'])
        with self.assertRaises(ValueError):
            self.tool.transition_phase(ROOT, self.project, 'ideation', 'Try to advance', ['research-brief.md'])
        with self.assertRaises(ValueError):
            self.tool.update_blockers(ROOT, self.project, add='Another blocker', reason='Too late')
        self.tool.set_project_status(ROOT, self.project, status='active', reason='Study reopened')
        self.assertEqual(self.state()['status'], 'active')

    def test_stopped_project_is_terminal_until_reactivated(self):
        self.tool.set_project_status(ROOT, self.project, status='stopped', reason='Study closed')
        with self.assertRaises(ValueError):
            self.tool.authorize(ROOT, self.project, mode='research',
                                reason='Too late', evidence=['research-brief.md'])
        self.tool.set_project_status(ROOT, self.project, status='active', reason='Study reopened')
        self.assertEqual(self.state()['status'], 'active')

    def test_stopped_project_rejects_preissued_packet_and_task_status_changes(self):
        self.create('t1', activity='analysis', skill='brainstorming-research-ideas', role='strategist',
                    acceptance='Falsifier per hypothesis')
        packet = self.tool.handoff(ROOT, self.project, 't1', 'Develop candidates', ['research-brief.md'],
                                   model='current', outputs=['hypotheses/t1.md'])
        self.tool.set_project_status(ROOT, self.project, status='stopped', reason='Pause decisions')
        before = (self.project / 'research-state.json').read_bytes()
        with self.assertRaisesRegex(ValueError, 'stopped|active'):
            self.tool.accept_assignment(ROOT, self.project, packet, self.receipt(packet))
        with self.assertRaisesRegex(ValueError, 'stopped|active'):
            self.tool.update_task(ROOT, self.project, 't1', 'cancelled', 'Too late', [])
        self.assertEqual(before, (self.project / 'research-state.json').read_bytes())

    def test_stopped_project_cannot_complete_submitted_task(self):
        self.create('t1', activity='analysis', skill='brainstorming-research-ideas', role='strategist',
                    acceptance='Falsifier per hypothesis')
        packet = self.tool.handoff(ROOT, self.project, 't1', 'Develop candidates', ['research-brief.md'],
                                   model='current', outputs=['hypotheses/t1.md'])
        self.tool.accept_assignment(ROOT, self.project, packet, self.receipt(packet))
        self.write('hypotheses/t1.md')
        self.tool.update_task(ROOT, self.project, 't1', 'submitted', 'Worker stopped',
                              ['hypotheses/t1.md'], executor_stopped=True)
        self.tool.set_project_status(ROOT, self.project, status='stopped', reason='Pause decisions')
        with self.assertRaisesRegex(ValueError, 'stopped|active'):
            self.tool.update_task(ROOT, self.project, 't1', 'completed', 'Too late', [])

    def test_gate_commands_record_history_and_revision(self):
        start = self.state()['revision']
        self.grant()
        self.evaluate()
        self.protocol()
        state = self.state()
        self.assertEqual(state['revision'], start + 3)
        actions = [event['action'] for event in state['history'][-3:]]
        self.assertEqual(actions, ['mode-set', 'evaluation-set', 'protocol-frozen'])
        for event in state['history'][-3:]:
            self.assertIn('reason', event)

    def test_cli_gate_commands(self):
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(self.tool.main(['authorize', '--project', str(self.project), '--mode', 'research',
                                             '--reason', 'User authorized the protocol',
                                             '--evidence', 'research-brief.md', '--services', 'sandbox',
                                             '--operations', 'run', '--scope', 'graph-study', '--max-runs', '10',
                                             '--expires-at', '2099-01-01T00:00:00Z']), 0)
            self.assertEqual(self.tool.main(['set-evaluation', '--project', str(self.project),
                                             '--primary-measure', 'macro F1', '--baseline', 'Matched baseline',
                                             '--validation-plan', 'Grouped split', '--uncertainty-plan', 'Five seeds',
                                             '--reason', 'Protocol accepted']), 0)
        self.assertEqual(self.state()['mode'], 'research')
        self.assertEqual(self.state()['evaluation']['primary_measure'], 'macro F1')


if __name__ == '__main__':
    unittest.main()
