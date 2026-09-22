from dataclasses import replace
import json
import subprocess
import sys
import unittest
from alaetheia.execution import LocalBinding, LocalExecutor, Outcome, validate_payload
from alaetheia.invocation_example import example
from alaetheia.output_values import snapshot_output
from alaetheia.workflow import InputBinding, Literal, Workflow, WorkflowRunner, WorkflowStep, StepStatus


class ConsolidationTests(unittest.TestCase):
    def setUp(self):
        self.registry, _, self.requirement, self.key = example()
        self.offer = self.registry.get(self.key)

    def executor(self, function):
        return LocalExecutor(self.registry, (LocalBinding(self.offer, function),))

    def test_exception_formatting_preserves_failure_and_skipped_records(self):
        class BrokenDiagnostic(Exception):
            def __str__(self):
                raise RuntimeError('broken formatter')
        calls = []
        def fail(payload):
            calls.append(payload)
            raise BrokenDiagnostic()
        executor = self.executor(fail)
        first = WorkflowStep('first', self.key, self.requirement, (InputBinding('text', Literal('Theia')),))
        record = WorkflowRunner(executor).run(Workflow('failure', (first, replace(first, step_id='second'))))
        execution = record.steps[0].execution
        self.assertEqual(execution.outcome, Outcome.PROVIDER_FAILURE)
        self.assertEqual(execution.exception_type, 'BrokenDiagnostic')
        self.assertEqual(execution.errors, ('BrokenDiagnostic: exception message unavailable',))
        self.assertEqual(record.steps[1].status, StepStatus.SKIPPED)
        self.assertEqual(len(calls), 1)

    def test_copy_hook_cannot_corrupt_success(self):
        output = {'count': 5}
        hooks = []
        class Extra:
            def __deepcopy__(self, memo):
                hooks.append('called')
                memo[id(output)]['count'] = 'invalid'
                return 'copied'
        output['extra'] = Extra()
        record = self.executor(lambda p: output).invoke(self.key, self.requirement, {'text': 'Theia'})
        self.assertEqual(record.outcome, Outcome.INVALID_OUTPUT)
        self.assertIsNone(record.outputs)
        self.assertEqual(hooks, [])
        self.assertEqual(output['count'], 5)

    def test_supported_nested_extras_are_retained_and_detached(self):
        shared = [None, True, 4, 2.5, 'text', {'value': 'nested'}]
        output = {'count': 5, 'first': shared, 'second': shared}
        record = self.executor(lambda p: output).invoke(self.key, self.requirement, {'text': 'Theia'})
        self.assertEqual(record.outcome, Outcome.SUCCESS)
        self.assertEqual(validate_payload(self.offer.contract.outputs, record.outputs, allow_extra=True), ())
        self.assertEqual(record.outputs, output)
        self.assertIsNot(record.outputs['first'], record.outputs['second'])
        shared[-1]['value'] = 'changed'
        self.assertEqual(record.outputs['first'][-1]['value'], 'nested')
        record.outputs['first'].append('local change')
        self.assertNotIn('local change', record.outputs['second'])

    def test_unsupported_values_and_subclasses_rejected(self):
        class DictSubclass(dict):
            def items(self):
                raise AssertionError('must not call hook')
        class IntSubclass(int):
            pass
        class ListSubclass(list):
            pass
        class StringSubclass(str):
            pass
        for value in (object(), (1, 2), {1, 2}, b'bytes', complex(1, 2),
                      float('nan'), float('inf'), -float('inf'),
                      DictSubclass(), IntSubclass(1), ListSubclass(), StringSubclass('s')):
            with self.subTest(type=type(value)), self.assertRaises(ValueError):
                snapshot_output({'extra': value})
        for payload in ([], None, DictSubclass(), {1: 'bad key'}, {'extra': {StringSubclass('key'): 1}}):
            with self.assertRaises(ValueError):
                snapshot_output(payload)

    def test_cycles_rejected_but_shared_acyclic_values_supported(self):
        cycle = []
        cycle.append(cycle)
        with self.assertRaisesRegex(ValueError, 'cycle'):
            snapshot_output({'extra': cycle})
        cycle_dict = {}
        cycle_dict['self'] = cycle_dict
        with self.assertRaisesRegex(ValueError, 'cycle'):
            snapshot_output(cycle_dict)
        self.assertEqual(snapshot_output({'a': [], 'b': []}), {'a': [], 'b': []})

    def test_depth_boundary(self):
        value = None
        for _ in range(63):
            value = [value]
        snapshot_output({'extra': value})  # Root plus 63 nested containers.
        with self.assertRaisesRegex(ValueError, '64 container levels'):
            snapshot_output({'extra': [value]})

    def test_recorded_snapshot_still_checks_both_contracts(self):
        for output in ({'count': 'wrong'}, {'count': None}, {}, {'count': True}):
            record = self.executor(lambda p: output).invoke(self.key, self.requirement, {'text': 'x'})
            self.assertEqual(record.outcome, Outcome.INVALID_OUTPUT)
        record = self.executor(lambda p: {}).invoke(self.key, self.requirement, {'text': 'x'})
        self.assertEqual(record.missing_output_fields, ('count',))

    def test_cli_empty_and_conflicting_filters_rejected(self):
        for args in (('--version', ''), ('--range', ''), ('--range', ' '),
                     ('--version', '', '--range', '>=2.0.0'),
                     ('--version', '2.0.0', '--range', '')):
            result = subprocess.run([sys.executable, '-m', 'alaetheia', 'inspect',
                'terrain.slope.analyze', *args, '--json'], capture_output=True, text=True)
            self.assertEqual(result.returncode, 2, args)
            self.assertEqual(result.stdout, '')
            self.assertIn('error:', result.stderr)
        result = subprocess.run([sys.executable, '-m', 'alaetheia', 'inspect',
            'terrain.slope.analyze', '--json'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(len(json.loads(result.stdout)), 5)
