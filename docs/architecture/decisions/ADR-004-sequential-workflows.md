# ADR-004: Compose explicit invocations in declared order

- **Status:** Accepted for Lab 003
- **Date:** 2026-09-21

## Context

Lab 002 validates one explicitly selected invocation. Its success does not prove that its output satisfies another capability's input. The next agreed experiment studies composition and failure propagation before introducing model uncertainty.

## Decision

Use a nonempty sequential workflow of exact offers with field-level bindings from finite scalar literals or earlier declared outputs. Validate structural wiring at construction; delegate selection, payload validation, and invocation to LocalExecutor at each step. Do not duplicate the executor's contract checker or introduce a graph scheduler. Every mapped value is validated against its destination input before that function runs.

Require referenced output fields to belong to the upstream provider contract, not merely occur as extra values. Optional declared outputs can be referenced, but their absence fails dependency resolution; no implicit defaults or omission are introduced. Output tolerance for inspection remains unchanged.

Stop on the first failure and mark all later steps skipped. A failed dependency has no ExecutionRecord because no invocation attempt was submitted; executor failures retain their ExecutionRecord. Preserve the definition, ordered step records, overall outcome, and failing step ID. No rollback occurs: this lab has only pure local examples.

## Consequences

This remains a workflow, not an agent: no component decides how to pursue a goal. Declared order already encodes dependencies. Requiring earlier references rules out cycles and forward references with a simple scan.

Runtime checks can discover a bad later handoff after earlier pure steps have completed. Full contract preflight and optional-output fallback are deferred decisions. A workflow record gives local provenance, not a persistent ledger, unique run identity, or tamper resistance. Lab 002's trust and synchronous-execution limitations remain.
