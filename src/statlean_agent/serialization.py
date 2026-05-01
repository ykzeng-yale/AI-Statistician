"""JSON serialization helpers for agent contracts."""

from __future__ import annotations

import json
from dataclasses import asdict, fields, is_dataclass
from enum import Enum
from pathlib import Path
from types import UnionType
from typing import Any, TypeVar, Union, get_args, get_origin, get_type_hints


T = TypeVar("T")


def to_jsonable(value: Any) -> Any:
    """Convert dataclasses, enums, tuples, and paths to JSON-compatible values."""

    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value) and not isinstance(value, type):
        return {key: to_jsonable(item) for key, item in asdict(value).items()}
    if isinstance(value, tuple | list):
        return [to_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {str(key): to_jsonable(item) for key, item in value.items()}
    if isinstance(value, Path):
        return str(value)
    return value


def dumps_json(value: Any) -> str:
    """Serialize a contract object as stable JSON."""

    return json.dumps(to_jsonable(value), sort_keys=True)


def write_jsonl(path: Path, values: list[Any]) -> None:
    """Write JSONL records."""

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for value in values:
            handle.write(dumps_json(value))
            handle.write("\n")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    """Read JSONL records as dictionaries."""

    records: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            value = json.loads(stripped)
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{line_number}: expected object")
            records.append(value)
    return records


def dataclass_from_dict(cls: type[T], data: dict[str, Any]) -> T:
    """Construct a nested dataclass from JSON-compatible data."""

    type_hints = get_type_hints(cls)
    kwargs: dict[str, Any] = {}
    for field in fields(cls):
        if field.name not in data:
            continue
        kwargs[field.name] = _coerce_value(type_hints[field.name], data[field.name])
    return cls(**kwargs)


def _coerce_value(annotation: Any, value: Any) -> Any:
    origin = get_origin(annotation)
    args = get_args(annotation)

    if origin is tuple and args:
        item_type = args[0]
        return tuple(_coerce_value(item_type, item) for item in value)

    if origin is list and args:
        item_type = args[0]
        return [_coerce_value(item_type, item) for item in value]

    if origin is dict:
        return value

    if origin is None and isinstance(annotation, type):
        if issubclass(annotation, Enum):
            return annotation(value)
        if is_dataclass(annotation):
            if not isinstance(value, dict):
                raise TypeError(f"expected object for {annotation.__name__}")
            return dataclass_from_dict(annotation, value)

    if origin in {Union, UnionType} and type(None) in args:
        non_none = [arg for arg in args if arg is not type(None)]
        if value is None or not non_none:
            return None
        return _coerce_value(non_none[0], value)

    return value
