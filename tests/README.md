# Labs 001–006 behavior tests

From the repository root after installing the package:

```sh
python -m unittest discover -s tests -v
```

Without installation, use `PYTHONPATH=src python -m unittest discover -s tests -v` with Python 3.12+. CLI tests launch subprocesses with the same interpreter. Tests require only the standard library. The Lab 001 catalog contains fictional declarations. Lab 002 tests invoke only local example functions and test doubles; no external services are used.

Lab 003 tests compose pure local functions, check definition validation and failure propagation, and run both workflow demo variants. The deliberately incompatible demo exits 1 by design.

Lab 004 tests compare advisory findings with explicit local runs and distinguish missing required outputs from absent optional references, malformed values, and skipped consumers.

Lab 005 tests reuse one parcel workflow with varied records, reject invalid envelopes before calls, check domain failures and optional-input semantics, and preserve missing-output observations. All data is supplied locally.

Lab 006 tests separate expected domain rejection from exceptions and malformed output, exercise multiple typed issues, and verify fail-fast workflows without false missing-output events. The prior parcel-domain expectation is intentionally updated to domain_rejected.
