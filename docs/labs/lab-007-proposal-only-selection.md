# Lab 007: Proposal-only workflow selection

- **Status:** Design scoped; not implemented. This increment defines the experiment before implementation.
- **Decision:** [ADR-009](../architecture/decisions/ADR-009-proposal-only-selection.md)
- **Question:** Can a bounded selector identify an existing workflow and preserve supplied inputs, while abstaining when the request cannot be resolved safely?

## Experimental boundary

Choose among developer-authored workflows, not individual providers. Each workflow retains its existing exact offers and wiring. A selection is an inspectable data proposal, never permission to execute. The proposal evaluator must not call providers or the workflow runner, even when a proposal passes every check.

Phase A establishes an offline deterministic baseline, fixtures, validation, and a human-readable evaluation report. Phase B would compare a live model against the frozen baseline; it requires a separate decision about model, prompt, budget, and data handling. Phase A does not install an SDK, require credentials, or make model calls. Scripted proposals test validation but are not evidence of model reasoning.

## Fixed catalog

Use a small explicit tuple or mapping of entries, not a new registry subsystem. Each entry has a unique workflow ID, description, input schema, and the full predefined workflow. Reject duplicate IDs. Retain definitions and exact manifests with the evaluation evidence so results are attributable to a specific catalog revision; do not introduce a persistent runtime ledger or workflow versioning system.

| Workflow | Intended request | Inputs and limits |
| --- | --- | --- |
| `text-count-raw` | Count all supplied text characters | Required string `text`; count Unicode code points, including surrounding whitespace |
| `text-count-trimmed` | Strip surrounding whitespace, then count characters | Required string `text`; same count semantics after stripping |
| `parcel-record-summary` | Summarize supplied parcel facts | Existing Lab 006 envelope; no lookup, verification, or suitability advice |

The two text definitions deliberately overlap. Build reusable definitions around the existing pure text functions and workflow-input mechanism; do not change the historical literal-only demonstration. Reuse the parcel definition. A request to count text without a whitespace policy is ambiguous for this experiment and must abstain. A Unicode code-point count must not be represented as a word, byte, or grapheme count.

## Requests and proposals

Each fixture supplies a natural-language request and a separate explicit input dictionary. Input extraction from prose is deferred: the selector must copy the supplied dictionary without coercion, inference, defaults, or silently dropping fields. This isolates selection from another reasoning problem. Descriptions and supplied text are data, not instructions that can extend the catalog or execution authority.

Use a closed, tagged data shape:

```json
{"kind": "select", "workflow_id": "text-count-raw", "inputs": {"text": "  Theia  "}}
```

```json
{"kind": "abstain", "reason": "ambiguous_request"}
```

Abstention reasons are `ambiguous_request`, `unsupported_request`, or `insufficient_inputs`. Reject extra proposal fields, mixed tags, unknown reasons, invalid scalar types, unknown IDs, missing required fields, and input fields outside the chosen workflow schema. Reuse the existing scalar validator and data-only snapshot vocabulary where applicable. Reject custom objects without invoking hooks. Preserve supplied input types as well as values: Python equality alone must not equate `True` with `1` or `1` with `1.0` for this check. Do not accept an abstention carrying a workflow or executable payload.

An input dictionary changed by the selector is invalid even if its schema is valid. Missing or mistyped supplied inputs should lead the baseline to `insufficient_inputs`; a fabricated replacement must fail validation. Schema-valid domain-invalid values (for example, negative acreage) remain unchanged in a selectable proposal. No provider is called to establish domain validity, and the report must explain that this does not predict successful execution.

Separate three observations: whether proposal data is valid, whether a selection matches the reviewed request intent, and whether a selected workflow could later execute successfully. Only the first two are evaluated here. A well-formed but incorrect selection remains incorrect; an accepted proposal is not an execution authorization. Existing preflight stays advisory and unchanged.

## Baseline and fixtures

Implement a small, documented, deterministic rule selector over request intent phrases plus the supplied inputs. Recognized raw/trimmed/parcel intent families must be explicit. Conflicting intents abstain; unrecognized intents abstain. Do not inspect fixture IDs, embed expected answers in selection code, or use fuzzy ranking. This deliberately limited baseline is a comparator, not a general language-understanding claim.

Before collecting outcomes, review and freeze at least 24 fixtures: four each for raw count, trimmed count, supplied parcel summary, ambiguous requests, unsupported requests, and missing/mistyped inputs. Include paraphrases, multiple intents, empty text, Unicode, surrounding whitespace, explicit false/zero values, domain-invalid but schema-valid parcel inputs, and requests for external lookup or unsupported counting semantics. Separate development examples from held-out cases; record any subsequent fixture/rule revision and rerun the full evaluation rather than silently tuning a reported result.

Each case records its ID, request, supplied inputs, expected selection or abstention reason, and a short rationale. Expected answers are authored before evaluating a selector. Keep malformed-proposal tests separate from intent fixtures: cover unknown IDs, altered values/types, fabricated inputs, custom values, and attempted executable/plan fields.

## Evaluation and acceptance

Report raw counts with denominators, per-case evidence, and separate development/held-out results. Do not collapse validation and semantic correctness into one success score.

- Exact selection: correct workflow ID / cases expecting selection.
- Input fidelity: unchanged, schema-valid inputs / emitted selections.
- Abstention recall: abstentions / cases requiring abstention; also report exact reason accuracy.
- Unnecessary abstention: abstentions / cases expecting selection.
- Invalid proposals and unknown IDs: each / all emitted proposals.
- Human correction: cases requiring a changed ID, changed inputs, or changed abstention decision / all cases; count each case once and retain its correction categories. This is a reviewed correction count, not measured human effort or time.

Mechanical acceptance requires every malformed proposal regression to be rejected, all accepted selections to preserve inputs, and zero provider invocations during selection, validation, or reporting. Verify zero calls with instrumented bindings, including accepted proposals. Run the complete existing test suite plus focused new tests. Keep the existing CLI inspection commands unchanged; a separate local example may print the evaluation.

Semantic results are experimental evidence, not a requirement to tune until perfect. Publish every miss and abstention. Before a live-model comparison, freeze the fixtures/catalog, baseline revision, and evaluation rules. A model would justify further exploration only if it reduces reviewed correction cases on held-out requests without increasing selections on must-abstain cases or invalid proposals. Ties favor the deterministic approach. The small synthetic sample cannot establish production reliability or justify automated execution.

## Deliverables and exclusions

Phase A implementation would provide typed proposal/diagnostic records, a closed validator, the three-entry catalog, baseline selector, reviewed fixtures, an evaluation example, focused tests, and a lab results document. Proposal diagnostics should use a small local code vocabulary; do not refactor all existing runtime diagnostics.

No generated workflows, provider selection, automatic execution, supervisor loop, input extraction from prose, model SDK, semantic search, repair, retries, defaults, branching, external data, side effects, persistence, agents, or web UI. Do not change runtime outcomes or existing missing-output observations.

## Questions to take back to architecture review

1. Do errors come mainly from choosing the operation, recognizing insufficient information, or understanding workflow descriptions?
2. Does the raw/trimmed distinction expose a need for better descriptions or structured semantic metadata?
3. Is abstention actionable enough, or does a later experiment need a clarification proposal?
4. Would input extraction add more value than a model selector over this small catalog?
5. Does a measured gain justify a live-model experiment at all? If so, what additional evidence would be needed before any execution authority is granted?
