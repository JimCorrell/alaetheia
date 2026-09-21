"""Run with: python -m alaetheia.invocation_example. No remote providers."""
import json
from collections.abc import Mapping
from .contracts import (CapabilityContract, CapabilityManifest, Field, FieldType,
                        Metadata, OfferKey, Requirement, Schema, Version, VersionRange)
from .execution import LocalBinding, LocalExecutor
from .registry import CapabilityRegistry


def count_direct(values: Mapping[str, object]) -> dict[str, object]:
    return {'count': len(values['text']), 'method': 'len'}


def count_iterated(values: Mapping[str, object]) -> dict[str, object]:
    return {'count': sum(1 for _ in values['text']), 'method': 'iteration'}


def example() -> tuple[CapabilityRegistry, LocalExecutor, Requirement, OfferKey]:
    contract = CapabilityContract('text.characters.count', Version(1, 0, 0),
        Schema((Field('text', FieldType.STRING, True, 'Python Unicode string.'),)),
        Schema((Field('count', FieldType.INTEGER, True, 'Number of Unicode code points, not graphemes.'),)))
    registry = CapabilityRegistry()
    bindings = []
    for implementation, function in (('direct', count_direct), ('iterated', count_iterated)):
        offer = CapabilityManifest(contract, 'local-python', implementation, Version(1, 0, 0),
            Metadata('Pure local character count example.', frozenset({'text'}),
                     frozenset(), frozenset(), 'alaetheia.invocation_example'))
        registry.register(offer)
        bindings.append(LocalBinding(offer, function))
    requirement = Requirement(contract.capability_id, VersionRange.parse('1.0.0'),
                              inputs=contract.inputs, outputs=contract.outputs)
    # Name the implementation explicitly; never take the first discovery result.
    selected = OfferKey('local-python', 'iterated', contract.capability_id, contract.version)
    return registry, LocalExecutor(registry, tuple(bindings)), requirement, selected


def main() -> None:
    _, executor, requirement, selected = example()
    record = executor.invoke(selected, requirement, {'text': 'Theia'})
    print(json.dumps({
        'capability': selected.capability_id,
        'contract_version': str(selected.contract_version),
        'provider': selected.provider_id,
        'implementation': selected.implementation_id,
        'implementation_version': str(record.offer.implementation_version),
        'outcome': record.outcome.value, 'invoked': record.invoked,
        'inputs': record.inputs, 'outputs': record.outputs, 'errors': record.errors,
    }, indent=2))


if __name__ == '__main__':
    main()
