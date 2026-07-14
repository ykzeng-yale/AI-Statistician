from __future__ import annotations

import json
import re
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, Mapping


_POLICY_PACK_GLOB = (
    "source_theorem_exact_semantic_definition_placeholders.*.json"
)


@dataclass(frozen=True)
class ExactSemanticDefinitionCandidateRiskRule:
    message: str
    scope: str = "definition_block"
    present_any: tuple[str, ...] = ()
    present_all: tuple[str, ...] = ()
    absent_all: tuple[str, ...] = ()
    absent_regex_all: tuple[str, ...] = ()
    case_sensitive: bool = True


@dataclass(frozen=True)
class ExactSemanticDefinitionPlaceholderPolicy:
    policy_id: str
    policy_scope: str
    placeholder_key: str
    semantic_goal: str
    task_families: tuple[str, ...] = ()
    question_ids: tuple[str, ...] = ()
    theorem_target_ids: tuple[str, ...] = ()
    placeholder_aliases: tuple[str, ...] = ()
    required_anchor_names: tuple[str, ...] = ()
    required_adapter_object_names: tuple[str, ...] = ()
    semantic_import_incompatible_terms: tuple[str, ...] = ()
    semantic_import_incompatible_status: str = (
        "SEMANTIC_MISMATCH_NOT_EXACT_SEMANTIC_DEFINITION"
    )
    semantic_import_incompatible_reason: str = ""
    semantic_import_required_signal_terms: tuple[str, ...] = ()
    semantic_import_allowed_declaration_names: tuple[str, ...] = ()
    semantic_import_allowed_declaration_prefixes: tuple[str, ...] = ()
    semantic_import_missing_required_signal_status: str = (
        "SEMANTIC_REVIEW_REQUIRED_EXACT_SEMANTIC_SIGNAL_NOT_EXPOSED"
    )
    semantic_import_missing_required_signal_reason: str = ""
    formal_environment_symbol_names: tuple[str, ...] = ()
    formal_environment_search_queries: tuple[str, ...] = ()
    formal_environment_preferred_resolution: str = ""
    formal_environment_signature_probe_fallback: str = ""
    formal_environment_promotion_blocker: str = ""
    source_lookup_search_terms: tuple[str, ...] = ()
    source_lookup_aliases: tuple[str, ...] = ()
    definition_contract: Mapping[str, Any] = field(default_factory=dict)
    source_to_bridge_premise_aliases: tuple[str, ...] = ()
    source_to_bridge_dependency_requirements: tuple[str, ...] = ()
    source_to_bridge_required_anchor_names: tuple[str, ...] = ()
    source_anchor_roles: Mapping[str, str] = field(default_factory=dict)
    candidate_risk_rules: tuple[
        ExactSemanticDefinitionCandidateRiskRule,
        ...,
    ] = ()


@dataclass(frozen=True)
class ExactSemanticDefinitionSourceAnchorRoleRule:
    role: str
    name_keys: tuple[str, ...] = ()
    name_prefixes: tuple[str, ...] = ()
    binder_type_contains: tuple[str, ...] = ()
    case_sensitive_binder_type: bool = True


def compact_exact_semantic_placeholder_key(value: str) -> str:
    return "".join(ch.lower() for ch in str(value or "") if ch.isalnum())


_GENERIC_POLICY = ExactSemanticDefinitionPlaceholderPolicy(
    policy_id="generic_exact_semantic_definition_placeholder",
    policy_scope="generic",
    placeholder_key="",
    semantic_goal=(
        "Define the exact semantic replacement for the placeholder from the "
        "listed source theorem binders and semantic constraints."
    ),
)


def _registry_from_policies(
    policies: tuple[ExactSemanticDefinitionPlaceholderPolicy, ...],
) -> dict[str, ExactSemanticDefinitionPlaceholderPolicy]:
    registry: dict[str, ExactSemanticDefinitionPlaceholderPolicy] = {}
    for policy in policies:
        keys = (policy.placeholder_key, *policy.placeholder_aliases)
        for key in keys:
            compact_key = compact_exact_semantic_placeholder_key(key)
            if compact_key:
                registry[compact_key] = policy
    return registry


def _load_policy_pack_policies() -> tuple[
    tuple[ExactSemanticDefinitionPlaceholderPolicy, ...],
    tuple[str, ...],
    tuple[ExactSemanticDefinitionSourceAnchorRoleRule, ...],
    tuple[dict[str, Any], ...],
    tuple[str, ...],
    tuple[dict[str, Any], ...],
    str,
]:
    policy_dir = Path(__file__).resolve().parent / "policies"
    if not policy_dir.exists():
        return (), (), (), (), (), (), "source_parameter"
    policies: list[ExactSemanticDefinitionPlaceholderPolicy] = []
    policy_pack_ids: list[str] = []
    source_anchor_role_rules: list[ExactSemanticDefinitionSourceAnchorRoleRule] = []
    statement_repair_rules: list[dict[str, Any]] = []
    adapter_object_names: list[str] = []
    semantic_anchor_fallback_rules: list[dict[str, Any]] = []
    default_source_anchor_role = "source_parameter"
    for path in sorted(policy_dir.glob(_POLICY_PACK_GLOB)):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, Mapping):
            raise ValueError(f"policy pack must be a JSON object: {path}")
        policy_pack_id = str(payload.get("policy_pack_id", "") or "").strip()
        if policy_pack_id:
            policy_pack_ids.append(policy_pack_id)
        pack_scope = str(payload.get("scope", "") or "").strip()
        pack_task_families = list(_string_tuple(payload.get("task_families")))
        if pack_scope.lower().startswith("task_family:"):
            scope_family = pack_scope.split(":", 1)[1].strip()
            if scope_family:
                pack_task_families.append(scope_family)
        pack_question_ids = _string_tuple(payload.get("question_ids"))
        pack_theorem_target_ids = _string_tuple(
            payload.get("theorem_target_ids")
        )
        source_anchor_role_rules.extend(
            _source_anchor_role_rule_from_mapping(row)
            for row in payload.get("source_anchor_role_fallback_rules", [])
            if isinstance(row, Mapping)
        )
        default_role = str(
            payload.get("default_source_anchor_role", "") or ""
        ).strip()
        if default_role:
            default_source_anchor_role = default_role
        adapter_object_names.extend(
            _string_tuple(
                payload.get(
                    "source_to_bridge_adapter_object_names_requiring_source_instantiation"
                )
            )
        )
        semantic_anchor_fallback_rules.extend(
            _source_to_bridge_semantic_anchor_fallback_rule_from_mapping(row)
            for row in payload.get(
                "source_to_bridge_semantic_anchor_fallback_rules",
                [],
            )
            if isinstance(row, Mapping)
        )
        statement_repair_rules.extend(
            _formal_environment_statement_repair_rule_from_mapping(row)
            for row in payload.get("formal_environment_statement_repair_rules", [])
            if isinstance(row, Mapping)
        )
        raw_policies = payload.get("placeholder_policies", [])
        if not isinstance(raw_policies, list):
            raise ValueError(
                "policy pack placeholder_policies must be a list: "
                f"{path}"
            )
        policies.extend(
            _policy_from_mapping(
                row,
                source_path=path,
                pack_task_families=tuple(dict.fromkeys(pack_task_families)),
                pack_question_ids=pack_question_ids,
                pack_theorem_target_ids=pack_theorem_target_ids,
            )
            for row in raw_policies
            if isinstance(row, Mapping)
        )
    return (
        tuple(policies),
        tuple(dict.fromkeys(policy_pack_ids)),
        tuple(source_anchor_role_rules),
        tuple(statement_repair_rules),
        tuple(dict.fromkeys(adapter_object_names)),
        tuple(semantic_anchor_fallback_rules),
        default_source_anchor_role,
    )


def _policy_from_mapping(
    row: Mapping[str, Any],
    *,
    source_path: Path,
    pack_task_families: tuple[str, ...] = (),
    pack_question_ids: tuple[str, ...] = (),
    pack_theorem_target_ids: tuple[str, ...] = (),
) -> ExactSemanticDefinitionPlaceholderPolicy:
    def required_text(key: str) -> str:
        text = str(row.get(key, "") or "").strip()
        if not text:
            raise ValueError(f"policy pack {source_path} missing {key}")
        return text

    return ExactSemanticDefinitionPlaceholderPolicy(
        policy_id=required_text("policy_id"),
        policy_scope=required_text("policy_scope"),
        placeholder_key=required_text("placeholder_key"),
        semantic_goal=required_text("semantic_goal"),
        task_families=tuple(
            dict.fromkeys(
                [
                    *pack_task_families,
                    *_string_tuple(row.get("task_families")),
                ]
            )
        ),
        question_ids=tuple(
            dict.fromkeys(
                [
                    *pack_question_ids,
                    *_string_tuple(row.get("question_ids")),
                ]
            )
        ),
        theorem_target_ids=tuple(
            dict.fromkeys(
                [
                    *pack_theorem_target_ids,
                    *_string_tuple(row.get("theorem_target_ids")),
                ]
            )
        ),
        placeholder_aliases=_string_tuple(row.get("placeholder_aliases")),
        required_anchor_names=_string_tuple(row.get("required_anchor_names")),
        required_adapter_object_names=_string_tuple(
            row.get("required_adapter_object_names")
        ),
        semantic_import_incompatible_terms=_string_tuple(
            row.get("semantic_import_incompatible_terms")
        ),
        semantic_import_incompatible_status=str(
            row.get(
                "semantic_import_incompatible_status",
                "SEMANTIC_MISMATCH_NOT_EXACT_SEMANTIC_DEFINITION",
            )
            or "SEMANTIC_MISMATCH_NOT_EXACT_SEMANTIC_DEFINITION"
        ),
        semantic_import_incompatible_reason=str(
            row.get("semantic_import_incompatible_reason", "") or ""
        ),
        semantic_import_required_signal_terms=_string_tuple(
            row.get("semantic_import_required_signal_terms")
        ),
        semantic_import_allowed_declaration_names=_string_tuple(
            row.get("semantic_import_allowed_declaration_names")
        ),
        semantic_import_allowed_declaration_prefixes=_string_tuple(
            row.get("semantic_import_allowed_declaration_prefixes")
        ),
        semantic_import_missing_required_signal_status=str(
            row.get(
                "semantic_import_missing_required_signal_status",
                "SEMANTIC_REVIEW_REQUIRED_EXACT_SEMANTIC_SIGNAL_NOT_EXPOSED",
            )
            or "SEMANTIC_REVIEW_REQUIRED_EXACT_SEMANTIC_SIGNAL_NOT_EXPOSED"
        ),
        semantic_import_missing_required_signal_reason=str(
            row.get("semantic_import_missing_required_signal_reason", "") or ""
        ),
        formal_environment_symbol_names=_string_tuple(
            row.get("formal_environment_symbol_names")
        ),
        formal_environment_search_queries=_string_tuple(
            row.get("formal_environment_search_queries")
        ),
        formal_environment_preferred_resolution=str(
            row.get("formal_environment_preferred_resolution", "") or ""
        ),
        formal_environment_signature_probe_fallback=str(
            row.get("formal_environment_signature_probe_fallback", "") or ""
        ),
        formal_environment_promotion_blocker=str(
            row.get("formal_environment_promotion_blocker", "") or ""
        ),
        source_lookup_search_terms=_string_tuple(
            row.get("source_lookup_search_terms")
        ),
        source_lookup_aliases=_string_tuple(row.get("source_lookup_aliases")),
        definition_contract=_mapping_or_empty(row.get("definition_contract")),
        source_to_bridge_premise_aliases=_string_tuple(
            row.get("source_to_bridge_premise_aliases")
        ),
        source_to_bridge_dependency_requirements=_string_tuple(
            row.get("source_to_bridge_dependency_requirements")
        ),
        source_to_bridge_required_anchor_names=_string_tuple(
            row.get("source_to_bridge_required_anchor_names")
        ),
        source_anchor_roles=_string_mapping(row.get("source_anchor_roles")),
        candidate_risk_rules=tuple(
            _risk_rule_from_mapping(rule)
            for rule in row.get("candidate_risk_rules", [])
            if isinstance(rule, Mapping)
        ),
    )


def _formal_environment_statement_repair_rule_from_mapping(
    row: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "rule_id": str(row.get("rule_id", "") or "").strip(),
        "typeclass_blocker_contains_any": _string_tuple(
            row.get("typeclass_blocker_contains_any")
        ),
        "missing_symbol_keys_any": _string_tuple(row.get("missing_symbol_keys_any")),
        "diagnosis": str(row.get("diagnosis", "") or ""),
        "repair_hint": str(row.get("repair_hint", "") or ""),
        "example_target_shape": str(row.get("example_target_shape", "") or ""),
        "honesty_boundary": str(row.get("honesty_boundary", "") or ""),
    }


def _source_to_bridge_semantic_anchor_fallback_rule_from_mapping(
    row: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "rule_id": str(row.get("rule_id", "") or "").strip(),
        "text_contains_any": _string_tuple(row.get("text_contains_any")),
        "anchor_names": _string_tuple(row.get("anchor_names")),
        "case_sensitive": _bool_like(
            row.get("case_sensitive", False),
            default=False,
        ),
    }


def _risk_rule_from_mapping(
    row: Mapping[str, Any],
) -> ExactSemanticDefinitionCandidateRiskRule:
    return ExactSemanticDefinitionCandidateRiskRule(
        message=str(row.get("message", "") or ""),
        scope=str(row.get("scope", "definition_block") or "definition_block"),
        present_any=_string_tuple(row.get("present_any")),
        present_all=_string_tuple(row.get("present_all")),
        absent_all=_string_tuple(row.get("absent_all")),
        absent_regex_all=_string_tuple(row.get("absent_regex_all")),
        case_sensitive=_bool_like(row.get("case_sensitive", True), default=True),
    )


def _source_anchor_role_rule_from_mapping(
    row: Mapping[str, Any],
) -> ExactSemanticDefinitionSourceAnchorRoleRule:
    return ExactSemanticDefinitionSourceAnchorRoleRule(
        role=str(row.get("role", "") or "").strip(),
        name_keys=_string_tuple(row.get("name_keys")),
        name_prefixes=_string_tuple(row.get("name_prefixes")),
        binder_type_contains=_string_tuple(row.get("binder_type_contains")),
        case_sensitive_binder_type=_bool_like(
            row.get("case_sensitive_binder_type", True),
            default=True,
        ),
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


def _string_tuple(value: Any) -> tuple[str, ...]:
    if isinstance(value, str):
        items: list[Any] = [value]
    elif isinstance(value, (list, tuple)):
        items = list(value)
    else:
        items = []
    strings: list[str] = []
    for item in items:
        if item is None:
            continue
        text = str(item).strip()
        if text:
            strings.append(text)
    return tuple(strings)


def _mapping_or_empty(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _string_mapping(value: Any) -> Mapping[str, str]:
    if not isinstance(value, Mapping):
        return {}
    rows: dict[str, str] = {}
    for key, child in value.items():
        text_key = str(key or "").strip()
        text_value = str(child or "").strip()
        if text_key and text_value:
            rows[text_key] = text_value
    return rows


def _build_policy_registry() -> tuple[
    Mapping[str, ExactSemanticDefinitionPlaceholderPolicy],
    tuple[str, ...],
    tuple[ExactSemanticDefinitionSourceAnchorRoleRule, ...],
    tuple[dict[str, Any], ...],
    tuple[str, ...],
    tuple[dict[str, Any], ...],
    str,
]:
    registry: dict[str, ExactSemanticDefinitionPlaceholderPolicy] = {}
    (
        policy_pack_policies,
        policy_pack_ids,
        source_anchor_role_rules,
        formal_environment_statement_repair_rules,
        source_to_bridge_adapter_object_names,
        source_to_bridge_semantic_anchor_fallback_rules,
        default_source_anchor_role,
    ) = _load_policy_pack_policies()
    if policy_pack_policies:
        registry.update(_registry_from_policies(policy_pack_policies))
    return (
        registry,
        policy_pack_ids,
        source_anchor_role_rules,
        formal_environment_statement_repair_rules,
        source_to_bridge_adapter_object_names,
        source_to_bridge_semantic_anchor_fallback_rules,
        default_source_anchor_role,
    )


(
    EXACT_SEMANTIC_DEFINITION_PLACEHOLDER_POLICIES,
    EXACT_SEMANTIC_DEFINITION_POLICY_PACK_IDS,
    EXACT_SEMANTIC_DEFINITION_SOURCE_ANCHOR_ROLE_RULES,
    EXACT_SEMANTIC_DEFINITION_FORMAL_ENVIRONMENT_STATEMENT_REPAIR_RULES,
    EXACT_SEMANTIC_DEFINITION_SOURCE_TO_BRIDGE_ADAPTER_OBJECT_NAMES,
    EXACT_SEMANTIC_DEFINITION_SOURCE_TO_BRIDGE_SEMANTIC_ANCHOR_FALLBACK_RULES,
    EXACT_SEMANTIC_DEFINITION_DEFAULT_SOURCE_ANCHOR_ROLE,
) = _build_policy_registry()


def exact_semantic_definition_policy_pack_ids() -> tuple[str, ...]:
    return EXACT_SEMANTIC_DEFINITION_POLICY_PACK_IDS


def exact_semantic_definition_source_anchor_role_rules() -> tuple[
    ExactSemanticDefinitionSourceAnchorRoleRule,
    ...,
]:
    return EXACT_SEMANTIC_DEFINITION_SOURCE_ANCHOR_ROLE_RULES


def exact_semantic_definition_formal_environment_statement_repair_rules() -> tuple[
    dict[str, Any],
    ...,
]:
    return EXACT_SEMANTIC_DEFINITION_FORMAL_ENVIRONMENT_STATEMENT_REPAIR_RULES


def exact_semantic_definition_source_to_bridge_adapter_object_names_requiring_source_instantiation() -> tuple[
    str,
    ...,
]:
    return EXACT_SEMANTIC_DEFINITION_SOURCE_TO_BRIDGE_ADAPTER_OBJECT_NAMES


def exact_semantic_definition_proof_body_adapter_synthesis_instruction() -> str:
    adapter_names = (
        exact_semantic_definition_source_to_bridge_adapter_object_names_requiring_source_instantiation()
    )
    adapter_text = ", ".join(adapter_names) if adapter_names else "the policy-listed"
    return (
        "Route to ProofEngineer adapter synthesis: the verified theorem-reduction "
        "closure declaration is available, but direct exact/simpa attempts do not "
        "instantiate it against the exact source theorem. Build a source-to-closure "
        f"adapter that supplies policy-listed source instantiations for {adapter_text} "
        "and bridges ENNReal/real-valued coverage before retrying the exact theorem."
    )


def exact_semantic_definition_source_to_bridge_premise_aliases() -> tuple[str, ...]:
    aliases: list[str] = []
    seen_policy_ids: set[str] = set()
    for policy in EXACT_SEMANTIC_DEFINITION_PLACEHOLDER_POLICIES.values():
        if policy.policy_id in seen_policy_ids:
            continue
        seen_policy_ids.add(policy.policy_id)
        aliases.extend(policy.source_to_bridge_premise_aliases)
    return tuple(dict.fromkeys(alias for alias in aliases if alias))


def exact_semantic_definition_source_to_bridge_premise_binder_aliases() -> tuple[
    str,
    ...,
]:
    semantic_object_keys = {
        compact_exact_semantic_placeholder_key(name)
        for name in EXACT_SEMANTIC_DEFINITION_SOURCE_TO_BRIDGE_ADAPTER_OBJECT_NAMES
    }
    seen_policy_ids: set[str] = set()
    for policy in EXACT_SEMANTIC_DEFINITION_PLACEHOLDER_POLICIES.values():
        if policy.policy_id in seen_policy_ids:
            continue
        seen_policy_ids.add(policy.policy_id)
        semantic_object_keys.add(
            compact_exact_semantic_placeholder_key(policy.placeholder_key)
        )
        semantic_object_keys.update(
            compact_exact_semantic_placeholder_key(alias)
            for alias in policy.placeholder_aliases
        )
        semantic_object_keys.update(
            compact_exact_semantic_placeholder_key(name)
            for name in policy.required_adapter_object_names
        )
    aliases = [
        alias
        for alias in exact_semantic_definition_source_to_bridge_premise_aliases()
        if compact_exact_semantic_placeholder_key(alias)
        not in semantic_object_keys
    ]
    return tuple(dict.fromkeys(aliases))


def exact_semantic_definition_source_to_bridge_source_anchor_terms() -> tuple[
    str,
    ...,
]:
    terms: list[str] = []
    seen_policy_ids: set[str] = set()
    for policy in EXACT_SEMANTIC_DEFINITION_PLACEHOLDER_POLICIES.values():
        if policy.policy_id in seen_policy_ids:
            continue
        seen_policy_ids.add(policy.policy_id)
        terms.extend(policy.required_anchor_names)
        terms.extend(policy.source_to_bridge_required_anchor_names)
        terms.extend(policy.source_anchor_roles.keys())
    for rule in EXACT_SEMANTIC_DEFINITION_SOURCE_ANCHOR_ROLE_RULES:
        terms.extend(rule.name_keys)
        terms.extend(rule.name_prefixes)
        terms.extend(rule.binder_type_contains)
    for rule in EXACT_SEMANTIC_DEFINITION_SOURCE_TO_BRIDGE_SEMANTIC_ANCHOR_FALLBACK_RULES:
        terms.extend(str(value or "") for value in rule.get("text_contains_any", ()))
        terms.extend(str(value or "") for value in rule.get("anchor_names", ()))
    return tuple(dict.fromkeys(term for term in terms if term))


def exact_semantic_definition_source_to_bridge_semantic_terms() -> tuple[str, ...]:
    terms: list[str] = [
        *EXACT_SEMANTIC_DEFINITION_SOURCE_TO_BRIDGE_ADAPTER_OBJECT_NAMES,
    ]
    seen_policy_ids: set[str] = set()
    for policy in EXACT_SEMANTIC_DEFINITION_PLACEHOLDER_POLICIES.values():
        if policy.policy_id in seen_policy_ids:
            continue
        seen_policy_ids.add(policy.policy_id)
        terms.extend(
            (
                policy.placeholder_key,
                policy.semantic_goal,
                *policy.placeholder_aliases,
                *policy.required_adapter_object_names,
                *policy.semantic_import_required_signal_terms,
                *policy.source_lookup_search_terms,
                *policy.source_lookup_aliases,
                *policy.source_to_bridge_premise_aliases,
                *policy.source_to_bridge_dependency_requirements,
            )
        )
    return tuple(dict.fromkeys(term for term in terms if term))


def exact_semantic_definition_source_to_bridge_anchor_fallback_names(
    *,
    premise_name: str,
    premise_target_type: str,
    semantic_requirements: tuple[str, ...] = (),
) -> tuple[str, ...]:
    text = " ".join(
        [
            str(premise_name or ""),
            str(premise_target_type or ""),
            *(str(value or "") for value in semantic_requirements),
        ]
    )
    names: list[str] = []
    for rule in EXACT_SEMANTIC_DEFINITION_SOURCE_TO_BRIDGE_SEMANTIC_ANCHOR_FALLBACK_RULES:
        case_sensitive = _bool_like(rule.get("case_sensitive", False), default=False)
        haystack = text if case_sensitive else text.lower()
        terms = tuple(str(value or "") for value in rule.get("text_contains_any", ()))
        if not case_sensitive:
            terms = tuple(value.lower() for value in terms)
        if terms and not any(term and term in haystack for term in terms):
            continue
        for anchor_name in rule.get("anchor_names", ()) or ():
            value = str(anchor_name or "").strip()
            if value and value not in names:
                names.append(value)
    return tuple(names)


def exact_semantic_definition_formal_environment_symbol_names() -> tuple[str, ...]:
    names: list[str] = []
    seen_policy_ids: set[str] = set()
    for policy in EXACT_SEMANTIC_DEFINITION_PLACEHOLDER_POLICIES.values():
        if policy.policy_id in seen_policy_ids:
            continue
        seen_policy_ids.add(policy.policy_id)
        names.extend(policy.formal_environment_symbol_names)
    return tuple(dict.fromkeys(name for name in names if name))


def exact_semantic_definition_formal_environment_declaration_hint(
    placeholder_symbol: str,
) -> dict[str, Any]:
    policy = exact_semantic_definition_placeholder_policy(placeholder_symbol)
    symbol = str(placeholder_symbol or "").strip()
    search_queries = (
        policy.formal_environment_search_queries
        or policy.source_lookup_search_terms
        or policy.source_lookup_aliases
    )
    preferred_resolution = (
        policy.formal_environment_preferred_resolution
        or f"search existing Lean sources before drafting `{symbol}`"
    )
    signature_probe_fallback = (
        policy.formal_environment_signature_probe_fallback
        or (
            "if no declaration exists, draft the narrowest local declaration "
            "needed to typecheck the source theorem and mark it as unproved"
        )
    )
    promotion_blocker = (
        policy.formal_environment_promotion_blocker
        or (
            "local declaration drafts are routing evidence only until reviewed "
            "and kernel verified in the target library"
        )
    )
    return {
        "symbol": symbol,
        "placeholder_policy_id": policy.policy_id,
        "placeholder_policy_scope": policy.policy_scope,
        "search_queries": list(search_queries),
        "preferred_resolution": preferred_resolution,
        "signature_probe_fallback": signature_probe_fallback,
        "promotion_blocker": promotion_blocker,
    }


def exact_semantic_definition_fallback_source_anchor_role(
    *,
    name: str,
    binder_type: str = "",
) -> str:
    compact_name = compact_exact_semantic_placeholder_key(name)
    type_text = str(binder_type or "")
    for rule in EXACT_SEMANTIC_DEFINITION_SOURCE_ANCHOR_ROLE_RULES:
        if not rule.role:
            continue
        compact_keys = {
            compact_exact_semantic_placeholder_key(value)
            for value in rule.name_keys
            if compact_exact_semantic_placeholder_key(value)
        }
        if compact_name and compact_name in compact_keys:
            return rule.role
        compact_prefixes = tuple(
            compact_exact_semantic_placeholder_key(value)
            for value in rule.name_prefixes
            if compact_exact_semantic_placeholder_key(value)
        )
        if compact_name and any(
            compact_name.startswith(prefix) for prefix in compact_prefixes
        ):
            return rule.role
        if _binder_type_contains_any(
            type_text,
            rule.binder_type_contains,
            case_sensitive=rule.case_sensitive_binder_type,
        ):
            return rule.role
    return EXACT_SEMANTIC_DEFINITION_DEFAULT_SOURCE_ANCHOR_ROLE


def _binder_type_contains_any(
    binder_type: str,
    needles: tuple[str, ...],
    *,
    case_sensitive: bool,
) -> bool:
    if not needles:
        return False
    haystack = str(binder_type or "")
    if not case_sensitive:
        haystack = haystack.lower()
    for needle in needles:
        item = str(needle or "")
        if not item:
            continue
        if not case_sensitive:
            item = item.lower()
        if item in haystack:
            return True
    return False


def exact_semantic_definition_placeholder_policy(
    placeholder_symbol: str,
) -> ExactSemanticDefinitionPlaceholderPolicy:
    key = compact_exact_semantic_placeholder_key(placeholder_symbol)
    policy = EXACT_SEMANTIC_DEFINITION_PLACEHOLDER_POLICIES.get(key)
    if policy is not None:
        return policy
    return replace(_GENERIC_POLICY, placeholder_key=key)


def exact_semantic_definition_policy_applicability(
    policy: ExactSemanticDefinitionPlaceholderPolicy,
    *,
    task_family: str = "",
    question_id: str = "",
    theorem_target_ids: tuple[str, ...] = (),
) -> dict[str, Any]:
    """Require explicit, nonconflicting selectors before using a policy pack."""

    allowed = {
        "task_family": {
            str(value).strip().lower()
            for value in policy.task_families
            if str(value).strip()
        },
        "question_id": {
            str(value).strip().lower()
            for value in policy.question_ids
            if str(value).strip()
        },
        "theorem_target_id": {
            str(value).strip().lower()
            for value in policy.theorem_target_ids
            if str(value).strip()
        },
    }
    observed = {
        "task_family": (
            {str(task_family).strip().lower()}
            if str(task_family).strip()
            else set()
        ),
        "question_id": (
            {str(question_id).strip().lower()}
            if str(question_id).strip()
            else set()
        ),
        "theorem_target_id": {
            str(value).strip().lower()
            for value in theorem_target_ids
            if str(value).strip()
        },
    }
    matched: list[str] = []
    conflicting: list[str] = []
    for selector_kind, allowed_values in allowed.items():
        observed_values = observed[selector_kind]
        if not allowed_values or not observed_values:
            continue
        if allowed_values & observed_values:
            matched.append(selector_kind)
        else:
            conflicting.append(selector_kind)
    applicable = bool(matched) and not conflicting
    return {
        "policy_id": policy.policy_id,
        "applicable": applicable,
        "status": (
            "TASK_SCOPED_POLICY_APPLICABLE"
            if applicable
            else "TASK_SCOPED_POLICY_CONFLICT"
            if conflicting
            else "TASK_SCOPED_POLICY_SELECTOR_MISSING"
        ),
        "matched_selector_kinds": matched,
        "conflicting_selector_kinds": conflicting,
        "observed_task_families": sorted(observed["task_family"]),
        "observed_question_ids": sorted(observed["question_id"]),
        "observed_theorem_target_ids": sorted(observed["theorem_target_id"]),
    }


def exact_semantic_definition_placeholder_policy_for_context(
    placeholder_symbol: str,
    *,
    task_family: str = "",
    question_id: str = "",
    theorem_target_ids: tuple[str, ...] = (),
) -> tuple[ExactSemanticDefinitionPlaceholderPolicy, dict[str, Any]]:
    candidate = exact_semantic_definition_placeholder_policy(placeholder_symbol)
    if candidate.policy_id == _GENERIC_POLICY.policy_id:
        return candidate, {
            "policy_id": candidate.policy_id,
            "applicable": True,
            "status": "GENERIC_DISCOVERY_POLICY",
            "matched_selector_kinds": [],
            "conflicting_selector_kinds": [],
        }
    applicability = exact_semantic_definition_policy_applicability(
        candidate,
        task_family=task_family,
        question_id=question_id,
        theorem_target_ids=theorem_target_ids,
    )
    if applicability["applicable"]:
        return candidate, applicability
    return (
        replace(
            _GENERIC_POLICY,
            placeholder_key=compact_exact_semantic_placeholder_key(
                placeholder_symbol
            ),
        ),
        applicability,
    )


def exact_semantic_definition_import_policy_blocker(
    placeholder_symbol: str,
    *,
    snippet: str = "",
    declaration_name: str = "",
    require_required_signal: bool = False,
) -> dict[str, str]:
    policy = exact_semantic_definition_placeholder_policy(placeholder_symbol)
    snippet_text = str(snippet or "")
    declaration_text = str(declaration_name or "")
    snippet_key = compact_exact_semantic_placeholder_key(snippet_text)
    declaration_key = compact_exact_semantic_placeholder_key(declaration_text)
    haystack = f"{declaration_key} {snippet_key}"
    incompatible_terms = tuple(
        compact_exact_semantic_placeholder_key(term)
        for term in policy.semantic_import_incompatible_terms
        if compact_exact_semantic_placeholder_key(term)
    )
    if incompatible_terms and any(term in haystack for term in incompatible_terms):
        return {
            "source_semantic_review_status": (
                policy.semantic_import_incompatible_status
            ),
            "source_semantic_review_reason": (
                policy.semantic_import_incompatible_reason
                or "candidate declaration is incompatible with the placeholder policy"
            ),
        }
    if require_required_signal and not _semantic_import_required_signal_present(
        policy,
        snippet=snippet_text,
        declaration_name=declaration_text,
    ):
        return {
            "source_semantic_review_status": (
                policy.semantic_import_missing_required_signal_status
            ),
            "source_semantic_review_reason": (
                policy.semantic_import_missing_required_signal_reason
                or "candidate declaration does not expose a required semantic signal"
            ),
        }
    return {}


def exact_semantic_definition_source_lookup_terms(
    placeholder_symbol: str,
) -> tuple[str, ...]:
    policy = exact_semantic_definition_placeholder_policy(placeholder_symbol)
    return policy.source_lookup_search_terms


def exact_semantic_definition_source_lookup_aliases(
    placeholder_symbol: str,
    *,
    policy: ExactSemanticDefinitionPlaceholderPolicy | None = None,
) -> tuple[str, ...]:
    selected_policy = policy or exact_semantic_definition_placeholder_policy(
        placeholder_symbol
    )
    aliases = [
        str(placeholder_symbol or "").strip(),
        selected_policy.placeholder_key,
        *selected_policy.source_lookup_search_terms,
        *selected_policy.source_lookup_aliases,
    ]
    return tuple(dict.fromkeys(alias for alias in aliases if alias))


def exact_semantic_definition_contract(
    placeholder_symbol: str,
    *,
    policy: ExactSemanticDefinitionPlaceholderPolicy | None = None,
) -> dict[str, Any]:
    selected_policy = policy or exact_semantic_definition_placeholder_policy(
        placeholder_symbol
    )
    if selected_policy.definition_contract:
        return {
            str(key): _copy_contract_value(value)
            for key, value in selected_policy.definition_contract.items()
        }
    placeholder = str(placeholder_symbol or "").strip()
    return {
        "semantic_intent": (
            "review or synthesize the exact Lean semantics needed to replace the "
            f"`{placeholder}` placeholder"
        ),
        "lean_target_shape": "minimal reviewed Lean declaration matching the source theorem",
        "required_properties": [
            "matches the source theorem statement",
            "supports downstream local Lean/AXLE verification",
        ],
        "forbidden_shortcuts": [
            "do not define the placeholder as True",
            "do not add axiom/sorry/admit/unsafe",
            "do not assume the target theorem",
        ],
    }


def _copy_contract_value(value: Any) -> Any:
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return {str(key): _copy_contract_value(item) for key, item in value.items()}
    return value


def exact_semantic_definition_candidate_risks(
    placeholder_symbol: str,
    *,
    definition_block: str,
) -> list[str]:
    policy = exact_semantic_definition_placeholder_policy(placeholder_symbol)
    risks = [
        rule.message
        for rule in policy.candidate_risk_rules
        if _candidate_risk_rule_matches(
            rule,
            definition_block=definition_block,
        )
    ]
    return list(dict.fromkeys(risks))


def _candidate_risk_rule_matches(
    rule: ExactSemanticDefinitionCandidateRiskRule,
    *,
    definition_block: str,
) -> bool:
    target = (
        definition_block.split(":=", 1)[1]
        if rule.scope == "definition_body" and ":=" in definition_block
        else definition_block
    )
    if not rule.case_sensitive:
        target_for_terms = target.lower()
        present_any = tuple(value.lower() for value in rule.present_any)
        present_all = tuple(value.lower() for value in rule.present_all)
        absent_all = tuple(value.lower() for value in rule.absent_all)
        regex_flags = re.IGNORECASE
    else:
        target_for_terms = target
        present_any = rule.present_any
        present_all = rule.present_all
        absent_all = rule.absent_all
        regex_flags = 0
    if present_any and not any(value in target_for_terms for value in present_any):
        return False
    if present_all and not all(value in target_for_terms for value in present_all):
        return False
    if absent_all and not all(value not in target_for_terms for value in absent_all):
        return False
    if rule.absent_regex_all and not all(
        re.search(pattern, target, flags=regex_flags) is None
        for pattern in rule.absent_regex_all
    ):
        return False
    return True


def _semantic_import_required_signal_present(
    policy: ExactSemanticDefinitionPlaceholderPolicy,
    *,
    snippet: str,
    declaration_name: str,
) -> bool:
    required_terms = tuple(
        compact_exact_semantic_placeholder_key(term)
        for term in policy.semantic_import_required_signal_terms
        if compact_exact_semantic_placeholder_key(term)
    )
    if not required_terms:
        return True
    declaration_key = compact_exact_semantic_placeholder_key(declaration_name)
    allowed_names = {
        compact_exact_semantic_placeholder_key(value)
        for value in policy.semantic_import_allowed_declaration_names
        if compact_exact_semantic_placeholder_key(value)
    }
    if declaration_key in allowed_names:
        return True
    allowed_prefixes = tuple(
        compact_exact_semantic_placeholder_key(value)
        for value in policy.semantic_import_allowed_declaration_prefixes
        if compact_exact_semantic_placeholder_key(value)
    )
    if allowed_prefixes and any(
        declaration_key.startswith(prefix) for prefix in allowed_prefixes
    ):
        return True
    snippet_key = compact_exact_semantic_placeholder_key(snippet)
    if "k" in required_terms and (" k " in f" {snippet} " or "(k :" in snippet):
        return True
    return any(term != "k" and term in snippet_key for term in required_terms)
