from __future__ import annotations

from collections import Counter
from copy import deepcopy
import re
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
PSEUDO_FORMAL_REFERENCE_REPO_URL = "https://github.com/Slim205/pseudo-formalization"
PSEUDO_FORMAL_REFERENCE_ARXIV_URL = "https://arxiv.org/abs/2605.20531"
PSEUDO_FORMAL_MAX_PROOF_TREE_DEPTH = 4
PSEUDO_FORMAL_DEFAULT_BLOCK_DEPTH = 1
PSEUDO_FORMAL_DEFAULT_DEPENDENCY_SCOPE = "earlier_block_statement_only"
PSEUDO_FORMAL_DEFAULT_CALIBRATION_STRICTNESS = "lean_bridge_conservative"
PSEUDO_FORMAL_DEFAULT_AGGREGATION_RULE = "parallel_pessimistic_aggregation"
PSEUDO_FORMAL_BLOCK_VERIFICATION_REQUEST_ROW_KIND = (
    "pseudo_formal_independent_block_verification_request"
)
PSEUDO_FORMAL_STRUCTURAL_DECOMPOSITION_REQUEST_ROW_KIND = (
    "pseudo_formal_structural_decomposition_request"
)
PSEUDO_FORMAL_FORMALIZER_PROPOSED_BLOCK_VERIFIER_PROVENANCE = "formalizer_proposed"
PSEUDO_FORMAL_NOT_RUN_BLOCK_VERIFIER_PROVENANCE = "not_run"
PSEUDO_FORMAL_INDEPENDENT_BLOCK_VERIFIER_PROVENANCES = (
    "independent_block_verifier",
    "runtime_block_verifier",
    "external_block_verifier",
)
PSEUDO_FORMAL_MAX_BLOCK_PREMISES = 12
PSEUDO_FORMAL_MAX_BLOCK_DEPENDENCIES = 8
PSEUDO_FORMAL_MAX_BLOCK_INHERITED_SCOPE_ITEMS = 8
PSEUDO_FORMAL_MAX_BLOCK_SOURCE_ANCHORS = 8
PSEUDO_FORMAL_MAX_BLOCK_CONCLUSION_CHARS = 1600
PSEUDO_FORMAL_MAX_BLOCK_PROOF_TEXT_CHARS = 6000
PSEUDO_FORMAL_MAX_BLOCK_LOCAL_CONTEXT_CHARS = 9000
PSEUDO_FORMAL_BLOCK_STRUCTURE_RULES = (
    "at most four proof-tree layers",
    "bounded local context per block: concise premises, conclusion, proof, inherited scope, and dependency list",
    "no trivial restatement-only decomposition",
    "dependencies are statement-level citations, not hidden proof-body access",
    "same-level dependency_ids must reference earlier blocks",
    "scope_parent_id encodes the scope-inheritance forest and references at most one earlier block",
    "assumptions modified from an enclosing context must be restated",
)
VALID_DEPENDENCY_SCOPES = (
    "earlier_block_statement_only",
    "direct_child_or_earlier_statement_only",
)
VALID_FAITHFULNESS_REPAIR_STATUSES = (
    "not_required",
    "needs_repair",
    "repaired",
    "unavailable",
)
VALID_CALIBRATION_STRICTNESS = (
    "lean_bridge_conservative",
    "publication_strict",
    "debug_lenient",
    "not_run",
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
BLOCK_TYPE_ALIASES = {
    "assumption": "fact",
    "assumption_block": "fact",
    "assumption_instantiation": "fact",
    "hypothesis": "fact",
    "hypothesis_block": "fact",
    "hypothesis_introduction": "fact",
    "premise": "fact",
    "premise_block": "fact",
    "theorem_step": "lemma",
    "lemma_step": "lemma",
    "lemma_application": "lemma",
    "proof_step": "lemma",
    "proof_block": "lemma",
    "derivation_step": "lemma",
    "derivation_block": "lemma",
    "argument_step": "lemma",
    "conclusion": "claim",
    "conclusion_block": "claim",
    "result": "claim",
    "result_block": "claim",
    "final_claim": "claim",
    "main_conclusion": "claim",
    "conclusion_step": "claim",
    "residual": "claim",
    "residual_block": "claim",
    "definition_block": "definition",
    "definition_instantiation": "definition",
    "calc_block": "calculation",
    "calculation_block": "calculation",
    "case_block": "case",
}
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
PSEUDO_FORMAL_PACKET_VALIDATION_QUARANTINE_ROW_KIND = (
    "pseudo_formal_packet_validation_quarantine"
)
PSEUDO_FORMAL_NON_ROUTABLE_WORK_ORDER_ROW_KINDS = (
    PSEUDO_FORMAL_PACKET_VALIDATION_QUARANTINE_ROW_KIND,
    "pseudo_formal_block_verification_pending",
    "pseudo_formal_block_verification_failure_blocked_by_faithfulness",
    "pseudo_formal_block_verification_failure_blocked_by_independent_bv",
    "pseudo_formal_lean_candidate_seed_blocked",
    "pseudo_formal_formal_library_grounding_query_blocked_by_faithfulness",
    "pseudo_formal_library_gap_blocked_by_faithfulness",
    "pseudo_formal_exact_semantic_definition_request_blocked_by_faithfulness",
    (
        "pseudo_formal_exact_semantic_definition_request"
        "_blocked_by_missing_semantic_requirements"
    ),
    "pseudo_formal_nonlean_residual_gap_blocked_by_faithfulness",
    "pseudo_formal_semantic_primitive_request_blocked_by_faithfulness",
)

PSEUDO_FORMAL_VALIDATION_ISSUE_MARKERS: tuple[
    tuple[str, tuple[str, ...]],
    ...,
] = (
    (
        "missing_required_packet",
        (
            "requires at least one pseudo_formal_proof_packets",
            "no locally valid pseudo_formal_proof_packets",
        ),
    ),
    ("missing_blocks", ("blocks must contain at least one pseudo-formal block",)),
    ("missing_conclusion", ("missing conclusion",)),
    ("missing_source_anchors", ("missing source_anchors",)),
    ("unsupported_block_type", ("unsupported block_type",)),
    ("unsupported_faithfulness_status", ("unsupported faithfulness_status",)),
    ("unsupported_lean_feasibility", ("unsupported lean_feasibility",)),
    ("unsupported_block_verdict", ("unsupported block verdict",)),
    (
        "accepted_without_rollout_count",
        (
            "accepted block_verification must record rollout_count",
            "accepted_without_rollout_count",
        ),
    ),
    (
        "forbidden_kernel_claim",
        (
            "kernel_verified must be false",
            "source_theorem_kernel_verified must be false",
            "proof_evidence_status must be pseudo-formal non-proof",
        ),
    ),
    (
        "dependency_or_scope_order",
        (
            "dependency_id must reference",
            "dependency_ids cannot include self",
            "scope_parent_id must reference",
            "scope_parent_id cannot be self",
            "dependency cycle",
        ),
    ),
    (
        "no_lane_routable_work_order_rows",
        (
            "valid pf/bv packet did not produce",
            "no lane-routable",
            "no effective lane-routable",
        ),
    ),
    (
        "missing_required_target_lane",
        ("only generic review rows", "did not route any effective row"),
    ),
)


def pseudo_formal_verification_method_contract() -> dict[str, Any]:
    return {
        "contract_id": PSEUDO_FORMAL_VERIFICATION_METHOD_CONTRACT_ID,
        "method_name": PSEUDO_FORMAL_VERIFICATION_METHOD_NAME,
        "source_basis": {
            "paper_title": "Pseudo-Formalization for Automatic Proof Verification",
            "arxiv_id": "2605.20531",
            "arxiv_url": PSEUDO_FORMAL_REFERENCE_ARXIV_URL,
            "reference_repo_url": PSEUDO_FORMAL_REFERENCE_REPO_URL,
            "method_short_name": "PF+BV",
            "benchmarks": ["Hard2Verify", "ArxivMathGradingBench"],
        },
        "integration_decision": {
            "adopt_as": "formalizer_proofengineer_intermediate_verifier_and_router",
            "do_not_adopt_as": (
                "kernel prover, Lean replacement, or proof-evidence promotion gate"
            ),
            "runtime_role": (
                "decompose large natural-language/statistical proof artifacts into "
                "bounded blocks, verify/reject blocks with explicit calibration, "
                "and route residuals into Lean/RAG/source-to-bridge/semantic-definition "
                "work orders"
            ),
            "maturity_boundary": (
                "the public repo is a prompt-and-benchmark implementation; reuse "
                "its method structure and evaluation ideas behind this system's "
                "typed generator/runtime contracts rather than vendoring it as a "
                "core prover dependency"
            ),
        },
        "pipeline_stages": deepcopy(PSEUDO_FORMAL_VERIFICATION_METHOD_STAGES),
        "graph_contract": {
            "dependency_graph": "directed_acyclic_graph",
            "scope_inheritance_graph": "forest",
            "scope_parent_field": "scope_parent_id",
            "dependency_access": "statement_only_no_hidden_proof_body_access",
            "same_level_order_rule": "same-level dependencies must cite earlier blocks",
            "scope_parent_order_rule": (
                "scope_parent_id is empty for roots and otherwise references an "
                "earlier block whose scope is inherited"
            ),
            "scope_access": (
                "block verification may use inherited parent scope plus explicit "
                "premises, but not hidden proof text from dependencies"
            ),
            "hoisting_rule": (
                "any intermediate object needed from another proof body must be "
                "hoisted into its own block statement before it can be cited"
            ),
        },
        "block_verification_scope": (
            "verify each pseudo-formal block independently against its explicit "
            "premises, inherited scope, declared dependencies, conclusion, and proof"
        ),
        "block_structure_contract": {
            "max_proof_tree_depth": PSEUDO_FORMAL_MAX_PROOF_TREE_DEPTH,
            "max_block_premises": PSEUDO_FORMAL_MAX_BLOCK_PREMISES,
            "max_block_dependencies": PSEUDO_FORMAL_MAX_BLOCK_DEPENDENCIES,
            "max_block_inherited_scope_items": (
                PSEUDO_FORMAL_MAX_BLOCK_INHERITED_SCOPE_ITEMS
            ),
            "max_block_source_anchors": PSEUDO_FORMAL_MAX_BLOCK_SOURCE_ANCHORS,
            "max_block_conclusion_chars": PSEUDO_FORMAL_MAX_BLOCK_CONCLUSION_CHARS,
            "max_block_proof_text_chars": PSEUDO_FORMAL_MAX_BLOCK_PROOF_TEXT_CHARS,
            "max_block_local_context_chars": (
                PSEUDO_FORMAL_MAX_BLOCK_LOCAL_CONTEXT_CHARS
            ),
            "dependency_scopes": list(VALID_DEPENDENCY_SCOPES),
            "rules": list(PSEUDO_FORMAL_BLOCK_STRUCTURE_RULES),
            "default_dependency_scope": PSEUDO_FORMAL_DEFAULT_DEPENDENCY_SCOPE,
        },
        "faithfulness_repair_contract": {
            "required_when_status": ["unfaithful", "needs_review"],
            "required_fields": [
                "status",
                "attempts",
                "flagged_discrepancies",
            ],
            "allowed_statuses": list(VALID_FAITHFULNESS_REPAIR_STATUSES),
        },
        "bv_calibration_contract": {
            "strictness_values": list(VALID_CALIBRATION_STRICTNESS),
            "default_strictness": PSEUDO_FORMAL_DEFAULT_CALIBRATION_STRICTNESS,
            "aggregation_rule": PSEUDO_FORMAL_DEFAULT_AGGREGATION_RULE,
            "acceptance_boundary": (
                "PF/BV acceptance is routing confidence only; theorem proof "
                "promotion still requires target-prover kernel replay"
            ),
        },
        "calibration_rule": (
            "aggregate block verifier reports under an explicit strictness "
            "threshold; distinguish source-proof errors from rewrite artifacts"
        ),
        "parallel_aggregation_rule": (
            "use independent stochastic rollouts with pessimistic proof acceptance "
            "and union/deduplication of flagged error locations for error finding"
        ),
        "runtime_activation_policy": {
            "activate_when": [
                "source-theorem proof-body repair is blocked",
                "semantic anchors or exact definitions are missing",
                "Lean library support is missing or unknown",
                "a proof step is too large or underspecified for one Lean translation pass",
            ],
            "required_outputs": [
                "bounded proof blocks",
                "source anchors",
                "faithfulness status and repair metadata",
                "block-verifier verdicts",
                "Lean feasibility triage",
                "lane-specific residual work orders",
            ],
            "forbidden_outputs": [
                "kernel_verified=true",
                "source_theorem_kernel_verified=true",
                "promotion without target-prover replay",
                "silent repair of an unfaithful source proof",
            ],
        },
        "reuse_policy": {
            "reuse": [
                "structured rewrite rules",
                "faithfulness-check and regeneration loop",
                "block verifier prompt pattern",
                "calibration and pessimistic parallel aggregation ideas",
                "benchmark harness pattern",
            ],
            "do_not_reuse_directly": [
                "benchmark-specific scoring assumptions",
                "hardcoded provider/model choices",
                "ad hoc XML parsing as the runtime source of truth",
                "data artifacts whose license or redistribution status is unclear",
            ],
            "adapter_boundary": (
                "all live calls must go through this system's GeneratorBackend, "
                "typed packet schemas, audit manifests, and proof-evidence gates"
            ),
        },
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
            "dependency_ids": [
                "earlier block ids, plus direct child block ids only when dependency_scope allows"
            ],
            "scope_parent_id": "empty for a root block, otherwise one earlier block id",
            "inherited_scope": [
                "optional bounded scope text inherited from scope_parent_id"
            ],
            "source_anchors": [
                {
                    "kind": "theory_trace|paper|proof_body|theorem_card|other",
                    "id": "source-local id",
                    "excerpt": "bounded source excerpt or pointer",
                }
            ],
            "block_depth": (
                "1..4 PF tree depth; keep decomposition shallow and nontrivial"
            ),
            "structural_quality": (
                "Good-PF bounded-context audit; all_ok must be true before "
                "the block can feed Lean/RAG/source-to-bridge lanes"
            ),
            "dependency_scope": list(VALID_DEPENDENCY_SCOPES),
            "semantic_primitive_requirements": ["missing primitive or definition ids"],
            "lean_feasibility": list(VALID_LEAN_FEASIBILITY),
            "faithfulness_status": list(VALID_FAITHFULNESS_STATUSES),
            "faithfulness_repair": {
                "status": list(VALID_FAITHFULNESS_REPAIR_STATUSES),
                "attempts": "number of rewrite/repair attempts",
                "flagged_discrepancies": [
                    "strengthening, weakening, omitted content, added content, notation drift, or scope error"
                ],
            },
            "block_verification": {
                "verdict": list(VALID_BLOCK_VERDICTS),
                "reason": "short verifier rationale",
                "verifier_provenance": (
                    "formalizer_proposed unless produced by a separate "
                    "independent block-verifier call"
                ),
                "independent_verifier": (
                    "true only for a verifier call independent from the "
                    "pseudo-formal rewrite generator"
                ),
                "strictness_threshold": list(VALID_CALIBRATION_STRICTNESS),
                "aggregation_rule": PSEUDO_FORMAL_DEFAULT_AGGREGATION_RULE,
                "rollout_count": (
                    "independent BV rollouts used for this report; must be at "
                    "least 1 when verdict=accepted"
                ),
            },
        },
        "packet_calibration_contract": {
            "strictness_threshold": list(VALID_CALIBRATION_STRICTNESS),
            "aggregation_rule": PSEUDO_FORMAL_DEFAULT_AGGREGATION_RULE,
            "pessimistic_acceptance": (
                "proof-level pseudo-formal acceptance requires every rollout/block "
                "accepted, but remains non-proof evidence"
            ),
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
            "block_depth",
            "premises",
            "conclusion",
            "proof_text",
            "dependency_ids",
            "scope_parent_id",
            "dependency_scope",
            "source_anchors",
            "semantic_primitive_requirements",
            "lean_feasibility",
            "faithfulness_status",
            "faithfulness_repair",
            "block_verification",
        ],
        "dependency_rule": (
            "dependency_ids must reference earlier block ids unless "
            "dependency_scope=direct_child_or_earlier_statement_only, in which "
            "case a block may also cite its own direct child block statements"
        ),
        "scope_parent_rule": (
            "scope_parent_id must be empty for a root block or reference one earlier "
            "block; this is the scope-inheritance forest, separate from dependency_ids"
        ),
        "dependency_scope_rule": (
            "dependencies are statement-level citations under PF/BV scope rules; "
            "hidden proof-body access must be hoisted into its own block; "
            "same-level dependencies must still cite earlier blocks"
        ),
        "block_structure_rules": list(PSEUDO_FORMAL_BLOCK_STRUCTURE_RULES),
        "max_proof_tree_depth": PSEUDO_FORMAL_MAX_PROOF_TREE_DEPTH,
        "source_anchor_rule": "every nontrivial block needs a source anchor",
        "lean_feasibility_values": list(VALID_LEAN_FEASIBILITY),
        "block_verdict_values": list(VALID_BLOCK_VERDICTS),
        "calibration_strictness_values": list(VALID_CALIBRATION_STRICTNESS),
        "default_bv_calibration": _default_bv_calibration(),
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
    raw["block_structure_contract"] = _default_block_structure_contract(
        raw.get("block_structure_contract")
    )
    raw["bv_calibration"] = _normalize_bv_calibration(raw.get("bv_calibration"))
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
    scope_parent_by_block_id: dict[str, str] = {}
    dependency_ids_by_block_id: dict[str, list[str]] = {}
    for block in blocks:
        block_id = str(block.get("block_id", "") or "").strip()
        if not block_id or block_id in scope_parent_by_block_id:
            continue
        scope_parent_by_block_id[block_id] = str(
            block.get(
                "scope_parent_id",
                block.get("scope_parent", block.get("parent_block_id", "")),
            )
            or ""
        ).strip()
    seen: set[str] = set()
    block_depths: dict[str, int] = {}
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
        block_depth = _int_or_none(block.get("block_depth"))
        if block_depth is None:
            errors.append(f"blocks[{index}] missing block_depth")
        elif (
            block_depth < 1
            or block_depth > PSEUDO_FORMAL_MAX_PROOF_TREE_DEPTH
        ):
            errors.append(
                f"blocks[{index}] block_depth must be between 1 and "
                f"{PSEUDO_FORMAL_MAX_PROOF_TREE_DEPTH}"
            )
        dependency_scope = str(
            block.get("dependency_scope", PSEUDO_FORMAL_DEFAULT_DEPENDENCY_SCOPE)
            or PSEUDO_FORMAL_DEFAULT_DEPENDENCY_SCOPE
        )
        if dependency_scope not in VALID_DEPENDENCY_SCOPES:
            errors.append(
                f"blocks[{index}] unsupported dependency_scope: {dependency_scope}"
            )
        scope_parent_id = str(block.get("scope_parent_id", "") or "").strip()
        if scope_parent_id:
            if scope_parent_id == block_id:
                errors.append(f"blocks[{index}] scope_parent_id cannot be self")
            elif scope_parent_id not in seen:
                errors.append(
                    "blocks[{}] scope_parent_id must reference an earlier block: "
                    "{}".format(index, scope_parent_id)
                )
            else:
                parent_depth = block_depths.get(scope_parent_id)
                if (
                    block_depth is not None
                    and parent_depth is not None
                    and block_depth <= parent_depth
                ):
                    errors.append(
                        f"blocks[{index}] block_depth must be deeper than "
                        f"scope_parent_id {scope_parent_id}"
                    )
        if not _as_mapping_rows(block.get("source_anchors")):
            errors.append(f"blocks[{index}] missing source_anchors")
        if bool(block.get("kernel_verified", False)):
            errors.append(f"blocks[{index}] kernel_verified must be false")
        faithfulness = str(block.get("faithfulness_status", "unchecked") or "unchecked")
        if faithfulness not in VALID_FAITHFULNESS_STATUSES:
            errors.append(
                f"blocks[{index}] unsupported faithfulness_status: {faithfulness}"
            )
        faithfulness_repair = block.get("faithfulness_repair", {})
        if not isinstance(faithfulness_repair, Mapping):
            errors.append(f"blocks[{index}] faithfulness_repair must be an object")
        else:
            repair_status = str(
                faithfulness_repair.get("status", "not_required")
                or "not_required"
            )
            if repair_status not in VALID_FAITHFULNESS_REPAIR_STATUSES:
                errors.append(
                    f"blocks[{index}] unsupported faithfulness_repair.status: "
                    f"{repair_status}"
                )
            if (
                faithfulness in {"unfaithful", "needs_review"}
                and repair_status == "not_required"
            ):
                errors.append(
                    f"blocks[{index}] faithfulness_repair.status must record "
                    "needs_repair, repaired, or unavailable when faithfulness "
                    f"status is {faithfulness}"
                )
        feasibility = str(block.get("lean_feasibility", "unknown") or "unknown")
        if feasibility not in VALID_LEAN_FEASIBILITY:
            errors.append(f"blocks[{index}] unsupported lean_feasibility: {feasibility}")
        verdict = _block_verdict(block)
        if verdict not in VALID_BLOCK_VERDICTS:
            errors.append(f"blocks[{index}] unsupported block verdict: {verdict}")
        block_verification = (
            block.get("block_verification", {})
            if isinstance(block.get("block_verification", {}), Mapping)
            else {}
        )
        block_verification_rollout_count = max(
            0,
            _int_or_none(block_verification.get("rollout_count")) or 0,
        )
        if verdict == "accepted" and block_verification_rollout_count < 1:
            errors.append(
                f"blocks[{index}] accepted block_verification must record "
                "rollout_count >= 1"
            )
        dependency_ids = _string_list(block.get("dependency_ids"))
        if block_id:
            dependency_ids_by_block_id[block_id] = dependency_ids
        for dep_id in dependency_ids:
            if dep_id == block_id:
                errors.append(f"blocks[{index}] dependency_ids cannot include self")
            elif dep_id not in seen and not (
                dependency_scope == "direct_child_or_earlier_statement_only"
                and scope_parent_by_block_id.get(dep_id) == block_id
            ):
                if dependency_scope == "direct_child_or_earlier_statement_only":
                    errors.append(
                        "blocks[{}] dependency_id must reference an earlier "
                        "block or direct child: {}".format(index, dep_id)
                    )
                else:
                    errors.append(
                        "blocks[{}] dependency_id must reference an earlier "
                        "block: {}".format(index, dep_id)
                    )
        seen.add(block_id)
        if block_depth is not None:
            block_depths[block_id] = block_depth
    cycle_nodes = _pseudo_formal_dependency_cycle_nodes(dependency_ids_by_block_id)
    if cycle_nodes:
        errors.append(
            "dependency graph must be acyclic; cycle includes: "
            + ", ".join(cycle_nodes)
        )
    return sorted(set(errors))


def pseudo_formal_validation_issue_summary(
    validation_errors: Sequence[Any],
) -> dict[str, Any]:
    """Classify PF/BV validation failures into compact repair issue kinds."""

    errors = [str(error) for error in validation_errors if str(error).strip()]
    counts: Counter[str] = Counter()
    seen_issue_occurrences: set[tuple[str, str]] = set()
    for error in errors:
        lowered = error.lower()
        matched = False
        for issue_kind, markers in PSEUDO_FORMAL_VALIDATION_ISSUE_MARKERS:
            if any(marker in lowered for marker in markers):
                occurrence_key = _pseudo_formal_validation_issue_occurrence_key(
                    lowered,
                    issue_kind,
                )
                if occurrence_key not in seen_issue_occurrences:
                    seen_issue_occurrences.add(occurrence_key)
                    counts[issue_kind] += 1
                matched = True
        if not matched:
            counts["other"] += 1
    issue_counts = dict(sorted(counts.items()))
    result: dict[str, Any] = {
        "artifact_kind": "PseudoFormalValidationIssueSummary",
        "n_validation_errors": len(errors),
        "issue_kinds": sorted(issue_counts),
        "issue_counts": issue_counts,
        "blocking_issue_kinds": sorted(
            issue for issue in issue_counts if issue != "other"
        ),
        "validation_errors_excerpt": errors[:6],
        "proof_evidence_status": PSEUDO_FORMALIZATION_NOT_PROOF_EVIDENCE,
        "proof_evidence_boundary": PSEUDO_FORMALIZATION_PROOF_BOUNDARY,
    }
    for issue_kind, count in issue_counts.items():
        result[f"n_{issue_kind}"] = count
    return result


def pseudo_formal_validation_issue_repair_actions(
    validation_issue_summary: Mapping[str, Any],
) -> list[dict[str, str]]:
    issue_kinds = [
        str(value)
        for value in validation_issue_summary.get("blocking_issue_kinds", []) or []
        if str(value).strip()
    ]
    actions: list[dict[str, str]] = []
    action_by_issue_kind = {
        "missing_required_packet": (
            "emit pseudo_formal_proof_packets with at least one concrete PF block "
            "instead of returning only formal_targets/gap_taxonomy"
        ),
        "missing_blocks": (
            "populate blocks with a bounded local PF module containing premises, "
            "conclusion, proof_text, source_anchors, dependency metadata, and BV status"
        ),
        "missing_conclusion": (
            "add a non-empty top-level conclusion field to every PF block; do not "
            "hide the local claim inside proof_text or next_actions"
        ),
        "missing_source_anchors": (
            "add source_anchors entries with non-empty id or excerpt for every "
            "nontrivial PF block, copied from theory trace, proof body, theorem card, or paper source"
        ),
        "unsupported_block_type": (
            "replace unsupported block_type labels with theorem, proposition, lemma, "
            "claim, fact, definition, calculation, or case"
        ),
        "unsupported_faithfulness_status": (
            "use lowercase faithfulness_status values only: faithful, needs_review, "
            "unfaithful, or unchecked"
        ),
        "unsupported_lean_feasibility": (
            "use lean_feasibility values from the PF/BV contract such as "
            "needs_semantic_definition, needs_rag, lean_now, needs_library, pseudo_only, or unknown"
        ),
        "unsupported_block_verdict": (
            "use block_verification.verdict values not_run, unknown, failed, or "
            "accepted; keep needs_review as faithfulness_status only"
        ),
        "accepted_without_rollout_count": (
            "if verdict=accepted, set block_verification.rollout_count to an "
            "integer >= 1; otherwise use not_run, unknown, or failed"
        ),
        "forbidden_kernel_claim": (
            "set kernel_verified=false, source_theorem_kernel_verified=false, and "
            "preserve PF/BV as non-proof routing evidence"
        ),
        "dependency_or_scope_order": (
            "order PF blocks so dependency_ids and scope_parent_id reference only "
            "earlier blocks unless direct-child dependency scope explicitly applies"
        ),
        "no_lane_routable_work_order_rows": (
            "make at least one faithful block lane-routable by setting "
            "lean_feasibility=needs_semantic_definition with semantic_primitive_requirements, "
            "lean_feasibility=needs_rag, or non-empty semantic_primitive_requirements for source_to_bridge"
        ),
        "missing_required_target_lane": (
            "route at least one PF block to the required target lane using "
            "field-inferred lane values, not only prose or generic needs_review rows"
        ),
    }
    for issue_kind in issue_kinds:
        action = action_by_issue_kind.get(issue_kind)
        if not action:
            continue
        actions.append(
            {
                "issue_kind": issue_kind,
                "required_repair_action": action,
            }
        )
    if issue_kinds and not actions:
        actions.append(
            {
                "issue_kind": "other",
                "required_repair_action": (
                    "repair the PF/BV packet against pseudo_formalization_contract "
                    "and rerun local packet validation before emitting downstream work"
                ),
            }
        )
    return actions


def _pseudo_formal_validation_issue_occurrence_key(
    lowered_error: str,
    issue_kind: str,
) -> tuple[str, str]:
    packet_block_match = re.search(
        r"(?:pseudo_formal_proof_packets\[(?P<packet>\d+)\].*?)?"
        r"blocks\[(?P<block>\d+)\]",
        lowered_error,
    )
    if packet_block_match:
        packet_index = packet_block_match.group("packet") or "*"
        return (
            issue_kind,
            "pseudo_formal_proof_packets[{}].blocks[{}]".format(
                packet_index,
                packet_block_match.group("block"),
            ),
        )
    packet_match = re.search(
        r"pseudo_formal_proof_packets\[(?P<packet>\d+)\]",
        lowered_error,
    )
    if packet_match:
        return (
            issue_kind,
            "pseudo_formal_proof_packets[{}]".format(packet_match.group("packet")),
        )
    return (issue_kind, lowered_error)


def _pseudo_formal_dependency_cycle_nodes(
    dependency_ids_by_block_id: Mapping[str, Sequence[str]],
) -> list[str]:
    visiting: set[str] = set()
    visited: set[str] = set()
    cycle_nodes: set[str] = set()

    def visit(node: str, path: list[str]) -> None:
        if node in visiting:
            if node in path:
                cycle_nodes.update(path[path.index(node) :])
            else:
                cycle_nodes.add(node)
            return
        if node in visited:
            return
        visiting.add(node)
        path.append(node)
        for dep_id in dependency_ids_by_block_id.get(node, []):
            if dep_id in dependency_ids_by_block_id:
                visit(dep_id, path)
        path.pop()
        visiting.remove(node)
        visited.add(node)

    for block_id in dependency_ids_by_block_id:
        visit(block_id, [])
    return sorted(cycle_nodes)


def pseudo_formal_block_work_order_rows(packet: Mapping[str, Any]) -> list[dict[str, Any]]:
    normalized = normalize_pseudo_formal_packet(packet)
    rows: list[dict[str, Any]] = []
    for block in _as_mapping_rows(normalized.get("blocks")):
        rows.extend(_work_order_rows_for_block(normalized, block))
    return rows


def pseudo_formal_routable_work_order_rows(
    rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    return [
        dict(row)
        for row in rows
        if str(row.get("row_kind", "") or "")
        not in PSEUDO_FORMAL_NON_ROUTABLE_WORK_ORDER_ROW_KINDS
    ]


def pseudo_formal_work_order_row_has_source_anchor(row: Mapping[str, Any]) -> bool:
    for anchor in row.get("source_anchors", []) or []:
        if not isinstance(anchor, Mapping):
            continue
        if str(anchor.get("id", "") or "").strip() or str(
            anchor.get("excerpt", "") or ""
        ).strip():
            return True
    return False


def pseudo_formal_work_order_row_has_semantic_requirements(
    row: Mapping[str, Any],
) -> bool:
    return any(
        str(value or "").strip()
        for value in row.get("semantic_primitive_requirements", []) or []
    )


def pseudo_formal_work_order_row_has_required_lineage(
    row: Mapping[str, Any],
) -> bool:
    required_fields = (
        "pseudo_formal_method_contract_id",
        "pseudo_formal_pipeline_stage",
        "source_packet_id",
        "source_block_id",
        "target_lane",
        "row_kind",
    )
    return all(str(row.get(field, "") or "").strip() for field in required_fields)


def pseudo_formal_block_structural_quality(block: Mapping[str, Any]) -> dict[str, Any]:
    """Measure whether a block is small enough for Good-PF style BV calls."""
    premises = _string_list(block.get("premises"))
    dependency_ids = _string_list(block.get("dependency_ids"))
    inherited_scope = _string_list(block.get("inherited_scope"))
    source_anchors = _as_mapping_rows(block.get("source_anchors"))
    conclusion = str(block.get("conclusion", "") or "")
    proof_text = str(block.get("proof_text", "") or "")
    premise_chars = sum(len(item) for item in premises)
    inherited_scope_chars = sum(len(item) for item in inherited_scope)
    source_anchor_chars = sum(
        len(str(anchor.get("excerpt", "") or ""))
        + len(str(anchor.get("id", "") or ""))
        for anchor in source_anchors
    )
    local_context_chars = (
        premise_chars
        + len(conclusion)
        + len(proof_text)
        + inherited_scope_chars
        + source_anchor_chars
    )
    metrics = {
        "n_premises": len(premises),
        "n_dependency_ids": len(dependency_ids),
        "n_inherited_scope_items": len(inherited_scope),
        "n_source_anchors": len(source_anchors),
        "premise_chars": premise_chars,
        "conclusion_chars": len(conclusion),
        "proof_text_chars": len(proof_text),
        "inherited_scope_chars": inherited_scope_chars,
        "source_anchor_chars": source_anchor_chars,
        "local_context_chars": local_context_chars,
    }
    issues: list[str] = []
    if len(premises) > PSEUDO_FORMAL_MAX_BLOCK_PREMISES:
        issues.append(
            "too_many_premises:"
            f"{len(premises)}>{PSEUDO_FORMAL_MAX_BLOCK_PREMISES}"
        )
    if len(dependency_ids) > PSEUDO_FORMAL_MAX_BLOCK_DEPENDENCIES:
        issues.append(
            "too_many_dependency_ids:"
            f"{len(dependency_ids)}>{PSEUDO_FORMAL_MAX_BLOCK_DEPENDENCIES}"
        )
    if len(inherited_scope) > PSEUDO_FORMAL_MAX_BLOCK_INHERITED_SCOPE_ITEMS:
        issues.append(
            "too_many_inherited_scope_items:"
            f"{len(inherited_scope)}>{PSEUDO_FORMAL_MAX_BLOCK_INHERITED_SCOPE_ITEMS}"
        )
    if len(source_anchors) > PSEUDO_FORMAL_MAX_BLOCK_SOURCE_ANCHORS:
        issues.append(
            "too_many_source_anchors:"
            f"{len(source_anchors)}>{PSEUDO_FORMAL_MAX_BLOCK_SOURCE_ANCHORS}"
        )
    if len(conclusion) > PSEUDO_FORMAL_MAX_BLOCK_CONCLUSION_CHARS:
        issues.append(
            "conclusion_too_long:"
            f"{len(conclusion)}>{PSEUDO_FORMAL_MAX_BLOCK_CONCLUSION_CHARS}"
        )
    if len(proof_text) > PSEUDO_FORMAL_MAX_BLOCK_PROOF_TEXT_CHARS:
        issues.append(
            "proof_text_too_long:"
            f"{len(proof_text)}>{PSEUDO_FORMAL_MAX_BLOCK_PROOF_TEXT_CHARS}"
        )
    if local_context_chars > PSEUDO_FORMAL_MAX_BLOCK_LOCAL_CONTEXT_CHARS:
        issues.append(
            "local_context_too_long:"
            f"{local_context_chars}>{PSEUDO_FORMAL_MAX_BLOCK_LOCAL_CONTEXT_CHARS}"
        )
    return {
        "all_ok": not issues,
        "issues": issues,
        "metrics": metrics,
        "maxima": {
            "max_premises": PSEUDO_FORMAL_MAX_BLOCK_PREMISES,
            "max_dependency_ids": PSEUDO_FORMAL_MAX_BLOCK_DEPENDENCIES,
            "max_inherited_scope_items": (
                PSEUDO_FORMAL_MAX_BLOCK_INHERITED_SCOPE_ITEMS
            ),
            "max_source_anchors": PSEUDO_FORMAL_MAX_BLOCK_SOURCE_ANCHORS,
            "max_conclusion_chars": PSEUDO_FORMAL_MAX_BLOCK_CONCLUSION_CHARS,
            "max_proof_text_chars": PSEUDO_FORMAL_MAX_BLOCK_PROOF_TEXT_CHARS,
            "max_local_context_chars": PSEUDO_FORMAL_MAX_BLOCK_LOCAL_CONTEXT_CHARS,
        },
    }


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
            "block_structure_contract": {"type": "object"},
            "bv_calibration": {"type": "object"},
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
            "block_depth",
            "conclusion",
            "proof_text",
            "dependency_ids",
            "scope_parent_id",
            "dependency_scope",
            "source_anchors",
            "lean_feasibility",
            "faithfulness_status",
            "faithfulness_repair",
            "block_verification",
        ],
        "properties": {
            "block_id": {"type": "string", "minLength": 1},
            "block_type": {"type": "string", "enum": list(VALID_BLOCK_TYPES)},
            "block_depth": {
                "type": "integer",
                "minimum": 1,
                "maximum": PSEUDO_FORMAL_MAX_PROOF_TREE_DEPTH,
            },
            "premises": {"type": "array"},
            "conclusion": {"type": "string", "minLength": 1},
            "proof_text": {"type": "string"},
            "dependency_ids": {"type": "array", "items": {"type": "string"}},
            "scope_parent_id": {"type": "string"},
            "inherited_scope": {"type": "array", "items": {"type": "string"}},
            "structural_quality": {"type": "object"},
            "dependency_scope": {
                "type": "string",
                "enum": list(VALID_DEPENDENCY_SCOPES),
            },
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
            "faithfulness_repair": {
                "type": "object",
                "required": ["status", "attempts", "flagged_discrepancies"],
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": list(VALID_FAITHFULNESS_REPAIR_STATUSES),
                    },
                    "attempts": {"type": "integer", "minimum": 0},
                    "flagged_discrepancies": {"type": "array"},
                },
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
                    "verifier_provenance": {"type": "string"},
                    "independent_verifier": {"type": "boolean"},
                    "strictness_threshold": {
                        "type": "string",
                        "enum": list(VALID_CALIBRATION_STRICTNESS),
                    },
                    "aggregation_rule": {"type": "string"},
                    "rollout_count": {"type": "integer", "minimum": 0},
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
            "block_depth",
            "dependency_scope",
            "scope_parent_id",
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
            "block_depth": {
                "type": "integer",
                "minimum": 1,
                "maximum": PSEUDO_FORMAL_MAX_PROOF_TREE_DEPTH,
            },
            "dependency_scope": {
                "type": "string",
                "enum": list(VALID_DEPENDENCY_SCOPES),
            },
            "dependency_statement_context": {"type": "array"},
            "scope_parent_id": {"type": "string"},
            "inherited_scope": {"type": "array", "items": {"type": "string"}},
            "source_block_premises": {"type": "array", "items": {"type": "string"}},
            "source_block_proof_text": {"type": "string"},
            "structural_quality": {"type": "object"},
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
    normalized["block_type"] = _normalize_block_type(
        _first_nonempty_value(normalized, "block_type", "type", default="claim")
    )
    normalized["premises"] = _string_list(
        _first_nonempty_value(
            normalized,
            "premises",
            "assumptions",
            "hypotheses",
            "given",
        )
    )
    normalized["conclusion"] = str(
        _first_nonempty_value(
            normalized,
            "conclusion",
            "conclusion_text",
            "statement",
            "statement_text",
            "block_statement",
            "local_statement",
            "claim",
            "claim_text",
            "local_claim",
            "assertion",
            "assertion_text",
            "goal",
            default="",
        )
        or ""
    ).strip()
    normalized["proof_text"] = str(
        _first_nonempty_value(
            normalized,
            "proof_text",
            "proof",
            "proof_step",
            "argument",
            "justification",
            "rationale",
            "reasoning",
            "derivation",
            "explanation",
            default="",
        )
        or ""
    )
    normalized["dependency_ids"] = _string_list(
        _first_nonempty_value(
            normalized,
            "dependency_ids",
            "dependencies",
            "depends_on",
        )
    )
    normalized["scope_parent_id"] = str(
        normalized.get(
            "scope_parent_id",
            normalized.get("scope_parent", normalized.get("parent_block_id", "")),
        )
        or ""
    ).strip()
    normalized["inherited_scope"] = _string_list(
        normalized.get("inherited_scope", normalized.get("scope_context"))
    )
    normalized["block_depth"] = _normalize_block_depth(
        normalized.get("block_depth")
    )
    normalized["dependency_scope"] = _normalize_dependency_scope(
        normalized.get("dependency_scope")
    )
    normalized["source_anchors"] = _normalize_source_anchors(
        _first_nonempty_value(
            normalized,
            "source_anchors",
            "source_anchor",
            "anchors",
            "source_refs",
            "source_references",
            "source_anchor_refs",
            "source_citations",
            "citations",
            "evidence_anchors",
            "evidence_refs",
            "source_lines",
            "source_evidence",
        )
    )
    normalized["semantic_primitive_requirements"] = _string_list(
        _first_nonempty_value(
            normalized,
            "semantic_primitive_requirements",
            "semantic_primitives",
            "required_semantic_primitives",
        )
    )
    normalized["lean_feasibility"] = str(
        normalized.get("lean_feasibility", "unknown") or "unknown"
    ).strip()
    normalized["faithfulness_status"] = _normalize_faithfulness_status(
        normalized.get("faithfulness_status", "unchecked")
    )
    normalized["faithfulness_repair"] = _normalize_faithfulness_repair(
        normalized.get("faithfulness_repair"),
        faithfulness_status=normalized["faithfulness_status"],
    )
    verification = normalized.get("block_verification", {})
    if not isinstance(verification, Mapping):
        verification = {"verdict": str(verification or "unknown")}
    original_verification_verdict = str(
        verification.get("verdict", "not_run") or "not_run"
    ).strip()
    verification_rollout_count = max(
        0,
        _int_or_none(verification.get("rollout_count")) or 0,
    )
    verification_verdict = _normalize_block_verdict(original_verification_verdict)
    block_verification_corrections: list[str] = []
    if verification_verdict != original_verification_verdict:
        block_verification_corrections.append(
            "verdict_normalized:"
            f"{original_verification_verdict or 'empty'}->{verification_verdict}"
        )
    if verification_verdict == "accepted" and verification_rollout_count < 1:
        verification_verdict = "unknown"
        block_verification_corrections.append(
            "accepted_without_rollout_count_downgraded_to_unknown"
        )
    verifier_provenance = _normalize_block_verifier_provenance(
        verification.get(
            "verifier_provenance",
            verification.get("verifier_source"),
        ),
        verdict=verification_verdict,
    )
    normalized["block_verification"] = {
        "verdict": verification_verdict,
        "reason": str(verification.get("reason", "") or "").strip(),
        "verifier_provenance": verifier_provenance,
        "independent_verifier": _block_verification_independent_from_values(
            verification.get("independent_verifier"),
            verifier_provenance=verifier_provenance,
        ),
        "strictness_threshold": _normalize_calibration_strictness(
            verification.get("strictness_threshold")
        ),
        "aggregation_rule": str(
            verification.get(
                "aggregation_rule",
                PSEUDO_FORMAL_DEFAULT_AGGREGATION_RULE,
            )
            or PSEUDO_FORMAL_DEFAULT_AGGREGATION_RULE
        ),
        "rollout_count": verification_rollout_count,
    }
    if block_verification_corrections:
        normalized["block_verification"]["normalizer_corrections"] = (
            block_verification_corrections
        )
    normalized["structural_quality"] = pseudo_formal_block_structural_quality(
        normalized
    )
    normalized["kernel_verified"] = False
    return normalized


def _first_nonempty_value(
    row: Mapping[str, Any],
    *keys: str,
    default: Any = None,
) -> Any:
    for key in keys:
        value = row.get(key)
        if value not in (None, "", [], {}):
            return value
    return default


def _normalize_block_type(value: Any) -> str:
    text = str(value or "claim").strip().lower().replace("-", "_").replace(" ", "_")
    return BLOCK_TYPE_ALIASES.get(text, text or "claim")


def _work_order_rows_for_block(
    packet: Mapping[str, Any],
    block: Mapping[str, Any],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    feasibility = str(block.get("lean_feasibility", "unknown") or "unknown")
    semantic_requirements = _string_list(block.get("semantic_primitive_requirements"))
    verdict = _block_verdict(block)
    faithfulness = str(block.get("faithfulness_status", "unchecked") or "unchecked")
    faithfulness_ready = faithfulness == "faithful"
    verification = (
        block.get("block_verification", {})
        if isinstance(block.get("block_verification", {}), Mapping)
        else {}
    )
    rollout_count = max(0, _int_or_none(verification.get("rollout_count")) or 0)
    independent_bv_ready = faithfulness_ready and _block_verification_is_independent(
        block
    )
    structural_quality = pseudo_formal_block_structural_quality(block)
    if not bool(structural_quality.get("all_ok", False)):
        rows.append(
            _work_order_row(
                packet,
                block,
                row_kind=PSEUDO_FORMAL_STRUCTURAL_DECOMPOSITION_REQUEST_ROW_KIND,
                target_lane=PSEUDO_FORMAL_TARGET_LANE_FORMAL_GAP,
                reason=(
                    "pseudo-formal block violates Good-PF bounded-context "
                    "structure; split or rewrite it before block verification, "
                    "Lean/RAG, source-to-bridge, or semantic-definition routing"
                ),
                extra={
                    "structural_quality": structural_quality,
                    "structural_quality_ok": False,
                    "structural_quality_issues": list(
                        structural_quality.get("issues", []) or []
                    ),
                    "requested_owner_subsystem": "Formalizer/ProofEngineer",
                },
            )
        )
        return rows
    if not faithfulness_ready:
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
        if independent_bv_ready:
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
        elif faithfulness_ready:
            rows.append(
                _work_order_row(
                    packet,
                    block,
                    row_kind=(
                        "pseudo_formal_block_verification_failure"
                        "_blocked_by_independent_bv"
                    ),
                    target_lane=PSEUDO_FORMAL_TARGET_LANE_FORMAL_GAP,
                    reason=(
                        "block-verification failure is diagnostic until an "
                        "independent PF/BV verifier records the failure"
                    ),
                    extra={
                        "blocked_row_kind": (
                            "pseudo_formal_block_verification_failure"
                        ),
                        "blocked_by": (
                            "independent_block_verification_not_established"
                        ),
                    },
                )
            )
        else:
            rows.append(
                _faithfulness_blocked_work_order_row(
                    packet,
                    block,
                    blocked_row_kind="pseudo_formal_block_verification_failure",
                    row_kind=(
                        "pseudo_formal_block_verification_failure"
                        "_blocked_by_faithfulness"
                    ),
                    reason=(
                        "block verification failure is not routable as a "
                        "source-proof gap until the pseudo-formal rewrite is "
                        f"faithful; faithfulness_status={faithfulness}"
                    ),
                )
            )
    elif verdict in {"not_run", "unknown"}:
        rows.append(
            _work_order_row(
                packet,
                block,
                row_kind="pseudo_formal_block_verification_pending",
                target_lane=PSEUDO_FORMAL_TARGET_LANE_FORMAL_GAP,
                reason=f"block_verification.verdict={verdict}",
            )
        )
    if faithfulness_ready and not _block_verification_is_independent(block):
        rows.append(
            _work_order_row(
                packet,
                block,
                row_kind=PSEUDO_FORMAL_BLOCK_VERIFICATION_REQUEST_ROW_KIND,
                target_lane=PSEUDO_FORMAL_TARGET_LANE_FORMAL_GAP,
                reason=(
                    "run an independent PF/BV block-verifier call for this "
                    "faithful pseudo-formal block before treating its block "
                    "verdict as verifier feedback"
                ),
                extra={
                    "requested_owner_subsystem": "BlockVerifier/CalibrationReferee",
                    "independent_block_verification_required": True,
                },
            )
        )
    if feasibility == "lean_now":
        if (
            faithfulness == "faithful"
            and verdict == "accepted"
            and rollout_count >= 1
            and independent_bv_ready
        ):
            rows.append(
                _work_order_row(
                    packet,
                    block,
                    row_kind="pseudo_formal_lean_candidate_seed",
                    target_lane=PSEUDO_FORMAL_TARGET_LANE_FORMAL_TARGETS,
                    reason="faithful BV-accepted block is triaged as Lean-feasible",
                )
            )
        else:
            rows.append(
                _work_order_row(
                    packet,
                    block,
                    row_kind="pseudo_formal_lean_candidate_seed_blocked",
                    target_lane=PSEUDO_FORMAL_TARGET_LANE_FORMAL_GAP,
                    reason=(
                        "Lean candidate seed blocked until faithfulness_status="
                        "faithful and block_verification.verdict=accepted with "
                        "rollout_count>=1 from an independent BV verifier"
                    ),
                    extra=(
                        {
                            "blocked_row_kind": "pseudo_formal_lean_candidate_seed",
                            "blocked_by": (
                                "independent_block_verification_not_established"
                            ),
                        }
                        if (
                            faithfulness_ready
                            and verdict == "accepted"
                            and rollout_count >= 1
                            and not independent_bv_ready
                        )
                        else None
                    ),
            )
        )
    elif feasibility == "needs_rag":
        if faithfulness_ready:
            rows.append(
                _work_order_row(
                    packet,
                    block,
                    row_kind="pseudo_formal_formal_library_grounding_query",
                    target_lane=PSEUDO_FORMAL_TARGET_LANE_LEAN_RAG,
                    reason="block needs target-prover library grounding",
                )
            )
        else:
            rows.append(
                _faithfulness_blocked_work_order_row(
                    packet,
                    block,
                    blocked_row_kind="pseudo_formal_formal_library_grounding_query",
                    blocked_target_lane=PSEUDO_FORMAL_TARGET_LANE_LEAN_RAG,
                    row_kind=(
                        "pseudo_formal_formal_library_grounding_query"
                        "_blocked_by_faithfulness"
                    ),
                    reason="formal library grounding waits for faithful PF rewrite",
                )
            )
    elif feasibility == "needs_library":
        if faithfulness_ready:
            rows.append(
                _work_order_row(
                    packet,
                    block,
                    row_kind="pseudo_formal_library_gap",
                    target_lane=PSEUDO_FORMAL_TARGET_LANE_FORMAL_GAP,
                    reason="block requires unavailable formal library support",
                )
            )
        else:
            rows.append(
                _faithfulness_blocked_work_order_row(
                    packet,
                    block,
                    blocked_row_kind="pseudo_formal_library_gap",
                    row_kind="pseudo_formal_library_gap_blocked_by_faithfulness",
                    reason="formal library gap waits for faithful PF rewrite",
                )
            )
    elif feasibility == "needs_semantic_definition":
        if faithfulness_ready and semantic_requirements:
            rows.append(
                _work_order_row(
                    packet,
                    block,
                    row_kind="pseudo_formal_exact_semantic_definition_request",
                    target_lane=PSEUDO_FORMAL_TARGET_LANE_EXACT_SEMANTIC_DEFINITION,
                    reason=(
                        "block requires exact semantic definitions before Lean replay"
                    ),
                )
            )
        elif faithfulness_ready:
            rows.append(
                _work_order_row(
                    packet,
                    block,
                    row_kind=(
                        "pseudo_formal_exact_semantic_definition_request"
                        "_blocked_by_missing_semantic_requirements"
                    ),
                    target_lane=PSEUDO_FORMAL_TARGET_LANE_FORMAL_GAP,
                    reason=(
                        "exact semantic-definition routing requires the block to "
                        "name the primitive/source object to define in "
                        "semantic_primitive_requirements"
                    ),
                    extra={
                        "blocked_row_kind": (
                            "pseudo_formal_exact_semantic_definition_request"
                        ),
                        "blocked_target_lane": (
                            PSEUDO_FORMAL_TARGET_LANE_EXACT_SEMANTIC_DEFINITION
                        ),
                        "blocked_by": "semantic_primitive_requirements_missing",
                        "requested_owner_subsystem": "Formalizer/ProofEngineer",
                    },
                )
            )
        else:
            rows.append(
                _faithfulness_blocked_work_order_row(
                    packet,
                    block,
                    blocked_row_kind="pseudo_formal_exact_semantic_definition_request",
                    blocked_target_lane=(
                        PSEUDO_FORMAL_TARGET_LANE_EXACT_SEMANTIC_DEFINITION
                    ),
                    row_kind=(
                        "pseudo_formal_exact_semantic_definition_request"
                        "_blocked_by_faithfulness"
                    ),
                    reason=(
                        "exact semantic-definition authoring waits for faithful "
                        "PF rewrite"
                    ),
                )
            )
    elif feasibility == "pseudo_only":
        if faithfulness_ready:
            rows.append(
                _work_order_row(
                    packet,
                    block,
                    row_kind="pseudo_formal_nonlean_residual_gap",
                    target_lane=PSEUDO_FORMAL_TARGET_LANE_FORMAL_GAP,
                    reason="block is not currently Lean-realizable",
                )
            )
        else:
            rows.append(
                _faithfulness_blocked_work_order_row(
                    packet,
                    block,
                    blocked_row_kind="pseudo_formal_nonlean_residual_gap",
                    row_kind=(
                        "pseudo_formal_nonlean_residual_gap"
                        "_blocked_by_faithfulness"
                    ),
                    reason="non-Lean residual classification waits for faithful PF rewrite",
                )
            )
    for primitive in semantic_requirements:
        if faithfulness_ready:
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
        else:
            rows.append(
                _faithfulness_blocked_work_order_row(
                    packet,
                    block,
                    blocked_row_kind="pseudo_formal_semantic_primitive_request",
                    blocked_target_lane=PSEUDO_FORMAL_TARGET_LANE_SOURCE_TO_BRIDGE,
                    row_kind=(
                        "pseudo_formal_semantic_primitive_request"
                        "_blocked_by_faithfulness"
                    ),
                    reason=(
                        f"semantic primitive request `{primitive}` waits for "
                        "faithful PF rewrite"
                    ),
                    extra={"semantic_primitive": primitive},
                )
            )
    return rows


def _faithfulness_blocked_work_order_row(
    packet: Mapping[str, Any],
    block: Mapping[str, Any],
    *,
    blocked_row_kind: str,
    row_kind: str,
    reason: str,
    blocked_target_lane: str = PSEUDO_FORMAL_TARGET_LANE_FORMAL_GAP,
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "blocked_row_kind": blocked_row_kind,
        "blocked_target_lane": blocked_target_lane,
        "blocked_by": "faithfulness_not_established",
    }
    if extra:
        payload.update(dict(extra))
    return _work_order_row(
        packet,
        block,
        row_kind=row_kind,
        target_lane=PSEUDO_FORMAL_TARGET_LANE_FORMAL_GAP,
        reason=reason,
        extra=payload,
    )


def _work_order_row(
    packet: Mapping[str, Any],
    block: Mapping[str, Any],
    *,
    row_kind: str,
    target_lane: str,
    reason: str,
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    structural_quality = pseudo_formal_block_structural_quality(block)
    base = {
        "source_packet_id": str(packet.get("packet_id", "") or ""),
        "source_theorem_id": str(packet.get("theorem_id", "") or ""),
        "source_artifact_id": str(packet.get("source_artifact_id", "") or ""),
        "source_block_id": str(block.get("block_id", "") or ""),
        "source_block_type": str(block.get("block_type", "") or ""),
        "source_block_conclusion": str(block.get("conclusion", "") or ""),
        "block_depth": int(
            _int_or_none(block.get("block_depth"))
            or PSEUDO_FORMAL_DEFAULT_BLOCK_DEPTH
        ),
        "dependency_scope": str(
            block.get("dependency_scope", PSEUDO_FORMAL_DEFAULT_DEPENDENCY_SCOPE)
            or PSEUDO_FORMAL_DEFAULT_DEPENDENCY_SCOPE
        ),
        "dependency_ids": _string_list(block.get("dependency_ids")),
        "dependency_statement_context": _pseudo_formal_dependency_statement_context(
            packet,
            block,
        ),
        "scope_parent_id": str(block.get("scope_parent_id", "") or ""),
        "inherited_scope": _string_list(block.get("inherited_scope")),
        "source_block_premises": _string_list(block.get("premises")),
        "source_block_proof_text": str(block.get("proof_text", "") or ""),
        "semantic_primitive_requirements": _string_list(
            block.get("semantic_primitive_requirements")
        ),
        "structural_quality": structural_quality,
        "structural_quality_ok": bool(structural_quality.get("all_ok", False)),
        "structural_quality_issues": list(
            structural_quality.get("issues", []) or []
        ),
        "source_anchors": list(_as_mapping_rows(block.get("source_anchors"))),
        "faithfulness_status": str(
            block.get("faithfulness_status", "unchecked") or "unchecked"
        ),
        "faithfulness_repair_status": str(
            (
                block.get("faithfulness_repair", {})
                if isinstance(block.get("faithfulness_repair", {}), Mapping)
                else {}
            ).get("status", "not_required")
            or "not_required"
        ),
        "lean_feasibility": str(block.get("lean_feasibility", "unknown") or "unknown"),
        "block_verification_verifier_provenance": _block_verification_provenance(
            block
        ),
        "block_verification_independent": _block_verification_is_independent(block),
        "block_verification": dict(
            block.get("block_verification", {})
            if isinstance(block.get("block_verification", {}), Mapping)
            else {}
        ),
        "bv_calibration": _normalize_bv_calibration(packet.get("bv_calibration")),
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


def _pseudo_formal_dependency_statement_context(
    packet: Mapping[str, Any],
    block: Mapping[str, Any],
) -> list[dict[str, str]]:
    blocks_by_id = {
        str(candidate.get("block_id", "") or ""): candidate
        for candidate in _as_mapping_rows(packet.get("blocks"))
        if str(candidate.get("block_id", "") or "")
    }
    context: list[dict[str, str]] = []
    for dep_id in _string_list(block.get("dependency_ids")):
        dep = blocks_by_id.get(dep_id)
        if not isinstance(dep, Mapping):
            context.append({"block_id": dep_id, "status": "missing"})
            continue
        context.append(
            {
                "block_id": dep_id,
                "block_type": str(dep.get("block_type", "") or ""),
                "conclusion": str(dep.get("conclusion", "") or ""),
                "dependency_scope": str(
                    dep.get(
                        "dependency_scope",
                        PSEUDO_FORMAL_DEFAULT_DEPENDENCY_SCOPE,
                    )
                    or PSEUDO_FORMAL_DEFAULT_DEPENDENCY_SCOPE
                ),
            }
        )
    return context


def _default_block_structure_contract(
    value: Any | None = None,
) -> dict[str, Any]:
    raw = dict(value) if isinstance(value, Mapping) else {}
    return {
        "max_proof_tree_depth": int(
            _int_or_none(raw.get("max_proof_tree_depth"))
            or PSEUDO_FORMAL_MAX_PROOF_TREE_DEPTH
        ),
        "max_block_premises": int(
            _int_or_none(raw.get("max_block_premises"))
            or PSEUDO_FORMAL_MAX_BLOCK_PREMISES
        ),
        "max_block_dependencies": int(
            _int_or_none(raw.get("max_block_dependencies"))
            or PSEUDO_FORMAL_MAX_BLOCK_DEPENDENCIES
        ),
        "max_block_inherited_scope_items": int(
            _int_or_none(raw.get("max_block_inherited_scope_items"))
            or PSEUDO_FORMAL_MAX_BLOCK_INHERITED_SCOPE_ITEMS
        ),
        "max_block_source_anchors": int(
            _int_or_none(raw.get("max_block_source_anchors"))
            or PSEUDO_FORMAL_MAX_BLOCK_SOURCE_ANCHORS
        ),
        "max_block_conclusion_chars": int(
            _int_or_none(raw.get("max_block_conclusion_chars"))
            or PSEUDO_FORMAL_MAX_BLOCK_CONCLUSION_CHARS
        ),
        "max_block_proof_text_chars": int(
            _int_or_none(raw.get("max_block_proof_text_chars"))
            or PSEUDO_FORMAL_MAX_BLOCK_PROOF_TEXT_CHARS
        ),
        "max_block_local_context_chars": int(
            _int_or_none(raw.get("max_block_local_context_chars"))
            or PSEUDO_FORMAL_MAX_BLOCK_LOCAL_CONTEXT_CHARS
        ),
        "dependency_scope_rule": str(
            raw.get(
                "dependency_scope_rule",
                PSEUDO_FORMAL_DEFAULT_DEPENDENCY_SCOPE,
            )
            or PSEUDO_FORMAL_DEFAULT_DEPENDENCY_SCOPE
        ),
        "rules": _string_list(raw.get("rules")) or list(PSEUDO_FORMAL_BLOCK_STRUCTURE_RULES),
    }


def _default_bv_calibration() -> dict[str, Any]:
    return {
        "strictness_threshold": PSEUDO_FORMAL_DEFAULT_CALIBRATION_STRICTNESS,
        "aggregation_rule": PSEUDO_FORMAL_DEFAULT_AGGREGATION_RULE,
        "pessimistic_acceptance": True,
        "proof_evidence_status": PSEUDO_FORMALIZATION_NOT_PROOF_EVIDENCE,
    }


def _normalize_bv_calibration(value: Any) -> dict[str, Any]:
    raw = dict(value) if isinstance(value, Mapping) else {}
    normalized = _default_bv_calibration()
    normalized.update(
        {
            "strictness_threshold": _normalize_calibration_strictness(
                raw.get("strictness_threshold")
            ),
            "aggregation_rule": str(
                raw.get("aggregation_rule", PSEUDO_FORMAL_DEFAULT_AGGREGATION_RULE)
                or PSEUDO_FORMAL_DEFAULT_AGGREGATION_RULE
            ),
            "pessimistic_acceptance": bool(
                raw.get("pessimistic_acceptance", True)
            ),
            "rollout_count": max(0, _int_or_none(raw.get("rollout_count")) or 0),
        }
    )
    return normalized


def _normalize_block_depth(value: Any) -> int:
    parsed = _int_or_none(value)
    if parsed is None:
        return PSEUDO_FORMAL_DEFAULT_BLOCK_DEPTH
    return max(1, min(PSEUDO_FORMAL_MAX_PROOF_TREE_DEPTH, parsed))


def _normalize_dependency_scope(value: Any) -> str:
    text = str(value or PSEUDO_FORMAL_DEFAULT_DEPENDENCY_SCOPE).strip()
    if text in VALID_DEPENDENCY_SCOPES:
        return text
    return PSEUDO_FORMAL_DEFAULT_DEPENDENCY_SCOPE


def _normalize_calibration_strictness(value: Any) -> str:
    text = str(value or PSEUDO_FORMAL_DEFAULT_CALIBRATION_STRICTNESS).strip()
    if text in VALID_CALIBRATION_STRICTNESS:
        return text
    return PSEUDO_FORMAL_DEFAULT_CALIBRATION_STRICTNESS


def _normalize_block_verdict(value: Any) -> str:
    text = str(value or "not_run").strip()
    normalized = text.lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "": "not_run",
        "notrun": "not_run",
        "not_run": "not_run",
        "not_started": "not_run",
        "pending": "not_run",
        "needs_review": "unknown",
        "needs_bv": "unknown",
        "requires_review": "unknown",
        "review": "unknown",
        "unchecked": "unknown",
        "unverified": "unknown",
        "unknown": "unknown",
        "accept": "accepted",
        "accepted": "accepted",
        "pass": "accepted",
        "passed": "accepted",
        "valid": "accepted",
        "reject": "failed",
        "rejected": "failed",
        "fail": "failed",
        "failed": "failed",
        "invalid": "failed",
    }
    candidate = aliases.get(normalized, normalized)
    return candidate if candidate in VALID_BLOCK_VERDICTS else "unknown"


def _normalize_block_verifier_provenance(
    value: Any,
    *,
    verdict: str,
) -> str:
    text = str(value or "").strip()
    if text:
        return text
    if verdict in {"not_run", "unknown"}:
        return PSEUDO_FORMAL_NOT_RUN_BLOCK_VERIFIER_PROVENANCE
    return PSEUDO_FORMAL_FORMALIZER_PROPOSED_BLOCK_VERIFIER_PROVENANCE


def _block_verification_independent_from_values(
    value: Any,
    *,
    verifier_provenance: str,
) -> bool:
    if isinstance(value, bool):
        return value
    return verifier_provenance in PSEUDO_FORMAL_INDEPENDENT_BLOCK_VERIFIER_PROVENANCES


def _block_verification_provenance(block: Mapping[str, Any]) -> str:
    verification = (
        block.get("block_verification", {})
        if isinstance(block.get("block_verification", {}), Mapping)
        else {}
    )
    return _normalize_block_verifier_provenance(
        verification.get(
            "verifier_provenance",
            verification.get("verifier_source"),
        ),
        verdict=_block_verdict(block),
    )


def _block_verification_is_independent(block: Mapping[str, Any]) -> bool:
    verification = (
        block.get("block_verification", {})
        if isinstance(block.get("block_verification", {}), Mapping)
        else {}
    )
    return _block_verification_independent_from_values(
        verification.get("independent_verifier"),
        verifier_provenance=_block_verification_provenance(block),
    )


def _normalize_faithfulness_repair(
    value: Any,
    *,
    faithfulness_status: str,
) -> dict[str, Any]:
    raw = dict(value) if isinstance(value, Mapping) else {}
    status = str(raw.get("status", "") or "").strip()
    if not status:
        status = (
            "needs_repair"
            if faithfulness_status in {"unfaithful", "needs_review"}
            else "not_required"
        )
    if status not in VALID_FAITHFULNESS_REPAIR_STATUSES:
        status = "needs_repair"
    return {
        "status": status,
        "attempts": max(0, _int_or_none(raw.get("attempts")) or 0),
        "flagged_discrepancies": _string_list(raw.get("flagged_discrepancies")),
    }


def _int_or_none(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


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
    if isinstance(value, Mapping):
        value = [value]
    if isinstance(value, str):
        value = [value]
    for item in value or []:
        if isinstance(item, Mapping):
            anchor = {
                "kind": str(item.get("kind", "other") or "other").strip(),
                "id": str(
                    _first_nonempty_value(
                        item,
                        "id",
                        "source_id",
                        "anchor_id",
                        "reference_id",
                        "artifact_id",
                        "trace_id",
                        "lineage_id",
                        default="",
                    )
                    or ""
                ).strip(),
                "excerpt": str(
                    _first_nonempty_value(
                        item,
                        "excerpt",
                        "source_excerpt",
                        "quote",
                        "text",
                        default="",
                    )
                    or ""
                ).strip(),
            }
            if anchor["id"] or anchor["excerpt"]:
                anchors.append(anchor)
        elif str(item or "").strip():
            anchors.append(
                {
                    "kind": "other",
                    "id": str(item or "").strip(),
                    "excerpt": "",
                }
            )
    return anchors


def _normalize_faithfulness_status(value: Any) -> str:
    normalized = str(value or "unchecked").strip().lower().replace("-", "_")
    if normalized in VALID_FAITHFULNESS_STATUSES:
        return normalized
    if normalized in {
        "unverified",
        "not_verified",
        "not_run",
        "unknown",
        "pending",
    }:
        return "unchecked"
    if normalized in {"review", "needs-review", "needs_review_required"}:
        return "needs_review"
    return normalized


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
