"""Gate refusals carry the command that clears them, and malformed input names the expected shape."""

import json
from pathlib import Path
import tempfile
import unittest

from test_framework import ROOT, load_tool

# A repair step is an executable command, so every step is checked against the
# registered CLI. A step naming a command that is not registered is a step the core
# cannot run, and such a command has to be registered first: no exemption list is
# kept here, because one would pension off the check that catches exactly that.


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

    def write(self, name, text='Artifact body'):
        """One project artifact, created where a later gate will look for it."""
        path = self.project / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        return name

    def audit_record(self, name):
        """A real audit record, filed wherever the caller asks for it."""
        findings = self.write('findings.md', 'Findings the audit binds')
        payload = {'schema_version': 2, 'reviewer': 'core', 'reviewed_at': '2026-01-01T00:00:00+00:00',
                   'summary': 'Audit binds findings and primary evidence',
                   'claims': [{'claim': 'The findings rest on bound primary evidence',
                               'support': 'Primary artifact hashes'}],
                   'subjects': [{'path': findings,
                                 'sha256': self.tool.digest(self.project / findings)}]}
        self.write(name, json.dumps(payload, ensure_ascii=False, indent=2))
        return name

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

    def assertRealCommands(self, steps):
        """Every repair step names a registered command and only real flags of it.

        A step has to be executable exactly as written, so it must also name every
        option the command requires. That is what separates a command from prose
        advice: advice can begin with a command name and carry no flags at all.
        """
        commands = {name: dict(options) for name, _, options in self.tool.CLI}
        for step in steps:
            name = step.split()[0]
            with self.subTest(step=step):
                self.assertIn(name, commands, f'{name} is not a registered command')
                for flag in [word for word in step.split() if word.startswith('--')]:
                    self.assertIn(flag[2:], commands[name], f'{name} has no {flag}')
                named = {word[2:] for word in step.split() if word.startswith('--')}
                self.assertEqual([], [option for option, kwargs in commands[name].items()
                                      if kwargs.get('required') and option not in named],
                                 f'{name} step omits a required option: {step}')

    def test_every_repair_step_names_a_real_command_and_real_flags(self):
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
        # An audit filed outside reviews/: the repair names the path it must be filed at.
        misplaced = self.audit_record('reviews-misplaced.json')
        steps += self.steps(lambda: self.tool.set_audit(ROOT, self.project, kind='evidence', path=misplaced,
                                                        status='verified', reason='Audit binds its subjects'))
        # A running executor handing back an artifact no assigned output scope holds.
        stray = self.write('reports/stray-finding.md')
        steps += self.steps(lambda: self.tool.update_task(ROOT, self.project, 't1', 'submitted',
                                                         'Artifacts returned', [stray], executor_stopped=True))
        self.assertRealCommands(steps)

    def test_every_board_repair_step_names_a_real_command_and_real_flags(self):
        """A board the core is told to follow must name commands that really exist."""
        steps = []

        def board_steps(**options):
            board = self.tool.next_steps_for(ROOT, self.project, **options)
            return [step for entry in board['blocked'] for step in entry['next']]

        self.tool.set_project_status(ROOT, self.project, status='stopped', reason='Planning only')
        steps += board_steps()
        self.tool.set_project_status(ROOT, self.project, status='active', reason='Planning resumed')
        steps += board_steps()
        steps += board_steps(task_id='absent')
        # A planned task under an open blocker: the handoff halt names the repairs.
        self.tool.update_blockers(ROOT, self.project, add='Human decision needed', reason='Approval missing')
        steps += board_steps(task_id='t1')
        # A running executor holds the phase, and a freeze-all halts completion.
        self.tool.update_blockers(ROOT, self.project, resolve='b1', reason='Approval recorded')
        packet = self.handoff()
        self.tool.accept_assignment(ROOT, self.project, packet, self.receipt(packet))
        steps += board_steps(task_id='t1')
        self.tool.update_blockers(ROOT, self.project, add='Stop all work', reason='Emergency', freeze_all=True)
        steps += board_steps()
        self.assertNotEqual(steps, [], 'no board repair was collected')
        self.assertRealCommands(steps)

    def test_the_grant_changed_repair_is_legal_for_the_task_it_was_refused_on(self):
        # This gate is reachable only while the task is running, so the single planned
        # move it used to name was refused for every task that could reach it.
        self.authorize()
        packet = self.handoff()
        self.tool.accept_assignment(ROOT, self.project, packet, self.receipt(packet))
        self.write('reports/user-approval-v2.md', 'User-approved scope, restated')
        self.tool.authorize(ROOT, self.project, mode='research', reason='Approval restated',
                            evidence=['reports/user-approval-v2.md'], services=['da-data'],
                            operations=['search_content'], scope='study', max_runs=5,
                            expires_at='2099-01-01T00:00:00Z')
        steps = self.steps(lambda: self.check(scope='study', packet_id=packet['packet_id']))
        self.assertEqual(steps,
                         [f'amend --project {self.project} --kind grant '
                          '--reason "<why the approval artifact changed>"',
                          f'task-status --project {self.project} --task t1 --status blocked '
                          '--executor-stopped --reason "stop the executor holding the old channels"',
                          f'task-status --project {self.project} --task t1 --status planned '
                          '--reason "reissue the packet"'])
        self.assertRealCommands(steps)

    def test_next_lists_the_legal_moves_for_an_active_project(self):
        board = self.tool.next_steps_for(ROOT, self.project)
        self.assertEqual(board['status'], 'active')
        joined = ' '.join(entry['command'] for entry in board['legal'])
        self.assertIn('--task t1', joined, 'a planned task must offer handoff and cancellation')
        self.assertIn('phase ', joined)

    def test_next_gives_a_stopped_project_exactly_one_move(self):
        self.tool.set_project_status(ROOT, self.project, status='stopped', reason='Awaiting approval')
        board = self.tool.next_steps_for(ROOT, self.project)
        self.assertEqual(board['legal'], [])
        self.assertEqual(len(board['blocked']), 1)
        self.assertIn('--to active', board['blocked'][0]['next'][0])
        # A consumer reads mode and note from every board, stopped ones included.
        self.assertEqual(sorted(board), ['blocked', 'legal', 'mode', 'note', 'phase', 'status'])

    def cancels(self, board, task_id='t1'):
        """The cancellation moves the board offers for one task."""
        return [entry['command'] for entry in board['legal']
                if '--status cancelled' in entry['command'] and f'--task {task_id}' in entry['command']]

    def assertNoOverlap(self, board):
        """No command may be offered and refused at once; the board would contradict itself."""
        legal = [entry['command'] for entry in board['legal']]
        blocked = [entry['command'] for entry in board['blocked']]
        self.assertEqual([], [command for command in legal if command in blocked], board)

    def test_next_offers_cancellation_from_every_open_task_state(self):
        """Cancellation is legal from planned, running, submitted and blocked alike."""
        self.assertEqual(len(self.cancels(self.tool.next_steps_for(ROOT, self.project, task_id='t1'))), 1)
        packet = self.handoff()
        self.tool.accept_assignment(ROOT, self.project, packet, self.receipt(packet))
        # A running task holds the phase, so cancelling it also confirms the executor stopped.
        board = self.tool.next_steps_for(ROOT, self.project, task_id='t1')
        self.assertEqual(self.cancels(board),
                         [f'task-status --project {self.project} --task t1 --status cancelled '
                          '--executor-stopped --reason "..."'])
        output = self.project / 'hypotheses/t1-v1.md'
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text('v1 finding')
        self.tool.update_task(ROOT, self.project, 't1', 'submitted', 'Artifacts returned',
                             ['hypotheses/t1-v1.md'], executor_stopped=True)
        self.assertEqual(len(self.cancels(self.tool.next_steps_for(ROOT, self.project, task_id='t1'))), 1)
        # A second task reaches blocked through the same gates: a running executor, then blocked.
        self.create('t2')
        packet = self.tool.handoff(ROOT, self.project, 't2', 'Work the evidence', ['research-brief.md'],
                                   model='current', outputs=['hypotheses/t2-v1.md'])
        self.tool.accept_assignment(ROOT, self.project, packet, self.receipt(packet, session_id='host:gate-2'))
        self.tool.update_task(ROOT, self.project, 't2', 'blocked', 'Executor stopped early', [],
                              executor_stopped=True)
        self.assertEqual(len(self.cancels(self.tool.next_steps_for(ROOT, self.project, task_id='t2'), 't2')), 1)

    def test_next_offers_the_blocked_move_a_running_task_may_take(self):
        # update_task allows running -> blocked and rebind_presteps names it, so a board
        # that omitted it left a running task with no legal repair but its cancellation.
        packet = self.handoff()
        self.tool.accept_assignment(ROOT, self.project, packet, self.receipt(packet))
        board = self.tool.next_steps_for(ROOT, self.project, task_id='t1')
        self.assertNoOverlap(board)
        moves = [entry['command'] for entry in board['legal'] if '--task t1' in entry['command']]
        self.assertIn(f'task-status --project {self.project} --task t1 --status blocked '
                      '--executor-stopped --reason "..."', moves, board['legal'])
        # The move is legal for real, not only on the board.
        state = self.tool.update_task(ROOT, self.project, 't1', 'blocked', 'Cannot continue', [],
                                      executor_stopped=True)
        self.assertEqual(state['tasks']['t1']['status'], 'blocked')

    def test_a_completed_project_is_refused_without_offering_the_reactivation(self):
        # A completed project is still active, so 'Project is not active' was false and
        # the repair it offered was refused with 'Project already has status active'.
        state = self.tool.project_state(ROOT, self.project)[0]
        state['phase'] = 'complete'
        (self.project / 'research-state.json').write_text(json.dumps(state))
        for label, call in (('handoff', lambda: self.handoff()),
                            ('accept', lambda: self.tool.accept_assignment(ROOT, self.project, {}, {}))):
            with self.subTest(command=label), self.assertRaisesRegex(
                    ValueError, 'Completed research reopens only through a new scope decision') as raised:
                call()
            self.assertNotIn('--to active', str(raised.exception))

    def test_next_explains_why_a_running_task_refuses_a_new_packet(self):
        packet = self.tool.handoff(ROOT, self.project, 't1', 'Work the evidence', ['research-brief.md'],
                                   model='current', outputs=['hypotheses/t1-v1.md'])
        self.tool.accept_assignment(ROOT, self.project, packet, self.receipt(packet))
        board = self.tool.next_steps_for(ROOT, self.project, task_id='t1')
        # The phase block names this task too, so the assertion picks out the packet
        # refusal itself instead of matching any entry that mentions the task.
        refusal = [entry for entry in board['blocked'] if entry['command'].startswith('handoff ')]
        self.assertEqual(len(refusal), 1, board['blocked'])
        self.assertIn('--task t1', refusal[0]['command'])
        self.assertIn('one task has at most one executor', refusal[0]['reason'])
        legal = ' '.join(entry['command'] for entry in board['legal'])
        self.assertIn(f'task-status --project {self.project} --task t1 --status submitted', legal)
        # The same executor holds the phase, so the phase move is refused here too.
        self.assertNotIn('phase ', legal, 'a running executor holds the phase decision')
        self.assertIn('A running executor holds the phase decision',
                      [entry['reason'] for entry in board['blocked']])

    def test_next_blocks_the_task_moves_an_open_blocker_halts(self):
        self.tool.update_blockers(ROOT, self.project, add='Human decision needed', reason='Approval missing')
        board = self.tool.next_steps_for(ROOT, self.project, task_id='t1')
        legal = ' '.join(entry['command'] for entry in board['legal'])
        self.assertNotIn('handoff ', legal, 'a task that resolves no open blocker must not be offered')
        halted = [entry for entry in board['blocked'] if '--task t1' in entry['command']]
        self.assertEqual(len(halted), 1, board['blocked'])
        self.assertIn('Open blockers halt unrelated work', halted[0]['reason'])
        self.assertIn(f'blockers --project {self.project} --resolve', halted[0]['next'][0])
        # Cancellation is not blocked work, so an ordinary blocker leaves it legal.
        self.assertEqual(len(self.cancels(board)), 1)

    def test_an_illegal_task_transition_names_the_moves_that_status_allows(self):
        """The dominant refusal class: it must name what is legal, not only what is not."""
        packet = self.handoff()
        self.tool.accept_assignment(ROOT, self.project, packet, self.receipt(packet))
        with self.assertRaisesRegex(ValueError, 'Illegal task status transition') as raised:
            self.tool.update_task(ROOT, self.project, 't1', 'planned', 'Jump straight back', [])
        text = str(raised.exception)
        self.assertIn('Next:', text, f'No repair offered: {text}')
        steps = [step.rstrip('.') for step in text.split(' Next: ')[1:]]
        # running -> planned is refused above, and the repair names the moves that
        # status allows, derived from the transition table the gate itself checks.
        # Every move out of running is refused without --executor-stopped, so the
        # step carries it: a repair that is itself refused is no repair at all.
        self.assertEqual(steps,
                         [f'task-status --project {self.project} --task t1 '
                          '--status blocked|submitted|cancelled --executor-stopped --reason "..."',
                          f'next --project {self.project} --task t1'])
        self.assertRealCommands(steps)
        self.tool.update_task(ROOT, self.project, 't1', 'blocked', 'Executor stopped', [], executor_stopped=True)
        self.tool.update_task(ROOT, self.project, 't1', 'planned', 'Reissue the packet', [])

    def test_a_task_gate_refusal_names_the_blockers_command_that_clears_it(self):
        """The four task gates raise the same halt; each must name its repair."""
        self.tool.update_blockers(ROOT, self.project, add='Human decision needed', reason='Approval missing')
        steps = self.steps(lambda: self.handoff())
        self.assertEqual(steps,
                         [f'blockers --project {self.project} --resolve <blocker-id> --reason "..."',
                          f'blockers --project {self.project} --edit <blocker-id> --text "..." --reason "..."'])
        self.assertRealCommands(steps)
        # A freeze-all is an explicit stop for every task, so only resolving it ends
        # the freeze; restating its text would leave the stop in place.
        self.tool.update_blockers(ROOT, self.project, add='Stop all work', reason='Emergency', freeze_all=True)
        steps = self.steps(lambda: self.handoff())
        self.assertEqual(steps,
                         [f'blockers --project {self.project} --resolve <blocker-id> --reason "..."'])
        self.assertRealCommands(steps)
        # The repair is real: resolving the freeze is what lets the handoff through,
        # once the ordinary blocker behind it is cleared too.
        self.tool.update_blockers(ROOT, self.project, resolve='b2', reason='Stop lifted')
        self.tool.update_blockers(ROOT, self.project, resolve='b1', reason='Approval recorded')
        self.assertIn('packet_id', self.handoff())

    def test_the_executor_and_job_gates_name_the_move_that_clears_them(self):
        """Leaving running needs the executor confirmed stopped and no job outstanding."""
        packet = self.handoff()
        self.tool.accept_assignment(ROOT, self.project, packet, self.receipt(packet))
        steps = self.steps(lambda: self.tool.update_task(ROOT, self.project, 't1', 'submitted',
                                                        'Artifacts returned', ['hypotheses/t1-v1.md']))
        self.assertEqual(steps, [f'task-status --project {self.project} --task t1 --status submitted '
                                 '--executor-stopped --reason "..."'])
        self.assertRealCommands(steps)
        # A job the host recorded as running outlives the executor's own claim to have
        # stopped, so the repair names the one command that reconciles it.
        self.tool.host_event(ROOT, self.project, 't1', 'job-1', 'running', 'Sandbox run started')
        steps = self.steps(lambda: self.tool.update_task(ROOT, self.project, 't1', 'submitted',
                                                        'Artifacts returned', ['hypotheses/t1-v1.md'],
                                                        executor_stopped=True))
        self.assertEqual(steps, [f'host-event --project {self.project} --task t1 --job job-1 '
                                 '--status succeeded|failed|cancelled --reason "..."'])
        self.assertRealCommands(steps)

    def test_the_phase_gates_name_the_command_that_clears_them(self):
        """A phase change is held by a running executor, an open blocker and a stopped project."""
        phase = lambda: self.tool.transition_phase(ROOT, self.project, 'ideation', 'Scope is bounded',
                                                  ['research-brief.md'])
        packet = self.handoff()
        self.tool.accept_assignment(ROOT, self.project, packet, self.receipt(packet))
        steps = self.steps(phase)
        self.assertEqual(steps, [f'task-status --project {self.project} --task t1 --status submitted '
                                 '--executor-stopped --reason "..." --evidence <paths>'])
        self.assertRealCommands(steps)
        self.tool.update_task(ROOT, self.project, 't1', 'cancelled', 'Work abandoned', [], executor_stopped=True)
        self.tool.update_blockers(ROOT, self.project, add='Human decision needed', reason='Approval missing')
        steps = self.steps(phase)
        self.assertEqual(steps, [f'blockers --project {self.project} --resolve <blocker-id> --reason "..."',
                                 f'blockers --project {self.project} --edit <blocker-id> --text "..." --reason "..."'])
        self.assertRealCommands(steps)
        # A stopped project has no legal task move at all, so naming task-status here
        # would offer a command the project gate refuses on sight.
        self.tool.update_blockers(ROOT, self.project, resolve='b1', reason='Approval recorded')
        self.tool.set_project_status(ROOT, self.project, status='stopped', reason='Planning only')
        steps = self.steps(phase)
        self.assertEqual(steps, [f'project-status --project {self.project} --to active '
                                 '--reason "<why the project resumes>"'])
        self.assertRealCommands(steps)

    def test_completing_a_phase_names_the_task_move_that_clears_it(self):
        state = self.tool.project_state(ROOT, self.project)[0]
        state['phase'] = 'review'
        (self.project / 'research-state.json').write_text(json.dumps(state))
        steps = self.steps(lambda: self.tool.transition_phase(ROOT, self.project, 'complete',
                                                             'Audits passed', ['research-brief.md']))
        self.assertEqual(steps, [f'task-status --project {self.project} --task t1 '
                                 '--status completed|cancelled --reason "..."'])
        self.assertRealCommands(steps)

    def test_an_expired_grant_names_the_authorize_that_renews_it(self):
        """The same expiry is read where the grant is issued and at every gate behind it."""
        expired = dict(mode='research', reason='Bounded channel', evidence=['reports/user-approval-v1.md'],
                       services=['da-data'], operations=['search_content'], scope='study', max_runs=3,
                       expires_at='2000-01-01T00:00:00Z')
        renewal = (f'authorize --project {self.project} --mode research --reason <reason> '
                   '--evidence <approval-path> --services da-data --operations search_content '
                   '--scope "study" --max-runs 3 --expires-at <iso>')
        self.assertEqual(self.steps(lambda: self.tool.authorize(ROOT, self.project, **expired)), [renewal])
        # A grant recorded before it lapsed is refused at the gate it guards, not only
        # at the command that issued it.
        state = self.tool.project_state(ROOT, self.project)[0]
        state['grant'] = {'evidence': {'path': 'reports/user-approval-v1.md',
                                       'sha256': self.tool.digest(self.project / 'reports/user-approval-v1.md')},
                          'services': ['da-data'], 'operations': ['search_content'], 'scope': 'study',
                          'max_runs': 3, 'expires_at': '2000-01-01T00:00:00Z'}
        steps = self.steps(lambda: self.tool.verify_grant(self.project, state))
        self.assertEqual(steps, [renewal])
        self.assertRealCommands(steps)

    def prepare_experiment(self):
        """Research mode, a grant of one run, the evaluation fields, a protocol and its task."""
        self.authorize(max_runs=1)
        self.tool.set_evaluation(ROOT, self.project, reason='Bounded measures', primary_measure='macro F1',
                                 baseline='Matched baseline', validation_plan='Grouped split',
                                 uncertainty_plan='Five paired seeds')
        self.protocol = self.write('experiments/h1/protocol.md', 'Frozen protocol for the first run')
        self.tool.set_protocol(ROOT, self.project, path=self.protocol, reason='Protocol frozen')
        self.tool.create_task(ROOT, self.project, 'run', 'Run the protocol', activity='experiment',
                              skill='graph-evaluation', role='experimenter', acceptance='Run completes')

    def test_an_exhausted_run_limit_names_the_authorize_that_raises_it(self):
        """The limit counts every experiment assignment, so the repair raises it or starts again."""
        self.prepare_experiment()
        packet = self.tool.handoff(ROOT, self.project, 'run', 'Run the protocol', [self.protocol],
                                   model='current', outputs=['experiments/h1/runs/run-001/analysis.md'])
        self.tool.accept_assignment(ROOT, self.project, packet, self.receipt(packet, session_id='host:run'))
        # Back to planned, because a second packet for a running task is refused for a
        # different reason entirely.
        self.tool.update_task(ROOT, self.project, 'run', 'blocked', 'Executor stopped', [], executor_stopped=True)
        self.tool.update_task(ROOT, self.project, 'run', 'planned', 'Reissue the packet', [])
        steps = self.steps(lambda: self.tool.handoff(ROOT, self.project, 'run', 'Run the protocol',
                                                    [self.protocol], model='current',
                                                    outputs=['experiments/h1/runs/run-002/analysis.md']))
        self.assertEqual(steps, [f'authorize --project {self.project} --mode research --reason <reason> '
                                 '--evidence <approval-path> --services da-data --operations search_content '
                                 '--scope "study" --max-runs 2 --expires-at <iso>',
                                 f'task --project {self.project} --task <new-id> --objective "..." '
                                 '--activity experiment --skill <skill> --role <role> --acceptance "..."'])
        self.assertRealCommands(steps)

    def test_the_task_and_tool_gates_name_the_blockers_command_that_clears_them(self):
        self.tool.update_blockers(ROOT, self.project, add='Human decision needed', reason='Approval missing')
        steps = self.steps(lambda: self.create('t2'))
        self.assertEqual(steps[0], f'blockers --project {self.project} --resolve <blocker-id> --reason "..."')
        self.assertRealCommands(steps)
        # The same halt at the tool gate, reachable only while a task is running.
        self.tool.update_blockers(ROOT, self.project, resolve='b1', reason='Approval recorded')
        self.authorize()
        packet = self.handoff()
        self.tool.accept_assignment(ROOT, self.project, packet, self.receipt(packet))
        self.tool.update_blockers(ROOT, self.project, add='Approval lapsed', reason='Renewal needed')
        steps = self.steps(lambda: self.check())
        self.assertEqual(steps[0], f'blockers --project {self.project} --resolve <blocker-id> --reason "..."')
        self.assertRealCommands(steps)

    def test_a_freeze_all_blocker_names_the_resolve_that_ends_the_freeze(self):
        packet = self.handoff()
        self.tool.accept_assignment(ROOT, self.project, packet, self.receipt(packet))
        self.write('hypotheses/t1-v1.md', 'v1 finding')
        self.tool.update_task(ROOT, self.project, 't1', 'submitted', 'Artifacts returned',
                             ['hypotheses/t1-v1.md'], executor_stopped=True)
        self.tool.update_blockers(ROOT, self.project, add='Stop all work', reason='Emergency', freeze_all=True)
        steps = self.steps(lambda: self.tool.update_task(ROOT, self.project, 't1', 'completed',
                                                        'Artifacts accepted', []))
        self.assertEqual(steps, [f'blockers --project {self.project} --resolve <blocker-id> --reason "..."'])
        self.assertRealCommands(steps)

    def test_next_lists_exactly_the_task_status_moves_update_task_allows(self):
        """Board and gate must agree: only completion is frozen, and only by a freeze-all.

        A blocker opened for a human decision while an executor is still running is
        the common case, and update_task lets that executor return its artifacts.
        """
        packet = self.handoff()
        self.tool.accept_assignment(ROOT, self.project, packet, self.receipt(packet))
        self.tool.update_blockers(ROOT, self.project, add='Human decision needed', reason='Approval missing')
        board = self.tool.next_steps_for(ROOT, self.project, task_id='t1')
        self.assertNoOverlap(board)
        legal = ' '.join(entry['command'] for entry in board['legal'])
        submitted = f'task-status --project {self.project} --task t1 --status submitted'
        self.assertIn(submitted, legal, 'an ordinary blocker does not halt a running executor')
        # The board claims it is legal, so the gate must accept it.
        output = self.project / 'hypotheses/t1-v1.md'
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text('v1 finding')
        self.tool.update_task(ROOT, self.project, 't1', 'submitted', 'Artifacts returned',
                             ['hypotheses/t1-v1.md'], executor_stopped=True)
        # A freeze-all is the only blocker state that freezes completion, and even
        # it leaves cancellation legal.
        self.tool.update_blockers(ROOT, self.project, add='Stop all work', reason='Emergency', freeze_all=True)
        board = self.tool.next_steps_for(ROOT, self.project, task_id='t1')
        self.assertNoOverlap(board)
        legal = ' '.join(entry['command'] for entry in board['legal'])
        self.assertNotIn('--status completed', legal, 'a freeze-all freezes completion')
        self.assertIn(f'task-status --project {self.project} --task t1 --status cancelled', legal)
        with self.assertRaisesRegex(ValueError, 'frozen by a freeze-all blocker'):
            self.tool.update_task(ROOT, self.project, 't1', 'completed', 'Artifacts accepted', [])
        # The cancellation the board still offers is legal for real.
        self.tool.update_task(ROOT, self.project, 't1', 'cancelled', 'Work abandoned', [])

    def test_next_blocks_the_phase_move_while_a_blocker_is_open(self):
        """transition_phase refuses under an open blocker, so the board must not offer it."""
        self.tool.update_blockers(ROOT, self.project, add='Human decision needed', reason='Approval missing')
        with self.assertRaisesRegex(ValueError, 'Resolve project blockers before changing phase'):
            self.tool.transition_phase(ROOT, self.project, 'ideation', 'Scope is bounded', ['research-brief.md'])
        board = self.tool.next_steps_for(ROOT, self.project)
        self.assertNoOverlap(board)
        legal = ' '.join(entry['command'] for entry in board['legal'])
        self.assertNotIn('phase ', legal, 'an open blocker closes the phase decision too')
        halted = [entry for entry in board['blocked'] if entry['command'].startswith('phase ')]
        self.assertEqual(len(halted), 1, board['blocked'])
        self.assertIn(f'blockers --project {self.project} --resolve', halted[0]['next'][0])
        self.assertIn(f'blockers --project {self.project} --edit', ' '.join(halted[0]['next']))
        # The repair is real: resolving the blocker is what makes the move legal again.
        self.tool.update_blockers(ROOT, self.project, resolve='b1', reason='Approval recorded')
        board = self.tool.next_steps_for(ROOT, self.project)
        self.assertIn(f'phase --project {self.project} --to ideation',
                      ' '.join(entry['command'] for entry in board['legal']))

    def test_next_offers_only_cancellation_under_a_freeze_all_blocker(self):
        """A freeze halts work, not the escape: cancelling stale work clears the stop."""
        # A submitted task is where completion is offered, so it pins both halves:
        # the freeze stops completion, never cancellation.
        self.create('t2')
        packet = self.tool.handoff(ROOT, self.project, 't2', 'Work the evidence', ['research-brief.md'],
                                   model='current', outputs=['hypotheses/t2-v1.md'])
        self.tool.accept_assignment(ROOT, self.project, packet, self.receipt(packet, session_id='host:gate-2'))
        output = self.project / 'hypotheses/t2-v1.md'
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text('v2 finding')
        self.tool.update_task(ROOT, self.project, 't2', 'submitted', 'Artifacts returned',
                             ['hypotheses/t2-v1.md'], executor_stopped=True)
        self.tool.update_blockers(ROOT, self.project, add='Stop all work', reason='Emergency', freeze_all=True)
        board = self.tool.next_steps_for(ROOT, self.project)
        self.assertNoOverlap(board)
        legal = ' '.join(entry['command'] for entry in board['legal'])
        self.assertNotIn('handoff ', legal, 'a freeze halts every work move')
        self.assertNotIn('--status completed', legal, 'a freeze-all freezes completion')
        self.assertEqual(len(self.cancels(board)), 1)
        self.assertEqual(len(self.cancels(board, 't2')), 1)
        # Every move left for a task is its cancellation, plus the rework a submitted
        # task may still be sent back for: update_task freezes completion alone.
        for task_id in ('t1', 't2'):
            with self.subTest(task=task_id):
                moves = [entry['command'] for entry in board['legal'] if f'--task {task_id}' in entry['command']]
                expected = self.cancels(board, task_id)
                if task_id == 't2':
                    expected = expected + [f'task-status --project {self.project} --task t2 '
                                           '--status planned --reason "..."']
                self.assertEqual(sorted(moves), sorted(expected), board['legal'])
                halted = [entry for entry in board['blocked'] if f'--task {task_id}' in entry['command']]
                self.assertNotEqual(halted, [], board['blocked'])
                for entry in halted:
                    self.assertIn('freeze-all', entry['reason'])
                    self.assertIn(f'blockers --project {self.project} --resolve', entry['next'][0])

    def test_status_and_brief_name_the_human_action_the_project_waits_on(self):
        self.tool.set_project_status(ROOT, self.project, status='stopped', reason='Awaiting approval')
        self.assertIn('Waiting on', self.tool.status(ROOT, self.project))
        self.assertIn('Waiting on', self.tool.render_brief(self.tool.project_state(ROOT, self.project)[0]))

    def test_operations_documents_every_refusal_repair(self):
        text = (ROOT / 'references' / 'operations.md').read_text()
        for command in ('next', 'bindings', 'amend'):
            with self.subTest(command=command):
                self.assertIn(f'`{command}`', text)
        for refusal in ('Project is stopped', 'Tool access requires an active assignment',
                        'Task input', 'Unassigned run artifact', 'hash mismatch'):
            with self.subTest(refusal=refusal):
                self.assertIn(refusal, text)
