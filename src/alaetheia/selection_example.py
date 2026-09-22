"""Print an offline proposal evaluation; --json includes full catalog evidence."""
import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path

from . import selection, selection_baseline, selection_catalog, selection_evaluation, selection_fixtures
from .selection_evaluation import evaluate, metrics


def report() -> dict[str, object]:
    catalog = selection_catalog.catalog()
    results = evaluate(selection_fixtures.cases(), catalog, selection_baseline.propose)
    return {
        'scope': 'Offline proposals only; no execution or domain validation. Synthetic single-author labels.',
        'revisions': {'catalog': selection_catalog.CATALOG_REVISION,
                      'baseline': selection_baseline.BASELINE_REVISION,
                      'fixtures': selection_fixtures.FIXTURE_REVISION,
                      'evaluation': selection_evaluation.EVALUATION_REVISION},
        'source_sha256': {m.__name__: hashlib.sha256(Path(m.__file__).read_bytes()).hexdigest()
                          for m in (selection, selection_baseline, selection_catalog,
                                    selection_evaluation, selection_fixtures)},
        'catalog': [asdict(e) for e in catalog],
        'metrics': {split: asdict(metrics(tuple(r for r in results if r.case.split == split)))
                    for split in ('development', 'held-out')},
        'cases': [asdict(r) for r in results],
    }


def json_report(evidence: dict[str, object]) -> str:
    # Only trusted dataclass evidence and validated builtin proposal data reach
    # this example encoder. It is not an external serialization protocol.
    def encode(value):
        if isinstance(value, frozenset):
            return sorted(value)
        raise TypeError(f'Unsupported report value: {type(value).__name__}')
    return json.dumps(evidence, default=encode, ensure_ascii=False, indent=2, sort_keys=True)


def human_report(evidence: dict[str, object]) -> str:
    lines = [evidence['scope']]
    for split, values in evidence['metrics'].items():
        lines.append(f'\n{split}:')
        for name, count in values.items():
            lines.append(f"  {name}: {count['numerator']}/{count['denominator']}")
    lines.append('\nCases (every selection and abstention):')
    for row in evidence['cases']:
        case = row['case']
        proposal = row['raw_proposal'] or {}
        observed = proposal.get('workflow_id', proposal.get('reason', 'invalid'))
        corrections = ', '.join(row['corrections']) or 'none'
        lines.append(f"  {case['case_id']} [{case['split']}]: expected={case['expected']}; "
                     f"observed={observed}; corrections={corrections}")
    lines.append('\nCounts of corrections use fixture labels; no human time or effort was measured.')
    return '\n'.join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--json', action='store_true', help='Include full definitions, manifests, cases and source hashes')
    args = parser.parse_args()
    evidence = report()
    print(json_report(evidence) if args.json else human_report(evidence))


if __name__ == '__main__':
    main()
