# ADR-008: Data-only output snapshots and review hardening

- **Status:** Accepted for architecture consolidation
- **Date:** 2026-09-22
- **Scope:** Fix F1–F3 from the architecture checkpoint; clarify output values and automate existing checks

## Context

The review reproduced a provider exception whose text formatter raised, a custom deepcopy hook that corrupted a successful output snapshot after validation, and empty CLI version arguments that silently widened discovery. The user authorized fixing all three, clarifying the output contract, updating the current architecture reference, and automating tests.

## Decision

Format ordinary provider exceptions defensively, retaining the original exception class with a stable fallback if message formatting fails. Do not catch process-control exceptions.

Replace arbitrary deepcopy with explicit builtin-data snapshotting. Successful outputs are plain string-keyed dictionaries of None, exact builtin scalar values (finite floats only), lists, and recursively string-keyed dictionaries. Reject custom objects/subclasses without invoking hooks; reject cycles and depth beyond 64 container levels. Shared acyclic containers are copied independently. Validate the resulting detached snapshot against provider and consumer schemas before marking success. This is a data contract, not a security sandbox or resource-isolation boundary.

The restriction deliberately narrows the previously unspecified extra-value vocabulary. Retain extra fields that satisfy it. Document the compatibility change in library 0.2.0; successful declared scalar schema rules and capability identities remain unchanged. Existing custom-object providers must adapt their extra values explicitly, with no automatic encoding or coercion.

Use an argparse mutually exclusive group for version/range and distinguish a missing flag (None) from supplied empty values. Empty version/range arguments are invalid input, never requests for all versions.

Provide `docs/architecture/current.md` as the current contract and boundary reference; preserve lab/ADR history with supersession links. Add GitHub Actions checks for package installation, the full unittest suite, compilation, and installed CLI on Python 3.12–3.14. CI has read-only repository permissions and no deployment action. No branch protection or static checker is introduced.

## Consequences

Successful records contain the same supported, validated data that downstream steps consume. Snapshot hooks cannot mutate recorded values because they are never called. Provider output can still be semantically wrong; shape validation is not verification of truth.

The 64-level limit is a deterministic representation bound, not a general memory/time quota. Huge acyclic payloads and nonreturning trusted providers are outside this hardening's resource guarantees.

Previously reproduced defects become ordinary regression tests; the reproduction script asserting broken behavior is retired. No new lab, model integration, or broader architecture change is authorized.
