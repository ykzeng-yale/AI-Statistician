from __future__ import annotations

import json
import shutil
from pathlib import Path

from ai_statistician.cli import main
from ai_statistician.formalization_gap_planner_llm_route_planner import (
    LLM_ROUTE_PLANNER_REQUEST_SCHEMA_ID,
    LLM_ROUTE_PLANNER_RESPONSE_SCHEMA_ID,
    LLM_ROUTE_PLANNER_ROW_SCHEMA_ID,
    PROOF_EVIDENCE_BOUNDARY,
    export_formalization_gap_planner_llm_route_planner,
    llm_route_planner_row_json_schema,
    validate_llm_route_planner_row,
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
    validate_standalone_input_payload,
)
from ai_statistician.formalization_gap_planner_source_grounding_audit import (
    audit_formalization_gap_planner_source_grounding,
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
            "bridge_lemmas": ["rank_uniformity"],
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
                        "route_evidence_nodes": [
                            {
                                "node_id": "paperclip:rank_uniformity",
                                "claim": "finite rank uniformity needs deterministic tie handling",
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
                                "evidence_role": "source-backed informal route evidence",
                            }
                        ],
                        "route_evidence_nodes": [
                            {
                                "node_id": "refinement-source:rank_uniformity",
                                "kind": "source_ref",
                                "source_ref": source_ref,
                                "claim": "finite-rank uniformity route evidence",
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
                "n_resource_request_rows": 1,
                "rows": [
                    {
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
    assert payload["n_requests_with_available_source_snippets"] == 1
    assert payload["n_request_available_source_snippets"] == 1
    assert payload["n_response_present"] == 0
    assert payload["n_awaiting_llm_response"] == 1
    assert payload["n_request_schema_valid"] == 1
    assert payload["request_schema"]["$id"] == LLM_ROUTE_PLANNER_REQUEST_SCHEMA_ID
    request = payload["request_packets"][0]
    assert "LLM route planner" in request["prompt_messages"]["system"]
    assert "required_output_contract" in request["prompt_messages"]["user"]
    assert request["minimal_delta_cost_policy"]["cost_policy_id"] == (
        "formalization_gap_planner_minimal_delta_cost_policy:1"
    )
    assert "minimal_delta_cost_policy" in request["prompt_messages"]["user"]
    assert "primitive_costs" in request["prompt_messages"]["user"]
    assert request["context_packet"]["current_route"]["route_id"] == "rank_route"
    assert "conformal_prediction_textbook" in set(
        request["context_packet"]["available_source_refs"]
    )
    assert request["context_packet"]["available_source_snippets"][0][
        "source_ref"
    ] == "conformal_prediction_textbook"
    assert "Exchangeability implies a uniform rank statistic" in request["context_packet"][
        "available_source_snippets"
    ][0]["claim"]
    assert "Probability.exchangeable" in set(
        request["context_packet"]["available_formal_declarations"]
    )
    declaration_rows = request["context_packet"]["available_formal_declaration_rows"]
    assert {
        (row["declaration"], row["target_prover_family"]) for row in declaration_rows
    } >= {("Probability.exchangeable", "lean4")}
    assert "available_source_refs" in request["prompt_messages"]["user"]
    assert "available_source_snippets" in request["prompt_messages"]["user"]
    assert "available_formal_declarations" in request["prompt_messages"]["user"]
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
    response["planner_next_actions"] = [
        {
            "owner": "lean_lsp_mcp",
            "action": "attempt focused proof-state feedback for rank_uniformity",
            "query": "rank_uniformity residual goals after exchangeability reuse",
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
    assert "lean_lsp_mcp" in hook["resource_ids"]
    assert hook["resource_request_bindings"][0]["resource_id"] == "lean_lsp_mcp"
    assert "rank_uniformity residual goals" in " ".join(hook["queries"])
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
    assert "rank_uniformity residual goals" in " ".join(queue_row["queries"])
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
    assert adapter_response["llm_route_planner_hook_trace"] == hook_trace
    evidence_payload = export_formalization_gap_planner_refinement_evidence(
        refinement_queue_dir,
        evidence_dir,
        response_jsonl=adapter_dir
        / "formalization_gap_planner_refinement_evidence_responses.jsonl",
    )
    assert evidence_payload["all_ok"]
    evidence_row = next(
        row
        for row in evidence_payload["rows"]
        if row.get("llm_route_planner_hook_trace")
    )
    assert evidence_row["llm_route_planner_hook_trace"] == hook_trace
    proposal = next(
        row
        for row in evidence_payload["route_revision_proposals"]
        if row.get("llm_route_planner_hook_trace")
    )
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
    ledger_row = context["resource_response_ledger_rows"][0]
    assert ledger_row["response_present"] is True
    assert ledger_row["response_contract_ok"] is True
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
    }
    assert summary["response_acceptance_status_counts"] == {
        "REJECTED_MISSING_RESPONSE_CONTRACT_FIELDS": 1
    }
    assert summary["residual_goals"] == []
    assert summary["route_revision_reasons"] == []
    assert summary["admissible_source_snippets"] == []
    assert summary["replan_required"] is False
    assert summary["recommended_next_actions"] == []


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
    assert tuple(request["residual_goals"]) == (
        "rank_uniformity: tie handling side condition from refinement evidence",
    )
    summary = context["feedback_loop_summary"]
    assert summary["refinement_evidence_admissibility"]["admissible_count"] == 1
    assert summary["admissible_source_snippets"][0]["source_ref"] == source_ref
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
    assert payload["n_requests_with_feedback_loop_summary"] == 1
    request = payload["request_packets"][0]
    context = request["context_packet"]
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
    assert "source_refs_and_snippets_present" in request["prompt_messages"]["user"]
    summary = context["feedback_loop_summary"]
    assert summary["evidence_counts"]["resource_request_queue_rows"] == 1
    assert summary["recommended_next_actions"][0]["source"] == (
        "resource_request_queue"
    )
    assert summary["recommended_next_actions"][0]["owner"] == "paperclip_cli_mcp"
    assert summary["recommended_next_actions"][0]["resource_contracts"] == [
        "paperclip:source_snippet_contract"
    ]


def test_llm_route_planner_cli_stages_resource_request_queue() -> None:
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
            "action": "dispatch queued literature evidence request",
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


def test_llm_route_planner_accepts_grounded_residual_interpretation() -> None:
    root = Path("runs/test_formalization_gap_planner_llm_route_planner_residual_accept")
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
            "interpretation": "The proof route has not fixed deterministic tie handling.",
            "route_repair": "Add a tie-breaking side condition before replay.",
            "source_refs": ["conformal_prediction_textbook"],
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
    assert payload["row_schema"]["$id"] == LLM_ROUTE_PLANNER_ROW_SCHEMA_ID
    assert payload["n_response_present"] == 1
    assert payload["n_response_contract_ok"] == 1
    assert payload["n_accepted_route_plans"] == 1
    assert payload["n_informal_knowledge_dag_nodes"] == 2
    assert payload["n_lean_realization_dag_nodes"] == 2
    assert payload["n_route_alignment_edges"] == 1
    assert payload["n_rows_with_realization_coverage_witness"] == 1
    assert payload["n_rows_with_complete_realization_coverage"] == 1
    assert payload["n_selected_primitives_missing_formal_realization"] == 0
    assert payload["n_delta_primitives_missing_route_alignment"] == 0
    assert payload["n_source_snippets"] == 1
    assert payload["n_rows_with_source_snippets"] == 1
    assert payload["n_rows_with_minimal_delta_rationale"] == 1
    assert payload["n_rows_with_minimal_delta_cost_witness"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "ACCEPTED_WITH_SEARCH_REQUESTS"
    assert "conformal_prediction_textbook" in row["source_refs"]
    assert validate_llm_route_planner_row(
        row,
        llm_route_planner_row_json_schema(),
    ) == []
    row_schema = llm_route_planner_row_json_schema()
    assert "formal_realization_dag_nodes" in row_schema["required"]
    assert "lean_realization_dag_nodes" not in row_schema["required"]
    assert "source_snippets" in row_schema["required"]
    assert "realization_coverage_witness" in row_schema["required"]
    assert row_schema["properties"]["realization_coverage_witness"] == {
        "$ref": "#/$defs/realization_coverage_witness"
    }
    witness_schema = row_schema["$defs"]["realization_coverage_witness"]
    assert "selected_primitives" in witness_schema["required"]
    assert "delta_primitives_missing_route_alignment_edge" in witness_schema["required"]
    assert "realization_coverage_complete" in witness_schema["required"]
    assert witness_schema["properties"]["realization_coverage_complete"]["type"] == "boolean"
    witness = row["realization_coverage_witness"]
    assert witness["selected_primitives"] == ["exchangeability", "rank_uniformity"]
    assert witness["selected_primitives_missing_formal_realization_node"] == []
    assert witness["delta_primitives"] == ["rank_uniformity"]
    assert witness["delta_primitives_missing_route_alignment_edge"] == []
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
    assert (
        payload["standalone_seed"]["routes"][0]["display_name"]
        == "distribution_free_rank_bound_llm_revision"
    )
    assert validate_standalone_input_payload(payload["standalone_seed"]) == []
    seed_route = payload["standalone_seed"]["routes"][0]
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
    assert queue_payload["n_proof_state_feedback_items"] >= 1
    assert any(
        row["hook_kind"] == "proof_state_feedback"
        and "try rank_uniformity bridge against Probability.exchangeable"
        in row["queries"]
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
    assert payload["n_lean_realization_dag_nodes"] == 2
    row = payload["rows"][0]
    assert row["target_prover_family"] == "rocq"
    assert row["formal_realization_dag_nodes"] == row["lean_realization_dag_nodes"]
    seed_route = payload["standalone_seed"]["routes"][0]
    metadata = seed_route["replan_metadata"]
    assert payload["standalone_seed"]["target_prover_family"] == "rocq"
    assert seed_route["target_prover_family"] == "rocq"
    assert metadata["target_prover_family"] == "rocq"
    assert seed_route["revised_formal_realization_dag_nodes"]
    assert seed_route["revised_formal_realization_dag_nodes"] == seed_route[
        "revised_lean_realization_dag_nodes"
    ]
    assert metadata["revised_formal_realization_dag_nodes"] == metadata[
        "revised_lean_realization_dag_nodes"
    ]
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
    packet = payload["request_packets"][0]
    assert packet["model"] == "claude-sonnet-4-6"
    assert packet["model_tier"] == "sonnet"
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
        "formal_realization_dag_nodes",
        "route_alignment_edges",
        "minimal_delta_plan",
        "standalone_route",
        "proof_evidence_boundary",
    ]
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
    packet = payload["request_packets"][0]
    assert packet["model_tier"] == "haiku"
    assert packet["model"] == "claude-haiku-4-5-20251001"
    assert "small route" in packet["model_selection_rationale"]
    row = payload["rows"][0]
    assert row["model_tier"] == "haiku"
    assert row["model"] == "claude-haiku-4-5-20251001"
    request = captured["request"]
    assert request.model == "claude-haiku-4-5-20251001"
    assert request.metadata["model_tier"] == "haiku"


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
    assert payload["n_response_contract_ok"] == 1
    assert payload["n_accepted_route_plans"] == 1
    assert len(requests) == 2
    assert requests[0].metadata["repair_attempt"] == 0
    assert requests[1].metadata["repair_attempt"] == 1
    assert "Repair your previous formalization-gap planner response" in requests[1].user_prompt
    assert "kernel_verified" in requests[1].user_prompt
    raw_response = payload["request_packets"][0]
    assert raw_response["model_tier"] == "sonnet"
    row = payload["rows"][0]
    assert row["acceptance_status"] == "ACCEPTED_WITH_SEARCH_REQUESTS"
    assert row["repair_attempts"] == 1
    assert row["repair_error_history"]
    assert any("kernel_verified" in " ".join(item["errors"]) for item in row["repair_error_history"])
    assert not row["generation_errors"]
    manifest = json.loads(
        (
            out_dir / "formalization_gap_planner_llm_route_planner_manifest.json"
        ).read_text(encoding="utf-8")
    )
    generated = manifest["request_packets"][0]
    assert generated["model_tier"] == "sonnet"
    manifest_row = manifest["rows"][0]
    assert manifest_row["repair_attempts"] == 1
    assert manifest_row["generation_errors"] == []


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
        "deterministic_tie_breaking"
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
        "phantom_compactness"
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
