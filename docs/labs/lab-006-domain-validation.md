# Lab 006: Structured domain-validation results

- **Status:** Implemented; see [results](lab-006-results.md)
- **Decision:** [ADR-007](../architecture/decisions/ADR-007-structured-domain-rejections.md)
- **Question:** Can callers distinguish expected data rejection from a provider malfunction without parsing exception messages?

## Scope

Add typed domain issues and a rejection result that local functions can return instead of success output. Record stable issue codes, messages, and optional input-field references. Keep invalid input, domain rejection, provider failure, and invalid output distinct. Preserve schema validation, fail-fast workflows, advisory preflight, and missing-output observation.

Update the parcel validation example to collect blank-text and nonpositive-acreage issues. Record the public behavior change in its capability version. Do not infer rejection from exceptions or return a partial success payload.

## Acceptance evidence

- Valid rejections carry a nonempty immutable typed issue collection. Invalid codes/messages/fields/collection shapes are rejected clearly.
- A rejection records invocation, selected versions, input snapshot, and domain issues with no successful outputs, exception, or missing-output alarm.
- Unexpected exceptions remain provider failures. Malformed dictionaries remain invalid output. A rejection pointing to an undeclared input is invalid output.
- Input/selection failures still prevent invocation. Successful payload validation and normalization are unchanged.
- A domain rejection stops its workflow, skips later steps, and appears distinctly in run comparisons and example output.
- Missing promised outputs still produce genuine omission observations; rejected records do not generate false missing-output incidents.
- The complete existing suite passes, with the previous parcel-domain expectation deliberately updated from provider failure to domain rejection.

## Boundary

No automated correction, defaults, branching, retries, per-capability error registry, generic domain constraint engine, persistence, remote providers, LLM, planner, or subsequent lab work.
