"""Three fixed workflow definitions with manifest evidence, no callable catalog."""
from .contracts import (CapabilityContract, CapabilityManifest, Field, FieldType,
                        Metadata, Requirement, Schema, Version, VersionRange)
from .parcel_example import example as parcel_example
from .selection import CatalogEntry, checked_catalog
from .workflow import InputBinding, OutputRef, Workflow, WorkflowInputRef, WorkflowStep

CATALOG_REVISION = '1'


def catalog() -> tuple[CatalogEntry, ...]:
    inputs = Schema((Field('text', FieldType.STRING, True, 'Supplied text; no coercion.'),))
    offers = []
    for capability, field, field_type in (
        ('text.strip', 'cleaned', FieldType.STRING),
        ('text.count', 'count', FieldType.INTEGER),
    ):
        # Same functions and semantics as workflow_example, with declarations
        # explicit here so the evaluation need not access a runner's internals.
        contract = CapabilityContract(capability, Version(1, 0, 0), inputs,
            Schema((Field(field, field_type, True, 'Strip surrounding whitespace or count Unicode code points.'),)))
        offers.append(CapabilityManifest(contract, 'local-python', 'direct', Version(1, 0, 0),
            Metadata('Pure local text function.', frozenset({'text'}), frozenset(),
                     frozenset(), 'alaetheia.workflow_example')))

    def step(name, offer, source):
        return WorkflowStep(name, offer.key,
            Requirement(offer.contract.capability_id, VersionRange.parse('1.0.0'),
                        offer.contract.inputs, offer.contract.outputs),
            (InputBinding('text', source),))

    strip, count = offers
    raw = Workflow('text-count-raw', (step('count', count, WorkflowInputRef('text')),), inputs)
    trimmed = Workflow('text-count-trimmed', (
        step('strip', strip, WorkflowInputRef('text')),
        step('count', count, OutputRef('strip', 'cleaned'))), inputs)
    # Reuse Lab 006 exactly. Construction creates bindings but invokes nothing;
    # only immutable definitions/manifests cross into the proposal evaluator.
    executor, parcel = parcel_example()
    manifests = tuple(executor.inspect_selection(s.selected_key, s.requirement).offer for s in parcel.steps)
    return checked_catalog((
        CatalogEntry('Count Unicode code points including surrounding whitespace.', raw, (count,)),
        CatalogEntry('Strip surrounding whitespace, then count Unicode code points.', trimmed, (strip, count)),
        CatalogEntry('Summarize supplied parcel facts; no lookup, verification, or suitability assessment.', parcel, manifests),
    ))
