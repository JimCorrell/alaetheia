# Lab 001 results and discussion

Implemented within the authorized Lab 001 boundary. The bootstrap prohibition was explicitly lifted by the implementation request. No architecture conflict or scope deviation was required. Example providers are declarations only, as required by the vision; there are no callable implementations.

## Decisions made in this experiment

- Frozen dataclasses, tuples, and frozensets make declarations and returned snapshots immutable. Constructors validate runtime types as well as values. No third-party runtime or test dependency.
- IDs use lowercase ASCII segments separated by `.`, `_`, or `-`: `[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*`. This applies to capability, provider, implementation, and field names.
- Versions support release `MAJOR.MINOR.PATCH` only, with numeric ordering and no leading zeros. Prerelease/build suffixes are rejected, not discarded. Implementation versions are descriptive and never used to match a contract requirement.
- Ranges accept a bare exact version, `==version`, or whitespace-separated lower/upper comparisons (`>`, `>=`, `<`, `<=`). A single bound is allowed. Repeated bounds, impossible intervals, wildcards, caret/tilde, unions, abbreviated versions, and compound exact comparisons are rejected. There is no implicit same-major rule: the caller must supply the intended upper bound. Major zero uses the same explicit comparisons.
- Schema vocabulary is flat string/integer/number/boolean fields, each with a required flag and semantics. No nested objects, arrays, coercion, defaults, or payload validation. Empty schemas mean zero fields. Duplicate names are rejected even when identical.
- Compatibility uses exact structural equivalence for each supplied input/output schema: names, types, and required flags. Field order and explanatory prose do not affect matching. Omitting a schema means no shape constraint, not an empty schema. Descriptions cannot establish semantic equivalence; the contract ID/version remains the author's semantic promise.
- The unique offer key is `(provider_id, implementation_id, capability_id, contract_version)`. Implementation version is intentionally excluded: registering a replacement release requires explicit unregister/register. This prevents accidental overwrite; it does not implement atomic replacement or concurrent access.
- Offers with the same semantic ID/version must agree on structural schemas. Different descriptions are permitted. This additional consistency check prevents contradictory shapes from masquerading as the same contract.
- `get` and `unregister` raise `KeyError` for missing keys. Register rejects duplicate keys and conflicting contracts with `ValueError`. Failed registration leaves the registry unchanged. Unregister removes exactly one offer and returns it.
- `list()` returns a tuple sorted ascending by capability ID, numeric contract version, provider ID, then implementation ID. `find()` uses that order and the public compatibility function, returning every match. Requirements support an exact provider filter and all-of tags. Compatibility returns a boolean plus all mismatch reasons; no ranking or hidden selection.
- Metadata explicitly declares description, tags, side effects, permissions, and source. Empty effect/permission sets are allowed. These are unverified declarations, not grants of authority or observations of execution.

## What the catalog demonstrates

`terrain.slope.analyze@2.1.0` has three offers: two local implementations and a remote provider. Version 2.0.0 has only `mean_slope`; 2.1.0 adds `max_slope`; 3.0.0 changes the output to `slope_percent`. The local provider also advertises `parcel.describe`.

`>=2.0.0 <3.0.0` returns four offers and excludes 3.0.0. Requesting the exact two-field output returns the three 2.1.0 offers. Requesting the one-field output returns only 2.0.0: this deliberately illustrates the conservatism of exact matching. Prose rewording and field reordering are compatible; changed types, names, or required flags are incompatible when that schema is requested. A future safe-subset rule might accept additive output fields, but this lab does not claim that behavior.

## Evidence and questions for the architecture discussion

1. **Discovery does not resolve selection.** Three offers survive the same exact 2.1.0 request. Which evidence should later distinguish them: locality, cost, permissions, provenance, or measured quality? This experiment provides no reason to create another agent.
2. **Version compatibility is a declaration, not proof.** Even an in-range offer can fail the requested schema. Should a future contract catalog enforce evolution rules across versions, and who owns the semantic identity?
3. **Exact schemas reject potentially safe additions.** Should input matching mean “the caller can satisfy every required provider field,” and output matching mean “the provider guarantees every requested field”? Optionality and closed versus open records need explicit decisions before relaxing these rules.
4. **Shared identity needs governance.** The registry catches conflicting shapes for the same ID/version, but cannot detect changed units hidden in prose. Should units, coordinate systems, or other domain semantics become machine-readable constraints?
5. **Implementation release identity remains a choice.** The current key allows distinct implementations but not simultaneous releases of the same implementation under one contract. Would future canary/rollback experiments need an additional deployment identity?
6. **Declared permissions are not enforcement.** The remote example declares network access and `gis.read`; nothing verifies either. Selection and execution authorization remain separate future questions.
7. **Minimal typing exposes a limit.** Flat scalar fields suffice for this catalog; real terrain geometry likely needs arrays or structured references. Extend the vocabulary only against a concrete contract example.

## Verification

Python 3.12.10: complete standard-library unittest suite (18 test methods with parameterized subcases) passes. Tests cover invalid declarations, range syntax/bounds, immutable data, overlap, exact keys, deterministic sorting, atomic rejection, schema/filter mismatches, compatibility/discovery agreement, and CLI subprocess output/error behavior. No external services are required.

Editable package installation also passed (`python -m pip install -e .`), followed by the complete suite against the installed package. The installed `alaetheia inspect terrain.slope.analyze --version 2.1.0` entry point displayed all three offers. Source compilation and `git diff --check` passed.
