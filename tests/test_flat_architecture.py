import contextlib
import importlib.util
import io
import json
from pathlib import Path
import re
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('flat_research', ROOT / 'scripts/research.py')
TOOL = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(TOOL)

# Key sets are asserted exactly, so an added routing or registry field fails loudly
# instead of being invisible to a single "not in" check.
TASK_KEYS = {'task_id', 'created_phase', 'objective', 'activity', 'skill', 'role',
             'acceptance_criteria', 'independent_review', 'status', 'assignments', 'submission'}
PACKET_KEYS = {'schema_version', 'packet_id', 'task_id', 'created_at', 'source_revision',
               'state_sha256', 'core_sha256', 'project_phase', 'objective', 'activity', 'skill',
               'target_role', 'requested_model', 'session', 'summary', 'acceptance_criteria', 'evidence',
               'allowed_outputs', 'dispatch_status', 'receipt_required',
               'framework_root', 'project_root', 'boundary'}
SKILL_KEYS = {'name', 'description', 'path', 'sha256'}
SESSION_KEYS = {'mode', 'reason', 'resume_session_id', 'independent_review', 'status',
                'bootstrap_policy', 'unavailable_policy'}


class FlatArchitectureTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=ROOT)
        self.addCleanup(self.temp.cleanup)
        self.project = Path(self.temp.name) / 'project'

    def initialize(self, role='strategist'):
        TOOL.initialize(ROOT, self.project, 'Study graph classification')
        prompt = None if role in TOOL.ROLE_IDS else 'Judge the material from an explicitly supplied standpoint.'
        TOOL.create_task(ROOT, self.project, 't1', 'Compare explanations', activity='analysis',
                         skill='brainstorming-research-ideas', role=role, acceptance='Every hypothesis has a falsifier',
                         role_prompt_text=prompt)

    def evidence(self, name='literature/evidence.md', text='Sourced evidence'):
        path = self.project / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')
        return {'path': name, 'sha256': TOOL.digest(path)}

    def state(self):
        return json.loads((self.project / 'research-state.json').read_text())

    def save(self, state):
        (self.project / 'research-state.json').write_text(json.dumps(state))

    def packet(self, **changes):
        options = dict(model='current', outputs=['hypotheses/candidates.md'])
        options.update(changes)
        return TOOL.handoff(ROOT, self.project, 't1', 'Compare plausible explanations',
                            ['research-brief.md'], **options)

    def test_intermediate_routing_layers_are_removed(self):
        for name in ('domains', 'core', 'adapters', 'catalog.json', 'library', 'extensions'):
            with self.subTest(name=name):
                self.assertFalse((ROOT / name).exists(), f'Redundant layer remains: {name}')

    def test_core_defines_workspace_and_decision_authority(self):
        text = (ROOT / 'SKILL.md').read_text()
        for fragment in ('## Research Workspace', '## Core Decision Authority',
                         '## Direct Skill Selection', '{hypothesis-id}', 'runs/', '{run-id}',
                         'protocol.md', 'Initialize only the four root documents',
                         'references/workspace.md', 'Only the core'):
            self.assertIn(fragment, text)
        detail = (ROOT / 'references/workspace.md').read_text()
        for fragment in ('runs/{run-id}/', 'code/', 'results/', 'analysis.md',
                         'Freeze `protocol.md`', 'external storage'):
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, detail)

    def test_role_selection_guidance_is_available_without_a_role_registry(self):
        core = (ROOT / 'SKILL.md').read_text()
        self.assertIn('references/role-guidance.md', core)
        self.assertIn('which judgment the task requires', core)
        guidance = (ROOT / 'references/role-guidance.md').read_text()
        for fragment in ('| Role |', 'strategist', 'methodologist', 'analyst', 'critic',
                         'A role carries no skill list', 'does not prove independence',
                         'Role Prompt Templates', 'Red Lines for Role Prompts'):
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, guidance)
        self.initialize()
        task = TOOL.create_task(ROOT, self.project, 't2', 'Explain an unexpected gain', activity='analysis',
                                skill='graph-evaluation', role='critic', acceptance='List rival explanations')
        self.assertEqual(task['role']['id'], 'critic')
        self.assertTrue(task['role']['prompt'])
        self.assertEqual(len(task['role']['sha256']), 64)
        self.assertEqual(set(task), TASK_KEYS)
        # A role id without a canonical template requires an explicit prompt.
        with self.assertRaisesRegex(ValueError, 'prompt'):
            TOOL.create_task(ROOT, self.project, 't3', 'Custom standpoint', activity='analysis',
                             skill='graph-evaluation', role='red-team', acceptance='Probe the claim')
        custom = TOOL.create_task(ROOT, self.project, 't3', 'Custom standpoint', activity='analysis',
                                  skill='graph-evaluation', role='red-team', acceptance='Probe the claim',
                                  role_prompt_text='Actively probe the claim for decisive counterexamples.')
        self.assertEqual(custom['role']['id'], 'red-team')
        self.assertIn('counterexamples', custom['role']['prompt'])

    def test_external_tool_policy_lives_in_the_task_objective(self):
        core = (ROOT / 'SKILL.md').read_text()
        for fragment in ('## External Tools and MCP Servers', 'assigned by the core',
                         'task objective'):
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, core)
        self.assertNotIn('allowed_tools', core, 'The removed allowed_tools field must not be referenced')
        template = json.loads((ROOT / 'templates/research-state.json').read_text())
        self.assertNotIn('allowed_tools', template)
        self.assertNotIn('authorization', template)
        self.assertNotIn('budget', template)
        self.assertNotIn('project_id', template)
        self.assertNotIn('next_action', template)
        self.initialize()
        # Permitted channels are declared in the objective text and reach the executor
        # through the packet summary/objective, not through a state field or tool list.
        packet = TOOL.handoff(ROOT, self.project, 't1',
                              'Work from the brief using the assigned literature-search channel only',
                              ['research-brief.md'],
                              model='current', outputs=['reports/tool-policy.md'])
        self.assertEqual(packet['activity'], 'analysis')
        self.assertNotIn('allowed_tools', packet)
        self.assertNotIn('authorization', packet)
        self.assertNotIn('budget', packet)

    def test_model_selection_guidance_is_available_without_a_model_registry(self):
        core = (ROOT / 'SKILL.md').read_text()
        self.assertIn('references/model-guidance.md', core)
        self.assertIn('judgment density', core)
        guidance = (ROOT / 'references/model-guidance.md').read_text()
        for fragment in ('Match Capability to the Task', 'current', 'No silent substitution',
                         'Independence Is Not Model Switching', 'Record the actual model'):
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, guidance)
        self.initialize()
        with self.assertRaises(ValueError):
            TOOL.handoff(ROOT, self.project, 't1', 'Work from evidence', ['research-brief.md'],
                         model='', outputs=['reports/m1.md'])
        packet = TOOL.handoff(ROOT, self.project, 't1', 'Work from evidence', ['research-brief.md'],
                              model='current', outputs=['reports/m1.md'])
        self.assertEqual(packet['requested_model'], 'current')
        self.assertEqual(set(packet), PACKET_KEYS)

    def test_phase_contract_stays_machine_readable_in_core(self):
        text = (ROOT / 'SKILL.md').read_text()
        for marker in ('<!-- phase-contract:start -->', '<!-- phase-contract:end -->',
                       '| Phase | Next | Goal | Exit criteria |', 'references/phase-guidance.md'):
            with self.subTest(marker=marker):
                self.assertIn(marker, text)
        self.assertEqual(TOOL.core_phases(ROOT)['scope']['next'], ['ideation'])
        guidance = (ROOT / 'references/phase-guidance.md').read_text()
        for fragment in ('## Allowed Transitions', 'Cross-Phase Tasks', 'project status'):
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, guidance)
        for name in TOOL.core_phases(ROOT):
            with self.subTest(phase=name):
                self.assertIn(f'- **{name}:**', guidance,
                              'Phase guidance must describe every authoritative phase')

    def test_entry_point_stays_within_reading_budget(self):
        notes = TOOL.budget_notes(ROOT)
        self.assertEqual(notes, [], 'Entry documents exceeded the progressive-disclosure budget')
        skill = max((p for p in (ROOT / 'skills').glob('*/SKILL.md')), key=lambda p: p.stat().st_size)
        self.assertLessEqual(skill.stat().st_size, TOOL.SKILL_BUDGET,
                             f'Specialist entry too large: {skill.parent.name}')

    def test_reading_budget_is_advisory_not_a_validation_failure(self):
        with tempfile.TemporaryDirectory() as fake:
            root = Path(fake)
            (root / 'SKILL.md').write_text('x' * (25001))
            (root / 'README.md').write_text('y')
            directory = root / 'skills' / 'demo'
            directory.mkdir(parents=True)
            (directory / 'SKILL.md').write_text('z' * (TOOL.SKILL_BUDGET + 1))
            notes = TOOL.budget_notes(root)
        self.assertEqual(len(notes), 2, notes)
        for note in notes:
            self.assertTrue(note.startswith(TOOL.ADVISORY_PREFIX), f'Budget note lacks the advisory prefix: {note}')
        self.assertEqual([x for x in TOOL.validate(ROOT) if not x.startswith(TOOL.ADVISORY_PREFIX)], [])

    def test_every_specialist_boundary_forbids_phase_advancement(self):
        for name, entry in TOOL.discover_skills(ROOT).items():
            text = (ROOT / entry['path']).read_text()
            with self.subTest(skill=name):
                self.assertRegex(text, r'advance (research )?phases',
                                 'Specialist boundaries must name phase advancement as core-only')

    def test_reference_documents_are_reachable_not_orphaned(self):
        documents = [path for path in ROOT.rglob('*.md') if '.git' not in path.parts]
        texts = {path: path.read_text(encoding='utf-8') for path in documents}
        references = sorted(path for path in documents if path.parent.name == 'references')
        self.assertGreaterEqual(len(references), 9)
        for reference in references:
            name = reference.relative_to(ROOT).as_posix()
            sources = [path for path, text in texts.items() if path != reference and reference.name in text]
            with self.subTest(reference=name):
                self.assertTrue(sources, f'Orphan reference document, linked from nowhere: {name}')

    def test_assignment_and_receipt_contract_is_linked_from_core(self):
        core = (ROOT / 'SKILL.md').read_text()
        self.assertIn('references/assignment-contracts.md', core)
        contract = (ROOT / 'references/assignment-contracts.md').read_text()
        for fragment in ('Separate Identities', '`actual_session_id`', 'What a Packet Binds', 'operations.md'):
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, contract)

    def test_research_log_template_defines_single_brief_block(self):
        template = (ROOT / 'templates/research-log.md').read_text(encoding='utf-8')
        self.assertEqual(template.count('<!-- brief:start -->'), 1, 'Brief block must be unique')
        self.assertEqual(template.count('<!-- brief:end -->'), 1, 'Brief block must be unique')
        self.assertLess(template.index('<!-- brief:start -->'), template.index('## Decision Narrative'),
                        'Brief block must precede the append-only narrative')
        for field in ('Updated', 'Status', 'Phase', 'Active task', 'Open blockers', 'Last decision', 'Next'):
            with self.subTest(field=field):
                self.assertIn(field, template)
        errors = TOOL.validate(ROOT)
        self.assertEqual(errors, [note for note in errors if note.startswith(TOOL.ADVISORY_PREFIX)],
                         'Validation must accept the brief markers')

    def test_initialize_carries_brief_block_into_project(self):
        TOOL.initialize(ROOT, self.project, 'Study brief propagation')
        log = (self.project / 'research-log.md').read_text(encoding='utf-8')
        self.assertEqual(log.count('<!-- brief:start -->'), 1)
        self.assertEqual(log.count('<!-- brief:end -->'), 1)

    def test_skills_are_directly_discoverable(self):
        self.assertTrue(callable(getattr(TOOL, 'discover_skills', None)), 'Direct skill discovery is missing')
        skills = TOOL.discover_skills(ROOT)
        self.assertIn('graph-evaluation', skills)
        for name, entry in skills.items():
            self.assertEqual(entry['path'], f'skills/{name}/SKILL.md')
            self.assertEqual(set(entry), SKILL_KEYS)

    def specialist_contract(self, name, fragments):
        path = ROOT / 'skills' / name / 'SKILL.md'
        self.assertTrue(path.is_file(), f'Missing specialist: {name}')
        text = path.read_text(encoding='utf-8')
        for fragment in fragments:
            with self.subTest(skill=name, fragment=fragment):
                self.assertIn(fragment, text)

    def test_literature_review_contract_limits_search_and_coverage_claims(self):
        self.specialist_contract('literature-review', (
            'supplied-corpus', 'eligibility criteria', 'deduplicate', 'PRISMA',
            'core approved', 'source locator', 'risk of bias',
            'Do not invent', 'Return to the core', 'Do not dispatch',
        ))

    def test_literature_review_bundles_local_method_references(self):
        skill = ROOT / 'skills' / 'literature-review'
        entry = (skill / 'SKILL.md').read_text(encoding='utf-8')
        expected = {
            'search-planning.md': ('Boolean', 'query log'),
            'screening-ledger.md': ('deduplicat', 'exclusion reason'),
            'bias-assessment.md': ('risk of bias', 'leakage'),
            'extraction-and-reporting.md': ('locator', 'pool'),
        }
        for name, fragments in expected.items():
            path = skill / 'references' / name
            with self.subTest(reference=name):
                self.assertTrue(path.is_file(), f'Missing reference: {name}')
                self.assertIn(f'references/{name}', entry)
                text = path.read_text(encoding='utf-8')
                self.assertNotRegex(text, r'\]\(\.\./')
                for fragment in fragments:
                    with self.subTest(fragment=fragment):
                        self.assertIn(fragment, text)

    def test_new_specialists_bundle_local_method_references(self):
        expected = {
            'llm-evaluation': {
                'contamination-checks.md': ('overlap', 'canary'),
                'prompt-sensitivity.md': ('template', 'variant'),
                'variance-and-reporting.md': ('interval', 'paired'),
            },
            'code-model-evaluation': {
                'estimators.md': ('unbiased', 'variance'),
                'sandbox-checklist.md': ('timeout', 'isolation'),
                'oracle-and-provenance.md': ('coverage', 'license'),
            },
            'interpretability-validation': {
                'baselines-and-controls.md': ('random', 'shuffl'),
                'causal-claims.md': ('necessity', 'sufficiency'),
                'statistics-and-reporting.md': ('multiplicity', 'agreement'),
            },
            'experimental-design': {
                'design-catalog.md': ('factorial', 'ablation'),
                'units-and-power.md': ('cluster', 'effect size'),
                'evaluation-plan-mapping.md': ('primary_measure', 'validation_plan'),
            },
            'reproducibility-audit': {
                'dependency-manifest.md': ('manifest', 'hash'),
                'audit-report-template.md': ('status', 'blocker'),
                'stale-binding-playbook.md': ('stale', 'rerun'),
            },
            'manuscript-review': {
                'severity-rubric.md': ('blocking', 'minor'),
                'review-report-template.md': ('claim', 'location'),
                'independence-checklist.md': ('isolation', 'fresh'),
            },
        }
        for skill, references in expected.items():
            entry = (ROOT / 'skills' / skill / 'SKILL.md').read_text(encoding='utf-8')
            for name, fragments in references.items():
                path = ROOT / 'skills' / skill / 'references' / name
                with self.subTest(skill=skill, reference=name):
                    self.assertTrue(path.is_file(), f'Missing reference: {skill}/{name}')
                    self.assertIn(f'references/{name}', entry)
                    text = path.read_text(encoding='utf-8')
                    self.assertNotRegex(text, r'\]\(\.\./')
                    for fragment in fragments:
                        with self.subTest(fragment=fragment):
                            self.assertIn(fragment, text)

    def test_experiment_execution_contract_bounds_protocol_runs(self):
        self.specialist_contract('experiment-execution', (
            'frozen protocol', 'sandbox', 'run directory', 'code snapshot',
            'environment', 'results', 'analysis.md', 'blocker',
            'Do not retry', 'Return to the core', 'Do not dispatch',
        ))

    def test_data_processing_contract_manifests_every_transformation(self):
        self.specialist_contract('data-processing', (
            'manifest', 'checksum', 'reason', 'traceable', 'reconcile',
            'Return to the core', 'Do not dispatch',
        ))

    def test_statistical_analysis_contract_preserves_prespecification(self):
        self.specialist_contract('statistical-analysis', (
            'confirmatory', 'exploratory', 'multiplicity', 'unit',
            'primary_measure', 'uncertainty_plan', 'blocker',
            'Return to the core', 'Do not dispatch',
        ))

    def test_execution_and_data_specialists_bundle_local_method_references(self):
        expected = {
            'experiment-execution': {
                'run-management.md': ('run id', 'run-summary'),
                'environment-and-code.md': ('seed', 'checksum'),
                'results-recovery.md': ('timeout', 'partial'),
                'sandbox-assignment.md': ('blocker', 'channel'),
            },
            'data-processing': {
                'manifest-schema.md': ('reason', 'sha256'),
            },
            'statistical-analysis': {
                'test-selection.md': ('estimand', 'unit'),
                'uncertainty-and-reporting.md': ('interval', 'multiplicity'),
            },
        }
        for skill, references in expected.items():
            entry = (ROOT / 'skills' / skill / 'SKILL.md').read_text(encoding='utf-8')
            for name, fragments in references.items():
                path = ROOT / 'skills' / skill / 'references' / name
                with self.subTest(skill=skill, reference=name):
                    self.assertTrue(path.is_file(), f'Missing reference: {skill}/{name}')
                    self.assertIn(f'references/{name}', entry)
                    text = path.read_text(encoding='utf-8')
                    self.assertNotRegex(text, r'\]\(\.\./')
                    for fragment in fragments:
                        with self.subTest(fragment=fragment):
                            self.assertIn(fragment, text)

    def test_host_bridge_and_diagrams_are_linked_from_core(self):
        core = (ROOT / 'SKILL.md').read_text()
        self.assertIn('references/host-bridge.md', core)
        self.assertIn('references/architecture-diagrams.md', core)
        bridge = (ROOT / 'references/host-bridge.md').read_text(encoding='utf-8')
        for fragment in ('Read-only', 'watchdog', 'intervention', 'receipt'):
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, bridge)

    def test_experimental_design_contract_handles_dependence_and_power(self):
        self.specialist_contract('experimental-design', (
            'estimand', 'randomization', 'pseudoreplication', 'power',
            'multiple comparisons', 'primary_measure', 'baseline',
            'validation_plan', 'uncertainty_plan', 'Do not freeze',
            'For proof-only work, skip', 'propose preprocessing and model-selection rules',
            'Never overwrite', 'Return to the core', 'Do not dispatch',
        ))

    def test_reproducibility_audit_contract_separates_inspection_from_approval(self):
        self.specialist_contract('reproducibility-audit', (
            'dependency', 'not checked', 'stale', 'schema_version', 'subjects',
            'sha256', 'findings.md', 'raw evidence', 'inspection',
            'Do not rerun', 'Return to the core', 'Do not dispatch',
        ))

    def test_manuscript_review_contract_preserves_independence_and_evidence_gaps(self):
        self.specialist_contract('manuscript-review', (
            'independent_review', 'fresh', 'drafting history', 'severity',
            'location', 'missing evidence', 'schema_version', 'subjects',
            'findings.md', 'Do not approve', 'Return to the core', 'Do not dispatch',
        ))

    def test_llm_evaluation_contract_covers_contamination_and_prompt_sensitivity(self):
        self.specialist_contract('llm-evaluation', (
            'contamination', 'held-out', 'few-shot', 'prompt', 'seed variance',
            'matched', 'Do not tune', 'Return to the core', 'Do not dispatch',
        ))

    def test_code_model_evaluation_contract_covers_estimators_and_sandbox(self):
        self.specialist_contract('code-model-evaluation', (
            'pass@k', 'unbiased estimator', 'sandbox', 'leakage', 'oracle',
            'Do not execute', 'Return to the core', 'Do not dispatch',
        ))

    def test_interpretability_validation_contract_demands_baselines_and_controls(self):
        self.specialist_contract('interpretability-validation', (
            'baseline', 'control', 'activation patching', 'SAE',
            'multiple comparisons', 'cherry-picked', 'Do not train',
            'Return to the core', 'Do not dispatch',
        ))

    def assert_references(self, skill, references):
        entry = (ROOT / 'skills' / skill / 'SKILL.md').read_text(encoding='utf-8')
        for name, fragments in references.items():
            path = ROOT / 'skills' / skill / 'references' / name
            with self.subTest(skill=skill, reference=name):
                self.assertTrue(path.is_file(), f'Missing reference: {skill}/{name}')
                self.assertIn(f'references/{name}', entry)
                text = path.read_text(encoding='utf-8')
                self.assertNotRegex(text, r'\]\(\.\./')
                for fragment in fragments:
                    with self.subTest(fragment=fragment):
                        self.assertIn(fragment, text)

    def test_evaluation_specialists_bundle_domain_references(self):
        expected = {
            'graph-evaluation': {
                'split-integrity.md': ('transductive', 'inductive'),
                'metric-protocol.md': ('macro', 'micro'),
            },
            'vision-evaluation': {
                'split-integrity.md': ('near-duplicate', 'subject'),
                'metric-protocol.md': ('threshold', 'confidence'),
            },
            'robotics-evaluation': {
                'rollout-protocol.md': ('episode', 'seed'),
                'safety-and-metrics.md': ('violation', 'success rate'),
            },
            'scientific-surrogate-validation': {
                'units-and-consistency.md': ('dimensional', 'extrapolation'),
                'uncertainty-and-baselines.md': ('calibration', 'interval'),
            },
            'symbolic-verification': {
                'certificate-checking.md': ('certificate', 'timeout'),
                'obligation-mapping.md': ('soundness', 'completeness'),
            },
        }
        for skill, references in expected.items():
            with self.subTest(skill=skill):
                self.assert_references(skill, references)

    def test_citation_reference_defers_channel_choice_to_the_core(self):
        text = (ROOT / 'skills/citation-verification/references/citation-workflow.md').read_text(encoding='utf-8')
        entry = (ROOT / 'skills/citation-verification/SKILL.md').read_text(encoding='utf-8')
        for stale in ('always verify programmatically', 'Confirm paper exists in 2+ sources',
                      'Paper found in at least 2 sources'):
            with self.subTest(stale=stale):
                self.assertNotIn(stale, text)
        for fragment in ('assigned channel', 'assigned retrieval channel',
                         'return that gap to the core', 'Channel Selection Belongs to the Core'):
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, text)
        self.assertIn('Use only retrieval explicitly permitted', entry)

    def test_selection_guidance_separates_the_two_ideation_skills(self):
        text = (ROOT / 'references/capability-selection.md').read_text(encoding='utf-8')
        for skill in ('brainstorming-research-ideas', 'creative-thinking-for-research'):
            with self.subTest(skill=skill):
                self.assertIn(skill, text)

    def test_model_guidance_separates_alias_from_session_isolation(self):
        text = (ROOT / 'references/model-guidance.md').read_text(encoding='utf-8')
        self.assertIn('Independence is established by session isolation', text)
        self.assertIn('session isolation', text)

    def test_ideation_specialists_bundle_method_references(self):
        expected = {
            'brainstorming-research-ideas': {
                'ideation-lenses.md': ('tension', 'stakeholder'),
                'candidate-schema.md': ('falsifier', 'ordinal'),
                'ideation-pitfalls.md': ('premature convergence', 'echo chamber'),
            },
            'creative-thinking-for-research': {
                'reformulation-frameworks.md': ('bisociation', 'constraint'),
                'analogy-validation.md': ('structural', 'surface'),
                'creative-blocks.md': ('fixation', 'tunnel vision'),
            },
        }
        for skill, references in expected.items():
            with self.subTest(skill=skill):
                self.assert_references(skill, references)

    def test_new_specialists_support_bounded_analysis_without_advancing_state(self):
        self.initialize()
        cases = (
            ('literature-review', 'analyst', 'literature/review-v1.md', False),
            ('experimental-design', 'methodologist', 'hypotheses/design-v1.md', False),
            ('reproducibility-audit', 'reviewer', 'reviews/reproduction-v1.json', True),
            ('manuscript-review', 'critic', 'reviews/manuscript-v1.json', True),
            ('llm-evaluation', 'analyst', 'reviews/llm-eval-v1.md', False),
            ('code-model-evaluation', 'analyst', 'reviews/code-eval-v1.md', False),
            ('interpretability-validation', 'critic', 'reviews/interpretability-v1.md', False),
        )
        available = TOOL.discover_skills(ROOT)
        for name, role, output, independent in cases:
            with self.subTest(skill=name):
                self.assertIn(name, available)
                task = TOOL.create_task(
                    ROOT, self.project, name, 'Inspect supplied material and report gaps',
                    activity='analysis', skill=name, role=role,
                    acceptance='Return a scoped proposal without approving or executing research',
                    independent_review=independent)
                before = (self.project / 'research-state.json').read_bytes()
                packet = TOOL.handoff(
                    ROOT, self.project, name, 'Bounded offline preparatory assignment',
                    ['research-brief.md'], model='current', outputs=[output])
                self.assertEqual(task['status'], 'planned')
                self.assertEqual(packet['skill']['name'], name)
                self.assertEqual(packet['allowed_outputs'], [output])
                self.assertEqual(packet['activity'], 'analysis')
                self.assertEqual(packet['project_phase'], 'scope')
                self.assertEqual(packet['session']['independent_review'], independent)
                self.assertEqual(packet['session']['mode'], 'fresh')
                self.assertNotIn('authorization', packet)
                self.assertEqual(before, (self.project / 'research-state.json').read_bytes())
                self.assertFalse((self.project / output).exists())
                with self.assertRaisesRegex(ValueError, 'evidence'):
                    TOOL.handoff(ROOT, self.project, name, 'No input supplied', [],
                                 model='current', outputs=[output])
                if independent:
                    for mode in ('current', 'reuse'):
                        options = dict(session_mode=mode, session_reason='Deadline pressure')
                        if mode == 'reuse':
                            options['resume_session_id'] = 'author-session'
                        with self.assertRaisesRegex(ValueError, 'Independent review'):
                            TOOL.handoff(ROOT, self.project, name, 'Reuse author history',
                                         ['research-brief.md'], model='current', outputs=[output],
                                         **options)

    def test_new_specialists_do_not_bypass_experiment_or_conclusions_gates(self):
        self.initialize()
        available = TOOL.discover_skills(ROOT)
        for name in ('literature-review', 'experimental-design', 'reproducibility-audit',
                     'manuscript-review', 'llm-evaluation', 'code-model-evaluation',
                     'interpretability-validation'):
            for activity, error in (('experiment', 'research mode'),
                                    ('conclusions', 'Verified findings required')):
                with self.subTest(skill=name, activity=activity):
                    self.assertIn(name, available)
                    task_id = f'{name}-{activity}'
                    TOOL.create_task(ROOT, self.project, task_id, 'Attempt restricted work',
                                     activity=activity, skill=name, role='analyst',
                                     acceptance='Check activity gates')
                    with self.assertRaisesRegex(ValueError, error):
                        TOOL.handoff(ROOT, self.project, task_id, 'No permission escalation',
                                     ['research-brief.md'], model='current',
                                     outputs=[f'reports/{task_id}.md'])

    def test_readme_describes_current_specialist_count_and_new_scopes(self):
        text = (ROOT / 'README.md').read_text(encoding='utf-8')
        count = re.search(r'The (\d+) direct entries cover:', text)
        self.assertIsNotNone(count)
        self.assertEqual(int(count.group(1)), len(TOOL.discover_skills(ROOT)))
        for name in ('literature-review', 'experimental-design',
                     'reproducibility-audit', 'manuscript-review'):
            with self.subTest(skill=name):
                self.assertIn(f'skills/{name}/SKILL.md', text)

    def test_each_specialist_has_vertical_contract(self):
        entries = list((ROOT / 'skills').glob('*/SKILL.md'))
        self.assertGreaterEqual(len(entries), 12)
        for path in entries:
            text = path.read_text()
            with self.subTest(skill=path.parent.name):
                for section in ('## Inputs', '## Method', '## Outputs', '## Checks', '## Boundary'):
                    self.assertIn(section, text)
                self.assertIn('Return to the core', text)
                self.assertIn('Do not dispatch', text)
                self.assertNotRegex(text, r'\]\(\.\./')

    def test_discovery_requires_no_registration(self):
        self.assertTrue(callable(getattr(TOOL, 'discover_skills', None)))
        bundle = Path(self.temp.name) / 'bundle'
        entry = bundle / 'skills/example/SKILL.md'
        entry.parent.mkdir(parents=True)
        entry.write_text('---\nname: example\ndescription: Use when examining examples.\n---\n# Example\n')
        self.assertIn('example', TOOL.discover_skills(bundle))

    def test_initialize_needs_no_domain_or_model_configuration(self):
        self.initialize()
        self.assertEqual({p.name for p in self.project.iterdir()},
                         {'research-state.json', 'research-brief.md', 'research-log.md', 'findings.md'})
        state = self.state()
        self.assertEqual(state['schema_version'], 4)
        self.assertEqual(state['mode'], 'planning')
        self.assertNotIn('domain', state)
        for removed in ('authorization', 'allowed_tools', 'budget', 'project_id', 'next_action'):
            with self.subTest(removed=removed):
                self.assertNotIn(removed, state, f'Dead field must not be initialized: {removed}')

    def test_explicit_single_skill_role_model_not_inferred(self):
        self.initialize(role='critical-reader')
        before = (self.project / 'research-state.json').read_bytes()
        packet = self.packet(model='provider/selected-model')
        self.assertEqual(packet['skill']['name'], 'brainstorming-research-ideas')
        self.assertEqual(packet['target_role']['id'], 'critical-reader')
        self.assertTrue(packet['target_role']['prompt'])
        self.assertEqual(packet['requested_model'], 'provider/selected-model')
        self.assertEqual(packet['dispatch_status'], 'not_dispatched')
        self.assertEqual(set(packet), PACKET_KEYS)
        self.assertEqual(before, (self.project / 'research-state.json').read_bytes())

    def test_outputs_cannot_touch_global_state(self):
        self.initialize()
        for path in ('research-state.json', 'findings.md', 'research-log.md', 'research-brief.md', '.', 'handoffs/', '../escape'):
            with self.subTest(path=path), self.assertRaises(ValueError):
                self.packet(outputs=[path])

    def test_explicit_task_contract_is_required(self):
        self.initialize()
        for change in ({'model': ''}, {'outputs': []}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.packet(**change)
        for change in ({'role': ''}, {'skill': '../escape'}, {'acceptance': ''}):
            options = dict(activity='analysis', skill='brainstorming-research-ideas', role='strategist', acceptance='Falsifier')
            options.update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                TOOL.create_task(ROOT, self.project, 't2', 'Compare', **options)

    def test_outputs_cannot_overwrite_inputs(self):
        self.initialize()
        with self.assertRaises(ValueError):
            self.packet(outputs=['research-brief.md'])

    def test_skill_selection_cannot_escape_flat_directory(self):
        self.assertTrue(callable(getattr(TOOL, 'discover_skills', None)))
        bundle = Path(self.temp.name) / 'bundle'
        (bundle / 'skills').mkdir(parents=True)
        external = Path(self.temp.name) / 'external'
        external.mkdir()
        (external / 'SKILL.md').write_text('---\nname: linked\ndescription: Use when testing.\n---\n')
        (bundle / 'skills/linked').symlink_to(external)
        with self.assertRaises(ValueError):
            TOOL.discover_skills(bundle)

    def test_frozen_protocol_and_mode_gate_remain(self):
        self.initialize()
        TOOL.create_task(ROOT, self.project, 'run', 'Evaluate frozen outputs', activity='experiment',
                         skill='graph-evaluation', role='experimenter', acceptance='Report per-seed metrics')
        protocol = self.evidence('experiments/H1/protocol.md')
        state = self.state()
        state.update(phase='design', mode='planning', protocol=protocol)
        state['evaluation'] = dict(primary_measure='Macro F1', baseline='Graph kernel',
                                   validation_plan='Grouped graph splits', uncertainty_plan='Five seeds')
        self.save(state)
        args = dict(model='current', outputs=['experiments/H1/runs/run-001/results/'])
        with self.assertRaisesRegex(ValueError, 'research mode'):
            TOOL.handoff(ROOT, self.project, 'run', 'Evaluate frozen outputs', [protocol['path']], **args)
        state['mode'] = 'research'
        self.save(state)
        packet = TOOL.handoff(ROOT, self.project, 'run', 'Evaluate frozen outputs', [protocol['path']], **args)
        self.assertEqual(packet['skill']['name'], 'graph-evaluation')
        self.evidence(protocol['path'], 'Changed protocol')
        with self.assertRaises(ValueError):
            TOOL.handoff(ROOT, self.project, 'run', 'Evaluate frozen outputs', [protocol['path']], **args)

    def test_packet_rejects_legacy_state_explicitly(self):
        self.initialize()
        state = self.state()
        state['schema_version'] = 1
        self.save(state)
        with self.assertRaisesRegex(ValueError, 'schema|version|migration'):
            self.packet()

    def test_primary_docs_do_not_prescribe_old_routing(self):
        for path in [ROOT / 'SKILL.md', ROOT / 'README.md']:
            self.assertNotIn('--domain', path.read_text())
        text = (ROOT / 'scripts/research.py').read_text()
        for name in ('optional_capabilities', 'catalog.json', 'domain-profile.json', 'model-routing.json'):
            self.assertNotIn(name, text)

    def test_cli_requires_explicit_decisions(self):
        self.initialize()
        args = ['handoff', '--project', str(self.project), '--task', 't1', '--summary', 'Explore',
                '--evidence', 'research-brief.md', '--model', 'current', '--outputs', 'hypotheses/ideas.md']
        with contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(TOOL.main(args), 0)
        self.assertEqual(json.loads(output.getvalue())['skill']['name'], 'brainstorming-research-ideas')


if __name__ == '__main__':
    unittest.main()
