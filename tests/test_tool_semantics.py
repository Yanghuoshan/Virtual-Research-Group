"""Tool semantics registry: catalog ingestion, classification, confirmation and gating."""

import hashlib
import json
from pathlib import Path
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

    def test_confirmation_works_when_the_host_exports_no_catalog(self):
        # This host does not export an MCP catalog, so the core authors the entry.
        # The record must say so: a classification without server evidence is a
        # documented boundary, not an enforced one.
        registry = self.tool.confirm_semantics(ROOT, self.project, 'host-web', 'fetch', 'read',
                                               'Core-authored entry; the host exports no catalog')
        self.assertEqual(registry['operations']['fetch']['classification'], 'read')
        self.assertEqual(registry['provenance'], 'core-authored')
        self.assertIsNone(registry['catalog_sha256'])


if __name__ == '__main__':
    unittest.main()
