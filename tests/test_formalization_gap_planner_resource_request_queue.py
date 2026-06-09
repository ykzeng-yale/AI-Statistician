from __future__ import annotations

import json
import shutil
from pathlib import Path

from ai_statistician.formalization_gap_planner_action_resource_plan import (
    export_formalization_gap_planner_action_resource_plan,
)
from ai_statistician.formalization_gap_planner_component_resource_registry import (
    export_formalization_gap_planner_component_resource_registry,
)
from ai_statistician.formalization_gap_planner_library_coverage_map import (
    export_formalization_gap_planner_library_coverage_map,
)
from ai_statistician.formalization_gap_planner_primitive_action_queue import (
    export_formalization_gap_planner_primitive_action_queue,
)
from ai_statistician.formalization_gap_planner_resource_request_queue import (
    RESOURCE_REQUEST_QUEUE_ROW_SCHEMA_ID,
    export_formalization_gap_planner_resource_request_queue,
    resource_request_queue_row_json_schema,
    validate_resource_request_queue_row,
)
from ai_statistician.formalization_gap_planner_standalone import (
    export_formalization_gap_planner_standalone_plan,
)


def test_resource_request_queue_expands_action_resources_to_dispatch_packets() -> None:
    root = Path("runs/test_formalization_gap_planner_resource_request_queue")
    input_json = root / "standalone_input.json"
    plan_dir = root / "plan"
    coverage_dir = root / "coverage"
    action_queue_dir = root / "action_queue"
    component_resource_registry_dir = root / "component_resource_registry"
    action_resource_plan_dir = root / "action_resource_plan"
    request_queue_dir = root / "request_queue"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "component_name": "formalization_gap_planner_standalone_input",
                "target_prover_family": "lean4",
                "library_snapshot_ref": "lean_mathlib_empirical_process_snapshot",
                "routes": [
                    {
                        "display_name": "distribution_free_rank_bound",
                        "theorem_statement": (
                            "A distribution-free rank bound follows from exchangeability."
                        ),
                        "source_refs": ["conformal_prediction_textbook"],
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
                            {
                                "primitive": "coverage_inequality",
                                "coverage_status": "source_port_needed",
                                "source_refs": ["vovk_gammerman_shafer"],
                            },
                        ],
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    export_formalization_gap_planner_standalone_plan(input_json, plan_dir)
    export_formalization_gap_planner_library_coverage_map(plan_dir, coverage_dir)
    export_formalization_gap_planner_primitive_action_queue(
        coverage_dir,
        action_queue_dir,
    )
    export_formalization_gap_planner_component_resource_registry(
        component_resource_registry_dir
    )
    action_payload = export_formalization_gap_planner_action_resource_plan(
        action_queue_dir,
        component_resource_registry_dir,
        action_resource_plan_dir,
    )

    payload = export_formalization_gap_planner_resource_request_queue(
        action_resource_plan_dir,
        request_queue_dir,
    )

    assert payload["all_ok"]
    assert (
        payload["n_action_resource_plan_rows"]
        == action_payload["n_resource_plan_rows"]
        == 3
    )
    assert payload["n_resource_request_rows"] > action_payload["n_resource_plan_rows"]
    assert payload["n_ok"] == payload["n_resource_request_rows"]
    assert payload["n_failed"] == 0
    assert payload["n_local_first_requests"] > 0
    assert payload["n_frontier_escalation_requests"] > 0
    assert payload["n_distinct_resources"] >= 5
    assert (
        payload["n_self_contained_request_payloads"]
        == payload["n_resource_request_rows"]
    )
    assert payload["n_request_payload_identity_mismatches"] == 0
    assert payload["n_with_request_playbooks"] == payload["n_resource_request_rows"]
    assert (
        payload["n_request_playbook_identity_valid"]
        == payload["n_resource_request_rows"]
    )
    assert payload["n_request_playbook_identity_mismatches"] == 0
    assert payload["n_with_candidate_declaration_rows"] > 0
    assert payload["n_candidate_declaration_rows"] == payload[
        "n_with_candidate_declaration_rows"
    ]
    assert payload["n_row_schema_valid"] == payload["n_resource_request_rows"]
    assert payload["n_row_schema_invalid"] == 0
    assert (
        payload["resource_request_queue_row_schema"]["$id"]
        == RESOURCE_REQUEST_QUEUE_ROW_SCHEMA_ID
    )
    rows = payload["rows"]
    assert rows
    exact_rows = [
        row for row in rows if row["queue_action_kind"] == "target_prover_replay"
    ]
    assert exact_rows
    exact_row = exact_rows[0]
    assert exact_row["candidate_declaration_rows"] == (
        {
            "declaration": "Probability.exchangeable",
            "target_prover_family": "lean4",
            "source_field": "candidate_declarations",
        },
    )
    assert (
        exact_row["request_payload"]["candidate_declaration_rows"]
        == exact_row["candidate_declaration_rows"]
    )
    source_rows = [
        row for row in rows if row["queue_action_kind"] == "source_port"
    ]
    assert any(row["resource_id"] == "local_literature_corpus" for row in source_rows)
    assert any(row["resource_id"] == "paperclip_cli_mcp" for row in source_rows)
    assert any(
        row["expected_response_artifact"]
        == "literature_or_source_grounding_response"
        for row in source_rows
    )
    bridge_rows = [
        row for row in rows if row["queue_action_kind"] == "prove_bridge_lemma"
    ]
    lean_lsp_row = next(
        row for row in bridge_rows if row["resource_id"] == "lean_lsp_mcp"
    )
    assert lean_lsp_row["request_phase"] == "frontier_escalation"
    assert (
        lean_lsp_row["expected_response_artifact"]
        == "proof_state_or_prover_feedback_response"
    )
    assert "target-prover LSP" in lean_lsp_row["mcp_or_cli_hint"]
    assert lean_lsp_row["dispatch_spec"]["dispatch_kind"] == "frontier_mcp_or_cli"
    assert lean_lsp_row["dispatch_spec"]["adapter_surface"] == "target_prover_lsp_mcp"
    assert (
        lean_lsp_row["dispatch_spec"]["execution_command"]
        == lean_lsp_row["execution_command"]
    )
    assert (
        lean_lsp_row["request_payload"]["dispatch_spec"]
        == lean_lsp_row["dispatch_spec"]
    )
    assert (
        lean_lsp_row["request_payload"]["request_playbook"]
        == lean_lsp_row["request_playbook"]
    )
    assert (
        lean_lsp_row["request_playbook"]["resource_request_id"]
        == lean_lsp_row["resource_request_id"]
    )
    assert (
        lean_lsp_row["request_playbook"]["expected_response_artifact"]
        == lean_lsp_row["expected_response_artifact"]
    )
    assert "rank_uniformity" in lean_lsp_row["request_playbook"]["operator_prompt"]
    assert tuple(lean_lsp_row["target_primitives"]) == ("rank_uniformity",)
    assert tuple(lean_lsp_row["request_payload"]["target_primitives"]) == (
        "rank_uniformity",
    )
    assert tuple(
        lean_lsp_row["request_playbook"]["input_summary"]["target_primitives"]
    ) == ("rank_uniformity",)
    assert (
        "prover_diagnostics"
        in lean_lsp_row["request_playbook"]["expected_response_fields"]
    )
    assert lean_lsp_row["request_playbook"]["acceptance_checklist"]
    assert (
        "not theorem proof evidence"
        in lean_lsp_row["request_payload"]["proof_evidence_boundary"]
    )
    assert (
        lean_lsp_row["request_payload"]["resource_request_id"]
        == lean_lsp_row["resource_request_id"]
    )
    assert (
        lean_lsp_row["request_payload"]["request_rank"]
        == lean_lsp_row["request_rank"]
    )
    assert (
        lean_lsp_row["request_payload"]["expected_response_artifact"]
        == lean_lsp_row["expected_response_artifact"]
    )
    assert "prover_diagnostics" in lean_lsp_row["response_contract_fields"]
    assert "source_refs" not in lean_lsp_row["response_contract_fields"]
    assert (
        lean_lsp_row["response_contract_fields"]
        == lean_lsp_row["request_payload"]["response_contract_fields"]
    )
    assert (
        payload["n_with_dispatch_specs"]
        == payload["n_dispatch_spec_identity_valid"]
        == payload["n_resource_request_rows"]
    )
    assert payload["n_dispatch_spec_identity_mismatches"] == 0
    source_paperclip_row = next(
        row for row in source_rows if row["resource_id"] == "paperclip_cli_mcp"
    )
    assert source_paperclip_row["dispatch_spec"]["adapter_surface"] == "paperclip_mcp_cli"
    assert "source_refs" in source_paperclip_row["response_contract_fields"]
    assert "prover_diagnostics" not in source_paperclip_row["response_contract_fields"]
    assert "mcp_tool_call" in source_paperclip_row["request_contract_fields"]
    assert (
        source_paperclip_row["resource_contract_ids"]
        == source_paperclip_row["request_payload"]["resource_contract_ids"]
    )
    formal_source_row = next(
        row
        for row in bridge_rows
        if row["resource_id"] == "local_formal_source_index"
    )
    assert (
        formal_source_row["expected_response_artifact"]
        == "formal_library_search_or_dependency_response"
    )
    assert validate_resource_request_queue_row(
        lean_lsp_row,
        resource_request_queue_row_json_schema(),
    ) == []
    malformed = dict(lean_lsp_row)
    malformed.pop("request_payload")
    assert "request_payload required" in validate_resource_request_queue_row(
        malformed,
        resource_request_queue_row_json_schema(),
    )
    malformed = dict(lean_lsp_row)
    malformed["request_payload"] = dict(lean_lsp_row["request_payload"])
    malformed["request_payload"].pop("resource_request_id")
    assert (
        "request_payload.resource_request_id required"
        in validate_resource_request_queue_row(
            malformed,
            resource_request_queue_row_json_schema(),
        )
    )
    malformed = dict(lean_lsp_row)
    malformed["request_payload"] = dict(lean_lsp_row["request_payload"])
    malformed["request_payload"]["expected_response_artifact"] = "stale_artifact"
    assert (
        "request_payload.expected_response_artifact must match row.expected_response_artifact"
        in validate_resource_request_queue_row(
            malformed,
            resource_request_queue_row_json_schema(),
        )
    )
    malformed = dict(exact_row)
    malformed["request_payload"] = dict(exact_row["request_payload"])
    malformed["request_payload"]["candidate_declaration_rows"] = [
        {
            "declaration": "Probability.exchangeable",
            "target_prover_family": "rocq",
            "source_field": "candidate_declarations",
        }
    ]
    assert (
        "request_payload.candidate_declaration_rows must match row.candidate_declaration_rows"
        in validate_resource_request_queue_row(
            malformed,
            resource_request_queue_row_json_schema(),
        )
    )
    malformed = dict(lean_lsp_row)
    malformed["dispatch_spec"] = dict(lean_lsp_row["dispatch_spec"])
    malformed["dispatch_spec"]["adapter_surface"] = "stale_adapter"
    assert (
        "dispatch_spec.adapter_surface must match resource_id/request_phase"
        in validate_resource_request_queue_row(
            malformed,
            resource_request_queue_row_json_schema(),
        )
    )
    malformed = dict(lean_lsp_row)
    malformed.pop("request_playbook")
    assert "request_playbook required" in validate_resource_request_queue_row(
        malformed,
        resource_request_queue_row_json_schema(),
    )
    malformed = dict(lean_lsp_row)
    malformed["request_playbook"] = dict(lean_lsp_row["request_playbook"])
    malformed["request_playbook"]["expected_response_fields"] = ["stale_field"]
    assert (
        "request_playbook.expected_response_fields must match row.response_contract_fields"
        in validate_resource_request_queue_row(
            malformed,
            resource_request_queue_row_json_schema(),
        )
    )
    malformed = dict(lean_lsp_row)
    malformed["request_payload"] = dict(lean_lsp_row["request_payload"])
    malformed["request_payload"]["target_primitives"] = ["rank_uniformity", "spectral_gap"]
    assert (
        "request_payload.target_primitives must match row.target_primitives"
        in validate_resource_request_queue_row(
            malformed,
            resource_request_queue_row_json_schema(),
        )
    )
    malformed = dict(lean_lsp_row)
    malformed["request_playbook"] = dict(lean_lsp_row["request_playbook"])
    malformed["request_playbook"]["input_summary"] = dict(
        lean_lsp_row["request_playbook"]["input_summary"]
    )
    malformed["request_playbook"]["input_summary"]["target_primitives"] = [
        "spectral_gap"
    ]
    assert (
        "request_playbook.input_summary.target_primitives must match row.target_primitives"
        in validate_resource_request_queue_row(
            malformed,
            resource_request_queue_row_json_schema(),
        )
    )
    assert (
        request_queue_dir
        / "formalization_gap_planner_resource_request_queue_manifest.json"
    ).exists()
    assert (
        request_queue_dir / "formalization_gap_planner_resource_request_queue.jsonl"
    ).exists()
    assert (
        request_queue_dir
        / "formalization_gap_planner_resource_request_queue_row.schema.json"
    ).exists()
    assert (
        request_queue_dir / "formalization_gap_planner_resource_request_queue.md"
    ).exists()


def test_resource_request_queue_dispatches_rocq_bridge_without_lean_resources() -> None:
    root = Path("runs/test_formalization_gap_planner_resource_request_queue_rocq")
    input_json = root / "standalone_input.json"
    plan_dir = root / "plan"
    coverage_dir = root / "coverage"
    action_queue_dir = root / "action_queue"
    component_resource_registry_dir = root / "component_resource_registry"
    action_resource_plan_dir = root / "action_resource_plan"
    request_queue_dir = root / "request_queue"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "component_name": "formalization_gap_planner_standalone_input",
                "target_prover_family": "rocq",
                "library_snapshot_ref": "rocq_conformal_snapshot",
                "routes": [
                    {
                        "route_id": "rocq_rank_route",
                        "display_name": "rocq_rank_route",
                        "theorem_statement": "A Rocq rank route.",
                        "primitives": [
                            {
                                "primitive": "rank_uniformity",
                                "coverage_status": "bridge_needed",
                                "expected_premises": ["exchangeability"],
                            }
                        ],
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    export_formalization_gap_planner_standalone_plan(input_json, plan_dir)
    export_formalization_gap_planner_library_coverage_map(plan_dir, coverage_dir)
    export_formalization_gap_planner_primitive_action_queue(
        coverage_dir,
        action_queue_dir,
    )
    export_formalization_gap_planner_component_resource_registry(
        component_resource_registry_dir
    )
    export_formalization_gap_planner_action_resource_plan(
        action_queue_dir,
        component_resource_registry_dir,
        action_resource_plan_dir,
    )

    payload = export_formalization_gap_planner_resource_request_queue(
        action_resource_plan_dir,
        request_queue_dir,
    )

    assert payload["all_ok"]
    resource_ids = {row["resource_id"] for row in payload["rows"]}
    assert "rocq_lsp_serapi" in resource_ids
    assert "local_target_formal_source_index" in resource_ids
    assert not resource_ids.intersection(
        {
            "local_formal_source_index",
            "local_lean_rag_dependency_graph",
            "loogle_leansearch",
            "leanexplore_mcp",
            "lean_blueprint_leanarchitect",
            "local_lake_lean",
            "lean_lsp_mcp",
            "leandojo_reprover",
        }
    )
    rocq_request = next(row for row in payload["rows"] if row["resource_id"] == "rocq_lsp_serapi")
    assert rocq_request["target_prover_family"] == "rocq"
    assert rocq_request["dispatch_spec"]["adapter_surface"] == "rocq_serapi"
    assert rocq_request["mcp_or_cli_hint"] == "Rocq SerAPI/LSP adapter"
    assert "dispatch rocq proof-state request" in rocq_request["execution_command"]
    assert "prover_diagnostics" in rocq_request["response_contract_fields"]
    assert "residual_goals" in rocq_request["response_contract_fields"]


def test_resource_request_queue_marks_missing_action_plan_as_blocker() -> None:
    root = Path("runs/test_formalization_gap_planner_resource_request_queue_rejects")
    missing_action_plan_dir = root / "missing_action_plan"
    shutil.rmtree(root, ignore_errors=True)

    payload = export_formalization_gap_planner_resource_request_queue(
        missing_action_plan_dir
    )

    assert not payload["all_ok"]
    assert payload["n_action_resource_plan_rows"] == 0
    assert payload["n_resource_request_rows"] == 0
    assert payload["errors"]
