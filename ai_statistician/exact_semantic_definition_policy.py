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
    draft_definition: str = ""
    draft_definition_semantic_risk: str = "draft definition requires semantic review"
    source_lookup_search_terms: tuple[str, ...] = ()
    source_lookup_aliases: tuple[str, ...] = ()
    definition_contract: Mapping[str, Any] = field(default_factory=dict)
    candidate_risk_rules: tuple[
        ExactSemanticDefinitionCandidateRiskRule,
        ...,
    ] = ()


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


_SPLIT_CONFORMAL_POLICIES: tuple[
    ExactSemanticDefinitionPlaceholderPolicy,
    ...,
] = (
    ExactSemanticDefinitionPlaceholderPolicy(
        policy_id="split_conformal_coverage.exchangeable",
        policy_scope="split_conformal_coverage",
        placeholder_key="exchangeable",
        semantic_goal=(
            "Define finite exchangeability as permutation-invariant joint law of "
            "the score process, not only pairwise score-order symmetry."
        ),
        required_anchor_names=("P", "s"),
        source_lookup_search_terms=("exchangeability", "exchangeab"),
        source_lookup_aliases=("exchangeable", "exchangeability"),
        definition_contract={
            "semantic_intent": (
                "finite calibration/test score family has a permutation-invariant "
                "joint law under the probability measure"
            ),
            "lean_target_shape": (
                "predicate over `P : Measure Ω` and `s : Fin (n + 1) -> Ω -> ℝ`"
            ),
            "required_properties": [
                "invariance under finite index permutations",
                "sufficient to derive uniform rank or bad-rank budget support lemmas",
                "compatible with MeasureTheory probability-measure assumptions",
            ],
            "forbidden_shortcuts": [
                "do not define Exchangeable as True",
                "do not add axiom/sorry/admit/unsafe",
                "do not assume the split_conformal_coverage target theorem",
            ],
        },
        draft_definition=(
            "def Exchangeable {Ω : Type _} [MeasurableSpace Ω] {ι : Type _} [Fintype ι]\n"
            "    (P : MeasureTheory.Measure Ω) (s : ι → Ω → ℝ) : Prop :=\n"
            "  ∀ σ : Equiv.Perm ι,\n"
            "    MeasureTheory.Measure.map (fun ω : Ω => fun i : ι => s (σ i) ω) P =\n"
            "      MeasureTheory.Measure.map (fun ω : Ω => fun i : ι => s i ω) P"
        ),
        draft_definition_semantic_risk=(
            "draft finite permutation-invariant joint-law exchangeability still "
            "requires source review and downstream local Lean/AXLE verification"
        ),
        candidate_risk_rules=(
            ExactSemanticDefinitionCandidateRiskRule(
                message=(
                    "semantic_definition_risk: Exchangeable candidate uses pairwise "
                    "score-order probability symmetry rather than finite permutation-"
                    "invariant joint-law exchangeability"
                ),
                present_any=("P.real",),
                absent_all=("Equiv.Perm",),
            ),
            ExactSemanticDefinitionCandidateRiskRule(
                message=(
                    "semantic_definition_risk: Exchangeable candidate does not expose "
                    "a finite permutation/invariance parameter"
                ),
                absent_all=("Equiv.Perm", "permutation"),
                case_sensitive=False,
            ),
        ),
    ),
    ExactSemanticDefinitionPlaceholderPolicy(
        policy_id="split_conformal_coverage.covered",
        policy_scope="split_conformal_coverage",
        placeholder_key="covered",
        semantic_goal=(
            "Define the source coverage event/object from the exact source theorem "
            "coverage binder hC and threshold q_hat, matching the held-out score "
            "event {\u03c9 | s (Fin.last n2) \u03c9 \u2264 q_hat \u03c9}."
        ),
        required_anchor_names=("s", "q_hat", "C", "hC"),
    ),
    ExactSemanticDefinitionPlaceholderPolicy(
        policy_id="split_conformal_coverage.rank",
        policy_scope="split_conformal_coverage",
        placeholder_key="rank",
        semantic_goal=(
            "Define the rank object from the exact score process s and the "
            "order-statistic threshold equation hq; it must support good-rank "
            "containment and bad-rank probability premises."
        ),
        required_anchor_names=("n2", "s", "q_hat", "hq"),
        source_lookup_aliases=("rank", "rank_uniformity"),
    ),
    ExactSemanticDefinitionPlaceholderPolicy(
        policy_id="split_conformal_coverage.order_statistic_threshold",
        policy_scope="split_conformal_coverage",
        placeholder_key="orderstat",
        semantic_goal=(
            "Define the finite-sample conformal order-statistic threshold from "
            "the exact score process s and the order-statistic threshold equation "
            "hq. The definition must preserve the requested rank, duplicate score "
            "multiplicities, and the reviewed tie policy instead of collapsing "
            "scores through a set/image shortcut."
        ),
        required_anchor_names=("n2", "s", "q_hat", "hq"),
        semantic_import_incompatible_terms=(
            "samplemean",
            "trimmedmean",
            "winsorizedmean",
            "lstatistic",
            "interquantilerange",
            "samplerange",
            "conditionalcdf",
            "cdf",
            "projection",
            "variance",
        ),
        semantic_import_incompatible_status=(
            "SEMANTIC_MISMATCH_NOT_EXACT_ORDER_STATISTIC"
        ),
        semantic_import_incompatible_reason=(
            "declaration name matches order-statistic literature but defines an "
            "aggregate/range/CDF display, not the rank-k conformal orderStat "
            "placeholder"
        ),
        semantic_import_required_signal_terms=("k", "rank"),
        semantic_import_allowed_declaration_names=("orderstat", "orderstatistic"),
        semantic_import_allowed_declaration_prefixes=("orderstatreview",),
        semantic_import_missing_required_signal_status=(
            "SEMANTIC_REVIEW_REQUIRED_ORDER_STATISTIC_RANK_NOT_EXPOSED"
        ),
        semantic_import_missing_required_signal_reason=(
            "candidate declaration does not visibly expose the requested rank "
            "parameter for orderStat"
        ),
        source_lookup_search_terms=("orderStatistic", "order statistic", "quantile"),
        source_lookup_aliases=("orderStat", "orderStatistic", "quantile"),
        definition_contract={
            "semantic_intent": (
                "finite order statistic / conformal quantile of calibration scores "
                "at the requested finite-sample rank"
            ),
            "lean_target_shape": (
                "function from finite indexed real scores and a Nat rank to a real "
                "threshold"
            ),
            "required_properties": [
                "monotone containment of good-rank events",
                "rank index matches the conformal ceiling expression",
                "preserves duplicate score multiplicities and reviewed tie policy",
                "compatible with finite `Fin (n + 1)` score families",
            ],
            "forbidden_shortcuts": [
                "do not define orderStat as a constant unrelated to scores",
                "do not use Finset.image/set sorting that collapses duplicate scores",
                "do not add axiom/sorry/admit/unsafe",
                "do not restate coverage as an order-statistic property",
            ],
        },
        draft_definition=(
            "def orderStat {Ω : Type _} {m : ℕ}\n"
            "    (s : Fin (m + 1) → Ω → ℝ) (k : ℕ) (ω : Ω) : ℝ :=\n"
            "  ((List.ofFn (fun i : Fin (m + 1) => s i ω)).mergeSort (· ≤ ·)).getD k 0"
        ),
        draft_definition_semantic_risk=(
            "draft sorted finite order statistic uses a duplicate-preserving finite "
            "score list and rank k, but still needs source review for indexing "
            "convention, tie behavior, and conformal quantile rank; "
            "the source theorem upper coverage bound is not eligible for proof-body search "
            "until ties are handled by a reviewed tie policy/no-tie assumption or the "
            "theorem is revised"
        ),
        candidate_risk_rules=(
            ExactSemanticDefinitionCandidateRiskRule(
                message=(
                    "semantic_definition_risk: orderStat candidate is a finite maximum, "
                    "not a reviewed rank-k order statistic/conformal quantile"
                ),
                scope="definition_body",
                present_any=(".max'", ".max ", ".max\n"),
            ),
            ExactSemanticDefinitionCandidateRiskRule(
                message=(
                    "semantic_definition_risk: orderStat candidate uses Finset.image, "
                    "which collapses duplicate score values and is not faithful to "
                    "finite-sample order statistics unless a reviewed no-tie or "
                    "multiplicity-preserving tie policy is supplied"
                ),
                scope="definition_body",
                present_any=("Finset.univ.image",),
            ),
            ExactSemanticDefinitionCandidateRiskRule(
                message=(
                    "semantic_definition_risk: orderStat candidate body does not use "
                    "the requested rank parameter k"
                ),
                scope="definition_body",
                absent_regex_all=(r"\bk\b",),
            ),
        ),
    ),
    ExactSemanticDefinitionPlaceholderPolicy(
        policy_id="split_conformal_coverage.BadRanks",
        policy_scope="split_conformal_coverage",
        placeholder_key="badranks",
        semantic_goal=(
            "Define the finite bad-rank set from n2, alpha, halpha, and hq so it "
            "matches the ranks that violate conformal coverage containment."
        ),
        required_anchor_names=("n2", "alpha", "halpha", "s", "q_hat", "hq"),
        required_adapter_object_names=("rank",),
        source_lookup_aliases=("BadRanks", "bad ranks", "bad-rank"),
    ),
    ExactSemanticDefinitionPlaceholderPolicy(
        policy_id="split_conformal_coverage.alpha",
        policy_scope="split_conformal_coverage",
        placeholder_key="alpha",
        semantic_goal=(
            "Define the rank-indexed probability budget \u03b1 from the exact source "
            "miscoverage level alpha and rank-uniformity/exchangeability anchor hexch."
        ),
        required_anchor_names=("P", "n2", "alpha", "s", "hexch"),
        source_lookup_search_terms=("alpha", "\u03b1", "miscoverage"),
        source_lookup_aliases=("alpha", "\u03b1"),
    ),
    ExactSemanticDefinitionPlaceholderPolicy(
        policy_id="split_conformal_coverage.alpha_total",
        policy_scope="split_conformal_coverage",
        placeholder_key="alphatotal",
        semantic_goal=(
            "Define the total bad-rank budget \u03b1_total from alpha and BadRanks, "
            "with the intended downstream finite-sum bound."
        ),
        required_anchor_names=("n2", "alpha", "halpha"),
        required_adapter_object_names=("BadRanks",),
        source_lookup_search_terms=(
            "alpha_total",
            "\u03b1_total",
            "alpha",
            "bad-rank budget",
        ),
        source_lookup_aliases=(
            "alpha_total",
            "\u03b1_total",
            "alphatotal",
            "alpha",
            "\u03b1",
        ),
    ),
)


def _split_conformal_registry() -> dict[str, ExactSemanticDefinitionPlaceholderPolicy]:
    registry = _registry_from_policies(_SPLIT_CONFORMAL_POLICIES)
    registry["\u03b1"] = registry["alpha"]
    registry["\u03b1total"] = registry["alphatotal"]
    return registry


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
]:
    policy_dir = Path(__file__).resolve().parent / "policies"
    if not policy_dir.exists():
        return (), ()
    policies: list[ExactSemanticDefinitionPlaceholderPolicy] = []
    policy_pack_ids: list[str] = []
    for path in sorted(policy_dir.glob(_POLICY_PACK_GLOB)):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, Mapping):
            raise ValueError(f"policy pack must be a JSON object: {path}")
        policy_pack_id = str(payload.get("policy_pack_id", "") or "").strip()
        if policy_pack_id:
            policy_pack_ids.append(policy_pack_id)
        raw_policies = payload.get("placeholder_policies", [])
        if not isinstance(raw_policies, list):
            raise ValueError(
                "policy pack placeholder_policies must be a list: "
                f"{path}"
            )
        policies.extend(
            _policy_from_mapping(row, source_path=path)
            for row in raw_policies
            if isinstance(row, Mapping)
        )
    return tuple(policies), tuple(dict.fromkeys(policy_pack_ids))


def _policy_from_mapping(
    row: Mapping[str, Any],
    *,
    source_path: Path,
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
        draft_definition=str(row.get("draft_definition", "") or ""),
        draft_definition_semantic_risk=str(
            row.get(
                "draft_definition_semantic_risk",
                "draft definition requires semantic review",
            )
            or "draft definition requires semantic review"
        ),
        source_lookup_search_terms=_string_tuple(
            row.get("source_lookup_search_terms")
        ),
        source_lookup_aliases=_string_tuple(row.get("source_lookup_aliases")),
        definition_contract=_mapping_or_empty(row.get("definition_contract")),
        candidate_risk_rules=tuple(
            _risk_rule_from_mapping(rule)
            for rule in row.get("candidate_risk_rules", [])
            if isinstance(rule, Mapping)
        ),
    )


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
        case_sensitive=bool(row.get("case_sensitive", True)),
    )


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


def _build_policy_registry() -> tuple[
    Mapping[str, ExactSemanticDefinitionPlaceholderPolicy],
    tuple[str, ...],
]:
    registry = _split_conformal_registry()
    policy_pack_policies, policy_pack_ids = _load_policy_pack_policies()
    if policy_pack_policies:
        registry.update(_registry_from_policies(policy_pack_policies))
        return registry, policy_pack_ids
    return registry, ()


(
    EXACT_SEMANTIC_DEFINITION_PLACEHOLDER_POLICIES,
    EXACT_SEMANTIC_DEFINITION_POLICY_PACK_IDS,
) = _build_policy_registry()


def exact_semantic_definition_policy_pack_ids() -> tuple[str, ...]:
    return EXACT_SEMANTIC_DEFINITION_POLICY_PACK_IDS


def exact_semantic_definition_placeholder_policy(
    placeholder_symbol: str,
) -> ExactSemanticDefinitionPlaceholderPolicy:
    key = compact_exact_semantic_placeholder_key(placeholder_symbol)
    policy = EXACT_SEMANTIC_DEFINITION_PLACEHOLDER_POLICIES.get(key)
    if policy is not None:
        return policy
    return replace(_GENERIC_POLICY, placeholder_key=key)


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


def exact_semantic_definition_draft_definition(placeholder_symbol: str) -> str:
    policy = exact_semantic_definition_placeholder_policy(placeholder_symbol)
    return policy.draft_definition


def exact_semantic_definition_draft_semantic_risk(placeholder_symbol: str) -> str:
    policy = exact_semantic_definition_placeholder_policy(placeholder_symbol)
    return policy.draft_definition_semantic_risk


def exact_semantic_definition_source_lookup_terms(
    placeholder_symbol: str,
) -> tuple[str, ...]:
    policy = exact_semantic_definition_placeholder_policy(placeholder_symbol)
    return policy.source_lookup_search_terms


def exact_semantic_definition_source_lookup_aliases(
    placeholder_symbol: str,
) -> tuple[str, ...]:
    policy = exact_semantic_definition_placeholder_policy(placeholder_symbol)
    aliases = [
        str(placeholder_symbol or "").strip(),
        policy.placeholder_key,
        *policy.source_lookup_search_terms,
        *policy.source_lookup_aliases,
    ]
    return tuple(dict.fromkeys(alias for alias in aliases if alias))


def exact_semantic_definition_contract(placeholder_symbol: str) -> dict[str, Any]:
    policy = exact_semantic_definition_placeholder_policy(placeholder_symbol)
    if policy.definition_contract:
        return {
            str(key): _copy_contract_value(value)
            for key, value in policy.definition_contract.items()
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
