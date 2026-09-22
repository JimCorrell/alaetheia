"""Inspect the explicit sample catalog in a fresh process-local registry."""
import argparse
from dataclasses import asdict
import json
from .contracts import Requirement, VersionRange, Version
from .examples import sample_registry


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    listing = sub.add_parser('list')
    listing.add_argument('--json', action='store_true')
    inspect = sub.add_parser('inspect')
    inspect.add_argument('capability_id')
    versions = inspect.add_mutually_exclusive_group()
    versions.add_argument('--version', help='Exact MAJOR.MINOR.PATCH')
    versions.add_argument('--range', dest='version_range', help='e.g. ">=2.0.0 <3.0.0"')
    inspect.add_argument('--json', action='store_true')
    args = parser.parse_args(argv)
    registry = sample_registry()
    try:
        if args.command == 'list':
            offers = registry.list()
        else:
            if args.version is not None:
                Version.parse(args.version)
                expression = args.version
            elif args.version_range is not None:
                expression = args.version_range
            else:
                expression = '>=0.0.0'
            requirement = Requirement(args.capability_id, VersionRange.parse(expression))
            offers = registry.find(requirement)
            if not offers:
                raise ValueError('No offers match the capability ID and version requirement')
    except ValueError as error:
        parser.error(str(error))
    records = []
    for offer in offers:
        record = asdict(offer)
        record['contract']['version'] = str(offer.contract.version)
        record['implementation_version'] = str(offer.implementation_version)
        for key in ('tags', 'permissions', 'side_effects'):
            record['metadata'][key] = sorted(record['metadata'][key])
        records.append(record)
    if args.json:
        print(json.dumps(records, indent=2))
    else:
        for record in records:
            contract = record['contract']
            print(f"{contract['capability_id']}@{contract['version']} | {record['provider_id']}/{record['implementation_id']} (implementation {record['implementation_version']})")
            for label in ('inputs', 'outputs'):
                print(f"  {label}: " + ', '.join(f"{f['name']}:{f['type'].value} ({'required' if f['required'] else 'optional'}) — {f['semantics']}" for f in contract[label]['fields']))
            print('  metadata: ' + json.dumps(record['metadata'], sort_keys=True))
    return 0
