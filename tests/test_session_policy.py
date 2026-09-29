import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest

from test_framework import ROOT, load_tool, register_task


class SessionPolicyTests(unittest.TestCase):
    def setUp(self):
        self.tool = load_tool()
        self.temp = tempfile.TemporaryDirectory(dir=ROOT)
        self.addCleanup(self.temp.cleanup)
        self.project = Path(self.temp.name) / 'project'
        self.tool.initialize(ROOT, self.project, 'Evaluate a bounded research hypothesis')
        register_task(self.tool, self.project)
        register_task(self.tool, self.project, 'review', independent_review=True)

    def packet(self, **changes):
        options = dict(model='current', outputs=['hypotheses/candidates.md'])
        options.update(changes)
        return self.tool.handoff(ROOT, self.project, 't1', 'Develop evidence-backed hypotheses',
                                 ['research-brief.md'], **options)

    def session_options(self, **changes):
        self.assertTrue(callable(getattr(self.tool, 'session_request', None)), 'Session request validation is missing')
        options = dict(mode='fresh', reason=None, resume_session_id=None, independent_review=False)
        options.update(changes)
        return self.tool.session_request(**options)

    def test_core_has_explicit_session_lifecycle(self):
        text = (ROOT / 'SKILL.md').read_text()
        for requirement in ('## Session Lifecycle', 'fresh', 'reuse', 'current', 'independent review',
                            'session overload', 'Do not forward the full conversation', 'No silent fallback',
                            'host-provided session ID'):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, text)

    def test_default_requests_fresh_session_without_claiming_it_exists(self):
        before = {str(p.relative_to(self.project)): p.read_bytes()
                  for p in self.project.rglob('*') if p.is_file()}
        packet = self.packet()
        self.assertIn('session', packet)
        request = packet['session']
        self.assertEqual(request['mode'], 'fresh')
        self.assertTrue(request['reason'])
        self.assertIsNone(request['resume_session_id'])
        self.assertEqual(request['status'], 'requested')
        self.assertNotIn('actual_session_id', request)
        self.assertEqual(packet['dispatch_status'], 'not_dispatched')
        self.assertEqual(before, {str(p.relative_to(self.project)): p.read_bytes()
                                  for p in self.project.rglob('*') if p.is_file()})

    def test_fresh_session_records_core_reason(self):
        session = self.session_options(reason='New specialist role requires separate working history')
        self.assertEqual(session['reason'], 'New specialist role requires separate working history')
        self.assertEqual(session['mode'], 'fresh')

    def test_current_session_requires_explicit_reason(self):
        for reason in (None, '', '   ', False):
            with self.subTest(reason=reason), self.assertRaises(ValueError):
                self.session_options(mode='current', reason=reason)

    def test_small_task_can_explicitly_use_current_session(self):
        packet = self.packet(session_mode='current', session_reason='Small bounded task; no independence needed')
        self.assertEqual(packet['session']['mode'], 'current')
        self.assertIsNone(packet['session']['resume_session_id'])

    def test_reuse_requires_reason_and_real_host_identifier(self):
        for options in ({'reason': 'Continue the same task'}, {'resume_session_id': 'host/session:123'},
                        {'reason': 'Same task', 'resume_session_id': ''},
                        {'reason': 'Same task', 'resume_session_id': False}):
            with self.subTest(options=options), self.assertRaises(ValueError):
                self.session_options(mode='reuse', **options)

    def test_reuse_preserves_opaque_host_identifier(self):
        packet = self.packet(session_mode='reuse', session_reason='Same skill, role and actual model; local revision',
                             resume_session_id='host/session:123.v2')
        self.assertEqual(packet['session']['resume_session_id'], 'host/session:123.v2')
        self.assertEqual(packet['session']['status'], 'requested')
        self.assertEqual(packet['skill']['name'], 'brainstorming-research-ideas')

    def test_resume_identifier_is_for_reuse_only(self):
        for mode in ('fresh', 'current'):
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                self.session_options(mode=mode, reason='Explicit decision', resume_session_id='old-session')

    def test_independent_review_requires_fresh_session(self):
        for mode in ('reuse', 'current'):
            options = dict(mode=mode, reason='Review', independent_review=True)
            if mode == 'reuse':
                options['resume_session_id'] = 'author-session'
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                self.session_options(**options)
        request = self.session_options(independent_review=True, reason='Independent assessment')
        self.assertTrue(request['independent_review'])
        self.assertEqual(request['mode'], 'fresh')

    def test_explicit_blank_fresh_reason_is_rejected(self):
        for reason in ('', '   ', 42):
            with self.subTest(reason=reason), self.assertRaises(ValueError):
                self.session_options(reason=reason)

    def test_invalid_session_mode_is_rejected(self):
        for mode in ('parallel', 'auto', '', None, []):
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                self.session_options(mode=mode)

    def test_independent_flag_requires_boolean(self):
        for value in ('false', 1, None):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.session_options(independent_review=value)

    def test_session_bootstrap_is_bounded(self):
        packet = self.packet()
        self.assertIn('session', packet)
        self.assertEqual(packet['session']['bootstrap_policy'], 'selected-skill-and-task-evidence-only')
        self.assertEqual(packet['session']['unavailable_policy'], 'return-to-core-no-silent-fallback')
        self.assertEqual(len(packet['evidence']), 1)
        self.assertNotIn('conversation', packet)
        self.assertNotIn('skills', packet)

    def test_receipt_distinguishes_requested_and_actual_session(self):
        receipt = json.loads((ROOT / 'templates/handoff-receipt.json').read_text())
        for field in ('actual_session_mode', 'actual_session_id', 'session_isolation_verified'):
            self.assertIn(field, receipt)
        self.assertIsNone(receipt['actual_session_mode'])
        self.assertIsNone(receipt['actual_session_id'])
        self.assertFalse(receipt['session_isolation_verified'])
        self.assertFalse(receipt['accepted'])

    def test_cli_session_options_round_trip(self):
        args = ['handoff', '--project', str(self.project), '--task', 't1',
                '--model', 'current',
                '--summary', 'Revise the candidate explanations', '--evidence', 'research-brief.md',
                '--outputs', 'hypotheses/revised.md',
                '--session', 'reuse', '--session-reason', 'Continue the same local task',
                '--resume-session', 'host:session-17']
        with contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(self.tool.main(args), 0)
        packet = json.loads(output.getvalue())
        self.assertEqual(packet['session']['mode'], 'reuse')
        self.assertEqual(packet['session']['resume_session_id'], 'host:session-17')

    def test_cli_independent_review_cannot_reuse_session(self):
        args = ['handoff', '--project', str(self.project), '--task', 'review', '--model', 'current',
                '--summary', 'Review hypotheses', '--evidence', 'research-brief.md',
                '--outputs', 'reviews/hypotheses.md', '--session', 'current', '--session-reason', 'Already open']
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(self.tool.main(args), 2)


if __name__ == '__main__':
    unittest.main()
