# Repository guidance for Codex and contributors

Read `README.md`, `docs/architecture/principles.md`, `docs/architecture/conceptual-model.md`, and the relevant lab brief before changing code. These Git-tracked files are the project handoff. Do not treat prior chat messages, assistant memory, or examples as canonical requirements.

## Current authorization boundary

The bootstrap phase creates documentation and an empty Python 3.12+ skeleton only. Do not implement Lab 001 until a later request explicitly authorizes it. Do not implement a supervisor, LLM integration, worker agents, persistence, or distributed infrastructure under the guise of scaffolding.

When Lab 001 is authorized, follow `docs/labs/lab-001-capability-registry.md`. Prefer small explicit types and algorithms, meaningful behavior tests, and a CLI that exposes registry contents. Keep semantic capability identity separate from the identity of the implementation providing it.

## Decision hygiene

- Use the vocabulary in `docs/glossary.md`; name concepts precisely.
- Prefer Function > Service > Workflow > Agent > Multi-Agent, choosing the least complex mechanism that meets the measured need.
- Keep capability contracts inspectable, typed, versioned, and independent of particular providers.
- Record a decision and its evidence in an ADR when changing an architectural boundary. Do not retrofit the docs to make an experiment appear predetermined.
- Treat project knowledge in Git as canonical. Runtime memory remains deferred.
- Keep the source tree compatible with Python 3.12 or newer. Do not add an agent framework or a dependency solely for convenience during bootstrap.

The enclosing ChatGPT project mirror has its own `AGENTS.md` and `sources/` material. Those managed files are read-only references and are outside this repository.

## Lab 002 follow-up

Lab 002 was explicitly authorized after the design PR merged. For its invocation boundary, read `docs/labs/lab-002-explicit-capability-invocation.md`, `docs/labs/lab-002-results.md`, and ADR-002/ADR-003. Keep invocation separate from discovery and limit examples to trusted local, side-effect-free functions. The historical bootstrap restriction above is not a prohibition on the authorized Lab 001 and Lab 002 implementations. No subsequent lab is authorized by this note.
