# Lab 004: Read-only preflight and missing-output observation

- **Status:** Implemented; see [results](lab-004-results.md)
- **Decision:** [ADR-005](../architecture/decisions/ADR-005-advisory-workflow-preflight.md)
- **Question:** Which workflow failures can declared contracts predict, and which still require runtime evidence?

## Scope

Add deterministic advisory reports with definite errors, conditional risks, and no-detected-issues status. Inspect offers, bindings, requirements, input wiring, literal values, and declared handoff types without invoking providers. Preserve workflow runner behavior and all runtime checks.

Compare reports with explicitly run workflows, recording missing-output observations with producer, field, consumer/input when applicable, whether an optionality risk was predicted, and skipped steps. Distinguish provider violations of required outputs from optional reference absence. A provider returning malformed output or wrong types is not the same event as an omitted field. Do not count skipped references as observed failures.

## Acceptance evidence

- Preflight causes no calls or registry mutation and produces deterministic reports.
- Missing offers/bindings, stale bindings, incompatible requirements, missing/extra input wiring, invalid literals, and undeclared references are reported.
- All scalar handoff type pairs are classified consistently with runtime validation. Integer values satisfy NUMBER; floats do not satisfy INTEGER.
- Optional references warn for required and optional destinations. Present values can succeed; absent references fail at resolution.
- A clear report can still be followed by a provider exception or required-output omission.
- Runtime records retain structured omission evidence and run comparisons attribute failures without parsing messages or double counting skipped steps.
- Existing Labs 001–003 tests remain green. No enforcement, execution policy, or retry behavior changes.

## Exclusions

No blocking preflight gate, automatic repair/defaults, persistence, scheduled execution, remote providers, side effects, planner, LLM, or subsequent lab implementation.
