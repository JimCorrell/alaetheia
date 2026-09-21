# Labs 001–003 behavior tests

From the repository root after installing the package:

```sh
python -m unittest discover -s tests -v
```

Without installation, use `PYTHONPATH=src python -m unittest discover -s tests -v` with Python 3.12+. CLI tests launch subprocesses with the same interpreter. Tests require only the standard library. The Lab 001 catalog contains fictional declarations. Lab 002 tests invoke only local example functions and test doubles; no external services are used.

Lab 003 tests compose pure local functions, check definition validation and failure propagation, and run both workflow demo variants. The deliberately incompatible demo exits 1 by design.
