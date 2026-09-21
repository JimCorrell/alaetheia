"""Declared-order workflows: explicit wiring, one invocation per step, fail fast."""
from dataclasses import dataclass
from enum import Enum
import math

from .contracts import OfferKey, Requirement, identifier
from .execution import ExecutionRecord, LocalExecutor, Outcome


@dataclass(frozen=True)
class Literal:
    value: str | int | float | bool

    def __post_init__(self) -> None:
        if type(self.value) not in (str, int, float, bool) or (
            type(self.value) is float and not math.isfinite(self.value)
        ):
            raise ValueError('Workflow literals must be finite scalar values')


@dataclass(frozen=True)
class OutputRef:
    step_id: str
    field: str

    def __post_init__(self) -> None:
        identifier(self.step_id)
        identifier(self.field)


@dataclass(frozen=True)
class InputBinding:
    field: str
    source: Literal | OutputRef

    def __post_init__(self) -> None:
        identifier(self.field)
        if not isinstance(self.source, (Literal, OutputRef)):
            raise ValueError('Input source must be a Literal or OutputRef')


@dataclass(frozen=True)
class WorkflowStep:
    step_id: str
    selected_key: OfferKey
    requirement: Requirement
    inputs: tuple[InputBinding, ...]

    def __post_init__(self) -> None:
        identifier(self.step_id)
        if not isinstance(self.selected_key, OfferKey) or not isinstance(self.requirement, Requirement):
            raise ValueError('Step needs an exact offer key and requirement')
        if not isinstance(self.inputs, tuple) or any(not isinstance(b, InputBinding) for b in self.inputs):
            raise ValueError('Step inputs must be a tuple of InputBindings')
        if len({b.field for b in self.inputs}) != len(self.inputs):
            raise ValueError('Duplicate input target field')


@dataclass(frozen=True)
class Workflow:
    workflow_id: str
    steps: tuple[WorkflowStep, ...]

    def __post_init__(self) -> None:
        identifier(self.workflow_id)
        if not isinstance(self.steps, tuple) or not self.steps or any(
            not isinstance(step, WorkflowStep) for step in self.steps
        ):
            raise ValueError('Workflow requires a nonempty tuple of steps')
        seen = set()
        for step in self.steps:
            if step.step_id in seen:
                raise ValueError(f'Duplicate step ID: {step.step_id}')
            for binding in step.inputs:
                if isinstance(binding.source, OutputRef) and binding.source.step_id not in seen:
                    raise ValueError(f'{step.step_id}: output reference must name an earlier step')
            seen.add(step.step_id)


class StepStatus(str, Enum):
    SUCCESS = 'success'
    FAILED = 'failed'
    SKIPPED = 'skipped'


class WorkflowOutcome(str, Enum):
    SUCCESS = 'success'
    FAILED = 'failed'


@dataclass(frozen=True)
class StepRecord:
    step_id: str
    status: StepStatus
    execution: ExecutionRecord | None
    errors: tuple[str, ...] = ()


@dataclass(frozen=True)
class WorkflowRecord:
    workflow: Workflow
    outcome: WorkflowOutcome
    steps: tuple[StepRecord, ...]
    failed_step: str | None


class WorkflowRunner:
    """No scheduling, ranking, expressions, retries, or persistent run state.

    Structural wiring is validated when constructing Workflow. Contract and value
    validation happens at each step via LocalExecutor, not via a new type checker.
    """
    def __init__(self, executor: LocalExecutor) -> None:
        self._executor = executor

    def run(self, workflow: Workflow) -> WorkflowRecord:
        records: list[StepRecord] = []
        successes: dict[str, ExecutionRecord] = {}
        failed_step = None
        for step in workflow.steps:
            if failed_step is not None:
                records.append(StepRecord(step.step_id, StepStatus.SKIPPED, None,
                                          (f'stopped after failed step {failed_step!r}',)))
                continue
            payload: dict[str, object] = {}
            errors = []
            for binding in step.inputs:
                source = binding.source
                if isinstance(source, Literal):
                    payload[binding.field] = source.value
                    continue
                upstream = successes[source.step_id]
                # Extra outputs are retained for inspection, but only fields in
                # the provider's contract are guaranteed to have been validated.
                declared = {field.name for field in upstream.offer.contract.outputs.fields}
                if source.field not in declared:
                    errors.append(f'{binding.field!r}: {source.step_id}.{source.field} is not a declared output')
                elif source.field not in upstream.outputs:
                    errors.append(f'{binding.field!r}: {source.step_id}.{source.field} is absent')
                else:
                    payload[binding.field] = upstream.outputs[source.field]
            if errors:
                failed_step = step.step_id
                records.append(StepRecord(step.step_id, StepStatus.FAILED, None, tuple(errors)))
                continue
            execution = self._executor.invoke(step.selected_key, step.requirement, payload)
            if execution.outcome == Outcome.SUCCESS:
                successes[step.step_id] = execution
                records.append(StepRecord(step.step_id, StepStatus.SUCCESS, execution))
            else:
                failed_step = step.step_id
                records.append(StepRecord(step.step_id, StepStatus.FAILED, execution, execution.errors))
        return WorkflowRecord(workflow, WorkflowOutcome.FAILED if failed_step else WorkflowOutcome.SUCCESS,
                              tuple(records), failed_step)
