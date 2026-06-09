from __future__ import annotations

from collections import Counter
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
    export_formalization_gap_planner_resource_request_queue,
)
from ai_statistician.formalization_gap_planner_resource_response_ledger import (
    RESOURCE_RESPONSE_LEDGER_ROW_SCHEMA_ID,
    RESOURCE_RESPONSE_SCHEMA_ID,
    export_formalization_gap_planner_resource_response_ledger,
    resource_response_ledger_row_json_schema,
    resource_response_json_schema,
    validate_resource_response_ledger_row,
    validate_resource_response_row,
)
from ai_statistician.formalization_gap_planner_standalone import (
    export_formalization_gap_planner_standalone_plan,
)


def _build_request_queue(
    root: Path,
    *,
    input_payload: dict[str, object] | None = None,
) -> tuple[dict[str, object], Path]:
    input_json = root / "standalone_input.json"
    plan_dir = root / "plan"
    coverage_dir = root / "coverage"
    action_queue_dir = root / "action_queue"
    component_resource_registry_dir = root / "component_resource_registry"
    action_resource_plan_dir = root / "action_resource_plan"
    request_queue_dir = root / "request_queue"
    payload = input_payload or {
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
                        "primitive": "rank_uniformity",
                        "coverage_status": "bridge_needed",
                        "candidate_declarations": [
                            "Probability.rankUniformityBridge"
                        ],
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
    }
    input_json.write_text(
        json.dumps(payload, indent=2),
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
    return payload, request_queue_dir


def test_resource_response_ledger_reports_mixed_targets_from_request_rows() -> None:
    root = Path("runs/test_formalization_gap_planner_resource_response_ledger_mixed")
    ledger_dir = root / "ledger"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    request_payload, request_queue_dir = _build_request_queue(
        root,
        input_payload={
            "schema_version": 1,
            "component_name": "formalization_gap_planner_standalone_input",
            "library_snapshot_ref": "mixed:response-ledger-target-summary",
            "routes": [
                {
                    "route_id": "lean_rank_route",
                    "display_name": "lean_rank_route",
                    "target_prover_family": "lean4",
                    "theorem_statement": "A Lean route.",
                    "primitives": [
                        {
                            "primitive": "rank_uniformity",
                            "coverage_status": "bridge_needed",
                            "candidate_declarations": [
                                "Probability.rankUniformityBridge"
                            ],
                            "expected_premises": ["exchangeability"],
                        }
                    ],
                },
                {
                    "route_id": "rocq_rank_route",
                    "display_name": "rocq_rank_route",
                    "target_prover_family": "rocq",
                    "theorem_statement": "A Rocq route.",
                    "source_refs": ["rocq_conformal_notes"],
                    "primitives": [
                        {
                            "primitive": "coverage_inequality",
                            "coverage_status": "source_port_needed",
                            "source_refs": ["rocq_conformal_notes"],
                        }
                    ],
                },
            ],
        },
    )

    payload = export_formalization_gap_planner_resource_response_ledger(
        request_queue_dir,
        ledger_dir,
    )

    request_counts = Counter(
        str(row["target_prover_family"]) for row in request_payload["rows"]
    )
    ledger_counts = Counter(str(row["target_prover_family"]) for row in payload["rows"])
    assert request_payload["all_ok"]
    assert request_payload["target_prover_family"] == "mixed:lean4,rocq"
    assert request_payload["n_target_prover_families"] == 2
    assert request_payload["by_target_prover_family"] == dict(
        sorted(request_counts.items())
    )
    assert payload["all_ok"]
    assert payload["target_prover_family"] == "mixed:lean4,rocq"
    assert payload["n_target_prover_families"] == 2
    assert payload["by_target_prover_family"] == dict(sorted(ledger_counts.items()))
    assert {row["target_prover_family"] for row in payload["rows"]} == {
        "lean4",
        "rocq",
    }


def test_resource_response_ledger_accepts_adapter_feedback_without_proof_claims() -> None:
    root = Path("runs/test_formalization_gap_planner_resource_response_ledger")
    ledger_dir = root / "ledger"
    response_jsonl = root / "resource_responses.jsonl"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    request_payload, request_queue_dir = _build_request_queue(root)
    source_request = next(
        row for row in request_payload["rows"] if row["resource_id"] == "paperclip_cli_mcp"
    )
    proof_request = next(
        row for row in request_payload["rows"] if row["resource_id"] == "lean_lsp_mcp"
    )
    responses = [
        {
            "resource_request_id": source_request["request_payload"][
                "resource_request_id"
            ],
            "resource_id": source_request["resource_id"],
            "tool_name": "paperclip_cli_mcp",
            "expected_response_artifact": source_request["request_payload"][
                "expected_response_artifact"
            ],
            "response_payload": {
                "source_refs": ["Vovk-Gammerman-Shafer conformal prediction"],
                "route_evidence_nodes": [
                    {
                        "node_id": "informal:coverage_inequality:source",
                        "claim": "exchangeability implies rank coverage bound",
                    }
                ],
                "response_summary": "source route evidence found",
            },
            "source_refs": ["Vovk-Gammerman-Shafer conformal prediction"],
            "route_evidence_nodes": [
                {
                    "node_id": "informal:coverage_inequality:source",
                    "claim": "exchangeability implies rank coverage bound",
                }
            ],
            "proof_evidence_boundary": "not theorem proof evidence",
        },
        {
            "resource_request_id": proof_request["request_payload"][
                "resource_request_id"
            ],
            "resource_id": proof_request["resource_id"],
            "tool_name": "lean_lsp_mcp",
            "expected_response_artifact": proof_request["request_payload"][
                "expected_response_artifact"
            ],
            "response_payload": {
                "prover_diagnostics": ["unknown identifier rank_uniformity"],
                "residual_goals": ["prove finite rank denominator is nonzero"],
                "prover_attempt_status": "failed_with_residual_goals",
                "prover_diagnostic_signature": "unknown_identifier:rank_uniformity",
                "route_revision_recommended": True,
                "route_revision_reasons": [
                    "proof-state feedback exposed a missing finite-rank bridge"
                ],
            },
            "prover_diagnostics": ["unknown identifier rank_uniformity"],
            "residual_goals": ["prove finite rank denominator is nonzero"],
            "route_revision_recommended": True,
            "route_revision_reasons": [
                "proof-state feedback exposed a missing finite-rank bridge"
            ],
            "proof_evidence_boundary": "not theorem proof evidence",
        },
    ]
    response_jsonl.write_text(
        "\n".join(json.dumps(response, sort_keys=True) for response in responses)
        + "\n",
        encoding="utf-8",
    )

    payload = export_formalization_gap_planner_resource_response_ledger(
        request_queue_dir,
        ledger_dir,
        response_jsonl=response_jsonl,
    )

    assert payload["all_ok"]
    assert payload["n_resource_requests"] == request_payload["n_resource_request_rows"]
    assert (
        request_payload["n_self_contained_request_payloads"]
        == request_payload["n_resource_request_rows"]
    )
    assert request_payload["n_request_payload_identity_mismatches"] == 0
    assert request_payload["n_dispatch_spec_identity_mismatches"] == 0
    assert payload["n_input_responses"] == 2
    assert payload["n_response_schema_valid"] == 2
    assert payload["n_response_schema_invalid"] == 0
    assert payload["n_ledger_rows"] == payload["n_resource_requests"]
    assert payload["n_ledger_row_schema_valid"] == payload["n_ledger_rows"]
    assert payload["n_ledger_row_schema_invalid"] == 0
    assert payload["n_response_present"] == 2
    assert payload["n_awaiting_response"] == payload["n_resource_requests"] - 2
    assert payload["n_response_contract_ok"] == 2
    assert payload["n_request_playbook_present"] == payload["n_resource_requests"]
    assert payload["n_response_playbook_grounded"] == 2
    assert payload["n_response_playbook_grounding_failures"] == 0
    assert payload["n_with_dispatch_specs"] == payload["n_ledger_rows"]
    assert payload["n_with_resource_contract_ids"] == payload["n_ledger_rows"]
    assert payload["n_with_stop_conditions"] == payload["n_ledger_rows"]
    assert payload["n_with_quality_controls"] == payload["n_ledger_rows"]
    assert payload["n_route_revision_recommended"] == 1
    assert payload["n_rejected"] == 0
    assert payload["resource_response_schema"]["$id"] == RESOURCE_RESPONSE_SCHEMA_ID
    assert (
        payload["resource_response_ledger_row_schema"]["$id"]
        == RESOURCE_RESPONSE_LEDGER_ROW_SCHEMA_ID
    )
    source_ledger = next(
        row
        for row in payload["rows"]
        if row["resource_request_id"] == source_request["resource_request_id"]
    )
    assert source_ledger["acceptance_status"] == "ACCEPTED_RESOURCE_RESPONSE"
    assert source_ledger["request_playbook_present"]
    assert source_ledger["response_playbook_grounded"]
    assert source_ledger["response_playbook_grounding_terms"]
    assert source_ledger["acceptance_gate"] == source_request["acceptance_gate"]
    assert source_ledger["response_contract_fields"] == source_request["response_contract_fields"]
    assert source_ledger["response_contract_minimum_met"]
    assert "source_refs" in source_ledger["matched_response_contract_fields"]
    assert source_ledger["dispatch_spec"] == source_request["dispatch_spec"]
    proof_ledger = next(
        row
        for row in payload["rows"]
        if row["resource_request_id"] == proof_request["resource_request_id"]
    )
    declaration_request = next(
        row for row in request_payload["rows"] if row["candidate_declaration_rows"]
    )
    declaration_ledger = next(
        row
        for row in payload["rows"]
        if row["resource_request_id"] == declaration_request["resource_request_id"]
    )
    assert declaration_ledger["candidate_declaration_rows"] == declaration_request[
        "candidate_declaration_rows"
    ]
    assert declaration_ledger["candidate_declaration_rows"] == (
        {
            "declaration": "Probability.rankUniformityBridge",
            "target_prover_family": "lean4",
            "source_field": "candidate_declarations",
        },
    )
    assert proof_ledger["acceptance_status"] == "ACCEPTED_WITH_ROUTE_REVISION"
    assert proof_ledger["request_playbook_present"]
    assert proof_ledger["response_playbook_grounded"]
    assert "rank_uniformity" in proof_ledger["response_playbook_grounding_terms"]
    assert proof_ledger["resource_contract_ids"] == proof_request[
        "resource_contract_ids"
    ]
    assert proof_ledger["stop_conditions"] == proof_request["stop_conditions"]
    assert proof_ledger["quality_controls"]["resource_contract_ids"] == proof_request[
        "resource_contract_ids"
    ]
    assert set(proof_request["stop_conditions"]).issubset(
        set(proof_ledger["quality_controls"]["stop_conditions"])
    )
    assert proof_ledger["response_contract_minimum_met"]
    assert proof_ledger["dispatch_spec"]["adapter_surface"] == "target_prover_lsp_mcp"
    assert "prover_diagnostics" in proof_ledger["matched_response_contract_fields"]
    assert proof_ledger["route_revision_recommended"]
    assert "not theorem proof evidence" in proof_ledger["proof_evidence_boundary"]
    assert validate_resource_response_row(
        responses[0],
        resource_response_json_schema(),
    ) == []
    assert validate_resource_response_ledger_row(
        proof_ledger,
        resource_response_ledger_row_json_schema(),
    ) == []
    malformed = dict(proof_ledger)
    malformed.pop("resource_id")
    assert "resource_id required" in validate_resource_response_ledger_row(
        malformed,
        resource_response_ledger_row_json_schema(),
    )
    assert (
        ledger_dir
        / "formalization_gap_planner_resource_response_ledger_manifest.json"
    ).exists()
    assert (
        ledger_dir / "formalization_gap_planner_resource_response_ledger.jsonl"
    ).exists()
    assert (
        ledger_dir / "formalization_gap_planner_resource_response.schema.json"
    ).exists()
    assert (
        ledger_dir
        / "formalization_gap_planner_resource_response_ledger_row.schema.json"
    ).exists()
    assert (
        ledger_dir / "formalization_gap_planner_resource_response_ledger.md"
    ).exists()


def test_resource_response_ledger_rejects_kernel_claims_in_resource_layer() -> None:
    root = Path("runs/test_formalization_gap_planner_resource_response_ledger_rejects")
    ledger_dir = root / "ledger"
    response_jsonl = root / "resource_responses.jsonl"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    request_payload, request_queue_dir = _build_request_queue(root)
    request = next(row for row in request_payload["rows"] if row["request_phase"])
    response = {
        "resource_request_id": request["resource_request_id"],
        "resource_id": request["resource_id"],
        "response_payload": {"kernel_verified": True},
        "kernel_verified": True,
        "proof_evidence_boundary": "not theorem proof evidence",
    }
    response_jsonl.write_text(json.dumps(response, sort_keys=True) + "\n", encoding="utf-8")

    payload = export_formalization_gap_planner_resource_response_ledger(
        request_queue_dir,
        ledger_dir,
        response_jsonl=response_jsonl,
    )

    assert not payload["all_ok"]
    assert payload["n_response_schema_invalid"] == 1
    assert payload["n_rejected"] == 1
    rejected = next(row for row in payload["rows"] if row["response_present"])
    assert rejected["acceptance_status"] == "REJECTED_KERNEL_PROOF_CLAIM"
    assert rejected["errors"]


def test_resource_response_ledger_rejects_request_identity_mismatch() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_resource_response_ledger_request_mismatch"
    )
    ledger_dir = root / "ledger"
    response_jsonl = root / "resource_responses.jsonl"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    request_payload, request_queue_dir = _build_request_queue(root)
    request = next(
        row for row in request_payload["rows"] if row["resource_id"] == "paperclip_cli_mcp"
    )
    stale_dispatch_spec = dict(request["dispatch_spec"])
    stale_dispatch_spec["adapter_surface"] = "stale_adapter_surface"
    response = {
        "resource_request_id": request["resource_request_id"],
        "resource_id": "lean_lsp_mcp",
        "expected_response_artifact": "proof_state_or_prover_feedback_response",
        "dispatch_spec": stale_dispatch_spec,
        "candidate_declaration_rows": [
            {
                "declaration": "Probability.exchangeable",
                "target_prover_family": "rocq",
                "source_field": "candidate_declarations",
            }
        ],
        "response_payload": {
            "source_refs": ["Vovk-Gammerman-Shafer conformal prediction"],
            "candidate_declaration_rows": [
                {
                    "declaration": "Probability.exchangeable",
                    "target_prover_family": "rocq",
                    "source_field": "candidate_declarations",
                }
            ],
        },
        "source_refs": ["Vovk-Gammerman-Shafer conformal prediction"],
        "proof_evidence_boundary": "not theorem proof evidence",
    }
    response_jsonl.write_text(json.dumps(response, sort_keys=True) + "\n", encoding="utf-8")

    payload = export_formalization_gap_planner_resource_response_ledger(
        request_queue_dir,
        ledger_dir,
        response_jsonl=response_jsonl,
    )

    assert not payload["all_ok"]
    assert payload["n_response_schema_valid"] == 1
    assert payload["n_response_request_mismatches"] == 1
    assert payload["n_response_contract_ok"] == 0
    assert payload["n_rejected"] == 1
    rejected = next(row for row in payload["rows"] if row["response_present"])
    assert rejected["acceptance_status"] == "REJECTED_RESPONSE_REQUEST_MISMATCH"
    assert any("response.resource_id" in error for error in rejected["errors"])
    assert any("response.expected_response_artifact" in error for error in rejected["errors"])
    assert any("response.dispatch_spec" in error for error in rejected["errors"])
    assert any("candidate_declaration_rows" in error for error in rejected["errors"])


def test_resource_response_ledger_rejects_missing_contract_evidence() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_resource_response_ledger_missing_contract"
    )
    ledger_dir = root / "ledger"
    response_jsonl = root / "resource_responses.jsonl"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    request_payload, request_queue_dir = _build_request_queue(root)
    request = next(
        row for row in request_payload["rows"] if row["resource_id"] == "paperclip_cli_mcp"
    )
    response = {
        "resource_request_id": request["resource_request_id"],
        "resource_id": request["resource_id"],
        "expected_response_artifact": request["expected_response_artifact"],
        "response_payload": {
            "response_summary": "tool ran but returned no source-grounding fields",
        },
        "response_summary": "tool ran but returned no source-grounding fields",
        "proof_evidence_boundary": "not theorem proof evidence",
    }
    response_jsonl.write_text(json.dumps(response, sort_keys=True) + "\n", encoding="utf-8")

    payload = export_formalization_gap_planner_resource_response_ledger(
        request_queue_dir,
        ledger_dir,
        response_jsonl=response_jsonl,
    )

    assert not payload["all_ok"]
    assert payload["n_response_schema_valid"] == 1
    assert payload["n_response_contract_ok"] == 0
    assert payload["n_response_contract_minimum_met"] == 0
    assert payload["n_missing_response_contract_field_rows"] == 1
    assert payload["n_rejected"] == 1
    rejected = next(row for row in payload["rows"] if row["response_present"])
    assert rejected["acceptance_status"] == "REJECTED_MISSING_RESPONSE_CONTRACT_FIELDS"
    assert not rejected["ok"]
    assert not rejected["response_contract_minimum_met"]
    assert rejected["response_contract_fields"] == request["response_contract_fields"]
    assert rejected["missing_response_contract_fields"] == request["response_contract_fields"]
    assert any("missing all queued response_contract_fields" in error for error in rejected["errors"])


def test_resource_response_ledger_rejects_response_not_grounded_in_playbook() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_resource_response_ledger_playbook_mismatch"
    )
    ledger_dir = root / "ledger"
    response_jsonl = root / "resource_responses.jsonl"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    request_payload, request_queue_dir = _build_request_queue(root)
    request = next(
        row for row in request_payload["rows"] if row["resource_id"] == "paperclip_cli_mcp"
    )
    response = {
        "resource_request_id": request["resource_request_id"],
        "resource_id": request["resource_id"],
        "expected_response_artifact": request["expected_response_artifact"],
        "response_payload": {
            "source_refs": ["compact operator spectral theorem"],
            "route_evidence_nodes": [
                {
                    "node_id": "informal:unrelated",
                    "claim": "a Hilbert basis diagonalizes a compact operator",
                }
            ],
            "response_summary": "unrelated functional analysis source evidence",
        },
        "source_refs": ["compact operator spectral theorem"],
        "route_evidence_nodes": [
            {
                "node_id": "informal:unrelated",
                "claim": "a Hilbert basis diagonalizes a compact operator",
            }
        ],
        "proof_evidence_boundary": "not theorem proof evidence",
    }
    response_jsonl.write_text(json.dumps(response, sort_keys=True) + "\n", encoding="utf-8")

    payload = export_formalization_gap_planner_resource_response_ledger(
        request_queue_dir,
        ledger_dir,
        response_jsonl=response_jsonl,
    )

    assert not payload["all_ok"]
    assert payload["n_response_contract_minimum_met"] == 1
    assert payload["n_response_contract_ok"] == 0
    assert payload["n_response_playbook_grounding_failures"] == 1
    assert payload["n_rejected"] == 1
    rejected = next(row for row in payload["rows"] if row["response_present"])
    assert rejected["acceptance_status"] == (
        "REJECTED_RESPONSE_NOT_GROUNDED_IN_REQUEST_PLAYBOOK"
    )
    assert rejected["request_playbook_present"]
    assert not rejected["response_playbook_grounded"]
    assert rejected["response_playbook_grounding_terms"] == ()
    assert any("not grounded in request_playbook" in error for error in rejected["errors"])
