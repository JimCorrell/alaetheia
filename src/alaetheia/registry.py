"""Discovery yields candidates, never rankings, authorization, or execution."""
from dataclasses import dataclass
from .contracts import CapabilityManifest, OfferKey, Requirement


@dataclass(frozen=True)
class Compatibility:
    matches: bool
    reasons: tuple[str, ...]

    def __bool__(self) -> bool:
        return self.matches


def compatible(requirement: Requirement, offer: CapabilityManifest) -> Compatibility:
    reasons = []
    contract = offer.contract
    if requirement.capability_id != contract.capability_id:
        reasons.append('capability ID differs')
    if not requirement.versions.contains(contract.version):
        reasons.append('contract version is outside requested range')
    for label in ('inputs', 'outputs'):
        wanted = getattr(requirement, label)
        if wanted is not None and wanted.shape() != getattr(contract, label).shape():
            reasons.append(f'{label} schema differs (exact shape required)')
    if not requirement.tags <= offer.metadata.tags:
        reasons.append('required tags are missing')
    if requirement.provider_id is not None and requirement.provider_id != offer.provider_id:
        reasons.append('provider ID differs')
    return Compatibility(not reasons, tuple(reasons))


class CapabilityRegistry:
    def __init__(self) -> None:
        self._offers: dict[OfferKey, CapabilityManifest] = {}

    def register(self, offer: CapabilityManifest) -> None:
        if not isinstance(offer, CapabilityManifest):
            raise ValueError('Expected CapabilityManifest')
        if offer.key in self._offers:
            raise ValueError(f'Duplicate offer key: {offer.key}')
        # One semantic ID/version cannot truthfully declare two different shapes.
        for existing in self._offers.values():
            a, b = existing.contract, offer.contract
            if (a.capability_id, a.version) == (b.capability_id, b.version) and (
                a.inputs.shape() != b.inputs.shape() or a.outputs.shape() != b.outputs.shape()
            ):
                raise ValueError('Conflicting schemas for the same capability ID/version')
        self._offers[offer.key] = offer

    def unregister(self, key: OfferKey) -> CapabilityManifest:
        """Remove exactly one offer; missing keys raise KeyError."""
        return self._offers.pop(key)

    def get(self, key: OfferKey) -> CapabilityManifest:
        """Exact lookup; missing keys raise KeyError."""
        return self._offers[key]

    def list(self) -> tuple[CapabilityManifest, ...]:
        """Snapshot sorted by capability, numeric version, provider, implementation."""
        return tuple(sorted(self._offers.values(), key=lambda o: (
            o.contract.capability_id, o.contract.version, o.provider_id, o.implementation_id)))

    def find(self, requirement: Requirement) -> tuple[CapabilityManifest, ...]:
        return tuple(o for o in self.list() if compatible(requirement, o))

    compatible = staticmethod(compatible)
