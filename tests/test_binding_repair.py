"""Hash bindings are visible and repairable instead of silent."""

import contextlib
import hashlib
import io
import json
from pathlib import Path
import shlex
import tempfile
import unittest

from test_framework import ROOT, load_tool

# A core-owned root document is a snapshot input, so its drift says so instead of
# promising a repair the core cannot make without undoing its own decision.
CORE_DRIFT_DETAIL = 'core-owned snapshot input; drift is recorded at completion'

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
        return [problem.get('detail') for problem in self.tool.watch(ROOT, self.project)['anomalies']
                if problem['reason'] == 'binding-drift']

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

    def assign_input(self, task_id, evidence, output):
        """A running task assigned one input; no output has been submitted yet."""
        self.create(task_id)
        self.tool.assign(ROOT, self.project, task_id, 'Work the evidence', [evidence], model='current',
                         outputs=[output], session_mode='current', session_reason='Small bounded task')

    def submit_with_input(self, task_id, evidence, output):
        """One task assigned a single input, with its output already submitted."""
        self.assign_input(task_id, evidence, output)
        self.write(output, 'Bounded result')
        self.tool.update_task(ROOT, self.project, task_id, 'submitted', 'Executor stopped', [output],
                              executor_stopped=True)

    def running_task(self, task_id, output, session_id):
        """A running task assigned one versioned input; no output has been returned yet."""
        self.create(task_id)
        evidence = self.write(f'hypotheses/{task_id}-input-v1.md', f'Supplied evidence for {task_id}')
        packet = self.tool.handoff(ROOT, self.project, task_id, 'Work the evidence', [evidence],
                                   model='current', outputs=[output])
        self.tool.accept_assignment(ROOT, self.project, packet, self.receipt(packet, session_id=session_id))
        return evidence

    def reflection_body(self, task_id):
        """A reflection proposal citing the one artifact that task returned."""
        artifact = f'reports/{task_id}-v1.md'
        return {'observation': 'The measured gain is below the target',
                'protocol_check': 'No deviation from the frozen protocol',
                'counterevidence': 'The matched baseline remains competitive',
                'alternatives': 'Attribute the gap to a data shift',
                'next_options': ['Replicate on an independent split'],
                'prediction': 'The gap disappears on an independent split',
                'decision': 'Replicate before drawing conclusions',
                'evidence': [{'path': artifact, 'sha256': self.tool.digest(self.project / artifact)}]}

    def run_cli(self, argv):
        """Run one command through the CLI; returns its exit code and everything it printed."""
        with contextlib.redirect_stdout(io.StringIO()) as out, contextlib.redirect_stderr(io.StringIO()) as err:
            code = self.tool.main(argv)
        return code, out.getvalue() + err.getvalue()

    def build_repair_fixture(self):
        """Every binding kind, each broken, across a task left in each open state.

        A frozen protocol is left out on purpose: an evidence audit has to bind it, so
        a drifted protocol and a re-verifiable audit cannot coexist in one project.
        """
        goal = self.write('hypotheses/goal-v1.md', GOAL_DOSSIER)
        self.tool.set_goal(ROOT, self.project, goal, 'Scope selected from the dossier')
        findings = self.write('findings.md', 'Bounded finding with its matching raw result')
        raw = self.write('experiments/H1/runs/run-001/results/metrics.json', '{"score": 0.7}')
        audit = self.audit('reviews/evidence-audit.json', [findings, raw],
                           'The reported gain is bound to raw evidence', 'Run artifacts under experiments/')
        self.tool.set_audit(ROOT, self.project, kind='evidence', path=audit, status='verified',
                            reason='Audit binds findings and raw evidence')
        sessions = {'open-running': 'host:s-running', 'open-submitted': 'host:s-submitted',
                    'open-blocked': 'host:s-blocked', 'open-planned': 'host:s-planned'}
        for task_id, session_id in sessions.items():
            self.running_task(task_id, f'reports/{task_id}-v1.md', session_id)
        for task_id in ('open-submitted', 'open-planned'):
            self.write(f'reports/{task_id}-v1.md', f'Bounded result from {task_id}')
            self.tool.update_task(ROOT, self.project, task_id, 'submitted', 'Executor stopped',
                                  [f'reports/{task_id}-v1.md'], executor_stopped=True)
        self.write('reports/open-blocked-v1.md', 'Partial result returned before the stop')
        self.tool.update_task(ROOT, self.project, 'open-blocked', 'blocked', 'Executor stopped early',
                              ['reports/open-blocked-v1.md'], executor_stopped=True)
        self.tool.update_task(ROOT, self.project, 'open-planned', 'planned', 'Rework requested', [])
        reflection = self.write('reports/reflection-v1.json', json.dumps(self.reflection_body('open-blocked')))
        self.tool.record_reflection(ROOT, self.project, 'open-blocked', reflection,
                                    'Review before selecting a follow-up')
        # The repair names a new versioned report, so making that step runnable means
        # writing the successor the core has to author anyway.
        self.write('reports/reflection-v2.json', json.dumps(self.reflection_body('open-blocked')))
        # Break every binding, each in a way its own repair accepts: the audit and the
        # reflection keep the subjects and sources their gates recheck.
        self.write(self.approval, 'Approved bounded channel, restated')
        self.write(goal, GOAL_DOSSIER.replace('one paired run per seed', 'two paired runs per seed'))
        payload = json.loads((self.project / audit).read_text())
        self.write(audit, json.dumps(dict(payload, summary='Revised: the audit binds its subjects'),
                                     ensure_ascii=False, indent=2))
        payload = json.loads((self.project / reflection).read_text())
        self.write(reflection, json.dumps(dict(payload, decision='Replicate, then reconsider the baseline'),
                                          ensure_ascii=False, indent=2))
        for task_id in sessions:
            self.write(f'hypotheses/{task_id}-input-v1.md', f'Supplied evidence for {task_id}, corrected')
        for task_id in ('open-submitted', 'open-planned'):
            self.write(f'reports/{task_id}-v1.md', f'Bounded result from {task_id}, corrected')

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

    def test_watch_names_a_deleted_binding_as_missing_and_not_as_a_mismatch(self):
        """A deleted file and an edited file are repaired differently, so they read differently."""
        protocol = self.write('experiments/H1/protocol.md', 'Frozen protocol for the paired runs')
        self.tool.set_protocol(ROOT, self.project, path=protocol, reason='Core froze the protocol')
        (self.project / protocol).unlink()
        details = self.drift_details()
        self.assertIn(f'protocol: {protocol} file is missing', details)
        self.assertEqual([], [text for text in details if 'no longer matches its recorded hash' in text],
                         details)

    def test_watch_still_reports_a_deleted_file_on_a_finished_task(self):
        # Content drift on a finished task is history; a deleted file is not a consequence
        # of finishing the work, so it stays visible.
        for status in ('completed', 'cancelled'):
            with self.subTest(status=status):
                task_id = f'deleted-{status}'
                self.create(task_id)
                _, artifact = self.submit_version(task_id, 1)
                self.tool.update_task(ROOT, self.project, task_id, status, 'Core closed the task', [])
                self.assertEqual(self.state()['tasks'][task_id]['status'], status)
                (self.project / artifact).unlink()
                self.assertIn(f'{task_id} submitted artifact: {artifact} file is missing',
                              self.drift_details())

    def test_bindings_report_reads_the_bytes_on_disk_and_not_the_hash_memo(self):
        """A report is a claim about the bytes on disk now, so the memo must not serve it."""
        target = self.project / self.approval
        expected = self.tool.digest(target, cached=False)
        self.tool.HASH_MEMO.clear()
        self.addCleanup(self.tool.HASH_MEMO.clear)
        self.assertEqual(self.tool.digest(target), expected, 'The memo starts from the real bytes')
        self.assertEqual(len(self.tool.HASH_MEMO), 1, 'Only this one file was hashed')
        key = next(iter(self.tool.HASH_MEMO))
        self.tool.HASH_MEMO[key] = 'a hash read before the file was edited'
        self.assertEqual(self.row_for(self.approval)['current_sha256'], expected)

    def repair_steps(self, call):
        """The repair commands one refusal carries, each stripped of its sentence stop."""
        with self.assertRaises(ValueError) as raised:
            call()
        text = str(raised.exception)
        self.assertIn('Next:', text, f'No repair offered: {text}')
        return [step.rstrip('.') for step in text.split(' Next: ')[1:]]

    def assertRealCommands(self, steps):
        """Every fix names a registered command and only real flags of it."""
        commands = {name: dict(options) for name, _, options in self.tool.CLI}
        for step in steps:
            name = step.split()[0]
            with self.subTest(step=step):
                self.assertIn(name, commands, f'{name} is not a registered command')
                for flag in [word for word in step.split() if word.startswith('--')]:
                    self.assertIn(flag[2:], commands[name], f'{name} has no {flag}')

    def test_every_binding_fix_is_a_command_built_with_the_project_and_task(self):
        """A fix is a command the core can issue now, so it names the project and task it applies to."""
        self.build_every_binding()
        fix_of = {row['binding']: row['fix']
                  for row in self.tool.binding_report(ROOT, self.project)['bindings']}
        self.assertEqual(sorted(fix_of),
                         ['evidence review', 'final review', 'goal dossier', 'grant evidence', 'protocol',
                          'reflection artifact', 'run assignment input', 'run submitted artifact'])
        # A completed task is terminal: no command can repair its bindings, and naming
        # one would be refused the moment the core issued it.
        for binding in ('run assignment input', 'run submitted artifact'):
            with self.subTest(binding=binding):
                self.assertIsNone(fix_of[binding], f'{binding} must not promise a repair')
        commands = {name: fix for name, fix in fix_of.items() if fix is not None}
        for binding, fix in commands.items():
            with self.subTest(binding=binding):
                self.assertIn(f'--project {self.project}', fix, f'{binding} names no project to repair')
        self.assertIn('--task run', commands['reflection artifact'])
        # The bound version is already recorded and reflect records a new one, so the
        # fix names the successor, derived from the bound path.
        self.assertEqual(commands['reflection artifact'],
                         f'reflect --project {self.project} --task run --path reports/reflection-v2.json '
                         '--reason "<record a new versioned report>"')
        self.assertEqual(commands['evidence review'],
                         f'set-audit --project {self.project} --kind evidence '
                         '--path reviews/evidence-audit.json --status verified --reason "..."')
        self.assertRealCommands(commands.values())
        # A task that can still be replanned does get the command naming it.
        self.tool.create_task(ROOT, self.project, 'sub2', 'Replannable work', activity='analysis',
                              skill='brainstorming-research-ideas', role='strategist',
                              acceptance='Each explanation has a falsifier')
        # A versioned input, not a core-owned root record: only the former is a frozen
        # contract the core can reissue by replanning the task.
        self.tool.assign(ROOT, self.project, 'sub2', 'Work the evidence',
                         [self.write('hypotheses/sub2-input-v1.md', 'Supplied evidence for the rework')],
                         model='current', outputs=['hypotheses/sub2-v1.md'],
                         session_mode='current', session_reason='Small bounded task')
        rows = {row['binding']: row for row in self.tool.binding_report(ROOT, self.project)['bindings']}
        # sub2 is running, so the reissue alone is refused: the fix is the stop and the
        # reissue is the step that follows it.
        self.assertEqual(rows['sub2 assignment input']['fix'],
                         f'task-status --project {self.project} --task sub2 --status blocked '
                         '--executor-stopped --reason "stop the executor holding the old channels"')
        self.assertEqual(rows['sub2 assignment input']['fix_next'],
                         [f'task-status --project {self.project} --task sub2 --status planned '
                          '--reason "reissue the packet"'])
        self.assertRealCommands([rows['sub2 assignment input']['fix']] + rows['sub2 assignment input']['fix_next'])

    def test_a_drifted_input_of_a_running_task_names_the_stop_before_the_reissue(self):
        """running -> planned is not a transition, so a running task needs both steps."""
        self.assign_input('live', self.write('hypotheses/live-input-v1.md', 'Supplied evidence'),
                          'reports/live-v1.md')
        self.assertEqual(self.state()['tasks']['live']['status'], 'running',
                         'The row must be judged while the task cannot legally be replanned')
        self.write('hypotheses/live-input-v1.md', 'Supplied evidence, corrected')
        row = self.row_for('hypotheses/live-input-v1.md')
        self.assertFalse(row['holds'])
        self.assertEqual(row['fix'],
                         f'task-status --project {self.project} --task live --status blocked '
                         '--executor-stopped --reason "stop the executor holding the old channels"')
        self.assertEqual(row['fix_next'],
                         [f'task-status --project {self.project} --task live --status planned '
                          '--reason "reissue the packet"'])
        self.assertRealCommands([row['fix']] + row['fix_next'])
        # Both steps are legal in this order, and the jump they replace is not.
        with self.assertRaisesRegex(ValueError, 'Illegal task status transition'):
            self.tool.update_task(ROOT, self.project, 'live', 'planned', 'Jump straight back', [])
        for status, stopped in (('blocked', True), ('planned', False)):
            self.tool.update_task(ROOT, self.project, 'live', status, 'Executor stopped', [],
                                  executor_stopped=stopped)

    def test_a_core_owned_record_bound_as_a_grant_artifact_is_repaired(self):
        """The core-writes-then-completes cycle is an assignment input, not any path."""
        # A grant citing a core-owned record used to inherit the exemption, so the row
        # was neither broken nor repairable nor visible in watch while the gate still
        # refused with 'User grant hash mismatch' and no repair.
        for path in self.tool.CORE_MUTABLE_RECORDS:
            with self.subTest(path=path):
                self.tool.authorize(ROOT, self.project, mode='research', reason='Bounded retrieval',
                                    evidence=[path], services=['da-data'], operations=['search_content'],
                                    scope='study', max_runs=3, expires_at='2099-01-01T00:00:00Z')
                self.write(path, f'{path} rewritten after the grant was authorized')
                row = self.row_for(path)
                self.assertEqual(row['binding'], 'grant evidence')
                self.assertFalse(row['holds'], f'{path} must be reported as broken, not exempted')
                self.assertEqual(row['fix'], f'amend --project {self.project} --kind grant '
                                             '--reason "<why the approval artifact changed>"')
                broken = [row['path'] for row in self.tool.binding_report(ROOT, self.project)['broken']]
                self.assertIn(path, broken, 'A broken grant binding must be counted as broken')
                self.assertIn(f'grant evidence: {path} no longer matches its recorded hash',
                              self.drift_details())

    def test_every_repair_a_binding_or_amend_offers_can_be_run(self):
        """A repair that is itself refused is no repair: run every step the CLI offers."""
        self.build_repair_fixture()
        # Each sequence is run from the state it was offered in, so no step can be
        # excused by a change an earlier sequence made.
        base = (self.project / 'research-state.json').read_bytes()
        sequences = []
        for row in self.tool.binding_report(ROOT, self.project)['bindings']:
            if row['fix'] is None:
                self.assertEqual(row['fix_next'], [], row)
                continue
            sequences.append((row['binding'], [row['fix']] + row['fix_next']))
        for kind in ('grant', 'goal'):
            result = self.tool.amend_binding(ROOT, self.project, kind, f'Corrected the {kind} artifact')
            self.assertNotEqual(result['next'], [], f'amend {kind} invalidated nothing')
            sequences.append((f'amend {kind}', result['next']))
        self.assertNotEqual(sequences, [], 'No repair was collected, so the test proves nothing')
        for label, steps in sequences:
            (self.project / 'research-state.json').write_bytes(base)
            for step in steps:
                with self.subTest(repair=label, step=step):
                    self.assertRealCommands([step])
                    code, output = self.run_cli(shlex.split(step))
                    self.assertEqual(code, 0, f'{label}: {step}\n{output}')
        """A watchdog degrades: a file it cannot read is reported, never raised."""
        protocol = self.write('experiments/H1/protocol.md', 'Frozen protocol for the paired runs')
        self.tool.set_protocol(ROOT, self.project, path=protocol, reason='Core froze the protocol')
        target = self.project / protocol
        mode = target.stat().st_mode
        target.chmod(0o000)
        self.addCleanup(target.chmod, mode)
        row = self.row_for(protocol)
        self.assertIsNone(row['current_sha256'])
        self.assertFalse(row['holds'])
        self.assertEqual(row['detail'], 'unreadable')
        self.assertIn(f'protocol: {protocol} unreadable', self.drift_details())

    def test_a_bound_path_that_escapes_the_project_is_unreadable(self):
        """A hand-edited state must not point the hasher outside the project."""
        protocol = self.write('experiments/H1/protocol.md', 'Frozen protocol for the paired runs')
        self.tool.set_protocol(ROOT, self.project, path=protocol, reason='Core froze the protocol')
        outside = Path(self.temp.name) / 'outside.md'
        outside.write_text('Private text outside the project')
        state = self.state()
        state['protocol'] = {'path': '../outside.md', 'sha256': self.tool.digest(outside)}
        (self.project / 'research-state.json').write_text(json.dumps(state))
        row = self.row_for('../outside.md')
        self.assertIsNone(row['current_sha256'])
        self.assertFalse(row['holds'])
        self.assertEqual(row['detail'], 'unreadable')

    def test_a_row_without_a_recorded_hash_says_so(self):
        """A broken row always says why: here the state recorded no hash to compare against."""
        protocol = self.write('experiments/H1/protocol.md', 'Frozen protocol for the paired runs')
        self.tool.set_protocol(ROOT, self.project, path=protocol, reason='Core froze the protocol')
        state = self.state()
        state['protocol'] = {'path': protocol}
        (self.project / 'research-state.json').write_text(json.dumps(state))
        row = self.row_for(protocol)
        self.assertIsNone(row['recorded_sha256'])
        self.assertFalse(row['holds'])
        self.assertEqual(row['detail'], 'no recorded hash')

    def receipt(self, packet, session_id='host:s1', **changes):
        """A host receipt for one packet, computed the way the tool recomputes it."""
        result = dict(schema_version=8, packet_id=packet['packet_id'], task_id=packet['task_id'],
                      source_revision=packet['source_revision'], accepted=True,
                      accepted_at='2026-01-01T00:00:00+00:00',
                      actual_role=packet['target_role']['id'], actual_model='provider/model-a',
                      actual_session_mode=packet['session']['mode'], actual_session_id=session_id,
                      session_isolation_verified=packet['session']['mode'] == 'fresh',
                      session_notes='Host execution identity and history verified',
                      state_hash_checked=True, core_hash_checked=True, skill_hash_checked=True,
                      evidence_hashes_checked=True)
        result['packet_sha256'] = hashlib.sha256(json.dumps(
            packet, sort_keys=True, ensure_ascii=False, separators=(',', ':'),
            allow_nan=False).encode('utf-8')).hexdigest()
        result.update(changes)
        return result

    def run_task(self):
        self.tool.create_task(ROOT, self.project, 't1', 'Compare explanations', activity='analysis',
                              skill='brainstorming-research-ideas', role='strategist',
                              acceptance='Each explanation has a falsifier')
        packet = self.tool.handoff(ROOT, self.project, 't1', 'Work the evidence', ['research-brief.md'],
                                   model='current', outputs=['hypotheses/t1-v1.md'])
        self.tool.accept_assignment(ROOT, self.project, packet, self.receipt(packet, session_id='host:s1'))
        return packet

    def test_core_record_input_drift_is_recorded_not_refused(self):
        # findings.md is the sink the core writes when it accepts results, so a
        # completion check demanding it stay byte-identical is unsatisfiable.
        self.tool.create_task(ROOT, self.project, 't9', 'Synthesize accepted findings',
                              activity='analysis', skill='results-synthesis', role='analyst',
                              acceptance='Bounded synthesis')
        packet = self.tool.handoff(ROOT, self.project, 't9', 'Synthesize', ['findings.md'],
                                   model='current', outputs=['reports/synthesis-v1.md'])
        self.tool.accept_assignment(ROOT, self.project, packet, self.receipt(packet, session_id='host:s9'))
        self.write('reports/synthesis-v1.md', 'Synthesis with limits')
        self.write('findings.md', 'Accepted finding recorded by the core')
        state = self.tool.update_task(ROOT, self.project, 't9', 'submitted', 'Returned synthesis',
                                      ['reports/synthesis-v1.md'], executor_stopped=True)
        state = self.tool.update_task(ROOT, self.project, 't9', 'completed', 'Core inspected it', [])
        self.assertEqual(state['tasks']['t9']['status'], 'completed')
        self.assertIn('findings.md', state['history'][-1].get('input_drift', []))

    def test_a_drifted_core_input_of_a_running_task_is_not_a_broken_binding(self):
        # The core rewriting findings.md is what deciding looks like, so the row stays
        # visible with the bytes it really measured but names no repair and is no fault.
        self.assign_input('t9', 'findings.md', 'reports/t9-synthesis-v1.md')
        self.assertEqual(self.state()['tasks']['t9']['status'], 'running',
                         'The row must be judged while the task cannot legally be replanned')
        self.write('findings.md', 'Accepted finding recorded by the core')
        report = self.tool.binding_report(ROOT, self.project)
        self.assertEqual(report['broken'], [], 'Legal core drift must not be reported as broken')
        row = self.row_for('findings.md')
        self.assertFalse(row['holds'], 'The row still reports what is on disk now')
        self.assertEqual(row['detail'], CORE_DRIFT_DETAIL)
        self.assertIsNone(row['fix'], 'No command repairs a drift deciding caused')
        self.assertEqual(self.drift_details(), [], 'watch must not report legal core drift')

    def test_input_drift_is_recorded_only_on_the_completion_event(self):
        # `input_drift` is a statement about the completion recheck. A submitted, blocked
        # or cancelled event never checked inputs, and an empty list there would read as
        # "no drift" when it means "not checked".
        self.submit_with_input('t6', 'findings.md', 'reports/t6-v1.md')
        self.assertNotIn('input_drift', self.state()['history'][-1])
        self.write('findings.md', 'Rewritten before the completion decision')
        state = self.tool.update_task(ROOT, self.project, 't6', 'completed', 'Core inspected it', [])
        self.assertIn('input_drift', state['history'][-1])
        self.assertEqual(state['history'][-1]['input_drift'], ['findings.md'])

    def test_completion_records_no_drift_when_the_core_input_is_unchanged(self):
        self.submit_with_input('t7', 'findings.md', 'reports/t7-v1.md')
        state = self.tool.update_task(ROOT, self.project, 't7', 'completed', 'Core inspected it', [])
        self.assertEqual(state['history'][-1]['input_drift'], [], 'Nothing drifted, so nothing is recorded')
        self.assertTrue(self.row_for('findings.md')['holds'])

    def test_a_deleted_core_record_is_recorded_and_not_reported_as_broken(self):
        self.submit_with_input('t8', 'findings.md', 'reports/t8-v1.md')
        (self.project / 'findings.md').unlink()
        row = self.row_for('findings.md')
        self.assertFalse(row['holds'])
        self.assertIsNone(row['current_sha256'], 'The row keeps the real measurement')
        self.assertEqual(row['detail'], CORE_DRIFT_DETAIL)
        self.assertIsNone(row['fix'])
        self.assertEqual(self.tool.binding_report(ROOT, self.project)['broken'], [])
        self.assertEqual(self.drift_details(), [])
        state = self.tool.update_task(ROOT, self.project, 't8', 'completed', 'Core inspected it', [])
        self.assertEqual(state['history'][-1]['input_drift'], ['findings.md'])

    def test_every_core_owned_record_drifts_without_refusing(self):
        # Membership in the constant is what exempts a path, so each member is checked
        # here and a look-alike that is not a member is checked below.
        for index, path in enumerate(self.tool.CORE_MUTABLE_RECORDS):
            with self.subTest(path=path):
                task_id = f'core-{index}'
                self.submit_with_input(task_id, path, f'reports/core-{index}-v1.md')
                self.write(path, f'Core rewrote {path} after the assignment')
                state = self.tool.update_task(ROOT, self.project, task_id, 'completed', 'Core inspected it', [])
                self.assertEqual(state['tasks'][task_id]['status'], 'completed')
                self.assertEqual(state['history'][-1]['input_drift'], [path])
                broken = [row['path'] for row in self.tool.binding_report(ROOT, self.project)['broken']]
                self.assertNotIn(path, broken)
                self.assertEqual(self.drift_details(), [])

    def test_a_versioned_copy_of_a_core_record_name_is_still_refused(self):
        # reports/findings.md shares its basename with the core-owned root record but is
        # a versioned artifact, so the basename alone does not buy the exemption.
        evidence = self.write('reports/findings.md', 'Versioned copy of the accepted findings')
        self.submit_with_input('t5', evidence, 'reports/t5-v1.md')
        self.write(evidence, 'Versioned copy, revised')
        with self.assertRaisesRegex(ValueError, 'Task input reports/findings.md changed') as raised:
            self.tool.update_task(ROOT, self.project, 't5', 'completed', 'Core inspected it', [])
        self.assertIn('--task t5 --status planned', str(raised.exception))

    def test_changed_versioned_input_is_refused_with_a_repair(self):
        self.run_task()
        # A running task cannot take a second packet, so pass one is returned and the
        # task replanned: the reissue is what binds the versioned input of pass two.
        self.write('hypotheses/t1-v1.md', 'Mechanism and falsifier')
        self.tool.update_task(ROOT, self.project, 't1', 'submitted', 'Returned', ['hypotheses/t1-v1.md'],
                              executor_stopped=True)
        self.tool.update_task(ROOT, self.project, 't1', 'planned', 'Rework requested', [])
        evidence = self.write('literature/review-v1.md', 'Sourced notes')
        packet = self.tool.handoff(ROOT, self.project, 't1', 'Work the evidence', [evidence],
                                   model='current', outputs=['hypotheses/t1-v2.md'])
        self.tool.accept_assignment(ROOT, self.project, packet, self.receipt(packet, session_id='host:s2'))
        self.write(evidence, 'Sourced notes, revised')
        self.write('hypotheses/t1-v2.md', 'Mechanism and falsifier')
        self.tool.update_task(ROOT, self.project, 't1', 'submitted', 'Returned', ['hypotheses/t1-v2.md'],
                              executor_stopped=True)
        with self.assertRaisesRegex(ValueError, 'Next:') as raised:
            self.tool.update_task(ROOT, self.project, 't1', 'completed', 'Core inspected it', [])
        self.assertIn('task-status', str(raised.exception))

    def test_amend_rebinds_the_grant_and_reports_invalidated_assignments(self):
        self.write('tools/da-data.json', json.dumps({'server': 'da-data', 'schema_version': 1,
                                                     'operations': {'search_content': {'classification': 'read',
                                                                                       'basis': 'auto'}}}))
        self.tool.create_task(ROOT, self.project, 't1', 'Retrieve sources', activity='analysis',
                              skill='literature-review', role='analyst', acceptance='Bounded coverage',
                              tools=['da-data:search_content'])
        packet = self.tool.handoff(ROOT, self.project, 't1', 'Retrieve', ['research-brief.md'],
                                   model='current', outputs=['literature/review-v1.md'])
        self.tool.accept_assignment(ROOT, self.project, packet, self.receipt(packet, session_id='host:s1'))
        before = self.tool.digest(self.project / self.approval, cached=False)
        self.write(self.approval, 'Approved bounded channel; corrected arXiv title')
        reason = 'Corrected a false title in the approval'
        result = self.tool.amend_binding(ROOT, self.project, 'grant', reason)
        self.assertNotEqual(result['from_sha256'], result['to_sha256'])
        self.assertEqual(result['from_sha256'], before)
        self.assertEqual(result['to_sha256'], self.tool.digest(self.project / self.approval, cached=False))
        self.assertEqual([row['task_id'] for row in result['invalidated']], ['t1'])
        event = self.state()['history'][-1]
        self.assertEqual(event['action'], 'grant-rebound')
        # A rebound hash that is not recorded is a correction nobody can reconstruct,
        # so every field the event carries is pinned here.
        self.assertEqual(event['from_sha256'], before)
        self.assertEqual(event['to_sha256'], result['to_sha256'])
        self.assertEqual(event['to_sha256'], self.tool.digest(self.project / self.approval, cached=False))
        self.assertEqual(event['path'], self.approval)
        self.assertEqual(event['invalidated'], result['invalidated'])
        self.assertEqual(event['invalidated'],
                         [{'task_id': 't1', 'packet_id': packet['packet_id'], 'status': 'running'}])
        self.assertEqual(event['reason'], reason)

    def test_amend_invalidates_a_running_task_and_not_a_finished_one(self):
        """A finished task answered for the old binding; only live work is invalidated."""
        self.submit_with_input('done', 'research-brief.md', 'reports/done-v1.md')
        self.tool.update_task(ROOT, self.project, 'done', 'completed', 'Core accepted it', [])
        self.assign_input('live', 'research-brief.md', 'reports/live-v1.md')
        self.assertEqual(self.state()['tasks']['done']['status'], 'completed')
        self.assertEqual(self.state()['tasks']['live']['status'], 'running')
        self.write(self.approval, 'Approved bounded channel; corrected arXiv title')
        result = self.tool.amend_binding(ROOT, self.project, 'grant', 'Corrected a false title')
        self.assertEqual([row['task_id'] for row in result['invalidated']], ['live'])
        # Both snapshots really diverge, so what excludes `done` is its status and not
        # a snapshot that happens still to match the contract.
        contract = self.tool.execution_contract(self.state())
        for task_id in ('done', 'live'):
            with self.subTest(task_id=task_id):
                self.assertNotEqual(self.state()['tasks'][task_id]['assignments'][-1]['execution_contract'],
                                    contract)

    def test_amend_rebinds_the_protocol_and_reports_invalidated_assignments(self):
        protocol = self.write('experiments/H1/protocol.md', 'Frozen protocol for the paired runs')
        self.tool.set_protocol(ROOT, self.project, path=protocol, reason='Core froze the protocol')
        before = self.tool.digest(self.project / protocol, cached=False)
        self.assign_input('p1', 'research-brief.md', 'reports/p1-v1.md')
        self.write(protocol, 'Frozen protocol for the paired runs, with a matched split')
        reason = 'Protocol gained the matched split'
        result = self.tool.amend_binding(ROOT, self.project, 'protocol', reason)
        self.assertNotEqual(result['from_sha256'], result['to_sha256'])
        self.assertEqual(result['from_sha256'], before)
        self.assertEqual(result['to_sha256'], self.tool.digest(self.project / protocol, cached=False))
        self.assertEqual([row['task_id'] for row in result['invalidated']], ['p1'])
        event = self.state()['history'][-1]
        self.assertEqual(event['action'], 'protocol-rebound')
        self.assertEqual(event['from_sha256'], before)
        self.assertEqual(event['to_sha256'], result['to_sha256'])
        self.assertEqual(event['path'], protocol)
        self.assertEqual(event['invalidated'], result['invalidated'])
        self.assertEqual(event['reason'], reason)

    def test_amend_rebinds_the_goal_and_reports_invalidated_assignments(self):
        goal = self.write('hypotheses/goal-v1.md', GOAL_DOSSIER)
        self.tool.set_goal(ROOT, self.project, goal, 'Scope selected from the dossier')
        before = self.tool.digest(self.project / goal, cached=False)
        self.assign_input('g1', 'research-brief.md', 'reports/g1-v1.md')
        self.write(goal, GOAL_DOSSIER.replace('one paired run per seed', 'two paired runs per seed'))
        reason = 'Dossier corrected its resource estimate'
        result = self.tool.amend_binding(ROOT, self.project, 'goal', reason)
        self.assertNotEqual(result['from_sha256'], result['to_sha256'])
        self.assertEqual(result['from_sha256'], before)
        self.assertEqual(result['to_sha256'], self.tool.digest(self.project / goal, cached=False))
        self.assertEqual([row['task_id'] for row in result['invalidated']], ['g1'])
        event = self.state()['history'][-1]
        self.assertEqual(event['action'], 'goal-rebound')
        self.assertEqual(event['from_sha256'], before)
        self.assertEqual(event['to_sha256'], result['to_sha256'])
        self.assertEqual(event['path'], goal)
        self.assertEqual(event['invalidated'], result['invalidated'])
        self.assertEqual(event['reason'], reason)

    def test_amend_refuses_to_rebind_what_was_never_frozen(self):
        """`amend` rebinds a frozen artifact; filling an empty slot is another command's job."""
        for kind, command, path in (('protocol', 'set-protocol', 'experiments/<id>/protocol.md'),
                                    ('goal', 'set-goal', 'hypotheses/goal-v1.md')):
            with self.subTest(kind=kind):
                steps = self.repair_steps(
                    lambda: self.tool.amend_binding(ROOT, self.project, kind, f'No {kind} was frozen'))
                self.assertEqual(steps, [f'{command} --project {self.project} --path {path} --reason "..."'])
                self.assertRealCommands(steps)

    def test_amend_refuses_to_rebind_a_grant_that_was_never_authorized(self):
        state = self.state()
        state['grant'] = None
        (self.project / 'research-state.json').write_text(json.dumps(state))
        steps = self.repair_steps(
            lambda: self.tool.amend_binding(ROOT, self.project, 'grant', 'Nothing was authorized'))
        self.assertEqual(steps, [f'authorize --project {self.project} --mode <planning|research> '
                                 '--reason <reason> --evidence <approval-path> --services <services> '
                                 '--operations <operations> --scope "<scope>" --max-runs <n> '
                                 '--expires-at <iso>'])
        self.assertRealCommands(steps)

    def test_amend_refuses_to_rewrite_a_contract_field(self):
        with self.assertRaisesRegex(ValueError, 'grant, protocol, goal'):
            self.tool.amend_binding(ROOT, self.project, 'objective', 'Not a rebinding')
