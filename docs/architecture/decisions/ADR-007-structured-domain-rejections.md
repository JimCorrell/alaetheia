# ADR-007: Represent expected domain rejection as a typed result

- **Status:** Accepted for Lab 006
- **Date:** 2026-09-22

## Context

Lab 005 represented nonpositive acreage and blank parcel identifiers as provider exceptions. Those are expected data rejections, not evidence that an implementation malfunctioned. The agreed next experiment separates these outcomes without introducing recovery or branching.

## Decision

A local callable may return its ordinary success dictionary or `DomainRejection`, an immutable nonempty tuple of `DomainIssue` values. Each issue has a machine-readable code, a human-readable message, and an optional input field. Codes and field identifiers use the existing identifier grammar; messages must be nonblank. None as the field denotes a record-level or cross-field issue.

The executor recognizes only the explicit rejection type, not exception messages or dictionary keys. A valid rejection produces `Outcome.DOMAIN_REJECTED`, `invoked=True`, the input snapshot, structured issues, and messages in the existing errors field. It has no outputs, exception type, or missing-output fields. Successful dictionaries still undergo the same full provider and consumer output validation.

Issue fields, when supplied, must name inputs in the selected offer. A rejection naming an undeclared field is invalid output. A malformed rejection constructed inside a provider raises a normal construction exception and remains a provider failure. Exceptions, including ValueError, are never automatically reclassified as expected domain rejection.

Workflow behavior remains fail-fast: the step and workflow are failed, later steps are skipped, and the ExecutionRecord carries the precise rejection outcome. Run comparisons add the failed execution outcome and domain issues, distinguishing expected rejection from provider exceptions while retaining existing missing-output observations. No retry, fallback, omission, or repair is added.

## Example and version boundary

The parcel validator returns all applicable issues in a stable order: blank parcel ID, blank municipality, then nonpositive acreage. Successful normalization and summary behavior remain unchanged. The validation capability and its implementation move from 1.0.0 to 2.0.0 because observable rejection behavior changed. The example requirement selects 2.0.0 explicitly. The summary capability remains 1.0.0.

DomainRejection is a standard local invocation outcome, not a new schema field or a successful payload with an error flag. Input/output schemas continue describing the normal exchange; the library protocol supplies the rejection alternative. This lab does not add per-capability issue catalogs, issue-code negotiation, remote serialization contracts, or a new metadata schema. Issue meanings remain documented with the example and owning capability.

## Consequences

Callers can distinguish bad domain data from execution faults without parsing prose. Multiple issues can be presented together, but messages are explanatory and codes/fields are the structured interface. The library does not prove that a provider's claimed domain rejection is substantively correct.

A clean structural preflight still cannot predict domain rejection. Rejection intentionally produces no success output, so it must not generate missing-output alarms. Independent failures such as a provider returning `{}` still produce invalid output and omission evidence.

This design makes failures clearer while leaving policy unchanged. Domain issue catalogs, generalized semantic constraints, repair, branching, or a new workflow-level rejection status require later evidence and decisions. Lab 007 is not authorized.
