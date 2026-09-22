"""Compare preflight findings with explicit local runs; no background monitor."""
from dataclasses import asdict
import json
from .contracts import (CapabilityContract, CapabilityManifest, Field, FieldType, Metadata,
                        Requirement, Schema, Version, VersionRange)
from .execution import LocalBinding, LocalExecutor
from .preflight import WorkflowPreflight, compare_run
from .registry import CapabilityRegistry
from .workflow import InputBinding, Literal, OutputRef, Workflow, WorkflowRunner, WorkflowStep


def scenario(*, optional: bool, omit: bool):
    registry = CapabilityRegistry()
    bindings = []
    steps = []
    for step_id, output_required in (('produce', not optional), ('consume', True)):
        contract = CapabilityContract(f'text.{step_id}', Version(1, 0, 0),
            Schema((Field('text', FieldType.STRING, True, 'Example text.'),)),
            Schema((Field('text', FieldType.STRING, output_required, 'Returned example text.'),)))
        offer = CapabilityManifest(contract, 'local-python', 'direct', Version(1, 0, 0),
            Metadata('Pure omission experiment.', frozenset(), frozenset(), frozenset(), 'alaetheia.preflight_example'))
        registry.register(offer)
        if step_id == 'produce' and omit:
            function = lambda payload: {}
        else:
            function = lambda payload: {'text': payload['text']}
        bindings.append(LocalBinding(offer, function))
        source = Literal('Theia') if step_id == 'produce' else OutputRef('produce', 'text')
        steps.append(WorkflowStep(step_id, offer.key,
            Requirement(contract.capability_id, VersionRange.parse('1.0.0')),
            (InputBinding('text', source),)))
    return LocalExecutor(registry, tuple(bindings)), Workflow('omission-example', tuple(steps))


def main():
    results = []
    for name, optional, omit in (('optional-present', True, False),
                                  ('optional-absent', True, True),
                                  ('required-absent', False, True)):
        executor, workflow = scenario(optional=optional, omit=omit)
        report = WorkflowPreflight(executor).inspect(workflow)
        # Running is a separate, explicit action; preflight never does it.
        record = WorkflowRunner(executor).run(workflow)
        results.append({'scenario': name, 'findings': [asdict(f) for f in report.findings],
                        'comparison': asdict(compare_run(report, record))})
    print(json.dumps(results, indent=2))


if __name__ == '__main__':
    main()
