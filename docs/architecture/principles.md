# Architecture principles

These are constraints for experiments, not claims that every future feature is already known.

1. **Start with one reasoning boundary.** Alaetheia begins as the sole supervisor and reasoning agent. An additional agent needs an explicit mission and authority, its own decision loop, and evidence of measurable benefit relative to the single-supervisor baseline. A named role or a wrapper around a tool does not meet that bar.
2. **Choose the least-agentic sufficient mechanism.** Prefer **Function > Service > Workflow > Agent > Multi-Agent**. Move right only when the simpler option cannot reliably achieve the outcome under stated constraints. Record the failure mode and the expected gain.
3. **Discover capabilities, not personalities.** A capability states what operation is available, with typed input, output, version, constraints, and metadata. A service, tool, workflow, or future agent can provide the same capability. Registry entries must preserve provider identity without making it the capability identity.
4. **Make contracts explicit and inspectable.** Discovery and compatibility should be deterministic over declared metadata. Document semantics where a type alone is insufficient. Reject ambiguous or invalid declarations rather than guessing. This favors understandable code over framework magic.
5. **Keep authority bounded.** The supervisor mediates any future delegation. Capability metadata should state relevant permissions and side effects. A declaration is descriptive; it is not itself permission to execute. Execution authorization belongs to a later design.
6. **Retain evidence and provenance.** Future results should be traceable to observations, versions, providers, and decisions. The execution ledger is planned for a later lab. Lab 001 records registry metadata only and must not pretend to have execution evidence.
7. **Separate contract from implementation.** A capability can have multiple implementations and versions. Changing implementation details need not change the public contract; changing accepted input, produced output, or semantics may require a contract version change.
8. **Keep canonical knowledge in Git.** Architecture, decisions, and lab scope live in version-controlled files. Conversations are inputs to review, not hidden dependencies for future implementation. Runtime memory is deferred.
9. **Experiment before scaling.** Local, in-memory, and single-process approaches are sufficient until measured needs justify persistence, a message bus, distributed execution, or a separate agent registry.

When principles conflict, make the tradeoff explicit in a decision record with a concrete use case and measurable criterion.
