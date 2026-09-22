# Lab 005: Workflow input contracts and reuse

- **Status:** Implemented; see [results](lab-005-results.md)
- **Decision:** [ADR-006](../architecture/decisions/ADR-006-reusable-workflow-inputs.md)
- **Question:** Can one declared workflow safely accept varied supplied records without rebuilding its steps or weakening its contracts?

## Scope

Give workflows typed input schemas and named workflow-input references. Validate the full supplied input envelope before any provider runs. Keep existing scalar rules and explicit missing-reference failures. Record inputs and pre-execution validation diagnostics in the workflow record.

Extend advisory preflight to the new references using existing type and optionality rules. Run a reusable local parcel-record validation/summary example against several records, including wrong scalar types and invalid domain values. Continue comparing preflight with runtime outcomes and testing missing-output attribution.

## Acceptance evidence

- Multiple records use the same unchanged definition and produce independent input/step/output snapshots.
- Missing required inputs, unexpected fields, invalid containers, nulls, wrong types, booleans passed as numbers, and nonfinite numbers are rejected before any invocation.
- Referenced workflow inputs must be declared. Optional values may be absent unless explicitly resolved by a step; no defaults or automatic omission occur.
- Workflow inputs mix with literal and output bindings and participate in preflight handoff analysis.
- Existing no-input workflows keep working. Invalid workflow envelopes mark all steps skipped and return workflow-level diagnostics rather than a fabricated invocation failure.
- Supplied parcel domain rules are explicit and tested. Summary wording distinguishes user-reported facts from verified facts.
- Existing missing-output monitoring and all earlier tests remain correct; input failures are not misclassified as output failures.

## Boundary

No data acquisition, database, GIS, valuation, suitability scoring, agents, planner, LLM, retries, default values, branching, persistent monitoring, or subsequent lab work. Preflight remains advisory; runtime envelope validation is mandatory.
