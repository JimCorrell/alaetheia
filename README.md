# Alaetheia

Alaetheia ("Theia") is an experimental personal supervisor for turning a goal into an inspectable sequence of capability discovery, planning, execution, observation, and evidence-backed results. This repository is also a learning laboratory: each increment should expose the mechanism being studied instead of hiding it behind an agent framework.

The first architectural hypothesis is **one reasoning supervisor with a registry of explicit capabilities**. Another agent is warranted only when an independently reasoning unit improves a measured outcome enough to justify its extra authority, cost, and complexity. There are no worker agents in the initial build.

## Current state

Lab 001 is implemented: immutable typed capability declarations, an in-memory registry, deterministic compatibility/discovery, and a sample-catalog inspection CLI. No capabilities are executed. See the [Lab 001 specification](docs/labs/lab-001-capability-registry.md) and [experiment results and open questions](docs/labs/lab-001-results.md).

## Read in order

1. [Vision](docs/vision.md): purpose, hypothesis, and learning goals.
2. [Principles](docs/architecture/principles.md): enduring design constraints.
3. [Conceptual model](docs/architecture/conceptual-model.md) and [glossary](docs/glossary.md): vocabulary and boundaries.
4. [ADR-001](docs/architecture/decisions/ADR-001-single-supervisor-first.md): why the first architecture has one supervisor.
5. [Lab 001](docs/labs/lab-001-capability-registry.md): implementable scope and acceptance criteria.

## Architecture horizon

| Horizon | Components | Status |
| --- | --- | --- |
| NOW | Typed capability contracts and in-memory capability registry | Implemented in Lab 001 |
| NEXT | Theia supervisor, planning, execution loop, execution ledger | Planned experiments; no implementation authority yet |
| LATER / UNPROVEN | Worker agents, agent registry, knowledge graph, vector memory, message bus, distributed runtime | Hypotheses requiring evidence |

Git is the canonical source for project decisions and implementation contracts. Chat transcripts can inform a proposal, but must not silently become architecture. Runtime memory for Theia is a separate, deferred design question.

## Repository layout

`docs/` holds the versioned design package and lab results. `src/alaetheia/contracts.py` defines the types; `registry.py` implements compatibility and discovery; `examples.py` declares the catalog; `cli.py` and `__main__.py` expose inspection. `tests/test_lab001.py` checks library and CLI behavior.

## Working agreement

Make one bounded lab change at a time. Update the relevant design document or add an ADR when a decision changes. Explain evidence, tradeoffs, and remaining uncertainty. Run the tests appropriate to the increment. Avoid adding dependencies or infrastructure before a concrete capability requires them.

## Run Lab 001

Use Python 3.12 or newer. There are no runtime dependencies.

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -e .
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/alaetheia list
.venv/bin/alaetheia list --json
.venv/bin/alaetheia inspect terrain.slope.analyze --version 2.1.0
.venv/bin/alaetheia inspect terrain.slope.analyze --range '>=2.0.0 <3.0.0' --json
```

For offline use without installing build tooling, run `PYTHONPATH=src python3.12 -m alaetheia list` and `PYTHONPATH=src python3.12 -m unittest discover -s tests -v`.

Each CLI invocation loads a fresh explicit sample catalog: six fictional offers, with no persistence, network access, or invocation. `inspect` returns all offers for the ID and optional exact version/range. Invalid input and no matching offers exit with code 2. JSON exposes complete contracts and metadata; human output includes field types, optionality, semantics, provider identity, and metadata.

## Library example

```python
from alaetheia import Requirement, VersionRange
from alaetheia.examples import sample_registry

registry = sample_registry()
requirement = Requirement(
    'terrain.slope.analyze',
    VersionRange.parse('>=2.0.0 <3.0.0'),
)
candidates = registry.find(requirement)  # Four offers; no ranking.
first = registry.get(candidates[0].key)  # Exact provider/implementation/contract.
check = registry.compatible(requirement, first)
assert check.matches and not check.reasons
removed = registry.unregister(first.key)  # Removes only this offer.
registry.register(removed)
```

`Requirement` optionally accepts `inputs`, `outputs`, all-of `tags`, and an exact `provider_id`. Specified input schemas require exact structural equivalence. Output requirements allow extra fields: required fields must be guaranteed, and every advertised requested field must have the exact requested type. Optional requested outputs may be absent. An empty output requirement imposes no field needs; omitted schemas impose no shape check. See [ADR-002](docs/architecture/decisions/ADR-002-output-subset-compatibility.md). Discovery checks declared contract versions, not implementation versions. See [Lab 001 results](docs/labs/lab-001-results.md) for naming, version grammar, unique keys, error behavior, schema limits, and discussion questions.

## Next experiment: Lab 002

[Lab 002](docs/labs/lab-002-explicit-capability-invocation.md) is specified but not implemented: one explicitly selected local, side-effect-free invocation with payload validation and a minimal inspectable execution record. [ADR-003](docs/architecture/decisions/ADR-003-bounded-execution-lab.md) records the agreed scope. A deterministic caller precedes any planner or LLM integration; implementation awaits a separate request.
