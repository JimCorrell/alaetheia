"""Run `python -m alaetheia.workflow_example [--incompatible]` to inspect a run."""
import argparse
from dataclasses import asdict
import json

from .contracts import (CapabilityContract, CapabilityManifest, Field, FieldType,
                        Metadata, Requirement, Schema, Version, VersionRange)
from .execution import LocalBinding, LocalExecutor
from .registry import CapabilityRegistry
from .workflow import InputBinding, Literal, OutputRef, Workflow, WorkflowRunner, WorkflowStep


def strip_text(payload):
    return {'cleaned': payload['text'].strip()}


def count_text(payload):
    return {'count': len(payload['text']), 'method': 'len'}


def format_count(payload):
    return {'message': f"Characters: {payload['count']}"}


def example(*, incompatible: bool = False) -> tuple[WorkflowRunner, Workflow]:
    registry = CapabilityRegistry()
    bindings = []
    offers = []
    for name, input_name, input_type, output_name, output_type, function in (
        ('text.strip', 'text', FieldType.STRING, 'cleaned', FieldType.STRING, strip_text),
        ('text.count', 'text', FieldType.STRING, 'count', FieldType.INTEGER, count_text),
        ('count.format', 'count', FieldType.INTEGER, 'message', FieldType.STRING, format_count),
    ):
        contract = CapabilityContract(name, Version(1, 0, 0),
            Schema((Field(input_name, input_type, True, 'Input to the local text example.'),)),
            Schema((Field(output_name, output_type, True, 'Text transformation result; counts measure Unicode code points.'),)))
        offer = CapabilityManifest(contract, 'local-python', 'direct', Version(1, 0, 0),
            Metadata('Pure local workflow example.', frozenset({'text'}), frozenset(),
                     frozenset(), 'alaetheia.workflow_example'))
        registry.register(offer)
        offers.append(offer)
        bindings.append(LocalBinding(offer, function))
    def step(step_id, offer, inputs):
        return WorkflowStep(step_id, offer.key,
            Requirement(offer.contract.capability_id, VersionRange.parse('1.0.0'),
                        inputs=offer.contract.inputs, outputs=offer.contract.outputs), inputs)
    workflow = Workflow('text-summary', (
        step('strip', offers[0], (InputBinding('text', Literal('  Theia  ')),)),
        # Failure variant deliberately feeds text to an integer input. The final
        # step will be skipped, making the fail-fast result visible in the demo.
        step('middle', offers[2] if incompatible else offers[1],
             (InputBinding('count' if incompatible else 'text', OutputRef('strip', 'cleaned')),)),
        step('format', offers[2], (InputBinding('count', OutputRef('middle', 'count')),)),
    ))
    return WorkflowRunner(LocalExecutor(registry, tuple(bindings))), workflow


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--incompatible', action='store_true')
    args = parser.parse_args()
    runner, workflow = example(incompatible=args.incompatible)
    record = runner.run(workflow)
    # This demo serializes only its own scalar text catalog; no generic storage
    # format or persistence contract is implied.
    def encode(value):
        if isinstance(value, Version):
            return str(value)
        if isinstance(value, frozenset):
            return sorted(value)
        raise TypeError(f'Unsupported value: {type(value).__name__}')
    print(json.dumps(asdict(record), default=encode, indent=2))
    return 0 if record.failed_step is None else 1


if __name__ == '__main__':
    raise SystemExit(main())
