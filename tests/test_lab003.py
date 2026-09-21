from dataclasses import replace
import json
import subprocess
import sys
import unittest

from alaetheia import (CapabilityContract, CapabilityManifest, CapabilityRegistry, Field,
    FieldType, Metadata, Requirement, Schema, Version, VersionRange)
from alaetheia.execution import LocalBinding, LocalExecutor, Outcome
from alaetheia.workflow import (InputBinding, Literal, OutputRef, StepStatus, Workflow,
    WorkflowOutcome, WorkflowRunner, WorkflowStep)
from alaetheia.workflow_example import example


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.calls = []
        self.registry = CapabilityRegistry()
        schema = Schema((Field('value', FieldType.STRING, True, 'Example text.'),))
        self.offer = CapabilityManifest(CapabilityContract('text.echo', Version(1, 0, 0), schema, schema),
            'local', 'echo', Version(1, 0, 0),
            Metadata('Local test function.', frozenset(), frozenset(), frozenset(), 'test_lab003'))
        self.registry.register(self.offer)
        self.requirement = Requirement('text.echo', VersionRange.parse('1.0.0'), inputs=schema, outputs=schema)

    def step(self, name, source):
        return WorkflowStep(name, self.offer.key, self.requirement, (InputBinding('value', source),))

    def chain(self):
        return Workflow('test', (self.step('a', Literal('start')),
            self.step('b', OutputRef('a', 'value')), self.step('c', OutputRef('b', 'value'))))

    def runner(self, function=None, offer=None):
        offer = offer or self.offer
        def echo(payload):
            self.calls.append(dict(payload))
            return {'value': payload['value'] + '!'}
        return WorkflowRunner(LocalExecutor(self.registry, (LocalBinding(offer, function or echo),)))

    def test_order_records_and_repeated_run_isolation(self):
        runner, workflow = self.runner(), self.chain()
        first = runner.run(workflow)
        self.assertEqual(first.outcome, WorkflowOutcome.SUCCESS)
        self.assertIsNone(first.failed_step)
        self.assertEqual(self.calls, [{'value': 'start'}, {'value': 'start!'}, {'value': 'start!!'}])
        self.assertEqual([r.step_id for r in first.steps], ['a', 'b', 'c'])
        for record in first.steps:
            self.assertEqual(record.execution.offer, self.offer)
            self.assertEqual(record.status, StepStatus.SUCCESS)
        self.assertEqual(first.workflow, workflow)
        first.steps[0].execution.outputs['value'] = 'edited by caller'
        second = runner.run(workflow)
        self.assertEqual(second.steps[0].execution.outputs, {'value': 'start!'})
        self.assertEqual(first.steps[1].execution.inputs, {'value': 'start!'})

    def test_prior_nonadjacent_reference_and_field_mapping(self):
        workflow = self.chain()
        workflow = replace(workflow, steps=workflow.steps[:2] + (self.step('c', OutputRef('a', 'value')),))
        record = self.runner().run(workflow)
        self.assertEqual(record.steps[2].execution.inputs, {'value': 'start!'})
        demo_runner, demo = example()
        result = demo_runner.run(demo)
        self.assertEqual(result.steps[1].execution.inputs, {'text': 'Theia'})
        self.assertEqual(result.steps[2].execution.inputs, {'count': 5})
        self.assertEqual(result.steps[2].execution.outputs, {'message': 'Characters: 5'})

    def test_invalid_definitions(self):
        step = self.step('a', Literal('x'))
        actions = (
            lambda: Workflow('empty', ()), lambda: Workflow('list', [step]),
            lambda: Workflow('duplicate', (step, step)),
            lambda: Workflow('self', (self.step('a', OutputRef('a', 'value')),)),
            lambda: Workflow('missing', (self.step('a', OutputRef('missing', 'value')),)),
            lambda: Workflow('forward', (self.step('a', OutputRef('b', 'value')), self.step('b', Literal('x')))),
            lambda: replace(step, inputs=step.inputs * 2),
            lambda: replace(step, inputs=['bad']), lambda: replace(step, selected_key=None),
            lambda: replace(step, requirement=None), lambda: InputBinding('value', 'implicit literal'),
            lambda: OutputRef('Bad ID', 'value'), lambda: Literal(None), lambda: Literal([]),
            lambda: Literal(float('inf')), lambda: Literal(float('nan')),
        )
        for action in actions:
            with self.subTest(action=action), self.assertRaises(ValueError):
                action()
        self.assertEqual(self.calls, [])

    def test_incompatible_handoff(self):
        runner, workflow = example(incompatible=True)
        result = runner.run(workflow)
        self.assertEqual(result.outcome, WorkflowOutcome.FAILED)
        self.assertEqual(result.failed_step, 'middle')
        self.assertEqual([s.status for s in result.steps], [StepStatus.SUCCESS, StepStatus.FAILED, StepStatus.SKIPPED])
        self.assertEqual(result.steps[1].execution.outcome, Outcome.INVALID_INPUT)
        self.assertFalse(result.steps[1].execution.invoked)
        self.assertIsNone(result.steps[2].execution)

    def test_provider_failure_stops_even_independent_steps(self):
        def fail_second(payload):
            self.calls.append(payload)
            if len(self.calls) == 2:
                raise RuntimeError('stop here')
            return {'value': 'first success'}
        workflow = self.chain()
        workflow = replace(workflow, steps=workflow.steps[:2] + (self.step('c', Literal('independent')),))
        result = self.runner(fail_second).run(workflow)
        self.assertEqual(len(self.calls), 2)
        self.assertEqual(result.failed_step, 'b')
        self.assertEqual(result.steps[1].execution.outcome, Outcome.PROVIDER_FAILURE)
        self.assertEqual(result.steps[1].errors, ('stop here',))
        self.assertEqual(result.steps[2].status, StepStatus.SKIPPED)
        self.assertEqual(result.steps[2].errors, ("stopped after failed step 'b'",))

    def test_executor_failure_categories_retained(self):
        for category in ('selection', 'input', 'output'):
            with self.subTest(category=category):
                workflow = self.chain()
                if category == 'selection':
                    first = replace(workflow.steps[0], selected_key=replace(self.offer.key, implementation_id='missing'))
                elif category == 'input':
                    first = self.step('a', Literal(42))
                else:
                    first = workflow.steps[0]
                workflow = replace(workflow, steps=(first,) + workflow.steps[1:])
                result = self.runner(lambda p: {}).run(workflow)
                expected = {'selection': Outcome.SELECTION_REJECTED, 'input': Outcome.INVALID_INPUT,
                            'output': Outcome.INVALID_OUTPUT}[category]
                self.assertEqual(result.steps[0].execution.outcome, expected)
                self.assertEqual(result.steps[0].execution.invoked, category == 'output')
                self.assertEqual([s.status for s in result.steps[1:]], [StepStatus.SKIPPED] * 2)

    def test_missing_optional_output_fails_resolution(self):
        optional = replace(self.offer.contract.outputs.fields[0], required=False)
        offer = replace(self.offer, contract=replace(self.offer.contract, outputs=Schema((optional,))))
        self.registry.unregister(self.offer.key)
        self.registry.register(offer)
        requirement = replace(self.requirement, outputs=Schema(()))
        workflow = self.chain()
        workflow = replace(workflow, steps=tuple(replace(s, requirement=requirement) for s in workflow.steps))
        def omit(payload):
            self.calls.append(payload)
            return {}
        result = self.runner(omit, offer).run(workflow)
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(result.failed_step, 'b')
        self.assertIsNone(result.steps[1].execution)
        self.assertEqual(result.steps[1].errors, ("'value': a.value is absent",))
        self.assertEqual(result.steps[2].status, StepStatus.SKIPPED)

    def test_extra_output_is_preserved_but_not_wireable(self):
        workflow = self.chain()
        workflow = replace(workflow, steps=(workflow.steps[0], self.step('b', OutputRef('a', 'extra')), workflow.steps[2]))
        result = self.runner(lambda p: {'value': 'valid', 'extra': 'unvalidated'}).run(workflow)
        self.assertEqual(result.steps[0].execution.outputs['extra'], 'unvalidated')
        self.assertEqual(result.steps[1].errors, ("'value': a.extra is not a declared output",))
        self.assertIsNone(result.steps[1].execution)
        self.assertEqual(result.failed_step, 'b')

    def test_stale_binding_still_rejected(self):
        runner = self.runner()
        self.registry.unregister(self.offer.key)
        self.registry.register(replace(self.offer, implementation_version=Version(2, 0, 0)))
        result = runner.run(self.chain())
        self.assertEqual(self.calls, [])
        self.assertEqual(result.steps[0].execution.outcome, Outcome.SELECTION_REJECTED)
        self.assertIn('stale', result.steps[0].errors[0])

    def test_empty_inputs_and_multiple_sources(self):
        schema = Schema((Field('left', FieldType.STRING, True, 'Left text.'),
                         Field('right', FieldType.STRING, True, 'Right text.')))
        offer = replace(self.offer, implementation_id='join',
                        contract=replace(self.offer.contract, capability_id='text.join', inputs=schema))
        self.registry.register(offer)
        executor = LocalExecutor(self.registry, (
            LocalBinding(self.offer, lambda p: {'value': p['value']}),
            LocalBinding(offer, lambda p: {'value': p['left'] + p['right']}),
        ))
        join = WorkflowStep('join', offer.key, Requirement('text.join', VersionRange.parse('1.0.0')),
            (InputBinding('left', OutputRef('a', 'value')), InputBinding('right', Literal('!'))))
        result = WorkflowRunner(executor).run(Workflow('join-example', (self.step('a', Literal('hello')), join)))
        self.assertEqual(result.steps[-1].execution.outputs, {'value': 'hello!'})
        empty = replace(self.step('empty', Literal('unused')), inputs=())
        result = WorkflowRunner(executor).run(Workflow('empty-input', (empty,)))
        self.assertEqual(result.steps[0].execution.outcome, Outcome.INVALID_INPUT)

    def test_process_control_propagates(self):
        def interrupt(payload):
            raise KeyboardInterrupt()
        with self.assertRaises(KeyboardInterrupt):
            self.runner(interrupt).run(self.chain())

    def test_demo_exit_codes_and_records(self):
        for args, expected in (([], 0), (['--incompatible'], 1)):
            result = subprocess.run([sys.executable, '-m', 'alaetheia.workflow_example', *args],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, expected, result.stderr)
            record = json.loads(result.stdout)
            self.assertEqual(record['outcome'], 'failed' if args else 'success')
            self.assertEqual(len(record['steps']), 3)
            self.assertIn('selected_key', record['workflow']['steps'][0])
