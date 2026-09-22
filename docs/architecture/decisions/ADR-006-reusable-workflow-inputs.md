# ADR-006: Typed inputs for reusable workflow definitions

- **Status:** Accepted for Lab 005
- **Date:** 2026-09-22

## Context

Lab 003 embedded caller values as literals in each definition. The next agreed experiment runs one explicit workflow against different supplied records, retaining advisory preflight and missing-output observations. This tests reuse without introducing a planner or external services.

## Decision

Add a workflow-level input Schema and WorkflowInputRef alongside literals and earlier output references. The schema defaults to empty for existing workflows. Reject undeclared workflow-input references during definition construction.

Accept supplied inputs in `WorkflowRunner.run(workflow, inputs)`. Validate the complete input dictionary against the workflow schema before resolving offers or invoking providers. Reject extra fields, wrong types, and missing required values using the existing scalar validator. No coercion or defaults are added. Omitted inputs mean an empty dictionary; explicit None is invalid.

On invalid supplied inputs, return workflow outcome `invalid_input`, workflow-level diagnostics, no failed step, and every step skipped with no execution record. Otherwise retain a detached scalar input snapshot in WorkflowRecord. Steps may explicitly map or reuse these values without changing the definition.

An optional workflow input may be absent in a valid envelope. If explicitly referenced, its absence fails that step's resolution, exactly as an absent optional output does. Optional does not mean null, and destination optionality does not introduce implicit omission. Unreferenced optional fields may remain absent.

Extend preflight's existing handoff rules to workflow inputs. Referenced optional inputs produce `optional_workflow_input_absent` risks. Preflight examines the reusable definition, not a particular run's supplied values; input validation remains a separate mandatory runtime check. Preflight stays advisory.

Use a local, side-effect-free supplied parcel-record example: validate domain values and summarize the supplied facts. String identity fields must be nonblank and acreage must be positive. These semantic checks belong to the example function rather than a new generic schema constraint engine. Domain failures use the existing provider-failure outcome. No property lookup, access verification, valuation, suitability assessment, or external facts are implied.

## Consequences

One definition and preflight report can serve multiple explicit runs, while each run records its own values and outcomes. A clean report cannot guarantee supplied values meet the workflow schema or domain rules. No registry snapshot, workflow versioning, or run identity is introduced.

Missing workflow inputs are distinct from missing provider outputs. Existing output monitoring continues to attribute producer contract violations and optional-output resolution failures; it must not count rejected input envelopes as missing-output incidents.

The new workflow outcome is additive. Callers inspecting outcomes should account for `invalid_input`; the runner does not fabricate a failed step for a failure that precedes all steps. Literal-only workflows retain their existing behavior when inputs are omitted.

No blocking preflight gate, automatic repair/defaults, retries, branching, persistence, LLM, or Lab 006 work is included.
