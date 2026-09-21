# Lab 002: One explicit capability invocation

- **Status:** Implemented; see [results and discussion](lab-002-results.md)
- **Prerequisites:** Merged Lab 001 and ADR-002 output compatibility refinement
- **Decision:** [ADR-003](../architecture/decisions/ADR-003-bounded-execution-lab.md)
- **Question:** Can a deterministic caller explicitly select and execute one capability, validate the exchange, and return an inspectable execution record?

## Scope

Use local, side-effect-free example functions and the existing capability registry. Keep semantic capability identity separate from the callable binding. The caller selects an exact offer; discovery must not become implicit ranking. Missing or incompatible selections must fail clearly before invocation.

Input schema discovery stays exact. Validate supplied values against the selected input contract before calling the implementation. Missing required fields and wrong types must not reach the function. Runtime value validation is separate from comparing schema declarations; document scalar type rules, optional-field handling, and unexpected-input behavior during implementation, without adding coercion.

Check returned values against the selected output contract and the consumer's needs. Required outputs must be present and correctly typed. Optional fields may be absent but must have their declared type when present. Additional output fields must not cause rejection merely because the consumer did not request them. Do not strip outputs or infer semantic equivalence from descriptions.

Return a minimal process-local record identifying the selected offer, its contract and implementation versions, and outcome. Distinguish success, invalid input, provider failure, and invalid output. Keep failures inspectable; do not add automatic retry or fallback behavior. Exact record types and exception representation remain implementation choices to document.

## Acceptance evidence

Tests should demonstrate:

1. Explicit selection executes the intended local implementation; overlapping offers do not cause implicit selection.
2. Invalid input, missing selections, and incompatible selections prevent invocation.
3. A successful invocation returns validated output and an inspectable record tied to the selected offer and versions.
4. Provider failure and invalid output produce distinct visible outcomes.
5. Extra outputs are accepted; missing required outputs and wrong types are rejected; optional output behavior follows ADR-002.
6. Existing Lab 001 discovery behavior and tests continue to pass.

## Boundary

No LLM, supervisor, planner, worker agents, automatic provider ranking, remote execution, side-effecting examples, persistent storage, runtime memory, distributed infrastructure, or web UI. This is one bounded invocation, not a plan execution system. This document records design approval, not authorization to implement Lab 002 in the current PR.

## Implementation handoff completed

The original design-only boundary above applied to PR #2. A subsequent explicit implementation request authorized this lab. The implementation and its payload/record choices are documented in [Lab 002 results](lab-002-results.md). Further experiments still require their own scope.
