# ADR-005: Advisory preflight with runtime observation

- **Status:** Accepted for Lab 004
- **Date:** 2026-09-21

## Context

Lab 003 found that structurally valid workflows can fail at a handoff. The agreed hybrid approach adds inspection before execution while preserving runtime validation. Missing-output failures need observation so optionality policy is informed by evidence.

## Decision

Preflight is read-only and never invokes code, changes selection, blocks a run, or supplies missing values. Inspect every step against current registered offers and explicit local bindings. Reuse the executor's selection checks, exposed as `inspect_selection`, to avoid a second interpretation of binding freshness and requirement compatibility.

Report errors for missing/stale/unbound selections, incompatible requirements, required inputs without bindings, unexpected inputs, invalid literals, undeclared output references, and disjoint handoff types. Report conditional risks for optional referenced outputs and NUMBER-to-INTEGER handoffs. Exact types and INTEGER-to-NUMBER are safe under the current scalar payload validator. NUMBER-to-INTEGER is not always an error: NUMBER may return an int or a float. These rules do not relax exact requirement-to-offer input schema matching.

A referenced optional output is a risk even if its destination is optional: the current runner resolves every explicit reference and fails when absent. No omission/default/fallback policy is introduced.

A report status is `errors`, `risks`, or `no_detected_issues`, with error taking precedence. “No detected issues” is not a promise of runtime success. Findings describe declarations at inspection time, including steps that runtime may skip. A run continues to check current registry/binding state and actual values.

After an explicitly requested run, compare its record with the report for the same workflow. Track required-output contract violations separately from absent optional references. Add structured missing-output field evidence to invalid-output execution records rather than parsing diagnostic prose. Do not count skipped consumers as additional failures. Observation is process-local; no schedule, database, background service, or automatic policy change is part of this code.

## Consequences

The caller chooses whether and when to inspect and run. A report does not reserve offers, pin a registry revision, or authorize execution. Conditions may change between inspection and invocation. Runtime checks remain authoritative.

Missing required outputs cannot be predicted from an otherwise valid declaration. Optional-output warnings can materialize or remain harmless in a run. Malformed output containers and wrong/null values are distinct validation failures, not automatically classified as missing fields.

Blocking policy, defaults, optional-input omission, persistent monitoring, and a run identity/ledger remain future decisions. No Lab 005 work is authorized here.
