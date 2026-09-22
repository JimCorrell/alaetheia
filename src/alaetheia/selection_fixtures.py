"""Fixture revision 1, authored before baseline evaluation; no selector imports.

Two development and two held-out cases per category. Held-out means excluded
from rule development, not independently blinded: one author prepared this lab.
Expected answers and rationales are reviewable experimental labels.
"""
from dataclasses import dataclass

FIXTURE_REVISION = '1'


@dataclass(frozen=True)
class Case:
    case_id: str
    split: str
    category: str
    request: str
    inputs: dict[str, object]
    expected: str  # Workflow ID or an abstention reason.
    rationale: str


def cases() -> tuple[Case, ...]:
    # Fresh dictionaries prevent one evaluation from changing later fixtures.
    parcel = {'parcel_id': ' P-1 ', 'municipality': 'Example Town',
              'acreage': 12, 'road_access': False}
    rows = (
        ('raw', 'Count characters including surrounding whitespace.', {'text': '  Theia  '}, 'text-count-raw', 'Explicit raw policy.'),
        ('raw', 'Count raw characters.', {'text': ''}, 'text-count-raw', 'Empty text is a supplied string.'),
        ('raw', 'How many Unicode code points, keeping whitespace?', {'text': ' é👩‍💻 '}, 'text-count-raw', 'Code points, not visual characters.'),
        ('raw', 'Measure the character length without removing the spaces at either end.', {'text': ' x '}, 'text-count-raw', 'Paraphrased raw policy.'),
        ('trimmed', 'Count characters after trimming.', {'text': '  Theia  '}, 'text-count-trimmed', 'Explicit trim policy.'),
        ('trimmed', 'Count characters without surrounding whitespace.', {'text': '\t\n'}, 'text-count-trimmed', 'Whitespace-only string is valid.'),
        ('trimmed', 'Count Unicode code points after trimming.', {'text': ' é '}, 'text-count-trimmed', 'Combining mark is a separate code point.'),
        ('trimmed', 'Remove the whitespace at both ends and tell me the character length.', {'text': ' x '}, 'text-count-trimmed', 'Paraphrased trim policy.'),
        ('parcel', 'Summarize the supplied parcel record.', dict(parcel), 'parcel-record-summary', 'Supplied facts only, false preserved.'),
        ('parcel', 'Summarize this parcel record.', {**parcel, 'acreage': -1}, 'parcel-record-summary', 'Domain-invalid data does not trigger a provider call.'),
        ('parcel', 'Describe these supplied parcel facts.', {**parcel, 'acreage': 0}, 'parcel-record-summary', 'Zero remains supplied, with domain validity deferred.'),
        ('parcel', 'Give me a descriptive digest of this supplied land record.', {**parcel, 'acreage': 0.25}, 'parcel-record-summary', 'Paraphrase of supplied-record summary.'),
        ('ambiguous', 'Count the characters.', {'text': ' x '}, 'ambiguous_request', 'No whitespace policy.'),
        ('ambiguous', 'Count raw characters and count characters after trimming.', {'text': ' x '}, 'ambiguous_request', 'Two requested operations.'),
        ('ambiguous', 'Count raw characters and summarize this parcel record.', {'text': ' x ', **parcel}, 'ambiguous_request', 'Two workflow intents take precedence over envelope issues.'),
        ('ambiguous', 'How long is this text?', {'text': ' x '}, 'ambiguous_request', 'Counting semantics and whitespace policy unresolved.'),
        ('unsupported', 'Look up this parcel and summarize it.', dict(parcel), 'unsupported_request', 'External lookup is unavailable.'),
        ('unsupported', 'Count words including surrounding whitespace.', {'text': 'one two'}, 'unsupported_request', 'Word counting is not character counting.'),
        ('unsupported', 'Count UTF-8 bytes including surrounding whitespace.', {'text': 'é'}, 'unsupported_request', 'Byte count differs from code points.'),
        ('unsupported', 'Count graphemes after trimming.', {'text': 'é'}, 'unsupported_request', 'Grapheme count differs from code points.'),
        ('insufficient', 'Count raw characters.', {}, 'insufficient_inputs', 'Missing required text.'),
        ('insufficient', 'Count characters after trimming.', {'text': False}, 'insufficient_inputs', 'False must not become text.'),
        ('insufficient', 'Summarize this parcel record.', {k: v for k, v in parcel.items() if k != 'road_access'}, 'insufficient_inputs', 'Missing access flag must not default to false.'),
        ('insufficient', 'Summarize this parcel record.', {**parcel, 'acreage': '12'}, 'insufficient_inputs', 'No numeric coercion.'),
    )
    return tuple(Case(f'{category}-{index % 4 + 1}', 'development' if index % 4 < 2 else 'held-out',
                      category, request, inputs, expected, rationale)
                 for index, (category, request, inputs, expected, rationale) in enumerate(rows))
