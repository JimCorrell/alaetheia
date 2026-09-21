# Lab 003 results: deterministic workflow composition

## Outcome

The three-step example strips surrounding whitespace, counts Unicode code points, and formats the count. Its explicit wiring maps `strip.cleaned` to the count function's `text` input and `middle.count` to the formatter's `count` input. The result is `Characters: 5` for `  Theia  `.

The incompatible variant sends the stripped string to an integer input in the second step. Step one succeeds, step two returns Lab 002's `invalid_input` without invoking its function, and step three is skipped. Individually valid capabilities therefore do not imply a valid composition.

## Implementation choices

- `workflow.py` defines immutable workflow declarations, input bindings, literal/output references, step records, workflow records, and a sequential runner. `workflow_example.py` contains only pure local text functions and a deterministic example caller.
- A workflow has a nonempty tuple of uniquely named steps. Each step names an exact offer and requirement. Repeated use of the same offer is allowed with different step IDs.
- Each destination input has exactly one source: a finite scalar literal or one named field from an earlier step. No implicit whole-output forwarding, expressions, defaults, conversion, nested paths, or workflow-input schema is introduced. The caller constructs literals for each run.
- Definition construction rejects duplicate step IDs/input targets, malformed types/identifiers, and missing/self/forward step references. Earlier-only references also exclude cycles. This is structural validation, not a static contract checker.
- The runner evaluates steps in declared order and reuses LocalExecutor for selection, input validation, invocation, and output validation. A source must be a declared provider output present in a successful upstream record. Optional declared outputs may be used when present; missing values fail dependency resolution. Undeclared extras remain visible in the record but cannot be routed as validated data.
- Runtime payload rules remain those of Lab 002. Field names may be mapped explicitly; values are not coerced. In particular a runtime integer value may satisfy a NUMBER input, while the requirements passed to each individual offer retain the existing exact input-schema rules. No new schema-to-schema edge compatibility rule is claimed.
- Any unsuccessful invocation or dependency resolution ends execution. Every later step is marked skipped, even if independent. There is no retry, fallback, rollback, or resume.
- Each WorkflowRecord retains the immutable workflow definition, ordered StepRecords, overall outcome, and first failed step ID. Invoked or executor-rejected steps retain the complete ExecutionRecord and its versions. Dependency-resolution failures have diagnostics but no ExecutionRecord; skipped steps likewise have no fabricated invocation record.
- The record contains all step outputs rather than introducing a separate workflow output schema. Payload snapshots have the same caller-editable dictionary semantics as Lab 002. Each run uses fresh local state; no identifiers, timestamps, storage, or persistent ledger are added.
- Process-control exceptions still propagate; this is not a cancellation-aware runner. It operates on trusted synchronous local functions and does not add purity enforcement or concurrency safety.

## Validation

Python 3.12.10: the complete suite passes with 48 test methods (21 Lab 001, 15 Lab 002, 12 Lab 003), including parameterized cases. Tests cover ordered execution, nonadjacent dependencies, field renaming, multiple inputs, malformed definitions, incompatible handoffs, optional output absence, unvalidated extras, all existing failure categories, stale bindings, skipping independent downstream steps, repeated-run isolation, and both example exit codes. Source compilation and whitespace checks pass.

Run `python -m alaetheia.workflow_example` for success (exit 0), or add `--incompatible` for the deliberate failed handoff (exit 1). Both print the complete workflow record as JSON for this example catalog.

## Observations and questions

1. **Definition validity and composition validity differ.** Structural checks can prove that a reference points backward without proving its value will satisfy a destination. Should a later lab preflight selected offer contracts before running any step? Optional values still require runtime handling.
2. **Optional outputs create control-flow decisions.** This lab stops when an explicitly referenced value is absent, even if its target could be optional. Should future wiring allow omission or a declared default? Such a rule should not be an accidental fallback.
3. **Extra-output tolerance is not a data contract.** Accepting extras during invocation does not make them safe dependencies. Requiring declared outputs keeps the distinction visible.
4. **Fail-fast is simple but coarse.** Independent later steps are skipped too. There is no evidence yet requiring partial-progress scheduling, branches, or compensation.
5. **Workflow provenance is useful without a ledger.** The definition explains the wiring; execution records explain actual inputs and outcomes. Correlating or resuming multiple runs would require new identity, retention, and lifecycle decisions.

No departure from the agreed Lab 003 scope was needed. ADR-004 records the implementation choices, and no Lab 004 work is included.
