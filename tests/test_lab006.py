from dataclasses import FrozenInstanceError, asdict, replace
import json
import subprocess
import sys
import unittest

from alaetheia import CapabilityRegistry, DomainIssue, DomainRejection, Version, VersionRange
from alaetheia.execution import LocalBinding, LocalExecutor, Outcome
from alaetheia.parcel_example import example, summarize_parcel, validate_parcel
from alaetheia.preflight import WorkflowPreflight, compare_run
from alaetheia.workflow import StepStatus, WorkflowOutcome, WorkflowRunner


class DomainValidationTests(unittest.TestCase):
    def setUp(self):
        self.executor, self.workflow = example()
        self.step = self.workflow.steps[0]
        self.offer = self.executor.inspect_selection(self.step.selected_key, self.step.requirement).offer
        self.values = {'parcel_id': ' P-1 ', 'municipality': ' Example Town ', 'acreage': 12, 'road_access': True}
        self.issue = DomainIssue('nonpositive_acreage', 'Acreage must be positive', 'acreage')

    def executor_with(self, function):
        registry = CapabilityRegistry()
        registry.register(self.offer)
        return LocalExecutor(registry, (LocalBinding(self.offer, function),))

    def invoke(self, function, values=None):
        return self.executor_with(function).invoke(self.step.selected_key, self.step.requirement,
                                                  self.values if values is None else values)

    def test_typed_rejection_validation_and_immutability(self):
        rejection = DomainRejection((self.issue,))
        with self.assertRaises(FrozenInstanceError):
            self.issue.message = 'changed'
        with self.assertRaises(FrozenInstanceError):
            rejection.issues = ()
        for action in (lambda: DomainRejection(()), lambda: DomainRejection([self.issue]),
                       lambda: DomainRejection(('bad',)), lambda: DomainIssue('', 'message'),
                       lambda: DomainIssue('valid', ''), lambda: DomainIssue('valid', 'message', 'Bad field')):
            with self.assertRaises(ValueError):
                action()
        self.assertIsNone(DomainIssue('record_conflict', 'Cross-field problem').field)

    def test_domain_rejection_record(self):
        record = self.invoke(lambda p: DomainRejection((self.issue,)))
        self.assertEqual(record.outcome, Outcome.DOMAIN_REJECTED)
        self.assertTrue(record.invoked)
        self.assertEqual(record.inputs, self.values)
        self.assertEqual(record.domain_issues, (self.issue,))
        self.assertEqual(record.errors, ('Acreage must be positive',))
        self.assertIsNone(record.outputs)
        self.assertIsNone(record.exception_type)
        self.assertEqual(record.missing_output_fields, ())
        self.assertEqual(record.offer, self.offer)

    def test_parcel_reports_all_issues_in_stable_order(self):
        values = {**self.values, 'parcel_id': ' ', 'municipality': '', 'acreage': -1}
        rejection = validate_parcel(values)
        self.assertIsInstance(rejection, DomainRejection)
        self.assertEqual([(i.code, i.field) for i in rejection.issues], [
            ('blank_text', 'parcel_id'), ('blank_text', 'municipality'), ('nonpositive_acreage', 'acreage')])
        self.assertEqual(values['parcel_id'], ' ')
        self.assertEqual(validate_parcel(values), rejection)

    def test_good_payload_still_validated_and_normalized(self):
        record = self.invoke(validate_parcel)
        self.assertEqual(record.outcome, Outcome.SUCCESS)
        self.assertEqual(record.outputs['parcel_id'], 'P-1')
        self.assertEqual(record.outputs['municipality'], 'Example Town')
        self.assertEqual(record.domain_issues, ())
        self.assertEqual(self.values['parcel_id'], ' P-1 ')
        missing = self.invoke(lambda p: {})
        self.assertEqual(missing.outcome, Outcome.INVALID_OUTPUT)
        self.assertIn('acreage', missing.missing_output_fields)

    def test_exceptions_not_reclassified_by_type_or_message(self):
        for exception in (ValueError('Acreage must be positive'), RuntimeError('provider broke')):
            def fail(payload):
                raise exception
            record = self.invoke(fail)
            self.assertEqual(record.outcome, Outcome.PROVIDER_FAILURE)
            self.assertEqual(record.exception_type, type(exception).__name__)
            self.assertEqual(record.domain_issues, ())

    def test_malformed_rejection_is_not_expected_rejection(self):
        record = self.invoke(lambda p: {'issues': [asdict(self.issue)]})
        self.assertEqual(record.outcome, Outcome.INVALID_OUTPUT)
        self.assertEqual(record.domain_issues, ())
        record = self.invoke(lambda p: DomainRejection(()))
        self.assertEqual(record.outcome, Outcome.PROVIDER_FAILURE)
        self.assertEqual(record.exception_type, 'ValueError')
        unknown = self.invoke(lambda p: DomainRejection((DomainIssue('unknown', 'Wrong field', 'not_an_input'),)))
        self.assertEqual(unknown.outcome, Outcome.INVALID_OUTPUT)
        self.assertEqual(unknown.domain_issues, ())
        self.assertEqual(unknown.missing_output_fields, ())
        record_level = self.invoke(lambda p: DomainRejection((DomainIssue('record_conflict', 'Cross-field problem'),)))
        self.assertEqual(record_level.outcome, Outcome.DOMAIN_REJECTED)

    def test_invalid_input_and_selection_precede_domain_validation(self):
        calls = []
        executor = self.executor_with(lambda p: calls.append(p))
        record = executor.invoke(self.step.selected_key, self.step.requirement, {**self.values, 'acreage': '12'})
        self.assertEqual(record.outcome, Outcome.INVALID_INPUT)
        self.assertFalse(record.invoked)
        record = executor.invoke(self.step.selected_key,
                                  replace(self.step.requirement, versions=VersionRange.parse('1.0.0')), self.values)
        self.assertEqual(record.outcome, Outcome.SELECTION_REJECTED)
        self.assertEqual(calls, [])
        self.assertEqual(self.offer.contract.version, Version(2, 0, 0))
        self.assertEqual(self.offer.implementation_version, Version(2, 0, 0))

    def test_rejection_fail_fast_and_comparison_no_output_false_alarm(self):
        calls = []
        registry = CapabilityRegistry()
        bindings = []
        for step in self.workflow.steps:
            offer = self.executor.inspect_selection(step.selected_key, step.requirement).offer
            registry.register(offer)
            def tracked(payload, name=step.step_id):
                calls.append(name)
                return validate_parcel(payload) if name == 'validate' else summarize_parcel(payload)
            bindings.append(LocalBinding(offer, tracked))
        executor = LocalExecutor(registry, tuple(bindings))
        report = WorkflowPreflight(executor).inspect(self.workflow)
        record = WorkflowRunner(executor).run(self.workflow, {**self.values, 'acreage': -1})
        self.assertEqual(report.status, 'no_detected_issues')
        self.assertEqual(record.outcome, WorkflowOutcome.FAILED)
        self.assertEqual(record.failed_step, 'validate')
        self.assertEqual(record.steps[0].status, StepStatus.FAILED)
        self.assertEqual(record.steps[1].status, StepStatus.SKIPPED)
        self.assertEqual(calls, ['validate'])
        comparison = compare_run(report, record)
        self.assertEqual(comparison.failed_execution_outcome, 'domain_rejected')
        self.assertEqual(comparison.domain_issues, (self.issue,))
        self.assertEqual(comparison.missing_outputs, ())
        self.assertEqual(comparison.skipped_steps, ('summarize',))

    def test_comparisons_distinguish_other_failure_kinds(self):
        for function, outcome in ((lambda p: {}, 'invalid_output'), (lambda p: validate_parcel(p), 'success')):
            executor = self.executor_with(function)
            workflow = replace(self.workflow, steps=(self.step,))
            report = WorkflowPreflight(executor).inspect(workflow)
            record = WorkflowRunner(executor).run(workflow, self.values)
            comparison = compare_run(report, record)
            self.assertEqual(comparison.failed_execution_outcome, None if outcome == 'success' else outcome)
            self.assertEqual(comparison.domain_issues, ())
            self.assertEqual(bool(comparison.missing_outputs), outcome == 'invalid_output')

    def test_serializable_structured_issues_in_demo(self):
        result = subprocess.run([sys.executable, '-m', 'alaetheia.parcel_example'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        records = json.loads(result.stdout)
        domain = next(r for r in records if r['case'] == 'invalid-domain')
        self.assertEqual(domain['steps'][0]['execution_outcome'], 'domain_rejected')
        self.assertEqual(domain['steps'][0]['domain_issues'], [asdict(self.issue)])
        self.assertEqual(domain['comparison']['domain_issues'], [asdict(self.issue)])
        self.assertEqual(domain['comparison']['missing_outputs'], [])
