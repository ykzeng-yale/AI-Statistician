from __future__ import annotations

import asyncio
from functools import lru_cache
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from .fingerprint import stable_hash
from .proof_audit import audit_proof_bank
from .proof_bank import FORMAL_OBLIGATIONS
from .task_family import compact_string_list, primary_task_family_from_mapping
from .verifier import LocalLeanProofVerifier


ARTIFACT_KIND = "SourceTheoremSemanticPrimitiveProofEngineerBridgeManifest"
BOUNDARY = (
    "Source-theorem semantic primitive ProofEngineer bridge rows are proof-task "
    "routing and registered-obligation support checks. They are not proof evidence "
    "unless the referenced proof_audit_manifest contains kernel_verified=true rows. "
    "Even kernel-verified registered semantic bridges do not by themselves prove the "
    "full source theorem or unformalized upstream statistical semantics."
)
SEMANTIC_SUPPORT_ONLY_STATUS = (
    "REGISTERED_SUPPORT_VERIFIED_PLACEHOLDER_DEFINITION_OPEN"
)
PLACEHOLDER_DEFINITION_OPEN_STATUS = (
    "OPEN_REQUIRES_REVIEWED_FORMAL_DEFINITION"
)
SOURCE_TO_BRIDGE_ADAPTER_INSTANTIATION_EXACT_GOAL_SHAPE_ROUTE = (
    "source_to_bridge_adapter_instantiation"
)
DEFAULT_SEMANTIC_SUPPORT_POLICY_PATH = (
    Path(__file__).resolve().parent
    / "policies"
    / "source_theorem_semantic_primitive_support.split_conformal.json"
)
_SOURCE_TO_BRIDGE_PREMISE_CONTEXT_KEYS = (
    "premise_name",
    "premise_target_status",
    "premise_target_matched_binder",
    "premise_target_type",
    "premise_derivation_gap_kind",
    "premise_derivation_gap_summary",
    "premise_semantic_dependency_status",
    "semantic_anchor_reference_gate",
)
_SOURCE_TO_BRIDGE_PREMISE_CONTEXT_LIST_KEYS = (
    "source_theorem_signature_excerpt",
    "adapter_signature_excerpt",
    "premise_semantic_dependency_requirements",
    "exact_source_theorem_binders",
    "premise_semantic_anchor_binders",
    "premise_semantic_anchor_binder_names",
    "required_semantic_anchor_reference_names",
    "missing_premise_semantic_anchor_binder_names",
    "recommended_repair_tasks",
)


def _bool_like(value: Any, *, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "y", "on"}:
            return True
        if normalized in {"0", "false", "no", "n", "off", ""}:
            return False
        return default
    if isinstance(value, (int, float)):
        return value != 0
    return bool(value)


@lru_cache(maxsize=8)
def _semantic_support_policy(policy_path: str = "") -> dict[str, Any]:
    path = Path(policy_path) if policy_path else DEFAULT_SEMANTIC_SUPPORT_POLICY_PATH
    payload = json.loads(path.read_text(encoding="utf-8"))
    scope = str(payload.get("scope", "") or "").strip()
    scope_task_family = (
        scope.split(":", 1)[1].strip()
        if scope.lower().startswith("task_family:") and ":" in scope
        else ""
    )
    task_families = _normalize_policy_selector_values(
        [*compact_string_list(payload.get("task_families", [])), scope_task_family]
    )
    question_ids = _normalize_policy_selector_values(
        payload.get("question_ids", [])
    )
    theorem_target_ids = _normalize_policy_selector_values(
        payload.get("theorem_target_ids", [])
    )
    primitive_support = _normalize_policy_support_map(
        payload.get("primitive_to_registered_support", {})
    )
    primitive_text_support = _normalize_semantic_primitive_text_support_rules(
        payload.get("semantic_primitive_text_to_registered_support", [])
    )
    exact_goal_shape_support = _normalize_policy_support_map(
        payload.get("exact_goal_shape_to_registered_support", {})
    )
    placeholder_support = _normalize_policy_support_map(
        payload.get("placeholder_symbol_to_registered_support", {})
    )
    placeholder_primitive_ids = _normalize_policy_string_map(
        payload.get("placeholder_symbol_to_semantic_primitive_id", {})
    )
    placeholder_semantic_gaps = _normalize_policy_string_map(
        payload.get("placeholder_symbol_to_semantic_gap", {})
    )
    placeholder_text_signals = _normalize_placeholder_text_signal_map(
        payload.get("placeholder_symbol_text_signals", {})
    )
    semantic_primitive_id_text_rules = _normalize_semantic_primitive_id_text_rules(
        payload.get("semantic_primitive_id_text_rules", [])
    )
    theorem_closure_strategies = _normalize_theorem_closure_reduction_strategies(
        payload.get("theorem_closure_reduction_strategies", {})
    )
    exact_goal_shape_semantic_gaps = _normalize_policy_string_map(
        payload.get("exact_goal_shape_to_semantic_gap", {})
    )
    exact_goal_shape_obligation_routes = (
        _normalize_exact_goal_shape_obligation_routes(
            payload.get("exact_goal_shape_obligation_routes", {})
        )
    )
    exact_goal_shape_inference_rules = (
        _normalize_exact_goal_shape_obligation_inference_rules(
            payload.get("exact_goal_shape_obligation_inference_rules", [])
        )
    )
    exact_goal_shape_feedback_rules = (
        _normalize_exact_goal_shape_obligation_feedback_rules(
            payload.get("exact_goal_shape_obligation_feedback_rules", [])
        )
    )
    return {
        "policy_id": str(payload.get("policy_id", path.stem) or path.stem),
        "schema_version": int(payload.get("schema_version", 1) or 1),
        "scope": scope,
        "path": str(path),
        "task_families": task_families,
        "question_ids": question_ids,
        "theorem_target_ids": theorem_target_ids,
        "primitive_to_registered_support": primitive_support,
        "semantic_primitive_text_to_registered_support": primitive_text_support,
        "placeholder_symbol_to_registered_support": placeholder_support,
        "placeholder_symbol_to_semantic_primitive_id": placeholder_primitive_ids,
        "placeholder_symbol_to_semantic_gap": placeholder_semantic_gaps,
        "placeholder_symbol_text_signals": placeholder_text_signals,
        "semantic_primitive_id_text_rules": semantic_primitive_id_text_rules,
        "theorem_closure_reduction_strategies": theorem_closure_strategies,
        "exact_goal_shape_to_registered_support": exact_goal_shape_support,
        "exact_goal_shape_to_semantic_gap": exact_goal_shape_semantic_gaps,
        "exact_goal_shape_obligation_routes": exact_goal_shape_obligation_routes,
        "exact_goal_shape_obligation_inference_rules": (
            exact_goal_shape_inference_rules
        ),
        "exact_goal_shape_obligation_feedback_rules": (
            exact_goal_shape_feedback_rules
        ),
    }


def _normalize_policy_selector_values(value: Any) -> tuple[str, ...]:
    return tuple(
        dict.fromkeys(
            text.strip()
            for text in compact_string_list(value)
            if text.strip()
        )
    )


def _normalize_policy_support_map(value: Any) -> dict[str, tuple[str, ...]]:
    if not isinstance(value, Mapping):
        return {}
    rows: dict[str, tuple[str, ...]] = {}
    for key, raw_items in value.items():
        item_key = str(key).strip()
        if not item_key:
            continue
        rows[item_key] = tuple(
            dict.fromkeys(
                str(item).strip()
                for item in raw_items or []
                if str(item).strip()
            )
        )
    return rows


def _normalize_semantic_primitive_text_support_rules(
    value: Any,
) -> tuple[dict[str, tuple[str, ...]], ...]:
    if not isinstance(value, (list, tuple)):
        return ()
    normalized: list[dict[str, tuple[str, ...]]] = []
    for raw_rule in value:
        if not isinstance(raw_rule, Mapping):
            continue
        registered_support_ids = tuple(
            dict.fromkeys(
                str(item).strip()
                for item in raw_rule.get("registered_support_ids", []) or []
                if str(item).strip()
            )
        )
        text_contains_any = tuple(
            dict.fromkeys(
                str(item).strip().lower()
                for item in raw_rule.get("work_order_text_contains_any", []) or []
                if str(item).strip()
            )
        )
        text_contains_all = tuple(
            dict.fromkeys(
                str(item).strip().lower()
                for item in raw_rule.get("work_order_text_contains_all", []) or []
                if str(item).strip()
            )
        )
        primitive_id_contains_any = tuple(
            dict.fromkeys(
                str(item).strip().lower()
                for item in raw_rule.get("semantic_primitive_id_contains_any", [])
                or []
                if str(item).strip()
            )
        )
        primitive_id_contains_all = tuple(
            dict.fromkeys(
                str(item).strip().lower()
                for item in raw_rule.get("semantic_primitive_id_contains_all", [])
                or []
                if str(item).strip()
            )
        )
        if registered_support_ids and (
            text_contains_any
            or text_contains_all
            or primitive_id_contains_any
            or primitive_id_contains_all
        ):
            normalized.append(
                {
                    "registered_support_ids": registered_support_ids,
                    "work_order_text_contains_any": text_contains_any,
                    "work_order_text_contains_all": text_contains_all,
                    "semantic_primitive_id_contains_any": primitive_id_contains_any,
                    "semantic_primitive_id_contains_all": primitive_id_contains_all,
                }
            )
    return tuple(normalized)


def _normalize_policy_string_map(value: Any) -> dict[str, str]:
    if not isinstance(value, Mapping):
        return {}
    normalized: dict[str, str] = {}
    for key, raw_value in value.items():
        item_key = str(key).strip()
        item_value = str(raw_value or "").strip()
        if item_key and item_value:
            normalized[item_key] = item_value
    return normalized


def _normalize_exact_goal_shape_obligation_routes(
    value: Any,
) -> dict[str, tuple[str, ...]]:
    if not isinstance(value, Mapping):
        return {}
    normalized: dict[str, tuple[str, ...]] = {}
    for route, raw_items in value.items():
        route_id = str(route).strip()
        if not route_id:
            continue
        items = (raw_items,) if isinstance(raw_items, str) else raw_items or []
        normalized[route_id] = tuple(
            dict.fromkeys(
                str(item).strip()
                for item in items
                if str(item).strip()
            )
        )
    return normalized


def _normalize_semantic_primitive_id_text_rules(
    value: Any,
) -> tuple[dict[str, Any], ...]:
    if not isinstance(value, (list, tuple)):
        return ()
    normalized: list[dict[str, Any]] = []
    for raw_rule in value:
        if not isinstance(raw_rule, Mapping):
            continue
        primitive_id = str(
            raw_rule.get("semantic_primitive_id", "")
            or raw_rule.get("primitive_id", "")
            or ""
        ).strip()
        if not primitive_id:
            continue
        patterns: list[tuple[str, ...]] = []
        for raw_pattern in raw_rule.get("contains_all_any", []) or []:
            if isinstance(raw_pattern, str):
                terms = (raw_pattern.strip().lower(),)
            else:
                terms = tuple(
                    dict.fromkeys(
                        str(term).strip().lower()
                        for term in raw_pattern or []
                        if str(term).strip()
                    )
                )
            if terms:
                patterns.append(terms)
        contains_all = tuple(
            dict.fromkeys(
                str(term).strip().lower()
                for term in raw_rule.get("contains_all", []) or []
                if str(term).strip()
            )
        )
        if contains_all:
            patterns.append(contains_all)
        for term in raw_rule.get("contains_any", []) or []:
            normalized_term = str(term).strip().lower()
            if normalized_term:
                patterns.append((normalized_term,))
        if patterns:
            normalized.append(
                {
                    "semantic_primitive_id": primitive_id,
                    "contains_all_any": tuple(patterns),
                }
            )
    return tuple(normalized)


def _normalize_exact_goal_shape_obligation_inference_rules(
    value: Any,
) -> tuple[dict[str, tuple[str, ...]], ...]:
    if not isinstance(value, (list, tuple)):
        return ()
    normalized: list[dict[str, tuple[str, ...]]] = []
    for raw_rule in value:
        if not isinstance(raw_rule, Mapping):
            continue
        failure_classifications = tuple(
            dict.fromkeys(
                str(item).strip()
                for item in raw_rule.get("failure_classifications", []) or []
                if str(item).strip()
            )
        )
        triggers = tuple(
            dict.fromkeys(
                str(item).strip()
                for item in raw_rule.get("triggers", []) or []
                if str(item).strip()
            )
        )
        obligation_ids = tuple(
            dict.fromkeys(
                str(item).strip()
                for item in raw_rule.get("obligation_ids", []) or []
                if str(item).strip()
            )
        )
        if obligation_ids and (failure_classifications or triggers):
            normalized.append(
                {
                    "failure_classifications": failure_classifications,
                    "triggers": triggers,
                    "obligation_ids": obligation_ids,
                }
            )
    return tuple(normalized)


def _normalize_exact_goal_shape_obligation_feedback_rules(
    value: Any,
) -> tuple[dict[str, Any], ...]:
    if not isinstance(value, (list, tuple)):
        return ()
    normalized: list[dict[str, Any]] = []
    for raw_rule in value:
        if not isinstance(raw_rule, Mapping):
            continue
        obligation_id = str(raw_rule.get("obligation_id", "") or "").strip()
        if not obligation_id:
            continue
        failure_classifications = tuple(
            dict.fromkeys(
                str(item).strip()
                for item in raw_rule.get("failure_classifications", []) or []
                if str(item).strip()
            )
        )
        triggers = tuple(
            dict.fromkeys(
                str(item).strip()
                for item in raw_rule.get("triggers", []) or []
                if str(item).strip()
            )
        )
        goal_text_contains_any = tuple(
            dict.fromkeys(
                str(item)
                for item in raw_rule.get("goal_text_contains_any", []) or []
                if str(item)
            )
        )
        goal_text_contains_all = tuple(
            dict.fromkeys(
                str(item)
                for item in raw_rule.get("goal_text_contains_all", []) or []
                if str(item)
            )
        )
        if (
            failure_classifications
            or triggers
            or goal_text_contains_any
            or goal_text_contains_all
        ):
            normalized.append(
                {
                    "obligation_id": obligation_id,
                    "failure_classifications": failure_classifications,
                    "triggers": triggers,
                    "goal_text_contains_any": goal_text_contains_any,
                    "goal_text_contains_all": goal_text_contains_all,
                    "case_sensitive_goal_text": _bool_like(
                        raw_rule.get("case_sensitive_goal_text", True),
                        default=True,
                    ),
                }
            )
    return tuple(normalized)


def _normalize_placeholder_text_signal_map(
    value: Any,
) -> dict[str, dict[str, tuple[str, ...]]]:
    if not isinstance(value, Mapping):
        return {}
    normalized: dict[str, dict[str, tuple[str, ...]]] = {}
    for symbol, raw_signals in value.items():
        placeholder_symbol = str(symbol).strip()
        if not placeholder_symbol or not isinstance(raw_signals, Mapping):
            continue
        signal_row: dict[str, tuple[str, ...]] = {}
        for key, raw_items in raw_signals.items():
            signal_key = str(key).strip()
            if not signal_key:
                continue
            signal_row[signal_key] = tuple(
                dict.fromkeys(
                    str(item).strip()
                    for item in raw_items or []
                    if str(item).strip()
                )
            )
        if signal_row:
            normalized[placeholder_symbol] = signal_row
    return normalized


def _normalize_theorem_closure_reduction_strategies(
    value: Any,
) -> dict[str, tuple[dict[str, str], ...]]:
    if not isinstance(value, Mapping):
        return {}
    normalized: dict[str, tuple[dict[str, str], ...]] = {}
    required_keys = (
        "proof_obligation_id",
        "source_theorem_name",
        "closure_theorem_name",
        "reduction_description",
    )
    for goal_id, raw_strategies in value.items():
        normalized_goal_id = str(goal_id).strip()
        if not normalized_goal_id:
            continue
        strategies: list[dict[str, str]] = []
        for raw_strategy in raw_strategies or []:
            if not isinstance(raw_strategy, Mapping):
                continue
            strategy = {
                key: str(raw_strategy.get(key, "") or "").strip()
                for key in required_keys
            }
            if all(strategy.values()):
                strategies.append(strategy)
        if strategies:
            normalized[normalized_goal_id] = tuple(strategies)
    return normalized


def _semantic_support_policy_summary() -> dict[str, Any]:
    policy = _semantic_support_policy()
    primitive_support = policy["primitive_to_registered_support"]
    primitive_text_support = policy["semantic_primitive_text_to_registered_support"]
    semantic_primitive_id_text_rules = policy["semantic_primitive_id_text_rules"]
    placeholder_support = policy["placeholder_symbol_to_registered_support"]
    placeholder_primitive_ids = policy[
        "placeholder_symbol_to_semantic_primitive_id"
    ]
    placeholder_semantic_gaps = policy["placeholder_symbol_to_semantic_gap"]
    placeholder_text_signals = policy["placeholder_symbol_text_signals"]
    theorem_closure_strategies = policy["theorem_closure_reduction_strategies"]
    exact_goal_shape_support = policy["exact_goal_shape_to_registered_support"]
    exact_goal_shape_semantic_gaps = policy["exact_goal_shape_to_semantic_gap"]
    exact_goal_shape_inference_rules = policy[
        "exact_goal_shape_obligation_inference_rules"
    ]
    exact_goal_shape_feedback_rules = policy[
        "exact_goal_shape_obligation_feedback_rules"
    ]
    exact_goal_shape_obligation_routes = policy[
        "exact_goal_shape_obligation_routes"
    ]
    return {
        "policy_id": policy["policy_id"],
        "schema_version": policy["schema_version"],
        "scope": policy["scope"],
        "path": policy["path"],
        "task_families": list(policy["task_families"]),
        "question_ids": list(policy["question_ids"]),
        "theorem_target_ids": list(policy["theorem_target_ids"]),
        "n_primitive_support_routes": len(primitive_support),
        "n_semantic_primitive_text_support_routes": len(primitive_text_support),
        "n_semantic_primitive_id_text_rules": len(semantic_primitive_id_text_rules),
        "n_placeholder_symbol_support_routes": len(placeholder_support),
        "n_placeholder_symbol_primitive_id_routes": len(placeholder_primitive_ids),
        "n_placeholder_symbol_semantic_gap_routes": len(placeholder_semantic_gaps),
        "n_placeholder_symbol_text_signal_routes": len(placeholder_text_signals),
        "n_theorem_closure_reduction_goal_routes": len(theorem_closure_strategies),
        "n_exact_goal_shape_support_routes": len(exact_goal_shape_support),
        "n_exact_goal_shape_semantic_gap_routes": len(
            exact_goal_shape_semantic_gaps
        ),
        "n_exact_goal_shape_obligation_route_groups": len(
            exact_goal_shape_obligation_routes
        ),
        "n_exact_goal_shape_obligation_inference_rules": len(
            exact_goal_shape_inference_rules
        ),
        "n_exact_goal_shape_obligation_feedback_rules": len(
            exact_goal_shape_feedback_rules
        ),
        "boundary": (
            "Semantic-support policy routes task-family primitive IDs, placeholder "
            "signals, exact goal-shape inference/feedback/queue routing, and "
            "theorem-closure strategies to registered support obligations. It is "
            "routing metadata only; proof evidence still requires "
            "kernel_verified=true rows in the proof audit manifest."
        ),
    }


def _semantic_support_policy_applicability(
    policy: Mapping[str, Any],
    row: Mapping[str, Any],
    *,
    fallback_question_id: str = "",
) -> dict[str, Any]:
    policy_selectors = {
        "task_family": {
            str(value).strip().lower()
            for value in policy.get("task_families", ()) or ()
            if str(value).strip()
        },
        "question_id": {
            str(value).strip().lower()
            for value in policy.get("question_ids", ()) or ()
            if str(value).strip()
        },
        "theorem_target_id": {
            str(value).strip().lower()
            for value in policy.get("theorem_target_ids", ()) or ()
            if str(value).strip()
        },
    }
    row_task_family = str(
        row.get("task_family", "")
        or row.get("primary_task_family", "")
        or primary_task_family_from_mapping(row)
        or ""
    ).strip()
    explicit_row_question_ids = {
        str(value).strip().lower()
        for value in compact_string_list(row.get("question_id", ""))
        if str(value).strip()
    }
    fallback_question = str(fallback_question_id).strip().lower()
    row_question_ids = explicit_row_question_ids or (
        {fallback_question} if fallback_question else set()
    )
    provenance = (
        row.get("source_theorem_target_provenance", {})
        if isinstance(row.get("source_theorem_target_provenance", {}), Mapping)
        else {}
    )
    row_theorem_target_ids = {
        str(value).strip().lower()
        for value in [
            *compact_string_list(row.get("target_theorem_goal_ids", [])),
            *compact_string_list(row.get("source_formal_target_ids", [])),
            str(row.get("target_theorem_name", "") or ""),
            str(row.get("source_theorem_id", "") or ""),
            str(row.get("source_theorem_goal_id", "") or ""),
            str(provenance.get("target_lean_declaration", "") or ""),
            str(provenance.get("source_theorem_goal_id", "") or ""),
        ]
        if str(value).strip()
    }
    row_selectors = {
        "task_family": {row_task_family.lower()} if row_task_family else set(),
        "question_id": row_question_ids,
        "theorem_target_id": row_theorem_target_ids,
    }
    matched_selector_kinds: list[str] = []
    conflicting_selector_kinds: list[str] = []
    for selector_kind, allowed_values in policy_selectors.items():
        observed_values = row_selectors[selector_kind]
        if not allowed_values or not observed_values:
            continue
        if allowed_values & observed_values:
            matched_selector_kinds.append(selector_kind)
        else:
            conflicting_selector_kinds.append(selector_kind)
    applicable = bool(matched_selector_kinds) and not conflicting_selector_kinds
    return {
        "policy_id": str(policy.get("policy_id", "") or ""),
        "work_order_id": _work_order_id(row),
        "applicable": applicable,
        "status": (
            "TASK_SCOPED_POLICY_APPLICABLE"
            if applicable
            else "TASK_SCOPED_POLICY_CONFLICT"
            if conflicting_selector_kinds
            else "TASK_SCOPED_POLICY_SELECTOR_MISSING"
        ),
        "matched_selector_kinds": matched_selector_kinds,
        "conflicting_selector_kinds": conflicting_selector_kinds,
        "task_family": row_task_family,
        "question_ids": sorted(row_question_ids),
        "theorem_target_ids": sorted(row_theorem_target_ids),
        "boundary": (
            "Policy-derived registered support is eligible only when explicit "
            "task, question, or theorem selectors match and no supplied selector "
            "conflicts. Nonmatching work orders return to generic discovery."
        ),
    }


def registered_support_for_semantic_primitive(
    primitive_id: str,
) -> tuple[str, ...]:
    policy = _semantic_support_policy()
    return policy["primitive_to_registered_support"].get(primitive_id, ())


def registered_support_for_semantic_primitive_text(
    *,
    primitive_id: str = "",
    semantic_primitive_gap: str = "",
    semantic_primitive_gap_kind: str = "",
) -> tuple[str, ...]:
    policy = _semantic_support_policy()
    primitive_text = str(primitive_id or "").lower()
    work_order_text = " ".join(
        [
            str(primitive_id or ""),
            str(semantic_primitive_gap or ""),
            str(semantic_primitive_gap_kind or ""),
        ]
    ).lower()
    registered_support_ids: list[str] = []
    for rule in policy["semantic_primitive_text_to_registered_support"]:
        if _semantic_primitive_text_support_rule_matches(
            rule,
            primitive_text=primitive_text,
            work_order_text=work_order_text,
        ):
            registered_support_ids.extend(rule.get("registered_support_ids", ()))
    return tuple(dict.fromkeys(registered_support_ids))


def _semantic_primitive_text_support_rule_matches(
    rule: Mapping[str, Any],
    *,
    primitive_text: str,
    work_order_text: str,
) -> bool:
    text_contains_any = tuple(
        str(item) for item in rule.get("work_order_text_contains_any", ()) or ()
    )
    text_contains_all = tuple(
        str(item) for item in rule.get("work_order_text_contains_all", ()) or ()
    )
    primitive_id_contains_any = tuple(
        str(item)
        for item in rule.get("semantic_primitive_id_contains_any", ()) or ()
    )
    primitive_id_contains_all = tuple(
        str(item)
        for item in rule.get("semantic_primitive_id_contains_all", ()) or ()
    )
    return bool(
        (
            text_contains_any
            and any(item in work_order_text for item in text_contains_any)
        )
        or (
            text_contains_all
            and all(item in work_order_text for item in text_contains_all)
        )
        or (
            primitive_id_contains_any
            and any(item in primitive_text for item in primitive_id_contains_any)
        )
        or (
            primitive_id_contains_all
            and all(item in primitive_text for item in primitive_id_contains_all)
        )
    )


def registered_support_for_placeholder_symbol(symbol: str) -> tuple[str, ...]:
    policy = _semantic_support_policy()
    return policy["placeholder_symbol_to_registered_support"].get(symbol.strip(), ())


def _format_semantic_gap_template(
    template: str,
    *,
    symbol: str = "",
    target_theorem_name: str = "",
) -> str:
    target_name = str(target_theorem_name or "").strip()
    target_suffix = f" for `{target_name}`" if target_name else ""
    return (
        str(template or "")
        .replace("{symbol}", str(symbol or "").strip())
        .replace("{target}", target_suffix)
        .replace("{target_theorem_name}", target_name)
        .strip()
    )


def semantic_gap_for_placeholder_symbol(
    symbol: str,
    *,
    target_theorem_name: str = "",
) -> str:
    policy = _semantic_support_policy()
    normalized_symbol = str(symbol or "").strip()
    template = policy["placeholder_symbol_to_semantic_gap"].get(
        normalized_symbol,
        "",
    )
    if not template:
        return ""
    return _format_semantic_gap_template(
        template,
        symbol=normalized_symbol,
        target_theorem_name=target_theorem_name,
    )


def semantic_gap_for_exact_goal_shape_obligation(
    obligation_id: str,
    *,
    target_theorem_name: str = "",
) -> str:
    policy = _semantic_support_policy()
    normalized_obligation_id = str(obligation_id or "").strip()
    template = policy["exact_goal_shape_to_semantic_gap"].get(
        normalized_obligation_id,
        "",
    )
    if not template:
        return ""
    return _format_semantic_gap_template(
        template,
        target_theorem_name=target_theorem_name,
    )


def inferred_exact_goal_shape_obligation_ids(
    *,
    failure_classification: str = "",
    trigger: str = "",
) -> tuple[str, ...]:
    policy = _semantic_support_policy()
    normalized_failure = str(failure_classification or "").strip()
    normalized_trigger = str(trigger or "").strip()
    obligation_ids: list[str] = []
    for rule in policy["exact_goal_shape_obligation_inference_rules"]:
        failure_matches = (
            normalized_failure
            and normalized_failure in rule.get("failure_classifications", ())
        )
        trigger_matches = (
            normalized_trigger
            and normalized_trigger in rule.get("triggers", ())
        )
        if failure_matches or trigger_matches:
            obligation_ids.extend(rule.get("obligation_ids", ()))
    return tuple(dict.fromkeys(obligation_ids))


def inferred_exact_goal_shape_obligation_ids_from_feedback(
    *,
    failure_classification: str = "",
    trigger: str = "",
    goal_text: str = "",
) -> tuple[str, ...]:
    policy = _semantic_support_policy()
    normalized_failure = str(failure_classification or "").strip()
    normalized_trigger = str(trigger or "").strip()
    obligation_ids: list[str] = []
    for rule in policy["exact_goal_shape_obligation_feedback_rules"]:
        if _exact_goal_shape_feedback_rule_matches(
            rule,
            failure_classification=normalized_failure,
            trigger=normalized_trigger,
            goal_text=goal_text,
        ):
            obligation_id = str(rule.get("obligation_id", "") or "").strip()
            if obligation_id:
                obligation_ids.append(obligation_id)
    return tuple(dict.fromkeys(obligation_ids))


def _exact_goal_shape_feedback_rule_matches(
    rule: Mapping[str, Any],
    *,
    failure_classification: str,
    trigger: str,
    goal_text: str,
) -> bool:
    failure_classifications = rule.get("failure_classifications", ()) or ()
    if failure_classification and failure_classification in failure_classifications:
        return True
    triggers = rule.get("triggers", ()) or ()
    if trigger and trigger in triggers:
        return True
    case_sensitive = _bool_like(
        rule.get("case_sensitive_goal_text", True),
        default=True,
    )
    text = str(goal_text or "")
    haystack = text if case_sensitive else text.lower()
    contains_any = tuple(
        str(item) for item in rule.get("goal_text_contains_any", ()) or ()
    )
    contains_all = tuple(
        str(item) for item in rule.get("goal_text_contains_all", ()) or ()
    )
    if not case_sensitive:
        contains_any = tuple(item.lower() for item in contains_any)
        contains_all = tuple(item.lower() for item in contains_all)
    if contains_any and any(item and item in haystack for item in contains_any):
        return True
    if contains_all and all(item and item in haystack for item in contains_all):
        return True
    return False


def semantic_primitive_id_for_gap(gap_text: str, gap_kind: str = "") -> str:
    policy = _semantic_support_policy()
    text = f"{gap_kind} {gap_text}".lower()
    for rule in policy["semantic_primitive_id_text_rules"]:
        primitive_id = str(rule.get("semantic_primitive_id", "") or "").strip()
        if not primitive_id:
            continue
        patterns = rule.get("contains_all_any", ()) or ()
        if any(all(term in text for term in pattern) for pattern in patterns):
            return primitive_id
    return ""


def semantic_primitive_id_for_placeholder_symbol(
    symbol: str,
    *,
    target_theorem_name: str = "",
) -> str:
    policy = _semantic_support_policy()
    normalized_symbol = str(symbol or "").strip()
    primitive_id = policy["placeholder_symbol_to_semantic_primitive_id"].get(
        normalized_symbol,
        "",
    )
    if primitive_id:
        return primitive_id
    gap = semantic_gap_for_placeholder_symbol(
        normalized_symbol,
        target_theorem_name=target_theorem_name,
    )
    primitive_id = semantic_primitive_id_for_gap(
        gap,
        "source_theorem_semantic_primitives",
    )
    if primitive_id:
        return primitive_id
    return (
        "source_theorem_semantic_primitive:"
        + stable_hash([normalized_symbol, target_theorem_name])[:16]
    )


def semantic_primitive_for_placeholder_symbol(
    symbol: str,
    *,
    target_theorem_name: str = "",
) -> tuple[str, str]:
    normalized_symbol = str(symbol or "").strip()
    primitive_id = semantic_primitive_id_for_placeholder_symbol(
        normalized_symbol,
        target_theorem_name=target_theorem_name,
    )
    gap = semantic_gap_for_placeholder_symbol(
        normalized_symbol,
        target_theorem_name=target_theorem_name,
    )
    if not gap:
        target = f" for `{target_theorem_name}`" if target_theorem_name else ""
        gap = (
            f"formalize placeholder {normalized_symbol} as a source-theorem "
            f"semantic primitive{target}"
        )
    return primitive_id, gap


def placeholder_symbols_for_registered_support_ids(
    support_ids: Sequence[str],
) -> tuple[str, ...]:
    policy = _semantic_support_policy()
    symbol_by_support_id: dict[str, str] = {}
    for symbol, registered_support_ids in policy[
        "placeholder_symbol_to_registered_support"
    ].items():
        for support_id in registered_support_ids:
            symbol_by_support_id.setdefault(support_id, symbol)
    return tuple(
        dict.fromkeys(
            symbol_by_support_id[support_id]
            for support_id in (
                str(value).strip() for value in support_ids if str(value).strip()
            )
            if support_id in symbol_by_support_id
        )
    )


def registered_support_for_exact_goal_shape_obligation(
    obligation_id: str,
) -> tuple[str, ...]:
    policy = _semantic_support_policy()
    return policy["exact_goal_shape_to_registered_support"].get(obligation_id, ())


def exact_goal_shape_obligation_ids_for_route(route_id: str) -> tuple[str, ...]:
    policy = _semantic_support_policy()
    normalized_route_id = str(route_id or "").strip()
    if not normalized_route_id:
        return ()
    return policy["exact_goal_shape_obligation_routes"].get(
        normalized_route_id,
        (),
    )


def exact_goal_shape_obligation_has_route(
    obligation_id: str,
    route_id: str,
) -> bool:
    normalized_obligation_id = str(obligation_id or "").strip()
    if not normalized_obligation_id:
        return False
    return normalized_obligation_id in set(
        exact_goal_shape_obligation_ids_for_route(route_id)
    )


def theorem_closure_reduction_strategy_for_goal(
    *,
    goal_id: str,
    verified_bridge_ids: Sequence[str],
) -> dict[str, str]:
    policy = _semantic_support_policy()
    strategies = policy["theorem_closure_reduction_strategies"].get(
        str(goal_id).strip(),
        (),
    )
    verified = {
        str(value).strip()
        for value in verified_bridge_ids
        if str(value).strip()
    }
    for strategy in strategies:
        if strategy["proof_obligation_id"] in verified:
            return dict(strategy)
    return {}


def placeholder_symbols_from_semantic_alignment_feedback(
    *,
    semantic_alignment_blockers: Sequence[str] = (),
    semantic_alignment_constraints: Sequence[str] = (),
    explicit_placeholder_symbols: Sequence[str] = (),
    failure_classification: str = "",
    include_executor_feedback_signals: bool = False,
) -> tuple[str, ...]:
    explicit_symbols = tuple(
        dict.fromkeys(
            str(value).strip()
            for value in explicit_placeholder_symbols
            if str(value).strip()
        )
    )
    if failure_classification == "formal_environment_placeholder_primitives":
        return explicit_symbols
    policy = _semantic_support_policy()
    text_signals = policy["placeholder_symbol_text_signals"]
    lower_text = " ".join(
        str(value).strip()
        for value in [*semantic_alignment_blockers, *semantic_alignment_constraints]
        if str(value).strip()
    ).lower()
    exact_text = "\n".join(
        str(value).strip()
        for value in [*semantic_alignment_blockers, *semantic_alignment_constraints]
        if str(value).strip()
    )
    inferred: list[str] = []
    for symbol, signals in text_signals.items():
        contains = list(signals.get("runtime_blocker_contains", ()))
        case_sensitive_contains = list(
            signals.get("runtime_blocker_case_sensitive_contains", ())
        )
        if include_executor_feedback_signals:
            contains.extend(signals.get("executor_feedback_contains", ()))
            case_sensitive_contains.extend(
                signals.get("executor_feedback_case_sensitive_contains", ())
            )
        if any(signal.lower() in lower_text for signal in contains) or any(
            signal in exact_text for signal in case_sensitive_contains
        ):
            inferred.append(symbol)
    inferred.extend(explicit_symbols)
    return tuple(dict.fromkeys(inferred))


def resolve_source_semantic_primitive_queue_path(
    *,
    runtime_dir: Path | None = None,
    queue_jsonl: Path | None = None,
    proof_body_executor_dir: Path | None = None,
    out_dir: Path | None = None,
) -> Path:
    if queue_jsonl is not None:
        return queue_jsonl
    if proof_body_executor_dir is not None:
        if out_dir is None:
            raise ValueError("out_dir is required with proof_body_executor_dir")
        return materialize_source_semantic_primitive_queue_from_proof_body_executor(
            proof_body_executor_dir=proof_body_executor_dir,
            out_dir=out_dir,
        )
    if runtime_dir is None:
        raise ValueError(
            "runtime_dir, queue_jsonl, or proof_body_executor_dir is required"
        )
    manifest_path = runtime_dir / "research_agent_runtime_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    artifacts = manifest.get("artifacts", {})
    if not isinstance(artifacts, Mapping):
        artifacts = {}
    raw_path = str(
        artifacts.get(
            "runtime_source_theorem_semantic_primitive_work_orders_jsonl",
            "",
        )
        or ""
    )
    if not raw_path:
        raise ValueError(
            "runtime manifest does not list "
            "runtime_source_theorem_semantic_primitive_work_orders_jsonl"
        )
    queue_path = Path(raw_path)
    if queue_path.is_absolute() or queue_path.exists():
        return queue_path
    candidates = [runtime_dir / queue_path]
    parts = queue_path.parts
    if len(parts) >= 2 and parts[0] == runtime_dir.parent.name:
        candidates.append(runtime_dir.parent.parent / queue_path)
    if parts and parts[0] == runtime_dir.name:
        candidates.append(runtime_dir.parent / queue_path)
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def materialize_source_semantic_primitive_queue_from_proof_body_executor(
    *,
    proof_body_executor_dir: Path,
    out_dir: Path,
) -> Path:
    learning_rows_path = _resolve_proof_body_executor_learning_rows_path(
        proof_body_executor_dir
    )
    learning_rows = _read_jsonl(learning_rows_path)
    queue_rows = _semantic_primitive_queue_rows_from_proof_body_executor_learning_rows(
        learning_rows
    )
    queue_path = out_dir / (
        "runtime_source_theorem_semantic_primitive_work_orders_from_"
        "proof_body_executor.jsonl"
    )
    _write_jsonl(queue_path, queue_rows)
    return queue_path


def _resolve_proof_body_executor_learning_rows_path(
    proof_body_executor_dir: Path,
) -> Path:
    direct = (
        proof_body_executor_dir
        / "runtime_learning_export"
        / "runtime_learning_rows.jsonl"
    )
    if direct.exists():
        return direct
    manifest_path = (
        proof_body_executor_dir
        / "runtime_learning_export"
        / "exact_source_theorem_proof_body_execution_learning_manifest.json"
    )
    if not manifest_path.exists():
        raise FileNotFoundError(
            "proof-body executor runtime learning rows not found under "
            f"{proof_body_executor_dir}"
        )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    raw_path = str(manifest.get("runtime_learning_rows_jsonl", "") or "")
    if not raw_path:
        raise ValueError(
            "proof-body executor learning manifest does not list "
            "runtime_learning_rows_jsonl"
        )
    rows_path = Path(raw_path)
    if rows_path.is_absolute() or rows_path.exists():
        return rows_path
    candidates = [
        proof_body_executor_dir / rows_path,
        proof_body_executor_dir.parent / rows_path,
        manifest_path.parent / rows_path,
    ]
    parts = rows_path.parts
    if parts and parts[0] == proof_body_executor_dir.name:
        candidates.append(proof_body_executor_dir.parent / rows_path)
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def _semantic_primitive_queue_rows_from_proof_body_executor_learning_rows(
    learning_rows: list[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in learning_rows:
        if not isinstance(row, Mapping):
            continue
        input_summary = row.get("input_summary", {})
        if not isinstance(input_summary, Mapping):
            continue
        learning_task = str(row.get("learning_task", "") or "")
        if learning_task != "exact_source_theorem_proof_body_execution_feedback":
            continue
        if (
            _bool_like(row.get("source_theorem_kernel_verified", False))
            or _bool_like(input_summary.get("source_theorem_kernel_verified", False))
        ):
            continue
        failure_classification = str(
            input_summary.get("failure_classification", "") or ""
        ).strip()
        exact_goal_shape_obligation_ids = [
            str(value).strip()
            for value in (
                input_summary.get("exact_goal_shape_obligation_ids", [])
                or row.get("exact_goal_shape_obligation_ids", [])
                or []
            )
            if str(value).strip()
        ]
        exact_goal_shape_obligations = [
            str(value).strip()
            for value in (
                input_summary.get("exact_goal_shape_obligations", [])
                or row.get("exact_goal_shape_obligations", [])
                or []
            )
            if str(value).strip()
        ]
        if not exact_goal_shape_obligation_ids:
            exact_goal_shape_obligation_ids = list(
                _inferred_exact_goal_shape_obligation_ids(
                    failure_classification=failure_classification,
                    trigger=str(row.get("trigger", "") or ""),
                )
            )
            exact_goal_shape_obligations = [
                _semantic_primitive_gap_for_exact_goal_shape_obligation(
                    obligation_id,
                    target_theorem_name=str(
                        row.get("target_theorem_name", "")
                        or input_summary.get("target_theorem_name", "")
                        or ""
                    ),
                )
                for obligation_id in exact_goal_shape_obligation_ids
            ]
        exact_goal_shape_obligation_by_id = {
            obligation_id: (
                exact_goal_shape_obligations[index]
                if index < len(exact_goal_shape_obligations)
                else _semantic_primitive_gap_for_exact_goal_shape_obligation(
                    obligation_id,
                    target_theorem_name="",
                )
            )
            for index, obligation_id in enumerate(exact_goal_shape_obligation_ids)
        }
        if failure_classification not in {
            "formal_environment_placeholder_primitives",
            "proof_body_reached_semantic_alignment_unreviewed",
            "source_theorem_semantic_alignment_unreviewed",
        } and not exact_goal_shape_obligation_ids:
            continue
        semantic_alignment_blockers = [
            str(value).strip()
            for value in (
                row.get("semantic_alignment_blockers", [])
                or input_summary.get("semantic_alignment_blockers", [])
                or []
            )
            if str(value).strip()
        ]
        semantic_alignment_constraints = [
            str(value).strip()
            for value in (
                row.get("semantic_alignment_constraints", [])
                or input_summary.get("semantic_alignment_constraints", [])
                or []
            )
            if str(value).strip()
        ]
        placeholder_symbols = _semantic_primitive_symbols_from_executor_feedback(
            input_summary=input_summary,
            semantic_alignment_blockers=semantic_alignment_blockers,
            semantic_alignment_constraints=semantic_alignment_constraints,
            failure_classification=failure_classification,
        )
        if not placeholder_symbols and not exact_goal_shape_obligation_ids:
            continue
        target_theorem_name = str(
            row.get("target_theorem_name", "")
            or input_summary.get("target_theorem_name", "")
            or input_summary.get("target_lean_declaration", "")
            or ""
        ).strip()
        candidate_artifact_path = str(
            input_summary.get("candidate_artifact_path", "")
            or row.get("candidate_artifact_path", "")
            or ""
        ).strip()
        typeclass_blockers = [
            str(value).strip()
            for value in input_summary.get("formal_environment_typeclass_blockers", [])
            or []
            if str(value).strip()
        ]
        proof_body_attempt_summaries = [
            str(value).strip()
            for value in input_summary.get("proof_body_attempt_summaries", []) or []
            if str(value).strip()
        ][:8]
        live_request = input_summary.get("candidate_live_proof_state_request", {})
        if not isinstance(live_request, Mapping):
            live_request = {}
        proof_body_goal_excerpt = [
            str(value).strip()
            for value in (
                live_request.get("proof_body_goal_excerpt", [])
                or input_summary.get("proof_body_goal_excerpt", [])
                or []
            )
            if str(value).strip()
        ][:18]
        closure_declarations = _merged_string_values(
            input_summary,
            row,
            "kernel_verified_theorem_reduction_closure_declarations",
        )[:8]
        closure_artifact_paths = _merged_string_values(
            input_summary,
            row,
            "verified_theorem_reduction_closure_artifact_paths",
        )[:8]
        closure_signature_excerpts = _merged_string_values(
            input_summary,
            row,
            "kernel_verified_theorem_reduction_closure_signature_excerpts",
        )[:4]
        closure_target_ids = _merged_string_values(
            input_summary,
            row,
            "kernel_verified_theorem_reduction_closure_target_ids",
        )[:8]
        provenance = dict(row.get("source_theorem_target_provenance", {}) or {})
        input_provenance = dict(
            input_summary.get("source_theorem_target_provenance", {}) or {}
        )
        for key, value in input_provenance.items():
            provenance.setdefault(key, value)
        if target_theorem_name:
            provenance.setdefault("target_lean_declaration", target_theorem_name)
        source_learning_row_id = str(
            row.get("runtime_learning_row_id", "")
            or row.get("learning_row_id", "")
            or row.get("execution_result_id", "")
            or ""
        ).strip()
        for symbol in placeholder_symbols:
            primitive_id, gap = _semantic_primitive_for_placeholder_symbol(
                symbol,
                target_theorem_name=target_theorem_name,
            )
            work_order_id = (
                "source_theorem_semantic_primitive_work_order:"
                + stable_hash(
                    [
                        source_learning_row_id,
                        row.get("execution_result_id", ""),
                        row.get("execution_queue_id", ""),
                        target_theorem_name,
                        symbol,
                        primitive_id,
                        candidate_artifact_path,
                    ]
                )[:20]
            )
            if work_order_id in seen:
                continue
            seen.add(work_order_id)
            rows.append(
                {
                    "schema_version": 1,
                    "artifact_kind": "SourceTheoremSemanticPrimitiveWorkOrder",
                    "work_order_id": work_order_id,
                    "semantic_primitive_id": primitive_id,
                    "semantic_primitive_gap": gap,
                    "semantic_primitive_gap_kind": "source_theorem_semantic_primitives",
                    "next_owner": "FormalizerProofEngineer",
                    "source_learning_task": learning_task,
                    "source_learning_row_id": source_learning_row_id,
                    "source_execution_result_id": str(
                        row.get("execution_result_id", "") or ""
                    ),
                    "source_execution_queue_id": str(
                        row.get("execution_queue_id", "") or ""
                    ),
                    "source_formal_environment_work_order_id": str(
                        row.get("source_work_order_id", "") or ""
                    ),
                    "target_theorem_name": target_theorem_name,
                    "source_theorem_target_known": (
                        _bool_like(row.get("source_theorem_target_known", False))
                        or _bool_like(
                            input_summary.get("source_theorem_target_known", False)
                        )
                        or _bool_like(
                            provenance.get("source_theorem_target_known", False)
                        )
                    ),
                    "source_theorem_target_provenance": provenance,
                    "semantic_alignment_constraints": (
                        semantic_alignment_constraints
                        or list(provenance.get("semantic_alignment_constraints", []) or [])
                    ),
                    "semantic_alignment_blockers": semantic_alignment_blockers,
                    "candidate_artifact_path": candidate_artifact_path,
                    "placeholder_symbol": symbol,
                    "failure_classification": failure_classification,
                    "diagnostics": list(input_summary.get("diagnostics", []) or [])[:8],
                    "formal_environment_typeclass_blockers": typeclass_blockers,
                    "proof_body_attempted": _bool_like(
                        input_summary.get("proof_body_attempted", False)
                    ),
                    "proof_body_attempt_success": _bool_like(
                        input_summary.get("proof_body_attempt_success", False)
                    ),
                    "proof_body_attempt_summaries": proof_body_attempt_summaries,
                    "proof_body_goal_excerpt": proof_body_goal_excerpt,
                    "kernel_verified_theorem_reduction_closure_declarations": (
                        closure_declarations
                    ),
                    "verified_theorem_reduction_closure_artifact_paths": (
                        closure_artifact_paths
                    ),
                    "kernel_verified_theorem_reduction_closure_signature_excerpts": (
                        closure_signature_excerpts
                    ),
                    "kernel_verified_theorem_reduction_closure_target_ids": (
                        closure_target_ids
                    ),
                    "exact_goal_shape_obligation_ids": exact_goal_shape_obligation_ids,
                    "exact_goal_shape_obligations": exact_goal_shape_obligations,
                    "target_theorem_goal_ids": (
                        [target_theorem_name] if target_theorem_name else []
                    ),
                    "candidate_registered_obligation_ids": list(
                        registered_support_for_semantic_primitive(primitive_id)
                    ),
                    "proof_mode": "source_theorem_semantic_primitive_closure",
                    "runtime_queue_status": "PENDING_SOURCE_SEMANTIC_LEAN_PROOF_ATTEMPT",
                    "runtime_queue_boundary": (
                        "This queue row was exported from exact source proof-body executor "
                        "feedback after exact source-theorem proof-body work reached an "
                        "upstream semantic primitive blocker. It is not proof evidence "
                        "until AXLE/local Lean kernel "
                        "verification accepts the intended semantic primitive."
                    ),
                    "acceptance_gate": (
                        "AXLE/local Lean kernel verifies the upstream semantic primitive "
                        "with no sorry, and the manifest keeps this primitive evidence "
                        "separate from signature scaffolds and full source theorem proof."
                    ),
                    "proof_evidence_status": "WORK_ORDER_NOT_PROOF_EVIDENCE",
                    "proof_evidence_boundary": BOUNDARY,
                }
            )
        for obligation_id in exact_goal_shape_obligation_ids:
            gap = _semantic_primitive_gap_for_exact_goal_shape_obligation(
                obligation_id,
                target_theorem_name=target_theorem_name,
            )
            obligation_text = exact_goal_shape_obligation_by_id.get(
                obligation_id,
                gap,
            )
            primitive_id = (
                "source_theorem_exact_goal_shape_obligation:"
                + stable_hash([obligation_id, target_theorem_name])[:16]
            )
            work_order_id = (
                "source_theorem_semantic_primitive_work_order:"
                + stable_hash(
                    [
                        source_learning_row_id,
                        row.get("execution_result_id", ""),
                        row.get("execution_queue_id", ""),
                        target_theorem_name,
                        obligation_id,
                        primitive_id,
                        candidate_artifact_path,
                    ]
                )[:20]
            )
            if work_order_id in seen:
                continue
            seen.add(work_order_id)
            rows.append(
                {
                    "schema_version": 1,
                    "artifact_kind": "SourceTheoremSemanticPrimitiveWorkOrder",
                    "work_order_id": work_order_id,
                    "semantic_primitive_id": primitive_id,
                    "semantic_primitive_gap": gap,
                    "semantic_primitive_gap_kind": (
                        "source_theorem_exact_goal_shape_obligation"
                    ),
                    "exact_goal_shape_obligation_id": obligation_id,
                    "exact_goal_shape_obligation": obligation_text,
                    "next_owner": "FormalizerProofEngineer",
                    "source_learning_task": learning_task,
                    "source_learning_row_id": source_learning_row_id,
                    "source_execution_result_id": str(
                        row.get("execution_result_id", "") or ""
                    ),
                    "source_execution_queue_id": str(
                        row.get("execution_queue_id", "") or ""
                    ),
                    "source_formal_environment_work_order_id": str(
                        row.get("source_work_order_id", "") or ""
                    ),
                    "target_theorem_name": target_theorem_name,
                    "source_theorem_target_known": (
                        _bool_like(row.get("source_theorem_target_known", False))
                        or _bool_like(
                            input_summary.get("source_theorem_target_known", False)
                        )
                        or _bool_like(
                            provenance.get("source_theorem_target_known", False)
                        )
                    ),
                    "source_theorem_target_provenance": provenance,
                    "semantic_alignment_constraints": (
                        semantic_alignment_constraints
                        or list(provenance.get("semantic_alignment_constraints", []) or [])
                    ),
                    "semantic_alignment_blockers": semantic_alignment_blockers,
                    "candidate_artifact_path": candidate_artifact_path,
                    "placeholder_symbol": obligation_id,
                    "failure_classification": failure_classification,
                    "diagnostics": list(input_summary.get("diagnostics", []) or [])[:8],
                    "formal_environment_typeclass_blockers": typeclass_blockers,
                    "proof_body_attempted": _bool_like(
                        input_summary.get("proof_body_attempted", False)
                    ),
                    "proof_body_attempt_success": _bool_like(
                        input_summary.get("proof_body_attempt_success", False)
                    ),
                    "proof_body_attempt_summaries": proof_body_attempt_summaries,
                    "proof_body_goal_excerpt": proof_body_goal_excerpt,
                    "kernel_verified_theorem_reduction_closure_declarations": (
                        closure_declarations
                    ),
                    "verified_theorem_reduction_closure_artifact_paths": (
                        closure_artifact_paths
                    ),
                    "kernel_verified_theorem_reduction_closure_signature_excerpts": (
                        closure_signature_excerpts
                    ),
                    "kernel_verified_theorem_reduction_closure_target_ids": (
                        closure_target_ids
                    ),
                    "exact_goal_shape_obligation_ids": exact_goal_shape_obligation_ids,
                    "exact_goal_shape_obligations": exact_goal_shape_obligations,
                    "target_theorem_goal_ids": (
                        [target_theorem_name] if target_theorem_name else []
                    ),
                    "candidate_registered_obligation_ids": list(
                        _registered_support_for_exact_goal_shape_obligation(
                            obligation_id
                        )
                    ),
                    "proof_mode": "source_theorem_semantic_primitive_closure",
                    "runtime_queue_status": (
                        "PENDING_SOURCE_SEMANTIC_LEAN_PROOF_ATTEMPT"
                    ),
                    "runtime_queue_boundary": (
                        "This queue row was exported from exact source proof-body executor "
                        "feedback after local Lean reached a source-theorem goal-shape "
                        "obligation. It is not proof evidence until AXLE/local Lean "
                        "kernel verification accepts the intended reusable primitive."
                    ),
                    "acceptance_gate": (
                        "AXLE/local Lean kernel verifies the exact goal-shape primitive "
                        "with no sorry, and the manifest keeps this primitive evidence "
                        "separate from adapter evidence and full source theorem proof."
                    ),
                    "proof_evidence_status": "WORK_ORDER_NOT_PROOF_EVIDENCE",
                    "proof_evidence_boundary": BOUNDARY,
                }
            )
    return rows


def _semantic_primitive_symbols_from_executor_feedback(
    *,
    input_summary: Mapping[str, Any],
    semantic_alignment_blockers: list[str],
    semantic_alignment_constraints: list[str],
    failure_classification: str,
) -> list[str]:
    return list(
        placeholder_symbols_from_semantic_alignment_feedback(
            semantic_alignment_blockers=semantic_alignment_blockers,
            semantic_alignment_constraints=semantic_alignment_constraints,
            explicit_placeholder_symbols=[
                str(value).strip()
                for value in (
                    input_summary.get("formal_environment_placeholder_symbols", [])
                    or []
                )
                if str(value).strip()
            ],
            failure_classification=failure_classification,
            include_executor_feedback_signals=True,
        )
    )


def _semantic_primitive_for_placeholder_symbol(
    symbol: str,
    *,
    target_theorem_name: str,
) -> tuple[str, str]:
    return semantic_primitive_for_placeholder_symbol(
        symbol,
        target_theorem_name=target_theorem_name,
    )


def _semantic_primitive_gap_for_exact_goal_shape_obligation(
    obligation_id: str,
    *,
    target_theorem_name: str,
) -> str:
    gap = semantic_gap_for_exact_goal_shape_obligation(
        obligation_id,
        target_theorem_name=target_theorem_name,
    )
    if gap:
        return gap
    target = f" for `{target_theorem_name}`" if target_theorem_name else ""
    return f"Close exact source theorem goal-shape obligation {obligation_id}{target}."


def _inferred_exact_goal_shape_obligation_ids(
    *,
    failure_classification: str,
    trigger: str,
) -> tuple[str, ...]:
    return inferred_exact_goal_shape_obligation_ids(
        failure_classification=failure_classification,
        trigger=trigger,
    )


def _registered_support_for_exact_goal_shape_obligation(
    obligation_id: str,
) -> tuple[str, ...]:
    return registered_support_for_exact_goal_shape_obligation(obligation_id)


def run_source_theorem_semantic_primitive_proofengineer_bridge(
    *,
    out_dir: Path,
    runtime_dir: Path | None = None,
    queue_jsonl: Path | None = None,
    proof_body_executor_dir: Path | None = None,
    question_id: str = "",
    local_lean: bool = False,
    lean_project: Path | None = None,
    lean_timeout: int = 90,
    proof_audit_manifest: Path | None = None,
) -> dict[str, object]:
    out_dir.mkdir(parents=True, exist_ok=True)
    queue_path = resolve_source_semantic_primitive_queue_path(
        runtime_dir=runtime_dir,
        queue_jsonl=queue_jsonl,
        proof_body_executor_dir=proof_body_executor_dir,
        out_dir=out_dir,
    )
    rows = _read_jsonl(queue_path)
    semantic_support_policy = _semantic_support_policy()
    policy_applicability_by_work_order = {
        _work_order_id(row): _semantic_support_policy_applicability(
            semantic_support_policy,
            row,
            fallback_question_id=question_id,
        )
        for row in rows
    }
    candidate_ids_by_work_order = {
        _work_order_id(row): _candidate_registered_obligation_ids(
            row,
            policy=semantic_support_policy,
            policy_applicability=policy_applicability_by_work_order.get(
                _work_order_id(row),
                {},
            ),
        )
        for row in rows
    }
    candidate_ids = sorted(
        {
            obligation_id
            for ids in candidate_ids_by_work_order.values()
            for obligation_id in ids
        }
    )

    audit_manifest_path = Path(proof_audit_manifest).expanduser().resolve() if proof_audit_manifest else None
    audit_payload: dict[str, Any] | None = None
    if audit_manifest_path is not None:
        audit_payload = json.loads(audit_manifest_path.read_text(encoding="utf-8"))
    elif local_lean and candidate_ids:
        audit_dir = out_dir / "proof_audit"
        verifier = LocalLeanProofVerifier(project_root=lean_project, timeout_s=lean_timeout)
        audit_payload = asyncio.run(
            audit_proof_bank(
                verifier,
                audit_dir,
                ids=candidate_ids,
                export_lean=True,
                export_attempt_log=True,
            )
        )
        audit_manifest_path = audit_dir / "proof_audit_manifest.json"

    verified_ids = list(_kernel_verified_ids_from_audit_payload(audit_payload))
    checks = [
        _bridge_check(
            row,
            candidate_ids_by_work_order.get(_work_order_id(row), ()),
            verified_ids,
            audit_manifest_path=audit_manifest_path,
            policy_applicability=policy_applicability_by_work_order.get(
                _work_order_id(row),
                {},
            ),
        )
        for row in rows
    ]
    kernel_verified_candidate_ids = list(
        dict.fromkeys(
            str(value).strip()
            for row in checks
            for value in row.get("kernel_verified_registered_obligation_ids", []) or []
            if str(value).strip()
        )
    )
    n_kernel_verified_support = sum(
        len(row.get("kernel_verified_registered_obligation_ids", []) or [])
        for row in checks
    )
    exact_goal_shape_checks = [
        row
        for row in checks
        if str(row.get("exact_goal_shape_obligation_id", "") or "").strip()
    ]
    exact_goal_shape_obligation_ids = list(
        dict.fromkeys(
            str(row.get("exact_goal_shape_obligation_id", "")).strip()
            for row in exact_goal_shape_checks
            if str(row.get("exact_goal_shape_obligation_id", "")).strip()
        )
    )
    unregistered_exact_goal_shape_obligation_ids = list(
        dict.fromkeys(
            str(row.get("exact_goal_shape_obligation_id", "")).strip()
            for row in exact_goal_shape_checks
            if str(row.get("exact_goal_shape_obligation_id", "")).strip()
            and not row.get("registered_candidate_obligation_ids")
        )
    )
    registered_exact_goal_shape_obligation_ids = [
        obligation_id
        for obligation_id in exact_goal_shape_obligation_ids
        if obligation_id not in set(unregistered_exact_goal_shape_obligation_ids)
    ]
    learning_result = _export_runtime_learning_rows(
        checks=checks,
        out_dir=out_dir / "runtime_learning_export",
        question_id=question_id,
        proof_audit_manifest=audit_manifest_path,
    )
    proof_library_expansion_result = _export_exact_goal_shape_proof_library_expansion_queue(
        checks=checks,
        out_dir=out_dir / "proof_library_expansion_queue",
        question_id=question_id,
    )
    adapter_instantiation_result = (
        _export_exact_goal_shape_adapter_instantiation_queue(
            checks=checks,
            out_dir=out_dir / "source_to_bridge_adapter_instantiation_queue",
            question_id=question_id,
        )
    )
    checks_path = out_dir / "source_theorem_semantic_primitive_bridge_checks.jsonl"
    _write_jsonl(checks_path, checks)
    manifest = {
        "schema_version": 1,
        "artifact_kind": ARTIFACT_KIND,
        "source_runtime_dir": str(runtime_dir or ""),
        "source_proof_body_executor_dir": str(proof_body_executor_dir or ""),
        "source_queue_jsonl": str(queue_path),
        "source_proof_audit_manifest": str(audit_manifest_path or ""),
        "checks_jsonl": str(checks_path),
        "runtime_learning_rows_jsonl": str(learning_result["runtime_learning_rows_jsonl"]),
        "runtime_learning_export_manifest": str(learning_result["export_manifest_path"]),
        "proof_library_expansion_queue_jsonl": str(
            proof_library_expansion_result["queue_jsonl"]
        ),
        "proof_library_expansion_queue_manifest": str(
            proof_library_expansion_result["manifest_path"]
        ),
        "source_to_bridge_adapter_instantiation_queue_jsonl": str(
            adapter_instantiation_result["queue_jsonl"]
        ),
        "source_to_bridge_adapter_instantiation_queue_manifest": str(
            adapter_instantiation_result["manifest_path"]
        ),
        "local_lean_requested": bool(local_lean),
        "local_lean_project": str(lean_project or ""),
        "local_lean_timeout_seconds": int(lean_timeout),
        "n_work_orders": len(rows),
        "n_proof_library_expansion_queue_rows": int(
            proof_library_expansion_result["n_queue_rows"]
        ),
        "n_source_to_bridge_adapter_instantiation_queue_rows": int(
            adapter_instantiation_result["n_queue_rows"]
        ),
        "n_exact_goal_shape_obligation_work_orders": len(exact_goal_shape_checks),
        "exact_goal_shape_obligation_ids": exact_goal_shape_obligation_ids,
        "n_registered_exact_goal_shape_obligations": len(
            registered_exact_goal_shape_obligation_ids
        ),
        "registered_exact_goal_shape_obligation_ids": (
            registered_exact_goal_shape_obligation_ids
        ),
        "n_unregistered_exact_goal_shape_obligations": len(
            unregistered_exact_goal_shape_obligation_ids
        ),
        "unregistered_exact_goal_shape_obligation_ids": (
            unregistered_exact_goal_shape_obligation_ids
        ),
        "n_registered_candidate_obligations": len(candidate_ids),
        "registered_candidate_obligation_ids": candidate_ids,
        "n_semantic_support_policy_applicable_work_orders": sum(
            1
            for applicability in policy_applicability_by_work_order.values()
            if applicability.get("applicable") is True
        ),
        "n_semantic_support_policy_inapplicable_work_orders": sum(
            1
            for applicability in policy_applicability_by_work_order.values()
            if applicability.get("applicable") is not True
        ),
        "semantic_support_policy_applicability": list(
            policy_applicability_by_work_order.values()
        ),
        "n_kernel_verified_registered_candidate_obligations": len(
            kernel_verified_candidate_ids
        ),
        "kernel_verified_registered_candidate_obligation_ids": (
            kernel_verified_candidate_ids
        ),
        "kernel_verified_source_theorem_semantic_support_obligation_ids": (
            kernel_verified_candidate_ids
        ),
        "n_kernel_verified_source_theorem_semantic_primitive_ids": len(
            kernel_verified_candidate_ids
        ),
        "kernel_verified_source_theorem_semantic_primitive_ids": (
            kernel_verified_candidate_ids
        ),
        "kernel_verified_source_theorem_semantic_definition_ids": [],
        "n_kernel_verified_source_theorem_semantic_definition_ids": 0,
        "semantic_support_policy": _semantic_support_policy_summary(),
        "semantic_closure_status": (
            SEMANTIC_SUPPORT_ONLY_STATUS
            if kernel_verified_candidate_ids
            else "NO_KERNEL_VERIFIED_REGISTERED_SEMANTIC_SUPPORT"
        ),
        "placeholder_definition_status": (
            PLACEHOLDER_DEFINITION_OPEN_STATUS
            if kernel_verified_candidate_ids
            else "REGISTERED_SUPPORT_NOT_KERNEL_VERIFIED"
        ),
        "source_theorem_ready_for_exact_proof_body": False,
        "source_theorem_semantic_support_only": bool(kernel_verified_candidate_ids),
        "n_kernel_verified_work_order_support_links": n_kernel_verified_support,
        "runtime_learning_ready": bool(learning_result["n_learning_rows"]),
        "proof_library_expansion_queue_ready": bool(
            proof_library_expansion_result["n_queue_rows"]
        ),
        "proof_library_expansion_queue_proof_evidence_status": (
            proof_library_expansion_result["proof_evidence_status"]
        ),
        "source_to_bridge_adapter_instantiation_queue_ready": bool(
            adapter_instantiation_result["n_queue_rows"]
        ),
        "source_to_bridge_adapter_instantiation_queue_proof_evidence_status": (
            adapter_instantiation_result["proof_evidence_status"]
        ),
        "proof_evidence_status": (
            "KERNEL_VERIFIED_SOURCE_SEMANTIC_PRIMITIVE_SUPPORT_PRESENT"
            if kernel_verified_candidate_ids
            else "NO_KERNEL_VERIFIED_SOURCE_SEMANTIC_PRIMITIVE_SUPPORT"
        ),
        "checks": checks,
        "boundary": BOUNDARY,
    }
    manifest_path = out_dir / "source_theorem_semantic_primitive_proofengineer_bridge_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, default=str),
        encoding="utf-8",
    )
    return manifest


def _bridge_check(
    row: Mapping[str, Any],
    candidate_ids: tuple[str, ...],
    verified_ids: tuple[str, ...],
    *,
    audit_manifest_path: Path | None,
    policy_applicability: Mapping[str, Any],
) -> dict[str, Any]:
    kernel_verified_support = [row for row in candidate_ids if row in set(verified_ids)]
    exact_goal_shape_obligation_id = str(
        row.get("exact_goal_shape_obligation_id", "") or ""
    ).strip()
    is_exact_goal_shape_obligation = bool(exact_goal_shape_obligation_id)
    status = (
        "KERNEL_VERIFIED_REGISTERED_SEMANTIC_BRIDGE_SUPPORT"
        if kernel_verified_support
        else "REGISTERED_SEMANTIC_BRIDGE_SUPPORT_NOT_KERNEL_VERIFIED"
        if candidate_ids
        else "TASK_SCOPED_POLICY_NOT_APPLICABLE_GENERIC_DISCOVERY_REQUIRED"
        if policy_applicability.get("applicable") is not True
        else "OPEN_EXACT_GOAL_SHAPE_OBLIGATION_NO_REGISTERED_SUPPORT"
        if is_exact_goal_shape_obligation
        else "FORMAL_BLOCKED_NO_REGISTERED_SEMANTIC_PRIMITIVE_SUPPORT"
    )
    source_theorem_target_provenance = dict(
        row.get("source_theorem_target_provenance", {}) or {}
    )
    semantic_alignment_constraints = [
        str(value).strip()
        for value in row.get("semantic_alignment_constraints", []) or []
        if str(value).strip()
    ]
    formal_environment_typeclass_blockers = [
        str(value).strip()
        for value in row.get("formal_environment_typeclass_blockers", []) or []
        if str(value).strip()
    ]
    proof_body_attempt_summaries = [
        str(value).strip()
        for value in row.get("proof_body_attempt_summaries", []) or []
        if str(value).strip()
    ]
    proof_body_goal_excerpt = [
        str(value).strip()
        for value in row.get("proof_body_goal_excerpt", []) or []
        if str(value).strip()
    ]
    closure_declarations = _string_values(
        row,
        "kernel_verified_theorem_reduction_closure_declarations",
    )[:8]
    closure_artifact_paths = _string_values(
        row,
        "verified_theorem_reduction_closure_artifact_paths",
    )[:8]
    closure_signature_excerpts = _string_values(
        row,
        "kernel_verified_theorem_reduction_closure_signature_excerpts",
    )[:4]
    closure_target_ids = _string_values(
        row,
        "kernel_verified_theorem_reduction_closure_target_ids",
    )[:8]
    return {
        "schema_version": 1,
        "work_order_id": _work_order_id(row),
        "question_id": str(row.get("question_id", "") or ""),
        "semantic_primitive_id": str(row.get("semantic_primitive_id", "") or ""),
        "semantic_primitive_gap": str(row.get("semantic_primitive_gap", "") or ""),
        "semantic_primitive_gap_kind": str(
            row.get("semantic_primitive_gap_kind", "") or ""
        ),
        **_source_to_bridge_premise_context(row),
        "exact_goal_shape_obligation_id": exact_goal_shape_obligation_id,
        "exact_goal_shape_obligation": str(
            row.get("exact_goal_shape_obligation", "") or ""
        ),
        "exact_goal_shape_obligation_ids": [
            str(value).strip()
            for value in row.get("exact_goal_shape_obligation_ids", []) or []
            if str(value).strip()
        ],
        "exact_goal_shape_obligations": [
            str(value).strip()
            for value in row.get("exact_goal_shape_obligations", []) or []
            if str(value).strip()
        ],
        "placeholder_symbol": str(row.get("placeholder_symbol", "") or ""),
        "target_theorem_name": str(row.get("target_theorem_name", "") or ""),
        "target_theorem_goal_ids": list(row.get("target_theorem_goal_ids", []) or []),
        "source_theorem_target_known": (
            _bool_like(row.get("source_theorem_target_known", False))
            or _bool_like(
                source_theorem_target_provenance.get(
                    "source_theorem_target_known", False
                )
            )
        ),
        "source_theorem_target_provenance": source_theorem_target_provenance,
        "semantic_alignment_constraints": semantic_alignment_constraints,
        "candidate_artifact_path": str(row.get("candidate_artifact_path", "") or ""),
        "failure_classification": str(row.get("failure_classification", "") or ""),
        "formal_environment_typeclass_blockers": formal_environment_typeclass_blockers,
        "proof_body_attempted": _bool_like(row.get("proof_body_attempted", False)),
        "proof_body_attempt_success": _bool_like(
            row.get("proof_body_attempt_success", False)
        ),
        "proof_body_attempt_summaries": proof_body_attempt_summaries,
        "proof_body_goal_excerpt": proof_body_goal_excerpt,
        "kernel_verified_theorem_reduction_closure_declarations": (
            closure_declarations
        ),
        "verified_theorem_reduction_closure_artifact_paths": closure_artifact_paths,
        "kernel_verified_theorem_reduction_closure_signature_excerpts": (
            closure_signature_excerpts
        ),
        "kernel_verified_theorem_reduction_closure_target_ids": closure_target_ids,
        "registered_candidate_obligation_ids": list(candidate_ids),
        "semantic_support_policy_applicability": dict(policy_applicability),
        "semantic_support_policy_applicable": (
            policy_applicability.get("applicable") is True
        ),
        "exact_goal_shape_registered_support_present": bool(
            is_exact_goal_shape_obligation and candidate_ids
        ),
        "exact_goal_shape_obligation_unregistered": bool(
            is_exact_goal_shape_obligation and not candidate_ids
        ),
        "kernel_verified_registered_obligation_ids": kernel_verified_support,
        "registered_support_level": (
            "registered_partial_semantic_bridge"
            if candidate_ids
            else "task_scoped_policy_not_applicable"
            if policy_applicability.get("applicable") is not True
            else "unregistered_exact_goal_shape_obligation"
            if is_exact_goal_shape_obligation
            else "missing_registered_semantic_primitive"
        ),
        "semantic_closure_status": (
            SEMANTIC_SUPPORT_ONLY_STATUS
            if kernel_verified_support
            else "REGISTERED_SUPPORT_NOT_KERNEL_VERIFIED"
            if candidate_ids
            else "EXACT_GOAL_SHAPE_OBLIGATION_UNREGISTERED"
            if is_exact_goal_shape_obligation
            else "NO_REGISTERED_SEMANTIC_SUPPORT"
        ),
        "placeholder_definition_status": (
            PLACEHOLDER_DEFINITION_OPEN_STATUS
            if kernel_verified_support
            else "REGISTERED_SUPPORT_NOT_KERNEL_VERIFIED"
            if candidate_ids
            else "EXACT_GOAL_SHAPE_OBLIGATION_REQUIRES_PROOF_LIBRARY_EXPANSION"
            if is_exact_goal_shape_obligation
            else "NO_REGISTERED_SEMANTIC_SUPPORT"
        ),
        "source_theorem_ready_for_exact_proof_body": False,
        "source_theorem_semantic_support_only": bool(kernel_verified_support),
        "kernel_verified_source_theorem_semantic_definition_ids": [],
        "status": status,
        "kernel_verified": bool(kernel_verified_support),
        "proof_audit_manifest": str(audit_manifest_path or ""),
        "proof_evidence_status": (
            "KERNEL_VERIFIED_REGISTERED_SOURCE_SEMANTIC_PRIMITIVE_SUPPORT"
            if kernel_verified_support
            else "NO_KERNEL_VERIFIED_SOURCE_SEMANTIC_PRIMITIVE_SUPPORT"
        ),
        "boundary": BOUNDARY,
    }


def _export_exact_goal_shape_proof_library_expansion_queue(
    *,
    checks: list[Mapping[str, Any]],
    out_dir: Path,
    question_id: str,
) -> dict[str, object]:
    out_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for check in checks:
        obligation_id = str(
            check.get("exact_goal_shape_obligation_id", "") or ""
        ).strip()
        if not obligation_id:
            continue
        if check.get("registered_candidate_obligation_ids"):
            continue
        if exact_goal_shape_obligation_has_route(
            obligation_id,
            SOURCE_TO_BRIDGE_ADAPTER_INSTANTIATION_EXACT_GOAL_SHAPE_ROUTE,
        ):
            continue
        work_order_id = str(check.get("work_order_id", "") or "").strip()
        queue_id = (
            "source_theorem_exact_goal_shape_proof_library_expansion:"
            + stable_hash(
                [
                    work_order_id,
                    obligation_id,
                    check.get("target_theorem_name", ""),
                    check.get("semantic_primitive_gap", ""),
                ]
            )[:20]
        )
        if queue_id in seen:
            continue
        seen.add(queue_id)
        rows.append(
            {
                "schema_version": 1,
                "artifact_kind": (
                    "SourceTheoremExactGoalShapeProofLibraryExpansionWorkOrder"
                ),
                "queue_id": queue_id,
                "source_work_order_id": work_order_id,
                "question_id": str(
                    question_id or check.get("question_id", "") or ""
                ),
                "target_theorem_name": str(
                    check.get("target_theorem_name", "") or ""
                ),
                "target_theorem_goal_ids": list(
                    check.get("target_theorem_goal_ids", []) or []
                ),
                "source_theorem_target_known": _bool_like(
                    check.get("source_theorem_target_known", False)
                ),
                "source_theorem_target_provenance": dict(
                    check.get("source_theorem_target_provenance", {}) or {}
                ),
                "semantic_primitive_id": str(
                    check.get("semantic_primitive_id", "") or ""
                ),
                "semantic_primitive_gap": str(
                    check.get("semantic_primitive_gap", "") or ""
                ),
                "semantic_primitive_gap_kind": str(
                    check.get("semantic_primitive_gap_kind", "") or ""
                ),
                "exact_goal_shape_obligation_id": obligation_id,
                "exact_goal_shape_obligation": str(
                    check.get("exact_goal_shape_obligation", "") or ""
                ),
                "candidate_artifact_path": str(
                    check.get("candidate_artifact_path", "") or ""
                ),
                "source_candidate_artifact_path": str(
                    check.get("source_candidate_artifact_path", "")
                    or check.get("candidate_artifact_path", "")
                    or ""
                ),
                "proof_body_goal_excerpt": list(
                    check.get("proof_body_goal_excerpt", []) or []
                ),
                "proof_body_attempt_summaries": list(
                    check.get("proof_body_attempt_summaries", []) or []
                ),
                "kernel_verified_theorem_reduction_closure_declarations": list(
                    check.get(
                        "kernel_verified_theorem_reduction_closure_declarations",
                        [],
                    )
                    or []
                ),
                "verified_theorem_reduction_closure_artifact_paths": list(
                    check.get("verified_theorem_reduction_closure_artifact_paths", [])
                    or []
                ),
                "kernel_verified_theorem_reduction_closure_signature_excerpts": list(
                    check.get(
                        "kernel_verified_theorem_reduction_closure_signature_excerpts",
                        [],
                    )
                    or []
                ),
                "kernel_verified_theorem_reduction_closure_target_ids": list(
                    check.get("kernel_verified_theorem_reduction_closure_target_ids", [])
                    or []
                ),
                "source_status": str(check.get("status", "") or ""),
                "registered_candidate_obligation_ids": [],
                "next_owner": "FormalizerProofEngineer",
                "runtime_queue_status": (
                    "PENDING_EXACT_GOAL_SHAPE_PROOF_LIBRARY_EXPANSION"
                ),
                "target_artifact_kind": (
                    "registered_reusable_lean_proof_obligation_or_support_mapping"
                ),
                "acceptance_gate": (
                    "A later ProofEngineer worker must either add a reusable Lean "
                    "obligation/support mapping and verify it with local Lean/AXLE, "
                    "or explicitly mark this exact goal-shape obligation as blocked. "
                    "This queue row itself is not proof evidence."
                ),
                "proof_evidence_status": "WORK_ORDER_NOT_PROOF_EVIDENCE",
                "proof_evidence_boundary": BOUNDARY,
            }
        )
    queue_path = out_dir / "exact_goal_shape_proof_library_expansion_queue.jsonl"
    _write_jsonl(queue_path, rows)
    manifest_path = out_dir / "exact_goal_shape_proof_library_expansion_queue_manifest.json"
    manifest = {
        "schema_version": 1,
        "artifact_kind": "ExactGoalShapeProofLibraryExpansionQueueManifest",
        "queue_jsonl": str(queue_path),
        "n_queue_rows": len(rows),
        "exact_goal_shape_obligation_ids": [
            row["exact_goal_shape_obligation_id"] for row in rows
        ],
        "runtime_queue_status": (
            "PENDING_EXACT_GOAL_SHAPE_PROOF_LIBRARY_EXPANSION"
            if rows
            else "NO_UNREGISTERED_EXACT_GOAL_SHAPE_OBLIGATIONS"
        ),
        "proof_evidence_status": (
            "WORK_ORDER_NOT_PROOF_EVIDENCE"
            if rows
            else "NO_PROOF_LIBRARY_EXPANSION_WORK_ORDERS"
        ),
        "boundary": BOUNDARY,
    }
    manifest_path.write_text(
        json.dumps(manifest, indent=2, default=str),
        encoding="utf-8",
    )
    return {
        "queue_rows": rows,
        "n_queue_rows": len(rows),
        "queue_jsonl": queue_path,
        "manifest_path": manifest_path,
        "manifest": manifest,
        "proof_evidence_status": manifest["proof_evidence_status"],
    }


def _export_exact_goal_shape_adapter_instantiation_queue(
    *,
    checks: list[Mapping[str, Any]],
    out_dir: Path,
    question_id: str,
) -> dict[str, object]:
    out_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for check in checks:
        obligation_id = str(
            check.get("exact_goal_shape_obligation_id", "") or ""
        ).strip()
        if not exact_goal_shape_obligation_has_route(
            obligation_id,
            SOURCE_TO_BRIDGE_ADAPTER_INSTANTIATION_EXACT_GOAL_SHAPE_ROUTE,
        ):
            continue
        if check.get("registered_candidate_obligation_ids"):
            continue
        work_order_id = str(check.get("work_order_id", "") or "").strip()
        queue_id = (
            "source_theorem_exact_goal_shape_adapter_instantiation:"
            + stable_hash(
                [
                    work_order_id,
                    obligation_id,
                    check.get("target_theorem_name", ""),
                    check.get("proof_body_attempt_summaries", []),
                ]
            )[:20]
        )
        if queue_id in seen:
            continue
        seen.add(queue_id)
        rows.append(
            {
                "schema_version": 1,
                "artifact_kind": (
                    "SourceTheoremExactGoalShapeAdapterInstantiationWorkOrder"
                ),
                "queue_id": queue_id,
                "source_work_order_id": work_order_id,
                "question_id": str(
                    question_id or check.get("question_id", "") or ""
                ),
                "target_theorem_name": str(
                    check.get("target_theorem_name", "") or ""
                ),
                "target_theorem_goal_ids": list(
                    check.get("target_theorem_goal_ids", []) or []
                ),
                "source_theorem_target_known": _bool_like(
                    check.get("source_theorem_target_known", False)
                ),
                "source_theorem_target_provenance": dict(
                    check.get("source_theorem_target_provenance", {}) or {}
                ),
                "semantic_primitive_id": str(
                    check.get("semantic_primitive_id", "") or ""
                ),
                "semantic_primitive_gap": str(
                    check.get("semantic_primitive_gap", "") or ""
                ),
                "semantic_primitive_gap_kind": str(
                    check.get("semantic_primitive_gap_kind", "") or ""
                ),
                "exact_goal_shape_obligation_id": obligation_id,
                "exact_goal_shape_obligation": str(
                    check.get("exact_goal_shape_obligation", "") or ""
                ),
                "candidate_artifact_path": str(
                    check.get("candidate_artifact_path", "") or ""
                ),
                "source_candidate_artifact_path": str(
                    check.get("source_candidate_artifact_path", "")
                    or check.get("candidate_artifact_path", "")
                    or ""
                ),
                "proof_body_goal_excerpt": list(
                    check.get("proof_body_goal_excerpt", []) or []
                ),
                "proof_body_attempt_summaries": list(
                    check.get("proof_body_attempt_summaries", []) or []
                ),
                "kernel_verified_theorem_reduction_closure_declarations": list(
                    check.get(
                        "kernel_verified_theorem_reduction_closure_declarations",
                        [],
                    )
                    or []
                ),
                "verified_theorem_reduction_closure_artifact_paths": list(
                    check.get("verified_theorem_reduction_closure_artifact_paths", [])
                    or []
                ),
                "kernel_verified_theorem_reduction_closure_signature_excerpts": list(
                    check.get(
                        "kernel_verified_theorem_reduction_closure_signature_excerpts",
                        [],
                    )
                    or []
                ),
                "kernel_verified_theorem_reduction_closure_target_ids": list(
                    check.get("kernel_verified_theorem_reduction_closure_target_ids", [])
                    or []
                ),
                "source_status": str(check.get("status", "") or ""),
                "registered_candidate_obligation_ids": [],
                "next_owner": "ProofEngineerAdapterSynthesizer",
                "runtime_queue_status": (
                    "PENDING_SOURCE_TO_BRIDGE_ADAPTER_INSTANTIATION"
                ),
                "target_artifact_kind": (
                    "source_theorem_exact_proof_body_adapter_instantiation"
                ),
                "acceptance_gate": (
                    "A later ProofEngineer worker must build or repair a checked "
                    "source-to-bridge adapter/proof body that derives the bridge "
                    "hypotheses from the exact source theorem assumptions, then "
                    "rerun local Lean/AXLE on the exact source theorem declaration. "
                    "This queue row itself is not proof evidence."
                ),
                "proof_evidence_status": "WORK_ORDER_NOT_PROOF_EVIDENCE",
                "proof_evidence_boundary": BOUNDARY,
            }
        )
    queue_path = out_dir / "source_to_bridge_adapter_instantiation_queue.jsonl"
    _write_jsonl(queue_path, rows)
    manifest_path = (
        out_dir / "source_to_bridge_adapter_instantiation_queue_manifest.json"
    )
    manifest = {
        "schema_version": 1,
        "artifact_kind": "SourceToBridgeAdapterInstantiationQueueManifest",
        "queue_jsonl": str(queue_path),
        "n_queue_rows": len(rows),
        "exact_goal_shape_obligation_ids": [
            row["exact_goal_shape_obligation_id"] for row in rows
        ],
        "runtime_queue_status": (
            "PENDING_SOURCE_TO_BRIDGE_ADAPTER_INSTANTIATION"
            if rows
            else "NO_SOURCE_TO_BRIDGE_ADAPTER_INSTANTIATION_WORK_ORDERS"
        ),
        "proof_evidence_status": (
            "WORK_ORDER_NOT_PROOF_EVIDENCE"
            if rows
            else "NO_SOURCE_TO_BRIDGE_ADAPTER_INSTANTIATION_WORK_ORDERS"
        ),
        "boundary": BOUNDARY,
    }
    manifest_path.write_text(
        json.dumps(manifest, indent=2, default=str),
        encoding="utf-8",
    )
    return {
        "queue_rows": rows,
        "n_queue_rows": len(rows),
        "queue_jsonl": queue_path,
        "manifest_path": manifest_path,
        "manifest": manifest,
        "proof_evidence_status": manifest["proof_evidence_status"],
    }


def _candidate_registered_obligation_ids(
    row: Mapping[str, Any],
    *,
    policy: Mapping[str, Any] | None = None,
    policy_applicability: Mapping[str, Any] | None = None,
) -> tuple[str, ...]:
    selected_policy = policy or _semantic_support_policy()
    applicability = policy_applicability or _semantic_support_policy_applicability(
        selected_policy,
        row,
    )
    if applicability.get("applicable") is not True:
        return ()
    primitive_id = str(row.get("semantic_primitive_id", "") or "").strip()
    gap_kind = str(row.get("semantic_primitive_gap_kind", "") or "").strip()
    if gap_kind == "source_to_bridge_premise_semantic_gap":
        return ()
    is_exact_goal_shape_obligation = (
        gap_kind == "source_theorem_exact_goal_shape_obligation"
        or bool(str(row.get("exact_goal_shape_obligation_id", "") or "").strip())
    )
    explicit = [
        str(value).strip()
        for value in row.get("candidate_registered_obligation_ids", []) or []
        if str(value).strip()
    ]
    exact_goal_shape_obligation_id = str(
        row.get("exact_goal_shape_obligation_id", "") or ""
    ).strip()
    candidates = list(
        explicit
        or _registered_support_for_exact_goal_shape_obligation(
            exact_goal_shape_obligation_id
        )
        or registered_support_for_semantic_primitive(primitive_id)
        or registered_support_for_semantic_primitive_text(
            primitive_id=primitive_id,
            semantic_primitive_gap=str(row.get("semantic_primitive_gap", "") or ""),
            semantic_primitive_gap_kind=gap_kind,
        )
    )
    if candidates:
        return tuple(
            dict.fromkeys(
                row
                for row in candidates
                if row in FORMAL_OBLIGATIONS
                and (
                    "source_theorem_semantic_primitive"
                    in FORMAL_OBLIGATIONS[row].tags
                    or (
                        is_exact_goal_shape_obligation
                        and "theorem_reduction_closure"
                        in FORMAL_OBLIGATIONS[row].tags
                    )
                )
            )
        )
    return ()


def _kernel_verified_ids_from_audit_payload(
    audit_payload: Mapping[str, Any] | None,
) -> tuple[str, ...]:
    if not audit_payload:
        return ()
    checks = audit_payload.get("checks", [])
    if not isinstance(checks, list):
        return ()
    return tuple(
        dict.fromkeys(
            str(row.get("obligation_id", "")).strip()
            for row in checks
            if isinstance(row, Mapping)
            and row.get("kernel_verified") is True
            and str(row.get("obligation_id", "")).strip()
        )
    )


def _export_runtime_learning_rows(
    *,
    checks: list[Mapping[str, Any]],
    out_dir: Path,
    question_id: str,
    proof_audit_manifest: Path | None,
) -> dict[str, object]:
    out_dir.mkdir(parents=True, exist_ok=True)
    verified_checks = [
        row
        for row in checks
        if row.get("kernel_verified") is True
        and row.get("kernel_verified_registered_obligation_ids")
    ]
    source_to_bridge_premise_repair_checks = [
        row
        for row in checks
        if str(row.get("semantic_primitive_gap_kind", "") or "").strip()
        == "source_to_bridge_premise_semantic_gap"
    ]
    rows: list[dict[str, Any]] = []
    for check in source_to_bridge_premise_repair_checks:
        context = _learning_check_context(check)
        premise_name = str(check.get("premise_name", "") or "")
        rows.append(
            {
                "schema_version": 1,
                "question_id": str(question_id or check.get("question_id", "") or ""),
                "learning_task": "source_to_bridge_premise_semantic_repair_feedback",
                "input_summary": {
                    **context,
                    "support_level": "source_to_bridge_premise_semantic_repair",
                    "source_theorem_ready_for_exact_proof_body": False,
                    "source_theorem_semantic_support_only": False,
                    "semantic_primitive_checks": [context],
                },
                "work_order_id": str(check.get("work_order_id", "") or ""),
                "semantic_primitive_id": str(
                    check.get("semantic_primitive_id", "") or ""
                ),
                "semantic_primitive_gap_kind": str(
                    check.get("semantic_primitive_gap_kind", "") or ""
                ),
                "semantic_primitive_gap": str(
                    check.get("semantic_primitive_gap", "") or ""
                ),
                "target_theorem_name": str(
                    check.get("target_theorem_name", "") or ""
                ),
                **_source_to_bridge_premise_context(check),
                "target_behavior": (
                    "Route this unresolved source-to-bridge premise semantic gap "
                    "upstream. TheoryDeveloper/Formalizer must supply the missing "
                    "statistical semantic assumption or lemma plan before ProofEngineer "
                    "can produce a non-vacuous Lean premise derivation"
                    + (f" for `{premise_name}`" if premise_name else "")
                    + "."
                ),
                "acceptance_gate": (
                    "A later ProofEngineer worker produces a non-vacuous premise "
                    "derivation candidate and AXLE/local Lean verifies that concrete "
                    "premise. This feedback row is not source theorem proof evidence."
                ),
                "proof_evidence_status": (
                    "SOURCE_TO_BRIDGE_PREMISE_SEMANTIC_REPAIR_FEEDBACK_NOT_PROOF_EVIDENCE"
                ),
                "proof_evidence_boundary": BOUNDARY,
            }
        )
    if verified_checks:
        kernel_ids = list(
            dict.fromkeys(
                str(value).strip()
                for row in verified_checks
                for value in row.get("kernel_verified_registered_obligation_ids", []) or []
                if str(value).strip()
            )
        )
        work_order_ids = [
            str(row.get("work_order_id", "") or "")
            for row in verified_checks
            if str(row.get("work_order_id", "") or "").strip()
        ]
        semantic_ids = [
            str(row.get("semantic_primitive_id", "") or "")
            for row in verified_checks
            if str(row.get("semantic_primitive_id", "") or "").strip()
        ]
        rows.append(
            {
                "schema_version": 1,
                "question_id": str(question_id or ""),
                "learning_task": "source_theorem_semantic_primitive_kernel_overlay",
                "input_summary": {
                    "source_theorem_semantic_primitive_work_order_ids": work_order_ids,
                    "semantic_primitive_ids": semantic_ids,
                    "kernel_verified_source_theorem_semantic_support_obligation_ids": (
                        kernel_ids
                    ),
                    "kernel_verified_source_theorem_semantic_primitive_ids": kernel_ids,
                    "kernel_verified_source_theorem_semantic_definition_ids": [],
                    "kernel_verified_proof_obligation_ids": kernel_ids,
                    "proof_audit_manifest": str(proof_audit_manifest or ""),
                    "support_level": "registered_partial_semantic_bridge",
                    "semantic_closure_status": SEMANTIC_SUPPORT_ONLY_STATUS,
                    "placeholder_definition_status": (
                        PLACEHOLDER_DEFINITION_OPEN_STATUS
                    ),
                    "source_theorem_ready_for_exact_proof_body": False,
                    "source_theorem_semantic_support_only": True,
                    "semantic_primitive_checks": [
                        _learning_check_context(row) for row in verified_checks
                    ],
                },
                "source_theorem_semantic_primitive_work_order_ids": work_order_ids,
                "semantic_primitive_ids": semantic_ids,
                "kernel_verified_source_theorem_semantic_support_obligation_ids": kernel_ids,
                "kernel_verified_source_theorem_semantic_primitive_ids": kernel_ids,
                "kernel_verified_source_theorem_semantic_definition_ids": [],
                "kernel_verified_proof_obligation_ids": kernel_ids,
                "semantic_closure_status": SEMANTIC_SUPPORT_ONLY_STATUS,
                "placeholder_definition_status": PLACEHOLDER_DEFINITION_OPEN_STATUS,
                "source_theorem_ready_for_exact_proof_body": False,
                "source_theorem_semantic_support_only": True,
                "target_behavior": (
                    "Treat listed registered source-theorem semantic bridge obligations "
                    "as kernel-verified runtime memory. Do not treat them as full source "
                    "theorem proof or as proof of unformalized exchangeability/order-statistic "
                    "definitions unless separate exact primitive rows are verified."
                ),
                "acceptance_gate": (
                    "Only registered obligations with kernel_verified=true in the referenced "
                    "proof_audit_manifest are exported."
                ),
                "boundary": BOUNDARY,
            }
        )
    learning_path = out_dir / "runtime_learning_rows.jsonl"
    _write_jsonl(learning_path, rows)
    kernel_overlay_row = next(
        (
            row
            for row in rows
            if row.get("learning_task")
            == "source_theorem_semantic_primitive_kernel_overlay"
        ),
        {},
    )
    n_premise_semantic_repair_feedback_rows = sum(
        1
        for row in rows
        if row.get("learning_task")
        == "source_to_bridge_premise_semantic_repair_feedback"
    )
    export_manifest = {
        "schema_version": 1,
        "artifact_kind": "SourceTheoremSemanticPrimitiveRuntimeLearningExportManifest",
        "proof_audit_manifest": str(proof_audit_manifest or ""),
        "runtime_learning_rows_jsonl": str(learning_path),
        "n_learning_rows": len(rows),
        "n_source_to_bridge_premise_semantic_repair_feedback_rows": (
            n_premise_semantic_repair_feedback_rows
        ),
        "kernel_verified_source_theorem_semantic_support_obligation_ids": (
            kernel_overlay_row.get(
                "kernel_verified_source_theorem_semantic_support_obligation_ids",
                [],
            )
            if kernel_overlay_row
            else []
        ),
        "kernel_verified_source_theorem_semantic_primitive_ids": (
            kernel_overlay_row.get(
                "kernel_verified_source_theorem_semantic_primitive_ids",
                [],
            )
            if kernel_overlay_row
            else []
        ),
        "kernel_verified_source_theorem_semantic_definition_ids": (
            kernel_overlay_row.get(
                "kernel_verified_source_theorem_semantic_definition_ids",
                [],
            )
            if kernel_overlay_row
            else []
        ),
        "semantic_closure_status": (
            kernel_overlay_row.get("semantic_closure_status", "")
            if kernel_overlay_row
            else "SOURCE_TO_BRIDGE_PREMISE_SEMANTIC_REPAIR_FEEDBACK_READY"
            if n_premise_semantic_repair_feedback_rows
            else "NO_RUNTIME_LEARNING_ROWS"
        ),
        "placeholder_definition_status": (
            kernel_overlay_row.get("placeholder_definition_status", "")
            if kernel_overlay_row
            else ""
        ),
        "source_theorem_ready_for_exact_proof_body": False,
        "source_theorem_semantic_support_only": bool(kernel_overlay_row),
        "source_theorem_semantic_primitive_work_order_ids": (
            kernel_overlay_row.get("source_theorem_semantic_primitive_work_order_ids", [])
            if kernel_overlay_row
            else []
        ),
        "boundary": BOUNDARY,
    }
    manifest_out = out_dir / "source_theorem_semantic_primitive_runtime_learning_export_manifest.json"
    manifest_out.write_text(
        json.dumps(export_manifest, indent=2, default=str),
        encoding="utf-8",
    )
    return {
        "rows": rows,
        "n_learning_rows": len(rows),
        "runtime_learning_rows_jsonl": learning_path,
        "export_manifest_path": manifest_out,
        "export_manifest": export_manifest,
    }


def _learning_check_context(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "work_order_id": str(row.get("work_order_id", "") or ""),
        "semantic_primitive_id": str(row.get("semantic_primitive_id", "") or ""),
        "semantic_primitive_gap_kind": str(
            row.get("semantic_primitive_gap_kind", "") or ""
        ),
        **_source_to_bridge_premise_context(row),
        "exact_goal_shape_obligation_id": str(
            row.get("exact_goal_shape_obligation_id", "") or ""
        ),
        "exact_goal_shape_obligation": str(
            row.get("exact_goal_shape_obligation", "") or ""
        ),
        "exact_goal_shape_obligation_ids": list(
            row.get("exact_goal_shape_obligation_ids", []) or []
        ),
        "exact_goal_shape_obligations": list(
            row.get("exact_goal_shape_obligations", []) or []
        ),
        "placeholder_symbol": str(row.get("placeholder_symbol", "") or ""),
        "target_theorem_name": str(row.get("target_theorem_name", "") or ""),
        "target_theorem_goal_ids": list(row.get("target_theorem_goal_ids", []) or []),
        "source_theorem_target_known": _bool_like(
            row.get("source_theorem_target_known", False)
        ),
        "source_theorem_target_provenance": dict(
            row.get("source_theorem_target_provenance", {}) or {}
        ),
        "semantic_alignment_constraints": list(
            row.get("semantic_alignment_constraints", []) or []
        ),
        "candidate_artifact_path": str(row.get("candidate_artifact_path", "") or ""),
        "formal_environment_typeclass_blockers": list(
            row.get("formal_environment_typeclass_blockers", []) or []
        ),
        "proof_body_attempted": _bool_like(row.get("proof_body_attempted", False)),
        "proof_body_attempt_success": _bool_like(
            row.get("proof_body_attempt_success", False)
        ),
        "proof_body_attempt_summaries": list(
            row.get("proof_body_attempt_summaries", []) or []
        ),
        "proof_body_goal_excerpt": list(row.get("proof_body_goal_excerpt", []) or []),
        "kernel_verified_registered_obligation_ids": list(
            row.get("kernel_verified_registered_obligation_ids", []) or []
        ),
        "semantic_closure_status": str(
            row.get("semantic_closure_status", "") or ""
        ),
        "placeholder_definition_status": str(
            row.get("placeholder_definition_status", "") or ""
        ),
        "source_theorem_ready_for_exact_proof_body": _bool_like(
            row.get("source_theorem_ready_for_exact_proof_body", False)
        ),
        "source_theorem_semantic_support_only": _bool_like(
            row.get("source_theorem_semantic_support_only", False)
        ),
        "kernel_verified_source_theorem_semantic_definition_ids": list(
            row.get("kernel_verified_source_theorem_semantic_definition_ids", [])
            or []
        ),
    }


def _source_to_bridge_premise_context(row: Mapping[str, Any]) -> dict[str, Any]:
    context: dict[str, Any] = {}
    for key in _SOURCE_TO_BRIDGE_PREMISE_CONTEXT_KEYS:
        context[key] = str(row.get(key, "") or "")
    for key in _SOURCE_TO_BRIDGE_PREMISE_CONTEXT_LIST_KEYS:
        values = row.get(key, []) or []
        if key in {"exact_source_theorem_binders", "premise_semantic_anchor_binders"}:
            context[key] = [dict(value) for value in values if isinstance(value, Mapping)]
        else:
            context[key] = [
                str(value).strip()
                for value in values
                if str(value).strip()
            ]
    return context


def _merged_string_values(
    primary: Mapping[str, Any],
    secondary: Mapping[str, Any],
    key: str,
) -> list[str]:
    values: list[str] = []
    for source in (primary, secondary):
        for value in source.get(key, []) or []:
            text = str(value).strip()
            if text and text not in values:
                values.append(text)
    return values


def _string_values(row: Mapping[str, Any], key: str) -> list[str]:
    return [
        str(value).strip()
        for value in row.get(key, []) or []
        if str(value).strip()
    ]


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_no, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"{path}:{line_no}: expected JSON object row")
        rows.append(value)
    return rows


def _write_jsonl(path: Path, rows: list[Mapping[str, Any]]) -> None:
    path.write_text(
        "".join(json.dumps(dict(row), sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def _work_order_id(row: Mapping[str, Any]) -> str:
    return str(row.get("work_order_id", "") or "").strip()
