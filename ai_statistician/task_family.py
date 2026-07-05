from __future__ import annotations

from typing import Any, Mapping


NON_EVIDENCE_TASK_FAMILY_LABELS = {
    "none",
    "null",
    "unknown",
    "unclassified",
    "unclassified_task_family",
}
TASK_FAMILY_TAG_PREFIXES = ("task_family:", "task-family:")
TASK_FAMILY_FIELD_CANDIDATES = (
    "primary_task_family",
    "task_family",
    "problem_family",
    "question_family",
    "benchmark_family",
    "estimator_family",
    "dgp_family",
    "problem_class",
    "topic",
)
CROSS_TASK_GENERALIZATION_DEFAULT_FAMILIES = (
    "experimental_design",
    "multiple_testing",
    "causal",
)


def compact_string_list(values: Any) -> list[str]:
    if values is None:
        return []
    if isinstance(values, (str, int, float, bool)):
        raw_values = [values]
    elif isinstance(values, Mapping):
        raw_values = values.values()
    else:
        try:
            raw_values = list(values)
        except TypeError:
            raw_values = [values]
    compacted: list[str] = []
    for value in raw_values:
        text = str(value or "").strip()
        if text:
            compacted.append(text)
    return list(dict.fromkeys(compacted))


def task_family_value(value: Any) -> str:
    text = str(value or "").strip()
    lowered = text.lower()
    for prefix in TASK_FAMILY_TAG_PREFIXES:
        if lowered.startswith(prefix):
            return text[len(prefix) :].strip()
    return text


def is_explicit_task_family(value: Any) -> bool:
    text = task_family_value(value)
    lowered = text.lower()
    return bool(
        text
        and lowered not in NON_EVIDENCE_TASK_FAMILY_LABELS
        and not lowered.startswith("question_id:")
    )


def explicit_task_family_list(values: Any) -> list[str]:
    return [
        task_family_value(value)
        for value in compact_string_list(values)
        if is_explicit_task_family(value)
    ]


def cross_task_generalization_family_pair(values: Any) -> tuple[str, str]:
    families: list[str] = []
    for family in [
        *explicit_task_family_list(values),
        *CROSS_TASK_GENERALIZATION_DEFAULT_FAMILIES,
    ]:
        if is_explicit_task_family(family) and family not in families:
            families.append(family)
        if len(families) >= 2:
            break
    return families[0], families[1]


def task_family_from_tags(tags: Any) -> str:
    for tag in compact_string_list(tags):
        value = task_family_value(tag)
        if value != tag and is_explicit_task_family(value):
            return value
    return ""


def primary_task_family_from_question(question: Any) -> str:
    tag_family = task_family_from_tags(getattr(question, "tags", ()))
    if tag_family:
        return tag_family
    for attr in TASK_FAMILY_FIELD_CANDIDATES:
        value = task_family_value(getattr(question, attr, "") or "")
        if is_explicit_task_family(value):
            return value
    tags = compact_string_list(getattr(question, "tags", ()))
    return task_family_value(tags[0]) if tags else "unclassified"


def primary_task_family_from_mapping(payload: Mapping[str, Any]) -> str:
    tag_family = task_family_from_tags(payload.get("tags", []))
    if tag_family:
        return tag_family
    for key in TASK_FAMILY_FIELD_CANDIDATES:
        value = task_family_value(payload.get(key, "") or "")
        if value:
            return value
    for nested_key in ("question", "source_question", "problem"):
        nested = payload.get(nested_key)
        if isinstance(nested, Mapping):
            family = primary_task_family_from_mapping(nested)
            if family:
                return family
    tags = compact_string_list(payload.get("tags", []))
    return task_family_value(tags[0]) if tags else ""
