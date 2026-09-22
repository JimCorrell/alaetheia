"""Revision 1: explicit phrase rules, not a general natural-language parser.

Unsupported operations take precedence, then conflicting intents, then missing
whitespace policy, then unknown intent, then input validation. Rules never read
fixture IDs, labels, descriptions, or supplied text as instructions. No tuning
against held-out outcomes is performed in this revision.
"""
import re

from .execution import validate_payload
from .output_values import snapshot_output
from .selection import AbstentionReason, CatalogEntry, checked_catalog

BASELINE_REVISION = '1'
RAW = ('raw', 'including surrounding whitespace', 'keeping whitespace')
TRIMMED = ('after trimming', 'without surrounding whitespace', 'strip surrounding whitespace')
UNSUPPORTED = ('look up', 'lookup', 'verify', 'suitability', 'words', 'bytes', 'graphemes')


def _contains(text: str, phrases: tuple[str, ...]) -> bool:
    return any(re.search(r'\b' + re.escape(phrase) + r'\b', text) for phrase in phrases)


def propose(request: str, supplied: object, catalog: tuple[CatalogEntry, ...]) -> dict[str, object]:
    checked_catalog(catalog)

    def abstain(reason):
        return {'kind': 'abstain', 'reason': reason.value}

    if type(request) is not str:
        raise ValueError('Request must be a plain string')
    text = ' '.join(request.casefold().split())
    if _contains(text, UNSUPPORTED):
        return abstain(AbstentionReason.UNSUPPORTED)
    counting = _contains(text, ('count', 'how many')) and _contains(text, ('characters', 'code points'))
    raw = counting and _contains(text, RAW)
    trimmed = counting and _contains(text, TRIMMED)
    parcel = _contains(text, ('parcel',)) and _contains(text, ('summarize', 'describe'))
    if sum((raw, trimmed, parcel)) > 1 or (counting and parcel):
        return abstain(AbstentionReason.AMBIGUOUS)
    if counting and not (raw or trimmed):
        return abstain(AbstentionReason.AMBIGUOUS)
    selected = ('text-count-raw' if raw else 'text-count-trimmed' if trimmed
                else 'parcel-record-summary' if parcel else None)
    if selected is None:
        return abstain(AbstentionReason.UNSUPPORTED)
    entry = next((e for e in catalog if e.workflow_id == selected), None)
    if entry is None:
        return abstain(AbstentionReason.UNSUPPORTED)
    if validate_payload(entry.inputs, supplied, allow_extra=False):
        return abstain(AbstentionReason.INSUFFICIENT)
    return {'kind': 'select', 'workflow_id': selected, 'inputs': snapshot_output(supplied)}
