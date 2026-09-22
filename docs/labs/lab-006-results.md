# Lab 006 results: domain rejection versus provider failure

## Outcome

The parcel validator now returns a structured domain rejection for expected data problems. It reports blank parcel ID, blank municipality, and nonpositive acreage together rather than stopping at the first exception. Successful supplied-record summaries are unchanged.

| Situation | Invocation outcome | Workflow behavior |
| --- | --- | --- |
| Wrong scalar input type | invalid_input, not invoked | Fail or reject workflow envelope before invocation |
| Valid types but negative acreage | domain_rejected, invoked | Failed validation step; summary skipped |
| Unexpected exception, even ValueError | provider_failure, invoked | Failed step; later steps skipped |
| Missing promised success field | invalid_output, invoked | Failed producer; missing-output observation retained |
| Valid domain and success payload | success | Continue normally |

## Implementation choices

`domain.py` contains frozen DomainIssue and DomainRejection types. An issue has a code, message, and optional input field; a rejection must contain a nonempty tuple of issues. Order is provider-defined and the parcel example uses a fixed order. Record-level issues use field=None. Multiple issues may refer to the same field; no uniqueness or general issue catalog is invented.

LocalExecutor recognizes explicit DomainRejection after invocation and before validating success output. It verifies issue field references against the selected input contract. Domain issues and a distinct outcome are added to ExecutionRecord; errors retains the issue messages for existing human-readable consumers. Input snapshots and the selected immutable manifest retain provenance.

Exceptions are still faults. A provider constructing an invalid rejection produces a provider failure because construction raises; returning a dictionary that resembles a rejection does not opt into the protocol. Returning an issue referring to an undeclared input yields invalid output. Valid rejection has no partial data or missing-output fields.

The workflow runner is unchanged: every non-success outcome stops execution. Workflow outcome remains failed rather than adding another top-level status. The detailed failed execution outcome and structured issues are now also included in RunComparison. This prevents callers from conflating data rejection with a technical error when viewing a comparison summary.

`parcel.record.validate` now declares contract and implementation 2.0.0, with the example requirement updated to the exact contract. `parcel.record.summarize` remains 1.0.0. Rejection rules have observable meaning and are not silently changed under the previous version. Historical Lab 005 results remain preserved and annotated.

## Missing-output monitoring

Expected rejection has no successful output by design. It therefore generates no missing-output event, and skipped summary steps are not counted as failures to supply data. A provider that returns an ordinary dictionary without required fields still produces invalid_output and the prior structured omission evidence. Tests cover both paths.

Monitoring remains local to explicit runs. No scheduled checks, event store, or automatic recovery was introduced.

## Validation

Python 3.12.10: all 86 test methods pass (76 prior methods, including the intentionally revised parcel-domain expectation, plus 10 Lab 006 methods with subcases). Tests cover immutable declaration validation, multi-issue aggregation, success behavior, exception separation, malformed rejections, unknown input-field references, pre-invocation rejection, version boundaries, fail-fast behavior, comparisons, omission attribution, and demo JSON output. Source compilation and whitespace checks pass.

## Questions surfaced

1. **Codes need ownership.** DomainIssue provides structure, but each capability owns its code meanings. Should future contracts explicitly declare allowed rejection codes before independent providers use them?
2. **Failure presentation differs from recovery policy.** We can now explain why data was rejected, but no evidence yet supports automatic repair, retries, or continuing the workflow.
3. **Aggregate workflow status is coarse.** A failed workflow can now be explained as domain_rejected through its record/comparison. Is that sufficient for callers, or would a separate workflow-level rejected status add value?
4. **Expected does not mean trustworthy.** A provider can incorrectly report a domain issue. Domain tests still matter; typed results do not validate semantic truth.

The implementation stays within the agreed scope. Lab 007 remains unimplemented.
