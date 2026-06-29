from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence


FORMALIZER_REPAIR_POLICY_SCHEMA_VERSION = 1

FORMALIZER_VALIDATION_REPAIR_POLICY_BOUNDARY = (
    "Formalizer validation repair policy rows are contract and routing guardrails. "
    "They classify why an LLM Formalizer packet cannot be sent to Lean/prover "
    "execution yet, but they do not supply domain proof content or theorem "
    "evidence. Theory derivation still belongs to the LLM/theory agent; Lean "
    "syntax/proof repair still belongs to the ProofEngineer/prover loop; proof "
    "evidence still requires local Lean/AXLE kernel verification."
)


@dataclass(frozen=True)
class FormalizerValidationRepairRule:
    rule_id: str
    violation_family: str
    trigger_markers: tuple[str, ...]
    prompt_directive: str
    allowed_resolution: str
    forbidden_resolution: str


FORMALIZER_VALIDATION_REPAIR_RULES: tuple[
    FormalizerValidationRepairRule, ...
] = (
    FormalizerValidationRepairRule(
        rule_id="forbidden_contradiction_shortcut",
        violation_family="proof_shortcut_guardrail",
        trigger_markers=(
            "unsupported contradiction proof shortcut",
            "absurd",
            "false.elim",
            "contradiction proof shortcut",
        ),
        prompt_directive=(
            "Remove unsupported contradiction shortcuts (`absurd`, `False.elim`, "
            "fabricated contradictory hypotheses, or fake impossible facts); derive "
            "the claim from real source assumptions/verified lemmas or emit an "
            "explicit FORMAL_GAP without Lean source."
        ),
        allowed_resolution=(
            "Use real source assumptions, retrieved/verified lemmas, or an explicit "
            "FORMAL_GAP that names the missing premise."
        ),
        forbidden_resolution=(
            "Do not prove a statement by inventing contradictory hypotheses or "
            "using impossible facts that are not present in the source context."
        ),
    ),
    FormalizerValidationRepairRule(
        rule_id="executable_candidate_expected_status",
        violation_family="kernel_queue_contract",
        trigger_markers=("must set expected_status=needs_kernel_check",),
        prompt_directive=(
            "Set expected_status=NEEDS_KERNEL_CHECK on every generated Lean "
            "candidate. Use expected_status=FORMAL_GAP only for an honest source "
            "theorem gap without a Lean sketch."
        ),
        allowed_resolution=(
            "Mark executable Lean candidates for kernel checking and keep "
            "non-executable source-theorem blockers as FORMAL_GAP."
        ),
        forbidden_resolution=(
            "Do not leave executable Lean source with OPEN/FORMAL_GAP status or "
            "use FORMAL_GAP to smuggle unchecked Lean code past the verifier queue."
        ),
    ),
    FormalizerValidationRepairRule(
        rule_id="lean_declaration_required",
        violation_family="lean_materialization_contract",
        trigger_markers=("must contain a lean theorem or lemma declaration",),
        prompt_directive=(
            "Do not put prose, dependency notes, or informal blockers in "
            "lean_statement_sketch. If a formal target is executable, its Lean "
            "sketch must contain a concrete theorem or lemma declaration and use "
            "expected_status=NEEDS_KERNEL_CHECK; if the source theorem is blocked, "
            "set expected_status=FORMAL_GAP with an empty lean_statement_sketch and "
            "record the blocker in gap_taxonomy, lemma_dependency_plan, or "
            "formal_blocker_resource_requests."
        ),
        allowed_resolution=(
            "Emit a real Lean theorem/lemma declaration for executable work, or "
            "clear the Lean sketch and record a non-executable blocker."
        ),
        forbidden_resolution=(
            "Do not place prose-only blockers or dependency notes in a field that "
            "the runtime treats as Lean source."
        ),
    ),
    FormalizerValidationRepairRule(
        rule_id="proof_hole_placeholder",
        violation_family="kernel_safety_contract",
        trigger_markers=(
            "lean sorry placeholder",
            "unsupported tactic hole",
            " exact?",
            " by?",
            "admit",
        ),
        prompt_directive=(
            "Remove `sorry`, `admit`, `by?`, `exact?`, and exploratory tactic holes; "
            "return a complete candidate or an explicit FORMAL_GAP."
        ),
        allowed_resolution=(
            "Provide complete Lean source for verifier execution, split the task, "
            "or declare a formal gap."
        ),
        forbidden_resolution=(
            "Do not send placeholder proof bodies to the kernel queue."
        ),
    ),
    FormalizerValidationRepairRule(
        rule_id="source_theorem_target_shape",
        violation_family="semantic_faithfulness_contract",
        trigger_markers=("violates target_shape_contract",),
        prompt_directive=(
            "Preserve the target_shape_contract: source-theorem formal targets "
            "must keep the probability/measure coverage conclusion; route helper "
            "lemmas through support/source-to-bridge channels."
        ),
        allowed_resolution=(
            "Keep the source theorem target semantically faithful, or mark it as "
            "FORMAL_GAP and route helper lemmas through support channels."
        ),
        forbidden_resolution=(
            "Do not replace a source theorem by a narrower arithmetic, typing, or "
            "helper lemma while claiming the source theorem target is ready."
        ),
    ),
    FormalizerValidationRepairRule(
        rule_id="materialized_next_action_reference",
        violation_family="runtime_queue_contract",
        trigger_markers=(
            "next_actions reference source_to_bridge_premise_derivation_candidates",
        ),
        prompt_directive=(
            "Do not point next_actions at phantom source-to-bridge work items. "
            "Either emit a concrete source_to_bridge_premise_derivation_candidates "
            "object with Lean source and source-binding metadata, or rewrite the "
            "action as an explicit FORMAL_GAP/proof-bank dependency task."
        ),
        allowed_resolution=(
            "Reference only candidate objects emitted by the same packet, or move "
            "the work request to gap/dependency planning."
        ),
        forbidden_resolution=(
            "Do not create runtime actions that point to absent executable objects."
        ),
    ),
    FormalizerValidationRepairRule(
        rule_id="source_to_bridge_candidate_required",
        violation_family="source_bridge_contract",
        trigger_markers=(
            "source-to-bridge premise derivation contract requires",
            "source_to_bridge_premise_derivation_candidates entry missing lean candidate source",
        ),
        prompt_directive=(
            "For each pending source-to-bridge premise, either emit a concrete "
            "source_to_bridge_premise_derivation_candidates object with Lean "
            "source, expected_status=NEEDS_KERNEL_CHECK, copied source-binding "
            "request metadata, and required semantic anchors, or emit no "
            "executable candidate and record the exact semantic/import/API "
            "blocker as a FORMAL_GAP. Helper-only formal_targets do not satisfy "
            "a pending source-to-bridge premise derivation contract."
        ),
        allowed_resolution=(
            "Use exact source-binding metadata and anchors for executable bridge "
            "work, or report the blocker as non-executable formal gap context."
        ),
        forbidden_resolution=(
            "Do not treat helper-only formal targets as proof of a pending "
            "source-to-bridge premise."
        ),
    ),
    FormalizerValidationRepairRule(
        rule_id="required_packet_scaffolding_fields",
        violation_family="packet_schema_contract",
        trigger_markers=("missing or empty field",),
        prompt_directive=(
            "Populate every missing required top-level planning field with concise "
            "routing metadata: lemma_dependency_plan, retrieval_queries, "
            "proof_search_plan, gap_taxonomy, critic_findings, and next_actions. "
            "These rows may name blockers or retrieval/prover work, but they must "
            "not claim proof or kernel verification."
        ),
        allowed_resolution=(
            "Use compact non-proof planning rows when executable Lean is blocked "
            "or when a safe candidate is emitted separately."
        ),
        forbidden_resolution=(
            "Do not omit required packet scaffolding, and do not fill it with "
            "fake proof claims or fabricated tool results."
        ),
    ),
    FormalizerValidationRepairRule(
        rule_id="source_to_bridge_adapter_objects_not_binders",
        violation_family="source_bridge_binding_contract",
        trigger_markers=(
            "takes adapter objects as theorem binders instead of deriving them "
            "from source binders",
        ),
        prompt_directive=(
            "Do not list adapter objects requiring source instantiation as theorem "
            "parameters, implicit parameters, or assumptions in "
            "source_to_bridge_premise_derivation_candidates. Derive those objects "
            "inside the candidate from exact source binders and copied request "
            "metadata, or emit no executable source-to-bridge candidate and record "
            "the semantic/source-binding blocker."
        ),
        allowed_resolution=(
            "Derive adapter objects from exact source hypotheses inside the proof, "
            "or fail closed with a non-executable blocker."
        ),
        forbidden_resolution=(
            "Do not satisfy a source-to-bridge premise by adding the required "
            "adapter objects as fresh theorem binders."
        ),
    ),
    FormalizerValidationRepairRule(
        rule_id="semantic_anchor_reference",
        violation_family="semantic_binding_contract",
        trigger_markers=("missing required semantic anchor references",),
        prompt_directive=(
            "Repair the source-to-bridge premise candidate by referencing every "
            "missing required semantic anchor by its exact name outside comments, "
            "not only in theorem headers or unused assumptions. If those anchors "
            "cannot be used non-vacuously in the Lean proof body, emit no executable "
            "source_to_bridge_premise_derivation_candidates entry and report the "
            "specific semantic-anchor blocker instead."
        ),
        allowed_resolution=(
            "Bind and use the required semantic anchors in the candidate source, "
            "or report that the semantic binding is not available."
        ),
        forbidden_resolution=(
            "Do not satisfy semantic anchoring by mentioning names only in comments, "
            "unused binders, or metadata."
        ),
    ),
)


def formalizer_validation_repair_policy(
    validation_errors: Sequence[str],
) -> dict[str, Any]:
    """Return typed guardrail rows for Formalizer packet validation failures."""

    error_text = " ".join(str(error) for error in validation_errors).lower()
    rules = [
        _rule_payload(rule)
        for rule in FORMALIZER_VALIDATION_REPAIR_RULES
        if any(marker in error_text for marker in rule.trigger_markers)
    ]
    return {
        "schema_version": FORMALIZER_REPAIR_POLICY_SCHEMA_VERSION,
        "policy_kind": "formalizer_validation_repair_policy",
        "boundary": FORMALIZER_VALIDATION_REPAIR_POLICY_BOUNDARY,
        "n_rules": len(rules),
        "rules": rules,
    }


def formalizer_validation_repair_directives(
    validation_errors: Sequence[str],
) -> list[str]:
    """Backward-compatible prompt directives derived from typed policy rows."""

    policy = formalizer_validation_repair_policy(validation_errors)
    return [
        str(row.get("prompt_directive", ""))
        for row in policy.get("rules", [])
        if isinstance(row, Mapping) and str(row.get("prompt_directive", "")).strip()
    ]


def render_formalizer_validation_repair_policy_instructions(
    feedback: Mapping[str, Any],
    *,
    max_rules: int = 4,
) -> list[str]:
    """Render typed validation policy rows as concise LLM-facing instructions."""

    policy = feedback.get("validation_repair_policy", {})
    if not isinstance(policy, Mapping):
        policy = {}
    rules = [
        row
        for row in policy.get("rules", []) or []
        if isinstance(row, Mapping)
    ]
    if not rules:
        rules = formalizer_validation_repair_policy(
            _text_values(feedback.get("validation_errors", []))
        ).get("rules", [])
    if not rules:
        return []
    rendered_rules = []
    for row in rules[:max_rules]:
        rule_id = str(row.get("rule_id", "") or "").strip()
        directive = str(row.get("prompt_directive", "") or "").strip()
        if rule_id and directive:
            rendered_rules.append(f"{rule_id}: {directive}")
    if not rendered_rules:
        return []
    return [
        "Typed validation repair policy is active. These rows are guardrails, "
        "not theorem/proof content; use them to route the next packet while "
        "leaving mathematical derivation and Lean repair to the LLM/prover loop: "
        + " | ".join(rendered_rules)
    ]


def _rule_payload(rule: FormalizerValidationRepairRule) -> dict[str, Any]:
    payload = asdict(rule)
    payload["schema_version"] = FORMALIZER_REPAIR_POLICY_SCHEMA_VERSION
    payload["boundary"] = FORMALIZER_VALIDATION_REPAIR_POLICY_BOUNDARY
    return payload


def _text_values(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, Mapping):
        return [str(value)]
    try:
        return [str(item) for item in value if str(item).strip()]
    except TypeError:
        text = str(value)
        return [text] if text.strip() else []
