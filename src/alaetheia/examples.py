"""Fictional provider declarations only; nothing here calculates terrain."""
from .contracts import (CapabilityContract, CapabilityManifest, Field, FieldType,
                        Metadata, Schema, Version)
from .registry import CapabilityRegistry

INPUT = Schema((Field('parcel_id', FieldType.STRING, True, 'Parcel identifier in the declared source catalog.'),))
OUTPUT = Schema((Field('mean_slope', FieldType.NUMBER, True, 'Mean slope in degrees.'),))
EXTENDED_OUTPUT = Schema(OUTPUT.fields + (Field('max_slope', FieldType.NUMBER, True, 'Maximum slope in degrees.'),))


def sample_registry() -> CapabilityRegistry:
    registry = CapabilityRegistry()
    for capability, version, provider, implementation, output in (
        ('terrain.slope.analyze', '2.0.0', 'local-python', 'basic', OUTPUT),
        ('terrain.slope.analyze', '2.1.0', 'local-python', 'basic', EXTENDED_OUTPUT),
        ('terrain.slope.analyze', '2.1.0', 'local-python', 'precise', EXTENDED_OUTPUT),
        ('terrain.slope.analyze', '2.1.0', 'remote-gis', 'standard', EXTENDED_OUTPUT),
        ('terrain.slope.analyze', '3.0.0', 'remote-gis', 'standard', Schema((Field('slope_percent', FieldType.NUMBER, True, 'Mean slope as a percentage.'),))),
        ('parcel.describe', '1.0.0', 'local-python', 'catalog', Schema((Field('label', FieldType.STRING, True, 'Display name.'),))),
    ):
        registry.register(CapabilityManifest(
            CapabilityContract(capability, Version.parse(version), INPUT, output),
            provider, implementation, Version.parse('1.0.0'),
            Metadata('Fictional catalog offer; no executable implementation.',
                     frozenset({'terrain' if capability.startswith('terrain') else 'parcel'}),
                     frozenset({'network-request'}) if provider == 'remote-gis' else frozenset(),
                     frozenset({'gis.read'}) if provider == 'remote-gis' else frozenset(),
                     'alaetheia.examples:sample_registry'),
        ))
    return registry
