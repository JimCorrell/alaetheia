# Conceptual model

This model names the boundaries that future implementations must preserve. It is not a class diagram and does not imply that every concept exists in Lab 001.

```text
User goal
  -> task(s) -> plan -> chosen capability requirement
                            |
                            v
                    capability registry
                     /      |       \
                provider provider provider
                            |
                     future execution
                            |
                  observation + evidence
                            |
                   execution ledger -> result
```

The **goal** is the desired outcome stated by a user. A **task** is a bounded piece of work toward that goal. A **plan** orders tasks and their dependencies; it may change after observation. A **capability** is a semantic operation contract. It answers *what can be done* and states the required input, promised output, contract version, constraints, and descriptive metadata. It is not an endpoint, a specific function, or a promise that execution is authorized.

A **provider/implementation** is one concrete way to supply a capability. Several providers may implement the same capability and version, with different costs, permissions, reliability, or dependencies. A provider may be a function, service, tool adapter, workflow, or, later, an agent. Registry discovery yields candidates; future selection and execution must still consider policy and runtime conditions.

A **function** is a local deterministic or bounded operation invoked in-process. A **service** exposes operations across a stable boundary, possibly a network or process boundary. A **tool** is an interface by which an agent or supervisor invokes an operation; the underlying provider might be a function or service. A **workflow** is an explicit sequence or graph of steps with control flow; it need not reason about its own goal. An **agent** is an independently addressable decision-making unit with a mission, capabilities, state, tools, authority, and lifecycle. It can observe and choose subsequent actions within bounds. These terms are not interchangeable.

The **supervisor** is Theia's initial and sole reasoning agent. It will interpret goals, form plans, select capabilities, coordinate execution, evaluate observations, and decide whether to continue. No worker agent is assumed. A future worker agent would take a delegated outcome and exercise bounded independent judgment; it would not merely run a scripted workflow.

**Context** is information made available for a decision or step. An **observation** is a reported outcome or state following an action. **Evidence** is material supporting a claim, with provenance sufficient for inspection. A **result** is the answer or artifact returned for a goal. An **execution** is one traceable attempt to carry out a plan. The **execution ledger** is a future record of decisions, invocations, observations, and evidence; it is distinct from the capability registry.

## Version and identity boundaries

Use a stable semantic capability ID such as `terrain.slope.analyze` and a semantic contract version such as `2.1.0`. The provider has its own identity and implementation version. A requirement such as `terrain.slope.analyze >=2.0.0 <3.0.0` is a request for a compatible contract, not a named agent. A provider can advertise several capabilities; several providers can advertise one capability. Lab 001 must allow both relationships without overwriting entries.

## Architecture horizon

| NOW | NEXT | LATER / UNPROVEN |
| --- | --- | --- |
| Capability contracts; in-memory registry; deterministic discovery and compatibility | One supervisor; planning; execution loop; execution ledger | Worker agents; agent registry; knowledge graph; vector memory; message bus; distributed runtime |

Only NOW is within Lab 001. The other columns are orientation and questions for later experiments, not a mandate to build them.
