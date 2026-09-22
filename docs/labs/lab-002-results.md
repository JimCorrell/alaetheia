# Lab 002 results: explicit local invocation

Historical snapshot note: arbitrary copyable extras described below are superseded by [ADR-008](../architecture/decisions/ADR-008-output-data-and-review-hardening.md) and the [current output contract](../architecture/current.md).


## Outcome and scope

Implemented the accepted ADR-003 experiment after explicit implementation authorization. Two pure local functions advertise the same `text.characters.count@1.0.0` contract. A deterministic caller names an exact offer, invokes it once, validates the exchange, and receives a process-local record. The Lab 001 catalog and inspection CLI continue to execute nothing.

No planner, LLM, agent, network provider, side-effecting example, persistence, ranking, retry, or fallback was added. The additional `selection_rejected` outcome makes pre-invocation failures explicit; it is a refinement within the brief, not a new architectural boundary.

## Mechanism and choices

`execution.py` exposes `LocalBinding`, `LocalExecutor`, `ExecutionRecord`, `Outcome`, and `validate_payload`. Bindings are supplied explicitly at executor construction and pin an immutable manifest to a Python callable. The registry remains a catalog of declarations. The executor never picks a discovery result.

Invocation proceeds in order:

1. Resolve the exact offer key in the current registry.
2. Check requirement compatibility and require a binding for the same complete manifest. Unregistered, unbound, incompatible, or replaced offers return `selection_rejected` without calling a function. A changed implementation version is detected even though it is not part of the offer key.
3. Validate the actual input dictionary against the offered contract, rejecting undeclared input fields. Invalid input returns `invalid_input` without invocation.
4. Call the selected function once with a separate input dictionary. Ordinary exceptions produce `provider_failure`, recording exception type and message. `KeyboardInterrupt` and `SystemExit` propagate.
5. Validate output against both the provider's full output contract and the consumer's output needs. Violations produce `invalid_output`. Do not weaken the provider's own promises just because a consumer asks for fewer fields.
6. Copy valid output for inspection and return `success`. Extra fields are retained. Uncopyable output produces an inspectable `invalid_output` outcome instead of leaking a copying exception.

Bindings with declared permissions or side effects are rejected to keep the experiment in scope. This check is not proof that a callable is pure: these are trusted, developer-supplied local functions. The executor is synchronous, single-process, and not thread-safe; it has no cancellation deadline or sandbox. No plugins are loaded and no callable is imported from manifest text.

## Payload rules

- Payloads must be plain dictionaries with string keys. Declared fields use the existing flat schema vocabulary.
- `string` accepts Python `str`, `boolean` accepts `bool`, `integer` accepts `int` excluding `bool`, and `number` accepts `int` or finite `float`, also excluding `bool`. No conversion occurs. Accepting an integer value under a NUMBER declaration does not relax exact schema-type matching between INTEGER and NUMBER declarations.
- Optional means the field may be absent. It does not permit `None`. Missing required fields and wrong types are rejected. NaN and infinities are not numbers in this lab's payload vocabulary.
- Input extras are rejected. Output extras are accepted and retained; their values are unconstrained unless declared by the provider or consumer. Nested extra values are not an extension to the schema language, and they must support copying to be retained in the record.
- An optional output need omitted from the provider's declaration still constrains that field's type if the provider returns it as an extra. This is why checking consumer needs at runtime remains necessary after discovery.

## Execution record

The record contains the selected key, resolved manifest (or `None` for a missing offer), outcome, an `invoked` flag, validated input snapshot when available, successful output snapshot, diagnostic strings, and an exception type for provider/copy failures. The key and manifest identify provider, implementation, contract version, and implementation version.

Payload dictionaries are detached copies but remain caller-editable. The record is not a tamper-proof audit log. Invalid raw payloads are not retained; their validation diagnostics are. Records are returned to the caller and not accumulated or persisted. No timestamp or attempt identifier is required to inspect this single synchronous invocation; a future ledger would need separate decisions about identity and retention.

## Evidence

Python 3.12.10: all 36 tests pass (21 Lab 001 tests and 15 Lab 002 tests with parameterized cases). Coverage includes explicit overlapping implementation selection, pre-invocation rejection, scalar and optional values, extra fields, failures without retry, stale bindings, contract versus consumer output validation, snapshot isolation, and the executable example. The example selects `iterated`, counts the five Unicode code points in `Theia`, and preserves its extra `method` output. Source compilation and whitespace checks pass.

## Questions surfaced for the next discussion

1. **Bindings need lifecycle semantics.** Pinning manifests prevents silently invoking an old implementation after catalog replacement. Should a future deployment model make revision identity part of selection, or retain explicit rebinding?
2. **Consumer needs and provider promises are distinct.** Successful subset matching does not excuse a provider from returning all of its guaranteed fields. Keep both validation layers when expanding schemas.
3. **Shape validation does not verify correctness.** A provider can return an integer count that is wrong. The example defines code points rather than graphemes explicitly, but semantic correctness still needs domain tests or evidence.
4. **Exceptions need policy before external use.** This lab returns exception class and message. Broader use would need error categories and decisions about what details to retain or expose.
5. **A record is not a ledger.** When multiple invocations become one task, correlation, ordering, retention, and record integrity will need an explicit design. No storage decision is justified by this lab alone.
6. **Trust remains local.** Arbitrary in-process code cannot be made side-effect-free by metadata validation. Remote or untrusted functions would require a new authority/isolation decision.

The next increment remains unimplemented. This experiment supplies evidence about invocation without yet justifying an LLM planner or additional agent.
