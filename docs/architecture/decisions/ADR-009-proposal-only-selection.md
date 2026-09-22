# ADR-009: Scope the proposal-only selection experiment

- **Status:** Accepted as the Lab 007 design boundary; implementation and live-model integration remain deferred
- **Date:** 2026-09-22
- **Scope:** Define the next experiment after the merged architecture consolidation

## Context

Labs 001–006 demonstrate deterministic discovery and execution, but not a reasoning supervisor. The architecture review recommended a bounded comparison of selection among predefined workflows. After consolidation, the user agreed to define Lab 007's scope before implementation.

## Decision

Use a fixed catalog of three pure local workflows: raw character count, trimmed character count, and supplied parcel summary. The selection unit is an entire predefined workflow, preserving its explicit provider choices. This narrows the earlier conversational phrase "capability selection" to the workflow-selection experiment recommended in the review.

First specify and then implement an offline deterministic baseline and proposal evaluator. Requests carry separately supplied structured inputs; prose-to-input extraction is outside this experiment. A proposal selects one known workflow with unchanged inputs or abstains for a known reason. A closed data validator checks shape, catalog membership, input schema, and input fidelity. Reviewed fixtures judge semantic selection separately. Neither validation nor a correct selection permits or initiates execution.

Keep catalog definitions, test expectations, and comparison rules inspectable and versioned in Git. Record per-case results and denominators, including misses. Instrument providers to demonstrate that proposal evaluation never invokes them. Preserve existing runtime validation, domain rejection, fail-fast behavior, and advisory preflight without changes.

Live-model comparison is a later, separately scoped phase, contingent on reviewing the baseline and agreeing on model/prompt identity, request data, cost limit, and measurement protocol. No model integration or supervisor implementation is authorized by this design increment.

## Consequences

Overlapping text operations expose ambiguity without introducing new infrastructure. Explicit structured inputs keep selection measurable, but the experiment does not measure arbitrary natural-language task completion. A valid proposal may still name the wrong operation or contain supplied domain-invalid data; schema validity is not semantic correctness or a success guarantee.

The baseline may be sufficient for such a small catalog. Prefer it if a later model adds no measured benefit. This experiment does not establish a need for additional agents, dynamic plans, or broader workflow machinery.

See the [Lab 007 brief](../../labs/lab-007-proposal-only-selection.md) for fixtures, metrics, acceptance evidence, exclusions, and discussion questions.
