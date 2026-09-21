"""One synchronous invocation of an explicitly bound, trusted local function.

This is not a sandbox, scheduler, persistent ledger, or authorization engine.
"""
from collections.abc import Callable, Mapping
from copy import deepcopy
from dataclasses import dataclass
from enum import Enum
import math

from .contracts import CapabilityManifest, FieldType, OfferKey, Requirement, Schema
from .registry import CapabilityRegistry, compatible


class Outcome(str, Enum):
    SUCCESS = 'success'
    SELECTION_REJECTED = 'selection_rejected'
    INVALID_INPUT = 'invalid_input'
    PROVIDER_FAILURE = 'provider_failure'
    INVALID_OUTPUT = 'invalid_output'


@dataclass(frozen=True)
class ExecutionRecord:
    """Detached payload snapshots; their dictionaries remain caller-editable.

    Missing selections have no resolved offer. Otherwise the immutable manifest
    records both contract and implementation versions, even if later unregistered.
    """
    selected_key: OfferKey
    offer: CapabilityManifest | None
    outcome: Outcome
    invoked: bool
    inputs: dict[str, object] | None = None
    outputs: dict[str, object] | None = None
    errors: tuple[str, ...] = ()
    exception_type: str | None = None


def _matches(value: object, field_type: FieldType) -> bool:
    # bool is an int subclass in Python, but is not a numeric payload here.
    if field_type == FieldType.STRING:
        return type(value) is str
    if field_type == FieldType.BOOLEAN:
        return type(value) is bool
    if field_type == FieldType.INTEGER:
        return type(value) is int
    return type(value) is int or (type(value) is float and math.isfinite(value))


def validate_payload(schema: Schema, payload: object, *, allow_extra: bool) -> tuple[str, ...]:
    """Validate a plain string-keyed dictionary without converting its values.

    NUMBER accepts int or finite float, INTEGER only int. Neither accepts bool.
    Optional means absent is allowed, not that None is valid. Extra output values
    are not schema-validated unless named by the offer or requirement.
    """
    if type(payload) is not dict or any(type(key) is not str for key in payload):
        return ('expected a plain dictionary with string keys',)
    errors = []
    for field in sorted(schema.fields, key=lambda field: field.name):
        if field.name not in payload:
            if field.required:
                errors.append(f'{field.name!r}: required field is missing')
        elif not _matches(payload[field.name], field.type):
            errors.append(f'{field.name!r}: expected {field.type.value}')
    if not allow_extra:
        for name in sorted(payload.keys() - {field.name for field in schema.fields}):
            errors.append(f'{name!r}: unexpected input field')
    return tuple(errors)


@dataclass(frozen=True)
class LocalBinding:
    offer: CapabilityManifest
    function: Callable[[Mapping[str, object]], object]

    def __post_init__(self) -> None:
        if not isinstance(self.offer, CapabilityManifest) or not callable(self.function):
            raise ValueError('Binding needs a manifest and a callable')
        if self.offer.metadata.side_effects or self.offer.metadata.permissions:
            raise ValueError('Lab 002 bindings must declare no side effects or permissions')


class LocalExecutor:
    """Explicit caller-owned bindings, with no discovery-based selection or retry.

    Callable purity is the developer's responsibility; declarations cannot enforce
    it. Bindings pin the full manifest to detect changed implementation versions.
    """
    def __init__(self, registry: CapabilityRegistry, bindings: tuple[LocalBinding, ...]) -> None:
        self._registry = registry
        self._bindings: dict[OfferKey, LocalBinding] = {}
        for binding in bindings:
            if not isinstance(binding, LocalBinding):
                raise ValueError('Expected LocalBinding')
            if binding.offer.key in self._bindings:
                raise ValueError('Duplicate local binding')
            if registry.get(binding.offer.key) != binding.offer:
                raise ValueError('Binding manifest differs from registered offer')
            self._bindings[binding.offer.key] = binding

    def invoke(self, key: OfferKey, requirement: Requirement, payload: object) -> ExecutionRecord:
        try:
            offer = self._registry.get(key)
        except KeyError:
            return ExecutionRecord(key, None, Outcome.SELECTION_REJECTED, False,
                                   errors=('selected offer is not registered',))
        binding = self._bindings.get(key)
        errors = list(compatible(requirement, offer).reasons)
        if binding is None:
            errors.append('selected offer has no local binding')
        elif binding.offer != offer:
            errors.append('local binding is stale: registered manifest changed')
        if errors:
            return ExecutionRecord(key, offer, Outcome.SELECTION_REJECTED, False, errors=tuple(errors))
        errors = validate_payload(offer.contract.inputs, payload, allow_extra=False)
        if errors:
            return ExecutionRecord(key, offer, Outcome.INVALID_INPUT, False, errors=errors)
        # Valid input values are immutable scalars. Give the provider its own dict
        # so provider edits cannot alter the caller's input or recorded snapshot.
        inputs = dict(payload)
        try:
            output = binding.function(dict(inputs))
        except Exception as error:
            # Process-control exceptions (KeyboardInterrupt, SystemExit) propagate.
            return ExecutionRecord(key, offer, Outcome.PROVIDER_FAILURE, True, inputs,
                                   errors=(str(error),), exception_type=type(error).__name__)
        errors = tuple(f'provider output: {e}' for e in validate_payload(
            offer.contract.outputs, output, allow_extra=True))
        if requirement.outputs is not None:
            errors += tuple(f'consumer output: {e}' for e in validate_payload(
                requirement.outputs, output, allow_extra=True))
        if errors:
            return ExecutionRecord(key, offer, Outcome.INVALID_OUTPUT, True, inputs, errors=errors)
        try:
            # Retain extra output fields, including nested extras, without sharing
            # mutable containers with the provider. This is not payload persistence.
            snapshot = deepcopy(output)
        except Exception as error:
            return ExecutionRecord(key, offer, Outcome.INVALID_OUTPUT, True, inputs,
                                   errors=('output cannot be copied for inspection',),
                                   exception_type=type(error).__name__)
        return ExecutionRecord(key, offer, Outcome.SUCCESS, True, inputs, snapshot)
