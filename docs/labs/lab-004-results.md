# Lab 004 results: preflight versus runtime

## Findings

The hybrid experiment separates predictable declaration problems from actual provider behavior. A clean preflight does not guarantee execution success, and a risk does not guarantee failure.

| Scenario | Preflight | Runtime | Missing-output observation |
| --- | --- | --- | --- |
| Optional source field present | Risk | Success | None |
| Optional source field absent | Risk | Consumer dependency resolution fails | One predicted optional-reference event |
| Required source field absent | No detected issues | Producer invalid output; consumer skipped | One required-output violation |
| Wrong type/null value present | May have no detected issues | Producer invalid output | Not classified as missing |
| Referenced optional output feeding optional input is absent | Risk | Dependency resolution still fails | One predicted optional-reference event |
| NUMBER source returns int to INTEGER input | Risk | Can succeed | None |
| NUMBER source returns float to INTEGER input | Risk | Consumer invalid input | None |

These are controlled local test observations, not production incident rates. They do not yet justify automatic defaults, omission, or enforcement.

## Implementation

`preflight.py` exposes `WorkflowPreflight`, `PreflightReport`, typed findings/severity, `compare_run`, and missing-output/run comparison records. Findings include stable codes and step/field locations. Ordering is deterministic: declared step order, selection diagnostics, required-input names, then input bindings sorted by destination name.

`LocalExecutor.inspect_selection` extracts the existing selection checks into a public read-only method used by both preflight and invoke. Existing selection error messages and invocation behavior remain unchanged. `ExecutionRecord.missing_output_fields` adds sorted, deduplicated required-field omission evidence for dictionary outputs rejected as invalid. Invalid raw output is still not retained.

The workflow runner is unchanged. Inspection, running, and comparison are separate caller actions. Preflight analyzes later steps even if earlier errors would prevent reaching them. Comparison only counts missing-output failures observed in completed records. A failed producer creates one event per omitted required field; skipped consumers are not counted again. A missing reference creates an event per consumer input binding that could not resolve it.

Comparison requires the report and record to describe equal workflow definitions. It does not establish a registry revision match or tamper-proof identity: registry contents may change between inspect and run, and payload snapshots remain caller-editable as in earlier labs. No findings are treated as execution permission or a provider reservation.

## Monitoring within the lab

Run `python -m alaetheia.preflight_example` to inspect three scenarios, explicitly execute them, and print the findings and observations together. It exits 0 when the demonstration completes, even though two scenarios intentionally produce failed workflow records. The API supports the same comparison after any explicit local workflow run; no background task or persistent event history is created.

Review future missing-output failures by category:

- `required_output_missing`: the provider broke a declared promise; investigate its implementation or contract.
- `referenced_output_absent`: the producer was allowed to omit the field, but the workflow explicitly required a reference; investigate workflow optionality policy.

`predicted_optional_risk` records whether the exact consumer/input/source warning appeared in preflight. It is not a general prediction-accuracy score; unrelated failures and skipped steps are not evidence that an optional risk did or did not materialize.

## Validation and boundaries

Python 3.12.10: all 63 test methods pass, including all 48 earlier-lab tests and 15 Lab 004 tests with parameterized cases. Tests cover read-only behavior, all scalar type pairs, selection freshness, wiring, optional destination behavior, present/absent fields, no double counting, wrong/malformed output classification, registry changes after a clean report, and the demonstration module. Source compilation and whitespace checks pass.

No change to runtime enforcement or scope deviation was needed. NUMBER-to-INTEGER is classified as conditional rather than a definite error because its accepted value sets overlap. Structured omission evidence is additive record metadata; success/failure decisions are unchanged.

## Questions for the next architecture discussion

1. Should explicit references to optional outputs continue to fail when absent, or should a future binding explicitly allow omission/defaults? The destination being optional alone currently changes nothing.
2. Should definite preflight errors eventually block a run, and how would the system handle registry changes after inspection?
3. Would contract preflight need versioned selection snapshots before results could be reused?
4. What volume and variety of real examples would justify defaults or repair? Three controlled scenarios are insufficient to select a general policy.
