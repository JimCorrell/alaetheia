# Vision and learning agenda

Alaetheia, or Theia, is intended to become a personal supervisor that accepts a goal, finds available capabilities, forms a plan, executes bounded actions, observes what happened, revises when necessary, and returns a result supported by evidence. The long-term aspiration is a reliable interface across tools and domains, not a predetermined collection of personas or agents.

The first executable hypothesis is narrower: **one supervisor can orchestrate explicit capabilities and ordinary services across a useful class of goals**. Before adding another reasoning component, we need to learn where this design fails. Capability discovery therefore comes first. A supervisor cannot choose responsibly among operations it cannot inspect or compare.

## What we are trying to learn

1. Can semantic, typed capability contracts tell a future supervisor what an operation accepts, produces, requires, and is allowed to do?
2. Can discovery handle several implementations of one capability without conflating an operation with its provider?
3. Which tasks can be handled by functions, services, or workflows before independent reasoning is needed?
4. When does a separate agent improve quality, context control, isolation, or throughput enough to offset delegation overhead?
5. What evidence must be retained so that a user can inspect both the answer and the route taken to it?

The project is deliberately educational. We should be able to explain and inspect each mechanism, vary one architectural assumption at a time, and compare behavior. An opaque framework is a poor foundation for these experiments even if it shortens an initial demo.

## Intended progression

**NOW — capability contracts and registry.** Define a capability independently of its provider. Make versions, schemas, metadata, overlap, and compatibility queryable. Lab 001 stops at discovery and inspection; it executes nothing.

**NEXT — supervisor, planning, execution loop, execution ledger.** Build a single reasoning supervisor that can use the registry to select a plan, invoke permitted operations, observe results, and preserve an auditable record. These are separate increments and are not specified for implementation by Lab 001.

**LATER / UNPROVEN — worker agents, agent registry, knowledge graph, vector memory, message bus, distributed runtime.** Each is a candidate response to observed limits, not a default feature list. Additional agents require a demonstrated independent reasoning boundary with measurable value.

## Boundaries

Theia may eventually use natural language, external systems, and domain tools. No provider, model, UI, infrastructure stack, or memory architecture is selected by this vision. Project design knowledge lives in version-controlled repository files. Runtime memory of user facts, observations, or past executions is deferred, and must not be confused with those design files.

Success for the first lab is not an impressive autonomous demo. It is a registry whose behavior is clear enough to test, inspect, and later use as the foundation of an execution system.
