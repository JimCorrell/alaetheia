"""Summarize supplied fictional parcel records using one reusable local workflow."""
from dataclasses import asdict
import json
from collections.abc import Mapping

from .contracts import (CapabilityContract, CapabilityManifest, Field, FieldType, Metadata,
                        Requirement, Schema, Version, VersionRange)
from .execution import LocalBinding, LocalExecutor
from .preflight import WorkflowPreflight, compare_run
from .registry import CapabilityRegistry
from .workflow import InputBinding, OutputRef, Workflow, WorkflowInputRef, WorkflowRunner, WorkflowStep

PARCEL_INPUTS = Schema((
    Field('parcel_id', FieldType.STRING, True, 'User-supplied parcel identifier; no external verification.'),
    Field('municipality', FieldType.STRING, True, 'User-supplied municipality name.'),
    Field('acreage', FieldType.NUMBER, True, 'User-supplied area in acres; must be positive.'),
    Field('road_access', FieldType.BOOLEAN, True, 'User-reported road access; not a legal access determination.'),
))
SUMMARY_OUTPUT = Schema((Field('summary', FieldType.STRING, True, 'Descriptive summary of supplied data only.'),))


def validate_parcel(values: Mapping[str, object]) -> dict[str, object]:
    # Scalar validation is the runtime's job; these are domain-specific rules.
    if not values['parcel_id'].strip() or not values['municipality'].strip():
        raise ValueError('Parcel ID and municipality must contain non-whitespace text')
    if values['acreage'] <= 0:
        raise ValueError('Acreage must be positive')
    return {**values, 'parcel_id': values['parcel_id'].strip(),
            'municipality': values['municipality'].strip()}


def summarize_parcel(values: Mapping[str, object]) -> dict[str, object]:
    access = 'yes' if values['road_access'] else 'no'
    return {'summary': f"Parcel {values['parcel_id']} in {values['municipality']}: "
            f"{values['acreage']} acres; reported road access: {access}. Supplied data only."}


def example() -> tuple[LocalExecutor, Workflow]:
    registry = CapabilityRegistry()
    bindings = []
    steps = []
    for step_id, outputs, function in (
        ('validate', PARCEL_INPUTS, validate_parcel),
        ('summarize', SUMMARY_OUTPUT, summarize_parcel),
    ):
        contract = CapabilityContract(f'parcel.record.{step_id}', Version(1, 0, 0), PARCEL_INPUTS, outputs)
        offer = CapabilityManifest(contract, 'local-python', 'direct', Version(1, 0, 0),
            Metadata('Pure supplied-record example; no parcel lookup or suitability assessment.',
                     frozenset({'parcel'}), frozenset(), frozenset(), 'alaetheia.parcel_example'))
        registry.register(offer)
        bindings.append(LocalBinding(offer, function))
        wiring = tuple(InputBinding(f.name, WorkflowInputRef(f.name) if step_id == 'validate'
                                   else OutputRef('validate', f.name)) for f in PARCEL_INPUTS.fields)
        steps.append(WorkflowStep(step_id, offer.key,
            Requirement(contract.capability_id, VersionRange.parse('1.0.0'), PARCEL_INPUTS, outputs), wiring))
    return LocalExecutor(registry, tuple(bindings)), Workflow('parcel-record-summary', tuple(steps), PARCEL_INPUTS)


def main() -> None:
    executor, workflow = example()
    report = WorkflowPreflight(executor).inspect(workflow)
    cases = (
        ('rural', {'parcel_id': 'R-101', 'municipality': 'Example Township', 'acreage': 42.5, 'road_access': False}),
        ('small-lot', {'parcel_id': ' L-2 ', 'municipality': ' Sample Town ', 'acreage': 0.25, 'road_access': True}),
        ('whole-acres', {'parcel_id': 'P-3', 'municipality': 'Test Village', 'acreage': 12, 'road_access': True}),
        ('wrong-type', {'parcel_id': 'P-4', 'municipality': 'Test Village', 'acreage': '12', 'road_access': True}),
        ('invalid-domain', {'parcel_id': 'P-5', 'municipality': 'Test Village', 'acreage': -1, 'road_access': True}),
    )
    results = []
    for name, values in cases:
        record = WorkflowRunner(executor).run(workflow, values)
        results.append({'case': name, 'inputs': record.inputs, 'errors': record.errors,
                        'comparison': asdict(compare_run(report, record)),
                        'steps': [{'step_id': s.step_id, 'status': s.status.value, 'errors': s.errors,
                                   'outputs': s.execution.outputs if s.execution else None} for s in record.steps]})
    print(json.dumps(results, indent=2))


if __name__ == '__main__':
    main()
