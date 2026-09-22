"""Offline comparison against reviewed labels, never workflow execution."""
from collections.abc import Callable
from dataclasses import dataclass

from .output_values import snapshot_output
from .selection import (AbstentionProposal, CatalogEntry, ProposalCheck,
                        SelectionProposal, checked_catalog, validate_proposal)
from .selection_fixtures import Case

EVALUATION_REVISION = '1'
Selector = Callable[[str, object, tuple[CatalogEntry, ...]], object]


@dataclass(frozen=True)
class CaseResult:
    case: Case
    raw_proposal: dict[str, object] | None
    validation: ProposalCheck
    expected_selection: bool
    emitted_selection: bool
    emitted_abstention: bool
    exact_selection: bool
    exact_reason: bool
    corrections: tuple[str, ...]


@dataclass(frozen=True)
class Count:
    numerator: int
    denominator: int


@dataclass(frozen=True)
class Metrics:
    exact_selection: Count
    input_fidelity: Count
    abstention_recall: Count
    abstention_reason_accuracy: Count
    unnecessary_abstention: Count
    invalid_proposals: Count
    unknown_ids: Count
    correction_cases: Count


def evaluate(fixtures: tuple[Case, ...], catalog: tuple[CatalogEntry, ...],
             selector: Selector) -> tuple[CaseResult, ...]:
    checked_catalog(catalog)
    ids = {e.workflow_id for e in catalog}
    reasons = {'ambiguous_request', 'unsupported_request', 'insufficient_inputs'}
    if len({c.case_id for c in fixtures}) != len(fixtures):
        raise ValueError('Duplicate case ID')
    if any(c.split not in ('development', 'held-out') or c.expected not in ids | reasons for c in fixtures):
        raise ValueError('Unknown fixture split or expected label')
    results = []
    for case in fixtures:
        # Protect ground truth from a selector that mutates its input dictionary.
        case = Case(case.case_id, case.split, case.category, case.request,
                    snapshot_output(case.inputs), case.expected, case.rationale)
        raw = selector(case.request, snapshot_output(case.inputs), catalog)
        check = validate_proposal(raw, case.inputs, catalog)
        try:
            data = snapshot_output(raw)
        except ValueError:
            data = None  # Never retain or serialize an unsupported object.
        emitted_selection = data is not None and data.get('kind') == 'select'
        emitted_abstention = data is not None and data.get('kind') == 'abstain'
        expected_selection = case.expected in ids
        exact_selection = (expected_selection and emitted_selection
                           and data.get('workflow_id') == case.expected)
        exact_reason = (not expected_selection and isinstance(check.proposal, AbstentionProposal)
                        and check.proposal.reason.value == case.expected)
        corrections = []
        if expected_selection:
            if not emitted_selection:
                corrections.append('decision')
            elif not exact_selection:
                corrections.append('workflow_id')
        elif not exact_reason:
            corrections.append('decision')
        if any(d.code in ('invalid_inputs', 'changed_inputs', 'invalid_supplied_data') for d in check.diagnostics):
            corrections.append('inputs')
        if not check.valid:
            corrections.append('proposal_format')
        results.append(CaseResult(case, data, check, expected_selection, emitted_selection,
                                  emitted_abstention, exact_selection, exact_reason, tuple(corrections)))
    return tuple(results)


def metrics(results: tuple[CaseResult, ...]) -> Metrics:
    total = len(results)
    expected = sum(r.expected_selection for r in results)
    emitted = sum(r.emitted_selection for r in results)
    must_abstain = total - expected
    return Metrics(
        Count(sum(r.exact_selection for r in results), expected),
        Count(sum(isinstance(r.validation.proposal, SelectionProposal) and r.validation.valid for r in results), emitted),
        Count(sum(r.emitted_abstention and not r.expected_selection for r in results), must_abstain),
        Count(sum(r.exact_reason for r in results), must_abstain),
        Count(sum(r.emitted_abstention and r.expected_selection for r in results), expected),
        Count(sum(not r.validation.valid for r in results), total),
        Count(sum(any(d.code == 'unknown_workflow' for d in r.validation.diagnostics) for r in results), total),
        Count(sum(bool(r.corrections) for r in results), total),
    )
