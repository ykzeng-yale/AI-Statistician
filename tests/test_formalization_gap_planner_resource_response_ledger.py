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
from ai_statistician.formalization_gap_planner_llm_route_planner import (
    export_formalization_gap_planner_llm_route_planner,
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
    llm_route_planner_rows: list[dict[str, object]] | None = None,
) -> tuple[dict[str, object], Path]:
    input_json = root / "standalone_input.json"
    plan_dir = root / "plan"
    coverage_dir = root / "coverage"
    action_queue_dir = root / "action_queue"
    component_resource_registry_dir = root / "component_resource_registry"
    action_resource_plan_dir = root / "action_resource_plan"
    llm_route_planner_dir = root / "llm_route_planner"
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
                "replan_metadata": {
                    "llm_route_planner_minimal_delta_plan": {
                        "bridge_lemmas": [
                            (
                                "rank_uniformity: prove finite rank uniformity "
                                "from exchangeability"
                            )
                        ],
                        "source_port_lemmas": [
                            (
                                "coverage_inequality: port the source-backed "
                                "coverage inequality"
                            )
                        ],
                    }
                },
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
    if llm_route_planner_rows is not None:
        llm_route_planner_dir.mkdir(parents=True, exist_ok=True)
        (
            llm_route_planner_dir
            / "formalization_gap_planner_llm_route_planner_manifest.json"
        ).write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "component_name": "formalization_gap_planner_llm_route_planner",
                    "rows": llm_route_planner_rows,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
    payload = export_formalization_gap_planner_resource_request_queue(
        action_resource_plan_dir,
        request_queue_dir,
        formalization_gap_planner_llm_route_planner_dir=(
            llm_route_planner_dir if llm_route_planner_rows is not None else None
        ),
    )
    return payload, request_queue_dir


def _build_prompt_only_route_brief_request_queue(
    root: Path,
) -> tuple[dict[str, object], dict[str, object], Path]:
    input_json = root / "standalone_input.json"
    plan_dir = root / "plan"
    coverage_dir = root / "coverage"
    action_queue_dir = root / "action_queue"
    component_resource_registry_dir = root / "component_resource_registry"
    action_resource_plan_dir = root / "action_resource_plan"
    llm_route_planner_dir = root / "llm_route_planner"
    request_queue_dir = root / "request_queue"
    input_json.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "component_name": "formalization_gap_planner_standalone_input",
                "target_prover_family": "lean4",
                "library_snapshot_ref": "lean_mathlib_empirical_process_snapshot",
                "routes": [
                    {
                        "route_id": "rank_route_prompt_only_response",
                        "display_name": "rank_route_prompt_only_response",
                        "theorem_statement": (
                            "A distribution-free rank bound follows from a "
                            "missing source-backed rank-uniformity argument."
                        ),
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
    llm_payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        llm_route_planner_dir,
        provider_name="prompt_only",
    )
    request_payload = export_formalization_gap_planner_resource_request_queue(
        action_resource_plan_dir,
        request_queue_dir,
        formalization_gap_planner_llm_route_planner_dir=llm_route_planner_dir,
    )
    return llm_payload, request_payload, request_queue_dir


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


def test_resource_response_ledger_accepts_portable_formal_declaration_hits() -> None:
    root = Path("runs/test_formalization_gap_planner_resource_response_ledger_rocq_hits")
    ledger_dir = root / "ledger"
    response_jsonl = root / "resource_responses.jsonl"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    _, request_queue_dir = _build_request_queue(
        root,
        input_payload={
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
    )
    request_manifest = json.loads(
        (
            request_queue_dir
            / "formalization_gap_planner_resource_request_queue_manifest.json"
        ).read_text(encoding="utf-8")
    )
    formal_request = next(
        row
        for row in request_manifest["rows"]
        if row["target_prover_family"] == "rocq"
        and "formal_declaration_hits" in row["response_contract_fields"]
    )
    response = {
        "resource_request_id": formal_request["resource_request_id"],
        "resource_id": formal_request["resource_id"],
        "expected_response_artifact": formal_request["expected_response_artifact"],
        "response_payload": {
            "formal_declaration_hits": [
                {
                    "declaration": "Rocq.Conformal.rank_uniformity_bridge",
                    "target_prover_family": "rocq",
                    "source_field": "formal_declaration_hits",
                }
            ],
            "coverage_updates": {"rank_uniformity": "bridge_needed"},
        },
        "formal_declaration_hits": [
            {
                "declaration": "Rocq.Conformal.rank_uniformity_bridge",
                "target_prover_family": "rocq",
                "source_field": "formal_declaration_hits",
            }
        ],
        "coverage_updates": {"rank_uniformity": "bridge_needed"},
        "proof_evidence_boundary": "not theorem proof evidence",
    }
    response_jsonl.write_text(
        json.dumps(response, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    payload = export_formalization_gap_planner_resource_response_ledger(
        request_queue_dir,
        ledger_dir,
        response_jsonl=response_jsonl,
    )

    assert payload["all_ok"]
    assert payload["target_prover_family"] == "rocq"
    assert payload["n_response_contract_ok"] == 1
    assert payload["n_rows_with_formal_declaration_hits"] == 1
    assert payload["n_formal_declaration_hits"] == 1
    assert payload["n_rows_with_legacy_lean_declaration_hits"] == 0
    row = next(
        row
        for row in payload["rows"]
        if row["resource_request_id"] == formal_request["resource_request_id"]
    )
    assert row["acceptance_status"] == "ACCEPTED_RESOURCE_RESPONSE"
    assert row["target_prover_family"] == "rocq"
    assert row["response_contract_ok"] is True
    assert row["formal_declaration_hits"] == (
        {
            "declaration": "Rocq.Conformal.rank_uniformity_bridge",
            "target_prover_family": "rocq",
            "source_field": "formal_declaration_hits",
        },
    )
    assert row["lean_declaration_hits"] == ()
    assert "formal_declaration_hits" in row["matched_response_contract_fields"]


def test_resource_response_ledger_preserves_llm_route_planner_trace() -> None:
    root = Path("runs/test_formalization_gap_planner_resource_response_ledger_llm")
    ledger_dir = root / "ledger"
    response_jsonl = root / "resource_responses.jsonl"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    request_payload, request_queue_dir = _build_request_queue(
        root,
        llm_route_planner_rows=[
            {
                "llm_route_planner_row_id": "llm_route_row:rank",
                "request_id": "llm_route_request:rank",
                "route_id": "distribution_free_rank_bound",
                "display_name": "distribution_free_rank_bound",
                "target_prover_family": "lean4",
                "library_snapshot_ref": "lean_mathlib_empirical_process_snapshot",
                "minimal_delta_plan": {
                    "selected_primitives": ["rank_uniformity"],
                },
                "search_requests": [
                    {
                        "request_kind": "literature_discovery",
                        "query": "exchangeability rank_uniformity source proof",
                        "reason": "ground rank_uniformity before route repair",
                        "target_primitives": ["rank_uniformity"],
                    }
                ],
                "planner_next_actions": [],
            }
        ],
    )
    llm_request = next(
        row
        for row in request_payload["rows"]
        if row["request_payload"].get("llm_route_planner_source_kind")
        == "search_request"
        and row["resource_id"] == "paperclip_cli_mcp"
    )
    response = {
        "resource_request_id": llm_request["resource_request_id"],
        "resource_id": llm_request["resource_id"],
        "tool_name": "paperclip_cli_mcp",
        "expected_response_artifact": llm_request["expected_response_artifact"],
        "llm_route_planner_row_id": "llm_route_row:rank",
        "llm_route_planner_request_id": "llm_route_request:rank",
        "llm_route_planner_source_kind": "search_request",
        "llm_route_planner_source_index": 0,
        "llm_route_planner_hook_kind": "literature_discovery",
        "response_payload": {
            "source_refs": ["source:rank_uniformity"],
            "route_evidence_nodes": [
                {
                    "node_id": "rank_uniformity:source",
                    "claim": "rank_uniformity follows from exchangeability",
                }
            ],
            "response_summary": (
                "rank_uniformity source evidence grounded for the LLM route request"
            ),
        },
        "proof_evidence_boundary": "not theorem proof evidence",
    }
    response_jsonl.write_text(
        json.dumps(response, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    payload = export_formalization_gap_planner_resource_response_ledger(
        request_queue_dir,
        ledger_dir,
        response_jsonl=response_jsonl,
    )

    assert payload["all_ok"]
    assert payload["n_llm_route_planner_traced_requests"] == request_payload[
        "n_llm_route_planner_resource_request_rows"
    ]
    assert payload["n_llm_route_planner_traced_responses"] == 1
    assert payload["n_llm_route_planner_response_trace_grounded"] == 1
    assert payload["n_llm_route_planner_response_trace_mismatches"] == 0
    assert payload["n_llm_route_planner_response_trace_missing_echo"] == 0
    ledger_row = next(
        row
        for row in payload["rows"]
        if row["resource_request_id"] == llm_request["resource_request_id"]
    )
    assert ledger_row["acceptance_status"] == "ACCEPTED_RESOURCE_RESPONSE"
    assert ledger_row["llm_route_planner_trace_present"]
    assert ledger_row["llm_route_planner_row_id"] == "llm_route_row:rank"
    assert ledger_row["llm_route_planner_request_id"] == "llm_route_request:rank"
    assert ledger_row["llm_route_planner_source_kind"] == "search_request"
    assert ledger_row["llm_route_planner_source_index"] == 0
    assert ledger_row["llm_route_planner_hook_kind"] == "literature_discovery"
    assert "exchangeability rank_uniformity" in " ".join(
        ledger_row["llm_route_planner_queries"]
    )
    assert ledger_row["llm_route_planner_source_item"]["request_kind"] == (
        "literature_discovery"
    )
    assert (
        payload["n_llm_route_planner_traced_target_theorem_context_packets"]
        == request_payload["n_llm_route_planner_resource_request_rows"]
    )
    assert (
        payload["n_llm_route_planner_traced_target_context_summaries"]
        == request_payload["n_llm_route_planner_resource_request_rows"]
    )
    assert (
        payload["n_llm_route_planner_traced_route_planning_briefs"]
        == request_payload["n_llm_route_planner_resource_request_rows"]
    )
    assert ledger_row["llm_route_planner_target_theorem_context_packet"][
        "route_id"
    ] == "distribution_free_rank_bound"
    assert ledger_row["llm_route_planner_target_context_summary"][
        "primitive_candidates"
    ] == ["rank_uniformity"]
    assert ledger_row["llm_route_planner_route_planning_brief"][
        "target_context"
    ]["route_id"] == "distribution_free_rank_bound"
    assert ledger_row["llm_route_planner_response_trace_grounded"]
    assert ledger_row["llm_route_planner_response_trace_mismatches"] == ()
    assert validate_resource_response_ledger_row(
        ledger_row,
        resource_response_ledger_row_json_schema(),
    ) == []


def test_resource_response_ledger_counts_route_brief_evidence_gap_trace() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_resource_response_ledger_route_brief_gap"
    )
    ledger_dir = root / "ledger"
    response_jsonl = root / "resource_responses.jsonl"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    llm_payload, request_payload, request_queue_dir = (
        _build_prompt_only_route_brief_request_queue(root)
    )
    brief_request = next(
        row
        for row in request_payload["rows"]
        if row["request_payload"].get("llm_route_planner_source_kind")
        == "route_planning_brief_evidence_gap"
        and row["resource_id"] == "paperclip_cli_mcp"
    )
    query = " ".join(
        brief_request["request_payload"]["llm_route_planner_queries"]
    )
    response = {
        "resource_request_id": brief_request["resource_request_id"],
        "resource_id": brief_request["resource_id"],
        "tool_name": "paperclip_cli_mcp",
        "expected_response_artifact": brief_request["expected_response_artifact"],
        "llm_route_planner_row_id": brief_request["request_payload"][
            "llm_route_planner_row_id"
        ],
        "llm_route_planner_request_id": brief_request["request_payload"][
            "llm_route_planner_request_id"
        ],
        "llm_route_planner_source_kind": "route_planning_brief_evidence_gap",
        "llm_route_planner_source_index": brief_request["request_payload"][
            "llm_route_planner_source_index"
        ],
        "llm_route_planner_hook_kind": "literature_discovery",
        "response_payload": {
            "source_refs": ["source:rank_uniformity_brief_gap"],
            "source_snippets": [
                {
                    "source_ref": "source:rank_uniformity_brief_gap",
                    "text": (
                        "rank_uniformity route_planning_brief evidence gap "
                        "source grounding for exchangeability"
                    ),
                    "target_primitives": ["rank_uniformity"],
                }
            ],
            "route_evidence_nodes": [
                {
                    "node_id": "rank_uniformity:brief_gap:source",
                    "claim": (
                        "rank_uniformity source evidence addresses the "
                        "route_planning_brief evidence gap"
                    ),
                    "target_primitives": ["rank_uniformity"],
                }
            ],
            "response_summary": (
                "rank_uniformity route_planning_brief evidence gap source "
                f"grounding for query {query}"
            ),
        },
        "proof_evidence_boundary": "not theorem proof evidence",
    }
    response_jsonl.write_text(
        json.dumps(response, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    payload = export_formalization_gap_planner_resource_response_ledger(
        request_queue_dir,
        ledger_dir,
        response_jsonl=response_jsonl,
    )

    assert llm_payload["n_request_route_planning_evidence_gaps"] == 2
    assert payload["all_ok"]
    assert (
        payload["n_llm_route_planner_traced_route_planning_brief_evidence_gap_rows"]
        == request_payload["n_llm_route_planner_route_planning_brief_evidence_gap_rows"]
    )
    assert (
        payload[
            "n_llm_route_planner_traced_route_planning_brief_evidence_gap_responses"
        ]
        == 1
    )
    assert (
        payload[
            "n_llm_route_planner_traced_route_planning_brief_evidence_gap_grounded_responses"
        ]
        == 1
    )
    assert payload["llm_route_planner_traced_request_by_source_kind"][
        "route_planning_brief_evidence_gap"
    ] == request_payload["n_llm_route_planner_route_planning_brief_evidence_gap_rows"]
    assert payload["llm_route_planner_traced_response_by_source_kind"] == {
        "route_planning_brief_evidence_gap": 1
    }
    assert payload["llm_route_planner_grounded_response_by_source_kind"] == {
        "route_planning_brief_evidence_gap": 1
    }
    ledger_row = next(
        row
        for row in payload["rows"]
        if row["resource_request_id"] == brief_request["resource_request_id"]
    )
    assert ledger_row["acceptance_status"] == "ACCEPTED_RESOURCE_RESPONSE"
    assert ledger_row["llm_route_planner_source_kind"] == (
        "route_planning_brief_evidence_gap"
    )
    assert ledger_row["llm_route_planner_source_item"][
        "route_planning_brief_gap_kind"
    ] == "source_grounding"
    required_fields = ledger_row["llm_route_planner_source_item"][
        "route_planning_brief_gap_required_response_fields"
    ]
    assert "source_refs" in required_fields
    assert "source_snippets" in required_fields
    assert "route_evidence_nodes" in required_fields
    assert ledger_row["llm_route_planner_target_theorem_context_packet"][
        "route_id"
    ] == "rank_route_prompt_only_response"
    assert (
        "distribution-free rank bound"
        in ledger_row["llm_route_planner_target_context_summary"][
            "theorem_statement"
        ]
    )
    assert ledger_row["llm_route_planner_route_planning_brief"][
        "target_context"
    ]["route_id"] == "rank_route_prompt_only_response"
    assert (
        payload["n_llm_route_planner_traced_target_theorem_context_packets"]
        == request_payload[
            "n_llm_route_planner_route_planning_brief_resource_request_rows"
        ]
    )
    assert (
        payload["n_llm_route_planner_traced_route_planning_briefs"]
        == request_payload[
            "n_llm_route_planner_route_planning_brief_resource_request_rows"
        ]
    )
    assert ledger_row["llm_route_planner_response_trace_grounded"]
    assert validate_resource_response_ledger_row(
        ledger_row,
        resource_response_ledger_row_json_schema(),
    ) == []


def test_resource_response_ledger_rejects_route_brief_gap_response_without_gap_required_fields() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_resource_response_ledger_route_brief_gap_contract"
    )
    ledger_dir = root / "ledger"
    response_jsonl = root / "resource_responses.jsonl"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    _, request_payload, request_queue_dir = _build_prompt_only_route_brief_request_queue(
        root
    )
    brief_request = next(
        row
        for row in request_payload["rows"]
        if row["request_payload"].get("llm_route_planner_source_kind")
        == "route_planning_brief_evidence_gap"
        and row["resource_id"] == "paperclip_cli_mcp"
    )
    query = " ".join(
        brief_request["request_payload"]["llm_route_planner_queries"]
    )
    response = {
        "resource_request_id": brief_request["resource_request_id"],
        "resource_id": brief_request["resource_id"],
        "tool_name": "paperclip_cli_mcp",
        "expected_response_artifact": brief_request["expected_response_artifact"],
        "llm_route_planner_row_id": brief_request["request_payload"][
            "llm_route_planner_row_id"
        ],
        "llm_route_planner_request_id": brief_request["request_payload"][
            "llm_route_planner_request_id"
        ],
        "llm_route_planner_source_kind": "route_planning_brief_evidence_gap",
        "llm_route_planner_source_index": brief_request["request_payload"][
            "llm_route_planner_source_index"
        ],
        "llm_route_planner_hook_kind": "literature_discovery",
        "response_payload": {
            "assumption_or_theorem_variant_updates": [
                {"variant": "rank_uniformity informal wording only"}
            ],
            "response_summary": (
                "rank_uniformity route_planning_brief evidence gap source "
                f"grounding for query {query}, but no source refs or snippets"
            ),
        },
        "proof_evidence_boundary": "not theorem proof evidence",
    }
    response_jsonl.write_text(
        json.dumps(response, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    payload = export_formalization_gap_planner_resource_response_ledger(
        request_queue_dir,
        ledger_dir,
        response_jsonl=response_jsonl,
    )

    assert not payload["all_ok"]
    ledger_row = next(
        row
        for row in payload["rows"]
        if row["resource_request_id"] == brief_request["resource_request_id"]
    )
    assert (
        ledger_row["acceptance_status"]
        == "REJECTED_ROUTE_PLANNING_BRIEF_GAP_RESPONSE_CONTRACT"
    )
    assert ledger_row["response_contract_minimum_met"] is True
    assert ledger_row["response_contract_ok"] is False
    assert "assumption_or_theorem_variant_updates" in (
        ledger_row["matched_response_contract_fields"]
    )
    assert any(
        "route_planning_brief evidence gap response missing required fields"
        in error
        for error in ledger_row["errors"]
    )
    assert validate_resource_response_ledger_row(
        ledger_row,
        resource_response_ledger_row_json_schema(),
    ) == []


def test_resource_response_ledger_preserves_llm_residual_goal_context() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_resource_response_ledger_llm_residual"
    )
    ledger_dir = root / "ledger"
    response_jsonl = root / "resource_responses.jsonl"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    request_payload, request_queue_dir = _build_request_queue(
        root,
        llm_route_planner_rows=[
            {
                "llm_route_planner_row_id": "llm_route_row:rank_residual",
                "request_id": "llm_route_request:rank_residual",
                "route_id": "distribution_free_rank_bound",
                "display_name": "distribution_free_rank_bound",
                "target_prover_family": "lean4",
                "library_snapshot_ref": "lean_mathlib_empirical_process_snapshot",
                "minimal_delta_plan": {
                    "selected_primitives": ["rank_uniformity"],
                },
                "search_requests": [],
                "planner_next_actions": [],
                "residual_interpretations": [
                    {
                        "residual_goal": (
                            "rank_uniformity: missing conditional exchangeability "
                            "side condition"
                        ),
                        "interpretation": (
                            "the proof route needs conditional exchangeability "
                            "before replay"
                        ),
                        "route_repair": (
                            "add conditional exchangeability to the informal "
                            "and formal route DAGs"
                        ),
                        "residual_primitives": ["rank_uniformity"],
                        "target_primitives": ["rank_uniformity"],
                        "source_refs": ["conformal_prediction_textbook"],
                    }
                ],
            }
        ],
    )
    route_revision_request = next(
        row
        for row in request_payload["rows"]
        if row["request_payload"].get("llm_route_planner_source_kind")
        == "residual_interpretation"
        and row["resource_id"] == "local_route_revision_overlay"
    )
    assert route_revision_request["request_payload"]["residual_goal_context"] == (
        route_revision_request["request_playbook"]["residual_goal_context"]
    )
    response = {
        "resource_request_id": route_revision_request["resource_request_id"],
        "resource_id": route_revision_request["resource_id"],
        "tool_name": "local_route_revision_overlay",
        "expected_response_artifact": route_revision_request[
            "expected_response_artifact"
        ],
        "llm_route_planner_row_id": "llm_route_row:rank_residual",
        "llm_route_planner_request_id": route_revision_request["request_payload"][
            "llm_route_planner_request_id"
        ],
        "llm_route_planner_source_kind": "residual_interpretation",
        "llm_route_planner_source_index": 0,
        "llm_route_planner_hook_kind": "route_revision",
        "response_payload": {
            "route_revision_decision": {
                "decision": "revise_route",
                "reason": "add conditional exchangeability for rank_uniformity",
            },
            "revised_informal_knowledge_dag_nodes": [
                {
                    "node_id": "informal:rank_uniformity:conditional_exchangeability",
                    "primitive": "rank_uniformity",
                    "claim": (
                        "rank_uniformity replay depends on conditional "
                        "exchangeability"
                    ),
                    "target_primitives": ["rank_uniformity"],
                }
            ],
            "revised_formal_realization_dag_nodes": [
                {
                    "node_id": "formal:rank_uniformity:conditional_exchangeability",
                    "primitive": "rank_uniformity",
                    "coverage_bucket": "bridge_needed",
                    "formalization_action": "prove_bridge",
                    "target_primitives": ["rank_uniformity"],
                }
            ],
            "minimal_delta_plan": {
                "selected_primitives": ["rank_uniformity"],
                "route_cost": 5,
            },
            "target_primitives": route_revision_request["target_primitives"],
            "route_revision_recommended": True,
            "route_revision_reasons": [
                "conditional exchangeability residual requires route repair"
            ],
            "response_summary": (
                "conditional exchangeability route revision for rank_uniformity"
            ),
        },
        "proof_evidence_boundary": "not theorem proof evidence",
    }
    response_jsonl.write_text(
        json.dumps(response, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    payload = export_formalization_gap_planner_resource_response_ledger(
        request_queue_dir,
        ledger_dir,
        response_jsonl=response_jsonl,
    )

    assert payload["all_ok"]
    assert payload["n_llm_route_planner_residual_context_rows"] == 2
    assert payload["n_llm_route_planner_traced_residual_interpretation_rows"] == 2
    assert payload["n_llm_route_planner_response_trace_grounded"] == 1
    ledger_row = next(
        row
        for row in payload["rows"]
        if row["resource_request_id"] == route_revision_request["resource_request_id"]
    )
    assert ledger_row["acceptance_status"] == "ACCEPTED_WITH_ROUTE_REVISION"
    assert ledger_row["llm_route_planner_source_kind"] == "residual_interpretation"
    assert ledger_row["llm_route_planner_hook_kind"] == "route_revision"
    residual_context = ledger_row["residual_goal_context"]
    assert residual_context["source_kind"] == "residual_interpretation"
    assert residual_context["residual_goal"].startswith("rank_uniformity")
    assert residual_context["residual_primitives"] == ("rank_uniformity",)
    assert "conditional exchangeability" in residual_context["route_repair"]
    assert residual_context == route_revision_request["request_payload"][
        "residual_goal_context"
    ]
    assert validate_resource_response_ledger_row(
        ledger_row,
        resource_response_ledger_row_json_schema(),
    ) == []


def test_resource_response_ledger_rejects_llm_route_planner_trace_mismatch() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_resource_response_ledger_llm_mismatch"
    )
    ledger_dir = root / "ledger"
    response_jsonl = root / "resource_responses.jsonl"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    request_payload, request_queue_dir = _build_request_queue(
        root,
        llm_route_planner_rows=[
            {
                "llm_route_planner_row_id": "llm_route_row:rank",
                "request_id": "llm_route_request:rank",
                "route_id": "distribution_free_rank_bound",
                "display_name": "distribution_free_rank_bound",
                "target_prover_family": "lean4",
                "library_snapshot_ref": "lean_mathlib_empirical_process_snapshot",
                "minimal_delta_plan": {
                    "selected_primitives": ["rank_uniformity"],
                },
                "search_requests": [
                    {
                        "request_kind": "literature_discovery",
                        "query": "exchangeability rank_uniformity source proof",
                        "target_primitives": ["rank_uniformity"],
                    }
                ],
                "planner_next_actions": [],
            }
        ],
    )
    llm_request = next(
        row
        for row in request_payload["rows"]
        if row["request_payload"].get("llm_route_planner_source_kind")
        == "search_request"
        and row["resource_id"] == "paperclip_cli_mcp"
    )
    response = {
        "resource_request_id": llm_request["resource_request_id"],
        "resource_id": llm_request["resource_id"],
        "expected_response_artifact": llm_request["expected_response_artifact"],
        "llm_route_planner_row_id": "llm_route_row:wrong",
        "response_payload": {
            "source_refs": ["source:rank_uniformity"],
            "route_evidence_nodes": [
                {
                    "node_id": "rank_uniformity:source",
                    "claim": "rank_uniformity follows from exchangeability",
                }
            ],
            "response_summary": "rank_uniformity source evidence",
        },
        "proof_evidence_boundary": "not theorem proof evidence",
    }
    response_jsonl.write_text(
        json.dumps(response, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    payload = export_formalization_gap_planner_resource_response_ledger(
        request_queue_dir,
        ledger_dir,
        response_jsonl=response_jsonl,
    )

    assert not payload["all_ok"]
    assert payload["n_response_contract_ok"] == 0
    assert payload["n_llm_route_planner_response_trace_mismatches"] == 1
    ledger_row = next(
        row
        for row in payload["rows"]
        if row["resource_request_id"] == llm_request["resource_request_id"]
    )
    assert ledger_row["acceptance_status"] == (
        "REJECTED_LLM_ROUTE_PLANNER_TRACE_MISMATCH"
    )
    assert not ledger_row["response_contract_ok"]
    assert "llm route-planner trace mismatch" in " ".join(ledger_row["errors"])


def test_resource_response_ledger_rejects_cross_prover_declaration_hit_mismatch() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_resource_response_ledger_rocq_hit_mismatch"
    )
    ledger_dir = root / "ledger"
    response_jsonl = root / "resource_responses.jsonl"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    _, request_queue_dir = _build_request_queue(
        root,
        input_payload={
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
    )
    request_manifest = json.loads(
        (
            request_queue_dir
            / "formalization_gap_planner_resource_request_queue_manifest.json"
        ).read_text(encoding="utf-8")
    )
    formal_request = next(
        row
        for row in request_manifest["rows"]
        if row["target_prover_family"] == "rocq"
        and "formal_declaration_hits" in row["response_contract_fields"]
    )
    response = {
        "resource_request_id": formal_request["resource_request_id"],
        "resource_id": formal_request["resource_id"],
        "expected_response_artifact": formal_request["expected_response_artifact"],
        "response_payload": {
            "formal_declaration_hits": [
                {
                    "declaration": "Mathlib.Probability.RankUniformityBridge",
                    "target_prover_family": "lean4",
                    "source_field": "formal_declaration_hits",
                }
            ],
            "lean_declaration_hits": [
                {
                    "declaration": "Mathlib.Probability.RankUniformityBridge",
                    "target_prover_family": "lean4",
                }
            ],
        },
        "formal_declaration_hits": [
            {
                "declaration": "Mathlib.Probability.RankUniformityBridge",
                "target_prover_family": "lean4",
                "source_field": "formal_declaration_hits",
            }
        ],
        "lean_declaration_hits": [
            {
                "declaration": "Mathlib.Probability.RankUniformityBridge",
                "target_prover_family": "lean4",
            }
        ],
        "proof_evidence_boundary": "not theorem proof evidence",
    }
    response_jsonl.write_text(
        json.dumps(response, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    payload = export_formalization_gap_planner_resource_response_ledger(
        request_queue_dir,
        ledger_dir,
        response_jsonl=response_jsonl,
    )

    assert not payload["all_ok"]
    assert payload["n_response_schema_valid"] == 1
    assert payload["n_response_contract_ok"] == 0
    assert payload["n_rejected"] == 1
    row = next(
        row
        for row in payload["rows"]
        if row["resource_request_id"] == formal_request["resource_request_id"]
    )
    assert row["acceptance_status"] == "REJECTED_DECLARATION_TARGET_MISMATCH"
    assert row["response_contract_minimum_met"] is True
    assert row["response_contract_ok"] is False
    assert row["lean_declaration_hits"]
    error_text = "\n".join(row["errors"])
    assert (
        "formal_declaration_hits[0].target_prover_family must match row target_prover_family"
        in error_text
    )
    assert (
        "lean_declaration_hits[0].target_prover_family must match row target_prover_family"
        in error_text
    )
    assert "lean_declaration_hits is a Lean-only legacy alias" in error_text
    malformed = dict(row)
    malformed["errors"] = []
    assert (
        "lean_declaration_hits is a Lean-only legacy alias; non-Lean "
        "resource response rows must use formal_declaration_hits only"
        in validate_resource_response_ledger_row(
            malformed,
            resource_response_ledger_row_json_schema(),
        )
    )


def test_resource_response_ledger_rejects_source_type_implied_target_mismatch() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_resource_response_ledger_source_type_mismatch"
    )
    ledger_dir = root / "ledger"
    response_jsonl = root / "resource_responses.jsonl"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    _, request_queue_dir = _build_request_queue(
        root,
        input_payload={
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
    )
    request_manifest = json.loads(
        (
            request_queue_dir
            / "formalization_gap_planner_resource_request_queue_manifest.json"
        ).read_text(encoding="utf-8")
    )
    formal_request = next(
        row
        for row in request_manifest["rows"]
        if row["target_prover_family"] == "rocq"
        and "formal_declaration_hits" in row["response_contract_fields"]
    )
    response = {
        "resource_request_id": formal_request["resource_request_id"],
        "resource_id": formal_request["resource_id"],
        "expected_response_artifact": formal_request["expected_response_artifact"],
        "response_payload": {
            "response_summary": "rank_uniformity formal library coverage",
            "formal_declaration_hits": [
                {
                    "declaration": "Mathlib.Probability.RankUniformityBridge",
                    "source_type": "lean_library",
                    "source_field": "formal_declaration_hits",
                }
            ],
            "coverage_updates": {"rank_uniformity": "exact_exists"},
        },
        "proof_evidence_boundary": "not theorem proof evidence",
    }
    response_jsonl.write_text(
        json.dumps(response, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    payload = export_formalization_gap_planner_resource_response_ledger(
        request_queue_dir,
        ledger_dir,
        response_jsonl=response_jsonl,
    )

    assert not payload["all_ok"]
    assert payload["n_response_contract_ok"] == 0
    assert payload["n_rejected"] == 1
    assert payload["n_declaration_hit_target_mismatch_rows"] == 1
    assert payload["n_declaration_hit_target_mismatches"] == 1
    row = next(
        row
        for row in payload["rows"]
        if row["resource_request_id"] == formal_request["resource_request_id"]
    )
    assert row["acceptance_status"] == "REJECTED_DECLARATION_TARGET_MISMATCH"
    assert row["response_contract_minimum_met"] is True
    assert row["response_contract_ok"] is False
    assert row["formal_declaration_hits"] == (
        {
            "declaration": "Mathlib.Probability.RankUniformityBridge",
            "source_type": "lean_library",
            "source_field": "formal_declaration_hits",
        },
    )
    error_text = "\n".join(row["errors"])
    assert (
        "formal_declaration_hits[0].source_type implies lean4 "
        "but row target_prover_family is rocq"
    ) in error_text


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
                "actionable_work_items": source_request["actionable_work_items"],
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
            "actionable_work_items": source_request["actionable_work_items"],
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
                "target_primitives": proof_request["target_primitives"],
                "actionable_work_items": proof_request["actionable_work_items"],
                "lean_declaration_hits": [
                    {
                        "declaration": "Mathlib.Probability.RankUniformityBridge",
                        "target_prover_family": "lean4",
                    }
                ],
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
            "actionable_work_items": proof_request["actionable_work_items"],
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
    assert payload["n_rows_with_target_primitives"] == payload["n_ledger_rows"]
    assert payload["n_target_primitives"] == payload["n_ledger_rows"]
    assert payload["n_rows_with_actionable_work_items"] == payload["n_ledger_rows"]
    assert payload["n_actionable_work_items"] == payload["n_ledger_rows"]
    assert payload["n_minimal_delta_reuse_ready"] == sum(
        1
        for row in request_payload["rows"]
        if int(row["minimal_delta_cost_score"]) <= 15
    )
    assert payload["n_minimal_delta_light_bridge_or_wrapper"] == sum(
        1
        for row in request_payload["rows"]
        if 15 < int(row["minimal_delta_cost_score"]) <= 45
    )
    assert payload["n_minimal_delta_source_or_new_theory"] == sum(
        1
        for row in request_payload["rows"]
        if 45 < int(row["minimal_delta_cost_score"]) < 100
    )
    assert payload["n_minimal_delta_alignment_blocked"] == sum(
        1
        for row in request_payload["rows"]
        if int(row["minimal_delta_cost_score"]) >= 100
    )
    assert payload["average_reuse_readiness_score"] == round(
        sum(int(row["reuse_readiness_score"]) for row in request_payload["rows"])
        / len(request_payload["rows"])
    )
    assert payload["average_evidence_readiness_score"] == round(
        sum(int(row["evidence_readiness_score"]) for row in request_payload["rows"])
        / len(request_payload["rows"])
    )
    assert payload["n_rows_with_formal_declaration_hits"] == 1
    assert payload["n_formal_declaration_hits"] == 1
    assert payload["n_rows_with_legacy_lean_declaration_hits"] == 1
    assert payload["n_route_revision_recommended"] == 1
    assert payload["n_rejected"] == 0
    assert payload["resource_response_schema"]["$id"] == RESOURCE_RESPONSE_SCHEMA_ID
    assert "formal_declaration_hits" in payload["resource_response_schema"]["properties"]
    assert (
        payload["resource_response_ledger_row_schema"]["$id"]
        == RESOURCE_RESPONSE_LEDGER_ROW_SCHEMA_ID
    )
    assert "formal_declaration_hits" in payload[
        "resource_response_ledger_row_schema"
    ]["required"]
    assert "actionable_work_items" in payload[
        "resource_response_ledger_row_schema"
    ]["required"]
    for priority_field in (
        "priority_score",
        "minimal_delta_cost_score",
        "reuse_readiness_score",
        "evidence_readiness_score",
        "priority_rationale",
    ):
        assert priority_field in payload["resource_response_ledger_row_schema"][
            "required"
        ]
    source_ledger = next(
        row
        for row in payload["rows"]
        if row["resource_request_id"] == source_request["resource_request_id"]
    )
    assert source_ledger["acceptance_status"] == "ACCEPTED_RESOURCE_RESPONSE"
    assert tuple(source_ledger["target_primitives"]) == tuple(
        source_request["target_primitives"]
    )
    assert tuple(source_ledger["actionable_work_items"]) == tuple(
        source_request["actionable_work_items"]
    )
    assert source_ledger["request_playbook_present"]
    assert source_ledger["response_playbook_grounded"]
    assert source_ledger["response_playbook_grounding_terms"]
    assert source_ledger["acceptance_gate"] == source_request["acceptance_gate"]
    assert source_ledger["response_contract_fields"] == source_request["response_contract_fields"]
    assert source_ledger["priority_score"] == source_request["priority_score"]
    assert source_ledger["minimal_delta_cost_score"] == source_request[
        "minimal_delta_cost_score"
    ]
    assert source_ledger["reuse_readiness_score"] == source_request[
        "reuse_readiness_score"
    ]
    assert source_ledger["evidence_readiness_score"] == source_request[
        "evidence_readiness_score"
    ]
    assert tuple(source_ledger["priority_rationale"]) == tuple(
        source_request["priority_rationale"]
    )
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
    assert tuple(proof_ledger["target_primitives"]) == tuple(
        proof_request["target_primitives"]
    )
    assert tuple(proof_ledger["actionable_work_items"]) == tuple(
        proof_request["actionable_work_items"]
    )
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
    assert proof_ledger["priority_score"] == proof_request["priority_score"]
    assert proof_ledger["minimal_delta_cost_score"] == proof_request[
        "minimal_delta_cost_score"
    ]
    assert proof_ledger["reuse_readiness_score"] == proof_request[
        "reuse_readiness_score"
    ]
    assert proof_ledger["evidence_readiness_score"] == proof_request[
        "evidence_readiness_score"
    ]
    assert tuple(proof_ledger["priority_rationale"]) == tuple(
        proof_request["priority_rationale"]
    )
    assert set(proof_request["stop_conditions"]).issubset(
        set(proof_ledger["quality_controls"]["stop_conditions"])
    )
    assert proof_ledger["response_contract_minimum_met"]
    assert proof_ledger["dispatch_spec"]["adapter_surface"] == "target_prover_lsp_mcp"
    assert "prover_diagnostics" in proof_ledger["matched_response_contract_fields"]
    assert proof_ledger["formal_declaration_hits"] == proof_ledger[
        "lean_declaration_hits"
    ]
    assert proof_ledger["formal_declaration_hits"] == (
        {
            "declaration": "Mathlib.Probability.RankUniformityBridge",
            "target_prover_family": "lean4",
        },
    )
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
    malformed_score = dict(proof_ledger)
    malformed_score["minimal_delta_cost_score"] = 101
    assert "minimal_delta_cost_score must be between 0 and 100" in (
        validate_resource_response_ledger_row(
            malformed_score,
            resource_response_ledger_row_json_schema(),
        )
    )
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


def test_resource_response_ledger_preserves_formal_attempt_context() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_resource_response_ledger_formal_attempt"
    )
    ledger_dir = root / "ledger"
    rejected_ledger_dir = root / "ledger_rejected"
    response_jsonl = root / "resource_responses.jsonl"
    rejected_response_jsonl = root / "resource_responses_rejected.jsonl"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    request_payload, request_queue_dir = _build_request_queue(
        root,
        llm_route_planner_rows=[
            {
                "llm_route_planner_row_id": "llm_route_row:formal_attempt",
                "request_id": "llm_route_request:formal_attempt",
                "route_id": "distribution_free_rank_bound",
                "display_name": "distribution_free_rank_bound",
                "target_prover_family": "lean4",
                "library_snapshot_ref": "lean_mathlib_empirical_process_snapshot",
                "minimal_delta_plan": {
                    "selected_primitives": ["exchangeability", "rank_uniformity"],
                },
                "formal_attempt_queue": [
                    {
                        "attempt_id": "attempt:exchangeability_reuse",
                        "formal_node_id": "formal:exchangeability",
                        "primitive": "exchangeability",
                        "target_primitives": ["exchangeability"],
                        "target_prover_family": "lean4",
                        "attempt_kind": "reuse_existing_declaration",
                        "action": "run exchangeability reuse in Lean",
                        "expected_feedback": ["kernel_status", "residual_goals"],
                        "prerequisite_formal_node_ids": [],
                    },
                    {
                        "attempt_id": "attempt:rank_uniformity_bridge",
                        "formal_node_id": "formal:rank_uniformity",
                        "primitive": "rank_uniformity",
                        "target_primitives": ["rank_uniformity"],
                        "target_prover_family": "lean4",
                        "attempt_kind": "bridge_lemma",
                        "action": "run rank uniformity after exchangeability closes",
                        "expected_feedback": ["kernel_status", "residual_goals"],
                        "prerequisite_formal_node_ids": ["formal:exchangeability"],
                    },
                ],
                "formal_attempt_queue_schedule": {
                    "attempt_dependency_rows": [
                        {
                            "formal_attempt_queue_index": 0,
                            "attempt_id": "attempt:exchangeability_reuse",
                            "formal_node_id": "formal:exchangeability",
                            "primitive": "exchangeability",
                            "attempt_kind": "reuse_existing_declaration",
                            "target_prover_family": "lean4",
                            "initial_ready": True,
                            "dependency_status": "initial_ready",
                            "prerequisite_formal_node_ids": [],
                            "prerequisite_attempt_ids": [],
                            "missing_prerequisite_formal_node_ids": [],
                        },
                        {
                            "formal_attempt_queue_index": 1,
                            "attempt_id": "attempt:rank_uniformity_bridge",
                            "formal_node_id": "formal:rank_uniformity",
                            "primitive": "rank_uniformity",
                            "attempt_kind": "bridge_lemma",
                            "target_prover_family": "lean4",
                            "initial_ready": False,
                            "dependency_status": (
                                "waiting_for_formal_prerequisite_attempts"
                            ),
                            "prerequisite_formal_node_ids": [
                                "formal:exchangeability"
                            ],
                            "prerequisite_attempt_ids": [
                                "attempt:exchangeability_reuse"
                            ],
                            "missing_prerequisite_formal_node_ids": [],
                        },
                    ],
                },
            }
        ],
    )
    request = next(
        row
        for row in request_payload["rows"]
        if row["request_payload"].get("llm_route_planner_source_kind")
        == "formal_attempt_queue"
        and row["resource_id"] == "lean_lsp_mcp"
    )
    formal_attempt_context = request["request_payload"]["formal_attempt_context"]
    response = {
        "resource_request_id": request["resource_request_id"],
        "resource_id": request["resource_id"],
        "tool_name": "lean_lsp_mcp",
        "expected_response_artifact": request["expected_response_artifact"],
        "response_payload": {
            "target_primitives": request["target_primitives"],
            "actionable_work_items": request["actionable_work_items"],
            "formal_attempt_context": formal_attempt_context,
            "prover_diagnostics": [
                "exchangeability reuse leaves an unresolved measurability goal"
            ],
            "residual_goals": ["prove exchangeability measurability side condition"],
            "prover_attempt_status": "failed_with_residual_goals",
            "prover_diagnostic_signature": (
                "residual_goal:exchangeability_measurability"
            ),
            "route_revision_recommended": True,
            "route_revision_reasons": [
                "formal attempt exposed an exchangeability measurability side condition"
            ],
        },
        "formal_attempt_context": formal_attempt_context,
        "actionable_work_items": request["actionable_work_items"],
        "proof_evidence_boundary": "not theorem proof evidence",
    }
    response_jsonl.write_text(
        json.dumps(response, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    payload = export_formalization_gap_planner_resource_response_ledger(
        request_queue_dir,
        ledger_dir,
        response_jsonl=response_jsonl,
    )

    assert payload["all_ok"]
    assert payload["n_llm_route_planner_formal_attempt_context_rows"] == 3
    assert payload["n_llm_route_planner_formal_attempt_context_responses"] == 1
    row = next(
        item
        for item in payload["rows"]
        if item["resource_request_id"] == request["resource_request_id"]
    )
    assert row["acceptance_status"] == "ACCEPTED_WITH_ROUTE_REVISION"
    assert row["formal_attempt_context"]["attempt_id"] == (
        "attempt:exchangeability_reuse"
    )
    assert row["formal_attempt_context"] == formal_attempt_context
    assert "formal_attempt_context" in row["matched_response_contract_fields"]
    assert row["response_contract_ok"] is True

    rejected_response = dict(response)
    rejected_response["response_payload"] = dict(response["response_payload"])
    rejected_response["response_payload"]["formal_attempt_context"] = {
        **formal_attempt_context,
        "attempt_id": "attempt:wrong",
    }
    rejected_response_jsonl.write_text(
        json.dumps(rejected_response, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    rejected_payload = export_formalization_gap_planner_resource_response_ledger(
        request_queue_dir,
        rejected_ledger_dir,
        response_jsonl=rejected_response_jsonl,
    )

    assert not rejected_payload["all_ok"]
    rejected_row = next(
        item
        for item in rejected_payload["rows"]
        if item["resource_request_id"] == request["resource_request_id"]
    )
    assert rejected_row["acceptance_status"] == (
        "REJECTED_FORMAL_ATTEMPT_CONTEXT_MISMATCH"
    )
    assert rejected_row["response_contract_ok"] is False
    assert "formal_attempt_context.attempt_id" in "\n".join(
        rejected_row["errors"]
    )


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


def test_resource_response_ledger_rejects_expanded_target_primitives() -> None:
    root = Path("runs/test_formalization_gap_planner_resource_response_ledger_scope")
    ledger_dir = root / "ledger"
    response_jsonl = root / "resource_responses.jsonl"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    request_payload, request_queue_dir = _build_request_queue(root)
    request = next(
        row for row in request_payload["rows"] if row["resource_id"] == "lean_lsp_mcp"
    )
    response = {
        "resource_request_id": request["resource_request_id"],
        "resource_id": request["resource_id"],
        "expected_response_artifact": request["expected_response_artifact"],
        "target_primitives": ["rank_uniformity", "spectral_gap"],
        "response_payload": {
            "prover_diagnostics": ["unknown identifier rank_uniformity"],
            "target_primitives": ["rank_uniformity", "spectral_gap"],
        },
        "prover_diagnostics": ["unknown identifier rank_uniformity"],
        "proof_evidence_boundary": "not theorem proof evidence",
    }
    response_jsonl.write_text(
        json.dumps(response, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    payload = export_formalization_gap_planner_resource_response_ledger(
        request_queue_dir,
        ledger_dir,
        response_jsonl=response_jsonl,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    assert payload["n_response_schema_valid"] == 1
    assert payload["n_response_contract_ok"] == 0
    assert payload["n_ledger_row_schema_valid"] == payload["n_ledger_rows"]
    row = next(
        row
        for row in payload["rows"]
        if row["resource_request_id"] == request["resource_request_id"]
    )
    assert row["acceptance_status"] == "REJECTED_RESPONSE_TARGET_SCOPE_EXPANSION"
    assert row["response_contract_ok"] is False
    assert tuple(row["target_primitives"]) == ("rank_uniformity", "spectral_gap")
    assert any(
        "target_primitives must not expand beyond resource request target_primitives"
        in error
        and "spectral_gap" in error
        for error in row["errors"]
    )
    malformed = dict(row)
    malformed["response_contract_ok"] = True
    assert (
        "rejected resource response rows must not set response_contract_ok=true"
        in validate_resource_response_ledger_row(
            malformed,
            resource_response_ledger_row_json_schema(),
        )
    )


def test_resource_response_ledger_rejects_expanded_actionable_work_items() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_resource_response_ledger_action_scope"
    )
    ledger_dir = root / "ledger"
    response_jsonl = root / "resource_responses.jsonl"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    request_payload, request_queue_dir = _build_request_queue(root)
    request = next(
        row for row in request_payload["rows"] if row["resource_id"] == "lean_lsp_mcp"
    )
    expanded_action_items = [
        *request["actionable_work_items"],
        "spectral_gap: prove an unrelated spectral gap bridge",
    ]
    response = {
        "resource_request_id": request["resource_request_id"],
        "resource_id": request["resource_id"],
        "expected_response_artifact": request["expected_response_artifact"],
        "actionable_work_items": expanded_action_items,
        "response_payload": {
            "prover_diagnostics": ["unknown identifier rank_uniformity"],
            "actionable_work_items": expanded_action_items,
        },
        "prover_diagnostics": ["unknown identifier rank_uniformity"],
        "proof_evidence_boundary": "not theorem proof evidence",
    }
    response_jsonl.write_text(
        json.dumps(response, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    payload = export_formalization_gap_planner_resource_response_ledger(
        request_queue_dir,
        ledger_dir,
        response_jsonl=response_jsonl,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    assert payload["n_response_schema_valid"] == 1
    assert payload["n_response_contract_ok"] == 0
    row = next(
        row
        for row in payload["rows"]
        if row["resource_request_id"] == request["resource_request_id"]
    )
    assert row["acceptance_status"] == "REJECTED_RESPONSE_ACTIONABLE_SCOPE_EXPANSION"
    assert row["response_contract_ok"] is False
    assert "spectral_gap: prove an unrelated spectral gap bridge" in row[
        "actionable_work_items"
    ]
    assert any(
        "actionable_work_items must not expand beyond resource request actionable_work_items"
        in error
        and "spectral_gap" in error
        for error in row["errors"]
    )
    malformed = dict(row)
    malformed["response_contract_ok"] = True
    assert (
        "actionable scope expansion rows must not set response_contract_ok=true"
        in validate_resource_response_ledger_row(
            malformed,
            resource_response_ledger_row_json_schema(),
        )
    )


def test_resource_response_ledger_rejects_off_scope_evidence_primitives() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_resource_response_ledger_evidence_scope"
    )
    ledger_dir = root / "ledger"
    response_jsonl = root / "resource_responses.jsonl"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    request_payload, request_queue_dir = _build_request_queue(root)
    request = next(
        row
        for row in request_payload["rows"]
        if row["resource_id"] == "paperclip_cli_mcp"
    )
    response = {
        "resource_request_id": request["resource_request_id"],
        "resource_id": request["resource_id"],
        "expected_response_artifact": request["expected_response_artifact"],
        "response_payload": {
            "response_summary": "coverage_inequality source evidence found",
            "source_refs": ["source:coverage_inequality"],
            "revised_selected_primitives": ["coverage_inequality", "spectral_gap"],
            "revised_delta_primitives": ["spectral_gap"],
            "route_evidence_nodes": [
                {
                    "node_id": "spectral_gap:source",
                    "primitive": "spectral_gap",
                    "claim": "spectral_gap follows from compactness",
                }
            ],
            "coverage_updates": {"spectral_gap": "exact_exists"},
        },
        "proof_evidence_boundary": "not theorem proof evidence",
    }
    response_jsonl.write_text(
        json.dumps(response, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    payload = export_formalization_gap_planner_resource_response_ledger(
        request_queue_dir,
        ledger_dir,
        response_jsonl=response_jsonl,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    assert payload["n_response_contract_ok"] == 0
    assert payload["n_response_evidence_scope_expansion_rows"] == 1
    row = next(
        row
        for row in payload["rows"]
        if row["resource_request_id"] == request["resource_request_id"]
    )
    assert row["acceptance_status"] == "REJECTED_RESPONSE_EVIDENCE_SCOPE_EXPANSION"
    assert row["response_contract_minimum_met"] is True
    assert row["response_contract_ok"] is False
    assert tuple(row["target_primitives"]) == tuple(request["target_primitives"])
    assert any(
        "coverage_updates primitives must not expand beyond resource request target_primitives"
        in error
        and "spectral_gap" in error
        for error in row["errors"]
    )
    assert any(
        "revised_selected_primitives primitives must not expand beyond resource request target_primitives"
        in error
        and "spectral_gap" in error
        for error in row["errors"]
    )
    assert any(
        "revised_delta_primitives primitives must not expand beyond resource request target_primitives"
        in error
        and "spectral_gap" in error
        for error in row["errors"]
    )
    assert any(
        "route_evidence_nodes[0] primitives must not expand beyond resource request target_primitives"
        in error
        and "spectral_gap" in error
        for error in row["errors"]
    )


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
