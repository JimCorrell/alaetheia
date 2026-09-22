from dataclasses import replace
import json
import subprocess
import sys
import unittest
from alaetheia import (CapabilityRegistry, Field, FieldType, Requirement, Schema,
                       Version, VersionRange)
from alaetheia.execution import (LocalBinding, LocalExecutor, Outcome, validate_payload)
from alaetheia.invocation_example import example


class PayloadValidation(unittest.TestCase):
    def test_scalar_matrix(self):
        for kind, accepted, rejected in (
            (FieldType.STRING, ('', 'hello'), (1, None, [], True)),
            (FieldType.BOOLEAN, (True, False), (0, 1, 'true', None)),
            (FieldType.INTEGER, (0, -1, 10**400), (True, 1.0, '1', None)),
            (FieldType.NUMBER, (0, -1, 1.5, 10**400), (True, '1', None, float('nan'), float('inf'), -float('inf'))),
        ):
            schema = Schema((Field('value', kind, True, 'Test value.'),))
            for value in accepted:
                with self.subTest(kind=kind, accepted=value):
                    self.assertEqual(validate_payload(schema, {'value': value}, allow_extra=False), ())
            for value in rejected:
                with self.subTest(kind=kind, rejected=value):
                    self.assertTrue(validate_payload(schema, {'value': value}, allow_extra=False))

    def test_optional_and_extra(self):
        schema = Schema((Field('flag', FieldType.BOOLEAN, False, 'Optional flag.'),))
        self.assertEqual(validate_payload(schema, {}, allow_extra=False), ())
        self.assertTrue(validate_payload(schema, {'flag': None}, allow_extra=False))
        self.assertTrue(validate_payload(schema, {'extra': 1}, allow_extra=False))
        self.assertEqual(validate_payload(schema, {'extra': ['anything']}, allow_extra=True), ())
        for payload in (None, [], {1: 'bad'}):
            self.assertTrue(validate_payload(schema, payload, allow_extra=True))


class Invocation(unittest.TestCase):
    def setUp(self):
        self.registry, self.executor, self.requirement, self.key = example()
        self.offer = self.registry.get(self.key)

    def executor_with(self, function, offer=None):
        offer = offer or self.offer
        registry = CapabilityRegistry()
        registry.register(offer)
        return LocalExecutor(registry, (LocalBinding(offer, function),))

    def test_explicit_overlap_and_record(self):
        self.assertEqual(len(self.registry.find(self.requirement)), 2)
        for implementation, method in (('direct', 'len'), ('iterated', 'iteration')):
            key = replace(self.key, implementation_id=implementation)
            record = self.executor.invoke(key, self.requirement, {'text': 'Theia'})
            self.assertEqual(record.outcome, Outcome.SUCCESS)
            self.assertTrue(record.invoked)
            self.assertEqual(record.selected_key, key)
            self.assertEqual(record.offer.implementation_version, Version(1, 0, 0))
            self.assertEqual(record.offer.contract.version, Version(1, 0, 0))
            self.assertEqual(record.outputs, {'count': 5, 'method': method})
            self.assertEqual(record.inputs, {'text': 'Theia'})
            self.assertEqual(record.errors, ())

    def test_invalid_input_never_invokes(self):
        calls = []
        executor = self.executor_with(lambda p: calls.append(p))
        for payload in ({}, {'text': None}, {'text': 5}, {'text': 'ok', 'extra': 1}, [], None):
            record = executor.invoke(self.key, self.requirement, payload)
            self.assertEqual(record.outcome, Outcome.INVALID_INPUT)
            self.assertFalse(record.invoked)
            self.assertTrue(record.errors)
        self.assertEqual(calls, [])

    def test_selection_failures_never_invoke(self):
        calls = []
        executor = self.executor_with(lambda p: calls.append(p))
        for change in ({'capability_id': 'other'}, {'versions': VersionRange.parse('2.0.0')},
                       {'inputs': Schema(())}, {'provider_id': 'other'}, {'tags': frozenset({'missing'})}):
            record = executor.invoke(self.key, replace(self.requirement, **change), {'text': 'x'})
            self.assertEqual(record.outcome, Outcome.SELECTION_REJECTED)
            self.assertFalse(record.invoked)
        self.assertEqual(calls, [])
        missing = executor.invoke(replace(self.key, implementation_id='missing'), self.requirement, {})
        self.assertIsNone(missing.offer)
        self.assertEqual(missing.outcome, Outcome.SELECTION_REJECTED)
        unbound = LocalExecutor(self.registry, ()).invoke(self.key, self.requirement, {'text': 'x'})
        self.assertIn('selected offer has no local binding', unbound.errors)

    def test_removed_or_replaced_offer_rejects_stale_binding(self):
        self.registry.unregister(self.key)
        self.assertFalse(self.executor.invoke(self.key, self.requirement, {}).invoked)
        changed = replace(self.offer, implementation_version=Version(1, 0, 1))
        self.registry.register(changed)
        record = self.executor.invoke(self.key, self.requirement, {'text': 'x'})
        self.assertFalse(record.invoked)
        self.assertEqual(record.offer, changed)
        self.assertIn('stale', record.errors[0])

    def test_failure_once_without_fallback(self):
        calls = []
        def fail(payload):
            calls.append(payload)
            raise RuntimeError('example failure')
        record = self.executor_with(fail).invoke(self.key, self.requirement, {'text': 'x'})
        self.assertEqual(record.outcome, Outcome.PROVIDER_FAILURE)
        self.assertTrue(record.invoked)
        self.assertEqual(record.exception_type, 'RuntimeError')
        self.assertEqual(record.errors, ('example failure',))
        self.assertEqual(len(calls), 1)
        self.assertIsNone(record.outputs)

    def test_process_control_propagates(self):
        def stop(payload):
            raise KeyboardInterrupt()
        with self.assertRaises(KeyboardInterrupt):
            self.executor_with(stop).invoke(self.key, self.requirement, {'text': 'x'})

    def test_invalid_outputs(self):
        for output in ({}, {'count': '1'}, {'count': True}, None, [], {1: 1}):
            with self.subTest(output=output):
                record = self.executor_with(lambda p: output).invoke(self.key, self.requirement, {'text': 'x'})
                self.assertEqual(record.outcome, Outcome.INVALID_OUTPUT)
                self.assertTrue(record.invoked)
                self.assertTrue(record.errors)
                self.assertIsNone(record.outputs)

    def test_full_provider_contract_checked_despite_subset_request(self):
        record = self.executor_with(lambda p: {}).invoke(
            self.key, replace(self.requirement, outputs=Schema(())), {'text': 'x'})
        self.assertEqual(record.outcome, Outcome.INVALID_OUTPUT)
        self.assertIn("provider output: 'count': required field is missing", record.errors)

    def test_optional_outputs_and_consumer_check(self):
        optional = Field('note', FieldType.STRING, False, 'Optional note.')
        contract = replace(self.offer.contract, outputs=Schema(self.offer.contract.outputs.fields + (optional,)))
        offer = replace(self.offer, contract=contract)
        for output, expected in (({'count': 1}, Outcome.SUCCESS), ({'count': 1, 'note': 'ok'}, Outcome.SUCCESS),
                                 ({'count': 1, 'note': None}, Outcome.INVALID_OUTPUT)):
            record = self.executor_with(lambda p: output, offer).invoke(self.key, self.requirement, {'text': 'x'})
            self.assertEqual(record.outcome, expected)
        required_note = replace(self.requirement, outputs=Schema((replace(optional, required=True),)))
        rejected = self.executor_with(lambda p: {'count': 1}, offer).invoke(self.key, required_note, {'text': 'x'})
        self.assertEqual(rejected.outcome, Outcome.SELECTION_REJECTED)
        # The consumer constrains even an optional field omitted from the manifest
        # when the provider actually returns that field as an extra.
        optional_need = replace(self.requirement, outputs=Schema((optional,)))
        record = self.executor_with(lambda p: {'count': 1, 'note': 4}).invoke(self.key, optional_need, {'text': 'x'})
        self.assertEqual(record.outcome, Outcome.INVALID_OUTPUT)
        self.assertIn("consumer output: 'note': expected string", record.errors)

    def test_snapshot_isolation_and_extra_outputs(self):
        output = {'count': 1, 'extra': {'items': [1]}}
        def provider(payload):
            payload['text'] = 'edited'
            return output
        payload = {'text': 'x'}
        record = self.executor_with(provider).invoke(self.key, self.requirement, payload)
        self.assertEqual(record.outcome, Outcome.SUCCESS)
        output['extra']['items'].append(2)
        payload['text'] = 'caller edit'
        self.assertEqual(record.inputs, {'text': 'x'})
        self.assertEqual(record.outputs, {'count': 1, 'extra': {'items': [1]}})

    def test_uncopyable_extra_is_inspectable_failure(self):
        class Uncopyable:
            def __deepcopy__(self, memo):
                raise ValueError('cannot copy')
        record = self.executor_with(lambda p: {'count': 1, 'extra': Uncopyable()}).invoke(
            self.key, self.requirement, {'text': 'x'})
        self.assertEqual(record.outcome, Outcome.INVALID_OUTPUT)
        self.assertEqual(record.errors, ('output contains an unsupported value; only builtin data values are allowed',))

    def test_binding_guards(self):
        binding = LocalBinding(self.offer, lambda p: {'count': 0})
        with self.assertRaises(ValueError):
            LocalExecutor(self.registry, (binding, binding))
        with self.assertRaises(ValueError):
            LocalBinding(self.offer, None)
        for metadata in (replace(self.offer.metadata, permissions=frozenset({'read'})),
                         replace(self.offer.metadata, side_effects=frozenset({'write'}))):
            with self.assertRaises(ValueError):
                LocalBinding(replace(self.offer, metadata=metadata), lambda p: {})
        with self.assertRaises(ValueError):
            LocalExecutor(self.registry, (LocalBinding(replace(self.offer, implementation_version=Version(9, 0, 0)), lambda p: {}),))

    def test_example_module(self):
        result = subprocess.run([sys.executable, '-m', 'alaetheia.invocation_example'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        record = json.loads(result.stdout)
        self.assertEqual(record['outcome'], 'success')
        self.assertEqual(record['implementation'], 'iterated')
        self.assertEqual(record['outputs'], {'count': 5, 'method': 'iteration'})
