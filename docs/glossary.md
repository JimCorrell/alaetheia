# Glossary

| Term | Meaning in Alaetheia |
| --- | --- |
| Alaetheia / Theia | The project and, later, its user-facing sole supervisor. "Theia" is a short name. |
| Goal | User-desired outcome, possibly broader than one operation. |
| Task | Bounded work item contributing to a goal. |
| Plan | Ordered or dependent tasks selected to pursue a goal; revisable after observation. |
| Capability | Semantic, versioned contract describing an operation's input, output, constraints, and meaning. Independent of provider. |
| Capability manifest | Machine-readable declaration of one offered capability and its metadata. Lab 001 defines this shape. |
| Provider / implementation | Concrete function, service, tool adapter, workflow, or future agent that fulfills a capability contract. Has identity separate from the capability. |
| Function | In-process operation with bounded behavior. Simplest preferred mechanism when sufficient. |
| Service | Operation or collection of operations behind a stable process or network boundary. |
| Tool | Invocation interface available to a reasoning unit; may wrap a function or service. It is not automatically an agent. |
| Workflow | Explicit control flow composing steps; may contain branching or retries without independent goal reasoning. |
| Agent | Independently addressable decision-making unit with mission, capabilities, state, tools, authority, and lifecycle; can decide how to pursue a delegated outcome within bounds. |
| Supervisor | Theia's initial, sole reasoning agent, responsible for interpreting goals and mediating future orchestration. |
| Registry | Discoverable collection of provider offers of versioned capabilities. Lab 001 uses memory only. |
| Contract version | Semantic version of a capability's publicly promised behavior and input/output semantics. Separate from provider implementation version. |
| Compatibility | Deterministic answer to whether an offered contract satisfies a stated capability/version and schema requirement under documented rules. It does not guarantee runtime success. |
| Context | Information supplied for a decision or execution step. |
| Observation | Reported outcome or state after an action. |
| Evidence | Inspectable support for a claim with provenance. |
| Result | Answer or artifact returned for a goal. |
| Execution | One traceable attempt to run a plan. Not part of Lab 001. |
| Execution ledger | Future record of decisions, invocations, observations, and evidence. Not runtime memory or the registry. |
| Project knowledge | Canonical version-controlled design and implementation facts in Git. |
| Runtime memory | Potential future storage of user/context facts or past experience for Theia; deferred. |

The distinction to keep in view: a capability describes **what** can be done; a provider describes **who or what implements it**; a tool describes **how a reasoning unit invokes it**; a workflow describes **ordered work**; an agent independently decides **how to achieve a delegated outcome**.

## Lab 006 additions

- **Domain issue:** A machine-readable code, explanatory message, and optional input-field reference describing an expected domain problem.
- **Domain rejection:** An explicit typed provider result containing one or more domain issues, with no successful output. Distinct from input-shape rejection, provider exception, and invalid success output.
