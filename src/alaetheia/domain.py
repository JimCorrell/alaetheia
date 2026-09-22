"""Expected domain rejections are values, not exceptions or successful payloads."""
from dataclasses import dataclass
from .contracts import identifier, nonempty


@dataclass(frozen=True)
class DomainIssue:
    """Code is machine-readable; field names an input or None for record-level rules."""
    code: str
    message: str
    field: str | None = None

    def __post_init__(self) -> None:
        identifier(self.code)
        nonempty(self.message)
        if self.field is not None:
            identifier(self.field)


@dataclass(frozen=True)
class DomainRejection:
    """A nonempty ordered collection of issues; never contains partial output."""
    issues: tuple[DomainIssue, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.issues, tuple) or not self.issues or any(
            not isinstance(issue, DomainIssue) for issue in self.issues
        ):
            raise ValueError('Domain rejection requires a nonempty tuple of DomainIssues')
