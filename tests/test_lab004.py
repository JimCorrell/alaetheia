from dataclasses import replace
import json
import subprocess
import sys
import unittest
from alaetheia import (CapabilityRegistry, FieldType, Requirement, Schema, Version, VersionRange)
from alaetheia.execution import LocalBinding, LocalExecutor, Outcome
from alaetheia.preflight import Severity, WorkflowPreflight, compare_run
from alaetheia.preflight_example import scenario
from alaetheia.workflow import InputBinding, Literal, OutputRef, Workflow, WorkflowRunner
from alaetheia.workflow_example import example


class PreflightTests(unittest.TestCase):
    def setup_case(self, source_type=FieldType.STRING, target_type=FieldType.STRING,
                   optional=False, target_required=True, payload='text'):
        original, workflow = scenario(optional=optional, omit=False)
        registry = CapabilityRegistry()
        bindings = []
        calls = []
        for step in workflow.steps:
            offer = original.inspect_selection(step.selected_key, step.requirement).offer
            if step.step_id == 'produce':
                schema = Schema((replace(offer.contract.outputs.fields[0], type=source_type),))
                offer = replace(offer, contract=replace(offer.contract, outputs=schema))
                def function(p):
                    calls.append('produce')
                    return {'text': payload}
            else:
                schema = Schema((replace(offer.contract.inputs.fields[0], type=target_type, required=target_required),))
                offer = replace(offer, contract=replace(offer.contract, inputs=schema))
                def function(p):
                    calls.append('consume')
                    return {'text': 'done'}
            registry.register(offer)
            bindings.append(LocalBinding(offer, function))
        return registry, LocalExecutor(registry, tuple(bindings)), workflow, calls

    def test_read_only_and_repeatable(self):
        registry, executor, workflow, calls = self.setup_case()
        before = registry.list()
        checker = WorkflowPreflight(executor)
        report = checker.inspect(workflow)
        self.assertEqual(report.status, 'no_detected_issues')
        self.assertEqual(checker.inspect(workflow), report)
        self.assertEqual(calls, [])
        self.assertEqual(registry.list(), before)
        run = WorkflowRunner(executor).run(workflow)
        self.assertEqual(calls, ['produce', 'consume'])
        self.assertEqual(compare_run(report, run).runtime_outcome, 'success')

    def test_all_handoff_type_pairs(self):
        for source in FieldType:
            for target in FieldType:
                with self.subTest(source=source, target=target):
                    _, executor, workflow, _ = self.setup_case(source, target)
                    report = WorkflowPreflight(executor).inspect(workflow)
                    if source == target or (source, target) == (FieldType.INTEGER, FieldType.NUMBER):
                        self.assertEqual(report.status, 'no_detected_issues')
                    elif (source, target) == (FieldType.NUMBER, FieldType.INTEGER):
                        self.assertEqual(report.findings[0].code, 'numeric_narrowing')
                        self.assertEqual(report.status, 'risks')
                    else:
                        self.assertEqual(report.findings[0].code, 'incompatible_type')
                        self.assertEqual(report.status, 'errors')

    def test_numeric_risk_compared_to_values(self):
        for value, expected in ((3, 'success'), (3.0, 'failed'), (3.5, 'failed')):
            _, executor, workflow, _ = self.setup_case(FieldType.NUMBER, FieldType.INTEGER, payload=value)
            report = WorkflowPreflight(executor).inspect(workflow)
            run = WorkflowRunner(executor).run(workflow)
            self.assertEqual(report.status, 'risks')
            self.assertEqual(compare_run(report, run).runtime_outcome, expected)
            self.assertEqual(compare_run(report, run).missing_outputs, ())

    def test_optional_risk_even_for_optional_destination(self):
        for target_required in (True, False):
            _, executor, workflow, _ = self.setup_case(optional=True, target_required=target_required)
            report = WorkflowPreflight(executor).inspect(workflow)
            finding = report.findings[0]
            self.assertEqual(finding.severity, Severity.RISK)
            self.assertEqual(finding.code, 'optional_output_absent')
            self.assertEqual((finding.step_id, finding.source_step, finding.source_field), ('consume', 'produce', 'text'))

    def test_selection_findings_and_no_reservation(self):
        registry, executor, workflow, calls = self.setup_case()
        checker = WorkflowPreflight(executor)
        clean = checker.inspect(workflow)
        selected = registry.get(workflow.steps[0].selected_key)
        registry.unregister(selected.key)
        self.assertEqual(checker.inspect(workflow).status, 'errors')
        # A clear earlier report never suppresses current runtime validation.
        run = WorkflowRunner(executor).run(workflow)
        self.assertEqual(run.steps[0].execution.outcome, Outcome.SELECTION_REJECTED)
        self.assertEqual(compare_run(clean, run).runtime_outcome, 'failed')
        self.assertEqual(calls, [])
        registry.register(replace(selected, implementation_version=Version(9, 0, 0)))
        self.assertTrue(any('stale' in f.message for f in checker.inspect(workflow).findings))
        unbound = WorkflowPreflight(LocalExecutor(registry, ())).inspect(workflow)
        self.assertTrue(any('no local binding' in f.message for f in unbound.findings))
        bad_step = replace(workflow.steps[0], requirement=Requirement('other', VersionRange.parse('1.0.0')))
        bad = checker.inspect(replace(workflow, steps=(bad_step,) + workflow.steps[1:]))
        self.assertTrue(any('capability ID differs' in f.message for f in bad.findings))

    def test_input_wiring_and_literals(self):
        _, executor, workflow, _ = self.setup_case()
        first = workflow.steps[0]
        for inputs, codes in (((), {'missing_input'}),
                              ((InputBinding('other', Literal('x')),), {'missing_input', 'unexpected_input'}),
                              ((InputBinding('text', Literal(7)),), {'invalid_literal'})):
            candidate = replace(workflow, steps=(replace(first, inputs=inputs),) + workflow.steps[1:])
            report = WorkflowPreflight(executor).inspect(candidate)
            self.assertEqual({f.code for f in report.findings}, codes)

    def test_undeclared_output_and_error_priority(self):
        _, executor, workflow, _ = self.setup_case(optional=True)
        second = replace(workflow.steps[1], inputs=(InputBinding('text', OutputRef('produce', 'missing')),))
        report = WorkflowPreflight(executor).inspect(replace(workflow, steps=(workflow.steps[0], second)))
        self.assertEqual(report.findings[0].code, 'undeclared_output')
        first = replace(workflow.steps[0], inputs=(InputBinding('text', Literal(True)),))
        report = WorkflowPreflight(executor).inspect(replace(workflow, steps=(first, workflow.steps[1])))
        self.assertEqual(report.status, 'errors')
        self.assertEqual({f.severity for f in report.findings}, {Severity.ERROR, Severity.RISK})

    def test_optional_absence_and_presence_observed(self):
        for omit in (False, True):
            executor, workflow = scenario(optional=True, omit=omit)
            report = WorkflowPreflight(executor).inspect(workflow)
            run = WorkflowRunner(executor).run(workflow)
            comparison = compare_run(report, run)
            self.assertEqual(comparison.preflight_status, 'risks')
            if omit:
                self.assertEqual(comparison.failed_step, 'consume')
                self.assertEqual(len(comparison.missing_outputs), 1)
                event = comparison.missing_outputs[0]
                self.assertEqual(event.kind, 'referenced_output_absent')
                self.assertTrue(event.predicted_optional_risk)
                self.assertEqual((event.producer_step, event.consumer_step, event.field), ('produce', 'consume', 'text'))
            else:
                self.assertEqual(comparison.runtime_outcome, 'success')
                self.assertEqual(comparison.missing_outputs, ())

    def test_required_omission_unpredictable_and_no_double_count(self):
        executor, workflow = scenario(optional=False, omit=True)
        report = WorkflowPreflight(executor).inspect(workflow)
        self.assertEqual(report.status, 'no_detected_issues')
        run = WorkflowRunner(executor).run(workflow)
        self.assertEqual(run.steps[0].execution.missing_output_fields, ('text',))
        comparison = compare_run(report, run)
        self.assertEqual(comparison.skipped_steps, ('consume',))
        self.assertEqual(len(comparison.missing_outputs), 1)
        event = comparison.missing_outputs[0]
        self.assertEqual(event.kind, 'required_output_missing')
        self.assertIsNone(event.consumer_step)
        self.assertFalse(event.predicted_optional_risk)

    def test_wrong_output_type_not_misreported_as_missing(self):
        _, executor, workflow, _ = self.setup_case(payload=123)
        report = WorkflowPreflight(executor).inspect(workflow)
        run = WorkflowRunner(executor).run(workflow)
        self.assertEqual(run.steps[0].execution.outcome, Outcome.INVALID_OUTPUT)
        self.assertEqual(compare_run(report, run).missing_outputs, ())

    def test_optional_destination_still_fails_when_reference_absent(self):
        registry, original, workflow, _ = self.setup_case(optional=True, target_required=False)
        def omit(payload):
            return {}
        executor = LocalExecutor(registry, tuple(LocalBinding(o, omit) for o in registry.list()))
        report = WorkflowPreflight(executor).inspect(workflow)
        run = WorkflowRunner(executor).run(workflow)
        comparison = compare_run(report, run)
        self.assertEqual(run.failed_step, 'consume')
        self.assertIsNone(run.steps[1].execution)
        self.assertTrue(comparison.missing_outputs[0].predicted_optional_risk)

    def test_malformed_output_not_misclassified_as_omission(self):
        registry, original, workflow, _ = self.setup_case()
        for bad_output in (None, [], {'text': None}):
            executor = LocalExecutor(registry, tuple(LocalBinding(o, lambda p: bad_output) for o in registry.list()))
            report = WorkflowPreflight(executor).inspect(workflow)
            run = WorkflowRunner(executor).run(workflow)
            self.assertEqual(run.steps[0].execution.outcome, Outcome.INVALID_OUTPUT)
            self.assertEqual(compare_run(report, run).missing_outputs, ())

    def test_report_run_mismatch_rejected(self):
        executor, workflow = scenario(optional=True, omit=True)
        report = WorkflowPreflight(executor).inspect(workflow)
        run = WorkflowRunner(executor).run(replace(workflow, workflow_id='other'))
        with self.assertRaises(ValueError):
            compare_run(report, run)

    def test_clear_report_and_provider_exception(self):
        registry, executor, workflow, _ = self.setup_case()
        def fail(payload):
            raise RuntimeError('failure not predictable from schema')
        executor = LocalExecutor(registry, tuple(LocalBinding(o, fail) for o in registry.list()))
        report = WorkflowPreflight(executor).inspect(workflow)
        run = WorkflowRunner(executor).run(workflow)
        self.assertEqual(report.status, 'no_detected_issues')
        self.assertEqual(run.steps[0].execution.outcome, Outcome.PROVIDER_FAILURE)
        self.assertEqual(compare_run(report, run).missing_outputs, ())

    def test_example_output(self):
        result = subprocess.run([sys.executable, '-m', 'alaetheia.preflight_example'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        records = json.loads(result.stdout)
        self.assertEqual(len(records), 3)
        self.assertEqual([r['comparison']['runtime_outcome'] for r in records], ['success', 'failed', 'failed'])
