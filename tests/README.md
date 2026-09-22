# Labs 001–007 behavior tests

From the repository root after installing the package:

```sh
python -m unittest discover -s tests -v
```

Without installation, use `PYTHONPATH=src python -m unittest discover -s tests -v` with Python 3.12+. CLI tests launch subprocesses with the same interpreter. Tests require only the standard library. The Lab 001 catalog contains fictional declarations. Lab 002 tests invoke only local example functions and test doubles; no external services are used.

Lab 003 tests compose pure local functions, check definition validation and failure propagation, and run both workflow demo variants. The deliberately incompatible demo exits 1 by design.

Lab 004 tests compare advisory findings with explicit local runs and distinguish missing required outputs from absent optional references, malformed values, and skipped consumers.

Lab 005 tests reuse one parcel workflow with varied records, reject invalid envelopes before calls, check domain failures and optional-input semantics, and preserve missing-output observations. All data is supplied locally.

Lab 006 tests separate expected domain rejection from exceptions and malformed output, exercise multiple typed issues, and verify fail-fast workflows without false missing-output events. The prior parcel-domain expectation is intentionally updated to domain_rejected.

Architecture consolidation adds regressions for F1–F3 and the data-only output contract, including cycles, depth, subclasses, and snapshot isolation. GitHub Actions runs the full suite on Python 3.12, 3.13, and 3.14 after package installation. It also compiles sources/tests and smoke-tests the installed CLI. Run the same suite locally with the command above; static typing is not part of these checks.

Consolidation verification: all 94 tests passed locally under Python 3.12.10 against both source and installed wheel 0.2.0. Package build/install and installed CLI smoke testing passed. The GitHub-hosted 3.13/3.14 runs await publication; YAML parsing is not a substitute for those runs. Action usage follows the official [checkout](https://github.com/actions/checkout) and [setup-python](https://github.com/actions/setup-python) documentation.

Lab 007 Phase A adds 14 tests for proposal validation, input fidelity, catalog definitions, evaluator isolation, metrics, and reproducible evidence. All 108 tests pass locally on Python 3.12.10. The separate explicit-run test checks that catalog workflows are usable; the evaluator/reporting test instruments bindings and forbids execution. Semantic fixture misses are reported as experiment results, not converted into passing expectations for the selector.
