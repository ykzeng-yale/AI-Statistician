from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence


@dataclass(frozen=True)
class RegisteredAlgorithmTemplate:
    template_id: str
    capability: str
    execution_owner: str
    executor: str
    tool_name: str
    match_any_terms: tuple[str, ...] = ()
    match_required_terms: tuple[str, ...] = ()
    match_required_any_terms: tuple[str, ...] = ()


REGISTERED_ALGORITHM_TEMPLATES: tuple[RegisteredAlgorithmTemplate, ...] = (
    RegisteredAlgorithmTemplate(
        template_id="crossfit_aipw",
        capability="AIPW binary-treatment ATE sandbox with stress metrics",
        execution_owner="AgentRuntime",
        executor="registered_crossfit_aipw_template",
        tool_name="python.crossfit_aipw_sandbox",
        match_any_terms=("crossfit", "aipw"),
    ),
    RegisteredAlgorithmTemplate(
        template_id="split_conformal_interval",
        capability="trusted split-conformal regression interval sandbox",
        execution_owner="AgentRuntime",
        executor="registered_split_conformal_interval_template",
        tool_name="python.split_conformal_interval_sandbox",
        match_required_terms=("conformal",),
        match_required_any_terms=("interval", "prediction", "coverage"),
    ),
)
CROSSFIT_AIPW_TEMPLATE_ID = "crossfit_aipw"
SPLIT_CONFORMAL_INTERVAL_TEMPLATE_ID = "split_conformal_interval"


def registered_algorithm_templates() -> tuple[RegisteredAlgorithmTemplate, ...]:
    return REGISTERED_ALGORITHM_TEMPLATES


def registered_algorithm_template_ids() -> tuple[str, ...]:
    return tuple(template.template_id for template in REGISTERED_ALGORITHM_TEMPLATES)


def registered_algorithm_template_hint_contract() -> str:
    return "|".join([*registered_algorithm_template_ids(), "none"])


def registered_algorithm_template_prompt_rows() -> list[dict[str, str]]:
    return [
        {
            "template_id": template.template_id,
            "capability": template.capability,
            "execution_owner": template.execution_owner,
        }
        for template in REGISTERED_ALGORITHM_TEMPLATES
    ]


def is_registered_algorithm_template_hint(template_hint: str) -> bool:
    return str(template_hint or "").strip() in registered_algorithm_template_ids()


def registered_algorithm_template_hint_from_context(
    *,
    explicit_template_hint: str = "",
    text_parts: Sequence[Any] = (),
) -> str:
    explicit = str(explicit_template_hint or "").strip()
    if explicit == "none":
        return ""
    if is_registered_algorithm_template_hint(explicit):
        return explicit
    haystack = " ".join(str(part) for part in text_parts if part is not None).lower()
    if not haystack:
        return ""
    for template in REGISTERED_ALGORITHM_TEMPLATES:
        if template.match_any_terms and any(
            term in haystack for term in template.match_any_terms
        ):
            return template.template_id
        if template.match_required_terms and not all(
            term in haystack for term in template.match_required_terms
        ):
            continue
        if template.match_required_any_terms and any(
            term in haystack for term in template.match_required_any_terms
        ):
            return template.template_id
    return ""


def registered_algorithm_template_row(template_id: str) -> Mapping[str, str]:
    for template in REGISTERED_ALGORITHM_TEMPLATES:
        if template.template_id == template_id:
            return {
                "template_id": template.template_id,
                "capability": template.capability,
                "execution_owner": template.execution_owner,
                "executor": template.executor,
                "tool_name": template.tool_name,
            }
    return {}
