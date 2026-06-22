from __future__ import annotations

import json
import shutil
from copy import deepcopy
from pathlib import Path

import pytest

from ai_statistician.cli import main
from ai_statistician.formalization_gap_planner_llm_route_planner import (
    LLM_ROUTE_PLANNER_LEGACY_CONTEXT_FIELD_ALIASES,
    LLM_ROUTE_PLANNER_LEGACY_RESPONSE_FIELD_ALIASES,
    LLM_ROUTE_PLANNER_LIBRARY_ALIGNMENT_SUMMARY_SCHEMA_ID,
    LLM_ROUTE_PLANNER_MANIFEST_SCHEMA_ID,
    LLM_ROUTE_PLANNER_MODEL_TIER_DECISION_LEDGER_SCHEMA_ID,
    LLM_ROUTE_PLANNER_REQUEST_SCHEMA_ID,
    LLM_ROUTE_PLANNER_RESPONSE_PAYLOAD_VALIDATION_MANIFEST_SCHEMA_ID,
    LLM_ROUTE_PLANNER_RESPONSE_PAYLOAD_VALIDATION_ROW_SCHEMA_ID,
    LLM_ROUTE_PLANNER_RESPONSE_PAYLOAD_SCHEMA_ID,
    LLM_ROUTE_PLANNER_RESPONSE_SCHEMA_ID,
    LLM_ROUTE_PLANNER_ROUTE_PLANNING_BRIEF_SCHEMA_ID,
    LLM_ROUTE_PLANNER_ROW_SCHEMA_ID,
    LLM_ROUTE_PLANNER_TARGET_THEOREM_CONTEXT_PACKET_SCHEMA_ID,
    PROOF_EVIDENCE_STATUS,
    PROOF_EVIDENCE_BOUNDARY,
    PROVIDER_EXECUTION_MODE_LIVE_PROVIDER_BACKEND,
    PROVIDER_EXECUTION_MODE_PROMPT_ONLY_STAGED,
    PROVIDER_EXECUTION_MODE_REVIEWED_RESPONSE_JSON,
    PROVIDER_EXECUTION_MODE_STATIC_GENERATOR_BACKEND,
    PROVIDER_EXECUTION_MODE_STATIC_RESPONSE_REPLAY,
    PROVIDER_EXECUTION_MODE_SUPPLIED_GENERATOR_BACKEND,
    ROUTE_ADOPTION_BLOCKER_PRIMITIVE_EVIDENCE_MATRIX,
    ROUTE_ADOPTION_BLOCKER_REALIZATION_COVERAGE,
    ROUTE_ADOPTION_BLOCKER_FORMAL_ATTEMPT_QUEUE,
    ROUTE_ADOPTION_BLOCKER_SOURCE_GROUNDING,
    TARGET_THEOREM_CONTEXT_PACKET_KIND,
    _adapter_targets_match,
    _available_formal_declaration_rows_for_context,
    _generator_model_for_request,
    _minimal_delta_route_option_selection_brief_errors,
    _route_adoption_readiness,
    _route_option_selection_brief,
    _target_compatible_formal_declaration_rows,
    export_formalization_gap_planner_llm_route_planner,
    llm_route_planner_library_alignment_summary_json_schema,
    llm_route_planner_manifest_json_schema,
    llm_route_planner_model_tier_decision_ledger_json_schema,
    llm_route_planner_route_planning_brief_json_schema,
    llm_route_planner_target_theorem_context_packet_json_schema,
    llm_route_planner_response_payload_schema,
    llm_route_planner_row_json_schema,
    route_adoption_blocker_taxonomy_json_schema,
    validate_formalization_gap_planner_llm_route_planner_response_payloads,
    validate_llm_route_planner_manifest,
    validate_llm_route_planner_request,
    validate_llm_route_planner_response_payload,
    validate_llm_route_planner_response_payload_validation_row,
    validate_llm_route_planner_response_payload_validation_manifest,
    validate_llm_route_planner_row,
    route_adoption_blocker_taxonomy_payload,
    validate_route_adoption_blocker_taxonomy_payload,
)
from ai_statistician.formalization_gap_planner_component_resource_registry import (
    export_formalization_gap_planner_component_resource_registry,
)
from ai_statistician.formalization_gap_planner_minimal_delta_audit import (
    audit_formalization_gap_planner_minimal_delta,
)
from ai_statistician.formalization_gap_planner_refinement_queue import (
    export_formalization_gap_planner_refinement_queue,
)
from ai_statistician.formalization_gap_planner_refinement_adapters import (
    export_formalization_gap_planner_refinement_adapter_responses,
)
from ai_statistician.formalization_gap_planner_refinement_evidence import (
    export_formalization_gap_planner_refinement_evidence,
)
from ai_statistician.formalization_gap_planner_route_revision_overlay import (
    export_formalization_gap_planner_route_revision_overlay,
)
from ai_statistician.formalization_gap_planner_route_replan_handoff import (
    export_formalization_gap_planner_route_replan_handoff,
)
from ai_statistician.formalization_gap_planner_standalone import (
    export_formalization_gap_planner_standalone_plan,
    standalone_input_json_schema,
    validate_llm_route_planner_seed_route_selection_payload,
    validate_standalone_input_payload,
)
from ai_statistician.formalization_gap_planner_source_grounding_audit import (
    audit_formalization_gap_planner_source_grounding,
)
from ai_statistician.formalization_gap_planner_target_intake import (
    normalize_formalization_gap_planner_target_intake,
)
from ai_statistician.model_backend import GeneratorResponse


def _write_input(root: Path) -> Path:
    input_json = root / "standalone_input.json"
    input_json.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "component_name": "formalization_gap_planner_standalone_input",
                "target_prover_family": "lean4",
                "library_snapshot_ref": "lean_mathlib_snapshot",
                "routes": [
                    {
                        "route_id": "rank_route",
                        "display_name": "distribution_free_rank_bound",
                        "theorem_statement": (
                            "A distribution-free rank bound follows from exchangeability."
                        ),
                        "source_refs": ["conformal_prediction_textbook"],
                        "source_snippets": [
                            {
                                "source_ref": "conformal_prediction_textbook",
                                "claim": "Exchangeability implies a uniform rank statistic.",
                                "excerpt": (
                                    "Under exchangeability, the rank of the test score "
                                    "among calibration scores is uniformly distributed "
                                    "up to the tie convention."
                                ),
                                "target_primitives": ["rank_uniformity"],
                            }
                        ],
                        "primitives": [
                            {
                                "primitive": "exchangeability",
                                "coverage_status": "exact_exists",
                                "candidate_declarations": ["Probability.exchangeable"],
                            },
                            {
                                "primitive": "rank_uniformity",
                                "coverage_status": "bridge_needed",
                                "expected_premises": ["exchangeability"],
                            },
                        ],
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return input_json


def _write_input_with_rank_bridge_candidate(root: Path) -> Path:
    input_json = _write_input(root)
    payload = json.loads(input_json.read_text(encoding="utf-8"))
    rank_primitive = payload["routes"][0]["primitives"][1]
    rank_primitive["candidate_declarations"] = ["Probability.rankUniformityBridge"]
    input_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return input_json


def test_route_option_selection_brief_uses_residual_coverage_tie_breaker() -> None:
    residual_goal = "rank_uniformity: missing finite tie-breaking side condition"
    brief = _route_option_selection_brief(
        {
            "library_alignment_summary": {
                "route_option_alignment": [
                    {
                        "route_option_id": "reuse_only",
                        "option_kind": "reuse",
                        "selected_primitives": ["exchangeability"],
                        "n_selected_primitives": 1,
                        "minimum_route_base_cost": 4,
                        "n_bridge_or_harder_primitives": 0,
                        "n_target_compatible_reuse_declarations": 1,
                    },
                    {
                        "route_option_id": "residual_bridge",
                        "option_kind": "bridge",
                        "selected_primitives": ["rank_uniformity"],
                        "n_selected_primitives": 1,
                        "minimum_route_base_cost": 4,
                        "n_bridge_or_harder_primitives": 0,
                        "n_target_compatible_reuse_declarations": 1,
                    },
                ]
            },
            "residual_goals": [residual_goal],
            "residual_goal_contexts": [
                {
                    "residual_goal": residual_goal,
                    "target_primitives": ["rank_uniformity"],
                    "source_field": "test_residual_context",
                }
            ],
        },
        route_id="rank_route",
        display_name="rank route",
        target_prover_family="lean4",
        library_snapshot_ref="lean_mathlib_snapshot",
    )

    assert brief["lower_bound_selected_route_option_id"] == "residual_bridge"
    assert brief["lower_bound_selected_residual_goal_count"] == 1
    assert brief["n_candidate_route_options_with_residual_goals"] == 1
    assert brief["n_candidate_route_option_residual_goals"] == 1
    selected = brief["candidate_route_options"][0]
    assert selected["route_option_id"] == "residual_bridge"
    assert selected["n_residual_goals"] == 1
    assert selected["n_residual_goal_contexts"] == 1
    assert selected["residual_target_primitives"] == ["rank_uniformity"]
    assert selected["residual_goal_samples"] == [residual_goal]


def test_route_option_selection_validation_rejects_residual_blind_same_cost_choice() -> None:
    request = {
        "context_packet": {
            "route_option_selection_brief": {
                "candidate_route_options": [
                    {
                        "route_option_id": "reuse_only",
                        "selected_primitives": ["exchangeability"],
                        "minimum_route_base_cost": 4,
                        "n_residual_goals": 0,
                    },
                    {
                        "route_option_id": "residual_bridge",
                        "selected_primitives": ["rank_uniformity"],
                        "minimum_route_base_cost": 4,
                        "n_residual_goals": 1,
                    },
                ],
                "lower_bound_selected_route_option_id": "residual_bridge",
                "lower_bound_selected_route_cost": 4,
                "lower_bound_selected_residual_goal_count": 1,
            }
        }
    }
    payload = {
        "minimal_delta_plan": {
            "and_or_cost_graph": {
                "selected_route_option_id": "reuse_only",
                "route_options": [
                    {
                        "route_option_id": "reuse_only",
                        "selected": True,
                        "selected_primitives": ["exchangeability"],
                        "route_cost": 4,
                        "cost_rationale": "Same base cost as the bridge option.",
                    },
                    {
                        "route_option_id": "residual_bridge",
                        "selected": False,
                        "selected_primitives": ["rank_uniformity"],
                        "route_cost": 4,
                        "cost_rationale": (
                            "Same base cost and covers the current residual goal."
                        ),
                    },
                ],
            }
        }
    }

    errors = _minimal_delta_route_option_selection_brief_errors(payload, request)

    assert any(
        "residual-aware lower-bound route option residual_bridge" in error
        and "selected reuse_only covers 0 residual goal(s)" in error
        for error in errors
    )

    residual_aware_payload = deepcopy(payload)
    graph = residual_aware_payload["minimal_delta_plan"]["and_or_cost_graph"]
    graph["selected_route_option_id"] = "residual_bridge"
    graph["route_options"][0]["selected"] = False
    graph["route_options"][1]["selected"] = True
    assert (
        _minimal_delta_route_option_selection_brief_errors(
            residual_aware_payload,
            request,
        )
        == []
    )


def _write_light_input(root: Path) -> Path:
    input_json = root / "standalone_input_light.json"
    input_json.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "component_name": "formalization_gap_planner_standalone_input",
                "target_prover_family": "lean4",
                "library_snapshot_ref": "lean_mathlib_snapshot",
                "routes": [
                    {
                        "route_id": "rank_route_light",
                        "display_name": "distribution_free_rank_bound_light",
                        "theorem_statement": "A small rank fact follows from existing exchangeability lemmas.",
                        "source_refs": ["conformal_prediction_textbook"],
                        "source_snippets": [
                            {
                                "source_ref": "conformal_prediction_textbook",
                                "claim": "Exchangeability implies a uniform rank statistic.",
                                "excerpt": (
                                    "Under exchangeability, the rank of the test score "
                                    "among calibration scores is uniformly distributed "
                                    "up to the tie convention."
                                ),
                                "target_primitives": ["rank_uniformity"],
                            }
                        ],
                        "primitives": [
                            {
                                "primitive": "exchangeability",
                                "coverage_status": "exact_exists",
                                "candidate_declarations": ["Probability.exchangeable"],
                            },
                            {
                                "primitive": "rank_uniformity",
                                "coverage_status": "near_exists",
                                "candidate_declarations": ["Probability.exchangeable"],
                            },
                        ],
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return input_json


def _write_rank_target_intake_manifest(target_intake_dir: Path) -> None:
    target_intake_dir.mkdir(parents=True, exist_ok=True)
    (
        target_intake_dir / "formalization_gap_planner_target_intake_manifest.json"
    ).write_text(
        json.dumps(
            {
                "component_name": "formalization_gap_planner_target_intake",
                "rows": [
                    {
                        "schema_version": 1,
                        "target_intake_id": "target-intake:rank-context",
                        "target_id": "distribution_free_rank_bound",
                        "display_name": "distribution free rank bound",
                        "domain": "conformal_prediction",
                        "target_prover_family": "lean4",
                        "library_snapshot_ref": "lean_mathlib_snapshot",
                        "theorem_statement": (
                            "A distribution-free rank bound follows from "
                            "exchangeability."
                        ),
                        "theorem_skeleton": "",
                        "normalized_objects": [
                            "calibration scores",
                            "test score",
                            "rank statistic",
                        ],
                        "normalized_assumptions": [
                            "exchangeability",
                            "deterministic tie handling",
                        ],
                        "normalized_procedure": "split conformal prediction",
                        "normalized_claim": "finite-sample rank coverage",
                        "desired_theorem_shape": "finite_sample_rank_coverage",
                        "proof_source_refs": ["conformal_prediction_textbook"],
                        "primitive_seed_rows": [
                            {
                                "primitive": "rank_uniformity",
                                "coverage_status": "bridge_needed",
                            }
                        ],
                        "extracted_primitive_candidates": ["rank_uniformity"],
                        "background_primitives": ["exchangeability"],
                        "standalone_route_id": "rank_route",
                        "literature_queries": ["finite rank coverage under exchangeability"],
                        "formal_library_grounding_queries": [
                            "rank uniformity bridge lemma"
                        ],
                        "lean_grounding_queries": [],
                        "proof_state_probe_required": False,
                        "missing_required_fields": [],
                        "review_flags": [],
                        "proof_evidence_status": (
                            "FORMALIZATION_GAP_PLANNER_TARGET_INTAKE_NOT_PROOF_EVIDENCE"
                        ),
                        "proof_evidence_boundary": (
                            "target intake is not theorem proof evidence"
                        ),
                        "ok": True,
                        "errors": [],
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def _llm_response_payload() -> dict[str, object]:
    rank_source_snippet = {
        "source_ref": "conformal_prediction_textbook",
        "claim": "Exchangeability implies a uniform rank statistic.",
        "excerpt": (
            "Under exchangeability, the rank of the test score among calibration "
            "scores is uniformly distributed up to the tie convention."
        ),
        "target_primitives": ["rank_uniformity"],
    }
    return {
        "source_snippets": [rank_source_snippet],
        "informal_knowledge_dag_nodes": [
            {
                "node_id": "informal:exchangeability",
                "claim": "The observations are exchangeable under the null route.",
                "depends_on": [],
                "source_refs": ["conformal_prediction_textbook"],
                "source_search_status": "SOURCE_BACKED",
                "semantic_role": "assumption",
            },
            {
                "node_id": "informal:rank_uniformity",
                "claim": "Exchangeability implies uniformity of the rank statistic.",
                "depends_on": ["informal:exchangeability"],
                "source_refs": ["conformal_prediction_textbook"],
                "source_snippets": [rank_source_snippet],
                "source_search_status": "SOURCE_BACKED",
                "semantic_role": "lemma",
            },
        ],
        "informal_knowledge_dag_edges": [
            {
                "source_node_id": "informal:exchangeability",
                "target_node_id": "informal:rank_uniformity",
                "edge_kind": "uses",
                "rationale": (
                    "The rank-uniformity lemma uses the exchangeability "
                    "assumption as its source-backed premise."
                ),
            }
        ],
        "lean_realization_dag_nodes": [
            {
                "node_id": "formal:exchangeability",
                "primitive": "exchangeability",
                "coverage_bucket": "already_exists",
                "candidate_declarations": ["Probability.exchangeable"],
                "formalization_action": "reuse",
            },
            {
                "node_id": "formal:rank_uniformity_bridge",
                "primitive": "rank_uniformity",
                "coverage_bucket": "bridge",
                "candidate_declarations": [],
                "formalization_action": "prove_bridge",
            },
        ],
        "formal_realization_dag_edges": [
            {
                "source_node_id": "formal:exchangeability",
                "target_node_id": "formal:rank_uniformity_bridge",
                "edge_kind": "bridges",
                "rationale": (
                    "The rank-uniformity bridge is proved from the reused "
                    "exchangeability formal primitive."
                ),
            }
        ],
        "route_alignment_edges": [
            {
                "informal_node_id": "informal:rank_uniformity",
                "formal_node_id": "formal:rank_uniformity_bridge",
                "alignment_status": "bridge_needed",
                "alignment_rationale": (
                    "The library has exchangeability but not the exact finite-rank "
                    "statement, so a bridge lemma is the minimal new Lean work."
                ),
            },
            {
                "informal_node_id": "informal:exchangeability",
                "formal_node_id": "formal:exchangeability",
                "alignment_status": "exact",
                "alignment_rationale": (
                    "The exchangeability assumption maps to the existing formal "
                    "declaration listed in the request context."
                ),
            },
        ],
        "minimal_delta_plan": {
            "selected_primitives": ["exchangeability", "rank_uniformity"],
            "cost_model_version": "formalization_gap_planner_minimal_delta_cost_policy:1",
            "route_cost": 4,
            "primitive_costs": [
                {
                    "primitive": "exchangeability",
                    "coverage_bucket": "already_exists",
                    "base_cost": 0,
                    "proof_difficulty_cost": 0,
                    "import_cone_cost": 0,
                    "definition_or_typeclass_cost": 0,
                    "semantic_risk_cost": 0,
                    "reuse_credit": 0,
                    "total_cost": 0,
                    "cost_rationale": "The route reuses the existing exchangeability declaration.",
                },
                {
                    "primitive": "rank_uniformity",
                    "coverage_bucket": "bridge_needed",
                    "base_cost": 4,
                    "proof_difficulty_cost": 0,
                    "import_cone_cost": 0,
                    "definition_or_typeclass_cost": 0,
                    "semantic_risk_cost": 0,
                    "reuse_credit": 0,
                    "total_cost": 4,
                    "cost_rationale": "Only a narrow bridge lemma is needed.",
                },
            ],
            "new_definitions": [],
            "wrapper_lemmas": [],
            "bridge_lemmas": [
                (
                    "rank_uniformity: prove finite rank uniformity from "
                    "exchangeability as the target-prover bridge lemma"
                )
            ],
            "source_port_lemmas": [],
            "do_not_formalize_now": ["full conformal prediction pipeline"],
            "and_or_cost_graph": {
                "graph_kind": "AND_OR_ROUTE_COST_GRAPH",
                "selected_route_option_id": "route_option:reuse_exchangeability_bridge_rank",
                "route_options": [
                    {
                        "route_option_id": "route_option:reuse_exchangeability_bridge_rank",
                        "selected": True,
                        "selected_primitives": ["exchangeability", "rank_uniformity"],
                        "route_cost": 4,
                        "cost_rationale": "Reuse exchangeability and add one bridge lemma.",
                    },
                    {
                        "route_option_id": "route_option:source_port_rank_theory",
                        "selected": False,
                        "selected_primitives": ["exchangeability", "rank_uniformity"],
                        "route_cost": 7,
                        "cost_rationale": "Porting a source theorem costs more than the focused bridge.",
                        "source_port_lemmas": [
                            (
                                "rank_uniformity: port the textbook finite-rank "
                                "uniformity theorem, including the target-prover "
                                "tie convention assumptions"
                            )
                        ],
                        "primitive_costs": [
                            {
                                "primitive": "exchangeability",
                                "coverage_bucket": "already_exists",
                                "base_cost": 0,
                                "proof_difficulty_cost": 0,
                                "import_cone_cost": 0,
                                "definition_or_typeclass_cost": 0,
                                "semantic_risk_cost": 0,
                                "reuse_credit": 0,
                                "total_cost": 0,
                                "cost_rationale": (
                                    "The source-port route still reuses the "
                                    "existing exchangeability declaration."
                                ),
                            },
                            {
                                "primitive": "rank_uniformity",
                                "coverage_bucket": "source_port",
                                "base_cost": 7,
                                "proof_difficulty_cost": 0,
                                "import_cone_cost": 0,
                                "definition_or_typeclass_cost": 0,
                                "semantic_risk_cost": 0,
                                "reuse_credit": 0,
                                "total_cost": 7,
                                "cost_rationale": (
                                    "This alternative ports the rank theorem "
                                    "instead of proving the bridge lemma."
                                ),
                            },
                        ],
                    },
                ],
                "or_nodes": [
                    {
                        "node_id": "or:rank_uniformity_realization",
                        "choices": [
                            "route_option:reuse_exchangeability_bridge_rank",
                            "route_option:source_port_rank_theory",
                        ],
                        "selection_rationale": "The bridge route has the lower enumerated route cost.",
                    }
                ],
                "and_edges": [
                    {
                        "route_option_id": "route_option:reuse_exchangeability_bridge_rank",
                        "requires": ["exchangeability", "rank_uniformity"],
                    },
                    {
                        "route_option_id": "route_option:source_port_rank_theory",
                        "requires": ["exchangeability", "rank_uniformity"],
                    },
                ],
            },
            "minimality_rationale": (
                "Reuse exchangeability and add only the rank-uniformity bridge "
                "instead of porting the whole conformal prediction theory."
            ),
        },
        "residual_interpretations": [],
        "search_requests": [
            {
                "request_kind": "prover_feedback",
                "query": "try rank_uniformity bridge against Probability.exchangeable",
                "reason": "confirm remaining side conditions before route adoption",
            }
        ],
        "uncertainty_flags": ["finite support and tie-breaking assumptions need review"],
        "semantic_alignment_risks": ["rank convention may differ from textbook"],
        "planner_next_actions": [
            {
                "owner": "lean_lsp_mcp",
                "action": "attempt the rank_uniformity bridge lemma",
                "target_primitives": ["rank_uniformity"],
            }
        ],
        "formal_attempt_queue": [
            {
                "attempt_id": "attempt:exchangeability_reuse",
                "formal_node_id": "formal:exchangeability",
                "primitive": "exchangeability",
                "target_prover_family": "lean4",
                "owner": "lean_lsp_mcp",
                "action": (
                    "lean_lsp proof-state reuse check for "
                    "Probability.exchangeable"
                ),
                "attempt_kind": "reuse_check",
                "prerequisite_formal_node_ids": [],
                "expected_feedback": ["closed_by_existing_declaration"],
                "target_primitives": ["exchangeability"],
            },
            {
                "attempt_id": "attempt:rank_uniformity_bridge",
                "formal_node_id": "formal:rank_uniformity_bridge",
                "primitive": "rank_uniformity",
                "target_prover_family": "lean4",
                "owner": "lean_lsp_mcp",
                "action": (
                    "lean_lsp proof-state attempt for the rank_uniformity bridge "
                    "lemma after exchangeability reuse"
                ),
                "attempt_kind": "bridge_proof",
                "prerequisite_formal_node_ids": ["formal:exchangeability"],
                "expected_feedback": [
                    "residual_goals",
                    "missing_side_conditions",
                    "closed_by_existing_declaration",
                ],
                "target_primitives": ["rank_uniformity"],
            },
        ],
        "standalone_route": {
            "route_id": "rank_route_llm_revision",
            "display_name": "distribution_free_rank_bound_llm_revision",
            "theorem_statement": (
                "A distribution-free rank bound follows from exchangeability and "
                "a finite-rank bridge lemma."
            ),
            "source_refs": ["conformal_prediction_textbook"],
            "source_snippets": [rank_source_snippet],
            "primitives": [
                {
                    "primitive": "exchangeability",
                    "coverage_status": "exact_exists",
                    "candidate_declarations": ["Probability.exchangeable"],
                    "source_refs": ["conformal_prediction_textbook"],
                },
                {
                    "primitive": "rank_uniformity",
                    "coverage_status": "bridge_needed",
                    "source_refs": ["conformal_prediction_textbook"],
                    "source_snippets": [rank_source_snippet],
                },
            ],
        },
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
    }


def _retarget_formal_attempt_queue(
    response: dict[str, object],
    *,
    target_prover_family: str,
    owner: str,
) -> None:
    for item in response.get("formal_attempt_queue", []):
        if not isinstance(item, dict):
            continue
        primitive = str(item.get("primitive", "")).strip()
        item["target_prover_family"] = target_prover_family
        item["owner"] = owner
        item["action"] = (
            f"{owner} proof-state attempt for {primitive} on "
            f"{target_prover_family}"
        )


def _set_existing_candidate_declaration_rows(
    response: dict[str, object],
    *,
    declaration: str,
    target_prover_family: str,
) -> None:
    declaration_row = {
        "declaration": declaration,
        "target_prover_family": target_prover_family,
        "source_field": "candidate_declarations",
    }
    for field_name in ("formal_realization_dag_nodes", "lean_realization_dag_nodes"):
        for node in response.get(field_name, []):
            if (
                not isinstance(node, dict)
                or node.get("primitive") != "exchangeability"
            ):
                continue
            node["candidate_declarations"] = [declaration]
            node["candidate_declaration_rows"] = [dict(declaration_row)]
    route = response.get("standalone_route", {})
    if not isinstance(route, dict):
        return
    route["target_prover_family"] = target_prover_family
    for primitive in route.get("primitives", []):
        if (
            not isinstance(primitive, dict)
            or primitive.get("primitive") != "exchangeability"
        ):
            continue
        primitive["candidate_declarations"] = [declaration]
        primitive["candidate_declaration_rows"] = [dict(declaration_row)]


def _append_bridge_cost(
    response: dict[str, object],
    primitive: str,
    *,
    total_cost: int = 4,
) -> None:
    minimal_delta = response["minimal_delta_plan"]
    assert isinstance(minimal_delta, dict)
    minimal_delta["route_cost"] = int(minimal_delta["route_cost"]) + total_cost
    primitive_costs = minimal_delta["primitive_costs"]
    assert isinstance(primitive_costs, list)
    bridge_witness = (
        f"{primitive}: prove the focused bridge lemma required by the "
        "augmented route option"
    )
    primitive_costs.append(
        {
            "primitive": primitive,
            "coverage_bucket": "bridge_needed",
            "base_cost": total_cost,
            "proof_difficulty_cost": 0,
            "import_cone_cost": 0,
            "definition_or_typeclass_cost": 0,
            "semantic_risk_cost": 0,
            "reuse_credit": 0,
            "total_cost": total_cost,
            "cost_rationale": "The added primitive is modeled as one focused bridge lemma.",
        }
    )
    minimal_delta.setdefault("bridge_lemmas", []).append(bridge_witness)
    graph = minimal_delta["and_or_cost_graph"]
    assert isinstance(graph, dict)
    route_options = graph["route_options"]
    assert isinstance(route_options, list)
    added_cost_row = {
        "primitive": primitive,
        "coverage_bucket": "bridge_needed",
        "base_cost": total_cost,
        "proof_difficulty_cost": 0,
        "import_cone_cost": 0,
        "definition_or_typeclass_cost": 0,
        "semantic_risk_cost": 0,
        "reuse_credit": 0,
        "total_cost": total_cost,
        "cost_rationale": "The added primitive is modeled as one focused bridge lemma.",
    }
    for option in route_options:
        option["route_cost"] = int(option["route_cost"]) + total_cost
        option["selected_primitives"] = [
            *option.get("selected_primitives", []),
            primitive,
        ]
        option_costs = option.get("primitive_costs")
        if isinstance(option_costs, list):
            option_costs.append(dict(added_cost_row))
            option.setdefault("bridge_lemmas", []).append(bridge_witness)
    edge_primitives_by_option = {
        str(option.get("route_option_id", "")): list(option["selected_primitives"])
        for option in route_options
        if str(option.get("route_option_id", ""))
    }
    updated_edges: set[str] = set()
    for edge in graph["and_edges"]:
        option_id = str(edge.get("route_option_id", ""))
        if option_id in edge_primitives_by_option:
            edge["requires"] = edge_primitives_by_option[option_id]
            updated_edges.add(option_id)
    for option_id, option_primitives in edge_primitives_by_option.items():
        if option_id in updated_edges:
            continue
        graph["and_edges"].append(
            {
                "route_option_id": option_id,
                "requires": option_primitives,
            }
        )


def _append_unselected_baseline_primitive(
    response: dict[str, object],
    *,
    primitive: str = "coverage_probability",
) -> None:
    minimal_delta = response["minimal_delta_plan"]
    assert isinstance(minimal_delta, dict)
    primitive_costs = minimal_delta["primitive_costs"]
    assert isinstance(primitive_costs, list)
    primitive_costs.append(
        {
            "primitive": primitive,
            "coverage_bucket": "already_exists",
            "base_cost": 0,
            "proof_difficulty_cost": 0,
            "import_cone_cost": 0,
            "definition_or_typeclass_cost": 0,
            "semantic_risk_cost": 0,
            "reuse_credit": 0,
            "total_cost": 0,
            "cost_rationale": (
                "This request-known baseline primitive is not part of the "
                "selected route."
            ),
        }
    )
    graph = minimal_delta["and_or_cost_graph"]
    assert isinstance(graph, dict)
    route_options = graph["route_options"]
    assert isinstance(route_options, list)
    option_id = "route_option:current_route_min_delta_baseline"
    route_options.append(
        {
            "route_option_id": option_id,
            "selected": False,
            "selected_primitives": [
                "exchangeability",
                "rank_uniformity",
                primitive,
            ],
            "route_cost": 4,
            "cost_rationale": (
                "The baseline route keeps the request-known primitive visible "
                "without selecting it for prover execution."
            ),
        }
    )
    or_nodes = graph["or_nodes"]
    assert isinstance(or_nodes, list)
    choices = or_nodes[0]["choices"]
    assert isinstance(choices, list)
    choices.append(option_id)
    and_edges = graph["and_edges"]
    assert isinstance(and_edges, list)
    and_edges.append(
        {
            "route_option_id": option_id,
            "requires": ["exchangeability", "rank_uniformity", primitive],
        }
    )


def _append_current_route_baseline_option(
    response: dict[str, object],
    *,
    selected_primitives: list[str] | None = None,
    route_cost: int = 4,
) -> None:
    minimal_delta = response["minimal_delta_plan"]
    assert isinstance(minimal_delta, dict)
    graph = minimal_delta["and_or_cost_graph"]
    assert isinstance(graph, dict)
    route_options = graph["route_options"]
    assert isinstance(route_options, list)
    option_id = "route_option:current_route_min_delta_baseline"
    baseline_primitives = selected_primitives or [
        "exchangeability",
        "rank_uniformity",
    ]
    if not any(option.get("route_option_id") == option_id for option in route_options):
        route_options.append(
            {
                "route_option_id": option_id,
                "selected": False,
                "selected_primitives": baseline_primitives,
                "route_cost": route_cost,
                "cost_rationale": (
                    "The current request baseline is retained for route-option "
                    "selection comparison."
                ),
            }
        )
    or_nodes = graph["or_nodes"]
    assert isinstance(or_nodes, list)
    choices = or_nodes[0]["choices"]
    assert isinstance(choices, list)
    if option_id not in choices:
        choices.append(option_id)
    and_edges = graph["and_edges"]
    assert isinstance(and_edges, list)
    for edge in and_edges:
        if edge.get("route_option_id") == option_id:
            edge["requires"] = baseline_primitives
            break
    else:
        and_edges.append(
            {
                "route_option_id": option_id,
                "requires": baseline_primitives,
            }
        )


def _append_request_route_primitive(
    input_json: Path,
    *,
    primitive: str = "coverage_probability",
) -> None:
    payload = json.loads(input_json.read_text(encoding="utf-8"))
    payload["routes"][0]["primitives"].append(
        {
            "primitive": primitive,
            "coverage_status": "exact_exists",
            "candidate_declarations": ["Probability.coverageProbability"],
        }
    )
    input_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _make_rank_uniformity_near_exists_response() -> dict[str, object]:
    response = _llm_response_payload()
    response["lean_realization_dag_nodes"][1]["coverage_bucket"] = "near_exists"
    response["lean_realization_dag_nodes"][1][
        "candidate_declarations"
    ] = ["Probability.exchangeable"]
    response["lean_realization_dag_nodes"][1][
        "formalization_action"
    ] = "compose_existing_declarations"
    response["route_alignment_edges"][0]["alignment_status"] = "near"
    minimal_delta = response["minimal_delta_plan"]
    assert isinstance(minimal_delta, dict)
    minimal_delta["route_cost"] = 1
    rank_cost = minimal_delta["primitive_costs"][1]
    assert isinstance(rank_cost, dict)
    rank_cost["coverage_bucket"] = "near_exists"
    rank_cost["base_cost"] = 1
    rank_cost["total_cost"] = 1
    rank_cost["cost_rationale"] = (
        "The answer claims an existing nearby declaration is enough."
    )
    minimal_delta["bridge_lemmas"] = []
    graph = minimal_delta["and_or_cost_graph"]
    assert isinstance(graph, dict)
    route_options = graph["route_options"]
    assert isinstance(route_options, list)
    route_options[0]["route_cost"] = 1
    route_options[0]["cost_rationale"] = (
        "The answer claims the rank fact is near existing library coverage."
    )
    route_options[1]["route_cost"] = 7
    standalone_rank = response["standalone_route"]["primitives"][1]
    assert isinstance(standalone_rank, dict)
    standalone_rank["coverage_status"] = "near_exists"
    standalone_rank["candidate_declarations"] = ["Probability.exchangeable"]
    rank_attempt = response["formal_attempt_queue"][1]
    assert isinstance(rank_attempt, dict)
    rank_attempt["attempt_kind"] = "reuse_check"
    rank_attempt["expected_feedback"] = [
        "closed_by_existing_declaration",
        "residual_goals",
    ]
    return response


def _make_rank_uniformity_coverage_downgrade_response() -> dict[str, object]:
    response = _llm_response_payload()
    rank_node = response["lean_realization_dag_nodes"][1]
    assert isinstance(rank_node, dict)
    rank_node["coverage_bucket"] = "near_exists"
    rank_node["candidate_declarations"] = ["Probability.rankUniformityBridge"]
    rank_node["formalization_action"] = "compose_existing_declarations"
    response["route_alignment_edges"][0]["alignment_status"] = "near"
    standalone_rank = response["standalone_route"]["primitives"][1]
    assert isinstance(standalone_rank, dict)
    standalone_rank["coverage_status"] = "near_exists"
    standalone_rank["candidate_declarations"] = [
        "Probability.rankUniformityBridge"
    ]
    return response


def _make_rank_uniformity_unanchored_wrapper_response() -> dict[str, object]:
    response = _llm_response_payload()
    rank_node = response["lean_realization_dag_nodes"][1]
    assert isinstance(rank_node, dict)
    rank_node["coverage_bucket"] = "wrapper"
    rank_node["formalization_action"] = "write_wrapper"
    rank_node.pop("candidate_declarations", None)
    rank_node.pop("candidate_declaration_rows", None)
    response["route_alignment_edges"][0]["alignment_status"] = "wrapper_needed"
    minimal_delta = response["minimal_delta_plan"]
    assert isinstance(minimal_delta, dict)
    minimal_delta["route_cost"] = 4
    minimal_delta["bridge_lemmas"] = []
    minimal_delta["wrapper_lemmas"] = [
        (
            "rank_uniformity wrapper theorem: prove the requested finite-rank "
            "statement from an existing declaration once the wrapped target is "
            "identified"
        )
    ]
    rank_cost = minimal_delta["primitive_costs"][1]
    assert isinstance(rank_cost, dict)
    rank_cost["coverage_bucket"] = "wrapper"
    rank_cost["base_cost"] = 2
    rank_cost["proof_difficulty_cost"] = 2
    rank_cost["total_cost"] = 4
    rank_cost["cost_rationale"] = (
        "The route writes a wrapper around an existing declaration."
    )
    graph = minimal_delta["and_or_cost_graph"]
    assert isinstance(graph, dict)
    route_options = graph["route_options"]
    assert isinstance(route_options, list)
    route_options[0]["route_cost"] = 4
    route_options[0]["cost_rationale"] = (
        "The selected route pays wrapper effort for rank uniformity."
    )
    route_options[1]["route_cost"] = 7
    standalone_rank = response["standalone_route"]["primitives"][1]
    assert isinstance(standalone_rank, dict)
    standalone_rank["coverage_status"] = "wrapper_needed"
    standalone_rank.pop("candidate_declarations", None)
    standalone_rank.pop("candidate_declaration_rows", None)
    return response


def _make_rank_uniformity_reuse_response(
    declaration_row: dict[str, object],
) -> dict[str, object]:
    response = _llm_response_payload()
    rank_node = response["lean_realization_dag_nodes"][1]
    assert isinstance(rank_node, dict)
    rank_node["coverage_bucket"] = "already_exists"
    rank_node.pop("candidate_declarations", None)
    rank_node["candidate_declaration_rows"] = [dict(declaration_row)]
    rank_node["formalization_action"] = "reuse"
    response["route_alignment_edges"][0]["alignment_status"] = "exact"
    response["route_alignment_edges"][0]["alignment_rationale"] = (
        "The response claims the rank primitive can be reused from a listed "
        "formal declaration."
    )
    minimal_delta = response["minimal_delta_plan"]
    assert isinstance(minimal_delta, dict)
    minimal_delta["route_cost"] = 0
    minimal_delta["bridge_lemmas"] = []
    rank_cost = minimal_delta["primitive_costs"][1]
    assert isinstance(rank_cost, dict)
    rank_cost["coverage_bucket"] = "already_exists"
    rank_cost["base_cost"] = 0
    rank_cost["total_cost"] = 0
    rank_cost["cost_rationale"] = (
        "The response claims the rank primitive is already covered."
    )
    graph = minimal_delta["and_or_cost_graph"]
    assert isinstance(graph, dict)
    route_options = graph["route_options"]
    assert isinstance(route_options, list)
    route_options[0]["route_cost"] = 0
    route_options[0]["cost_rationale"] = (
        "The response claims both selected primitives reuse existing declarations."
    )
    route_options[1]["route_cost"] = 7
    standalone_rank = response["standalone_route"]["primitives"][1]
    assert isinstance(standalone_rank, dict)
    standalone_rank["coverage_status"] = "exact_exists"
    standalone_rank.pop("candidate_declarations", None)
    standalone_rank["candidate_declaration_rows"] = [dict(declaration_row)]
    rank_attempt = response["formal_attempt_queue"][1]
    assert isinstance(rank_attempt, dict)
    rank_attempt["attempt_kind"] = "reuse_check"
    rank_attempt["expected_feedback"] = ["closed_by_existing_declaration"]
    return response


def _make_rank_uniformity_omitted_response(
    *,
    include_baseline_route_option: bool = False,
    baseline_route_cost: int = 4,
) -> dict[str, object]:
    response = _llm_response_payload()
    response["informal_knowledge_dag_nodes"] = [
        response["informal_knowledge_dag_nodes"][0]
    ]
    response["informal_knowledge_dag_edges"] = []
    response["lean_realization_dag_nodes"] = [
        response["lean_realization_dag_nodes"][0]
    ]
    response["formal_realization_dag_edges"] = []
    if include_baseline_route_option:
        response["lean_realization_dag_nodes"].append(
            {
                "node_id": "formal:rank_uniformity_bridge",
                "primitive": "rank_uniformity",
                "coverage_bucket": "bridge",
                "candidate_declarations": [],
                "formalization_action": "prove_bridge",
            }
        )
        response["formal_realization_dag_edges"] = [
            {
                "source_node_id": "formal:exchangeability",
                "target_node_id": "formal:rank_uniformity_bridge",
                "edge_kind": "bridges",
                "rationale": (
                    "The baseline rank-uniformity bridge depends on the "
                    "exchangeability formal primitive."
                ),
            }
        ]
    response["route_alignment_edges"] = [
        {
            "informal_node_id": "informal:exchangeability",
            "formal_node_id": "formal:exchangeability",
            "alignment_status": "exact",
            "alignment_rationale": (
                "The response claims exchangeability alone is the selected route."
            ),
        }
    ]
    minimal_delta = response["minimal_delta_plan"]
    assert isinstance(minimal_delta, dict)
    minimal_delta["selected_primitives"] = ["exchangeability"]
    minimal_delta["route_cost"] = 0
    if not include_baseline_route_option:
        minimal_delta["primitive_costs"] = [minimal_delta["primitive_costs"][0]]
    minimal_delta["bridge_lemmas"] = []
    graph = minimal_delta["and_or_cost_graph"]
    assert isinstance(graph, dict)
    graph["selected_route_option_id"] = "route_option:exchangeability_only"
    route_options = [
        {
            "route_option_id": "route_option:exchangeability_only",
            "selected": True,
            "selected_primitives": ["exchangeability"],
            "route_cost": 0,
            "cost_rationale": (
                "The response claims the current rank-uniformity primitive is "
                "unnecessary."
            ),
        }
    ]
    if include_baseline_route_option:
        route_options.append(
            {
                "route_option_id": "route_option:current_route_min_delta_baseline",
                "selected": False,
                "selected_primitives": ["exchangeability", "rank_uniformity"],
                "route_cost": baseline_route_cost,
                "cost_rationale": (
                    "The original request baseline keeps rank_uniformity."
                ),
            }
        )
    graph["route_options"] = route_options
    graph["or_nodes"] = [
        {
            "node_id": "or:rank_route_choice",
            "choices": [option["route_option_id"] for option in route_options],
            "selection_rationale": (
                "The response selects the exchangeability-only route."
            ),
        }
    ]
    graph["and_edges"] = [
        {
            "route_option_id": option["route_option_id"],
            "requires": option["selected_primitives"],
        }
        for option in route_options
    ]
    standalone_primitives = [response["standalone_route"]["primitives"][0]]
    if include_baseline_route_option:
        standalone_primitives.append(response["standalone_route"]["primitives"][1])
    response["standalone_route"]["primitives"] = standalone_primitives
    response["standalone_route"]["theorem_statement"] = (
        "A distribution-free rank bound follows from exchangeability."
    )
    return response


def _append_underpriced_rank_route_option(
    response: dict[str, object],
    *,
    route_cost: int = 3,
) -> None:
    minimal_delta = response["minimal_delta_plan"]
    assert isinstance(minimal_delta, dict)
    graph = minimal_delta["and_or_cost_graph"]
    assert isinstance(graph, dict)
    route_options = graph["route_options"]
    assert isinstance(route_options, list)
    underpriced_option = {
        "route_option_id": "route_option:underpriced_rank_only",
        "selected": False,
        "selected_primitives": ["rank_uniformity"],
        "route_cost": route_cost,
        "cost_rationale": (
            "This corrupted option underprices the request-bound rank bridge."
        ),
    }
    route_options.append(underpriced_option)
    or_nodes = graph["or_nodes"]
    assert isinstance(or_nodes, list)
    assert isinstance(or_nodes[0], dict)
    choices = or_nodes[0]["choices"]
    assert isinstance(choices, list)
    choices.append(underpriced_option["route_option_id"])
    and_edges = graph["and_edges"]
    assert isinstance(and_edges, list)
    and_edges.append(
        {
            "route_option_id": underpriced_option["route_option_id"],
            "requires": underpriced_option["selected_primitives"],
        }
    )


def _promote_response_to_source_port_costs(response: dict[str, object]) -> None:
    for node in response.get("lean_realization_dag_nodes", []):
        if isinstance(node, dict):
            node["coverage_bucket"] = "source_port_needed"
            node["formalization_action"] = "port_external_source"
    for attempt in response.get("formal_attempt_queue", []):
        if isinstance(attempt, dict):
            attempt["attempt_kind"] = "source_port_probe"
            attempt["expected_feedback"] = [
                "source_port_targets",
                "residual_goals",
                "missing_side_conditions",
            ]
    for edge in response.get("route_alignment_edges", []):
        if isinstance(edge, dict):
            edge["alignment_status"] = "source_port_needed"
    response["route_alignment_edges"].append(
        {
            "informal_node_id": "informal:exchangeability",
            "formal_node_id": "formal:exchangeability",
            "alignment_status": "source_port_needed",
            "alignment_rationale": (
                "The carried replan handoff prices exchangeability as a "
                "source-port obligation, so the response must align it "
                "explicitly before adoption."
            ),
        }
    )
    minimal_delta = response["minimal_delta_plan"]
    assert isinstance(minimal_delta, dict)
    minimal_delta["route_cost"] = 14
    for row in minimal_delta["primitive_costs"]:
        assert isinstance(row, dict)
        row["coverage_bucket"] = "source_port_needed"
        row["base_cost"] = 7
        row["total_cost"] = 7
        row["cost_rationale"] = (
            "The carried replan handoff marks this primitive as a source-port "
            "obligation under the published minimal-delta cost policy."
        )
    minimal_delta["bridge_lemmas"] = []
    minimal_delta["source_port_lemmas"] = [
        (
            "exchangeability: port the source-backed exchangeability premise "
            "needed by the target rank route"
        ),
        (
            "rank_uniformity: port the source-backed finite-rank uniformity "
            "lemma with the carried tie-breaking side condition"
        ),
    ]
    graph = minimal_delta["and_or_cost_graph"]
    assert isinstance(graph, dict)
    route_options = graph["route_options"]
    assert isinstance(route_options, list)
    route_options[0]["route_cost"] = 14
    route_options[0]["cost_rationale"] = (
        "The selected replan route carries two source-port obligations."
    )
    route_options[1]["route_cost"] = 16
    route_options[1]["source_port_lemmas"] = [
        (
            "exchangeability: port the alternative source-backed exchangeability "
            "premise before replaying the rank route"
        ),
        (
            "rank_uniformity: port the alternative source-backed finite-rank "
            "uniformity theorem with the extra side-condition allowance"
        ),
    ]
    route_options[1]["primitive_costs"] = [
        {
            "primitive": "exchangeability",
            "coverage_bucket": "source_port_needed",
            "base_cost": 7,
            "proof_difficulty_cost": 0,
            "import_cone_cost": 0,
            "definition_or_typeclass_cost": 0,
            "semantic_risk_cost": 0,
            "reuse_credit": 0,
            "total_cost": 7,
            "cost_rationale": (
                "The alternative replan route ports the exchangeability premise."
            ),
        },
        {
            "primitive": "rank_uniformity",
            "coverage_bucket": "source_port_needed",
            "base_cost": 7,
            "proof_difficulty_cost": 2,
            "import_cone_cost": 0,
            "definition_or_typeclass_cost": 0,
            "semantic_risk_cost": 0,
            "reuse_credit": 0,
            "total_cost": 9,
            "cost_rationale": (
                "The alternative replan route ports the rank lemma with an "
                "extra proof-difficulty allowance."
            ),
        },
    ]
    standalone_route = response.get("standalone_route", {})
    if isinstance(standalone_route, dict):
        for primitive in standalone_route.get("primitives", []):
            if isinstance(primitive, dict):
                primitive["coverage_status"] = "source_port_needed"


def _replace_source_ref(value, old: str, new: str):
    if isinstance(value, dict):
        return {key: _replace_source_ref(item, old, new) for key, item in value.items()}
    if isinstance(value, list):
        return [_replace_source_ref(item, old, new) for item in value]
    if isinstance(value, tuple):
        return tuple(_replace_source_ref(item, old, new) for item in value)
    return new if value == old else value


def _replace_source_snippets(value, snippet: dict[str, object]):
    if isinstance(value, dict):
        updated = {
            key: _replace_source_snippets(item, snippet)
            for key, item in value.items()
        }
        if "source_snippets" in updated:
            updated["source_snippets"] = [dict(snippet)]
        return updated
    if isinstance(value, list):
        return [_replace_source_snippets(item, snippet) for item in value]
    if isinstance(value, tuple):
        return tuple(_replace_source_snippets(item, snippet) for item in value)
    return value


def _drop_source_snippets(value):
    if isinstance(value, dict):
        return {
            key: _drop_source_snippets(item)
            for key, item in value.items()
            if key != "source_snippets"
        }
    if isinstance(value, list):
        return [_drop_source_snippets(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_drop_source_snippets(item) for item in value)
    return value


def _write_interactive_session(root: Path) -> Path:
    session_dir = root / "interactive_session"
    session_dir.mkdir(parents=True, exist_ok=True)
    (session_dir / "formalization_gap_planner_interactive_session_manifest.json").write_text(
        json.dumps(
            {
                "component_name": "formalization_gap_planner_interactive_session",
                "rows": [
                    {
                        "interactive_session_row_id": "session:rank_route",
                        "goal_plan_id": "goal:rank_route",
                        "route_id": "rank_route",
                        "display_name": "distribution_free_rank_bound",
                        "session_state": "EXPAND_PROOF_STATE_FEEDBACK",
                        "next_interaction_kind": "proof_state_feedback",
                        "next_owner_agent": "formal_verifier",
                        "next_tools": ["lean-lsp-mcp"],
                        "next_queries": ["rank_uniformity residual side conditions"],
                        "next_commands": ["lake build"],
                        "resource_request_ids": ["resource-request:rank_route"],
                        "resource_request_resource_ids": ["lean_lsp_mcp"],
                        "resource_request_queue_action_kinds": [
                            "proof_state_feedback"
                        ],
                        "resource_request_dispatch_summaries": [
                            {
                                "resource_request_id": "resource-request:rank_route",
                                "resource_id": "lean_lsp_mcp",
                                "request_phase": "frontier_escalation",
                                "request_rank": 1,
                                "queue_action_kind": "proof_state_feedback",
                                "expected_response_artifact": (
                                    "formalization_gap_planner_prover_adapter_packet"
                                ),
                                "dispatch_spec": {
                                    "resource_request_id": "resource-request:rank_route",
                                    "resource_id": "lean_lsp_mcp",
                                    "adapter": "lean_lsp_mcp",
                                },
                            }
                        ],
                        "resource_request_execution_commands": [
                            "lean-lsp-mcp goal rank_uniformity"
                        ],
                        "user_checkpoint": "review proof-state residual before route adoption",
                        "stability_decision": "EXPAND_EVIDENCE_BOUND",
                        "stable_under_current_evidence_bound": False,
                        "needs_more_proof_state_feedback": True,
                        "residual_goals": ["missing finite tie-breaking side condition"],
                        "triage_class": "repair_local_lean_proof_state",
                        "triage_required_gate": "rerun proof-state adapter",
                        "replan_required": False,
                    }
                ],
                "decision_policy_rows": [
                    {
                        "decision_policy_row_id": "policy:rank_route",
                        "interactive_session_row_id": "session:rank_route",
                        "goal_plan_id": "goal:rank_route",
                        "route_id": "rank_route",
                        "display_name": "distribution_free_rank_bound",
                        "session_state": "EXPAND_PROOF_STATE_FEEDBACK",
                        "next_interaction_kind": "proof_state_feedback",
                        "decision_rationale": "Lean residuals should be resolved before broadening literature search.",
                        "trigger_signals": ["residual_goals_present"],
                        "evidence_inputs": ["formalization_gap_planner_interactive_session"],
                        "required_tool_contracts": ["prover_feedback_refinement"],
                        "component_ids": ["prover_feedback_refinement"],
                        "local_first_resource_ids": ["lean_lsp"],
                        "frontier_escalation_resource_ids": ["leandojo"],
                        "resource_contract_ids": ["lean_lsp:proof_state_feedback"],
                        "required_quality_signals": ["diagnostic_signature"],
                        "quality_gates": ["response_schema_valid"],
                        "response_validation_signals": ["residual_goals_or_diagnostics_present"],
                        "stop_conditions": ["residual interpreted or source search requested"],
                        "fallback_actions": ["route_revision"],
                        "bounded_evidence_claim": "proof-state feedback is route-planning evidence only",
                        "resource_selection_rationale": "local Lean diagnostics are cheaper before frontier proof search",
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return session_dir


def _write_resource_response_ledger(root: Path) -> Path:
    ledger_dir = root / "resource_response_ledger"
    ledger_dir.mkdir(parents=True, exist_ok=True)
    (
        ledger_dir
        / "formalization_gap_planner_resource_response_ledger_manifest.json"
    ).write_text(
        json.dumps(
            {
                "component_name": "formalization_gap_planner_resource_response_ledger",
                "n_ledger_rows": 1,
                "rows": [
                    {
                        "resource_response_ledger_id": "resource-response:rank_route",
                        "resource_request_id": "resource-request:rank_route",
                        "goal_plan_id": "goal:rank_route",
                        "route_id": "rank_route",
                        "display_name": "distribution_free_rank_bound",
                        "primitive": "rank_uniformity",
                        "target_primitives": ["rank_uniformity"],
                        "resource_id": "paperclip_mcp",
                        "expected_response_artifact": "source_evidence",
                        "priority_score": 88,
                        "minimal_delta_cost_score": 40,
                        "reuse_readiness_score": 70,
                        "evidence_readiness_score": 90,
                        "priority_rationale": [
                            "coverage_status=bridge_needed",
                            "minimal_delta_cost_score=40",
                            "reuse_readiness_score=70",
                            "evidence_readiness_score=90",
                        ],
                        "acceptance_gate": "source evidence must satisfy queued contract fields",
                        "response_present": True,
                        "response_contract_minimum_met": True,
                        "response_contract_ok": True,
                        "response_summary": (
                            "Paperclip extracted a source-backed finite-rank "
                            "uniformity lemma and identified a tie-breaking "
                            "side condition."
                        ),
                        "response_payload": {
                            "source_snippets": [
                                {
                                    "source_ref": "conformal_prediction_textbook",
                                    "claim": "exchangeability implies rank uniformity after deterministic tie handling",
                                }
                            ],
                            "route_revision_recommended": True,
                        },
                        "response_artifacts": ["paperclip://rank-uniformity"],
                        "source_refs": ["conformal_prediction_textbook"],
                        "request_playbook_present": True,
                        "response_playbook_grounded": True,
                        "response_playbook_grounding_terms": [
                            "rank_uniformity",
                            "tie handling",
                        ],
                        "route_evidence_nodes": [
                            {
                                "node_id": "paperclip:rank_uniformity",
                                "claim": "finite rank uniformity needs deterministic tie handling",
                            }
                        ],
                        "formal_declaration_hits": [
                            {
                                "declaration": "Probability.rankUniformityBridge",
                                "target_prover_family": "lean4",
                                "source_field": "formal_declaration_hits",
                            }
                        ],
                        "coverage_updates": {"rank_uniformity": "bridge_needed"},
                        "residual_goals": [
                            "rank_uniformity: deterministic tie handling"
                        ],
                        "route_revision_recommended": True,
                        "route_revision_reasons": [
                            "add deterministic tie-breaking assumption"
                        ],
                        "acceptance_status": "ACCEPTED_WITH_ROUTE_REVISION",
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return ledger_dir


def _write_source_theorem_planner_feedback(root: Path) -> dict[str, Path]:
    provenance = {"source_theorem_route_id": "rank_route"}
    semantic_bridge_dir = root / "source_theorem_semantic_primitive_bridge"
    semantic_bridge_dir.mkdir(parents=True, exist_ok=True)
    (
        semantic_bridge_dir
        / "source_theorem_semantic_primitive_proofengineer_bridge_manifest.json"
    ).write_text(
        json.dumps(
            {
                "schema_version": 1,
                "artifact_kind": (
                    "SourceTheoremSemanticPrimitiveProofEngineerBridgeManifest"
                ),
                "checks": [
                    {
                        "artifact_kind": "SourceTheoremSemanticPrimitiveBridgeCheck",
                        "work_order_id": "semantic-work:rank_route",
                        "target_theorem_name": "distribution_free_rank_bound",
                        "source_theorem_target_provenance": provenance,
                        "semantic_primitive_id": (
                            "exchangeability_to_uniform_rank_semantics"
                        ),
                        "target_primitives": ["rank_uniformity"],
                        "semantic_primitive_gap": (
                            "formalize exchangeability-to-uniform-rank semantics"
                        ),
                        "candidate_registered_obligation_ids": [
                            "obligation:rank_uniformity_semantics"
                        ],
                        "proof_evidence_status": (
                            "NO_KERNEL_VERIFIED_SOURCE_SEMANTIC_PRIMITIVE_SUPPORT"
                        ),
                        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    semantic_from_executor_dir = (
        root
        / "source_theorem_semantic_primitive_from_proof_body_executor_work_orders"
    )
    semantic_from_executor_dir.mkdir(parents=True, exist_ok=True)
    (
        semantic_from_executor_dir
        / "runtime_source_theorem_semantic_primitive_work_orders_from_proof_body_executor.jsonl"
    ).write_text(
        json.dumps(
            {
                "schema_version": 1,
                "artifact_kind": "SourceTheoremSemanticPrimitiveWorkOrder",
                "work_order_id": "semantic-from-proof-body:rank_route",
                "target_theorem_name": "distribution_free_rank_bound",
                "source_theorem_target_provenance": provenance,
                "semantic_primitive_id": "order_statistic_quantile_semantics",
                "target_primitives": ["rank_uniformity"],
                "semantic_primitive_gap": (
                    "formalize order-statistic quantile semantics"
                ),
                "placeholder_symbol": "OrderStatisticQuantileSemantics",
                "failure_classification": (
                    "formal_environment_placeholder_primitives"
                ),
                "proof_body_goal_excerpt": [
                    "|- rank statistic is uniformly distributed"
                ],
                "proof_evidence_status": "WORK_ORDER_NOT_PROOF_EVIDENCE",
                "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
            }
        )
        + "\n",
        encoding="utf-8",
    )

    formal_environment_dir = root / "source_theorem_formal_environment_bridge"
    formal_environment_dir.mkdir(parents=True, exist_ok=True)
    repair_packets_path = formal_environment_dir / "repair_packets.jsonl"
    repair_packets_path.write_text(
        json.dumps(
            {
                "artifact_kind": "SourceTheoremFormalEnvironmentRepairPacket",
                "work_order_id": "formal-env:rank_route",
                "target_theorem_name": "distribution_free_rank_bound",
                "source_theorem_target_provenance": provenance,
                "target_primitives": ["rank_uniformity"],
                "missing_formal_symbols": ["OrderStatisticQuantileSemantics"],
                "typeclass_blockers": ["DecidableEq score"],
                "formal_environment_typeclass_blockers": ["DecidableEq score"],
                "proof_evidence_status": (
                    "FORMAL_ENVIRONMENT_REPAIR_PACKETS_NOT_PROOF_EVIDENCE"
                ),
                "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (
        formal_environment_dir
        / "source_theorem_formal_environment_proofengineer_bridge_manifest.json"
    ).write_text(
        json.dumps(
            {
                "schema_version": 1,
                "artifact_kind": (
                    "SourceTheoremFormalEnvironmentProofEngineerBridgeManifest"
                ),
                "repair_packets_jsonl": str(repair_packets_path),
                "n_repair_packets": 1,
                "proof_evidence_status": (
                    "FORMAL_ENVIRONMENT_REPAIR_PACKETS_NOT_PROOF_EVIDENCE"
                ),
                "boundary": PROOF_EVIDENCE_BOUNDARY,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    proof_body_executor_dir = root / "exact_source_theorem_proof_body_executor"
    proof_body_executor_dir.mkdir(parents=True, exist_ok=True)
    (
        proof_body_executor_dir
        / "exact_source_theorem_proof_body_execution_result_manifest.json"
    ).write_text(
        json.dumps(
            {
                "schema_version": 1,
                "artifact_kind": "ExactSourceTheoremProofBodyExecutionResult",
                "rows": [
                    {
                        "artifact_kind": (
                            "ExactSourceTheoremProofBodyExecutionResultRow"
                        ),
                        "execution_result_id": "proof-body-result:rank_route",
                        "execution_queue_id": "proof-body-queue:rank_route",
                        "target_theorem_name": "distribution_free_rank_bound",
                        "source_theorem_target_provenance": provenance,
                        "target_primitives": ["rank_uniformity"],
                        "failure_classification": (
                            "formal_environment_placeholder_primitives"
                        ),
                        "formal_environment_placeholder_symbols": [
                            "OrderStatisticQuantileSemantics"
                        ],
                        "candidate_live_proof_state_request": {
                            "proof_body_goal_excerpt": [
                                "|- rank statistic is uniformly distributed"
                            ]
                        },
                        "source_theorem_kernel_verified": False,
                        "proof_evidence_status": (
                            "EXACT_SOURCE_THEOREM_PROOF_BODY_EXECUTION_NOT_PROOF_EVIDENCE"
                        ),
                        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    return {
        "semantic_bridge": semantic_bridge_dir,
        "semantic_from_executor": semantic_from_executor_dir,
        "formal_environment": formal_environment_dir,
        "proof_body_executor": proof_body_executor_dir,
    }


def _write_refinement_evidence(
    root: Path,
    *,
    source_ref: str,
    accepted: bool,
) -> Path:
    evidence_dir = root / (
        "refinement_evidence_accepted" if accepted else "refinement_evidence_rejected"
    )
    evidence_dir.mkdir(parents=True, exist_ok=True)
    status = (
        "REFINEMENT_EVIDENCE_RECORDED_NOT_PROOF_EVIDENCE"
        if accepted
        else "REJECTED_REFINEMENT_EVIDENCE_CONTRACT"
    )
    (
        evidence_dir / "formalization_gap_planner_refinement_evidence_manifest.json"
    ).write_text(
        json.dumps(
            {
                "component_name": "formalization_gap_planner_refinement_evidence",
                "n_evidence_rows": 1,
                "rows": [
                    {
                        "refinement_evidence_id": (
                            "refinement-evidence:rank_route:"
                            + ("accepted" if accepted else "rejected")
                        ),
                        "refinement_item_id": "refinement:rank_route:literature",
                        "goal_plan_id": "goal:rank_route",
                        "route_id": "rank_route",
                        "display_name": "distribution_free_rank_bound",
                        "hook_kind": "literature_discovery",
                        "response_present": True,
                        "response_contract_ok": accepted,
                        "evidence_kind": "literature_route_evidence",
                        "tool_name": "fixture_literature_adapter",
                        "source_refs": [source_ref],
                        "source_snippets": [
                            {
                                "source_ref": source_ref,
                                "claim": "refinement evidence supports finite-rank uniformity",
                                "excerpt": (
                                    "A refinement-evidence snippet states that exchangeability "
                                    "supports finite-rank uniformity once tie handling is fixed."
                                ),
                                "target_primitives": ["rank_uniformity"],
                                "supported_target_primitives": [
                                    "rank_uniformity"
                                ],
                                "unsupported_target_primitives": [],
                                "source_support_status": (
                                    "source_backed_all_target_primitives"
                                ),
                                "evidence_role": "source-backed informal route evidence",
                            }
                        ],
                        "route_evidence_nodes": [
                            {
                                "node_id": "refinement-source:rank_uniformity",
                                "kind": "source_ref",
                                "source_ref": source_ref,
                                "claim": "finite-rank uniformity route evidence",
                                "target_primitives": ["rank_uniformity"],
                                "supported_target_primitives": [
                                    "rank_uniformity"
                                ],
                                "unsupported_target_primitives": [],
                                "source_support_status": (
                                    "source_backed_all_target_primitives"
                                ),
                            }
                        ],
                        "residual_goals": [
                            "rank_uniformity: tie handling side condition from refinement evidence"
                        ],
                        "route_revision_recommended": True,
                        "route_revision_reasons": [
                            "refinement evidence requested deterministic tie handling"
                        ],
                        "acceptance_status": status,
                        "ok": accepted,
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return evidence_dir


def _write_resource_request_queue(root: Path) -> Path:
    queue_dir = root / "resource_request_queue"
    queue_dir.mkdir(parents=True, exist_ok=True)
    (
        queue_dir
        / "formalization_gap_planner_resource_request_queue_manifest.json"
    ).write_text(
        json.dumps(
            {
                "component_name": "formalization_gap_planner_resource_request_queue",
                "schema_version": 3,
                "n_resource_request_rows": 1,
                "n_with_request_playbooks": 1,
                "n_request_playbook_identity_valid": 1,
                "rows": [
                    {
                        "schema_version": 3,
                        "resource_request_id": "resource-request:rank_route",
                        "action_resource_plan_id": "action-resource:rank_route",
                        "primitive_action_id": "primitive-action:rank_route",
                        "coverage_map_id": "coverage-map:rank_route",
                        "goal_plan_id": "goal:rank_route",
                        "route_id": "rank_route",
                        "display_name": "distribution_free_rank_bound",
                        "primitive": "rank_uniformity",
                        "coverage_bucket": "bridge_needed",
                        "queue_action_kind": "literature_grounded_route_synthesis",
                        "target_prover_family": "lean4",
                        "library_snapshot_ref": "lean_mathlib_snapshot",
                        "candidate_declaration_rows": [
                            {
                                "declaration": "Probability.rankUniformityBridge",
                                "target_prover_family": "lean4",
                                "source_field": "resource_request_candidate_declarations",
                            }
                        ],
                        "request_phase": "frontier_escalation",
                        "request_rank": 2,
                        "component_ids": ["literature_grounded_route_synthesis"],
                        "resource_id": "paperclip_cli_mcp",
                        "resource_contract_ids": ["paperclip:source_snippet_contract"],
                        "request_contract_fields": [
                            "target_theorem",
                            "primitive",
                            "source_query",
                        ],
                        "response_contract_fields": [
                            "source_refs",
                            "source_snippets",
                            "route_revision_recommended",
                        ],
                        "request_playbook": {
                            "resource_request_id": "resource-request:rank_route",
                            "resource_id": "paperclip_cli_mcp",
                            "request_phase": "frontier_escalation",
                            "target_prover_family": "lean4",
                            "operator_prompt": (
                                "Use paperclip_cli_mcp to find source-backed rank "
                                "uniformity evidence for the rank_uniformity primitive."
                            ),
                            "input_summary": {
                                "route_id": "rank_route",
                                "display_name": "distribution_free_rank_bound",
                                "primitive": "rank_uniformity",
                                "coverage_bucket": "bridge_needed",
                                "queue_action_kind": (
                                    "literature_grounded_route_synthesis"
                                ),
                                "candidate_declarations": [
                                    "Probability.rankUniformityBridge"
                                ],
                            },
                            "required_inputs": [
                                "target_theorem",
                                "primitive",
                                "source_query",
                            ],
                            "expected_response_fields": [
                                "source_refs",
                                "source_snippets",
                                "route_revision_recommended",
                            ],
                            "expected_response_artifact": "source_evidence",
                            "acceptance_checklist": [
                                "response echoes resource_request_id and resource_id",
                                "response artifact equals source_evidence",
                                (
                                    "response covers required fields: source_refs, "
                                    "source_snippets, route_revision_recommended"
                                ),
                            ],
                            "rejection_triggers": [
                                "local_literature_low_recall",
                                (
                                    "response claims theorem proof evidence without "
                                    "target-prover replay"
                                ),
                            ],
                            "stop_conditions": ["source-backed route node found"],
                            "execution_command": (
                                "paperclip search --query 'rank uniformity exchangeability'"
                            ),
                            "mcp_or_cli_hint": "paperclip_cli_mcp",
                            "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
                        },
                        "expected_response_artifact": "source_evidence",
                        "acceptance_gate": "source_refs_and_snippets_present",
                        "escalation_triggers": ["local_literature_low_recall"],
                        "stop_conditions": ["source-backed route node found"],
                        "execution_command": (
                            "paperclip search --query 'rank uniformity exchangeability'"
                        ),
                        "mcp_or_cli_hint": "paperclip_cli_mcp",
                        "dispatch_spec": {
                            "resource_id": "paperclip_cli_mcp",
                            "surface": "mcp_or_cli",
                            "expected_response_artifact": "source_evidence",
                        },
                        "request_payload": {
                            "resource_request_id": "resource-request:rank_route",
                            "route_id": "rank_route",
                            "primitive": "rank_uniformity",
                            "candidate_declaration_rows": [
                                {
                                    "declaration": "Probability.rankUniformityBridge",
                                    "target_prover_family": "lean4",
                                    "source_field": "resource_request_candidate_declarations",
                                }
                            ],
                            "source_query": "rank uniformity exchangeability",
                            "request_playbook": {
                                "resource_request_id": "resource-request:rank_route",
                                "resource_id": "paperclip_cli_mcp",
                                "request_phase": "frontier_escalation",
                                "target_prover_family": "lean4",
                                "operator_prompt": (
                                    "Use paperclip_cli_mcp to find source-backed rank "
                                    "uniformity evidence for the rank_uniformity primitive."
                                ),
                                "expected_response_fields": [
                                    "source_refs",
                                    "source_snippets",
                                    "route_revision_recommended",
                                ],
                                "acceptance_checklist": [
                                    "response echoes resource_request_id and resource_id",
                                    "response artifact equals source_evidence",
                                ],
                            },
                        },
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return queue_dir


def test_llm_route_planner_default_stages_claude_context_packet_without_api_call() -> None:
    root = Path("runs/test_formalization_gap_planner_llm_route_planner_default_claude")
    out_dir = root / "llm_route_planner"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
    )

    assert payload["all_ok"]
    assert payload["provider_name"] == "anthropic"
    assert payload["invoke_provider"] is False
    assert payload["provider_execution_mode"] == (
        PROVIDER_EXECUTION_MODE_PROMPT_ONLY_STAGED
    )
    assert payload["response_json_supplied"] is False
    assert payload["static_response_json_supplied"] is False
    assert payload["generator_backend_supplied"] is False
    assert payload["live_provider_backend_requested"] is False
    assert payload["provider_generation_requested"] is False
    assert payload["by_request_model_tier"] == {"sonnet": 1}
    assert payload["n_request_packets"] == 1
    assert payload["n_requests_with_context_packet_inventory"] == 1
    assert payload["n_requests_with_route_planning_brief"] == 1
    assert payload["n_request_route_planning_focus_rows"] >= 4
    assert payload["n_request_route_planning_evidence_gaps"] == 0
    assert payload["n_request_route_planning_primitive_evidence_rows"] == 2
    assert payload["n_request_route_planning_source_backed_primitives"] == 1
    assert payload["n_request_route_planning_formal_supported_primitives"] == 1
    assert payload["legacy_context_field_aliases"] == (
        LLM_ROUTE_PLANNER_LEGACY_CONTEXT_FIELD_ALIASES
    )
    assert payload["n_requests_with_legacy_context_field_aliases"] == 1
    assert payload["n_requests_with_available_source_snippets"] == 1
    assert payload["n_request_available_source_snippets"] == 1
    assert payload["n_requests_with_minimal_delta_cost_hints"] == 1
    assert payload["n_request_primitive_cost_hints"] == 2
    assert payload["n_request_route_option_cost_hints"] == 1
    assert payload["n_requests_with_library_alignment_summary"] == 1
    assert payload["n_request_library_alignment_primitives"] == 2
    assert payload["n_request_library_alignment_reuse_ready_primitives"] == 1
    assert payload["n_request_library_alignment_bridge_primitives"] == 1
    assert payload["n_request_library_alignment_bridge_or_harder_primitives"] == 1
    assert (
        payload["n_request_library_alignment_target_compatible_reuse_declarations"]
        >= 1
    )
    assert payload["n_request_library_alignment_route_options"] == 1
    assert payload["n_request_library_alignment_route_option_primitives"] == 2
    assert (
        payload[
            "n_request_library_alignment_route_option_bridge_or_harder_primitives"
        ]
        == 1
    )
    assert (
        payload[
            "n_request_library_alignment_route_option_target_compatible_reuse_declarations"
        ]
        >= 1
    )
    assert (
        payload[
            "total_request_library_alignment_route_option_minimum_base_cost"
        ]
        == 4.0
    )
    assert payload["n_requests_with_route_option_selection_brief"] == 1
    assert payload["n_request_route_option_selection_candidate_options"] == 1
    assert payload["n_request_route_option_selection_candidate_primitives"] == 2
    assert (
        payload[
            "n_request_route_option_selection_candidates_with_residual_goals"
        ]
        == 0
    )
    assert payload["n_request_route_option_selection_candidate_residual_goals"] == 0
    assert payload["n_request_route_option_selection_lower_bound_options"] == 1
    assert payload["n_request_route_option_selection_lower_bound_residual_goals"] == 0
    assert payload["by_request_library_alignment_delta_class"] == {
        "bridge": 1,
        "reuse_ready": 1,
    }
    assert payload["by_request_library_alignment_minimum_coverage_bucket"] == {
        "bridge_needed": 1,
        "exact_exists": 1,
    }
    assert payload["n_response_present"] == 0
    assert payload["n_awaiting_llm_response"] == 1
    assert payload["n_rows_with_primitive_evidence_matrix_witness"] == 1
    assert payload["n_rows_with_complete_primitive_evidence_matrix_accounting"] == 0
    assert payload["n_primitive_evidence_matrix_witness_rows"] == 2
    assert payload["n_primitive_evidence_matrix_unaccounted_primitives"] == 2
    assert (
        payload["n_selected_primitives_without_primitive_evidence_matrix_row"]
        == 0
    )
    assert payload["standalone_replay_gate_ok"] is False
    assert payload["n_standalone_replay_route_candidates"] == 1
    assert payload["n_standalone_replay_adoptable_route_candidates"] == 0
    assert payload["n_standalone_replay_blocked_route_candidates"] == 1
    assert payload["standalone_replay_gate_blockers"] == [
        "llm_route_planner_response_missing"
    ]
    assert payload["standalone_replay_gate"]["gate_status"] == (
        "AWAITING_LLM_ROUTE_PLANNER_RESPONSE"
    )
    assert (
        payload["standalone_replay_gate"][
            "selected_route_adoptable_for_standalone_replay"
        ]
        is False
    )
    assert payload["route_adoption_blocker_counts"] == {
        "llm_route_planner_response_missing": 1
    }
    assert payload[
        "n_route_adoption_pending_primitive_evidence_matrix_blockers"
    ] == 0
    staged_row = payload["rows"][0]
    assert staged_row["primitive_evidence_matrix_witness"][
        "matrix_accounting_complete"
    ] is False
    assert staged_row["primitive_evidence_matrix_witness"][
        "matrix_unaccounted_primitives"
    ] == ["exchangeability", "rank_uniformity"]
    assert payload["by_route_adoption_blocker"][
        "llm_route_planner_response_missing"
    ]["by_route_adoption_status"] == {
        "AWAITING_LLM_ROUTE_PLANNER_RESPONSE": 1
    }
    assert payload["n_request_schema_valid"] == 1
    assert payload["n_requests_with_llm_generation_policy"] == 1
    assert payload["n_request_llm_generation_policy_tier_model_matches"] == 1
    assert payload["n_request_llm_generation_policy_codex_exclusions"] == 1
    assert payload[
        "n_request_llm_generation_policy_current_claude_tier_source"
    ] == 1
    assert payload["request_schema"]["$id"] == LLM_ROUTE_PLANNER_REQUEST_SCHEMA_ID
    assert "llm_generation_policy" in payload["request_schema"]["required"]
    alignment_schema = llm_route_planner_library_alignment_summary_json_schema()
    assert (
        alignment_schema["$id"]
        == LLM_ROUTE_PLANNER_LIBRARY_ALIGNMENT_SUMMARY_SCHEMA_ID
    )
    assert payload["request_schema"]["$defs"]["library_alignment_summary"][
        "$id"
    ] == LLM_ROUTE_PLANNER_LIBRARY_ALIGNMENT_SUMMARY_SCHEMA_ID
    route_planning_brief_schema = llm_route_planner_route_planning_brief_json_schema()
    assert (
        route_planning_brief_schema["$id"]
        == LLM_ROUTE_PLANNER_ROUTE_PLANNING_BRIEF_SCHEMA_ID
    )
    assert payload["request_schema"]["$defs"]["route_planning_brief"][
        "$id"
    ] == LLM_ROUTE_PLANNER_ROUTE_PLANNING_BRIEF_SCHEMA_ID
    assert "library_alignment_summary" in payload["request_schema"]["properties"][
        "context_packet"
    ]["required"]
    assert "route_planning_brief" in payload["request_schema"]["properties"][
        "context_packet"
    ]["required"]
    assert (
        out_dir
        / "formalization_gap_planner_llm_route_planner_library_alignment_summary.schema.json"
    ).exists()
    route_planning_brief_schema_path = (
        out_dir
        / "formalization_gap_planner_llm_route_planner_route_planning_brief.schema.json"
    )
    assert route_planning_brief_schema_path.exists()
    assert (
        json.loads(route_planning_brief_schema_path.read_text(encoding="utf-8"))
        == route_planning_brief_schema
    )
    library_alignment_summary_rows = [
        json.loads(line)
        for line in (
            out_dir
            / "formalization_gap_planner_llm_route_planner_library_alignment_summaries.jsonl"
        )
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    assert len(library_alignment_summary_rows) == 1
    route_planning_brief_rows = [
        json.loads(line)
        for line in (
            out_dir
            / "formalization_gap_planner_llm_route_planner_route_planning_briefs.jsonl"
        )
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    assert tuple(route_planning_brief_rows) == payload["route_planning_briefs"]
    assert payload["n_route_planning_briefs"] == 1
    request = payload["request_packets"][0]
    target_context_schema = (
        llm_route_planner_target_theorem_context_packet_json_schema()
    )
    assert (
        target_context_schema["$id"]
        == LLM_ROUTE_PLANNER_TARGET_THEOREM_CONTEXT_PACKET_SCHEMA_ID
    )
    target_context_schema_path = (
        out_dir
        / "formalization_gap_planner_llm_route_planner_target_theorem_context_packet.schema.json"
    )
    assert target_context_schema_path.exists()
    assert (
        json.loads(target_context_schema_path.read_text(encoding="utf-8"))
        == target_context_schema
    )
    target_context_packet_rows = [
        json.loads(line)
        for line in (
            out_dir
            / "formalization_gap_planner_llm_route_planner_target_theorem_context_packets.jsonl"
        )
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    assert tuple(target_context_packet_rows) == payload["target_theorem_context_packets"]
    assert payload["n_target_theorem_context_packets"] == 1
    ledger_schema = llm_route_planner_model_tier_decision_ledger_json_schema()
    assert (
        ledger_schema["$id"]
        == LLM_ROUTE_PLANNER_MODEL_TIER_DECISION_LEDGER_SCHEMA_ID
    )
    assert (
        out_dir
        / "formalization_gap_planner_llm_route_planner_model_tier_decision_ledger.schema.json"
    ).exists()
    ledger_rows = [
        json.loads(line)
        for line in (
            out_dir
            / "formalization_gap_planner_llm_route_planner_model_tier_decision_ledger.jsonl"
        )
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    assert ledger_rows == list(payload["model_tier_decision_ledger"])
    assert payload["n_model_tier_decision_ledger_rows"] == 1
    assert payload["n_model_tier_decision_ledger_rows_with_escalation"] == 0
    ledger_row = ledger_rows[0]
    assert ledger_row["request_id"] == request["request_id"]
    assert ledger_row["operator_requested_model_tier"] == "auto"
    assert ledger_row["selected_model_tier"] == request["model_tier"]
    assert ledger_row["effective_model_tier"] == request["model_tier"]
    assert ledger_row["decision_basis"] == "auto_sonnet_triggers"
    assert ledger_row["route_signal_counts"] == request[
        "model_tier_decision_evidence"
    ]["route_signal_counts"]
    assert ledger_row["context_resource_dispatch_counts"] == request[
        "model_tier_decision_evidence"
    ]["context_resource_dispatch_counts"]
    assert ledger_row["interactive_route_adoption_precondition_counts"] == request[
        "model_tier_decision_evidence"
    ]["interactive_route_adoption_precondition_counts"]
    assert ledger_row["source_grounding_obligations"] == request[
        "model_tier_decision_evidence"
    ]["source_grounding_obligations"]
    assert ledger_row["response_present"] is False
    assert ledger_row["provider_failure"] is False
    assert ledger_row["proof_evidence_status"] == (
        "FORMALIZATION_GAP_PLANNER_LLM_ROUTE_PLANNER_NOT_PROOF_EVIDENCE"
    )
    assert "LLM route planner" in request["prompt_messages"]["system"]
    assert "required_output_contract" in request["prompt_messages"]["user"]
    assert request["minimal_delta_cost_policy"]["cost_policy_id"] == (
        "formalization_gap_planner_minimal_delta_cost_policy:1"
    )
    assert "minimal_delta_cost_policy" in request["prompt_messages"]["user"]
    assert "primitive_costs" in request["prompt_messages"]["user"]
    context = request["context_packet"]
    assert context["current_route"]["route_id"] == "rank_route"
    target_context_packet = context["target_theorem_context_packet"]
    route_planning_brief = context["route_planning_brief"]
    assert target_context_packet["context_packet_kind"] == (
        TARGET_THEOREM_CONTEXT_PACKET_KIND
    )
    assert target_context_packet["route_id"] == "rank_route"
    assert target_context_packet["target_prover_family"] == "lean4"
    assert target_context_packet["theorem_statement"] == (
        "A distribution-free rank bound follows from exchangeability."
    )
    assert target_context_packet["primitive_candidates"] == [
        "exchangeability",
        "rank_uniformity",
    ]
    assert target_context_packet["proof_source_refs"] == [
        "conformal_prediction_textbook"
    ]
    assert payload["target_theorem_context_packets"] == (target_context_packet,)
    assert target_context_packet_rows == [target_context_packet]
    assert payload["rows"][0]["target_theorem_context_packet"] == target_context_packet
    assert payload["rows"][0]["route_planning_brief"] == route_planning_brief
    fallback_seed_route = payload["standalone_seed"]["routes"][0]
    assert fallback_seed_route["target_theorem_context_packet"] == (
        target_context_packet
    )
    assert fallback_seed_route["llm_route_planner_route_planning_brief"] == (
        route_planning_brief
    )
    assert fallback_seed_route["replan_metadata"][
        "target_theorem_context_packet"
    ] == target_context_packet
    assert fallback_seed_route["replan_metadata"][
        "llm_route_planner_target_theorem_context_packet"
    ] == target_context_packet
    assert fallback_seed_route["replan_metadata"][
        "llm_route_planner_route_planning_brief"
    ] == route_planning_brief
    brief = context["route_planning_brief"]
    assert brief["brief_kind"] == (
        "formalization_gap_planner_llm_route_planner_route_planning_brief"
    )
    assert brief["route_id"] == "rank_route"
    assert brief["target_prover_family"] == "lean4"
    assert brief["target_context"]["context_packet_kind"] == (
        TARGET_THEOREM_CONTEXT_PACKET_KIND
    )
    assert brief["target_context"]["primitive_candidates"] == [
        "exchangeability",
        "rank_uniformity",
    ]
    assert brief["evidence_summary"]["source_ref_count"] == len(
        context["available_source_refs"]
    )
    assert brief["evidence_summary"]["formal_declaration_row_count"] == len(
        context["available_formal_declaration_rows"]
    )
    assert brief["evidence_summary"]["primitive_evidence_row_count"] == 2
    assert brief["evidence_summary"]["primitive_source_backed_count"] == 1
    assert brief["evidence_summary"]["primitive_formal_supported_count"] == 1
    assert brief["evidence_summary"]["primitive_needing_source_search_count"] == 1
    assert brief["evidence_summary"]["primitive_needing_formal_delta_count"] == 1
    primitive_evidence_by_primitive = {
        row["primitive"]: row for row in brief["primitive_evidence_matrix"]
    }
    assert set(primitive_evidence_by_primitive) == {
        "exchangeability",
        "rank_uniformity",
    }
    exchangeability_evidence = primitive_evidence_by_primitive["exchangeability"]
    assert exchangeability_evidence["formal_support_status"] == (
        "existing_library_reuse_ready"
    )
    assert exchangeability_evidence["source_support_status"] == (
        "source_search_pending"
    )
    assert "Probability.exchangeable" in set(
        exchangeability_evidence["target_compatible_declarations"]
    )
    assert "reuse_target_compatible_declarations" in set(
        exchangeability_evidence["recommended_planner_actions"]
    )
    rank_evidence = primitive_evidence_by_primitive["rank_uniformity"]
    assert rank_evidence["source_support_status"] == "source_backed"
    assert rank_evidence["formal_support_status"] == "bridge_needed"
    assert rank_evidence["library_delta_class"] == "bridge"
    assert rank_evidence["minimum_base_cost"] == 4.0
    assert rank_evidence["source_refs"] == ["conformal_prediction_textbook"]
    assert rank_evidence["source_snippet_count"] == 1
    assert "plan_minimal_formal_delta" in set(
        rank_evidence["recommended_planner_actions"]
    )
    assert {
        focus["focus_id"] for focus in brief["planner_focus"]
    } >= {
        "preserve_target_theorem_identity",
        "synthesize_source_grounded_informal_route",
        "map_formal_library_coverage",
        "minimize_formalization_delta",
    }
    assert brief["evidence_gaps"] == []
    inventory = context["context_packet_inventory"]
    assert inventory["inventory_kind"] == (
        "formalization_gap_planner_llm_route_planner_context_packet_inventory"
    )
    assert inventory["proof_evidence_boundary"] == PROOF_EVIDENCE_BOUNDARY
    assert payload["n_request_context_inventory_total_rows"] == inventory[
        "total_context_rows"
    ]
    assert inventory["row_counts"]["target_intake_rows"] == len(
        context["target_intake_rows"]
    )
    assert inventory["row_counts"]["library_coverage_rows"] == len(
        context["library_coverage_rows"]
    )
    assert inventory["available_source_snippet_count"] == len(
        context["available_source_snippets"]
    )
    assert inventory["resource_request_playbook_count"] == 0
    assert inventory["legacy_context_field_alias_count"] == len(
        LLM_ROUTE_PLANNER_LEGACY_CONTEXT_FIELD_ALIASES
    )
    assert inventory["route_planning_brief_present"] is True
    assert inventory["route_planning_brief_focus_count"] == len(
        brief["planner_focus"]
    )
    assert inventory["route_planning_brief_evidence_gap_count"] == len(
        brief["evidence_gaps"]
    )
    assert inventory["route_planning_brief_primitive_evidence_row_count"] == len(
        brief["primitive_evidence_matrix"]
    )
    assert inventory["primitive_cost_hint_count"] == 2
    assert inventory["route_option_cost_hint_count"] == 1
    assert inventory["library_alignment_summary_present"] is True
    assert inventory["library_alignment_primitive_count"] == 2
    assert inventory["library_alignment_reuse_ready_count"] == 1
    assert inventory["library_alignment_bridge_count"] == 1
    assert inventory["library_alignment_bridge_or_harder_count"] == 1
    assert inventory["route_option_selection_brief_present"] is True
    assert inventory["route_option_selection_candidate_count"] == 1
    assert inventory["route_option_selection_candidate_primitive_count"] == 2
    assert inventory["route_option_selection_lower_bound_selected"] is True
    assert inventory["feedback_loop_summary_present"] is bool(
        context["feedback_loop_summary"]
    )
    assert "conformal_prediction_textbook" in set(
        context["available_source_refs"]
    )
    assert context["available_source_snippets"][0][
        "source_ref"
    ] == "conformal_prediction_textbook"
    assert "Exchangeability implies a uniform rank statistic" in context[
        "available_source_snippets"
    ][0]["claim"]
    assert "Probability.exchangeable" in set(
        context["available_formal_declarations"]
    )
    declaration_rows = context["available_formal_declaration_rows"]
    assert inventory["available_formal_declaration_row_count"] == len(
        declaration_rows
    )
    assert inventory["target_theorem_context_packet_present"] is True
    assert inventory["target_theorem_context_object_count"] == 0
    assert inventory["target_theorem_context_assumption_count"] == 0
    assert inventory["target_theorem_context_procedure_count"] == 0
    assert inventory["target_theorem_context_desired_conclusion_count"] == 0
    assert inventory["target_theorem_context_proof_style_hint_count"] == 0
    assert {
        (row["declaration"], row["target_prover_family"]) for row in declaration_rows
    } >= {("Probability.exchangeable", "lean4")}
    cost_hints = context["minimal_delta_cost_hints"]
    assert cost_hints["cost_policy_id"] == (
        "formalization_gap_planner_minimal_delta_cost_policy:1"
    )
    cost_by_primitive = {
        row["primitive"]: row for row in cost_hints["primitive_cost_hints"]
    }
    assert cost_by_primitive["exchangeability"]["minimum_base_cost"] == 0.0
    assert cost_by_primitive["rank_uniformity"]["minimum_base_cost"] == 4.0
    assert cost_by_primitive["rank_uniformity"][
        "minimum_coverage_bucket"
    ] == "bridge_needed"
    assert cost_hints["route_option_hints"][0]["minimum_route_base_cost"] == 4.0
    alignment_summary = context["library_alignment_summary"]
    assert library_alignment_summary_rows[0] == alignment_summary
    assert alignment_summary["schema_version"] == 1
    assert (
        alignment_summary["schema_id"]
        == LLM_ROUTE_PLANNER_LIBRARY_ALIGNMENT_SUMMARY_SCHEMA_ID
    )
    assert alignment_summary["summary_kind"] == (
        "formalization_gap_planner_llm_route_planner_library_alignment_summary"
    )
    assert alignment_summary["route_id"] == "rank_route"
    assert alignment_summary["display_name"] == "distribution_free_rank_bound"
    assert alignment_summary["n_primitives"] == 2
    assert alignment_summary["n_reuse_ready_primitives"] == 1
    assert alignment_summary["n_bridge_primitives"] == 1
    assert alignment_summary["n_bridge_or_harder_primitives"] == 1
    assert alignment_summary["n_route_options"] == 1
    route_option_alignment = alignment_summary["route_option_alignment"][0]
    assert route_option_alignment["route_option_id"] == (
        "route_option:current_route_min_delta_baseline"
    )
    assert route_option_alignment["selected_primitives"] == [
        "exchangeability",
        "rank_uniformity",
    ]
    assert route_option_alignment["minimum_route_base_cost"] == 4.0
    assert route_option_alignment["n_bridge_or_harder_primitives"] == 1
    assert route_option_alignment["by_library_delta_class"] == {
        "bridge": 1,
        "reuse_ready": 1,
    }
    route_option_brief = context["route_option_selection_brief"]
    assert route_option_brief["brief_kind"] == (
        "formalization_gap_planner_llm_route_planner_route_option_selection_brief"
    )
    assert route_option_brief["route_id"] == "rank_route"
    assert route_option_brief["cost_policy_id"] == (
        "formalization_gap_planner_minimal_delta_cost_policy:1"
    )
    assert route_option_brief["n_candidate_route_options"] == 1
    assert route_option_brief["n_candidate_route_option_primitives"] == 2
    assert route_option_brief["lower_bound_selected_route_option_id"] == (
        "route_option:current_route_min_delta_baseline"
    )
    assert route_option_brief["lower_bound_selected_route_cost"] == 4.0
    assert route_option_brief["candidate_route_options"][0][
        "selected_by_lower_bound_policy"
    ] is True
    assert route_option_brief["candidate_route_options"][0][
        "selected_primitives"
    ] == ["exchangeability", "rank_uniformity"]
    assert route_option_brief["candidate_route_options"][0][
        "by_library_delta_class"
    ] == {"bridge": 1, "reuse_ready": 1}
    assert route_option_brief["candidate_route_options"][0]["n_residual_goals"] == 0
    assert (
        route_option_brief["n_candidate_route_options_with_residual_goals"]
        == 0
    )
    assert route_option_brief["n_candidate_route_option_residual_goals"] == 0
    assert route_option_brief["lower_bound_selected_residual_goal_count"] == 0
    alignment_by_primitive = {
        row["primitive"]: row for row in alignment_summary["primitive_alignment"]
    }
    assert alignment_by_primitive["exchangeability"]["library_delta_class"] == (
        "reuse_ready"
    )
    assert alignment_by_primitive["rank_uniformity"]["library_delta_class"] == (
        "bridge"
    )
    assert "Probability.exchangeable" in set(
        alignment_by_primitive["exchangeability"][
            "target_compatible_declarations"
        ]
    )
    assert "available_source_refs" in request["prompt_messages"]["user"]
    assert "available_source_snippets" in request["prompt_messages"]["user"]
    assert "available_formal_declarations" in request["prompt_messages"]["user"]
    assert context["legacy_context_field_aliases"] == (
        LLM_ROUTE_PLANNER_LEGACY_CONTEXT_FIELD_ALIASES
    )
    assert "legacy_context_field_aliases" in request["prompt_messages"]["user"]
    assert "prefer portable fields" in request["prompt_messages"]["user"]
    assert "minimal_delta_cost_hints" in request["prompt_messages"]["user"]
    assert "library_alignment_summary" in request["prompt_messages"]["user"]
    assert "route_option_selection_brief" in request["prompt_messages"]["user"]
    assert "minimum_base_cost" in request["prompt_messages"]["user"]
    assert "context_packet_inventory" in request["prompt_messages"]["user"]
    assert "route_planning_brief" in request["prompt_messages"]["user"]
    assert "primitive_evidence_matrix" in request["prompt_messages"]["user"]
    assert (
        out_dir
        / "formalization_gap_planner_llm_route_planner_manifest.json"
    ).exists()
    assert (
        out_dir / "formalization_gap_planner_llm_route_planner_requests.jsonl"
    ).exists()
    assert request["provider_name"] == "anthropic"
    assert request["model"] == "claude-sonnet-4-6"
    assert request["model_tier"] == "sonnet"
    generation_policy = request["llm_generation_policy"]
    assert generation_policy["policy_kind"] == (
        "request_scoped_generator_only_llm_policy"
    )
    assert generation_policy["provider_name"] == "anthropic"
    assert generation_policy["resolved_model"] == request["model"]
    assert generation_policy["selected_model_tier"] == request["model_tier"]
    assert generation_policy["requested_model_tier"] == "auto"
    assert generation_policy["claude_models_by_tier"] == {
        "haiku": "claude-haiku-4-5-20251001",
        "sonnet": "claude-sonnet-4-6",
        "opus": "claude-opus-4-8",
    }
    assert "not evergreen aliases" in generation_policy["claude_model_id_versioning"]
    assert {
        "codex",
        "codex_exec",
        "claude_code",
        "cursor",
        "gemini_cli",
    }.issubset(
        set(generation_policy["prohibited_generator_providers"])
    )
    assert {
        "codex",
        "codex_exec",
        "claude_code",
        "cursor",
        "gemini_cli",
    }.isdisjoint(
        set(generation_policy["supported_live_generator_providers"])
    )
    assert any(
        "source-grounding" in rule.lower() and "sonnet" in rule.lower()
        for rule in generation_policy["auto_tier_rules"]
    )
    assert generation_policy["proof_evidence_status"] == (
        "FORMALIZATION_GAP_PLANNER_LLM_ROUTE_PLANNER_NOT_PROOF_EVIDENCE"
    )
    assert validate_llm_route_planner_request(request) == []
    drifted_inventory_request = deepcopy(request)
    drifted_inventory_request["context_packet"]["context_packet_inventory"][
        "available_source_snippet_count"
    ] = 999
    assert (
        "context_packet.context_packet_inventory.available_source_snippet_count "
        "must match context_packet"
        in validate_llm_route_planner_request(drifted_inventory_request)
    )
    drifted_brief_request = deepcopy(request)
    drifted_brief_request["context_packet"]["route_planning_brief"][
        "evidence_summary"
    ]["source_ref_count"] = 999
    assert (
        "context_packet.route_planning_brief.evidence_summary.source_ref_count "
        "must match context_packet"
        in validate_llm_route_planner_request(drifted_brief_request)
    )
    drifted_matrix_inventory_request = deepcopy(request)
    drifted_matrix_inventory_request["context_packet"]["context_packet_inventory"][
        "route_planning_brief_primitive_evidence_row_count"
    ] = 999
    assert (
        "context_packet.context_packet_inventory."
        "route_planning_brief_primitive_evidence_row_count must match "
        "context_packet.route_planning_brief"
        in validate_llm_route_planner_request(drifted_matrix_inventory_request)
    )
    drifted_matrix_summary_request = deepcopy(request)
    drifted_matrix_summary_request["context_packet"]["route_planning_brief"][
        "evidence_summary"
    ]["primitive_evidence_row_count"] = 999
    assert (
        "context_packet.route_planning_brief.evidence_summary."
        "primitive_evidence_row_count must match "
        "context_packet.route_planning_brief.primitive_evidence_matrix"
        in validate_llm_route_planner_request(drifted_matrix_summary_request)
    )
    drifted_route_option_request = deepcopy(request)
    drifted_route_option_request["context_packet"]["route_option_selection_brief"][
        "n_candidate_route_options"
    ] = 999
    assert (
        "context_packet.route_option_selection_brief.n_candidate_route_options "
        "must match context_packet.library_alignment_summary"
        in validate_llm_route_planner_request(drifted_route_option_request)
    )
    drifted_route_option_inventory_request = deepcopy(request)
    drifted_route_option_inventory_request["context_packet"][
        "context_packet_inventory"
    ]["route_option_selection_candidate_count"] = 999
    assert (
        "context_packet.context_packet_inventory."
        "route_option_selection_candidate_count must match "
        "context_packet.route_option_selection_brief"
        in validate_llm_route_planner_request(
            drifted_route_option_inventory_request
        )
    )
    drifted_target_context_request = deepcopy(request)
    drifted_target_context_request["context_packet"][
        "target_theorem_context_packet"
    ]["route_id"] = "wrong_route"
    assert (
        "context_packet.target_theorem_context_packet.route_id must match request route_id"
        in validate_llm_route_planner_request(drifted_target_context_request)
    )
    drifted_target_context_statement_request = deepcopy(request)
    drifted_target_context_statement_request["context_packet"][
        "target_theorem_context_packet"
    ]["theorem_statement"] = (
        "A central limit theorem for independent sample means follows from "
        "Lindeberg conditions."
    )
    assert (
        "context_packet.target_theorem_context_packet.theorem_statement "
        "must match request route or target-intake theorem statement"
        in validate_llm_route_planner_request(
            drifted_target_context_statement_request
        )
    )
    drifted_target_context_inventory_request = deepcopy(request)
    drifted_target_context_inventory_request["context_packet"][
        "context_packet_inventory"
    ]["target_theorem_context_proof_style_hint_count"] = 999
    assert (
        "context_packet.context_packet_inventory."
        "target_theorem_context_proof_style_hint_count must match "
        "target_theorem_context_packet"
        in validate_llm_route_planner_request(
            drifted_target_context_inventory_request
        )
    )
    drifted_alias_request = deepcopy(request)
    drifted_alias_request["context_packet"]["legacy_context_field_aliases"] = {}
    assert (
        "context_packet.legacy_context_field_aliases must match planner legacy "
        "context alias contract for target_prover_family"
        in validate_llm_route_planner_request(drifted_alias_request)
    )
    drifted_request = dict(request)
    drifted_request["llm_generation_policy"] = {
        **generation_policy,
        "resolved_model": "claude-haiku-4-5-20251001",
    }
    assert (
        "llm_generation_policy.resolved_model must match model"
        in validate_llm_route_planner_request(drifted_request)
    )
    stale_auto_rule_request = deepcopy(request)
    stale_auto_rule_request["llm_generation_policy"]["auto_tier_rules"] = [
        rule
        for rule in generation_policy["auto_tier_rules"]
        if "source-grounding" not in rule.lower()
    ]
    assert (
        "llm_generation_policy.auto_tier_rules must route pending "
        "source-grounding obligations to Sonnet"
        in validate_llm_route_planner_request(stale_auto_rule_request)
    )
    stale_tier_policy_request = deepcopy(request)
    stale_tier_policy_request["llm_generation_policy"]["claude_models_by_tier"][
        "sonnet"
    ] = "claude-sonnet-4-5"
    assert (
        "llm_generation_policy.claude_models_by_tier must match current "
        "Claude tier policy"
        in validate_llm_route_planner_request(stale_tier_policy_request)
    )
    stale_source_date_request = deepcopy(request)
    stale_source_date_request["llm_generation_policy"][
        "claude_model_source_checked_date"
    ] = "2026-01-01"
    assert (
        "llm_generation_policy.claude_model_source_checked_date must match "
        "current Claude tier policy source_checked_date"
        in validate_llm_route_planner_request(stale_source_date_request)
    )
    stale_source_evidence_request = deepcopy(request)
    stale_source_evidence_request["llm_generation_policy"][
        "claude_model_selection"
    ]["source_evidence"]["verified_latest_cost_tier_api_ids"][
        "haiku"
    ] = "claude-haiku-4-5"
    assert (
        "llm_generation_policy.claude_model_selection.source_evidence."
        "verified_latest_cost_tier_api_ids must match current Claude tier policy"
        in validate_llm_route_planner_request(stale_source_evidence_request)
    )


def test_llm_route_planner_stages_agentic_proof_execution_feedback() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_proof_execution_feedback"
    )
    out_dir = root / "llm_route_planner"
    materializer_dir = root / "materializer"
    artifact_verifier_dir = root / "artifact_verifier"
    source_promotion_dir = root / "source_theorem_promotion"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    for directory in (materializer_dir, artifact_verifier_dir, source_promotion_dir):
        directory.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    input_payload = json.loads(input_json.read_text(encoding="utf-8"))
    input_payload["target_prover_family"] = "rocq"
    input_payload["routes"][0]["target_prover_family"] = "rocq"
    input_json.write_text(json.dumps(input_payload, indent=2), encoding="utf-8")
    provenance = {
        "source_route_id": "rank_route",
        "target_prover_family": "rocq",
    }
    common_row = {
        "schema_version": 1,
        "execution_queue_id": "agentic-proof-execution:rank_route",
        "display_name": "distribution_free_rank_bound",
        "target_theorem_name": "distribution_free_rank_bound",
        "target_prover_family": "rocq",
        "formal_statement_sketch": "Theorem distribution_free_rank_bound : True.",
        "formal_imports": ["Coq.Init.Logic"],
        "candidate_artifact_path": "",
        "target_lean_declaration": "",
        "source_theorem_target_known": False,
        "source_theorem_target_provenance": provenance,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
        "ok": True,
        "errors": [],
    }
    (
        materializer_dir
        / "formal_verifier_agentic_proof_execution_materializer_manifest.json"
    ).write_text(
        json.dumps(
            {
                "n_materializer_rows": 1,
                "n_unsupported_target_prover_rows": 1,
                "by_target_prover_family": {"rocq": 1},
                "rows": [
                    {
                        **common_row,
                        "materialization_id": "materialization:rank_route",
                        "materialization_status": (
                            "UNSUPPORTED_TARGET_PROVER_FOR_LEAN_MATERIALIZER"
                        ),
                        "proof_evidence_status": (
                            "AGENTIC_PROOF_EXECUTION_MATERIALIZER_NOT_PROOF_EVIDENCE"
                        ),
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (
        artifact_verifier_dir
        / "formal_verifier_agentic_proof_execution_artifact_verifier_manifest.json"
    ).write_text(
        json.dumps(
            {
                "n_verifier_rows": 1,
                "n_unsupported_target_prover_rows": 1,
                "by_target_prover_family": {"rocq": 1},
                "rows": [
                    {
                        **common_row,
                        "artifact_verification_id": (
                            "artifact-verification:rank_route"
                        ),
                        "materialization_id": "materialization:rank_route",
                        "materialization_status": (
                            "UNSUPPORTED_TARGET_PROVER_FOR_LEAN_MATERIALIZER"
                        ),
                        "verification_status": (
                            "UNSUPPORTED_TARGET_PROVER_FOR_LEAN_ARTIFACT_VERIFIER"
                        ),
                        "artifact_kernel_verified": False,
                        "source_theorem_kernel_verified": False,
                        "local_lean_checked": False,
                        "local_lean_compiled": False,
                        "proof_evidence_status": (
                            "AGENTIC_ARTIFACT_KERNEL_CHECK_NOT_SOURCE_THEOREM_PROOF"
                        ),
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (
        source_promotion_dir
        / "formal_verifier_agentic_proof_source_theorem_promotion_queue_manifest.json"
    ).write_text(
        json.dumps(
            {
                "n_promotion_rows": 1,
                "n_unsupported_target_prover_rows": 1,
                "by_target_prover_family": {"rocq": 1},
                "rows": [
                    {
                        **common_row,
                        "source_theorem_promotion_id": (
                            "source-theorem-promotion:rank_route"
                        ),
                        "artifact_verification_id": (
                            "artifact-verification:rank_route"
                        ),
                        "materialization_id": "materialization:rank_route",
                        "source_verification_status": (
                            "UNSUPPORTED_TARGET_PROVER_FOR_LEAN_ARTIFACT_VERIFIER"
                        ),
                        "promotion_status": (
                            "UNSUPPORTED_TARGET_PROVER_FOR_SOURCE_THEOREM_PROMOTION_QUEUE"
                        ),
                        "artifact_kernel_verified": False,
                        "source_theorem_kernel_verified": False,
                        "owner_agent": "formal_verifier_source_theorem_integrator",
                        "action_type": "dispatch_compatible_target_prover_adapter",
                        "required_gate": "compatible Rocq proof replay",
                        "required_inputs": ["rocq_statement", "rocq_adapter"],
                        "command_plan": ["dispatch Rocq adapter before promotion"],
                        "proof_evidence_status": (
                            "SOURCE_THEOREM_PROMOTION_QUEUE_NOT_PROOF_EVIDENCE"
                        ),
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        formal_verifier_agentic_proof_execution_materializer_dir=materializer_dir,
        formal_verifier_agentic_proof_execution_artifact_verifier_dir=(
            artifact_verifier_dir
        ),
        formal_verifier_agentic_proof_source_theorem_promotion_queue_dir=(
            source_promotion_dir
        ),
    )

    assert payload["all_ok"]
    assert payload["n_request_agentic_proof_execution_materializer_rows"] == 1
    assert payload["n_request_agentic_proof_execution_artifact_verifier_rows"] == 1
    assert payload["n_request_agentic_proof_source_theorem_promotion_rows"] == 1
    assert payload["n_requests_with_proof_execution_feedback_summary"] == 1
    assert payload["n_request_proof_execution_feedback_rows"] == 3
    assert payload["n_request_proof_execution_unsupported_target_prover_rows"] == 3
    request = payload["request_packets"][0]
    context = request["context_packet"]
    assert context["target_prover_family"] == "rocq"
    assert context["agentic_proof_execution_materializer_rows"][0][
        "materialization_status"
    ] == "UNSUPPORTED_TARGET_PROVER_FOR_LEAN_MATERIALIZER"
    assert context["agentic_proof_execution_artifact_verifier_rows"][0][
        "verification_status"
    ] == "UNSUPPORTED_TARGET_PROVER_FOR_LEAN_ARTIFACT_VERIFIER"
    assert context["agentic_proof_source_theorem_promotion_rows"][0][
        "promotion_status"
    ] == "UNSUPPORTED_TARGET_PROVER_FOR_SOURCE_THEOREM_PROMOTION_QUEUE"
    assert context["agentic_proof_execution_materializer_rows"][0][
        "formal_imports"
    ] == ["Coq.Init.Logic"]
    proof_execution_summary = context["proof_execution_feedback_summary"]
    assert proof_execution_summary["total_rows"] == 3
    assert proof_execution_summary["unsupported_target_prover_rows"] == 3
    assert proof_execution_summary["by_target_prover_family"] == {"rocq": 3}
    assert proof_execution_summary["by_stage"]["materializer"][
        "unsupported_target_prover_rows"
    ] == 1
    assert proof_execution_summary["by_stage"]["artifact_verifier"][
        "unsupported_target_prover_rows"
    ] == 1
    assert proof_execution_summary["by_stage"]["source_theorem_promotion"][
        "unsupported_target_prover_rows"
    ] == 1
    inventory = context["context_packet_inventory"]
    assert inventory["row_counts"]["agentic_proof_execution_materializer_rows"] == 1
    assert inventory["row_counts"][
        "agentic_proof_execution_artifact_verifier_rows"
    ] == 1
    assert inventory["row_counts"][
        "agentic_proof_source_theorem_promotion_rows"
    ] == 1
    assert inventory["proof_execution_feedback_summary_present"] is True
    assert inventory["proof_execution_feedback_row_count"] == 3
    assert inventory["proof_execution_feedback_unsupported_target_prover_count"] == 3
    brief = context["route_planning_brief"]
    assert brief["proof_execution_feedback_summary"] == proof_execution_summary
    assert brief["evidence_summary"]["proof_execution_feedback_row_count"] == 3
    assert brief["evidence_summary"][
        "proof_execution_feedback_unsupported_target_prover_count"
    ] == 3
    report = (out_dir / "formalization_gap_planner_llm_route_planner.md").read_text(
        encoding="utf-8"
    )
    assert "Agentic proof execution context rows" in report
    assert "Proof execution unsupported target-prover rows: 3" in report


def test_llm_route_planner_stages_patch_rerun_residual_obligations() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_patch_rerun_residual_obligations"
    )
    out_dir = root / "llm_route_planner"
    residual_obligations_dir = root / "residual_obligations"
    shutil.rmtree(root, ignore_errors=True)
    residual_obligations_dir.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    rows = [
        {
            "schema_version": 1,
            "residual_obligation_id": "residual-obligation:rank_route:exchangeability",
            "rerun_calibration_id": "rerun-calibration:rank_route",
            "rerun_id": "patch-rerun:rank_route",
            "rerun_attempt_id": "patch-rerun-attempt:rank_route",
            "replay_id": "replay:rank_route",
            "route_id": "rank_route",
            "display_name": "distribution_free_rank_bound",
            "target_theorem_name": "distribution_free_rank_bound",
            "candidate_bridge_lemma_name": "rank_uniformity_bridge",
            "patched_artifact_path": "patched/Rank.lean",
            "patch_rerun_calibration_status": "residual_formal_gaps_remain",
            "residual_gap": "exchangeability",
            "residual_kind": "residual_formal_gap",
            "source_support_classification": "exact_source_supported",
            "action_class": "reuse_exact_proof_bank_obligation",
            "action_type": "reuse_exact_proof_bank_obligation",
            "proof_bank_action_id": "proof-bank-action:exchangeability",
            "priority": "high",
            "priority_rank": 1,
            "exact_proof_bank_obligation": "Probability.exchangeable",
            "proof_bank_bridge_obligations": [],
            "local_candidate_declarations": ["Probability.exchangeable"],
            "external_candidate_declarations": [],
            "expected_premises": ["calibration scores are exchangeable"],
            "required_gate": "compose exact proof-bank obligation into patch rerun",
            "next_action": "compose_exact_proof_bank_obligation",
            "proof_evidence_status": (
                "PATCH_RERUN_RESIDUAL_OBLIGATION_NOT_PROOF_EVIDENCE"
            ),
            "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
            "ok": True,
            "errors": [],
        },
        {
            "schema_version": 1,
            "residual_obligation_id": "residual-obligation:rank_route:rank_uniformity",
            "rerun_calibration_id": "rerun-calibration:rank_route",
            "rerun_id": "patch-rerun:rank_route",
            "rerun_attempt_id": "patch-rerun-attempt:rank_route",
            "replay_id": "replay:rank_route",
            "route_id": "rank_route",
            "display_name": "distribution_free_rank_bound",
            "target_theorem_name": "distribution_free_rank_bound",
            "candidate_bridge_lemma_name": "rank_uniformity_bridge",
            "patched_artifact_path": "patched/Rank.lean",
            "patch_rerun_calibration_status": "residual_formal_gaps_remain",
            "residual_gap": "rank_uniformity",
            "residual_kind": "residual_formal_gap",
            "source_support_classification": "coverage_missing_for_residual_gap",
            "action_class": "source_discovery_needed",
            "action_type": "run_source_discovery",
            "proof_bank_action_id": "",
            "priority": "high",
            "priority_rank": 2,
            "exact_proof_bank_obligation": "",
            "proof_bank_bridge_obligations": [],
            "local_candidate_declarations": [],
            "external_candidate_declarations": [],
            "expected_premises": ["rank of test score among calibration scores"],
            "required_gate": "source support before patch replay can be adopted",
            "next_action": "run_source_discovery_for_residual_gap",
            "proof_evidence_status": (
                "PATCH_RERUN_RESIDUAL_OBLIGATION_NOT_PROOF_EVIDENCE"
            ),
            "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
            "ok": True,
            "errors": [],
        },
    ]
    (
        residual_obligations_dir
        / "formal_verifier_replay_repair_patch_rerun_residual_obligations_manifest.json"
    ).write_text(
        json.dumps(
            {
                "schema_version": 1,
                "n_residual_obligation_rows": len(rows),
                "n_source_discovery_needed": 1,
                "n_exact_proof_bank_reuse": 1,
                "all_ok": True,
                "rows": rows,
                "proof_evidence_status": (
                    "PATCH_RERUN_RESIDUAL_OBLIGATION_NOT_PROOF_EVIDENCE"
                ),
                "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        formal_verifier_replay_repair_patch_rerun_residual_obligations_dir=(
            residual_obligations_dir
        ),
    )

    assert payload["all_ok"]
    assert (
        payload[
            "n_request_formal_verifier_patch_rerun_residual_obligation_rows"
        ]
        == 2
    )
    assert payload["n_requests_with_patch_rerun_residual_obligation_summary"] == 1
    assert payload["n_request_patch_rerun_residual_obligation_rows"] == 2
    assert (
        payload[
            "n_request_patch_rerun_residual_obligation_source_discovery_needed"
        ]
        == 1
    )
    request = payload["request_packets"][0]
    context = request["context_packet"]
    assert len(context["formal_verifier_patch_rerun_residual_obligation_rows"]) == 2
    residual_summary = context["patch_rerun_residual_obligation_summary"]
    assert residual_summary["total_rows"] == 2
    assert residual_summary["source_discovery_needed_count"] == 1
    assert residual_summary["exact_reuse_count"] == 1
    assert residual_summary["by_action_class"] == {
        "reuse_exact_proof_bank_obligation": 1,
        "source_discovery_needed": 1,
    }
    feedback_summary = context["feedback_loop_summary"]
    assert feedback_summary["replan_required"] is True
    assert (
        feedback_summary["patch_rerun_residual_obligations"] == residual_summary
    )
    assert any(
        action["source"] == "formal_verifier_patch_rerun_residual_obligations"
        and action["owner"] == "literature_router"
        and action["residual_gap"] == "rank_uniformity"
        for action in feedback_summary["recommended_next_actions"]
    )
    preconditions = context["route_adoption_preconditions"]
    assert preconditions["blocked_before_response"] is True
    assert (
        "feedback_summary_actions_pending_resolution"
        in preconditions["known_pre_response_blockers"]
    )
    assert (
        "feedback_loop_replan_required"
        in preconditions["known_pre_response_blockers"]
    )
    inventory = context["context_packet_inventory"]
    assert (
        inventory["row_counts"][
            "formal_verifier_patch_rerun_residual_obligation_rows"
        ]
        == 2
    )
    assert inventory["patch_rerun_residual_obligation_summary_present"] is True
    assert inventory["patch_rerun_residual_obligation_row_count"] == 2
    assert inventory["patch_rerun_residual_source_discovery_needed_count"] == 1
    brief = context["route_planning_brief"]
    assert brief["patch_rerun_residual_obligation_summary"] == residual_summary
    assert brief["evidence_summary"]["patch_rerun_residual_obligation_row_count"] == 2
    assert (
        brief["evidence_summary"][
            "patch_rerun_residual_source_discovery_needed_count"
        ]
        == 1
    )
    assert any(
        focus["focus_id"] == "repair_patch_rerun_residual_obligations"
        for focus in brief["planner_focus"]
    )
    assert any(
        gap["gap_id"] == "patch_rerun_residual_source_discovery_needed"
        for gap in brief["evidence_gaps"]
    )
    report = (out_dir / "formalization_gap_planner_llm_route_planner.md").read_text(
        encoding="utf-8"
    )
    assert "Patch-rerun residual obligations: rows=2 source_discovery=1" in report


def test_llm_route_planner_stages_patch_rerun_residual_followup_queue() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_patch_rerun_residual_followup_queue"
    )
    out_dir = root / "llm_route_planner"
    followup_queue_dir = root / "followup_queue"
    shutil.rmtree(root, ignore_errors=True)
    followup_queue_dir.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    rows = [
        {
            "schema_version": 1,
            "followup_id": "followup:rank_route:patch",
            "residual_response_validation_id": "validation:rank_route:patch",
            "prompt_packet_id": "packet:rank_route:patch",
            "residual_obligation_id": "residual-obligation:rank_route:exchangeability",
            "rerun_calibration_id": "rerun-calibration:rank_route",
            "rerun_id": "patch-rerun:rank_route",
            "rerun_attempt_id": "patch-rerun-attempt:rank_route",
            "replay_id": "replay:rank_route",
            "route_id": "rank_route",
            "display_name": "distribution_free_rank_bound",
            "target_theorem_name": "distribution_free_rank_bound",
            "candidate_bridge_lemma_name": "rank_uniformity_bridge",
            "residual_gap": "exchangeability",
            "action_class": "reuse_exact_proof_bank_obligation",
            "source_acceptance_status": (
                "RESIDUAL_PATCH_PROPOSAL_RECORDED_NOT_PROOF_EVIDENCE"
            ),
            "response_present": True,
            "response_contract_ok": True,
            "proposed_lean_artifact_path": "patched/Rank.lean",
            "proposed_artifact_exists": True,
            "changed_lean_declarations": ["Probability.exchangeable"],
            "used_proof_bank_obligations": ["Probability.exchangeable"],
            "used_local_declarations": ["Probability.exchangeable"],
            "source_discovery_queries": [],
            "remaining_residual_formal_gaps": [],
            "followup_kind": "residual_patch_rerun",
            "followup_status": "READY_FOR_RESIDUAL_PATCH_RERUN",
            "owner_agent": "formal_verifier",
            "priority": "high",
            "required_gate": "rerun patch artifact through calibration",
            "execution_commands": ["lake env lean patched/Rank.lean"],
            "proof_evidence_status": "RESIDUAL_FOLLOWUP_QUEUE_NOT_PROOF_EVIDENCE",
            "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
            "ok": True,
            "errors": [],
        },
        {
            "schema_version": 1,
            "followup_id": "followup:rank_route:source",
            "residual_response_validation_id": "validation:rank_route:source",
            "prompt_packet_id": "packet:rank_route:source",
            "residual_obligation_id": "residual-obligation:rank_route:rank_uniformity",
            "rerun_calibration_id": "rerun-calibration:rank_route",
            "rerun_id": "patch-rerun:rank_route",
            "rerun_attempt_id": "patch-rerun-attempt:rank_route",
            "replay_id": "replay:rank_route",
            "route_id": "rank_route",
            "display_name": "distribution_free_rank_bound",
            "target_theorem_name": "distribution_free_rank_bound",
            "candidate_bridge_lemma_name": "rank_uniformity_bridge",
            "residual_gap": "rank_uniformity",
            "action_class": "source_discovery_needed",
            "source_acceptance_status": (
                "SOURCE_DISCOVERY_RESPONSE_RECORDED_NOT_PROOF_EVIDENCE"
            ),
            "response_present": True,
            "response_contract_ok": True,
            "proposed_lean_artifact_path": "",
            "proposed_artifact_exists": False,
            "changed_lean_declarations": [],
            "used_proof_bank_obligations": [],
            "used_local_declarations": [],
            "source_discovery_queries": [
                "rank uniformity exchangeable calibration scores",
            ],
            "remaining_residual_formal_gaps": ["rank_uniformity"],
            "followup_kind": "residual_source_discovery",
            "followup_status": "READY_FOR_RESIDUAL_SOURCE_DISCOVERY",
            "owner_agent": "rag_retrieval",
            "priority": "medium",
            "required_gate": "expand source coverage before replay adoption",
            "execution_commands": [
                "rerun primitive-source coverage for rank uniformity",
            ],
            "proof_evidence_status": "RESIDUAL_FOLLOWUP_QUEUE_NOT_PROOF_EVIDENCE",
            "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
            "ok": True,
            "errors": [],
        },
    ]
    (
        followup_queue_dir
        / "formal_verifier_replay_repair_patch_rerun_residual_followup_queue_manifest.json"
    ).write_text(
        json.dumps(
            {
                "schema_version": 1,
                "n_followup_items": len(rows),
                "n_ready": 2,
                "n_source_discovery_items": 1,
                "n_patch_rerun_items": 1,
                "all_ok": True,
                "rows": rows,
                "limitations": [
                    "residual follow-up queue rows are operational work items, not theorem proof evidence"
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        formal_verifier_replay_repair_patch_rerun_residual_followup_queue_dir=(
            followup_queue_dir
        ),
    )

    assert payload["all_ok"]
    assert (
        payload[
            "n_request_formal_verifier_patch_rerun_residual_followup_queue_rows"
        ]
        == 2
    )
    assert payload["n_requests_with_patch_rerun_residual_followup_queue_summary"] == 1
    assert payload["n_request_patch_rerun_residual_followup_queue_rows"] == 2
    assert payload["n_request_patch_rerun_residual_followup_queue_ready"] == 2
    assert (
        payload[
            "n_request_patch_rerun_residual_followup_queue_source_discovery"
        ]
        == 1
    )
    request = payload["request_packets"][0]
    context = request["context_packet"]
    assert len(context["formal_verifier_patch_rerun_residual_followup_queue_rows"]) == 2
    followup_summary = context["patch_rerun_residual_followup_queue_summary"]
    assert followup_summary["total_rows"] == 2
    assert followup_summary["ready_count"] == 2
    assert followup_summary["patch_rerun_count"] == 1
    assert followup_summary["source_discovery_count"] == 1
    assert followup_summary["with_artifact_count"] == 1
    assert followup_summary["with_source_queries_count"] == 1
    feedback_summary = context["feedback_loop_summary"]
    assert feedback_summary["replan_required"] is True
    assert (
        feedback_summary["patch_rerun_residual_followup_queue"]
        == followup_summary
    )
    assert any(
        action["source"] == "formal_verifier_patch_rerun_residual_followup_queue"
        and action["action"] == "run_residual_source_discovery_followup"
        and action["residual_gap"] == "rank_uniformity"
        for action in feedback_summary["recommended_next_actions"]
    )
    assert any(
        action["source"] == "formal_verifier_patch_rerun_residual_followup_queue"
        and action["action"] == "rerun_residual_patch_followup"
        and action["residual_gap"] == "exchangeability"
        for action in feedback_summary["recommended_next_actions"]
    )
    preconditions = context["route_adoption_preconditions"]
    assert preconditions["blocked_before_response"] is True
    assert (
        "feedback_summary_actions_pending_resolution"
        in preconditions["known_pre_response_blockers"]
    )
    assert (
        "feedback_loop_replan_required"
        in preconditions["known_pre_response_blockers"]
    )
    inventory = context["context_packet_inventory"]
    assert (
        inventory["row_counts"][
            "formal_verifier_patch_rerun_residual_followup_queue_rows"
        ]
        == 2
    )
    assert inventory["patch_rerun_residual_followup_queue_summary_present"] is True
    assert inventory["patch_rerun_residual_followup_queue_row_count"] == 2
    assert inventory["patch_rerun_residual_followup_queue_ready_count"] == 2
    assert inventory["patch_rerun_residual_followup_queue_source_discovery_count"] == 1
    brief = context["route_planning_brief"]
    assert brief["patch_rerun_residual_followup_queue_summary"] == followup_summary
    assert (
        brief["evidence_summary"][
            "patch_rerun_residual_followup_queue_row_count"
        ]
        == 2
    )
    assert (
        brief["evidence_summary"][
            "patch_rerun_residual_followup_queue_source_discovery_count"
        ]
        == 1
    )
    assert any(
        focus["focus_id"] == "dispatch_patch_rerun_residual_followup_queue"
        for focus in brief["planner_focus"]
    )
    assert any(
        gap["gap_id"] == "patch_rerun_residual_followup_source_discovery"
        for gap in brief["evidence_gaps"]
    )
    report = (out_dir / "formalization_gap_planner_llm_route_planner.md").read_text(
        encoding="utf-8"
    )
    assert (
        "Patch-rerun residual follow-up queue: rows=2 ready=2 source_discovery=1"
        in report
    )


def test_llm_route_planner_stages_agentic_proof_strategy_plan() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_agentic_strategy_plan"
    )
    out_dir = root / "llm_route_planner"
    strategy_plan_dir = root / "agentic_strategy_plan"
    shutil.rmtree(root, ignore_errors=True)
    strategy_plan_dir.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    rows = [
        {
            "schema_version": 1,
            "strategy_id": "strategy:rank_route:patch",
            "followup_id": "followup:rank_route:patch",
            "residual_response_validation_id": "validation:rank_route:patch",
            "prompt_packet_id": "packet:rank_route:patch",
            "residual_obligation_id": "residual-obligation:rank_route:exchangeability",
            "route_id": "rank_route",
            "display_name": "distribution_free_rank_bound",
            "target_theorem_name": "distribution_free_rank_bound",
            "candidate_bridge_lemma_name": "exchangeability_bridge",
            "residual_gap": "exchangeability",
            "action_class": "reuse_exact_proof_bank_obligation",
            "followup_kind": "residual_patch_rerun",
            "followup_status": "READY_FOR_AGENTIC_PROOF_STRATEGY",
            "agentic_strategy_kind": "evolve_block_residual_patch",
            "paper_patterns": ["exchangeable calibration scores"],
            "required_live_tools": ["lean_goal", "lean_multi_attempt"],
            "evaluator_gates": [
                "patch-rerun calibration",
                "full-route Lean kernel verification",
            ],
            "evolve_block_scope": "residual bridge candidate for exchangeability",
            "global_goal_cache_keys": [],
            "candidate_database_key": "candidate-db:rank_route:exchangeability",
            "expected_artifacts": ["patched/Rank.lean", "strategy_trace.json"],
            "priority_score": 130,
            "rank": 1,
            "proof_evidence_status": (
                "AGENTIC_STRATEGY_PLAN_NOT_PROOF_EVIDENCE"
            ),
            "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
            "ok": True,
            "errors": [],
        },
        {
            "schema_version": 1,
            "strategy_id": "strategy:rank_route:source",
            "followup_id": "followup:rank_route:source",
            "residual_response_validation_id": "validation:rank_route:source",
            "prompt_packet_id": "packet:rank_route:source",
            "residual_obligation_id": "residual-obligation:rank_route:rank_uniformity",
            "route_id": "rank_route",
            "display_name": "distribution_free_rank_bound",
            "target_theorem_name": "distribution_free_rank_bound",
            "candidate_bridge_lemma_name": "rank_uniformity_bridge",
            "residual_gap": "rank_uniformity",
            "action_class": "source_discovery_needed",
            "followup_kind": "residual_source_discovery",
            "followup_status": "READY_FOR_AGENTIC_PROOF_STRATEGY",
            "agentic_strategy_kind": "global_goal_cache_source_discovery",
            "paper_patterns": ["uniform rank statistic"],
            "required_live_tools": ["lean_local_search", "lean_leansearch"],
            "evaluator_gates": ["primitive-source coverage expansion"],
            "evolve_block_scope": "",
            "global_goal_cache_keys": ["rank_uniformity:exchangeable_scores"],
            "candidate_database_key": "candidate-db:rank_route:rank_uniformity",
            "expected_artifacts": ["source_cache/rank_uniformity.json"],
            "priority_score": 80,
            "rank": 2,
            "proof_evidence_status": (
                "AGENTIC_STRATEGY_PLAN_NOT_PROOF_EVIDENCE"
            ),
            "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
            "ok": True,
            "errors": [],
        },
    ]
    (
        strategy_plan_dir / "formal_verifier_agentic_proof_strategy_plan_manifest.json"
    ).write_text(
        json.dumps(
            {
                "schema_version": 1,
                "n_strategy_rows": len(rows),
                "n_ready": 2,
                "n_patch_evolve_blocks": 1,
                "n_source_discovery_cache_items": 1,
                "n_kernel_overlay_composition_seeds": 0,
                "n_with_live_tool_plan": 2,
                "all_ok": True,
                "rows": rows,
                "limitations": [
                    "agentic proof strategy rows are proof-search contracts, not theorem proof evidence"
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        formal_verifier_agentic_proof_strategy_plan_dir=strategy_plan_dir,
    )

    assert payload["all_ok"]
    assert payload["n_request_formal_verifier_agentic_proof_strategy_plan_rows"] == 2
    assert payload["n_requests_with_agentic_proof_strategy_plan_summary"] == 1
    assert payload["n_request_agentic_proof_strategy_plan_rows"] == 2
    assert payload["n_request_agentic_proof_strategy_plan_ready"] == 2
    assert (
        payload[
            "n_request_agentic_proof_strategy_plan_source_discovery_cache_items"
        ]
        == 1
    )
    request = payload["request_packets"][0]
    context = request["context_packet"]
    prompt_text = request["prompt_messages"]["user"]
    assert "context_packet.formal_verifier_agentic_proof_strategy_plan_rows" in (
        prompt_text
    )
    assert "context_packet.agentic_proof_strategy_plan_summary" in prompt_text
    assert "global_goal_cache_source_discovery" in prompt_text
    assert "evolve_block_residual_patch" in prompt_text
    assert "kernel_overlay_composition_patch_seed" in prompt_text
    assert len(context["formal_verifier_agentic_proof_strategy_plan_rows"]) == 2
    strategy_summary = context["agentic_proof_strategy_plan_summary"]
    assert strategy_summary["total_rows"] == 2
    assert strategy_summary["ready_count"] == 2
    assert strategy_summary["patch_evolve_block_count"] == 1
    assert strategy_summary["source_discovery_cache_item_count"] == 1
    assert strategy_summary["with_live_tool_plan_count"] == 2
    feedback_summary = context["feedback_loop_summary"]
    assert feedback_summary["replan_required"] is True
    assert feedback_summary["needs_more_library_grounding"] is True
    assert feedback_summary["agentic_proof_strategy_plan"] == strategy_summary
    assert any(
        action["source"] == "formal_verifier_agentic_proof_strategy_plan"
        and action["action"] == "run_agentic_patch_evolve_block"
        and action["residual_gap"] == "exchangeability"
        for action in feedback_summary["recommended_next_actions"]
    )
    assert any(
        action["source"] == "formal_verifier_agentic_proof_strategy_plan"
        and action["action"] == "run_agentic_source_discovery_cache_item"
        and action["residual_gap"] == "rank_uniformity"
        for action in feedback_summary["recommended_next_actions"]
    )
    preconditions = context["route_adoption_preconditions"]
    assert preconditions["blocked_before_response"] is True
    assert (
        "feedback_summary_actions_pending_resolution"
        in preconditions["known_pre_response_blockers"]
    )
    assert (
        "feedback_loop_replan_required"
        in preconditions["known_pre_response_blockers"]
    )
    inventory = context["context_packet_inventory"]
    assert (
        inventory["row_counts"]["formal_verifier_agentic_proof_strategy_plan_rows"]
        == 2
    )
    assert inventory["agentic_proof_strategy_plan_summary_present"] is True
    assert inventory["agentic_proof_strategy_plan_row_count"] == 2
    assert inventory["agentic_proof_strategy_plan_ready_count"] == 2
    assert (
        inventory[
            "agentic_proof_strategy_plan_source_discovery_cache_item_count"
        ]
        == 1
    )
    brief = context["route_planning_brief"]
    assert brief["agentic_proof_strategy_plan_summary"] == strategy_summary
    assert brief["evidence_summary"]["agentic_proof_strategy_plan_row_count"] == 2
    assert (
        brief["evidence_summary"][
            "agentic_proof_strategy_plan_source_discovery_cache_item_count"
        ]
        == 1
    )
    assert any(
        focus["focus_id"] == "dispatch_agentic_proof_strategy_plan"
        for focus in brief["planner_focus"]
    )
    assert any(
        gap["gap_id"] == "agentic_strategy_source_discovery_cache_items"
        for gap in brief["evidence_gaps"]
    )
    report = (out_dir / "formalization_gap_planner_llm_route_planner.md").read_text(
        encoding="utf-8"
    )
    assert (
        "Agentic proof strategy plan: rows=2 ready=2 source_discovery_cache=1"
        in report
    )


def test_llm_route_planner_matches_context_rows_by_route_aliases() -> None:
    root = Path("runs/test_formalization_gap_planner_llm_route_alias_context")
    out_dir = root / "llm_route_planner"
    source_grounding_dir = root / "source_grounding"
    resource_response_dir = root / "resource_response_ledger"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    source_grounding_dir.mkdir(parents=True, exist_ok=True)
    resource_response_dir.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)

    source_manifest = (
        source_grounding_dir
        / "formalization_gap_planner_source_grounding_audit_manifest.json"
    )
    source_manifest.write_text(
        json.dumps(
            {
                "component_name": "formalization_gap_planner_source_grounding_audit",
                "rows": [
                    {
                        "goal_plan_id": "goal:alias",
                        "source_route_id": "rank_route",
                        "source_refs": ["alias_rank_source"],
                        "source_snippets": [
                            {
                                "source_ref": "alias_rank_source",
                                "claim": (
                                    "Alias route source supports rank "
                                    "exchangeability."
                                ),
                                "excerpt": (
                                    "The exchangeability route can be carried "
                                    "through the same finite rank argument."
                                ),
                                "target_primitives": ["rank_uniformity"],
                            }
                        ],
                        "source_grounding_status": "source_backed",
                        "ok": True,
                        "errors": [],
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    ledger_manifest = (
        resource_response_dir
        / "formalization_gap_planner_resource_response_ledger_manifest.json"
    )
    ledger_manifest.write_text(
        json.dumps(
            {
                "component_name": "formalization_gap_planner_resource_response_ledger",
                "rows": [
                    {
                        "resource_response_ledger_id": "ledger:alias",
                        "standalone_input_trace": {
                            "trace_kind": "route_replan_seed",
                            "source_route_id": "rank_route",
                            "source_goal_plan_id": "goal:alias",
                        },
                        "target_prover_family": "lean4",
                        "response_present": True,
                        "response_contract_ok": True,
                        "response_contract_minimum_met": True,
                        "acceptance_status": "accepted",
                        "response_summary": (
                            "Alias trace found a reusable rank bridge."
                        ),
                        "formal_declaration_hits": [
                            {
                                "declaration": "Probability.aliasRankBridge",
                                "target_prover_family": "lean4",
                                "source_field": "formal_declaration_hits",
                            }
                        ],
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        formalization_gap_planner_source_grounding_audit_dir=source_grounding_dir,
        formalization_gap_planner_resource_response_ledger_dir=resource_response_dir,
    )

    assert payload["all_ok"]
    assert payload["n_requests_with_source_grounding_rows"] == 1
    assert payload["n_requests_with_resource_response_ledger_rows"] == 1
    request = payload["request_packets"][0]
    context = request["context_packet"]
    assert context["source_grounding_rows"][0]["source_route_id"] == "rank_route"
    assert context["resource_response_ledger_rows"][0]["standalone_input_trace"][
        "source_route_id"
    ] == "rank_route"
    assert "alias_rank_source" in set(context["available_source_refs"])
    assert any(
        snippet.get("source_ref") == "alias_rank_source"
        for snippet in context["available_source_snippets"]
    )
    assert any(
        row["declaration"] == "Probability.aliasRankBridge"
        for row in context["available_formal_declaration_rows"]
    )
    inventory = context["context_packet_inventory"]
    assert inventory["row_counts"]["source_grounding_rows"] == 1
    assert inventory["row_counts"]["resource_response_ledger_rows"] == 1
    assert inventory["available_source_ref_count"] == len(
        context["available_source_refs"]
    )


def test_llm_route_planner_prompt_only_remains_explicit_no_provider_mode() -> None:
    root = Path("runs/test_formalization_gap_planner_llm_route_planner_prompt_only")
    out_dir = root / "llm_route_planner"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        provider_name="prompt_only",
    )

    assert payload["all_ok"]
    assert payload["provider_name"] == "prompt_only"
    assert payload["invoke_provider"] is False
    assert payload["n_response_present"] == 0
    request = payload["request_packets"][0]
    assert request["provider_name"] == "prompt_only"
    assert request["model"] == ""


def test_llm_route_planner_cost_hints_use_library_coverage_lower_bound() -> None:
    root = Path("runs/test_formalization_gap_planner_llm_route_planner_cost_hints")
    out_dir = root / "llm_route_planner"
    coverage_dir = root / "library_coverage_map"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    coverage_dir.mkdir(parents=True, exist_ok=True)
    input_json = _write_light_input(root)
    (
        coverage_dir / "formalization_gap_planner_library_coverage_map_manifest.json"
    ).write_text(
        json.dumps(
            {
                "component_name": "formalization_gap_planner_library_coverage_map",
                "rows": [
                    {
                        "goal_plan_id": "goal:rank_route_light",
                        "route_id": "rank_route_light",
                        "display_name": "distribution_free_rank_bound_light",
                        "target_prover_family": "lean4",
                        "library_snapshot_ref": "lean_mathlib_snapshot",
                        "primitive": "rank_uniformity",
                        "coverage_bucket": "bridge_needed",
                        "coverage_status": "bridge_needed",
                        "action_class": "design_bridge_lemma",
                        "candidate_declaration_rows": [
                            {
                                "declaration": "Probability.rankUniformityBridge",
                                "target_prover_family": "lean4",
                                "source_field": "library_coverage_map_fixture",
                            }
                        ],
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        formalization_gap_planner_library_coverage_map_dir=coverage_dir,
    )

    assert payload["all_ok"]
    assert payload["n_requests_with_library_coverage_rows"] == 1
    assert payload["n_requests_with_minimal_delta_cost_hints"] == 1
    assert payload["n_request_primitive_cost_hints"] == 2
    assert payload["by_request_model_tier"] == {"sonnet": 1}
    request = payload["request_packets"][0]
    assert request["model_tier"] == "sonnet"
    assert "minimal-delta cost hint requires bridge-or-harder work" in request[
        "model_selection_rationale"
    ]
    cost_hints = request["context_packet"]["minimal_delta_cost_hints"]
    rank_hint = {
        row["primitive"]: row for row in cost_hints["primitive_cost_hints"]
    }["rank_uniformity"]
    assert rank_hint["minimum_base_cost"] == 4.0
    assert rank_hint["minimum_coverage_bucket"] == "bridge_needed"
    assert rank_hint["minimum_cost_source"] == "library_coverage_rows"
    assert "current_route.primitives" in rank_hint["evidence_sources"]
    assert "library_coverage_rows" in rank_hint["evidence_sources"]
    assert {
        (row["declaration"], row["target_prover_family"])
        for row in rank_hint["candidate_declaration_rows"]
    } >= {("Probability.rankUniformityBridge", "lean4")}
    assert cost_hints["route_option_hints"][0]["minimum_route_base_cost"] == 4.0
    alignment_summary = request["context_packet"]["library_alignment_summary"]
    assert (
        alignment_summary["schema_id"]
        == LLM_ROUTE_PLANNER_LIBRARY_ALIGNMENT_SUMMARY_SCHEMA_ID
    )
    assert alignment_summary["route_id"] == "rank_route_light"
    assert alignment_summary["n_primitives"] == 2
    assert alignment_summary["n_bridge_primitives"] == 1
    assert alignment_summary["n_bridge_or_harder_primitives"] == 1
    assert alignment_summary["n_route_options"] == 1
    assert alignment_summary["route_option_alignment"][0][
        "minimum_route_base_cost"
    ] == 4.0
    assert alignment_summary["by_library_delta_class"]["bridge"] == 1
    rank_alignment = {
        row["primitive"]: row for row in alignment_summary["primitive_alignment"]
    }["rank_uniformity"]
    assert rank_alignment["minimum_coverage_bucket"] == "bridge_needed"
    assert rank_alignment["library_delta_class"] == "bridge"
    assert "Probability.rankUniformityBridge" in set(
        rank_alignment["target_compatible_declarations"]
    )
    assert payload["n_request_library_alignment_bridge_primitives"] == 1
    assert payload["n_request_library_alignment_bridge_or_harder_primitives"] == 1
    assert payload["n_request_library_alignment_route_options"] == 1
    assert (
        payload[
            "total_request_library_alignment_route_option_minimum_base_cost"
        ]
        == 4.0
    )


def test_llm_route_planner_stages_target_intake_context() -> None:
    root = Path("runs/test_formalization_gap_planner_llm_route_planner_target_intake")
    target_intake_dir = root / "target_intake"
    out_dir = root / "llm_route_planner"
    raw_target_json = root / "target.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    raw_target_json.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "component_name": "formalization_gap_planner_target_intake",
                "target_prover_family": "lean4",
                "library_snapshot_ref": "lean_mathlib_snapshot",
                "target_id": "split_conformal_rank_bound",
                "title": "Split conformal rank bound",
                "domain": "conformal_prediction",
                "theorem_statement": (
                    "For exchangeable calibration and test scores, the split "
                    "conformal rank bound has finite-sample coverage."
                ),
                "theorem_skeleton": "theorem split_conformal_rank_bound : ...",
                "objects": ["calibration scores", "test score", "rank statistic"],
                "assumptions": ["exchangeability", "deterministic tie handling"],
                "statistical_procedure": "split conformal prediction",
                "desired_conclusion": "finite-sample coverage inequality",
                "desired_theorem_shape": "finite_sample_rank_coverage",
                "known_proof_sources": ["conformal_prediction_textbook"],
                "candidate_primitives": [
                    {
                        "primitive": "rank_uniformity",
                        "coverage_status": "needs_search",
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    target_payload = normalize_formalization_gap_planner_target_intake(
        raw_target_json,
        target_intake_dir,
    )
    assert target_payload["all_ok"]
    standalone_seed = (
        target_intake_dir
        / "formalization_gap_planner_target_intake_standalone_seed.json"
    )

    payload = export_formalization_gap_planner_llm_route_planner(
        standalone_seed,
        out_dir,
        formalization_gap_planner_target_intake_dir=target_intake_dir,
    )

    assert payload["all_ok"]
    assert payload["n_requests_with_target_intake_rows"] == 1
    assert payload["n_request_target_intake_rows"] == 1
    request = payload["request_packets"][0]
    context = request["context_packet"]
    intake_row = context["target_intake_rows"][0]
    assert intake_row["target_id"] == "split_conformal_rank_bound"
    assert intake_row["normalized_objects"] == [
        "calibration scores",
        "test score",
        "rank statistic",
    ]
    assert intake_row["normalized_assumptions"] == [
        "exchangeability",
        "deterministic tie handling",
    ]
    assert intake_row["normalized_procedure"] == "split conformal prediction"
    assert intake_row["normalized_claim"] == "finite-sample coverage inequality"
    assert intake_row["desired_theorem_shape"] == "finite_sample_rank_coverage"
    assert "rank_uniformity" in intake_row["extracted_primitive_candidates"]
    target_context_packet = context["target_theorem_context_packet"]
    assert target_context_packet["context_packet_kind"] == (
        TARGET_THEOREM_CONTEXT_PACKET_KIND
    )
    assert target_context_packet["theorem_statement"] == (
        "For exchangeable calibration and test scores, the split "
        "conformal rank bound has finite-sample coverage."
    )
    assert target_context_packet["theorem_skeletons"] == [
        "theorem split_conformal_rank_bound : ..."
    ]
    assert target_context_packet["normalized_objects"] == [
        "calibration scores",
        "test score",
        "rank statistic",
    ]
    assert target_context_packet["normalized_assumptions"] == [
        "exchangeability",
        "deterministic tie handling",
    ]
    assert target_context_packet["normalized_procedures"] == [
        "split conformal prediction"
    ]
    assert target_context_packet["desired_conclusions"] == [
        "finite-sample coverage inequality"
    ]
    assert target_context_packet["desired_theorem_shapes"] == [
        "finite_sample_rank_coverage"
    ]
    assert target_context_packet["proof_style_hints"] == [
        "desired theorem shape: finite_sample_rank_coverage",
        "proof-state probe required",
    ]
    assert "rank_uniformity" in target_context_packet["primitive_candidates"]
    assert "conformal_prediction_textbook" in target_context_packet[
        "proof_source_refs"
    ]
    assert context["route_planning_brief"]["target_context"][
        "normalized_procedures"
    ] == ["split conformal prediction"]
    assert context["context_packet_inventory"][
        "target_theorem_context_assumption_count"
    ] == 2
    assert context["context_packet_inventory"][
        "target_theorem_context_procedure_count"
    ] == 1
    assert context["context_packet_inventory"][
        "target_theorem_context_desired_conclusion_count"
    ] == 1
    assert context["context_packet_inventory"][
        "target_theorem_context_proof_style_hint_count"
    ] == 2
    prompt_text = request["prompt_messages"]["user"]
    assert "context_packet.target_intake_rows" in prompt_text
    assert "context_packet.target_theorem_context_packet" in prompt_text
    assert "normalized_assumptions" in prompt_text
    assert "statistical procedure" in prompt_text
    assert "desired conclusion" in prompt_text
    assert "proof-style hints" in prompt_text
    assert "formal_library_grounding_queries" in prompt_text
    assert "legacy alias" in prompt_text
    assert "target intake is not proof evidence" in prompt_text


def test_llm_route_planner_rejects_missing_target_context_summary() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_missing_target_context_summary"
    )
    out_dir = root / "llm_route_planner"
    target_intake_dir = root / "target_intake"
    response_json = root / "response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    _write_rank_target_intake_manifest(target_intake_dir)
    response_json.write_text(
        json.dumps(_llm_response_payload(), indent=2),
        encoding="utf-8",
    )

    payload = export_formalization_gap_planner_llm_route_planner(
        _write_input(root),
        out_dir,
        provider_name="static",
        static_response_json=response_json,
        formalization_gap_planner_target_intake_dir=target_intake_dir,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    assert row["response_contract_ok"] is False
    assert any(
        "target_context_summary required when "
        "context_packet.target_theorem_context_packet has normalized" in error
        for error in row["errors"]
    )


def test_llm_route_planner_rejects_missing_source_only_target_context_summary() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_missing_source_only_target_context"
    )
    out_dir = root / "llm_route_planner"
    response_json = root / "response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    response = _llm_response_payload()
    response.pop("target_context_summary", None)
    response["source_refs"] = []
    response["source_snippets"] = []
    response["standalone_route"]["source_refs"] = []
    response["standalone_route"]["source_snippets"] = []
    response_json.write_text(json.dumps(response, indent=2), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        _write_input(root),
        out_dir,
        provider_name="static",
        static_response_json=response_json,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    assert any(
        "target_context_summary or standalone_route.source_refs required" in error
        for error in row["errors"]
    )


def test_llm_route_planner_accepts_target_context_summary() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_accepts_target_context_summary"
    )
    out_dir = root / "llm_route_planner"
    target_intake_dir = root / "target_intake"
    response_json = root / "response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    _write_rank_target_intake_manifest(target_intake_dir)
    response = _llm_response_payload()
    response["target_context_summary"] = {
        "normalized_objects": [
            "calibration scores",
            "test score",
            "rank statistic",
        ],
        "normalized_assumptions": [
            "exchangeability",
            "deterministic tie handling",
        ],
        "normalized_procedures": ["split conformal prediction"],
        "desired_conclusions": ["finite-sample rank coverage"],
        "desired_theorem_shapes": ["finite_sample_rank_coverage"],
        "target_intake_ids": ["target-intake:rank-context"],
        "proof_source_refs": ["conformal_prediction_textbook"],
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
    }
    response_json.write_text(json.dumps(response, indent=2), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        _write_input(root),
        out_dir,
        provider_name="static",
        static_response_json=response_json,
        formalization_gap_planner_target_intake_dir=target_intake_dir,
    )

    assert payload["all_ok"]
    row = payload["rows"][0]
    assert row["response_contract_ok"] is True
    assert payload["n_rows_with_target_context_summary"] == 1
    assert row["target_context_summary"] == response["target_context_summary"]
    assert row["target_theorem_context_packet"]["normalized_assumptions"] == [
        "exchangeability",
        "deterministic tie handling",
    ]
    row_schema = llm_route_planner_row_json_schema()
    assert "target_context_summary" in row_schema["required"]
    assert validate_llm_route_planner_row(row, row_schema) == []
    drifted_row = deepcopy(row)
    drifted_row["target_context_summary"]["normalized_assumptions"] = [
        "exchangeability"
    ]
    assert (
        "target_context_summary.normalized_assumptions must match "
        "target_theorem_context_packet values"
    ) in validate_llm_route_planner_row(drifted_row, row_schema)
    seed_route = payload["standalone_seed"]["routes"][0]
    metadata = seed_route["replan_metadata"]
    assert seed_route["llm_route_planner_target_context_summary"] == row[
        "target_context_summary"
    ]
    assert metadata["llm_route_planner_target_context_summary"] == row[
        "target_context_summary"
    ]
    drifted_seed = deepcopy(payload["standalone_seed"])
    drifted_seed["routes"][0]["replan_metadata"][
        "llm_route_planner_target_context_summary"
    ]["normalized_assumptions"] = ["exchangeability"]
    assert (
        "routes[0].llm_route_planner_target_context_summary must match "
        "routes[0].replan_metadata.llm_route_planner_target_context_summary"
    ) in validate_standalone_input_payload(drifted_seed)
    legacy_alias_seed = deepcopy(payload["standalone_seed"])
    legacy_summary = dict(response["target_context_summary"])
    legacy_summary["normalized_statistical_procedures"] = legacy_summary.pop(
        "normalized_procedures"
    )
    legacy_summary["normalized_desired_conclusions"] = legacy_summary.pop(
        "desired_conclusions"
    )
    legacy_summary["normalized_theorem_shapes"] = legacy_summary.pop(
        "desired_theorem_shapes"
    )
    legacy_alias_seed["routes"][0]["replan_metadata"][
        "llm_route_planner_target_context_summary"
    ] = legacy_summary
    assert validate_standalone_input_payload(legacy_alias_seed) == []
    drifted_packet_seed = deepcopy(payload["standalone_seed"])
    drifted_packet_seed["routes"][0]["llm_route_planner_target_context_summary"][
        "desired_conclusions"
    ] = ["different theorem"]
    drifted_packet_seed["routes"][0]["replan_metadata"][
        "llm_route_planner_target_context_summary"
    ]["desired_conclusions"] = ["different theorem"]
    assert (
        "routes[0].llm_route_planner_target_context_summary."
        "desired_conclusions must preserve target_theorem_context_packet "
        "values"
    ) in "\n".join(validate_standalone_input_payload(drifted_packet_seed))
    legacy_packet_seed = deepcopy(payload["standalone_seed"])
    legacy_packet_route = legacy_packet_seed["routes"][0]
    legacy_packet_metadata = legacy_packet_route["replan_metadata"]
    legacy_packet_candidates = [
        legacy_packet_route["target_theorem_context_packet"],
    ]
    for packet_key in (
        "target_theorem_context_packet",
        "llm_route_planner_target_theorem_context_packet",
    ):
        if packet_key in legacy_packet_metadata:
            legacy_packet_candidates.append(legacy_packet_metadata[packet_key])
    for packet in legacy_packet_candidates:
        if "normalized_procedures" in packet:
            packet["normalized_statistical_procedures"] = packet.pop(
                "normalized_procedures"
            )
        if "desired_conclusions" in packet:
            packet["normalized_desired_conclusions"] = packet.pop(
                "desired_conclusions"
            )
        if "desired_theorem_shapes" in packet:
            packet["normalized_theorem_shapes"] = packet.pop(
                "desired_theorem_shapes"
            )
    legacy_packet_route["llm_route_planner_target_context_summary"][
        "desired_conclusions"
    ] = ["different theorem"]
    legacy_packet_metadata["llm_route_planner_target_context_summary"][
        "desired_conclusions"
    ] = ["different theorem"]
    assert (
        "routes[0].llm_route_planner_target_context_summary."
        "desired_conclusions must preserve target_theorem_context_packet "
        "values"
    ) in "\n".join(validate_standalone_input_payload(legacy_packet_seed))
    plan_payload = export_formalization_gap_planner_standalone_plan(
        out_dir / "formalization_gap_planner_llm_route_planner_standalone_seed.json",
        root / "standalone_plan_from_target_context_summary",
    )
    assert plan_payload["all_ok"]
    assert (
        plan_payload[
            "n_standalone_input_traces_with_llm_target_context_summary"
        ]
        == 1
    )
    trace = plan_payload["rows"][0]["standalone_input_trace"]
    assert trace["llm_route_planner_target_context_summary"] == row[
        "target_context_summary"
    ]
    assert trace["has_llm_route_planner_target_context_summary"] is True


def test_llm_route_planner_accepts_legacy_alias_target_context_summary_response() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_accepts_legacy_target_context_summary"
    )
    out_dir = root / "llm_route_planner"
    target_intake_dir = root / "target_intake"
    response_json = root / "response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    _write_rank_target_intake_manifest(target_intake_dir)
    response = _llm_response_payload()
    response["target_context_summary"] = {
        "normalized_objects": [
            "calibration scores",
            "test score",
            "rank statistic",
        ],
        "normalized_assumptions": [
            "exchangeability",
            "deterministic tie handling",
        ],
        "normalized_statistical_procedures": ["split conformal prediction"],
        "normalized_desired_conclusions": ["finite-sample rank coverage"],
        "normalized_theorem_shapes": ["finite_sample_rank_coverage"],
        "target_intake_ids": ["target-intake:rank-context"],
        "proof_source_refs": ["conformal_prediction_textbook"],
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
    }
    response_json.write_text(json.dumps(response, indent=2), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        _write_input(root),
        out_dir,
        provider_name="static",
        static_response_json=response_json,
        formalization_gap_planner_target_intake_dir=target_intake_dir,
    )

    assert payload["all_ok"]
    row = payload["rows"][0]
    assert row["target_context_summary"]["normalized_procedures"] == [
        "split conformal prediction"
    ]
    assert row["target_context_summary"]["desired_conclusions"] == [
        "finite-sample rank coverage"
    ]
    assert row["target_context_summary"]["desired_theorem_shapes"] == [
        "finite_sample_rank_coverage"
    ]
    assert "normalized_statistical_procedures" not in row["target_context_summary"]
    assert validate_llm_route_planner_row(row, llm_route_planner_row_json_schema()) == []
    assert validate_standalone_input_payload(payload["standalone_seed"]) == []


def test_llm_route_planner_accepts_standalone_route_target_context_summary() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_accepts_standalone_target_context_summary"
    )
    out_dir = root / "llm_route_planner"
    target_intake_dir = root / "target_intake"
    response_json = root / "response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    _write_rank_target_intake_manifest(target_intake_dir)
    response = _llm_response_payload()
    target_context_summary = {
        "normalized_objects": [
            "calibration scores",
            "test score",
            "rank statistic",
        ],
        "normalized_assumptions": [
            "exchangeability",
            "deterministic tie handling",
        ],
        "normalized_procedures": ["split conformal prediction"],
        "desired_conclusions": ["finite-sample rank coverage"],
        "desired_theorem_shapes": ["finite_sample_rank_coverage"],
        "target_intake_ids": ["target-intake:rank-context"],
        "proof_source_refs": ["conformal_prediction_textbook"],
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
    }
    response["standalone_route"]["llm_route_planner_target_context_summary"] = (
        target_context_summary
    )
    response_json.write_text(json.dumps(response, indent=2), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        _write_input(root),
        out_dir,
        provider_name="static",
        static_response_json=response_json,
        formalization_gap_planner_target_intake_dir=target_intake_dir,
    )

    assert payload["all_ok"]
    row = payload["rows"][0]
    assert row["response_contract_ok"] is True
    assert row["target_context_summary"] == target_context_summary
    assert payload["n_rows_with_target_context_summary"] == 1
    seed_route = payload["standalone_seed"]["routes"][0]
    assert seed_route["llm_route_planner_target_context_summary"] == (
        target_context_summary
    )
    assert seed_route["replan_metadata"][
        "llm_route_planner_target_context_summary"
    ] == target_context_summary


def test_llm_route_planner_auto_uses_sonnet_for_source_unbacked_target_intake() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_target_intake_tier"
    )
    target_intake_dir = root / "target_intake"
    out_dir = root / "llm_route_planner"
    raw_target_json = root / "target.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    raw_target_json.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "component_name": "formalization_gap_planner_target_intake",
                "target_prover_family": "lean4",
                "library_snapshot_ref": "lean_mathlib_snapshot",
                "target_id": "light_rank_bound_without_sources",
                "title": "Light rank bound without sources",
                "domain": "conformal_prediction",
                "theorem_statement": "A small rank fact follows from exchangeability.",
                "assumptions": ["exchangeability"],
                "desired_conclusion": "finite-sample rank coverage",
                "desired_theorem_shape": "finite_sample_rank_coverage",
                "candidate_primitives": [
                    {
                        "primitive": "exchangeability",
                        "coverage_status": "exact_exists",
                        "candidate_declarations": ["Probability.exchangeable"],
                    },
                    {
                        "primitive": "rank_uniformity",
                        "coverage_status": "near_exists",
                        "candidate_declarations": ["Probability.exchangeable"],
                    },
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    target_payload = normalize_formalization_gap_planner_target_intake(
        raw_target_json,
        target_intake_dir,
    )
    assert target_payload["all_ok"]
    assert "proof_source_refs_missing" in target_payload["rows"][0]["review_flags"]

    payload = export_formalization_gap_planner_llm_route_planner(
        target_intake_dir
        / "formalization_gap_planner_target_intake_standalone_seed.json",
        out_dir,
        formalization_gap_planner_target_intake_dir=target_intake_dir,
    )

    assert payload["all_ok"]
    assert payload["by_request_model_tier"] == {"sonnet": 1}
    packet = payload["request_packets"][0]
    assert packet["model_tier"] == "sonnet"
    assert packet["model"] == "claude-sonnet-4-6"
    assert "target intake review flag(s):" in packet["model_selection_rationale"]
    assert "proof_source_refs_missing" in packet["model_selection_rationale"]


def test_llm_route_planner_stages_component_resource_registry_context() -> None:
    root = Path("runs/test_formalization_gap_planner_llm_route_planner_registry_context")
    out_dir = root / "llm_route_planner"
    registry_dir = root / "component_resource_registry"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    export_formalization_gap_planner_component_resource_registry(registry_dir)

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        formalization_gap_planner_component_resource_registry_dir=registry_dir,
    )

    assert payload["all_ok"]
    assert payload["n_requests_with_component_resource_registry_context"] == 1
    assert payload["n_component_resource_registry_components_in_prompt"] > 0
    assert payload["n_component_resource_registry_resources_in_prompt"] > 0
    assert payload["n_component_resource_registry_contracts_in_prompt"] > 0
    assert payload[
        "n_requests_with_source_theorem_semantic_primitive_bridge_context"
    ] == 1
    assert (
        payload[
            "n_component_resource_registry_source_theorem_semantic_primitive_bridge_resources_in_prompt"
        ]
        == 1
    )
    assert (
        payload[
            "n_component_resource_registry_source_theorem_semantic_primitive_bridge_contracts_in_prompt"
        ]
        == 1
    )
    assert (
        payload[
            "n_requests_with_source_theorem_semantic_primitive_from_proof_body_executor_bridge_context"
        ]
        == 1
    )
    assert (
        payload[
            "n_component_resource_registry_source_theorem_semantic_primitive_from_proof_body_executor_bridge_resources_in_prompt"
        ]
        == 1
    )
    assert (
        payload[
            "n_component_resource_registry_source_theorem_semantic_primitive_from_proof_body_executor_bridge_contracts_in_prompt"
        ]
        == 1
    )
    assert (
        payload[
            "n_requests_with_source_theorem_formal_environment_bridge_context"
        ]
        == 1
    )
    assert (
        payload[
            "n_component_resource_registry_source_theorem_formal_environment_bridge_resources_in_prompt"
        ]
        == 1
    )
    assert (
        payload[
            "n_component_resource_registry_source_theorem_formal_environment_bridge_contracts_in_prompt"
        ]
        == 1
    )
    assert (
        payload[
            "n_requests_with_exact_source_theorem_proof_body_executor_context"
        ]
        == 1
    )
    assert (
        payload[
            "n_component_resource_registry_exact_source_theorem_proof_body_executor_resources_in_prompt"
        ]
        == 1
    )
    assert (
        payload[
            "n_component_resource_registry_exact_source_theorem_proof_body_executor_contracts_in_prompt"
        ]
        == 1
    )
    request = payload["request_packets"][0]
    registry_context = request["context_packet"][
        "component_resource_registry_context"
    ]
    resource_ids = {
        row["resource_id"] for row in registry_context["resource_rows"]
    }
    assert "paperclip_cli_mcp" in resource_ids
    assert "lean_lsp_mcp" in resource_ids
    assert "source_theorem_semantic_primitive_bridge" in resource_ids
    assert "source_theorem_semantic_primitive_from_proof_body_executor_bridge" in (
        resource_ids
    )
    assert "source_theorem_formal_environment_bridge" in resource_ids
    assert "exact_source_theorem_proof_body_executor" in resource_ids
    assert any(
        row["component_id"] == "literature_grounded_route_synthesis"
        for row in registry_context["component_rows"]
    )
    assert any(
        row["resource_id"] == "paperclip_cli_mcp"
        for row in registry_context["resource_contract_rows"]
    )
    semantic_bridge_contract = next(
        row
        for row in registry_context["resource_contract_rows"]
        if row["resource_id"] == "source_theorem_semantic_primitive_bridge"
    )
    assert "source_theorem_semantic_primitive_work_orders" in semantic_bridge_contract[
        "request_contract_fields"
    ]
    assert semantic_bridge_contract[
        "output_artifact_kind"
    ] == "source_theorem_semantic_primitive_bridge_response"
    post_proof_body_semantic_bridge_contract = next(
        row
        for row in registry_context["resource_contract_rows"]
        if row["resource_id"]
        == "source_theorem_semantic_primitive_from_proof_body_executor_bridge"
    )
    assert "exact_source_theorem_proof_body_execution_feedback_rows" in (
        post_proof_body_semantic_bridge_contract["request_contract_fields"]
    )
    assert "source_theorem_semantic_primitive_work_orders_from_proof_body_executor" in (
        post_proof_body_semantic_bridge_contract["request_contract_fields"]
    )
    assert post_proof_body_semantic_bridge_contract[
        "output_artifact_kind"
    ] == "source_theorem_semantic_primitive_from_proof_body_executor_bridge_response"
    formal_environment_contract = next(
        row
        for row in registry_context["resource_contract_rows"]
        if row["resource_id"] == "source_theorem_formal_environment_bridge"
    )
    assert "source_theorem_formal_environment_work_orders" in formal_environment_contract[
        "request_contract_fields"
    ]
    assert formal_environment_contract[
        "output_artifact_kind"
    ] == "source_theorem_formal_environment_bridge_response"
    proof_body_executor_contract = next(
        row
        for row in registry_context["resource_contract_rows"]
        if row["resource_id"] == "exact_source_theorem_proof_body_executor"
    )
    assert "exact_source_theorem_proof_body_execution_queue_rows" in proof_body_executor_contract[
        "request_contract_fields"
    ]
    assert proof_body_executor_contract[
        "output_artifact_kind"
    ] == "exact_source_theorem_proof_body_execution_response"
    assert "component_resource_registry_context" in request["prompt_messages"]["user"]
    assert (
        "source_theorem_semantic_primitive_bridge"
        in request["prompt_messages"]["user"]
    )
    assert (
        "source_theorem_semantic_primitive_from_proof_body_executor_bridge"
        in request["prompt_messages"]["user"]
    )
    assert (
        "source_theorem_formal_environment_bridge"
        in request["prompt_messages"]["user"]
    )
    assert (
        "exact_source_theorem_proof_body_executor"
        in request["prompt_messages"]["user"]
    )
    assert "registry rows are not evidence" in request["prompt_messages"]["user"]


def test_llm_route_planner_filters_registry_context_for_rocq_target() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_registry_context_rocq"
    )
    out_dir = root / "llm_route_planner"
    registry_dir = root / "component_resource_registry"
    input_json = root / "standalone_input.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "component_name": "formalization_gap_planner_standalone_input",
                "target_prover_family": "rocq",
                "library_snapshot_ref": "rocq_probability_snapshot",
                "routes": [
                    {
                        "route_id": "rocq_rank_route",
                        "display_name": "rocq_distribution_free_rank_bound",
                        "target_prover_family": "rocq",
                        "theorem_statement": (
                            "A Rocq rank bound follows from exchangeability."
                        ),
                        "source_refs": ["conformal_prediction_textbook"],
                        "primitives": [
                            {
                                "primitive": "rank_uniformity",
                                "coverage_status": "bridge_needed",
                            }
                        ],
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    export_formalization_gap_planner_component_resource_registry(registry_dir)

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        formalization_gap_planner_component_resource_registry_dir=registry_dir,
    )

    assert payload["all_ok"]
    assert (
        payload["n_requests_with_source_theorem_semantic_primitive_bridge_context"]
        == 0
    )
    assert (
        payload[
            "n_component_resource_registry_source_theorem_semantic_primitive_bridge_resources_in_prompt"
        ]
        == 0
    )
    assert (
        payload[
            "n_component_resource_registry_source_theorem_semantic_primitive_bridge_contracts_in_prompt"
        ]
        == 0
    )
    assert (
        payload[
            "n_requests_with_source_theorem_semantic_primitive_from_proof_body_executor_bridge_context"
        ]
        == 0
    )
    assert (
        payload[
            "n_component_resource_registry_source_theorem_semantic_primitive_from_proof_body_executor_bridge_resources_in_prompt"
        ]
        == 0
    )
    assert (
        payload[
            "n_component_resource_registry_source_theorem_semantic_primitive_from_proof_body_executor_bridge_contracts_in_prompt"
        ]
        == 0
    )
    assert (
        payload[
            "n_requests_with_source_theorem_formal_environment_bridge_context"
        ]
        == 0
    )
    assert (
        payload[
            "n_component_resource_registry_source_theorem_formal_environment_bridge_resources_in_prompt"
        ]
        == 0
    )
    assert (
        payload[
            "n_component_resource_registry_source_theorem_formal_environment_bridge_contracts_in_prompt"
        ]
        == 0
    )
    assert (
        payload[
            "n_requests_with_exact_source_theorem_proof_body_executor_context"
        ]
        == 0
    )
    assert (
        payload[
            "n_component_resource_registry_exact_source_theorem_proof_body_executor_resources_in_prompt"
        ]
        == 0
    )
    assert (
        payload[
            "n_component_resource_registry_exact_source_theorem_proof_body_executor_contracts_in_prompt"
        ]
        == 0
    )
    request = payload["request_packets"][0]
    registry_context = request["context_packet"][
        "component_resource_registry_context"
    ]
    resource_ids = {
        row["resource_id"] for row in registry_context["resource_rows"]
    }
    assert "local_target_formal_source_index" in resource_ids
    assert "rocq_lsp_serapi" in resource_ids
    lean_only_resource_ids = {
        "local_formal_source_index",
        "local_lean_rag_dependency_graph",
        "loogle_leansearch",
        "leanexplore_mcp",
        "lean_blueprint_leanarchitect",
        "local_lake_lean",
        "source_theorem_semantic_primitive_bridge",
        "source_theorem_formal_environment_bridge",
        "exact_source_theorem_proof_body_executor",
        "lean_lsp_mcp",
        "leandojo_reprover",
    }
    lean_only_adapter_ids = lean_only_resource_ids | {"loogle_leansearchclient"}
    assert not resource_ids.intersection(lean_only_resource_ids)
    for row in (
        *registry_context["component_rows"],
        *registry_context["execution_plan_rows"],
    ):
        row_resource_ids = set()
        for field_name in (
            "local_fallback_resource_ids",
            "frontier_resource_ids",
            "local_first_resource_ids",
            "frontier_escalation_resource_ids",
            "resource_ids",
        ):
            row_resource_ids.update(row.get(field_name, ()))
        assert not row_resource_ids.intersection(lean_only_resource_ids)
        assert not set(row.get("adapter_ids", ())).intersection(lean_only_adapter_ids)
        assert not set(row.get("detected_adapter_statuses", {})).intersection(
            lean_only_adapter_ids
        )
    contract_resource_ids = {
        row["resource_id"] for row in registry_context["resource_contract_rows"]
    }
    assert "rocq_lsp_serapi" in contract_resource_ids
    assert not contract_resource_ids.intersection(lean_only_resource_ids)
    assert "lean_realization_dag_nodes" not in request["required_output_contract"]
    assert request["context_packet"]["legacy_context_field_aliases"] == {}
    assert request["context_packet"]["context_packet_inventory"][
        "legacy_context_field_alias_count"
    ] == 0
    rocq_schema = llm_route_planner_response_payload_schema(
        target_prover_family="rocq"
    )
    assert rocq_schema["anyOf"] == [{"required": ["formal_realization_dag_nodes"]}]
    assert "lean_realization_dag_nodes" not in rocq_schema["properties"]
    lean_schema = llm_route_planner_response_payload_schema(
        target_prover_family="lean4"
    )
    assert {"required": ["lean_realization_dag_nodes"]} in lean_schema["anyOf"]
    assert "lean_realization_dag_nodes" in lean_schema["properties"]
    prompt_text = request["prompt_messages"]["user"]
    assert "target-prover realization DAG" in prompt_text
    assert "Lean/prover realization DAG" not in prompt_text
    assert "target-prover effort" in prompt_text
    assert "Lean/prover effort" not in prompt_text
    assert "lean_realization_dag_nodes" not in prompt_text
    assert "lean_grounding_queries" not in prompt_text
    for lean_only_id in lean_only_adapter_ids:
        assert lean_only_id not in prompt_text


def test_llm_route_planner_accepts_registry_bound_actions_without_queue() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_registry_bound_static"
    )
    out_dir = root / "llm_route_planner"
    registry_dir = root / "component_resource_registry"
    response_json = root / "response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    export_formalization_gap_planner_component_resource_registry(registry_dir)
    response_json.write_text(json.dumps(_llm_response_payload()), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        provider_name="static",
        static_response_json=response_json,
        formalization_gap_planner_component_resource_registry_dir=registry_dir,
    )

    assert payload["all_ok"]
    row = payload["rows"][0]
    assert row["response_contract_ok"] is True
    assert row["planner_next_actions"][0]["owner"] == "lean_lsp_mcp"


def test_llm_route_planner_rejects_unregistered_formal_attempt_queue_resource() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_bad_attempt_queue_resource"
    )
    out_dir = root / "llm_route_planner"
    registry_dir = root / "component_resource_registry"
    response_json = root / "response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    export_formalization_gap_planner_component_resource_registry(registry_dir)
    response = _llm_response_payload()
    response["formal_attempt_queue"][0]["resource_id"] = "invented_prover_mcp"
    response_json.write_text(json.dumps(response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        provider_name="static",
        static_response_json=response_json,
        formalization_gap_planner_component_resource_registry_dir=registry_dir,
    )

    assert not payload["all_ok"]
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    assert any(
        "formal_attempt_queue[0] references resource_id(s) not present "
        "in request queue or registry context" in error
        and "invented_prover_mcp" in error
        for error in row["errors"]
    )


def test_llm_route_planner_rejects_missing_delta_action_witness() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_missing_delta_action"
    )
    response_json = root / "bad_response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    bad_response = _llm_response_payload()
    minimal_delta = bad_response["minimal_delta_plan"]
    assert isinstance(minimal_delta, dict)
    minimal_delta["bridge_lemmas"] = []
    response_json.write_text(json.dumps(bad_response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        provider_name="static",
        static_response_json=response_json,
    )

    assert not payload["all_ok"]
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    witness = row["realization_coverage_witness"]
    assert witness["delta_action_witness_missing_primitives"] == [
        "rank_uniformity"
    ]
    assert witness["delta_action_witness_complete"] is False
    assert witness["realization_coverage_complete"] is False
    assert payload["n_delta_action_witness_missing_primitives"] == 1
    assert any(
        "selected primitive rank_uniformity requires actionable action witness in bridge_lemmas"
        in error
        for error in row["errors"]
    )


def test_llm_route_planner_rejects_placeholder_delta_action_witness() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_placeholder_delta_action"
    )
    response_json = root / "bad_response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    bad_response = _llm_response_payload()
    minimal_delta = bad_response["minimal_delta_plan"]
    assert isinstance(minimal_delta, dict)
    minimal_delta["bridge_lemmas"] = ["rank_uniformity"]
    response_json.write_text(json.dumps(bad_response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        provider_name="static",
        static_response_json=response_json,
    )

    assert not payload["all_ok"]
    row = payload["rows"][0]
    witness = row["realization_coverage_witness"]
    assert witness["delta_action_witness_missing_primitives"] == [
        "rank_uniformity"
    ]
    assert witness["delta_action_witness_complete"] is False
    assert witness["missing_delta_action_witnesses"][0][
        "placeholder_action_fields"
    ] == ["bridge_lemmas"]
    assert witness["missing_delta_action_witnesses"][0][
        "placeholder_action_items_by_field"
    ] == {"bridge_lemmas": ["rank_uniformity"]}
    assert any(
        "selected primitive rank_uniformity requires actionable action witness in bridge_lemmas"
        in error
        for error in row["errors"]
    )


def test_llm_route_planner_materializes_action_only_refinement_hooks() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_action_only_hooks"
    )
    out_dir = root / "llm_route_planner"
    registry_dir = root / "component_resource_registry"
    response_json = root / "response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    export_formalization_gap_planner_component_resource_registry(registry_dir)
    response = _llm_response_payload()
    response["search_requests"] = []
    response["uncertainty_flags"] = []
    response["semantic_alignment_risks"] = []
    response["planner_next_actions"] = [
        {
            "owner": "lean_lsp_mcp",
            "action": "attempt focused proof-state feedback for rank_uniformity",
            "query": "residual goals after exchangeability reuse",
            "target_primitives": ["rank_uniformity"],
            "resource_id": "lean_lsp_mcp",
        }
    ]
    response_json.write_text(json.dumps(response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        provider_name="static",
        static_response_json=response_json,
        formalization_gap_planner_component_resource_registry_dir=registry_dir,
    )

    assert payload["all_ok"]
    assert payload["n_search_requests"] == 0
    assert payload["n_planner_next_actions"] == 1
    assert payload["n_rows_with_planner_next_actions"] == 1
    assert payload["by_acceptance_status"] == {
        "ACCEPTED_WITH_PLANNER_NEXT_ACTIONS": 1
    }
    row = payload["rows"][0]
    assert row["acceptance_status"] == "ACCEPTED_WITH_PLANNER_NEXT_ACTIONS"
    seed_route = payload["standalone_seed"]["routes"][0]
    assert (
        seed_route["llm_route_planner_acceptance_status"]
        == "ACCEPTED_WITH_PLANNER_NEXT_ACTIONS"
    )
    assert (
        seed_route["replan_metadata"]["llm_route_planner_acceptance_status"]
        == "ACCEPTED_WITH_PLANNER_NEXT_ACTIONS"
    )
    hook = seed_route["interactive_refinement_hooks"][0]
    assert hook["hook_kind"] == "proof_state_feedback"
    assert hook["llm_route_planner_planner_next_action_index"] == 0
    assert hook["target_primitives"] == ["rank_uniformity"]
    assert "lean_lsp_mcp" in hook["resource_ids"]
    assert hook["resource_request_bindings"][0]["resource_id"] == "lean_lsp_mcp"
    assert "residual goals after exchangeability reuse" in " ".join(hook["queries"])
    trigger = seed_route["route_revision_triggers"][0]
    assert trigger["trigger_kind"] == "blocked_by_formal_side_condition"
    assert "lean_lsp_mcp" in trigger["resource_ids"]

    plan_dir = root / "standalone_plan_from_action_only_llm_seed"
    refinement_queue_dir = root / "refinement_queue_from_action_only_llm_seed"
    plan_payload = export_formalization_gap_planner_standalone_plan(
        out_dir / "formalization_gap_planner_llm_route_planner_standalone_seed.json",
        plan_dir,
    )
    assert plan_payload["all_ok"]
    plan_row = plan_payload["rows"][0]
    plan_hook = next(
        hook
        for hook in plan_row["interactive_refinement_hooks"]
        if hook.get("llm_route_planner_planner_next_action_index") == 0
    )
    assert plan_hook["hook_kind"] == "proof_state_feedback"
    assert plan_hook["target_primitives"] == ["rank_uniformity"]
    queue_payload = export_formalization_gap_planner_refinement_queue(
        plan_dir,
        refinement_queue_dir,
    )
    assert queue_payload["all_ok"]
    queue_row = next(
        row
        for row in queue_payload["rows"]
        if row.get("hook_kind") == "proof_state_feedback"
        and "lean_lsp_mcp" in row.get("resource_ids", ())
        and row["llm_route_planner_hook_trace"].get(
            "llm_route_planner_planner_next_action_index"
        )
        == 0
    )
    assert "residual goals after exchangeability reuse" in " ".join(queue_row["queries"])
    assert tuple(queue_row["target_primitives"]) == ("rank_uniformity",)
    hook_trace = queue_row["llm_route_planner_hook_trace"]
    assert hook_trace["trace_kind"] == "llm_route_planner_hook_trace"
    assert hook_trace["llm_route_planner_planner_next_action_index"] == 0
    assert hook_trace["llm_route_planner_planner_next_action"]["owner"] == "lean_lsp_mcp"
    adapter_dir = root / "adapter_responses_from_action_only_llm_seed"
    evidence_dir = root / "refinement_evidence_from_action_only_llm_seed"
    adapter_payload = export_formalization_gap_planner_refinement_adapter_responses(
        refinement_queue_dir,
        adapter_dir,
    )
    assert adapter_payload["all_ok"]
    adapter_response = next(
        response
        for response in adapter_payload["responses"]
        if response.get("llm_route_planner_hook_trace") == hook_trace
    )
    assert tuple(adapter_response["target_primitives"]) == ("rank_uniformity",)
    assert adapter_response["llm_route_planner_hook_trace"] == hook_trace
    evidence_payload = export_formalization_gap_planner_refinement_evidence(
        refinement_queue_dir,
        evidence_dir,
        response_jsonl=adapter_dir
        / "formalization_gap_planner_refinement_evidence_responses.jsonl",
    )
    assert evidence_payload["all_ok"]
    assert evidence_payload["n_rows_with_target_primitives"] >= 1
    evidence_row = next(
        row
        for row in evidence_payload["rows"]
        if row.get("llm_route_planner_hook_trace") == hook_trace
    )
    assert tuple(evidence_row["target_primitives"]) == ("rank_uniformity",)
    assert evidence_row["llm_route_planner_hook_trace"] == hook_trace
    proposal = next(
        row
        for row in evidence_payload["route_revision_proposals"]
        if row.get("llm_route_planner_hook_trace") == hook_trace
    )
    assert tuple(proposal["target_primitives"]) == ("rank_uniformity",)
    assert proposal["llm_route_planner_hook_trace"] == hook_trace
    overlay_dir = root / "route_revision_overlay_from_action_only_llm_seed"
    overlay_payload = export_formalization_gap_planner_route_revision_overlay(
        plan_dir,
        evidence_dir,
        overlay_dir,
    )
    assert overlay_payload["all_ok"]
    assert overlay_payload["n_applied_llm_route_planner_hook_traces"] >= 1
    overlay_row = next(
        row
        for row in overlay_payload["rows"]
        if row.get("applied_llm_route_planner_hook_traces")
    )
    applied_hook_traces = list(overlay_row["applied_llm_route_planner_hook_traces"])
    assert hook_trace in applied_hook_traces
    assert (
        overlay_payload["n_applied_llm_route_planner_hook_traces"]
        == len(applied_hook_traces)
    )
    handoff_dir = root / "route_replan_handoff_from_action_only_llm_seed"
    handoff_payload = export_formalization_gap_planner_route_replan_handoff(
        plan_dir,
        overlay_dir,
        handoff_dir,
    )
    assert handoff_payload["all_ok"]
    assert handoff_payload["n_applied_llm_route_planner_hook_traces"] == len(
        applied_hook_traces
    )
    handoff_row = next(
        row
        for row in handoff_payload["rows"]
        if row.get("applied_llm_route_planner_hook_traces")
    )
    assert list(handoff_row["applied_llm_route_planner_hook_traces"]) == applied_hook_traces
    handoff_seed_route = handoff_payload["standalone_seed"]["routes"][0]
    assert handoff_seed_route["replan_metadata"][
        "applied_llm_route_planner_hook_traces"
    ] == applied_hook_traces
    replan_prompt_dir = root / "llm_route_planner_from_action_only_handoff"
    replan_prompt_payload = export_formalization_gap_planner_llm_route_planner(
        handoff_dir / "formalization_gap_planner_route_replan_standalone_seed.json",
        replan_prompt_dir,
        provider_name="prompt_only",
        formalization_gap_planner_route_replan_handoff_dir=handoff_dir,
    )
    assert replan_prompt_payload["all_ok"]
    assert (
        replan_prompt_payload[
            "n_feedback_loop_summary_prior_llm_route_planner_hook_traces"
        ]
        == len(applied_hook_traces)
    )
    assert (
        replan_prompt_payload[
            "n_requests_with_feedback_loop_summary_prior_llm_route_planner_hook_traces"
        ]
        == 1
    )
    replan_request = replan_prompt_payload["request_packets"][0]
    replan_feedback_summary = replan_request["context_packet"][
        "feedback_loop_summary"
    ]
    replan_inventory = replan_request["context_packet"]["context_packet_inventory"]
    assert (
        replan_inventory[
            "feedback_loop_summary_prior_llm_route_planner_hook_trace_count"
        ]
        == len(applied_hook_traces)
    )
    assert replan_feedback_summary["prior_replan_metadata"][
        "applied_llm_route_planner_hook_traces"
    ] == applied_hook_traces
    assert (
        "applied_llm_route_planner_hook_traces"
        in replan_request["prompt_messages"]["user"]
    )


def test_llm_route_planner_materializes_formal_attempt_queue_hooks() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_formal_attempt_queue_hooks"
    )
    out_dir = root / "llm_route_planner"
    response_json = root / "response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    response = _llm_response_payload()
    response["search_requests"] = []
    response["planner_next_actions"] = []
    response["uncertainty_flags"] = []
    response["semantic_alignment_risks"] = []
    response_json.write_text(json.dumps(response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        provider_name="static",
        static_response_json=response_json,
    )

    assert payload["all_ok"]
    assert payload["by_acceptance_status"] == {
        "ACCEPTED_WITH_FORMAL_ATTEMPT_QUEUE": 1
    }
    assert payload["n_accepted_route_plans"] == 1
    assert payload["n_accepted_with_formal_attempt_queue"] == 1
    assert payload["n_formal_attempt_queue_items"] == 2
    assert payload["n_route_adoption_ready"] == 0
    assert payload["n_route_adoption_pending_refinement"] == 1
    assert payload["n_route_adoption_pending_formal_attempt_queue_blockers"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "ACCEPTED_WITH_FORMAL_ATTEMPT_QUEUE"
    assert row["route_adoption_status"] == (
        "PENDING_REFINEMENT_BEFORE_ROUTE_ADOPTION"
    )
    assert row["route_adoption_blockers"] == (
        ROUTE_ADOPTION_BLOCKER_FORMAL_ATTEMPT_QUEUE,
    )
    schedule = row["formal_attempt_queue_schedule"]
    assert schedule["n_attempts"] == 2
    assert schedule["n_initial_ready_attempts"] == 1
    assert schedule["n_waiting_for_formal_prerequisite_attempts"] == 1
    assert schedule["n_missing_prerequisite_attempts"] == 0
    assert schedule["has_initial_ready_attempt"] is True
    assert schedule["all_prerequisites_queued"] is True
    assert schedule["bottom_up_schedule_complete"] is True
    assert schedule["initial_ready_attempt_ids"] == ["attempt:exchangeability_reuse"]
    assert schedule["waiting_attempt_ids"] == ["attempt:rank_uniformity_bridge"]
    assert [
        item["dependency_status"]
        for item in schedule["attempt_dependency_rows"]
    ] == ["initial_ready", "waiting_for_formal_prerequisite_attempts"]
    seed_route = payload["standalone_seed"]["routes"][0]
    assert seed_route["llm_route_planner_acceptance_status"] == (
        "ACCEPTED_WITH_FORMAL_ATTEMPT_QUEUE"
    )
    assert seed_route["llm_route_planner_formal_attempt_queue_schedule"] == schedule
    assert seed_route["replan_metadata"][
        "llm_route_planner_formal_attempt_queue_schedule"
    ] == schedule
    queue_hooks = [
        hook
        for hook in seed_route["interactive_refinement_hooks"]
        if "llm_route_planner_formal_attempt_queue_index" in hook
    ]
    assert [
        hook["llm_route_planner_formal_attempt_queue_index"]
        for hook in queue_hooks
    ] == [0, 1]
    assert [hook["formal_node_id"] for hook in queue_hooks] == [
        "formal:exchangeability",
        "formal:rank_uniformity_bridge",
    ]
    assert queue_hooks[1]["prerequisite_formal_node_ids"] == [
        "formal:exchangeability"
    ]
    assert "residual_goals" in queue_hooks[1]["expected_feedback"]
    assert queue_hooks[0]["minimal_delta_action_witness_count"] == 0
    assert queue_hooks[0]["has_minimal_delta_action_witness"] is False
    assert queue_hooks[1]["minimal_delta_action_witness_count"] == 1
    assert queue_hooks[1]["has_minimal_delta_action_witness"] is True
    rank_action_witness = queue_hooks[1]["minimal_delta_action_witnesses"][0]
    assert rank_action_witness["primitive"] == "rank_uniformity"
    assert rank_action_witness["attempt_kind"] == "bridge_proof"
    assert rank_action_witness["action_field"] == "bridge_lemmas"
    assert rank_action_witness["source_label"] == "minimal_delta_plan.bridge_lemmas"
    assert rank_action_witness["action_item"] == (
        "rank_uniformity: prove finite rank uniformity from exchangeability "
        "as the target-prover bridge lemma"
    )
    assert "rank_uniformity" in rank_action_witness["action_item_key"]
    assert "exchangeability" in rank_action_witness["action_item_key"]
    assert any(
        query.startswith("minimal_delta_action_witness: rank_uniformity: prove")
        for query in queue_hooks[1]["queries"]
    )
    queue_triggers = [
        trigger
        for trigger in seed_route["route_revision_triggers"]
        if "llm_route_planner_formal_attempt_queue_index" in trigger
    ]
    assert [
        trigger["llm_route_planner_formal_attempt_queue_index"]
        for trigger in queue_triggers
    ] == [0, 1]
    assert all(
        trigger["trigger_kind"] == "blocked_by_formal_side_condition"
        for trigger in queue_triggers
    )
    assert queue_triggers[1]["minimal_delta_action_witness_count"] == 1
    assert "minimal_delta_action_witness: rank_uniformity: prove" in queue_triggers[
        1
    ]["condition"]

    plan_dir = root / "standalone_plan_from_formal_attempt_queue_seed"
    refinement_queue_dir = root / "refinement_queue_from_formal_attempt_queue_seed"
    plan_payload = export_formalization_gap_planner_standalone_plan(
        out_dir / "formalization_gap_planner_llm_route_planner_standalone_seed.json",
        plan_dir,
    )
    assert plan_payload["all_ok"]
    queue_payload = export_formalization_gap_planner_refinement_queue(
        plan_dir,
        refinement_queue_dir,
    )
    assert queue_payload["all_ok"]
    queue_rows = [
        row
        for row in queue_payload["rows"]
        if row["llm_route_planner_hook_trace"].get(
            "llm_route_planner_formal_attempt_queue_index"
        )
        is not None
    ]
    assert len(queue_rows) == 2
    assert queue_payload["n_formal_attempt_dependency_rows"] == 2
    assert queue_payload["n_formal_attempt_dependency_initial_ready"] == 1
    assert queue_payload["n_formal_attempt_dependency_waiting"] == 1
    assert queue_payload["n_formal_attempt_dependency_missing_prerequisites"] == 0
    exchangeability_attempt_row = next(
        row
        for row in queue_rows
        if row["llm_route_planner_hook_trace"]["formal_node_id"]
        == "formal:exchangeability"
    )
    rank_attempt_row = next(
        row
        for row in queue_rows
        if row["llm_route_planner_hook_trace"]["formal_node_id"]
        == "formal:rank_uniformity_bridge"
    )
    assert exchangeability_attempt_row["formal_attempt_initial_ready"] is True
    assert (
        exchangeability_attempt_row["formal_attempt_dependency_status"]
        == "ready_no_formal_prerequisites"
    )
    assert exchangeability_attempt_row["formal_attempt_queue_index"] == 0
    assert exchangeability_attempt_row["rank"] < rank_attempt_row["rank"]
    assert rank_attempt_row["hook_kind"] == "proof_state_feedback"
    assert tuple(rank_attempt_row["target_primitives"]) == ("rank_uniformity",)
    assert "lean_lsp_mcp" in rank_attempt_row["resource_ids"]
    assert rank_attempt_row["formal_attempt_queue_index"] == 1
    assert rank_attempt_row["formal_attempt_initial_ready"] is False
    assert (
        rank_attempt_row["formal_attempt_dependency_status"]
        == "waiting_for_formal_prerequisite_attempts"
    )
    assert rank_attempt_row["llm_route_planner_hook_trace"][
        "prerequisite_formal_node_ids"
    ] == ["formal:exchangeability"]
    assert rank_attempt_row["llm_route_planner_hook_trace"][
        "minimal_delta_action_witnesses"
    ] == queue_hooks[1]["minimal_delta_action_witnesses"]
    assert (
        rank_attempt_row["llm_route_planner_hook_trace"][
            "minimal_delta_action_witness_count"
        ]
        == 1
    )
    assert tuple(rank_attempt_row["formal_attempt_prerequisite_formal_node_ids"]) == (
        "formal:exchangeability",
    )
    assert tuple(rank_attempt_row["formal_attempt_prerequisite_refinement_item_ids"]) == (
        exchangeability_attempt_row["refinement_item_id"],
    )
    assert tuple(
        rank_attempt_row["formal_attempt_blocking_prerequisite_formal_node_ids"]
    ) == ("formal:exchangeability",)
    assert "expected_feedback: residual_goals" in " ".join(
        rank_attempt_row["queries"]
    )

    adapter_dir = root / "adapter_responses_from_formal_attempt_queue_seed"
    evidence_dir = root / "refinement_evidence_from_formal_attempt_queue_seed"
    adapter_payload = export_formalization_gap_planner_refinement_adapter_responses(
        refinement_queue_dir,
        adapter_dir,
    )
    assert adapter_payload["all_ok"]
    assert adapter_payload["n_formal_attempt_dependency_waiting_responses"] == 1
    adapter_responses_by_item = {
        response["refinement_item_id"]: response
        for response in adapter_payload["responses"]
    }
    exchangeability_response = adapter_responses_by_item[
        exchangeability_attempt_row["refinement_item_id"]
    ]
    rank_response = adapter_responses_by_item[rank_attempt_row["refinement_item_id"]]
    assert exchangeability_response["formal_attempt_queue_index"] == 0
    assert rank_response["attempt_status"] == "waiting_for_formal_prerequisite_attempts"
    assert rank_response["prover_attempt_class"] == "formal_attempt_dependency_waiting"
    assert rank_response["route_revision_recommended"] is False
    assert tuple(rank_response["formal_attempt_blocking_prerequisite_formal_node_ids"]) == (
        "formal:exchangeability",
    )

    evidence_payload = export_formalization_gap_planner_refinement_evidence(
        refinement_queue_dir,
        evidence_dir,
        response_jsonl=adapter_dir
        / "formalization_gap_planner_refinement_evidence_responses.jsonl",
    )
    assert evidence_payload["all_ok"]
    evidence_by_item = {
        row["refinement_item_id"]: row for row in evidence_payload["rows"]
    }
    rank_evidence = evidence_by_item[rank_attempt_row["refinement_item_id"]]
    assert rank_evidence["prover_attempt_status"] == (
        "waiting_for_formal_prerequisite_attempts"
    )
    assert not any(
        proposal["refinement_item_id"] == rank_attempt_row["refinement_item_id"]
        for proposal in evidence_payload["route_revision_proposals"]
    )


def test_llm_route_planner_materializes_explicit_search_target_primitives() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_search_target_primitives"
    )
    out_dir = root / "llm_route_planner"
    response_json = root / "response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    response = _llm_response_payload()
    response["search_requests"] = [
        {
            "request_kind": "literature",
            "query": "deterministic tie handling",
            "reason": "bounded source search for the rank route side condition",
            "target_primitives": ["rank_uniformity"],
        }
    ]
    response["planner_next_actions"] = []
    response_json.write_text(json.dumps(response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        provider_name="static",
        static_response_json=response_json,
    )

    assert payload["all_ok"]
    row = payload["rows"][0]
    assert row["response_contract_ok"] is True
    seed_route = payload["standalone_seed"]["routes"][0]
    hook = next(
        hook
        for hook in seed_route["interactive_refinement_hooks"]
        if hook.get("llm_route_planner_search_request_index") == 0
    )
    assert hook["hook_kind"] == "literature_discovery"
    assert hook["target_primitives"] == ["rank_uniformity"]
    assert hook["llm_route_planner_search_request"]["target_primitives"] == [
        "rank_uniformity"
    ]


def test_llm_route_planner_rejects_ungrounded_search_target_primitives() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_search_target_primitive"
    )
    response_json = root / "bad_response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    bad_response = _llm_response_payload()
    bad_response["search_requests"] = [
        {
            "request_kind": "literature",
            "query": "spectral gap compact operator route",
            "reason": "bad fixture tries to add an unrelated route primitive",
            "target_primitives": ["spectral_gap"],
        }
    ]
    response_json.write_text(json.dumps(bad_response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        provider_name="static",
        static_response_json=response_json,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    assert any(
        "search_requests[0].target_primitives must be drawn from request"
        in error
        and "spectral_gap" in error
        for error in row["errors"]
    )


def test_llm_route_planner_rejects_ungrounded_action_target_primitives() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_action_target_primitive"
    )
    response_json = root / "bad_response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    bad_response = _llm_response_payload()
    bad_response["planner_next_actions"] = [
        {
            "owner": "lean_lsp_mcp",
            "action": "attempt proof-state feedback for a spectral_gap side route",
            "query": "spectral_gap residual goals",
            "target_primitives": ["spectral_gap"],
        }
    ]
    response_json.write_text(json.dumps(bad_response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        provider_name="static",
        static_response_json=response_json,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    assert any(
        "planner_next_actions[0].target_primitives must be drawn from request"
        in error
        and "spectral_gap" in error
        for error in row["errors"]
    )


def test_llm_route_planner_rejects_registry_unavailable_tool_actions() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_registry_unavailable_tool"
    )
    out_dir = root / "llm_route_planner"
    registry_dir = root / "component_resource_registry"
    response_json = root / "response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    export_formalization_gap_planner_component_resource_registry(registry_dir)
    response = _llm_response_payload()
    response["search_requests"] = [
        {
            "request_kind": "literature",
            "query": "rank uniformity exchangeability",
            "reason": "bad fixture invents an unavailable paper tool",
            "resource_id": "invented_paperclip_mcp",
        }
    ]
    response["planner_next_actions"] = [
        {
            "owner": "invented_paperclip_mcp",
            "action": "dispatch invented literature evidence tool",
        }
    ]
    response_json.write_text(json.dumps(response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        provider_name="static",
        static_response_json=response_json,
        formalization_gap_planner_component_resource_registry_dir=registry_dir,
    )

    assert not payload["all_ok"]
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    error_text = "\n".join(row["errors"])
    assert "not present in request queue or registry context" in error_text
    assert "owner/tool is not available" in error_text


def test_llm_route_planner_rejects_unknown_registry_resource_contract_ids() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_registry_bad_contract"
    )
    out_dir = root / "llm_route_planner"
    registry_dir = root / "component_resource_registry"
    response_json = root / "response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    export_formalization_gap_planner_component_resource_registry(registry_dir)
    response = _llm_response_payload()
    response["search_requests"] = [
        {
            "request_kind": "prover_feedback",
            "query": "rank uniformity proof-state residuals",
            "reason": "bad fixture cites a contract not exposed by context",
            "resource_id": "lean_lsp_mcp",
            "resource_contract_ids": ["invented:proof_state_contract"],
        }
    ]
    response["planner_next_actions"] = [
        {
            "owner": "lean_lsp_mcp",
            "action": "attempt the rank_uniformity bridge lemma",
            "resource_contract_ids": ["invented:proof_state_contract"],
        }
    ]
    response_json.write_text(json.dumps(response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        provider_name="static",
        static_response_json=response_json,
        formalization_gap_planner_component_resource_registry_dir=registry_dir,
    )

    assert not payload["all_ok"]
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    error_text = "\n".join(row["errors"])
    assert "references resource_contract_id(s) not present" in error_text
    assert "invented_proof_state_contract" in error_text


def test_llm_route_planner_stages_resource_response_content() -> None:
    root = Path("runs/test_formalization_gap_planner_llm_route_planner_resource_context")
    out_dir = root / "llm_route_planner"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    resource_response_ledger_dir = _write_resource_response_ledger(root)

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        formalization_gap_planner_resource_response_ledger_dir=(
            resource_response_ledger_dir
        ),
    )

    assert payload["all_ok"]
    assert payload["n_requests_with_resource_response_ledger_rows"] == 1
    assert payload["n_requests_with_feedback_loop_summary"] == 1
    assert payload["n_feedback_loop_summary_residual_goals"] == 1
    assert payload["n_feedback_loop_summary_replan_required"] == 1
    assert payload["n_feedback_loop_summary_resource_response_admissible"] == 1
    assert payload["n_feedback_loop_summary_resource_response_status_only"] == 0
    assert payload["n_requests_with_resource_feedback_readiness_summary"] == 1
    assert payload["n_request_resource_feedback_readiness_rows"] == 1
    assert payload["n_request_resource_feedback_reuse_ready_rows"] == 0
    assert payload["n_feedback_loop_summary_source_snippets"] == 1
    assert payload["n_requests_with_available_source_snippets"] == 1
    assert payload["n_request_available_source_snippets"] >= 2
    assert payload["n_requests_with_residual_goal_contexts"] == 1
    assert payload["n_request_residual_goal_contexts"] == 1
    assert payload["n_request_context_residual_goal_contexts"] == 1
    assert payload["n_request_inventory_residual_goal_contexts"] == 1
    request = payload["request_packets"][0]
    context = request["context_packet"]
    inventory = context["context_packet_inventory"]
    assert inventory["row_counts"]["resource_response_ledger_rows"] == 1
    assert inventory["residual_goal_count"] == 1
    assert inventory["residual_goal_context_count"] == 1
    assert inventory["feedback_loop_summary_replan_required"] is True
    residual_contexts = context["residual_goal_contexts"]
    assert len(residual_contexts) == 1
    residual_context = residual_contexts[0]
    assert residual_context["source_kind"] == "resource_response_ledger"
    assert residual_context["residual_goal"] == (
        "rank_uniformity: deterministic tie handling"
    )
    assert residual_context["resource_response_ledger_id"] == (
        "resource-response:rank_route"
    )
    assert residual_context["resource_request_id"] == (
        "resource-request:rank_route"
    )
    assert residual_context["target_primitives"] == ("rank_uniformity",)
    assert residual_context["source_refs"] == ("conformal_prediction_textbook",)
    assert residual_context["evidence_ids"] == ("resource-response:rank_route",)
    assert residual_context["route_repair"].startswith(
        "Apply accepted resource_response_ledger route revision"
    )
    assert residual_context["source_snippets"][0]["source_ref"] == (
        "conformal_prediction_textbook"
    )
    assert "exchangeability implies rank uniformity" in residual_context[
        "source_snippets"
    ][0]["claim"]
    target_context = context["target_theorem_context_packet"]
    assert target_context["residual_goal_context_count"] == 1
    assert target_context["residual_goal_contexts"] == [dict(residual_context)]
    ledger_row = context["resource_response_ledger_rows"][0]
    assert ledger_row["response_present"] is True
    assert ledger_row["response_contract_ok"] is True
    assert ledger_row["minimal_delta_cost_score"] == 40
    assert ledger_row["reuse_readiness_score"] == 70
    assert ledger_row["evidence_readiness_score"] == 90
    assert ledger_row["priority_rationale"] == [
        "coverage_status=bridge_needed",
        "minimal_delta_cost_score=40",
        "reuse_readiness_score=70",
        "evidence_readiness_score=90",
    ]
    assert ledger_row["formal_declaration_hits"] == [
        {
            "declaration": "Probability.rankUniformityBridge",
            "target_prover_family": "lean4",
            "source_field": "formal_declaration_hits",
        }
    ]
    assert any(
        row["declaration"] == "Probability.rankUniformityBridge"
        for row in context["available_formal_declaration_rows"]
    )
    assert "finite-rank uniformity lemma" in ledger_row["response_summary"]
    assert (
        ledger_row["response_payload"]["source_snippets"][0]["source_ref"]
        == "conformal_prediction_textbook"
    )
    assert "Paperclip extracted" in request["prompt_messages"]["user"]
    assert "source_snippets" in request["prompt_messages"]["user"]
    assert any(
        "exchangeability implies rank uniformity" in snippet.get("claim", "")
        for snippet in context["available_source_snippets"]
    )
    summary = context["feedback_loop_summary"]
    assert summary["summary_kind"] == "formalization_gap_planner_feedback_loop_summary"
    readiness_summary = context["resource_feedback_readiness_summary"]
    assert readiness_summary["total_count"] == 1
    assert readiness_summary["light_bridge_or_wrapper_count"] == 1
    assert readiness_summary["average_reuse_readiness_score"] == 70
    assert readiness_summary["average_evidence_readiness_score"] == 90
    assert readiness_summary["high_priority_rows"][0]["resource_request_id"] == (
        "resource-request:rank_route"
    )
    assert summary["resource_feedback_readiness_summary"] == readiness_summary
    assert summary["residual_goals"] == ["rank_uniformity: deterministic tie handling"]
    assert summary["evidence_counts"]["resource_response_ledger_rows"] == 1
    assert summary["resource_response_admissibility"] == {
        "total_count": 1,
        "admissible_count": 1,
        "status_only_count": 0,
        "admissible_request_ids": ["resource-request:rank_route"],
        "status_only_request_ids": [],
        "rejected_request_ids": [],
        "awaiting_request_ids": [],
        "absent_response_request_ids": [],
        "failed_contract_request_ids": [],
        "request_playbook_present_count": 1,
        "playbook_grounded_count": 1,
        "playbook_grounding_failed_count": 0,
        "playbook_grounded_request_ids": ["resource-request:rank_route"],
        "playbook_grounding_failed_request_ids": [],
    }
    assert summary["response_acceptance_status_counts"] == {
        "ACCEPTED_WITH_ROUTE_REVISION": 1
    }
    assert summary["replan_required"] is True
    assert summary["route_revision_reasons"] == [
        "add deterministic tie-breaking assumption"
    ]
    assert summary["recommended_next_actions"][0]["source"] == (
        "resource_response_ledger"
    )
    assert summary["recommended_next_actions"][0]["resource_request_id"] == (
        "resource-request:rank_route"
    )
    assert summary["recommended_next_actions"][0]["acceptance_status"] == (
        "ACCEPTED_WITH_ROUTE_REVISION"
    )
    assert summary["recommended_next_actions"][0]["minimal_delta_cost_score"] == 40
    assert summary["recommended_next_actions"][0]["reuse_readiness_score"] == 70
    route_brief = context["route_planning_brief"]
    assert route_brief["evidence_summary"]["residual_goal_context_count"] == 1
    assert route_brief["evidence_summary"]["resource_feedback_readiness_row_count"] == 1
    assert route_brief["evidence_summary"][
        "resource_feedback_light_bridge_or_wrapper_count"
    ] == 1
    assert route_brief["evidence_summary"][
        "resource_feedback_average_evidence_readiness_score"
    ] == 90
    assert {
        focus["focus_id"] for focus in route_brief["planner_focus"]
    } >= {
        "preserve_resource_feedback_minimal_delta_priority",
        "repair_from_residual_goal_contexts",
    }
    assert inventory["resource_feedback_readiness_summary_present"] is True
    assert inventory["resource_feedback_readiness_row_count"] == 1
    assert inventory["resource_feedback_readiness_reuse_ready_count"] == 0
    assert summary["admissible_source_refs"] == ["conformal_prediction_textbook"]
    assert summary["admissible_source_snippets"][0]["source_ref"] == (
        "conformal_prediction_textbook"
    )
    assert "exchangeability implies rank uniformity" in summary[
        "admissible_source_snippets"
    ][0]["claim"]
    assert "feedback_loop_summary" in request["prompt_messages"]["user"]
    assert "residual_goal_contexts" in request["prompt_messages"]["user"]
    assert "resource_feedback_readiness_summary" in request["prompt_messages"]["user"]
    assert "status-only; do not use them as residual-goal" in request[
        "prompt_messages"
    ]["user"]
    assert "Accepted context_packet.resource_response_ledger_rows" in request[
        "prompt_messages"
    ]["user"]
    assert "preserve available resource_response_ledger_id" in request[
        "prompt_messages"
    ]["user"]
    assert "prover-feedback provenance ids or diagnostic signatures" in request[
        "prompt_messages"
    ]["user"]


def test_llm_route_planner_stages_source_theorem_feedback_rows() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_source_theorem_feedback"
    )
    out_dir = root / "llm_route_planner"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    feedback_dirs = _write_source_theorem_planner_feedback(root)

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        source_theorem_semantic_primitive_bridge_dir=feedback_dirs[
            "semantic_bridge"
        ],
        source_theorem_semantic_primitive_from_proof_body_executor_work_orders_dir=(
            feedback_dirs["semantic_from_executor"]
        ),
        source_theorem_formal_environment_bridge_dir=feedback_dirs[
            "formal_environment"
        ],
        exact_source_theorem_proof_body_executor_dir=feedback_dirs[
            "proof_body_executor"
        ],
    )

    assert payload["all_ok"]
    assert payload[
        "n_requests_with_source_theorem_semantic_primitive_rows"
    ] == 1
    assert payload["n_request_source_theorem_semantic_primitive_rows"] == 1
    assert payload[
        "n_requests_with_proof_body_semantic_primitive_work_order_rows"
    ] == 1
    assert payload[
        "n_request_proof_body_semantic_primitive_work_order_rows"
    ] == 1
    assert payload[
        "n_requests_with_source_theorem_formal_environment_rows"
    ] == 1
    assert payload["n_request_source_theorem_formal_environment_rows"] == 1
    assert payload[
        "n_requests_with_source_theorem_proof_body_execution_result_rows"
    ] == 1
    assert payload[
        "n_request_source_theorem_proof_body_execution_result_rows"
    ] == 1

    request = payload["request_packets"][0]
    context = request["context_packet"]
    inventory = context["context_packet_inventory"]
    assert inventory["row_counts"][
        "source_theorem_semantic_primitive_rows"
    ] == 1
    assert inventory["row_counts"][
        "proof_body_semantic_primitive_work_order_rows"
    ] == 1
    assert inventory["row_counts"][
        "source_theorem_formal_environment_rows"
    ] == 1
    assert inventory["row_counts"][
        "source_theorem_proof_body_execution_result_rows"
    ] == 1
    assert payload["n_request_context_inventory_total_rows"] == inventory[
        "total_context_rows"
    ]

    semantic_work_order = context[
        "proof_body_semantic_primitive_work_order_rows"
    ][0]
    assert semantic_work_order["target_theorem_name"] == (
        "distribution_free_rank_bound"
    )
    assert semantic_work_order["source_theorem_target_provenance"][
        "source_theorem_route_id"
    ] == "rank_route"
    assert semantic_work_order["proof_body_goal_excerpt"] == [
        "|- rank statistic is uniformly distributed"
    ]
    formal_environment_row = context[
        "source_theorem_formal_environment_rows"
    ][0]
    assert formal_environment_row["missing_formal_symbols"] == [
        "OrderStatisticQuantileSemantics"
    ]
    proof_body_row = context[
        "source_theorem_proof_body_execution_result_rows"
    ][0]
    assert proof_body_row["failure_classification"] == (
        "formal_environment_placeholder_primitives"
    )
    assert proof_body_row["source_theorem_kernel_verified"] is False
    summary = context["feedback_loop_summary"]
    assert summary["replan_required"] is True
    assert summary["evidence_counts"]["source_theorem_semantic_primitive_rows"] == 1
    assert summary["evidence_counts"][
        "proof_body_semantic_primitive_work_order_rows"
    ] == 1
    assert summary["evidence_counts"]["source_theorem_formal_environment_rows"] == 1
    assert summary["evidence_counts"][
        "source_theorem_proof_body_execution_result_rows"
    ] == 1
    source_theorem_feedback = summary["source_theorem_feedback"]
    assert source_theorem_feedback["total_count"] == 4
    assert source_theorem_feedback["unverified_semantic_primitive_row_count"] == 2
    assert source_theorem_feedback["proof_body_execution_failure_count"] == 1
    assert source_theorem_feedback["formal_environment_blocker_count"] == 3
    assert source_theorem_feedback["replan_required"] is True
    assert source_theorem_feedback["semantic_primitive_ids"] == [
        "exchangeability_to_uniform_rank_semantics",
        "order_statistic_quantile_semantics",
    ]
    assert source_theorem_feedback["target_primitives"] == ["rank_uniformity"]
    assert source_theorem_feedback["placeholder_symbols"] == [
        "OrderStatisticQuantileSemantics"
    ]
    assert source_theorem_feedback["missing_formal_symbols"] == [
        "OrderStatisticQuantileSemantics"
    ]
    assert source_theorem_feedback["typeclass_blockers"] == ["DecidableEq score"]
    assert {
        tuple(action.get("target_primitives", []))
        for action in summary["recommended_next_actions"]
        if action["source"]
        in {
            "source_theorem_semantic_primitive_rows",
            "proof_body_semantic_primitive_work_order_rows",
            "source_theorem_formal_environment_rows",
            "source_theorem_proof_body_execution_result_rows",
        }
    } == {("rank_uniformity",)}
    assert {
        action["source"] for action in summary["recommended_next_actions"]
    } >= {
        "source_theorem_semantic_primitive_rows",
        "proof_body_semantic_primitive_work_order_rows",
        "source_theorem_formal_environment_rows",
        "source_theorem_proof_body_execution_result_rows",
    }
    brief = context["route_planning_brief"]
    assert brief["evidence_summary"]["source_theorem_feedback_row_count"] == 4
    assert brief["evidence_summary"][
        "source_theorem_feedback_proof_body_execution_failure_count"
    ] == 1
    assert brief["evidence_summary"][
        "source_theorem_feedback_formal_environment_blocker_count"
    ] == 3
    assert brief["evidence_summary"][
        "source_theorem_feedback_replan_required"
    ] is True
    generic_feedback_focus = next(
        focus
        for focus in brief["planner_focus"]
        if focus["focus_id"] == "revise_route_from_feedback"
    )
    assert generic_feedback_focus["target_primitives"] == ["rank_uniformity"]
    assert "exchangeability_to_uniform_rank_semantics" not in (
        generic_feedback_focus["target_primitives"]
    )
    source_theorem_focus = next(
        focus
        for focus in brief["planner_focus"]
        if focus["focus_id"] == "repair_source_theorem_feedback"
    )
    assert source_theorem_focus["target_primitives"] == ["rank_uniformity"]
    assert "exchangeability_to_uniform_rank_semantics" not in (
        source_theorem_focus["target_primitives"]
    )
    source_theorem_gap = next(
        gap
        for gap in brief["evidence_gaps"]
        if gap["gap_id"] == "source_theorem_feedback_requires_repair"
    )
    assert source_theorem_gap["target_primitives"] == ["rank_uniformity"]
    assert "order_statistic_quantile_semantics" not in (
        source_theorem_gap["target_primitives"]
    )
    decision_evidence = request["model_tier_decision_evidence"]
    assert decision_evidence["decision_basis"] == "auto_sonnet_triggers"
    assert decision_evidence["route_signal_counts"][
        "source_theorem_feedback_row_count"
    ] == 4
    assert decision_evidence["route_signal_counts"][
        "source_theorem_proof_body_execution_failure_count"
    ] == 1
    assert decision_evidence["route_signal_counts"][
        "source_theorem_formal_environment_blocker_count"
    ] == 3
    assert decision_evidence["source_theorem_feedback_counts"][
        "proof_body_execution_failure_count"
    ] == 1
    assert any(
        "source-theorem proof-body execution failure" in trigger
        for trigger in decision_evidence["sonnet_triggers"]
    )
    assert any(
        "source-theorem formal-environment blocker" in trigger
        for trigger in decision_evidence["sonnet_triggers"]
    )
    prompt = request["prompt_messages"]["user"]
    assert "source_theorem_semantic_primitive_rows" in prompt
    assert "source_theorem_formal_environment_rows" in prompt
    assert "proof-body feedback for route repair" in prompt
    assert "not theorem proof evidence" in prompt
    assert validate_llm_route_planner_request(request) == []

    drifted_request = deepcopy(request)
    drifted_request["context_packet"]["context_packet_inventory"]["row_counts"][
        "proof_body_semantic_primitive_work_order_rows"
    ] = 0
    assert (
        "context_packet.context_packet_inventory.row_counts."
        "proof_body_semantic_primitive_work_order_rows "
        "must match context_packet."
        "proof_body_semantic_primitive_work_order_rows"
        in validate_llm_route_planner_request(drifted_request)
    )

    drifted_manifest = deepcopy(payload)
    drifted_manifest[
        "n_request_source_theorem_proof_body_execution_result_rows"
    ] = 0
    assert (
        "n_request_source_theorem_proof_body_execution_result_rows "
        "must match request_packets"
        in validate_llm_route_planner_manifest(drifted_manifest)
    )


def test_llm_route_planner_filters_lean_source_theorem_feedback_for_rocq_target() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_source_theorem_feedback_rocq"
    )
    out_dir = root / "llm_route_planner"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    input_payload = json.loads(input_json.read_text(encoding="utf-8"))
    input_payload["target_prover_family"] = "rocq"
    input_payload["library_snapshot_ref"] = "rocq_probability_snapshot"
    input_payload["routes"][0]["target_prover_family"] = "rocq"
    input_payload["routes"][0]["library_snapshot_ref"] = "rocq_probability_snapshot"
    input_json.write_text(json.dumps(input_payload, indent=2), encoding="utf-8")
    feedback_dirs = _write_source_theorem_planner_feedback(root)

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        source_theorem_semantic_primitive_bridge_dir=feedback_dirs[
            "semantic_bridge"
        ],
        source_theorem_semantic_primitive_from_proof_body_executor_work_orders_dir=(
            feedback_dirs["semantic_from_executor"]
        ),
        source_theorem_formal_environment_bridge_dir=feedback_dirs[
            "formal_environment"
        ],
        exact_source_theorem_proof_body_executor_dir=feedback_dirs[
            "proof_body_executor"
        ],
    )

    assert payload["all_ok"]
    assert payload[
        "n_requests_with_source_theorem_semantic_primitive_rows"
    ] == 0
    assert payload["n_request_source_theorem_semantic_primitive_rows"] == 0
    assert payload[
        "n_requests_with_proof_body_semantic_primitive_work_order_rows"
    ] == 0
    assert (
        payload["n_request_proof_body_semantic_primitive_work_order_rows"] == 0
    )
    assert (
        payload["n_requests_with_source_theorem_formal_environment_rows"] == 0
    )
    assert payload["n_request_source_theorem_formal_environment_rows"] == 0
    assert (
        payload[
            "n_requests_with_source_theorem_proof_body_execution_result_rows"
        ]
        == 0
    )
    assert payload[
        "n_request_source_theorem_proof_body_execution_result_rows"
    ] == 0

    request = payload["request_packets"][0]
    context = request["context_packet"]
    assert context["target_prover_family"] == "rocq"
    for field_name in (
        "source_theorem_semantic_primitive_rows",
        "proof_body_semantic_primitive_work_order_rows",
        "source_theorem_formal_environment_rows",
        "source_theorem_proof_body_execution_result_rows",
    ):
        assert not context[field_name]
        assert context["context_packet_inventory"]["row_counts"][field_name] == 0
    assert (
        context["feedback_loop_summary"]
        .get("source_theorem_feedback", {})
        .get("total_count", 0)
        == 0
    )
    prompt = request["prompt_messages"]["user"]
    assert "OrderStatisticQuantileSemantics" not in prompt
    assert "exchangeability_to_uniform_rank_semantics" not in prompt
    assert validate_llm_route_planner_request(request) == []


def test_llm_route_planner_routes_source_theorem_feedback_hooks() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_source_theorem_feedback_hooks"
    )
    out_dir = root / "llm_route_planner"
    response_json = root / "response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    feedback_dirs = _write_source_theorem_planner_feedback(root)
    response = _llm_response_payload()
    response["search_requests"] = []
    response["planner_next_actions"] = []
    response["uncertainty_flags"] = []
    response["semantic_alignment_risks"] = []
    response["residual_interpretations"] = []
    response_json.write_text(json.dumps(response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        provider_name="static",
        static_response_json=response_json,
        source_theorem_semantic_primitive_bridge_dir=feedback_dirs[
            "semantic_bridge"
        ],
        source_theorem_semantic_primitive_from_proof_body_executor_work_orders_dir=(
            feedback_dirs["semantic_from_executor"]
        ),
        source_theorem_formal_environment_bridge_dir=feedback_dirs[
            "formal_environment"
        ],
        exact_source_theorem_proof_body_executor_dir=feedback_dirs[
            "proof_body_executor"
        ],
    )

    assert payload["all_ok"]
    assert payload["n_response_contract_ok"] == 1
    assert payload["n_route_adoption_ready"] == 0
    assert payload["n_route_adoption_pending_refinement"] == 1
    assert payload["n_route_adoption_pending_feedback_action_blockers"] == 1
    assert payload["n_route_adoption_pending_feedback_replan_blockers"] == 1
    row = payload["rows"][0]
    assert set(row["route_adoption_blockers"]) >= {
        "feedback_summary_actions_pending_resolution",
        "feedback_loop_replan_required",
    }
    seed_route = payload["standalone_seed"]["routes"][0]
    feedback_hooks = [
        hook
        for hook in seed_route["interactive_refinement_hooks"]
        if hook.get("llm_route_planner_feedback_next_action", {}).get("source")
        in {
            "source_theorem_semantic_primitive_rows",
            "proof_body_semantic_primitive_work_order_rows",
            "source_theorem_formal_environment_rows",
            "source_theorem_proof_body_execution_result_rows",
        }
    ]
    hook_kind_by_source = {
        hook["llm_route_planner_feedback_next_action"]["source"]: hook["hook_kind"]
        for hook in feedback_hooks
    }
    assert hook_kind_by_source == {
        "source_theorem_semantic_primitive_rows": "proof_state_feedback",
        "proof_body_semantic_primitive_work_order_rows": "proof_state_feedback",
        "source_theorem_formal_environment_rows": "formal_library_grounding",
        "source_theorem_proof_body_execution_result_rows": "route_revision",
    }
    assert {
        tuple(hook.get("target_primitives", []))
        for hook in feedback_hooks
    } == {("rank_uniformity",)}
    assert {
        tuple(
            hook["llm_route_planner_feedback_next_action"].get(
                "target_primitives", []
            )
        )
        for hook in feedback_hooks
    } == {("rank_uniformity",)}
    assert "literature_discovery" not in set(hook_kind_by_source.values())
    assert any(
        "distribution-free rank bound follows from exchangeability"
        in " ".join(hook.get("queries", []))
        for hook in feedback_hooks
        if hook["hook_kind"] == "proof_state_feedback"
    )
    trigger_sources = {
        trigger.get("llm_route_planner_feedback_next_action", {}).get("source")
        for trigger in seed_route["route_revision_triggers"]
        if trigger.get("llm_route_planner_feedback_next_action", {}).get("source")
    }
    assert trigger_sources >= {
        "source_theorem_semantic_primitive_rows",
        "proof_body_semantic_primitive_work_order_rows",
        "source_theorem_formal_environment_rows",
        "source_theorem_proof_body_execution_result_rows",
    }
    feedback_triggers = [
        trigger
        for trigger in seed_route["route_revision_triggers"]
        if trigger.get("llm_route_planner_feedback_next_action", {}).get("source")
        in {
            "source_theorem_semantic_primitive_rows",
            "proof_body_semantic_primitive_work_order_rows",
            "source_theorem_formal_environment_rows",
            "source_theorem_proof_body_execution_result_rows",
        }
    ]
    assert {
        tuple(trigger.get("target_primitives", []))
        for trigger in feedback_triggers
    } == {("rank_uniformity",)}


def test_llm_route_planner_materializes_bare_feedback_replan_required() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_bare_feedback_replan"
    )
    out_dir = root / "llm_route_planner"
    response_json = root / "response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    resource_response_ledger_dir = _write_resource_response_ledger(root)
    manifest_path = (
        resource_response_ledger_dir
        / "formalization_gap_planner_resource_response_ledger_manifest.json"
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    row = manifest["rows"][0]
    row["acceptance_status"] = "ACCEPTED_RESOURCE_RESPONSE"
    row["route_revision_recommended"] = False
    row["route_revision_reasons"] = []
    row["residual_goals"] = []
    row["replan_required"] = True
    row["response_payload"]["route_revision_recommended"] = False
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    response = _llm_response_payload()
    response["search_requests"] = []
    response["planner_next_actions"] = []
    response["uncertainty_flags"] = []
    response["semantic_alignment_risks"] = []
    response["residual_interpretations"] = []
    response_json.write_text(json.dumps(response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        provider_name="static",
        static_response_json=response_json,
        formalization_gap_planner_resource_response_ledger_dir=(
            resource_response_ledger_dir
        ),
    )

    assert payload["all_ok"]
    assert payload["n_route_adoption_ready"] == 0
    assert payload["n_route_adoption_pending_refinement"] == 1
    assert payload["n_route_adoption_pending_feedback_action_blockers"] == 0
    assert payload["n_route_adoption_pending_feedback_replan_blockers"] == 1
    row_payload = payload["rows"][0]
    assert row_payload["route_adoption_blockers"] == (
        "feedback_loop_replan_required",
        ROUTE_ADOPTION_BLOCKER_PRIMITIVE_EVIDENCE_MATRIX,
    )
    assert row_payload["primitive_evidence_matrix_witness"][
        "formal_supported_matrix_primitives_missing_reuse"
    ] == ["rank_uniformity"]
    summary = payload["request_packets"][0]["context_packet"]["feedback_loop_summary"]
    assert summary["replan_required"] is True
    assert summary["recommended_next_actions"] == []
    seed_route = payload["standalone_seed"]["routes"][0]
    replan_hook = next(
        hook
        for hook in seed_route["interactive_refinement_hooks"]
        if hook.get("llm_route_planner_feedback_replan_required") is True
    )
    assert replan_hook["hook_kind"] == "route_revision"
    assert "rank_uniformity" in replan_hook["target_primitives"]
    assert replan_hook["llm_route_planner_feedback_loop_summary"][
        "replan_required"
    ] is True
    assert any(
        trigger.get("trigger_kind") == "feedback_loop_replan_required"
        for trigger in seed_route["route_revision_triggers"]
    )

    plan_dir = root / "standalone_plan_from_bare_feedback_replan_seed"
    refinement_queue_dir = root / "refinement_queue_from_bare_feedback_replan_seed"
    plan_payload = export_formalization_gap_planner_standalone_plan(
        out_dir / "formalization_gap_planner_llm_route_planner_standalone_seed.json",
        plan_dir,
    )
    assert plan_payload["all_ok"]
    queue_payload = export_formalization_gap_planner_refinement_queue(
        plan_dir,
        refinement_queue_dir,
    )
    assert queue_payload["all_ok"]
    queue_row = next(
        row
        for row in queue_payload["rows"]
        if row["hook_kind"] == "route_revision"
        and row["llm_route_planner_hook_trace"].get(
            "llm_route_planner_feedback_replan_required"
        )
        is True
    )
    assert "feedback_loop_replan_required" in queue_row["trigger_kinds"]
    assert "rank_uniformity" in queue_row["target_primitives"]
    assert queue_row["llm_route_planner_hook_trace"][
        "llm_route_planner_feedback_loop_summary"
    ]["recommended_next_actions"] == []


def test_llm_route_planner_materializes_feedback_replan_with_resource_actions() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_feedback_replan_with_actions"
    )
    out_dir = root / "llm_route_planner"
    response_json = root / "response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    resource_request_queue_dir = _write_resource_request_queue(root)
    resource_response_ledger_dir = _write_resource_response_ledger(root)
    manifest_path = (
        resource_response_ledger_dir
        / "formalization_gap_planner_resource_response_ledger_manifest.json"
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    row = manifest["rows"][0]
    row["acceptance_status"] = "ACCEPTED_RESOURCE_RESPONSE"
    row["route_revision_recommended"] = False
    row["route_revision_reasons"] = []
    row["residual_goals"] = []
    row["replan_required"] = True
    row["response_payload"]["route_revision_recommended"] = False
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    response = _llm_response_payload()
    response["search_requests"] = []
    response["planner_next_actions"] = [
        {
            "owner": "paperclip_cli_mcp",
            "action": "dispatch queued rank_uniformity resource response before route replan",
            "resource_request_id": "resource-request:rank_route",
            "resource_id": "paperclip_cli_mcp",
            "target_primitives": ["rank_uniformity"],
        }
    ]
    response["uncertainty_flags"] = []
    response["semantic_alignment_risks"] = []
    response["residual_interpretations"] = []
    response_json.write_text(json.dumps(response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        provider_name="static",
        static_response_json=response_json,
        formalization_gap_planner_resource_request_queue_dir=(
            resource_request_queue_dir
        ),
        formalization_gap_planner_resource_response_ledger_dir=(
            resource_response_ledger_dir
        ),
    )

    assert payload["all_ok"]
    assert payload["n_route_adoption_pending_feedback_action_blockers"] == 1
    assert payload["n_route_adoption_pending_resource_request_queue_blockers"] == 1
    assert payload["n_route_adoption_pending_feedback_replan_blockers"] == 1
    summary = payload["request_packets"][0]["context_packet"]["feedback_loop_summary"]
    assert summary["replan_required"] is True
    assert [
        action["source"] for action in summary["recommended_next_actions"]
    ] == ["resource_request_queue"]
    seed_route = payload["standalone_seed"]["routes"][0]
    assert any(
        hook.get("llm_route_planner_feedback_next_action", {}).get("source")
        == "resource_request_queue"
        for hook in seed_route["interactive_refinement_hooks"]
    )
    assert any(
        hook.get("llm_route_planner_feedback_replan_required") is True
        and hook["hook_kind"] == "route_revision"
        for hook in seed_route["interactive_refinement_hooks"]
    )
    assert any(
        trigger.get("trigger_kind") == "queued_resource_response_required"
        for trigger in seed_route["route_revision_triggers"]
    )
    assert any(
        trigger.get("trigger_kind") == "feedback_loop_replan_required"
        for trigger in seed_route["route_revision_triggers"]
    )

    plan_dir = root / "standalone_plan_from_feedback_replan_with_actions_seed"
    refinement_queue_dir = (
        root / "refinement_queue_from_feedback_replan_with_actions_seed"
    )
    plan_payload = export_formalization_gap_planner_standalone_plan(
        out_dir / "formalization_gap_planner_llm_route_planner_standalone_seed.json",
        plan_dir,
    )
    assert plan_payload["all_ok"]
    queue_payload = export_formalization_gap_planner_refinement_queue(
        plan_dir,
        refinement_queue_dir,
    )
    assert queue_payload["all_ok"]
    assert any(
        row["hook_kind"] == "literature_discovery"
        and "queued_resource_response_required" in row["trigger_kinds"]
        for row in queue_payload["rows"]
    )
    assert any(
        row["hook_kind"] == "route_revision"
        and row["llm_route_planner_hook_trace"].get(
            "llm_route_planner_feedback_replan_required"
        )
        is True
        and "feedback_loop_replan_required" in row["trigger_kinds"]
        for row in queue_payload["rows"]
    )


def test_llm_route_planner_feedback_coverage_updates_raise_cost_hint_floor() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_feedback_cost_hint"
    )
    out_dir = root / "llm_route_planner"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    resource_response_ledger_dir = _write_resource_response_ledger(root)
    input_payload = json.loads(input_json.read_text(encoding="utf-8"))
    input_payload["routes"][0]["primitives"][1]["coverage_status"] = "exact_exists"
    input_json.write_text(json.dumps(input_payload, indent=2), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        formalization_gap_planner_resource_response_ledger_dir=(
            resource_response_ledger_dir
        ),
    )

    assert payload["all_ok"]
    request = payload["request_packets"][0]
    cost_hints = request["context_packet"]["minimal_delta_cost_hints"]
    cost_by_primitive = {
        row["primitive"]: row for row in cost_hints["primitive_cost_hints"]
    }
    rank_hint = cost_by_primitive["rank_uniformity"]
    assert rank_hint["minimum_coverage_bucket"] == "bridge_needed"
    assert rank_hint["minimum_base_cost"] == 4
    assert (
        rank_hint["minimum_cost_source"]
        == "resource_response_ledger_rows.coverage_updates"
    )
    assert rank_hint["minimum_cost_marker"] == "bridge_needed"
    assert {
        (row["declaration"], row["target_prover_family"], row["source_field"])
        for row in rank_hint["candidate_declaration_rows"]
    } >= {
        (
            "Probability.rankUniformityBridge",
            "lean4",
            "formal_declaration_hits",
        )
    }
    assert "Probability.rankUniformityBridge" in rank_hint["candidate_declarations"]


def test_llm_route_planner_cost_hints_preserve_candidate_declaration_scope() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_cost_hint_declaration_scope"
    )
    out_dir = root / "llm_route_planner"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    input_payload = json.loads(input_json.read_text(encoding="utf-8"))
    rank_primitive = input_payload["routes"][0]["primitives"][1]
    declaration_row = {
        "declaration": "Probability.rankUniformityBridge",
        "target_prover_family": "lean4",
        "source_field": "route_level_formal_context",
        "source_fields": [
            "route_level_formal_context",
            "local_formal_source_adapter",
        ],
        "target_primitives": ["rank_uniformity"],
        "supported_target_primitives": ["rank_uniformity"],
        "unsupported_target_primitives": ["exchangeability"],
        "source_refs": ["conformal_prediction_textbook"],
        "matched_terms": ["rank uniformity", "exchangeability"],
    }
    rank_primitive["candidate_declaration_rows"] = [declaration_row]
    input_json.write_text(json.dumps(input_payload, indent=2), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
    )

    assert payload["all_ok"]
    request = payload["request_packets"][0]
    cost_hints = request["context_packet"]["minimal_delta_cost_hints"]
    rank_hint = {
        row["primitive"]: row for row in cost_hints["primitive_cost_hints"]
    }["rank_uniformity"]
    scoped_rows = [
        row
        for row in rank_hint["candidate_declaration_rows"]
        if row["declaration"] == "Probability.rankUniformityBridge"
    ]
    assert len(scoped_rows) == 1
    assert scoped_rows[0] == declaration_row
    prompt_text = request["prompt_messages"]["user"]
    assert "supported_target_primitives" in prompt_text
    assert "matched_terms" in prompt_text


def test_llm_route_planner_feedback_cost_hints_ignore_non_lean_legacy_alias() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_rocq_feedback_cost_hint"
    )
    out_dir = root / "llm_route_planner"
    resource_response_dir = root / "resource_response_ledger"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    resource_response_dir.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    input_payload = json.loads(input_json.read_text(encoding="utf-8"))
    input_payload["target_prover_family"] = "rocq"
    input_payload["library_snapshot_ref"] = "rocq_probability_snapshot"
    route = input_payload["routes"][0]
    route["target_prover_family"] = "rocq"
    route["route_id"] = "rocq_rank_route"
    route["primitives"][0]["candidate_declarations"] = [
        "RocqProbability.exchangeable"
    ]
    route["primitives"][1]["coverage_status"] = "exact_exists"
    input_json.write_text(json.dumps(input_payload, indent=2), encoding="utf-8")
    (
        resource_response_dir
        / "formalization_gap_planner_resource_response_ledger_manifest.json"
    ).write_text(
        json.dumps(
            {
                "component_name": "formalization_gap_planner_resource_response_ledger",
                "rows": [
                    {
                        "resource_response_ledger_id": "resource-response:rocq-rank",
                        "resource_request_id": "resource-request:rocq-rank",
                        "goal_plan_id": "goal:rocq_rank_route",
                        "route_id": "rocq_rank_route",
                        "display_name": "distribution_free_rank_bound",
                        "primitive": "rank_uniformity",
                        "target_primitives": ["rank_uniformity"],
                        "target_prover_family": "rocq",
                        "response_present": True,
                        "response_contract_ok": True,
                        "response_contract_minimum_met": True,
                        "formal_declaration_hits": [
                            {
                                "declaration": "RocqProbability.rank_uniformity",
                                "target_prover_family": "rocq",
                                "source_field": "formal_declaration_hits",
                                "target_primitives": ["rank_uniformity"],
                            }
                        ],
                        "lean_declaration_hits": [
                            {
                                "declaration": "Mathlib.Probability.rankUniformity",
                                "target_prover_family": "lean4",
                                "source_field": "lean_declaration_hits",
                                "target_primitives": ["rank_uniformity"],
                            }
                        ],
                        "coverage_updates": {"rank_uniformity": "bridge_needed"},
                        "acceptance_status": "ACCEPTED_WITH_ROUTE_REVISION",
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        formalization_gap_planner_resource_response_ledger_dir=resource_response_dir,
    )

    assert payload["all_ok"]
    request = payload["request_packets"][0]
    cost_hints = request["context_packet"]["minimal_delta_cost_hints"]
    rank_hint = {
        row["primitive"]: row for row in cost_hints["primitive_cost_hints"]
    }["rank_uniformity"]
    assert {
        (row["declaration"], row["target_prover_family"], row["source_field"])
        for row in rank_hint["candidate_declaration_rows"]
    } >= {
        (
            "RocqProbability.rank_uniformity",
            "rocq",
            "formal_declaration_hits",
        )
    }
    assert all(
        row["source_field"] != "lean_declaration_hits"
        for row in rank_hint["candidate_declaration_rows"]
    )
    assert "RocqProbability.rank_uniformity" in rank_hint["candidate_declarations"]
    assert "Mathlib.Probability.rankUniformity" not in rank_hint[
        "candidate_declarations"
    ]


def test_llm_route_planner_merges_declaration_row_provenance_and_scope() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_declaration_row_scope"
    )
    out_dir = root / "llm_route_planner"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    resource_request_queue_dir = _write_resource_request_queue(root)
    resource_response_ledger_dir = _write_resource_response_ledger(root)

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        formalization_gap_planner_resource_request_queue_dir=(
            resource_request_queue_dir
        ),
        formalization_gap_planner_resource_response_ledger_dir=(
            resource_response_ledger_dir
        ),
    )

    assert payload["all_ok"]
    request = payload["request_packets"][0]
    declaration_rows = request["context_packet"]["available_formal_declaration_rows"]
    rank_rows = [
        row
        for row in declaration_rows
        if row["declaration"] == "Probability.rankUniformityBridge"
    ]
    assert len(rank_rows) == 1
    rank_row = rank_rows[0]
    assert rank_row["source_field"] == "formal_declaration_hits"
    assert set(rank_row["source_fields"]) == {
        "resource_request_candidate_declarations",
        "formal_declaration_hits",
    }
    assert rank_row["target_primitives"] == ["rank_uniformity"]
    assert rank_row["supported_target_primitives"] == ["rank_uniformity"]
    prompt_text = request["prompt_messages"]["user"]
    assert "source_fields" in prompt_text
    assert "target_primitives" in prompt_text


def test_llm_route_planner_rejects_reuse_under_feedback_coverage_update() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_rejects_feedback_underprice"
    )
    response_json = root / "bad_response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    resource_response_ledger_dir = _write_resource_response_ledger(root)
    declaration_row = {
        "declaration": "Probability.rankUniformityBridge",
        "target_prover_family": "lean4",
        "source_field": "formal_declaration_hits",
    }
    input_payload = json.loads(input_json.read_text(encoding="utf-8"))
    rank_primitive = input_payload["routes"][0]["primitives"][1]
    rank_primitive["coverage_status"] = "exact_exists"
    rank_primitive["candidate_declaration_rows"] = [declaration_row]
    input_json.write_text(json.dumps(input_payload, indent=2), encoding="utf-8")
    bad_response = _make_rank_uniformity_reuse_response(declaration_row)
    bad_response["residual_interpretations"] = [
        {
            "residual_goal": "rank_uniformity: deterministic tie handling",
            "interpretation": "Accepted feedback says rank uniformity still needs deterministic tie handling.",
            "route_repair": "Keep rank_uniformity as a bridge until the side condition is replayed.",
            "source_refs": ["conformal_prediction_textbook"],
        }
    ]
    response_json.write_text(json.dumps(bad_response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        provider_name="static",
        static_response_json=response_json,
        formalization_gap_planner_resource_response_ledger_dir=(
            resource_response_ledger_dir
        ),
    )

    assert not payload["all_ok"]
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    error_text = "\n".join(row["errors"])
    assert "base_cost underprices request minimal_delta_cost_hints" in error_text
    assert "source=resource_response_ledger_rows.coverage_updates" in error_text


def test_llm_route_planner_feedback_summary_uses_standalone_realization_witness() -> None:
    root = Path("runs/test_formalization_gap_planner_llm_route_planner_realization_feedback")
    out_dir = root / "llm_route_planner"
    plan_dir = root / "goal_plan"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    input_payload = json.loads(input_json.read_text(encoding="utf-8"))
    input_payload["routes"][0]["realization_coverage_witness"] = {
        "selected_primitives": ["exchangeability", "rank_uniformity"],
        "delta_primitives": ["rank_uniformity"],
        "introduced_primitives": [],
        "aligned_primitives": ["exchangeability"],
        "selected_primitives_missing_formal_realization_node": [
            "rank_uniformity"
        ],
        "delta_primitives_missing_route_alignment_edge": ["rank_uniformity"],
        "introduced_primitives_missing_route_alignment_edge": [],
        "realization_coverage_complete": False,
    }
    input_json.write_text(json.dumps(input_payload, indent=2), encoding="utf-8")
    export_formalization_gap_planner_standalone_plan(input_json, plan_dir)

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        goal_conditioned_minimal_formalization_plan_dir=plan_dir,
    )

    assert payload["all_ok"]
    assert payload["n_requests_with_feedback_loop_summary"] == 1
    assert payload["n_feedback_loop_summary_realization_witnesses"] == 1
    assert payload["n_feedback_loop_summary_incomplete_realization_coverage"] == 1
    assert payload["n_feedback_loop_summary_missing_selected_formal_primitives"] == 1
    assert payload["n_feedback_loop_summary_missing_delta_alignment_primitives"] == 1
    request = payload["request_packets"][0]
    context = request["context_packet"]
    goal_plan_row = context["current_goal_plan_rows"][0]
    trace = goal_plan_row["standalone_input_trace"]
    assert trace["has_realization_coverage_witness"] is True
    assert trace["realization_coverage_complete"] is False
    summary = context["feedback_loop_summary"]
    assert summary["replan_required"] is True
    assert summary["needs_more_library_grounding"] is True
    assert summary["realization_coverage"]["complete"] is False
    assert summary["realization_coverage"]["missing_selected_formal_primitives"] == [
        "rank_uniformity"
    ]
    assert summary["realization_coverage"]["missing_delta_alignment_primitives"] == [
        "rank_uniformity"
    ]
    action_by_name = {
        action["action"]: action for action in summary["recommended_next_actions"]
    }
    assert action_by_name[
        "add_or_reformulate_formal_realization_nodes"
    ]["target_primitives"] == ["rank_uniformity"]
    assert action_by_name[
        "add_route_alignment_edges_for_delta_primitives"
    ]["target_primitives"] == ["rank_uniformity"]
    assert "realization_coverage" in request["prompt_messages"]["user"]


def test_llm_route_planner_feedback_summary_repairs_omitted_cost_hint_primitives() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_omitted_cost_hint_feedback"
    )
    out_dir = root / "llm_route_planner"
    plan_dir = root / "goal_plan"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    input_payload = json.loads(input_json.read_text(encoding="utf-8"))
    input_payload["routes"][0]["realization_coverage_witness"] = {
        "selected_primitives": ["exchangeability"],
        "delta_primitives": [],
        "introduced_primitives": [],
        "aligned_primitives": ["exchangeability"],
        "selected_primitives_missing_formal_realization_node": [],
        "delta_primitives_missing_route_alignment_edge": [],
        "introduced_primitives_missing_route_alignment_edge": [],
        "cost_hint_baseline_primitives": ["exchangeability", "rank_uniformity"],
        "omitted_cost_hint_primitives": ["rank_uniformity"],
        "cost_hint_baseline_coverage_complete": False,
        "realization_coverage_complete": True,
    }
    input_json.write_text(json.dumps(input_payload, indent=2), encoding="utf-8")
    export_formalization_gap_planner_standalone_plan(input_json, plan_dir)

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        goal_conditioned_minimal_formalization_plan_dir=plan_dir,
    )

    assert payload["all_ok"]
    assert payload["n_requests_with_feedback_loop_summary"] == 1
    assert payload["n_feedback_loop_summary_realization_witnesses"] == 1
    assert payload["n_feedback_loop_summary_incomplete_realization_coverage"] == 0
    assert (
        payload["n_feedback_loop_summary_incomplete_cost_hint_baseline_coverage"]
        == 1
    )
    assert payload["n_feedback_loop_summary_omitted_cost_hint_primitives"] == 1
    request = payload["request_packets"][0]
    assert request["model_tier"] == "sonnet"
    assert "omitted cost-hint primitive" in request["model_selection_rationale"]
    summary = request["context_packet"]["feedback_loop_summary"]
    assert summary["replan_required"] is True
    assert summary["realization_coverage"]["complete"] is True
    assert (
        summary["realization_coverage"]["cost_hint_baseline_coverage_complete"]
        is False
    )
    assert summary["realization_coverage"]["cost_hint_baseline_primitives"] == [
        "exchangeability",
        "rank_uniformity",
    ]
    assert summary["realization_coverage"]["omitted_cost_hint_primitives"] == [
        "rank_uniformity"
    ]
    action_by_name = {
        action["action"]: action for action in summary["recommended_next_actions"]
    }
    assert action_by_name[
        "review_or_restore_omitted_cost_hint_primitives"
    ]["target_primitives"] == ["rank_uniformity"]
    assert "omitted_cost_hint_primitives" in request["prompt_messages"]["user"]


def test_llm_route_planner_rejected_resource_response_is_status_not_repair_signal() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_rejected_resource_context"
    )
    out_dir = root / "llm_route_planner"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    resource_response_ledger_dir = _write_resource_response_ledger(root)
    manifest_path = (
        resource_response_ledger_dir
        / "formalization_gap_planner_resource_response_ledger_manifest.json"
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    row = manifest["rows"][0]
    row["acceptance_status"] = "REJECTED_MISSING_RESPONSE_CONTRACT_FIELDS"
    row["response_contract_ok"] = False
    row["response_contract_minimum_met"] = False
    row["matched_response_contract_fields"] = []
    row["missing_response_contract_fields"] = ["source_refs", "source_snippets"]
    row["ok"] = False
    row["errors"] = ["resource response missing all queued response_contract_fields"]
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        formalization_gap_planner_resource_response_ledger_dir=(
            resource_response_ledger_dir
        ),
    )

    assert payload["all_ok"]
    assert payload["n_requests_with_resource_response_ledger_rows"] == 1
    assert payload["n_feedback_loop_summary_residual_goals"] == 0
    assert payload["n_feedback_loop_summary_replan_required"] == 0
    assert payload["n_feedback_loop_summary_resource_response_admissible"] == 0
    assert payload["n_feedback_loop_summary_resource_response_status_only"] == 1
    request = payload["request_packets"][0]
    assert request["residual_goals"] == ()
    context = request["context_packet"]
    assert len(context["available_source_snippets"]) == 1
    assert "Paperclip extracted" not in json.dumps(
        context["available_source_snippets"]
    )
    summary = context["feedback_loop_summary"]
    assert summary["evidence_counts"]["resource_response_ledger_rows"] == 1
    assert summary["resource_response_admissibility"] == {
        "total_count": 1,
        "admissible_count": 0,
        "status_only_count": 1,
        "admissible_request_ids": [],
        "status_only_request_ids": ["resource-request:rank_route"],
        "rejected_request_ids": ["resource-request:rank_route"],
        "awaiting_request_ids": [],
        "absent_response_request_ids": [],
        "failed_contract_request_ids": ["resource-request:rank_route"],
        "request_playbook_present_count": 1,
        "playbook_grounded_count": 1,
        "playbook_grounding_failed_count": 0,
        "playbook_grounded_request_ids": ["resource-request:rank_route"],
        "playbook_grounding_failed_request_ids": [],
    }
    assert summary["response_acceptance_status_counts"] == {
        "REJECTED_MISSING_RESPONSE_CONTRACT_FIELDS": 1
    }
    assert summary["residual_goals"] == []
    assert summary["route_revision_reasons"] == []
    assert summary["admissible_source_snippets"] == []
    assert summary["replan_required"] is False
    assert summary["recommended_next_actions"] == []


def test_llm_route_planner_rejects_action_primitive_from_rejected_context_row() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_rejected_context_scope"
    )
    response_json = root / "bad_response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    resource_response_ledger_dir = _write_resource_response_ledger(root)
    manifest_path = (
        resource_response_ledger_dir
        / "formalization_gap_planner_resource_response_ledger_manifest.json"
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    row = manifest["rows"][0]
    row["primitive"] = "spectral_gap"
    row["target_primitives"] = ["spectral_gap"]
    row["coverage_updates"] = {"spectral_gap": "bridge_needed"}
    row["acceptance_status"] = "REJECTED_MISSING_RESPONSE_CONTRACT_FIELDS"
    row["response_contract_ok"] = False
    row["response_contract_minimum_met"] = False
    row["ok"] = False
    row["errors"] = ["resource response missing all queued response_contract_fields"]
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    bad_response = _llm_response_payload()
    bad_response["planner_next_actions"] = [
        {
            "owner": "lean_lsp_mcp",
            "action": "attempt proof-state feedback for rejected spectral_gap row",
            "query": "spectral_gap residual goals",
            "target_primitives": ["spectral_gap"],
        }
    ]
    response_json.write_text(json.dumps(bad_response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        provider_name="static",
        static_response_json=response_json,
        formalization_gap_planner_resource_response_ledger_dir=(
            resource_response_ledger_dir
        ),
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    request = payload["request_packets"][0]
    ledger_row = request["context_packet"]["resource_response_ledger_rows"][0]
    assert "spectral_gap" in json.dumps(ledger_row)
    assert ledger_row["response_contract_ok"] is False
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    assert any(
        "planner_next_actions[0].target_primitives must be drawn from request"
        in error
        and "spectral_gap" in error
        for error in row["errors"]
    )


def test_llm_route_planner_rejected_playbook_grounding_response_requests_redispatch() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_rejected_playbook_grounding"
    )
    out_dir = root / "llm_route_planner"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    resource_response_ledger_dir = _write_resource_response_ledger(root)
    manifest_path = (
        resource_response_ledger_dir
        / "formalization_gap_planner_resource_response_ledger_manifest.json"
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    row = manifest["rows"][0]
    row["acceptance_status"] = "REJECTED_RESPONSE_NOT_GROUNDED_IN_REQUEST_PLAYBOOK"
    row["response_contract_fields"] = [
        "source_refs",
        "source_snippets",
        "route_revision_recommended",
    ]
    row["response_contract_ok"] = False
    row["response_contract_minimum_met"] = True
    row["matched_response_contract_fields"] = ["source_refs", "source_snippets"]
    row["missing_response_contract_fields"] = ["route_revision_recommended"]
    row["request_playbook_present"] = True
    row["response_playbook_grounded"] = False
    row["response_playbook_grounding_terms"] = []
    row["ok"] = False
    row["errors"] = ["resource response is not grounded in request_playbook"]
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        formalization_gap_planner_resource_response_ledger_dir=(
            resource_response_ledger_dir
        ),
    )

    assert payload["all_ok"]
    assert payload["n_requests_with_resource_response_ledger_rows"] == 1
    assert payload["n_feedback_loop_summary_resource_response_admissible"] == 0
    assert payload["n_feedback_loop_summary_resource_response_status_only"] == 1
    request = payload["request_packets"][0]
    summary = request["context_packet"]["feedback_loop_summary"]
    assert summary["resource_response_admissibility"] == {
        "total_count": 1,
        "admissible_count": 0,
        "status_only_count": 1,
        "admissible_request_ids": [],
        "status_only_request_ids": ["resource-request:rank_route"],
        "rejected_request_ids": ["resource-request:rank_route"],
        "awaiting_request_ids": [],
        "absent_response_request_ids": [],
        "failed_contract_request_ids": ["resource-request:rank_route"],
        "request_playbook_present_count": 1,
        "playbook_grounded_count": 0,
        "playbook_grounding_failed_count": 1,
        "playbook_grounded_request_ids": [],
        "playbook_grounding_failed_request_ids": ["resource-request:rank_route"],
    }
    assert summary["replan_required"] is False
    assert summary["admissible_source_snippets"] == []
    assert summary["response_acceptance_status_counts"] == {
        "REJECTED_RESPONSE_NOT_GROUNDED_IN_REQUEST_PLAYBOOK": 1
    }
    assert summary["recommended_next_actions"] == [
        {
            "source": "resource_response_ledger",
            "owner": "paperclip_mcp",
            "action": "redispatch_resource_response_with_request_playbook",
            "resource_request_id": "resource-request:rank_route",
            "primitive": "rank_uniformity",
            "target_primitives": ["rank_uniformity"],
            "acceptance_status": (
                "REJECTED_RESPONSE_NOT_GROUNDED_IN_REQUEST_PLAYBOOK"
            ),
            "reason": "response_present but not grounded in queued request_playbook",
            "response_contract_fields": [
                "source_refs",
                "source_snippets",
                "route_revision_recommended",
            ],
            "matched_response_contract_fields": ["source_refs", "source_snippets"],
            "missing_response_contract_fields": ["route_revision_recommended"],
        }
    ]


def test_llm_route_planner_accepts_source_from_admissible_refinement_evidence() -> None:
    root = Path("runs/test_formalization_gap_planner_llm_route_planner_refinement_source")
    out_dir = root / "llm_route_planner"
    response_json = root / "response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    source_ref = "paper:refinement-evidence#rank-uniformity"
    refinement_evidence_dir = _write_refinement_evidence(
        root,
        source_ref=source_ref,
        accepted=True,
    )
    response = _replace_source_ref(
        _llm_response_payload(),
        "conformal_prediction_textbook",
        source_ref,
    )
    response = _replace_source_snippets(
        response,
        {
            "source_ref": source_ref,
            "claim": "refinement evidence supports finite-rank uniformity",
            "excerpt": (
                "A refinement-evidence snippet states that exchangeability "
                "supports finite-rank uniformity once tie handling is fixed."
            ),
            "target_primitives": ["rank_uniformity"],
            "evidence_role": "source-backed informal route evidence",
        },
    )
    residual_source_snippet = {
        "source_ref": source_ref,
        "claim": "refinement evidence supports finite-rank uniformity",
        "excerpt": (
            "A refinement-evidence snippet states that exchangeability "
            "supports finite-rank uniformity once tie handling is fixed."
        ),
        "target_primitives": ["rank_uniformity"],
        "evidence_role": "source-backed informal route evidence",
    }
    response["residual_interpretations"] = [
        {
            "residual_goal": (
                "rank_uniformity: tie handling side condition from refinement evidence"
            ),
            "interpretation": "The refinement evidence identifies deterministic tie handling as a missing side condition.",
            "route_repair": "Add deterministic tie handling as a source-backed assumption before proving the bridge lemma.",
            "target_primitives": ["rank_uniformity"],
            "source_refs": [source_ref],
            "source_snippets": [residual_source_snippet],
            "source_search_status": "SOURCE_BACKED",
            "refinement_evidence_id": "refinement-evidence:rank_route:accepted",
            "evidence_ids": ["refinement-evidence:rank_route:accepted"],
        }
    ]
    response_json.write_text(json.dumps(response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        provider_name="static",
        static_response_json=response_json,
        formalization_gap_planner_refinement_evidence_dir=refinement_evidence_dir,
    )

    assert payload["all_ok"]
    assert payload["n_response_contract_ok"] == 1
    assert payload["n_requests_with_refinement_evidence_rows"] == 1
    assert payload["n_feedback_loop_summary_refinement_evidence_admissible"] == 1
    assert payload["n_feedback_loop_summary_refinement_evidence_status_only"] == 0
    assert payload["n_feedback_loop_summary_source_snippets"] == 1
    request = payload["request_packets"][0]
    context = request["context_packet"]
    assert source_ref in context["available_source_refs"]
    assert any(
        snippet["source_ref"] == source_ref
        for snippet in context["available_source_snippets"]
    )
    source_snippet = next(
        snippet
        for snippet in context["available_source_snippets"]
        if snippet["source_ref"] == source_ref
    )
    assert source_snippet["source_support_status"] == (
        "source_backed_all_target_primitives"
    )
    assert source_snippet["supported_target_primitives"] == ("rank_uniformity",)
    assert source_snippet["unsupported_target_primitives"] == ()
    assert tuple(request["residual_goals"]) == (
        "rank_uniformity: tie handling side condition from refinement evidence",
    )
    assert payload["n_requests_with_residual_goal_contexts"] == 1
    assert payload["n_request_residual_goal_contexts"] == 1
    residual_context = context["residual_goal_contexts"][0]
    assert residual_context["source_kind"] == "refinement_evidence"
    assert residual_context["target_primitives"] == ("rank_uniformity",)
    assert residual_context["source_refs"] == (source_ref,)
    assert residual_context["refinement_evidence_id"] == (
        "refinement-evidence:rank_route:accepted"
    )
    assert residual_context["evidence_ids"] == (
        "refinement-evidence:rank_route:accepted",
    )
    summary = context["feedback_loop_summary"]
    assert summary["refinement_evidence_admissibility"]["admissible_count"] == 1
    assert summary["admissible_source_snippets"][0]["source_ref"] == source_ref
    assert summary["admissible_source_snippets"][0]["source_support_status"] == (
        "source_backed_all_target_primitives"
    )
    assert "refinement-evidence snippet" in summary["admissible_source_snippets"][0][
        "excerpt"
    ]
    row = payload["rows"][0]
    assert source_ref in row["source_refs"]
    assert row["acceptance_status"] == "ACCEPTED_WITH_SEARCH_REQUESTS"


def test_llm_route_planner_rejected_refinement_evidence_is_status_not_source() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_rejected_refinement_source"
    )
    out_dir = root / "llm_route_planner"
    response_json = root / "response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    rejected_source_ref = "paper:rejected-refinement#rank-uniformity"
    refinement_evidence_dir = _write_refinement_evidence(
        root,
        source_ref=rejected_source_ref,
        accepted=False,
    )
    response = _replace_source_ref(
        _llm_response_payload(),
        "conformal_prediction_textbook",
        rejected_source_ref,
    )
    response_json.write_text(json.dumps(response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        provider_name="static",
        static_response_json=response_json,
        formalization_gap_planner_refinement_evidence_dir=refinement_evidence_dir,
    )

    assert not payload["all_ok"]
    assert payload["n_requests_with_refinement_evidence_rows"] == 1
    assert payload["n_feedback_loop_summary_refinement_evidence_admissible"] == 0
    assert payload["n_feedback_loop_summary_refinement_evidence_status_only"] == 1
    assert payload["n_feedback_loop_summary_source_snippets"] == 0
    request = payload["request_packets"][0]
    context = request["context_packet"]
    assert rejected_source_ref not in context["available_source_refs"]
    assert rejected_source_ref not in {
        snippet["source_ref"] for snippet in context["available_source_snippets"]
    }
    assert request["residual_goals"] == ()
    summary = context["feedback_loop_summary"]
    assert summary["refinement_evidence_admissibility"]["rejected_evidence_ids"] == [
        "refinement-evidence:rank_route:rejected"
    ]
    assert summary["admissible_source_snippets"] == []
    assert summary["route_revision_reasons"] == []
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    assert any("ungrounded source_refs" in error for error in row["errors"])


def test_llm_route_planner_stages_pending_resource_request_queue() -> None:
    root = Path("runs/test_formalization_gap_planner_llm_route_planner_request_queue")
    out_dir = root / "llm_route_planner"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    resource_request_queue_dir = _write_resource_request_queue(root)

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        formalization_gap_planner_resource_request_queue_dir=(
            resource_request_queue_dir
        ),
    )

    assert payload["all_ok"]
    assert payload["n_requests_with_resource_request_queue_rows"] == 1
    assert payload["n_request_resource_request_queue_rows"] == 1
    assert payload["n_requests_with_resource_request_playbooks"] == 1
    assert payload["n_request_resource_request_playbooks"] == 1
    assert payload["n_feedback_loop_summary_resource_request_playbooks"] == 1
    assert payload["n_requests_with_feedback_loop_summary"] == 1
    request = payload["request_packets"][0]
    context = request["context_packet"]
    inventory = context["context_packet_inventory"]
    assert inventory["row_counts"]["resource_request_queue_rows"] == 1
    assert inventory["resource_request_playbook_count"] == 1
    assert inventory["feedback_loop_summary_recommended_next_action_count"] >= 1
    queue_row = context["resource_request_queue_rows"][0]
    assert queue_row["resource_request_id"] == "resource-request:rank_route"
    assert queue_row["resource_id"] == "paperclip_cli_mcp"
    assert queue_row["request_phase"] == "frontier_escalation"
    assert queue_row["acceptance_gate"] == "source_refs_and_snippets_present"
    assert queue_row["response_contract_fields"] == [
        "source_refs",
        "source_snippets",
        "route_revision_recommended",
    ]
    assert "paperclip search" in queue_row["execution_command"]
    assert queue_row["request_playbook"]["operator_prompt"].startswith(
        "Use paperclip_cli_mcp"
    )
    playbook = context["resource_request_playbooks"][0]
    assert playbook["resource_request_id"] == "resource-request:rank_route"
    assert playbook["resource_id"] == "paperclip_cli_mcp"
    assert playbook["primitive"] == "rank_uniformity"
    assert playbook["target_primitives"] == ["rank_uniformity"]
    assert playbook["operator_prompt"] == queue_row["request_playbook"][
        "operator_prompt"
    ]
    assert playbook["expected_response_fields"] == [
        "source_refs",
        "source_snippets",
        "route_revision_recommended",
    ]
    assert "response artifact equals source_evidence" in playbook[
        "acceptance_checklist"
    ]
    declaration_rows = context["available_formal_declaration_rows"]
    assert {
        (
            row["declaration"],
            row["target_prover_family"],
            row["source_field"],
        )
        for row in declaration_rows
    } >= {
        (
            "Probability.rankUniformityBridge",
            "lean4",
            "resource_request_candidate_declarations",
        )
    }
    assert "Probability.rankUniformityBridge" in context[
        "available_formal_declarations"
    ]
    assert "resource_request_queue_rows" in request["prompt_messages"]["user"]
    assert "resource_request_playbooks" in request["prompt_messages"]["user"]
    assert "operator_prompt" in request["prompt_messages"]["user"]
    assert "source_refs_and_snippets_present" in request["prompt_messages"]["user"]
    playbook_focus = next(
        focus
        for focus in context["route_planning_brief"]["planner_focus"]
        if focus["focus_id"] == "align_followup_to_resource_playbooks"
    )
    assert playbook_focus["target_primitives"] == ["rank_uniformity"]
    summary = context["feedback_loop_summary"]
    assert summary["evidence_counts"]["resource_request_queue_rows"] == 1
    assert summary["resource_request_playbook_count"] == 1
    assert summary["resource_request_playbooks"][0]["resource_request_id"] == (
        "resource-request:rank_route"
    )
    assert summary["recommended_next_actions"][0]["source"] == (
        "resource_request_queue"
    )
    assert summary["recommended_next_actions"][0]["owner"] == "paperclip_cli_mcp"
    assert summary["recommended_next_actions"][0]["primitive"] == "rank_uniformity"
    assert summary["recommended_next_actions"][0]["target_primitives"] == [
        "rank_uniformity"
    ]
    assert summary["recommended_next_actions"][0]["request_playbook_present"] is True
    assert summary["recommended_next_actions"][0]["operator_prompt"].startswith(
        "Use paperclip_cli_mcp"
    )
    assert "response artifact equals source_evidence" in summary[
        "recommended_next_actions"
    ][0]["acceptance_checklist"]
    assert summary["recommended_next_actions"][0]["resource_contracts"] == [
        "paperclip:source_snippet_contract"
    ]


def test_llm_route_planner_resource_queue_feedback_uses_structured_target_primitives() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_resource_queue_structured_targets"
    )
    out_dir = root / "llm_route_planner"
    response_json = root / "response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    resource_request_queue_dir = _write_resource_request_queue(root)
    manifest_path = (
        resource_request_queue_dir
        / "formalization_gap_planner_resource_request_queue_manifest.json"
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    queue_row = manifest["rows"][0]
    queue_row["queue_action_kind"] = "literature_grounded_route_synthesis"
    queue_row["execution_command"] = "paperclip search --query 'queued source evidence'"
    queue_row["request_payload"]["source_query"] = "queued source evidence"
    queue_row["request_playbook"]["operator_prompt"] = (
        "Use paperclip_cli_mcp to satisfy this queued source-evidence request."
    )
    queue_row["request_playbook"]["execution_command"] = (
        "paperclip search --query 'queued source evidence'"
    )
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    response = _llm_response_payload()
    response["search_requests"] = []
    response["planner_next_actions"] = [
        {
            "owner": "paperclip_cli_mcp",
            "action": (
                "dispatch queued source_refs source_snippets "
                "route_revision_recommended evidence request"
            ),
            "resource_request_id": "resource-request:rank_route",
            "resource_id": "paperclip_cli_mcp",
            "target_primitives": ["rank_uniformity"],
        }
    ]
    response["uncertainty_flags"] = []
    response["semantic_alignment_risks"] = []
    response_json.write_text(json.dumps(response, indent=2), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        provider_name="static",
        static_response_json=response_json,
        formalization_gap_planner_resource_request_queue_dir=(
            resource_request_queue_dir
        ),
    )

    assert payload["all_ok"]
    feedback_action = payload["request_packets"][0]["context_packet"][
        "feedback_loop_summary"
    ]["recommended_next_actions"][0]
    assert feedback_action["source"] == "resource_request_queue"
    assert feedback_action["primitive"] == "rank_uniformity"
    assert feedback_action["target_primitives"] == ["rank_uniformity"]
    seed_route = payload["standalone_seed"]["routes"][0]
    feedback_hook = next(
        hook
        for hook in seed_route["interactive_refinement_hooks"]
        if hook.get("llm_route_planner_feedback_next_action", {}).get("source")
        == "resource_request_queue"
    )
    assert feedback_hook["target_primitives"] == ["rank_uniformity"]

    plan_dir = root / "standalone_plan_from_resource_queue_structured_targets"
    refinement_queue_dir = root / "refinement_queue_from_resource_queue_structured_targets"
    plan_payload = export_formalization_gap_planner_standalone_plan(
        out_dir / "formalization_gap_planner_llm_route_planner_standalone_seed.json",
        plan_dir,
    )
    assert plan_payload["all_ok"]
    queue_payload = export_formalization_gap_planner_refinement_queue(
        plan_dir,
        refinement_queue_dir,
    )
    assert queue_payload["all_ok"]
    feedback_queue_row = next(
        row
        for row in queue_payload["rows"]
        if row["hook_kind"] == "literature_discovery"
        and row["llm_route_planner_hook_trace"].get(
            "llm_route_planner_feedback_next_action", {}
        ).get("source")
        == "resource_request_queue"
    )
    assert feedback_queue_row["target_primitives"] == ("rank_uniformity",)


def test_llm_route_planner_cli_stages_resource_request_queue(capsys) -> None:
    root = Path("runs/test_formalization_gap_planner_llm_route_planner_cli_request_queue")
    out_dir = root / "llm_route_planner"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    resource_request_queue_dir = _write_resource_request_queue(root)

    code = main(
        [
            "formalization-gap-planner-llm-route-planner",
            "--input",
            str(input_json),
            "--formalization-gap-planner-resource-request-queue-dir",
            str(resource_request_queue_dir),
            "--out",
            str(out_dir),
        ]
    )

    assert code == 0
    stdout = capsys.readouterr().out
    assert "preflight_blocks=0" in stdout
    manifest = json.loads(
        (
            out_dir / "formalization_gap_planner_llm_route_planner_manifest.json"
        ).read_text(encoding="utf-8")
    )
    assert manifest["n_requests_with_resource_request_queue_rows"] == 1
    request = manifest["request_packets"][0]
    assert request["context_packet"]["resource_request_queue_rows"][0][
        "resource_id"
    ] == "paperclip_cli_mcp"


def test_llm_route_planner_accepts_response_aligned_to_resource_request_queue() -> None:
    root = Path("runs/test_formalization_gap_planner_llm_route_planner_queue_aligned_response")
    out_dir = root / "llm_route_planner"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    resource_request_queue_dir = _write_resource_request_queue(root)
    response_json = root / "response.json"
    response = _llm_response_payload()
    response["search_requests"] = [
        {
            "request_kind": "literature",
            "query": "rank uniformity exchangeability deterministic tie handling",
            "reason": "dispatch the queued Paperclip source search before adopting the bridge route",
            "resource_request_id": "resource-request:rank_route",
            "resource_id": "paperclip_cli_mcp",
        }
    ]
    response["planner_next_actions"] = [
        {
            "owner": "paperclip_cli_mcp",
            "action": "dispatch queued rank_uniformity literature evidence request",
            "resource_request_id": "resource-request:rank_route",
            "resource_id": "paperclip_cli_mcp",
        }
    ]
    response_json.write_text(json.dumps(response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        provider_name="static",
        static_response_json=response_json,
        formalization_gap_planner_resource_request_queue_dir=(
            resource_request_queue_dir
        ),
    )

    assert payload["all_ok"]
    row = payload["rows"][0]
    assert row["response_contract_ok"] is True
    assert row["acceptance_status"] == "ACCEPTED_WITH_SEARCH_REQUESTS"
    assert row["planner_next_actions"][0]["resource_request_id"] == (
        "resource-request:rank_route"
    )
    seed_route = payload["standalone_seed"]["routes"][0]
    hook = seed_route["interactive_refinement_hooks"][0]
    assert hook["resource_request_ids"] == ["resource-request:rank_route"]
    assert "paperclip_cli_mcp" in hook["resource_ids"]
    assert hook["resource_request_bindings"][0]["resource_request_id"] == (
        "resource-request:rank_route"
    )

    plan_dir = root / "standalone_plan_from_queue_aligned_llm_seed"
    refinement_queue_dir = root / "refinement_queue_from_queue_aligned_llm_seed"
    plan_payload = export_formalization_gap_planner_standalone_plan(
        out_dir / "formalization_gap_planner_llm_route_planner_standalone_seed.json",
        plan_dir,
    )
    assert plan_payload["all_ok"]
    plan_row = plan_payload["rows"][0]
    plan_hook = next(
        hook
        for hook in plan_row["interactive_refinement_hooks"]
        if hook.get("resource_request_ids")
    )
    assert plan_hook["resource_request_ids"] == ["resource-request:rank_route"]
    assert "paperclip_cli_mcp" in plan_hook["resource_ids"]
    queue_payload = export_formalization_gap_planner_refinement_queue(
        plan_dir,
        refinement_queue_dir,
    )
    assert queue_payload["all_ok"]
    queue_row = next(
        row for row in queue_payload["rows"] if row.get("resource_request_ids")
    )
    assert list(queue_row["resource_request_ids"]) == ["resource-request:rank_route"]
    assert "paperclip_cli_mcp" in queue_row["resource_ids"]
    assert queue_row["resource_request_bindings"][0]["resource_request_id"] == (
        "resource-request:rank_route"
    )
    adapter_dir = root / "adapter_responses_from_queue_aligned_llm_seed"
    evidence_dir = root / "refinement_evidence_from_queue_aligned_llm_seed"
    adapter_payload = export_formalization_gap_planner_refinement_adapter_responses(
        refinement_queue_dir,
        adapter_dir,
    )
    assert adapter_payload["all_ok"]
    adapter_response = next(
        response for response in adapter_payload["responses"] if response.get("resource_request_ids")
    )
    assert adapter_response["resource_request_ids"] == ["resource-request:rank_route"]
    assert "paperclip_cli_mcp" in adapter_response["resource_ids"]
    evidence_payload = export_formalization_gap_planner_refinement_evidence(
        refinement_queue_dir,
        evidence_dir,
        response_jsonl=adapter_dir
        / "formalization_gap_planner_refinement_evidence_responses.jsonl",
    )
    assert evidence_payload["all_ok"]
    evidence_row = next(
        row for row in evidence_payload["rows"] if row.get("resource_request_ids")
    )
    assert list(evidence_row["resource_request_ids"]) == [
        "resource-request:rank_route"
    ]
    assert "paperclip_cli_mcp" in evidence_row["resource_ids"]
    proposal = next(
        row
        for row in evidence_payload["route_revision_proposals"]
        if row.get("resource_request_ids")
    )
    assert list(proposal["resource_request_ids"]) == ["resource-request:rank_route"]


def test_llm_route_planner_rejects_unqueued_resource_request_references() -> None:
    root = Path("runs/test_formalization_gap_planner_llm_route_planner_queue_bad_response")
    out_dir = root / "llm_route_planner"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    resource_request_queue_dir = _write_resource_request_queue(root)
    response_json = root / "response.json"
    response = _llm_response_payload()
    response["search_requests"] = [
        {
            "request_kind": "literature",
            "query": "rank uniformity exchangeability",
            "reason": "bad fixture references a nonqueued request",
            "resource_request_id": "resource-request:not-queued",
            "resource_id": "unknown_paper_tool",
        }
    ]
    response["planner_next_actions"] = [
        {
            "owner": "unknown_paper_tool",
            "action": "dispatch an unqueued source search",
            "resource_id": "unknown_paper_tool",
        }
    ]
    response_json.write_text(json.dumps(response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        provider_name="static",
        static_response_json=response_json,
        formalization_gap_planner_resource_request_queue_dir=(
            resource_request_queue_dir
        ),
    )

    assert not payload["all_ok"]
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    assert row["response_contract_ok"] is False
    error_text = "\n".join(row["errors"])
    assert "unknown resource_request_id" in error_text
    assert "not present in request queue or registry context" in error_text


def test_llm_route_planner_rejects_resource_request_not_grounded_in_playbook() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_queue_playbook_mismatch"
    )
    out_dir = root / "llm_route_planner"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    resource_request_queue_dir = _write_resource_request_queue(root)
    response_json = root / "response.json"
    response = _llm_response_payload()
    response["search_requests"] = [
        {
            "request_kind": "literature",
            "query": "compact operator spectral theorem Hilbert basis",
            "reason": "unrelated functional analysis search despite queued request id",
            "resource_request_id": "resource-request:rank_route",
            "resource_id": "paperclip_cli_mcp",
        }
    ]
    response["planner_next_actions"] = [
        {
            "owner": "paperclip_cli_mcp",
            "action": "dispatch compact operator spectral theorem search",
            "resource_request_id": "resource-request:rank_route",
            "resource_id": "paperclip_cli_mcp",
        }
    ]
    response_json.write_text(json.dumps(response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        provider_name="static",
        static_response_json=response_json,
        formalization_gap_planner_resource_request_queue_dir=(
            resource_request_queue_dir
        ),
    )

    assert not payload["all_ok"]
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    assert row["response_contract_ok"] is False
    error_text = "\n".join(row["errors"])
    assert "not grounded in the queued request_playbook" in error_text


def test_llm_route_planner_stages_interactive_session_context() -> None:
    root = Path("runs/test_formalization_gap_planner_llm_route_planner_interactive_context")
    out_dir = root / "llm_route_planner"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    interactive_session_dir = _write_interactive_session(root)
    interactive_manifest_path = (
        interactive_session_dir
        / "formalization_gap_planner_interactive_session_manifest.json"
    )
    interactive_manifest = json.loads(
        interactive_manifest_path.read_text(encoding="utf-8")
    )
    interactive_preconditions = {
        "precondition_kind": (
            "formalization_gap_planner_llm_route_planner_route_adoption_preconditions"
        ),
        "status": "PENDING_CONTEXT_OBLIGATIONS",
        "blocked_before_response": True,
        "known_pre_response_blockers": [
            ROUTE_ADOPTION_BLOCKER_SOURCE_GROUNDING
        ],
        "n_known_pre_response_blockers": 1,
        "response_required_fields": ["search_requests", "planner_next_actions"],
        "n_response_required_fields": 2,
        "target_primitives": ["rank_uniformity"],
        "n_target_primitives": 1,
    }
    interactive_manifest["rows"][0].update(
        {
            "session_state": "AWAITING_REFINEMENT_RESPONSES",
            "route_adoption_preconditions": interactive_preconditions,
            "route_adoption_precondition_present": True,
            "route_adoption_precondition_blocked_before_response": True,
            "route_adoption_precondition_unresolved": True,
            "route_adoption_precondition_known_blockers": [
                ROUTE_ADOPTION_BLOCKER_SOURCE_GROUNDING
            ],
            "route_adoption_precondition_required_response_fields": [
                "search_requests",
                "planner_next_actions",
            ],
            "route_adoption_precondition_target_primitives": ["rank_uniformity"],
            "route_adoption_precondition_known_blocker_count": 1,
            "route_adoption_precondition_required_response_field_count": 2,
            "route_adoption_precondition_target_primitive_count": 1,
        }
    )
    interactive_manifest_path.write_text(
        json.dumps(interactive_manifest, indent=2),
        encoding="utf-8",
    )

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        formalization_gap_planner_interactive_session_dir=interactive_session_dir,
    )

    assert payload["all_ok"]
    assert payload["n_requests_with_interactive_session_rows"] == 1
    assert payload["n_requests_with_interactive_decision_policy_rows"] == 1
    assert payload["n_requests_with_feedback_loop_summary"] == 1
    assert payload["n_request_residual_goals"] == 1
    assert payload["n_feedback_loop_summary_interactive_resource_requests"] == 1
    assert (
        payload[
            "n_feedback_loop_summary_interactive_route_adoption_preconditions"
        ]
        == 1
    )
    assert (
        payload[
            "n_feedback_loop_summary_interactive_unresolved_route_adoption_preconditions"
        ]
        == 1
    )
    assert (
        payload[
            "n_feedback_loop_summary_interactive_route_adoption_precondition_known_blockers"
        ]
        == 1
    )
    assert (
        payload[
            "n_feedback_loop_summary_interactive_route_adoption_precondition_required_response_fields"
        ]
        == 2
    )
    assert (
        payload[
            "n_feedback_loop_summary_interactive_route_adoption_precondition_target_primitives"
        ]
        == 1
    )
    assert (
        payload[
            "n_feedback_loop_summary_interactive_resource_request_dispatch_summaries"
        ]
        == 1
    )
    assert (
        payload[
            "n_feedback_loop_summary_interactive_resource_request_execution_commands"
        ]
        == 1
    )
    request = payload["request_packets"][0]
    context = request["context_packet"]
    assert context["interactive_session_rows"][0]["next_interaction_kind"] == "proof_state_feedback"
    assert context["interactive_session_rows"][0]["resource_request_ids"] == [
        "resource-request:rank_route"
    ]
    assert context["interactive_session_rows"][0][
        "resource_request_dispatch_summaries"
    ][0]["resource_id"] == "lean_lsp_mcp"
    assert context["interactive_decision_policy_rows"][0]["resource_contract_ids"] == [
        "lean_lsp:proof_state_feedback"
    ]
    assert tuple(context["residual_goals"]) == ("missing finite tie-breaking side condition",)
    inventory = context["context_packet_inventory"]
    assert inventory["interactive_session_resource_request_count"] == 1
    assert (
        inventory["interactive_session_resource_request_dispatch_summary_count"]
        == 1
    )
    assert (
        inventory["interactive_session_resource_request_execution_command_count"]
        == 1
    )
    assert inventory["interactive_route_adoption_precondition_count"] == 1
    assert inventory["interactive_unresolved_route_adoption_precondition_count"] == 1
    assert (
        inventory[
            "interactive_route_adoption_precondition_known_blocker_count"
        ]
        == 1
    )
    assert (
        inventory[
            "interactive_route_adoption_precondition_required_response_field_count"
        ]
        == 2
    )
    assert (
        inventory[
            "interactive_route_adoption_precondition_target_primitive_count"
        ]
        == 1
    )
    assert context["feedback_loop_summary"]["needs_more_proof_state_feedback"] is True
    precondition_summary = context["feedback_loop_summary"][
        "interactive_route_adoption_preconditions"
    ]
    assert precondition_summary["unresolved_count"] == 1
    assert precondition_summary["known_pre_response_blockers"] == [
        ROUTE_ADOPTION_BLOCKER_SOURCE_GROUNDING
    ]
    assert set(precondition_summary["response_required_fields"]) == {
        "search_requests",
        "planner_next_actions",
    }
    assert precondition_summary["target_primitives"] == ["rank_uniformity"]
    assert precondition_summary["n_target_primitives"] == 1
    assert ROUTE_ADOPTION_BLOCKER_SOURCE_GROUNDING in context[
        "route_adoption_preconditions"
    ]["known_pre_response_blockers"]
    assert set(
        context["route_adoption_preconditions"]["response_required_fields"]
    ) >= {"search_requests", "planner_next_actions"}
    assert context["route_adoption_preconditions"]["target_primitives"] == [
        "rank_uniformity"
    ]
    assert "target_primitives as blocking route-repair obligations" in request[
        "prompt_messages"
    ]["user"]
    assert context["feedback_loop_summary"]["interactive_session_resource_requests"][
        "resource_request_ids"
    ] == ["resource-request:rank_route"]
    assert context["feedback_loop_summary"]["interactive_session_resource_requests"][
        "resource_ids"
    ] == ["lean_lsp_mcp"]
    assert context["feedback_loop_summary"]["recommended_next_actions"][0]["owner"] == (
        "formal_verifier"
    )
    assert context["feedback_loop_summary"]["recommended_next_actions"][0][
        "resource_request_ids"
    ] == ["resource-request:rank_route"]
    assert context["feedback_loop_summary"]["recommended_next_actions"][0][
        "resource_request_dispatch_summaries"
    ][0]["resource_id"] == "lean_lsp_mcp"
    assert context["feedback_loop_summary"]["recommended_next_actions"][0][
        "resource_request_execution_commands"
    ] == ["lean-lsp-mcp goal rank_uniformity"]
    assert context["feedback_loop_summary"]["recommended_next_actions"][0][
        "route_adoption_precondition_unresolved"
    ] is True
    assert context["feedback_loop_summary"]["recommended_next_actions"][0][
        "route_adoption_precondition_known_blockers"
    ] == [ROUTE_ADOPTION_BLOCKER_SOURCE_GROUNDING]
    assert "interactive_decision_policy_rows" in request["prompt_messages"]["user"]
    assert "interactive_route_adoption_preconditions" in request["prompt_messages"][
        "user"
    ]
    assert "resource_request_dispatch_summaries" in request["prompt_messages"]["user"]


def test_llm_route_planner_interactive_feedback_uses_structured_target_primitives() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_interactive_structured_targets"
    )
    out_dir = root / "llm_route_planner"
    response_json = root / "response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    interactive_session_dir = _write_interactive_session(root)
    interactive_manifest_path = (
        interactive_session_dir
        / "formalization_gap_planner_interactive_session_manifest.json"
    )
    manifest = json.loads(interactive_manifest_path.read_text(encoding="utf-8"))
    session_row = manifest["rows"][0]
    session_row["next_queries"] = ["inspect residual side conditions"]
    session_row["next_commands"] = ["lake build"]
    session_row["resource_request_execution_commands"] = [
        "lean-lsp-mcp goal current"
    ]
    session_row["resource_request_dispatch_summaries"][0][
        "target_primitives"
    ] = ["rank_uniformity"]
    interactive_manifest_path.write_text(
        json.dumps(manifest, indent=2),
        encoding="utf-8",
    )
    response = _llm_response_payload()
    response["residual_interpretations"] = [
        {
            "residual_goal": "missing finite tie-breaking side condition",
            "interpretation": (
                "The proof-state residual needs a bounded side-condition "
                "repair before route adoption."
            ),
            "route_repair": (
                "Keep the repair scoped to the rank_uniformity proof-state "
                "feedback path."
            ),
            "target_primitives": ["rank_uniformity"],
            "source_refs": ["conformal_prediction_textbook"],
        }
    ]
    response_json.write_text(json.dumps(response, indent=2), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        provider_name="static",
        static_response_json=response_json,
        formalization_gap_planner_interactive_session_dir=interactive_session_dir,
    )

    assert payload["all_ok"]
    feedback_action = payload["request_packets"][0]["context_packet"][
        "feedback_loop_summary"
    ]["recommended_next_actions"][0]
    assert feedback_action["source"] == "interactive_session"
    assert feedback_action["primitive"] == "rank_uniformity"
    assert feedback_action["target_primitives"] == ["rank_uniformity"]
    seed_route = payload["standalone_seed"]["routes"][0]
    feedback_hook = next(
        hook
        for hook in seed_route["interactive_refinement_hooks"]
        if hook.get("llm_route_planner_feedback_next_action", {}).get("source")
        == "interactive_session"
    )
    assert feedback_hook["hook_kind"] == "proof_state_feedback"
    assert feedback_hook["target_primitives"] == ["rank_uniformity"]

    plan_dir = root / "standalone_plan_from_interactive_structured_targets"
    refinement_queue_dir = root / "refinement_queue_from_interactive_structured_targets"
    plan_payload = export_formalization_gap_planner_standalone_plan(
        out_dir / "formalization_gap_planner_llm_route_planner_standalone_seed.json",
        plan_dir,
    )
    assert plan_payload["all_ok"]
    queue_payload = export_formalization_gap_planner_refinement_queue(
        plan_dir,
        refinement_queue_dir,
    )
    assert queue_payload["all_ok"]
    feedback_queue_row = next(
        row
        for row in queue_payload["rows"]
        if row["hook_kind"] == "proof_state_feedback"
        and row["llm_route_planner_hook_trace"].get(
            "llm_route_planner_feedback_next_action", {}
        ).get("source")
        == "interactive_session"
    )
    assert feedback_queue_row["target_primitives"] == ("rank_uniformity",)


def test_llm_route_planner_overlay_feedback_uses_revised_delta_target_primitives() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_overlay_structured_targets"
    )
    out_dir = root / "llm_route_planner"
    response_json = root / "response.json"
    overlay_dir = root / "route_revision_overlay"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    overlay_dir.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    (
        overlay_dir / "formalization_gap_planner_route_revision_overlay_manifest.json"
    ).write_text(
        json.dumps(
            {
                "component_name": "formalization_gap_planner_route_revision_overlay",
                "rows": [
                    {
                        "route_revision_overlay_id": "overlay:rank_route",
                        "route_id": "rank_route",
                        "display_name": "distribution_free_rank_bound",
                        "revision_status": "ROUTE_REVISION_APPLIED",
                        "route_revision_summary": "apply revised source-backed route",
                        "revised_selected_primitives": [
                            "exchangeability",
                            "rank_uniformity",
                        ],
                        "revised_delta_primitives": ["rank_uniformity"],
                        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    response_json.write_text(
        json.dumps(_llm_response_payload(), indent=2),
        encoding="utf-8",
    )

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        provider_name="static",
        static_response_json=response_json,
        formalization_gap_planner_route_revision_overlay_dir=overlay_dir,
    )

    assert payload["all_ok"]
    feedback_action = next(
        action
        for action in payload["request_packets"][0]["context_packet"][
            "feedback_loop_summary"
        ]["recommended_next_actions"]
        if action["source"] == "route_revision_overlay"
    )
    assert feedback_action["primitive"] == "rank_uniformity"
    assert feedback_action["target_primitives"] == ["rank_uniformity"]
    assert feedback_action["revised_delta_primitives"] == ["rank_uniformity"]
    seed_route = payload["standalone_seed"]["routes"][0]
    feedback_hook = next(
        hook
        for hook in seed_route["interactive_refinement_hooks"]
        if hook.get("llm_route_planner_feedback_next_action", {}).get("source")
        == "route_revision_overlay"
    )
    assert feedback_hook["hook_kind"] == "route_revision"
    assert feedback_hook["target_primitives"] == ["rank_uniformity"]
    feedback_trigger = next(
        trigger
        for trigger in seed_route["route_revision_triggers"]
        if trigger.get("llm_route_planner_feedback_next_action", {}).get("source")
        == "route_revision_overlay"
    )
    assert feedback_trigger["target_primitives"] == ["rank_uniformity"]

    plan_dir = root / "standalone_plan_from_overlay_structured_targets"
    refinement_queue_dir = root / "refinement_queue_from_overlay_structured_targets"
    plan_payload = export_formalization_gap_planner_standalone_plan(
        out_dir / "formalization_gap_planner_llm_route_planner_standalone_seed.json",
        plan_dir,
    )
    assert plan_payload["all_ok"]
    queue_payload = export_formalization_gap_planner_refinement_queue(
        plan_dir,
        refinement_queue_dir,
    )
    assert queue_payload["all_ok"]
    feedback_queue_row = next(
        row
        for row in queue_payload["rows"]
        if row["hook_kind"] == "route_revision"
        and row["llm_route_planner_hook_trace"].get(
            "llm_route_planner_feedback_next_action", {}
        ).get("source")
        == "route_revision_overlay"
    )
    assert feedback_queue_row["target_primitives"] == ("rank_uniformity",)


def test_llm_route_planner_accepts_policy_grounded_quality_controls() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_quality_controls"
    )
    out_dir = root / "llm_route_planner"
    response_json = root / "response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    interactive_session_dir = _write_interactive_session(root)
    response = _llm_response_payload()
    response["residual_interpretations"] = [
        {
            "residual_goal": "missing finite tie-breaking side condition",
            "interpretation": "The proof-state residual requires explicit finite tie-breaking.",
            "route_repair": "Keep proof-state feedback bounded to the Lean residual before route adoption.",
            "target_primitives": ["rank_uniformity"],
            "source_refs": ["conformal_prediction_textbook"],
        }
    ]
    response["planner_next_actions"][0].update(
        {
            "resource_contract_ids": ["lean_lsp:proof_state_feedback"],
            "required_quality_signals": ["diagnostic_signature"],
            "quality_gates": ["response_schema_valid"],
            "response_validation_signals": [
                "residual_goals_or_diagnostics_present"
            ],
            "stop_conditions": ["residual interpreted or source search requested"],
        }
    )
    response_json.write_text(json.dumps(response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        provider_name="static",
        static_response_json=response_json,
        formalization_gap_planner_interactive_session_dir=interactive_session_dir,
    )

    assert payload["all_ok"]
    row = payload["rows"][0]
    assert row["response_contract_ok"] is True
    action = row["planner_next_actions"][0]
    assert action["resource_contract_ids"] == ["lean_lsp:proof_state_feedback"]
    assert action["required_quality_signals"] == ["diagnostic_signature"]
    assert action["quality_gates"] == ["response_schema_valid"]
    assert action["response_validation_signals"] == [
        "residual_goals_or_diagnostics_present"
    ]
    seed_route = payload["standalone_seed"]["routes"][0]
    hook = next(
        hook
        for hook in seed_route["interactive_refinement_hooks"]
        if any(
            binding.get("source") == "planner_next_actions[0]"
            for binding in hook.get("resource_request_bindings", [])
        )
    )
    assert hook["planner_next_actions"][0]["resource_contract_ids"] == [
        "lean_lsp:proof_state_feedback"
    ]
    hook_binding = next(
        binding
        for binding in hook["resource_request_bindings"]
        if binding.get("source") == "planner_next_actions[0]"
    )
    assert hook_binding["resource_id"] == "lean_lsp_mcp"
    assert hook_binding["quality_controls"]["quality_gates"] == [
        "response_schema_valid"
    ]

    plan_dir = root / "standalone_plan_from_quality_control_seed"
    refinement_queue_dir = root / "refinement_queue_from_quality_control_seed"
    plan_payload = export_formalization_gap_planner_standalone_plan(
        out_dir / "formalization_gap_planner_llm_route_planner_standalone_seed.json",
        plan_dir,
    )
    assert plan_payload["all_ok"]
    queue_payload = export_formalization_gap_planner_refinement_queue(
        plan_dir,
        refinement_queue_dir,
    )
    assert queue_payload["all_ok"]
    queue_row = next(
        row
        for row in queue_payload["rows"]
        if row.get("hook_kind") == "proof_state_feedback"
        and any(
            binding.get("source") == "planner_next_actions[0]"
            for binding in row.get("resource_request_bindings", [])
        )
    )
    queue_binding = next(
        binding
        for binding in queue_row["resource_request_bindings"]
        if binding.get("source") == "planner_next_actions[0]"
    )
    assert queue_binding["quality_controls"]["resource_contract_ids"] == [
        "lean_lsp:proof_state_feedback"
    ]
    assert queue_binding["quality_controls"]["required_quality_signals"] == [
        "diagnostic_signature"
    ]
    assert queue_binding["quality_controls"]["response_validation_signals"] == [
        "residual_goals_or_diagnostics_present"
    ]

    adapter_dir = root / "adapter_responses_from_quality_control_queue"
    evidence_dir = root / "refinement_evidence_from_quality_control_queue"
    adapter_payload = export_formalization_gap_planner_refinement_adapter_responses(
        refinement_queue_dir,
        adapter_dir,
    )
    assert adapter_payload["all_ok"]
    adapter_response = next(
        response
        for response in adapter_payload["responses"]
        if response.get("resource_request_bindings")
        and tuple(
            response.get("quality_controls", {}).get("resource_contract_ids", [])
        )
        == ("lean_lsp:proof_state_feedback",)
    )
    assert tuple(adapter_response["quality_controls"]["resource_contract_ids"]) == (
        "lean_lsp:proof_state_feedback",
    )
    assert tuple(adapter_response["quality_controls"]["quality_gates"]) == (
        "response_schema_valid",
    )
    response_rows = [dict(response) for response in adapter_payload["responses"]]
    for response_row in response_rows:
        if response_row.get("refinement_item_id") == adapter_response.get(
            "refinement_item_id"
        ):
            response_row.update(
                {
                    "route_revision_recommended": True,
                    "route_revision_reasons": [
                        "quality-gated proof-state residual requires bounded route repair"
                    ],
                    "residual_goals": [
                        "rank_uniformity: missing finite tie-breaking side condition"
                    ],
                    "residual_goal_context": {
                        "source_kind": "proof_state_feedback",
                        "residual_goal": (
                            "rank_uniformity: missing finite tie-breaking side condition"
                        ),
                        "residual_goals": [
                            "rank_uniformity: missing finite tie-breaking side condition"
                        ],
                        "residual_primitives": ["rank_uniformity"],
                        "target_primitives": ["rank_uniformity"],
                        "interpretation": (
                            "The proof-state residual requires explicit finite "
                            "tie-breaking."
                        ),
                        "route_repair": (
                            "Keep proof-state feedback bounded to the Lean "
                            "residual before route adoption."
                        ),
                        "repair_action": (
                            "rerun route planning with rank_uniformity "
                            "side-condition evidence"
                        ),
                        "source_refs": ["conformal_prediction_textbook"],
                        "queries": [
                            "ask Lean LSP for rank_uniformity residual goals"
                        ],
                    },
                }
            )
    response_jsonl = root / "quality_control_route_revision_responses.jsonl"
    response_jsonl.write_text(
        "\n".join(json.dumps(response_row) for response_row in response_rows) + "\n",
        encoding="utf-8",
    )
    evidence_payload = export_formalization_gap_planner_refinement_evidence(
        refinement_queue_dir,
        evidence_dir,
        response_jsonl=response_jsonl,
    )
    assert evidence_payload["all_ok"]
    evidence_row = next(
        row
        for row in evidence_payload["rows"]
        if row.get("resource_request_bindings")
        and tuple(
            row.get("quality_controls", {}).get("required_quality_signals", [])
        )
        == ("diagnostic_signature",)
    )
    assert tuple(evidence_row["quality_controls"]["required_quality_signals"]) == (
        "diagnostic_signature",
    )
    assert tuple(evidence_row["quality_controls"]["response_validation_signals"]) == (
        "residual_goals_or_diagnostics_present",
    )
    assert evidence_payload["n_route_revision_proposals"] >= 1

    overlay_dir = root / "route_revision_overlay_from_quality_controls"
    overlay_payload = export_formalization_gap_planner_route_revision_overlay(
        plan_dir,
        evidence_dir,
        overlay_dir,
    )
    assert overlay_payload["all_ok"]
    overlay_row = overlay_payload["rows"][0]
    assert tuple(overlay_row["quality_controls"]["resource_contract_ids"]) == (
        "lean_lsp:proof_state_feedback",
    )
    assert tuple(overlay_row["quality_controls"]["quality_gates"]) == (
        "response_schema_valid",
    )

    handoff_dir = root / "route_replan_handoff_from_quality_controls"
    handoff_payload = export_formalization_gap_planner_route_replan_handoff(
        plan_dir,
        overlay_dir,
        handoff_dir,
    )
    assert handoff_payload["all_ok"]
    handoff_row = handoff_payload["rows"][0]
    assert tuple(handoff_row["quality_controls"]["required_quality_signals"]) == (
        "diagnostic_signature",
    )
    standalone_route = handoff_payload["standalone_seed"]["routes"][0]
    assert tuple(standalone_route["quality_controls"]["response_validation_signals"]) == (
        "residual_goals_or_diagnostics_present",
    )
    assert tuple(
        standalone_route["replan_metadata"]["quality_controls"]["stop_conditions"]
    ) == ("residual interpreted or source search requested",)
    assert not validate_standalone_input_payload(handoff_payload["standalone_seed"])
    handoff_manifest_path = (
        handoff_dir
        / "formalization_gap_planner_route_replan_handoff_manifest.json"
    )
    handoff_manifest = json.loads(handoff_manifest_path.read_text(encoding="utf-8"))
    handoff_manifest["rows"][0]["applied_resource_response_traces"] = [
        {
            "resource_response_ledger_id": "ledger:rank_uniformity",
            "resource_request_id": "request:rank_uniformity",
            "resource_id": "lean_lsp_mcp",
            "primitive": "rank_uniformity",
            "target_primitives": ["rank_uniformity"],
            "priority_score": 91,
            "minimal_delta_cost_score": 10,
            "reuse_readiness_score": 95,
            "evidence_readiness_score": 80,
            "priority_rationale": [
                "coverage_status=exact_exists",
                "minimal_delta_cost_score=10",
                "reuse_readiness_score=95",
                "evidence_readiness_score=80",
            ],
            "acceptance_status": "ACCEPTED_WITH_ROUTE_REVISION",
            "proof_evidence_boundary": "not theorem proof evidence",
        }
    ]
    handoff_manifest_path.write_text(
        json.dumps(handoff_manifest, indent=2),
        encoding="utf-8",
    )

    replan_response = _llm_response_payload()
    replan_response["residual_interpretations"] = [
        {
            "residual_goal": (
                "rank_uniformity: missing finite tie-breaking side condition"
            ),
            "interpretation": (
                "The carried handoff residual still requires the finite tie-breaking "
                "condition before route adoption."
            ),
            "route_repair": (
                "Keep the proof-state feedback contract attached to the next "
                "rank_uniformity bridge attempt."
            ),
            "source_refs": ["conformal_prediction_textbook"],
        }
    ]
    replan_response["planner_next_actions"][0].update(
        {
            "resource_contract_ids": ["lean_lsp:proof_state_feedback"],
            "required_quality_signals": ["diagnostic_signature"],
            "quality_gates": ["response_schema_valid"],
            "response_validation_signals": [
                "residual_goals_or_diagnostics_present"
            ],
            "stop_conditions": ["residual interpreted or source search requested"],
        }
    )
    _promote_response_to_source_port_costs(replan_response)
    replan_response_json = root / "replan_response.json"
    replan_response_json.write_text(json.dumps(replan_response), encoding="utf-8")
    replan_llm_dir = root / "llm_route_planner_from_quality_control_handoff"
    replan_payload = export_formalization_gap_planner_llm_route_planner(
        handoff_dir / "formalization_gap_planner_route_replan_standalone_seed.json",
        replan_llm_dir,
        provider_name="static",
        static_response_json=replan_response_json,
        formalization_gap_planner_route_replan_handoff_dir=handoff_dir,
    )
    assert replan_payload["all_ok"]
    assert replan_payload["n_requests_with_route_replan_handoff_rows"] == 1
    assert replan_payload["n_request_route_replan_handoff_rows"] == 1
    assert tuple(replan_payload["request_packets"][0]["residual_goals"]) == (
        "rank_uniformity: missing finite tie-breaking side condition",
    )
    replan_context = replan_payload["request_packets"][0]["context_packet"]
    assert tuple(replan_context["residual_goals"]) == (
        "rank_uniformity: missing finite tie-breaking side condition",
    )
    assert replan_payload["n_requests_with_residual_goal_contexts"] == 1
    assert replan_payload["n_request_residual_goal_contexts"] == 1
    assert replan_payload["n_request_context_residual_goal_contexts"] == 1
    assert replan_payload["n_request_inventory_residual_goal_contexts"] == 1
    assert (
        replan_payload["request_packets"][0]["residual_goal_contexts"]
        == replan_context["residual_goal_contexts"]
    )
    assert len(replan_context["residual_goal_contexts"]) == 1
    residual_context = replan_context["residual_goal_contexts"][0]
    assert residual_context["residual_goal"] == (
        "rank_uniformity: missing finite tie-breaking side condition"
    )
    assert residual_context["route_repair"].startswith(
        "Keep proof-state feedback"
    )
    assert residual_context["source_refs"] == ("conformal_prediction_textbook",)
    target_context = replan_context["target_theorem_context_packet"]
    assert target_context["residual_goal_context_count"] == 1
    assert target_context["residual_goal_contexts"] == [
        dict(residual_context)
    ]
    route_brief = replan_context["route_planning_brief"]
    assert route_brief["evidence_summary"]["residual_goal_context_count"] == 1
    assert {
        focus["focus_id"] for focus in route_brief["planner_focus"]
    } >= {"repair_from_residual_goal_contexts"}
    assert replan_context["context_packet_inventory"][
        "residual_goal_context_count"
    ] == 1
    assert replan_context["context_packet_inventory"][
        "target_theorem_context_residual_goal_context_count"
    ] == 1
    handoff_rows = replan_context["route_replan_handoff_rows"]
    assert len(handoff_rows) == 1
    assert handoff_rows[0]["route_replan_handoff_id"].startswith(
        "formalization_gap_planner_route_replan_handoff:"
    )
    assert handoff_rows[0]["route_revision_overlay_id"] == (
        handoff_row["route_revision_overlay_id"]
    )
    assert handoff_rows[0]["next_commands"]
    assert handoff_rows[0]["applied_resource_response_traces"][0][
        "minimal_delta_cost_score"
    ] == 10
    assert replan_payload["n_requests_with_resource_feedback_readiness_summary"] == 1
    assert replan_payload["n_request_resource_feedback_readiness_rows"] == 1
    assert replan_payload["n_request_resource_feedback_reuse_ready_rows"] == 1
    replan_readiness_summary = replan_context[
        "resource_feedback_readiness_summary"
    ]
    assert replan_readiness_summary["reuse_ready_count"] == 1
    assert replan_readiness_summary["average_reuse_readiness_score"] == 95
    assert replan_context["feedback_loop_summary"][
        "resource_feedback_readiness_summary"
    ] == replan_readiness_summary
    assert replan_context["route_planning_brief"]["evidence_summary"][
        "resource_feedback_reuse_ready_count"
    ] == 1
    assert {
        focus["focus_id"]
        for focus in replan_context["route_planning_brief"]["planner_focus"]
    } >= {"preserve_resource_feedback_minimal_delta_priority"}
    assert replan_context["context_packet_inventory"][
        "resource_feedback_readiness_reuse_ready_count"
    ] == 1
    assert replan_context["feedback_loop_summary"]["residual_goal_count"] == 1
    assert replan_context["feedback_loop_summary"]["evidence_counts"][
        "route_replan_handoff_rows"
    ] == 1
    assert any(
        action["source"] == "route_replan_handoff"
        for action in replan_context["feedback_loop_summary"][
            "recommended_next_actions"
        ]
    )
    prior_metadata = replan_context["feedback_loop_summary"]["prior_replan_metadata"]
    assert tuple(
        prior_metadata["quality_controls"]["resource_contract_ids"]
    ) == ("lean_lsp:proof_state_feedback",)
    assert tuple(
        prior_metadata["quality_controls"]["response_validation_signals"]
    ) == ("residual_goals_or_diagnostics_present",)
    assert "prior_replan_metadata" in replan_payload["request_packets"][0][
        "prompt_messages"
    ]["user"]
    assert "route_replan_handoff_rows" in replan_payload["request_packets"][0][
        "prompt_messages"
    ]["user"]
    assert "resource_feedback_readiness_summary" in replan_payload[
        "request_packets"
    ][0]["prompt_messages"]["user"]
    assert "residual_goal_contexts" in replan_payload["request_packets"][0][
        "prompt_messages"
    ]["user"]
    replan_row = replan_payload["rows"][0]
    assert replan_row["residual_goal_contexts"] == (
        dict(residual_context),
    )
    assert replan_payload["n_rows_with_residual_goal_contexts"] == 1
    assert replan_payload["n_row_residual_goal_contexts"] == 1
    assert replan_row["response_contract_ok"] is True
    assert replan_row["planner_next_actions"][0]["quality_gates"] == [
        "response_schema_valid"
    ]


def test_llm_route_planner_promotes_seed_residual_interpretations_to_context() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_seed_residual_context"
    )
    out_dir = root / "llm_route_planner"
    response_json = root / "response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_light_input(root)
    input_payload = json.loads(input_json.read_text(encoding="utf-8"))
    residual_context = {
        "residual_goal": "rank_uniformity: missing finite tie-breaking side condition",
        "interpretation": (
            "The previous LLM route repair identified a finite tie-breaking "
            "side condition that still needs replay."
        ),
        "route_repair": (
            "Carry the finite tie-breaking side condition into the next "
            "rank_uniformity route before claiming adoption readiness."
        ),
        "target_primitives": ["rank_uniformity"],
        "source_refs": ["conformal_prediction_textbook"],
        "residual_attempt_status": "local_lean_failed",
        "residual_diagnostic_signature": "prover_diagnostic_signature:tie",
        "evidence_ids": ["evidence:llm-residual-tie"],
    }
    input_payload["routes"][0]["replan_metadata"] = {
        "llm_route_planner_residual_interpretations": [dict(residual_context)]
    }
    input_json.write_text(json.dumps(input_payload, indent=2), encoding="utf-8")
    response = _llm_response_payload()
    response["residual_interpretations"] = [dict(residual_context)]
    response["search_requests"] = []
    response["uncertainty_flags"] = []
    response["semantic_alignment_risks"] = []
    response["planner_next_actions"] = []
    response_json.write_text(json.dumps(response, indent=2), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        provider_name="static",
        static_response_json=response_json,
    )

    assert payload["all_ok"]
    assert payload["n_request_residual_goals"] == 1
    assert payload["n_requests_with_residual_goal_contexts"] == 1
    assert payload["n_request_residual_goal_contexts"] == 1
    assert payload["n_request_context_residual_goal_contexts"] == 1
    assert payload["n_request_inventory_residual_goal_contexts"] == 1
    assert payload["n_request_model_tier_decision_auto_sonnet_triggered"] == 1
    assert (
        payload[
            "n_request_route_option_selection_candidates_with_residual_goals"
        ]
        == 1
    )
    assert payload["n_request_route_option_selection_candidate_residual_goals"] == 1
    assert payload["n_request_route_option_selection_lower_bound_residual_goals"] == 1
    request = payload["request_packets"][0]
    assert request["model_tier"] == "sonnet"
    assert "1 prover residual goal(s)" in request[
        "model_tier_decision_evidence"
    ]["sonnet_triggers"]
    assert tuple(request["residual_goals"]) == (
        "rank_uniformity: missing finite tie-breaking side condition",
    )
    context_packet = request["context_packet"]
    assert tuple(context_packet["residual_goals"]) == (
        "rank_uniformity: missing finite tie-breaking side condition",
    )
    contexts = context_packet["residual_goal_contexts"]
    assert len(contexts) == 1
    context = contexts[0]
    assert context["source_kind"] == "llm_route_planner_residual_interpretation"
    assert context["residual_goal"] == (
        "rank_uniformity: missing finite tie-breaking side condition"
    )
    assert context["route_repair"].startswith("Carry the finite tie-breaking")
    assert context["source_refs"] == ("conformal_prediction_textbook",)
    assert context["target_primitives"] == ("rank_uniformity",)
    assert context["evidence_ids"] == ("evidence:llm-residual-tie",)
    target_context = context_packet["target_theorem_context_packet"]
    assert target_context["residual_goal_context_count"] == 1
    assert target_context["residual_goal_contexts"] == [dict(context)]
    route_option_brief = context_packet["route_option_selection_brief"]
    assert route_option_brief["n_candidate_route_options_with_residual_goals"] == 1
    assert route_option_brief["n_candidate_route_option_residual_goals"] == 1
    assert route_option_brief["lower_bound_selected_residual_goal_count"] == 1
    selected_option = route_option_brief["candidate_route_options"][0]
    assert selected_option["n_residual_goals"] == 1
    assert selected_option["n_residual_goal_contexts"] == 1
    assert selected_option["residual_target_primitives"] == ["rank_uniformity"]
    assert selected_option["residual_goal_samples"] == [
        "rank_uniformity: missing finite tie-breaking side condition"
    ]
    inventory = context_packet["context_packet_inventory"]
    assert (
        inventory["route_option_selection_candidate_with_residual_goal_count"]
        == 1
    )
    assert inventory["route_option_selection_candidate_residual_goal_count"] == 1
    assert inventory["route_option_selection_lower_bound_residual_goal_count"] == 1
    route_brief = context_packet["route_planning_brief"]
    assert route_brief["evidence_summary"]["residual_goal_context_count"] == 1
    assert {
        focus["focus_id"] for focus in route_brief["planner_focus"]
    } >= {"repair_from_residual_goal_contexts"}
    assert "residual_goal_contexts" in request["prompt_messages"]["user"]
    row = payload["rows"][0]
    assert row["residual_goal_contexts"] == (dict(context),)
    assert row["route_adoption_status"] == (
        "PENDING_REFINEMENT_BEFORE_ROUTE_ADOPTION"
    )
    assert "residual_interpretations_require_route_replay" in row[
        "route_adoption_blockers"
    ]


def test_llm_route_planner_rejects_residual_context_primitive_drift() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_residual_context_drift"
    )
    out_dir = root / "llm_route_planner"
    response_json = root / "response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_light_input(root)
    input_payload = json.loads(input_json.read_text(encoding="utf-8"))
    residual_context = {
        "residual_goal": "missing finite tie-breaking side condition",
        "interpretation": (
            "The previous proof-state feedback exposed a finite tie-breaking "
            "side condition."
        ),
        "route_repair": (
            "Carry the side condition into the rank_uniformity route before "
            "claiming replay readiness."
        ),
        "target_primitives": ["rank_uniformity"],
        "source_refs": ["conformal_prediction_textbook"],
    }
    input_payload["routes"][0]["replan_metadata"] = {
        "llm_route_planner_residual_interpretations": [dict(residual_context)]
    }
    input_json.write_text(json.dumps(input_payload, indent=2), encoding="utf-8")
    response = _llm_response_payload()
    response["residual_interpretations"] = [
        {
            "residual_goal": "missing finite tie-breaking side condition",
            "interpretation": (
                "The residual text is repeated, but the response scopes the "
                "repair to the wrong primitive."
            ),
            "route_repair": (
                "Repair the exchangeability premise instead of the carried "
                "rank_uniformity residual."
            ),
            "target_primitives": ["exchangeability"],
            "source_refs": ["conformal_prediction_textbook"],
        }
    ]
    response["search_requests"] = []
    response["uncertainty_flags"] = []
    response["semantic_alignment_risks"] = []
    response["planner_next_actions"] = []
    response_json.write_text(json.dumps(response, indent=2), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        provider_name="static",
        static_response_json=response_json,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    assert row["response_contract_ok"] is False
    assert any(
        "context_packet.residual_goal_contexts[0] matching "
        "residual_interpretations row must preserve target/residual primitive "
        "scope" in error
        and "rank_uniformity" in error
        for error in row["errors"]
    )


def test_llm_route_planner_rejects_residual_context_source_provenance_drift() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_residual_context_source_drift"
    )
    out_dir = root / "llm_route_planner"
    response_json = root / "response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_light_input(root)
    input_payload = json.loads(input_json.read_text(encoding="utf-8"))
    input_payload["routes"][0]["source_refs"].append("alternate_rank_source")
    residual_context = {
        "residual_goal": "rank_uniformity: missing finite tie-breaking side condition",
        "interpretation": (
            "The previous proof-state feedback exposed a finite tie-breaking "
            "side condition."
        ),
        "route_repair": (
            "Carry the source-backed side condition into the rank_uniformity "
            "route before claiming replay readiness."
        ),
        "target_primitives": ["rank_uniformity"],
        "source_refs": ["conformal_prediction_textbook"],
        "residual_diagnostic_signature": "prover_diagnostic_signature:tie",
        "evidence_ids": ["evidence:llm-residual-tie"],
    }
    input_payload["routes"][0]["replan_metadata"] = {
        "llm_route_planner_residual_interpretations": [dict(residual_context)]
    }
    input_json.write_text(json.dumps(input_payload, indent=2), encoding="utf-8")
    response = _llm_response_payload()
    response["residual_interpretations"] = [
        {
            "residual_goal": (
                "rank_uniformity: missing finite tie-breaking side condition"
            ),
            "interpretation": (
                "The response keeps the residual and primitive but points to "
                "different source and diagnostic evidence."
            ),
            "route_repair": (
                "Carry the side condition into the rank_uniformity route."
            ),
            "target_primitives": ["rank_uniformity"],
            "source_refs": ["alternate_rank_source"],
            "residual_diagnostic_signature": "prover_diagnostic_signature:other",
        }
    ]
    response["search_requests"] = []
    response["uncertainty_flags"] = []
    response["semantic_alignment_risks"] = []
    response["planner_next_actions"] = []
    response_json.write_text(json.dumps(response, indent=2), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        provider_name="static",
        static_response_json=response_json,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    error_text = "\n".join(row["errors"])
    assert "must preserve at least one carried source_ref" in error_text
    assert "conformal_prediction_textbook" in error_text
    assert (
        "must preserve at least one carried prover-feedback provenance id or "
        "diagnostic signature"
    ) in error_text
    assert "evidence:llm-residual-tie" in error_text
    assert "prover_diagnostic_signature:tie" in error_text


def test_llm_route_planner_flags_unsourced_seed_residual_context() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_unsourced_seed_residual"
    )
    out_dir = root / "llm_route_planner"
    response_json = root / "response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_light_input(root)
    input_payload = json.loads(input_json.read_text(encoding="utf-8"))
    residual_context = {
        "residual_goal": "rank_uniformity: missing finite tie-breaking side condition",
        "interpretation": (
            "A prior prover residual indicated a finite tie-breaking side "
            "condition, but no source grounding was attached."
        ),
        "route_repair": (
            "Search the source literature before promoting this side condition "
            "into the rank_uniformity route."
        ),
        "target_primitives": ["rank_uniformity"],
        "residual_attempt_status": "local_lean_failed",
        "residual_diagnostic_signature": "prover_diagnostic_signature:tie",
    }
    input_payload["routes"][0]["replan_metadata"] = {
        "llm_route_planner_residual_interpretations": [dict(residual_context)]
    }
    input_json.write_text(json.dumps(input_payload, indent=2), encoding="utf-8")
    response = _llm_response_payload()
    response["residual_interpretations"] = [dict(residual_context)]
    response["search_requests"] = [
        {
            "request_kind": "literature",
            "query": (
                "finite tie-breaking side condition rank_uniformity "
                "exchangeability source"
            ),
            "reason": (
                "The carried residual context is unaccounted and needs bounded "
                "source grounding before route promotion."
            ),
            "target_primitives": ["rank_uniformity"],
        }
    ]
    response["uncertainty_flags"] = []
    response["semantic_alignment_risks"] = []
    response["planner_next_actions"] = []
    response_json.write_text(json.dumps(response, indent=2), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        provider_name="static",
        static_response_json=response_json,
    )

    assert payload["all_ok"]
    assert payload["n_request_residual_goals"] == 1
    assert payload["n_requests_with_source_grounding_rows"] == 1
    assert payload["n_request_source_grounding_rows"] == 1
    assert payload["n_requests_with_source_grounding_obligation_inventory"] == 1
    assert (
        payload["n_requests_with_pending_source_grounding_obligation_inventory"]
        == 1
    )
    assert payload["n_request_source_grounding_unresolved_rows"] == 1
    assert payload["n_request_residual_source_grounding_unresolved_rows"] == 1
    request = payload["request_packets"][0]
    context_packet = request["context_packet"]
    source_rows = context_packet["source_grounding_rows"]
    assert len(source_rows) == 1
    assert source_rows[0]["node_source"] == "llm_route_planner_residual_goal_context"
    assert source_rows[0]["grounding_status"] == "unaccounted"
    assert source_rows[0]["ok"] is False
    assert source_rows[0]["residual_goals"] == [
        "rank_uniformity: missing finite tie-breaking side condition"
    ]
    assert source_rows[0]["residual_primitives"] == ["rank_uniformity"]
    obligations = context_packet["source_grounding_obligations"]
    assert obligations["present"] is True
    assert obligations["pending"] is True
    assert obligations["n_inline_residual_context_rows"] == 1
    assert obligations["n_residual_unresolved_rows"] == 1
    assert obligations["target_primitives"] == ["rank_uniformity"]
    assert obligations["unresolved_grounding_statuses"] == ["unaccounted"]
    assert obligations["residual_unresolved_row_ids"][0].startswith(
        "inline_residual_context_source_grounding:"
    )
    route_brief = context_packet["route_planning_brief"]
    grounding_focus = next(
        focus
        for focus in route_brief["planner_focus"]
        if focus["focus_id"] == "resolve_source_grounding_obligations"
    )
    assert grounding_focus["target_primitives"] == ["rank_uniformity"]
    grounding_gap = next(
        gap
        for gap in route_brief["evidence_gaps"]
        if gap["gap_id"] == "pending_source_grounding"
    )
    assert grounding_gap["target_primitives"] == ["rank_uniformity"]
    inventory = context_packet["context_packet_inventory"]
    assert inventory["row_counts"]["source_grounding_rows"] == 1
    assert inventory["source_grounding_obligation_pending"] is True
    assert inventory["residual_source_grounding_unresolved_count"] == 1
    preconditions = context_packet["route_adoption_preconditions"]
    assert ROUTE_ADOPTION_BLOCKER_SOURCE_GROUNDING in preconditions[
        "known_pre_response_blockers"
    ]
    assert set(preconditions["response_required_fields"]) >= {
        "residual_interpretations",
        "search_requests",
        "planner_next_actions",
    }
    row = payload["rows"][0]
    assert row["source_grounding_rows"] == (dict(source_rows[0]),)
    assert row["source_grounding_obligations"] == obligations
    assert row["acceptance_status"] == "ACCEPTED_WITH_SEARCH_REQUESTS"
    assert row["response_contract_ok"] is True
    assert set(row["route_adoption_blockers"]) >= {
        "search_requests_pending_evidence",
        "residual_interpretations_require_route_replay",
        ROUTE_ADOPTION_BLOCKER_SOURCE_GROUNDING,
    }
    seed_route = payload["standalone_seed"]["routes"][0]
    assert seed_route["llm_route_planner_source_grounding_rows"] == [
        dict(source_rows[0])
    ]
    assert seed_route["llm_route_planner_source_grounding_obligations"] == obligations
    assert seed_route["replan_metadata"][
        "llm_route_planner_source_grounding_rows"
    ] == [dict(source_rows[0])]
    assert seed_route["replan_metadata"][
        "llm_route_planner_source_grounding_obligations"
    ] == obligations


def test_llm_route_planner_rejects_ungrounded_quality_controls() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_bad_quality_controls"
    )
    out_dir = root / "llm_route_planner"
    response_json = root / "response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    interactive_session_dir = _write_interactive_session(root)
    response = _llm_response_payload()
    response["residual_interpretations"] = [
        {
            "residual_goal": "missing finite tie-breaking side condition",
            "interpretation": "The proof-state residual requires explicit finite tie-breaking.",
            "route_repair": "Keep proof-state feedback bounded to the Lean residual before route adoption.",
            "source_refs": ["conformal_prediction_textbook"],
        }
    ]
    response["search_requests"][0].update(
        {
            "resource_contract_ids": ["lean_lsp:proof_state_feedback"],
            "required_quality_signals": ["invented_quality_signal"],
            "quality_gates": ["invented_quality_gate"],
            "response_validation_signals": ["invented_response_signal"],
            "stop_conditions": ["invented stop condition"],
        }
    )
    response_json.write_text(json.dumps(response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        provider_name="static",
        static_response_json=response_json,
        formalization_gap_planner_interactive_session_dir=interactive_session_dir,
    )

    assert not payload["all_ok"]
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    error_text = "\n".join(row["errors"])
    assert "required_quality_signals not present" in error_text
    assert "quality_gates not present" in error_text
    assert "response_validation_signals not present" in error_text
    assert "stop_conditions not present" in error_text
    assert "not supported by the referenced resource_contract_id" in error_text


def test_llm_route_planner_accepts_grounded_residual_interpretation() -> None:
    root = Path("runs/test_formalization_gap_planner_llm_route_planner_residual_accept")
    out_dir = root / "llm_route_planner"
    response_json = root / "response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    residual_source_ref = "paper:tie-side-condition"
    primitive_source_ref = "paper:rank-primitive-route"
    input_payload = json.loads(input_json.read_text(encoding="utf-8"))
    input_payload["routes"][0]["source_refs"].extend(
        [residual_source_ref, primitive_source_ref]
    )
    input_json.write_text(json.dumps(input_payload, indent=2), encoding="utf-8")
    interactive_session_dir = _write_interactive_session(root)
    response = _llm_response_payload()
    response["standalone_route"]["primitives"][1]["source_refs"] = [
        primitive_source_ref
    ]
    response["residual_interpretations"] = [
        {
            "residual_goal": "missing finite tie-breaking side condition",
            "interpretation": "The proof route has not fixed deterministic tie handling.",
            "route_repair": "Add a tie-breaking side condition before replay.",
            "target_primitives": ["rank_uniformity"],
            "source_refs": [residual_source_ref],
        }
    ]
    response_json.write_text(json.dumps(response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        provider_name="static",
        static_response_json=response_json,
        formalization_gap_planner_interactive_session_dir=interactive_session_dir,
    )

    assert payload["all_ok"]
    assert payload["n_response_contract_ok"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "ACCEPTED_WITH_SEARCH_REQUESTS"
    assert row["residual_interpretations"][0]["route_repair"] == (
        "Add a tie-breaking side condition before replay."
    )
    assert residual_source_ref in row["source_refs"]
    assert primitive_source_ref in row["source_refs"]


def test_llm_route_planner_rejects_residual_repair_without_target_primitive() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_rejects_residual_without_target_primitive"
    )
    response_json = root / "bad_response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    input_payload = json.loads(input_json.read_text(encoding="utf-8"))
    input_payload["routes"][0]["source_refs"].append("paper:tie-side-condition")
    input_json.write_text(json.dumps(input_payload, indent=2), encoding="utf-8")
    interactive_session_dir = _write_interactive_session(root)
    bad_response = _llm_response_payload()
    bad_response["search_requests"] = []
    bad_response["planner_next_actions"] = []
    bad_response["uncertainty_flags"] = []
    bad_response["semantic_alignment_risks"] = []
    bad_response["residual_interpretations"] = [
        {
            "residual_goal": "missing finite tie-breaking side condition",
            "interpretation": "The proof route has not fixed deterministic tie handling.",
            "route_repair": "Add a tie-breaking side condition before replay.",
            "source_refs": ["paper:tie-side-condition"],
        }
    ]
    response_json.write_text(json.dumps(bad_response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        provider_name="static",
        static_response_json=response_json,
        formalization_gap_planner_interactive_session_dir=interactive_session_dir,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    assert any(
        "residual_interpretations[0] route repair requires target_primitives"
        in error
        and "primitive-prefixed residual_goal" in error
        for error in row["errors"]
    )


def test_llm_route_planner_accepts_prefixed_residual_goal_target_primitive() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_accepts_prefixed_residual_goal_target"
    )
    out_dir = root / "llm_route_planner"
    response_json = root / "response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    input_payload = json.loads(input_json.read_text(encoding="utf-8"))
    input_payload["routes"][0]["source_refs"].append("paper:tie-side-condition")
    input_json.write_text(json.dumps(input_payload, indent=2), encoding="utf-8")
    interactive_session_dir = _write_interactive_session(root)
    manifest_path = (
        interactive_session_dir
        / "formalization_gap_planner_interactive_session_manifest.json"
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["rows"][0]["residual_goals"] = [
        "rank_uniformity: missing finite tie-breaking side condition"
    ]
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    response = _llm_response_payload()
    response["search_requests"] = []
    response["planner_next_actions"] = [
        {
            "owner": "lean_lsp_mcp",
            "action": "run proof-state feedback for the tie-breaking residual",
            "query": "rank_uniformity residual side conditions",
            "target_primitives": ["rank_uniformity"],
            "resource_id": "lean_lsp_mcp",
        }
    ]
    response["uncertainty_flags"] = []
    response["semantic_alignment_risks"] = []
    response["residual_interpretations"] = [
        {
            "residual_goal": (
                "rank_uniformity: missing finite tie-breaking side condition"
            ),
            "interpretation": "The proof route has not fixed deterministic tie handling.",
            "route_repair": "Add a tie-breaking side condition before replay.",
            "source_refs": ["paper:tie-side-condition"],
        }
    ]
    response_json.write_text(json.dumps(response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        provider_name="static",
        static_response_json=response_json,
        formalization_gap_planner_interactive_session_dir=interactive_session_dir,
    )

    assert payload["all_ok"]
    row = payload["rows"][0]
    assert row["acceptance_status"] == "ACCEPTED_WITH_PLANNER_NEXT_ACTIONS"
    seed = json.loads(
        (
            out_dir
            / "formalization_gap_planner_llm_route_planner_standalone_seed.json"
        ).read_text(encoding="utf-8")
    )
    replan_metadata = seed["routes"][0]["replan_metadata"]
    residual_hooks = [
        hook
        for hook in replan_metadata["llm_route_planner_interactive_refinement_hooks"]
        if hook.get("llm_route_planner_residual_interpretation_index") == 0
    ]
    assert residual_hooks
    assert residual_hooks[0]["target_primitives"] == ["rank_uniformity"]


def test_llm_route_planner_accepts_target_prover_prefixed_residual_goal() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_accepts_target_prover_prefixed_residual_goal"
    )
    out_dir = root / "llm_route_planner"
    response_json = root / "response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    input_payload = json.loads(input_json.read_text(encoding="utf-8"))
    input_payload["routes"][0]["source_refs"].append("paper:rocq-adapter-boundary")
    input_json.write_text(json.dumps(input_payload, indent=2), encoding="utf-8")
    interactive_session_dir = _write_interactive_session(root)
    manifest_path = (
        interactive_session_dir
        / "formalization_gap_planner_interactive_session_manifest.json"
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["rows"][0]["residual_goals"] = [
        "rocq:rank_uniformity: awaiting prover adapter mapping"
    ]
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    response = _llm_response_payload()
    response["search_requests"] = []
    response["planner_next_actions"] = [
        {
            "owner": "lean_lsp_mcp",
            "action": "run proof-state feedback for the adapter-prefixed residual",
            "query": "rank_uniformity adapter-prefixed residual side conditions",
            "target_primitives": ["rank_uniformity"],
            "resource_id": "lean_lsp_mcp",
        }
    ]
    response["uncertainty_flags"] = []
    response["semantic_alignment_risks"] = []
    response["residual_interpretations"] = [
        {
            "residual_goal": "rocq:rank_uniformity: awaiting prover adapter mapping",
            "interpretation": (
                "The Rocq route needs an adapter mapping for rank_uniformity "
                "before kernel replay."
            ),
            "route_repair": "run Rocq adapter mapping for rank_uniformity",
            "source_refs": ["paper:rocq-adapter-boundary"],
        }
    ]
    response_json.write_text(json.dumps(response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        provider_name="static",
        static_response_json=response_json,
        formalization_gap_planner_interactive_session_dir=interactive_session_dir,
    )

    assert payload["all_ok"]
    row = payload["rows"][0]
    assert row["acceptance_status"] == "ACCEPTED_WITH_PLANNER_NEXT_ACTIONS"
    assert not any("ungrounded target_primitives: rocq" in error for error in row["errors"])
    seed = json.loads(
        (
            out_dir
            / "formalization_gap_planner_llm_route_planner_standalone_seed.json"
        ).read_text(encoding="utf-8")
    )
    replan_metadata = seed["routes"][0]["replan_metadata"]
    residual_hooks = [
        hook
        for hook in replan_metadata["llm_route_planner_interactive_refinement_hooks"]
        if hook.get("llm_route_planner_residual_interpretation_index") == 0
    ]
    assert residual_hooks
    assert residual_hooks[0]["target_primitives"] == ["rank_uniformity"]


def test_llm_route_planner_marks_residual_repair_as_pending_replay() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_residual_repair_pending"
    )
    out_dir = root / "llm_route_planner"
    response_json = root / "response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    residual_source_ref = "paper:tie-side-condition"
    input_payload = json.loads(input_json.read_text(encoding="utf-8"))
    input_payload["routes"][0]["source_refs"].append(residual_source_ref)
    input_json.write_text(json.dumps(input_payload, indent=2), encoding="utf-8")
    interactive_session_dir = _write_interactive_session(root)
    response = _llm_response_payload()
    response["search_requests"] = []
    response["planner_next_actions"] = [
        {
            "owner": "lean_lsp_mcp",
            "action": "run proof-state feedback for the tie-breaking residual",
            "query": "rank_uniformity residual side conditions",
            "target_primitives": ["rank_uniformity"],
            "resource_id": "lean_lsp_mcp",
        }
    ]
    response["uncertainty_flags"] = []
    response["semantic_alignment_risks"] = []
    response["residual_interpretations"] = [
        {
            "residual_goal": "missing finite tie-breaking side condition",
            "interpretation": "The proof route has not fixed deterministic tie handling.",
            "route_repair": "Add a tie-breaking side condition before replay.",
            "target_primitives": ["rank_uniformity"],
            "source_refs": [residual_source_ref],
        }
    ]
    response_json.write_text(json.dumps(response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        provider_name="static",
        static_response_json=response_json,
        formalization_gap_planner_interactive_session_dir=interactive_session_dir,
    )

    assert payload["all_ok"]
    assert payload["n_route_adoption_ready"] == 0
    assert payload["n_route_adoption_pending_refinement"] == 1
    assert payload["n_route_adoption_pending_residual_repair_blockers"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "ACCEPTED_WITH_PLANNER_NEXT_ACTIONS"
    assert row["route_adoption_status"] == (
        "PENDING_REFINEMENT_BEFORE_ROUTE_ADOPTION"
    )
    assert "residual_interpretations_require_route_replay" in row[
        "route_adoption_blockers"
    ]
    assert "planner_next_actions_pending_evidence" in row[
        "route_adoption_blockers"
    ]
    seed_route = payload["standalone_seed"]["routes"][0]
    residual_hook = next(
        hook
        for hook in seed_route["interactive_refinement_hooks"]
        if hook.get("llm_route_planner_residual_interpretation_index") == 0
    )
    assert residual_hook["hook_kind"] == "route_revision"
    assert residual_hook["target_primitives"] == ["rank_uniformity"]
    assert "missing finite tie-breaking side condition" in residual_hook["queries"]
    assert residual_hook["llm_route_planner_residual_interpretation"][
        "route_repair"
    ] == "Add a tie-breaking side condition before replay."
    residual_trigger = next(
        trigger
        for trigger in seed_route["route_revision_triggers"]
        if trigger.get("llm_route_planner_residual_interpretation_index") == 0
    )
    assert residual_trigger["trigger_kind"] == "llm_route_revision_requested"
    assert residual_trigger["target_primitives"] == ["rank_uniformity"]
    assert residual_trigger["condition"] == "missing finite tie-breaking side condition"
    assert (
        "Add a tie-breaking side condition before replay."
        in residual_trigger["next_action"]
    )

    plan_dir = root / "standalone_plan_from_residual_repair_seed"
    refinement_queue_dir = root / "refinement_queue_from_residual_repair_seed"
    plan_payload = export_formalization_gap_planner_standalone_plan(
        out_dir / "formalization_gap_planner_llm_route_planner_standalone_seed.json",
        plan_dir,
    )
    assert plan_payload["all_ok"]
    queue_payload = export_formalization_gap_planner_refinement_queue(
        plan_dir,
        refinement_queue_dir,
    )
    assert queue_payload["all_ok"]
    residual_queue_row = next(
        item
        for item in queue_payload["rows"]
        if item["hook_kind"] == "route_revision"
        and item["llm_route_planner_hook_trace"].get(
            "llm_route_planner_residual_interpretation_index"
        )
        == 0
    )
    assert residual_queue_row["target_primitives"] == ("rank_uniformity",)
    assert "llm_route_revision_requested" in residual_queue_row["trigger_kinds"]


def test_llm_route_planner_materializes_uncertainty_and_risk_review_work_items() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_uncertainty_review_handoff"
    )
    out_dir = root / "llm_route_planner"
    response_json = root / "response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    response = _llm_response_payload()
    response["search_requests"] = []
    response["planner_next_actions"] = []
    response["residual_interpretations"] = []
    response["uncertainty_flags"] = [
        "rank_uniformity finite support assumption needs review"
    ]
    response["semantic_alignment_risks"] = [
        "rank_uniformity rank convention may differ from textbook"
    ]
    response_json.write_text(json.dumps(response, indent=2), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        provider_name="static",
        static_response_json=response_json,
    )

    assert payload["all_ok"]
    assert payload["n_route_adoption_ready"] == 0
    assert payload["n_route_adoption_pending_refinement"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "ACCEPTED_WITH_UNCERTAINTY_FLAGS"
    assert set(row["route_adoption_blockers"]) >= {
        "uncertainty_flags_require_review",
        "semantic_alignment_risks_require_review",
    }
    seed_route = payload["standalone_seed"]["routes"][0]
    uncertainty_hook = next(
        hook
        for hook in seed_route["interactive_refinement_hooks"]
        if hook.get("llm_route_planner_review_source") == "uncertainty_flags"
    )
    risk_hook = next(
        hook
        for hook in seed_route["interactive_refinement_hooks"]
        if hook.get("llm_route_planner_review_source") == "semantic_alignment_risks"
    )
    assert uncertainty_hook["hook_kind"] == "route_revision"
    assert risk_hook["hook_kind"] == "route_revision"
    assert uncertainty_hook["target_primitives"] == ["rank_uniformity"]
    assert risk_hook["target_primitives"] == ["rank_uniformity"]
    assert uncertainty_hook["llm_route_planner_uncertainty_flags"] == (
        response["uncertainty_flags"]
    )
    assert risk_hook["llm_route_planner_semantic_alignment_risks"] == (
        response["semantic_alignment_risks"]
    )
    assert any(
        trigger.get("trigger_kind") == "llm_uncertainty_review_required"
        for trigger in seed_route["route_revision_triggers"]
    )
    assert any(
        trigger.get("trigger_kind") == "llm_semantic_alignment_review_required"
        for trigger in seed_route["route_revision_triggers"]
    )

    plan_dir = root / "standalone_plan_from_uncertainty_review_seed"
    refinement_queue_dir = root / "refinement_queue_from_uncertainty_review_seed"
    plan_payload = export_formalization_gap_planner_standalone_plan(
        out_dir / "formalization_gap_planner_llm_route_planner_standalone_seed.json",
        plan_dir,
    )
    assert plan_payload["all_ok"]
    queue_payload = export_formalization_gap_planner_refinement_queue(
        plan_dir,
        refinement_queue_dir,
    )
    assert queue_payload["all_ok"]
    uncertainty_queue_row = next(
        item
        for item in queue_payload["rows"]
        if item["hook_kind"] == "route_revision"
        and item["llm_route_planner_hook_trace"].get(
            "llm_route_planner_review_source"
        )
        == "uncertainty_flags"
    )
    risk_queue_row = next(
        item
        for item in queue_payload["rows"]
        if item["hook_kind"] == "route_revision"
        and item["llm_route_planner_hook_trace"].get(
            "llm_route_planner_review_source"
        )
        == "semantic_alignment_risks"
    )
    assert uncertainty_queue_row["target_primitives"] == ("rank_uniformity",)
    assert risk_queue_row["target_primitives"] == ("rank_uniformity",)
    assert "llm_uncertainty_review_required" in uncertainty_queue_row["trigger_kinds"]
    assert (
        "llm_semantic_alignment_review_required"
        in risk_queue_row["trigger_kinds"]
    )


def test_llm_route_planner_marks_semantic_risk_only_response_as_review_pending() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_semantic_risk_pending"
    )
    out_dir = root / "llm_route_planner"
    response_json = root / "response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    response = _llm_response_payload()
    response["search_requests"] = []
    response["planner_next_actions"] = []
    response["residual_interpretations"] = []
    response["uncertainty_flags"] = []
    response["semantic_alignment_risks"] = [
        "rank_uniformity rank convention may differ from textbook"
    ]
    response_json.write_text(json.dumps(response, indent=2), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        provider_name="static",
        static_response_json=response_json,
    )

    assert payload["all_ok"]
    assert payload["n_route_adoption_ready"] == 0
    assert payload["n_route_adoption_pending_refinement"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "ACCEPTED_WITH_SEMANTIC_ALIGNMENT_RISKS"
    assert row["route_adoption_blockers"] == (
        "semantic_alignment_risks_require_review",
    )
    seed_route = payload["standalone_seed"]["routes"][0]
    risk_hook = next(
        hook
        for hook in seed_route["interactive_refinement_hooks"]
        if hook.get("llm_route_planner_review_source") == "semantic_alignment_risks"
    )
    assert risk_hook["hook_kind"] == "route_revision"
    assert risk_hook["target_primitives"] == ["rank_uniformity"]
    assert any(
        trigger.get("trigger_kind") == "llm_semantic_alignment_review_required"
        for trigger in seed_route["route_revision_triggers"]
    )


def test_llm_route_planner_rejects_unsourced_residual_repair() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_rejects_unsourced_residual_repair"
    )
    out_dir = root / "llm_route_planner"
    response_json = root / "bad_response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    interactive_session_dir = _write_interactive_session(root)
    bad_response = _llm_response_payload()
    bad_response["residual_interpretations"] = [
        {
            "residual_goal": "missing finite tie-breaking side condition",
            "interpretation": "The proof route has not fixed deterministic tie handling.",
            "route_repair": "Add a tie-breaking side condition before replay.",
        }
    ]
    response_json.write_text(json.dumps(bad_response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        provider_name="static",
        static_response_json=response_json,
        formalization_gap_planner_interactive_session_dir=interactive_session_dir,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    assert any(
        "residual_interpretations[0] route repair requires source_refs/source_snippets"
        in error
        for error in row["errors"]
    )


def test_llm_route_planner_rejects_primitive_residual_repair_with_vague_search_request() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_rejects_vague_residual_search"
    )
    out_dir = root / "llm_route_planner"
    response_json = root / "bad_response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    interactive_session_dir = _write_interactive_session(root)
    bad_response = _llm_response_payload()
    bad_response["residual_interpretations"] = [
        {
            "residual_goal": "missing finite tie-breaking side condition",
            "interpretation": (
                "The proof route has not fixed deterministic tie handling."
            ),
            "route_repair": "Add a tie-breaking side condition before replay.",
            "target_primitives": ["rank_uniformity"],
        }
    ]
    bad_response["search_requests"] = [
        {
            "request_kind": "literature",
            "query": "finite tie-breaking side condition source",
            "reason": (
                "This vague request overlaps residual words but does not name "
                "or target the repaired primitive."
            ),
        }
    ]
    response_json.write_text(json.dumps(bad_response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        provider_name="static",
        static_response_json=response_json,
        formalization_gap_planner_interactive_session_dir=interactive_session_dir,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    assert any(
        "residual_interpretations[0] route repair requires source_refs/source_snippets"
        in error
        and "matching literature/source search_request" in error
        for error in row["errors"]
    )


def test_llm_route_planner_rejects_primitive_residual_repair_with_vague_formal_boundary() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_rejects_vague_residual_boundary"
    )
    out_dir = root / "llm_route_planner"
    response_json = root / "bad_response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    interactive_session_dir = _write_interactive_session(root)
    bad_response = _llm_response_payload()
    bad_response["search_requests"] = []
    bad_response["residual_interpretations"] = [
        {
            "residual_goal": "missing finite tie-breaking side condition",
            "interpretation": (
                "The proof route has not fixed deterministic tie handling."
            ),
            "route_repair": "Add a tie-breaking side condition before replay.",
            "target_primitives": ["rank_uniformity"],
            "formal_gap_boundary": (
                "The finite tie-breaking side condition is a formal boundary "
                "for the repair route and needs separate handling."
            ),
        }
    ]
    response_json.write_text(json.dumps(bad_response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        provider_name="static",
        static_response_json=response_json,
        formalization_gap_planner_interactive_session_dir=interactive_session_dir,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    assert any(
        "residual_interpretations[0] route repair requires source_refs/source_snippets"
        in error
        and "formal_gap_boundary naming the target primitive" in error
        for error in row["errors"]
    )


def test_llm_route_planner_cli_rejects_codex_generator_alias() -> None:
    root = Path("runs/test_formalization_gap_planner_llm_route_planner_cli_codex")
    out_dir = root / "out"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)

    try:
        main(
            [
                "formalization-gap-planner-llm-route-planner",
                "--input",
                str(input_json),
                "--provider",
                "codex",
                "--out",
                str(out_dir),
            ]
        )
    except SystemExit as exc:
        assert exc.code == 2
    else:
        raise AssertionError("Codex must not be accepted as a normal LLM provider")
    assert not (
        out_dir / "formalization_gap_planner_llm_route_planner_requests.jsonl"
    ).exists()


@pytest.mark.parametrize("provider_name", ("codex_exec", "claude_code"))
def test_llm_route_planner_api_rejects_agent_generator_alias(
    provider_name: str,
) -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_api_agent_provider"
    )
    out_dir = root / "out"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)

    try:
        export_formalization_gap_planner_llm_route_planner(
            input_json,
            out_dir,
            provider_name=provider_name,
        )
    except ValueError as exc:
        assert "agent-style CLI providers are not accepted as pure LLM" in str(exc)
    else:
        raise AssertionError("agent-style providers must not be accepted through the API")
    assert not (
        out_dir / "formalization_gap_planner_llm_route_planner_requests.jsonl"
    ).exists()


def test_llm_route_planner_request_validator_rejects_codex_provider() -> None:
    root = Path("runs/test_formalization_gap_planner_llm_route_planner_request_codex")
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        provider_name="prompt_only",
    )
    request = dict(payload["request_packets"][0])
    request["provider_name"] = "codex"

    assert (
        "provider_name must be one of prompt_only, static, anthropic, openai"
        in validate_llm_route_planner_request(request)
    )


def test_llm_route_planner_cli_invoke_provider_requires_live_provider() -> None:
    root = Path("runs/test_formalization_gap_planner_llm_route_planner_cli_prompt_only_invoke")
    out_dir = root / "out"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)

    try:
        main(
                [
                    "formalization-gap-planner-llm-route-planner",
                    "--input",
                    str(input_json),
                    "--provider",
                    "prompt_only",
                    "--invoke-provider",
                    "--out",
                    str(out_dir),
            ]
        )
    except ValueError as exc:
        assert "invoke_provider requires provider_name in {anthropic, openai}" in str(exc)
    else:
        raise AssertionError("prompt_only must not be invoked as a live LLM provider")
    assert not (
        out_dir / "formalization_gap_planner_llm_route_planner_requests.jsonl"
    ).exists()


def test_llm_route_planner_accepts_source_grounded_static_response() -> None:
    root = Path("runs/test_formalization_gap_planner_llm_route_planner_static")
    out_dir = root / "llm_route_planner"
    response_json = root / "response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    response_json.write_text(
        json.dumps(_llm_response_payload(), indent=2),
        encoding="utf-8",
    )

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        provider_name="static",
        static_response_json=response_json,
    )

    assert payload["all_ok"]
    assert payload["provider_execution_mode"] == (
        PROVIDER_EXECUTION_MODE_STATIC_RESPONSE_REPLAY
    )
    assert payload["invoke_provider"] is False
    assert payload["response_json_supplied"] is False
    assert payload["static_response_json_supplied"] is True
    assert payload["generator_backend_supplied"] is False
    assert payload["live_provider_backend_requested"] is False
    assert payload["static_generator_backend_requested"] is False
    assert payload["provider_generation_requested"] is False
    assert payload["response_schema"]["$id"] == LLM_ROUTE_PLANNER_RESPONSE_SCHEMA_ID
    assert payload["response_payload_schema"]["$id"] == (
        LLM_ROUTE_PLANNER_RESPONSE_PAYLOAD_SCHEMA_ID
    )
    response_payload_schema = payload["response_payload_schema"]
    assert response_payload_schema["anyOf"] == [
        {"required": ["formal_realization_dag_nodes"]},
        {"required": ["lean_realization_dag_nodes"]},
    ]
    assert response_payload_schema["properties"]["minimal_delta_plan"] == {
        "$ref": "#/$defs/minimal_delta_plan"
    }
    minimal_delta_schema = response_payload_schema["$defs"]["minimal_delta_plan"]
    assert "and_or_cost_graph" in minimal_delta_schema["required"]
    assert minimal_delta_schema["properties"]["primitive_costs"]["items"] == {
        "$ref": "#/$defs/primitive_cost"
    }
    route_option_schema = response_payload_schema["$defs"]["route_option"]
    assert route_option_schema["properties"]["primitive_costs"]["items"] == {
        "$ref": "#/$defs/primitive_cost"
    }
    assert "source_port_lemmas" in route_option_schema["properties"]
    assert "bridge_lemmas" in route_option_schema["properties"]
    residual_schema = response_payload_schema["properties"]["residual_interpretations"][
        "items"
    ]
    assert residual_schema["properties"]["target_primitives"] == {
        "type": "array",
        "items": {"type": "string"},
    }
    search_schema = response_payload_schema["properties"]["search_requests"]["items"]
    assert search_schema["properties"]["target_primitives"] == {
        "type": "array",
        "items": {"type": "string"},
    }
    assert "resource_request_id" in search_schema["properties"]
    action_schema = response_payload_schema["properties"]["planner_next_actions"][
        "items"
    ]
    assert action_schema["properties"]["target_primitives"] == {
        "type": "array",
        "items": {"type": "string"},
    }
    assert "resource_request_id" in action_schema["properties"]
    contract = payload["request_packets"][0]["required_output_contract"]
    assert "target_primitives" in contract["search_requests"][0]
    assert "resource_contract_ids" in contract["search_requests"][0]
    assert "target_primitives" in contract["planner_next_actions"][0]
    assert "resource_contract_ids" in contract["planner_next_actions"][0]
    assert validate_llm_route_planner_response_payload(_llm_response_payload()) == []
    manifest_schema_path = (
        out_dir / "formalization_gap_planner_llm_route_planner_manifest.schema.json"
    )
    assert manifest_schema_path.exists()
    manifest_schema = json.loads(manifest_schema_path.read_text(encoding="utf-8"))
    assert manifest_schema["$id"] == LLM_ROUTE_PLANNER_MANIFEST_SCHEMA_ID
    assert manifest_schema["properties"]["request_schema"]["properties"]["$id"][
        "const"
    ] == LLM_ROUTE_PLANNER_REQUEST_SCHEMA_ID
    assert manifest_schema["properties"]["response_payload_schema"]["properties"][
        "$id"
    ]["const"] == LLM_ROUTE_PLANNER_RESPONSE_PAYLOAD_SCHEMA_ID
    assert manifest_schema["properties"]["response_schema"]["properties"]["$id"][
        "const"
    ] == LLM_ROUTE_PLANNER_RESPONSE_SCHEMA_ID
    assert manifest_schema["properties"]["row_schema"]["properties"]["$id"][
        "const"
    ] == LLM_ROUTE_PLANNER_ROW_SCHEMA_ID
    assert manifest_schema["properties"]["route_planning_brief_schema"][
        "properties"
    ]["$id"]["const"] == LLM_ROUTE_PLANNER_ROUTE_PLANNING_BRIEF_SCHEMA_ID
    assert manifest_schema["properties"]["target_theorem_context_packet_schema"][
        "properties"
    ]["$id"]["const"] == LLM_ROUTE_PLANNER_TARGET_THEOREM_CONTEXT_PACKET_SCHEMA_ID
    assert manifest_schema["properties"]["model_tier_decision_ledger_schema"][
        "properties"
    ]["$id"]["const"] == LLM_ROUTE_PLANNER_MODEL_TIER_DECISION_LEDGER_SCHEMA_ID
    assert llm_route_planner_manifest_json_schema()["$id"] == (
        LLM_ROUTE_PLANNER_MANIFEST_SCHEMA_ID
    )
    assert "legacy_context_field_aliases" in manifest_schema["required"]
    assert "n_requests_with_legacy_context_field_aliases" in manifest_schema["required"]
    assert "n_requests_with_route_planning_brief" in manifest_schema["required"]
    assert "n_request_route_planning_focus_rows" in manifest_schema["required"]
    assert "n_request_route_planning_evidence_gaps" in manifest_schema["required"]
    assert (
        "n_request_route_planning_primitive_evidence_rows"
        in manifest_schema["required"]
    )
    assert (
        "n_request_route_planning_source_backed_primitives"
        in manifest_schema["required"]
    )
    assert (
        "n_request_route_planning_formal_supported_primitives"
        in manifest_schema["required"]
    )
    assert (
        "n_rows_with_primitive_evidence_matrix_witness"
        in manifest_schema["required"]
    )
    assert (
        "n_rows_with_complete_primitive_evidence_matrix_accounting"
        in manifest_schema["required"]
    )
    assert (
        "n_primitive_evidence_matrix_unaccounted_primitives"
        in manifest_schema["required"]
    )
    assert (
        "n_primitive_evidence_matrix_source_backed_missing_response_source_snippets"
        in manifest_schema["required"]
    )
    assert (
        "n_primitive_evidence_matrix_formal_supported_missing_reuse"
        in manifest_schema["required"]
    )
    assert (
        "n_primitive_evidence_matrix_delta_needed_missing_accounting"
        in manifest_schema["required"]
    )
    assert (
        "n_request_llm_generation_policy_current_claude_tier_source"
        in manifest_schema["required"]
    )
    assert "n_request_model_freshness_warnings" in manifest_schema["required"]
    assert "n_request_target_prover_families" in manifest_schema["required"]
    assert "by_request_target_prover_family" in manifest_schema["required"]
    assert payload["n_requests_with_route_planning_brief"] == 1
    assert payload["n_request_target_prover_families"] == 1
    assert payload["by_request_target_prover_family"] == {"lean4": 1}
    assert payload["n_request_route_planning_focus_rows"] >= 4
    assert payload["n_request_route_planning_primitive_evidence_rows"] == 2
    assert payload["n_rows_with_primitive_evidence_matrix_witness"] == 1
    assert payload["n_rows_with_complete_primitive_evidence_matrix_accounting"] == 1
    assert payload["n_primitive_evidence_matrix_witness_rows"] == 2
    assert payload["n_primitive_evidence_matrix_accounted_primitives"] == 2
    assert payload["n_primitive_evidence_matrix_unaccounted_primitives"] == 0
    assert (
        payload[
            "n_primitive_evidence_matrix_source_backed_missing_response_source_snippets"
        ]
        == 0
    )
    assert (
        payload["n_primitive_evidence_matrix_formal_supported_missing_reuse"]
        == 0
    )
    assert (
        payload["n_primitive_evidence_matrix_delta_needed_missing_accounting"]
        == 0
    )
    assert (
        payload["n_selected_primitives_without_primitive_evidence_matrix_row"]
        == 0
    )
    assert payload["n_route_option_action_witness_required_primitives"] == 1
    assert payload["n_route_option_action_witness_missing_primitives"] == 0
    assert payload["n_rows_with_route_option_action_witness_obligations"] == 1
    assert payload["n_rows_with_complete_route_option_action_witness"] == 1
    route_option_witness = payload["rows"][0]["realization_coverage_witness"]
    assert route_option_witness["route_option_action_witness_complete"] is True
    assert route_option_witness[
        "route_option_action_witness_required_primitives"
    ] == ["rank_uniformity"]
    assert "repair_attempt_ledger" in manifest_schema["required"]
    assert "n_repair_attempt_ledger_rows" in manifest_schema["required"]
    assert "model_tier_decision_ledger" in manifest_schema["required"]
    assert "n_model_tier_decision_ledger_rows" in manifest_schema["required"]
    assert "provider_usage_rows" in manifest_schema["required"]
    assert "provider_usage_summary" in manifest_schema["required"]
    assert "n_rows_with_provider_usage" in manifest_schema["required"]
    assert "total_provider_input_tokens" in manifest_schema["required"]
    assert "total_provider_output_tokens" in manifest_schema["required"]
    prompt_token_budget_fields = (
        "max_tokens",
        "temperature",
        "max_estimated_prompt_input_tokens",
        "prompt_token_budget_rows",
        "prompt_token_budget_summary",
        "n_prompt_token_budget_rows",
        "prompt_token_budget_preflight_errors",
        "n_prompt_token_budget_preflight_blocked",
        "estimated_prompt_input_tokens",
        "estimated_prompt_max_output_tokens",
        "estimated_prompt_total_token_budget",
    )
    for field_name in prompt_token_budget_fields:
        assert field_name in manifest_schema["required"]
        assert field_name in manifest_schema["properties"]
    assert "target_theorem_context_packet_schema" in manifest_schema["required"]
    assert "target_theorem_context_packets" in manifest_schema["required"]
    assert "n_target_theorem_context_packets" in manifest_schema["required"]
    assert "route_planning_brief_schema" in manifest_schema["required"]
    assert "route_planning_briefs" in manifest_schema["required"]
    assert "n_route_planning_briefs" in manifest_schema["required"]
    execution_mode_fields = (
        "provider_execution_mode",
        "response_json_supplied",
        "static_response_json_supplied",
        "generator_backend_supplied",
        "live_provider_backend_requested",
        "static_generator_backend_requested",
        "provider_generation_requested",
    )
    for field_name in execution_mode_fields:
        assert field_name in manifest_schema["required"]
    assert manifest_schema["properties"]["provider_execution_mode"]["enum"] == [
        "prompt_only_staged",
        "reviewed_response_json",
        "static_response_replay",
        "static_generator_backend",
        "supplied_generator_backend",
        "live_provider_backend",
        "mixed_response_json_and_provider_generation",
    ]
    assert (
        "n_model_tier_decision_ledger_rows_with_escalation"
        in manifest_schema["required"]
    )
    ledger_schema = llm_route_planner_model_tier_decision_ledger_json_schema()
    assert "context_resource_dispatch_counts" in ledger_schema["required"]
    assert (
        "interactive_route_adoption_precondition_counts"
        in ledger_schema["required"]
    )
    assert "source_grounding_obligations" in ledger_schema["required"]
    assert (
        ledger_schema["properties"]["context_resource_dispatch_counts"]["type"]
        == "object"
    )
    assert (
        ledger_schema["properties"][
            "interactive_route_adoption_precondition_counts"
        ]["type"]
        == "object"
    )
    assert (
        ledger_schema["properties"]["source_grounding_obligations"]["type"]
        == "object"
    )
    assert "standalone_replay_gate" in manifest_schema["required"]
    assert "standalone_replay_gate_ok" in manifest_schema["required"]
    component_resource_manifest_fields = (
        "n_requests_with_component_resource_registry_context",
        "n_component_resource_registry_components_in_prompt",
        "n_component_resource_registry_resources_in_prompt",
        "n_component_resource_registry_contracts_in_prompt",
        "n_requests_with_source_theorem_semantic_primitive_bridge_context",
        "n_component_resource_registry_source_theorem_semantic_primitive_bridge_resources_in_prompt",
        "n_component_resource_registry_source_theorem_semantic_primitive_bridge_contracts_in_prompt",
        "n_requests_with_source_theorem_semantic_primitive_from_proof_body_executor_bridge_context",
        "n_component_resource_registry_source_theorem_semantic_primitive_from_proof_body_executor_bridge_resources_in_prompt",
        "n_component_resource_registry_source_theorem_semantic_primitive_from_proof_body_executor_bridge_contracts_in_prompt",
        "n_requests_with_source_theorem_formal_environment_bridge_context",
        "n_component_resource_registry_source_theorem_formal_environment_bridge_resources_in_prompt",
        "n_component_resource_registry_source_theorem_formal_environment_bridge_contracts_in_prompt",
        "n_requests_with_exact_source_theorem_proof_body_executor_context",
        "n_component_resource_registry_exact_source_theorem_proof_body_executor_resources_in_prompt",
        "n_component_resource_registry_exact_source_theorem_proof_body_executor_contracts_in_prompt",
    )
    for field_name in component_resource_manifest_fields:
        assert field_name in manifest_schema["required"]
        assert manifest_schema["properties"][field_name]["type"] == "integer"
        assert manifest_schema["properties"][field_name]["minimum"] == 0
    staged_context_manifest_fields = (
        "n_requests_with_target_intake_rows",
        "n_request_target_intake_rows",
        "n_requests_with_current_goal_plan_rows",
        "n_request_current_goal_plan_rows",
    )
    for field_name in staged_context_manifest_fields:
        assert field_name in manifest_schema["required"]
        assert manifest_schema["properties"][field_name]["type"] == "integer"
        assert manifest_schema["properties"][field_name]["minimum"] == 0
    assert payload["repair_attempt_ledger"] == ()
    assert payload["n_repair_attempt_ledger_rows"] == 0
    assert payload["n_requests_with_repair_attempt_ledger"] == 0
    assert payload["n_repair_attempt_ledger_error_items"] == 0
    assert payload["n_model_tier_decision_ledger_rows"] == 1
    assert payload["n_model_tier_decision_ledger_rows_with_escalation"] == 0
    assert payload["n_model_tier_decision_ledger_provider_failure_rows"] == 0
    assert payload["n_rows_with_provider_usage"] == 0
    assert payload["provider_usage_rows"] == []
    assert payload["provider_usage_summary"]["row_count"] == 0
    assert payload["total_provider_input_tokens"] == 0
    assert payload["total_provider_output_tokens"] == 0
    assert payload["total_provider_total_tokens"] == 0
    assert payload["max_tokens"] == 9000
    assert payload["temperature"] == 0.1
    assert payload["max_estimated_prompt_input_tokens"] == 0
    assert payload["n_prompt_token_budget_rows"] == payload["n_request_packets"] == 1
    assert payload["n_prompt_token_budget_preflight_blocked"] == 0
    assert payload["prompt_token_budget_preflight_errors"] == ()
    assert len(payload["prompt_token_budget_rows"]) == 1
    prompt_token_budget_row = payload["prompt_token_budget_rows"][0]
    assert prompt_token_budget_row["request_id"] == payload["request_packets"][0][
        "request_id"
    ]
    assert prompt_token_budget_row["provider_name"] == "static"
    assert prompt_token_budget_row["model_tier"] == "sonnet"
    assert prompt_token_budget_row["estimated_input_tokens"] > 0
    assert prompt_token_budget_row["max_output_tokens"] == 9000
    assert prompt_token_budget_row["estimated_total_token_budget"] == (
        prompt_token_budget_row["estimated_input_tokens"] + 9000
    )
    assert "not provider billing records" in prompt_token_budget_row["budget_boundary"]
    assert payload["prompt_token_budget_summary"]["row_count"] == 1
    assert payload["prompt_token_budget_summary"]["by_provider"]["static"][
        "n_rows"
    ] == 1
    assert payload["prompt_token_budget_summary"]["by_model_tier"]["sonnet"][
        "n_rows"
    ] == 1
    assert payload["estimated_prompt_input_tokens"] == prompt_token_budget_row[
        "estimated_input_tokens"
    ]
    assert payload["estimated_prompt_max_output_tokens"] == 9000
    assert payload["estimated_prompt_total_token_budget"] == (
        payload["estimated_prompt_input_tokens"] + 9000
    )
    prompt_token_budget_jsonl = (
        out_dir
        / "formalization_gap_planner_llm_route_planner_prompt_token_budget.jsonl"
    )
    assert prompt_token_budget_jsonl.exists()
    assert [
        json.loads(line)
        for line in prompt_token_budget_jsonl.read_text(encoding="utf-8").splitlines()
    ] == [dict(prompt_token_budget_row)]
    assert (
        manifest_schema["properties"]["legacy_context_field_aliases"][
            "properties"
        ]["lean_declaration_hits"]["const"]
        == "formal_declaration_hits"
    )
    assert validate_llm_route_planner_manifest(payload, manifest_schema) == []
    drifted_manifest = dict(payload)
    drifted_manifest["n_rows"] = 999
    assert (
        "n_rows must match rows length"
        in validate_llm_route_planner_manifest(drifted_manifest, manifest_schema)
    )
    drifted_target_context_support_count_manifest = deepcopy(payload)
    drifted_target_context_support_count_manifest[
        "n_target_context_summary_proof_source_ref_support_source_fields"
    ] = 999
    assert (
        "n_target_context_summary_proof_source_ref_support_source_fields "
        "must match rows"
        in validate_llm_route_planner_manifest(
            drifted_target_context_support_count_manifest,
            manifest_schema,
        )
    )
    drifted_execution_mode_manifest = deepcopy(payload)
    drifted_execution_mode_manifest["provider_execution_mode"] = (
        PROVIDER_EXECUTION_MODE_LIVE_PROVIDER_BACKEND
    )
    assert (
        "provider_execution_mode must match invoke_provider and supplied inputs"
        in validate_llm_route_planner_manifest(
            drifted_execution_mode_manifest,
            manifest_schema,
        )
    )
    drifted_live_flag_manifest = deepcopy(payload)
    drifted_live_flag_manifest["live_provider_backend_requested"] = True
    assert (
        "live_provider_backend_requested must match provider_execution_mode"
        in validate_llm_route_planner_manifest(
            drifted_live_flag_manifest,
            manifest_schema,
        )
    )
    drifted_schema_manifest = deepcopy(payload)
    drifted_schema_manifest["request_schema"]["$id"] = "urn:wrong-request-schema"
    assert (
        f"request_schema.$id must equal {LLM_ROUTE_PLANNER_REQUEST_SCHEMA_ID}"
        in validate_llm_route_planner_manifest(
            drifted_schema_manifest,
            manifest_schema,
        )
    )
    drifted_taxonomy_manifest = deepcopy(payload)
    drifted_taxonomy_manifest["route_adoption_blocker_values"] = []
    assert (
        "route_adoption_blocker_values must match route adoption blocker constants"
        in validate_llm_route_planner_manifest(
            drifted_taxonomy_manifest,
            manifest_schema,
        )
    )
    drifted_alias_manifest = deepcopy(payload)
    drifted_alias_manifest["legacy_context_field_aliases"] = {}
    assert (
        "legacy_context_field_aliases must match planner legacy context aliases"
        in validate_llm_route_planner_manifest(
            drifted_alias_manifest,
            manifest_schema,
        )
    )
    drifted_alias_count_manifest = deepcopy(payload)
    drifted_alias_count_manifest["n_requests_with_legacy_context_field_aliases"] = 0
    assert (
        "n_requests_with_legacy_context_field_aliases must match request_packets"
        in validate_llm_route_planner_manifest(
            drifted_alias_count_manifest,
            manifest_schema,
        )
    )
    drifted_target_intake_count_manifest = deepcopy(payload)
    drifted_target_intake_count_manifest["n_requests_with_target_intake_rows"] = 999
    assert (
        "n_requests_with_target_intake_rows must match request_packets"
        in validate_llm_route_planner_manifest(
            drifted_target_intake_count_manifest,
            manifest_schema,
        )
    )
    drifted_target_intake_rows_manifest = deepcopy(payload)
    drifted_target_intake_rows_manifest["n_request_target_intake_rows"] = 999
    assert (
        "n_request_target_intake_rows must match request_packets"
        in validate_llm_route_planner_manifest(
            drifted_target_intake_rows_manifest,
            manifest_schema,
        )
    )
    drifted_goal_plan_count_manifest = deepcopy(payload)
    drifted_goal_plan_count_manifest["n_requests_with_current_goal_plan_rows"] = 999
    assert (
        "n_requests_with_current_goal_plan_rows must match request_packets"
        in validate_llm_route_planner_manifest(
            drifted_goal_plan_count_manifest,
            manifest_schema,
        )
    )
    drifted_goal_plan_rows_manifest = deepcopy(payload)
    drifted_goal_plan_rows_manifest["n_request_current_goal_plan_rows"] = 999
    assert (
        "n_request_current_goal_plan_rows must match request_packets"
        in validate_llm_route_planner_manifest(
            drifted_goal_plan_rows_manifest,
            manifest_schema,
        )
    )
    drifted_target_family_count_manifest = deepcopy(payload)
    drifted_target_family_count_manifest["n_request_target_prover_families"] = 999
    assert (
        "n_request_target_prover_families must match request_packets"
        in validate_llm_route_planner_manifest(
            drifted_target_family_count_manifest,
            manifest_schema,
        )
    )
    drifted_target_family_manifest = deepcopy(payload)
    drifted_target_family_manifest["by_request_target_prover_family"] = {"rocq": 1}
    assert (
        "by_request_target_prover_family must match request_packets"
        in validate_llm_route_planner_manifest(
            drifted_target_family_manifest,
            manifest_schema,
        )
    )
    drifted_repair_ledger_manifest = deepcopy(payload)
    drifted_repair_ledger_manifest["n_repair_attempt_ledger_rows"] = 1
    assert (
        "n_repair_attempt_ledger_rows must match repair_attempt_ledger"
        in validate_llm_route_planner_manifest(
            drifted_repair_ledger_manifest,
            manifest_schema,
        )
    )
    drifted_tier_ledger_count_manifest = deepcopy(payload)
    drifted_tier_ledger_count_manifest["n_model_tier_decision_ledger_rows"] = 0
    assert (
        "n_model_tier_decision_ledger_rows must match model_tier_decision_ledger"
        in validate_llm_route_planner_manifest(
            drifted_tier_ledger_count_manifest,
            manifest_schema,
        )
    )
    drifted_tier_ledger_manifest = deepcopy(payload)
    drifted_tier_ledger_manifest["model_tier_decision_ledger"] = [
        dict(row) for row in payload["model_tier_decision_ledger"]
    ]
    drifted_tier_ledger_manifest["model_tier_decision_ledger"][0]["decision_basis"] = (
        "wrong"
    )
    assert (
        "model_tier_decision_ledger must match request_packets and rows"
        in validate_llm_route_planner_manifest(
            drifted_tier_ledger_manifest,
            manifest_schema,
        )
    )
    drifted_provider_usage_manifest = deepcopy(payload)
    drifted_provider_usage_manifest["total_provider_input_tokens"] = 99
    assert (
        "total_provider_input_tokens must match provider_usage_summary"
        in validate_llm_route_planner_manifest(
            drifted_provider_usage_manifest,
            manifest_schema,
        )
    )
    drifted_prompt_budget_rows_manifest = deepcopy(payload)
    drifted_prompt_budget_rows = [
        dict(row) for row in payload["prompt_token_budget_rows"]
    ]
    drifted_prompt_budget_rows[0]["estimated_input_tokens"] = 0
    drifted_prompt_budget_rows_manifest["prompt_token_budget_rows"] = (
        drifted_prompt_budget_rows
    )
    assert (
        "prompt_token_budget_rows must match request_packets"
        in validate_llm_route_planner_manifest(
            drifted_prompt_budget_rows_manifest,
            manifest_schema,
        )
    )
    drifted_prompt_budget_summary_manifest = deepcopy(payload)
    drifted_prompt_budget_summary_manifest["prompt_token_budget_summary"] = {
        **dict(payload["prompt_token_budget_summary"]),
        "estimated_input_tokens": 0,
    }
    assert (
        "prompt_token_budget_summary must match prompt_token_budget_rows"
        in validate_llm_route_planner_manifest(
            drifted_prompt_budget_summary_manifest,
            manifest_schema,
        )
    )
    drifted_prompt_budget_count_manifest = deepcopy(payload)
    drifted_prompt_budget_count_manifest["estimated_prompt_input_tokens"] = 0
    assert (
        "estimated_prompt_input_tokens must match prompt_token_budget_summary"
        in validate_llm_route_planner_manifest(
            drifted_prompt_budget_count_manifest,
            manifest_schema,
        )
    )
    drifted_prompt_budget_preflight_manifest = deepcopy(payload)
    drifted_prompt_budget_preflight_manifest[
        "max_estimated_prompt_input_tokens"
    ] = 1
    assert (
        "prompt_token_budget_preflight_errors must match "
        "prompt_token_budget_rows and max_estimated_prompt_input_tokens"
        in validate_llm_route_planner_manifest(
            drifted_prompt_budget_preflight_manifest,
            manifest_schema,
        )
    )
    drifted_prompt_budget_preflight_count_manifest = deepcopy(payload)
    drifted_prompt_budget_preflight_count_manifest[
        "n_prompt_token_budget_preflight_blocked"
    ] = 1
    assert (
        "n_prompt_token_budget_preflight_blocked must match "
        "prompt_token_budget_preflight_errors"
        in validate_llm_route_planner_manifest(
            drifted_prompt_budget_preflight_count_manifest,
            manifest_schema,
        )
    )
    drifted_route_planning_brief_schema_manifest = deepcopy(payload)
    drifted_route_planning_brief_schema_manifest["route_planning_brief_schema"][
        "$id"
    ] = "urn:wrong"
    assert (
        "route_planning_brief_schema.$id must equal "
        + LLM_ROUTE_PLANNER_ROUTE_PLANNING_BRIEF_SCHEMA_ID
        in validate_llm_route_planner_manifest(
            drifted_route_planning_brief_schema_manifest,
            manifest_schema,
        )
    )
    drifted_target_context_schema_manifest = deepcopy(payload)
    drifted_target_context_schema_manifest["target_theorem_context_packet_schema"][
        "$id"
    ] = "urn:wrong"
    assert (
        "target_theorem_context_packet_schema.$id must equal "
        + LLM_ROUTE_PLANNER_TARGET_THEOREM_CONTEXT_PACKET_SCHEMA_ID
        in validate_llm_route_planner_manifest(
            drifted_target_context_schema_manifest,
            manifest_schema,
        )
    )
    drifted_target_context_manifest = deepcopy(payload)
    drifted_target_context_manifest["target_theorem_context_packets"] = []
    assert (
        "target_theorem_context_packets must match request_packets"
        in validate_llm_route_planner_manifest(
            drifted_target_context_manifest,
            manifest_schema,
        )
    )
    drifted_target_context_count_manifest = deepcopy(payload)
    drifted_target_context_count_manifest["n_target_theorem_context_packets"] = 0
    assert (
        "n_target_theorem_context_packets must match "
        "target_theorem_context_packets"
        in validate_llm_route_planner_manifest(
            drifted_target_context_count_manifest,
            manifest_schema,
        )
    )
    drifted_route_planning_brief_manifest = deepcopy(payload)
    drifted_route_planning_brief_manifest["route_planning_briefs"] = []
    assert (
        "route_planning_briefs must match request_packets"
        in validate_llm_route_planner_manifest(
            drifted_route_planning_brief_manifest,
            manifest_schema,
        )
    )
    drifted_route_planning_brief_count_manifest = deepcopy(payload)
    drifted_route_planning_brief_count_manifest["n_route_planning_briefs"] = 0
    assert (
        "n_route_planning_briefs must match route_planning_briefs"
        in validate_llm_route_planner_manifest(
            drifted_route_planning_brief_count_manifest,
            manifest_schema,
        )
    )
    drifted_replay_gate_manifest = deepcopy(payload)
    drifted_replay_gate_manifest["standalone_replay_gate"] = {
        **drifted_replay_gate_manifest["standalone_replay_gate"],
        "gate_ok": not drifted_replay_gate_manifest["standalone_replay_gate"][
            "gate_ok"
        ],
    }
    assert (
        "standalone_replay_gate must match rows and standalone_seed"
        in validate_llm_route_planner_manifest(
            drifted_replay_gate_manifest,
            manifest_schema,
        )
    )
    drifted_replay_gate_count_manifest = deepcopy(payload)
    drifted_replay_gate_count_manifest[
        "n_standalone_replay_adoptable_route_candidates"
    ] = 999
    assert (
        "n_standalone_replay_adoptable_route_candidates must match standalone_replay_gate"
        in validate_llm_route_planner_manifest(
            drifted_replay_gate_count_manifest,
            manifest_schema,
        )
    )
    drifted_brief_count_manifest = deepcopy(payload)
    drifted_brief_count_manifest["n_requests_with_route_planning_brief"] = 0
    assert (
        "n_requests_with_route_planning_brief must match request_packets"
        in validate_llm_route_planner_manifest(
            drifted_brief_count_manifest,
            manifest_schema,
        )
    )
    drifted_matrix_count_manifest = deepcopy(payload)
    drifted_matrix_count_manifest[
        "n_request_route_planning_primitive_evidence_rows"
    ] = 999
    assert (
        "n_request_route_planning_primitive_evidence_rows must match request_packets"
        in validate_llm_route_planner_manifest(
            drifted_matrix_count_manifest,
            manifest_schema,
        )
    )
    missing_component_resource_manifest = deepcopy(payload)
    missing_component_resource_manifest.pop(
        "n_requests_with_source_theorem_semantic_primitive_from_proof_body_executor_bridge_context"
    )
    assert (
        "n_requests_with_source_theorem_semantic_primitive_from_proof_body_executor_bridge_context required"
        in validate_llm_route_planner_manifest(
            missing_component_resource_manifest,
            manifest_schema,
        )
    )
    drifted_component_resource_manifest = deepcopy(payload)
    drifted_component_resource_manifest[
        "n_component_resource_registry_source_theorem_semantic_primitive_from_proof_body_executor_bridge_resources_in_prompt"
    ] = 1
    assert (
        "n_component_resource_registry_source_theorem_semantic_primitive_from_proof_body_executor_bridge_resources_in_prompt must match request_packets"
        in validate_llm_route_planner_manifest(
            drifted_component_resource_manifest,
            manifest_schema,
        )
    )
    drifted_generation_policy_count_manifest = deepcopy(payload)
    drifted_generation_policy_count_manifest[
        "n_request_llm_generation_policy_current_claude_tier_source"
    ] = 0
    assert (
        "n_request_llm_generation_policy_current_claude_tier_source must match request_packets"
        in validate_llm_route_planner_manifest(
            drifted_generation_policy_count_manifest,
            manifest_schema,
        )
    )
    drifted_model_freshness_count_manifest = deepcopy(payload)
    drifted_model_freshness_count_manifest[
        "n_request_model_freshness_warnings"
    ] = 1
    assert (
        "n_request_model_freshness_warnings must match request_packets"
        in validate_llm_route_planner_manifest(
            drifted_model_freshness_count_manifest,
            manifest_schema,
        )
    )
    drifted_model_freshness_rows_manifest = deepcopy(payload)
    drifted_model_freshness_rows_manifest["request_model_freshness_warnings"] = [
        {
            "request_id": "formalization_gap_planner_llm_route_request:stale",
            "route_id": "route:rank",
            "provider_name": "anthropic",
            "model": "claude-sonnet-4-5",
            "model_tier": "sonnet",
            "warning": "stale model",
        }
    ]
    assert (
        "request_model_freshness_warnings must match request_packets"
        in validate_llm_route_planner_manifest(
            drifted_model_freshness_rows_manifest,
            manifest_schema,
        )
    )
    assert payload["row_schema"]["$id"] == LLM_ROUTE_PLANNER_ROW_SCHEMA_ID
    assert (
        out_dir
        / "formalization_gap_planner_llm_route_planner_response_payload.schema.json"
    ).exists()
    assert payload["n_response_present"] == 1
    assert payload["n_response_contract_ok"] == 1
    assert payload["n_accepted_route_plans"] == 1
    assert payload["n_route_adoption_ready"] == 0
    assert payload["n_route_adoption_pending_refinement"] == 1
    assert payload["n_route_adoption_pending_search_request_blockers"] == 1
    assert payload["n_route_adoption_pending_planner_next_action_blockers"] == 1
    assert payload["n_route_adoption_pending_uncertainty_blockers"] == 1
    assert payload["route_adoption_blocker_taxonomy_id"] == (
        "formalization_gap_planner_route_adoption_blocker_taxonomy:1"
    )
    assert set(payload["route_adoption_blocker_values"]) >= {
        "search_requests_pending_evidence",
        "planner_next_actions_pending_evidence",
        "uncertainty_flags_require_review",
        "semantic_alignment_risks_require_review",
        "feedback_summary_actions_pending_resolution",
        "resource_request_queue_pending_response",
        "realization_coverage_incomplete",
    }
    assert payload["by_route_adoption_status"] == {
        "PENDING_REFINEMENT_BEFORE_ROUTE_ADOPTION": 1
    }
    assert payload["route_adoption_blocker_counts"] == {
        "planner_next_actions_pending_evidence": 1,
        "search_requests_pending_evidence": 1,
        "semantic_alignment_risks_require_review": 1,
        "uncertainty_flags_require_review": 1,
    }
    assert payload["by_route_adoption_blocker"][
        "search_requests_pending_evidence"
    ] == {
        "n_rows": 1,
        "n_blocker_occurrences": 1,
        "by_route_adoption_status": {
            "PENDING_REFINEMENT_BEFORE_ROUTE_ADOPTION": 1
        },
        "by_acceptance_status": {
            "ACCEPTED_WITH_SEARCH_REQUESTS": 1
        },
        "n_response_present": 1,
        "n_response_contract_ok": 1,
        "n_provider_failures": 0,
    }
    assert payload["n_informal_knowledge_dag_nodes"] == 2
    assert payload["n_informal_knowledge_dag_edges"] == 1
    assert payload["n_lean_realization_dag_nodes"] == 2
    assert payload["n_formal_realization_dag_edges"] == 1
    assert (
        payload["legacy_response_field_aliases"]
        == LLM_ROUTE_PLANNER_LEGACY_RESPONSE_FIELD_ALIASES
        == {"lean_realization_dag_nodes": "formal_realization_dag_nodes"}
    )
    assert payload["n_route_alignment_edges"] == 2
    assert payload["n_rows_with_realization_coverage_witness"] == 1
    assert payload["n_rows_with_complete_realization_coverage"] == 1
    assert payload["n_rows_with_primitive_evidence_matrix_witness"] == 1
    assert payload["n_rows_with_complete_primitive_evidence_matrix_accounting"] == 1
    assert payload[
        "n_route_adoption_pending_primitive_evidence_matrix_blockers"
    ] == 0
    assert payload["n_rows_with_context_packet_inventory"] == 1
    assert payload["n_selected_primitives_missing_formal_realization"] == 0
    assert payload["n_delta_primitives_missing_route_alignment"] == 0
    assert payload["n_source_snippets"] == 1
    assert payload["n_rows_with_source_snippets"] == 1
    assert payload["n_rows_with_minimal_delta_rationale"] == 1
    assert payload["n_rows_with_minimal_delta_cost_witness"] == 1
    assert payload["n_delta_action_witness_required_primitives"] == 1
    assert payload["n_delta_action_witness_missing_primitives"] == 0
    assert payload["n_rows_with_delta_action_witness_obligations"] == 1
    assert payload["n_rows_with_complete_delta_action_witness"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "ACCEPTED_WITH_SEARCH_REQUESTS"
    assert row["route_adoption_status"] == (
        "PENDING_REFINEMENT_BEFORE_ROUTE_ADOPTION"
    )
    assert set(row["route_adoption_blockers"]) >= {
        "search_requests_pending_evidence",
        "planner_next_actions_pending_evidence",
        "uncertainty_flags_require_review",
        "semantic_alignment_risks_require_review",
    }
    matrix_witness = row["primitive_evidence_matrix_witness"]
    assert matrix_witness["matrix_accounting_complete"] is True
    assert matrix_witness["matrix_primitives"] == [
        "exchangeability",
        "rank_uniformity",
    ]
    assert matrix_witness["matrix_accounted_primitives"] == [
        "exchangeability",
        "rank_uniformity",
    ]
    assert matrix_witness["matrix_unaccounted_primitives"] == []
    assert matrix_witness["selected_primitives_without_matrix_row"] == []
    assert matrix_witness[
        "source_backed_matrix_primitives_with_response_source_snippet"
    ] == ["rank_uniformity"]
    assert (
        matrix_witness[
            "source_backed_matrix_primitives_missing_response_source_snippet"
        ]
        == []
    )
    assert matrix_witness["formal_supported_matrix_primitives_reused"] == [
        "exchangeability"
    ]
    assert matrix_witness["formal_supported_matrix_primitives_missing_reuse"] == []
    assert matrix_witness["delta_needed_matrix_primitives"] == ["rank_uniformity"]
    assert matrix_witness["delta_needed_matrix_primitives_accounted"] == [
        "rank_uniformity"
    ]
    assert matrix_witness["delta_needed_matrix_primitives_missing_accounting"] == []
    assert "minimal_delta.selected_primitives" in set(
        matrix_witness["accounted_by_primitive"]["rank_uniformity"]
    )
    assert "conformal_prediction_textbook" in row["source_refs"]
    assert row["context_packet_inventory"] == payload["request_packets"][0][
        "context_packet"
    ]["context_packet_inventory"]
    assert row["target_theorem_context_packet"] == payload["request_packets"][0][
        "context_packet"
    ]["target_theorem_context_packet"]
    assert row["target_context_summary"]["proof_source_refs"] == [
        "conformal_prediction_textbook"
    ]
    assert row["target_context_summary"]["summary_source"] == (
        "standalone_route.source_refs"
    )
    assert set(row["target_context_summary"]["summary_sources"]) == {
        "response.source_snippets",
        "standalone_route.source_refs",
        "standalone_route.source_snippets",
    }
    assert row["target_context_summary"]["proof_source_ref_support_rows"] == [
        {
            "source_ref": "conformal_prediction_textbook",
            "source_fields": [
                "standalone_route.source_refs",
                "response.source_snippets",
                "standalone_route.source_snippets",
            ],
        }
    ]
    assert payload["n_rows_with_target_context_summary"] == 1
    assert payload["n_target_context_summary_proof_source_refs"] == 1
    assert payload["n_rows_with_target_context_summary_proof_source_refs"] == 1
    assert payload["n_target_context_summary_proof_source_ref_support_rows"] == 1
    assert (
        payload["n_rows_with_target_context_summary_proof_source_ref_support_rows"]
        == 1
    )
    assert (
        payload[
            "n_target_context_summary_proof_source_ref_support_source_fields"
        ]
        == 3
    )
    assert row["route_option_selection_brief"] == payload["request_packets"][0][
        "context_packet"
    ]["route_option_selection_brief"]
    assert payload["n_rows_with_route_option_selection_brief"] == 1
    assert row["informal_knowledge_dag_edges"][0]["source_node_id"] == (
        "informal:exchangeability"
    )
    assert row["formal_realization_dag_edges"][0]["target_node_id"] == (
        "formal:rank_uniformity_bridge"
    )
    assert row["context_packet_inventory"]["inventory_kind"] == (
        "formalization_gap_planner_llm_route_planner_context_packet_inventory"
    )
    assert validate_llm_route_planner_row(
        row,
        llm_route_planner_row_json_schema(),
    ) == []
    row_schema = llm_route_planner_row_json_schema()
    assert "formal_realization_dag_nodes" in row_schema["required"]
    assert "informal_knowledge_dag_edges" in row_schema["required"]
    assert "formal_realization_dag_edges" in row_schema["required"]
    assert "lean_realization_dag_nodes" not in row_schema["required"]
    assert "source_snippets" in row_schema["required"]
    assert "realization_coverage_witness" in row_schema["required"]
    assert "primitive_evidence_matrix_witness" in row_schema["required"]
    assert "target_theorem_context_packet" in row_schema["required"]
    assert "target_context_summary" in row_schema["required"]
    assert "route_option_selection_brief" in row_schema["required"]
    assert "context_packet_inventory" in row_schema["required"]
    assert "model_tier_decision_evidence" in row_schema["required"]
    assert row_schema["properties"]["model_tier_decision_evidence"]["type"] == "object"
    assert row_schema["properties"]["target_theorem_context_packet"]["type"] == "object"
    assert row_schema["properties"]["target_context_summary"]["type"] == "object"
    assert row_schema["properties"]["route_option_selection_brief"]["type"] == (
        "object"
    )
    assert row_schema["properties"]["context_packet_inventory"]["type"] == "object"
    assert row_schema["properties"]["realization_coverage_witness"] == {
        "$ref": "#/$defs/realization_coverage_witness"
    }
    assert set(
        row_schema["properties"]["route_adoption_blockers"]["items"]["enum"]
    ) == set(payload["route_adoption_blocker_values"])
    witness_schema = row_schema["$defs"]["realization_coverage_witness"]
    assert "selected_primitives" in witness_schema["required"]
    assert "cost_hint_baseline_primitives" in witness_schema["required"]
    assert "omitted_cost_hint_primitives" in witness_schema["required"]
    assert "cost_hint_baseline_coverage_complete" in witness_schema["required"]
    assert "delta_action_witness_required_primitives" in witness_schema["required"]
    assert "delta_action_witness_complete" in witness_schema["required"]
    assert "delta_primitives_missing_route_alignment_edge" in witness_schema["required"]
    assert "route_relevant_dag_endpoint_complete" in witness_schema["required"]
    assert (
        "route_relevant_formal_nodes_missing_dag_edge_endpoint"
        in witness_schema["required"]
    )
    manifest_schema = llm_route_planner_manifest_json_schema()
    assert "legacy_response_field_aliases" in manifest_schema["required"]
    assert "n_rows_with_target_context_summary" in manifest_schema["required"]
    target_context_summary_count_fields = (
        "n_target_context_summary_proof_source_refs",
        "n_rows_with_target_context_summary_proof_source_refs",
        "n_target_context_summary_proof_source_ref_support_rows",
        "n_rows_with_target_context_summary_proof_source_ref_support_rows",
        "n_target_context_summary_proof_source_ref_support_source_fields",
    )
    for field_name in target_context_summary_count_fields:
        assert field_name in manifest_schema["required"]
        assert manifest_schema["properties"][field_name]["type"] == "integer"
        assert manifest_schema["properties"][field_name]["minimum"] == 0
    assert "n_rows_with_route_option_selection_brief" in manifest_schema["required"]
    assert (
        "n_request_source_theorem_semantic_primitive_rows"
        in manifest_schema["required"]
    )
    assert (
        "n_request_proof_body_semantic_primitive_work_order_rows"
        in manifest_schema["required"]
    )
    assert (
        "n_request_source_theorem_formal_environment_rows"
        in manifest_schema["required"]
    )
    assert (
        "n_request_source_theorem_proof_body_execution_result_rows"
        in manifest_schema["required"]
    )
    assert (
        manifest_schema["properties"]["legacy_response_field_aliases"][
            "properties"
        ]["lean_realization_dag_nodes"]["const"]
        == "formal_realization_dag_nodes"
    )
    assert "realization_coverage_complete" in witness_schema["required"]
    assert witness_schema["properties"]["realization_coverage_complete"]["type"] == "boolean"
    assert (
        witness_schema["properties"]["cost_hint_baseline_coverage_complete"]["type"]
        == "boolean"
    )
    witness = row["realization_coverage_witness"]
    assert witness["selected_primitives"] == ["exchangeability", "rank_uniformity"]
    assert witness["cost_hint_baseline_primitives"] == [
        "exchangeability",
        "rank_uniformity",
    ]
    assert witness["omitted_cost_hint_primitives"] == []
    assert witness["cost_hint_baseline_coverage_complete"] is True
    assert witness["selected_primitives_missing_formal_realization_node"] == []
    assert witness["delta_primitives"] == ["rank_uniformity"]
    assert witness["delta_primitives_missing_route_alignment_edge"] == []
    assert witness["delta_action_witness_required_primitives"] == [
        "rank_uniformity"
    ]
    assert witness["delta_action_witnessed_primitives"] == ["rank_uniformity"]
    assert witness["delta_action_witness_missing_primitives"] == []
    assert witness["delta_action_witness_complete"] is True
    assert witness["delta_action_witness_rows"][0]["matched_action_fields"] == [
        "bridge_lemmas"
    ]
    assert witness["route_relevant_alignment_primitives"] == [
        "exchangeability",
        "rank_uniformity",
    ]
    assert witness["route_relevant_informal_nodes_missing_dag_edge_endpoint"] == []
    assert witness["route_relevant_formal_nodes_missing_dag_edge_endpoint"] == []
    assert witness["route_relevant_dag_endpoint_complete"] is True
    assert witness["route_option_alignment_complete"] is True
    assert witness["realization_coverage_complete"] is True
    assert row["source_snippets"][0]["source_ref"] == (
        "conformal_prediction_textbook"
    )
    declaration_rows = row["formal_realization_dag_nodes"][0][
        "candidate_declaration_rows"
    ]
    assert declaration_rows == [
        {
            "declaration": "Probability.exchangeable",
            "target_prover_family": "lean4",
            "source_field": "candidate_declarations",
        }
    ]
    legacy_free_row = dict(row)
    legacy_free_row.pop("lean_realization_dag_nodes", None)
    assert validate_llm_route_planner_row(legacy_free_row, row_schema) == []
    missing_generic_row = dict(row)
    missing_generic_row.pop("formal_realization_dag_nodes", None)
    assert "formal_realization_dag_nodes required" in validate_llm_route_planner_row(
        missing_generic_row,
        row_schema,
    )
    missing_target_context_row = dict(row)
    missing_target_context_row.pop("target_theorem_context_packet", None)
    assert "target_theorem_context_packet required" in validate_llm_route_planner_row(
        missing_target_context_row,
        row_schema,
    )
    corrupted_target_context_row = deepcopy(row)
    corrupted_target_context_row["target_theorem_context_packet"][
        "route_id"
    ] = "wrong_route"
    assert (
        "target_theorem_context_packet.route_id must match row route_id"
        in validate_llm_route_planner_row(corrupted_target_context_row, row_schema)
    )
    corrupted_route_option_brief_row = deepcopy(row)
    corrupted_route_option_brief_row["route_option_selection_brief"][
        "lower_bound_selected_route_option_id"
    ] = "route_option:missing"
    assert (
        "route_option_selection_brief.lower_bound_selected_route_option_id "
        "must name a candidate_route_options route_option_id"
        in validate_llm_route_planner_row(
            corrupted_route_option_brief_row,
            row_schema,
        )
    )
    corrupted_decision_row = deepcopy(row)
    corrupted_decision_row["model_tier_decision_evidence"][
        "decision_basis"
    ] = "auto_haiku_bounded_route"
    decision_errors = validate_llm_route_planner_row(
        corrupted_decision_row,
        row_schema,
    )
    assert any("auto_haiku_bounded_route must select haiku" in error for error in decision_errors)
    corrupted_request = deepcopy(payload["request_packets"][0])
    corrupted_request["model_tier_decision_evidence"]["sonnet_triggers"] = []
    request_decision_errors = validate_llm_route_planner_request(corrupted_request)
    assert any("sonnet_triggers required for auto Sonnet" in error for error in request_decision_errors)
    assert (
        payload["standalone_seed"]["routes"][0]["display_name"]
        == "distribution_free_rank_bound_llm_revision"
    )
    assert validate_standalone_input_payload(payload["standalone_seed"]) == []
    drifted_standalone_seed = deepcopy(payload["standalone_seed"])
    drifted_standalone_seed["routes"][0]["target_theorem_context_packet"] = {
        **drifted_standalone_seed["routes"][0]["target_theorem_context_packet"],
        "theorem_statement": "A different theorem is now being planned.",
    }
    assert (
        "routes[0].target_theorem_context_packet must match "
        "routes[0].replan_metadata.target_theorem_context_packet"
        in validate_standalone_input_payload(drifted_standalone_seed)
    )
    drifted_metadata_seed = deepcopy(payload["standalone_seed"])
    drifted_metadata_seed["routes"][0]["replan_metadata"][
        "target_theorem_context_packet"
    ]["target_prover_family"] = "rocq"
    assert (
        "routes[0].replan_metadata.target_theorem_context_packet.target_prover_family "
        "rocq does not match target_prover_family lean4"
        in validate_standalone_input_payload(drifted_metadata_seed)
    )
    standalone_schema = standalone_input_json_schema()
    standalone_route_props = standalone_schema["$defs"]["route"]["properties"]
    standalone_metadata_props = standalone_schema["$defs"]["replan_metadata"][
        "properties"
    ]
    assert standalone_route_props["target_theorem_context_packet"]["type"] == (
        "object"
    )
    assert standalone_metadata_props["target_theorem_context_packet"]["type"] == (
        "object"
    )
    assert standalone_metadata_props[
        "llm_route_planner_target_theorem_context_packet"
    ]["type"] == "object"
    assert standalone_route_props["llm_route_planner_route_option_selection_brief"][
        "type"
    ] == "object"
    assert standalone_route_props[
        "llm_route_planner_route_option_selected_route_option_id"
    ]["type"] == "string"
    assert standalone_metadata_props[
        "llm_route_planner_route_option_selection_brief"
    ]["type"] == "object"
    assert standalone_metadata_props[
        "llm_route_planner_route_option_selected_route_option_id"
    ]["type"] == "string"
    assert (
        payload[
            "n_standalone_seed_routes_with_llm_route_option_selected_route_option"
        ]
        == 1
    )
    seed_selection = payload["standalone_seed"][
        "llm_route_planner_seed_route_selection"
    ]
    assert seed_selection["selected_route_adoptable_for_standalone_replay"] is False
    assert seed_selection["n_adoptable_route_candidates"] == 0
    assert seed_selection["n_selected_route_candidates_not_adoptable"] == 1
    assert (
        seed_selection["selection_rows"][0][
            "adoptable_for_standalone_replay"
        ]
        is False
    )
    seed_route = payload["standalone_seed"]["routes"][0]
    assert (
        seed_route["llm_route_planner_seed_adoptable_for_standalone_replay"]
        is False
    )
    assert seed_route["primitives"][0]["candidate_declaration_rows"] == [
        {
            "declaration": "Probability.exchangeable",
            "target_prover_family": "lean4",
            "source_field": "candidate_declarations",
        }
    ]
    metadata = seed_route["replan_metadata"]
    assert seed_route["target_theorem_context_packet"] == row[
        "target_theorem_context_packet"
    ]
    assert seed_route["llm_route_planner_route_planning_brief"] == row[
        "route_planning_brief"
    ]
    assert seed_route["llm_route_planner_route_option_selection_brief"] == row[
        "route_option_selection_brief"
    ]
    assert (
        seed_route[
            "llm_route_planner_route_option_selected_route_option_id"
        ]
        == "route_option:current_route_min_delta_baseline"
    )
    assert seed_route["llm_route_planner_primitive_evidence_matrix_witness"] == row[
        "primitive_evidence_matrix_witness"
    ]
    assert seed_route["llm_route_planner_route_adoption_preconditions"] == row[
        "route_adoption_preconditions"
    ]
    assert metadata["target_theorem_context_packet"] == row[
        "target_theorem_context_packet"
    ]
    assert metadata["llm_route_planner_target_theorem_context_packet"] == row[
        "target_theorem_context_packet"
    ]
    assert metadata["llm_route_planner_route_planning_brief"] == row[
        "route_planning_brief"
    ]
    assert metadata["llm_route_planner_route_option_selection_brief"] == row[
        "route_option_selection_brief"
    ]
    assert (
        metadata[
            "llm_route_planner_route_option_selected_route_option_id"
        ]
        == "route_option:current_route_min_delta_baseline"
    )
    assert metadata["llm_route_planner_primitive_evidence_matrix_witness"] == row[
        "primitive_evidence_matrix_witness"
    ]
    assert metadata["llm_route_planner_route_adoption_preconditions"] == row[
        "route_adoption_preconditions"
    ]
    assert seed_route["source_snippets"][0]["source_ref"] == (
        "conformal_prediction_textbook"
    )
    assert metadata["source_snippets"][0]["source_ref"] == (
        "conformal_prediction_textbook"
    )
    assert metadata["llm_route_planner_row_id"] == row["llm_route_planner_row_id"]
    assert metadata["llm_route_planner_acceptance_status"] == row["acceptance_status"]
    assert (
        seed_route["llm_route_planner_route_adoption_status"]
        == row["route_adoption_status"]
    )
    assert (
        metadata["llm_route_planner_route_adoption_status"]
        == row["route_adoption_status"]
    )
    assert (
        metadata["llm_route_planner_route_adoption_blockers"]
        == list(row["route_adoption_blockers"])
    )
    assert metadata["llm_route_planner_model_tier"] == row["model_tier"]
    assert (
        metadata["llm_route_planner_model_selection_rationale"]
        == row["model_selection_rationale"]
    )
    assert metadata["llm_route_planner_generator_metadata"] == row[
        "generator_metadata"
    ]
    assert metadata["llm_route_planner_generator_metadata_keys"] == sorted(
        row["generator_metadata"]
    )
    assert (
        metadata["llm_route_planner_seed_adoptable_for_standalone_replay"]
        is False
    )
    assert metadata["applied_hook_kinds"] == ["llm_route_planner"]
    assert seed_route["realization_coverage_witness"] == row[
        "realization_coverage_witness"
    ]
    assert metadata["llm_route_planner_realization_coverage_witness"] == row[
        "realization_coverage_witness"
    ]
    assert metadata["llm_route_planner_primitive_evidence_matrix_witness"] == row[
        "primitive_evidence_matrix_witness"
    ]
    drifted_route_option_seed = deepcopy(payload["standalone_seed"])
    drifted_route_option_seed["routes"][0]["replan_metadata"][
        "llm_route_planner_route_option_selection_brief"
    ]["lower_bound_selected_route_option_id"] = "route_option:missing"
    assert (
        "routes[0].llm_route_planner_route_option_selection_brief must match "
        "routes[0].replan_metadata.llm_route_planner_route_option_selection_brief"
        in validate_standalone_input_payload(drifted_route_option_seed)
    )
    consistently_drifted_route_option_seed = deepcopy(payload["standalone_seed"])
    seed_route_brief = consistently_drifted_route_option_seed["routes"][0][
        "llm_route_planner_route_option_selection_brief"
    ]
    seed_metadata_brief = consistently_drifted_route_option_seed["routes"][0][
        "replan_metadata"
    ]["llm_route_planner_route_option_selection_brief"]
    for brief in (seed_route_brief, seed_metadata_brief):
        brief["lower_bound_selected_route_option_id"] = "route_option:missing"
        brief["n_candidate_route_options"] = 99
        brief["candidate_route_options"][0]["n_selected_primitives"] = 99
    standalone_route_option_errors = validate_standalone_input_payload(
        consistently_drifted_route_option_seed
    )
    assert (
        "routes[0].llm_route_planner_route_option_selection_brief."
        "lower_bound_selected_route_option_id must name a "
        "candidate_route_options route_option_id"
        in standalone_route_option_errors
    )
    assert (
        "routes[0].llm_route_planner_route_option_selection_brief."
        "n_candidate_route_options must match candidate_route_options"
        in standalone_route_option_errors
    )
    assert (
        "routes[0].llm_route_planner_route_option_selection_brief."
        "candidate_route_options[0].n_selected_primitives must match "
        "selected_primitives"
        in standalone_route_option_errors
    )
    assert metadata["revised_informal_knowledge_dag_nodes"][0]["node_source"] == (
        "llm_route_planner_revised_informal_dag"
    )
    assert seed_route["revised_informal_knowledge_dag_edges"][0][
        "source_node_id"
    ] == row["informal_knowledge_dag_edges"][0]["source_node_id"]
    assert seed_route["revised_formal_realization_dag_edges"][0][
        "target_node_id"
    ] == row["formal_realization_dag_edges"][0]["target_node_id"]
    assert metadata["revised_informal_knowledge_dag_edges"][0][
        "proof_evidence_status"
    ] == PROOF_EVIDENCE_STATUS
    assert metadata["revised_formal_realization_dag_edges"][0][
        "proof_evidence_status"
    ] == PROOF_EVIDENCE_STATUS

    assert (
        metadata["llm_route_planner_minimal_delta_plan"]["minimality_rationale"]
        == row["minimal_delta_plan"]["minimality_rationale"]
    )
    assert seed_route["minimal_delta_and_or_cost_graph"] == row[
        "minimal_delta_plan"
    ]["and_or_cost_graph"]
    assert metadata["minimal_delta_and_or_cost_graph"] == row[
        "minimal_delta_plan"
    ]["and_or_cost_graph"]
    alignment_edge = metadata["revised_route_alignment_edges"][0]
    assert alignment_edge["source"] == "informal:rank_uniformity"
    assert alignment_edge["target"] == "formal:rank_uniformity_bridge"
    assert alignment_edge["primitive"] == "rank_uniformity"
    plan_dir = root / "standalone_plan_from_llm_seed"
    source_audit_dir = root / "source_grounding_from_llm_seed"
    plan_payload = export_formalization_gap_planner_standalone_plan(
        out_dir / "formalization_gap_planner_llm_route_planner_standalone_seed.json",
        plan_dir,
    )
    assert plan_payload["all_ok"]
    assert (
        plan_payload[
            "n_standalone_input_traces_with_llm_route_planner_metadata"
        ]
        == 1
    )
    assert (
        plan_payload[
            "n_standalone_input_traces_with_target_theorem_context_packet"
        ]
        == 1
    )
    assert (
        plan_payload[
            "n_standalone_input_traces_with_llm_target_theorem_context_packet"
        ]
        == 1
    )
    assert (
        plan_payload[
            "n_standalone_input_traces_with_llm_route_planning_brief"
        ]
        == 1
    )
    assert (
        plan_payload[
            "n_standalone_input_traces_with_llm_route_option_selection_brief"
        ]
        == 1
    )
    assert (
        plan_payload[
            "n_standalone_input_traces_with_llm_route_option_selected_route_option"
        ]
        == 1
    )
    assert (
        plan_payload[
            "n_standalone_input_traces_with_llm_primitive_evidence_matrix_witness"
        ]
        == 1
    )
    assert (
        plan_payload[
            "n_standalone_input_traces_with_complete_llm_primitive_evidence_matrix_accounting"
        ]
        == 1
    )
    assert (
        plan_payload[
            "n_standalone_input_trace_llm_primitive_evidence_matrix_repair_obligations"
        ]
        == 0
    )
    assert (
        plan_payload[
            "n_standalone_input_traces_with_llm_route_adoption_preconditions"
        ]
        == 1
    )
    assert (
        plan_payload[
            "n_standalone_input_trace_target_theorem_context_target_mismatches"
        ]
        == 0
    )
    assert (
        plan_payload[
            "n_standalone_input_trace_target_theorem_context_route_statement_differs"
        ]
        == 1
    )
    assert plan_payload["n_standalone_input_traces_with_llm_model_tier"] == 1
    assert plan_payload["standalone_input_trace_by_llm_model_tier"] == {
        row["model_tier"]: 1
    }
    assert plan_payload["n_standalone_input_traces_with_llm_generator_metadata"] == 0
    assert plan_payload["n_standalone_input_traces_with_llm_seed_selection"] == 1
    assert plan_payload["n_standalone_input_traces_llm_seed_selected"] == 1
    assert (
        plan_payload[
            "n_standalone_input_traces_llm_seed_adoptable_for_standalone_replay"
        ]
        == 0
    )
    assert (
        plan_payload[
            "n_standalone_input_traces_llm_seed_selected_not_adoptable"
        ]
        == 1
    )
    assert plan_payload[
        "standalone_input_trace_by_llm_seed_selection_rank"
    ] == {"1": 1}
    assert (
        plan_payload[
            "n_standalone_input_traces_with_llm_seed_minimal_delta_route_cost"
        ]
        == 1
    )
    source_payload = audit_formalization_gap_planner_source_grounding(
        plan_dir,
        source_audit_dir,
    )
    assert source_payload["all_ok"]
    assert (
        source_payload["by_node_source"]["llm_route_planner_revised_informal_dag"]
        == 2
    )
    minimal_delta_payload = audit_formalization_gap_planner_minimal_delta(
        plan_dir,
        root / "minimal_delta_audit_from_llm_seed",
    )
    assert minimal_delta_payload["all_ok"]
    assert minimal_delta_payload["n_minimal_delta_decision_rows"] == 1
    assert minimal_delta_payload["n_rows_with_cost_formula_ok"] == 1
    assert minimal_delta_payload["n_rows_with_node_cost_accounting_ok"] == 1
    assert (
        minimal_delta_payload["n_minimal_delta_decision_row_schema_valid"]
        == minimal_delta_payload["n_minimal_delta_decision_rows"]
    )
    plan_row = plan_payload["rows"][0]
    trace = plan_row["standalone_input_trace"]
    assert trace["llm_route_planner_row_id"] == row["llm_route_planner_row_id"]
    assert trace["target_theorem_context_packet"] == row[
        "target_theorem_context_packet"
    ]
    assert trace["llm_route_planner_route_planning_brief"] == row[
        "route_planning_brief"
    ]
    assert trace["llm_route_planner_route_option_selection_brief"] == row[
        "route_option_selection_brief"
    ]
    assert (
        trace["llm_route_planner_route_option_selected_route_option_id"]
        == "route_option:current_route_min_delta_baseline"
    )
    assert trace["llm_route_planner_primitive_evidence_matrix_witness"] == row[
        "primitive_evidence_matrix_witness"
    ]
    assert (
        trace[
            "llm_route_planner_primitive_evidence_matrix_accounting_complete"
        ]
        is True
    )
    assert (
        trace[
            "llm_route_planner_primitive_evidence_matrix_repair_obligation_count"
        ]
        == 0
    )
    assert (
        trace[
            "llm_route_planner_primitive_evidence_matrix_source_backed_missing_response_source_snippet_count"
        ]
        == 0
    )
    assert (
        trace[
            "llm_route_planner_primitive_evidence_matrix_formal_supported_missing_reuse_count"
        ]
        == 0
    )
    assert (
        trace[
            "llm_route_planner_primitive_evidence_matrix_delta_needed_missing_accounting_count"
        ]
        == 0
    )
    assert trace["llm_route_planner_route_adoption_preconditions"] == row[
        "route_adoption_preconditions"
    ]
    assert trace["has_target_theorem_context_packet"] is True
    assert trace["has_llm_route_planner_target_theorem_context_packet"] is True
    assert trace["has_llm_route_planner_route_planning_brief"] is True
    assert trace["has_llm_route_planner_route_option_selection_brief"] is True
    assert trace["llm_route_option_selection_brief_candidate_count"] == 1
    assert (
        trace[
            "llm_route_option_selection_brief_lower_bound_selected_route_option_id"
        ]
        == "route_option:current_route_min_delta_baseline"
    )
    assert trace["has_llm_route_planner_route_adoption_preconditions"] is True
    assert trace["llm_route_adoption_precondition_blocker_count"] == len(
        row["route_adoption_preconditions"]["known_pre_response_blockers"]
    )
    assert trace["llm_route_planning_brief_focus_count"] == len(
        row["route_planning_brief"]["planner_focus"]
    )
    assert trace["target_theorem_context_packet_kind"] == (
        TARGET_THEOREM_CONTEXT_PACKET_KIND
    )
    assert trace["target_theorem_context_route_id"] == row["route_id"]
    assert trace["target_theorem_context_target_prover_family"] == "lean4"
    assert trace["target_theorem_context_theorem_statement"] == row[
        "target_theorem_context_packet"
    ]["theorem_statement"]
    assert trace["target_theorem_context_theorem_statement"] != seed_route[
        "theorem_statement"
    ]
    assert trace["target_theorem_context_packet_target_mismatch"] is False
    assert trace["target_theorem_context_route_statement_differs"] is True
    assert trace["llm_route_planner_model_tier"] == row["model_tier"]
    assert trace["llm_route_planner_seed_selected"] is True
    assert trace["llm_route_planner_seed_adoptable_for_standalone_replay"] is False
    assert trace["llm_route_planner_seed_selection_rank"] == 1
    assert trace["llm_route_planner_seed_minimal_delta_route_cost"] == 4.0
    assert trace["llm_route_planner_route_adoption_status"] == (
        "PENDING_REFINEMENT_BEFORE_ROUTE_ADOPTION"
    )
    assert set(trace["llm_route_planner_route_adoption_blockers"]) >= {
        "search_requests_pending_evidence",
        "planner_next_actions_pending_evidence",
    }
    assert (
        trace["llm_route_planner_model_selection_rationale"]
        == row["model_selection_rationale"]
    )
    assert trace["llm_route_planner_generator_metadata"] == {}
    assert trace["llm_route_planner_has_generator_metadata"] is False
    assert trace["has_source_snippets"]
    assert trace["source_snippets"][0]["source_ref"] == (
        "conformal_prediction_textbook"
    )
    assert trace["primitive_source_snippets"][0]["primitive"] == "rank_uniformity"
    assert trace["has_minimal_delta_and_or_cost_graph"]
    assert trace["minimal_delta_and_or_cost_graph"]["selected_route_option_id"] == (
        row["minimal_delta_plan"]["and_or_cost_graph"]["selected_route_option_id"]
    )
    assert trace["minimal_delta_route_option_count"] == 2
    assert trace["minimal_delta_selected_route_cost"] == 4
    assert plan_row["minimal_cut_summary"]["add_bridge_lemmas"] == ["rank_uniformity"]


def test_llm_route_planner_marks_static_response_file_as_fake_generator_when_invoked() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_static_generator_mode"
    )
    out_dir = root / "llm_route_planner"
    response_json = root / "response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    response_json.write_text(
        json.dumps(_llm_response_payload(), indent=2),
        encoding="utf-8",
    )

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        provider_name="static",
        invoke_provider=True,
        static_response_json=response_json,
    )

    assert payload["all_ok"]
    assert payload["provider_execution_mode"] == (
        PROVIDER_EXECUTION_MODE_STATIC_GENERATOR_BACKEND
    )
    assert payload["invoke_provider"] is True
    assert payload["response_json_supplied"] is False
    assert payload["static_response_json_supplied"] is True
    assert payload["generator_backend_supplied"] is False
    assert payload["live_provider_backend_requested"] is False
    assert payload["static_generator_backend_requested"] is True
    assert payload["provider_generation_requested"] is True
    assert payload["n_raw_responses"] == 1
    assert payload["rows"][0]["provider_name"] == "static"
    assert payload["rows"][0]["generator_metadata"]["generator_only"] is True
    report = (
        out_dir / "formalization_gap_planner_llm_route_planner.md"
    ).read_text(encoding="utf-8")
    assert "Provider execution mode: static_generator_backend" in report


def test_llm_route_planner_marks_response_json_as_reviewed_replay() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_reviewed_response_mode"
    )
    out_dir = root / "llm_route_planner"
    response_json = root / "reviewed_response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    response_json.write_text(
        json.dumps(_llm_response_payload(), indent=2),
        encoding="utf-8",
    )

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        provider_name="anthropic",
        response_json=response_json,
    )

    assert payload["all_ok"]
    assert payload["provider_execution_mode"] == (
        PROVIDER_EXECUTION_MODE_REVIEWED_RESPONSE_JSON
    )
    assert payload["invoke_provider"] is False
    assert payload["response_json_supplied"] is True
    assert payload["static_response_json_supplied"] is False
    assert payload["generator_backend_supplied"] is False
    assert payload["live_provider_backend_requested"] is False
    assert payload["static_generator_backend_requested"] is False
    assert payload["provider_generation_requested"] is False
    assert payload["n_raw_responses"] == 1


def test_llm_route_planner_blocks_matrix_accounted_route_missing_source_snippet() -> None:
    root = Path("runs/test_formalization_gap_planner_llm_route_planner_matrix_source_gap")
    out_dir = root / "llm_route_planner"
    response_json = root / "response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    response_payload = _drop_source_snippets(_llm_response_payload())
    response_json.write_text(json.dumps(response_payload, indent=2), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        provider_name="static",
        static_response_json=response_json,
    )

    assert payload["n_rows"] == 1
    assert payload["all_ok"] is False
    assert payload["n_response_contract_ok"] == 0
    row = payload["rows"][0]
    assert row["response_contract_ok"] is False
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    assert any(
        "primitive_evidence_matrix source-backed primitives require response source_snippets"
        in error
        and "rank_uniformity" in error
        for error in row["errors"]
    )
    matrix_witness = row["primitive_evidence_matrix_witness"]
    assert matrix_witness["matrix_accounted_primitives"] == [
        "exchangeability",
        "rank_uniformity",
    ]
    assert matrix_witness["matrix_unaccounted_primitives"] == []
    assert matrix_witness[
        "source_backed_matrix_primitives_missing_response_source_snippet"
    ] == ["rank_uniformity"]
    assert matrix_witness["matrix_accounting_complete"] is False
    assert (
        payload[
            "n_primitive_evidence_matrix_source_backed_missing_response_source_snippets"
        ]
        == 1
    )
    assert payload["n_route_adoption_pending_primitive_evidence_matrix_blockers"] == 0
    assert payload["n_route_adoption_rejected"] == 1
    assert row["route_adoption_blockers"] == ("response_not_accepted",)
    assert validate_llm_route_planner_manifest(payload) == []


def test_llm_route_planner_rejects_payload_missing_schema_level_cost_graph() -> None:
    root = Path("runs/test_formalization_gap_planner_llm_route_planner_payload_schema")
    out_dir = root / "llm_route_planner"
    response_json = root / "response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    response = _llm_response_payload()
    minimal_delta = response["minimal_delta_plan"]
    assert isinstance(minimal_delta, dict)
    minimal_delta.pop("and_or_cost_graph")
    response_json.write_text(json.dumps(response, indent=2), encoding="utf-8")

    schema_errors = validate_llm_route_planner_response_payload(response)
    assert (
        "response_payload.minimal_delta_plan.and_or_cost_graph required"
        in schema_errors
    )

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        provider_name="static",
        static_response_json=response_json,
    )

    assert not payload["all_ok"]
    assert payload["n_response_schema_invalid"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    assert any(
        "response_payload.minimal_delta_plan.and_or_cost_graph required" in error
        for error in row["errors"]
    )


def test_llm_route_planner_rejects_missing_informal_dag_edges() -> None:
    root = Path("runs/test_formalization_gap_planner_llm_route_planner_missing_informal_edges")
    out_dir = root / "llm_route_planner"
    response_json = root / "response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    response = _llm_response_payload()
    response["informal_knowledge_dag_edges"] = []
    response_json.write_text(json.dumps(response, indent=2), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        provider_name="static",
        static_response_json=response_json,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    assert any(
        "informal_knowledge_dag_edges must be non-empty" in error
        and "informal_knowledge_dag_nodes has multiple nodes" in error
        for error in row["errors"]
    )


def test_llm_route_planner_rejects_informal_depends_on_missing_edge() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_depends_on_missing_edge"
    )
    out_dir = root / "llm_route_planner"
    response_json = root / "response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    response = _llm_response_payload()
    response["informal_knowledge_dag_nodes"].append(
        {
            "node_id": "informal:tie_breaking",
            "claim": "The rank route also needs a deterministic tie-breaking step.",
            "depends_on": ["informal:rank_uniformity"],
            "source_refs": ["conformal_prediction_textbook"],
            "source_search_status": "SOURCE_BACKED",
            "semantic_role": "side_condition",
        }
    )
    response_json.write_text(json.dumps(response, indent=2), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        provider_name="static",
        static_response_json=response_json,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    assert any(
        "informal_knowledge_dag_nodes[2].depends_on informal:rank_uniformity "
        "missing matching informal_knowledge_dag_edges edge "
        "informal:rank_uniformity -> informal:tie_breaking" in error
        for error in row["errors"]
    )


def test_llm_route_planner_rejects_informal_edge_missing_depends_on() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_edge_missing_depends_on"
    )
    out_dir = root / "llm_route_planner"
    response_json = root / "response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    response = _llm_response_payload()
    response["informal_knowledge_dag_nodes"][1]["depends_on"] = []
    response_json.write_text(json.dumps(response, indent=2), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        provider_name="static",
        static_response_json=response_json,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    assert any(
        "informal_knowledge_dag_edges[0] informal:exchangeability -> "
        "informal:rank_uniformity missing matching informal_knowledge_dag_nodes "
        "target depends_on entry" in error
        for error in row["errors"]
    )


def test_llm_route_planner_rejects_cyclic_formal_dag_edges() -> None:
    root = Path("runs/test_formalization_gap_planner_llm_route_planner_cyclic_formal_edges")
    out_dir = root / "llm_route_planner"
    response_json = root / "response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    response = _llm_response_payload()
    response["formal_realization_dag_edges"].append(
        {
            "source_node_id": "formal:rank_uniformity_bridge",
            "target_node_id": "formal:exchangeability",
            "edge_kind": "uses",
            "rationale": "Bad fixture creates a reverse dependency cycle.",
        }
    )
    response_json.write_text(json.dumps(response, indent=2), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        provider_name="static",
        static_response_json=response_json,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    assert any(
        "formal_realization_dag_edges must be acyclic" in error
        and "formal:exchangeability" in error
        and "formal:rank_uniformity_bridge" in error
        for error in row["errors"]
    )


def test_llm_route_planner_rejects_reversed_formal_dag_dependency_alignment() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_reversed_formal_dag_dependency"
    )
    out_dir = root / "llm_route_planner"
    response_json = root / "response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    response = _llm_response_payload()
    response["formal_realization_dag_edges"] = [
        {
            "source_node_id": "formal:rank_uniformity_bridge",
            "target_node_id": "formal:exchangeability",
            "edge_kind": "uses",
            "rationale": (
                "Bad fixture reverses the formal dependency while keeping the "
                "formal DAG acyclic."
            ),
        }
    ]
    response_json.write_text(json.dumps(response, indent=2), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        provider_name="static",
        static_response_json=response_json,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    assert not any(
        "formal_realization_dag_edges must be acyclic" in error
        for error in row["errors"]
    )
    assert any(
        "route_alignment_edges must preserve informal DAG dependencies" in error
        and "informal:exchangeability -> informal:rank_uniformity" in error
        and "formal:exchangeability" in error
        and "formal:rank_uniformity_bridge" in error
        for error in row["errors"]
    )


def test_llm_route_planner_rejects_missing_formal_attempt_queue_node() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_missing_attempt_queue_node"
    )
    out_dir = root / "llm_route_planner"
    response_json = root / "response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    response = _llm_response_payload()
    response["formal_attempt_queue"] = [
        item
        for item in response["formal_attempt_queue"]
        if item["formal_node_id"] != "formal:rank_uniformity_bridge"
    ]
    response_json.write_text(json.dumps(response, indent=2), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        provider_name="static",
        static_response_json=response_json,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    assert any(
        "formal_attempt_queue missing selected-route formal DAG nodes" in error
        and "formal:rank_uniformity_bridge" in error
        for error in row["errors"]
    )


def test_llm_route_planner_rejects_formal_attempt_queue_unselected_route_primitive() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_unselected_attempt_queue_primitive"
    )
    out_dir = root / "llm_route_planner"
    response_json = root / "response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    _append_request_route_primitive(input_json, primitive="coverage_probability")
    response = _llm_response_payload()
    _append_unselected_baseline_primitive(
        response,
        primitive="coverage_probability",
    )
    response["formal_attempt_queue"][0]["target_primitives"] = [
        "exchangeability",
        "coverage_probability",
    ]
    response_json.write_text(json.dumps(response, indent=2), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        provider_name="static",
        static_response_json=response_json,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    assert any(
        "formal_attempt_queue[0].target_primitives must stay within selected "
        "minimal_delta_plan primitives or formal_realization_dag_nodes primitives"
        in error
        and "coverage_probability" in error
        for error in row["errors"]
    )


def test_llm_route_planner_rejects_formal_attempt_queue_with_mismatched_action_target() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_rejects_mismatched_attempt_target"
    )
    out_dir = root / "llm_route_planner"
    response_json = root / "response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    response = _llm_response_payload()
    response["formal_attempt_queue"][0]["action"] = (
        "lean_lsp proof-state attempt for the rank_uniformity bridge lemma"
    )
    response_json.write_text(json.dumps(response, indent=2), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        provider_name="static",
        static_response_json=response_json,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    assert any(
        "formal_attempt_queue[0] action/query primitive mentions must include "
        "a scoped target_primitives/primitive value" in error
        and "explicit targets: exchangeability" in error
        and "action/query mentions: rank_uniformity" in error
        for error in row["errors"]
    )


def test_llm_route_planner_rejects_formal_attempt_queue_attempt_kind_drift() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_bad_attempt_queue_kind"
    )
    out_dir = root / "llm_route_planner"
    response_json = root / "response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    response = _llm_response_payload()
    response["formal_attempt_queue"][1]["attempt_kind"] = "reuse_check"
    response_json.write_text(json.dumps(response, indent=2), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        provider_name="static",
        static_response_json=response_json,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    assert any(
        "formal_attempt_queue[1].attempt_kind reuse_check is inconsistent "
        "with formal node formal:rank_uniformity_bridge coverage/action bucket "
        "bridge" in error
        and "bridge_proof" in error
        for error in row["errors"]
    )


def test_llm_route_planner_rejects_formal_attempt_queue_feedback_drift() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_bad_attempt_queue_feedback"
    )
    out_dir = root / "llm_route_planner"
    response_json = root / "response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    response = _llm_response_payload()
    response["formal_attempt_queue"][1]["expected_feedback"] = [
        "closed_by_existing_declaration"
    ]
    response_json.write_text(json.dumps(response, indent=2), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        provider_name="static",
        static_response_json=response_json,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    assert any(
        "formal_attempt_queue[1].expected_feedback for attempt_kind "
        "bridge_proof must include at least one of" in error
        and "residual_goals" in error
        and "missing_side_conditions" in error
        for error in row["errors"]
    )


def test_llm_route_planner_rejects_formal_attempt_queue_order_drift() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_bad_attempt_queue_order"
    )
    out_dir = root / "llm_route_planner"
    response_json = root / "response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    response = _llm_response_payload()
    response["formal_attempt_queue"] = list(reversed(response["formal_attempt_queue"]))
    response_json.write_text(json.dumps(response, indent=2), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        provider_name="static",
        static_response_json=response_json,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    assert any(
        "must appear after prerequisite formal node formal:exchangeability"
        in error
        for error in row["errors"]
    )
    assert any(
        "formal_attempt_queue order must follow formal_realization_dag_edges"
        in error
        and "formal:exchangeability before formal:rank_uniformity_bridge" in error
        for error in row["errors"]
    )


def test_llm_route_planner_rejects_formal_attempt_queue_prerequisite_mismatch() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_bad_attempt_queue_prereq"
    )
    out_dir = root / "llm_route_planner"
    response_json = root / "response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    response = _llm_response_payload()
    response["formal_attempt_queue"][1]["prerequisite_formal_node_ids"] = []
    response_json.write_text(json.dumps(response, indent=2), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        provider_name="static",
        static_response_json=response_json,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    assert any(
        "formal_attempt_queue[1].prerequisite_formal_node_ids must match "
        "formal_realization_dag_edges immediate predecessors" in error
        and "formal:exchangeability" in error
        for error in row["errors"]
    )


def test_llm_route_planner_rejects_route_aligned_nodes_disconnected_from_dag_edges() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_disconnected_aligned_nodes"
    )
    out_dir = root / "llm_route_planner"
    response_json = root / "response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    response = _llm_response_payload()
    response["informal_knowledge_dag_nodes"].append(
        {
            "node_id": "informal:rank_uniformity_isolated",
            "claim": "An isolated duplicate rank-uniformity informal step.",
            "source_refs": ["conformal_prediction_textbook"],
            "source_search_status": "SOURCE_BACKED",
            "semantic_role": "lemma",
            "supported_target_primitives": ["rank_uniformity"],
        }
    )
    response["lean_realization_dag_nodes"].append(
        {
            "node_id": "formal:rank_uniformity_isolated",
            "primitive": "rank_uniformity",
            "coverage_bucket": "bridge",
            "candidate_declarations": [],
            "formalization_action": "prove_bridge",
        }
    )
    response["route_alignment_edges"][0]["informal_node_id"] = (
        "informal:rank_uniformity_isolated"
    )
    response["route_alignment_edges"][0]["formal_node_id"] = (
        "formal:rank_uniformity_isolated"
    )
    response_json.write_text(json.dumps(response, indent=2), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        provider_name="static",
        static_response_json=response_json,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    witness = row["realization_coverage_witness"]
    assert witness["route_relevant_dag_endpoint_complete"] is False
    assert witness["route_relevant_informal_nodes_missing_dag_edge_endpoint"] == [
        "informal:rank_uniformity_isolated"
    ]
    assert witness["route_relevant_formal_nodes_missing_dag_edge_endpoint"] == [
        "formal:rank_uniformity_isolated"
    ]
    assert any(
        "informal_knowledge_dag_edges do not connect route-relevant" in error
        and "informal:rank_uniformity_isolated" in error
        for error in row["errors"]
    )
    assert any(
        "formal_realization_dag_edges do not connect route-relevant" in error
        and "formal:rank_uniformity_isolated" in error
        for error in row["errors"]
    )


def test_llm_route_planner_response_payload_validator_accepts_raw_payload() -> None:
    root = Path("runs/test_formalization_gap_planner_llm_payload_validate")
    out_dir = root / "out"
    response_json = root / "response_payload.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    response_json.write_text(
        json.dumps(_llm_response_payload(), indent=2),
        encoding="utf-8",
    )

    payload = validate_formalization_gap_planner_llm_route_planner_response_payloads(
        response_json,
        out_dir,
    )

    assert payload["all_ok"]
    assert payload["component_name"] == (
        "formalization_gap_planner_llm_route_planner_response_payload_validator"
    )
    assert payload["response_payload_schema_id"] == (
        LLM_ROUTE_PLANNER_RESPONSE_PAYLOAD_SCHEMA_ID
    )
    assert payload["response_payload_validation_manifest_schema_id"] == (
        LLM_ROUTE_PLANNER_RESPONSE_PAYLOAD_VALIDATION_MANIFEST_SCHEMA_ID
    )
    assert payload["response_payload_validation_row_schema_id"] == (
        LLM_ROUTE_PLANNER_RESPONSE_PAYLOAD_VALIDATION_ROW_SCHEMA_ID
    )
    assert payload["response_payload_validation_manifest_schema"]["$id"] == (
        LLM_ROUTE_PLANNER_RESPONSE_PAYLOAD_VALIDATION_MANIFEST_SCHEMA_ID
    )
    assert payload["response_payload_validation_row_schema"]["$id"] == (
        LLM_ROUTE_PLANNER_RESPONSE_PAYLOAD_VALIDATION_ROW_SCHEMA_ID
    )
    manifest_schema = payload["response_payload_validation_manifest_schema"]
    assert manifest_schema["properties"]["response_payload_schema"]["properties"][
        "$id"
    ]["const"] == LLM_ROUTE_PLANNER_RESPONSE_PAYLOAD_SCHEMA_ID
    assert manifest_schema["properties"][
        "response_payload_validation_manifest_schema"
    ]["properties"]["$id"]["const"] == (
        LLM_ROUTE_PLANNER_RESPONSE_PAYLOAD_VALIDATION_MANIFEST_SCHEMA_ID
    )
    assert manifest_schema["properties"]["response_payload_validation_row_schema"][
        "properties"
    ]["$id"]["const"] == LLM_ROUTE_PLANNER_RESPONSE_PAYLOAD_VALIDATION_ROW_SCHEMA_ID
    assert (
        validate_llm_route_planner_response_payload_validation_manifest(
            payload,
            manifest_schema,
        )
        == []
    )
    assert payload["n_payloads"] == 1
    assert payload["n_valid_payloads"] == 1
    assert payload["n_invalid_payloads"] == 0
    assert payload["n_request_context_packets"] == 0
    assert payload["n_request_contexts_with_context_packet_inventory"] == 0
    assert payload["n_request_context_inventory_total_rows"] == 0
    assert payload["n_request_bound_payloads"] == 0
    assert payload["n_request_bound_payloads_with_route_adoption_status"] == 0
    assert payload["n_request_bound_payloads_route_adoption_ready"] == 0
    assert payload["n_request_bound_payloads_route_adoption_pending_refinement"] == 0
    assert payload["n_request_bound_payloads_route_adoption_rejected"] == 0
    assert payload["n_request_bound_payloads_adoptable_for_standalone_replay"] == 0
    assert payload["by_request_bound_payload_route_adoption_status"] == {}
    assert payload["request_bound_payload_route_adoption_blocker_counts"] == {}
    assert payload["n_request_bound_payloads_with_context_packet_inventory"] == 0
    assert payload["n_request_bound_payload_context_inventory_total_rows"] == 0
    assert payload["n_request_bound_payloads_with_route_adoption_preconditions"] == 0
    assert (
        payload[
            "n_request_bound_payloads_with_blocking_route_adoption_preconditions"
        ]
        == 0
    )
    assert (
        payload[
            "n_request_bound_payload_route_adoption_precondition_known_blockers"
        ]
        == 0
    )
    assert (
        payload[
            "n_request_bound_payload_route_adoption_precondition_required_response_fields"
        ]
        == 0
    )
    assert payload["n_payloads_with_formal_attempt_queue"] == 1
    assert payload["n_payload_formal_attempt_queue_items"] == 2
    assert payload["n_payloads_with_formal_attempt_queue_errors"] == 0
    assert payload["n_formal_attempt_queue_errors"] == 0
    assert payload["n_payloads_with_declared_target_prover_family"] == 0
    assert (
        payload["n_request_bound_payloads_with_target_prover_family_mismatch"]
        == 0
    )
    assert payload["by_payload_target_prover_family"] == {}
    assert payload["by_request_context_target_prover_family"] == {}
    row = payload["rows"][0]
    assert row["ok"]
    assert not row["response_wrapper_present"]
    assert row["payload_schema_id"] == LLM_ROUTE_PLANNER_RESPONSE_PAYLOAD_SCHEMA_ID
    assert row["request_context_validation_mode"] == "schema_only"
    assert row["request_context_id"] == ""
    assert row["payload_target_prover_family"] == ""
    assert row["payload_target_prover_key"] == ""
    assert row["request_context_target_prover_family"] == ""
    assert row["request_context_target_prover_key"] == ""
    assert row["target_prover_family_consistent"] is True
    assert row["request_context_inventory_present"] is False
    assert row["request_context_inventory_total_rows"] == 0
    assert row["request_context_route_adoption_precondition_present"] is False
    assert (
        row[
            "request_context_route_adoption_precondition_blocked_before_response"
        ]
        is False
    )
    assert row["request_context_route_adoption_precondition_known_blocker_count"] == 0
    assert (
        row[
            "request_context_route_adoption_precondition_required_response_field_count"
        ]
        == 0
    )
    assert row["request_context_agentic_proof_strategy_plan_present"] is False
    assert row["request_context_agentic_proof_strategy_plan_row_count"] == 0
    assert row["request_context_agentic_proof_strategy_plan_ready_count"] == 0
    assert row["request_bound_response_contract_ok"] is False
    assert row["request_bound_route_adoption_status"] == ""
    assert row["request_bound_route_adoption_blockers"] == []
    assert row["request_bound_adoptable_for_standalone_replay"] is False
    assert row["payload_formal_attempt_queue_present"] is True
    assert row["payload_formal_attempt_queue_item_count"] == 2
    assert row["n_formal_attempt_queue_errors"] == 0
    assert row["n_agentic_proof_strategy_plan_obligation_errors"] == 0
    assert row["n_schema_errors"] == 0
    assert row["n_request_context_errors"] == 0
    row_schema = payload["response_payload_validation_row_schema"]
    assert row_schema["properties"]["n_errors"]["minimum"] == 0
    assert row_schema["properties"]["payload_index"]["minimum"] == 0
    assert row_schema["properties"]["target_prover_family_consistent"][
        "type"
    ] == "boolean"
    assert row_schema["properties"][
        "request_context_route_adoption_precondition_present"
    ]["type"] == "boolean"
    assert (
        row_schema["properties"]["request_bound_route_adoption_status"]["enum"]
        == [
            "",
            "READY_FOR_STANDALONE_REPLAY",
            "PENDING_REFINEMENT_BEFORE_ROUTE_ADOPTION",
            "AWAITING_LLM_ROUTE_PLANNER_RESPONSE",
            "REJECTED_LLM_ROUTE_PLAN",
        ]
    )
    assert (
        validate_llm_route_planner_response_payload_validation_row(
            row,
            row_schema,
        )
        == []
    )
    drifted_row = deepcopy(row)
    drifted_row["n_errors"] = 1
    assert "n_errors must match errors length" in (
        validate_llm_route_planner_response_payload_validation_row(
            drifted_row,
            row_schema,
        )
    )
    drifted_ok_row = deepcopy(row)
    drifted_ok_row["ok"] = False
    assert "failed validation row must carry n_errors" in (
        validate_llm_route_planner_response_payload_validation_row(
            drifted_ok_row,
            row_schema,
        )
    )
    drifted_negative_row = deepcopy(row)
    drifted_negative_row["n_schema_errors"] = -1
    assert "n_schema_errors must be nonnegative" in (
        validate_llm_route_planner_response_payload_validation_row(
            drifted_negative_row,
            row_schema,
        )
    )
    drifted_schema_only_adoption_row = deepcopy(row)
    drifted_schema_only_adoption_row["request_bound_route_adoption_status"] = (
        "READY_FOR_STANDALONE_REPLAY"
    )
    assert (
        "request_bound_route_adoption_status must be empty without "
        "request_bound context"
    ) in validate_llm_route_planner_response_payload_validation_row(
        drifted_schema_only_adoption_row,
        row_schema,
    )
    drifted_adoption_manifest = deepcopy(payload)
    drifted_adoption_manifest[
        "n_request_bound_payloads_with_route_adoption_status"
    ] = 1
    assert (
        "n_request_bound_payloads_with_route_adoption_status must match "
        "request_bound rows with route adoption status"
    ) in validate_llm_route_planner_response_payload_validation_manifest(
        drifted_adoption_manifest,
        manifest_schema,
    )
    drifted_queue_count_row = deepcopy(row)
    drifted_queue_count_row["payload_formal_attempt_queue_present"] = False
    assert (
        "payload_formal_attempt_queue_present must be true when "
        "payload_formal_attempt_queue_item_count is nonzero"
        in validate_llm_route_planner_response_payload_validation_row(
            drifted_queue_count_row,
            row_schema,
        )
    )
    drifted_queue_error_row = deepcopy(row)
    drifted_queue_error_row["n_formal_attempt_queue_errors"] = 1
    assert (
        "n_formal_attempt_queue_errors must match errors containing "
        "formal_attempt_queue"
        in validate_llm_route_planner_response_payload_validation_row(
            drifted_queue_error_row,
            row_schema,
        )
    )
    drifted_agentic_count_row = deepcopy(row)
    drifted_agentic_count_row["n_agentic_proof_strategy_plan_obligation_errors"] = 1
    assert (
        "n_agentic_proof_strategy_plan_obligation_errors must match "
        "agentic strategy obligation errors"
        in validate_llm_route_planner_response_payload_validation_row(
            drifted_agentic_count_row,
            row_schema,
        )
    )
    drifted_agentic_presence_row = deepcopy(row)
    drifted_agentic_presence_row[
        "request_context_agentic_proof_strategy_plan_row_count"
    ] = 1
    assert (
        "request_context_agentic_proof_strategy_plan_present must be true "
        "when agentic strategy plan count fields are nonzero"
        in validate_llm_route_planner_response_payload_validation_row(
            drifted_agentic_presence_row,
            row_schema,
        )
    )
    drifted_target_row = deepcopy(row)
    drifted_target_row["payload_target_prover_family"] = "Lean 4"
    drifted_target_row["payload_target_prover_key"] = "lean4"
    drifted_target_row["request_context_target_prover_family"] = "Rocq"
    drifted_target_row["request_context_target_prover_key"] = "rocq"
    drifted_target_row["target_prover_family_consistent"] = True
    assert (
        "target_prover_family_consistent must match normalized payload and request target prover keys"
        in validate_llm_route_planner_response_payload_validation_row(
            drifted_target_row,
            row_schema,
        )
    )
    assert (
        out_dir
        / "formalization_gap_planner_llm_route_planner_response_payload_validation_manifest.json"
    ).exists()
    assert (
        out_dir
        / "formalization_gap_planner_llm_route_planner_response_payload_validation.jsonl"
    ).exists()
    assert (
        out_dir
        / "formalization_gap_planner_llm_route_planner_response_payload_validation_manifest.schema.json"
    ).exists()
    assert (
        out_dir
        / "formalization_gap_planner_llm_route_planner_response_payload_validation_row.schema.json"
    ).exists()
    drifted_count_manifest = deepcopy(payload)
    drifted_count_manifest["n_valid_payloads"] = 0
    assert (
        "n_valid_payloads must match rows with ok=true"
        in validate_llm_route_planner_response_payload_validation_manifest(
            drifted_count_manifest,
            manifest_schema,
        )
    )
    drifted_target_count_manifest = deepcopy(payload)
    drifted_target_count_manifest["n_payloads_with_declared_target_prover_family"] = 1
    assert (
        "n_payloads_with_declared_target_prover_family must match rows with payload_target_prover_family"
        in validate_llm_route_planner_response_payload_validation_manifest(
            drifted_target_count_manifest,
            manifest_schema,
        )
    )
    drifted_queue_items_manifest = deepcopy(payload)
    drifted_queue_items_manifest["n_payload_formal_attempt_queue_items"] = 0
    assert (
        "n_payload_formal_attempt_queue_items must match row "
        "payload_formal_attempt_queue_item_count sum"
        in validate_llm_route_planner_response_payload_validation_manifest(
            drifted_queue_items_manifest,
            manifest_schema,
        )
    )
    drifted_agentic_manifest = deepcopy(payload)
    drifted_agentic_manifest[
        "n_agentic_proof_strategy_plan_obligation_errors"
    ] = 1
    assert (
        "n_agentic_proof_strategy_plan_obligation_errors must match row "
        "n_agentic_proof_strategy_plan_obligation_errors sum"
        in validate_llm_route_planner_response_payload_validation_manifest(
            drifted_agentic_manifest,
            manifest_schema,
        )
    )
    drifted_schema_manifest = deepcopy(payload)
    drifted_schema_manifest["response_payload_validation_row_schema"][
        "$id"
    ] = "urn:wrong-validation-row-schema"
    assert (
        "response_payload_validation_row_schema.$id must equal "
        + LLM_ROUTE_PLANNER_RESPONSE_PAYLOAD_VALIDATION_ROW_SCHEMA_ID
        in validate_llm_route_planner_response_payload_validation_manifest(
            drifted_schema_manifest,
            manifest_schema,
        )
    )
    drifted_row_manifest = deepcopy(payload)
    drifted_row_manifest["rows"][0].pop("payload_schema_id")
    assert (
        "rows[0].payload_schema_id required"
        in validate_llm_route_planner_response_payload_validation_manifest(
            drifted_row_manifest,
            manifest_schema,
        )
    )
    drifted_row_count_manifest = deepcopy(payload)
    drifted_row_count_manifest["rows"][0]["n_errors"] = 1
    assert (
        "rows[0].n_errors must match errors length"
        in validate_llm_route_planner_response_payload_validation_manifest(
            drifted_row_count_manifest,
            manifest_schema,
        )
    )


def test_response_payload_validator_blocks_request_bound_formal_attempt_queue_adoption() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_payload_validate_request_ready"
    )
    out_dir = root / "llm_route_planner"
    response_json = root / "responses.json"
    request_context_json = root / "request_context.json"
    validation_out_dir = root / "response_payload_validation"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    prompt_payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        provider_name="prompt_only",
    )
    request = prompt_payload["request_packets"][0]
    request_context_json.write_text(
        json.dumps({"request_packets": [request]}, indent=2),
        encoding="utf-8",
    )
    response_payload = _llm_response_payload()
    response_payload["search_requests"] = []
    response_payload["planner_next_actions"] = []
    response_payload["uncertainty_flags"] = []
    response_payload["semantic_alignment_risks"] = []
    response_json.write_text(
        json.dumps(
            {
                "responses": [
                    {
                        "request_id": request["request_id"],
                        "route_id": request["route_id"],
                        "response_payload": response_payload,
                    }
                ]
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    validation_payload = validate_formalization_gap_planner_llm_route_planner_response_payloads(
        response_json,
        validation_out_dir,
        request_context_json=request_context_json,
    )

    assert validation_payload["all_ok"] is True
    assert validation_payload["n_request_bound_payloads"] == 1
    assert validation_payload["n_request_bound_payloads_with_route_adoption_status"] == 1
    assert validation_payload["n_request_bound_payloads_route_adoption_ready"] == 0
    assert (
        validation_payload[
            "n_request_bound_payloads_route_adoption_pending_refinement"
        ]
        == 1
    )
    assert (
        validation_payload[
            "n_request_bound_payloads_adoptable_for_standalone_replay"
        ]
        == 0
    )
    assert validation_payload["by_request_bound_payload_route_adoption_status"] == {
        "PENDING_REFINEMENT_BEFORE_ROUTE_ADOPTION": 1
    }
    assert validation_payload[
        "request_bound_payload_route_adoption_blocker_counts"
    ] == {ROUTE_ADOPTION_BLOCKER_FORMAL_ATTEMPT_QUEUE: 1}
    row = validation_payload["rows"][0]
    assert row["request_bound_response_contract_ok"] is True
    assert row["request_bound_route_adoption_status"] == (
        "PENDING_REFINEMENT_BEFORE_ROUTE_ADOPTION"
    )
    assert row["request_bound_route_adoption_blockers"] == [
        ROUTE_ADOPTION_BLOCKER_FORMAL_ATTEMPT_QUEUE
    ]
    assert row["request_bound_adoptable_for_standalone_replay"] is False
    assert (
        validate_llm_route_planner_response_payload_validation_manifest(
            validation_payload,
            validation_payload["response_payload_validation_manifest_schema"],
        )
        == []
    )


def test_llm_route_planner_response_payload_validator_rejects_wrapper_payload() -> None:
    root = Path("runs/test_formalization_gap_planner_llm_payload_validate_bad")
    out_dir = root / "out"
    response_json = root / "response_payload.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    response = _llm_response_payload()
    minimal_delta = response["minimal_delta_plan"]
    assert isinstance(minimal_delta, dict)
    minimal_delta.pop("and_or_cost_graph")
    response_json.write_text(
        json.dumps(
            {
                "request_id": "request:fixture",
                "route_id": "route:fixture",
                "response_payload": response,
                "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    payload = validate_formalization_gap_planner_llm_route_planner_response_payloads(
        response_json,
        out_dir,
    )

    assert not payload["all_ok"]
    assert payload["n_payloads"] == 1
    assert payload["n_valid_payloads"] == 0
    assert payload["n_invalid_payloads"] == 1
    row = payload["rows"][0]
    assert row["response_wrapper_present"]
    assert row["request_id"] == "request:fixture"
    assert row["route_id"] == "route:fixture"
    assert row["errors"] == [
        "response_payload.minimal_delta_plan.and_or_cost_graph required"
    ]


def test_llm_route_planner_response_payload_validator_counts_formal_attempt_queue_errors() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_payload_validate_bad_attempt_queue"
    )
    out_dir = root / "out"
    response_json = root / "response_payload.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    response = _llm_response_payload()
    response["formal_attempt_queue"] = [
        item
        for item in response["formal_attempt_queue"]
        if item["formal_node_id"] != "formal:rank_uniformity_bridge"
    ]
    response_json.write_text(json.dumps(response, indent=2), encoding="utf-8")

    payload = validate_formalization_gap_planner_llm_route_planner_response_payloads(
        response_json,
        out_dir,
    )

    assert not payload["all_ok"]
    assert payload["n_payloads"] == 1
    assert payload["n_valid_payloads"] == 0
    assert payload["n_invalid_payloads"] == 1
    assert payload["n_payloads_with_formal_attempt_queue"] == 1
    assert payload["n_payload_formal_attempt_queue_items"] == 1
    assert payload["n_payloads_with_formal_attempt_queue_errors"] == 1
    assert payload["n_formal_attempt_queue_errors"] >= 1
    row = payload["rows"][0]
    assert row["payload_formal_attempt_queue_present"] is True
    assert row["payload_formal_attempt_queue_item_count"] == 1
    assert row["n_formal_attempt_queue_errors"] >= 1
    assert row["n_schema_errors"] >= row["n_formal_attempt_queue_errors"]
    assert any(
        "formal_attempt_queue missing selected-route formal DAG nodes" in error
        and "formal:rank_uniformity_bridge" in error
        for error in row["errors"]
    )


def test_llm_route_planner_payload_validator_rejects_unselected_attempt_queue_primitive() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_payload_validate_unselected_attempt_primitive"
    )
    out_dir = root / "out"
    response_json = root / "response_payload.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    response = _llm_response_payload()
    _append_unselected_baseline_primitive(
        response,
        primitive="coverage_probability",
    )
    response["formal_attempt_queue"][0]["target_primitives"] = [
        "exchangeability",
        "coverage_probability",
    ]
    response_json.write_text(json.dumps(response, indent=2), encoding="utf-8")

    payload = validate_formalization_gap_planner_llm_route_planner_response_payloads(
        response_json,
        out_dir,
    )

    assert not payload["all_ok"]
    assert payload["n_payloads"] == 1
    assert payload["n_valid_payloads"] == 0
    assert payload["n_invalid_payloads"] == 1
    assert payload["n_payloads_with_formal_attempt_queue"] == 1
    assert payload["n_payload_formal_attempt_queue_items"] == 2
    assert payload["n_payloads_with_formal_attempt_queue_errors"] == 1
    assert payload["n_formal_attempt_queue_errors"] == 1
    row = payload["rows"][0]
    assert row["payload_formal_attempt_queue_present"] is True
    assert row["payload_formal_attempt_queue_item_count"] == 2
    assert row["n_formal_attempt_queue_errors"] == 1
    assert row["n_schema_errors"] >= row["n_formal_attempt_queue_errors"]
    assert any(
        "formal_attempt_queue[0].target_primitives must stay within selected "
        "minimal_delta_plan primitives or formal_realization_dag_nodes primitives"
        in error
        and "coverage_probability" in error
        for error in row["errors"]
    )


def test_llm_route_planner_payload_validator_rejects_attempt_queue_kind_drift() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_payload_validate_attempt_kind_drift"
    )
    out_dir = root / "out"
    response_json = root / "response_payload.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    response = _llm_response_payload()
    response["formal_attempt_queue"][1]["attempt_kind"] = "reuse_check"
    response_json.write_text(json.dumps(response, indent=2), encoding="utf-8")

    payload = validate_formalization_gap_planner_llm_route_planner_response_payloads(
        response_json,
        out_dir,
    )

    assert not payload["all_ok"]
    assert payload["n_payloads"] == 1
    assert payload["n_valid_payloads"] == 0
    assert payload["n_invalid_payloads"] == 1
    assert payload["n_payloads_with_formal_attempt_queue"] == 1
    assert payload["n_payload_formal_attempt_queue_items"] == 2
    assert payload["n_payloads_with_formal_attempt_queue_errors"] == 1
    assert payload["n_formal_attempt_queue_errors"] == 1
    row = payload["rows"][0]
    assert row["n_formal_attempt_queue_errors"] == 1
    assert any(
        "formal_attempt_queue[1].attempt_kind reuse_check is inconsistent "
        "with formal node formal:rank_uniformity_bridge coverage/action bucket "
        "bridge" in error
        and "bridge_proof" in error
        for error in row["errors"]
    )


def test_llm_route_planner_payload_validator_rejects_attempt_queue_feedback_drift() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_payload_validate_attempt_feedback_drift"
    )
    out_dir = root / "out"
    response_json = root / "response_payload.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    response = _llm_response_payload()
    response["formal_attempt_queue"][1]["expected_feedback"] = [
        "closed_by_existing_declaration"
    ]
    response_json.write_text(json.dumps(response, indent=2), encoding="utf-8")

    payload = validate_formalization_gap_planner_llm_route_planner_response_payloads(
        response_json,
        out_dir,
    )

    assert not payload["all_ok"]
    assert payload["n_payloads"] == 1
    assert payload["n_valid_payloads"] == 0
    assert payload["n_invalid_payloads"] == 1
    assert payload["n_payloads_with_formal_attempt_queue"] == 1
    assert payload["n_payload_formal_attempt_queue_items"] == 2
    assert payload["n_payloads_with_formal_attempt_queue_errors"] == 1
    assert payload["n_formal_attempt_queue_errors"] == 1
    row = payload["rows"][0]
    assert row["n_formal_attempt_queue_errors"] == 1
    assert any(
        "formal_attempt_queue[1].expected_feedback for attempt_kind "
        "bridge_proof must include at least one of" in error
        and "residual_goals" in error
        and "missing_side_conditions" in error
        for error in row["errors"]
    )


def test_llm_route_planner_payload_validator_rejects_non_lean_legacy_alias_schema_only() -> None:
    root = Path("runs/test_formalization_gap_planner_llm_payload_validate_rocq_alias")
    out_dir = root / "out"
    response_json = root / "response_payload.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    response = _llm_response_payload()
    response["target_prover_family"] = "rocq"
    response["standalone_route"]["target_prover_family"] = "rocq"
    response_json.write_text(json.dumps(response, indent=2), encoding="utf-8")

    direct_errors = validate_llm_route_planner_response_payload(response)
    assert any(
        "lean_realization_dag_nodes is a Lean-only legacy alias" in error
        for error in direct_errors
    )

    payload = validate_formalization_gap_planner_llm_route_planner_response_payloads(
        response_json,
        out_dir,
    )

    assert not payload["all_ok"]
    assert payload["n_payloads"] == 1
    assert payload["n_valid_payloads"] == 0
    assert payload["n_invalid_payloads"] == 1
    row = payload["rows"][0]
    assert row["request_context_validation_mode"] == "schema_only"
    assert row["n_schema_errors"] == 3
    assert row["n_request_context_errors"] == 0
    assert row["n_formal_attempt_queue_errors"] == 2
    assert any(
        "lean_realization_dag_nodes is a Lean-only legacy alias" in error
        for error in row["errors"]
    )
    assert any(
        "formal_attempt_queue[0].target_prover_family lean4 does not match "
        "request target_prover_family rocq" in error
        for error in row["errors"]
    )


def test_llm_route_planner_payload_validator_rejects_candidate_row_target_mismatch_schema_only() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_payload_validate_candidate_target"
    )
    out_dir = root / "out"
    response_json = root / "response_payload.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    response = _llm_response_payload()
    response["target_prover_family"] = "rocq"
    response["formal_realization_dag_nodes"] = response.pop(
        "lean_realization_dag_nodes"
    )
    response["standalone_route"]["target_prover_family"] = "rocq"
    bad_declaration_row = {
        "declaration": "Mathlib.Probability.exchangeable",
        "target_prover_family": "lean4",
        "source_field": "available_formal_declaration_rows",
    }
    response["formal_realization_dag_nodes"][0].pop("candidate_declarations", None)
    response["formal_realization_dag_nodes"][0]["candidate_declaration_rows"] = [
        bad_declaration_row
    ]
    response["standalone_route"]["primitives"][0].pop(
        "candidate_declarations",
        None,
    )
    response["standalone_route"]["primitives"][0][
        "candidate_declaration_rows"
    ] = [bad_declaration_row]
    response_json.write_text(json.dumps(response, indent=2), encoding="utf-8")

    direct_errors = validate_llm_route_planner_response_payload(response)
    assert any(
        "candidate_declaration_rows[0].target_prover_family lean4 does not "
        "match declared payload target_prover_family rocq" in error
        for error in direct_errors
    )

    payload = validate_formalization_gap_planner_llm_route_planner_response_payloads(
        response_json,
        out_dir,
    )

    assert not payload["all_ok"]
    assert payload["n_payloads"] == 1
    assert payload["n_valid_payloads"] == 0
    assert payload["n_invalid_payloads"] == 1
    row = payload["rows"][0]
    assert row["request_context_validation_mode"] == "schema_only"
    assert row["n_schema_errors"] >= 1
    assert any(
        "candidate_declaration_rows[0].target_prover_family lean4 does not "
        "match declared payload target_prover_family rocq" in error
        for error in row["errors"]
    )


def test_llm_route_planner_payload_validator_rejects_non_lean_legacy_declaration_hits_schema_only() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_payload_validate_rocq_legacy_hits"
    )
    out_dir = root / "out"
    response_json = root / "response_payload.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    response = _llm_response_payload()
    response["target_prover_family"] = "rocq"
    response["formal_realization_dag_nodes"] = response.pop(
        "lean_realization_dag_nodes"
    )
    response["standalone_route"]["target_prover_family"] = "rocq"
    response["formal_realization_dag_nodes"][0]["lean_declaration_hits"] = [
        {"declaration": "Mathlib.Probability.exchangeable"}
    ]
    response["standalone_route"]["primitives"][0]["lean_declaration_hits"] = [
        {"declaration": "Mathlib.Probability.exchangeable"}
    ]
    response_json.write_text(json.dumps(response, indent=2), encoding="utf-8")

    direct_errors = validate_llm_route_planner_response_payload(response)
    assert any(
        "formal_realization_dag_nodes[0].lean_declaration_hits is a Lean-only "
        "legacy declaration field" in error
        for error in direct_errors
    )
    assert any(
        "standalone_route.primitives[0].lean_declaration_hits is a Lean-only "
        "legacy declaration field" in error
        for error in direct_errors
    )

    payload = validate_formalization_gap_planner_llm_route_planner_response_payloads(
        response_json,
        out_dir,
    )

    assert not payload["all_ok"]
    assert payload["n_payloads"] == 1
    assert payload["n_valid_payloads"] == 0
    assert payload["n_invalid_payloads"] == 1
    row = payload["rows"][0]
    assert row["request_context_validation_mode"] == "schema_only"
    assert row["n_schema_errors"] >= 2
    assert any(
        "lean_declaration_hits is a Lean-only legacy declaration field" in error
        for error in row["errors"]
    )


def test_llm_route_planner_response_payload_validator_request_context_accepts_payload() -> None:
    root = Path("runs/test_formalization_gap_planner_llm_payload_validate_request_bound")
    planner_dir = root / "llm_route_planner"
    out_dir = root / "out"
    response_json = root / "response_payload.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    staged = export_formalization_gap_planner_llm_route_planner(
        _write_input(root),
        planner_dir,
        provider_name="prompt_only",
    )
    request = staged["request_packets"][0]
    response_json.write_text(
        json.dumps(
            {
                "request_id": request["request_id"],
                "route_id": request["route_id"],
                "response_payload": _llm_response_payload(),
                "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    payload = validate_formalization_gap_planner_llm_route_planner_response_payloads(
        response_json,
        out_dir,
        request_context_json=planner_dir,
    )

    assert payload["all_ok"]
    assert payload["n_request_context_packets"] == 1
    assert payload["n_request_contexts_with_context_packet_inventory"] == 1
    assert payload["n_request_context_inventory_total_rows"] == request[
        "context_packet"
    ]["context_packet_inventory"]["total_context_rows"]
    assert payload["n_request_bound_payloads"] == 1
    assert payload["n_request_bound_payloads_with_context_packet_inventory"] == 1
    assert payload[
        "n_request_bound_payload_context_inventory_total_rows"
    ] == request["context_packet"]["context_packet_inventory"]["total_context_rows"]
    assert payload["n_payloads_with_declared_target_prover_family"] == 0
    assert (
        payload["n_request_bound_payloads_with_target_prover_family_mismatch"]
        == 0
    )
    assert payload["by_payload_target_prover_family"] == {}
    assert payload["by_request_context_target_prover_family"] == {"lean4": 1}
    assert payload["n_request_context_errors"] == 0
    row = payload["rows"][0]
    assert row["request_context_validation_mode"] == "request_bound"
    assert row["request_context_id"] == request["request_id"]
    assert row["request_context_route_id"] == request["route_id"]
    assert row["payload_target_prover_family"] == ""
    assert row["payload_target_prover_key"] == ""
    assert row["request_context_target_prover_family"] == "lean4"
    assert row["request_context_target_prover_key"] == "lean4"
    assert row["target_prover_family_consistent"] is True
    assert row["request_context_inventory_present"] is True
    assert row["request_context_inventory_total_rows"] == request["context_packet"][
        "context_packet_inventory"
    ]["total_context_rows"]
    assert row["n_schema_errors"] == 0
    assert row["n_request_context_errors"] == 0


def test_llm_route_planner_response_payload_validator_accepts_legacy_target_summary_aliases() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_payload_validate_legacy_target_summary"
    )
    planner_dir = root / "llm_route_planner"
    target_intake_dir = root / "target_intake"
    out_dir = root / "out"
    response_json = root / "response_payload.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    _write_rank_target_intake_manifest(target_intake_dir)
    staged = export_formalization_gap_planner_llm_route_planner(
        _write_input(root),
        planner_dir,
        provider_name="prompt_only",
        formalization_gap_planner_target_intake_dir=target_intake_dir,
    )
    request = staged["request_packets"][0]
    response = _llm_response_payload()
    response["target_context_summary"] = {
        "normalized_objects": [
            "calibration scores",
            "test score",
            "rank statistic",
        ],
        "normalized_assumptions": [
            "exchangeability",
            "deterministic tie handling",
        ],
        "normalized_statistical_procedures": ["split conformal prediction"],
        "normalized_desired_conclusions": ["finite-sample rank coverage"],
        "normalized_theorem_shapes": ["finite_sample_rank_coverage"],
        "target_intake_ids": ["target-intake:rank-context"],
        "proof_source_refs": ["conformal_prediction_textbook"],
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
    }
    response_json.write_text(
        json.dumps(
            {
                "request_id": request["request_id"],
                "route_id": request["route_id"],
                "response_payload": response,
                "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    payload = validate_formalization_gap_planner_llm_route_planner_response_payloads(
        response_json,
        out_dir,
        request_context_json=planner_dir,
    )

    assert payload["all_ok"]
    row = payload["rows"][0]
    assert row["request_context_validation_mode"] == "request_bound"
    assert row["n_schema_errors"] == 0
    assert row["n_request_context_errors"] == 0
    assert validate_llm_route_planner_response_payload_validation_manifest(payload) == []


def test_response_payload_validator_accepts_formal_supported_route_revision_action() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_payload_validate_route_revision_action"
    )
    planner_dir = root / "llm_route_planner"
    out_dir = root / "out"
    response_json = root / "response_payload.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    staged = export_formalization_gap_planner_llm_route_planner(
        _write_input_with_rank_bridge_candidate(root),
        planner_dir,
        provider_name="prompt_only",
    )
    request = staged["request_packets"][0]
    response = _llm_response_payload()
    response_json.write_text(
        json.dumps(
            {
                "request_id": request["request_id"],
                "route_id": request["route_id"],
                "response_payload": response,
                "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    payload = validate_formalization_gap_planner_llm_route_planner_response_payloads(
        response_json,
        out_dir,
        request_context_json=planner_dir,
    )

    assert payload["all_ok"]
    assert payload["n_valid_payloads"] == 1
    row = payload["rows"][0]
    assert row["n_schema_errors"] == 0
    assert row["n_request_context_errors"] == 0


def test_response_payload_validator_rejects_incomplete_primitive_matrix_accounting() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_payload_validate_primitive_matrix"
    )
    planner_dir = root / "llm_route_planner"
    out_dir = root / "out"
    response_json = root / "response_payload.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    staged = export_formalization_gap_planner_llm_route_planner(
        _write_input(root),
        planner_dir,
        provider_name="prompt_only",
    )
    request = staged["request_packets"][0]
    response_json.write_text(
        json.dumps(
            {
                "request_id": request["request_id"],
                "route_id": request["route_id"],
                "response_payload": _drop_source_snippets(_llm_response_payload()),
                "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    payload = validate_formalization_gap_planner_llm_route_planner_response_payloads(
        response_json,
        out_dir,
        request_context_json=planner_dir,
    )

    assert payload["all_ok"] is False
    assert payload["n_payloads"] == 1
    assert payload["n_invalid_payloads"] == 1
    assert payload["n_request_bound_payloads"] == 1
    row = payload["rows"][0]
    assert row["request_context_validation_mode"] == "request_bound"
    assert row["n_schema_errors"] == 0
    assert row["n_request_context_errors"] == 1
    assert any(
        "primitive_evidence_matrix source-backed primitives require response source_snippets"
        in error
        and "rank_uniformity" in error
        for error in row["errors"]
    )
    assert (
        validate_llm_route_planner_response_payload_validation_manifest(
            payload,
            payload["response_payload_validation_manifest_schema"],
        )
        == []
    )


def test_llm_route_planner_response_payload_validator_rejects_failed_context_source_ref_fallback() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_payload_validate_rejected_source_fallback"
    )
    planner_dir = root / "llm_route_planner"
    out_dir = root / "out"
    response_json = root / "response_payload.json"
    request_context_json = root / "request_context.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    staged = export_formalization_gap_planner_llm_route_planner(
        _write_input(root),
        planner_dir,
        provider_name="prompt_only",
    )
    request = deepcopy(staged["request_packets"][0])
    rejected_source_ref = "paper:rejected-resource#rank-uniformity"
    context = request["context_packet"]
    context.pop("available_source_refs", None)
    context.pop("available_source_snippets", None)
    context.pop("context_packet_inventory", None)
    context.pop("route_planning_brief", None)
    context["resource_response_ledger_rows"] = [
        {
            "resource_response_ledger_id": "resource-response:rejected-rank-route",
            "resource_request_id": "resource-request:rejected-rank-route",
            "route_id": request["route_id"],
            "resource_id": "paperclip_mcp",
            "response_present": True,
            "response_contract_ok": False,
            "response_contract_minimum_met": False,
            "ok": False,
            "acceptance_status": "REJECTED_MISSING_RESPONSE_CONTRACT_FIELDS",
            "source_refs": [rejected_source_ref],
            "response_payload": {
                "source_refs": [rejected_source_ref],
                "source_snippets": [
                    {
                        "source_ref": rejected_source_ref,
                        "claim": "Rejected Paperclip evidence should not ground the route.",
                        "excerpt": (
                            "This rejected resource response is retained for audit "
                            "but is not admissible route evidence."
                        ),
                    }
                ],
            },
        }
    ]
    assert rejected_source_ref in json.dumps(context["resource_response_ledger_rows"])
    request_context_json.write_text(json.dumps(request, indent=2), encoding="utf-8")

    response = _replace_source_ref(
        _drop_source_snippets(_llm_response_payload()),
        "conformal_prediction_textbook",
        rejected_source_ref,
    )
    response_json.write_text(
        json.dumps(
            {
                "request_id": request["request_id"],
                "route_id": request["route_id"],
                "response_payload": response,
                "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    payload = validate_formalization_gap_planner_llm_route_planner_response_payloads(
        response_json,
        out_dir,
        request_context_json=request_context_json,
    )

    assert not payload["all_ok"]
    assert payload["n_request_bound_payloads"] == 1
    assert payload["n_invalid_payloads"] == 1
    row = payload["rows"][0]
    assert row["request_context_validation_mode"] == "request_bound"
    assert row["n_schema_errors"] == 0
    assert row["n_request_context_errors"] == 1
    assert any(
        "response source_refs must be drawn from request/context evidence" in error
        and rejected_source_ref in error
        for error in row["errors"]
    )


def test_llm_route_planner_response_payload_validator_counts_target_prover_mismatch() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_payload_validate_target_mismatch"
    )
    planner_dir = root / "llm_route_planner"
    out_dir = root / "out"
    response_json = root / "response_payload.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    input_payload = json.loads(input_json.read_text(encoding="utf-8"))
    input_payload["target_prover_family"] = "rocq"
    input_payload["routes"][0]["target_prover_family"] = "rocq"
    input_json.write_text(json.dumps(input_payload, indent=2), encoding="utf-8")
    staged = export_formalization_gap_planner_llm_route_planner(
        input_json,
        planner_dir,
        provider_name="prompt_only",
    )
    request = staged["request_packets"][0]
    response = _llm_response_payload()
    response["target_prover_family"] = "lean4"
    response_json.write_text(
        json.dumps(
            {
                "request_id": request["request_id"],
                "route_id": request["route_id"],
                "response_payload": response,
                "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    payload = validate_formalization_gap_planner_llm_route_planner_response_payloads(
        response_json,
        out_dir,
        request_context_json=planner_dir,
    )

    assert not payload["all_ok"]
    assert payload["n_payloads_with_declared_target_prover_family"] == 1
    assert (
        payload["n_request_bound_payloads_with_target_prover_family_mismatch"]
        == 1
    )
    assert payload["by_payload_target_prover_family"] == {"lean4": 1}
    assert payload["by_request_context_target_prover_family"] == {"rocq": 1}
    row = payload["rows"][0]
    assert row["request_context_validation_mode"] == "request_bound"
    assert row["payload_target_prover_family"] == "lean4"
    assert row["payload_target_prover_key"] == "lean4"
    assert row["request_context_target_prover_family"] == "rocq"
    assert row["request_context_target_prover_key"] == "rocq"
    assert row["target_prover_family_consistent"] is False
    assert any(
        "does not match request target_prover_family rocq" in error
        for error in row["errors"]
    )


def test_llm_route_planner_response_payload_validator_request_context_rejects_cost_hint_underpricing() -> None:
    root = Path("runs/test_formalization_gap_planner_llm_payload_validate_cost_hint")
    planner_dir = root / "llm_route_planner"
    out_dir = root / "out"
    response_json = root / "response_payload.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    staged = export_formalization_gap_planner_llm_route_planner(
        _write_input(root),
        planner_dir,
        provider_name="prompt_only",
    )
    request = staged["request_packets"][0]
    response_json.write_text(
        json.dumps(
            {
                "request_id": request["request_id"],
                "route_id": request["route_id"],
                "response_payload": _make_rank_uniformity_near_exists_response(),
                "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    payload = validate_formalization_gap_planner_llm_route_planner_response_payloads(
        response_json,
        out_dir,
        request_context_json=planner_dir,
    )

    assert not payload["all_ok"]
    assert payload["n_schema_errors"] == 0
    assert payload["n_request_context_errors"] >= 1
    row = payload["rows"][0]
    assert row["request_context_validation_mode"] == "request_bound"
    assert row["n_schema_errors"] == 0
    assert row["n_request_context_errors"] >= 1
    assert any(
        "underprices request minimal_delta_cost_hints" in error
        and "minimum_base_cost=4" in error
        for error in row["errors"]
    )
    assert any(
        "minimum_route_base_cost=4" in error for error in row["errors"]
    )


def test_llm_route_planner_response_payload_validator_request_context_rejects_silent_cost_hint_primitive_omission() -> None:
    root = Path("runs/test_formalization_gap_planner_llm_payload_validate_cost_hint_omission")
    planner_dir = root / "llm_route_planner"
    out_dir = root / "out"
    response_json = root / "response_payload.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    staged = export_formalization_gap_planner_llm_route_planner(
        _write_input(root),
        planner_dir,
        provider_name="prompt_only",
    )
    request = staged["request_packets"][0]
    response_json.write_text(
        json.dumps(
            {
                "request_id": request["request_id"],
                "route_id": request["route_id"],
                "response_payload": _make_rank_uniformity_omitted_response(),
                "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    payload = validate_formalization_gap_planner_llm_route_planner_response_payloads(
        response_json,
        out_dir,
        request_context_json=planner_dir,
    )

    assert not payload["all_ok"]
    row = payload["rows"][0]
    assert row["request_context_validation_mode"] == "request_bound"
    assert row["n_schema_errors"] == 1
    assert row["n_request_context_errors"] >= 1
    assert row["n_formal_attempt_queue_errors"] == 1
    assert any(
        "formal_attempt_queue[1].formal_node_id references unknown "
        "formal_realization_dag_nodes node: formal:rank_uniformity_bridge"
        in error
        for error in row["errors"]
    )
    assert any(
        "baseline route option" in error and "rank_uniformity" in error
        for error in row["errors"]
    )
    assert any(
        "context_packet.route_option_selection_brief candidate route option "
        "must be represented" in error
        and "route_option:current_route_min_delta_baseline" in error
        and "rank_uniformity" in error
        for error in row["errors"]
    )


def test_llm_route_planner_response_payload_validator_request_context_rejects_theorem_drift() -> None:
    root = Path("runs/test_formalization_gap_planner_llm_payload_validate_theorem_drift")
    planner_dir = root / "llm_route_planner"
    out_dir = root / "out"
    response_json = root / "response_payload.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    staged = export_formalization_gap_planner_llm_route_planner(
        _write_input(root),
        planner_dir,
        provider_name="prompt_only",
    )
    request = staged["request_packets"][0]
    response = _llm_response_payload()
    standalone_route = response["standalone_route"]
    assert isinstance(standalone_route, dict)
    standalone_route["theorem_statement"] = (
        "A Gaussian central limit theorem follows from Lindeberg conditions."
    )
    response_json.write_text(
        json.dumps(
            {
                "request_id": request["request_id"],
                "route_id": request["route_id"],
                "response_payload": response,
                "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    payload = validate_formalization_gap_planner_llm_route_planner_response_payloads(
        response_json,
        out_dir,
        request_context_json=planner_dir,
    )

    assert not payload["all_ok"]
    assert payload["n_schema_errors"] == 0
    assert payload["n_request_context_errors"] >= 1
    row = payload["rows"][0]
    assert row["request_context_validation_mode"] == "request_bound"
    assert row["n_schema_errors"] == 0
    assert row["n_request_context_errors"] >= 1
    assert any(
        "standalone_route.theorem_statement appears to target a different theorem"
        in error
        for error in row["errors"]
    )


def test_llm_route_planner_response_payload_validator_cli() -> None:
    root = Path("runs/test_formalization_gap_planner_llm_payload_validate_cli")
    out_dir = root / "out"
    response_json = root / "response_payload.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    response_json.write_text(
        json.dumps({"responses": [_llm_response_payload()]}, indent=2),
        encoding="utf-8",
    )

    code = main(
        [
            "formalization-gap-planner-llm-route-planner-response-payload-validate",
            "--input",
            str(response_json),
            "--out",
            str(out_dir),
        ]
    )

    assert code == 0
    manifest = json.loads(
        (
            out_dir
            / "formalization_gap_planner_llm_route_planner_response_payload_validation_manifest.json"
        ).read_text(encoding="utf-8")
    )
    assert manifest["all_ok"]
    assert manifest["n_valid_payloads"] == 1


def test_llm_route_planner_response_payload_validator_cli_request_context() -> None:
    root = Path("runs/test_formalization_gap_planner_llm_payload_validate_cli_request_bound")
    planner_dir = root / "llm_route_planner"
    out_dir = root / "out"
    response_json = root / "response_payload.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    staged = export_formalization_gap_planner_llm_route_planner(
        _write_input(root),
        planner_dir,
        provider_name="prompt_only",
    )
    request = staged["request_packets"][0]
    response_json.write_text(
        json.dumps(
            {
                "request_id": request["request_id"],
                "route_id": request["route_id"],
                "response_payload": _llm_response_payload(),
                "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    code = main(
        [
            "formalization-gap-planner-llm-route-planner-response-payload-validate",
            "--input",
            str(response_json),
            "--request-context",
            str(planner_dir),
            "--out",
            str(out_dir),
        ]
    )

    assert code == 0
    manifest = json.loads(
        (
            out_dir
            / "formalization_gap_planner_llm_route_planner_response_payload_validation_manifest.json"
        ).read_text(encoding="utf-8")
    )
    assert manifest["all_ok"]
    assert manifest["n_request_bound_payloads"] == 1
    assert manifest["n_request_bound_payloads_with_context_packet_inventory"] == 1
    assert (
        manifest["rows"][0]["request_context_inventory_present"] is True
    )
    assert manifest["rows"][0]["request_context_validation_mode"] == "request_bound"


def test_llm_route_planner_blocks_replay_ready_on_pending_formal_attempt_queue() -> None:
    root = Path("runs/test_formalization_gap_planner_llm_route_planner_ready")
    out_dir = root / "llm_route_planner"
    response_json = root / "response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    response = _llm_response_payload()
    response["search_requests"] = []
    response["planner_next_actions"] = []
    response["uncertainty_flags"] = []
    response["semantic_alignment_risks"] = []
    response_json.write_text(json.dumps(response, indent=2), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        provider_name="static",
        static_response_json=response_json,
    )

    assert payload["all_ok"]
    assert (
        payload[
            "n_standalone_seed_routes_with_llm_route_option_selected_route_option"
        ]
        == 1
    )
    assert payload["n_route_adoption_ready"] == 0
    assert payload["n_route_adoption_pending_refinement"] == 1
    assert payload["n_route_adoption_pending_formal_attempt_queue_blockers"] == 1
    assert payload["standalone_replay_gate_ok"] is False
    assert payload["n_standalone_replay_route_candidates"] == 1
    assert payload["n_standalone_replay_adoptable_route_candidates"] == 0
    assert payload["n_standalone_replay_blocked_route_candidates"] == 1
    assert payload["standalone_replay_gate_blockers"] == [
        ROUTE_ADOPTION_BLOCKER_FORMAL_ATTEMPT_QUEUE
    ]
    assert payload["standalone_replay_gate"]["gate_status"] == (
        "PENDING_REFINEMENT_BEFORE_ROUTE_ADOPTION"
    )
    assert (
        payload["standalone_replay_gate"][
            "selected_route_adoptable_for_standalone_replay"
        ]
        is False
    )
    assert payload["by_route_adoption_status"] == {
        "PENDING_REFINEMENT_BEFORE_ROUTE_ADOPTION": 1
    }
    row = payload["rows"][0]
    assert row["acceptance_status"] == "ACCEPTED_WITH_FORMAL_ATTEMPT_QUEUE"
    assert row["route_adoption_status"] == (
        "PENDING_REFINEMENT_BEFORE_ROUTE_ADOPTION"
    )
    assert row["route_adoption_blockers"] == (
        ROUTE_ADOPTION_BLOCKER_FORMAL_ATTEMPT_QUEUE,
    )
    seed_route = payload["standalone_seed"]["routes"][0]
    assert (
        seed_route["llm_route_planner_route_adoption_status"]
        == "PENDING_REFINEMENT_BEFORE_ROUTE_ADOPTION"
    )
    assert seed_route["replan_metadata"][
        "llm_route_planner_route_adoption_blockers"
    ] == [ROUTE_ADOPTION_BLOCKER_FORMAL_ATTEMPT_QUEUE]
    selection = payload["standalone_seed"][
        "llm_route_planner_seed_route_selection"
    ]
    assert selection["selected_route_adoptable_for_standalone_replay"] is False
    assert (
        selection["selected_minimal_delta_selected_route_option_id"]
        == "route_option:reuse_exchangeability_bridge_rank"
    )
    assert selection["n_adoptable_route_candidates"] == 0
    assert selection["n_selected_route_candidates_not_adoptable"] == 1
    assert (
        selection["selection_rows"][0]["adoptable_for_standalone_replay"]
        is False
    )
    assert (
        seed_route["llm_route_planner_seed_adoptable_for_standalone_replay"]
        is False
    )
    assert (
        seed_route["llm_route_planner_seed_minimal_delta_selected_route_option_id"]
        == "route_option:reuse_exchangeability_bridge_rank"
    )
    assert (
        seed_route[
            "llm_route_planner_route_option_selected_route_option_id"
        ]
        == "route_option:current_route_min_delta_baseline"
    )
    assert (
        seed_route["replan_metadata"][
            "llm_route_planner_seed_minimal_delta_selected_route_option_id"
        ]
        == "route_option:reuse_exchangeability_bridge_rank"
    )
    assert (
        seed_route["replan_metadata"][
            "llm_route_planner_route_option_selected_route_option_id"
        ]
        == "route_option:current_route_min_delta_baseline"
    )

    plan_dir = root / "standalone_plan_from_ready_llm_seed"
    plan_payload = export_formalization_gap_planner_standalone_plan(
        out_dir / "formalization_gap_planner_llm_route_planner_standalone_seed.json",
        plan_dir,
    )
    assert plan_payload["all_ok"]
    assert plan_payload[
        "n_standalone_input_traces_ready_for_route_adoption"
    ] == 0
    assert plan_payload[
        "n_standalone_input_traces_pending_refinement_before_route_adoption"
    ] == 1
    assert (
        plan_payload[
            "n_standalone_input_traces_llm_seed_adoptable_for_standalone_replay"
        ]
        == 0
    )
    assert (
        plan_payload[
            "n_standalone_input_traces_llm_seed_selected_not_adoptable"
        ]
        == 1
    )
    assert (
        plan_payload[
            "n_standalone_input_traces_with_llm_route_option_selected_route_option"
        ]
        == 1
    )
    trace = plan_payload["rows"][0]["standalone_input_trace"]
    assert trace["llm_route_planner_route_adoption_status"] == (
        "PENDING_REFINEMENT_BEFORE_ROUTE_ADOPTION"
    )
    assert trace["llm_route_planner_route_adoption_blockers"] == [
        ROUTE_ADOPTION_BLOCKER_FORMAL_ATTEMPT_QUEUE
    ]
    assert trace["llm_route_planner_seed_adoptable_for_standalone_replay"] is False
    assert (
        trace["llm_route_planner_seed_minimal_delta_selected_route_option_id"]
        == "route_option:reuse_exchangeability_bridge_rank"
    )
    assert (
        trace["llm_route_planner_route_option_selected_route_option_id"]
        == "route_option:current_route_min_delta_baseline"
    )


def test_llm_route_planner_rejects_selected_primitive_without_alignment_edge() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_rejects_selected_alignment_gap"
    )
    out_dir = root / "llm_route_planner"
    response_json = root / "response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    response = _llm_response_payload()
    response["search_requests"] = []
    response["planner_next_actions"] = []
    response["uncertainty_flags"] = []
    response["semantic_alignment_risks"] = []
    response["route_alignment_edges"] = [
        edge
        for edge in response["route_alignment_edges"]
        if edge.get("formal_node_id") != "formal:exchangeability"
    ]
    response_json.write_text(json.dumps(response, indent=2), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        provider_name="static",
        static_response_json=response_json,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    assert row["response_contract_ok"] is False
    assert any(
        "minimal_delta_plan.selected_primitives missing route_alignment_edges: "
        "exchangeability" in error
        for error in row["errors"]
    )


def test_llm_route_planner_rejects_selected_primitive_with_unresolved_alignment_edge() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_rejects_unresolved_selected_alignment"
    )
    out_dir = root / "llm_route_planner"
    response_json = root / "response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    response = _llm_response_payload()
    response["search_requests"] = []
    response["planner_next_actions"] = []
    response["uncertainty_flags"] = []
    response["semantic_alignment_risks"] = []
    for edge in response["route_alignment_edges"]:
        if edge.get("formal_node_id") == "formal:exchangeability":
            edge["alignment_status"] = "missing"
            edge["alignment_rationale"] = (
                "The model could not resolve the selected exchangeability "
                "alignment to a formal declaration."
            )
    response_json.write_text(json.dumps(response, indent=2), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        provider_name="static",
        static_response_json=response_json,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    assert row["response_contract_ok"] is False
    assert any(
        "minimal_delta_plan.selected_primitives have unresolved route_alignment_edges: "
        "exchangeability" in error
        for error in row["errors"]
    )
    assert "exchangeability" not in row["realization_coverage_witness"][
        "aligned_primitives"
    ]


def test_llm_route_planner_rejects_free_text_alignment_status() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_rejects_free_text_alignment_status"
    )
    out_dir = root / "llm_route_planner"
    response_json = root / "response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    response = _llm_response_payload()
    response["search_requests"] = []
    response["planner_next_actions"] = []
    response["uncertainty_flags"] = []
    response["semantic_alignment_risks"] = []
    for edge in response["route_alignment_edges"]:
        if edge.get("formal_node_id") == "formal:exchangeability":
            edge["alignment_status"] = "maybe_exact"
            edge["alignment_rationale"] = (
                "This free-text status should not be accepted as a resolved "
                "library alignment."
            )
    response_json.write_text(json.dumps(response, indent=2), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        provider_name="static",
        static_response_json=response_json,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    assert row["response_contract_ok"] is False
    assert any(
        "route_alignment_edges[1].alignment_status unsupported: maybe_exact"
        in error
        for error in row["errors"]
    )
    assert any(
        "minimal_delta_plan.selected_primitives have unresolved route_alignment_edges: "
        "exchangeability" in error
        for error in row["errors"]
    )


def test_llm_route_planner_seed_ranks_accepted_routes_by_minimal_delta_cost() -> None:
    root = Path("runs/test_formalization_gap_planner_llm_route_planner_seed_route_selection")
    out_dir = root / "llm_route_planner"
    response_json = root / "responses.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    input_payload = json.loads(input_json.read_text(encoding="utf-8"))
    alternative_route = deepcopy(input_payload["routes"][0])
    alternative_route["route_id"] = "rank_route_alt"
    alternative_route["display_name"] = "distribution_free_rank_bound_alt"
    input_payload["routes"].append(alternative_route)
    input_json.write_text(json.dumps(input_payload, indent=2), encoding="utf-8")

    high_cost = _llm_response_payload()
    high_cost["search_requests"] = []
    high_cost["planner_next_actions"] = []
    high_cost["uncertainty_flags"] = []
    high_cost["semantic_alignment_risks"] = []
    high_cost["standalone_route"]["route_id"] = "rank_route_high_cost_seed"
    high_cost["standalone_route"]["display_name"] = "rank route high cost"
    high_cost_delta = high_cost["minimal_delta_plan"]
    assert isinstance(high_cost_delta, dict)
    high_cost_delta["route_cost"] = 8
    high_rank_cost = high_cost_delta["primitive_costs"][1]
    assert isinstance(high_rank_cost, dict)
    high_rank_cost["proof_difficulty_cost"] = 4
    high_rank_cost["total_cost"] = 8
    high_rank_cost["cost_rationale"] = (
        "The bridge requires an extra proof-difficulty allowance."
    )
    high_cost_graph = high_cost_delta["and_or_cost_graph"]
    assert isinstance(high_cost_graph, dict)
    for option in high_cost_graph["route_options"]:
        assert isinstance(option, dict)
        option["route_cost"] = 8 if option["selected"] else 9
        option_costs = option.get("primitive_costs")
        if isinstance(option_costs, list):
            for cost_row in option_costs:
                if (
                    isinstance(cost_row, dict)
                    and cost_row.get("primitive") == "rank_uniformity"
                ):
                    cost_row["proof_difficulty_cost"] = 2
                    cost_row["total_cost"] = 9
                    cost_row["cost_rationale"] = (
                        "The source-port alternative carries an extra "
                        "proof-difficulty allowance in this high-cost fixture."
                    )

    low_cost = _llm_response_payload()
    low_cost["search_requests"] = []
    low_cost["planner_next_actions"] = []
    low_cost["uncertainty_flags"] = []
    low_cost["semantic_alignment_risks"] = []
    low_cost["standalone_route"]["route_id"] = "rank_route_low_cost_seed"
    low_cost["standalone_route"]["display_name"] = "rank route low cost"

    response_json.write_text(
        json.dumps(
            [
                {
                    "route_id": "rank_route",
                    "response_payload": high_cost,
                    "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
                },
                {
                    "route_id": "rank_route_alt",
                    "response_payload": low_cost,
                    "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
                },
            ],
            indent=2,
        ),
        encoding="utf-8",
    )

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        provider_name="static",
        static_response_json=response_json,
    )

    assert payload["all_ok"]
    selection = payload["standalone_seed"][
        "llm_route_planner_seed_route_selection"
    ]
    assert validate_llm_route_planner_seed_route_selection_payload(selection) == []
    assert validate_standalone_input_payload(payload["standalone_seed"]) == []
    assert selection["selection_status"] == "accepted_llm_routes_ranked"
    assert selection["selected_route_id"] == "rank_route_alt"
    assert selection["selected_seed_route_id"] == "rank_route_low_cost_seed"
    assert selection["selected_route_adoptable_for_standalone_replay"] is False
    assert selection["n_adoptable_route_candidates"] == 0
    assert selection["n_selected_route_candidates_not_adoptable"] == 1
    assert selection["selected_minimal_delta_route_cost"] == 4.0
    assert (
        selection["selected_minimal_delta_selected_route_option_id"]
        == "route_option:reuse_exchangeability_bridge_rank"
    )
    assert [row["route_id"] for row in selection["selection_rows"]] == [
        "rank_route_alt",
        "rank_route",
    ]
    seed_routes = payload["standalone_seed"]["routes"]
    assert [route["route_id"] for route in seed_routes] == [
        "rank_route_low_cost_seed",
        "rank_route_high_cost_seed",
    ]
    assert seed_routes[0]["llm_route_planner_seed_selected"] is True
    assert (
        seed_routes[0]["llm_route_planner_seed_adoptable_for_standalone_replay"]
        is False
    )
    assert seed_routes[0]["llm_route_planner_seed_selection_rank"] == 1
    assert seed_routes[0]["replan_metadata"][
        "llm_route_planner_seed_minimal_delta_route_cost"
    ] == 4.0
    assert (
        seed_routes[0][
            "llm_route_planner_seed_minimal_delta_selected_route_option_id"
        ]
        == "route_option:reuse_exchangeability_bridge_rank"
    )
    assert (
        seed_routes[0]["replan_metadata"][
            "llm_route_planner_seed_minimal_delta_selected_route_option_id"
        ]
        == "route_option:reuse_exchangeability_bridge_rank"
    )
    assert seed_routes[1]["llm_route_planner_seed_selected"] is False
    assert (
        seed_routes[1]["llm_route_planner_seed_adoptable_for_standalone_replay"]
        is False
    )
    assert seed_routes[1]["llm_route_planner_seed_selection_rank"] == 2

    plan_payload = export_formalization_gap_planner_standalone_plan(
        out_dir / "formalization_gap_planner_llm_route_planner_standalone_seed.json",
        root / "standalone_plan_from_ranked_llm_seed",
    )
    assert plan_payload["all_ok"]
    assert plan_payload["n_standalone_input_traces_with_llm_seed_selection"] == 2
    assert plan_payload["n_standalone_input_traces_llm_seed_selected"] == 1
    assert (
        plan_payload[
            "n_standalone_input_traces_llm_seed_adoptable_for_standalone_replay"
        ]
        == 0
    )
    assert (
        plan_payload[
            "n_standalone_input_traces_llm_seed_selected_not_adoptable"
        ]
        == 1
    )
    assert plan_payload[
        "standalone_input_trace_by_llm_seed_selection_rank"
    ] == {"1": 1, "2": 1}
    traces = [
        row["standalone_input_trace"]
        for row in plan_payload["rows"]
    ]
    assert [trace["llm_route_planner_seed_selected"] for trace in traces] == [
        True,
        False,
    ]
    assert [
        trace["llm_route_planner_seed_adoptable_for_standalone_replay"]
        for trace in traces
    ] == [False, False]
    assert [
        trace["llm_route_planner_seed_minimal_delta_route_cost"]
        for trace in traces
    ] == [4.0, 8.0]
    assert [
        trace["llm_route_planner_seed_minimal_delta_selected_route_option_id"]
        for trace in traces
    ] == [
        "route_option:reuse_exchangeability_bridge_rank",
        "route_option:reuse_exchangeability_bridge_rank",
    ]

    corrupted_seed = deepcopy(payload["standalone_seed"])
    corrupted_selection = corrupted_seed["llm_route_planner_seed_route_selection"]
    corrupted_selection["n_route_candidates"] = 99
    corrupted_selection["selection_rows"][0]["selected"] = False
    selection_errors = validate_llm_route_planner_seed_route_selection_payload(
        corrupted_selection
    )
    assert "n_route_candidates must match selection_rows length" in selection_errors
    assert (
        "selection_rows must mark exactly one selected route, found 0"
        in selection_errors
    )
    option_corrupted_selection = deepcopy(selection)
    option_corrupted_selection[
        "selected_minimal_delta_selected_route_option_id"
    ] = "route_option:wrong"
    option_selection_errors = validate_llm_route_planner_seed_route_selection_payload(
        option_corrupted_selection
    )
    assert (
        "selected_minimal_delta_selected_route_option_id must match selected selection_row"
        in option_selection_errors
    )
    standalone_errors = validate_standalone_input_payload(corrupted_seed)
    assert any(
        error.startswith("llm_route_planner_seed_route_selection.")
        for error in standalone_errors
    )


def test_llm_route_planner_blocks_route_adoption_on_formal_gap_boundary() -> None:
    root = Path("runs/test_formalization_gap_planner_llm_route_planner_boundary_blocker")
    out_dir = root / "llm_route_planner"
    response_json = root / "response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    response = _llm_response_payload()
    response["search_requests"] = []
    response["planner_next_actions"] = []
    response["uncertainty_flags"] = []
    response["semantic_alignment_risks"] = []
    response["lean_realization_dag_nodes"][1]["formal_gap_boundary"] = (
        "Rank uniformity bridge remains a formal library boundary requiring "
        "a new Lean lemma before kernel replay."
    )
    response_json.write_text(json.dumps(response, indent=2), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        provider_name="static",
        static_response_json=response_json,
    )

    assert payload["all_ok"]
    assert payload["n_route_adoption_ready"] == 0
    assert payload["n_route_adoption_pending_refinement"] == 1
    assert payload["n_route_adoption_pending_formal_gap_boundary_blockers"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "ACCEPTED_WITH_FORMAL_ATTEMPT_QUEUE"
    assert row["route_adoption_status"] == (
        "PENDING_REFINEMENT_BEFORE_ROUTE_ADOPTION"
    )
    assert row["route_adoption_blockers"] == (
        "formal_gap_boundaries_require_resolution",
    )
    seed_route = payload["standalone_seed"]["routes"][0]
    assert seed_route["replan_metadata"][
        "llm_route_planner_route_adoption_blockers"
    ] == ["formal_gap_boundaries_require_resolution"]


def test_llm_route_planner_blocks_route_adoption_on_unresolved_source_grounding() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_source_grounding_blocker"
    )
    out_dir = root / "llm_route_planner"
    source_grounding_dir = root / "source_grounding"
    response_json = root / "response.json"
    shutil.rmtree(root, ignore_errors=True)
    source_grounding_dir.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    (
        source_grounding_dir
        / "formalization_gap_planner_source_grounding_audit_manifest.json"
    ).write_text(
        json.dumps(
            {
                "component_name": "formalization_gap_planner_source_grounding_audit",
                "rows": [
                    {
                        "source_grounding_id": "source-grounding:rank-residual",
                        "route_id": "rank_route",
                        "display_name": "distribution_free_rank_bound",
                        "node_source": "refinement_evidence_prover_feedback",
                        "node_id": "residual:rank_uniformity:measurability",
                        "node_kind": "prover_residual_goal",
                        "node_label": "Rank bridge residual measurability condition",
                        "source_refs": [],
                        "source_snippets": [],
                        "residual_goals": [
                            "rank_uniformity: missing measurability side condition"
                        ],
                        "residual_primitives": ["rank_uniformity"],
                        "residual_evidence_ids": ["evidence:rank-lsp"],
                        "grounding_status": "unaccounted",
                        "required_next_action": "route_repair_or_source_search",
                        "ok": False,
                        "errors": ["residual goal has no source-backed route repair"],
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    response = _llm_response_payload()
    response["search_requests"] = []
    response["planner_next_actions"] = []
    response["uncertainty_flags"] = []
    response["semantic_alignment_risks"] = []
    response["residual_interpretations"] = [
        {
            "residual_goal": "rank_uniformity: missing measurability side condition",
            "interpretation": (
                "The attempted rank-uniformity bridge exposed a side condition "
                "that is not yet source-backed."
            ),
            "route_repair": (
                "Keep the measurability side condition as a route-repair "
                "obligation until source evidence or a formal boundary is added."
            ),
            "target_primitives": ["rank_uniformity"],
            "source_refs": ["conformal_prediction_textbook"],
        }
    ]
    silent_response_json = root / "silent_response.json"
    silent_response = deepcopy(response)
    silent_response_json.write_text(
        json.dumps(silent_response, indent=2),
        encoding="utf-8",
    )
    response["search_requests"] = [
        {
            "request_kind": "literature",
            "query": (
                "source-backed measurability side condition for finite rank "
                "uniformity under exchangeability"
            ),
            "reason": (
                "route_adoption_preconditions require a source-grounding "
                "follow-up before adopting the repaired route"
            ),
            "target_primitives": ["rank_uniformity"],
        }
    ]
    response_json.write_text(json.dumps(response, indent=2), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        provider_name="static",
        static_response_json=response_json,
        formalization_gap_planner_source_grounding_audit_dir=source_grounding_dir,
    )

    assert payload["all_ok"]
    assert payload["n_requests_with_source_grounding_rows"] == 1
    assert payload["n_request_source_grounding_rows"] == 1
    assert payload["n_requests_with_source_grounding_obligation_inventory"] == 1
    assert (
        payload["n_requests_with_pending_source_grounding_obligation_inventory"]
        == 1
    )
    assert payload["n_request_source_grounding_unresolved_rows"] == 1
    assert payload["n_request_residual_source_grounding_unresolved_rows"] == 1
    assert payload["n_requests_with_route_adoption_preconditions"] == 1
    assert payload["n_request_route_adoption_precondition_known_blockers"] >= 2
    assert (
        payload["n_request_route_adoption_precondition_required_response_fields"]
        >= 3
    )
    assert payload["n_route_adoption_ready"] == 0
    assert payload["n_route_adoption_pending_refinement"] == 1
    assert payload["n_route_adoption_pending_residual_repair_blockers"] == 1
    assert payload["n_route_adoption_pending_source_grounding_blockers"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "ACCEPTED_WITH_SEARCH_REQUESTS"
    assert row["route_adoption_status"] == (
        "PENDING_REFINEMENT_BEFORE_ROUTE_ADOPTION"
    )
    assert set(row["route_adoption_blockers"]) >= {
        "search_requests_pending_evidence",
        "residual_interpretations_require_route_replay",
        ROUTE_ADOPTION_BLOCKER_SOURCE_GROUNDING,
    }
    request = payload["request_packets"][0]
    context = request["context_packet"]
    source_row = context["source_grounding_rows"][0]
    assert source_row["grounding_status"] == "unaccounted"
    assert source_row["node_source"] == "refinement_evidence_prover_feedback"
    obligations = context["source_grounding_obligations"]
    assert obligations["pending"] is True
    assert obligations["n_unresolved_rows"] == 1
    assert obligations["n_residual_unresolved_rows"] == 1
    preconditions = context["route_adoption_preconditions"]
    assert preconditions["precondition_kind"] == (
        "formalization_gap_planner_llm_route_planner_route_adoption_preconditions"
    )
    assert preconditions["blocked_before_response"] is True
    assert set(preconditions["known_pre_response_blockers"]) >= {
        "residual_interpretations_require_route_replay",
        ROUTE_ADOPTION_BLOCKER_SOURCE_GROUNDING,
    }
    assert set(preconditions["response_required_fields"]) >= {
        "residual_interpretations",
        "search_requests",
        "planner_next_actions",
    }
    assert preconditions["target_primitives"] == ["rank_uniformity"]
    route_brief = context["route_planning_brief"]
    precondition_focus = next(
        focus
        for focus in route_brief["planner_focus"]
        if focus["focus_id"] == "resolve_route_adoption_preconditions"
    )
    assert precondition_focus["target_primitives"] == ["rank_uniformity"]
    precondition_gap = next(
        gap
        for gap in route_brief["evidence_gaps"]
        if gap["gap_id"] == "known_route_adoption_preconditions"
    )
    assert precondition_gap["target_primitives"] == ["rank_uniformity"]
    assert (
        row["route_adoption_preconditions"]
        == context["route_adoption_preconditions"]
    )
    inventory = context["context_packet_inventory"]
    assert inventory["source_grounding_obligation_pending"] is True
    assert inventory["residual_source_grounding_unresolved_count"] == 1
    assert inventory["route_adoption_precondition_pending"] is True
    assert inventory["route_adoption_precondition_known_blocker_count"] == (
        preconditions["n_known_pre_response_blockers"]
    )
    assert "route_adoption_preconditions" in request["prompt_messages"]["user"]
    assert ROUTE_ADOPTION_BLOCKER_SOURCE_GROUNDING in payload[
        "route_adoption_blocker_values"
    ]
    seed_route = payload["standalone_seed"]["routes"][0]
    assert seed_route["llm_route_planner_route_adoption_preconditions"] == (
        preconditions
    )
    assert seed_route["replan_metadata"][
        "llm_route_planner_route_adoption_preconditions"
    ] == preconditions
    assert set(
        seed_route["replan_metadata"]["llm_route_planner_route_adoption_blockers"]
    ) >= {
        "search_requests_pending_evidence",
        "residual_interpretations_require_route_replay",
        ROUTE_ADOPTION_BLOCKER_SOURCE_GROUNDING,
    }

    silent_payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        root / "llm_route_planner_silent_precondition_response",
        provider_name="static",
        static_response_json=silent_response_json,
        formalization_gap_planner_source_grounding_audit_dir=source_grounding_dir,
    )
    assert not silent_payload["all_ok"]
    silent_row = silent_payload["rows"][0]
    assert silent_row["response_contract_ok"] is False
    assert silent_row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    assert any(
        "route_adoption_preconditions require at least one nonempty "
        "search_requests or planner_next_actions row" in error
        for error in silent_row["errors"]
    )


def test_route_adoption_readiness_uses_current_realization_witness() -> None:
    status, blockers = _route_adoption_readiness(
        response_present=True,
        provider_failure=False,
        response_contract_ok=True,
        search_requests=(),
        planner_next_actions=(),
        uncertainty_flags=(),
        semantic_alignment_risks=(),
        residual_interpretations=(),
        feedback_summary={},
        realization_coverage_witness={"realization_coverage_complete": False},
        omitted_cost_hint_primitives=(),
        formal_gap_boundary_obligations=(),
        quality_control_obligations_pending=False,
    )

    assert status == "PENDING_REFINEMENT_BEFORE_ROUTE_ADOPTION"
    assert blockers == ("realization_coverage_incomplete",)

    status, blockers = _route_adoption_readiness(
        response_present=True,
        provider_failure=False,
        response_contract_ok=True,
        search_requests=(),
        planner_next_actions=(),
        uncertainty_flags=(),
        semantic_alignment_risks=(),
        residual_interpretations=(),
        feedback_summary={},
        realization_coverage_witness={"realization_coverage_complete": True},
        primitive_evidence_matrix_witness={
            "matrix_accounting_complete": False,
            "matrix_unaccounted_primitives": ["rank_uniformity"],
        },
        omitted_cost_hint_primitives=(),
        formal_gap_boundary_obligations=(),
        quality_control_obligations_pending=False,
    )

    assert status == "PENDING_REFINEMENT_BEFORE_ROUTE_ADOPTION"
    assert blockers == ("primitive_evidence_matrix_incomplete",)


def test_route_adoption_taxonomy_publishes_blocker_trigger_fields() -> None:
    payload = route_adoption_blocker_taxonomy_payload()
    schema = route_adoption_blocker_taxonomy_json_schema()

    assert validate_route_adoption_blocker_taxonomy_payload(payload) == ()
    trigger_fields = payload["blocker_trigger_fields"][
        ROUTE_ADOPTION_BLOCKER_REALIZATION_COVERAGE
    ]
    assert (
        "rows[].realization_coverage_witness.realization_coverage_complete"
        in trigger_fields
    )
    quality_control_trigger_fields = payload["blocker_trigger_fields"][
        "quality_control_obligations_pending"
    ]
    assert (
        "context_packet.context_packet_inventory.pending_quality_control_value_count"
        in quality_control_trigger_fields
    )
    assert not any(
        "n_pending_quality_control_values" in field
        for field in quality_control_trigger_fields
    )
    trigger_schema = schema["properties"]["blocker_trigger_fields"]
    assert trigger_schema["additionalProperties"] is False
    assert trigger_schema["properties"][
        ROUTE_ADOPTION_BLOCKER_REALIZATION_COVERAGE
    ]["const"] == trigger_fields
    assert trigger_schema["properties"][
        "quality_control_obligations_pending"
    ]["const"] == quality_control_trigger_fields

    corrupted_payload = deepcopy(payload)
    corrupted_payload["blocker_trigger_fields"][
        ROUTE_ADOPTION_BLOCKER_REALIZATION_COVERAGE
    ] = []
    assert any(
        "blocker_trigger_fields must list at least one trigger field" in error
        for error in validate_route_adoption_blocker_taxonomy_payload(
            corrupted_payload
        )
    )

    stale_payload = deepcopy(payload)
    stale_payload["blocker_trigger_fields"][
        ROUTE_ADOPTION_BLOCKER_REALIZATION_COVERAGE
    ] = ["stale.realization_coverage_flag"]
    assert any(
        "blocker_trigger_fields values must match route adoption blocker trigger constants"
        in error
        for error in validate_route_adoption_blocker_taxonomy_payload(
            stale_payload
        )
    )


def test_llm_route_planner_blocks_route_adoption_on_unmet_quality_controls() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_quality_control_adoption"
    )
    out_dir = root / "llm_route_planner_pending_quality_controls"
    discharged_dir = root / "llm_route_planner_discharged_quality_controls"
    response_json = root / "response.json"
    ledger_dir = root / "resource_response_ledger"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    input_payload = json.loads(input_json.read_text(encoding="utf-8"))
    quality_controls = {
        "target_primitives": ["rank_uniformity"],
        "resource_contract_ids": ["lean_lsp:proof_state_feedback"],
        "required_quality_signals": ["diagnostic_signature"],
        "quality_gates": ["response_schema_valid"],
        "response_validation_signals": [
            "residual_goals_or_diagnostics_present"
        ],
        "stop_conditions": ["residual interpreted or source search requested"],
    }
    input_payload["routes"][0]["quality_controls"] = quality_controls
    input_json.write_text(json.dumps(input_payload, indent=2), encoding="utf-8")
    response = _llm_response_payload()
    response["search_requests"] = []
    response["planner_next_actions"] = [
        {
            "owner": "lean_lsp_mcp",
            "action": (
                "collect proof-state feedback with diagnostic_signature before "
                "adopting the quality-controlled route"
            ),
            "query": "rank_uniformity bridge residual goals and diagnostics",
            "target_primitives": ["rank_uniformity"],
            "resource_id": "lean_lsp_mcp",
            "resource_contract_ids": ["lean_lsp:proof_state_feedback"],
            "required_quality_signals": ["diagnostic_signature"],
            "quality_gates": ["response_schema_valid"],
            "response_validation_signals": [
                "residual_goals_or_diagnostics_present"
            ],
            "stop_conditions": ["residual interpreted or source search requested"],
        }
    ]
    response["uncertainty_flags"] = []
    response["semantic_alignment_risks"] = []
    response_json.write_text(json.dumps(response, indent=2), encoding="utf-8")

    pending_payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        provider_name="static",
        static_response_json=response_json,
    )

    assert pending_payload["all_ok"]
    assert pending_payload["n_route_adoption_ready"] == 0
    assert pending_payload["n_route_adoption_pending_refinement"] == 1
    assert pending_payload["n_route_adoption_pending_quality_control_blockers"] == 1
    assert pending_payload["n_requests_with_quality_control_obligation_inventory"] == 1
    assert (
        pending_payload[
            "n_requests_with_pending_quality_control_obligation_inventory"
        ]
        == 1
    )
    assert pending_payload["n_request_quality_control_obligation_fields"] == 5
    assert pending_payload["n_request_quality_control_obligation_values"] == 5
    assert pending_payload["n_request_pending_quality_control_fields"] == 5
    assert pending_payload["n_request_pending_quality_control_values"] == 5
    assert pending_payload["n_request_discharged_quality_control_fields"] == 0
    assert pending_payload["n_request_discharged_quality_control_values"] == 0
    assert pending_payload["n_requests_with_route_adoption_preconditions"] == 1
    assert (
        pending_payload["n_request_route_adoption_precondition_known_blockers"]
        == 1
    )
    assert (
        pending_payload[
            "n_request_route_adoption_precondition_required_response_fields"
        ]
        == 2
    )
    pending_row = pending_payload["rows"][0]
    assert pending_row["acceptance_status"] == "ACCEPTED_WITH_PLANNER_NEXT_ACTIONS"
    assert pending_row["route_adoption_status"] == (
        "PENDING_REFINEMENT_BEFORE_ROUTE_ADOPTION"
    )
    assert pending_row["route_adoption_blockers"] == (
        "planner_next_actions_pending_evidence",
        "quality_control_obligations_pending",
    )
    pending_summary = pending_payload["request_packets"][0]["context_packet"][
        "feedback_loop_summary"
    ]["quality_control_obligations"]
    assert pending_summary["pending"] is True
    assert pending_summary["target_primitives"] == ["rank_uniformity"]
    assert pending_summary["pending_quality_controls"]["required_quality_signals"] == [
        "diagnostic_signature"
    ]
    pending_context = pending_payload["request_packets"][0]["context_packet"]
    pending_inventory = pending_context["context_packet_inventory"]
    pending_preconditions = pending_context["route_adoption_preconditions"]
    assert pending_preconditions["blocked_before_response"] is True
    assert pending_preconditions["known_pre_response_blockers"] == [
        "quality_control_obligations_pending"
    ]
    assert pending_preconditions["response_required_fields"] == [
        "search_requests",
        "planner_next_actions",
    ]
    assert pending_preconditions["target_primitives"] == ["rank_uniformity"]
    quality_focus = next(
        focus
        for focus in pending_context["route_planning_brief"]["planner_focus"]
        if focus["focus_id"] == "discharge_pending_quality_controls"
    )
    assert quality_focus["target_primitives"] == ["rank_uniformity"]
    quality_gap = next(
        gap
        for gap in pending_context["route_planning_brief"]["evidence_gaps"]
        if gap["gap_id"] == "pending_quality_controls"
    )
    assert quality_gap["target_primitives"] == ["rank_uniformity"]
    assert pending_row["route_adoption_preconditions"] == pending_preconditions
    assert pending_payload["n_rows_with_route_adoption_preconditions"] == 1
    assert (
        pending_payload["n_row_route_adoption_precondition_known_blockers"]
        == 1
    )
    assert pending_inventory["quality_control_obligation_present"] is True
    assert pending_inventory["quality_control_obligation_pending"] is True
    assert pending_inventory["quality_control_obligation_discharged"] is False
    assert pending_inventory["quality_control_obligation_field_count"] == 5
    assert pending_inventory["quality_control_obligation_value_count"] == 5
    assert pending_inventory["pending_quality_control_field_count"] == 5
    assert pending_inventory["pending_quality_control_value_count"] == 5
    assert pending_inventory["discharged_quality_control_field_count"] == 0
    assert pending_inventory["discharged_quality_control_value_count"] == 0
    assert pending_inventory["route_adoption_precondition_pending"] is True
    assert pending_inventory["route_adoption_precondition_known_blocker_count"] == 1
    drifted_pending_request = deepcopy(pending_payload["request_packets"][0])
    drifted_pending_request["context_packet"]["context_packet_inventory"][
        "pending_quality_control_value_count"
    ] = 0
    assert (
        "context_packet.context_packet_inventory."
        "pending_quality_control_value_count must match quality_control_obligations"
        in validate_llm_route_planner_request(drifted_pending_request)
    )
    assert (
        pending_payload["standalone_seed"]["routes"][0]["replan_metadata"][
            "llm_route_planner_route_adoption_blockers"
        ]
        == [
            "planner_next_actions_pending_evidence",
            "quality_control_obligations_pending",
        ]
    )
    seed_route = pending_payload["standalone_seed"]["routes"][0]
    assert seed_route["llm_route_planner_route_adoption_preconditions"] == (
        pending_preconditions
    )
    assert seed_route["replan_metadata"][
        "llm_route_planner_route_adoption_preconditions"
    ] == pending_preconditions
    expected_quality_control_gates = {
        key: value
        for key, value in quality_controls.items()
        if key != "target_primitives"
    }
    assert seed_route["replan_metadata"]["quality_controls"] == (
        expected_quality_control_gates
    )
    assert seed_route["replan_metadata"][
        "llm_route_planner_quality_control_obligations"
    ]["pending"] is True
    quality_hook = next(
        hook
        for hook in seed_route["interactive_refinement_hooks"]
        if hook.get("llm_route_planner_review_source")
        == "quality_control_obligations"
    )
    assert quality_hook["hook_kind"] == "proof_state_feedback"
    assert quality_hook["quality_controls"] == expected_quality_control_gates
    assert quality_hook["target_primitives"] == ["rank_uniformity"]
    assert "diagnostic_signature" in " ".join(quality_hook["queries"])
    quality_trigger = next(
        trigger
        for trigger in seed_route["route_revision_triggers"]
        if trigger.get("trigger_kind") == "quality_control_evidence_required"
    )
    assert quality_trigger["target_primitives"] == ["rank_uniformity"]

    plan_dir = root / "standalone_plan_from_pending_quality_control_seed"
    refinement_queue_dir = root / "refinement_queue_from_pending_quality_control_seed"
    plan_payload = export_formalization_gap_planner_standalone_plan(
        out_dir / "formalization_gap_planner_llm_route_planner_standalone_seed.json",
        plan_dir,
    )
    assert plan_payload["all_ok"]
    queue_payload = export_formalization_gap_planner_refinement_queue(
        plan_dir,
        refinement_queue_dir,
    )
    assert queue_payload["all_ok"]
    quality_queue_row = next(
        row
        for row in queue_payload["rows"]
        if row["hook_kind"] == "proof_state_feedback"
        and row["llm_route_planner_hook_trace"].get(
            "llm_route_planner_review_source"
        )
        == "quality_control_obligations"
    )
    assert quality_queue_row["quality_controls"]["required_quality_signals"] == (
        "diagnostic_signature",
    )
    assert (
        "quality_control_evidence_required" in quality_queue_row["trigger_kinds"]
    )
    assert quality_queue_row["target_primitives"] == ("rank_uniformity",)

    ledger_dir.mkdir(parents=True, exist_ok=True)
    (
        ledger_dir
        / "formalization_gap_planner_resource_response_ledger_manifest.json"
    ).write_text(
        json.dumps(
            {
                "component_name": "formalization_gap_planner_resource_response_ledger",
                "rows": [
                    {
                        "resource_response_ledger_id": "ledger:quality-controls",
                        "route_id": "rank_route",
                        "display_name": "distribution_free_rank_bound",
                        "acceptance_status": "ACCEPTED_RESOURCE_RESPONSE",
                        "response_present": True,
                        "response_contract_ok": True,
                        "response_contract_minimum_met": True,
                        "quality_controls": quality_controls,
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    discharged_response = deepcopy(response)
    discharged_response["planner_next_actions"] = []
    response_json.write_text(
        json.dumps(discharged_response, indent=2),
        encoding="utf-8",
    )

    discharged_payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        discharged_dir,
        provider_name="static",
        static_response_json=response_json,
        formalization_gap_planner_resource_response_ledger_dir=ledger_dir,
    )

    assert discharged_payload["all_ok"]
    assert discharged_payload["n_route_adoption_ready"] == 0
    assert discharged_payload["n_route_adoption_pending_refinement"] == 1
    assert discharged_payload["n_route_adoption_pending_quality_control_blockers"] == 0
    assert (
        discharged_payload["n_route_adoption_pending_formal_attempt_queue_blockers"]
        == 1
    )
    assert discharged_payload["n_requests_with_quality_control_obligation_inventory"] == 1
    assert (
        discharged_payload[
            "n_requests_with_pending_quality_control_obligation_inventory"
        ]
        == 0
    )
    assert discharged_payload["n_request_quality_control_obligation_fields"] == 5
    assert discharged_payload["n_request_quality_control_obligation_values"] == 5
    assert discharged_payload["n_request_pending_quality_control_fields"] == 0
    assert discharged_payload["n_request_pending_quality_control_values"] == 0
    assert discharged_payload["n_request_discharged_quality_control_fields"] == 5
    assert discharged_payload["n_request_discharged_quality_control_values"] == 5
    discharged_row = discharged_payload["rows"][0]
    assert discharged_row["route_adoption_status"] == (
        "PENDING_REFINEMENT_BEFORE_ROUTE_ADOPTION"
    )
    assert discharged_row["route_adoption_blockers"] == (
        ROUTE_ADOPTION_BLOCKER_FORMAL_ATTEMPT_QUEUE,
    )
    discharged_summary = discharged_payload["request_packets"][0]["context_packet"][
        "feedback_loop_summary"
    ]["quality_control_obligations"]
    assert discharged_summary["pending"] is False
    assert discharged_summary["discharged"] is True
    assert discharged_summary["pending_quality_controls"] == {}
    discharged_inventory = discharged_payload["request_packets"][0]["context_packet"][
        "context_packet_inventory"
    ]
    assert discharged_inventory["quality_control_obligation_present"] is True
    assert discharged_inventory["quality_control_obligation_pending"] is False
    assert discharged_inventory["quality_control_obligation_discharged"] is True
    assert discharged_inventory["quality_control_obligation_field_count"] == 5
    assert discharged_inventory["quality_control_obligation_value_count"] == 5
    assert discharged_inventory["pending_quality_control_field_count"] == 0
    assert discharged_inventory["pending_quality_control_value_count"] == 0
    assert discharged_inventory["discharged_quality_control_field_count"] == 5
    assert discharged_inventory["discharged_quality_control_value_count"] == 5
    assert not any(
        hook.get("llm_route_planner_review_source")
        == "quality_control_obligations"
        for hook in discharged_payload["standalone_seed"]["routes"][0][
            "interactive_refinement_hooks"
        ]
    )


def test_llm_route_planner_blocks_route_adoption_on_feedback_redispatch_actions() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_feedback_action_blocks_adoption"
    )
    out_dir = root / "llm_route_planner"
    response_json = root / "response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    response = _llm_response_payload()
    response["search_requests"] = []
    response["planner_next_actions"] = []
    response["uncertainty_flags"] = []
    response["semantic_alignment_risks"] = []
    response_json.write_text(json.dumps(response, indent=2), encoding="utf-8")
    resource_response_ledger_dir = _write_resource_response_ledger(root)
    manifest_path = (
        resource_response_ledger_dir
        / "formalization_gap_planner_resource_response_ledger_manifest.json"
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    row = manifest["rows"][0]
    row["acceptance_status"] = "REJECTED_RESPONSE_NOT_GROUNDED_IN_REQUEST_PLAYBOOK"
    row["response_contract_fields"] = [
        "source_refs",
        "source_snippets",
        "route_revision_recommended",
    ]
    row["response_contract_ok"] = False
    row["response_contract_minimum_met"] = True
    row["matched_response_contract_fields"] = ["source_refs", "source_snippets"]
    row["missing_response_contract_fields"] = ["route_revision_recommended"]
    row["request_playbook_present"] = True
    row["response_playbook_grounded"] = False
    row["response_playbook_grounding_terms"] = []
    row["ok"] = False
    row["errors"] = ["resource response is not grounded in request_playbook"]
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        provider_name="static",
        static_response_json=response_json,
        formalization_gap_planner_resource_response_ledger_dir=(
            resource_response_ledger_dir
        ),
    )

    assert payload["all_ok"]
    assert payload["n_response_contract_ok"] == 1
    assert payload["n_route_adoption_ready"] == 0
    assert payload["n_route_adoption_pending_refinement"] == 1
    assert payload["n_route_adoption_pending_feedback_action_blockers"] == 1
    assert (
        payload[
            "n_route_adoption_pending_resource_playbook_redispatch_blockers"
        ]
        == 1
    )
    row = payload["rows"][0]
    assert row["acceptance_status"] == "ACCEPTED_WITH_FORMAL_ATTEMPT_QUEUE"
    assert row["route_adoption_status"] == (
        "PENDING_REFINEMENT_BEFORE_ROUTE_ADOPTION"
    )
    assert set(row["route_adoption_blockers"]) >= {
        "feedback_summary_actions_pending_resolution",
        "resource_response_playbook_redispatch_pending",
    }
    seed_route = payload["standalone_seed"]["routes"][0]
    assert seed_route["llm_route_planner_route_adoption_status"] == (
        "PENDING_REFINEMENT_BEFORE_ROUTE_ADOPTION"
    )
    assert set(
        seed_route["replan_metadata"]["llm_route_planner_route_adoption_blockers"]
    ) >= {
        "feedback_summary_actions_pending_resolution",
        "resource_response_playbook_redispatch_pending",
    }
    redispatch_hook = next(
        hook
        for hook in seed_route["interactive_refinement_hooks"]
        if hook.get("llm_route_planner_feedback_next_action", {}).get("action")
        == "redispatch_resource_response_with_request_playbook"
    )
    assert redispatch_hook["hook_kind"] == "literature_discovery"
    assert redispatch_hook["llm_route_planner_feedback_next_action_index"] == 0
    assert "route_revision_recommended" in " ".join(redispatch_hook["queries"])
    assert any(
        trigger.get("trigger_kind")
        == "resource_response_playbook_redispatch_required"
        for trigger in seed_route["route_revision_triggers"]
    )

    plan_dir = root / "standalone_plan_from_feedback_redispatch_seed"
    refinement_queue_dir = root / "refinement_queue_from_feedback_redispatch_seed"
    plan_payload = export_formalization_gap_planner_standalone_plan(
        out_dir / "formalization_gap_planner_llm_route_planner_standalone_seed.json",
        plan_dir,
    )
    assert plan_payload["all_ok"]
    queue_payload = export_formalization_gap_planner_refinement_queue(
        plan_dir,
        refinement_queue_dir,
    )
    assert queue_payload["all_ok"]
    redispatch_queue_row = next(
        row
        for row in queue_payload["rows"]
        if row["hook_kind"] == "literature_discovery"
        and row["llm_route_planner_hook_trace"].get(
            "llm_route_planner_feedback_next_action", {}
        ).get("action")
        == "redispatch_resource_response_with_request_playbook"
    )
    assert (
        "resource_response_playbook_redispatch_required"
        in redispatch_queue_row["trigger_kinds"]
    )


def test_llm_route_planner_blocks_route_adoption_on_pending_resource_request_queue() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_resource_queue_blocks_adoption"
    )
    out_dir = root / "llm_route_planner"
    response_json = root / "response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    resource_request_queue_dir = _write_resource_request_queue(root)
    response = _llm_response_payload()
    response["search_requests"] = []
    response["planner_next_actions"] = [
        {
            "owner": "paperclip_cli_mcp",
            "action": "dispatch queued rank_uniformity literature evidence request",
            "resource_request_id": "resource-request:rank_route",
            "resource_id": "paperclip_cli_mcp",
            "target_primitives": ["rank_uniformity"],
        }
    ]
    response["uncertainty_flags"] = []
    response["semantic_alignment_risks"] = []
    response_json.write_text(json.dumps(response, indent=2), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        provider_name="static",
        static_response_json=response_json,
        formalization_gap_planner_resource_request_queue_dir=(
            resource_request_queue_dir
        ),
    )

    assert payload["all_ok"]
    assert payload["n_response_contract_ok"] == 1
    assert payload["n_route_adoption_ready"] == 0
    assert payload["n_route_adoption_pending_refinement"] == 1
    assert payload["n_route_adoption_pending_feedback_action_blockers"] == 1
    assert payload["n_route_adoption_pending_resource_request_queue_blockers"] == 1
    assert payload["n_route_adoption_pending_feedback_replan_blockers"] == 0
    assert payload["n_route_adoption_pending_realization_coverage_blockers"] == 0
    row = payload["rows"][0]
    assert row["acceptance_status"] == "ACCEPTED_WITH_PLANNER_NEXT_ACTIONS"
    assert row["route_adoption_status"] == (
        "PENDING_REFINEMENT_BEFORE_ROUTE_ADOPTION"
    )
    assert set(row["route_adoption_blockers"]) >= {
        "planner_next_actions_pending_evidence",
        "feedback_summary_actions_pending_resolution",
        "resource_request_queue_pending_response",
    }
    seed_route = payload["standalone_seed"]["routes"][0]
    queue_hook = next(
        hook
        for hook in seed_route["interactive_refinement_hooks"]
        if hook.get("llm_route_planner_feedback_next_action", {}).get("source")
        == "resource_request_queue"
    )
    assert queue_hook["hook_kind"] == "literature_discovery"
    assert queue_hook["resource_request_ids"] == ["resource-request:rank_route"]
    assert "paperclip_cli_mcp" in queue_hook["resource_ids"]
    assert queue_hook["quality_controls"]["resource_contract_ids"] == [
        "paperclip:source_snippet_contract"
    ]
    assert queue_hook["llm_route_planner_feedback_next_action"][
        "request_playbook_present"
    ] is True
    assert any(
        trigger.get("trigger_kind") == "queued_resource_response_required"
        for trigger in seed_route["route_revision_triggers"]
    )

    plan_dir = root / "standalone_plan_from_resource_queue_seed"
    refinement_queue_dir = root / "refinement_queue_from_resource_queue_seed"
    plan_payload = export_formalization_gap_planner_standalone_plan(
        out_dir / "formalization_gap_planner_llm_route_planner_standalone_seed.json",
        plan_dir,
    )
    assert plan_payload["all_ok"]
    queue_payload = export_formalization_gap_planner_refinement_queue(
        plan_dir,
        refinement_queue_dir,
    )
    assert queue_payload["all_ok"]
    queue_item = next(
        item
        for item in queue_payload["rows"]
        if item["hook_kind"] == "literature_discovery"
        and item["llm_route_planner_hook_trace"].get(
            "llm_route_planner_feedback_next_action", {}
        ).get("source")
        == "resource_request_queue"
    )
    assert queue_item["resource_request_ids"] == ("resource-request:rank_route",)
    assert "queued_resource_response_required" in queue_item["trigger_kinds"]


def test_llm_route_planner_accepts_candidate_declaration_rows_only_response() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_candidate_rows_only"
    )
    out_dir = root / "llm_route_planner"
    response_json = root / "response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    response = _llm_response_payload()
    declaration_row = {
        "declaration": "Probability.exchangeable",
        "target_prover_family": "lean4",
        "source_field": "available_formal_declaration_rows",
    }
    response["lean_realization_dag_nodes"][0].pop("candidate_declarations", None)
    response["lean_realization_dag_nodes"][0]["candidate_declaration_rows"] = [
        declaration_row
    ]
    response["standalone_route"]["primitives"][0].pop("candidate_declarations", None)
    response["standalone_route"]["primitives"][0]["candidate_declaration_rows"] = [
        declaration_row
    ]
    response_json.write_text(json.dumps(response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        provider_name="static",
        static_response_json=response_json,
    )

    assert payload["all_ok"]
    row = payload["rows"][0]
    formal_node = row["formal_realization_dag_nodes"][0]
    assert formal_node["candidate_declaration_rows"] == [declaration_row]
    assert formal_node["candidate_declarations"] == ["Probability.exchangeable"]
    seed_route = payload["standalone_seed"]["routes"][0]
    assert seed_route["primitives"][0]["candidate_declaration_rows"] == [
        declaration_row
    ]
    assert seed_route["primitives"][0]["candidate_declarations"] == [
        "Probability.exchangeable"
    ]


def test_llm_route_planner_preserves_candidate_declaration_row_scope_in_seed() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_candidate_row_scope_seed"
    )
    out_dir = root / "llm_route_planner"
    response_json = root / "response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    response = _llm_response_payload()
    declaration_row = {
        "declaration": "Probability.exchangeable",
        "target_prover_family": "lean4",
        "source_field": "available_formal_declaration_rows",
        "source_fields": [
            "available_formal_declaration_rows",
            "candidate_declarations",
        ],
        "target_primitives": ["exchangeability"],
        "supported_target_primitives": ["exchangeability"],
        "unsupported_target_primitives": ["rank_uniformity"],
        "source_refs": ["conformal_prediction_textbook"],
        "matched_terms": ["exchangeability"],
    }
    response["lean_realization_dag_nodes"][0].pop("candidate_declarations", None)
    response["lean_realization_dag_nodes"][0]["candidate_declaration_rows"] = [
        declaration_row
    ]
    response["standalone_route"]["primitives"][0].pop("candidate_declarations", None)
    response["standalone_route"]["primitives"][0]["candidate_declaration_rows"] = [
        declaration_row
    ]
    response_json.write_text(json.dumps(response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        provider_name="static",
        static_response_json=response_json,
    )

    assert payload["all_ok"]
    row = payload["rows"][0]
    assert row["formal_realization_dag_nodes"][0][
        "candidate_declaration_rows"
    ] == [declaration_row]
    seed_route = payload["standalone_seed"]["routes"][0]
    assert seed_route["primitives"][0]["candidate_declaration_rows"] == [
        declaration_row
    ]


def test_llm_route_planner_accepts_introduced_reuse_with_candidate_declaration_rows() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_introduced_candidate_rows"
    )
    out_dir = root / "llm_route_planner"
    response_json = root / "response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    input_payload = json.loads(input_json.read_text(encoding="utf-8"))
    input_payload["routes"][0]["candidate_declaration_rows"] = [
        {
            "declaration": "Probability.rankOrderStatistic",
            "target_prover_family": "lean4",
            "source_field": "route_level_formal_context",
        }
    ]
    input_json.write_text(json.dumps(input_payload, indent=2), encoding="utf-8")
    response = _llm_response_payload()
    helper_declaration_row = {
        "declaration": "Probability.rankOrderStatistic",
        "target_prover_family": "lean4",
        "source_field": "available_formal_declaration_rows",
    }
    response["informal_knowledge_dag_nodes"].append(
        {
            "node_id": "informal:rank_order_statistic",
            "claim": "The rank argument uses an order-statistic helper.",
            "depends_on": ["informal:rank_uniformity"],
            "source_refs": ["conformal_prediction_textbook"],
            "source_search_status": "SOURCE_BACKED",
            "semantic_role": "lemma",
        }
    )
    response["informal_knowledge_dag_edges"].append(
        {
            "source_node_id": "informal:rank_uniformity",
            "target_node_id": "informal:rank_order_statistic",
            "edge_kind": "uses",
            "rationale": (
                "The helper lemma refines the source-backed rank-uniformity "
                "argument."
            ),
        }
    )
    response["lean_realization_dag_nodes"].append(
        {
            "node_id": "formal:rank_order_statistic",
            "primitive": "rank_order_statistic",
            "coverage_bucket": "already_exists",
            "candidate_declaration_rows": [helper_declaration_row],
            "formalization_action": "reuse",
        }
    )
    response["formal_realization_dag_edges"].append(
        {
            "source_node_id": "formal:rank_uniformity_bridge",
            "target_node_id": "formal:rank_order_statistic",
            "edge_kind": "uses",
            "rationale": (
                "The reused order-statistic helper supports the formal "
                "rank-uniformity bridge route."
            ),
        }
    )
    response["route_alignment_edges"].append(
        {
            "informal_node_id": "informal:rank_order_statistic",
            "formal_node_id": "formal:rank_order_statistic",
            "alignment_status": "exact",
            "alignment_rationale": (
                "The introduced helper is realized by an existing declaration "
                "whose target-prover provenance is carried in a structured row."
            ),
        }
    )
    response["standalone_route"]["primitives"].append(
        {
            "primitive": "rank_order_statistic",
            "coverage_status": "exact_exists",
            "candidate_declaration_rows": [helper_declaration_row],
            "source_refs": ["conformal_prediction_textbook"],
        }
    )
    minimal_delta = response["minimal_delta_plan"]
    minimal_delta["selected_primitives"].append("rank_order_statistic")
    minimal_delta["primitive_costs"].append(
        {
            "primitive": "rank_order_statistic",
            "coverage_bucket": "already_exists",
            "base_cost": 0,
            "proof_difficulty_cost": 0,
            "import_cone_cost": 0,
            "definition_or_typeclass_cost": 0,
            "semantic_risk_cost": 0,
            "reuse_credit": 0,
            "total_cost": 0,
            "cost_rationale": (
                "The helper is an exact existing declaration, so it adds no "
                "new formalization delta."
            ),
        }
    )
    for option in minimal_delta["and_or_cost_graph"]["route_options"]:
        option["selected_primitives"].append("rank_order_statistic")
        option_costs = option.get("primitive_costs")
        if isinstance(option_costs, list):
            option_costs.append(
                {
                    "primitive": "rank_order_statistic",
                    "coverage_bucket": "already_exists",
                    "base_cost": 0,
                    "proof_difficulty_cost": 0,
                    "import_cone_cost": 0,
                    "definition_or_typeclass_cost": 0,
                    "semantic_risk_cost": 0,
                    "reuse_credit": 0,
                    "total_cost": 0,
                    "cost_rationale": (
                        "The helper is reused exactly in this route option."
                    ),
                }
            )
    option_primitives_by_id = {
        option["route_option_id"]: list(option["selected_primitives"])
        for option in minimal_delta["and_or_cost_graph"]["route_options"]
    }
    for edge in minimal_delta["and_or_cost_graph"]["and_edges"]:
        edge["requires"] = option_primitives_by_id[edge["route_option_id"]]
    response["formal_attempt_queue"].append(
        {
            "attempt_id": "attempt:rank_order_statistic_reuse",
            "formal_node_id": "formal:rank_order_statistic",
            "primitive": "rank_order_statistic",
            "target_prover_family": "lean4",
            "owner": "lean_lsp_mcp",
            "action": (
                "lean_lsp proof-state reuse check for "
                "Probability.rankOrderStatistic after rank_uniformity"
            ),
            "attempt_kind": "reuse_check",
            "prerequisite_formal_node_ids": ["formal:rank_uniformity_bridge"],
            "expected_feedback": ["closed_by_existing_declaration"],
            "target_primitives": ["rank_order_statistic"],
        }
    )
    _append_current_route_baseline_option(response)
    response_json.write_text(json.dumps(response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        provider_name="static",
        static_response_json=response_json,
    )

    assert payload["all_ok"]
    row = payload["rows"][0]
    witness = row["realization_coverage_witness"]
    assert "rank_order_statistic" in witness["introduced_primitives"]
    assert "rank_order_statistic" in witness["introduced_primitives_with_route_alignment_edge"]
    helper_node = next(
        node
        for node in row["formal_realization_dag_nodes"]
        if node["primitive"] == "rank_order_statistic"
    )
    assert helper_node["candidate_declarations"] == [
        "Probability.rankOrderStatistic"
    ]
    assert helper_node["candidate_declaration_rows"] == [helper_declaration_row]


def test_llm_route_planner_rejects_wrong_target_candidate_declaration_rows() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_rejects_wrong_target_candidate_rows"
    )
    response_json = root / "bad_response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    bad_response = _llm_response_payload()
    wrong_row = {
        "declaration": "Probability.exchangeable",
        "target_prover_family": "rocq",
        "source_field": "available_formal_declaration_rows",
    }
    bad_response["lean_realization_dag_nodes"][0].pop("candidate_declarations", None)
    bad_response["lean_realization_dag_nodes"][0]["candidate_declaration_rows"] = [
        wrong_row
    ]
    bad_response["standalone_route"]["primitives"][0].pop(
        "candidate_declarations",
        None,
    )
    bad_response["standalone_route"]["primitives"][0][
        "candidate_declaration_rows"
    ] = [wrong_row]
    response_json.write_text(json.dumps(bad_response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        provider_name="static",
        static_response_json=response_json,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    assert any(
        "candidate_declaration_rows[0].target_prover_family" in error
        and "does not match request target_prover_family lean4" in error
        for error in row["errors"]
    )


def test_llm_route_planner_rejects_wrong_candidate_declaration_row_provenance() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_rejects_wrong_candidate_row_provenance"
    )
    response_json = root / "bad_response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    bad_response = _llm_response_payload()
    wrong_row = {
        "declaration": "Probability.exchangeable",
        "target_prover_family": "lean4",
        "source_field": "unreviewed_external_search",
    }
    bad_response["lean_realization_dag_nodes"][0].pop("candidate_declarations", None)
    bad_response["lean_realization_dag_nodes"][0]["candidate_declaration_rows"] = [
        wrong_row
    ]
    bad_response["standalone_route"]["primitives"][0].pop(
        "candidate_declarations",
        None,
    )
    bad_response["standalone_route"]["primitives"][0][
        "candidate_declaration_rows"
    ] = [wrong_row]
    response_json.write_text(json.dumps(bad_response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        provider_name="static",
        static_response_json=response_json,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    assert any(
        "candidate_declaration_rows must preserve request/context formal-library provenance"
        in error
        and "unreviewed_external_search" in error
        for error in row["errors"]
    )


def test_llm_route_planner_search_requests_materialize_refinement_work_items() -> None:
    root = Path("runs/test_formalization_gap_planner_llm_route_planner_search_handoff")
    out_dir = root / "llm_route_planner"
    response_json = root / "response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    response_json.write_text(
        json.dumps(_llm_response_payload(), indent=2),
        encoding="utf-8",
    )

    llm_payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        provider_name="static",
        static_response_json=response_json,
    )

    assert llm_payload["all_ok"]
    seed_route = llm_payload["standalone_seed"]["routes"][0]
    assert seed_route["interactive_refinement_hooks"]
    assert seed_route["route_revision_triggers"]
    assert seed_route["replan_metadata"][
        "llm_route_planner_interactive_refinement_hooks"
    ][0]["hook_kind"] == "proof_state_feedback"
    assert seed_route["replan_metadata"]["llm_route_planner_planner_next_actions"][
        0
    ]["owner"] == "lean_lsp_mcp"
    assert any(
        hook.get("llm_route_planner_planner_next_action", {}).get("owner")
        == "lean_lsp_mcp"
        for hook in seed_route["interactive_refinement_hooks"]
    )
    assert any(
        trigger.get("llm_route_planner_planner_next_action", {}).get("owner")
        == "lean_lsp_mcp"
        for trigger in seed_route["route_revision_triggers"]
    )

    plan_dir = root / "standalone_plan_from_llm_seed"
    refinement_queue_dir = root / "refinement_queue_from_llm_seed"
    plan_payload = export_formalization_gap_planner_standalone_plan(
        out_dir / "formalization_gap_planner_llm_route_planner_standalone_seed.json",
        plan_dir,
    )
    assert plan_payload["all_ok"]
    plan_row = plan_payload["rows"][0]
    assert any(
        hook.get("llm_route_planner_search_request", {}).get("request_kind")
        == "prover_feedback"
        for hook in plan_row["interactive_refinement_hooks"]
    )

    queue_payload = export_formalization_gap_planner_refinement_queue(
        plan_dir,
        refinement_queue_dir,
    )
    assert queue_payload["all_ok"]
    assert queue_payload["n_proof_state_feedback_items"] >= 2
    assert any(
        row["hook_kind"] == "proof_state_feedback"
        and "try rank_uniformity bridge against Probability.exchangeable"
        in row["queries"]
        for row in queue_payload["rows"]
    )
    assert any(
        row["hook_kind"] == "proof_state_feedback"
        and row["llm_route_planner_hook_trace"]
        .get("llm_route_planner_search_request", {})
        .get("request_kind")
        == "prover_feedback"
        for row in queue_payload["rows"]
    )
    assert any(
        row["hook_kind"] == "proof_state_feedback"
        and row["llm_route_planner_hook_trace"]
        .get("llm_route_planner_planner_next_action", {})
        .get("owner")
        == "lean_lsp_mcp"
        and "attempt the rank_uniformity bridge lemma" in row["queries"]
        for row in queue_payload["rows"]
    )


def test_llm_route_planner_accepts_non_lean_generic_formal_realization_nodes() -> None:
    root = Path("runs/test_formalization_gap_planner_llm_route_planner_rocq_generic")
    out_dir = root / "llm_route_planner"
    input_json = root / "standalone_input.json"
    response_json = root / "response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "component_name": "formalization_gap_planner_standalone_input",
                "target_prover_family": "rocq",
                "library_snapshot_ref": "rocq:coq-community-probability",
                "routes": [
                        {
                            "route_id": "rocq_rank_route",
                            "display_name": "rocq_distribution_free_rank_bound",
                            "theorem_statement": "A Rocq rank bound follows from exchangeability.",
                            "source_refs": ["conformal_prediction_textbook"],
                            "source_snippets": [
                                {
                                    "source_ref": "conformal_prediction_textbook",
                                    "claim": "Exchangeability implies a uniform rank statistic.",
                                    "excerpt": (
                                        "Under exchangeability, the rank of the test score "
                                        "among calibration scores is uniformly distributed "
                                        "up to the tie convention."
                                    ),
                                    "target_primitives": ["rank_uniformity"],
                                }
                            ],
                            "quality_controls": {
                                "target_primitives": ["rank_uniformity"],
                                "resource_contract_ids": [
                                    "lean_lsp:proof_state_feedback"
                                ],
                                "required_quality_signals": [
                                    "diagnostic_signature"
                                ],
                                "response_validation_signals": [
                                    "residual_goals_or_diagnostics_present"
                                ],
                                "stop_conditions": [
                                    "residual interpreted or source search requested"
                                ],
                            },
                            "primitives": [
                            {
                                "primitive": "exchangeability",
                                "coverage_status": "exact_exists",
                                "candidate_declarations": ["Rocq.Probability.exchangeable"],
                            },
                            {
                                "primitive": "rank_uniformity",
                                "coverage_status": "bridge_needed",
                            },
                        ],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    response = _llm_response_payload()
    response["formal_realization_dag_nodes"] = [
        {
            **dict(node),
            "candidate_declarations": (
                ["Rocq.Probability.exchangeable"]
                if node["primitive"] == "exchangeability"
                else []
            ),
        }
        for node in response.pop("lean_realization_dag_nodes")
    ]
    response["standalone_route"]["primitives"][0]["candidate_declarations"] = [
        "Rocq.Probability.exchangeable"
    ]
    _set_existing_candidate_declaration_rows(
        response,
        declaration="Rocq.Probability.exchangeable",
        target_prover_family="rocq",
    )
    _retarget_formal_attempt_queue(
        response,
        target_prover_family="rocq",
        owner="rocq_serapi",
    )
    response["search_requests"][0] = {
        "request_kind": "prover_feedback",
        "query": "try the Rocq rank_uniformity bridge against Rocq.Probability.exchangeable",
        "reason": "confirm Rocq-side residual goals before route adoption",
    }
    response["search_requests"].append(
        {
            "request_kind": "formal_library",
            "query": "rank_uniformity Rocq probability exchangeability declarations",
            "reason": "search the target Rocq library before committing to the bridge formulation",
        }
    )
    response["planner_next_actions"] = [
        {
            "owner": "rocq_serapi",
            "action": "attempt Rocq proof-state feedback for rank_uniformity",
            "target_primitives": ["rank_uniformity"],
        }
    ]
    response_json.write_text(json.dumps(response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        provider_name="static",
        static_response_json=response_json,
    )

    assert payload["all_ok"]
    assert payload["n_response_contract_ok"] == 1
    assert payload["n_formal_realization_dag_nodes"] == 2
    assert payload["n_lean_realization_dag_nodes"] == 0
    row = payload["rows"][0]
    assert row["target_prover_family"] == "rocq"
    assert row["formal_realization_dag_nodes"]
    assert not row["lean_realization_dag_nodes"]
    seed_route = payload["standalone_seed"]["routes"][0]
    metadata = seed_route["replan_metadata"]
    assert payload["standalone_seed"]["target_prover_family"] == "rocq"
    assert seed_route["target_prover_family"] == "rocq"
    assert metadata["target_prover_family"] == "rocq"
    assert seed_route["revised_formal_realization_dag_nodes"]
    assert "revised_lean_realization_dag_nodes" not in seed_route
    assert "revised_lean_realization_dag_nodes" not in metadata
    hook_kinds = {
        hook["hook_kind"] for hook in seed_route["interactive_refinement_hooks"]
    }
    assert "formal_library_grounding" in hook_kinds
    assert "lean_library_grounding" not in hook_kinds
    formal_hook = next(
        hook
        for hook in seed_route["interactive_refinement_hooks"]
        if hook["hook_kind"] == "formal_library_grounding"
    )
    assert "target-prover library search/RAG" in formal_hook["recommended_tools"]
    proof_hook = next(
        hook
        for hook in seed_route["interactive_refinement_hooks"]
        if hook["hook_kind"] == "proof_state_feedback"
        and hook.get("llm_route_planner_planner_next_action", {}).get("action")
        == "attempt Rocq proof-state feedback for rank_uniformity"
    )
    assert "Rocq/coq-lsp proof-state adapter" in proof_hook["recommended_tools"]
    assert "lean-lsp-mcp" not in proof_hook["recommended_tools"]
    assert "lake build" not in proof_hook["recommended_tools"]
    quality_hook = next(
        hook
        for hook in seed_route["interactive_refinement_hooks"]
        if hook.get("llm_route_planner_review_source")
        == "quality_control_obligations"
    )
    assert quality_hook["hook_kind"] == "proof_state_feedback"
    assert "Rocq/coq-lsp proof-state adapter" in quality_hook["recommended_tools"]
    assert quality_hook["quality_controls"]["resource_contract_ids"] == [
        "rocq_lsp_serapi:proof_state_feedback"
    ]
    assert quality_hook["source_quality_controls"]["resource_contract_ids"] == [
        "lean_lsp:proof_state_feedback"
    ]
    assert quality_hook["quality_control_projection"][
        "projected_resource_contract_ids"
    ] == ["rocq_lsp_serapi:proof_state_feedback"]
    quality_trigger = next(
        trigger
        for trigger in seed_route["route_revision_triggers"]
        if trigger.get("llm_route_planner_review_source")
        == "quality_control_obligations"
    )
    assert quality_trigger["quality_controls"]["resource_contract_ids"] == [
        "rocq_lsp_serapi:proof_state_feedback"
    ]
    assert quality_trigger["source_quality_controls"]["resource_contract_ids"] == [
        "lean_lsp:proof_state_feedback"
    ]


def test_llm_route_planner_target_scopes_lean_search_hooks_for_rocq() -> None:
    root = Path("runs/test_formalization_gap_planner_llm_route_planner_rocq_lean_search")
    out_dir = root / "llm_route_planner"
    input_json = root / "standalone_input.json"
    response_json = root / "response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "component_name": "formalization_gap_planner_standalone_input",
                "target_prover_family": "rocq",
                "library_snapshot_ref": "rocq:coq-community-probability",
                "routes": [
                    {
                        "route_id": "rocq_rank_route",
                        "display_name": "rocq_distribution_free_rank_bound",
                        "target_prover_family": "rocq",
                        "theorem_statement": "A Rocq rank bound follows from exchangeability.",
                        "source_refs": ["conformal_prediction_textbook"],
                        "source_snippets": [
                            {
                                "source_ref": "conformal_prediction_textbook",
                                "claim": "Exchangeability implies a uniform rank statistic.",
                                "excerpt": (
                                    "Under exchangeability, the rank of the test score "
                                    "among calibration scores is uniformly distributed "
                                    "up to the tie convention."
                                ),
                                "target_primitives": ["rank_uniformity"],
                            }
                        ],
                        "primitives": [
                            {
                                "primitive": "exchangeability",
                                "coverage_status": "exact_exists",
                                "candidate_declarations": [
                                    "Rocq.Probability.exchangeable"
                                ],
                            },
                            {
                                "primitive": "rank_uniformity",
                                "coverage_status": "bridge_needed",
                            },
                        ],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    response = _llm_response_payload()
    response["formal_realization_dag_nodes"] = [
        {
            **dict(node),
            "candidate_declarations": (
                ["Rocq.Probability.exchangeable"]
                if node["primitive"] == "exchangeability"
                else []
            ),
        }
        for node in response.pop("lean_realization_dag_nodes")
    ]
    response["standalone_route"]["target_prover_family"] = "rocq"
    response["standalone_route"]["primitives"][0]["candidate_declarations"] = [
        "Rocq.Probability.exchangeable"
    ]
    _set_existing_candidate_declaration_rows(
        response,
        declaration="Rocq.Probability.exchangeable",
        target_prover_family="rocq",
    )
    _retarget_formal_attempt_queue(
        response,
        target_prover_family="rocq",
        owner="formal_retrieval",
    )
    response["search_requests"] = [
        {
            "request_kind": "formal_library",
            "query": "rank_uniformity target-library query for Rocq exchangeability",
            "reason": (
                "search the target Rocq library through the portable "
                "formal-library contract"
            ),
        }
    ]
    response["planner_next_actions"] = [
        {
            "owner": "formal_retrieval",
            "action": "run target-prover declaration query against the Rocq adapter",
        }
    ]
    response_json.write_text(json.dumps(response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        provider_name="static",
        static_response_json=response_json,
    )

    assert payload["all_ok"]
    route = payload["standalone_seed"]["routes"][0]
    hook_kinds = {
        hook["hook_kind"] for hook in route["interactive_refinement_hooks"]
    }
    trigger_kinds = {
        trigger["trigger_kind"] for trigger in route["route_revision_triggers"]
    }
    assert "formal_library_grounding" in hook_kinds
    assert "lean_library_grounding" not in hook_kinds
    assert "formal_leaf_attempt_required" in trigger_kinds
    assert "lean_leaf_attempt_required" not in trigger_kinds
    formal_hooks = [
        hook
        for hook in route["interactive_refinement_hooks"]
        if hook["hook_kind"] == "formal_library_grounding"
    ]
    assert formal_hooks
    assert all(
        "LeanSearch" not in hook["recommended_tools"]
        and "Loogle" not in hook["recommended_tools"]
        for hook in formal_hooks
    )


def test_llm_route_planner_accepts_target_filtered_registry_adapter_id() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_rocq_registry_adapter"
    )
    out_dir = root / "llm_route_planner"
    registry_dir = root / "component_resource_registry"
    input_json = root / "standalone_input.json"
    response_json = root / "response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "component_name": "formalization_gap_planner_standalone_input",
                "target_prover_family": "rocq",
                "library_snapshot_ref": "rocq:coq-community-probability",
                "routes": [
                    {
                        "route_id": "rocq_rank_route",
                        "display_name": "rocq_distribution_free_rank_bound",
                        "target_prover_family": "rocq",
                        "theorem_statement": (
                            "A Rocq rank bound follows from exchangeability."
                        ),
                        "source_refs": ["conformal_prediction_textbook"],
                        "source_snippets": [
                            {
                                "source_ref": "conformal_prediction_textbook",
                                "claim": "Exchangeability implies a uniform rank statistic.",
                                "excerpt": (
                                    "Under exchangeability, the rank of the test score "
                                    "among calibration scores is uniformly distributed "
                                    "up to the tie convention."
                                ),
                                "target_primitives": ["rank_uniformity"],
                            }
                        ],
                        "primitives": [
                            {
                                "primitive": "exchangeability",
                                "coverage_status": "exact_exists",
                                "candidate_declarations": [
                                    "Rocq.Probability.exchangeable"
                                ],
                            },
                            {
                                "primitive": "rank_uniformity",
                                "coverage_status": "bridge_needed",
                            },
                        ],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    export_formalization_gap_planner_component_resource_registry(registry_dir)
    response = _llm_response_payload()
    response["formal_realization_dag_nodes"] = [
        {
            **dict(node),
            "candidate_declarations": (
                ["Rocq.Probability.exchangeable"]
                if node["primitive"] == "exchangeability"
                else []
            ),
        }
        for node in response.pop("lean_realization_dag_nodes")
    ]
    response["standalone_route"]["target_prover_family"] = "rocq"
    response["standalone_route"]["primitives"][0]["candidate_declarations"] = [
        "Rocq.Probability.exchangeable"
    ]
    _set_existing_candidate_declaration_rows(
        response,
        declaration="Rocq.Probability.exchangeable",
        target_prover_family="rocq",
    )
    _retarget_formal_attempt_queue(
        response,
        target_prover_family="rocq",
        owner="rocq_serapi",
    )
    response["planner_next_actions"] = [
        {
            "owner": "route_revision_overlay",
            "adapter_id": "route_revision_overlay",
            "action": "apply route_revision route repair for rank_uniformity",
        }
    ]
    response_json.write_text(json.dumps(response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        provider_name="static",
        static_response_json=response_json,
        formalization_gap_planner_component_resource_registry_dir=registry_dir,
    )

    assert payload["all_ok"]
    row = payload["rows"][0]
    assert row["response_contract_ok"]
    assert row["planner_next_actions"][0]["adapter_id"] == "route_revision_overlay"


def test_llm_route_planner_rejects_non_lean_legacy_realization_alias() -> None:
    root = Path("runs/test_formalization_gap_planner_llm_route_planner_rocq_alias")
    out_dir = root / "llm_route_planner"
    input_json = root / "standalone_input.json"
    response_json = root / "response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "component_name": "formalization_gap_planner_standalone_input",
                "target_prover_family": "rocq",
                "library_snapshot_ref": "rocq:coq-community-probability",
                "routes": [
                    {
                        "route_id": "rocq_rank_route",
                        "display_name": "rocq_distribution_free_rank_bound",
                        "theorem_statement": (
                            "A Rocq rank bound follows from exchangeability."
                        ),
                        "source_refs": ["conformal_prediction_textbook"],
                        "source_snippets": [
                            {
                                "source_ref": "conformal_prediction_textbook",
                                "claim": "Exchangeability implies a uniform rank statistic.",
                                "excerpt": (
                                    "Under exchangeability, the rank of the test score "
                                    "among calibration scores is uniformly distributed "
                                    "up to the tie convention."
                                ),
                                "target_primitives": ["rank_uniformity"],
                            }
                        ],
                        "primitives": [
                            {
                                "primitive": "exchangeability",
                                "coverage_status": "exact_exists",
                                "candidate_declarations": [
                                    "Rocq.Probability.exchangeable"
                                ],
                            },
                            {
                                "primitive": "rank_uniformity",
                                "coverage_status": "bridge_needed",
                            },
                        ],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    response = _llm_response_payload()
    response["standalone_route"]["primitives"][0]["candidate_declarations"] = [
        "Rocq.Probability.exchangeable"
    ]
    for node in response["lean_realization_dag_nodes"]:
        if node["primitive"] == "exchangeability":
            node["candidate_declarations"] = ["Rocq.Probability.exchangeable"]
    response["planner_next_actions"] = [
        {
            "owner": "rocq_serapi",
            "action": "attempt Rocq proof-state feedback for rank_uniformity",
        }
    ]
    response_json.write_text(json.dumps(response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        provider_name="static",
        static_response_json=response_json,
    )

    assert not payload["all_ok"]
    assert payload["n_response_contract_ok"] == 0
    row = payload["rows"][0]
    assert row["target_prover_family"] == "rocq"
    assert row["response_contract_ok"] is False
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    assert any(
        "lean_realization_dag_nodes is a Lean-only legacy alias" in error
        for error in row["errors"]
    )


def test_llm_route_planner_invokes_anthropic_generator_backend_without_live_api() -> None:
    root = Path("runs/test_formalization_gap_planner_llm_route_planner_anthropic_fake")
    out_dir = root / "llm_route_planner"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    captured: dict[str, object] = {}

    class FakeAnthropicBackend:
        provider_name = "anthropic"

        def generate(self, request):
            captured["request"] = request
            return GeneratorResponse(
                text=json.dumps(_llm_response_payload()),
                provider="anthropic",
                model=request.model,
                metadata={
                    "generator_only": True,
                    "tools_available": False,
                    "schema_supplied": request.schema is not None,
                    "retry_count": 1,
                    "provider_usage": {
                        "input_tokens": 123,
                        "output_tokens": 45,
                        "cache_read_input_tokens": 7,
                    },
                },
            )

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        provider_name="anthropic",
        invoke_provider=True,
        generator_backend=FakeAnthropicBackend(),
    )

    assert payload["all_ok"]
    assert payload["provider_name"] == "anthropic"
    assert payload["provider_execution_mode"] == (
        PROVIDER_EXECUTION_MODE_SUPPLIED_GENERATOR_BACKEND
    )
    assert payload["invoke_provider"] is True
    assert payload["response_json_supplied"] is False
    assert payload["static_response_json_supplied"] is False
    assert payload["generator_backend_supplied"] is True
    assert payload["live_provider_backend_requested"] is False
    assert payload["static_generator_backend_requested"] is False
    assert payload["provider_generation_requested"] is True
    assert payload["model_tier_selection_mode"] == "auto"
    assert payload["by_request_model_tier"] == {"sonnet": 1}
    assert payload["n_requests_with_model_tier_decision_evidence"] == 1
    assert payload["n_request_model_tier_decision_auto_sonnet_triggered"] == 1
    assert payload["n_request_model_tier_decision_auto_haiku_bounded"] == 0
    assert payload["n_request_model_tier_decision_operator_override"] == 0
    assert payload["n_request_model_tier_decision_sonnet_triggers"] >= 1
    assert payload["n_request_model_tier_decision_evidence_invalid"] == 0
    assert payload["by_request_model_tier_decision_basis"] == {
        "auto_sonnet_triggers": 1
    }
    assert payload["n_raw_responses"] == 1
    assert payload["n_response_present"] == 1
    assert payload["n_provider_failures"] == 0
    assert payload["n_rows_with_generator_metadata"] == 1
    assert payload["n_rows_with_provider_usage"] == 1
    assert payload["total_provider_input_tokens"] == 123
    assert payload["total_provider_output_tokens"] == 45
    assert payload["total_provider_cache_read_input_tokens"] == 7
    assert payload["total_provider_total_tokens"] == 175
    assert payload["provider_usage_summary"]["row_count"] == 1
    assert payload["provider_usage_summary"]["by_model_tier"]["sonnet"][
        "input_tokens"
    ] == 123
    assert payload["provider_usage_summary"]["by_provider"]["anthropic"][
        "output_tokens"
    ] == 45
    usage_row = payload["provider_usage_rows"][0]
    assert usage_row["provider_name"] == "anthropic"
    assert usage_row["model_tier"] == "sonnet"
    assert usage_row["input_tokens"] == 123
    assert usage_row["output_tokens"] == 45
    assert usage_row["cache_read_input_tokens"] == 7
    assert usage_row["total_tokens"] == 175
    assert payload["n_response_contract_ok"] == 1
    assert payload["n_accepted_route_plans"] == 1
    row = payload["rows"][0]
    assert row["provider_name"] == "anthropic"
    assert row["model"] == "claude-sonnet-4-6"
    assert row["model_tier"] == "sonnet"
    assert row["provider_failure"] is False
    assert row["generator_metadata"]["generator_only"] is True
    assert row["generator_metadata"]["tools_available"] is False
    assert row["generator_metadata"]["schema_supplied"] is True
    assert row["generator_metadata"]["retry_count"] == 1
    assert row["generator_metadata"]["provider_usage"]["input_tokens"] == 123
    assert "bridge_needed" in row["model_selection_rationale"]
    assert row["model_tier_decision_evidence"]["selected_model_tier"] == "sonnet"
    assert row["model_tier_decision_evidence"]["effective_model_tier"] == "sonnet"
    assert (
        row["model_tier_decision_evidence"]["decision_basis"]
        == "auto_sonnet_triggers"
    )
    assert any(
        "bridge_needed" in trigger
        for trigger in row["model_tier_decision_evidence"]["sonnet_triggers"]
    )
    tier_ledger_row = payload["model_tier_decision_ledger"][0]
    assert tier_ledger_row["provider_name"] == "anthropic"
    assert tier_ledger_row["selected_model_tier"] == "sonnet"
    assert tier_ledger_row["effective_model_tier"] == "sonnet"
    assert tier_ledger_row["request_model"] == "claude-sonnet-4-6"
    assert tier_ledger_row["effective_model"] == "claude-sonnet-4-6"
    assert tier_ledger_row["response_present"] is True
    assert tier_ledger_row["response_contract_ok"] is True
    assert tier_ledger_row["provider_failure"] is False
    assert "retry_count" in tier_ledger_row["generator_metadata_keys"]
    packet = payload["request_packets"][0]
    assert packet["model"] == "claude-sonnet-4-6"
    assert packet["model_tier"] == "sonnet"
    assert packet["model_tier_decision_evidence"] == row[
        "model_tier_decision_evidence"
    ]
    assert packet["minimal_delta_cost_policy"]["proof_boundary"]
    assert packet["prompt_messages"]["user"].count("available_source_snippets") >= 1
    assert payload["llm_route_planner_model_tier_policy"]["claude_model_selection"]["models_by_tier"] == {
        "haiku": "claude-haiku-4-5-20251001",
        "sonnet": "claude-sonnet-4-6",
        "opus": "claude-opus-4-8",
    }
    assert (
        "not evergreen aliases"
        in payload["llm_route_planner_model_tier_policy"]["claude_model_selection"]["model_id_versioning"]
    )
    request = captured["request"]
    assert request.model == "claude-sonnet-4-6"
    assert request.max_tokens == 9000
    assert request.temperature == 0.1
    assert "LLM route planner" in request.system_prompt
    assert "required_output_contract" in request.user_prompt
    assert request.schema["required"] == [
        "informal_knowledge_dag_nodes",
        "informal_knowledge_dag_edges",
        "formal_realization_dag_edges",
        "route_alignment_edges",
        "minimal_delta_plan",
        "formal_attempt_queue",
        "standalone_route",
        "proof_evidence_boundary",
    ]
    assert request.schema["properties"]["formal_realization_dag_nodes"][
        "items"
    ] == {"$ref": "#/$defs/formal_realization_node"}
    assert request.schema["properties"]["lean_realization_dag_nodes"]["items"] == {
        "$ref": "#/$defs/formal_realization_node"
    }
    assert request.metadata["component"] == "formalization_gap_planner_llm_route_planner"
    assert request.metadata["request_id"] == payload["request_packets"][0]["request_id"]
    assert request.metadata["model_tier"] == "sonnet"
    seed_metadata = payload["standalone_seed"]["routes"][0]["replan_metadata"]
    assert seed_metadata["llm_route_planner_model_tier"] == "sonnet"
    assert "bridge_needed" in seed_metadata[
        "llm_route_planner_model_selection_rationale"
    ]
    assert seed_metadata["llm_route_planner_generator_metadata"][
        "schema_supplied"
    ] is True
    assert seed_metadata["llm_route_planner_generator_metadata"]["retry_count"] == 1
    assert seed_metadata["llm_route_planner_generator_metadata"][
        "provider_usage"
    ]["output_tokens"] == 45
    assert set(seed_metadata["llm_route_planner_generator_metadata_keys"]) >= {
        "generator_only",
        "provider_usage",
        "retry_count",
        "schema_supplied",
        "tools_available",
    }
    assert (
        out_dir
        / "formalization_gap_planner_llm_route_planner_standalone_seed.json"
    ).exists()


def test_llm_route_planner_records_provider_failure_as_rejected_row() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_provider_failure"
    )
    out_dir = root / "llm_route_planner"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)

    class FailingAnthropicBackend:
        provider_name = "anthropic"

        def generate(self, request):
            raise TimeoutError("simulated Anthropic timeout")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        provider_name="anthropic",
        invoke_provider=True,
        generator_backend=FailingAnthropicBackend(),
        max_repair_attempts=0,
    )

    assert not payload["all_ok"]
    assert payload["n_raw_responses"] == 1
    assert payload["n_response_present"] == 0
    assert payload["n_provider_failures"] == 1
    assert payload["n_rows_with_generation_errors"] == 1
    assert payload["n_awaiting_llm_response"] == 0
    assert payload["n_rejected"] == 1
    assert payload["by_acceptance_status"] == {
        "REJECTED_LLM_ROUTE_PLANNER_PROVIDER_FAILURE": 1
    }
    row = payload["rows"][0]
    assert row["provider_failure"] is True
    assert row["response_present"] is False
    assert row["response_contract_ok"] is False
    assert row["ok"] is False
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_PROVIDER_FAILURE"
    assert any("TimeoutError" in error for error in row["generation_errors"])
    assert row["generator_metadata"]["provider_failure"] is True
    assert row["generator_metadata"]["exception_type"] == "TimeoutError"
    assert row["generator_metadata"]["tools_available"] is False
    manifest = json.loads(
        (
            out_dir / "formalization_gap_planner_llm_route_planner_manifest.json"
        ).read_text(encoding="utf-8")
    )
    assert manifest["n_provider_failures"] == 1
    assert manifest["rows"][0]["provider_failure"] is True
    report = (
        out_dir / "formalization_gap_planner_llm_route_planner.md"
    ).read_text(encoding="utf-8")
    assert "- Provider failures: 1" in report


def test_llm_route_planner_auto_uses_haiku_for_small_bounded_routes() -> None:
    root = Path("runs/test_formalization_gap_planner_llm_route_planner_haiku_fake")
    out_dir = root / "llm_route_planner"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_light_input(root)
    captured: dict[str, object] = {}

    class FakeAnthropicBackend:
        provider_name = "anthropic"

        def generate(self, request):
            captured["request"] = request
            return GeneratorResponse(
                text=json.dumps(_llm_response_payload()),
                provider="anthropic",
                model=request.model,
                metadata={
                    "generator_only": True,
                    "tools_available": False,
                    "schema_supplied": request.schema is not None,
                },
            )

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        provider_name="anthropic",
        invoke_provider=True,
        generator_backend=FakeAnthropicBackend(),
    )

    assert payload["all_ok"]
    assert payload["by_request_model_tier"] == {"haiku": 1}
    assert payload["n_requests_with_model_tier_decision_evidence"] == 1
    assert payload["n_request_model_tier_decision_auto_haiku_bounded"] == 1
    assert payload["n_request_model_tier_decision_auto_sonnet_triggered"] == 0
    assert payload["n_request_model_tier_decision_sonnet_triggers"] == 0
    assert payload["n_request_model_tier_decision_evidence_invalid"] == 0
    assert payload["by_request_model_tier_decision_basis"] == {
        "auto_haiku_bounded_route": 1
    }
    packet = payload["request_packets"][0]
    assert packet["model_tier"] == "haiku"
    assert packet["model"] == "claude-haiku-4-5-20251001"
    assert "small route" in packet["model_selection_rationale"]
    assert (
        packet["model_tier_decision_evidence"]["decision_basis"]
        == "auto_haiku_bounded_route"
    )
    assert packet["model_tier_decision_evidence"]["haiku_safety_checks"] == {
        "no_residual_goals": True,
        "primitive_count_at_most_four": True,
        "source_ref_count_at_most_six": True,
        "theorem_statement_at_most_600_chars": True,
        "no_complex_coverage_or_action_markers": True,
        "no_pending_resource_request_queue": True,
        "no_resource_request_playbooks": True,
        "no_interactive_resource_requests": True,
        "no_interactive_dispatch_summaries": True,
        "no_interactive_execution_commands": True,
        "no_interactive_formal_attempt_queue": True,
        "no_interactive_formal_attempt_execution_commands": True,
        "no_unresolved_interactive_route_adoption_preconditions": True,
        "no_interactive_route_adoption_blockers": True,
        "no_resource_feedback_readiness_context": True,
        "no_formal_attempt_feedback_context": True,
        "no_source_theorem_feedback": True,
        "no_pending_source_grounding_obligations": True,
        "no_residual_source_grounding_obligations": True,
        "no_agentic_proof_strategy_plan_ready": True,
    }
    stale_haiku_safety_request = deepcopy(packet)
    stale_haiku_checks = stale_haiku_safety_request[
        "model_tier_decision_evidence"
    ]["haiku_safety_checks"]
    stale_haiku_checks.pop("no_pending_source_grounding_obligations")
    stale_haiku_checks.pop("no_residual_source_grounding_obligations")
    stale_haiku_checks.pop("no_agentic_proof_strategy_plan_ready")
    stale_haiku_checks.pop("no_interactive_formal_attempt_queue")
    stale_haiku_checks.pop("no_interactive_formal_attempt_execution_commands")
    stale_haiku_checks.pop("no_resource_feedback_readiness_context")
    stale_haiku_checks.pop("no_formal_attempt_feedback_context")
    stale_haiku_errors = validate_llm_route_planner_request(
        stale_haiku_safety_request
    )
    assert any(
        "haiku_safety_checks missing required checks" in error
        and "no_pending_source_grounding_obligations" in error
        and "no_residual_source_grounding_obligations" in error
        and "no_agentic_proof_strategy_plan_ready" in error
        and "no_interactive_formal_attempt_queue" in error
        and "no_interactive_formal_attempt_execution_commands" in error
        and "no_resource_feedback_readiness_context" in error
        and "no_formal_attempt_feedback_context" in error
        for error in stale_haiku_errors
    )
    assert packet["model_tier_decision_evidence"]["route_signal_counts"][
        "source_grounding_unresolved_count"
    ] == 0
    row = payload["rows"][0]
    assert row["model_tier"] == "haiku"
    assert row["model"] == "claude-haiku-4-5-20251001"
    assert row["model_tier_decision_evidence"] == packet[
        "model_tier_decision_evidence"
    ]
    request = captured["request"]
    assert request.model == "claude-haiku-4-5-20251001"
    assert request.metadata["model_tier"] == "haiku"


def test_llm_route_planner_auto_uses_sonnet_for_light_route_resource_feedback_readiness() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_light_resource_feedback_tier"
    )
    out_dir = root / "llm_route_planner"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_light_input(root)
    resource_response_ledger_dir = _write_resource_response_ledger(root)
    ledger_manifest_path = (
        resource_response_ledger_dir
        / "formalization_gap_planner_resource_response_ledger_manifest.json"
    )
    ledger_manifest = json.loads(ledger_manifest_path.read_text(encoding="utf-8"))
    for row in ledger_manifest["rows"]:
        row["resource_response_ledger_id"] = (
            "resource-response:rank_route_light"
        )
        row["resource_request_id"] = "resource-request:rank_route_light"
        row["goal_plan_id"] = "goal:rank_route_light"
        row["route_id"] = "rank_route_light"
        row["display_name"] = "distribution_free_rank_bound_light"
        row["minimal_delta_cost_score"] = 10
        row["reuse_readiness_score"] = 95
        row["evidence_readiness_score"] = 85
        row["coverage_updates"] = {"rank_uniformity": "near_exists"}
        row["residual_goals"] = []
        row["route_revision_recommended"] = False
        row["route_revision_reasons"] = []
        row["response_payload"]["route_revision_recommended"] = False
        row["acceptance_status"] = "ACCEPTED_RESOURCE_RESPONSE"
    ledger_manifest_path.write_text(
        json.dumps(ledger_manifest, indent=2),
        encoding="utf-8",
    )

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        provider_name="anthropic",
        formalization_gap_planner_resource_response_ledger_dir=(
            resource_response_ledger_dir
        ),
    )

    assert payload["all_ok"]
    assert payload["by_request_model_tier"] == {"sonnet": 1}
    assert payload["n_request_model_tier_decision_auto_sonnet_triggered"] == 1
    assert payload["n_request_model_tier_decision_auto_haiku_bounded"] == 0
    assert payload["n_requests_with_resource_feedback_readiness_summary"] == 1
    assert payload["n_request_resource_feedback_readiness_rows"] == 1
    assert payload["n_request_resource_feedback_reuse_ready_rows"] == 1
    packet = payload["request_packets"][0]
    assert packet["model_tier"] == "sonnet"
    assert packet["model"] == "claude-sonnet-4-6"
    evidence = packet["model_tier_decision_evidence"]
    assert evidence["decision_basis"] == "auto_sonnet_triggers"
    assert evidence["route_signal_counts"][
        "resource_feedback_readiness_row_count"
    ] == 1
    assert evidence["route_signal_counts"][
        "resource_feedback_readiness_reuse_ready_count"
    ] == 1
    assert evidence["resource_feedback_readiness_counts"] == {
        "total_count": 1,
        "reuse_ready_count": 1,
        "light_bridge_or_wrapper_count": 0,
        "source_or_new_theory_count": 0,
        "alignment_blocked_count": 0,
    }
    assert any(
        "resource-feedback readiness row" in trigger
        for trigger in evidence["sonnet_triggers"]
    )
    context = packet["context_packet"]
    assert context["feedback_loop_summary"]["replan_required"] is False
    assert context["feedback_loop_summary"]["recommended_next_actions"] == []
    ledger_row = payload["model_tier_decision_ledger"][0]
    assert ledger_row["resource_feedback_readiness_counts"] == (
        evidence["resource_feedback_readiness_counts"]
    )
    assert ledger_row["route_signal_counts"][
        "resource_feedback_readiness_row_count"
    ] == 1


def test_llm_route_planner_auto_uses_sonnet_for_ready_agentic_strategy_plan() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_light_agentic_strategy_tier"
    )
    out_dir = root / "llm_route_planner"
    strategy_plan_dir = root / "agentic_strategy_plan"
    shutil.rmtree(root, ignore_errors=True)
    strategy_plan_dir.mkdir(parents=True, exist_ok=True)
    input_json = _write_light_input(root)
    strategy_rows = [
        {
            "schema_version": 1,
            "strategy_id": "strategy:rank_route_light:source",
            "followup_id": "followup:rank_route_light:source",
            "residual_response_validation_id": "validation:rank_route_light:source",
            "prompt_packet_id": "packet:rank_route_light:source",
            "residual_obligation_id": (
                "residual-obligation:rank_route_light:rank_uniformity"
            ),
            "route_id": "rank_route_light",
            "display_name": "distribution_free_rank_bound_light",
            "target_theorem_name": "distribution_free_rank_bound_light",
            "candidate_bridge_lemma_name": "rank_uniformity_bridge",
            "residual_gap": "rank_uniformity",
            "action_class": "source_discovery_needed",
            "followup_kind": "residual_source_discovery",
            "followup_status": "READY_FOR_AGENTIC_PROOF_STRATEGY",
            "agentic_strategy_kind": "global_goal_cache_source_discovery",
            "paper_patterns": ["uniform rank statistic"],
            "required_live_tools": ["paperqa", "lean_leansearch"],
            "evaluator_gates": ["primitive-source coverage expansion"],
            "global_goal_cache_keys": ["rank_uniformity:exchangeable_scores"],
            "candidate_database_key": "candidate-db:rank_route_light:rank_uniformity",
            "expected_artifacts": ["source_cache/rank_uniformity.json"],
            "priority_score": 80,
            "rank": 1,
            "proof_evidence_status": (
                "AGENTIC_STRATEGY_PLAN_NOT_PROOF_EVIDENCE"
            ),
            "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
            "ok": True,
            "errors": [],
        }
    ]
    (
        strategy_plan_dir / "formal_verifier_agentic_proof_strategy_plan_manifest.json"
    ).write_text(
        json.dumps(
            {
                "schema_version": 1,
                "n_strategy_rows": len(strategy_rows),
                "n_ready": 1,
                "n_patch_evolve_blocks": 0,
                "n_source_discovery_cache_items": 1,
                "n_kernel_overlay_composition_seeds": 0,
                "n_with_live_tool_plan": 1,
                "all_ok": True,
                "rows": strategy_rows,
                "limitations": [
                    "agentic proof strategy rows are proof-search contracts, not theorem proof evidence"
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        provider_name="anthropic",
        formal_verifier_agentic_proof_strategy_plan_dir=strategy_plan_dir,
    )

    assert payload["all_ok"]
    assert payload["by_request_model_tier"] == {"sonnet": 1}
    assert payload["n_request_model_tier_decision_auto_sonnet_triggered"] == 1
    assert payload["n_request_model_tier_decision_auto_haiku_bounded"] == 0
    packet = payload["request_packets"][0]
    assert packet["model_tier"] == "sonnet"
    assert packet["model"] == "claude-sonnet-4-6"
    evidence = packet["model_tier_decision_evidence"]
    assert evidence["decision_basis"] == "auto_sonnet_triggers"
    assert evidence["route_signal_counts"][
        "agentic_proof_strategy_plan_row_count"
    ] == 1
    assert evidence["route_signal_counts"][
        "agentic_proof_strategy_plan_ready_count"
    ] == 1
    assert evidence["route_signal_counts"][
        "agentic_proof_strategy_plan_source_discovery_cache_item_count"
    ] == 1
    assert evidence["agentic_proof_strategy_plan_counts"]["ready_count"] == 1
    assert any(
        "ready agentic proof-strategy plan" in trigger
        for trigger in evidence["sonnet_triggers"]
    )


def test_llm_route_planner_auto_uses_sonnet_for_pending_source_grounding() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_light_source_grounding_tier"
    )
    out_dir = root / "llm_route_planner"
    source_grounding_dir = root / "source_grounding"
    shutil.rmtree(root, ignore_errors=True)
    source_grounding_dir.mkdir(parents=True, exist_ok=True)
    input_json = _write_light_input(root)
    (
        source_grounding_dir
        / "formalization_gap_planner_source_grounding_audit_manifest.json"
    ).write_text(
        json.dumps(
            {
                "component_name": "formalization_gap_planner_source_grounding_audit",
                "rows": [
                    {
                        "source_grounding_id": "source-grounding:rank-light",
                        "route_id": "rank_route_light",
                        "display_name": "distribution_free_rank_bound_light",
                        "node_source": "literature_route_review",
                        "node_id": "informal:rank_uniformity",
                        "node_kind": "informal_knowledge_dag_node",
                        "node_label": "Rank uniformity source support needs review",
                        "source_refs": [],
                        "source_snippets": [],
                        "residual_goals": [],
                        "residual_primitives": ["rank_uniformity"],
                        "grounding_status": "source_search_pending",
                        "required_next_action": "source_search",
                        "ok": False,
                        "errors": ["rank uniformity source evidence is pending"],
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        provider_name="anthropic",
        formalization_gap_planner_source_grounding_audit_dir=source_grounding_dir,
    )

    assert payload["all_ok"]
    assert payload["by_request_model_tier"] == {"sonnet": 1}
    assert payload["n_request_model_tier_decision_auto_sonnet_triggered"] == 1
    assert payload["n_request_model_tier_decision_auto_haiku_bounded"] == 0
    packet = payload["request_packets"][0]
    assert packet["model_tier"] == "sonnet"
    assert packet["model"] == "claude-sonnet-4-6"
    evidence = packet["model_tier_decision_evidence"]
    assert evidence["decision_basis"] == "auto_sonnet_triggers"
    assert evidence["route_signal_counts"]["source_grounding_unresolved_count"] == 1
    assert evidence["source_grounding_obligations"]["pending"] is True
    assert evidence["source_grounding_obligations"]["unresolved_grounding_statuses"] == [
        "source_search_pending"
    ]
    assert any(
        "pending source-grounding obligation" in trigger
        for trigger in evidence["sonnet_triggers"]
    )


def test_llm_route_planner_auto_uses_sonnet_for_unresolved_light_route_alignment() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_unresolved_light_route_alignment"
    )
    out_dir = root / "llm_route_planner"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_light_input(root)
    input_payload = json.loads(input_json.read_text(encoding="utf-8"))
    input_payload["routes"][0]["primitives"][1]["alignment_status"] = "uncertain"
    input_json.write_text(json.dumps(input_payload, indent=2), encoding="utf-8")
    captured: dict[str, object] = {}

    class FakeAnthropicBackend:
        provider_name = "anthropic"

        def generate(self, request):
            captured["request"] = request
            return GeneratorResponse(
                text=json.dumps(_llm_response_payload()),
                provider="anthropic",
                model=request.model,
                metadata={
                    "generator_only": True,
                    "tools_available": False,
                    "schema_supplied": request.schema is not None,
                },
            )

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        provider_name="anthropic",
        invoke_provider=True,
        generator_backend=FakeAnthropicBackend(),
    )

    assert payload["all_ok"]
    assert payload["by_request_model_tier"] == {"sonnet": 1}
    assert payload["n_request_model_tier_decision_auto_sonnet_triggered"] == 1
    assert payload["n_request_model_tier_decision_auto_haiku_bounded"] == 0
    packet = payload["request_packets"][0]
    assert packet["model_tier"] == "sonnet"
    assert packet["model"] == "claude-sonnet-4-6"
    evidence = packet["model_tier_decision_evidence"]
    assert evidence["decision_basis"] == "auto_sonnet_triggers"
    assert "uncertain" in evidence["coverage_action_markers"]
    assert "uncertain" in evidence["complex_coverage_action_markers"]
    assert any("uncertain" in trigger for trigger in evidence["sonnet_triggers"])
    assert "uncertain" in packet["model_selection_rationale"]
    request = captured["request"]
    assert request.model == "claude-sonnet-4-6"
    assert request.metadata["model_tier"] == "sonnet"


def test_llm_route_planner_auto_uses_sonnet_for_light_route_resource_dispatch() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_light_route_resource_dispatch"
    )
    out_dir = root / "llm_route_planner"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_light_input(root)
    resource_request_queue_dir = _write_resource_request_queue(root)
    manifest_path = (
        resource_request_queue_dir
        / "formalization_gap_planner_resource_request_queue_manifest.json"
    )
    queue_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for row in queue_manifest["rows"]:
        row["route_id"] = "rank_route_light"
        row["display_name"] = "distribution_free_rank_bound_light"
        row["goal_plan_id"] = "goal:rank_route_light"
        row["request_playbook"]["input_summary"]["route_id"] = "rank_route_light"
        row["request_playbook"]["input_summary"][
            "display_name"
        ] = "distribution_free_rank_bound_light"
        row["request_payload"]["route_id"] = "rank_route_light"
        row["request_payload"]["request_playbook"][
            "route_id"
        ] = "rank_route_light"
    manifest_path.write_text(json.dumps(queue_manifest, indent=2), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        provider_name="anthropic",
        formalization_gap_planner_resource_request_queue_dir=(
            resource_request_queue_dir
        ),
    )

    assert payload["all_ok"]
    assert payload["by_request_model_tier"] == {"sonnet": 1}
    assert payload["n_request_model_tier_decision_auto_sonnet_triggered"] == 1
    assert payload["n_request_model_tier_decision_auto_haiku_bounded"] == 0
    assert any(
        "resource-request queue rows" in rule
        for rule in payload["llm_route_planner_model_tier_policy"][
            "auto_tier_rules"
        ]
    )
    packet = payload["request_packets"][0]
    assert packet["model"] == "claude-sonnet-4-6"
    evidence = packet["model_tier_decision_evidence"]
    assert evidence["decision_basis"] == "auto_sonnet_triggers"
    assert evidence["route_signal_counts"]["residual_goal_count"] == 0
    assert evidence["route_signal_counts"]["resource_request_queue_count"] == 1
    assert evidence["route_signal_counts"]["resource_request_playbook_count"] == 1
    assert evidence["context_resource_dispatch_counts"][
        "resource_request_queue_count"
    ] == 1
    assert evidence["context_resource_dispatch_counts"][
        "resource_request_playbook_count"
    ] == 1
    ledger_row = payload["model_tier_decision_ledger"][0]
    assert ledger_row["context_resource_dispatch_counts"][
        "resource_request_queue_count"
    ] == 1
    assert ledger_row["context_resource_dispatch_counts"][
        "resource_request_playbook_count"
    ] == 1
    assert ledger_row["interactive_route_adoption_precondition_counts"][
        "unresolved_count"
    ] == 0
    assert any(
        "pending resource-request queue row" in trigger
        for trigger in evidence["sonnet_triggers"]
    )
    assert any(
        "resource-request playbook" in trigger
        for trigger in evidence["sonnet_triggers"]
    )


def test_llm_route_planner_auto_uses_sonnet_for_light_route_interactive_dispatch() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_light_route_interactive_dispatch"
    )
    out_dir = root / "llm_route_planner"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_light_input(root)
    interactive_session_dir = _write_interactive_session(root)
    manifest_path = (
        interactive_session_dir
        / "formalization_gap_planner_interactive_session_manifest.json"
    )
    session_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for row in session_manifest["rows"]:
        row["route_id"] = "rank_route_light"
        row["display_name"] = "distribution_free_rank_bound_light"
        row["goal_plan_id"] = "goal:rank_route_light"
        row["needs_more_proof_state_feedback"] = False
        row["residual_goals"] = []
    for row in session_manifest["decision_policy_rows"]:
        row["route_id"] = "rank_route_light"
        row["display_name"] = "distribution_free_rank_bound_light"
        row["goal_plan_id"] = "goal:rank_route_light"
        row["trigger_signals"] = ["resource_request_dispatch_pending"]
    manifest_path.write_text(json.dumps(session_manifest, indent=2), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        provider_name="anthropic",
        formalization_gap_planner_interactive_session_dir=interactive_session_dir,
    )

    assert payload["all_ok"]
    assert payload["by_request_model_tier"] == {"sonnet": 1}
    assert payload["n_request_model_tier_decision_auto_sonnet_triggered"] == 1
    assert payload["n_request_model_tier_decision_auto_haiku_bounded"] == 0
    packet = payload["request_packets"][0]
    evidence = packet["model_tier_decision_evidence"]
    assert evidence["decision_basis"] == "auto_sonnet_triggers"
    assert evidence["route_signal_counts"]["residual_goal_count"] == 0
    assert (
        evidence["route_signal_counts"][
            "interactive_session_resource_request_count"
        ]
        == 1
    )
    assert (
        evidence["route_signal_counts"][
            "interactive_session_resource_request_dispatch_summary_count"
        ]
        == 1
    )
    assert evidence["context_resource_dispatch_counts"][
        "interactive_session_resource_request_count"
    ] == 1
    assert any(
        "interactive-session linked resource request" in trigger
        for trigger in evidence["sonnet_triggers"]
    )
    assert any(
        "interactive dispatch summary" in trigger
        for trigger in evidence["sonnet_triggers"]
    )


def test_llm_route_planner_auto_uses_sonnet_for_interactive_execution_commands_only() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_interactive_execution_commands_only"
    )
    out_dir = root / "llm_route_planner"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_light_input(root)
    interactive_session_dir = _write_interactive_session(root)
    manifest_path = (
        interactive_session_dir
        / "formalization_gap_planner_interactive_session_manifest.json"
    )
    session_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for row in session_manifest["rows"]:
        row["route_id"] = "rank_route_light"
        row["display_name"] = "distribution_free_rank_bound_light"
        row["goal_plan_id"] = "goal:rank_route_light"
        row["needs_more_proof_state_feedback"] = False
        row["residual_goals"] = []
        row["resource_request_ids"] = []
        row["resource_request_resource_ids"] = []
        row["resource_request_queue_action_kinds"] = []
        row["resource_request_dispatch_summaries"] = []
        row["resource_request_execution_commands"] = [
            "lean-lsp-mcp goal rank_uniformity"
        ]
    session_manifest["decision_policy_rows"] = []
    manifest_path.write_text(json.dumps(session_manifest, indent=2), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        provider_name="anthropic",
        formalization_gap_planner_interactive_session_dir=interactive_session_dir,
    )

    assert payload["all_ok"]
    assert payload["by_request_model_tier"] == {"sonnet": 1}
    assert payload["n_request_model_tier_decision_auto_sonnet_triggered"] == 1
    packet = payload["request_packets"][0]
    evidence = packet["model_tier_decision_evidence"]
    assert evidence["decision_basis"] == "auto_sonnet_triggers"
    assert (
        evidence["route_signal_counts"][
            "interactive_session_resource_request_count"
        ]
        == 0
    )
    assert (
        evidence["route_signal_counts"][
            "interactive_session_resource_request_dispatch_summary_count"
        ]
        == 0
    )
    assert (
        evidence["route_signal_counts"][
            "interactive_session_resource_request_execution_command_count"
        ]
        == 1
    )
    assert evidence["context_resource_dispatch_counts"][
        "interactive_session_resource_request_execution_command_count"
    ] == 1
    assert any(
        "interactive execution command" in trigger
        for trigger in evidence["sonnet_triggers"]
    )


def test_llm_route_planner_auto_uses_sonnet_for_interactive_formal_attempt_queue() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_interactive_formal_attempt_queue_tier"
    )
    out_dir = root / "llm_route_planner"
    interactive_session_dir = root / "interactive_session"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    interactive_session_dir.mkdir(parents=True, exist_ok=True)
    input_json = _write_light_input(root)
    (
        interactive_session_dir
        / "formalization_gap_planner_interactive_session_manifest.json"
    ).write_text(
        json.dumps(
            {
                "component_name": "formalization_gap_planner_interactive_session",
                "rows": [
                    {
                        "interactive_session_row_id": (
                            "session:rank_route_light_formal_attempt_queue"
                        ),
                        "goal_plan_id": "goal:rank_route_light",
                        "route_id": "rank_route_light",
                        "display_name": "distribution_free_rank_bound_light",
                        "session_state": "EXPAND_TARGET_PROVER_REPLAY",
                        "next_interaction_kind": "target_prover_replay",
                        "next_owner_agent": "formal_verifier",
                        "next_tools": [
                            "formalization_gap_planner_prover_adapter_contract",
                            "target_prover_kernel_replay",
                        ],
                        "formal_attempt_queue_items": [
                            {
                                "attempt_id": "attempt:rank_uniformity",
                                "formal_node_id": "formal:rank_uniformity",
                                "primitive": "rank_uniformity",
                                "target_primitives": ["rank_uniformity"],
                                "target_prover_family": "lean4",
                                "attempt_kind": "kernel_probe",
                                "formal_attempt_dependency_status": (
                                    "ready_no_formal_prerequisites"
                                ),
                                "formal_attempt_initial_ready": True,
                            },
                            {
                                "attempt_id": "attempt:coverage_bridge",
                                "formal_node_id": "formal:coverage_bridge",
                                "primitive": "coverage_bridge",
                                "target_primitives": ["coverage_bridge"],
                                "target_prover_family": "lean4",
                                "attempt_kind": "bridge_lemma",
                                "formal_attempt_dependency_status": (
                                    "waiting_for_formal_prerequisite_attempts"
                                ),
                                "formal_attempt_initial_ready": False,
                            },
                        ],
                        "formal_attempt_queue_item_count": 2,
                        "formal_attempt_queue_ready_item_count": 1,
                        "formal_attempt_queue_blocked_item_count": 1,
                        "formal_attempt_queue_attempt_ids": [
                            "attempt:rank_uniformity",
                            "attempt:coverage_bridge",
                        ],
                        "formal_attempt_queue_ready_attempt_ids": [
                            "attempt:rank_uniformity"
                        ],
                        "formal_attempt_queue_execution_commands": [
                            (
                                "formalization-gap-planner-prover-adapter-contract "
                                "--target-prover-family lean4"
                            ),
                            (
                                "execute formal_attempt_queue item "
                                "formal_attempt_queue_index=0 "
                                "attempt_id=attempt:rank_uniformity "
                                "target_prover_family=lean4"
                            ),
                        ],
                        "needs_more_proof_state_feedback": False,
                        "residual_goals": [],
                        "replan_required": False,
                    }
                ],
                "decision_policy_rows": [],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        provider_name="anthropic",
        formalization_gap_planner_interactive_session_dir=interactive_session_dir,
    )

    assert payload["all_ok"]
    assert payload["by_request_model_tier"] == {"sonnet": 1}
    assert payload["n_request_model_tier_decision_auto_sonnet_triggered"] == 1
    assert payload["n_request_model_tier_decision_auto_haiku_bounded"] == 0
    assert any(
        "formal-attempt queues" in rule
        for rule in payload["llm_route_planner_model_tier_policy"][
            "auto_tier_rules"
        ]
    )
    packet = payload["request_packets"][0]
    evidence = packet["model_tier_decision_evidence"]
    signal_counts = evidence["route_signal_counts"]
    dispatch_counts = evidence["context_resource_dispatch_counts"]
    assert packet["model"] == "claude-sonnet-4-6"
    assert packet["model_tier"] == "sonnet"
    assert evidence["decision_basis"] == "auto_sonnet_triggers"
    assert signal_counts["residual_goal_count"] == 0
    assert signal_counts["interactive_session_resource_request_count"] == 0
    assert signal_counts["interactive_session_formal_attempt_queue_row_count"] == 1
    assert signal_counts["interactive_session_formal_attempt_queue_item_count"] == 2
    assert (
        signal_counts["interactive_session_formal_attempt_queue_ready_item_count"]
        == 1
    )
    assert (
        signal_counts["interactive_session_formal_attempt_queue_blocked_item_count"]
        == 1
    )
    assert (
        signal_counts[
            "interactive_session_formal_attempt_queue_execution_command_count"
        ]
        == 2
    )
    assert dispatch_counts["interactive_session_formal_attempt_queue_item_count"] == 2
    assert any(
        "interactive formal-attempt queue item" in trigger
        for trigger in evidence["sonnet_triggers"]
    )
    assert any(
        "interactive formal-attempt execution command" in trigger
        for trigger in evidence["sonnet_triggers"]
    )
    queue_summary = packet["context_packet"]["feedback_loop_summary"][
        "interactive_session_formal_attempt_queue"
    ]
    inventory = packet["context_packet"]["context_packet_inventory"]
    assert inventory["interactive_session_formal_attempt_queue_row_count"] == 1
    assert inventory["interactive_session_formal_attempt_queue_item_count"] == 2
    assert (
        inventory["interactive_session_formal_attempt_queue_ready_item_count"]
        == 1
    )
    assert (
        inventory["interactive_session_formal_attempt_queue_blocked_item_count"]
        == 1
    )
    assert (
        inventory[
            "interactive_session_formal_attempt_queue_execution_command_count"
        ]
        == 2
    )
    assert queue_summary["item_count"] == 2
    assert queue_summary["ready_item_count"] == 1
    assert queue_summary["blocked_item_count"] == 1
    assert queue_summary["execution_command_count"] == 2
    ledger_row = payload["model_tier_decision_ledger"][0]
    assert ledger_row["context_resource_dispatch_counts"][
        "interactive_session_formal_attempt_queue_execution_command_count"
    ] == 2


def test_llm_route_planner_auto_uses_sonnet_for_formal_attempt_feedback_context() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_formal_attempt_feedback_tier"
    )
    out_dir = root / "llm_route_planner"
    route_replan_handoff_dir = root / "route_replan_handoff"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    route_replan_handoff_dir.mkdir(parents=True, exist_ok=True)
    input_json = _write_light_input(root)
    formal_attempt_context = {
        "attempt_id": "attempt:rank_uniformity_bridge",
        "formal_node_id": "formal:rank_uniformity",
        "formal_attempt_queue_index": 0,
        "formal_attempt_dependency_status": "initial_ready",
        "attempt_kind": "bridge_lemma",
        "primitive": "rank_uniformity",
        "target_primitives": ["rank_uniformity"],
        "target_prover_family": "lean4",
        "prerequisite_formal_node_ids": [],
        "prerequisite_attempt_ids": [],
        "missing_prerequisite_formal_node_ids": [],
        "expected_feedback": ["kernel_status", "residual_goals"],
    }
    (
        route_replan_handoff_dir
        / "formalization_gap_planner_route_replan_handoff_manifest.json"
    ).write_text(
        json.dumps(
            {
                "component_name": "formalization_gap_planner_route_replan_handoff",
                "rows": [
                    {
                        "route_replan_handoff_id": (
                            "handoff:rank_route_formal_attempt_feedback"
                        ),
                        "route_revision_overlay_id": (
                            "overlay:rank_route_formal_attempt_feedback"
                        ),
                        "goal_plan_id": "goal:rank_route_light",
                        "route_id": "rank_route_light",
                        "display_name": "distribution_free_rank_bound_light",
                        "applied_hook_kinds": ["resource_response_ledger"],
                        "applied_resource_response_traces": [
                            {
                                "resource_response_ledger_id": (
                                    "ledger:rank_uniformity_attempt"
                                ),
                                "resource_request_id": (
                                    "request:rank_uniformity_attempt"
                                ),
                                "resource_id": "lean_lsp_mcp",
                                "target_primitives": ["rank_uniformity"],
                                "formal_attempt_context": formal_attempt_context,
                                "residual_goals": [
                                    "rank_uniformity needs a measurability side condition"
                                ],
                                "prover_attempt_status": (
                                    "failed_with_residual_goals"
                                ),
                                "prover_diagnostic_signature": (
                                    "residual_goal:rank_uniformity_measurability"
                                ),
                                "route_revision_recommended": True,
                                "route_revision_reasons": [
                                    (
                                        "formal attempt exposed a rank-uniformity "
                                        "measurability side condition"
                                    )
                                ],
                            }
                        ],
                        "applied_llm_route_planner_hook_traces": [
                            {
                                "llm_route_planner_row_id": (
                                    "llm_route:rank_uniformity_feedback"
                                ),
                                "llm_route_planner_request_id": (
                                    "llm_request:rank_uniformity_feedback"
                                ),
                                "llm_route_planner_hook_kind": (
                                    "formal_attempt_feedback"
                                ),
                                "formal_attempt_context": formal_attempt_context,
                            }
                        ],
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        provider_name="anthropic",
        formalization_gap_planner_route_replan_handoff_dir=(
            route_replan_handoff_dir
        ),
    )

    assert payload["all_ok"]
    assert payload["by_request_model_tier"] == {"sonnet": 1}
    packet = payload["request_packets"][0]
    context = packet["context_packet"]
    formal_feedback = context["formal_attempt_feedback_summary"]
    inventory = context["context_packet_inventory"]
    feedback_summary = context["feedback_loop_summary"]
    evidence = packet["model_tier_decision_evidence"]
    signal_counts = evidence["route_signal_counts"]

    assert packet["model_tier"] == "sonnet"
    assert evidence["decision_basis"] == "auto_sonnet_triggers"
    assert signal_counts["formal_attempt_feedback_context_count"] == 1
    assert signal_counts["formal_attempt_feedback_residual_goal_count"] == 1
    assert signal_counts["formal_attempt_feedback_failed_status_count"] == 1
    assert evidence["formal_attempt_feedback_counts"]["total_count"] == 1
    assert evidence["formal_attempt_feedback_counts"]["residual_goal_count"] == 1
    assert (
        evidence["formal_attempt_feedback_counts"]["failed_status_count"]
        == 1
    )
    assert any(
        "formal-attempt feedback context" in trigger
        for trigger in evidence["sonnet_triggers"]
    )
    assert formal_feedback["attempt_ids"] == ["attempt:rank_uniformity_bridge"]
    assert formal_feedback["formal_node_ids"] == ["formal:rank_uniformity"]
    assert formal_feedback["residual_goal_count"] == 1
    assert formal_feedback["failed_status_count"] == 1
    assert formal_feedback["replan_required"] is True
    assert formal_feedback["contexts"][0]["attempt_id"] == (
        "attempt:rank_uniformity_bridge"
    )
    assert (
        "route_replan_handoff_rows.applied_resource_response_traces"
        in formal_feedback["contexts"][0]["source_fields"]
    )
    assert feedback_summary["formal_attempt_feedback_summary"] == formal_feedback
    assert inventory["formal_attempt_feedback_summary_present"] is True
    assert inventory["formal_attempt_feedback_context_count"] == 1
    assert inventory["formal_attempt_feedback_residual_goal_count"] == 1
    assert inventory["formal_attempt_feedback_failed_status_count"] == 1
    ledger_row = payload["model_tier_decision_ledger"][0]
    assert ledger_row["formal_attempt_feedback_counts"]["total_count"] == 1


def test_llm_route_planner_auto_uses_sonnet_for_light_route_interactive_preconditions() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_light_route_interactive_preconditions"
    )
    out_dir = root / "llm_route_planner"
    interactive_session_dir = root / "interactive_session"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    interactive_session_dir.mkdir(parents=True, exist_ok=True)
    input_json = _write_light_input(root)
    (
        interactive_session_dir
        / "formalization_gap_planner_interactive_session_manifest.json"
    ).write_text(
        json.dumps(
            {
                "component_name": "formalization_gap_planner_interactive_session",
                "rows": [
                    {
                        "interactive_session_row_id": "session:rank_route_light",
                        "goal_plan_id": "goal:rank_route_light",
                        "route_id": "rank_route_light",
                        "display_name": "distribution_free_rank_bound_light",
                        "session_state": "AWAITING_REFINEMENT_RESPONSES",
                        "route_adoption_preconditions": {
                            "precondition_kind": (
                                "formalization_gap_planner_llm_route_planner_route_adoption_preconditions"
                            ),
                            "status": "PENDING_CONTEXT_OBLIGATIONS",
                            "blocked_before_response": True,
                            "known_pre_response_blockers": [
                                ROUTE_ADOPTION_BLOCKER_SOURCE_GROUNDING
                            ],
                            "n_known_pre_response_blockers": 1,
                            "response_required_fields": [
                                "search_requests",
                                "planner_next_actions",
                            ],
                            "n_response_required_fields": 2,
                            "target_primitives": ["rank_uniformity"],
                            "n_target_primitives": 1,
                        },
                        "route_adoption_precondition_present": True,
                        "route_adoption_precondition_blocked_before_response": True,
                        "route_adoption_precondition_unresolved": True,
                        "route_adoption_precondition_known_blockers": [
                            ROUTE_ADOPTION_BLOCKER_SOURCE_GROUNDING
                        ],
                        "route_adoption_precondition_required_response_fields": [
                            "search_requests",
                            "planner_next_actions",
                        ],
                        "route_adoption_precondition_target_primitives": [
                            "rank_uniformity"
                        ],
                        "route_adoption_precondition_known_blocker_count": 1,
                        "route_adoption_precondition_required_response_field_count": 2,
                        "route_adoption_precondition_target_primitive_count": 1,
                    }
                ],
                "decision_policy_rows": [],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        provider_name="anthropic",
        formalization_gap_planner_interactive_session_dir=interactive_session_dir,
    )

    assert payload["all_ok"]
    assert payload["by_request_model_tier"] == {"sonnet": 1}
    assert payload["n_request_model_tier_decision_auto_sonnet_triggered"] == 1
    assert payload["n_request_model_tier_decision_auto_haiku_bounded"] == 0
    packet = payload["request_packets"][0]
    evidence = packet["model_tier_decision_evidence"]
    assert packet["model"] == "claude-sonnet-4-6"
    assert evidence["decision_basis"] == "auto_sonnet_triggers"
    assert any(
        "interactive route-adoption precondition" in trigger
        for trigger in evidence["sonnet_triggers"]
    )
    assert any(
        "interactive route-adoption blocker" in trigger
        for trigger in evidence["sonnet_triggers"]
    )
    assert evidence["route_signal_counts"][
        "interactive_unresolved_route_adoption_precondition_count"
    ] == 1
    assert evidence["route_signal_counts"][
        "interactive_route_adoption_precondition_known_blocker_count"
    ] == 1
    assert evidence["interactive_route_adoption_precondition_counts"][
        "required_response_field_count"
    ] == 2
    assert evidence["interactive_route_adoption_precondition_counts"][
        "target_primitive_count"
    ] == 1
    ledger_row = payload["model_tier_decision_ledger"][0]
    assert ledger_row["interactive_route_adoption_precondition_counts"][
        "unresolved_count"
    ] == 1
    assert ledger_row["interactive_route_adoption_precondition_counts"][
        "known_blocker_count"
    ] == 1
    assert ledger_row["interactive_route_adoption_precondition_counts"][
        "target_primitive_count"
    ] == 1
    assert evidence["route_signal_counts"][
        "interactive_route_adoption_precondition_target_primitive_count"
    ] == 1
    assert ledger_row["context_resource_dispatch_counts"][
        "resource_request_queue_count"
    ] == 0
    context = packet["context_packet"]
    assert context["feedback_loop_summary"][
        "interactive_route_adoption_preconditions"
    ]["unresolved_count"] == 1
    assert context["context_packet_inventory"][
        "interactive_unresolved_route_adoption_precondition_count"
    ] == 1


def test_llm_route_planner_escalates_failed_haiku_repair_to_sonnet() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_haiku_sonnet_repair"
    )
    out_dir = root / "llm_route_planner"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_light_input(root)
    requests = []

    class RepairingFakeAnthropicBackend:
        provider_name = "anthropic"

        def generate(self, request):
            requests.append(request)
            if len(requests) == 1:
                return GeneratorResponse(
                    text=json.dumps(
                        {
                            "kernel_verified": True,
                            "informal_knowledge_dag_nodes": [],
                        }
                    ),
                    provider="anthropic",
                    model=request.model,
                    metadata={"generator_only": True, "tools_available": False},
                )
            return GeneratorResponse(
                text=json.dumps(_llm_response_payload()),
                provider="anthropic",
                model=request.model,
                metadata={"generator_only": True, "tools_available": False},
            )

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        provider_name="anthropic",
        invoke_provider=True,
        generator_backend=RepairingFakeAnthropicBackend(),
        max_repair_attempts=1,
    )

    assert payload["all_ok"]
    assert payload["by_request_model_tier"] == {"haiku": 1}
    assert payload["n_generated_responses_model_tier_escalated"] == 1
    assert payload["n_generated_responses_haiku_to_sonnet_escalated"] == 1
    assert payload["n_repair_attempt_ledger_model_tier_escalations"] == 1
    assert payload["n_rows_with_model_tier_escalation"] == 1
    assert payload["n_request_model_tier_decision_auto_haiku_bounded"] == 1
    assert len(requests) == 2
    assert requests[0].model == "claude-haiku-4-5-20251001"
    assert requests[0].metadata["model_tier"] == "haiku"
    assert requests[0].metadata["model_tier_escalated"] is False
    assert requests[1].model == "claude-sonnet-4-6"
    assert requests[1].metadata["requested_model_tier"] == "haiku"
    assert requests[1].metadata["model_tier"] == "sonnet"
    assert requests[1].metadata["model_tier_escalated"] is True
    row = payload["rows"][0]
    assert row["model"] == "claude-sonnet-4-6"
    assert row["model_tier"] == "sonnet"
    assert row["generator_metadata"]["requested_model_tier"] == "haiku"
    assert row["generator_metadata"]["effective_model_tier"] == "sonnet"
    assert row["generator_metadata"]["model_tier_escalated"] is True
    assert row["model_tier_decision_evidence"]["selected_model_tier"] == "haiku"
    assert row["model_tier_decision_evidence"]["effective_model_tier"] == "sonnet"
    assert row["model_tier_decision_evidence"]["model_tier_escalated"] is True
    assert "auto escalated Claude Haiku repair attempt to Sonnet" in row[
        "model_selection_rationale"
    ]
    tier_ledger_row = payload["model_tier_decision_ledger"][0]
    assert tier_ledger_row["operator_requested_model_tier"] == "auto"
    assert tier_ledger_row["selected_model_tier"] == "haiku"
    assert tier_ledger_row["effective_model_tier"] == "sonnet"
    assert tier_ledger_row["request_model"] == "claude-haiku-4-5-20251001"
    assert tier_ledger_row["effective_model"] == "claude-sonnet-4-6"
    assert tier_ledger_row["model_tier_escalated"] is True
    assert "Haiku repair attempt to Sonnet" in tier_ledger_row[
        "model_tier_escalation_reason"
    ]
    assert payload["n_model_tier_decision_ledger_rows_with_escalation"] == 1
    assert row["repair_error_history"][0]["model_tier"] == "haiku"
    assert row["repair_error_history"][0]["next_repair_model_tier"] == "sonnet"
    repair_ledger_row = row["repair_attempt_ledger"][0]
    assert repair_ledger_row["requested_model_tier"] == "haiku"
    assert repair_ledger_row["model_tier"] == "sonnet"
    assert repair_ledger_row["failed_attempt_model_tier"] == "haiku"
    assert repair_ledger_row["next_repair_model_tier"] == "sonnet"
    assert repair_ledger_row["model_tier_escalated"] is True
    seed_metadata = payload["standalone_seed"]["routes"][0]["replan_metadata"]
    assert seed_metadata["llm_route_planner_model"] == "claude-sonnet-4-6"
    assert seed_metadata["llm_route_planner_model_tier"] == "sonnet"


def test_llm_route_planner_auto_uses_sonnet_for_seed_route_risk_markers() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_seed_risk_tier"
    )
    out_dir = root / "llm_route_planner"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_light_input(root)
    payload = json.loads(input_json.read_text(encoding="utf-8"))
    route = payload["routes"][0]
    route["uncertainty_flags"] = [
        "finite tie-breaking assumption needs review",
    ]
    route["semantic_alignment_risks"] = [
        "rank convention may weaken the theorem statement",
    ]
    route["primitives"][1]["formal_gap_boundary"] = (
        "The finite-rank bridge needs a deterministic tie-handling side "
        "condition before target-prover replay."
    )
    route["primitives"][1]["source_search_status"] = "source_search_pending"
    input_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    planner_payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
    )

    assert planner_payload["all_ok"]
    assert planner_payload["by_request_model_tier"] == {"sonnet": 1}
    packet = planner_payload["request_packets"][0]
    assert packet["model_tier"] == "sonnet"
    assert packet["model"] == "claude-sonnet-4-6"
    rationale = packet["model_selection_rationale"]
    assert "seed route uncertainty flag(s)" in rationale
    assert "seed route semantic alignment risk(s)" in rationale
    assert "seed route formal-gap boundary marker(s)" in rationale
    assert "seed route source-search status requires route synthesis" in rationale


def test_llm_route_planner_generator_model_fallback_preserves_selected_tier() -> None:
    class FakeAnthropicBackend:
        provider_name = "anthropic"

    backend = FakeAnthropicBackend()

    assert (
        _generator_model_for_request(backend, "", model_tier="haiku")
        == "claude-haiku-4-5-20251001"
    )
    assert (
        _generator_model_for_request(backend, "", model_tier="sonnet")
        == "claude-sonnet-4-6"
    )
    assert (
        _generator_model_for_request(
            backend,
            "claude-haiku-custom",
            model_tier="sonnet",
        )
        == "claude-haiku-custom"
    )


def test_llm_route_planner_auto_uses_sonnet_for_generic_formal_library_queries() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_generic_formal_queries"
    )
    out_dir = root / "llm_route_planner"
    target_intake_dir = root / "target_intake"
    shutil.rmtree(root, ignore_errors=True)
    target_intake_dir.mkdir(parents=True, exist_ok=True)
    input_json = _write_light_input(root)
    target_intake_manifest = {
        "component_name": "formalization_gap_planner_target_intake",
        "rows": [
            {
                "schema_version": 1,
                "target_intake_id": "target-intake:generic-formal-queries",
                "target_id": "generic_formal_queries",
                "display_name": "generic formal query load",
                "domain": "portable_prover_test",
                "target_prover_family": "rocq",
                "library_snapshot_ref": "rocq_snapshot",
                "theorem_statement": "A small rank fact follows from reuse.",
                "theorem_skeleton": "",
                "normalized_objects": ["rank statistic"],
                "normalized_assumptions": ["exchangeability"],
                "normalized_procedure": "",
                "normalized_claim": "rank reuse",
                "desired_theorem_shape": "finite_sample_rank_coverage",
                "proof_source_refs": ["conformal_prediction_textbook"],
                "primitive_seed_rows": [
                    {"primitive": "rank_uniformity", "coverage_status": "near_exists"}
                ],
                "extracted_primitive_candidates": ["rank_uniformity"],
                "background_primitives": [],
                "standalone_route_id": "rank_route_light",
                "literature_queries": ["rank reuse route"],
                "formal_library_grounding_queries": [
                    f"formal query {idx}" for idx in range(9)
                ],
                "lean_grounding_queries": [],
                "proof_state_probe_required": False,
                "missing_required_fields": [],
                "review_flags": [],
                "proof_evidence_status": (
                    "FORMALIZATION_GAP_PLANNER_TARGET_INTAKE_NOT_PROOF_EVIDENCE"
                ),
                "proof_evidence_boundary": "target intake is not theorem proof evidence",
                "ok": True,
                "errors": [],
            }
        ],
    }
    (
        target_intake_dir / "formalization_gap_planner_target_intake_manifest.json"
    ).write_text(json.dumps(target_intake_manifest, indent=2), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        formalization_gap_planner_target_intake_dir=target_intake_dir,
    )

    assert payload["all_ok"]
    assert payload["by_request_model_tier"] == {"sonnet": 1}
    packet = payload["request_packets"][0]
    assert packet["model_tier"] == "sonnet"
    assert packet["model"] == "claude-sonnet-4-6"
    assert "formal-library grounding query(s)" in packet["model_selection_rationale"]
    intake_row = packet["context_packet"]["target_intake_rows"][0]
    assert len(intake_row["formal_library_grounding_queries"]) == 9
    assert "lean_grounding_queries" not in intake_row


def test_llm_route_planner_rejects_provider_returned_model_tier_mismatch() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_returned_model_tier_mismatch"
    )
    out_dir = root / "llm_route_planner"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_light_input(root)
    captured: dict[str, object] = {}

    class FakeAnthropicBackend:
        provider_name = "anthropic"

        def generate(self, request):
            captured["request"] = request
            return GeneratorResponse(
                text=json.dumps(_llm_response_payload()),
                provider="anthropic",
                model="claude-sonnet-4-6",
                metadata={
                    "generator_only": True,
                    "tools_available": False,
                    "schema_supplied": request.schema is not None,
                    "returned_model_overrode_request": True,
                },
            )

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        provider_name="anthropic",
        invoke_provider=True,
        generator_backend=FakeAnthropicBackend(),
    )

    request = captured["request"]
    assert request.model == "claude-haiku-4-5-20251001"
    assert request.metadata["model_tier"] == "haiku"
    assert not payload["all_ok"]
    assert payload["by_request_model_tier"] == {"haiku": 1}
    assert payload["n_rejected"] == 1
    assert payload["n_response_contract_ok"] == 0
    assert payload["n_response_model_tier_mismatches"] == 1
    response_mismatch = payload["response_model_tier_mismatches"][0]
    assert response_mismatch["provider_name"] == "anthropic"
    assert response_mismatch["model"] == "claude-sonnet-4-6"
    assert response_mismatch["model_tier"] == "haiku"
    assert response_mismatch["response_present"] is True
    assert response_mismatch["acceptance_status"] == (
        "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    )
    assert "expected Claude haiku tier" in response_mismatch["error"]
    assert payload["n_row_schema_invalid"] == 1
    row = payload["rows"][0]
    assert row["model_tier"] == "haiku"
    assert row["model"] == "claude-sonnet-4-6"
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    assert any("expected Claude haiku tier" in error for error in row["errors"])


def test_llm_route_planner_rejects_anthropic_explicit_model_tier_mismatch() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_model_tier_mismatch"
    )
    out_dir = root / "llm_route_planner"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_light_input(root)

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        provider_name="anthropic",
        model="claude-sonnet-4-6",
        model_tier="haiku",
    )

    assert not payload["all_ok"]
    assert payload["by_request_model_tier"] == {"haiku": 1}
    assert payload["n_request_model_tier_mismatches"] == 1
    assert payload["n_request_schema_invalid"] == 1
    mismatch = payload["request_model_tier_mismatches"][0]
    assert mismatch["provider_name"] == "anthropic"
    assert mismatch["model"] == "claude-sonnet-4-6"
    assert mismatch["model_tier"] == "haiku"
    assert "expected Claude haiku tier" in mismatch["error"]
    packet = payload["request_packets"][0]
    assert packet["model"] == "claude-sonnet-4-6"
    assert packet["model_tier"] == "haiku"
    row = payload["rows"][0]
    assert row["ok"] is False
    assert row["response_present"] is False
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_REQUEST_CONTRACT"
    assert any("expected Claude haiku tier" in error for error in row["errors"])


def test_llm_route_planner_preflight_blocks_live_provider_on_model_tier_mismatch() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_preflight_tier_block"
    )
    out_dir = root / "llm_route_planner"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_light_input(root)
    calls: list[object] = []

    class ShouldNotCallAnthropicBackend:
        provider_name = "anthropic"

        def generate(self, request):
            calls.append(request)
            raise AssertionError("preflight-invalid request should not call provider")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        provider_name="anthropic",
        model="claude-sonnet-4-6",
        model_tier="haiku",
        invoke_provider=True,
        generator_backend=ShouldNotCallAnthropicBackend(),
    )

    assert calls == []
    assert not payload["all_ok"]
    assert payload["invoke_provider"] is True
    assert payload["n_generation_preflight_blocked"] == 1
    assert payload["n_raw_responses"] == 0
    assert payload["n_awaiting_llm_response"] == 0
    assert payload["n_rejected"] == 1
    assert payload["n_route_adoption_rejected"] == 1
    preflight_error = payload["generation_preflight_errors"][0]
    assert preflight_error["model"] == "claude-sonnet-4-6"
    assert preflight_error["model_tier"] == "haiku"
    assert any(
        "expected Claude haiku tier" in error
        for error in preflight_error["errors"]
    )
    report = (
        out_dir / "formalization_gap_planner_llm_route_planner.md"
    ).read_text(encoding="utf-8")
    assert "- Generation preflight blocks: 1" in report
    row = payload["rows"][0]
    assert row["provider_failure"] is False
    assert row["response_present"] is False
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_REQUEST_CONTRACT"
    assert row["route_adoption_status"] == "REJECTED_LLM_ROUTE_PLAN"
    assert "response_not_accepted" in row["route_adoption_blockers"]
    seed_route = payload["standalone_seed"]["routes"][0]
    seed_metadata = seed_route["replan_metadata"]
    assert seed_route["llm_route_planner_acceptance_status"] == (
        "REJECTED_LLM_ROUTE_PLANNER_REQUEST_CONTRACT"
    )
    assert seed_route["llm_route_planner_route_adoption_status"] == (
        "REJECTED_LLM_ROUTE_PLAN"
    )
    assert seed_metadata["llm_route_planner_request_contract_blocked"] is True
    assert any(
        "expected Claude haiku tier" in error
        for error in seed_metadata["llm_route_planner_errors"]
    )

    plan_payload = export_formalization_gap_planner_standalone_plan(
        out_dir / "formalization_gap_planner_llm_route_planner_standalone_seed.json",
        root / "standalone_plan",
    )
    assert plan_payload[
        "n_standalone_input_traces_with_llm_route_planner_metadata"
    ] == 1
    assert plan_payload[
        "n_standalone_input_traces_with_llm_request_contract_blocked"
    ] == 1
    plan_trace = plan_payload["rows"][0]["standalone_input_trace"]
    assert plan_trace["llm_route_planner_request_contract_blocked"] is True
    assert plan_trace["llm_route_planner_route_adoption_status"] == (
        "REJECTED_LLM_ROUTE_PLAN"
    )


def test_llm_route_planner_preflight_blocks_live_provider_on_stale_claude_model() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_preflight_stale_model"
    )
    out_dir = root / "llm_route_planner"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_light_input(root)
    calls: list[object] = []

    class ShouldNotCallAnthropicBackend:
        provider_name = "anthropic"

        def generate(self, request):
            calls.append(request)
            raise AssertionError("stale Claude request should not call provider")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        provider_name="anthropic",
        model="claude-sonnet-4-5",
        model_tier="sonnet",
        invoke_provider=True,
        generator_backend=ShouldNotCallAnthropicBackend(),
    )

    assert calls == []
    assert not payload["all_ok"]
    assert payload["by_request_model_tier"] == {"sonnet": 1}
    assert payload["n_request_model_tier_mismatches"] == 0
    assert payload["n_request_model_freshness_warnings"] == 1
    freshness_warning = payload["request_model_freshness_warnings"][0]
    assert freshness_warning["provider_name"] == "anthropic"
    assert freshness_warning["model"] == "claude-sonnet-4-5"
    assert freshness_warning["model_tier"] == "sonnet"
    assert "current source-checked API ID is claude-sonnet-4-6" in (
        freshness_warning["warning"]
    )
    assert payload["n_request_schema_invalid"] == 1
    assert payload["n_generation_preflight_blocked"] == 1
    assert payload["n_raw_responses"] == 0
    assert payload["n_rejected"] == 1
    preflight_error = payload["generation_preflight_errors"][0]
    assert preflight_error["model"] == "claude-sonnet-4-5"
    assert preflight_error["model_tier"] == "sonnet"
    assert any(
        "current source-checked API ID is claude-sonnet-4-6" in error
        for error in preflight_error["errors"]
    )
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_REQUEST_CONTRACT"
    assert row["provider_failure"] is False
    assert row["response_present"] is False
    assert any(
        "current source-checked API ID is claude-sonnet-4-6" in error
        for error in row["errors"]
    )
    report = (
        out_dir / "formalization_gap_planner_llm_route_planner.md"
    ).read_text(encoding="utf-8")
    assert "- Request model freshness warnings: 1" in report


def test_llm_route_planner_preflight_blocks_live_provider_on_prompt_budget_cap() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_preflight_budget_block"
    )
    out_dir = root / "llm_route_planner"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_light_input(root)
    calls: list[object] = []

    class ShouldNotCallAnthropicBackend:
        provider_name = "anthropic"

        def generate(self, request):
            calls.append(request)
            raise AssertionError("budget-blocked request should not call provider")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        provider_name="anthropic",
        model_tier="sonnet",
        invoke_provider=True,
        generator_backend=ShouldNotCallAnthropicBackend(),
        max_estimated_prompt_input_tokens=1,
    )

    assert calls == []
    assert not payload["all_ok"]
    assert payload["invoke_provider"] is True
    assert payload["max_estimated_prompt_input_tokens"] == 1
    assert payload["n_prompt_token_budget_preflight_blocked"] == 1
    assert payload["n_generation_preflight_blocked"] == 1
    assert payload["n_raw_responses"] == 0
    assert payload["n_awaiting_llm_response"] == 0
    assert payload["n_rejected"] == 1
    assert payload["n_route_adoption_rejected"] == 1
    prompt_budget_error = payload["prompt_token_budget_preflight_errors"][0]
    assert prompt_budget_error["max_estimated_prompt_input_tokens"] == 1
    assert prompt_budget_error["estimated_input_tokens"] > 1
    assert any(
        "estimated prompt input tokens" in error
        for error in prompt_budget_error["errors"]
    )
    generation_preflight_error = payload["generation_preflight_errors"][0]
    assert generation_preflight_error["request_id"] == prompt_budget_error[
        "request_id"
    ]
    assert any(
        "estimated prompt input tokens" in error
        for error in generation_preflight_error["errors"]
    )
    row = payload["rows"][0]
    assert row["provider_failure"] is False
    assert row["response_present"] is False
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_REQUEST_CONTRACT"
    assert row["route_adoption_status"] == "REJECTED_LLM_ROUTE_PLAN"
    assert any("estimated prompt input tokens" in error for error in row["errors"])
    seed_metadata = payload["standalone_seed"]["routes"][0]["replan_metadata"]
    assert seed_metadata["llm_route_planner_request_contract_blocked"] is True
    assert any(
        "estimated prompt input tokens" in error
        for error in seed_metadata["llm_route_planner_errors"]
    )
    report = (
        out_dir / "formalization_gap_planner_llm_route_planner.md"
    ).read_text(encoding="utf-8")
    assert "- Prompt token budget preflight blocks: 1 cap=1" in report
    assert "- Generation preflight blocks: 1" in report
    assert validate_llm_route_planner_manifest(payload) == []


def test_llm_route_planner_rejects_outside_cost_tier_model_for_tier_request() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_outside_tier_model"
    )
    out_dir = root / "llm_route_planner"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_light_input(root)

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        provider_name="anthropic",
        model="claude-fable-5",
        model_tier="sonnet",
    )

    assert not payload["all_ok"]
    assert payload["by_request_model_tier"] == {"sonnet": 1}
    assert payload["n_request_model_tier_mismatches"] == 1
    mismatch = payload["request_model_tier_mismatches"][0]
    assert mismatch["model"] == "claude-fable-5"
    assert mismatch["model_tier"] == "sonnet"
    assert "outside-tier Claude fable model" in mismatch["error"]
    packet = payload["request_packets"][0]
    assert packet["model"] == "claude-fable-5"
    assert packet["model_tier"] == "sonnet"
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_REQUEST_CONTRACT"
    assert any("outside-tier Claude fable model" in error for error in row["errors"])


def test_llm_route_planner_auto_uses_sonnet_for_incomplete_realization_feedback() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_realization_tier_fake"
    )
    out_dir = root / "llm_route_planner"
    plan_dir = root / "goal_plan"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_light_input(root)
    input_payload = json.loads(input_json.read_text(encoding="utf-8"))
    input_payload["routes"][0]["realization_coverage_witness"] = {
        "selected_primitives": ["exchangeability", "rank_uniformity"],
        "delta_primitives": ["rank_uniformity"],
        "introduced_primitives": [],
        "aligned_primitives": ["exchangeability"],
        "selected_primitives_missing_formal_realization_node": [
            "rank_uniformity"
        ],
        "delta_primitives_missing_route_alignment_edge": ["rank_uniformity"],
        "introduced_primitives_missing_route_alignment_edge": [],
        "realization_coverage_complete": False,
    }
    input_json.write_text(json.dumps(input_payload, indent=2), encoding="utf-8")
    export_formalization_gap_planner_standalone_plan(input_json, plan_dir)
    captured: dict[str, object] = {}

    class FakeAnthropicBackend:
        provider_name = "anthropic"

        def generate(self, request):
            captured["request"] = request
            return GeneratorResponse(
                text=json.dumps(_llm_response_payload()),
                provider="anthropic",
                model=request.model,
                metadata={
                    "generator_only": True,
                    "tools_available": False,
                    "schema_supplied": request.schema is not None,
                },
            )

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        provider_name="anthropic",
        invoke_provider=True,
        generator_backend=FakeAnthropicBackend(),
        goal_conditioned_minimal_formalization_plan_dir=plan_dir,
    )

    assert payload["all_ok"]
    assert payload["by_request_model_tier"] == {"sonnet": 1}
    assert payload["n_feedback_loop_summary_incomplete_realization_coverage"] == 1
    packet = payload["request_packets"][0]
    assert packet["model_tier"] == "sonnet"
    assert packet["model"] == "claude-sonnet-4-6"
    assert "incomplete realization-coverage witness" in packet[
        "model_selection_rationale"
    ]
    request = captured["request"]
    assert request.model == "claude-sonnet-4-6"
    assert request.metadata["model_tier"] == "sonnet"


def test_llm_route_planner_repairs_invalid_provider_response_with_local_validator_feedback() -> None:
    root = Path("runs/test_formalization_gap_planner_llm_route_planner_repair_fake")
    out_dir = root / "llm_route_planner"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    requests = []

    class RepairingFakeAnthropicBackend:
        provider_name = "anthropic"

        def generate(self, request):
            requests.append(request)
            if len(requests) == 1:
                return GeneratorResponse(
                    text=json.dumps(
                        {
                            "kernel_verified": True,
                            "informal_knowledge_dag_nodes": [],
                        }
                    ),
                    provider="anthropic",
                    model=request.model,
                    metadata={"generator_only": True, "tools_available": False},
                )
            return GeneratorResponse(
                text=json.dumps(_llm_response_payload()),
                provider="anthropic",
                model=request.model,
                metadata={"generator_only": True, "tools_available": False},
            )

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        provider_name="anthropic",
        invoke_provider=True,
        generator_backend=RepairingFakeAnthropicBackend(),
        max_repair_attempts=1,
    )

    assert payload["all_ok"]
    assert payload["n_raw_responses"] == 1
    assert payload["n_generated_response_repair_attempts"] == 1
    assert payload["n_generated_responses_repaired"] == 1
    assert payload["n_repair_attempt_ledger_rows"] == 1
    assert payload["n_requests_with_repair_attempt_ledger"] == 1
    assert payload["n_repair_attempt_ledger_error_items"] >= 1
    assert payload["n_response_contract_ok"] == 1
    assert payload["n_accepted_route_plans"] == 1
    assert len(requests) == 2
    assert requests[0].metadata["repair_attempt"] == 0
    assert requests[1].metadata["repair_attempt"] == 1
    assert "Repair your previous formalization-gap planner response" in requests[1].user_prompt
    assert "repair_guidance_rows" in requests[1].user_prompt
    assert "proof_boundary_violation" in requests[1].user_prompt
    assert "kernel_verified" in requests[1].user_prompt
    raw_response = payload["request_packets"][0]
    assert raw_response["model_tier"] == "sonnet"
    row = payload["rows"][0]
    assert row["acceptance_status"] == "ACCEPTED_WITH_SEARCH_REQUESTS"
    assert row["repair_attempts"] == 1
    assert row["repair_error_history"]
    assert row["repair_error_history"][0]["next_repair_attempt"] == 1
    assert row["repair_error_history"][0]["repair_prompt_fingerprint"]
    assert "proof_boundary_violation" in row["repair_error_history"][0][
        "repair_guidance_categories"
    ]
    assert row["repair_error_history"][0]["repair_guidance_fingerprint"]
    assert any("kernel_verified" in " ".join(item["errors"]) for item in row["repair_error_history"])
    assert row["repair_attempt_ledger"] == payload["repair_attempt_ledger"]
    repair_ledger_row = row["repair_attempt_ledger"][0]
    assert repair_ledger_row["ledger_kind"] == (
        "formalization_gap_planner_llm_route_planner_repair_attempt_ledger"
    )
    assert repair_ledger_row["request_id"] == row["request_id"]
    assert repair_ledger_row["failed_attempt_index"] == 0
    assert repair_ledger_row["next_repair_attempt"] == 1
    assert repair_ledger_row["final_repair_attempts"] == 1
    assert repair_ledger_row["final_response_contract_ok"] is True
    assert repair_ledger_row["final_acceptance_status"] == (
        "ACCEPTED_WITH_SEARCH_REQUESTS"
    )
    assert repair_ledger_row["repair_prompt_fingerprint"] == (
        row["repair_error_history"][0]["repair_prompt_fingerprint"]
    )
    assert "proof_boundary_violation" in repair_ledger_row[
        "repair_guidance_categories"
    ]
    assert repair_ledger_row["repair_guidance_fingerprint"] == (
        row["repair_error_history"][0]["repair_guidance_fingerprint"]
    )
    assert any("kernel_verified" in error for error in repair_ledger_row["errors"])
    drifted_row = deepcopy(row)
    drifted_row["repair_attempt_ledger"][0]["error_count"] = 0
    assert (
        "repair_attempt_ledger[0].error_count must match errors"
        in validate_llm_route_planner_row(drifted_row)
    )
    drifted_guidance_row = deepcopy(row)
    drifted_guidance_row["repair_attempt_ledger"][0][
        "repair_guidance_categories"
    ] = []
    assert (
        "repair_attempt_ledger[0].repair_guidance_categories must match "
        "repair_error_history"
        in validate_llm_route_planner_row(drifted_guidance_row)
    )
    assert not row["generation_errors"]
    manifest = json.loads(
        (
            out_dir / "formalization_gap_planner_llm_route_planner_manifest.json"
        ).read_text(encoding="utf-8")
    )
    generated = manifest["request_packets"][0]
    assert generated["model_tier"] == "sonnet"
    assert manifest["n_repair_attempt_ledger_rows"] == 1
    assert manifest["n_requests_with_repair_attempt_ledger"] == 1
    assert manifest["repair_attempt_ledger"][0] == manifest["rows"][0][
        "repair_attempt_ledger"
    ][0]
    manifest_row = manifest["rows"][0]
    assert manifest_row["repair_attempts"] == 1
    assert manifest_row["generation_errors"] == []
    manifest["repair_attempt_ledger"] = []
    assert (
        "repair_attempt_ledger must match row repair_attempt_ledger"
        in validate_llm_route_planner_manifest(manifest)
    )
    report = (
        out_dir / "formalization_gap_planner_llm_route_planner.md"
    ).read_text(encoding="utf-8")
    assert "- Repair ledger rows: 1" in report


def test_llm_route_planner_repair_guidance_dispatches_agentic_strategy_obligations() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_agentic_strategy_repair"
    )
    out_dir = root / "llm_route_planner"
    strategy_plan_dir = root / "agentic_strategy_plan"
    shutil.rmtree(root, ignore_errors=True)
    strategy_plan_dir.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    strategy_rows = [
        {
            "schema_version": 1,
            "strategy_id": "strategy:rank_route:tie-source",
            "followup_id": "followup:rank_route:tie-source",
            "residual_response_validation_id": "validation:rank_route:tie-source",
            "prompt_packet_id": "packet:rank_route:tie-source",
            "residual_obligation_id": "residual-obligation:rank_route:tie-source",
            "route_id": "rank_route",
            "display_name": "distribution_free_rank_bound",
            "target_theorem_name": "distribution_free_rank_bound",
            "candidate_bridge_lemma_name": "calibration_quantile_tie_policy_bridge",
            "residual_gap": "calibration_quantile_tie_policy",
            "action_class": "source_discovery_needed",
            "followup_kind": "residual_source_discovery",
            "followup_status": "READY_FOR_AGENTIC_PROOF_STRATEGY",
            "agentic_strategy_kind": "global_goal_cache_source_discovery",
            "paper_patterns": ["calibration quantile tie policy"],
            "required_live_tools": ["paperclip", "paperqa"],
            "evaluator_gates": ["source-backed residual route repair"],
            "global_goal_cache_keys": [
                "calibration_quantile_tie_policy:rank_route"
            ],
            "candidate_database_key": "candidate-db:rank_route:tie-source",
            "expected_artifacts": [
                "source_cache/calibration_quantile_tie_policy.json"
            ],
            "priority_score": 90,
            "rank": 1,
            "proof_evidence_status": (
                "AGENTIC_STRATEGY_PLAN_NOT_PROOF_EVIDENCE"
            ),
            "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
            "ok": True,
            "errors": [],
        }
    ]
    (
        strategy_plan_dir / "formal_verifier_agentic_proof_strategy_plan_manifest.json"
    ).write_text(
        json.dumps(
            {
                "schema_version": 1,
                "n_strategy_rows": len(strategy_rows),
                "n_ready": 1,
                "n_patch_evolve_blocks": 0,
                "n_source_discovery_cache_items": 1,
                "n_kernel_overlay_composition_seeds": 0,
                "n_with_live_tool_plan": 1,
                "all_ok": True,
                "rows": strategy_rows,
                "limitations": [
                    "agentic proof strategy rows are proof-search contracts, not theorem proof evidence"
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    repaired_response = _llm_response_payload()
    repaired_response["search_requests"] = [
        *repaired_response["search_requests"],
        {
            "request_kind": "source_search",
            "query": (
                "source search for calibration_quantile_tie_policy "
                "strategy:rank_route:tie-source"
            ),
            "reason": (
                "answer ready agentic proof strategy row "
                "strategy:rank_route:tie-source before route repair"
            ),
            "strategy_id": "strategy:rank_route:tie-source",
            "residual_obligation_id": "residual-obligation:rank_route:tie-source",
            "agentic_strategy_kind": "global_goal_cache_source_discovery",
        },
    ]
    requests = []

    class RepairingFakeAnthropicBackend:
        provider_name = "anthropic"

        def generate(self, request):
            requests.append(request)
            if len(requests) == 1:
                return GeneratorResponse(
                    text=json.dumps(_llm_response_payload()),
                    provider="anthropic",
                    model=request.model,
                    metadata={"generator_only": True, "tools_available": False},
                )
            return GeneratorResponse(
                text=json.dumps(repaired_response),
                provider="anthropic",
                model=request.model,
                metadata={"generator_only": True, "tools_available": False},
            )

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        provider_name="anthropic",
        invoke_provider=True,
        generator_backend=RepairingFakeAnthropicBackend(),
        formal_verifier_agentic_proof_strategy_plan_dir=strategy_plan_dir,
        max_repair_attempts=1,
    )

    assert payload["all_ok"]
    assert payload["n_generated_response_repair_attempts"] == 1
    assert payload["n_generated_responses_repaired"] == 1
    assert len(requests) == 2
    assert "agentic_strategy_obligation" in requests[1].user_prompt
    assert (
        "context_packet.formal_verifier_agentic_proof_strategy_plan_rows"
        in requests[1].user_prompt
    )
    assert "strategy:rank_route:tie-source" in requests[1].user_prompt
    row = payload["rows"][0]
    assert row["repair_attempts"] == 1
    assert row["repair_error_history"]
    assert "agentic_strategy_obligation" in row["repair_error_history"][0][
        "repair_guidance_categories"
    ]
    assert any(
        "agentic proof strategy plan ready row" in error
        for error in row["repair_error_history"][0]["errors"]
    )
    repair_ledger_row = payload["repair_attempt_ledger"][0]
    assert "agentic_strategy_obligation" in repair_ledger_row[
        "repair_guidance_categories"
    ]
    assert not row["generation_errors"]


def test_llm_route_planner_repairs_primitive_matrix_accountability_failure() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_matrix_repair_fake"
    )
    out_dir = root / "llm_route_planner"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    requests = []

    class RepairingFakeAnthropicBackend:
        provider_name = "anthropic"

        def generate(self, request):
            requests.append(request)
            if len(requests) == 1:
                return GeneratorResponse(
                    text=json.dumps(_drop_source_snippets(_llm_response_payload())),
                    provider="anthropic",
                    model=request.model,
                    metadata={"generator_only": True, "tools_available": False},
                )
            return GeneratorResponse(
                text=json.dumps(_llm_response_payload()),
                provider="anthropic",
                model=request.model,
                metadata={"generator_only": True, "tools_available": False},
            )

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        provider_name="anthropic",
        invoke_provider=True,
        generator_backend=RepairingFakeAnthropicBackend(),
        max_repair_attempts=1,
    )

    assert payload["all_ok"]
    assert payload["n_generated_response_repair_attempts"] == 1
    assert payload["n_generated_responses_repaired"] == 1
    assert payload["n_response_contract_ok"] == 1
    assert len(requests) == 2
    repair_prompt = requests[1].user_prompt
    assert "primitive_evidence_matrix_accountability" in repair_prompt
    assert (
        "primitive_evidence_matrix source-backed primitives require response source_snippets"
        in repair_prompt
    )
    assert "rank_uniformity" in repair_prompt
    row = payload["rows"][0]
    assert row["repair_attempts"] == 1
    assert row["primitive_evidence_matrix_witness"][
        "matrix_accounting_complete"
    ] is True
    repair_categories = row["repair_error_history"][0][
        "repair_guidance_categories"
    ]
    assert "primitive_evidence_matrix_accountability" in repair_categories
    repair_ledger_row = row["repair_attempt_ledger"][0]
    assert "primitive_evidence_matrix_accountability" in repair_ledger_row[
        "repair_guidance_categories"
    ]
    assert any(
        "primitive_evidence_matrix source-backed primitives require response source_snippets"
        in error
        for error in repair_ledger_row["errors"]
    )


def test_llm_route_planner_preserves_exhausted_repair_attempt_ledger() -> None:
    root = Path("runs/test_formalization_gap_planner_llm_route_planner_repair_exhausted")
    out_dir = root / "llm_route_planner"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)

    class InvalidAnthropicBackend:
        provider_name = "anthropic"

        def generate(self, request):
            return GeneratorResponse(
                text=json.dumps(
                    {
                        "kernel_verified": True,
                        "informal_knowledge_dag_nodes": [],
                    }
                ),
                provider="anthropic",
                model=request.model,
                metadata={"generator_only": True, "tools_available": False},
            )

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        provider_name="anthropic",
        invoke_provider=True,
        generator_backend=InvalidAnthropicBackend(),
        max_repair_attempts=1,
    )

    assert not payload["all_ok"]
    assert payload["n_generated_response_repair_attempts"] == 1
    assert payload["n_generated_responses_repaired"] == 0
    assert payload["n_repair_attempt_ledger_rows"] == 2
    assert payload["n_response_contract_ok"] == 0
    assert payload["n_row_schema_valid"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    assert row["repair_attempts"] == 1
    assert [item["attempt"] for item in row["repair_error_history"]] == [0, 1]
    assert [item["failed_attempt_index"] for item in row["repair_attempt_ledger"]] == [
        0,
        1,
    ]
    assert row["repair_attempt_ledger"][0]["next_repair_attempt"] == 1
    assert row["repair_attempt_ledger"][1]["next_repair_attempt"] == ""
    assert all(
        "proof_boundary_violation" in item["repair_guidance_categories"]
        for item in row["repair_attempt_ledger"]
    )
    assert any("kernel_verified" in error for error in row["generation_errors"])
    assert validate_llm_route_planner_row(row) == []


def test_llm_route_planner_cli_validates_reviewed_static_response() -> None:
    root = Path("runs/test_formalization_gap_planner_llm_route_planner_cli")
    out_dir = root / "out"
    response_json = root / "response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    response_json.write_text(json.dumps(_llm_response_payload()), encoding="utf-8")

    code = main(
        [
            "formalization-gap-planner-llm-route-planner",
            "--input",
            str(input_json),
            "--provider",
            "static",
            "--static-response-file",
            str(response_json),
            "--out",
            str(out_dir),
        ]
    )

    assert code == 0
    manifest = json.loads(
        (
            out_dir
            / "formalization_gap_planner_llm_route_planner_manifest.json"
        ).read_text(encoding="utf-8")
    )
    assert manifest["n_accepted_route_plans"] == 1
    assert (
        out_dir
        / "formalization_gap_planner_llm_route_planner_standalone_seed.json"
    ).exists()


def test_llm_route_planner_rejects_kernel_verified_claim() -> None:
    root = Path("runs/test_formalization_gap_planner_llm_route_planner_rejects")
    response_json = root / "bad_response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    bad_response = _llm_response_payload()
    bad_response["kernel_verified"] = True
    response_json.write_text(json.dumps(bad_response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        provider_name="static",
        static_response_json=response_json,
    )

    assert not payload["all_ok"]
    assert payload["n_response_schema_invalid"] == 1
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    assert any("kernel_verified" in error for error in row["errors"])


def test_llm_route_planner_rejects_nested_kernel_proof_claims() -> None:
    root = Path("runs/test_formalization_gap_planner_llm_route_planner_rejects_nested_kernel")
    response_json = root / "bad_response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    bad_response = _llm_response_payload()
    bad_response["standalone_route"]["replan_metadata"] = {
        "claim_status": "KERNEL_VERIFIED"
    }
    bad_response["standalone_route"]["primitives"][0]["kernel_verified"] = True
    response_json.write_text(json.dumps(bad_response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        provider_name="static",
        static_response_json=response_json,
    )

    assert not payload["all_ok"]
    assert payload["n_response_schema_invalid"] == 1
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    assert any(
        "standalone_route.replan_metadata.claim_status" in error
        for error in row["errors"]
    )
    assert any(
        "standalone_route.primitives[0].kernel_verified" in error
        for error in row["errors"]
    )


def test_llm_route_planner_rejects_ungrounded_source_refs() -> None:
    root = Path("runs/test_formalization_gap_planner_llm_route_planner_rejects_sources")
    response_json = root / "bad_response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    bad_response = _llm_response_payload()
    for node in bad_response["informal_knowledge_dag_nodes"]:
        node["source_refs"] = ["invented_unreviewed_paper"]
    bad_response["standalone_route"]["source_refs"] = ["invented_unreviewed_paper"]
    for primitive in bad_response["standalone_route"]["primitives"]:
        primitive["source_refs"] = ["invented_unreviewed_paper"]
    response_json.write_text(json.dumps(bad_response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        provider_name="static",
        static_response_json=response_json,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    assert any("ungrounded source_refs" in error for error in row["errors"])


def test_llm_route_planner_rejects_ungrounded_source_snippets() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_rejects_source_snippets"
    )
    response_json = root / "bad_response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    bad_response = _llm_response_payload()
    bad_response["source_snippets"] = [
        {
            "source_ref": "invented_unreviewed_paper",
            "excerpt": "This fabricated excerpt should not ground the route.",
            "target_primitives": ["rank_uniformity"],
        }
    ]
    response_json.write_text(json.dumps(bad_response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        provider_name="static",
        static_response_json=response_json,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    assert any("ungrounded source_refs" in error for error in row["errors"])
    assert any(
        "response.source_snippets" in error or "invented_unreviewed_paper" in error
        for error in row["errors"]
    )


def test_llm_route_planner_rejects_fabricated_source_snippet_excerpt() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_rejects_fake_excerpt"
    )
    response_json = root / "bad_response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    bad_response = _llm_response_payload()
    bad_response["source_snippets"] = [
        {
            "source_ref": "conformal_prediction_textbook",
            "claim": "Exchangeability implies a uniform rank statistic.",
            "excerpt": (
                "This excerpt was never supplied by the request context and "
                "should not be accepted merely because the source_ref is known."
            ),
            "target_primitives": ["rank_uniformity"],
        }
    ]
    response_json.write_text(json.dumps(bad_response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        provider_name="static",
        static_response_json=response_json,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    assert any("unsupported snippets" in error for error in row["errors"])


def test_llm_route_planner_rejects_trivial_source_snippet_substring() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_rejects_tiny_excerpt"
    )
    response_json = root / "bad_response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    bad_response = _llm_response_payload()
    bad_response["source_snippets"] = [
        {
            "source_ref": "conformal_prediction_textbook",
            "excerpt": "rank",
            "target_primitives": ["rank_uniformity"],
        }
    ]
    response_json.write_text(json.dumps(bad_response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        provider_name="static",
        static_response_json=response_json,
    )

    assert not payload["all_ok"]
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    assert any("unsupported snippets" in error for error in row["errors"])


def test_llm_route_planner_rejects_partial_source_snippet_primitive_overclaim() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_rejects_partial_source_overclaim"
    )
    response_json = root / "bad_response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    source_ref = "paper:partial-rank-source"
    partial_snippet = {
        "source_ref": source_ref,
        "claim": "This source supports exchangeability but not rank uniformity.",
        "excerpt": (
            "The paper states that the calibration observations are exchangeable. "
            "It does not prove the finite rank uniformity bridge lemma."
        ),
        "target_primitives": ["exchangeability", "rank_uniformity"],
        "supported_target_primitives": ["exchangeability"],
        "unsupported_target_primitives": ["rank_uniformity"],
        "source_support_status": "source_backed_partial_target_primitives",
        "evidence_role": "source-backed informal route evidence",
    }
    input_payload = json.loads(input_json.read_text(encoding="utf-8"))
    input_payload["routes"][0]["source_refs"] = [source_ref]
    input_payload["routes"][0]["source_snippets"] = [partial_snippet]
    input_json.write_text(json.dumps(input_payload, indent=2), encoding="utf-8")

    bad_response = _replace_source_ref(
        _llm_response_payload(),
        "conformal_prediction_textbook",
        source_ref,
    )
    bad_response = _replace_source_snippets(
        bad_response,
        {
            "source_ref": source_ref,
            "claim": partial_snippet["claim"],
            "excerpt": partial_snippet["excerpt"],
            "target_primitives": ["rank_uniformity"],
            "evidence_role": "source-backed informal route evidence",
        },
    )
    response_json.write_text(json.dumps(bad_response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        provider_name="static",
        static_response_json=response_json,
    )

    assert not payload["all_ok"]
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    assert any(
        "partial source evidence" in error
        and "rank_uniformity" in error
        and "search_request" in error
        for error in row["errors"]
    )


def test_llm_route_planner_rejects_partial_source_snippet_enclosing_primitive_overclaim() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_rejects_enclosing_partial_source"
    )
    response_json = root / "bad_response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    source_ref = "paper:partial-rank-source"
    partial_snippet = {
        "source_ref": source_ref,
        "claim": "This source supports exchangeability but not rank uniformity.",
        "excerpt": (
            "The paper states that the calibration observations are exchangeable. "
            "It does not prove the finite rank uniformity bridge lemma."
        ),
        "target_primitives": ["exchangeability", "rank_uniformity"],
        "supported_target_primitives": ["exchangeability"],
        "unsupported_target_primitives": ["rank_uniformity"],
        "source_support_status": "source_backed_partial_target_primitives",
        "evidence_role": "source-backed informal route evidence",
    }
    input_payload = json.loads(input_json.read_text(encoding="utf-8"))
    input_payload["routes"][0]["source_refs"] = [source_ref]
    input_payload["routes"][0]["source_snippets"] = [partial_snippet]
    input_json.write_text(json.dumps(input_payload, indent=2), encoding="utf-8")

    emitted_snippet = {
        "source_ref": source_ref,
        "claim": partial_snippet["claim"],
        "excerpt": partial_snippet["excerpt"],
        "evidence_role": "source-backed informal route evidence",
    }
    bad_response = _replace_source_ref(
        _llm_response_payload(),
        "conformal_prediction_textbook",
        source_ref,
    )
    bad_response = _replace_source_snippets(bad_response, emitted_snippet)
    response_json.write_text(json.dumps(bad_response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        provider_name="static",
        static_response_json=response_json,
    )

    assert not payload["all_ok"]
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    assert any(
        "partial source evidence" in error
        and "rank_uniformity" in error
        and "search_request" in error
        for error in row["errors"]
    )


def test_llm_route_planner_allows_partial_source_snippet_with_search_request() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_partial_source_search_request"
    )
    response_json = root / "response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    source_ref = "paper:partial-rank-source"
    partial_snippet = {
        "source_ref": source_ref,
        "claim": "This source supports exchangeability but not rank uniformity.",
        "excerpt": (
            "The paper states that the calibration observations are exchangeable. "
            "It does not prove the finite rank uniformity bridge lemma."
        ),
        "target_primitives": ["exchangeability", "rank_uniformity"],
        "supported_target_primitives": ["exchangeability"],
        "unsupported_target_primitives": ["rank_uniformity"],
        "source_support_status": "source_backed_partial_target_primitives",
        "evidence_role": "source-backed informal route evidence",
    }
    input_payload = json.loads(input_json.read_text(encoding="utf-8"))
    input_payload["routes"][0]["source_refs"] = [source_ref]
    input_payload["routes"][0]["source_snippets"] = [partial_snippet]
    input_json.write_text(json.dumps(input_payload, indent=2), encoding="utf-8")

    response = _replace_source_ref(
        _llm_response_payload(),
        "conformal_prediction_textbook",
        source_ref,
    )
    response = _replace_source_snippets(
        response,
        {
            "source_ref": source_ref,
            "claim": partial_snippet["claim"],
            "excerpt": partial_snippet["excerpt"],
            "target_primitives": ["exchangeability"],
            "evidence_role": "partial source context requiring follow-up search",
        },
    )
    response["search_requests"] = [
        {
            "request_kind": "literature",
            "query": "finite rank uniformity bridge lemma under exchangeability",
            "reason": (
                "The available source supports exchangeability but not the "
                "rank_uniformity bridge primitive."
            ),
            "target_primitives": ["rank_uniformity"],
        }
    ]
    response_json.write_text(json.dumps(response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        provider_name="static",
        static_response_json=response_json,
    )

    assert payload["all_ok"]
    row = payload["rows"][0]
    assert row["acceptance_status"] == "ACCEPTED_WITH_SEARCH_REQUESTS"
    assert row["route_adoption_status"] == "PENDING_REFINEMENT_BEFORE_ROUTE_ADOPTION"
    assert "search_requests_pending_evidence" in row["route_adoption_blockers"]


def test_llm_route_planner_rejects_target_prover_family_drift() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_rejects_target_drift"
    )
    response_json = root / "bad_response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    bad_response = _llm_response_payload()
    bad_response["target_prover_family"] = "isabelle"
    bad_response["standalone_route"]["target_prover_family"] = "isabelle"
    bad_response["standalone_route"]["replan_metadata"] = {
        "target_prover_family": "isabelle",
    }
    bad_response["lean_realization_dag_nodes"][0][
        "target_prover_family"
    ] = "isabelle"
    response_json.write_text(json.dumps(bad_response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        provider_name="static",
        static_response_json=response_json,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    assert any(
        "target_prover_family" in error and "does not match request" in error
        for error in row["errors"]
    )


def test_llm_route_planner_rejects_target_prover_family_drift_in_action_rows() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_rejects_action_target_drift"
    )
    response_json = root / "bad_response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    interactive_session_dir = _write_interactive_session(root)
    bad_response = _llm_response_payload()
    bad_response["search_requests"][0]["target_prover_family"] = "rocq"
    bad_response["planner_next_actions"][0]["target_prover_family"] = "rocq"
    bad_response["residual_interpretations"] = [
        {
            "residual_goal": "missing finite tie-breaking side condition",
            "interpretation": "The rank route still has a target-prover side condition.",
            "route_repair": "Replay the rank_uniformity bridge after resolving the side condition.",
            "target_primitives": ["rank_uniformity"],
            "source_refs": ["conformal_prediction_textbook"],
            "target_prover_family": "rocq",
        }
    ]
    response_json.write_text(json.dumps(bad_response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        provider_name="static",
        static_response_json=response_json,
        formalization_gap_planner_interactive_session_dir=interactive_session_dir,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    error_text = "\n".join(row["errors"])
    assert "search_requests[0].target_prover_family rocq" in error_text
    assert "planner_next_actions[0].target_prover_family rocq" in error_text
    assert "residual_interpretations[0].target_prover_family rocq" in error_text
    assert "does not match request target_prover_family lean4" in error_text


def test_llm_route_planner_accepts_matching_target_prover_family_on_action_rows() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_accepts_action_target_scope"
    )
    response_json = root / "response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    interactive_session_dir = _write_interactive_session(root)
    response = _llm_response_payload()
    response["search_requests"][0]["target_prover_family"] = "lean4"
    response["planner_next_actions"][0]["target_prover_family"] = "lean4"
    response["residual_interpretations"] = [
        {
            "residual_goal": "missing finite tie-breaking side condition",
            "interpretation": "The rank route still has a target-prover side condition.",
            "route_repair": "Replay the rank_uniformity bridge after resolving the side condition.",
            "target_primitives": ["rank_uniformity"],
            "source_refs": ["conformal_prediction_textbook"],
            "target_prover_family": "lean4",
        }
    ]
    response_json.write_text(json.dumps(response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        provider_name="static",
        static_response_json=response_json,
        formalization_gap_planner_interactive_session_dir=interactive_session_dir,
    )

    assert payload["all_ok"]
    assert payload["n_response_contract_ok"] == 1


def test_llm_route_planner_rejects_target_specific_lean_tools_for_rocq_target() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_rejects_lean_tool_for_rocq"
    )
    response_json = root / "bad_response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    input_payload = json.loads(input_json.read_text(encoding="utf-8"))
    input_payload["target_prover_family"] = "rocq"
    input_payload["library_snapshot_ref"] = "rocq_probability_snapshot"
    input_json.write_text(json.dumps(input_payload), encoding="utf-8")
    bad_response = _llm_response_payload()
    bad_response["formal_realization_dag_nodes"] = bad_response.pop(
        "lean_realization_dag_nodes"
    )
    bad_response["search_requests"] = [
        {
            "request_kind": "lean_search",
            "owner": "leansearch",
            "query": "rank_uniformity Lean declaration search",
            "reason": "This incorrectly dispatches a Lean-specific search for Rocq.",
            "target_primitives": ["rank_uniformity"],
        }
    ]
    bad_response["planner_next_actions"] = [
        {
            "owner": "lean_lsp_mcp",
            "action": "attempt the rank_uniformity bridge lemma",
            "target_primitives": ["rank_uniformity"],
        }
    ]
    response_json.write_text(json.dumps(bad_response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        provider_name="static",
        static_response_json=response_json,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    error_text = "\n".join(row["errors"])
    assert "search_requests[0] uses target-specific tool/resource" in error_text
    assert "leansearch targets lean4" in error_text
    assert "planner_next_actions[0] uses target-specific tool/resource" in error_text
    assert "lean_lsp_mcp targets lean4" in error_text
    assert "target_prover_family rocq" in error_text


def test_llm_route_planner_rejects_lean_search_kind_for_rocq_target_without_owner() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_rejects_lean_request_kind_for_rocq"
    )
    response_json = root / "bad_response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    input_payload = json.loads(input_json.read_text(encoding="utf-8"))
    input_payload["target_prover_family"] = "rocq"
    input_payload["library_snapshot_ref"] = "rocq_probability_snapshot"
    input_json.write_text(json.dumps(input_payload), encoding="utf-8")
    bad_response = _llm_response_payload()
    bad_response["formal_realization_dag_nodes"] = bad_response.pop(
        "lean_realization_dag_nodes"
    )
    _retarget_formal_attempt_queue(
        bad_response,
        target_prover_family="rocq",
        owner="rocq_lsp_serapi",
    )
    bad_response["search_requests"] = [
        {
            "request_kind": "lean_search",
            "query": "rank_uniformity declaration search",
            "reason": (
                "This hides a Lean-specific search kind without naming a Lean "
                "owner or resource."
            ),
            "target_primitives": ["rank_uniformity"],
        }
    ]
    bad_response["planner_next_actions"] = [
        {
            "owner": "rocq_lsp_serapi",
            "action": "run Rocq proof-state feedback for the rank route",
            "target_primitives": ["rank_uniformity"],
        }
    ]
    response_json.write_text(json.dumps(bad_response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        provider_name="static",
        static_response_json=response_json,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    error_text = "\n".join(row["errors"])
    assert "search_requests[0] uses target-specific tool/resource" in error_text
    assert "lean_search targets lean4" in error_text
    assert "target_prover_family rocq" in error_text


def test_llm_route_planner_rejects_lean_action_text_for_rocq_formal_attempt() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_rejects_lean_action_for_rocq_attempt"
    )
    response_json = root / "bad_response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    input_payload = json.loads(input_json.read_text(encoding="utf-8"))
    input_payload["target_prover_family"] = "rocq"
    input_payload["library_snapshot_ref"] = "rocq_probability_snapshot"
    input_json.write_text(json.dumps(input_payload), encoding="utf-8")
    bad_response = _llm_response_payload()
    bad_response["formal_realization_dag_nodes"] = bad_response.pop(
        "lean_realization_dag_nodes"
    )
    _retarget_formal_attempt_queue(
        bad_response,
        target_prover_family="rocq",
        owner="formal_verifier",
    )
    bad_response["formal_attempt_queue"][1]["action"] = (
        "run lean_lsp proof-state feedback for the Rocq rank_uniformity bridge"
    )
    bad_response["search_requests"] = [
        {
            "request_kind": "formal_library",
            "query": "rank_uniformity Rocq declaration search",
            "reason": "Search the Rocq library adapter for the target primitive.",
            "target_primitives": ["rank_uniformity"],
        }
    ]
    bad_response["planner_next_actions"] = [
        {
            "owner": "formal_verifier",
            "action": "run Rocq proof-state feedback for the rank route",
            "target_primitives": ["rank_uniformity"],
        }
    ]
    response_json.write_text(json.dumps(bad_response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        provider_name="static",
        static_response_json=response_json,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    error_text = "\n".join(row["errors"])
    assert "formal_attempt_queue[1] uses target-specific tool/resource" in error_text
    assert "lean_lsp proof-state feedback" in error_text
    assert "targets lean4" in error_text
    assert "target_prover_family rocq" in error_text


def test_llm_route_planner_accepts_target_specific_rocq_tools_for_rocq_target() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_accepts_rocq_tool_for_rocq"
    )
    response_json = root / "response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    input_payload = json.loads(input_json.read_text(encoding="utf-8"))
    input_payload["target_prover_family"] = "rocq"
    input_payload["library_snapshot_ref"] = "rocq_probability_snapshot"
    input_payload["routes"][0]["target_prover_family"] = "rocq"
    input_payload["routes"][0]["primitives"][0]["candidate_declarations"] = [
        "Rocq.Probability.exchangeable"
    ]
    input_json.write_text(json.dumps(input_payload), encoding="utf-8")
    response = _llm_response_payload()
    response["formal_realization_dag_nodes"] = response.pop(
        "lean_realization_dag_nodes"
    )
    _set_existing_candidate_declaration_rows(
        response,
        declaration="Rocq.Probability.exchangeable",
        target_prover_family="rocq",
    )
    _retarget_formal_attempt_queue(
        response,
        target_prover_family="rocq",
        owner="rocq_lsp_serapi",
    )
    response["search_requests"] = [
        {
            "request_kind": "formal_library",
            "owner": "rocq_lsp_serapi",
            "query": "rank_uniformity Rocq declaration search",
            "reason": "Search the Rocq library adapter for the target primitive.",
            "target_primitives": ["rank_uniformity"],
        }
    ]
    response["planner_next_actions"] = [
        {
            "owner": "rocq_lsp_serapi",
            "action": "run Rocq proof-state feedback for the rank_uniformity bridge",
            "target_primitives": ["rank_uniformity"],
        }
    ]
    response_json.write_text(json.dumps(response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        provider_name="static",
        static_response_json=response_json,
    )

    assert payload["all_ok"]
    assert payload["n_response_contract_ok"] == 1


def test_llm_route_planner_accepts_target_specific_hol4_tools_for_hol4_target() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_accepts_hol4_tool_for_hol4"
    )
    response_json = root / "response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    input_payload = json.loads(input_json.read_text(encoding="utf-8"))
    input_payload["target_prover_family"] = "hol_4"
    input_payload["library_snapshot_ref"] = "hol4_probability_snapshot"
    input_payload["routes"][0]["target_prover_family"] = "hol_4"
    input_payload["routes"][0]["primitives"][0]["candidate_declarations"] = [
        "HOL4.Probability.exchangeable"
    ]
    input_json.write_text(json.dumps(input_payload), encoding="utf-8")
    response = _llm_response_payload()
    response["formal_realization_dag_nodes"] = response.pop(
        "lean_realization_dag_nodes"
    )
    _set_existing_candidate_declaration_rows(
        response,
        declaration="HOL4.Probability.exchangeable",
        target_prover_family="hol_4",
    )
    _retarget_formal_attempt_queue(
        response,
        target_prover_family="hol_4",
        owner="hol4_kernel_replay",
    )
    response["search_requests"] = [
        {
            "request_kind": "formal_library",
            "owner": "hol4_tactic_search",
            "query": "rank uniformity HOL4 theorem search",
            "reason": "Search the HOL4 library adapter for the target primitive.",
            "target_primitives": ["rank_uniformity"],
        }
    ]
    response["planner_next_actions"] = [
        {
            "owner": "hol4_kernel_replay",
            "action": "run HOL4 proof-state feedback for the rank route",
            "target_primitives": ["rank_uniformity"],
        }
    ]
    response_json.write_text(json.dumps(response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        provider_name="static",
        static_response_json=response_json,
    )

    assert payload["all_ok"]
    assert payload["n_response_contract_ok"] == 1
    assert payload["rows"][0]["target_prover_family"] == "hol_4"


def test_llm_route_planner_rejects_target_specific_hol4_tools_for_isabelle_target() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_rejects_hol4_tool_for_isabelle"
    )
    response_json = root / "bad_response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    input_payload = json.loads(input_json.read_text(encoding="utf-8"))
    input_payload["target_prover_family"] = "isabelle_hol"
    input_payload["library_snapshot_ref"] = "isabelle_afp_snapshot"
    input_json.write_text(json.dumps(input_payload), encoding="utf-8")
    bad_response = _llm_response_payload()
    bad_response["formal_realization_dag_nodes"] = bad_response.pop(
        "lean_realization_dag_nodes"
    )
    bad_response["search_requests"] = [
        {
            "request_kind": "formal_library",
            "owner": "hol4_tactic_search",
            "query": "rank uniformity HOL4 theorem search",
            "reason": "This incorrectly dispatches a HOL4-specific search for Isabelle.",
            "target_primitives": ["rank_uniformity"],
        }
    ]
    bad_response["planner_next_actions"] = [
        {
            "owner": "hol4_kernel_replay",
            "action": "run a HOL4 replay despite the Isabelle target",
            "target_primitives": ["rank_uniformity"],
        }
    ]
    response_json.write_text(json.dumps(bad_response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        provider_name="static",
        static_response_json=response_json,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    error_text = "\n".join(row["errors"])
    assert "search_requests[0] uses target-specific tool/resource" in error_text
    assert "hol4_tactic_search targets hol4" in error_text
    assert "planner_next_actions[0] uses target-specific tool/resource" in error_text
    assert "hol4_kernel_replay targets hol4" in error_text
    assert "target_prover_family isabelle_hol" in error_text


def test_llm_route_planner_adapter_target_filter_supports_extended_provers() -> None:
    assert _adapter_targets_match(
        "hol4_tactic_search",
        target_prover_family="hol_4",
        compatible_resource_ids=set(),
        resource_row_by_id={},
    )
    assert not _adapter_targets_match(
        "hol4_tactic_search",
        target_prover_family="isabelle_hol",
        compatible_resource_ids=set(),
        resource_row_by_id={},
    )
    assert _adapter_targets_match(
        "mizar_mml_search",
        target_prover_family="mizar",
        compatible_resource_ids=set(),
        resource_row_by_id={},
    )
    assert not _adapter_targets_match(
        "set_mm_lookup",
        target_prover_family="mizar",
        compatible_resource_ids=set(),
        resource_row_by_id={},
    )


def test_llm_route_planner_rejects_target_theorem_identity_drift() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_rejects_theorem_drift"
    )
    response_json = root / "bad_response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    bad_response = _llm_response_payload()
    bad_response["standalone_route"]["theorem_statement"] = (
        "A central limit theorem for independent sample means follows from "
        "Lindeberg conditions."
    )
    response_json.write_text(json.dumps(bad_response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        provider_name="static",
        static_response_json=response_json,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    assert any(
        "theorem_statement appears to target a different theorem" in error
        for error in row["errors"]
    )


def test_response_payload_validation_uses_target_theorem_context_packet_anchor() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_response_validation_uses_target_context_anchor"
    )
    out_dir = root / "llm_route_planner"
    response_json = root / "bad_response.json"
    request_context_json = root / "request_context.json"
    validation_out_dir = root / "response_payload_validation"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)

    prompt_payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        provider_name="prompt_only",
    )
    request = deepcopy(prompt_payload["request_packets"][0])
    request["target_route"]["theorem_statement"] = ""
    request["context_packet"]["current_route"]["theorem_statement"] = ""
    request_context_json.write_text(
        json.dumps({"request_packets": [request]}, indent=2),
        encoding="utf-8",
    )
    bad_response = {
        "request_id": request["request_id"],
        "route_id": request["route_id"],
        "response_payload": _llm_response_payload(),
    }
    bad_response["response_payload"]["standalone_route"]["theorem_statement"] = (
        "A central limit theorem for independent sample means follows from "
        "Lindeberg conditions."
    )
    response_json.write_text(json.dumps(bad_response, indent=2), encoding="utf-8")

    validation_payload = validate_formalization_gap_planner_llm_route_planner_response_payloads(
        response_json,
        validation_out_dir,
        request_context_json=request_context_json,
    )

    assert validation_payload["n_payloads"] == 1
    assert validation_payload["n_valid_payloads"] == 0
    assert validation_payload["n_request_context_errors"] == 1
    rows = validation_payload["rows"]
    assert any(
        "theorem_statement appears to target a different theorem" in error
        for error in rows[0]["errors"]
    )


def test_response_payload_validation_enforces_route_adoption_preconditions() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_response_validation_route_preconditions"
    )
    out_dir = root / "llm_route_planner"
    source_grounding_dir = root / "source_grounding"
    response_json = root / "responses.json"
    request_context_json = root / "request_context.json"
    validation_out_dir = root / "response_payload_validation"
    shutil.rmtree(root, ignore_errors=True)
    source_grounding_dir.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    (
        source_grounding_dir
        / "formalization_gap_planner_source_grounding_audit_manifest.json"
    ).write_text(
        json.dumps(
            {
                "component_name": "formalization_gap_planner_source_grounding_audit",
                "rows": [
                    {
                        "source_grounding_id": "source-grounding:rank-residual",
                        "route_id": "rank_route",
                        "display_name": "distribution_free_rank_bound",
                        "node_source": "refinement_evidence_prover_feedback",
                        "node_id": "residual:rank_uniformity:measurability",
                        "node_kind": "prover_residual_goal",
                        "node_label": "Rank bridge residual measurability condition",
                        "source_refs": [],
                        "source_snippets": [],
                        "residual_goals": [
                            "rank_uniformity: missing measurability side condition"
                        ],
                        "residual_primitives": ["rank_uniformity"],
                        "residual_evidence_ids": ["evidence:rank-lsp"],
                        "grounding_status": "unaccounted",
                        "required_next_action": "route_repair_or_source_search",
                        "ok": False,
                        "errors": ["residual goal has no source-backed route repair"],
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    prompt_payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        provider_name="prompt_only",
        formalization_gap_planner_source_grounding_audit_dir=source_grounding_dir,
    )
    request = prompt_payload["request_packets"][0]
    preconditions = request["context_packet"]["route_adoption_preconditions"]
    assert preconditions["blocked_before_response"] is True
    assert set(preconditions["response_required_fields"]) >= {
        "residual_interpretations",
        "search_requests",
        "planner_next_actions",
    }
    request_context_json.write_text(
        json.dumps({"request_packets": [request]}, indent=2),
        encoding="utf-8",
    )

    valid_payload = _llm_response_payload()
    valid_payload["residual_interpretations"] = [
        {
            "residual_goal": "rank_uniformity: missing measurability side condition",
            "interpretation": (
                "The attempted rank-uniformity bridge exposed a side condition "
                "that is not yet source-backed."
            ),
            "route_repair": (
                "Keep the measurability side condition as a route-repair "
                "obligation until source evidence or a formal boundary is added."
            ),
            "target_primitives": ["rank_uniformity"],
            "source_refs": ["conformal_prediction_textbook"],
        }
    ]
    valid_payload["search_requests"] = [
        {
            "request_kind": "literature",
            "query": (
                "source-backed measurability side condition for finite rank "
                "uniformity under exchangeability"
            ),
            "reason": (
                "route_adoption_preconditions require a source-grounding "
                "follow-up before adopting the repaired route"
            ),
            "target_primitives": ["rank_uniformity"],
        }
    ]
    valid_payload["planner_next_actions"] = []
    silent_payload = deepcopy(valid_payload)
    silent_payload["search_requests"] = []
    silent_payload["planner_next_actions"] = []
    wrong_scope_payload = deepcopy(valid_payload)
    wrong_scope_payload["search_requests"] = [
        {
            "request_kind": "literature",
            "query": "source-backed exchangeability follow-up for the finite route",
            "reason": (
                "This is intentionally scoped to the wrong primitive for the "
                "route-adoption precondition."
            ),
            "target_primitives": ["exchangeability"],
        }
    ]
    response_json.write_text(
        json.dumps(
            {
                "responses": [
                    {
                        "request_id": request["request_id"],
                        "route_id": request["route_id"],
                        "response_payload": valid_payload,
                    },
                    {
                        "request_id": request["request_id"],
                        "route_id": request["route_id"],
                        "response_payload": wrong_scope_payload,
                    },
                    {
                        "request_id": request["request_id"],
                        "route_id": request["route_id"],
                        "response_payload": silent_payload,
                    },
                ]
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    validation_payload = validate_formalization_gap_planner_llm_route_planner_response_payloads(
        response_json,
        validation_out_dir,
        request_context_json=request_context_json,
    )

    assert validation_payload["all_ok"] is False
    assert validation_payload["n_payloads"] == 3
    assert validation_payload["n_valid_payloads"] == 1
    assert validation_payload["n_invalid_payloads"] == 2
    assert validation_payload["n_request_bound_payloads"] == 3
    assert (
        validation_payload[
            "n_request_bound_payloads_with_route_adoption_preconditions"
        ]
        == 3
    )
    assert (
        validation_payload[
            "n_request_bound_payloads_with_blocking_route_adoption_preconditions"
        ]
        == 3
    )
    assert (
        validation_payload[
            "n_request_bound_payload_route_adoption_precondition_known_blockers"
        ]
        == preconditions["n_known_pre_response_blockers"] * 3
    )
    assert (
        validation_payload[
            "n_request_bound_payload_route_adoption_precondition_required_response_fields"
        ]
        == preconditions["n_response_required_fields"] * 3
    )
    assert validation_payload["n_request_bound_payloads_with_route_adoption_status"] == 3
    assert validation_payload["n_request_bound_payloads_route_adoption_ready"] == 0
    assert (
        validation_payload[
            "n_request_bound_payloads_route_adoption_pending_refinement"
        ]
        == 1
    )
    assert validation_payload["n_request_bound_payloads_route_adoption_rejected"] == 2
    assert (
        validation_payload[
            "n_request_bound_payloads_adoptable_for_standalone_replay"
        ]
        == 0
    )
    assert validation_payload["by_request_bound_payload_route_adoption_status"] == {
        "PENDING_REFINEMENT_BEFORE_ROUTE_ADOPTION": 1,
        "REJECTED_LLM_ROUTE_PLAN": 2,
    }
    blocker_counts = validation_payload[
        "request_bound_payload_route_adoption_blocker_counts"
    ]
    assert blocker_counts["response_not_accepted"] == 2
    assert blocker_counts["search_requests_pending_evidence"] == 1
    assert blocker_counts["residual_interpretations_require_route_replay"] == 1
    assert blocker_counts[ROUTE_ADOPTION_BLOCKER_SOURCE_GROUNDING] == 1
    assert (
        validate_llm_route_planner_response_payload_validation_manifest(
            validation_payload,
            validation_payload["response_payload_validation_manifest_schema"],
        )
        == []
    )
    valid_row, wrong_scope_row, silent_row = validation_payload["rows"]
    assert valid_row["ok"] is True
    assert valid_row["request_bound_response_contract_ok"] is True
    assert valid_row["request_bound_route_adoption_status"] == (
        "PENDING_REFINEMENT_BEFORE_ROUTE_ADOPTION"
    )
    assert set(valid_row["request_bound_route_adoption_blockers"]) >= {
        "search_requests_pending_evidence",
        "residual_interpretations_require_route_replay",
        ROUTE_ADOPTION_BLOCKER_SOURCE_GROUNDING,
    }
    assert valid_row["request_bound_adoptable_for_standalone_replay"] is False
    assert valid_row["n_request_context_errors"] == 0
    assert valid_row["request_context_route_adoption_precondition_present"] is True
    assert (
        valid_row[
            "request_context_route_adoption_precondition_blocked_before_response"
        ]
        is True
    )
    assert (
        valid_row["request_context_route_adoption_precondition_known_blocker_count"]
        == preconditions["n_known_pre_response_blockers"]
    )
    assert (
        valid_row[
            "request_context_route_adoption_precondition_required_response_field_count"
        ]
        == preconditions["n_response_required_fields"]
    )
    assert wrong_scope_row["ok"] is False
    assert wrong_scope_row["request_bound_response_contract_ok"] is False
    assert wrong_scope_row["request_bound_route_adoption_status"] == (
        "REJECTED_LLM_ROUTE_PLAN"
    )
    assert wrong_scope_row["request_bound_route_adoption_blockers"] == [
        "response_not_accepted"
    ]
    assert wrong_scope_row["request_bound_adoptable_for_standalone_replay"] is False
    assert wrong_scope_row["n_request_context_errors"] == 1
    assert any(
        "route_adoption_preconditions require search_requests or "
        "planner_next_actions scoped to precondition target_primitives: "
        "rank_uniformity" in error
        for error in wrong_scope_row["errors"]
    )
    assert silent_row["ok"] is False
    assert silent_row["request_bound_response_contract_ok"] is False
    assert silent_row["request_bound_route_adoption_status"] == (
        "REJECTED_LLM_ROUTE_PLAN"
    )
    assert silent_row["request_bound_route_adoption_blockers"] == [
        "response_not_accepted"
    ]
    assert silent_row["request_bound_adoptable_for_standalone_replay"] is False
    assert silent_row["n_request_context_errors"] == 1
    assert any(
        "route_adoption_preconditions require at least one nonempty "
        "search_requests or planner_next_actions row" in error
        for error in silent_row["errors"]
    )


def test_response_payload_validation_enforces_formal_attempt_queue_precondition() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_response_validation_formal_attempt_precondition"
    )
    out_dir = root / "llm_route_planner"
    interactive_session_dir = root / "interactive_session"
    response_json = root / "responses.json"
    request_context_json = root / "request_context.json"
    validation_out_dir = root / "response_payload_validation"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    interactive_session_dir.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    (
        interactive_session_dir
        / "formalization_gap_planner_interactive_session_manifest.json"
    ).write_text(
        json.dumps(
            {
                "component_name": "formalization_gap_planner_interactive_session",
                "rows": [
                    {
                        "interactive_session_row_id": (
                            "session:rank_route_formal_attempt_precondition"
                        ),
                        "goal_plan_id": "goal:rank_route",
                        "route_id": "rank_route",
                        "display_name": "distribution_free_rank_bound",
                        "session_state": "AWAITING_REFINEMENT_RESPONSES",
                        "next_interaction_kind": "target_prover_replay",
                        "next_owner_agent": "formal_verifier",
                        "route_adoption_precondition_blocked_before_response": True,
                        "route_adoption_precondition_unresolved": True,
                        "route_adoption_precondition_known_blockers": [
                            ROUTE_ADOPTION_BLOCKER_REALIZATION_COVERAGE
                        ],
                        "route_adoption_precondition_required_response_fields": [
                            "formal_attempt_queue"
                        ],
                        "route_adoption_precondition_target_primitives": [
                            "rank_uniformity"
                        ],
                    }
                ],
                "decision_policy_rows": [],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    prompt_payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        provider_name="prompt_only",
        formalization_gap_planner_interactive_session_dir=interactive_session_dir,
    )
    request = prompt_payload["request_packets"][0]
    preconditions = request["context_packet"]["route_adoption_preconditions"]
    assert (
        prompt_payload[
            "n_request_route_adoption_precondition_target_primitives"
        ]
        == 1
    )
    assert (
        prompt_payload[
            "n_row_route_adoption_precondition_target_primitives"
        ]
        == 1
    )
    assert preconditions["blocked_before_response"] is True
    assert "formal_attempt_queue" in preconditions["response_required_fields"]
    assert preconditions["target_primitives"] == ["rank_uniformity"]
    request_context_json.write_text(
        json.dumps({"request_packets": [request]}, indent=2),
        encoding="utf-8",
    )

    valid_payload = _llm_response_payload()
    valid_payload["search_requests"] = []
    valid_payload["planner_next_actions"] = []
    valid_payload["uncertainty_flags"] = []
    valid_payload["semantic_alignment_risks"] = []
    missing_queue_payload = deepcopy(valid_payload)
    missing_queue_payload["formal_attempt_queue"] = []
    response_json.write_text(
        json.dumps(
            {
                "responses": [
                    {
                        "request_id": request["request_id"],
                        "route_id": request["route_id"],
                        "response_payload": valid_payload,
                    },
                    {
                        "request_id": request["request_id"],
                        "route_id": request["route_id"],
                        "response_payload": missing_queue_payload,
                    },
                ]
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    validation_payload = validate_formalization_gap_planner_llm_route_planner_response_payloads(
        response_json,
        validation_out_dir,
        request_context_json=request_context_json,
    )

    assert validation_payload["all_ok"] is False
    assert validation_payload["n_payloads"] == 2
    assert validation_payload["n_valid_payloads"] == 1
    assert validation_payload["n_invalid_payloads"] == 1
    assert validation_payload["n_request_bound_payloads_with_route_adoption_status"] == 2
    assert validation_payload["n_request_bound_payloads_route_adoption_ready"] == 0
    assert (
        validation_payload[
            "n_request_bound_payloads_route_adoption_pending_refinement"
        ]
        == 1
    )
    assert validation_payload["n_request_bound_payloads_route_adoption_rejected"] == 1
    assert (
        validation_payload[
            "n_request_bound_payloads_adoptable_for_standalone_replay"
        ]
        == 0
    )
    assert validation_payload["by_request_bound_payload_route_adoption_status"] == {
        "PENDING_REFINEMENT_BEFORE_ROUTE_ADOPTION": 1,
        "REJECTED_LLM_ROUTE_PLAN": 1,
    }
    assert validation_payload["request_bound_payload_route_adoption_blocker_counts"] == {
        "feedback_loop_replan_required": 1,
        "feedback_summary_actions_pending_resolution": 1,
        "response_not_accepted": 1,
    }
    valid_row, missing_queue_row = validation_payload["rows"]
    assert valid_row["ok"] is True
    assert valid_row["n_request_context_errors"] == 0
    assert valid_row["request_bound_response_contract_ok"] is True
    assert valid_row["request_bound_route_adoption_status"] == (
        "PENDING_REFINEMENT_BEFORE_ROUTE_ADOPTION"
    )
    assert valid_row["request_bound_route_adoption_blockers"] == [
        "feedback_summary_actions_pending_resolution",
        "feedback_loop_replan_required",
    ]
    assert valid_row["request_bound_adoptable_for_standalone_replay"] is False
    assert missing_queue_row["ok"] is False
    assert missing_queue_row["n_request_context_errors"] >= 1
    assert missing_queue_row["request_bound_response_contract_ok"] is False
    assert missing_queue_row["request_bound_route_adoption_status"] == (
        "REJECTED_LLM_ROUTE_PLAN"
    )
    assert missing_queue_row["request_bound_route_adoption_blockers"] == [
        "response_not_accepted"
    ]
    assert (
        missing_queue_row["request_bound_adoptable_for_standalone_replay"]
        is False
    )
    assert any(
        "route_adoption_preconditions require at least one nonempty "
        "formal_attempt_queue row" in error
        for error in missing_queue_row["errors"]
    )


def test_response_payload_validation_enforces_agentic_strategy_plan_obligations() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_response_validation_agentic_strategy_obligations"
    )
    out_dir = root / "llm_route_planner"
    strategy_plan_dir = root / "agentic_strategy_plan"
    response_json = root / "responses.json"
    request_context_json = root / "request_context.json"
    validation_out_dir = root / "response_payload_validation"
    shutil.rmtree(root, ignore_errors=True)
    strategy_plan_dir.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    strategy_rows = [
        {
            "schema_version": 1,
            "strategy_id": "strategy:rank_route:patch_gap",
            "followup_id": "followup:rank_route:patch_gap",
            "residual_response_validation_id": "validation:rank_route:patch_gap",
            "prompt_packet_id": "packet:rank_route:patch_gap",
            "residual_obligation_id": "residual-obligation:rank_route:patch_gap",
            "route_id": "rank_route",
            "display_name": "distribution_free_rank_bound",
            "target_theorem_name": "distribution_free_rank_bound",
            "candidate_bridge_lemma_name": "exchangeability_patch_bridge",
            "residual_gap": "exchangeability_patch_gap",
            "action_class": "reuse_exact_proof_bank_obligation",
            "followup_kind": "residual_patch_rerun",
            "followup_status": "READY_FOR_AGENTIC_PROOF_STRATEGY",
            "agentic_strategy_kind": "evolve_block_residual_patch",
            "required_live_tools": ["lean_goal", "lean_multi_attempt"],
            "evaluator_gates": ["patch-rerun calibration"],
            "candidate_database_key": "candidate-db:rank_route:patch_gap",
            "expected_artifacts": ["patched/Rank.lean"],
            "priority_score": 130,
            "rank": 1,
            "proof_evidence_status": (
                "AGENTIC_STRATEGY_PLAN_NOT_PROOF_EVIDENCE"
            ),
            "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
            "ok": True,
            "errors": [],
        },
        {
            "schema_version": 1,
            "strategy_id": "strategy:rank_route:source_gap",
            "followup_id": "followup:rank_route:source_gap",
            "residual_response_validation_id": "validation:rank_route:source_gap",
            "prompt_packet_id": "packet:rank_route:source_gap",
            "residual_obligation_id": "residual-obligation:rank_route:source_gap",
            "route_id": "rank_route",
            "display_name": "distribution_free_rank_bound",
            "target_theorem_name": "distribution_free_rank_bound",
            "candidate_bridge_lemma_name": "rank_uniformity_source_bridge",
            "residual_gap": "source_cache_rank_uniformity_gap",
            "action_class": "source_discovery_needed",
            "followup_kind": "residual_source_discovery",
            "followup_status": "READY_FOR_AGENTIC_PROOF_STRATEGY",
            "agentic_strategy_kind": "global_goal_cache_source_discovery",
            "required_live_tools": ["paperqa", "lean_leansearch"],
            "evaluator_gates": ["primitive-source coverage expansion"],
            "global_goal_cache_keys": ["source_cache_rank_uniformity_gap"],
            "candidate_database_key": "candidate-db:rank_route:source_gap",
            "expected_artifacts": ["source_cache/rank_uniformity.json"],
            "priority_score": 80,
            "rank": 2,
            "proof_evidence_status": (
                "AGENTIC_STRATEGY_PLAN_NOT_PROOF_EVIDENCE"
            ),
            "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
            "ok": True,
            "errors": [],
        },
    ]
    (
        strategy_plan_dir / "formal_verifier_agentic_proof_strategy_plan_manifest.json"
    ).write_text(
        json.dumps(
            {
                "schema_version": 1,
                "n_strategy_rows": len(strategy_rows),
                "n_ready": 2,
                "n_patch_evolve_blocks": 1,
                "n_source_discovery_cache_items": 1,
                "n_kernel_overlay_composition_seeds": 0,
                "n_with_live_tool_plan": 2,
                "all_ok": True,
                "rows": strategy_rows,
                "limitations": [
                    "agentic proof strategy rows are proof-search contracts, not theorem proof evidence"
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    prompt_payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        provider_name="prompt_only",
        formal_verifier_agentic_proof_strategy_plan_dir=strategy_plan_dir,
    )
    request = prompt_payload["request_packets"][0]
    assert (
        len(request["context_packet"]["formal_verifier_agentic_proof_strategy_plan_rows"])
        == 2
    )
    request_context_json.write_text(
        json.dumps({"request_packets": [request]}, indent=2),
        encoding="utf-8",
    )

    valid_payload = _llm_response_payload()
    valid_payload["search_requests"].append(
        {
            "request_kind": "literature",
            "query": (
                "source_cache_rank_uniformity_gap source evidence for the "
                "rank-uniformity strategy row"
            ),
            "reason": (
                "Answer strategy:rank_route:source_gap before route adoption"
            ),
            "strategy_id": "strategy:rank_route:source_gap",
        }
    )
    valid_payload["planner_next_actions"].append(
        {
            "owner": "lean_lsp_mcp",
            "action": (
                "run lean_lsp patch evolve block for exchangeability_patch_gap"
            ),
            "target_primitives": ["exchangeability"],
            "strategy_id": "strategy:rank_route:patch_gap",
            "agentic_strategy_kind": "evolve_block_residual_patch",
        }
    )
    silent_payload = _llm_response_payload()
    response_json.write_text(
        json.dumps(
            {
                "responses": [
                    {
                        "request_id": request["request_id"],
                        "route_id": request["route_id"],
                        "response_payload": valid_payload,
                    },
                    {
                        "request_id": request["request_id"],
                        "route_id": request["route_id"],
                        "response_payload": silent_payload,
                    },
                ]
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    validation_payload = validate_formalization_gap_planner_llm_route_planner_response_payloads(
        response_json,
        validation_out_dir,
        request_context_json=request_context_json,
    )

    assert validation_payload["all_ok"] is False
    assert validation_payload["n_payloads"] == 2
    assert validation_payload["n_valid_payloads"] == 1
    assert validation_payload["n_invalid_payloads"] == 1
    assert (
        validation_payload[
            "n_request_bound_payloads_with_agentic_proof_strategy_plan"
        ]
        == 2
    )
    assert (
        validation_payload[
            "n_request_bound_payload_agentic_proof_strategy_plan_rows"
        ]
        == 4
    )
    assert (
        validation_payload[
            "n_request_bound_payload_agentic_proof_strategy_plan_ready"
        ]
        == 4
    )
    assert (
        validation_payload[
            "n_payloads_with_agentic_proof_strategy_plan_obligation_errors"
        ]
        == 1
    )
    assert (
        validation_payload["n_agentic_proof_strategy_plan_obligation_errors"] == 2
    )
    assert (
        validate_llm_route_planner_response_payload_validation_manifest(
            validation_payload,
            validation_payload["response_payload_validation_manifest_schema"],
        )
        == []
    )
    valid_row, silent_row = validation_payload["rows"]
    assert valid_row["ok"] is True
    assert valid_row["request_context_agentic_proof_strategy_plan_present"] is True
    assert valid_row["request_context_agentic_proof_strategy_plan_row_count"] == 2
    assert valid_row["request_context_agentic_proof_strategy_plan_ready_count"] == 2
    assert valid_row["n_agentic_proof_strategy_plan_obligation_errors"] == 0
    assert silent_row["ok"] is False
    assert silent_row["n_agentic_proof_strategy_plan_obligation_errors"] == 2
    assert silent_row["n_request_context_errors"] == 2
    assert all(
        "agentic proof strategy plan ready row" in error
        for error in silent_row["errors"]
    )


def test_llm_route_planner_rejects_unsupported_source_search_status() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_rejects_bad_source_status"
    )
    response_json = root / "bad_response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    bad_response = _llm_response_payload()
    bad_response["informal_knowledge_dag_nodes"][0]["source_refs"] = []
    bad_response["informal_knowledge_dag_nodes"][0][
        "source_search_status"
    ] = "MODEL_CONFIDENT_WITHOUT_EVIDENCE"
    bad_response["standalone_route"]["primitives"][0][
        "source_search_status"
    ] = "UNREGISTERED_STATUS"
    response_json.write_text(json.dumps(bad_response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        provider_name="static",
        static_response_json=response_json,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    error_text = "\n".join(row["errors"])
    assert "source_search_status unsupported" in error_text
    assert "MODEL_CONFIDENT_WITHOUT_EVIDENCE" in error_text
    assert "UNREGISTERED_STATUS" in error_text


def test_llm_route_planner_rejects_placeholder_formal_gap_boundary() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_rejects_placeholder_boundary"
    )
    response_json = root / "bad_response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    bad_response = _llm_response_payload()
    bad_response["informal_knowledge_dag_nodes"][0]["source_refs"] = []
    bad_response["informal_knowledge_dag_nodes"][0][
        "source_search_status"
    ] = "FORMAL_GAP_BOUNDARY"
    bad_response["lean_realization_dag_nodes"][0]["formal_gap_boundary"] = "todo"
    bad_response["standalone_route"]["primitives"][0][
        "formal_gap_boundary"
    ] = "later"
    response_json.write_text(json.dumps(bad_response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        provider_name="static",
        static_response_json=response_json,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    error_text = "\n".join(row["errors"])
    assert "formal_gap_boundary required" in error_text
    assert "formal_gap_boundary must be a substantive" in error_text
    assert "formal_realization_dag_nodes[0]" in error_text
    assert "standalone_route.primitives[0]" in error_text


def test_llm_route_planner_rejects_unanchored_formal_gap_boundary() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_rejects_unanchored_boundary"
    )
    response_json = root / "bad_response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    bad_response = _llm_response_payload()
    unanchored_boundary = (
        "Needs further investigation before adoption by the verification team."
    )
    bad_response["lean_realization_dag_nodes"][1][
        "formal_gap_boundary"
    ] = unanchored_boundary
    bad_response["standalone_route"]["primitives"][1][
        "formal_gap_boundary"
    ] = unanchored_boundary
    response_json.write_text(json.dumps(bad_response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        provider_name="static",
        static_response_json=response_json,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    error_text = "\n".join(row["errors"])
    assert "formal_gap_boundary must name the affected primitive" in error_text
    assert "formal_realization_dag_nodes[1]" in error_text
    assert "standalone_route.primitives[1]" in error_text


def test_llm_route_planner_rejects_source_backed_node_without_source_ref() -> None:
    root = Path("runs/test_formalization_gap_planner_llm_route_planner_rejects_source_backed_without_ref")
    response_json = root / "bad_response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    bad_response = _llm_response_payload()
    bad_response["informal_knowledge_dag_nodes"][0]["source_refs"] = []
    bad_response["informal_knowledge_dag_nodes"][0][
        "source_search_status"
    ] = "SOURCE_BACKED"
    response_json.write_text(json.dumps(bad_response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        provider_name="static",
        static_response_json=response_json,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    assert any("SOURCE_BACKED requires grounded source_refs" in error for error in row["errors"])


def test_llm_route_planner_rejects_source_backed_primitive_without_source_ref() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_rejects_source_backed_primitive_without_ref"
    )
    response_json = root / "bad_response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    bad_response = _llm_response_payload()
    rank_primitive = bad_response["standalone_route"]["primitives"][1]
    rank_primitive["source_search_status"] = "SOURCE_BACKED"
    rank_primitive["source_refs"] = []
    rank_primitive["source_snippets"] = []
    response_json.write_text(json.dumps(bad_response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        provider_name="static",
        static_response_json=response_json,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    assert any(
        "standalone_route.primitives[1] SOURCE_BACKED requires primitive-level"
        in error
        for error in row["errors"]
    )


def test_llm_route_planner_rejects_source_backed_residual_without_source_ref() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_rejects_source_backed_residual_without_ref"
    )
    response_json = root / "bad_response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    interactive_session_dir = _write_interactive_session(root)
    bad_response = _llm_response_payload()
    bad_response["residual_interpretations"] = [
        {
            "residual_goal": "missing finite tie-breaking side condition",
            "interpretation": (
                "The rank route still has a source-backed residual side condition."
            ),
            "route_repair": (
                "Add the rank_uniformity side-condition repair after checking "
                "the source route."
            ),
            "target_primitives": ["rank_uniformity"],
            "source_search_status": "SOURCE_BACKED",
        }
    ]
    bad_response["search_requests"].append(
        {
            "request_kind": "literature",
            "query": "rank_uniformity residual source route",
            "reason": "search request alone must not satisfy SOURCE_BACKED residual status",
            "target_primitives": ["rank_uniformity"],
        }
    )
    response_json.write_text(json.dumps(bad_response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        provider_name="static",
        static_response_json=response_json,
        formalization_gap_planner_interactive_session_dir=interactive_session_dir,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    assert any(
        "residual_interpretations[0] SOURCE_BACKED requires grounded source_refs"
        in error
        for error in row["errors"]
    )


def test_llm_route_planner_accepts_source_backed_residual_with_source_ref() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_accepts_source_backed_residual"
    )
    response_json = root / "response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    interactive_session_dir = _write_interactive_session(root)
    response = _llm_response_payload()
    response["residual_interpretations"] = [
        {
            "residual_goal": "missing finite tie-breaking side condition",
            "interpretation": (
                "The rank route still has a source-backed residual side condition."
            ),
            "route_repair": (
                "Add the rank_uniformity side-condition repair after checking "
                "the source route."
            ),
            "target_primitives": ["rank_uniformity"],
            "source_refs": ["conformal_prediction_textbook"],
            "source_search_status": "SOURCE_BACKED",
        }
    ]
    response_json.write_text(json.dumps(response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        provider_name="static",
        static_response_json=response_json,
        formalization_gap_planner_interactive_session_dir=interactive_session_dir,
    )

    assert payload["all_ok"]
    assert payload["n_response_contract_ok"] == 1


def test_llm_route_planner_rejects_search_requested_without_search_request() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_rejects_search_status_without_request"
    )
    response_json = root / "bad_response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    bad_response = _llm_response_payload()
    rank_node = bad_response["informal_knowledge_dag_nodes"][1]
    rank_node["source_refs"] = []
    rank_node["source_snippets"] = []
    rank_node["source_search_status"] = "SEARCH_REQUESTED"
    bad_response["search_requests"] = []
    response_json.write_text(json.dumps(bad_response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        provider_name="static",
        static_response_json=response_json,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    assert any(
        "SEARCH_REQUESTED requires a matching literature/source search_request"
        in error
        for error in row["errors"]
    )


def test_llm_route_planner_rejects_formal_source_search_as_literature_request() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_rejects_formal_source_as_literature"
    )
    response_json = root / "bad_response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    bad_response = _llm_response_payload()
    rank_node = bad_response["informal_knowledge_dag_nodes"][1]
    rank_node["source_refs"] = []
    rank_node["source_snippets"] = []
    rank_node["source_search_status"] = "SEARCH_REQUESTED"
    bad_response["search_requests"] = [
        {
            "request_kind": "formal_source",
            "query": "rank_uniformity formal source declaration search",
            "reason": "formal-source search is not literature evidence",
            "target_primitives": ["rank_uniformity"],
        }
    ]
    response_json.write_text(json.dumps(bad_response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        provider_name="static",
        static_response_json=response_json,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    assert any(
        "informal_knowledge_dag_nodes[1] SEARCH_REQUESTED requires a matching "
        "literature/source search_request" in error
        for error in row["errors"]
    )


def test_llm_route_planner_rejects_search_request_with_mismatched_explicit_target() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_rejects_mismatched_search_target"
    )
    response_json = root / "bad_response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    bad_response = _llm_response_payload()
    rank_node = bad_response["informal_knowledge_dag_nodes"][1]
    rank_node["source_refs"] = []
    rank_node["source_snippets"] = []
    rank_node["source_search_status"] = "SEARCH_REQUESTED"
    bad_response["search_requests"] = [
        {
            "request_kind": "literature",
            "query": "rank_uniformity finite-rank source route",
            "reason": (
                "This prose mentions rank_uniformity, but the structured "
                "target points to the wrong primitive."
            ),
            "target_primitives": ["exchangeability"],
        }
    ]
    response_json.write_text(json.dumps(bad_response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        provider_name="static",
        static_response_json=response_json,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    assert any(
        "informal_knowledge_dag_nodes[1] SEARCH_REQUESTED requires a matching "
        "literature/source search_request" in error
        for error in row["errors"]
    )


def test_llm_route_planner_rejects_planner_action_with_mismatched_explicit_target() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_rejects_mismatched_action_target"
    )
    response_json = root / "bad_response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    bad_response = _llm_response_payload()
    bad_response["planner_next_actions"] = [
        {
            "owner": "lean_lsp_mcp",
            "action": (
                "lean_lsp proof-state attempt for the rank_uniformity bridge "
                "lemma"
            ),
            "target_primitives": ["exchangeability"],
        }
    ]
    response_json.write_text(json.dumps(bad_response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        provider_name="static",
        static_response_json=response_json,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    assert any(
        "planner_next_actions[0] action/query primitive mentions must include "
        "a scoped target_primitives/primitive value" in error
        for error in row["errors"]
    )


def test_llm_route_planner_rejects_residual_search_requested_without_search_request() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_rejects_residual_search_without_request"
    )
    response_json = root / "bad_response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    interactive_session_dir = _write_interactive_session(root)
    bad_response = _llm_response_payload()
    bad_response["residual_interpretations"] = [
        {
            "residual_goal": "missing finite tie-breaking side condition",
            "interpretation": (
                "The rank route still has a residual side condition that needs "
                "literature confirmation."
            ),
            "route_repair": (
                "Add the rank_uniformity side-condition repair only after "
                "source search resolves the residual."
            ),
            "target_primitives": ["rank_uniformity"],
            "source_refs": ["conformal_prediction_textbook"],
            "source_search_status": "SEARCH_REQUESTED",
        }
    ]
    bad_response["search_requests"] = []
    response_json.write_text(json.dumps(bad_response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        provider_name="static",
        static_response_json=response_json,
        formalization_gap_planner_interactive_session_dir=interactive_session_dir,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    assert any(
        "residual_interpretations[0] SEARCH_REQUESTED requires a matching "
        "literature/source search_request" in error
        for error in row["errors"]
    )


def test_llm_route_planner_rejects_route_search_requested_without_search_request() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_rejects_route_search_without_request"
    )
    response_json = root / "bad_response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    bad_response = _llm_response_payload()
    bad_response["standalone_route"]["source_search_status"] = "SEARCH_REQUESTED"
    bad_response["search_requests"] = []
    response_json.write_text(json.dumps(bad_response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        provider_name="static",
        static_response_json=response_json,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    assert any(
        "standalone_route SEARCH_REQUESTED requires a matching "
        "literature/source search_request" in error
        for error in row["errors"]
    )


def test_llm_route_planner_rejects_malformed_search_request() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_rejects_malformed_search_request"
    )
    response_json = root / "bad_response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    bad_response = _llm_response_payload()
    bad_response["search_requests"] = [
        {
            "request_kind": "invented_tool_dispatch",
            "query": "",
            "reason": "",
        }
    ]
    response_json.write_text(json.dumps(bad_response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        provider_name="static",
        static_response_json=response_json,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    assert any(
        "search_requests[0].request_kind unsupported" in error
        for error in row["errors"]
    )
    assert any("search_requests[0].query missing" in error for error in row["errors"])
    assert any("search_requests[0].reason missing" in error for error in row["errors"])


def test_llm_route_planner_rejects_malformed_planner_next_action() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_rejects_malformed_planner_action"
    )
    response_json = root / "bad_response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    bad_response = _llm_response_payload()
    bad_response["planner_next_actions"] = [
        {
            "owner": "",
            "action": "",
        }
    ]
    response_json.write_text(json.dumps(bad_response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        provider_name="static",
        static_response_json=response_json,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    assert any(
        "planner_next_actions[0].owner missing" in error
        for error in row["errors"]
    )
    assert any(
        "planner_next_actions[0].action missing" in error
        for error in row["errors"]
    )
    assert any(
        "planner_next_actions[0] does not resolve to a supported hook family"
        in error
        for error in row["errors"]
    )


def test_llm_route_planner_rejects_minimal_delta_without_cost_witness() -> None:
    root = Path("runs/test_formalization_gap_planner_llm_route_planner_rejects_missing_cost")
    response_json = root / "bad_response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    bad_response = _llm_response_payload()
    for field_name in (
        "cost_model_version",
        "route_cost",
        "primitive_costs",
        "and_or_cost_graph",
    ):
        bad_response["minimal_delta_plan"].pop(field_name, None)
    response_json.write_text(json.dumps(bad_response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        provider_name="static",
        static_response_json=response_json,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    assert any("cost_model_version" in error for error in row["errors"])
    assert any("route_cost" in error for error in row["errors"])
    assert any("primitive_costs" in error for error in row["errors"])
    assert any("and_or_cost_graph" in error for error in row["errors"])


def test_llm_route_planner_rejects_unaccounted_primitive_cost_dimensions() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_rejects_unaccounted_cost"
    )
    response_json = root / "bad_response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    bad_response = _llm_response_payload()
    bad_response["minimal_delta_plan"]["primitive_costs"][1][
        "proof_difficulty_cost"
    ] = 2
    response_json.write_text(json.dumps(bad_response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        provider_name="static",
        static_response_json=response_json,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    assert any(
        "total_cost must equal base_cost + proof_difficulty_cost" in error
        for error in row["errors"]
    )


def test_llm_route_planner_rejects_coverage_bucket_base_cost_mismatch() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_rejects_bucket_base_cost"
    )
    response_json = root / "bad_response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    bad_response = _llm_response_payload()
    cost_row = bad_response["minimal_delta_plan"]["primitive_costs"][1]
    cost_row["coverage_bucket"] = "source_port_needed"
    response_json.write_text(json.dumps(bad_response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        provider_name="static",
        static_response_json=response_json,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    assert any(
        "base_cost must equal minimal_delta_cost_policy.coverage_bucket_base_cost"
        in error
        for error in row["errors"]
    )


def test_llm_route_planner_rejects_underpriced_coverage_evidence() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_rejects_underpriced_coverage"
    )
    response_json = root / "bad_response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    bad_response = _llm_response_payload()
    bad_response["standalone_route"]["primitives"][1][
        "coverage_status"
    ] = "source_port_needed"
    response_json.write_text(json.dumps(bad_response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        provider_name="static",
        static_response_json=response_json,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    assert any(
        "coverage_bucket/base_cost underprices formal/standalone coverage evidence"
        in error
        for error in row["errors"]
    )


def test_llm_route_planner_rejects_wrapper_without_formal_anchor() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_rejects_unanchored_wrapper"
    )
    response_json = root / "bad_response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    response_json.write_text(
        json.dumps(_make_rank_uniformity_unanchored_wrapper_response()),
        encoding="utf-8",
    )

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        provider_name="static",
        static_response_json=response_json,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    assert row["response_contract_ok"] is False
    assert any(
        "formal_realization_dag_nodes[1] wrapper coverage requires "
        "candidate_declarations" in error
        for error in row["errors"]
    )
    assert any(
        "standalone_route.primitives[1] wrapper coverage requires "
        "candidate_declarations" in error
        for error in row["errors"]
    )


def test_llm_route_planner_rejects_coverage_downgrade_against_request_hints() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_rejects_coverage_hint_downgrade"
    )
    response_json = root / "bad_response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input_with_rank_bridge_candidate(root)
    response_json.write_text(
        json.dumps(_make_rank_uniformity_coverage_downgrade_response()),
        encoding="utf-8",
    )

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        provider_name="static",
        static_response_json=response_json,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    assert row["response_contract_ok"] is False
    assert any(
        "formal_realization_dag_nodes[1].coverage_bucket downgrades "
        "request minimal_delta_cost_hints for primitive rank_uniformity" in error
        and "minimum_coverage_bucket=bridge_needed" in error
        for error in row["errors"]
    )
    assert any(
        "standalone_route.primitives[1].coverage_status downgrades "
        "request minimal_delta_cost_hints for primitive rank_uniformity" in error
        and "minimum_base_cost=4" in error
        for error in row["errors"]
    )


def test_llm_route_planner_rejects_underpriced_request_cost_hints() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_rejects_cost_hint_underpricing"
    )
    response_json = root / "bad_response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    response_json.write_text(
        json.dumps(_make_rank_uniformity_near_exists_response()),
        encoding="utf-8",
    )

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        provider_name="static",
        static_response_json=response_json,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    assert row["response_contract_ok"] is False
    assert any(
        "underprices request minimal_delta_cost_hints" in error
        and "minimum_base_cost=4" in error
        for error in row["errors"]
    )
    assert any(
        "minimum_route_base_cost=4" in error for error in row["errors"]
    )


def test_llm_route_planner_rejects_silent_cost_hint_primitive_omission() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_rejects_cost_hint_omission"
    )
    response_json = root / "bad_response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    response_json.write_text(
        json.dumps(_make_rank_uniformity_omitted_response()),
        encoding="utf-8",
    )

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        provider_name="static",
        static_response_json=response_json,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    assert row["response_contract_ok"] is False
    assert any(
        "baseline route option" in error and "rank_uniformity" in error
        for error in row["errors"]
    )


def test_llm_route_planner_rejects_underpriced_baseline_option_when_cost_hint_primitive_omitted() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_rejects_underpriced_cost_hint_baseline"
    )
    response_json = root / "bad_response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    response_json.write_text(
        json.dumps(
            _make_rank_uniformity_omitted_response(
                include_baseline_route_option=True,
                baseline_route_cost=1,
            )
        ),
        encoding="utf-8",
    )

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        provider_name="static",
        static_response_json=response_json,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    assert row["response_contract_ok"] is False
    assert any(
        "baseline route option" in error and "minimum_route_base_cost=4" in error
        for error in row["errors"]
    )
    assert any(
        "underprices context_packet.route_option_selection_brief candidate "
        "route_option:current_route_min_delta_baseline" in error
        and "route_cost=1" in error
        and "minimum_route_base_cost=4" in error
        for error in row["errors"]
    )


def test_llm_route_planner_rejects_underpriced_unselected_option_from_primitive_hints() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_rejects_underpriced_unselected_option"
    )
    response_json = root / "bad_response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    response = _make_rank_uniformity_omitted_response(
        include_baseline_route_option=True,
        baseline_route_cost=4,
    )
    _append_underpriced_rank_route_option(response, route_cost=3)
    response_json.write_text(json.dumps(response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        provider_name="static",
        static_response_json=response_json,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    assert row["response_contract_ok"] is False
    assert any(
        "route_options[2].route_cost underprices request primitive cost hints" in error
        and "minimum_known_base_cost=4" in error
        and "rank_uniformity" in error
        for error in row["errors"]
    )


def test_llm_route_planner_blocks_route_adoption_when_cost_hint_primitive_omitted() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_blocks_cost_hint_omission"
    )
    response_json = root / "response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    response = _make_rank_uniformity_omitted_response(
        include_baseline_route_option=True,
        baseline_route_cost=4,
    )
    response["search_requests"] = []
    response["planner_next_actions"] = []
    response["uncertainty_flags"] = []
    response["semantic_alignment_risks"] = []
    response_json.write_text(json.dumps(response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        provider_name="static",
        static_response_json=response_json,
    )

    assert payload["all_ok"]
    assert payload["n_response_contract_ok"] == 1
    assert payload["n_route_adoption_ready"] == 0
    assert payload["n_route_adoption_pending_refinement"] == 1
    assert (
        payload["n_route_adoption_pending_omitted_cost_hint_primitive_blockers"]
        == 1
    )
    assert payload["n_route_adoption_omitted_cost_hint_primitives"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "ACCEPTED_WITH_FORMAL_ATTEMPT_QUEUE"
    assert row["response_contract_ok"] is True
    assert row["route_adoption_status"] == (
        "PENDING_REFINEMENT_BEFORE_ROUTE_ADOPTION"
    )
    assert set(row["route_adoption_blockers"]) == {
        ROUTE_ADOPTION_BLOCKER_PRIMITIVE_EVIDENCE_MATRIX,
        "omitted_cost_hint_primitives_require_review",
    }
    assert row["primitive_evidence_matrix_witness"][
        "delta_needed_matrix_primitives_missing_accounting"
    ] == ["rank_uniformity"]
    witness = row["realization_coverage_witness"]
    assert witness["selected_primitives"] == ["exchangeability"]
    assert witness["cost_hint_baseline_primitives"] == [
        "exchangeability",
        "rank_uniformity",
    ]
    assert witness["omitted_cost_hint_primitives"] == ["rank_uniformity"]
    assert witness["cost_hint_baseline_coverage_complete"] is False
    seed_route = payload["standalone_seed"]["routes"][0]
    assert seed_route["realization_coverage_witness"][
        "omitted_cost_hint_primitives"
    ] == ["rank_uniformity"]
    assert seed_route["llm_route_planner_route_adoption_status"] == (
        "PENDING_REFINEMENT_BEFORE_ROUTE_ADOPTION"
    )
    assert seed_route["replan_metadata"][
        "llm_route_planner_route_adoption_blockers"
    ] == list(row["route_adoption_blockers"])
    assert seed_route["replan_metadata"][
        "llm_route_planner_realization_coverage_witness"
    ]["omitted_cost_hint_primitives"] == ["rank_uniformity"]
    omitted_hook = next(
        hook
        for hook in seed_route["interactive_refinement_hooks"]
        if hook.get("llm_route_planner_realization_coverage_action", {}).get(
            "action"
        )
        == "review_or_restore_omitted_cost_hint_primitives"
    )
    assert omitted_hook["hook_kind"] == "route_revision"
    assert omitted_hook["target_primitives"] == ["rank_uniformity"]
    assert omitted_hook["llm_route_planner_realization_coverage_witness"][
        "omitted_cost_hint_primitives"
    ] == ["rank_uniformity"]
    assert any(
        trigger.get("trigger_kind")
        == "omitted_cost_hint_primitives_review_required"
        for trigger in seed_route["route_revision_triggers"]
    )
    seed_json = root / "standalone_seed.json"
    seed_json.write_text(json.dumps(payload["standalone_seed"]), encoding="utf-8")
    plan_payload = export_formalization_gap_planner_standalone_plan(
        seed_json,
        root / "standalone_plan_from_omitted_cost_hint_seed",
    )
    assert plan_payload["all_ok"]
    refinement_queue_payload = export_formalization_gap_planner_refinement_queue(
        root / "standalone_plan_from_omitted_cost_hint_seed",
        root / "refinement_queue_from_omitted_cost_hint_seed",
    )
    assert refinement_queue_payload["all_ok"]
    omitted_queue_row = next(
        row
        for row in refinement_queue_payload["rows"]
        if row["hook_kind"] == "route_revision"
        and row["llm_route_planner_hook_trace"].get(
            "llm_route_planner_realization_coverage_action", {}
        ).get("action")
        == "review_or_restore_omitted_cost_hint_primitives"
    )
    assert omitted_queue_row["target_primitives"] == ("rank_uniformity",)
    assert (
        "omitted_cost_hint_primitives_review_required"
        in omitted_queue_row["trigger_kinds"]
    )
    trace_witness = plan_payload["rows"][0]["standalone_input_trace"][
        "realization_coverage_witness"
    ]
    assert trace_witness["cost_hint_baseline_primitives"] == [
        "exchangeability",
        "rank_uniformity",
    ]
    assert trace_witness["omitted_cost_hint_primitives"] == ["rank_uniformity"]
    assert trace_witness["cost_hint_baseline_coverage_complete"] is False


def test_llm_route_planner_rejects_missing_primitive_cost_dimensions() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_rejects_missing_cost_dimensions"
    )
    response_json = root / "bad_response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    bad_response = _llm_response_payload()
    bad_response["minimal_delta_plan"]["primitive_costs"][1].pop("reuse_credit")
    response_json.write_text(json.dumps(bad_response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        provider_name="static",
        static_response_json=response_json,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    assert any(
        "cost dimension fields missing: reuse_credit" in error
        for error in row["errors"]
    )


def test_llm_route_planner_rejects_route_cost_not_matching_primitive_totals() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_rejects_route_cost_sum"
    )
    response_json = root / "bad_response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    bad_response = _llm_response_payload()
    bad_response["minimal_delta_plan"]["route_cost"] = 5
    graph = bad_response["minimal_delta_plan"]["and_or_cost_graph"]
    graph["route_options"][0]["route_cost"] = 5
    graph["route_options"][1]["route_cost"] = 7
    response_json.write_text(json.dumps(bad_response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        provider_name="static",
        static_response_json=response_json,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    assert any(
        "route_cost must equal the sum of selected primitive_costs total_cost values"
        in error
        for error in row["errors"]
    )


def test_llm_route_planner_rejects_placeholder_minimality_rationale() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_rejects_placeholder_minimality_rationale"
    )
    response_json = root / "bad_response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    bad_response = _llm_response_payload()
    bad_response["minimal_delta_plan"]["minimality_rationale"] = "minimal"
    response_json.write_text(json.dumps(bad_response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        provider_name="static",
        static_response_json=response_json,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    assert any(
        "minimal_delta_plan.minimality_rationale must be substantive"
        in error
        and "placeholder" in error
        for error in row["errors"]
    )


def test_llm_route_planner_rejects_unanchored_minimality_rationale() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_rejects_unanchored_minimality_rationale"
    )
    response_json = root / "bad_response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    bad_response = _llm_response_payload()
    bad_response["minimal_delta_plan"]["minimality_rationale"] = (
        "This route keeps the proof small while saving effort."
    )
    response_json.write_text(json.dumps(bad_response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        provider_name="static",
        static_response_json=response_json,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    assert any(
        "minimal_delta_plan.minimality_rationale must mention selected primitives"
        in error
        and "selected route option" in error
        and "actionable delta evidence" in error
        for error in row["errors"]
    )


def test_llm_route_planner_rejects_route_option_cost_without_witness() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_rejects_route_option_cost_without_witness"
    )
    response_json = root / "bad_response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    bad_response = _llm_response_payload()
    graph = bad_response["minimal_delta_plan"]["and_or_cost_graph"]
    graph["route_options"][1].pop("primitive_costs", None)
    response_json.write_text(json.dumps(bad_response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        provider_name="static",
        static_response_json=response_json,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    assert any(
        "route_options[1].route_cost must equal the sum of route option primitive_costs"
        in error
        and "route_cost=7" in error
        and "primitive_total=4" in error
        for error in row["errors"]
    )


def test_llm_route_planner_rejects_route_option_cost_bucket_underpricing_evidence() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_rejects_route_option_bucket_underpricing"
    )
    response_json = root / "bad_response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    bad_response = _llm_response_payload()
    graph = bad_response["minimal_delta_plan"]["and_or_cost_graph"]
    alternative = graph["route_options"][1]
    alternative["primitive_costs"][1] = {
        "primitive": "rank_uniformity",
        "coverage_bucket": "exact_exists",
        "base_cost": 0,
        "proof_difficulty_cost": 7,
        "import_cone_cost": 0,
        "definition_or_typeclass_cost": 0,
        "semantic_risk_cost": 0,
        "reuse_credit": 0,
        "total_cost": 7,
        "cost_rationale": (
            "This corrupted option hides bridge evidence behind proof difficulty."
        ),
    }
    alternative["route_cost"] = 7
    response_json.write_text(json.dumps(bad_response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        provider_name="static",
        static_response_json=response_json,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    assert any(
        "and_or_cost_graph.route_options[1].primitive_costs[1].coverage_bucket/base_cost underprices"
        in error
        and "coverage_bucket=exact_exists" in error
        and "requires at least 4" in error
        for error in row["errors"]
    )


def test_llm_route_planner_rejects_route_option_cost_without_action_witness() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_rejects_route_option_cost_without_action_witness"
    )
    response_json = root / "bad_response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    bad_response = _llm_response_payload()
    graph = bad_response["minimal_delta_plan"]["and_or_cost_graph"]
    graph["route_options"][1].pop("source_port_lemmas", None)
    response_json.write_text(json.dumps(bad_response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        provider_name="static",
        static_response_json=response_json,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    assert any(
        "and_or_cost_graph.route_options[1] primitive rank_uniformity requires actionable route option action witness"
        in error
        and "source_port_lemmas" in error
        and "coverage_bucket=source_port" in error
        for error in row["errors"]
    )
    witness = row["realization_coverage_witness"]
    assert witness["route_option_action_witness_complete"] is False
    assert witness["route_option_action_witness_missing_primitives"] == [
        "rank_uniformity"
    ]


def test_llm_route_planner_rejects_route_option_primitive_without_cost_row() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_rejects_route_option_primitive_without_cost_row"
    )
    response_json = root / "bad_response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    bad_response = _llm_response_payload()
    graph = bad_response["minimal_delta_plan"]["and_or_cost_graph"]
    graph["route_options"][1]["selected_primitives"].append("rank_order_statistic")
    graph["and_edges"][1]["requires"].append("rank_order_statistic")
    response_json.write_text(json.dumps(bad_response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        provider_name="static",
        static_response_json=response_json,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    assert any(
        "primitive_costs missing route option primitives" in error
        and "rank_order_statistic" in error
        for error in row["errors"]
    )


def test_llm_route_planner_rejects_route_option_primitive_without_realization_coverage() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_rejects_route_option_primitive_without_realization_coverage"
    )
    response_json = root / "bad_response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    bad_response = _llm_response_payload()
    graph = bad_response["minimal_delta_plan"]["and_or_cost_graph"]
    alternative = graph["route_options"][1]
    alternative["selected_primitives"].append("rank_order_statistic")
    alternative["primitive_costs"].append(
        {
            "primitive": "rank_order_statistic",
            "coverage_bucket": "already_exists",
            "base_cost": 0,
            "proof_difficulty_cost": 0,
            "import_cone_cost": 0,
            "definition_or_typeclass_cost": 0,
            "semantic_risk_cost": 0,
            "reuse_credit": 0,
            "total_cost": 0,
            "cost_rationale": (
                "This corrupted alternative claims the extra primitive is free."
            ),
        }
    )
    graph["and_edges"][1]["requires"].append("rank_order_statistic")
    response_json.write_text(json.dumps(bad_response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        provider_name="static",
        static_response_json=response_json,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    error_text = "\n".join(row["errors"])
    assert (
        "route option primitives missing from standalone_route.primitives"
        in error_text
    )
    assert (
        "route option primitives missing from formal_realization_dag_nodes"
        in error_text
    )
    assert "rank_order_statistic" in error_text


def test_llm_route_planner_rejects_route_option_primitive_without_alignment() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_rejects_route_option_primitive_without_alignment"
    )
    response_json = root / "bad_response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    bad_response = _llm_response_payload()
    primitive = "rank_order_statistic"
    bad_response["lean_realization_dag_nodes"].append(
        {
            "node_id": "formal:rank_order_statistic_bridge",
            "primitive": primitive,
            "coverage_bucket": "bridge",
            "candidate_declarations": [],
            "formalization_action": "prove_bridge",
        }
    )
    bad_response["standalone_route"]["primitives"].append(
        {
            "primitive": primitive,
            "coverage_status": "bridge_needed",
            "source_refs": ["conformal_prediction_textbook"],
        }
    )
    cost_row = {
        "primitive": primitive,
        "coverage_bucket": "bridge_needed",
        "base_cost": 4,
        "proof_difficulty_cost": 0,
        "import_cone_cost": 0,
        "definition_or_typeclass_cost": 0,
        "semantic_risk_cost": 0,
        "reuse_credit": 0,
        "total_cost": 4,
        "cost_rationale": "The alternative route adds an unaligned bridge primitive.",
    }
    bad_response["minimal_delta_plan"]["primitive_costs"].append(cost_row)
    graph = bad_response["minimal_delta_plan"]["and_or_cost_graph"]
    alternative = graph["route_options"][1]
    alternative["selected_primitives"].append(primitive)
    alternative["primitive_costs"].append(dict(cost_row))
    alternative["route_cost"] = 11
    graph["and_edges"][1]["requires"].append(primitive)
    response_json.write_text(json.dumps(bad_response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        provider_name="static",
        static_response_json=response_json,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    assert any(
        "and_or_cost_graph route option primitives missing route_alignment_edges"
        in error
        and primitive in error
        for error in row["errors"]
    )


def test_llm_route_planner_accepts_aligned_route_option_primitive() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_accepts_aligned_route_option_primitive"
    )
    response_json = root / "response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    response = _llm_response_payload()
    primitive = "rank_order_statistic"
    response["informal_knowledge_dag_nodes"].append(
        {
            "node_id": "informal:rank_order_statistic",
            "claim": (
                "An alternative rank route may introduce a rank order statistic "
                "bridge before proving the final bound."
            ),
            "depends_on": ["informal:rank_uniformity"],
            "source_refs": ["conformal_prediction_textbook"],
            "source_search_status": "SOURCE_BACKED",
            "semantic_role": "lemma",
        }
    )
    response["informal_knowledge_dag_edges"].append(
        {
            "source_node_id": "informal:rank_uniformity",
            "target_node_id": "informal:rank_order_statistic",
            "edge_kind": "uses",
            "rationale": (
                "The rank-order statistic bridge refines the source-backed "
                "rank-uniformity route."
            ),
        }
    )
    response["lean_realization_dag_nodes"].append(
        {
            "node_id": "formal:rank_order_statistic_bridge",
            "primitive": primitive,
            "coverage_bucket": "bridge",
            "candidate_declarations": [],
            "formalization_action": "prove_bridge",
        }
    )
    response["formal_realization_dag_edges"].append(
        {
            "source_node_id": "formal:rank_uniformity_bridge",
            "target_node_id": "formal:rank_order_statistic_bridge",
            "edge_kind": "bridges",
            "rationale": (
                "The rank-order statistic bridge is downstream of the "
                "rank-uniformity formal bridge."
            ),
        }
    )
    response["route_alignment_edges"].append(
        {
            "informal_node_id": "informal:rank_order_statistic",
            "formal_node_id": "formal:rank_order_statistic_bridge",
            "alignment_status": "bridge_needed",
            "alignment_rationale": (
                "The alternative AND/OR branch realizes the source-backed rank "
                "order statistic step as one bridge lemma."
            ),
        }
    )
    response["standalone_route"]["primitives"].append(
        {
            "primitive": primitive,
            "coverage_status": "bridge_needed",
            "source_refs": ["conformal_prediction_textbook"],
        }
    )
    cost_row = {
        "primitive": primitive,
        "coverage_bucket": "bridge_needed",
        "base_cost": 4,
        "proof_difficulty_cost": 0,
        "import_cone_cost": 0,
        "definition_or_typeclass_cost": 0,
        "semantic_risk_cost": 0,
        "reuse_credit": 0,
        "total_cost": 4,
        "cost_rationale": "The alternative route adds one aligned bridge primitive.",
    }
    response["minimal_delta_plan"]["primitive_costs"].append(cost_row)
    graph = response["minimal_delta_plan"]["and_or_cost_graph"]
    alternative = graph["route_options"][1]
    alternative["selected_primitives"].append(primitive)
    alternative.setdefault("bridge_lemmas", []).append(
        (
            "rank_order_statistic: prove the alternative rank-order bridge "
            "from the source-backed rank uniformity step"
        )
    )
    alternative["primitive_costs"].append(dict(cost_row))
    alternative["route_cost"] = 11
    graph["and_edges"][1]["requires"].append(primitive)
    response_json.write_text(json.dumps(response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        provider_name="static",
        static_response_json=response_json,
    )

    assert payload["all_ok"]
    assert payload["n_response_contract_ok"] == 1


def test_llm_route_planner_rejects_flat_and_or_cost_graph() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_rejects_flat_cost_graph"
    )
    response_json = root / "bad_response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    bad_response = _llm_response_payload()
    graph = bad_response["minimal_delta_plan"]["and_or_cost_graph"]
    graph.pop("or_nodes")
    graph.pop("and_edges")
    response_json.write_text(json.dumps(bad_response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        provider_name="static",
        static_response_json=response_json,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    assert any("and_or_cost_graph.or_nodes must be non-empty" in error for error in row["errors"])
    assert any("and_or_cost_graph.and_edges must be non-empty" in error for error in row["errors"])


def test_llm_route_planner_rejects_and_edge_route_option_mismatch() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_rejects_and_edge_mismatch"
    )
    response_json = root / "bad_response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    bad_response = _llm_response_payload()
    graph = bad_response["minimal_delta_plan"]["and_or_cost_graph"]
    graph["and_edges"][0]["requires"] = ["exchangeability"]
    response_json.write_text(json.dumps(bad_response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        provider_name="static",
        static_response_json=response_json,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    assert any(
        "and_edges[0].requires must match route_options selected_primitives"
        in error
        for error in row["errors"]
    )


def test_llm_route_planner_rejects_route_option_without_and_edge() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_rejects_route_option_without_and_edge"
    )
    response_json = root / "bad_response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    bad_response = _llm_response_payload()
    graph = bad_response["minimal_delta_plan"]["and_or_cost_graph"]
    graph["and_edges"] = [
        edge
        for edge in graph["and_edges"]
        if edge["route_option_id"] != "route_option:source_port_rank_theory"
    ]
    response_json.write_text(json.dumps(bad_response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        provider_name="static",
        static_response_json=response_json,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    assert any(
        "and_edges must include every route option" in error
        and "route_option:source_port_rank_theory" in error
        for error in row["errors"]
    )


def test_llm_route_planner_rejects_duplicate_route_option_id() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_rejects_duplicate_route_option_id"
    )
    response_json = root / "bad_response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    bad_response = _llm_response_payload()
    graph = bad_response["minimal_delta_plan"]["and_or_cost_graph"]
    graph["route_options"][1]["route_option_id"] = (
        "route_option:reuse_exchangeability_bridge_rank"
    )
    graph["or_nodes"][0]["choices"] = [
        "route_option:reuse_exchangeability_bridge_rank"
    ]
    graph["and_edges"][1]["route_option_id"] = (
        "route_option:reuse_exchangeability_bridge_rank"
    )
    response_json.write_text(json.dumps(bad_response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        provider_name="static",
        static_response_json=response_json,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    assert any(
        "route_options[1].route_option_id duplicates another route option" in error
        and "route_option:reuse_exchangeability_bridge_rank" in error
        for error in row["errors"]
    )


def test_llm_route_planner_rejects_unknown_selected_route_option_id() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_rejects_unknown_selected_route_option_id"
    )
    response_json = root / "bad_response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    bad_response = _llm_response_payload()
    graph = bad_response["minimal_delta_plan"]["and_or_cost_graph"]
    graph["selected_route_option_id"] = "route_option:missing_candidate"
    response_json.write_text(json.dumps(bad_response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        provider_name="static",
        static_response_json=response_json,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    assert any(
        "selected_route_option_id references unknown route option" in error
        and "route_option:missing_candidate" in error
        for error in row["errors"]
    )


def test_llm_route_planner_rejects_duplicate_or_choice() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_rejects_duplicate_or_choice"
    )
    response_json = root / "bad_response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    bad_response = _llm_response_payload()
    graph = bad_response["minimal_delta_plan"]["and_or_cost_graph"]
    graph["or_nodes"][0]["choices"].append("route_option:source_port_rank_theory")
    response_json.write_text(json.dumps(bad_response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        provider_name="static",
        static_response_json=response_json,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    assert any(
        "or_nodes[0].choices must not contain duplicates" in error
        and "route_option:source_port_rank_theory" in error
        for error in row["errors"]
    )


def test_llm_route_planner_rejects_duplicate_and_edge_for_route_option() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_rejects_duplicate_and_edge"
    )
    response_json = root / "bad_response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    bad_response = _llm_response_payload()
    graph = bad_response["minimal_delta_plan"]["and_or_cost_graph"]
    graph["and_edges"].append(dict(graph["and_edges"][0]))
    response_json.write_text(json.dumps(bad_response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        provider_name="static",
        static_response_json=response_json,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    assert any(
        "and_edges must include exactly one edge per route option" in error
        and "route_option:reuse_exchangeability_bridge_rank" in error
        for error in row["errors"]
    )


def test_llm_route_planner_rejects_duplicate_selected_primitive() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_rejects_duplicate_selected_primitive"
    )
    response_json = root / "bad_response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    bad_response = _llm_response_payload()
    bad_response["minimal_delta_plan"]["selected_primitives"].append(
        "exchangeability"
    )
    response_json.write_text(json.dumps(bad_response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        provider_name="static",
        static_response_json=response_json,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    assert any(
        "minimal_delta_plan.selected_primitives must not contain duplicates" in error
        and "exchangeability" in error
        for error in row["errors"]
    )


def test_llm_route_planner_rejects_duplicate_route_option_primitive() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_rejects_duplicate_route_option_primitive"
    )
    response_json = root / "bad_response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    bad_response = _llm_response_payload()
    graph = bad_response["minimal_delta_plan"]["and_or_cost_graph"]
    graph["route_options"][1]["selected_primitives"].append("exchangeability")
    graph["and_edges"][1]["requires"].append("exchangeability")
    response_json.write_text(json.dumps(bad_response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        provider_name="static",
        static_response_json=response_json,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    assert any(
        "route_options[1].selected_primitives must not contain duplicates" in error
        and "exchangeability" in error
        for error in row["errors"]
    )
    assert any(
        "and_edges[1].requires must not contain duplicate primitives" in error
        and "exchangeability" in error
        for error in row["errors"]
    )


def test_llm_route_planner_rejects_duplicate_and_edge_required_primitive() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_rejects_duplicate_and_edge_required_primitive"
    )
    response_json = root / "bad_response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    bad_response = _llm_response_payload()
    graph = bad_response["minimal_delta_plan"]["and_or_cost_graph"]
    graph["and_edges"][1]["requires"].append("exchangeability")
    response_json.write_text(json.dumps(bad_response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        provider_name="static",
        static_response_json=response_json,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    assert any(
        "and_edges[1].requires must not contain duplicate primitives" in error
        and "exchangeability" in error
        for error in row["errors"]
    )


def test_llm_route_planner_rejects_unreachable_route_option() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_rejects_unreachable_route_option"
    )
    response_json = root / "bad_response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    bad_response = _llm_response_payload()
    graph = bad_response["minimal_delta_plan"]["and_or_cost_graph"]
    graph["or_nodes"][0]["choices"] = [
        "route_option:reuse_exchangeability_bridge_rank"
    ]
    response_json.write_text(json.dumps(bad_response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        provider_name="static",
        static_response_json=response_json,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    assert any(
        "or_nodes choices must reference every route option" in error
        and "route_option:source_port_rank_theory" in error
        for error in row["errors"]
    )


def test_llm_route_planner_rejects_nonminimal_route_option_cost() -> None:
    root = Path("runs/test_formalization_gap_planner_llm_route_planner_rejects_nonminimal_cost")
    response_json = root / "bad_response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    bad_response = _llm_response_payload()
    graph = bad_response["minimal_delta_plan"]["and_or_cost_graph"]
    graph["route_options"][1]["route_cost"] = 3
    graph["route_options"][1]["cost_rationale"] = (
        "This fixture intentionally makes an unselected route cheaper."
    )
    response_json.write_text(json.dumps(bad_response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        provider_name="static",
        static_response_json=response_json,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    assert any("selected route option is not minimal" in error for error in row["errors"])


def test_llm_route_planner_rejects_unrequested_residual_interpretations() -> None:
    root = Path("runs/test_formalization_gap_planner_llm_route_planner_rejects_unrequested_residual")
    response_json = root / "bad_response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    bad_response = _llm_response_payload()
    bad_response["residual_interpretations"] = [
        {
            "residual_goal": "invented side condition",
            "interpretation": "This residual was not in the request.",
            "route_repair": "Do not invent prover residuals.",
        }
    ]
    response_json.write_text(json.dumps(bad_response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        provider_name="static",
        static_response_json=response_json,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    assert any("residual_interpretations require request residual_goals" in error for error in row["errors"])


def test_llm_route_planner_rejects_unmatched_residual_interpretation() -> None:
    root = Path("runs/test_formalization_gap_planner_llm_route_planner_rejects_unmatched_residual")
    response_json = root / "bad_response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    interactive_session_dir = _write_interactive_session(root)
    bad_response = _llm_response_payload()
    bad_response["residual_interpretations"] = [
        {
            "residual_goal": "invented side condition",
            "interpretation": "This residual was not in the request.",
            "route_repair": "Do not invent prover residuals.",
        }
    ]
    response_json.write_text(json.dumps(bad_response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        provider_name="static",
        static_response_json=response_json,
        formalization_gap_planner_interactive_session_dir=interactive_session_dir,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    assert any("not present in request residual_goals" in error for error in row["errors"])
    assert any("missing request residual_goals" in error for error in row["errors"])


def test_llm_route_planner_rejects_off_scope_residual_target_primitives() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_rejects_residual_scope"
    )
    response_json = root / "bad_response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    interactive_session_dir = _write_interactive_session(root)
    bad_response = _llm_response_payload()
    bad_response["residual_interpretations"] = [
        {
            "residual_goal": "missing finite tie-breaking side condition",
            "interpretation": (
                "The residual is a local side condition for the rank route."
            ),
            "route_repair": (
                "Keep the repair bounded to the existing rank-uniformity route."
            ),
            "target_primitives": ["spectral_gap"],
            "residual_primitives": ["spectral_gap"],
            "formal_gap_boundary": (
                "The residual repair is bounded to the existing rank theorem "
                "side condition and needs separate source confirmation before adoption."
            ),
        }
    ]
    response_json.write_text(json.dumps(bad_response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        provider_name="static",
        static_response_json=response_json,
        formalization_gap_planner_interactive_session_dir=interactive_session_dir,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    assert any(
        "residual_interpretations[0].target_primitives must be drawn from request"
        in error
        and "spectral_gap" in error
        for error in row["errors"]
    )


def test_llm_route_planner_rejects_residual_formal_search_without_formal_library_request() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_rejects_residual_formal_without_search"
    )
    response_json = root / "bad_response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    interactive_session_dir = _write_interactive_session(root)
    bad_response = _llm_response_payload()
    bad_response["residual_interpretations"] = [
        {
            "residual_goal": "missing finite tie-breaking side condition",
            "interpretation": (
                "The proof-state residual shows the rank route still has an "
                "unresolved formal side condition."
            ),
            "route_repair": (
                "Search the target-prover library for the side-condition "
                "declarations before revising the bridge lemma."
            ),
            "target_primitives": ["rank_uniformity"],
            "source_refs": ["conformal_prediction_textbook"],
            "formal_search_status": "needs_search",
        }
    ]
    bad_response["search_requests"] = []
    response_json.write_text(json.dumps(bad_response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        provider_name="static",
        static_response_json=response_json,
        formalization_gap_planner_interactive_session_dir=interactive_session_dir,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    assert any(
        "residual_interpretations[0] unknown/formal-library-search-pending repair requires "
        "a matching formal_library/library search_request" in error
        for error in row["errors"]
    )


def test_llm_route_planner_accepts_residual_formal_search_with_structured_target_primitive_request() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_accepts_residual_formal_search"
    )
    response_json = root / "response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    interactive_session_dir = _write_interactive_session(root)
    response = _llm_response_payload()
    response["residual_interpretations"] = [
        {
            "residual_goal": "missing finite tie-breaking side condition",
            "interpretation": (
                "The proof-state residual shows the rank route still has an "
                "unresolved formal side condition."
            ),
            "route_repair": (
                "Search the target-prover library for the side-condition "
                "declarations before revising the bridge lemma."
            ),
            "target_primitives": ["rank_uniformity"],
            "source_refs": ["conformal_prediction_textbook"],
            "formal_search_status": "needs_search",
        }
    ]
    response["search_requests"].append(
        {
            "request_kind": "formal_library",
            "query": "search target-prover declarations for the residual side condition",
            "reason": "resolve the proof-state residual before route repair",
            "target_primitives": ["rank_uniformity"],
        }
    )
    response_json.write_text(json.dumps(response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        provider_name="static",
        static_response_json=response_json,
        formalization_gap_planner_interactive_session_dir=interactive_session_dir,
    )

    assert payload["all_ok"]
    assert payload["n_response_contract_ok"] == 1


def test_llm_route_planner_rejects_ungrounded_candidate_declarations() -> None:
    root = Path("runs/test_formalization_gap_planner_llm_route_planner_rejects_declarations")
    response_json = root / "bad_response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    bad_response = _llm_response_payload()
    bad_response["lean_realization_dag_nodes"][0]["candidate_declarations"] = [
        "Probability.inventedExchangeability"
    ]
    bad_response["standalone_route"]["primitives"][0]["candidate_declarations"] = [
        "Probability.inventedExchangeability"
    ]
    response_json.write_text(json.dumps(bad_response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        provider_name="static",
        static_response_json=response_json,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    assert any("ungrounded candidate_declarations" in error for error in row["errors"])


def test_llm_route_planner_rejects_wrong_target_candidate_declarations() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_rejects_wrong_target_declarations"
    )
    input_json = root / "standalone_input.json"
    response_json = root / "bad_response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "component_name": "formalization_gap_planner_standalone_input",
                "target_prover_family": "rocq",
                "library_snapshot_ref": "rocq:coq-community-probability",
                "routes": [
                    {
                        "route_id": "rocq_rank_route",
                        "display_name": "rocq_distribution_free_rank_bound",
                        "theorem_statement": "A Rocq rank bound follows from exchangeability.",
                        "source_refs": ["conformal_prediction_textbook"],
                        "source_snippets": [
                            {
                                "source_ref": "conformal_prediction_textbook",
                                "claim": "Exchangeability implies a uniform rank statistic.",
                                "excerpt": (
                                    "Under exchangeability, the rank of the test score "
                                    "among calibration scores is uniformly distributed "
                                    "up to the tie convention."
                                ),
                                "target_primitives": ["rank_uniformity"],
                            }
                        ],
                        "formal_declaration_hits": [
                            {
                                "declaration": "Probability.exchangeable",
                                "target_prover_family": "lean4",
                            }
                        ],
                        "primitives": [
                            {
                                "primitive": "exchangeability",
                                "coverage_status": "exact_exists",
                                "candidate_declarations": [
                                    "Rocq.Probability.exchangeable"
                                ],
                            },
                            {
                                "primitive": "rank_uniformity",
                                "coverage_status": "bridge_needed",
                                "expected_premises": ["exchangeability"],
                            },
                        ],
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    bad_response = _llm_response_payload()
    response_json.write_text(json.dumps(bad_response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        provider_name="static",
        static_response_json=response_json,
    )

    request = payload["request_packets"][0]
    assert "Rocq.Probability.exchangeable" in request["context_packet"][
        "available_formal_declarations"
    ]
    assert "Probability.exchangeable" not in request["context_packet"][
        "available_formal_declarations"
    ]
    assert any(
        row["declaration"] == "Probability.exchangeable"
        and row["target_prover_family"] == "lean4"
        for row in request["context_packet"]["available_formal_declaration_rows"]
    )
    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    assert any("ungrounded candidate_declarations" in error for error in row["errors"])


def test_llm_route_planner_rejects_non_lean_bare_candidate_declarations() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_rejects_rocq_bare_declarations"
    )
    response_json = root / "bad_response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    input_payload = json.loads(input_json.read_text(encoding="utf-8"))
    input_payload["target_prover_family"] = "rocq"
    input_payload["library_snapshot_ref"] = "rocq_probability_snapshot"
    input_payload["routes"][0]["target_prover_family"] = "rocq"
    input_payload["routes"][0]["primitives"][0]["candidate_declarations"] = [
        "Rocq.Probability.exchangeable"
    ]
    input_json.write_text(json.dumps(input_payload), encoding="utf-8")

    bad_response = _llm_response_payload()
    bad_response["formal_realization_dag_nodes"] = bad_response.pop(
        "lean_realization_dag_nodes"
    )
    for node in bad_response["formal_realization_dag_nodes"]:
        if node["primitive"] == "exchangeability":
            node["candidate_declarations"] = ["Rocq.Probability.exchangeable"]
            node.pop("candidate_declaration_rows", None)
    bad_response["standalone_route"]["target_prover_family"] = "rocq"
    bad_response["standalone_route"]["primitives"][0]["candidate_declarations"] = [
        "Rocq.Probability.exchangeable"
    ]
    bad_response["standalone_route"]["primitives"][0].pop(
        "candidate_declaration_rows",
        None,
    )
    _retarget_formal_attempt_queue(
        bad_response,
        target_prover_family="rocq",
        owner="rocq_lsp_serapi",
    )
    bad_response["search_requests"] = [
        {
            "request_kind": "formal_library",
            "owner": "rocq_lsp_serapi",
            "query": "rank_uniformity Rocq declaration search",
            "reason": "Search the Rocq library adapter for the target primitive.",
            "target_primitives": ["rank_uniformity"],
        }
    ]
    bad_response["planner_next_actions"] = [
        {
            "owner": "rocq_lsp_serapi",
            "action": "run Rocq proof-state feedback for the rank_uniformity bridge",
            "target_primitives": ["rank_uniformity"],
        }
    ]
    response_json.write_text(json.dumps(bad_response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        provider_name="static",
        static_response_json=response_json,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    error_text = "\n".join(row["errors"])
    assert "non-Lean target_prover_family rocq" in error_text
    assert "candidate_declaration_rows" in error_text
    assert "bare candidate_declarations are not sufficient" in error_text


def test_llm_route_planner_keeps_legacy_lean_declaration_hits_lean_scoped() -> None:
    route = {
        "route_id": "rocq_rank_route",
        "target_prover_family": "rocq",
        "primitives": [{"primitive": "exchangeability"}],
    }
    context_packet = {
        "resource_response_ledger_rows": [
            {
                "target_prover_family": "rocq",
                "formal_declaration_hits": [
                    {
                        "declaration": "Rocq.Probability.exchangeable",
                        "target_primitives": ["exchangeability"],
                    }
                ],
                "lean_declaration_hits": [
                    {
                        "declaration": "Mathlib.Probability.exchangeable",
                        "target_primitives": ["exchangeability"],
                    }
                ],
            }
        ]
    }

    declaration_rows = _available_formal_declaration_rows_for_context(
        route,
        context_packet,
        target_prover_family="rocq",
    )
    rows_by_declaration = {
        row["declaration"]: row for row in declaration_rows
    }

    assert rows_by_declaration["Rocq.Probability.exchangeable"][
        "target_prover_family"
    ] == "rocq"
    assert rows_by_declaration["Mathlib.Probability.exchangeable"][
        "target_prover_family"
    ] == "lean4"
    compatible = _target_compatible_formal_declaration_rows(
        declaration_rows,
        target_prover_family="rocq",
    )
    assert {
        row["declaration"] for row in compatible
    } == {"Rocq.Probability.exchangeable"}


def test_llm_route_planner_uses_route_level_targets_without_top_level_target() -> None:
    root = Path("runs/test_formalization_gap_planner_llm_route_planner_mixed_targets")
    out_dir = root / "llm_route_planner"
    input_json = root / "standalone_input.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "component_name": "formalization_gap_planner_standalone_input",
                "library_snapshot_ref": "portable:probability-snapshots",
                "routes": [
                    {
                        "route_id": "lean_rank_route",
                        "display_name": "lean_distribution_free_rank_bound",
                        "target_prover_family": "lean4",
                        "theorem_statement": (
                            "A Lean rank bound follows from exchangeability."
                        ),
                        "source_refs": ["conformal_prediction_textbook"],
                        "primitives": [
                            {
                                "primitive": "exchangeability",
                                "coverage_status": "exact_exists",
                                "candidate_declarations": [
                                    "Probability.exchangeable"
                                ],
                            }
                        ],
                    },
                    {
                        "route_id": "rocq_rank_route",
                        "display_name": "rocq_distribution_free_rank_bound",
                        "target_prover_family": "rocq",
                        "theorem_statement": (
                            "A Rocq rank bound follows from exchangeability."
                        ),
                        "source_refs": ["conformal_prediction_textbook"],
                        "primitives": [
                            {
                                "primitive": "exchangeability",
                                "coverage_status": "exact_exists",
                                "candidate_declarations": [
                                    "Rocq.Probability.exchangeable"
                                ],
                            }
                        ],
                    },
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        provider_name="static",
    )

    assert payload["n_request_packets"] == 2
    assert [request["target_prover_family"] for request in payload["request_packets"]] == [
        "lean4",
        "rocq",
    ]
    assert [
        request["context_packet"]["target_prover_family"]
        for request in payload["request_packets"]
    ] == ["lean4", "rocq"]
    assert "target_prover_family" not in payload["standalone_seed"]
    assert [
        route["target_prover_family"]
        for route in payload["standalone_seed"]["routes"]
    ] == ["lean4", "rocq"]


def test_llm_route_planner_rejects_existing_coverage_without_declaration() -> None:
    root = Path("runs/test_formalization_gap_planner_llm_route_planner_rejects_existing_without_declaration")
    response_json = root / "bad_response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    bad_response = _llm_response_payload()
    bad_response["lean_realization_dag_nodes"][0]["candidate_declarations"] = []
    bad_response["standalone_route"]["primitives"][0]["candidate_declarations"] = []
    response_json.write_text(json.dumps(bad_response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        provider_name="static",
        static_response_json=response_json,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    assert any(
        "existing-library coverage requires grounded candidate_declarations" in error
        for error in row["errors"]
    )


def test_llm_route_planner_rejects_reuse_from_resource_request_seed() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_rejects_resource_request_reuse"
    )
    response_json = root / "bad_response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    resource_request_queue_dir = _write_resource_request_queue(root)
    declaration_row = {
        "declaration": "Probability.rankUniformityBridge",
        "target_prover_family": "lean4",
        "source_field": "resource_request_candidate_declarations",
    }
    bad_response = _make_rank_uniformity_reuse_response(declaration_row)
    response_json.write_text(json.dumps(bad_response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        provider_name="static",
        static_response_json=response_json,
        formalization_gap_planner_resource_request_queue_dir=(
            resource_request_queue_dir
        ),
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    assert any(
        "existing-library coverage uses provisional or unsupported formal declaration evidence"
        in error
        for error in row["errors"]
    )


def test_llm_route_planner_rejects_wrong_primitive_formal_hit_reuse() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_rejects_wrong_primitive_hit"
    )
    response_json = root / "bad_response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    resource_response_ledger_dir = _write_resource_response_ledger(root)
    declaration_row = {
        "declaration": "Probability.rankUniformityBridge",
        "target_prover_family": "lean4",
        "source_field": "formal_declaration_hits",
    }
    bad_response = _llm_response_payload()
    bad_response["lean_realization_dag_nodes"][0].pop(
        "candidate_declarations", None
    )
    bad_response["lean_realization_dag_nodes"][0][
        "candidate_declaration_rows"
    ] = [declaration_row]
    bad_response["standalone_route"]["primitives"][0].pop(
        "candidate_declarations", None
    )
    bad_response["standalone_route"]["primitives"][0][
        "candidate_declaration_rows"
    ] = [declaration_row]
    bad_response["residual_interpretations"] = [
        {
            "residual_goal": "rank_uniformity: deterministic tie handling",
            "interpretation": "Accepted feedback says rank uniformity still needs deterministic tie handling.",
            "route_repair": "Keep rank_uniformity as a bridge until the side condition is replayed.",
            "source_refs": ["conformal_prediction_textbook"],
        }
    ]
    response_json.write_text(json.dumps(bad_response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        provider_name="static",
        static_response_json=response_json,
        formalization_gap_planner_resource_response_ledger_dir=(
            resource_response_ledger_dir
        ),
    )

    assert not payload["all_ok"]
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    error_text = "\n".join(row["errors"])
    assert "primitive-scoped formal declaration evidence" in error_text
    assert "not exchangeability" in error_text


def test_llm_route_planner_rejects_unsupported_primitive_formal_hit_reuse() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_rejects_unsupported_primitive_hit"
    )
    response_json = root / "bad_response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    declaration_row = {
        "declaration": "Probability.exchangeable",
        "target_prover_family": "lean4",
        "source_field": "formal_declaration_hits",
        "target_primitives": ["rank_uniformity"],
        "unsupported_target_primitives": ["rank_uniformity"],
    }
    input_payload = json.loads(input_json.read_text(encoding="utf-8"))
    input_payload["routes"][0]["primitives"][1]["formal_declaration_hits"] = [
        declaration_row
    ]
    input_json.write_text(json.dumps(input_payload, indent=2), encoding="utf-8")

    bad_response = _make_rank_uniformity_reuse_response(declaration_row)
    response_json.write_text(json.dumps(bad_response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        provider_name="static",
        static_response_json=response_json,
    )

    assert not payload["all_ok"]
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    error_text = "\n".join(row["errors"])
    assert "marked unsupported for rank_uniformity" in error_text


def test_llm_route_planner_accepts_reuse_from_accepted_formal_hit() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_accepts_formal_hit_reuse"
    )
    response_json = root / "response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    declaration_row = {
        "declaration": "Probability.rankUniformityBridge",
        "target_prover_family": "lean4",
        "source_field": "formal_declaration_hits",
    }
    input_payload = json.loads(input_json.read_text(encoding="utf-8"))
    rank_primitive = input_payload["routes"][0]["primitives"][1]
    rank_primitive["coverage_status"] = "exact_exists"
    rank_primitive["candidate_declaration_rows"] = [declaration_row]
    input_json.write_text(json.dumps(input_payload, indent=2), encoding="utf-8")
    response = _make_rank_uniformity_reuse_response(declaration_row)
    response_json.write_text(json.dumps(response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        provider_name="static",
        static_response_json=response_json,
    )

    assert payload["all_ok"]
    assert payload["n_response_contract_ok"] == 1


def test_llm_route_planner_rejects_unknown_formal_coverage_without_search_request() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_rejects_unknown_formal_without_search"
    )
    response_json = root / "bad_response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    bad_response = _llm_response_payload()
    bad_response["lean_realization_dag_nodes"][1]["coverage_bucket"] = "unknown"
    bad_response["lean_realization_dag_nodes"][1]["formalization_action"] = ""
    bad_response["standalone_route"]["primitives"][1]["coverage_status"] = "unknown"
    bad_response["search_requests"] = []
    response_json.write_text(json.dumps(bad_response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        provider_name="static",
        static_response_json=response_json,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    assert any(
        "unknown/formal-library-search-pending coverage requires a matching formal_library/library search_request"
        in error
        for error in row["errors"]
    )


def test_llm_route_planner_accepts_formal_source_search_for_formal_coverage() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_accepts_formal_source_for_formal_coverage"
    )
    response_json = root / "response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    response = _llm_response_payload()
    response["lean_realization_dag_nodes"][1][
        "formal_search_status"
    ] = "formal_library_search_pending"
    response["standalone_route"]["primitives"][1][
        "formal_search_status"
    ] = "formal_library_search_pending"
    response["search_requests"] = [
        {
            "request_kind": "formal_source",
            "query": "rank_uniformity Lean declaration formal source search",
            "reason": "search the formal source/library before deciding the bridge",
            "target_primitives": ["rank_uniformity"],
        }
    ]
    response_json.write_text(json.dumps(response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        provider_name="static",
        static_response_json=response_json,
    )

    assert payload["all_ok"]
    assert payload["n_response_contract_ok"] == 1


def test_llm_route_planner_rejects_unresolved_formal_coverage_masked_by_delta_action_without_search_request() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_rejects_unresolved_formal_masked_by_delta"
    )
    shutil.rmtree(root, ignore_errors=True)
    for marker in ("needs_search", "missing", "search_pending", "uncertain"):
        marker_root = root / marker
        response_json = marker_root / "bad_response.json"
        marker_root.mkdir(parents=True, exist_ok=True)
        input_json = _write_input(marker_root)
        bad_response = _llm_response_payload()
        bad_response["lean_realization_dag_nodes"][1]["coverage_bucket"] = marker
        bad_response["standalone_route"]["primitives"][1][
            "coverage_status"
        ] = marker
        bad_response["search_requests"] = []
        response_json.write_text(json.dumps(bad_response), encoding="utf-8")

        payload = export_formalization_gap_planner_llm_route_planner(
            input_json,
            provider_name="static",
            static_response_json=response_json,
        )

        assert not payload["all_ok"], marker
        assert payload["n_rejected"] == 1, marker
        row = payload["rows"][0]
        assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
        assert any(
            "formal_realization_dag_nodes[1] unknown/formal-library-search-pending coverage requires a matching formal_library/library search_request"
            in error
            for error in row["errors"]
        ), marker
        assert any(
            "standalone_route.primitives[1] unknown/formal-library-search-pending coverage requires a matching formal_library/library search_request"
            in error
            for error in row["errors"]
        ), marker


def test_llm_route_planner_rejects_free_text_formal_coverage_markers() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_rejects_free_text_formal_coverage"
    )
    response_json = root / "bad_response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    bad_response = _llm_response_payload()
    bad_response["lean_realization_dag_nodes"][1][
        "coverage_bucket"
    ] = "probably_reuse"
    bad_response["standalone_route"]["primitives"][1][
        "coverage_status"
    ] = "library_maybe_has_it"
    response_json.write_text(json.dumps(bad_response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        provider_name="static",
        static_response_json=response_json,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    assert row["response_contract_ok"] is False
    assert any(
        "formal_realization_dag_nodes[1].coverage_bucket unsupported: "
        "probably_reuse" in error
        for error in row["errors"]
    )
    assert any(
        "standalone_route.primitives[1].coverage_status unsupported: "
        "library_maybe_has_it" in error
        for error in row["errors"]
    )


def test_llm_route_planner_accepts_introduced_source_backed_bridge_primitive() -> None:
    root = Path("runs/test_formalization_gap_planner_llm_route_planner_accepts_new_bridge")
    response_json = root / "response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    response = _llm_response_payload()
    response["informal_knowledge_dag_nodes"].append(
        {
            "node_id": "informal:deterministic_tie_breaking",
            "claim": "The rank route fixes ties by a deterministic tie-breaking rule.",
            "depends_on": ["informal:rank_uniformity"],
            "source_refs": ["conformal_prediction_textbook"],
            "source_search_status": "SOURCE_BACKED",
            "semantic_role": "side_condition",
        }
    )
    response["informal_knowledge_dag_edges"].append(
        {
            "source_node_id": "informal:rank_uniformity",
            "target_node_id": "informal:deterministic_tie_breaking",
            "edge_kind": "requires",
            "rationale": (
                "The deterministic tie-breaking side condition specializes "
                "the source-backed rank-uniformity route."
            ),
        }
    )
    response["lean_realization_dag_nodes"].append(
        {
            "node_id": "formal:deterministic_tie_breaking_bridge",
            "primitive": "deterministic_tie_breaking",
            "coverage_bucket": "bridge",
            "candidate_declarations": [],
            "formalization_action": "prove_bridge",
        }
    )
    response["formal_realization_dag_edges"].append(
        {
            "source_node_id": "formal:rank_uniformity_bridge",
            "target_node_id": "formal:deterministic_tie_breaking_bridge",
            "edge_kind": "bridges",
            "rationale": (
                "The deterministic tie-breaking bridge is a downstream "
                "side-condition bridge for the rank-uniformity route."
            ),
        }
    )
    response["route_alignment_edges"].append(
        {
            "informal_node_id": "informal:deterministic_tie_breaking",
            "formal_node_id": "formal:deterministic_tie_breaking_bridge",
            "alignment_status": "bridge_needed",
            "alignment_rationale": "The textbook source supports the tie-breaking side condition.",
        }
    )
    response["minimal_delta_plan"]["selected_primitives"].append(
        "deterministic_tie_breaking"
    )
    response["minimal_delta_plan"]["bridge_lemmas"].append(
        (
            "deterministic_tie_breaking: prove a bridge lemma adding the "
            "deterministic tie-breaking side condition to the rank route"
        )
    )
    _append_bridge_cost(response, "deterministic_tie_breaking")
    response["standalone_route"]["primitives"].append(
        {
            "primitive": "deterministic_tie_breaking",
            "coverage_status": "bridge_needed",
            "source_refs": ["conformal_prediction_textbook"],
        }
    )
    response["formal_attempt_queue"].append(
        {
            "attempt_id": "attempt:deterministic_tie_breaking_bridge",
            "formal_node_id": "formal:deterministic_tie_breaking_bridge",
            "primitive": "deterministic_tie_breaking",
            "target_prover_family": "lean4",
            "owner": "lean_lsp_mcp",
            "action": (
                "lean_lsp proof-state attempt for deterministic_tie_breaking "
                "after rank_uniformity"
            ),
            "attempt_kind": "bridge_proof",
            "prerequisite_formal_node_ids": ["formal:rank_uniformity_bridge"],
            "expected_feedback": ["residual_goals", "missing_side_conditions"],
            "target_primitives": ["deterministic_tie_breaking"],
        }
    )
    _append_current_route_baseline_option(
        response,
        selected_primitives=[
            "exchangeability",
            "rank_uniformity",
            "deterministic_tie_breaking",
        ],
        route_cost=8,
    )
    response_json.write_text(json.dumps(response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        provider_name="static",
        static_response_json=response_json,
    )

    assert payload["all_ok"]
    assert payload["n_response_contract_ok"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "ACCEPTED_WITH_SEARCH_REQUESTS"


def test_llm_route_planner_rejects_introduced_primitive_with_vague_source_node() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_rejects_vague_source_node"
    )
    response_json = root / "bad_response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    bad_response = _llm_response_payload()
    primitive = "phantom_compactness"
    bad_response["informal_knowledge_dag_nodes"].append(
        {
            "node_id": "informal:source_backed_side_condition",
            "claim": (
                "A source-backed side condition is needed somewhere in this "
                "rank route."
            ),
            "depends_on": ["informal:rank_uniformity"],
            "source_refs": ["conformal_prediction_textbook"],
            "source_search_status": "SOURCE_BACKED",
            "semantic_role": "side_condition",
        }
    )
    bad_response["informal_knowledge_dag_edges"].append(
        {
            "source_node_id": "informal:rank_uniformity",
            "target_node_id": "informal:source_backed_side_condition",
            "edge_kind": "requires",
            "rationale": (
                "The vague side condition is downstream of the rank-uniformity "
                "route."
            ),
        }
    )
    bad_response["lean_realization_dag_nodes"].append(
        {
            "node_id": "formal:phantom_compactness_bridge",
            "primitive": primitive,
            "coverage_bucket": "bridge",
            "candidate_declarations": [],
            "formalization_action": "prove_bridge",
        }
    )
    bad_response["formal_realization_dag_edges"].append(
        {
            "source_node_id": "formal:rank_uniformity_bridge",
            "target_node_id": "formal:phantom_compactness_bridge",
            "edge_kind": "bridges",
            "rationale": (
                "The phantom compactness bridge is downstream of the rank "
                "uniformity bridge."
            ),
        }
    )
    bad_response["route_alignment_edges"].append(
        {
            "informal_node_id": "informal:source_backed_side_condition",
            "formal_node_id": "formal:phantom_compactness_bridge",
            "alignment_status": "bridge_needed",
            "alignment_rationale": (
                "The vague source-backed side condition is claimed to support "
                "the phantom_compactness bridge."
            ),
        }
    )
    bad_response["minimal_delta_plan"]["selected_primitives"].append(primitive)
    bad_response["minimal_delta_plan"]["bridge_lemmas"].append(
        "phantom_compactness: prove the claimed compactness bridge lemma"
    )
    _append_bridge_cost(bad_response, primitive)
    bad_response["standalone_route"]["primitives"].append(
        {
            "primitive": primitive,
            "coverage_status": "bridge_needed",
            "source_refs": ["conformal_prediction_textbook"],
        }
    )
    bad_response["formal_attempt_queue"].append(
        {
            "attempt_id": "attempt:phantom_compactness_bridge",
            "formal_node_id": "formal:phantom_compactness_bridge",
            "primitive": primitive,
            "target_prover_family": "lean4",
            "owner": "lean_lsp_mcp",
            "action": (
                "lean_lsp proof-state attempt for phantom_compactness after "
                "rank_uniformity"
            ),
            "attempt_kind": "bridge_proof",
            "prerequisite_formal_node_ids": ["formal:rank_uniformity_bridge"],
            "expected_feedback": ["residual_goals", "missing_side_conditions"],
            "target_primitives": [primitive],
        }
    )
    response_json.write_text(json.dumps(bad_response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        provider_name="static",
        static_response_json=response_json,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    assert any(
        "introduced primitive requires aligned informal evidence" in error
        and "explicit primitive scope" in error
        and primitive in error
        for error in row["errors"]
    )


def test_llm_route_planner_rejects_introduced_primitive_with_vague_formal_boundary() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_rejects_vague_formal_boundary"
    )
    response_json = root / "bad_response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    bad_response = _llm_response_payload()
    primitive = "phantom_compactness"
    bad_response["informal_knowledge_dag_nodes"].append(
        {
            "node_id": "informal:generic_formal_boundary_side_condition",
            "claim": (
                "The rank route has a local side condition boundary that needs "
                "separate handling."
            ),
            "depends_on": ["informal:rank_uniformity"],
            "source_search_status": "FORMAL_GAP_BOUNDARY",
            "formal_gap_boundary": (
                "The local side condition boundary for the rank route cannot "
                "be adopted until it is separately justified."
            ),
            "semantic_role": "side_condition",
        }
    )
    bad_response["informal_knowledge_dag_edges"].append(
        {
            "source_node_id": "informal:rank_uniformity",
            "target_node_id": "informal:generic_formal_boundary_side_condition",
            "edge_kind": "requires",
            "rationale": (
                "The generic formal boundary is downstream of the rank-uniformity "
                "route."
            ),
        }
    )
    bad_response["lean_realization_dag_nodes"].append(
        {
            "node_id": "formal:phantom_compactness_bridge",
            "primitive": primitive,
            "coverage_bucket": "bridge",
            "candidate_declarations": [],
            "formalization_action": "prove_bridge",
        }
    )
    bad_response["formal_realization_dag_edges"].append(
        {
            "source_node_id": "formal:rank_uniformity_bridge",
            "target_node_id": "formal:phantom_compactness_bridge",
            "edge_kind": "bridges",
            "rationale": (
                "The phantom compactness bridge is downstream of the rank "
                "uniformity bridge."
            ),
        }
    )
    bad_response["route_alignment_edges"].append(
        {
            "informal_node_id": "informal:generic_formal_boundary_side_condition",
            "formal_node_id": "formal:phantom_compactness_bridge",
            "alignment_status": "bridge_needed",
            "alignment_rationale": (
                "The generic formal boundary is claimed to support the "
                "phantom_compactness bridge."
            ),
        }
    )
    bad_response["minimal_delta_plan"]["selected_primitives"].append(primitive)
    bad_response["minimal_delta_plan"]["bridge_lemmas"].append(
        "phantom_compactness: prove the claimed compactness bridge lemma"
    )
    _append_bridge_cost(bad_response, primitive)
    bad_response["standalone_route"]["primitives"].append(
        {
            "primitive": primitive,
            "coverage_status": "bridge_needed",
            "formal_gap_boundary": (
                "phantom_compactness is a new formal bridge boundary for the "
                "selected route."
            ),
        }
    )
    bad_response["formal_attempt_queue"].append(
        {
            "attempt_id": "attempt:phantom_compactness_bridge",
            "formal_node_id": "formal:phantom_compactness_bridge",
            "primitive": primitive,
            "target_prover_family": "lean4",
            "owner": "lean_lsp_mcp",
            "action": (
                "lean_lsp proof-state attempt for phantom_compactness after "
                "rank_uniformity"
            ),
            "attempt_kind": "bridge_proof",
            "prerequisite_formal_node_ids": ["formal:rank_uniformity_bridge"],
            "expected_feedback": ["residual_goals", "missing_side_conditions"],
            "target_primitives": [primitive],
        }
    )
    response_json.write_text(json.dumps(bad_response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        provider_name="static",
        static_response_json=response_json,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    assert any(
        "introduced primitive requires aligned informal evidence" in error
        and "formal_gap_boundary naming/scoping" in error
        and primitive in error
        for error in row["errors"]
    )


def test_llm_route_planner_rejects_incoherent_selected_primitives() -> None:
    root = Path("runs/test_formalization_gap_planner_llm_route_planner_rejects_primitives")
    response_json = root / "bad_response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    bad_response = _llm_response_payload()
    bad_response["minimal_delta_plan"]["selected_primitives"] = [
        "exchangeability",
        "phantom_compactness",
    ]
    response_json.write_text(json.dumps(bad_response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        provider_name="static",
        static_response_json=response_json,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    assert any("standalone_route.primitives" in error for error in row["errors"])
    assert any("formal_realization_dag_nodes" in error for error in row["errors"])


def test_llm_route_planner_rejects_introduced_primitive_without_literature_search() -> None:
    root = Path("runs/test_formalization_gap_planner_llm_route_planner_rejects_new_without_search")
    response_json = root / "bad_response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    bad_response = _llm_response_payload()
    bad_response["informal_knowledge_dag_nodes"].append(
        {
            "node_id": "informal:phantom_compactness",
            "claim": "A compactness lemma is needed for this rank route.",
            "depends_on": ["informal:rank_uniformity"],
            "source_refs": [],
            "source_search_status": "SEARCH_REQUESTED",
            "semantic_role": "lemma",
        }
    )
    bad_response["lean_realization_dag_nodes"].append(
        {
            "node_id": "formal:phantom_compactness_bridge",
            "primitive": "phantom_compactness",
            "coverage_bucket": "bridge",
            "candidate_declarations": [],
            "formalization_action": "prove_bridge",
        }
    )
    bad_response["route_alignment_edges"].append(
        {
            "informal_node_id": "informal:phantom_compactness",
            "formal_node_id": "formal:phantom_compactness_bridge",
            "alignment_status": "bridge_needed",
            "alignment_rationale": "The LLM suspects a compactness bridge is needed.",
        }
    )
    bad_response["minimal_delta_plan"]["selected_primitives"].append(
        "phantom_compactness"
    )
    bad_response["minimal_delta_plan"]["bridge_lemmas"].append(
        "phantom_compactness: prove the suspected compactness bridge lemma"
    )
    _append_bridge_cost(bad_response, "phantom_compactness")
    bad_response["standalone_route"]["primitives"].append(
        {
            "primitive": "phantom_compactness",
            "coverage_status": "bridge_needed",
            "source_search_status": "SEARCH_REQUESTED",
        }
    )
    response_json.write_text(json.dumps(bad_response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        provider_name="static",
        static_response_json=response_json,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    assert any("introduced primitive requires aligned informal evidence" in error for error in row["errors"])


def test_llm_route_planner_rejects_introduced_selected_primitive_without_alignment() -> None:
    root = Path("runs/test_formalization_gap_planner_llm_route_planner_rejects_new_without_alignment")
    response_json = root / "bad_response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    bad_response = _llm_response_payload()
    bad_response["informal_knowledge_dag_nodes"].append(
        {
            "node_id": "informal:deterministic_tie_breaking",
            "claim": "The rank route fixes ties by a deterministic tie-breaking rule.",
            "depends_on": ["informal:rank_uniformity"],
            "source_refs": ["conformal_prediction_textbook"],
            "source_search_status": "SOURCE_BACKED",
            "semantic_role": "side_condition",
        }
    )
    bad_response["lean_realization_dag_nodes"].append(
        {
            "node_id": "formal:deterministic_tie_breaking_bridge",
            "primitive": "deterministic_tie_breaking",
            "coverage_bucket": "bridge",
            "candidate_declarations": [],
            "formalization_action": "prove_bridge",
        }
    )
    bad_response["minimal_delta_plan"]["selected_primitives"].append(
        "deterministic_tie_breaking"
    )
    _append_bridge_cost(bad_response, "deterministic_tie_breaking")
    bad_response["standalone_route"]["primitives"].append(
        {
            "primitive": "deterministic_tie_breaking",
            "coverage_status": "bridge_needed",
            "source_refs": ["conformal_prediction_textbook"],
        }
    )
    response_json.write_text(json.dumps(bad_response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        provider_name="static",
        static_response_json=response_json,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    assert any("introduced selected primitives require route_alignment_edges" in error for error in row["errors"])


def test_llm_route_planner_rejects_unaligned_delta_primitive() -> None:
    root = Path("runs/test_formalization_gap_planner_llm_route_planner_rejects_alignment")
    response_json = root / "bad_response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    bad_response = _llm_response_payload()
    bad_response["route_alignment_edges"] = [
        {
            "informal_node_id": "informal:exchangeability",
            "formal_node_id": "formal:exchangeability",
            "alignment_status": "already_exists",
            "alignment_rationale": "Exchangeability is already aligned.",
        }
    ]
    response_json.write_text(json.dumps(bad_response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        provider_name="static",
        static_response_json=response_json,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    assert any("delta primitives missing route_alignment_edges" in error for error in row["errors"])


def test_llm_route_planner_rejects_dangling_alignment_edge_endpoint() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_rejects_dangling_alignment_endpoint"
    )
    response_json = root / "bad_response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    bad_response = _llm_response_payload()
    bad_response["route_alignment_edges"][0][
        "formal_node_id"
    ] = "formal:missing_rank_uniformity_bridge"
    response_json.write_text(json.dumps(bad_response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        provider_name="static",
        static_response_json=response_json,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    assert any(
        "route_alignment_edges references unknown formal_node_id" in error
        for error in row["errors"]
    )


def test_llm_route_planner_rejects_placeholder_alignment_rationale() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_rejects_placeholder_alignment_rationale"
    )
    response_json = root / "bad_response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    bad_response = _llm_response_payload()
    bad_response["route_alignment_edges"][0]["alignment_rationale"] = "ok"
    response_json.write_text(json.dumps(bad_response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        provider_name="static",
        static_response_json=response_json,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    assert any(
        "route_alignment_edges[0].alignment_rationale must be substantive"
        in error
        for error in row["errors"]
    )


def test_llm_route_planner_rejects_unanchored_alignment_rationale() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_rejects_unanchored_alignment_rationale"
    )
    response_json = root / "bad_response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    bad_response = _llm_response_payload()
    bad_response["route_alignment_edges"][0]["alignment_rationale"] = (
        "Asymptotic compactness makes the argument convenient for a proof."
    )
    response_json.write_text(json.dumps(bad_response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        provider_name="static",
        static_response_json=response_json,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    assert any(
        "route_alignment_edges[0].alignment_rationale must mention an informal "
        "claim, formal primitive, declaration, coverage/action, or source-backed "
        "route anchor" in error
        for error in row["errors"]
    )


def test_llm_route_planner_rejects_alignment_edge_primitive_formal_node_mismatch() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_rejects_alignment_primitive_mismatch"
    )
    response_json = root / "bad_response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    bad_response = _llm_response_payload()
    bad_response["route_alignment_edges"][0][
        "formal_node_id"
    ] = "formal:exchangeability"
    bad_response["route_alignment_edges"][0]["primitive"] = "rank_uniformity"
    response_json.write_text(json.dumps(bad_response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        provider_name="static",
        static_response_json=response_json,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    assert any(
        "route_alignment_edges primitive/formal_node_id mismatch" in error
        and "rank_uniformity" in error
        and "formal:exchangeability" in error
        and "exchangeability" in error
        for error in row["errors"]
    )
    assert "rank_uniformity" in row["realization_coverage_witness"][
        "delta_primitives_missing_route_alignment_edge"
    ]


def test_llm_route_planner_rejects_alignment_edge_informal_scope_mismatch() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_llm_route_planner_rejects_alignment_informal_scope_mismatch"
    )
    response_json = root / "bad_response.json"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)
    bad_response = _llm_response_payload()
    bad_response["informal_knowledge_dag_nodes"][0]["target_primitives"] = [
        "exchangeability"
    ]
    bad_response["informal_knowledge_dag_nodes"][0][
        "unsupported_target_primitives"
    ] = ["rank_uniformity"]
    bad_response["route_alignment_edges"][0][
        "informal_node_id"
    ] = "informal:exchangeability"
    response_json.write_text(json.dumps(bad_response), encoding="utf-8")

    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        provider_name="static",
        static_response_json=response_json,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    assert any(
        "informal_node_id/formal_node_id primitive scope mismatch" in error
        and "informal:exchangeability" in error
        and "rank_uniformity" in error
        and "unsupported" in error
        for error in row["errors"]
    )
