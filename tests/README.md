# Lab 001 behavior tests

From the repository root after installing the package:

```sh
python -m unittest discover -s tests -v
```

Without installation, use `PYTHONPATH=src python -m unittest discover -s tests -v` with Python 3.12+. CLI tests launch subprocesses with the same interpreter. Tests require only the standard library. The catalog contains fictional declarations, not running providers.
