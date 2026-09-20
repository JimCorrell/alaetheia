# ADR-001: Begin with one supervisor

- **Status:** Accepted for the initial architecture
- **Date:** 2026-09-20
- **Scope:** Alaetheia's first executable increments

## Context

Alaetheia is envisioned as a supervisor capable of reaching many domain tools and, perhaps eventually, specialist agents. A multi-agent layout is attractive, but a service registry and one capable supervisor may solve many tasks. Introducing separate agents before measuring that baseline would obscure whether an independent reasoning boundary is useful. This project also aims to teach how discovery and orchestration work; inspectable mechanics matter as much as feature breadth.

## Decision

Theia starts as the sole supervisor and reasoning agent. The first foundation is a registry of semantic capability contracts, separate from any provider or future agent identity. Subsequent work may add planning, execution, observation, and an execution ledger around that registry. We do not create worker agents or an agent registry as part of this decision.

When choosing a mechanism, prefer **Function > Service > Workflow > Agent > Multi-Agent**. Propose another agent only for a bounded outcome requiring independent decisions, with a defined mission, authority, state, and lifecycle. Compare it to a single-supervisor implementation using a measurable criterion such as result quality, context isolation, latency, cost, reliability, or operator burden. Record the result in a new ADR before changing the boundary.

## Consequences

- The initial system remains easier to inspect, test, and reason about. Capabilities can be added without creating personas.
- The supervisor may eventually face context and coordination limits. Those limits become experimental signals rather than assumptions.
- Registry design must support overlapping providers so later agent implementations can be added without changing capability identity.
- A capability contract does not authorize invocation; execution governance remains later work.
- Project knowledge must be recorded in Git. A conversation or model memory does not amend this ADR. Runtime memory is a separate deferred concern.

## Revisit triggers

Revisit when a concrete task repeatedly fails under the single-supervisor baseline and a bounded independent reasoning unit plausibly improves it; when a controlled comparison shows meaningful gains; or when authority isolation requires a separate decision boundary. Mere growth in the number of tools, a desire for named specialists, or available multi-agent frameworks is insufficient evidence.
