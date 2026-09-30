import contextlib
import io
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from test_framework import ROOT, load_tool, register_task


class ReviewGuardTests(unittest.TestCase):
    def setUp(self):
        self.tool = load_tool()
        self.temp = tempfile.TemporaryDirectory(dir=ROOT)
        self.addCleanup(self.temp.cleanup)
        self.project = Path(self.temp.name) / 'project'
        self.tool.initialize(ROOT, self.project, 'Research question')
        register_task(self.tool, self.project)
        register_task(self.tool, self.project, 'draft', activity='conclusions', skill='ml-paper-writing', role='writer')

    def mutate(self, path, edit):
        data = json.loads(path.read_text())
        edit(data)
        path.write_text(json.dumps(data))

    def artifact(self, name, text='Traceable evidence'):
        path = self.project / name
        path.parent.mkdir(exist_ok=True, parents=True)
        path.write_text(text)
        return {'path': name, 'sha256': self.tool.digest(path)}

    def audited(self):
        protocol = self.artifact('experiments/H1/protocol.md')
        raw = self.artifact('experiments/H1/runs/run-001/results/metrics.json', '{"value": 0.6}')
        findings = self.artifact('findings.md', 'A bounded finding with raw evidence')
        audit = {'schema_version': 1, 'subjects': [protocol, raw, findings], 'summary': 'Independent evidence check'}
        ref = self.artifact('reviews/evidence-audit.json', json.dumps(audit))
        ref['status'] = 'verified'
        self.mutate(self.project / 'research-state.json', lambda x: x.update(
            phase='synthesize', protocol=protocol, evidence_review=ref))
        return ref

    def handoff(self, evidence=None):
        return self.tool.handoff(ROOT, self.project, 'draft', 'Write from verified evidence', evidence or [],
                                 model='current', outputs=['paper/draft-v2.md'])

    def test_valid_audit_allows_writing(self):
        audit = self.audited()
        self.assertEqual(self.handoff(evidence=[audit['path']])['target_role']['id'], 'writer')

    def test_changed_findings_cannot_reuse_old_audit(self):
        audit = self.audited()
        self.artifact('findings.md', 'Unreviewed new finding')
        with self.assertRaises(ValueError):
            self.handoff(evidence=[audit['path']])

    def test_changed_raw_data_cannot_reuse_old_audit(self):
        audit = self.audited()
        self.artifact('experiments/H1/runs/run-001/results/metrics.json', '{"value": 0.99}')
        with self.assertRaises(ValueError):
            self.handoff(evidence=[audit['path']])

    def test_changed_protocol_blocks_write(self):
        audit = self.audited()
        self.artifact('experiments/H1/protocol.md', 'Unreviewed protocol')
        with self.assertRaises(ValueError):
            self.handoff(evidence=[audit['path']])

    def test_empty_audit_subjects_block_write(self):
        audit = self.audited()
        path = self.project / audit['path']
        self.mutate(path, lambda x: x.update(subjects=[]))
        self.mutate(self.project / 'research-state.json', lambda x: x['evidence_review'].update(sha256=self.tool.digest(path)))
        with self.assertRaises(ValueError):
            self.handoff(evidence=[audit['path']])

    def test_protocol_and_findings_alone_are_not_raw_evidence(self):
        audit = self.audited()
        path = self.project / audit['path']
        self.mutate(path, lambda x: x.update(subjects=[s for s in x['subjects']
                                                      if '/results/' not in s['path']]))
        self.mutate(self.project / 'research-state.json',
                    lambda x: x['evidence_review'].update(sha256=self.tool.digest(path)))
        with self.assertRaisesRegex(ValueError, 'primary artifacts'):
            self.handoff(evidence=[audit['path']])

    def test_existing_output_directory_cannot_hide_aliases(self):
        output = self.project / 'reports/task'
        output.mkdir(parents=True)
        protected = self.project / 'research-state.json'
        (output / 'alias.json').symlink_to(protected)
        (output / 'hardlink.json').hardlink_to(protected)
        (output / 'previous.txt').write_text('Existing result')
        with self.assertRaises(ValueError):
            self.tool.handoff(ROOT, self.project, 't1', 'Inspect', ['research-brief.md'],
                              model='current',
                              outputs=['reports/task/'])

    def test_existing_empty_output_directory_is_rejected(self):
        (self.project / 'reports/task').mkdir(parents=True)
        with self.assertRaises(ValueError):
            self.tool.check_outputs(self.project, ['reports/task/'], [])

    def test_dangling_output_symlink_is_rejected(self):
        output = self.project / 'reports/task'
        output.parent.mkdir()
        output.symlink_to(self.project / 'reports/future')
        with self.assertRaises(ValueError):
            self.tool.check_outputs(self.project, ['reports/task'], [])

    def test_changed_paper_invalidates_completion(self):
        self.audited()
        paper = self.artifact('paper/draft.md')
        findings = {'path': 'findings.md', 'sha256': self.tool.digest(self.project / 'findings.md')}
        review = self.artifact('reviews/final.json', json.dumps({'schema_version': 1, 'subjects': [paper, findings]}))
        review['status'] = 'passed'
        self.mutate(self.project / 'research-state.json', lambda x: x.update(phase='review', review=review))
        self.tool.update_task(ROOT, self.project, 't1', 'cancelled', 'Not needed', [])
        self.tool.update_task(ROOT, self.project, 'draft', 'cancelled', 'Not needed', [])
        saved = (self.project / 'research-state.json').read_bytes()
        self.assertEqual(self.tool.transition_phase(ROOT, self.project, 'complete', 'Reviewed', [review['path']])['phase'], 'complete')
        (self.project / 'research-state.json').write_bytes(saved)
        self.artifact('paper/draft.md', 'Changed after acceptance')
        with self.assertRaises(ValueError):
            self.tool.transition_phase(ROOT, self.project, 'complete', 'Reviewed', [review['path']])

    def test_unreviewed_attachments_are_rejected(self):
        audit = self.audited()
        new = self.artifact('data/unreviewed.json')
        with self.assertRaises(ValueError):
            self.handoff(evidence=[audit['path'], new['path']])

    def test_blockers_remain_blocking(self):
        audit = self.audited()
        self.mutate(self.project / 'research-state.json', lambda x: x.update(blockers=['Baseline not reproduced']))
        with self.assertRaises(ValueError):
            self.handoff(evidence=[audit['path']])

    def test_directory_output_cannot_cover_frozen_protocol(self):
        self.audited()
        with self.assertRaises(ValueError):
            self.tool.handoff(ROOT, self.project, 't1', 'Revise design', ['research-brief.md'],
                              model='current',
                              outputs=['experiments/H1/'])

    def test_output_symlink_cannot_escape_project(self):
        (self.project / 'hypotheses').symlink_to(Path(self.temp.name))
        with self.assertRaises(ValueError):
            self.tool.handoff(ROOT, self.project, 't1', 'Propose', ['research-brief.md'],
                              model='current',
                              outputs=['hypotheses/escape.md'])

    def test_skill_discovery_rejects_invalid_frontmatter(self):
        bundle = Path(self.temp.name) / 'bundle'
        path = bundle / 'skills/example/SKILL.md'
        path.parent.mkdir(parents=True)
        for text in ('# No metadata', '---\nname: other\ndescription: A mismatch\n---\n'):
            path.write_text(text)
            with self.assertRaises(ValueError):
                self.tool.discover_skills(bundle)

    def test_specialist_links_stay_local(self):
        package = Path(self.temp.name) / 'package'
        package.mkdir()
        entry = package / 'SKILL.md'
        entry.write_text('[missing](missing.md)')
        with self.assertRaises(ValueError):
            self.tool.check_links(entry, package)
        entry.write_text('[other](../project/research-brief.md)')
        with self.assertRaises(ValueError):
            self.tool.check_links(entry, package)

    def test_phase_rules_are_read_from_core_not_another_config(self):
        bundle = Path(self.temp.name) / 'bundle'
        bundle.mkdir()
        text = (ROOT / 'SKILL.md').read_text().replace('| scope | ideation |', '| scope | design |')
        (bundle / 'SKILL.md').write_text(text)
        self.assertEqual(self.tool.core_phases(bundle)['scope']['next'], ['design'])

    def test_invalid_core_phase_is_rejected(self):
        bundle = Path(self.temp.name) / 'bundle'
        bundle.mkdir()
        text = (ROOT / 'SKILL.md').read_text().replace('| scope | ideation |', '| scope | nowhere |')
        (bundle / 'SKILL.md').write_text(text)
        with self.assertRaises(ValueError):
            self.tool.core_phases(bundle)

    def test_cli_reports_existing_project(self):
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(self.tool.main(['init', '--project', str(self.project), '--question', 'Duplicate']), 2)


if __name__ == '__main__':
    unittest.main()
