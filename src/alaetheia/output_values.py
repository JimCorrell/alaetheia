"""Snapshot inert output data without invoking user-defined copy/encoding hooks."""
import math

MAX_OUTPUT_DEPTH = 64


def snapshot_output(value: object) -> dict[str, object]:
    """Accept a plain string-keyed dict of data values; see current architecture.

    Nested values may be None, exact builtin scalars, lists, or string-keyed
    dictionaries. Reject subclasses, custom objects, nonfinite floats, cycles,
    and nesting beyond 64 container levels. Shared acyclic containers are copied
    independently; no mutable provider container is retained.
    """
    if type(value) is not dict:
        raise ValueError('output must be a plain dictionary')
    active: set[int] = set()

    def copy_data(item: object, depth: int) -> object:
        if item is None or type(item) in (str, bool, int):
            return item
        if type(item) is float:
            if not math.isfinite(item):
                raise ValueError('output contains a nonfinite float')
            return item
        if type(item) not in (list, dict):
            raise ValueError('output contains an unsupported value; only builtin data values are allowed')
        if depth >= MAX_OUTPUT_DEPTH:
            raise ValueError('output exceeds 64 container levels')
        if id(item) in active:
            raise ValueError('output contains a container cycle')
        active.add(id(item))
        try:
            if type(item) is list:
                return [copy_data(child, depth + 1) for child in item]
            result = {}
            for key, child in item.items():
                if type(key) is not str:
                    raise ValueError('output dictionary keys must be plain strings')
                result[key] = copy_data(child, depth + 1)
            return result
        finally:
            active.remove(id(item))

    return copy_data(value, 0)
