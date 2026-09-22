# Alaetheia

Alaetheia ("Theia") is an experimental personal supervisor for turning a goal into an inspectable sequence of capability discovery, planning, execution, observation, and evidence-backed results. This repository is also a learning laboratory: each increment should expose the mechanism being studied instead of hiding it behind an agent framework.

The first architectural hypothesis is **one reasoning supervisor with a registry of explicit capabilities**. Another agent is warranted only when an independently reasoning unit improves a measured outcome enough to justify its extra authority, cost, and complexity. There are no worker agents in the initial build.

## Current state

Start with the [current architecture and public contract](docs/architecture/current.md), including the supported output values, outcome model, and CI targets. Historical lab sections below explain how the design evolved.

Lab 001 is implemented: immutable typed capability declarations, an in-memory registry, deterministic compatibility/discovery, and a sample-catalog inspection CLI. Lab 002 adds explicit invocation of trusted, pure local examples with payload validation and an inspectable record. Lab 003 composes explicit invocations into sequential workflows with data dependencies and fail-fast records. Lab 004 adds advisory preflight and missing-output comparisons without changing runtime enforcement. Lab 005 adds typed workflow inputs and reuse across supplied parcel records. Lab 006 distinguishes expected domain rejection from provider exceptions. The catalog inspection CLI still executes nothing. See the [Lab 001 specification](docs/labs/lab-001-capability-registry.md) and [experiment results and open questions](docs/labs/lab-001-results.md).

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
| NOW | Explicit local invocation and process-local outcome record | Implemented in Lab 002 |
| NOW | Sequential workflows with explicit wiring and fail-fast records | Implemented in Lab 003 |
| NOW | Advisory workflow preflight and run comparisons | Implemented in Lab 004 |
| NOW | Typed workflow inputs and reusable local workflows | Implemented in Lab 005 |
| NOW | Structured domain rejection results | Implemented in Lab 006 |
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

## Run Lab 002

[Lab 002](docs/labs/lab-002-explicit-capability-invocation.md) implements one explicitly selected local invocation. [ADR-003](docs/architecture/decisions/ADR-003-bounded-execution-lab.md) records its scope; [results and design choices](docs/labs/lab-002-results.md) explain validation, binding lifecycle, record contents, and open questions.

```sh
.venv/bin/python -m alaetheia.invocation_example
.venv/bin/python -m unittest discover -s tests -v
```

The example uses two side-effect-free character-count functions and explicitly selects `local-python/iterated`. It prints a successful record with `count: 5` and the extra `method: iteration` field. `execution.py` contains the invocation boundary; `invocation_example.py` is the deterministic caller; `tests/test_lab002.py` covers its behavior. No changes to the Lab 001 CLI commands are required.

```python
from alaetheia.invocation_example import example

registry, executor, requirement, selected_key = example()
record = executor.invoke(selected_key, requirement, {'text': 'Theia'})
print(record.outcome.value, record.outputs)
```

The outcome is `success`, `selection_rejected`, `invalid_input`, `domain_rejected`, `provider_failure`, or `invalid_output`. Discovery never selects an implementation automatically. Bindings refer to exact manifests and must be rebuilt after an implementation replacement. Input fields are closed; additional outputs are retained. Optional fields may be absent but may not be `None`. See the results document for precise scalar rules and limitations.

## Run Lab 003

[Lab 003](docs/labs/lab-003-deterministic-workflow.md) composes invocations without a planner. [ADR-004](docs/architecture/decisions/ADR-004-sequential-workflows.md) records the decisions; [results](docs/labs/lab-003-results.md) explain the behavior and open questions.

```sh
.venv/bin/python -m alaetheia.workflow_example
.venv/bin/python -m alaetheia.workflow_example --incompatible
.venv/bin/python -m unittest discover -s tests -v
```

The first example strips text, counts characters, and formats `Characters: 5`, exiting 0. The deliberately incompatible variant fails the second step's input validation, skips the third, and exits 1. Both print a workflow record containing the definition and ordered step outcomes.

```python
from alaetheia import InputBinding, Literal, OutputRef, Workflow, WorkflowRunner, WorkflowStep

# Given a LocalExecutor and exact keys/requirements for two local offers:
workflow = Workflow('two-counts', (
    WorkflowStep('first', selected_key, requirement,
                 (InputBinding('text', Literal('Theia')),)),
    WorkflowStep('second', other_key, other_requirement,
                 (InputBinding('count', OutputRef('first', 'count')),)),
))
record = WorkflowRunner(executor).run(workflow)
```

For a fully wired runnable example, use `example()` in `alaetheia.workflow_example`. Only earlier declared output fields can be referenced. Missing referenced values fail the step; no defaults or implicit forwarding occur. All later steps are skipped after the first failure. Inputs and outputs still pass through the Lab 002 validator. `workflow.py` contains the types and runner; `tests/test_lab003.py` covers composition and failure propagation.

## Run Lab 004

[Lab 004](docs/labs/lab-004-workflow-preflight.md) adds a read-only report; [ADR-005](docs/architecture/decisions/ADR-005-advisory-workflow-preflight.md) defines the hybrid approach. [Results](docs/labs/lab-004-results.md) record observed missing-output failures and remaining questions.

```sh
.venv/bin/python -m alaetheia.preflight_example
.venv/bin/python -m unittest discover -s tests -v
```

The demo compares optional-present, optional-absent, and required-absent scenarios. It exits 0 after displaying the expected success and failure records. Inspection never invokes providers and does not block execution.

```python
from alaetheia import WorkflowPreflight, WorkflowRunner, compare_run
from alaetheia.preflight_example import scenario

executor, workflow = scenario(optional=True, omit=True)
report = WorkflowPreflight(executor).inspect(workflow)
record = WorkflowRunner(executor).run(workflow)  # Explicit, separate execution.
observation = compare_run(report, record)
print(report.status, observation.missing_outputs)
```

Reports classify errors and conditional risks, including optional references even when the destination is optional. A clean report does not promise success. Run comparisons identify missing fields without parsing diagnostic text. Monitoring is per explicit run; no background schedule or persistent history is installed.

## Run Lab 005

[Lab 005](docs/labs/lab-005-reusable-workflows.md) gives workflows a reusable input contract. [ADR-006](docs/architecture/decisions/ADR-006-reusable-workflow-inputs.md) records the boundary; [results](docs/labs/lab-005-results.md) describe domain validation, input failures, and missing-output observations.

```sh
.venv/bin/python -m alaetheia.parcel_example
.venv/bin/python -m unittest discover -s tests -v
```

The five-case demo prints successes, a rejected input envelope, and a domain-validation failure. It exits 0 when the demonstration completes; intentional failed cases remain visible in their records.

```python
from alaetheia import WorkflowPreflight, WorkflowRunner, compare_run
from alaetheia.parcel_example import example

executor, workflow = example()
report = WorkflowPreflight(executor).inspect(workflow)
record = WorkflowRunner(executor).run(workflow, {
    'parcel_id': 'P-101', 'municipality': 'Example Town',
    'acreage': 12.5, 'road_access': True,
})
print(record.steps[-1].execution.outputs)
print(compare_run(report, record))
```

Supply new records to the same definition for subsequent runs. `WorkflowInputRef('acreage')` names a declared workflow input; step bindings choose their destination field explicitly. Inputs are validated before any provider runs. Invalid envelopes return workflow outcome `invalid_input` with `record.errors` and every step skipped. Optional fields may be absent, but explicit references to absent values still fail without defaults. Older literal-only workflows continue to run with omitted inputs.

The example summarizes supplied facts only. Its parcel identifiers and road-access flag are not verified against external sources. Monitoring remains per explicit run, and preflight remains advisory.

## Lab 006: Structured domain rejection

[ADR-007](docs/architecture/decisions/ADR-007-structured-domain-rejections.md), the [lab brief](docs/labs/lab-006-domain-validation.md), and [results](docs/labs/lab-006-results.md) document the distinction between expected domain rejection and provider exceptions.

```python
from alaetheia import DomainIssue, DomainRejection

# A local provider can return this instead of its normal success dictionary:
rejection = DomainRejection((
    DomainIssue('nonpositive_acreage', 'Acreage must be positive', 'acreage'),
))
```

Run `.venv/bin/python -m alaetheia.parcel_example` to see structured issues for the negative-acreage case. The validator now uses contract 2.0.0. Its step outcome is `domain_rejected`; the workflow still stops and skips summary. ExecutionRecord exposes `domain_issues`, and run comparisons expose both `failed_execution_outcome` and `domain_issues`. Expected rejection creates no missing-output event.

Successful dictionary outputs still undergo full schema validation. Exceptions remain `provider_failure`, even if their message describes bad data. Rejection issue fields must name declared provider inputs or be `None` for record-level issues. No automatic repair, defaults, or retry is performed.

## Architecture consolidation

Library 0.2.0 fixes the three [review findings](docs/architecture/reviews/2026-09-22-architecture-review.md). Successful outputs now contain only supported builtin data values; custom copy hooks are never invoked. See [ADR-008](docs/architecture/decisions/ADR-008-output-data-and-review-hardening.md) for the compatibility change. [CI](.github/workflows/tests.yml) installs the package and runs the full suite, compilation, and CLI smoke test on Python 3.12–3.14 for pushes and PRs. No model integration or next lab is included.
