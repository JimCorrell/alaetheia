"""Advisory workflow analysis and explicit, process-local run comparison."""
from dataclasses import dataclass
from enum import Enum

from .contracts import FieldType, Schema
from .execution import LocalExecutor, Outcome, validate_payload
from .domain import DomainIssue
from .workflow import Literal, OutputRef, StepStatus, Workflow, WorkflowInputRef, WorkflowRecord


class Severity(str, Enum):
    ERROR = 'error'
    RISK = 'risk'


@dataclass(frozen=True)
class Finding:
    severity: Severity
    code: str
    step_id: str
    message: str
    input_field: str | None = None
    source_step: str | None = None
    source_field: str | None = None


@dataclass(frozen=True)
class PreflightReport:
    workflow: Workflow
    findings: tuple[Finding, ...]

    @property
    def status(self) -> str:
        if any(f.severity == Severity.ERROR for f in self.findings):
            return 'errors'
        return 'risks' if self.findings else 'no_detected_issues'


class WorkflowPreflight:
    def __init__(self, executor: LocalExecutor) -> None:
        self._executor = executor

    def inspect(self, workflow: Workflow) -> PreflightReport:
        # Inspect every step, including steps runtime might skip. No invocation,
        # selection changes, or state mutation occurs here.
        selections = {step.step_id: self._executor.inspect_selection(step.selected_key, step.requirement)
                      for step in workflow.steps}
        findings = []
        for step in workflow.steps:
            selection = selections[step.step_id]
            for error in selection.errors:
                findings.append(Finding(Severity.ERROR, 'selection_rejected', step.step_id, error))
            if selection.offer is None:
                continue  # Missing declarations cannot support further analysis.
            inputs = {f.name: f for f in selection.offer.contract.inputs.fields}
            bound = {b.field for b in step.inputs}
            for field in sorted(inputs.values(), key=lambda f: f.name):
                if field.required and field.name not in bound:
                    findings.append(Finding(Severity.ERROR, 'missing_input', step.step_id,
                                            'Required input has no binding', field.name))
            for binding in sorted(step.inputs, key=lambda b: b.field):
                target = inputs.get(binding.field)
                if target is None:
                    findings.append(Finding(Severity.ERROR, 'unexpected_input', step.step_id,
                                            'Input is not declared by selected offer', binding.field))
                source = binding.source
                if isinstance(source, Literal):
                    if target is not None:
                        errors = validate_payload(Schema((target,)), {target.name: source.value}, allow_extra=False)
                        for error in errors:
                            findings.append(Finding(Severity.ERROR, 'invalid_literal', step.step_id,
                                                    error, binding.field))
                    continue
                if isinstance(source, WorkflowInputRef):
                    offered = next(f for f in workflow.inputs.fields if f.name == source.field)
                    source_step = None
                    optional_code = 'optional_workflow_input_absent'
                    optional_message = 'Referenced workflow input may be absent; explicit reference resolution will fail'
                else:
                    upstream = selections[source.step_id].offer
                    if upstream is None:
                        findings.append(Finding(Severity.ERROR, 'source_unavailable', step.step_id,
                                                'Source offer is unavailable', binding.field, source.step_id, source.field))
                        continue
                    offered = next((f for f in upstream.contract.outputs.fields if f.name == source.field), None)
                    source_step = source.step_id
                    optional_code = 'optional_output_absent'
                    optional_message = 'Referenced output may be absent; resolution fails even for an optional destination'
                def add(severity, code, message):
                    findings.append(Finding(severity, code, step.step_id, message,
                                            binding.field, source_step, source.field))
                if offered is None:
                    add(Severity.ERROR, 'undeclared_output', 'Reference does not name a declared provider output')
                    continue
                if not offered.required:
                    add(Severity.RISK, optional_code, optional_message)
                if target is None or offered.type == target.type:
                    continue
                if offered.type == FieldType.INTEGER and target.type == FieldType.NUMBER:
                    continue  # Every valid integer payload is accepted by NUMBER.
                if offered.type == FieldType.NUMBER and target.type == FieldType.INTEGER:
                    add(Severity.RISK, 'numeric_narrowing', 'NUMBER may return a float rejected by INTEGER')
                else:
                    add(Severity.ERROR, 'incompatible_type',
                        f'{offered.type.value} output cannot satisfy {target.type.value} input')
        return PreflightReport(workflow, tuple(findings))


@dataclass(frozen=True)
class MissingOutputEvent:
    kind: str
    producer_step: str
    field: str
    consumer_step: str | None
    input_field: str | None
    predicted_optional_risk: bool


@dataclass(frozen=True)
class RunComparison:
    preflight_status: str
    runtime_outcome: str
    failed_step: str | None
    skipped_steps: tuple[str, ...]
    missing_outputs: tuple[MissingOutputEvent, ...]
    failed_execution_outcome: str | None = None
    domain_issues: tuple[DomainIssue, ...] = ()


def compare_run(report: PreflightReport, record: WorkflowRecord) -> RunComparison:
    """Observe a completed run, without execution, persistence, or diagnostic parsing.

    A clear report is not a runtime success prediction. Optional warnings on
    skipped steps are not counted as observed missing-output failures.
    """
    if report.workflow != record.workflow:
        raise ValueError('Report and run must describe the same workflow')
    events = []
    records = {step.step_id: step for step in record.steps}
    definitions = {step.step_id: step for step in record.workflow.steps}
    for step in record.steps:
        execution = step.execution
        if execution is not None and execution.outcome == Outcome.INVALID_OUTPUT:
            for field in execution.missing_output_fields:
                events.append(MissingOutputEvent('required_output_missing', step.step_id, field, None, None, False))
        if step.status != StepStatus.FAILED or execution is not None:
            continue
        for binding in definitions[step.step_id].inputs:
            source = binding.source
            if not isinstance(source, OutputRef):
                continue
            upstream = records[source.step_id].execution
            if upstream is None or upstream.outcome != Outcome.SUCCESS:
                continue
            declared = {f.name for f in upstream.offer.contract.outputs.fields}
            if source.field in declared and source.field not in upstream.outputs:
                predicted = any(f.code == 'optional_output_absent' and f.step_id == step.step_id
                                and f.input_field == binding.field and f.source_step == source.step_id
                                and f.source_field == source.field for f in report.findings)
                events.append(MissingOutputEvent('referenced_output_absent', source.step_id, source.field,
                                                step.step_id, binding.field, predicted))
    failed = records.get(record.failed_step)
    execution = failed.execution if failed is not None else None
    return RunComparison(report.status, record.outcome.value, record.failed_step,
                         tuple(s.step_id for s in record.steps if s.status == StepStatus.SKIPPED), tuple(events),
                         execution.outcome.value if execution else None,
                         execution.domain_issues if execution else ())
