# Lab 007 Phase A results: offline proposal selection

## Scope and evidence

Implemented the [approved brief](lab-007-proposal-only-selection.md) and [ADR-009](../architecture/decisions/ADR-009-proposal-only-selection.md) after the user authorized proceeding. Phase A only: no model calls, supervisor, generated workflow, or execution from a proposal. Existing runtime behavior and catalog-inspection CLI are unchanged.

The [complete evaluation evidence](evidence/lab-007-baseline-v1.json) includes every request, supplied input, expected label and rationale, actual proposal, validation diagnostics, correction categories, full workflow definitions and exact manifests, revision labels, and SHA-256 hashes of the five experimental modules. The existing runtime base is merged revision `5889a38`; the experiment's source and evidence are versioned together in this change. This is a checked-in experiment report, not runtime persistence or a ledger.

Fixtures were authored before evaluating the baseline. Revision 1 has four cases in each of six categories: raw count, trimmed count, parcel summary, ambiguity, unsupported operation, and insufficient inputs. The first two in each category are development examples; the remaining two are held-out evaluation cases. One author prepared both rules and labels, so this split is not independently blinded or statistically representative. Expected labels are open for human review. No rule or label was changed to improve the observed scores.

## Results

| Metric | Development | Held-out |
| --- | --- | --- |
| Exact workflow selection / cases expecting selection | 6/6 | 3/6 |
| Unchanged, schema-valid inputs / emitted selections | 6/6 | 3/3 |
| Abstentions / cases requiring abstention | 6/6 | 6/6 |
| Correct abstention reason / cases requiring abstention | 6/6 | 5/6 |
| Unnecessary abstentions / cases expecting selection | 0/6 | 3/6 |
| Invalid proposals / all proposals | 0/12 | 0/12 |
| Unknown workflow IDs / all proposals | 0/12 | 0/12 |
| Cases needing correction against reviewed labels / all cases | 0/12 | 4/12 |

There were nine emitted selections in total. All were valid and preserved inputs. No must-abstain case produced a selection. Four held-out cases need a decision correction:

| Case | Expected | Observed | Interpretation |
| --- | --- | --- | --- |
| raw-4 | Raw count | Unsupported request | Did not recognize “character length without removing the spaces at either end” |
| trimmed-4 | Trimmed count | Unsupported request | Did not recognize “whitespace at both ends” and “character length” |
| parcel-4 | Parcel summary | Unsupported request | Did not recognize “descriptive digest” of a “land record” |
| ambiguous-4 | Ambiguous request | Unsupported request | “How long is this text?” needs clarification, not an assertion of missing capability |

These results measure a narrow phrase baseline. They do not establish that natural-language requests are safe to execute: negation, additional unsupported intentions, and arbitrary wording are not comprehensively parsed. A valid proposal may still select the wrong operation. Domain-invalid negative or zero acreage was preserved without invocation; execution success was deliberately not evaluated by the selector.

The correction metric is a comparison with authored labels, not a measured human review session or time estimate. Changing an abstention reason counts as a decision correction. Invalid proposals can additionally carry input or format correction categories, counted once per case in the aggregate. Exact selection measures the ID independently from proposal/input validity; the two metrics must be read together. Zero denominators are displayed as raw 0/0 counts, not invented percentages.

## Design choices

- `selection.py` validates closed data into typed selection/abstention and diagnostic records. It reuses builtin-data snapshotting and the existing scalar validator. Type-sensitive comparison rejects integer/float/bool substitutions, even where Python equality would accept them. Records remain detached but caller-editable, like current execution records.
- The catalog is a checked tuple of three entries, with definitions and manifest evidence but no callables. Text definitions reuse existing strip/count semantics; the parcel definition is reused exactly. Catalog construction inspects the parcel executor's declarations without invoking providers; the evaluator receives no executor.
- `selection_baseline.py` uses explicitly listed phrase families and precedence. It reads request text only for intent; supplied text remains payload. Unknown phrasing abstains rather than selecting a fallback. It is intentionally not a general parser, and metadata is not authorization.
- `selection_evaluation.py` protects fixture inputs from selector mutation and reports proposal validity independently from semantic correctness. Stable local diagnostic codes avoid changing runtime error categories. No runtime diagnostic refactor was necessary.
- `selection_example.py` prints a readable report or full JSON evidence. Hashes identify source content; they do not verify executable purity or establish a general serialization protocol.

## Verification

All **108 tests passed** under Python 3.12.10, including 14 new Lab 007 tests. Source/test compilation and whitespace checks passed. No live-model evaluation or remote CI run was performed in this local implementation step. Focused tests cover closed shapes, unknown IDs/reasons, missing/extra/mistyped inputs, fabricated/dropped/changed values, type fidelity, hostile custom hooks and unsupported data, duplicate catalog IDs, evidence reproducibility, metric denominators, and fixture isolation.

An evaluation test instruments actual local bindings and forbids both executor and workflow-runner entry points. Selection, validation, and both report formats produce zero invocations, including accepted selections. A separate test explicitly executes each predefined workflow to establish that the definitions are usable; those calls are outside the evaluator and grant it no authority.

## Observations for the next discussion

1. The principal observed weakness is recognizing paraphrases, not preserving structured inputs. A later model comparison has a concrete target: reduce the four held-out correction cases without increasing selections on must-abstain cases or invalid proposals. This is a hypothesis, not evidence that a model will help.
2. Unsupported and ambiguous requests need different user-facing responses. A future clarification proposal may be more useful than extending a list of phrases, but is outside this lab.
3. Whitespace and code-point semantics matter even for tiny operations. These examples justify clear descriptions; they do not yet justify a general semantic metadata system.
4. Structured inputs isolate selection, but avoid the harder input-extraction problem. Decide whether that simplification matches the first useful user task before expanding the architecture.
5. Human review of the fixture labels and independent requests should precede model comparison. Model, prompt, budget, data handling, and evaluation protocol still need a separate decision. Phase B has not begun.

No material scope deviation. The single-author synthetic evaluation limits the strength of the evidence; no production reliability, live-model quality, or measured reviewer effort is claimed.
