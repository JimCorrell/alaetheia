# Lab 005 results: reusable workflow inputs

Historical report: Lab 006 subsequently replaces the parcel validator's exception-based domain rejection with structured results under contract 2.0.0. See [Lab 006 results](lab-006-results.md).

## Outcome

One immutable `parcel-record-summary` workflow now accepts multiple supplied parcel records. It first validates domain values and trims identifier/municipality whitespace, then produces a descriptive summary from the validated outputs. No provider is selected dynamically and no external source is consulted.

The five-case demo uses fictional municipalities and records:

| Case | Result | Evidence |
| --- | --- | --- |
| Rural parcel, 42.5 acres, reported no road access | Success | Supplied facts summarized |
| Small lot, 0.25 acres, whitespace in identifiers | Success | Explicit normalization in validation step |
| Whole-acre record, 12 acres | Success | Integer payload valid for NUMBER field |
| Acreage supplied as string `"12"` | Workflow `invalid_input` | All steps skipped, no invocation |
| Acreage supplied as -1 | Workflow failed at validate | Scalar type valid; domain rule rejected it |

These are controlled examples, not verified parcel facts or real-world suitability conclusions.

## Changes and behavior

- `Workflow.inputs` is a typed Schema, defaulting to empty for earlier workflows. `WorkflowInputRef(field)` provides explicit data wiring alongside Literal and OutputRef. Construction rejects undeclared references.
- `WorkflowRunner.run(workflow, inputs)` checks the complete envelope first with the existing validator, including required fields that are not routed to a step. Extra fields are rejected. Omitted arguments mean `{}`; explicit `None` is invalid.
- WorkflowRecord adds an input snapshot and workflow-level errors. Input rejection returns the new `WorkflowOutcome.INVALID_INPUT`, no failed-step ID, and all steps skipped. Invalid raw input is not retained.
- Validated workflow inputs are immutable scalar values copied into a detached record dictionary. Step payloads and execution snapshots remain separate. Caller edits to input or record dictionaries do not alter earlier step records or later runs.
- A missing optional workflow input is acceptable to envelope validation. An explicit reference to it still fails resolution when reached. The step has no execution record, later steps are skipped, and no default is invented. Optional unreferenced fields may remain absent.
- Preflight inspects workflow-input declarations using existing handoff rules and emits optional-input risks. It does not inspect a particular run's values. The same report can be compared with multiple runs; this does not reserve bindings or pin a registry revision.
- Input-to-step name mapping is explicit. Literal overrides and earlier-output bindings continue to work. There is no implicit pass-through of the entire workflow payload.
- `parcel_example.py` contains pure local validation and summary functions, a reusable example factory, and a five-case demonstration. Blank IDs/municipalities and nonpositive acreage are domain failures reported through the existing provider-failure mechanism. No generic semantic constraint engine was added.

## Missing-output observation

A fault-injection test deliberately omits the required `acreage` output from the validation provider. Preflight has no detected issues because the declaration promises acreage. Runtime returns producer `invalid_output`, skips summary, and records exactly one `required_output_missing` event for acreage.

Rejected workflow inputs and absent optional workflow-input references generate no missing-output events. Their diagnostics remain in WorkflowRecord or the failed StepRecord. Earlier optional-output tests continue to pass unchanged. Monitoring remains explicit and local, with no automatic defaults, scheduled checks, or stored event history.

## Validation

Python 3.12.10: all 76 test methods pass (63 prior tests and 13 Lab 005 tests, including parameterized cases). Coverage includes repeated reuse, snapshot isolation, complete-envelope validation before calls, domain failures, undeclared references, optional inputs, mixed bindings, preflight compatibility, missing-output attribution, backward compatibility, and the demo subprocess. Source compilation and whitespace checks pass.

No architectural conflict or scope deviation was needed. The new workflow-level input rejection is separate from Lab 002's step-level invalid input so records identify where validation occurred.

## Questions surfaced

1. **Types are not domain validity.** A negative acreage is numerically valid but unsuitable for this record contract. Should later work standardize domain-validation outcomes, or are explicit provider failures sufficient for now?
2. **Optional references still imply a decision.** A caller can omit an optional input, yet an unconditional reference to it fails. We have preserved that rule; future omission/default policies should be explicitly declared and tested.
3. **A reusable definition needs eventual identity discipline.** The same workflow ID can describe changed schemas or wiring. Do we need versioned workflow contracts before reuse crosses process or repository boundaries? This lab does not introduce such boundaries.
4. **Supplied data is not evidence of truth.** Summarizing reported road access does not verify legal access. A later data-acquisition experiment would need explicit provenance and verification semantics.

Lab 006 remains unimplemented.
