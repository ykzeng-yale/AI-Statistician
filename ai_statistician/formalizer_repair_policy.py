from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence


FORMALIZER_REPAIR_POLICY_SCHEMA_VERSION = 2

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
        rule_id="pseudo_formalization_required",
        violation_family="pseudo_formal_block_verification_contract",
        trigger_markers=(
            "pseudo_formalization_required",
            "requires at least one pseudo_formal_proof_packets",
            "no locally valid pseudo_formal_proof_packets",
            "valid pf/bv packet did not produce",
            "only generic review rows",
        ),
        prompt_directive=(
            "PF/BV activation is required: emit at least one "
            "pseudo_formal_proof_packets entry with source-anchored blocks, "
            "PF/BV method lineage, faithfulness/block-verifier status, and at "
            "least one lane-routable residual work order. Do not replace this "
            "with another direct Lean API retry or a FORMAL_GAP-only packet. "
            "Runtime target-lane routing is inferred from block fields: use "
            "faithfulness_status=faithful with "
            "lean_feasibility=needs_semantic_definition for exact semantic "
            "definition work, faithfulness_status=faithful with "
            "lean_feasibility=needs_rag for Lean/RAG grounding, or "
            "faithfulness_status=faithful with non-empty "
            "semantic_primitive_requirements for source_to_bridge work. Generic "
            "needs_review/not_run blocks are diagnostic only and do not satisfy "
            "required PF/BV activation."
        ),
        allowed_resolution=(
            "Produce valid pseudo-formal blocks that route residuals to Lean/RAG, "
            "source-to-bridge, exact semantic-definition authoring, or formal-gap "
            "lanes while preserving non-proof boundaries."
        ),
        forbidden_resolution=(
            "Do not satisfy required PF/BV activation with ordinary formal_targets, "
            "unchecked Lean sketches, broad prose, or pseudo-formal packets that "
            "produce no lane-routable work-order rows."
        ),
    ),
    FormalizerValidationRepairRule(
        rule_id="pseudo_formal_blocks_required_when_packet_present",
        violation_family="pseudo_formal_block_verification_contract",
        trigger_markers=(
            "blocks must contain at least one pseudo-formal block",
            "pseudo_formal_proof_packets",
        ),
        prompt_directive=(
            "If you emit pseudo_formal_proof_packets, every packet must contain "
            "at least one concrete pseudo-formal block with premises, conclusion, "
            "proof text, dependency/scope metadata, PF/BV method lineage, and "
            "non-proof boundary. When PF/BV activation is not required and no "
            "valid block can be produced, omit the optional packet instead of "
            "returning an empty PF/BV shell."
        ),
        allowed_resolution=(
            "Emit non-empty source-anchored PF/BV blocks, or leave the optional "
            "pseudo_formal_proof_packets list empty when the current feedback does "
            "not require PF/BV activation."
        ),
        forbidden_resolution=(
            "Do not return pseudo-formal packets with an empty blocks list or "
            "placeholder-only block content."
        ),
    ),
    FormalizerValidationRepairRule(
        rule_id="pseudo_formal_block_schema_fields",
        violation_family="pseudo_formal_block_verification_contract",
        trigger_markers=(
            "missing conclusion",
            "missing source_anchors",
            "unsupported faithfulness_status",
        ),
        prompt_directive=(
            "Repair each pseudo-formal block against the block schema: use a "
            "top-level conclusion field for the local claim, include at least one "
            "source_anchors entry pointing to a theory trace/paper/proof-body "
            "source with a non-empty id or excerpt, for example "
            "{\"kind\":\"theory_trace\",\"id\":\"source_step_1\","
            "\"excerpt\":\"exact intermediate claim from the derivation\"}; do not "
            "put anchor names only in prose, comments, or next_actions. Set "
            "faithfulness_status to one of lowercase "
            "`faithful`, `needs_review`, `unfaithful`, or `unchecked`. Do not use "
            "uppercase statuses such as UNVERIFIED."
        ),
        allowed_resolution=(
            "Return schema-valid blocks with explicit source anchors and a valid "
            "faithfulness status, or route the block as needs_review/unfaithful "
            "with faithfulness_repair metadata."
        ),
        forbidden_resolution=(
            "Do not put the conclusion only inside prose, omit source anchors, or "
            "invent unsupported faithfulness status labels."
        ),
    ),
    FormalizerValidationRepairRule(
        rule_id="pseudo_formal_block_verification_rollout_count",
        violation_family="pseudo_formal_block_verification_contract",
        trigger_markers=(
            "rollout_count",
            "accepted block_verification",
            "block verification",
        ),
        prompt_directive=(
            "When a pseudo-formal block uses "
            "block_verification.verdict=`accepted`, include "
            "block_verification.rollout_count as an integer >= 1. If no "
            "independent BV rollout was actually recorded, use a valid "
            "non-accepted verdict such as `not_run`, `unknown`, or `failed` "
            "instead of `accepted`; keep the block's top-level conclusion and "
            "source_anchors fields intact. Use `needs_review` only as a "
            "faithfulness_status value, not as a block_verification verdict."
        ),
        allowed_resolution=(
            "Either record rollout_count >= 1 for accepted blocks, or downgrade "
            "the block verdict to a non-accepted residual route that still "
            "produces a lane-routable PF/BV work order."
        ),
        forbidden_resolution=(
            "Do not claim an accepted BV block with rollout_count 0/missing, and "
            "do not repair that error by dropping the block conclusion or source "
            "anchors."
        ),
    ),
    FormalizerValidationRepairRule(
        rule_id="pseudo_formal_block_type_normalization",
        violation_family="pseudo_formal_block_verification_contract",
        trigger_markers=("unsupported block_type",),
        prompt_directive=(
            "Use the pseudo-formal block_type vocabulary: theorem, proposition, "
            "lemma, claim, fact, definition, calculation, or case. Natural "
            "decomposition labels such as theorem_step, assumption_block, "
            "derivation_block, and conclusion_block must be rewritten into that "
            "vocabulary before returning the packet."
        ),
        allowed_resolution=(
            "Map assumption/premise blocks to fact, derivation/proof/theorem "
            "steps to lemma or calculation, and final/result blocks to claim "
            "while keeping source anchors and local conclusions explicit."
        ),
        forbidden_resolution=(
            "Do not invent new block_type labels or hide the block role in prose "
            "while leaving the schema field invalid."
        ),
    ),
    FormalizerValidationRepairRule(
        rule_id="formal_target_role_routing",
        violation_family="formal_target_routing_contract",
        trigger_markers=("formal_target_role",),
        prompt_directive=(
            "Give every formal_targets row one explicit routing role. Use "
            "SOURCE_THEOREM_CANDIDATE only for a nonempty whole-target Lean "
            "candidate with candidate_lean_declaration and source provenance; use "
            "SOURCE_THEOREM_FORMAL_GAP for the same source theorem with empty Lean "
            "source and expected_status=FORMAL_GAP; use HELPER_OR_SUPPORT for a "
            "smaller executable candidate and set source_theorem_target_known=false. "
            "These roles route artifacts and do not certify semantic faithfulness or "
            "proof."
        ),
        allowed_resolution=(
            "Separate the source-theorem candidate or gap from helper/support Lean, "
            "then let independent semantic review and Lean verification evaluate the "
            "routed artifacts."
        ),
        forbidden_resolution=(
            "Do not leave a formal target role unspecified, label a helper as the "
            "source theorem, or attach executable Lean to a source-theorem gap row."
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
            "must keep the task-bound objects, assumptions, quantifiers, and "
            "conclusion; route helper "
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
    FormalizerValidationRepairRule(
        rule_id="source_theorem_candidate_materialization_required",
        violation_family="source_theorem_materialization_contract",
        trigger_markers=(
            "source_theorem_exact_candidate_materialization_required requires",
            "formal_gap and helper/support candidates do not satisfy this materialization gate",
            "formal_targets candidate must preserve a requested target id/name",
        ),
        prompt_directive=(
            "In source-theorem candidate-materialization mode, emit a concrete "
            "exact source-theorem formal_targets entry with "
            "expected_status=NEEDS_KERNEL_CHECK, a nonempty Lean theorem/lemma "
            "sketch, source_theorem_target_provenance.source_theorem_target_known=true, "
            "and copied requested target_ids/names. Do not satisfy this mode with "
            "FORMAL_GAP-only, helper-only, support-only, or source-to-bridge-only "
            "outputs; materialization is still not proof evidence until Lean/AXLE "
            "checks the exact candidate."
        ),
        allowed_resolution=(
            "Create the exact source-theorem Lean candidate artifact for signature "
            "probe/local Lean feedback while preserving target identity and proof "
            "boundaries."
        ),
        forbidden_resolution=(
            "Do not route materialization-mode feedback back into a FORMAL_GAP-only "
            "or helper/support-only packet, and do not claim kernel proof from the "
            "candidate."
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
