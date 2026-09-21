# Lab 001: Capability contracts and in-memory registry

- **Status:** Implemented; see [results and discussion](lab-001-results.md)
- **Prerequisite:** Read the vision, principles, conceptual model, glossary, and ADR-001.
- **Question:** How can Theia know what operations are available before any LLM-based discovery or execution exists?

## Objective

Build a small, explicit Python 3.12+ library that declares typed semantic capability contracts and discovers matching implementations in an in-memory registry. Add meaningful tests and a small CLI for inspecting capabilities. Lab 001 does **not** invoke a capability. Its output is an inspectable catalog and deterministic selection of candidate offers for future orchestration.

## Required model

Use explicit typed models (dataclasses, protocols, or comparably clear Python types). Public behavior must be documented and testable without a running service.

**Capability identity and contract.** A stable semantic ID (for example `terrain.slope.analyze`) and a SemVer `MAJOR.MINOR.PATCH` contract version identify the promised operation. Define and validate accepted names and versions. Keep an optional human description separate from the machine-readable fields. Decide and document whether prerelease/build metadata is supported; reject unsupported forms rather than silently sorting them incorrectly.

**Input/output contracts.** Declare named fields with explicit types, required/optional status, and human-readable semantics. Define a small, documented schema/type vocabulary suitable for deterministic inspection and compatibility; do not require a full schema engine. The registry must reject malformed or contradictory declarations. State whether compatibility considers exact schema equivalence or a documented safe subset; do not infer compatibility from descriptions alone. Include examples of both compatible and incompatible changes.

**Capability metadata.** Include at least a description, tags or domain, declared side effects, required permissions, and provenance or source information for the offer. Metadata may include dependencies, cost/latency hints, or maturity if their semantics are explicit. Descriptive metadata must not grant execution authority. Keep any provider implementation version distinct from the contract version.

**Provider offer.** Give each provider a stable identity and distinguish its implementation or offer identity from the capability ID/version. Allow one provider to offer several capabilities and several providers to offer the same capability/version. An overlapping registration must never silently replace another provider. Define a unique key, duplicate behavior, and what unregister removes.

**Registry.** Implement an in-memory collection with documented methods:

| Method | Required behavior |
| --- | --- |
| `register(offer)` | Validate and add an offer; reject a duplicate unique key or invalid contract. |
| `unregister(key)` | Remove exactly the identified offer, with explicit behavior for a missing key. |
| `get(key)` | Return one exact offer or a clear missing result/error. |
| `list(...)` | Enumerate offers deterministically; document sort order and optional filters. |
| `find(requirement)` | Return all candidates matching semantic ID and filters, including overlapping implementations. |
| `compatible(requirement, offer)` | Give a deterministic compatibility answer under documented version and input/output rules; expose the reason when incompatible. |

The precise Python signatures are an implementation choice. Preserve the above semantics. A requirement should express a capability ID, a semantic version range, and any declared input/output needs used by compatibility checking. At minimum, support a practical range form such as `>=2.0.0 <3.0.0`, with defined inclusive/exclusive behavior and clear invalid-range errors. Version ordering must be numeric (`2.10.0` follows `2.9.0`). `find` should use the same compatibility rules as `compatible`, rather than a second looser matcher. Returned order should be stable and documented, not an accidental dictionary insertion order.

## Suggested inspection example

Two offers may advertise `terrain.slope.analyze@2.1.0`, one supplied by a local Python provider and another by a remote GIS service. A query for `terrain.slope.analyze >=2.0.0 <3.0.0` should return both if their contracts satisfy the requirement. A `3.0.0` offer should be excluded. A requirement for a required output field absent from one provider should exclude that provider and give an intelligible incompatibility reason. This is discovery, not provider ranking or invocation.

## CLI

Provide a small command-line entry point that can display a human-readable table or structured JSON of registered offers and inspect a selected capability ID/version. Because this lab has no database or running service, use a small explicit sample catalog or an input manifest file to populate the process-local registry; document which. The CLI should show capability ID, contract version, provider ID, input/output summary, and relevant metadata. Invalid input and unknown IDs should produce clear messages and nonzero exits. Do not create a web UI or execution command.

## Tests and acceptance criteria

Tests should demonstrate:

1. Valid typed declarations and clear rejection of malformed IDs, versions, schemas, missing metadata, and conflicting fields.
2. Numeric semantic-version ordering, version-range boundaries, and explicit behavior for unsupported version syntax.
3. Registration, exact retrieval, deletion, missing keys, duplicate-key handling, and stable list order.
4. Two overlapping providers for one capability/version remain independently discoverable and removable; one provider can offer more than one capability.
5. Matching and nonmatching capability IDs, version ranges, input/output needs, and metadata filters; `find` and `compatible` agree.
6. CLI listing and inspection with useful output and error codes.

Done means the package installs or runs under Python 3.12+, tests pass locally, the README explains how to use the library and CLI, and the implementation stays small enough for a reader to follow discovery from manifest to result. If the chosen compatibility rules require a tradeoff, record it in the lab notes or an ADR with an example.

## Explicit exclusions

No LLM integration; no supervisor implementation; no agents or agent registry; no capability execution or execution ledger; no databases; no semantic or vector search; no Kubernetes; no message brokers; no web UI. Do not add placeholders that imply these features work. Runtime memory is deferred. A function or service named in sample metadata is only a declarative provider example.

## Handoff for the next session

This document authorizes no implementation in the bootstrap session. In a later Lab 001 implementation session, create the types, registry, CLI, tests, and usage documentation within the boundaries above. Report the compatibility rules chosen, commands run, test results, and any unresolved ambiguity before proposing Lab 002.

## Accepted compatibility refinement

Following the initial experiment, [ADR-002](../architecture/decisions/ADR-002-output-subset-compatibility.md) permits extra output fields. Input matching remains exact; required output presence and exact field types remain enforced. The registry still rejects inconsistent schemas under one capability ID/version.
