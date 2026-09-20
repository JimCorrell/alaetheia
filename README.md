# Alaetheia

Alaetheia ("Theia") is an experimental personal supervisor for turning a goal into an inspectable sequence of capability discovery, planning, execution, observation, and evidence-backed results. This repository is also a learning laboratory: each increment should expose the mechanism being studied instead of hiding it behind an agent framework.

The first architectural hypothesis is **one reasoning supervisor with a registry of explicit capabilities**. Another agent is warranted only when an independently reasoning unit improves a measured outcome enough to justify its extra authority, cost, and complexity. There are no worker agents in the initial build.

## Current state

This bootstrap contains design documents and an empty Python 3.12+ package and test skeleton. It intentionally contains no working application, capability registry, CLI, LLM integration, or supervisor. [Lab 001](docs/labs/lab-001-capability-registry.md) is a specification for the next implementation session, not an implementation claim.

## Read in order

1. [Vision](docs/vision.md): purpose, hypothesis, and learning goals.
2. [Principles](docs/architecture/principles.md): enduring design constraints.
3. [Conceptual model](docs/architecture/conceptual-model.md) and [glossary](docs/glossary.md): vocabulary and boundaries.
4. [ADR-001](docs/architecture/decisions/ADR-001-single-supervisor-first.md): why the first architecture has one supervisor.
5. [Lab 001](docs/labs/lab-001-capability-registry.md): implementable scope and acceptance criteria.

## Architecture horizon

| Horizon | Components | Status |
| --- | --- | --- |
| NOW | Typed capability contracts and in-memory capability registry | Design specified by Lab 001 |
| NEXT | Theia supervisor, planning, execution loop, execution ledger | Planned experiments; no implementation authority yet |
| LATER / UNPROVEN | Worker agents, agent registry, knowledge graph, vector memory, message bus, distributed runtime | Hypotheses requiring evidence |

Git is the canonical source for project decisions and implementation contracts. Chat transcripts can inform a proposal, but must not silently become architecture. Runtime memory for Theia is a separate, deferred design question.

## Repository layout

`docs/` holds the versioned design package; `src/alaetheia/` is the future Python package; `tests/` is reserved for executable behavior checks. The empty package marks the layout only.

## Working agreement

Make one bounded lab change at a time. Update the relevant design document or add an ADR when a decision changes. Explain evidence, tradeoffs, and remaining uncertainty. Run the tests appropriate to the increment. Avoid adding dependencies or infrastructure before a concrete capability requires them.
