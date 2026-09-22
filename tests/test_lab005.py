from dataclasses import replace
import json
import subprocess
import sys
import unittest
from alaetheia import CapabilityRegistry, Field, FieldType, Schema
from alaetheia.execution import LocalBinding, LocalExecutor, Outcome
from alaetheia.parcel_example import example, validate_parcel, summarize_parcel
from alaetheia.preflight import WorkflowPreflight, compare_run
from alaetheia.workflow import (InputBinding, Literal, WorkflowInputRef, WorkflowOutcome,
                               WorkflowRunner, StepStatus)


class ReusableWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.original, self.workflow = example()
        self.values = {'parcel_id': ' P-101 ', 'municipality': ' Example Town ', 'acreage': 12.5, 'road_access': True}
        self.calls = []
        self.registry = CapabilityRegistry()
        bindings = []
        for step, function in zip(self.workflow.steps, (validate_parcel, summarize_parcel)):
            offer = self.original.inspect_selection(step.selected_key, step.requirement).offer
            self.registry.register(offer)
            def tracked(payload, name=step.step_id, function=function):
                self.calls.append(name)
                return function(payload)
            bindings.append(LocalBinding(offer, tracked))
        self.executor = LocalExecutor(self.registry, tuple(bindings))
        self.runner = WorkflowRunner(self.executor)

    def test_reuse_multiple_inputs_and_snapshot_isolation(self):
        report = WorkflowPreflight(self.executor).inspect(self.workflow)
        self.assertEqual(report.status, 'no_detected_issues')
        for acreage, access in ((42.5, False), (0.25, True), (12, True)):
            values = {**self.values, 'acreage': acreage, 'road_access': access}
            record = self.runner.run(self.workflow, values)
            self.assertIs(record.workflow, self.workflow)
            self.assertEqual(record.outcome, WorkflowOutcome.SUCCESS)
            summary = record.steps[-1].execution.outputs['summary']
            self.assertIn(f'{acreage} acres', summary)
            self.assertIn('access: yes' if access else 'access: no', summary)
            self.assertEqual(record.inputs['parcel_id'], ' P-101 ')
            self.assertEqual(record.steps[0].execution.outputs['parcel_id'], 'P-101')
            values['parcel_id'] = 'changed'
            self.assertEqual(record.inputs['parcel_id'], ' P-101 ')
            record.inputs['parcel_id'] = 'edited record'
            self.assertEqual(record.steps[0].execution.inputs['parcel_id'], ' P-101 ')
            self.assertEqual(compare_run(report, record).missing_outputs, ())
        self.assertEqual(self.calls, ['validate', 'summarize'] * 3)

    def test_bad_envelopes_rejected_before_any_invocation(self):
        for values in (None, [], {1: 'bad'}, {}, {**self.values, 'acreage': '12'},
                       {**self.values, 'acreage': True}, {**self.values, 'acreage': float('inf')},
                       {**self.values, 'road_access': 1}, {**self.values, 'municipality': None},
                       {**self.values, 'unexpected': 'x'}):
            with self.subTest(values=values):
                record = self.runner.run(self.workflow, values)
                self.assertEqual(record.outcome, WorkflowOutcome.INVALID_INPUT)
                self.assertIsNone(record.failed_step)
                self.assertIsNone(record.inputs)
                self.assertTrue(record.errors)
                self.assertTrue(all(s.status == StepStatus.SKIPPED and s.execution is None for s in record.steps))
        self.assertEqual(self.calls, [])
        self.assertEqual(self.runner.run(self.workflow).outcome, WorkflowOutcome.INVALID_INPUT)

    def test_domain_rules_still_require_execution(self):
        report = WorkflowPreflight(self.executor).inspect(self.workflow)
        for change in ({'acreage': 0}, {'acreage': -2}, {'municipality': '  '}, {'parcel_id': ''}):
            record = self.runner.run(self.workflow, {**self.values, **change})
            self.assertEqual(report.status, 'no_detected_issues')
            self.assertEqual(record.outcome, WorkflowOutcome.FAILED)
            self.assertEqual(record.failed_step, 'validate')
            self.assertEqual(record.steps[0].execution.outcome, Outcome.PROVIDER_FAILURE)
            self.assertEqual(record.steps[1].status, StepStatus.SKIPPED)
            self.assertEqual(compare_run(report, record).missing_outputs, ())

    def test_undeclared_input_reference_and_schema_rejected(self):
        with self.assertRaises(ValueError):
            WorkflowInputRef('Bad name')
        with self.assertRaises(ValueError):
            replace(self.workflow, inputs=None)
        first = self.workflow.steps[0]
        with self.assertRaisesRegex(ValueError, 'undeclared workflow input'):
            replace(self.workflow, steps=(replace(first, inputs=(InputBinding('parcel_id', WorkflowInputRef('unknown')),)),))

    def test_optional_referenced_input_absence_is_not_defaulted(self):
        fields = tuple(replace(f, required=False) if f.name == 'municipality' else f for f in self.workflow.inputs.fields)
        workflow = replace(self.workflow, inputs=Schema(fields))
        report = WorkflowPreflight(self.executor).inspect(workflow)
        self.assertEqual(report.status, 'risks')
        finding = report.findings[0]
        self.assertEqual(finding.code, 'optional_workflow_input_absent')
        self.assertIsNone(finding.source_step)
        self.assertEqual(finding.source_field, 'municipality')
        absent = dict(self.values)
        del absent['municipality']
        record = self.runner.run(workflow, absent)
        self.assertEqual(record.outcome, WorkflowOutcome.FAILED)
        self.assertEqual(record.failed_step, 'validate')
        self.assertIsNone(record.steps[0].execution)
        self.assertIn('is absent', record.steps[0].errors[0])
        self.assertEqual(self.calls, [])
        self.assertEqual(compare_run(report, record).missing_outputs, ())
        self.assertEqual(self.runner.run(workflow, self.values).outcome, WorkflowOutcome.SUCCESS)

    def test_unused_optional_input_can_be_absent(self):
        workflow = replace(self.workflow, inputs=Schema(self.workflow.inputs.fields + (
            Field('note', FieldType.STRING, False, 'Optional caller note; not routed.'),)))
        self.assertEqual(WorkflowPreflight(self.executor).inspect(workflow).status, 'no_detected_issues')
        for values in (self.values, {**self.values, 'note': 'Caller supplied'}):
            self.assertEqual(self.runner.run(workflow, values).outcome, WorkflowOutcome.SUCCESS)
        self.assertEqual(self.runner.run(workflow, {**self.values, 'note': None}).outcome, WorkflowOutcome.INVALID_INPUT)

    def test_all_declared_inputs_validated_even_if_not_routed(self):
        workflow = replace(self.workflow, inputs=Schema(self.workflow.inputs.fields + (
            Field('batch_id', FieldType.STRING, True, 'Required but not passed to provider.'),)))
        self.assertEqual(self.runner.run(workflow, self.values).outcome, WorkflowOutcome.INVALID_INPUT)
        self.assertEqual(self.calls, [])

    def test_mixed_literals_and_workflow_inputs(self):
        first = self.workflow.steps[0]
        bindings = tuple(InputBinding('road_access', Literal(False)) if b.field == 'road_access' else b for b in first.inputs)
        workflow = replace(self.workflow, steps=(replace(first, inputs=bindings), self.workflow.steps[1]))
        record = self.runner.run(workflow, self.values)
        self.assertEqual(record.outcome, WorkflowOutcome.SUCCESS)
        self.assertTrue(record.inputs['road_access'])
        self.assertFalse(record.steps[0].execution.inputs['road_access'])

    def test_workflow_input_type_checks_in_preflight(self):
        for kind, status in ((FieldType.INTEGER, 'no_detected_issues'), (FieldType.NUMBER, 'no_detected_issues'),
                             (FieldType.STRING, 'errors'), (FieldType.BOOLEAN, 'errors')):
            schema = Schema(tuple(replace(f, type=kind) if f.name == 'acreage' else f for f in self.workflow.inputs.fields))
            workflow = replace(self.workflow, inputs=schema)
            report = WorkflowPreflight(self.executor).inspect(workflow)
            self.assertEqual(report.status, status)
        self.assertEqual(self.calls, [])

    def test_missing_output_monitoring_preserved(self):
        bindings = []
        for step in self.workflow.steps:
            offer = self.registry.get(step.selected_key)
            def omit(values):
                result = validate_parcel(values)
                del result['acreage']
                return result
            bindings.append(LocalBinding(offer, omit if step.step_id == 'validate' else summarize_parcel))
        executor = LocalExecutor(self.registry, tuple(bindings))
        report = WorkflowPreflight(executor).inspect(self.workflow)
        record = WorkflowRunner(executor).run(self.workflow, self.values)
        comparison = compare_run(report, record)
        self.assertEqual(report.status, 'no_detected_issues')
        self.assertEqual(record.steps[0].execution.outcome, Outcome.INVALID_OUTPUT)
        self.assertEqual(comparison.skipped_steps, ('summarize',))
        self.assertEqual(len(comparison.missing_outputs), 1)
        self.assertEqual(comparison.missing_outputs[0].field, 'acreage')
        self.assertEqual(comparison.missing_outputs[0].kind, 'required_output_missing')

    def test_invalid_workflow_input_is_not_missing_output(self):
        report = WorkflowPreflight(self.executor).inspect(self.workflow)
        record = self.runner.run(self.workflow, {})
        observation = compare_run(report, record)
        self.assertEqual(observation.runtime_outcome, 'invalid_input')
        self.assertEqual(observation.missing_outputs, ())
        self.assertEqual(observation.skipped_steps, ('validate', 'summarize'))

    def test_no_input_workflows_remain_usable(self):
        from alaetheia.workflow_example import example as old_example
        runner, workflow = old_example()
        self.assertEqual(runner.run(workflow).outcome, WorkflowOutcome.SUCCESS)
        self.assertEqual(runner.run(workflow, {}).outcome, WorkflowOutcome.SUCCESS)
        self.assertEqual(runner.run(workflow, None).outcome, WorkflowOutcome.INVALID_INPUT)
        self.assertEqual(runner.run(workflow, {'extra': 1}).outcome, WorkflowOutcome.INVALID_INPUT)

    def test_parcel_demo(self):
        result = subprocess.run([sys.executable, '-m', 'alaetheia.parcel_example'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        records = json.loads(result.stdout)
        self.assertEqual([r['comparison']['runtime_outcome'] for r in records],
                         ['success', 'success', 'success', 'invalid_input', 'failed'])
        self.assertTrue(all(r['comparison']['missing_outputs'] == [] for r in records))
