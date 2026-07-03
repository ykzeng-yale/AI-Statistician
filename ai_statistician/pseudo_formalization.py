from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping, Sequence

from .fingerprint import stable_hash


PSEUDO_FORMALIZATION_SCHEMA_VERSION = 1
PSEUDO_FORMALIZATION_SCHEMA_ID = (
    "urn:ai-statistician:schemas:pseudo-formal-proof-packet:1"
)
PSEUDO_FORMAL_BLOCK_SCHEMA_ID = (
    "urn:ai-statistician:schemas:pseudo-formal-proof-block:1"
)
PSEUDO_FORMAL_WORK_ORDER_ROW_SCHEMA_ID = (
    "urn:ai-statistician:schemas:pseudo-formal-work-order-row:1"
)
PSEUDO_FORMALIZATION_COMPONENT = "pseudo_formalization"
PSEUDO_FORMALIZATION_NOT_PROOF_EVIDENCE = (
    "PSEUDO_FORMAL_VERIFICATION_NOT_PROOF_EVIDENCE"
)
PSEUDO_FORMALIZATION_PROOF_BOUNDARY = (
    "Pseudo-formalization and block-verification rows are decomposition, "
    "faithfulness, routing, and repair-planning artifacts. They are not theorem "
    "proof evidence. Source theorem proof requires target-prover kernel replay."
)
PSEUDO_FORMALIZATION_PROMOTION_GATE = "requires_target_prover_kernel_replay"
PSEUDO_FORMAL_VERIFICATION_METHOD_CONTRACT_ID = (
    "urn:ai-statistician:contracts:pseudo-formal-pf-bv:1"
)
PSEUDO_FORMAL_VERIFICATION_METHOD_NAME = (
    "pseudo_formalization_plus_block_verification"
)
PSEUDO_FORMAL_BLOCK_ROUTING_METHOD_STAGE = "route_pseudo_formal_block_residuals"
PSEUDO_FORMAL_VERIFICATION_METHOD_STAGES = (
    {
        "stage_id": "translate_to_pseudo_formal",
        "owner": "Formalizer/ProofEngineer",
        "acceptance_gate": (
            "source proof is decomposed into bounded blocks with explicit "
            "premises, conclusions, dependency ids, scope context, and source anchors"
        ),
    },
    {
        "stage_id": "faithfulness_check_and_repair",
        "owner": "Formalizer/Referee",
        "acceptance_gate": (
            "each block is checked against the source artifact for strengthened, "
            "weakened, omitted, added, notation-drift, or scope-drift content"
        ),
    },
    {
        "stage_id": "independent_block_verification",
        "owner": "BlockVerifier",
        "acceptance_gate": (
            "each block is verified using only its premises, inherited scope, "
            "declared dependencies, conclusion, and local proof text"
        ),
    },
    {
        "stage_id": "calibrate_block_reports",
        "owner": "CalibrationReferee",
        "acceptance_gate": (
            "block-level objections are aggregated under an explicit strictness "
            "threshold and separated from rewrite artifacts"
        ),
    },
    {
        "stage_id": "parallel_pessimistic_aggregation",
        "owner": "AgentRuntime",
        "acceptance_gate": (
            "independent rollouts are combined pessimistically: a proof-level "
            "acceptance requires every rollout to accept, while error-finding "
            "uses unioned and deduplicated flagged locations"
        ),
    },
    {
        "stage_id": PSEUDO_FORMAL_BLOCK_ROUTING_METHOD_STAGE,
        "owner": "AgentRuntime",
        "acceptance_gate": (
            "residual blocks become lane-specific work orders for Lean/RAG/"
            "source-to-bridge/semantic-definition/formal-gap follow-up"
        ),
    },
)
PSEUDO_FORMAL_BLOCK_ROUTING_LEARNING_TASK = "pseudo_formal_block_routing_feedback"
PSEUDO_FORMAL_BLOCK_ROUTING_TRIGGER = "PSEUDO_FORMAL_WORK_ORDER_READY"
PSEUDO_FORMAL_BLOCK_ROUTING_QUEUE_NAME = "pseudo_formal_work_orders_from_formalizer"
PSEUDO_FORMAL_BLOCK_ROUTING_MEMORY_STATUS = "PSEUDO_FORMAL_ROUTING_MEMORY"
PSEUDO_FORMAL_TARGET_LANE_FORMAL_TARGETS = "formal_targets"
PSEUDO_FORMAL_TARGET_LANE_LEAN_RAG = "lean_rag"
PSEUDO_FORMAL_TARGET_LANE_SOURCE_TO_BRIDGE = "source_to_bridge"
PSEUDO_FORMAL_TARGET_LANE_EXACT_SEMANTIC_DEFINITION = (
    "source_theorem_exact_semantic_definition"
)
PSEUDO_FORMAL_TARGET_LANE_FORMAL_GAP = "formal_gap"
PSEUDO_FORMAL_BLOCK_ROUTING_TARGET_LANES = (
    PSEUDO_FORMAL_TARGET_LANE_FORMAL_TARGETS,
    PSEUDO_FORMAL_TARGET_LANE_LEAN_RAG,
    PSEUDO_FORMAL_TARGET_LANE_SOURCE_TO_BRIDGE,
    PSEUDO_FORMAL_TARGET_LANE_EXACT_SEMANTIC_DEFINITION,
    PSEUDO_FORMAL_TARGET_LANE_FORMAL_GAP,
)
PSEUDO_FORMAL_BLOCK_ROUTING_HIGH_PRIORITY_TARGET_LANES = (
    PSEUDO_FORMAL_TARGET_LANE_FORMAL_TARGETS,
    PSEUDO_FORMAL_TARGET_LANE_SOURCE_TO_BRIDGE,
    PSEUDO_FORMAL_TARGET_LANE_EXACT_SEMANTIC_DEFINITION,
)
PSEUDO_FORMAL_BLOCK_ROUTING_QUEUE_STATUS_BY_TARGET_LANE = {
    PSEUDO_FORMAL_TARGET_LANE_FORMAL_TARGETS: (
        "PENDING_FORMALIZER_LEAN_CANDIDATE_FROM_PSEUDO_FORMAL_BLOCK"
    ),
    PSEUDO_FORMAL_TARGET_LANE_LEAN_RAG: (
        "PENDING_FORMAL_LIBRARY_GROUNDING_FROM_PSEUDO_FORMAL_BLOCK"
    ),
    PSEUDO_FORMAL_TARGET_LANE_SOURCE_TO_BRIDGE: (
        "PENDING_SOURCE_TO_BRIDGE_FROM_PSEUDO_FORMAL_BLOCK"
    ),
    PSEUDO_FORMAL_TARGET_LANE_EXACT_SEMANTIC_DEFINITION: (
        "PENDING_EXACT_SEMANTIC_DEFINITION_FROM_PSEUDO_FORMAL_BLOCK"
    ),
    PSEUDO_FORMAL_TARGET_LANE_FORMAL_GAP: (
        "PENDING_FORMAL_GAP_REVIEW_FROM_PSEUDO_FORMAL_BLOCK"
    ),
}
PSEUDO_FORMAL_LEAN_FEASIBILITY_TARGET_LANES = {
    "lean_now": PSEUDO_FORMAL_TARGET_LANE_FORMAL_TARGETS,
    "needs_rag": PSEUDO_FORMAL_TARGET_LANE_LEAN_RAG,
    "needs_library": PSEUDO_FORMAL_TARGET_LANE_FORMAL_GAP,
    "needs_semantic_definition": PSEUDO_FORMAL_TARGET_LANE_EXACT_SEMANTIC_DEFINITION,
    "pseudo_only": PSEUDO_FORMAL_TARGET_LANE_FORMAL_GAP,
}

VALID_BLOCK_TYPES = (
    "theorem",
    "proposition",
    "lemma",
    "claim",
    "fact",
    "definition",
    "calculation",
    "case",
)
VALID_BLOCK_VERDICTS = ("not_run", "accepted", "failed", "unknown")
VALID_FAITHFULNESS_STATUSES = ("unchecked", "faithful", "unfaithful", "needs_review")
VALID_LEAN_FEASIBILITY = (
    "lean_now",
    "needs_rag",
    "needs_library",
    "needs_semantic_definition",
    "pseudo_only",
    "unknown",
)


def pseudo_formal_verification_method_contract() -> dict[str, Any]:
    return {
        "contract_id": PSEUDO_FORMAL_VERIFICATION_METHOD_CONTRACT_ID,
        "method_name": PSEUDO_FORMAL_VERIFICATION_METHOD_NAME,
        "source_basis": {
            "paper_title": "Pseudo-Formalization for Automatic Proof Verification",
            "arxiv_id": "2605.20531",
            "method_short_name": "PF+BV",
        },
        "pipeline_stages": deepcopy(PSEUDO_FORMAL_VERIFICATION_METHOD_STAGES),
        "block_verification_scope": (
            "verify each pseudo-formal block independently against its explicit "
            "premises, inherited scope, declared dependencies, conclusion, and proof"
        ),
        "calibration_rule": (
            "aggregate block verifier reports under an explicit strictness "
            "threshold; distinguish source-proof errors from rewrite artifacts"
        ),
        "parallel_aggregation_rule": (
            "use independent stochastic rollouts with pessimistic proof acceptance "
            "and union/deduplication of flagged error locations for error finding"
        ),
        "row_lineage_required": [
            "pseudo_formal_method_contract_id",
            "pseudo_formal_pipeline_stage",
            "source_pseudo_formal_work_order_id",
            "source_block_id",
            "source_anchors",
        ],
        "proof_evidence_status": PSEUDO_FORMALIZATION_NOT_PROOF_EVIDENCE,
        "promotion_gate": PSEUDO_FORMALIZATION_PROMOTION_GATE,
        "proof_evidence_boundary": PSEUDO_FORMALIZATION_PROOF_BOUNDARY,
    }


def pseudo_formalizer_output_contract() -> dict[str, Any]:
    return {
        "schema_id": PSEUDO_FORMALIZATION_SCHEMA_ID,
        "schema_version": PSEUDO_FORMALIZATION_SCHEMA_VERSION,
        "component_name": PSEUDO_FORMALIZATION_COMPONENT,
        "verification_method_contract": pseudo_formal_verification_method_contract(),
        "packet_fields": {
            "theorem_id": "source theorem or theorem-card id",
            "source_artifact_id": "paper/proof/theory packet/source theorem artifact id",
            "blocks": "ordered proof blocks; dependencies must reference earlier block ids",
        },
        "block_contract": {
            "block_id": "stable local id",
            "block_type": list(VALID_BLOCK_TYPES),
            "premises": ["local premise text or referenced earlier blocks"],
            "conclusion": "single local conclusion",
            "proof_text": "proof body for only this block; use None/empty only when absent",
            "dependency_ids": ["earlier block ids"],
            "source_anchors": [
                {
                    "kind": "theory_trace|paper|proof_body|theorem_card|other",
                    "id": "source-local id",
                    "excerpt": "bounded source excerpt or pointer",
                }
            ],
            "semantic_primitive_requirements": ["missing primitive or definition ids"],
            "lean_feasibility": list(VALID_LEAN_FEASIBILITY),
            "faithfulness_status": list(VALID_FAITHFULNESS_STATUSES),
            "block_verification": {
                "verdict": list(VALID_BLOCK_VERDICTS),
                "reason": "short verifier rationale",
            },
        },
        "proof_evidence_status": PSEUDO_FORMALIZATION_NOT_PROOF_EVIDENCE,
        "promotion_gate": PSEUDO_FORMALIZATION_PROMOTION_GATE,
        "proof_evidence_boundary": PSEUDO_FORMALIZATION_PROOF_BOUNDARY,
        "work_order_routing_contract": {
            "learning_task": PSEUDO_FORMAL_BLOCK_ROUTING_LEARNING_TASK,
            "trigger": PSEUDO_FORMAL_BLOCK_ROUTING_TRIGGER,
            "runtime_generated_queue_name": PSEUDO_FORMAL_BLOCK_ROUTING_QUEUE_NAME,
            "memory_status": PSEUDO_FORMAL_BLOCK_ROUTING_MEMORY_STATUS,
            "target_lanes": list(PSEUDO_FORMAL_BLOCK_ROUTING_TARGET_LANES),
            "queue_status_by_target_lane": dict(
                PSEUDO_FORMAL_BLOCK_ROUTING_QUEUE_STATUS_BY_TARGET_LANE
            ),
        },
    }


def pseudo_formalizer_prompt_contract() -> dict[str, Any]:
    return {
        "output_key": "pseudo_formal_proof_packets",
        "schema_id": PSEUDO_FORMALIZATION_SCHEMA_ID,
        "method_contract_id": PSEUDO_FORMAL_VERIFICATION_METHOD_CONTRACT_ID,
        "method_name": PSEUDO_FORMAL_VERIFICATION_METHOD_NAME,
        "verification_method_contract": pseudo_formal_verification_method_contract(),
        "required_packet_fields": ["theorem_id", "source_artifact_id", "blocks"],
        "required_block_fields": [
            "block_id",
            "block_type",
            "premises",
            "conclusion",
            "proof_text",
            "dependency_ids",
            "source_anchors",
            "lean_feasibility",
            "faithfulness_status",
            "block_verification",
        ],
        "dependency_rule": "dependency_ids must reference earlier block ids",
        "source_anchor_rule": "every nontrivial block needs a source anchor",
        "lean_feasibility_values": list(VALID_LEAN_FEASIBILITY),
        "block_verdict_values": list(VALID_BLOCK_VERDICTS),
        "proof_evidence_status": PSEUDO_FORMALIZATION_NOT_PROOF_EVIDENCE,
        "kernel_verified": False,
        "source_theorem_kernel_verified": False,
        "promotion_gate": PSEUDO_FORMALIZATION_PROMOTION_GATE,
        "boundary": "not theorem proof evidence; route residual blocks to existing work-order lanes",
        "work_order_target_lanes": list(PSEUDO_FORMAL_BLOCK_ROUTING_TARGET_LANES),
        "work_order_trigger": PSEUDO_FORMAL_BLOCK_ROUTING_TRIGGER,
        "work_order_learning_task": PSEUDO_FORMAL_BLOCK_ROUTING_LEARNING_TASK,
    }


def normalize_pseudo_formal_packet(packet: Mapping[str, Any]) -> dict[str, Any]:
    raw = deepcopy(dict(packet or {}))
    boundary_corrections = _boundary_corrections(raw)
    raw["schema_version"] = PSEUDO_FORMALIZATION_SCHEMA_VERSION
    raw["schema_id"] = PSEUDO_FORMALIZATION_SCHEMA_ID
    raw["component_name"] = PSEUDO_FORMALIZATION_COMPONENT
    raw["pseudo_formal_method_contract_id"] = (
        PSEUDO_FORMAL_VERIFICATION_METHOD_CONTRACT_ID
    )
    raw["pseudo_formal_method_name"] = PSEUDO_FORMAL_VERIFICATION_METHOD_NAME
    raw["pseudo_formal_pipeline_stages"] = [
        str(stage["stage_id"])
        for stage in PSEUDO_FORMAL_VERIFICATION_METHOD_STAGES
    ]
    raw["proof_evidence_status"] = PSEUDO_FORMALIZATION_NOT_PROOF_EVIDENCE
    raw["proof_evidence_boundary"] = PSEUDO_FORMALIZATION_PROOF_BOUNDARY
    raw["kernel_verified"] = False
    raw["source_theorem_kernel_verified"] = False
    raw["promotion_gate"] = PSEUDO_FORMALIZATION_PROMOTION_GATE
    raw["blocks"] = [
        _normalize_block(block, index)
        for index, block in enumerate(_as_mapping_rows(raw.get("blocks")))
    ]
    if not str(raw.get("packet_id", "") or "").strip():
        raw["packet_id"] = "pseudo_formal_packet:" + stable_hash(
            {
                "theorem_id": raw.get("theorem_id", ""),
                "source_artifact_id": raw.get("source_artifact_id", ""),
                "blocks": raw["blocks"],
            }
        )[:16]
    raw["boundary_corrections"] = boundary_corrections
    raw["all_ok"] = not validate_pseudo_formal_packet(raw)
    return raw


def validate_pseudo_formal_packet(packet: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if int(packet.get("schema_version", 0) or 0) != PSEUDO_FORMALIZATION_SCHEMA_VERSION:
        errors.append("schema_version must be 1")
    if str(packet.get("schema_id", "") or "") not in {
        "",
        PSEUDO_FORMALIZATION_SCHEMA_ID,
    }:
        errors.append("schema_id must be pseudo-formal proof packet schema id")
    if str(packet.get("pseudo_formal_method_contract_id", "") or "") != (
        PSEUDO_FORMAL_VERIFICATION_METHOD_CONTRACT_ID
    ):
        errors.append("pseudo_formal_method_contract_id must match PF+BV contract")
    if str(packet.get("proof_evidence_status", "") or "") != (
        PSEUDO_FORMALIZATION_NOT_PROOF_EVIDENCE
    ):
        errors.append("proof_evidence_status must be pseudo-formal non-proof")
    if bool(packet.get("kernel_verified", False)):
        errors.append("kernel_verified must be false for pseudo-formal packets")
    if bool(packet.get("source_theorem_kernel_verified", False)):
        errors.append(
            "source_theorem_kernel_verified must be false for pseudo-formal packets"
        )
    if str(packet.get("promotion_gate", "") or "") not in {
        "",
        PSEUDO_FORMALIZATION_PROMOTION_GATE,
    }:
        errors.append("promotion_gate must require target-prover kernel replay")
    if "not theorem proof evidence" not in str(
        packet.get("proof_evidence_boundary", PSEUDO_FORMALIZATION_PROOF_BOUNDARY)
    ).lower():
        errors.append("proof_evidence_boundary must say not theorem proof evidence")
    blocks = _as_mapping_rows(packet.get("blocks"))
    if not blocks:
        errors.append("blocks must contain at least one pseudo-formal block")
        return sorted(set(errors))
    seen: set[str] = set()
    for index, block in enumerate(blocks):
        block_id = str(block.get("block_id", "") or "").strip()
        if not block_id:
            errors.append(f"blocks[{index}] missing block_id")
        elif block_id in seen:
            errors.append(f"duplicate block_id: {block_id}")
        block_type = str(block.get("block_type", "") or "").strip()
        if block_type not in VALID_BLOCK_TYPES:
            errors.append(f"blocks[{index}] unsupported block_type: {block_type}")
        if not str(block.get("conclusion", "") or "").strip():
            errors.append(f"blocks[{index}] missing conclusion")
        if "proof_text" not in block:
            errors.append(f"blocks[{index}] missing proof_text")
        if not _as_mapping_rows(block.get("source_anchors")):
            errors.append(f"blocks[{index}] missing source_anchors")
        if bool(block.get("kernel_verified", False)):
            errors.append(f"blocks[{index}] kernel_verified must be false")
        faithfulness = str(block.get("faithfulness_status", "unchecked") or "unchecked")
        if faithfulness not in VALID_FAITHFULNESS_STATUSES:
            errors.append(
                f"blocks[{index}] unsupported faithfulness_status: {faithfulness}"
            )
        feasibility = str(block.get("lean_feasibility", "unknown") or "unknown")
        if feasibility not in VALID_LEAN_FEASIBILITY:
            errors.append(f"blocks[{index}] unsupported lean_feasibility: {feasibility}")
        verdict = _block_verdict(block)
        if verdict not in VALID_BLOCK_VERDICTS:
            errors.append(f"blocks[{index}] unsupported block verdict: {verdict}")
        for dep_id in _string_list(block.get("dependency_ids")):
            if dep_id == block_id:
                errors.append(f"blocks[{index}] dependency_ids cannot include self")
            elif dep_id not in seen:
                errors.append(
                    f"blocks[{index}] dependency_id must reference an earlier block: {dep_id}"
                )
        seen.add(block_id)
    return sorted(set(errors))


def pseudo_formal_block_work_order_rows(packet: Mapping[str, Any]) -> list[dict[str, Any]]:
    normalized = normalize_pseudo_formal_packet(packet)
    rows: list[dict[str, Any]] = []
    for block in _as_mapping_rows(normalized.get("blocks")):
        rows.extend(_work_order_rows_for_block(normalized, block))
    return rows


def pseudo_formal_packet_json_schema() -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": PSEUDO_FORMALIZATION_SCHEMA_ID,
        "title": "Pseudo-Formal Proof Packet",
        "type": "object",
        "required": [
            "schema_version",
            "packet_id",
            "blocks",
            "pseudo_formal_method_contract_id",
            "pseudo_formal_pipeline_stages",
            "proof_evidence_status",
            "kernel_verified",
            "source_theorem_kernel_verified",
            "promotion_gate",
        ],
        "properties": {
            "schema_version": {
                "type": "integer",
                "const": PSEUDO_FORMALIZATION_SCHEMA_VERSION,
            },
            "schema_id": {"type": "string", "const": PSEUDO_FORMALIZATION_SCHEMA_ID},
            "packet_id": {"type": "string", "minLength": 1},
            "component_name": {
                "type": "string",
                "const": PSEUDO_FORMALIZATION_COMPONENT,
            },
            "pseudo_formal_method_contract_id": {
                "type": "string",
                "const": PSEUDO_FORMAL_VERIFICATION_METHOD_CONTRACT_ID,
            },
            "pseudo_formal_method_name": {
                "type": "string",
                "const": PSEUDO_FORMAL_VERIFICATION_METHOD_NAME,
            },
            "pseudo_formal_pipeline_stages": {
                "type": "array",
                "items": {"type": "string"},
                "contains": {"const": PSEUDO_FORMAL_BLOCK_ROUTING_METHOD_STAGE},
            },
            "proof_evidence_status": {
                "type": "string",
                "const": PSEUDO_FORMALIZATION_NOT_PROOF_EVIDENCE,
            },
            "proof_evidence_boundary": {
                "type": "string",
                "pattern": "not theorem proof evidence",
            },
            "kernel_verified": {"type": "boolean", "const": False},
            "source_theorem_kernel_verified": {"type": "boolean", "const": False},
            "promotion_gate": {
                "type": "string",
                "const": PSEUDO_FORMALIZATION_PROMOTION_GATE,
            },
            "blocks": {
                "type": "array",
                "minItems": 1,
                "items": pseudo_formal_block_json_schema(),
            },
        },
    }


def pseudo_formal_block_json_schema() -> dict[str, Any]:
    return {
        "$id": PSEUDO_FORMAL_BLOCK_SCHEMA_ID,
        "type": "object",
        "required": [
            "block_id",
            "block_type",
            "conclusion",
            "proof_text",
            "dependency_ids",
            "source_anchors",
            "lean_feasibility",
            "faithfulness_status",
            "block_verification",
        ],
        "properties": {
            "block_id": {"type": "string", "minLength": 1},
            "block_type": {"type": "string", "enum": list(VALID_BLOCK_TYPES)},
            "premises": {"type": "array"},
            "conclusion": {"type": "string", "minLength": 1},
            "proof_text": {"type": "string"},
            "dependency_ids": {"type": "array", "items": {"type": "string"}},
            "source_anchors": {"type": "array", "minItems": 1},
            "semantic_primitive_requirements": {"type": "array"},
            "lean_feasibility": {
                "type": "string",
                "enum": list(VALID_LEAN_FEASIBILITY),
            },
            "faithfulness_status": {
                "type": "string",
                "enum": list(VALID_FAITHFULNESS_STATUSES),
            },
            "block_verification": {
                "type": "object",
                "required": ["verdict"],
                "properties": {
                    "verdict": {
                        "type": "string",
                        "enum": list(VALID_BLOCK_VERDICTS),
                    },
                    "reason": {"type": "string"},
                },
            },
            "kernel_verified": {"type": "boolean", "const": False},
        },
    }


def pseudo_formal_work_order_row_json_schema() -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": PSEUDO_FORMAL_WORK_ORDER_ROW_SCHEMA_ID,
        "title": "Pseudo-Formal Work Order Row",
        "type": "object",
        "required": [
            "row_id",
            "source_packet_id",
            "source_block_id",
            "row_kind",
            "target_lane",
            "pseudo_formal_method_contract_id",
            "pseudo_formal_pipeline_stage",
            "proof_evidence_status",
            "kernel_verified",
            "promotion_gate",
        ],
        "properties": {
            "row_id": {"type": "string", "minLength": 1},
            "source_packet_id": {"type": "string", "minLength": 1},
            "source_block_id": {"type": "string", "minLength": 1},
            "row_kind": {"type": "string", "minLength": 1},
            "target_lane": {
                "type": "string",
                "enum": list(PSEUDO_FORMAL_BLOCK_ROUTING_TARGET_LANES),
            },
            "pseudo_formal_method_contract_id": {
                "type": "string",
                "const": PSEUDO_FORMAL_VERIFICATION_METHOD_CONTRACT_ID,
            },
            "pseudo_formal_pipeline_stage": {
                "type": "string",
                "const": PSEUDO_FORMAL_BLOCK_ROUTING_METHOD_STAGE,
            },
            "proof_evidence_status": {
                "type": "string",
                "const": PSEUDO_FORMALIZATION_NOT_PROOF_EVIDENCE,
            },
            "kernel_verified": {"type": "boolean", "const": False},
            "promotion_gate": {
                "type": "string",
                "const": PSEUDO_FORMALIZATION_PROMOTION_GATE,
            },
        },
    }


def _normalize_block(block: Mapping[str, Any], index: int) -> dict[str, Any]:
    normalized = deepcopy(dict(block or {}))
    if not str(normalized.get("block_id", "") or "").strip():
        normalized["block_id"] = f"pf_block_{index + 1}"
    normalized["block_id"] = str(normalized["block_id"]).strip()
    normalized["block_type"] = str(
        normalized.get("block_type", "claim") or "claim"
    ).strip()
    normalized["premises"] = _string_list(normalized.get("premises"))
    normalized["conclusion"] = str(
        normalized.get("conclusion", normalized.get("statement", "")) or ""
    ).strip()
    normalized["proof_text"] = str(normalized.get("proof_text", "") or "")
    normalized["dependency_ids"] = _string_list(normalized.get("dependency_ids"))
    normalized["source_anchors"] = _normalize_source_anchors(
        normalized.get("source_anchors")
    )
    normalized["semantic_primitive_requirements"] = _string_list(
        normalized.get("semantic_primitive_requirements")
    )
    normalized["lean_feasibility"] = str(
        normalized.get("lean_feasibility", "unknown") or "unknown"
    ).strip()
    normalized["faithfulness_status"] = str(
        normalized.get("faithfulness_status", "unchecked") or "unchecked"
    ).strip()
    verification = normalized.get("block_verification", {})
    if not isinstance(verification, Mapping):
        verification = {"verdict": str(verification or "unknown")}
    normalized["block_verification"] = {
        "verdict": str(verification.get("verdict", "not_run") or "not_run").strip(),
        "reason": str(verification.get("reason", "") or "").strip(),
    }
    normalized["kernel_verified"] = False
    return normalized


def _work_order_rows_for_block(
    packet: Mapping[str, Any],
    block: Mapping[str, Any],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    feasibility = str(block.get("lean_feasibility", "unknown") or "unknown")
    verdict = _block_verdict(block)
    faithfulness = str(block.get("faithfulness_status", "unchecked") or "unchecked")
    if faithfulness in {"unfaithful", "needs_review"}:
        rows.append(
            _work_order_row(
                packet,
                block,
                row_kind="pseudo_formal_faithfulness_review",
                target_lane=PSEUDO_FORMAL_TARGET_LANE_FORMAL_GAP,
                reason=f"faithfulness_status={faithfulness}",
            )
        )
    if verdict == "failed":
        rows.append(
            _work_order_row(
                packet,
                block,
                row_kind="pseudo_formal_block_verification_failure",
                target_lane=PSEUDO_FORMAL_TARGET_LANE_FORMAL_GAP,
                reason=str(
                    block.get("block_verification", {}).get(
                        "reason", "block verifier rejected local proof"
                    )
                ),
            )
        )
    if feasibility == "lean_now":
        rows.append(
            _work_order_row(
                packet,
                block,
                row_kind="pseudo_formal_lean_candidate_seed",
                target_lane=PSEUDO_FORMAL_TARGET_LANE_FORMAL_TARGETS,
                reason="block is triaged as Lean-feasible",
            )
        )
    elif feasibility == "needs_rag":
        rows.append(
            _work_order_row(
                packet,
                block,
                row_kind="pseudo_formal_formal_library_grounding_query",
                target_lane=PSEUDO_FORMAL_TARGET_LANE_LEAN_RAG,
                reason="block needs target-prover library grounding",
            )
        )
    elif feasibility == "needs_library":
        rows.append(
            _work_order_row(
                packet,
                block,
                row_kind="pseudo_formal_library_gap",
                target_lane=PSEUDO_FORMAL_TARGET_LANE_FORMAL_GAP,
                reason="block requires unavailable formal library support",
            )
        )
    elif feasibility == "needs_semantic_definition":
        rows.append(
            _work_order_row(
                packet,
                block,
                row_kind="pseudo_formal_exact_semantic_definition_request",
                target_lane=PSEUDO_FORMAL_TARGET_LANE_EXACT_SEMANTIC_DEFINITION,
                reason="block requires exact semantic definitions before Lean replay",
            )
        )
    elif feasibility == "pseudo_only":
        rows.append(
            _work_order_row(
                packet,
                block,
                row_kind="pseudo_formal_nonlean_residual_gap",
                target_lane=PSEUDO_FORMAL_TARGET_LANE_FORMAL_GAP,
                reason="block is not currently Lean-realizable",
            )
        )
    for primitive in _string_list(block.get("semantic_primitive_requirements")):
        rows.append(
            _work_order_row(
                packet,
                block,
                row_kind="pseudo_formal_semantic_primitive_request",
                target_lane=PSEUDO_FORMAL_TARGET_LANE_SOURCE_TO_BRIDGE,
                reason=f"semantic primitive required: {primitive}",
                extra={"semantic_primitive": primitive},
            )
        )
    return rows


def _work_order_row(
    packet: Mapping[str, Any],
    block: Mapping[str, Any],
    *,
    row_kind: str,
    target_lane: str,
    reason: str,
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    base = {
        "source_packet_id": str(packet.get("packet_id", "") or ""),
        "source_theorem_id": str(packet.get("theorem_id", "") or ""),
        "source_artifact_id": str(packet.get("source_artifact_id", "") or ""),
        "source_block_id": str(block.get("block_id", "") or ""),
        "source_block_type": str(block.get("block_type", "") or ""),
        "source_block_conclusion": str(block.get("conclusion", "") or ""),
        "source_anchors": list(_as_mapping_rows(block.get("source_anchors"))),
        "row_kind": row_kind,
        "target_lane": target_lane,
        "pseudo_formal_method_contract_id": str(
            packet.get(
                "pseudo_formal_method_contract_id",
                PSEUDO_FORMAL_VERIFICATION_METHOD_CONTRACT_ID,
            )
            or PSEUDO_FORMAL_VERIFICATION_METHOD_CONTRACT_ID
        ),
        "pseudo_formal_method_name": str(
            packet.get(
                "pseudo_formal_method_name",
                PSEUDO_FORMAL_VERIFICATION_METHOD_NAME,
            )
            or PSEUDO_FORMAL_VERIFICATION_METHOD_NAME
        ),
        "pseudo_formal_pipeline_stage": PSEUDO_FORMAL_BLOCK_ROUTING_METHOD_STAGE,
        "pseudo_formal_upstream_pipeline_stages": _string_list(
            packet.get("pseudo_formal_pipeline_stages")
        ),
        "reason": reason,
        "proof_evidence_status": PSEUDO_FORMALIZATION_NOT_PROOF_EVIDENCE,
        "proof_evidence_boundary": PSEUDO_FORMALIZATION_PROOF_BOUNDARY,
        "kernel_verified": False,
        "source_theorem_kernel_verified": False,
        "promotion_gate": PSEUDO_FORMALIZATION_PROMOTION_GATE,
    }
    if extra:
        base.update(dict(extra))
    base["row_id"] = "pseudo_formal_work_order:" + stable_hash(base)[:16]
    return base


def _boundary_corrections(packet: Mapping[str, Any]) -> list[str]:
    corrections: list[str] = []
    if bool(packet.get("kernel_verified", False)):
        corrections.append("kernel_verified_forced_false")
    if bool(packet.get("source_theorem_kernel_verified", False)):
        corrections.append("source_theorem_kernel_verified_forced_false")
    if str(packet.get("proof_evidence_status", "") or "") not in {
        "",
        PSEUDO_FORMALIZATION_NOT_PROOF_EVIDENCE,
    }:
        corrections.append("proof_evidence_status_forced_non_proof")
    if str(packet.get("promotion_gate", "") or "") not in {
        "",
        PSEUDO_FORMALIZATION_PROMOTION_GATE,
    }:
        corrections.append("promotion_gate_forced_kernel_replay")
    return corrections


def _normalize_source_anchors(value: Any) -> list[dict[str, str]]:
    anchors: list[dict[str, str]] = []
    for item in value or []:
        if isinstance(item, Mapping):
            anchors.append(
                {
                    "kind": str(item.get("kind", "other") or "other").strip(),
                    "id": str(item.get("id", item.get("source_id", "")) or "").strip(),
                    "excerpt": str(item.get("excerpt", "") or "").strip(),
                }
            )
        elif str(item or "").strip():
            anchors.append(
                {
                    "kind": "other",
                    "id": str(item or "").strip(),
                    "excerpt": "",
                }
            )
    return anchors


def _block_verdict(block: Mapping[str, Any]) -> str:
    verification = block.get("block_verification", {})
    if isinstance(verification, Mapping):
        return str(verification.get("verdict", "not_run") or "not_run")
    return str(verification or "unknown")


def _as_mapping_rows(value: Any) -> list[Mapping[str, Any]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return [row for row in value if isinstance(row, Mapping)]


def _string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    if not isinstance(value, Sequence) or isinstance(value, (bytes, bytearray)):
        return [str(value).strip()] if str(value).strip() else []
    return [str(item).strip() for item in value if str(item).strip()]
