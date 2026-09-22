"""Proposal data validation. This module has no executor or runner to invoke.

Typed records are validation results, not an external deserialization shortcut.
Call validate_proposal for every untrusted proposal. Snapshots remain editable.
"""
from dataclasses import dataclass
from enum import Enum

from .contracts import CapabilityManifest, Schema
from .execution import validate_payload
from .output_values import snapshot_output
from .workflow import Workflow


class AbstentionReason(str, Enum):
    AMBIGUOUS = 'ambiguous_request'
    UNSUPPORTED = 'unsupported_request'
    INSUFFICIENT = 'insufficient_inputs'


@dataclass(frozen=True)
class CatalogEntry:
    description: str
    workflow: Workflow
    manifests: tuple[CapabilityManifest, ...]

    @property
    def workflow_id(self) -> str:
        return self.workflow.workflow_id

    @property
    def inputs(self) -> Schema:
        return self.workflow.inputs


def checked_catalog(entries: tuple[CatalogEntry, ...]) -> tuple[CatalogEntry, ...]:
    """Validate the explicit catalog; do not discover, rank, or bind providers."""
    if type(entries) is not tuple or not entries or any(type(e) is not CatalogEntry for e in entries):
        raise ValueError('Expected a nonempty tuple of CatalogEntry records')
    if len({e.workflow_id for e in entries}) != len(entries):
        raise ValueError('Duplicate workflow ID')
    for entry in entries:
        if type(entry.description) is not str or not entry.description.strip():
            raise ValueError('Catalog description must be nonempty')
        if type(entry.manifests) is not tuple or any(type(m) is not CapabilityManifest for m in entry.manifests):
            raise ValueError('Expected manifest tuple')
        keys = [m.key for m in entry.manifests]
        if len(set(keys)) != len(keys) or set(keys) != {s.selected_key for s in entry.workflow.steps}:
            raise ValueError('Manifests must exactly cover selected offers')
    return entries


@dataclass(frozen=True)
class SelectionProposal:
    workflow_id: str
    inputs: dict[str, object]


@dataclass(frozen=True)
class AbstentionProposal:
    reason: AbstentionReason


@dataclass(frozen=True)
class Diagnostic:
    code: str
    location: str
    message: str


@dataclass(frozen=True)
class ProposalCheck:
    proposal: SelectionProposal | AbstentionProposal | None
    diagnostics: tuple[Diagnostic, ...] = ()

    @property
    def valid(self) -> bool:
        return self.proposal is not None and not self.diagnostics


def same_data(left: object, right: object) -> bool:
    """Type-sensitive equality on already snapshotted builtin data only."""
    if type(left) is not type(right):
        return False
    if type(left) is dict:
        return left.keys() == right.keys() and all(same_data(left[k], right[k]) for k in left)
    if type(left) is list:
        return len(left) == len(right) and all(same_data(a, b) for a, b in zip(left, right))
    return left == right


def validate_proposal(raw: object, supplied: object,
                      catalog: tuple[CatalogEntry, ...]) -> ProposalCheck:
    checked_catalog(catalog)

    def reject(code, location, message):
        return ProposalCheck(None, (Diagnostic(code, location, message),))

    try:
        data = snapshot_output(raw)
    except ValueError as error:
        return reject('unsupported_data', 'proposal', str(error))
    kind = data.get('kind')
    if type(kind) is not str or kind not in ('select', 'abstain'):
        return reject('invalid_shape', 'kind', 'Expected select or abstain tag')
    if kind == 'abstain':
        if set(data) != {'kind', 'reason'} or type(data['reason']) is not str:
            return reject('invalid_shape', 'proposal', 'Abstention requires only kind and string reason')
        try:
            return ProposalCheck(AbstentionProposal(AbstentionReason(data['reason'])))
        except ValueError:
            return reject('unknown_reason', 'reason', 'Unknown abstention reason')
    if set(data) != {'kind', 'workflow_id', 'inputs'} or type(data['workflow_id']) is not str:
        return reject('invalid_shape', 'proposal', 'Selection requires only kind, string workflow_id, and inputs')
    entry = next((e for e in catalog if e.workflow_id == data['workflow_id']), None)
    if entry is None:
        return reject('unknown_workflow', 'workflow_id', 'Workflow is not in the fixed catalog')
    errors = validate_payload(entry.inputs, data['inputs'], allow_extra=False)
    if errors:
        return ProposalCheck(None, tuple(Diagnostic('invalid_inputs', 'inputs', e) for e in errors))
    try:
        original = snapshot_output(supplied)
    except ValueError as error:
        return reject('invalid_supplied_data', 'supplied', str(error))
    if not same_data(original, data['inputs']):
        return reject('changed_inputs', 'inputs', 'Proposed inputs differ in values, keys, or types from supplied inputs')
    return ProposalCheck(SelectionProposal(entry.workflow_id, data['inputs']))
