"""Tool semantics registry: catalog ingestion, classification, confirmation and gating."""

import contextlib
import hashlib
import io
import json
from pathlib import Path
import shlex
import tempfile
import unittest

from test_framework import ROOT, load_tool


class ToolSemanticsTests(unittest.TestCase):
    def setUp(self):
        self.tool = load_tool()
        self.temp = tempfile.TemporaryDirectory(dir=ROOT)
        self.addCleanup(self.temp.cleanup)
        self.project = Path(self.temp.name) / 'project'
        self.tool.initialize(ROOT, self.project, 'Evaluate a bounded research question')

    def state(self):
        return json.loads((self.project / 'research-state.json').read_text())

    def write(self, name, text):
        path = self.project / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        return name

    def ingest(self, tools, server='da-data', name='tools/catalog-dump.json'):
        path = self.write(name, json.dumps({'tools': tools}))
        return self.tool.ingest_catalog(ROOT, self.project, server, path, 'Host exported the catalog')

    def authorize(self, mode, services, operations):
        approval = self.write('reports/user-approval-v1.md', 'Approved bounded channel')
        return self.tool.authorize(ROOT, self.project, mode=mode, reason='Bounded channel',
                                   evidence=[approval], services=services, operations=operations,
                                   scope='graph-study', max_runs=10, expires_at='2099-01-01T00:00:00Z')

    def receipt(self, packet, session_id='host:tools'):
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

    def channel_task(self, task_id, operations):
        """A planned analysis task whose channels are declared, not inferred from its objective."""
        return self.tool.create_task(ROOT, self.project, task_id, 'Retrieve sources', activity='analysis',
                                     skill='literature-review', role='analyst', acceptance='Bounded coverage',
                                     tools=[f'da-data:{name}' for name in operations])

    def complete(self, task_id):
        """Drive a planned task to completed: the terminal state no repair can leave."""
        outputs = [f'literature/{task_id}.md']
        packet = self.tool.handoff(ROOT, self.project, task_id, 'Retrieve sources', ['research-brief.md'],
                                   model='current', outputs=outputs)
        self.tool.accept_assignment(ROOT, self.project, packet, self.receipt(packet))
        self.write(outputs[0], 'Findings with provenance, limits and open questions')
        return self.tool.submit(ROOT, self.project, task_id, 'Core verified the artifact', outputs, verdict='met')

    def refusal(self, call):
        """The message and the repair steps of one refusal."""
        with self.assertRaises(ValueError) as raised:
            call()
        text = str(raised.exception)
        self.assertIn('Next:', text, f'No repair offered: {text}')
        return text, [step.rstrip('.') for step in text.split(' Next: ')[1:]]

    def run_cli(self, argv):
        """Run one command through the CLI and return its exit code and output."""
        with contextlib.redirect_stdout(io.StringIO()) as captured:
            code = self.tool.main(argv)
        return code, captured.getvalue()

    def assert_real_commands(self, steps):
        """Every step names a registered command and only real flags of it."""
        commands = {name: dict(options) for name, _, options in self.tool.CLI}
        for step in steps:
            name = step.split()[0]
            with self.subTest(step=step):
                self.assertIn(name, commands, f'{name} is not a registered command')
                for flag in [word for word in step.split() if word.startswith('--')]:
                    self.assertIn(flag[2:], commands[name], f'{name} has no {flag}')

    def test_catalog_ingest_classifies_from_server_evidence(self):
        registry = self.ingest([
            {'name': 'search_content', 'description': 'Search indexed documents'},
            {'name': 'create_query_job', 'description': 'Submit a query job',
             'annotations': {'destructiveHint': False}},
            {'name': 'analyse_data', 'description': 'Run an analysis',
             'input_schema': {'properties': {'sql': {'type': 'string'}}}},
            {'name': 'get_chart_data', 'description': 'Fetch chart rows',
             'annotations': {'readOnlyHint': True}},
        ])
        operations = registry['operations']
        self.assertEqual(operations['search_content']['classification'], 'read')
        self.assertEqual(operations['create_query_job']['classification'], 'write')
        self.assertEqual(operations['analyse_data']['classification'], 'unknown')
        self.assertEqual(operations['get_chart_data']['classification'], 'read')
        self.assertEqual({name: entry['basis'] for name, entry in operations.items()},
                         {'search_content': 'auto', 'create_query_job': 'auto',
                          'analyse_data': 'auto', 'get_chart_data': 'auto'})

    def test_write_evidence_overrides_a_read_only_hint(self):
        registry = self.ingest([{'name': 'get_or_create_row',
                                 'description': 'Fetch a row when present',
                                 'annotations': {'readOnlyHint': True}}])
        self.assertEqual(registry['operations']['get_or_create_row']['classification'], 'write')

    def test_confirmation_survives_reingest_and_resets_on_drift(self):
        tool = {'name': 'analyse_data', 'description': 'Run an analysis',
                'input_schema': {'properties': {'sql': {'type': 'string'}}}}
        self.ingest([tool])
        confirmed = self.tool.confirm_semantics(ROOT, self.project, 'da-data', 'analyse_data',
                                                'write', 'It submits a warehouse job')
        self.assertEqual(confirmed['operations']['analyse_data']['basis'], 'confirmed')
        # Re-ingesting the identical catalog keeps the user's answer.
        again = self.ingest([tool])
        self.assertEqual(again['operations']['analyse_data']['classification'], 'write')
        self.assertEqual(again['operations']['analyse_data']['basis'], 'confirmed')
        # A changed description is drift: the answer no longer applies.
        drifted = self.ingest([dict(tool, description='Run an analysis with side effects')])
        self.assertEqual(drifted['operations']['analyse_data']['classification'], 'unknown')
        self.assertEqual(drifted['operations']['analyse_data']['basis'], 'auto')

    def test_planning_grants_require_read_classified_operations(self):
        self.ingest([
            {'name': 'search_content', 'description': 'Search indexed documents'},
            {'name': 'create_query_job', 'description': 'Submit a query job'},
            {'name': 'analyse_data', 'description': 'Run an analysis',
             'input_schema': {'properties': {'sql': {'type': 'string'}}}},
        ])

        def authorize(operations):
            return self.authorize('planning', ['da-data'], operations)

        state = authorize(['search_content'])
        self.assertEqual(state['grant']['operations'], ['search_content'])
        for operations in (['create_query_job'], ['analyse_data']):
            with self.subTest(operations=operations), self.assertRaisesRegex(ValueError, 'read-classified'):
                authorize(operations)
        # The user's one-time answer unlocks the ambiguous operation for planning.
        self.tool.confirm_semantics(ROOT, self.project, 'da-data', 'analyse_data', 'read',
                                    'Warehouse-side analysis only reads')
        state = authorize(['analyse_data'])
        self.assertEqual(state['grant']['operations'], ['analyse_data'])

    def test_check_tool_reports_semantics_and_needs_confirmation(self):
        self.ingest([{'name': 'analyse_data', 'description': 'Run an analysis',
                      'input_schema': {'properties': {'sql': {'type': 'string'}}}}])
        self.authorize('research', ['da-data'], ['analyse_data'])
        self.tool.set_evaluation(ROOT, self.project, primary_measure='macro F1', baseline='Matched',
                                 validation_plan='Grouped split', uncertainty_plan='Five seeds',
                                 reason='Core accepted the protocol')
        protocol = self.write('experiments/H1/protocol.md', 'Frozen protocol')
        self.tool.set_protocol(ROOT, self.project, path=protocol, reason='Core froze the protocol')
        self.tool.create_task(ROOT, self.project, 'run', 'Use da-data analyse_data in graph-study',
                              activity='experiment', skill='experiment-execution', role='experimenter',
                              acceptance='Report protocol-bound measurements', tools=['da-data:analyse_data'])
        packet = self.tool.handoff(ROOT, self.project, 'run', 'Run the frozen protocol', [protocol],
                                  model='current', outputs=['experiments/H1/runs/run-001/analysis.md'])
        self.tool.accept_assignment(ROOT, self.project, packet, self.receipt(packet))
        result = self.tool.check_tool(ROOT, self.project, task_id='run', packet_id=packet['packet_id'],
                                      server='da-data', operation='analyse_data', scope='graph-study')
        self.assertTrue(result['allowed'])
        self.assertTrue(result['needs_confirmation'])
        self.assertEqual(result['operation_semantics']['classification'], 'unknown')
        # After the user answers once, the same call carries the confirmed semantics.
        self.tool.confirm_semantics(ROOT, self.project, 'da-data', 'analyse_data', 'write',
                                    'It submits a warehouse job')
        result = self.tool.check_tool(ROOT, self.project, task_id='run', packet_id=packet['packet_id'],
                                      server='da-data', operation='analyse_data', scope='graph-study')
        self.assertTrue(result['allowed'])
        self.assertFalse(result['needs_confirmation'])
        self.assertEqual(result['operation_semantics']['classification'], 'write')

    def test_read_classified_channel_works_in_planning(self):
        self.ingest([{'name': 'search_content', 'description': 'Search indexed documents'}])
        self.authorize('planning', ['da-data'], ['search_content'])
        self.tool.create_task(ROOT, self.project, 'scope-1',
                              'Search da-data search_content in graph-study',
                              activity='analysis', skill='literature-review', role='analyst',
                              acceptance='Bounded retrieval with coverage limits',
                              tools=['da-data:search_content'])
        packet = self.tool.handoff(ROOT, self.project, 'scope-1', 'Bounded retrieval', ['research-brief.md'],
                                   model='current', outputs=['literature/review-v1.md'])
        self.tool.accept_assignment(ROOT, self.project, packet, self.receipt(packet))
        result = self.tool.check_tool(ROOT, self.project, task_id='scope-1', packet_id=packet['packet_id'],
                                      server='da-data', operation='search_content', scope='graph-study')
        self.assertTrue(result['allowed'])
        self.assertFalse(result['needs_confirmation'])
        self.assertEqual(result['operation_semantics']['classification'], 'read')
        # The executor is told where the classification came from, so a confirmed
        # answer over a catalog entry is not read as one with no server evidence.
        self.assertEqual(result['operation_semantics']['provenance'], 'catalog')

    def test_operation_semantics_names_a_classification_without_server_evidence(self):
        self.ingest([{'name': 'search_content', 'description': 'Search indexed documents'}])
        self.tool.confirm_semantics(ROOT, self.project, 'host-web', 'fetch', 'read',
                                    'Core-authored entry; the host exports no catalog')
        classified = self.tool.operation_semantics(self.project, 'da-data', 'search_content')
        authored = self.tool.operation_semantics(self.project, 'host-web', 'fetch')
        self.assertEqual(classified['provenance'], 'catalog')
        self.assertEqual(authored['provenance'], 'core-authored')
        self.assertEqual(authored['basis'], 'confirmed')
        # A server that never exported anything still classifies as unknown.
        unknown = self.tool.operation_semantics(self.project, 'never-seen', 'fetch')
        self.assertEqual(unknown['classification'], 'unknown')
        self.assertEqual(unknown['provenance'], 'none')

    def test_tool_calls_are_recorded_against_preflight_tokens(self):
        self.ingest([{'name': 'search_content', 'description': 'Search indexed documents'}])
        self.authorize('planning', ['da-data'], ['search_content'])
        self.tool.create_task(ROOT, self.project, 'scope-1',
                              'Search da-data search_content in graph-study',
                              activity='analysis', skill='literature-review', role='analyst',
                              acceptance='Bounded retrieval with coverage limits',
                              tools=['da-data:search_content'])
        packet = self.tool.handoff(ROOT, self.project, 'scope-1', 'Bounded retrieval', ['research-brief.md'],
                                   model='current', outputs=['literature/review-v1.md'])
        self.tool.accept_assignment(ROOT, self.project, packet, self.receipt(packet))
        result = self.tool.check_tool(ROOT, self.project, task_id='scope-1', packet_id=packet['packet_id'],
                                      server='da-data', operation='search_content', scope='graph-study')
        token = result['preflight_token']
        # A wrong or fabricated token is refused; the record must match the check.
        with self.assertRaisesRegex(ValueError, 'token'):
            self.tool.record_tool_call(ROOT, self.project, task_id='scope-1', packet_id=packet['packet_id'],
                                       server='da-data', operation='search_content', scope='graph-study',
                                       token='0' * 64)
        state = self.tool.record_tool_call(ROOT, self.project, task_id='scope-1', packet_id=packet['packet_id'],
                                           server='da-data', operation='search_content', scope='graph-study',
                                           token=token)
        event = state['history'][-1]
        self.assertEqual(event['action'], 'tool-call-recorded')
        self.assertEqual(event['token'], token)
        # The token binds the facts: a different request cannot reuse it.
        other = self.tool.check_tool(ROOT, self.project, task_id='scope-1', packet_id=packet['packet_id'],
                                     server='da-data', operation='search_content', scope='graph-study')
        self.assertEqual(other['preflight_token'], token)

    def test_tool_call_burst_is_recorded_with_count(self):
        self.ingest([{'name': 'search_content', 'description': 'Search indexed documents'}])
        self.authorize('planning', ['da-data'], ['search_content'])
        self.tool.create_task(ROOT, self.project, 'scope-1',
                              'Search da-data search_content in graph-study',
                              activity='analysis', skill='literature-review', role='analyst',
                              acceptance='Bounded retrieval with coverage limits',
                              tools=['da-data:search_content'])
        packet = self.tool.handoff(ROOT, self.project, 'scope-1', 'Bounded retrieval', ['research-brief.md'],
                                   model='current', outputs=['literature/review-v1.md'])
        self.tool.accept_assignment(ROOT, self.project, packet, self.receipt(packet))
        token = self.tool.check_tool(ROOT, self.project, task_id='scope-1', packet_id=packet['packet_id'],
                                     server='da-data', operation='search_content', scope='graph-study')['preflight_token']
        state = self.tool.record_tool_call(ROOT, self.project, task_id='scope-1', packet_id=packet['packet_id'],
                                           server='da-data', operation='search_content', scope='graph-study',
                                           token=token, count=5)
        event = state['history'][-1]
        self.assertEqual(event['count'], 5)
        self.assertIn('5 identical calls', event['reason'])
        for bad in (0, -1, 101, 'many'):
            with self.subTest(count=bad), self.assertRaises(ValueError):
                self.tool.record_tool_call(ROOT, self.project, task_id='scope-1', packet_id=packet['packet_id'],
                                           server='da-data', operation='search_content', scope='graph-study',
                                           token=token, count=bad)

    def test_prose_coincidence_does_not_assign_a_channel(self):
        # 'stat' is in the grant and 'statistics' appears in the objective; under the
        # old substring check this coincidence passed. Only the structural assignment
        # may authorize the call.
        self.ingest([{'name': 'stat', 'description': 'Show table statistics'},
                     {'name': 'search_content', 'description': 'Search indexed documents'}])
        self.authorize('planning', ['da-data'], ['stat', 'search_content'])
        self.tool.create_task(ROOT, self.project, 'scope-1',
                              'Review corpus statistics via da-data search_content',
                              activity='analysis', skill='literature-review', role='analyst',
                              acceptance='Bounded retrieval with coverage limits',
                              tools=['da-data:search_content'])
        packet = self.tool.handoff(ROOT, self.project, 'scope-1', 'Bounded retrieval', ['research-brief.md'],
                                   model='current', outputs=['literature/review-v1.md'])
        self.tool.accept_assignment(ROOT, self.project, packet, self.receipt(packet))
        with self.assertRaisesRegex(ValueError, 'was not assigned'):
            self.tool.check_tool(ROOT, self.project, task_id='scope-1', packet_id=packet['packet_id'],
                                 server='da-data', operation='stat', scope='graph-study')
        result = self.tool.check_tool(ROOT, self.project, task_id='scope-1', packet_id=packet['packet_id'],
                                      server='da-data', operation='search_content', scope='graph-study')
        self.assertTrue(result['allowed'])

    def test_invalid_tool_assignments_are_rejected_at_creation(self):
        for index, value in enumerate(('da-data', 'da-data:', ':search', 'da-data:Search',
                                        'da data:search', 42, None, {'server': 'x'})):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.tool.create_task(ROOT, self.project, f't{index}', 'Inspect supplied evidence',
                                      activity='analysis', skill='literature-review', role='analyst',
                                      acceptance='Bounded', tools=[value])
        task = self.tool.create_task(ROOT, self.project, 'valid', 'Inspect supplied evidence',
                                     activity='analysis', skill='literature-review', role='analyst',
                                     acceptance='Bounded', tools=['da-data:search_content'])
        self.assertEqual(task['tools'], [{'server': 'da-data', 'operation': 'search_content'}])

    def test_a_channel_is_declared_once(self):
        # The same channel twice is one channel, so the second declaration says
        # nothing and is refused instead of silently collapsing.
        with self.assertRaisesRegex(ValueError, 'Duplicate tool assignment: da-data:search_content'):
            self.channel_task('t1', ['search_content', 'search_content'])
        self.assertNotIn('t1', self.state()['tasks'], 'A refused declaration must not create the task')

    def test_ingest_reports_tasks_whose_frozen_channels_disappeared(self):
        self.ingest([{'name': 'search_content', 'description': 'Search indexed documents'},
                     {'name': 'fetch', 'description': 'Fetch a document'}])
        self.tool.create_task(ROOT, self.project, 't1', 'Retrieve sources', activity='analysis',
                              skill='literature-review', role='analyst', acceptance='Bounded coverage',
                              tools=['da-data:search_content', 'da-data:fetch'])
        registry = self.ingest([{'name': 'search_content', 'description': 'Search indexed documents'}],
                               name='tools/catalog-dump-2.json')
        self.assertEqual([row['operation'] for row in registry['orphaned_channels']], ['fetch'])
        self.assertEqual(registry['orphaned_channels'][0]['task_id'], 't1')

    def test_orphan_collateral_is_returned_and_never_persisted(self):
        # The file describes the server. The stranded channels are collateral of this
        # one decision, so they travel with it and are never written beside the
        # operations that stranded them.
        self.ingest([{'name': 'search_content', 'description': 'Search indexed documents'},
                     {'name': 'fetch', 'description': 'Fetch a document'}])
        self.channel_task('t1', ['fetch'])
        registry = self.ingest([{'name': 'search_content', 'description': 'Search indexed documents'}],
                               name='tools/catalog-dump-2.json')
        self.assertEqual(registry['orphaned_channels'],
                         [{'task_id': 't1', 'status': 'planned', 'server': 'da-data', 'operation': 'fetch'}])
        self.assertEqual(len(registry['next']), 1)
        step = registry['next'][0]
        # The dropped channel cannot be the replacement: the new catalog does not
        # export it, so the repair names a placeholder and the reason says what it
        # replaces.
        for fragment in ('amend ', '--kind tools', '--task t1', '--tool <server:operation>',
                         'replaces da-data:fetch', '--reason'):
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, step)
        self.assert_real_commands(registry['next'])
        on_disk = json.loads((self.project / 'tools' / 'da-data.json').read_text())
        self.assertNotIn('orphaned_channels', on_disk)
        self.assertNotIn('next', on_disk)
        self.assertEqual(sorted(on_disk), ['catalog_sha256', 'operations', 'schema_version', 'server'])

    def test_the_repair_a_rewrite_offers_can_be_run(self):
        # A vocabulary check cannot catch this defect: the repair used to name the
        # channel this very catalog had just dropped, so following it was refused
        # with 'No registry entry', and the second-order repair it pointed at then
        # resurrected the dropped operation. Only running the offered command proves
        # the replacement it names is reachable.
        self.ingest([{'name': 'search_content', 'description': 'Search indexed documents'},
                     {'name': 'fetch', 'description': 'Fetch a document'}])
        self.channel_task('t1', ['fetch'])
        registry = self.ingest([{'name': 'search_content', 'description': 'Search indexed documents'}],
                               name='tools/catalog-dump-2.json')
        # Substitute the one channel the rewritten registry still exports.
        command = registry['next'][0].replace('<server:operation>', 'da-data:search_content')
        code, _ = self.run_cli(shlex.split(command))
        self.assertEqual(code, 0, command)
        self.assertEqual(self.state()['tasks']['t1']['tools'],
                         [{'server': 'da-data', 'operation': 'search_content'}])

    def test_orphan_repair_for_a_task_that_is_not_planned_names_the_state_change(self):
        # A channel may only be rebound while the task is planned, so promising the
        # amend alone would name a command that is certain to be refused.
        self.ingest([{'name': 'fetch', 'description': 'Fetch a document'}])
        self.channel_task('t-running', ['fetch'])
        packet = self.tool.handoff(ROOT, self.project, 't-running', 'Retrieve', ['research-brief.md'],
                                  model='current', outputs=['literature/review-v1.md'])
        self.tool.accept_assignment(ROOT, self.project, packet, self.receipt(packet))
        registry = self.ingest([{'name': 'search_content', 'description': 'Search indexed documents'}],
                               name='tools/catalog-dump-2.json')
        self.assertEqual([row['status'] for row in registry['orphaned_channels']], ['running'])
        self.assertEqual(registry['next'],
                         [f'task-status --project {self.project} --task t-running --status blocked '
                          '--executor-stopped --reason "stop the executor holding the old channels"',
                          f'task-status --project {self.project} --task t-running --status planned '
                          '--reason "reissue the packet"'])
        self.assert_real_commands(registry['next'])

    def test_ingest_event_records_the_channels_it_stranded(self):
        self.ingest([{'name': 'fetch', 'description': 'Fetch a document'}])
        self.channel_task('t1', ['fetch'])
        self.ingest([{'name': 'search_content', 'description': 'Search indexed documents'}],
                    name='tools/catalog-dump-2.json')
        ingested = [row for row in self.state()['history'] if row['action'] == 'tool-catalog-ingested']
        self.assertEqual(ingested[-1]['orphaned_channels'],
                         [{'task_id': 't1', 'status': 'planned', 'server': 'da-data', 'operation': 'fetch'}])

    def test_orphaned_channels_ignores_finished_tasks(self):
        # A completed or cancelled task can never be repaired, so reporting it as
        # stranded would name work no command can fix.
        self.ingest([{'name': 'fetch', 'description': 'Fetch a document'}])
        self.channel_task('t-done', ['fetch'])
        self.complete('t-done')
        self.channel_task('t-cancelled', ['fetch'])
        self.tool.update_task(ROOT, self.project, 't-cancelled', 'cancelled', 'Objective changed', [])
        self.channel_task('t-planned', ['fetch'])
        self.assertEqual(self.state()['tasks']['t-done']['status'], 'completed')
        self.assertEqual(self.state()['tasks']['t-cancelled']['status'], 'cancelled')
        registry = self.ingest([{'name': 'search_content', 'description': 'Search indexed documents'}],
                               name='tools/catalog-dump-2.json')
        self.assertEqual([row['task_id'] for row in registry['orphaned_channels']], ['t-planned'])

    def test_view_registry_names_the_tasks_a_channel_is_frozen_into(self):
        self.ingest([{'name': 'search_content', 'description': 'Search indexed documents'}])
        # Declared in reverse order: the view is sorted, so it is not declaration order.
        self.channel_task('t2', ['search_content'])
        self.channel_task('t1', ['search_content'])
        self.channel_task('t3', [])
        view = self.tool.view_registry(ROOT, self.project)
        self.assertEqual(view['servers']['da-data']['operations']['search_content']['used_by'], ['t1', 't2'])
        # The view is read-only: the file describes the server, not the tasks naming it.
        path = self.project / 'tools' / 'da-data.json'
        self.assertNotIn('used_by', path.read_text())
        on_disk = json.loads(path.read_text())
        for name, entry in on_disk['operations'].items():
            with self.subTest(operation=name):
                self.assertNotIn('used_by', entry)

    def test_amend_tools_repairs_a_planned_task_after_a_registry_rewrite(self):
        self.ingest([{'name': 'search_content', 'description': 'Search indexed documents'}])
        self.tool.create_task(ROOT, self.project, 't1', 'Retrieve sources', activity='analysis',
                              skill='literature-review', role='analyst', acceptance='Bounded coverage',
                              tools=['da-data:fetch'])
        result = self.tool.amend_binding(ROOT, self.project, 'tools', 'Registry merged into retrieval',
                                         task_id='t1', tools=['da-data:search_content'])
        self.assertEqual(result['to'], [{'server': 'da-data', 'operation': 'search_content'}])
        state = json.loads((self.project / 'research-state.json').read_text())
        self.assertEqual(state['tasks']['t1']['tools'], [{'server': 'da-data', 'operation': 'search_content'}])

    def test_amend_tools_event_carries_both_channel_sets(self):
        # A channel carries no hash, so the decision is recorded as the channels
        # themselves: what the task declared before and what it declares now.
        self.ingest([{'name': 'search_content', 'description': 'Search indexed documents'}])
        self.channel_task('t1', ['fetch'])
        self.tool.amend_binding(ROOT, self.project, 'tools', 'Registry merged into retrieval',
                                task_id='t1', tools=['da-data:search_content'])
        event = self.state()['history'][-1]
        self.assertEqual(event['action'], 'task-tools-amended')
        self.assertEqual(event['task_id'], 't1')
        self.assertEqual(event['from'], [{'server': 'da-data', 'operation': 'fetch'}])
        self.assertEqual(event['to'], [{'server': 'da-data', 'operation': 'search_content'}])

    def test_amend_tools_with_no_channels_clears_a_stranded_one(self):
        # Dropping a channel the registry can no longer satisfy is a legal repair.
        self.ingest([{'name': 'search_content', 'description': 'Search indexed documents'}])
        self.channel_task('t1', ['fetch'])
        result = self.tool.amend_binding(ROOT, self.project, 'tools', 'Drop the stranded channel',
                                         task_id='t1', tools=[])
        self.assertEqual(result['from'], [{'server': 'da-data', 'operation': 'fetch'}])
        self.assertEqual(result['to'], [])
        task = self.state()['tasks']['t1']
        self.assertEqual(task['tools'], [])
        event = self.state()['history'][-1]
        self.assertEqual(event['action'], 'task-tools-amended')
        self.assertEqual(event['from'], [{'server': 'da-data', 'operation': 'fetch'}])
        self.assertEqual(event['to'], [])

    def test_amend_tools_without_channels_is_refused_not_cleared(self):
        # The CLI default was [], so an omitted channel list wiped every channel the
        # task declared with no warning. Omitting them is a refusal; the library's
        # empty list stays legal, because there it is an explicit decision.
        self.ingest([{'name': 'search_content', 'description': 'Search indexed documents'}])
        self.channel_task('t1', ['search_content'])
        text, steps = self.refusal(lambda: self.tool.amend_binding(
            ROOT, self.project, 'tools', 'Forgot to name the channel', task_id='t1'))
        self.assertIn('--tool', text)
        self.assertIn('--no-tools', text)
        self.assertEqual(len(steps), 2)
        self.assert_real_commands(steps)
        self.assertEqual(self.state()['tasks']['t1']['tools'],
                         [{'server': 'da-data', 'operation': 'search_content'}])
        self.tool.amend_binding(ROOT, self.project, 'tools', 'Cleared on purpose', task_id='t1', tools=[])
        self.assertEqual(self.state()['tasks']['t1']['tools'], [])

    def test_cli_amend_tools_omitting_the_channel_list_clears_nothing(self):
        self.ingest([{'name': 'search_content', 'description': 'Search indexed documents'}])
        self.channel_task('t1', ['search_content'])
        code, _ = self.run_cli(['amend', '--project', str(self.project), '--kind', 'tools',
                                '--task', 't1', '--reason', 'No channel named'])
        self.assertEqual(code, 2, 'An omitted channel list must be refused, not applied')
        self.assertEqual(self.state()['tasks']['t1']['tools'],
                         [{'server': 'da-data', 'operation': 'search_content'}])
        # --no-tools is the explicit way to say the task needs no channel.
        code, _ = self.run_cli(['amend', '--project', str(self.project), '--kind', 'tools',
                                '--task', 't1', '--no-tools', '--reason', 'Channel no longer needed'])
        self.assertEqual(code, 0)
        self.assertEqual(self.state()['tasks']['t1']['tools'], [])

    def test_amend_tools_refuses_a_running_task(self):
        self.ingest([{'name': 'search_content', 'description': 'Search indexed documents'}])
        self.tool.create_task(ROOT, self.project, 't1', 'Retrieve sources', activity='analysis',
                              skill='literature-review', role='analyst', acceptance='Bounded coverage',
                              tools=['da-data:search_content'])
        packet = self.tool.handoff(ROOT, self.project, 't1', 'Retrieve', ['research-brief.md'],
                                  model='current', outputs=['literature/review-v1.md'])
        self.tool.accept_assignment(ROOT, self.project, packet, self.receipt(packet))
        with self.assertRaisesRegex(ValueError, 'planned'):
            self.tool.amend_binding(ROOT, self.project, 'tools', 'Too late', task_id='t1',
                                    tools=['da-data:search_content'])

    def test_amend_tools_repair_names_only_legal_transitions(self):
        # running -> planned is not a transition, so the repair used to name a move
        # that is refused on sight. It must name the stop first, then the return.
        self.ingest([{'name': 'search_content', 'description': 'Search indexed documents'}])
        self.channel_task('t1', ['search_content'])
        packet = self.tool.handoff(ROOT, self.project, 't1', 'Retrieve', ['research-brief.md'],
                                  model='current', outputs=['literature/review-v1.md'])
        self.tool.accept_assignment(ROOT, self.project, packet, self.receipt(packet))
        text, steps = self.refusal(lambda: self.tool.amend_binding(
            ROOT, self.project, 'tools', 'Replace the channel', task_id='t1',
            tools=['da-data:search_content']))
        self.assertEqual(steps,
                         [f'task-status --project {self.project} --task t1 --status blocked '
                          '--executor-stopped --reason "stop the executor holding the old channels"',
                          f'task-status --project {self.project} --task t1 --status planned '
                          '--reason "reissue the packet"'])
        self.assert_real_commands(steps)
        # The repair is executable: the direct jump is illegal, the two moves are not.
        with self.assertRaisesRegex(ValueError, 'Illegal task status transition'):
            self.tool.update_task(ROOT, self.project, 't1', 'planned', 'Jump straight back', [])
        self.tool.update_task(ROOT, self.project, 't1', 'blocked', 'Executor stopped', [],
                              executor_stopped=True)
        self.tool.update_task(ROOT, self.project, 't1', 'planned', 'Reissue the packet', [])
        self.assertEqual(self.state()['tasks']['t1']['status'], 'planned')

    def test_amend_tools_names_the_confirmation_an_unclassified_channel_needs(self):
        self.ingest([{'name': 'search_content', 'description': 'Search indexed documents'}])
        self.channel_task('t1', ['search_content'])
        text, steps = self.refusal(lambda: self.tool.amend_binding(
            ROOT, self.project, 'tools', 'Wrong channel', task_id='t1', tools=['da-data:ghost']))
        self.assertIn('No registry entry for da-data:ghost', text)
        self.assertEqual(len(steps), 1)
        step = steps[0]
        for fragment in ('tools --project', str(self.project), '--server da-data', '--operation ghost',
                         '--confirm', '--semantics read|write', '--reason'):
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, step)
        self.assert_real_commands(steps)
        # A refused amendment leaves the declared channels alone.
        self.assertEqual(self.state()['tasks']['t1']['tools'], [{'server': 'da-data', 'operation': 'search_content'}])

    def test_confirmation_works_when_the_host_exports_no_catalog(self):
        # This host does not export an MCP catalog, so the core authors the entry.
        # The record must say so: a classification without server evidence is a
        # documented boundary, not an enforced one.
        registry = self.tool.confirm_semantics(ROOT, self.project, 'host-web', 'fetch', 'read',
                                               'Core-authored entry; the host exports no catalog')
        self.assertEqual(registry['operations']['fetch']['classification'], 'read')
        self.assertEqual(registry['provenance'], 'core-authored')
        self.assertIsNone(registry['catalog_sha256'])
        # The entry itself is marked, so the answer stays distinguishable from one
        # confirmed over a catalog entry after the registry is re-read.
        self.assertEqual(registry['operations']['fetch']['provenance'], 'core-authored')
        event = self.state()['history'][-1]
        self.assertEqual(event['action'], 'tool-semantics-confirmed')
        self.assertEqual(event['provenance'], 'core-authored')

    def test_confirmation_cannot_author_an_operation_the_catalog_never_listed(self):
        # The host does export a catalog, so the operations are the ones it listed.
        # Authoring one here would let any task declare a channel the server was
        # never shown to export, and it would carry a `confirmed` basis that reads
        # more trustworthy than an automatic classification.
        self.ingest([{'name': 'search_content', 'description': 'Search indexed documents'}])
        text, steps = self.refusal(lambda: self.tool.confirm_semantics(
            ROOT, self.project, 'da-data', 'ghost_operation', 'read', 'A task declared it'))
        self.assertIn('Unknown operation for server da-data: ghost_operation', text)
        self.assertEqual(len(steps), 1)
        for fragment in ('tools --project', str(self.project), '--server da-data', '--catalog',
                         '--reason'):
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, steps[0])
        self.assert_real_commands(steps)
        on_disk = json.loads((self.project / 'tools' / 'da-data.json').read_text())
        self.assertNotIn('ghost_operation', on_disk['operations'])
        # An operation the catalog did list is still confirmable.
        self.tool.confirm_semantics(ROOT, self.project, 'da-data', 'search_content', 'read',
                                    'Core read the catalog entry')
        event = self.state()['history'][-1]
        self.assertEqual(event['provenance'], 'catalog')


if __name__ == '__main__':
    unittest.main()
