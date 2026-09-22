"""Typed discovery contracts and bounded explicit local invocation."""
from .contracts import (CapabilityContract, CapabilityManifest, Field, FieldType,
                        Metadata, OfferKey, Requirement, Schema, Version, VersionRange)
from .registry import CapabilityRegistry, Compatibility, compatible

__all__ = ['CapabilityContract', 'CapabilityManifest', 'Field', 'FieldType',
           'Metadata', 'OfferKey', 'Requirement', 'Schema', 'Version', 'VersionRange',
           'CapabilityRegistry', 'Compatibility', 'compatible']

from .execution import ExecutionRecord, LocalBinding, LocalExecutor, Outcome, validate_payload

__all__ += ["ExecutionRecord", "LocalBinding", "LocalExecutor", "Outcome", "validate_payload"]

from .workflow import (InputBinding, Literal, OutputRef, StepRecord, StepStatus, Workflow,
                       WorkflowOutcome, WorkflowRecord, WorkflowRunner, WorkflowStep)

__all__ += ["InputBinding", "Literal", "OutputRef", "StepRecord", "StepStatus", "Workflow",
            "WorkflowOutcome", "WorkflowRecord", "WorkflowRunner", "WorkflowStep"]

from .preflight import (Finding, MissingOutputEvent, PreflightReport, RunComparison,
                        Severity, WorkflowPreflight, compare_run)

__all__ += ["Finding", "MissingOutputEvent", "PreflightReport", "RunComparison",
            "Severity", "WorkflowPreflight", "compare_run"]

from .workflow import WorkflowInputRef

__all__ += ["WorkflowInputRef"]
