from __future__ import annotations

import json
import shutil
from copy import deepcopy
from pathlib import Path

from ai_statistician.cli import main
from ai_statistician.formalization_gap_planner_llm_route_planner import (
    LLM_ROUTE_PLANNER_LEGACY_CONTEXT_FIELD_ALIASES,
    LLM_ROUTE_PLANNER_LEGACY_RESPONSE_FIELD_ALIASES,
    LLM_ROUTE_PLANNER_MANIFEST_SCHEMA_ID,
    LLM_ROUTE_PLANNER_REQUEST_SCHEMA_ID,
    LLM_ROUTE_PLANNER_RESPONSE_PAYLOAD_VALIDATION_MANIFEST_SCHEMA_ID,
    LLM_ROUTE_PLANNER_RESPONSE_PAYLOAD_VALIDATION_ROW_SCHEMA_ID,
    LLM_ROUTE_PLANNER_RESPONSE_PAYLOAD_SCHEMA_ID,
    LLM_ROUTE_PLANNER_RESPONSE_SCHEMA_ID,
    LLM_ROUTE_PLANNER_ROW_SCHEMA_ID,
    PROOF_EVIDENCE_BOUNDARY,
    ROUTE_ADOPTION_BLOCKER_REALIZATION_COVERAGE,
    ROUTE_ADOPTION_BLOCKER_SOURCE_GROUNDING,
    _available_formal_declaration_rows_for_context,
    _generator_model_for_request,
    _route_adoption_readiness,
    _target_compatible_formal_declaration_rows,
    export_formalization_gap_planner_llm_route_planner,
    llm_route_planner_manifest_json_schema,
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
        "route_alignment_edges": [
            {
                "informal_node_id": "informal:rank_uniformity",
                "formal_node_id": "formal:rank_uniformity_bridge",
                "alignment_status": "bridge_needed",
                "alignment_rationale": (
                    "The library has exchangeability but not the exact finite-rank "
                    "statement, so a bridge lemma is the minimal new Lean work."
                ),
            }
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
                    }
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
            }
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
    graph = minimal_delta["and_or_cost_graph"]
    assert isinstance(graph, dict)
    route_options = graph["route_options"]
    assert isinstance(route_options, list)
    for option in route_options:
        option["route_cost"] = int(option["route_cost"]) + total_cost
        option["selected_primitives"] = [
            *option.get("selected_primitives", []),
            primitive,
        ]
    graph["and_edges"].append(
        {
            "route_option_id": graph["selected_route_option_id"],
            "requires": [primitive],
        }
    )


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
    response["route_alignment_edges"].append(
        {
            "informal_node_id": "informal:exchangeability",
            "formal_node_id": "formal:exchangeability",
            "alignment_status": "exact",
            "alignment_rationale": (
                "The exchangeability assumption maps to the existing formal "
                "declaration listed in the request context."
            ),
        }
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
    response["lean_realization_dag_nodes"] = [
        response["lean_realization_dag_nodes"][0]
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
    response["standalone_route"]["primitives"] = [
        response["standalone_route"]["primitives"][0]
    ]
    response["standalone_route"]["theorem_statement"] = (
        "A distribution-free rank bound follows from exchangeability."
    )
    return response


def _promote_response_to_source_port_costs(response: dict[str, object]) -> None:
    for node in response.get("lean_realization_dag_nodes", []):
        if isinstance(node, dict):
            node["coverage_bucket"] = "source_port_needed"
            node["formalization_action"] = "port_external_source"
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
    assert payload["by_request_model_tier"] == {"sonnet": 1}
    assert payload["n_request_packets"] == 1
    assert payload["n_requests_with_context_packet_inventory"] == 1
    assert payload["n_requests_with_route_planning_brief"] == 1
    assert payload["n_request_route_planning_focus_rows"] >= 4
    assert payload["n_request_route_planning_evidence_gaps"] == 0
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
    request = payload["request_packets"][0]
    assert "LLM route planner" in request["prompt_messages"]["system"]
    assert "required_output_contract" in request["prompt_messages"]["user"]
    assert request["minimal_delta_cost_policy"]["cost_policy_id"] == (
        "formalization_gap_planner_minimal_delta_cost_policy:1"
    )
    assert "minimal_delta_cost_policy" in request["prompt_messages"]["user"]
    assert "primitive_costs" in request["prompt_messages"]["user"]
    context = request["context_packet"]
    assert context["current_route"]["route_id"] == "rank_route"
    brief = context["route_planning_brief"]
    assert brief["brief_kind"] == (
        "formalization_gap_planner_llm_route_planner_route_planning_brief"
    )
    assert brief["route_id"] == "rank_route"
    assert brief["target_prover_family"] == "lean4"
    assert brief["evidence_summary"]["source_ref_count"] == len(
        context["available_source_refs"]
    )
    assert brief["evidence_summary"]["formal_declaration_row_count"] == len(
        context["available_formal_declaration_rows"]
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
    assert inventory["primitive_cost_hint_count"] == 2
    assert inventory["route_option_cost_hint_count"] == 1
    assert inventory["library_alignment_summary_present"] is True
    assert inventory["library_alignment_primitive_count"] == 2
    assert inventory["library_alignment_reuse_ready_count"] == 1
    assert inventory["library_alignment_bridge_count"] == 1
    assert inventory["library_alignment_bridge_or_harder_count"] == 1
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
    assert alignment_summary["summary_kind"] == (
        "formalization_gap_planner_llm_route_planner_library_alignment_summary"
    )
    assert alignment_summary["n_primitives"] == 2
    assert alignment_summary["n_reuse_ready_primitives"] == 1
    assert alignment_summary["n_bridge_primitives"] == 1
    assert alignment_summary["n_bridge_or_harder_primitives"] == 1
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
    assert "minimum_base_cost" in request["prompt_messages"]["user"]
    assert "context_packet_inventory" in request["prompt_messages"]["user"]
    assert "route_planning_brief" in request["prompt_messages"]["user"]
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
    assert {"codex", "codex_exec"}.issubset(
        set(generation_policy["prohibited_generator_providers"])
    )
    assert {"codex", "codex_exec"}.isdisjoint(
        set(generation_policy["supported_live_generator_providers"])
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
    assert alignment_summary["n_primitives"] == 2
    assert alignment_summary["n_bridge_primitives"] == 1
    assert alignment_summary["n_bridge_or_harder_primitives"] == 1
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
    prompt_text = request["prompt_messages"]["user"]
    assert "context_packet.target_intake_rows" in prompt_text
    assert "normalized_assumptions" in prompt_text
    assert "formal_library_grounding_queries" in prompt_text
    assert "legacy alias" in prompt_text
    assert "target intake is not proof evidence" in prompt_text


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
    request = payload["request_packets"][0]
    registry_context = request["context_packet"][
        "component_resource_registry_context"
    ]
    resource_ids = {
        row["resource_id"] for row in registry_context["resource_rows"]
    }
    assert "paperclip_cli_mcp" in resource_ids
    assert "lean_lsp_mcp" in resource_ids
    assert any(
        row["component_id"] == "literature_grounded_route_synthesis"
        for row in registry_context["component_rows"]
    )
    assert any(
        row["resource_id"] == "paperclip_cli_mcp"
        for row in registry_context["resource_contract_rows"]
    )
    assert "component_resource_registry_context" in request["prompt_messages"]["user"]
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
        if response.get("llm_route_planner_hook_trace")
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
        if row.get("llm_route_planner_hook_trace")
    )
    assert tuple(evidence_row["target_primitives"]) == ("rank_uniformity",)
    assert evidence_row["llm_route_planner_hook_trace"] == hook_trace
    proposal = next(
        row
        for row in evidence_payload["route_revision_proposals"]
        if row.get("llm_route_planner_hook_trace")
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
    assert overlay_payload["n_applied_llm_route_planner_hook_traces"] == 1
    overlay_row = next(
        row
        for row in overlay_payload["rows"]
        if row.get("applied_llm_route_planner_hook_traces")
    )
    assert list(overlay_row["applied_llm_route_planner_hook_traces"]) == [hook_trace]
    handoff_dir = root / "route_replan_handoff_from_action_only_llm_seed"
    handoff_payload = export_formalization_gap_planner_route_replan_handoff(
        plan_dir,
        overlay_dir,
        handoff_dir,
    )
    assert handoff_payload["all_ok"]
    assert handoff_payload["n_applied_llm_route_planner_hook_traces"] == 1
    handoff_row = next(
        row
        for row in handoff_payload["rows"]
        if row.get("applied_llm_route_planner_hook_traces")
    )
    assert list(handoff_row["applied_llm_route_planner_hook_traces"]) == [hook_trace]
    handoff_seed_route = handoff_payload["standalone_seed"]["routes"][0]
    assert handoff_seed_route["replan_metadata"][
        "applied_llm_route_planner_hook_traces"
    ] == [hook_trace]
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
        == 1
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
        == 1
    )
    assert replan_feedback_summary["prior_replan_metadata"][
        "applied_llm_route_planner_hook_traces"
    ] == [hook_trace]
    assert (
        "applied_llm_route_planner_hook_traces"
        in replan_request["prompt_messages"]["user"]
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
    assert payload["n_feedback_loop_summary_source_snippets"] == 1
    assert payload["n_requests_with_available_source_snippets"] == 1
    assert payload["n_request_available_source_snippets"] >= 2
    request = payload["request_packets"][0]
    context = request["context_packet"]
    inventory = context["context_packet_inventory"]
    assert inventory["row_counts"]["resource_response_ledger_rows"] == 1
    assert inventory["residual_goal_count"] == 1
    assert inventory["feedback_loop_summary_replan_required"] is True
    ledger_row = context["resource_response_ledger_rows"][0]
    assert ledger_row["response_present"] is True
    assert ledger_row["response_contract_ok"] is True
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
    assert summary["admissible_source_refs"] == ["conformal_prediction_textbook"]
    assert summary["admissible_source_snippets"][0]["source_ref"] == (
        "conformal_prediction_textbook"
    )
    assert "exchangeability implies rank uniformity" in summary[
        "admissible_source_snippets"
    ][0]["claim"]
    assert "feedback_loop_summary" in request["prompt_messages"]["user"]
    assert "status-only; do not use them as residual-goal" in request[
        "prompt_messages"
    ]["user"]


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
    )
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
    response["residual_interpretations"] = [
        {
            "residual_goal": (
                "rank_uniformity: tie handling side condition from refinement evidence"
            ),
            "interpretation": "The refinement evidence identifies deterministic tie handling as a missing side condition.",
            "route_repair": "Add deterministic tie handling as a source-backed assumption before proving the bridge lemma.",
            "source_refs": [source_ref],
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
    request = payload["request_packets"][0]
    context = request["context_packet"]
    assert context["interactive_session_rows"][0]["next_interaction_kind"] == "proof_state_feedback"
    assert context["interactive_decision_policy_rows"][0]["resource_contract_ids"] == [
        "lean_lsp:proof_state_feedback"
    ]
    assert tuple(context["residual_goals"]) == ("missing finite tie-breaking side condition",)
    assert context["feedback_loop_summary"]["needs_more_proof_state_feedback"] is True
    assert context["feedback_loop_summary"]["recommended_next_actions"][0]["owner"] == (
        "formal_verifier"
    )
    assert "interactive_decision_policy_rows" in request["prompt_messages"]["user"]


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

    replan_response = _llm_response_payload()
    replan_response["source_snippets"] = []
    for node in replan_response.get("informal_knowledge_dag_nodes", []):
        if isinstance(node, dict):
            node.pop("source_snippets", None)
    standalone_replan_route = replan_response.get("standalone_route", {})
    if isinstance(standalone_replan_route, dict):
        standalone_replan_route.pop("source_snippets", None)
        for primitive in standalone_replan_route.get("primitives", []):
            if isinstance(primitive, dict):
                primitive.pop("source_snippets", None)
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
    handoff_rows = replan_context["route_replan_handoff_rows"]
    assert len(handoff_rows) == 1
    assert handoff_rows[0]["route_replan_handoff_id"].startswith(
        "formalization_gap_planner_route_replan_handoff:"
    )
    assert handoff_rows[0]["route_revision_overlay_id"] == (
        handoff_row["route_revision_overlay_id"]
    )
    assert handoff_rows[0]["next_commands"]
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
    replan_row = replan_payload["rows"][0]
    assert replan_row["response_contract_ok"] is True
    assert replan_row["planner_next_actions"][0]["quality_gates"] == [
        "response_schema_valid"
    ]


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
    response["planner_next_actions"] = []
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
    assert row["acceptance_status"] == "ACCEPTED_WITH_RESIDUAL_REPAIR"
    assert row["route_adoption_status"] == (
        "PENDING_REFINEMENT_BEFORE_ROUTE_ADOPTION"
    )
    assert "residual_interpretations_require_route_replay" in row[
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


def test_llm_route_planner_api_rejects_codex_generator_alias() -> None:
    root = Path("runs/test_formalization_gap_planner_llm_route_planner_api_codex")
    out_dir = root / "out"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json = _write_input(root)

    try:
        export_formalization_gap_planner_llm_route_planner(
            input_json,
            out_dir,
            provider_name="codex_exec",
        )
    except ValueError as exc:
        assert "Codex/Codex exec are not accepted as pure LLM" in str(exc)
    else:
        raise AssertionError("Codex exec must not be accepted through the API")
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
    assert llm_route_planner_manifest_json_schema()["$id"] == (
        LLM_ROUTE_PLANNER_MANIFEST_SCHEMA_ID
    )
    assert "legacy_context_field_aliases" in manifest_schema["required"]
    assert "n_requests_with_legacy_context_field_aliases" in manifest_schema["required"]
    assert "n_requests_with_route_planning_brief" in manifest_schema["required"]
    assert "n_request_route_planning_focus_rows" in manifest_schema["required"]
    assert "n_request_route_planning_evidence_gaps" in manifest_schema["required"]
    assert (
        "n_request_llm_generation_policy_current_claude_tier_source"
        in manifest_schema["required"]
    )
    assert payload["n_requests_with_route_planning_brief"] == 1
    assert payload["n_request_route_planning_focus_rows"] >= 4
    assert "repair_attempt_ledger" in manifest_schema["required"]
    assert "n_repair_attempt_ledger_rows" in manifest_schema["required"]
    assert "standalone_replay_gate" in manifest_schema["required"]
    assert "standalone_replay_gate_ok" in manifest_schema["required"]
    assert payload["repair_attempt_ledger"] == ()
    assert payload["n_repair_attempt_ledger_rows"] == 0
    assert payload["n_requests_with_repair_attempt_ledger"] == 0
    assert payload["n_repair_attempt_ledger_error_items"] == 0
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
    drifted_repair_ledger_manifest = deepcopy(payload)
    drifted_repair_ledger_manifest["n_repair_attempt_ledger_rows"] = 1
    assert (
        "n_repair_attempt_ledger_rows must match repair_attempt_ledger"
        in validate_llm_route_planner_manifest(
            drifted_repair_ledger_manifest,
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
    assert payload["n_lean_realization_dag_nodes"] == 2
    assert (
        payload["legacy_response_field_aliases"]
        == LLM_ROUTE_PLANNER_LEGACY_RESPONSE_FIELD_ALIASES
        == {"lean_realization_dag_nodes": "formal_realization_dag_nodes"}
    )
    assert payload["n_route_alignment_edges"] == 1
    assert payload["n_rows_with_realization_coverage_witness"] == 1
    assert payload["n_rows_with_complete_realization_coverage"] == 1
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
    assert "conformal_prediction_textbook" in row["source_refs"]
    assert row["context_packet_inventory"] == payload["request_packets"][0][
        "context_packet"
    ]["context_packet_inventory"]
    assert row["context_packet_inventory"]["inventory_kind"] == (
        "formalization_gap_planner_llm_route_planner_context_packet_inventory"
    )
    assert validate_llm_route_planner_row(
        row,
        llm_route_planner_row_json_schema(),
    ) == []
    row_schema = llm_route_planner_row_json_schema()
    assert "formal_realization_dag_nodes" in row_schema["required"]
    assert "lean_realization_dag_nodes" not in row_schema["required"]
    assert "source_snippets" in row_schema["required"]
    assert "realization_coverage_witness" in row_schema["required"]
    assert "context_packet_inventory" in row_schema["required"]
    assert "model_tier_decision_evidence" in row_schema["required"]
    assert row_schema["properties"]["model_tier_decision_evidence"]["type"] == "object"
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
    manifest_schema = llm_route_planner_manifest_json_schema()
    assert "legacy_response_field_aliases" in manifest_schema["required"]
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
    assert metadata["revised_informal_knowledge_dag_nodes"][0]["node_source"] == (
        "llm_route_planner_revised_informal_dag"
    )

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
    assert payload["n_request_bound_payloads_with_context_packet_inventory"] == 0
    assert payload["n_request_bound_payload_context_inventory_total_rows"] == 0
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
    assert row["n_schema_errors"] == 0
    assert row["n_request_context_errors"] == 0
    row_schema = payload["response_payload_validation_row_schema"]
    assert row_schema["properties"]["n_errors"]["minimum"] == 0
    assert row_schema["properties"]["payload_index"]["minimum"] == 0
    assert row_schema["properties"]["target_prover_family_consistent"][
        "type"
    ] == "boolean"
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
    assert row["n_schema_errors"] == 1
    assert row["n_request_context_errors"] == 0
    assert any(
        "lean_realization_dag_nodes is a Lean-only legacy alias" in error
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
    assert row["n_schema_errors"] == 0
    assert row["n_request_context_errors"] >= 1
    assert any(
        "baseline route option" in error and "rank_uniformity" in error
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


def test_llm_route_planner_marks_clean_accepted_route_adoption_ready() -> None:
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
    assert payload["n_route_adoption_ready"] == 1
    assert payload["n_route_adoption_pending_refinement"] == 0
    assert payload["standalone_replay_gate_ok"] is True
    assert payload["n_standalone_replay_route_candidates"] == 1
    assert payload["n_standalone_replay_adoptable_route_candidates"] == 1
    assert payload["n_standalone_replay_blocked_route_candidates"] == 0
    assert payload["standalone_replay_gate_blockers"] == []
    assert payload["standalone_replay_gate"]["gate_status"] == (
        "READY_FOR_STANDALONE_REPLAY"
    )
    assert (
        payload["standalone_replay_gate"][
            "selected_route_adoptable_for_standalone_replay"
        ]
        is True
    )
    assert payload["by_route_adoption_status"] == {
        "READY_FOR_STANDALONE_REPLAY": 1
    }
    row = payload["rows"][0]
    assert row["acceptance_status"] == "ACCEPTED_LLM_ROUTE_PLAN"
    assert row["route_adoption_status"] == "READY_FOR_STANDALONE_REPLAY"
    assert row["route_adoption_blockers"] == ()
    seed_route = payload["standalone_seed"]["routes"][0]
    assert (
        seed_route["llm_route_planner_route_adoption_status"]
        == "READY_FOR_STANDALONE_REPLAY"
    )
    assert seed_route["replan_metadata"][
        "llm_route_planner_route_adoption_blockers"
    ] == []
    selection = payload["standalone_seed"][
        "llm_route_planner_seed_route_selection"
    ]
    assert selection["selected_route_adoptable_for_standalone_replay"] is True
    assert selection["n_adoptable_route_candidates"] == 1
    assert selection["n_selected_route_candidates_not_adoptable"] == 0
    assert (
        selection["selection_rows"][0]["adoptable_for_standalone_replay"]
        is True
    )
    assert (
        seed_route["llm_route_planner_seed_adoptable_for_standalone_replay"]
        is True
    )

    plan_dir = root / "standalone_plan_from_ready_llm_seed"
    plan_payload = export_formalization_gap_planner_standalone_plan(
        out_dir / "formalization_gap_planner_llm_route_planner_standalone_seed.json",
        plan_dir,
    )
    assert plan_payload["all_ok"]
    assert plan_payload[
        "n_standalone_input_traces_ready_for_route_adoption"
    ] == 1
    assert plan_payload[
        "n_standalone_input_traces_pending_refinement_before_route_adoption"
    ] == 0
    assert (
        plan_payload[
            "n_standalone_input_traces_llm_seed_adoptable_for_standalone_replay"
        ]
        == 1
    )
    assert (
        plan_payload[
            "n_standalone_input_traces_llm_seed_selected_not_adoptable"
        ]
        == 0
    )
    trace = plan_payload["rows"][0]["standalone_input_trace"]
    assert trace["llm_route_planner_route_adoption_status"] == (
        "READY_FOR_STANDALONE_REPLAY"
    )
    assert trace["llm_route_planner_route_adoption_blockers"] == []
    assert trace["llm_route_planner_seed_adoptable_for_standalone_replay"] is True


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
    assert selection["selected_route_adoptable_for_standalone_replay"] is True
    assert selection["n_adoptable_route_candidates"] == 2
    assert selection["n_selected_route_candidates_not_adoptable"] == 0
    assert selection["selected_minimal_delta_route_cost"] == 4.0
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
        is True
    )
    assert seed_routes[0]["llm_route_planner_seed_selection_rank"] == 1
    assert seed_routes[0]["replan_metadata"][
        "llm_route_planner_seed_minimal_delta_route_cost"
    ] == 4.0
    assert seed_routes[1]["llm_route_planner_seed_selected"] is False
    assert (
        seed_routes[1]["llm_route_planner_seed_adoptable_for_standalone_replay"]
        is True
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
        == 2
    )
    assert (
        plan_payload[
            "n_standalone_input_traces_llm_seed_selected_not_adoptable"
        ]
        == 0
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
    ] == [True, True]
    assert [
        trace["llm_route_planner_seed_minimal_delta_route_cost"]
        for trace in traces
    ] == [4.0, 8.0]

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
    assert row["acceptance_status"] == "ACCEPTED_LLM_ROUTE_PLAN"
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
    assert payload["n_route_adoption_ready"] == 0
    assert payload["n_route_adoption_pending_refinement"] == 1
    assert payload["n_route_adoption_pending_residual_repair_blockers"] == 1
    assert payload["n_route_adoption_pending_source_grounding_blockers"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "ACCEPTED_WITH_RESIDUAL_REPAIR"
    assert row["route_adoption_status"] == (
        "PENDING_REFINEMENT_BEFORE_ROUTE_ADOPTION"
    )
    assert set(row["route_adoption_blockers"]) >= {
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
    inventory = context["context_packet_inventory"]
    assert inventory["source_grounding_obligation_pending"] is True
    assert inventory["residual_source_grounding_unresolved_count"] == 1
    assert ROUTE_ADOPTION_BLOCKER_SOURCE_GROUNDING in payload[
        "route_adoption_blocker_values"
    ]
    seed_route = payload["standalone_seed"]["routes"][0]
    assert set(
        seed_route["replan_metadata"]["llm_route_planner_route_adoption_blockers"]
    ) >= {
        "residual_interpretations_require_route_replay",
        ROUTE_ADOPTION_BLOCKER_SOURCE_GROUNDING,
    }


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
    trigger_schema = schema["properties"]["blocker_trigger_fields"]
    assert trigger_schema["additionalProperties"] is False
    assert trigger_schema["properties"][
        ROUTE_ADOPTION_BLOCKER_REALIZATION_COVERAGE
    ]["const"] == trigger_fields

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
    response["planner_next_actions"] = []
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
    pending_row = pending_payload["rows"][0]
    assert pending_row["acceptance_status"] == "ACCEPTED_LLM_ROUTE_PLAN"
    assert pending_row["route_adoption_status"] == (
        "PENDING_REFINEMENT_BEFORE_ROUTE_ADOPTION"
    )
    assert pending_row["route_adoption_blockers"] == (
        "quality_control_obligations_pending",
    )
    pending_summary = pending_payload["request_packets"][0]["context_packet"][
        "feedback_loop_summary"
    ]["quality_control_obligations"]
    assert pending_summary["pending"] is True
    assert pending_summary["pending_quality_controls"]["required_quality_signals"] == [
        "diagnostic_signature"
    ]
    pending_inventory = pending_payload["request_packets"][0]["context_packet"][
        "context_packet_inventory"
    ]
    assert pending_inventory["quality_control_obligation_present"] is True
    assert pending_inventory["quality_control_obligation_pending"] is True
    assert pending_inventory["quality_control_obligation_discharged"] is False
    assert pending_inventory["quality_control_obligation_field_count"] == 5
    assert pending_inventory["quality_control_obligation_value_count"] == 5
    assert pending_inventory["pending_quality_control_field_count"] == 5
    assert pending_inventory["pending_quality_control_value_count"] == 5
    assert pending_inventory["discharged_quality_control_field_count"] == 0
    assert pending_inventory["discharged_quality_control_value_count"] == 0
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
        == ["quality_control_obligations_pending"]
    )
    seed_route = pending_payload["standalone_seed"]["routes"][0]
    assert seed_route["replan_metadata"]["quality_controls"] == quality_controls
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
    assert quality_hook["quality_controls"] == quality_controls
    assert "diagnostic_signature" in " ".join(quality_hook["queries"])
    assert any(
        trigger.get("trigger_kind") == "quality_control_evidence_required"
        for trigger in seed_route["route_revision_triggers"]
    )

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

    discharged_payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        discharged_dir,
        provider_name="static",
        static_response_json=response_json,
        formalization_gap_planner_resource_response_ledger_dir=ledger_dir,
    )

    assert discharged_payload["all_ok"]
    assert discharged_payload["n_route_adoption_ready"] == 1
    assert discharged_payload["n_route_adoption_pending_refinement"] == 0
    assert discharged_payload["n_route_adoption_pending_quality_control_blockers"] == 0
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
    assert discharged_row["route_adoption_status"] == "READY_FOR_STANDALONE_REPLAY"
    assert discharged_row["route_adoption_blockers"] == ()
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
    assert row["acceptance_status"] == "ACCEPTED_LLM_ROUTE_PLAN"
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
    response["planner_next_actions"] = []
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
    assert row["acceptance_status"] == "ACCEPTED_LLM_ROUTE_PLAN"
    assert row["route_adoption_status"] == (
        "PENDING_REFINEMENT_BEFORE_ROUTE_ADOPTION"
    )
    assert set(row["route_adoption_blockers"]) >= {
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
    response["lean_realization_dag_nodes"].append(
        {
            "node_id": "formal:rank_order_statistic",
            "primitive": "rank_order_statistic",
            "coverage_bucket": "already_exists",
            "candidate_declaration_rows": [helper_declaration_row],
            "formalization_action": "reuse",
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
    )
    assert "Rocq/coq-lsp proof-state adapter" in proof_hook["recommended_tools"]
    assert "lean-lsp-mcp" not in proof_hook["recommended_tools"]
    assert "lake build" not in proof_hook["recommended_tools"]


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
    response["search_requests"] = [
        {
            "request_kind": "lean_search",
            "query": "LeanSearch-style rank_uniformity query for Rocq exchangeability",
            "reason": "reuse the LLM vocabulary but search the target Rocq library",
        }
    ]
    response["planner_next_actions"] = [
        {
            "owner": "formal_retrieval",
            "action": "run LeanSearch-style declaration query against the Rocq adapter",
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
        "route_alignment_edges",
        "minimal_delta_plan",
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
    assert set(seed_metadata["llm_route_planner_generator_metadata_keys"]) >= {
        "generator_only",
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
    }
    row = payload["rows"][0]
    assert row["model_tier"] == "haiku"
    assert row["model"] == "claude-haiku-4-5-20251001"
    assert row["model_tier_decision_evidence"] == packet[
        "model_tier_decision_evidence"
    ]
    request = captured["request"]
    assert request.model == "claude-haiku-4-5-20251001"
    assert request.metadata["model_tier"] == "haiku"


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
            "target_primitives": ["rank_uniformity"],
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
    assert row["acceptance_status"] == "ACCEPTED_LLM_ROUTE_PLAN"
    assert row["response_contract_ok"] is True
    assert row["route_adoption_status"] == (
        "PENDING_REFINEMENT_BEFORE_ROUTE_ADOPTION"
    )
    assert set(row["route_adoption_blockers"]) == {
        "omitted_cost_hint_primitives_require_review"
    }
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
    ] == ["omitted_cost_hint_primitives_require_review"]
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
    response["lean_realization_dag_nodes"].append(
        {
            "node_id": "formal:deterministic_tie_breaking_bridge",
            "primitive": "deterministic_tie_breaking",
            "coverage_bucket": "bridge",
            "candidate_declarations": [],
            "formalization_action": "prove_bridge",
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
