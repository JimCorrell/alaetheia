import json
import os
import subprocess
import sys
import unittest
from dataclasses import FrozenInstanceError, replace
from alaetheia import *
from alaetheia.examples import sample_registry, INPUT, OUTPUT, EXTENDED_OUTPUT


class Versions(unittest.TestCase):
    def test_numeric_order_and_round_trip(self):
        self.assertGreater(Version.parse('2.10.0'), Version.parse('2.9.0'))
        self.assertEqual(str(Version.parse('10.20.30')), '10.20.30')

    def test_invalid_versions(self):
        for raw in ('1', '1.0', '01.0.0', '-1.0.0', '1.0.0-alpha', '1.0.0+build', ' 1.0.0', '١.0.0', None):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                Version.parse(raw)
        for args in ((True, 0, 0), (-1, 0, 0), (1.0, 0, 0)):
            with self.assertRaises(ValueError):
                Version(*args)

    def test_range_boundaries(self):
        for expression, included, excluded in (
            ('>=2.0.0 <3.0.0', ('2.0.0', '2.10.0'), ('1.9.9', '3.0.0')),
            ('>2.0.0 <=3.0.0', ('2.0.1', '3.0.0'), ('2.0.0', '3.0.1')),
            ('==2.0.0', ('2.0.0',), ('2.0.1', '1.9.9')),
            ('2.0.0', ('2.0.0',), ('2.1.0',)),
            ('<1.0.0', ('0.0.0',), ('1.0.0',)),
            ('>=0.2.0', ('0.2.0', '9.0.0'), ('0.1.9',)),
        ):
            selected = VersionRange.parse(expression)
            for value in included:
                self.assertTrue(selected.contains(Version.parse(value)), (expression, value))
            for value in excluded:
                self.assertFalse(selected.contains(Version.parse(value)), (expression, value))

    def test_invalid_ranges(self):
        for raw in ('', '*', '^2.0.0', '~2.0.0', '>=2 <3', '>=3.0.0 <2.0.0', '>2.0.0 <2.0.1', '<0.0.0', '>=2.0.0 >=3.0.0', '2.0.0 <3.0.0', '>=2.0.0 || <1.0.0'):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                VersionRange.parse(raw)


class Declarations(unittest.TestCase):
    def setUp(self):
        self.offer = sample_registry().list()[0]

    def test_invalid_ids(self):
        for raw in ('', 'Upper.case', 'bad..id', '.id', 'id ', 'id/name', None):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                replace(self.offer.contract, capability_id=raw)
            with self.assertRaises(ValueError):
                replace(self.offer, provider_id=raw)

    def test_malformed_schemas(self):
        for action in (
            lambda: Schema([INPUT.fields[0]]),
            lambda: Schema(('not a field',)),
            lambda: Schema(INPUT.fields * 2),
            lambda: Field('name', 'string', True, 'Meaning'),
            lambda: Field('name', FieldType.STRING, 1, 'Meaning'),
            lambda: Field('name', FieldType.STRING, True, ''),
            lambda: replace(self.offer.contract, inputs=None),
            lambda: replace(self.offer, contract=None),
        ):
            with self.assertRaises(ValueError):
                action()
        self.assertEqual(Schema(()).shape(), ())

    def test_metadata_required_and_immutable(self):
        for change in ({'description': ''}, {'source': ' '}, {'tags': {'mutable'}}, {'permissions': frozenset({''})}):
            with self.assertRaises(ValueError):
                replace(self.offer.metadata, **change)
        with self.assertRaises(ValueError):
            replace(self.offer, metadata=None)
        with self.assertRaises(FrozenInstanceError):
            self.offer.provider_id = 'changed'
        with self.assertRaises(ValueError):
            replace(self.offer, implementation_version='1.0.0')

    def test_shape_ignores_order_and_prose(self):
        reversed_schema = Schema(tuple(replace(f, semantics='Reworded description') for f in reversed(EXTENDED_OUTPUT.fields)))
        self.assertEqual(reversed_schema.shape(), EXTENDED_OUTPUT.shape())

    def test_invalid_requirements_and_keys(self):
        for action in (
            lambda: Requirement('terrain.slope.analyze', '>=2.0.0'),
            lambda: Requirement('terrain.slope.analyze', VersionRange.parse('2.0.0'), inputs='schema'),
            lambda: OfferKey('local', 'basic', 'capability', '1.0.0'),
            lambda: VersionRange(Version(1, 0, 0), include_lower=1),
        ):
            with self.assertRaises(ValueError):
                action()


class Registry(unittest.TestCase):
    def setUp(self):
        self.registry = sample_registry()
        self.requirement = Requirement('terrain.slope.analyze', VersionRange.parse('>=2.0.0 <3.0.0'))

    def test_exact_get_duplicate_and_unregister(self):
        offer = self.registry.list()[0]
        self.assertEqual(self.registry.get(offer.key), offer)
        with self.assertRaises(ValueError):
            self.registry.register(offer)
        with self.assertRaises(ValueError):
            self.registry.register(replace(offer, implementation_version=Version(9, 0, 0)))
        self.assertEqual(self.registry.unregister(offer.key), offer)
        for method in (self.registry.get, self.registry.unregister):
            with self.assertRaises(KeyError):
                method(offer.key)
        with self.assertRaises(ValueError):
            self.registry.register(None)

    def test_overlap_and_one_provider_many_capabilities(self):
        candidates = self.registry.find(self.requirement)
        self.assertEqual(len(candidates), 4)
        self.assertEqual(len({o.provider_id for o in candidates}), 2)
        self.assertEqual(len({o.implementation_id for o in candidates if o.provider_id == 'local-python'}), 2)
        self.registry.unregister(candidates[1].key)
        self.assertEqual(len(self.registry.find(self.requirement)), 3)
        self.assertTrue(self.registry.find(Requirement('parcel.describe', VersionRange.parse('1.0.0'), provider_id='local-python')))

    def test_stable_order_snapshot_and_isolation(self):
        snapshot = self.registry.list()
        other = CapabilityRegistry()
        for offer in reversed(snapshot):
            other.register(offer)
        self.assertEqual(other.list(), snapshot)
        other.unregister(snapshot[0].key)
        self.assertEqual(self.registry.list(), snapshot)
        self.assertEqual(len(snapshot), 6)
        numeric = CapabilityRegistry()
        for version in ('2.10.0', '2.9.0'):
            numeric.register(replace(snapshot[0], contract=replace(snapshot[0].contract, version=Version.parse(version))))
        self.assertEqual([str(o.contract.version) for o in numeric.list()], ['2.9.0', '2.10.0'])

    def test_schema_conflict_atomic(self):
        original = self.registry.list()[0]
        conflict = replace(original, provider_id='other', contract=replace(original.contract, outputs=OUTPUT))
        with self.assertRaisesRegex(ValueError, 'Conflicting schemas'):
            self.registry.register(conflict)
        self.assertEqual(len(self.registry.list()), 6)

    def test_schema_and_metadata_filters(self):
        self.assertEqual(len(self.registry.find(replace(self.requirement, outputs=EXTENDED_OUTPUT))), 3)
        self.assertEqual(len(self.registry.find(replace(self.requirement, outputs=OUTPUT))), 4)
        self.assertEqual(len(self.registry.find(replace(self.requirement, inputs=INPUT))), 4)
        for change in ({'inputs': Schema(())}, {'tags': frozenset({'missing'})}, {'provider_id': 'missing'}, {'capability_id': 'missing'}):
            self.assertEqual(self.registry.find(replace(self.requirement, **change)), ())
        self.assertEqual(len(self.registry.find(replace(self.requirement, tags=frozenset({'terrain'}), provider_id='remote-gis'))), 1)
        optional = Schema((replace(OUTPUT.fields[0], required=False),))
        self.assertEqual(len(self.registry.find(replace(self.requirement, outputs=optional))), 4)
        changed_type = Schema((replace(OUTPUT.fields[0], type=FieldType.INTEGER),))
        self.assertFalse(self.registry.find(replace(self.requirement, outputs=changed_type)))

    def test_output_presence_and_type_matrix(self):
        base = next(o for o in self.registry.list() if str(o.contract.version) == '2.0.0')
        for requested_required in (False, True):
            wanted = replace(OUTPUT.fields[0], required=requested_required)
            requirement = replace(self.requirement, outputs=Schema((wanted,)))
            for present in (False, True):
                for offered_required in (False, True):
                    for field_type in FieldType:
                        fields = (replace(wanted, required=offered_required, type=field_type),) if present else ()
                        offer = replace(base, contract=replace(base.contract, outputs=Schema(fields)))
                        expected = (not requested_required if not present else
                                    field_type == wanted.type and (not requested_required or offered_required))
                        with self.subTest(requested_required=requested_required, present=present,
                                          offered_required=offered_required, field_type=field_type):
                            result = compatible(requirement, offer)
                            self.assertEqual(result.matches, expected)
                            self.assertEqual(bool(result.reasons), not expected)
                            registry = CapabilityRegistry()
                            registry.register(offer)
                            self.assertEqual(registry.find(requirement), (offer,) if expected else ())

    def test_extra_outputs_and_empty_needs(self):
        for outputs in (OUTPUT, Schema(()), None):
            self.assertEqual(len(self.registry.find(replace(self.requirement, outputs=outputs))), 4)
        wanted = Schema(tuple(reversed(EXTENDED_OUTPUT.fields)))
        self.assertEqual(len(self.registry.find(replace(self.requirement, outputs=wanted))), 3)
        # Accepting output extras must not relax input checks or major versions.
        extra_input = Schema(INPUT.fields + (Field('resolution', FieldType.NUMBER, False, 'Resolution.'),))
        self.assertFalse(self.registry.find(replace(self.requirement, inputs=extra_input, outputs=OUTPUT)))
        major_three = next(o for o in self.registry.list() if o.contract.version.major == 3)
        self.assertFalse(compatible(replace(self.requirement, outputs=Schema(())), major_three))

    def test_output_diagnostics(self):
        base = next(o for o in self.registry.list() if str(o.contract.version) == '2.0.0')
        requirement = replace(self.requirement, outputs=EXTENDED_OUTPUT)
        altered = Schema((replace(OUTPUT.fields[0], required=False, type=FieldType.STRING),))
        offer = replace(base, contract=replace(base.contract, outputs=altered))
        self.assertEqual(compatible(requirement, offer).reasons, (
            "output 'max_slope' is required but missing",
            "output 'mean_slope' type differs: expected number, offered string",
            "output 'mean_slope' is required but only optional in offer",
        ))

    def test_find_compatible_agree_and_reasons(self):
        for requirement in (self.requirement, replace(self.requirement, outputs=EXTENDED_OUTPUT), replace(self.requirement, tags=frozenset({'missing'}))):
            self.assertEqual(self.registry.find(requirement), tuple(o for o in self.registry.list() if self.registry.compatible(requirement, o).matches))
        wrong_major = next(o for o in self.registry.list() if o.contract.version.major == 3)
        result = compatible(self.requirement, wrong_major)
        self.assertFalse(result)
        self.assertIn('contract version is outside requested range', result.reasons)
        old = next(o for o in self.registry.list() if str(o.contract.version) == '2.0.0')
        self.assertIn("output 'max_slope' is required but missing", compatible(replace(self.requirement, outputs=EXTENDED_OUTPUT), old).reasons)


class CLI(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run([sys.executable, '-m', 'alaetheia', *args], text=True, capture_output=True, env=os.environ.copy())

    def test_list_json(self):
        result = self.run_cli('list', '--json')
        self.assertEqual(result.returncode, 0, result.stderr)
        records = json.loads(result.stdout)
        self.assertEqual(len(records), 6)
        self.assertIn('permissions', records[0]['metadata'])
        self.assertEqual(records[0]['contract']['version'], '1.0.0')

    def test_inspect_and_human_listing(self):
        result = self.run_cli('inspect', 'terrain.slope.analyze', '--version', '2.1.0', '--json')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(json.loads(result.stdout)), 3)
        result = self.run_cli('inspect', 'terrain.slope.analyze', '--range', '>=2.0.0 <3.0.0', '--json')
        self.assertEqual(len(json.loads(result.stdout)), 4)
        result = self.run_cli('list')
        self.assertEqual(result.returncode, 0, result.stderr)
        for text in ('inputs:', 'outputs:', 'metadata:', 'remote-gis', 'source', 'implementation'):
            self.assertIn(text, result.stdout)

    def test_errors(self):
        for args in ((), ('execute',), ('inspect', 'unknown'), ('inspect', 'Bad.ID'), ('inspect', 'terrain.slope.analyze', '--version', '1'), ('inspect', 'terrain.slope.analyze', '--range', '^2.0.0'), ('inspect', 'terrain.slope.analyze', '--version', '9.0.0'), ('inspect', 'terrain.slope.analyze', '--version', '2.0.0', '--range', '>=2.0.0')):
            with self.subTest(args=args):
                result = self.run_cli(*args)
                self.assertEqual(result.returncode, 2)
                self.assertIn('error:', result.stderr)
                self.assertNotIn('Traceback', result.stderr)


if __name__ == '__main__':
    unittest.main()
