# ADR-002: Allow extra output fields during discovery

- **Status:** Accepted
- **Date:** 2026-09-21
- **Scope:** Lab 001 requirement-to-offer compatibility

## Context and evidence

The initial exact-schema experiment excluded all three 2.1.0 slope offers from a consumer needing only `mean_slope`, because those offers also guarantee `max_slope`. The consumer's actual need was satisfied. The architecture discussion accepted extra output fields as safe for consumers that tolerate them.

## Decision

Output requirements describe minimum consumer needs, not a closed response shape. A consumer using this discovery policy must tolerate additional fields. Matching does not strip fields, adapt payloads, or invoke providers.

- Every required requested output must be declared and required in the offer.
- An optional requested output may be absent, optional, or required in the offer.
- Any requested output that the offer declares must have exactly the requested type, including optional fields. There is no coercion or integer-to-number widening.
- Extra offered outputs are allowed regardless of type or requiredness.
- An empty output requirement has no field constraints, as does an omitted output requirement.
- Input schemas still match exactly. Version ranges, capability identity, and metadata filters remain independent checks.
- Providers advertising the same capability ID/version must still agree on complete schema shapes. Consumer compatibility does not relax contract identity.
- Failures identify the field and missing guarantee or type mismatch; field diagnostics are sorted by name for deterministic inspection.

## Consequences

A `mean_slope` requirement now discovers four offers in `>=2.0.0 <3.0.0`; a requirement for both slope fields still discovers three. Optional output declarations cannot fulfill required needs. Matching does not prove semantic equivalence (such as degrees versus percent), runtime success, or authorization.

This is an intentional broadening of discovery behavior. Callers requiring closed response records must not interpret a match as a closed-schema guarantee. Future execution consumers must honor the extra-field tolerance policy; no execution code is added here.

Input subset rules, nested schemas, type widening, units, and provider ranking remain separate decisions. No Lab 002 work is authorized by this change.

## Validation

The full 21-method suite passes under Python 3.12.10. Added tests cover the output presence/requiredness/type matrix, field-specific diagnostics, empty output needs, extra fields, discovery/compatibility agreement, and unchanged input/version restrictions. Existing conflicting-contract registration tests still pass.
