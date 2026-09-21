"""Small immutable declarations; no schema engine and no invocation machinery."""
from dataclasses import dataclass
from enum import Enum
import re


def identifier(value: str) -> None:
    if not isinstance(value, str) or not re.fullmatch(r"[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*", value):
        raise ValueError(f"Invalid identifier: {value!r}")


def nonempty(value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Expected nonempty text")


def strings(values: frozenset[str]) -> None:
    if not isinstance(values, frozenset):
        raise ValueError("Expected immutable frozenset of strings")
    for value in values:
        nonempty(value)


@dataclass(frozen=True, order=True)
class Version:
    major: int
    minor: int
    patch: int

    def __post_init__(self) -> None:
        if any(type(n) is not int or n < 0 for n in (self.major, self.minor, self.patch)):
            raise ValueError("Version components must be nonnegative integers")

    @classmethod
    def parse(cls, text: str) -> 'Version':
        if not isinstance(text, str) or not re.fullmatch(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)", text):
            raise ValueError(f"Expected release MAJOR.MINOR.PATCH: {text!r}")
        return cls(*(int(n) for n in text.split('.')))

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"


@dataclass(frozen=True)
class VersionRange:
    """Inclusive/exclusive bounds on discrete release versions; no implied caret rules."""
    lower: Version
    upper: Version | None = None
    include_lower: bool = True
    include_upper: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.lower, Version) or (self.upper is not None and not isinstance(self.upper, Version)):
            raise ValueError("Bounds must be Versions")
        if type(self.include_lower) is not bool or type(self.include_upper) is not bool:
            raise ValueError("Boundary flags must be booleans")
        first = self.lower if self.include_lower else Version(self.lower.major, self.lower.minor, self.lower.patch + 1)
        if self.upper is not None and (first > self.upper or (first == self.upper and not self.include_upper)):
            raise ValueError("Empty or contradictory version range")

    @classmethod
    def parse(cls, text: str) -> 'VersionRange':
        if not isinstance(text, str) or not text.strip():
            raise ValueError("Version range cannot be empty")
        lower, upper, il, iu = Version(0, 0, 0), None, True, False
        seen: set[str] = set()
        for token in text.split():
            match = re.fullmatch(r"(>=|<=|>|<|==)?([0-9]+\.[0-9]+\.[0-9]+)", token)
            if match is None:
                raise ValueError(f"Unsupported range token: {token!r}")
            op, raw = match.groups()
            version = Version.parse(raw)
            side = 'lower' if op in ('>', '>=') else 'upper'
            if op in (None, '=='):
                if len(text.split()) != 1:
                    raise ValueError("Exact version must stand alone")
                return cls(version, version, True, True)
            if side in seen:
                raise ValueError(f"Repeated {side} bound")
            seen.add(side)
            if side == 'lower':
                lower, il = version, op == '>='
            else:
                upper, iu = version, op == '<='
        return cls(lower, upper, il, iu)

    def contains(self, version: Version) -> bool:
        return (version > self.lower or (self.include_lower and version == self.lower)) and (
            self.upper is None or version < self.upper or (self.include_upper and version == self.upper))


class FieldType(str, Enum):
    STRING = 'string'
    INTEGER = 'integer'
    NUMBER = 'number'
    BOOLEAN = 'boolean'


@dataclass(frozen=True)
class Field:
    name: str
    type: FieldType
    required: bool
    semantics: str

    def __post_init__(self) -> None:
        identifier(self.name)
        if not isinstance(self.type, FieldType) or type(self.required) is not bool:
            raise ValueError("Field needs a FieldType and boolean required flag")
        nonempty(self.semantics)


@dataclass(frozen=True)
class Schema:
    """Closed flat field declarations. Order and explanatory prose do not affect shape."""
    fields: tuple[Field, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.fields, tuple) or any(not isinstance(f, Field) for f in self.fields):
            raise ValueError("Schema fields must be a tuple of Fields")
        if len({f.name for f in self.fields}) != len(self.fields):
            raise ValueError("Duplicate or conflicting field name")

    def shape(self) -> tuple:
        return tuple(sorted((f.name, f.type.value, f.required) for f in self.fields))


@dataclass(frozen=True)
class Metadata:
    description: str
    tags: frozenset[str]
    side_effects: frozenset[str]
    permissions: frozenset[str]
    source: str

    def __post_init__(self) -> None:
        nonempty(self.description)
        nonempty(self.source)
        for values in (self.tags, self.side_effects, self.permissions):
            strings(values)


@dataclass(frozen=True)
class CapabilityContract:
    capability_id: str
    version: Version
    inputs: Schema
    outputs: Schema

    def __post_init__(self) -> None:
        identifier(self.capability_id)
        if not isinstance(self.version, Version) or not all(isinstance(s, Schema) for s in (self.inputs, self.outputs)):
            raise ValueError("Contract requires a Version and input/output Schemas")


@dataclass(frozen=True, order=True)
class OfferKey:
    provider_id: str
    implementation_id: str
    capability_id: str
    contract_version: Version

    def __post_init__(self) -> None:
        for value in (self.provider_id, self.implementation_id, self.capability_id):
            identifier(value)
        if not isinstance(self.contract_version, Version):
            raise ValueError("Offer key requires a Version")


@dataclass(frozen=True)
class CapabilityManifest:
    contract: CapabilityContract
    provider_id: str
    implementation_id: str
    implementation_version: Version
    metadata: Metadata

    def __post_init__(self) -> None:
        identifier(self.provider_id)
        identifier(self.implementation_id)
        if not isinstance(self.contract, CapabilityContract) or not isinstance(self.implementation_version, Version) or not isinstance(self.metadata, Metadata):
            raise ValueError("Manifest requires typed contract, implementation version, and metadata")

    @property
    def key(self) -> OfferKey:
        return OfferKey(self.provider_id, self.implementation_id, self.contract.capability_id, self.contract.version)


@dataclass(frozen=True)
class Requirement:
    capability_id: str
    versions: VersionRange
    inputs: Schema | None = None
    outputs: Schema | None = None
    tags: frozenset[str] = frozenset()
    provider_id: str | None = None

    def __post_init__(self) -> None:
        identifier(self.capability_id)
        if not isinstance(self.versions, VersionRange) or any(s is not None and not isinstance(s, Schema) for s in (self.inputs, self.outputs)):
            raise ValueError("Requirement needs a VersionRange and optional Schemas")
        strings(self.tags)
        if self.provider_id is not None:
            identifier(self.provider_id)
