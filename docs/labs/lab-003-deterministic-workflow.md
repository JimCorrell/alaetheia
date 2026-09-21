# Lab 003: Deterministic workflow composition

- **Status:** Implemented; see [results and discussion](lab-003-results.md)
- **Question:** Can individually valid capabilities compose into a valid, inspectable workflow?
- **Decision:** [ADR-004](../architecture/decisions/ADR-004-sequential-workflows.md)

## Scope and acceptance criteria

Declare a nonempty ordered tuple of steps, each with a unique step ID, exact offer key, requirement, and explicit named input bindings. Inputs come from finite scalar literals or named output fields of earlier steps. Reject malformed definitions, duplicate IDs/targets, and missing/self/forward step references before any execution. Earlier-only references also exclude cycles without requiring a graph scheduler.

Execute in declared order using the existing LocalExecutor. At every step, resolve referenced outputs and validate the assembled input through Lab 002. Each reference must name a declared output field present in the upstream successful execution. No inference from field names, implicit whole-record forwarding, conversions, or unvalidated extra-output wiring.

Stop at the first failed dependency resolution or unsuccessful invocation. Preserve the failing step's diagnostics and execution record when one exists. Mark every later step skipped, including independent steps. Retain successful earlier records, the workflow definition and selected offers, and an overall success/failed outcome identifying the first failed step. Records remain process-local and no state carries into a new run.

Provide a three-step success example and an incompatible-handoff variant. Test explicit order and data mapping, invalid definitions, incompatible handoffs, missing output values, each Lab 002 failure category, skipped downstream calls, record provenance, repeated-run isolation, and the existing complete suite.

## Exclusions

No LLM, planner, ranking, dynamic steps, branching, parallelism, retries, fallback, compensation, persistence, remote execution, side-effecting examples, runtime memory, agents, distributed infrastructure, or web UI. Structural definition validation does not promise static verification of all future handoffs. Lab 004 is not authorized.
