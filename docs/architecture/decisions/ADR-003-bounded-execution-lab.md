# ADR-003: Test one explicit invocation before planning

- **Status:** Accepted; implemented in Lab 002. Original design-only authorization notes below are historical.
- **Date:** 2026-09-21
- **Scope:** Next experiment after the Lab 001 discovery foundation

## Context

Lab 001 discovers multiple compatible offers but does not execute them. We need evidence about the contract-to-execution boundary before adding a planner or LLM. The architecture discussion accepted a bounded experiment using an explicit caller and local functions.

## Decision

Lab 002 will ask: can we select and execute one capability safely and produce an inspectable result?

1. Use a deterministic caller. No supervisor, planner, or LLM is needed for this experiment.
2. Select an exact provider/implementation offer explicitly. Discovery remains a candidate list, not a ranking algorithm; ambiguity must not silently select the first entry.
3. Keep exact input-schema compatibility during discovery. Separately validate actual supplied values before invocation: a compatible declaration does not prove that a payload is valid.
4. Limit implementations to local, side-effect-free example functions. Capability metadata remains descriptive and is not execution authorization.
5. Distinguish success, invalid input, provider failure, and invalid output. Produce a minimal inspectable record identifying the selected offer, contract and implementation versions, and outcome. No database or persistent ledger is required.
6. Honor ADR-002: consumers tolerate additional outputs while checking required fields and exact declared types. Optional requested outputs may be absent; optional advertised fields must have the declared type when present. An optional provider output cannot satisfy a required consumer need.

## Consequences and deferred choices

The experiment isolates invocation and validation from reasoning and provider ranking. It does not establish production execution safety or a general authorization model. Failure handling should be visible, not hidden behind automatic retries or fallback selection.

Input subsets, cost-based ranking, nested geometry schemas, deployment identity, machine-readable units, persistence, remote providers, and side-effecting actions remain deferred until a concrete experiment requires them. Worker agents, runtime memory, distributed infrastructure, and web UI remain outside scope.

The accompanying Lab 002 brief records the agreed boundary. This PR prepares the design only; implementation requires a subsequent request.
