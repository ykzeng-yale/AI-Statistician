from __future__ import annotations

import json
from pathlib import Path

import pytest

from ai_statistician.cli import main
from ai_statistician.formalizer_llm import (
    _formalizer_repair_context,
    build_formalizer_prompt,
)
from ai_statistician.formalizer_pseudo_formal_packet_eval import (
    FORMALIZER_PSEUDO_FORMAL_PACKET_EVAL_NOT_PROOF_EVIDENCE,
    _pseudo_formal_packet_eval_feedback,
    _pseudo_formal_packet_eval_question,
    _pseudo_formal_packet_eval_theory_packet,
    run_formalizer_pseudo_formal_packet_eval,
    write_formalizer_pseudo_formal_packet_eval_failure_manifest,
)
from ai_statistician.llm_json_repair import PacketValidationError
from ai_statistician.pseudo_formalization import (
    PSEUDO_FORMAL_BLOCK_ROUTING_METHOD_STAGE,
    PSEUDO_FORMALIZATION_NOT_PROOF_EVIDENCE,
    PSEUDO_FORMALIZATION_PROMOTION_GATE,
    PSEUDO_FORMAL_TARGET_LANE_EXACT_SEMANTIC_DEFINITION,
    PSEUDO_FORMAL_TARGET_LANE_SOURCE_TO_BRIDGE,
    pseudo_formal_block_work_order_rows,
    pseudo_formal_routable_work_order_rows,
    PSEUDO_FORMAL_VERIFICATION_METHOD_CONTRACT_ID,
)


def _write_static_formalizer_response(path: Path) -> None:
    response = {
        "formal_targets": [
            {
                "id": "source_theorem_gap",
                "informal_source": "Source theorem coverage step needs semantic grounding.",
                "lean_statement_sketch": "",
                "expected_status": "FORMAL_GAP",
                "source_theorem_target_provenance": {
                    "source_theorem_target_known": True,
                    "target_lean_declaration": "blocked_source_theorem",
                    "source_theorem_goal_id": "theorem:coverage",
                },
            }
        ],
        "lemma_dependency_plan": [
            {
                "from": "pf_block",
                "to": "source theorem semantic-definition lane",
                "role": "route exact semantic definition before Lean replay",
                "risk": "coverage event definition is missing",
            }
        ],
        "retrieval_queries": [
            {
                "query": "rank threshold coverage event semantic definition Lean",
                "target_library": "LeanRAG",
                "purpose": "ground PF residual in exact source definitions",
            }
        ],
        "proof_search_plan": {
            "preferred_tools": ["local_lean"],
            "kernel_check_plan": ["only after PF residuals are grounded"],
            "known_blockers": ["coverage_event exact definition missing"],
        },
        "proof_bank_obligation_requests": [],
        "source_to_bridge_premise_derivation_candidates": [],
        "source_to_bridge_premise_derivation_candidate_requests": [],
        "pseudo_formal_proof_packets": [
            {
                "schema_version": 1,
                "packet_id": "pseudo_formal_packet:coverage_rank_threshold",
                "theorem_id": "theorem:coverage",
                "source_artifact_id": (
                    "theory:formalizer_pseudo_formal_packet_eval"
                ),
                "pseudo_formal_method_contract_id": (
                    PSEUDO_FORMAL_VERIFICATION_METHOD_CONTRACT_ID
                ),
                "pseudo_formal_pipeline_stages": [
                    PSEUDO_FORMAL_BLOCK_ROUTING_METHOD_STAGE
                ],
                "proof_evidence_status": PSEUDO_FORMALIZATION_NOT_PROOF_EVIDENCE,
                "kernel_verified": False,
                "source_theorem_kernel_verified": False,
                "promotion_gate": PSEUDO_FORMALIZATION_PROMOTION_GATE,
                "proof_evidence_boundary": (
                    "Pseudo-formalization rows are not theorem proof evidence; "
                    "source theorem proof requires target-prover kernel replay."
                ),
                "blocks": [
                    {
                        "block_id": "b_semantic",
                        "block_type": "claim",
                        "block_depth": 1,
                        "dependency_scope": "earlier_block_statement_only",
                        "premises": [
                            "source proof invokes rank-threshold coverage event"
                        ],
                        "conclusion": (
                            "the coverage event depends on the exact "
                            "rank-threshold semantic definition"
                        ),
                        "proof_text": (
                            "The informal step identifies coverage with a rank "
                            "threshold event, so Formalizer must request the exact "
                            "source definition before Lean replay."
                        ),
                        "dependency_ids": [],
                        "scope_parent_id": "",
                        "inherited_scope": [],
                        "source_anchors": [
                            {
                                "kind": "proof_body",
                                "id": "proof_body:rank_threshold_step",
                                "excerpt": "rank-threshold coverage event",
                            }
                        ],
                        "semantic_primitive_requirements": ["coverage_event"],
                        "lean_feasibility": "needs_semantic_definition",
                        "faithfulness_status": "faithful",
                        "faithfulness_repair": {
                            "status": "not_required",
                            "attempts": 0,
                            "flagged_discrepancies": [],
                        },
                        "block_verification": {
                            "verdict": "unknown",
                            "reason": "exact coverage_event definition is pending",
                        },
                        "kernel_verified": False,
                    }
                ],
            }
        ],
        "gap_taxonomy": [
            {
                "gap": "exact coverage event semantic definition",
                "kind": "semantic_alignment",
                "next_owner": "FormalizerProofEngineer",
            }
        ],
        "critic_findings": [
            {"critic": "pf_eval", "finding": "PF/BV packet is routing only"}
        ],
        "next_actions": [
            {
                "owner_agent": "AgentRuntime",
                "action": "route PF residual block",
                "acceptance_gate": "target-prover kernel replay required",
            }
        ],
    }
    path.write_text(json.dumps(response), encoding="utf-8")


def _prompt_payload(prompt: str) -> dict[str, object]:
    json_start = prompt.index('{"question":')
    return json.loads(prompt[json_start:])


def test_formalizer_required_pf_prompt_includes_source_bound_packet_seed() -> None:
    question = _pseudo_formal_packet_eval_question()
    theory_packet = _pseudo_formal_packet_eval_theory_packet()
    feedback = _pseudo_formal_packet_eval_feedback()
    prompt = build_formalizer_prompt(
        question=question,
        theory_packet=theory_packet,
        simulation_manifest={
            "manifest_id": "simulation:pf_seed_test",
            "simulation_passed": True,
            "proof_evidence_status": "SIMULATION_NOT_PROOF_EVIDENCE",
        },
        algorithm_manifest={"manifest_id": "algorithm:pf_seed_test", "n_executed": 1},
        registered_problem={"question_id": question.id},
        theorem_goals=[],
        proof_bank_obligation_catalog=[],
        proof_bank_runtime_memory_summary={},
        environment_feedback=feedback,
    )

    payload = _prompt_payload(prompt)
    seed = payload["pseudo_formalization_required_packet_seed"]
    block = seed["blocks"][0]

    assert seed["theorem_id"] == "theorem:coverage"
    assert seed["source_artifact_id"] == "theory:formalizer_pseudo_formal_packet_eval"
    assert seed["proof_evidence_status"] == PSEUDO_FORMALIZATION_NOT_PROOF_EVIDENCE
    assert seed["kernel_verified"] is False
    assert seed["source_theorem_kernel_verified"] is False
    assert PSEUDO_FORMAL_TARGET_LANE_EXACT_SEMANTIC_DEFINITION in (
        seed["required_target_lanes_to_satisfy"]
    )
    assert block["conclusion"]
    assert block["source_anchors"][0]["id"] == "proof_body:rank_threshold_step"
    assert block["lean_feasibility"] == "needs_semantic_definition"
    assert block["semantic_primitive_requirements"]
    assert block["faithfulness_status"] == "faithful"
    assert feedback["pseudo_formal_block_routing_target_lanes"] == [
        "source_theorem_exact_semantic_definition",
        "source_to_bridge",
    ]
    assert "pseudo_formalization_required_packet_seed" in prompt


def test_formalizer_prompt_prefers_component_gate_failure_repair_seed() -> None:
    question = _pseudo_formal_packet_eval_question()
    component_seed = {
        "schema_version": 1,
        "packet_id": "pseudo_formal_packet:component_gate_repair",
        "theorem_id": "theorem:coverage",
        "source_artifact_id": "formalizer_pf_component_gate:failed_manifest",
        "proof_evidence_status": PSEUDO_FORMALIZATION_NOT_PROOF_EVIDENCE,
        "kernel_verified": False,
        "source_theorem_kernel_verified": False,
        "blocks": [
            {
                "block_id": "pf_block:component_gate_exact",
                "block_type": "claim",
                "block_depth": 1,
                "premises": ["calibration rank threshold source step"],
                "conclusion": (
                    "C_n is the exact source semantic primitive for the "
                    "coverage event."
                ),
                "proof_text": "The source proof uses C_n as the rank threshold.",
                "dependency_ids": [],
                "scope_parent_id": "",
                "dependency_scope": "earlier_block_statement_only",
                "inherited_scope": [],
                "source_anchors": [
                    {
                        "kind": "proof_body",
                        "id": "proof_body:component_gate_rank_threshold",
                        "excerpt": "C_n rank threshold coverage event",
                    }
                ],
                "semantic_primitive_requirements": ["component_gate_C_n"],
                "lean_feasibility": "needs_semantic_definition",
                "faithfulness_status": "faithful",
                "faithfulness_repair": {
                    "status": "not_required",
                    "attempts": 0,
                    "flagged_discrepancies": [],
                },
                "block_verification": {
                    "verdict": "unknown",
                    "verifier_provenance": "not_run",
                    "independent_verifier": False,
                    "rollout_count": 0,
                },
                "kernel_verified": False,
            }
        ],
    }
    proof_memory_summary = {
        "pseudo_formalization_required": True,
        "requires_pseudo_formalization": True,
        "pseudo_formalization_required_reason": (
            "formalizer_pseudo_formal_packet_component_gate_failed_required_repair"
        ),
        "formalizer_pseudo_formal_packet_component_gate_failure_available": True,
        "formalizer_pseudo_formal_packet_component_gate_failure_memory": [
            {
                "component_eval_manifest_path": (
                    "runs/component_gate_failure/manifest.json"
                ),
                "result_status": "FAILED",
                "failure_type": "PacketValidationError",
                "required_target_lanes": [
                    PSEUDO_FORMAL_TARGET_LANE_EXACT_SEMANTIC_DEFINITION,
                    PSEUDO_FORMAL_TARGET_LANE_SOURCE_TO_BRIDGE,
                ],
                "validation_issue_summary": {
                    "issue_kinds": [
                        "missing_conclusion",
                        "missing_source_anchors",
                    ],
                    "blocking_issue_kinds": [
                        "missing_conclusion",
                        "missing_source_anchors",
                    ],
                    "n_no_lane_routable_work_order_rows": 1,
                },
                "concrete_lane_routable_repair_seed": component_seed,
                "proof_evidence_status": (
                    "FORMALIZER_PSEUDO_FORMAL_PACKET_COMPONENT_GATE_FEEDBACK_"
                    "NOT_PROOF_EVIDENCE"
                ),
            }
        ],
    }

    prompt = build_formalizer_prompt(
        question=question,
        theory_packet=_pseudo_formal_packet_eval_theory_packet(),
        simulation_manifest={
            "manifest_id": "simulation:component_seed_test",
            "proof_evidence_status": "SIMULATION_NOT_PROOF_EVIDENCE",
        },
        algorithm_manifest={"manifest_id": "algorithm:component_seed_test"},
        registered_problem={"question_id": question.id},
        theorem_goals=[],
        proof_bank_obligation_catalog=[],
        proof_bank_runtime_memory_summary=proof_memory_summary,
        environment_feedback={},
    )
    payload = _prompt_payload(prompt)
    seed = payload["pseudo_formalization_required_packet_seed"]
    copy_packet = payload["pseudo_formalization_required_copy_fragment"][
        "pseudo_formal_proof_packets"
    ][0]
    rows = pseudo_formal_routable_work_order_rows(
        pseudo_formal_block_work_order_rows(copy_packet)
    )

    assert seed["packet_id"] == "pseudo_formal_packet:component_gate_repair"
    assert seed["component_gate_failure_seed_source"] == (
        "formalizer_pseudo_formal_packet_component_gate_failure_memory"
    )
    assert seed["prompt_scaffold_origin"]["source"] == (
        "formalizer_pseudo_formal_packet_component_gate_failure_memory"
    )
    assert seed["blocks"][0]["source_anchors"][0]["id"] == (
        "proof_body:component_gate_rank_threshold"
    )
    assert seed["blocks"][0]["semantic_primitive_requirements"] == [
        "component_gate_C_n"
    ]
    assert payload["pseudo_formalization_component_gate_failure_repair_seed"][
        "packet_id"
    ] == "pseudo_formal_packet:component_gate_repair"
    assert copy_packet["packet_id"] == "pseudo_formal_packet:component_gate_repair"
    assert any(
        row["target_lane"] == PSEUDO_FORMAL_TARGET_LANE_EXACT_SEMANTIC_DEFINITION
        and row["source_anchors"][0]["id"]
        == "proof_body:component_gate_rank_threshold"
        and row["semantic_primitive_requirements"] == ["component_gate_C_n"]
        for row in rows
    )

    repair_context = _formalizer_repair_context(
        errors=[
            "pseudo_formal_proof_packets[0] invalid: blocks[0] missing conclusion",
            (
                "pseudo_formalization_required: valid PF/BV packet did not "
                "produce any effective lane-routable pseudo-formal work-order rows"
            ),
        ],
        question=question,
        theory_packet=_pseudo_formal_packet_eval_theory_packet(),
        environment_feedback={},
        proof_bank_runtime_memory_summary=proof_memory_summary,
    )
    blueprint = repair_context["pseudo_formal_required_repair_blueprint"]
    assert blueprint["component_gate_failure_repair_seed"]["packet_id"] == (
        "pseudo_formal_packet:component_gate_repair"
    )
    assert blueprint["copy_ready_response_fragment"]["pseudo_formal_proof_packets"][
        0
    ]["blocks"][0]["source_anchors"][0]["id"] == (
        "proof_body:component_gate_rank_threshold"
    )


def test_formalizer_prompt_string_false_does_not_require_pf_bv() -> None:
    question = _pseudo_formal_packet_eval_question()
    prompt = build_formalizer_prompt(
        question=question,
        theory_packet=_pseudo_formal_packet_eval_theory_packet(),
        simulation_manifest={
            "manifest_id": "simulation:false_pf",
            "proof_evidence_status": "SIMULATION_NOT_PROOF_EVIDENCE",
        },
        algorithm_manifest={"manifest_id": "algorithm:false_pf"},
        registered_problem={"question_id": question.id},
        theorem_goals=[],
        proof_bank_obligation_catalog=[],
        proof_bank_runtime_memory_summary={
            "pseudo_formalization_required": "false",
            "requires_pseudo_formalization": "false",
            "source_theorem_exact_semantic_definition_structural_reformulation_required": (
                "false"
            ),
            "formalizer_pseudo_formal_packet_component_gate_failure_available": (
                "false"
            ),
        },
        environment_feedback={"requires_pf_bv": "false"},
    )
    payload = _prompt_payload(prompt)

    assert payload["pseudo_formalization_required_packet_seed"] == {}
    assert payload["pseudo_formalization_component_gate_failure_repair_seed"] == {}
    assert payload["pseudo_formalization_required_copy_fragment"] == {}
    assert not isinstance(
        payload["required_output_contract"]["pseudo_formal_proof_packets"],
        dict,
    )
    assert "you must emit at least one pseudo_formal_proof_packets" not in prompt


def test_formalizer_pseudo_formal_packet_eval_static_fixture_routes_rows(
    tmp_path: Path,
) -> None:
    response_file = tmp_path / "formalizer_response.json"
    _write_static_formalizer_response(response_file)

    manifest = run_formalizer_pseudo_formal_packet_eval(
        out_dir=tmp_path / "out",
        provider_name="static",
        static_response_file=response_file,
    )

    assert manifest["artifact_kind"] == "FormalizerPseudoFormalPacketEvalManifest"
    assert manifest["result_status"] == "OK"
    assert manifest["live_generator"] is False
    assert manifest["static_or_fixture_only"] is True
    assert manifest["capability_evidence_ok"] is False
    assert manifest["fixture_plumbing_ok"] is True
    assert manifest["capability_evidence_requirements"]["live_generator"] is False
    assert all(manifest["fixture_plumbing_requirements"].values())
    assert manifest["n_pseudo_formal_packets"] == 1
    assert manifest["n_pseudo_formal_routable_work_order_rows"] >= 3
    assert manifest["n_pseudo_formal_exact_semantic_definition_rows"] == 1
    assert (
        manifest[
            "n_pseudo_formal_exact_semantic_definition_rows_with_source_anchors"
        ]
        == 1
    )
    assert (
        manifest[
            "n_pseudo_formal_exact_semantic_definition_rows_with_semantic_requirements"
        ]
        == 1
    )
    assert manifest["n_pseudo_formal_exact_semantic_definition_rows_with_lineage"] == 1
    assert manifest["exact_semantic_definition_lane_present"] is True
    assert manifest["exact_semantic_definition_rows_source_anchored"] is True
    assert (
        manifest["exact_semantic_definition_rows_semantic_requirements_present"]
        is True
    )
    assert manifest["exact_semantic_definition_rows_lineage_complete"] is True
    assert (
        manifest["fixture_plumbing_requirements"][
            "exact_semantic_definition_lane_present"
        ]
        is True
    )
    assert (
        manifest["fixture_plumbing_requirements"][
            "exact_semantic_definition_rows_source_anchored"
        ]
        is True
    )
    assert (
        manifest["fixture_plumbing_requirements"][
            "exact_semantic_definition_rows_semantic_requirements_present"
        ]
        is True
    )
    assert (
        manifest["fixture_plumbing_requirements"][
            "exact_semantic_definition_rows_lineage_complete"
        ]
        is True
    )
    assert "source_theorem_exact_semantic_definition" in (
        manifest["pseudo_formal_routable_target_lanes"]
    )
    assert "source_to_bridge" in manifest["pseudo_formal_routable_target_lanes"]
    assert "pseudo_formal_exact_semantic_definition_request" in (
        manifest["pseudo_formal_routable_row_kinds"]
    )
    assert "pseudo_formal_independent_block_verification_request" in (
        manifest["pseudo_formal_routable_row_kinds"]
    )
    assert manifest["raw_model_output_written"] is False
    assert manifest["proof_evidence_status"] == (
        FORMALIZER_PSEUDO_FORMAL_PACKET_EVAL_NOT_PROOF_EVIDENCE
    )
    assert manifest["source_theorem_kernel_verified"] is False
    assert manifest["full_frontier_theorem_proved"] is False
    assert "not theorem proof evidence" in manifest["boundary"]
    assert Path(manifest["artifacts"]["manifest_json"]).exists()
    assert Path(manifest["artifacts"]["result_json"]).exists()
    assert Path(manifest["artifacts"]["work_order_rows_jsonl"]).exists()
    assert Path(manifest["artifacts"]["routable_work_order_rows_jsonl"]).exists()
    assert Path(
        manifest["artifacts"]["exact_semantic_definition_rows_jsonl"]
    ).exists()
    exact_rows = [
        json.loads(line)
        for line in Path(
            manifest["artifacts"]["exact_semantic_definition_rows_jsonl"]
        ).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(exact_rows) == 1
    assert exact_rows[0]["target_lane"] == (
        PSEUDO_FORMAL_TARGET_LANE_EXACT_SEMANTIC_DEFINITION
    )
    assert exact_rows[0]["semantic_primitive_requirements"] == [
        "coverage_event"
    ]
    assert exact_rows[0]["source_anchors"][0]["id"] == (
        "proof_body:rank_threshold_step"
    )
    diagnostic_rows = [
        json.loads(line)
        for line in Path(
            manifest["artifacts"]["diagnostic_work_order_rows_jsonl"]
        ).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert any(
        row["row_kind"] == "pseudo_formal_block_verification_pending"
        for row in diagnostic_rows
    )
    public_manifest = json.loads(
        Path(manifest["artifacts"]["manifest_json"]).read_text(encoding="utf-8")
    )
    assert "_artifact_rows" not in public_manifest
    result = json.loads(
        Path(manifest["artifacts"]["result_json"]).read_text(encoding="utf-8")
    )
    assert result["artifacts"]["exact_semantic_definition_rows_jsonl"] == (
        manifest["artifacts"]["exact_semantic_definition_rows_jsonl"]
    )


def test_formalizer_pseudo_formal_packet_eval_rejects_missing_exact_lane(
    tmp_path: Path,
) -> None:
    response_file = tmp_path / "formalizer_response.json"
    _write_static_formalizer_response(response_file)
    response = json.loads(response_file.read_text(encoding="utf-8"))
    response["pseudo_formal_proof_packets"][0]["blocks"][0][
        "lean_feasibility"
    ] = "unknown"
    response_file.write_text(json.dumps(response), encoding="utf-8")

    with pytest.raises(PacketValidationError) as exc_info:
        run_formalizer_pseudo_formal_packet_eval(
            out_dir=tmp_path / "out",
            provider_name="static",
            static_response_file=response_file,
        )

    assert any(
        "required source_theorem_exact_semantic_definition routing" in error
        for error in exc_info.value.errors
    )


def test_formalizer_pseudo_formal_packet_eval_rejects_inactionable_exact_rows(
    tmp_path: Path,
) -> None:
    response_file = tmp_path / "formalizer_response.json"
    _write_static_formalizer_response(response_file)
    response = json.loads(response_file.read_text(encoding="utf-8"))
    response["pseudo_formal_proof_packets"][0]["blocks"][0][
        "semantic_primitive_requirements"
    ] = []
    response_file.write_text(json.dumps(response), encoding="utf-8")

    with pytest.raises(PacketValidationError) as exc_info:
        run_formalizer_pseudo_formal_packet_eval(
            out_dir=tmp_path / "out",
            provider_name="static",
            static_response_file=response_file,
        )

    assert any(
        "required source_theorem_exact_semantic_definition routing was not materialized"
        in error
        and "non-empty semantic_primitive_requirements" in error
        for error in exc_info.value.errors
    )
    assert any(
        "semantic_primitive_requirements" in error
        for error in exc_info.value.errors
    )


def test_formalizer_pseudo_formal_packet_eval_failure_manifest_exports_repair_seed(
    tmp_path: Path,
) -> None:
    exc = PacketValidationError(
        validation_label="LLM Formalizer/ProofEngineer packet",
        attempts=2,
        errors=[
            (
                "pseudo_formal_proof_packets[0] invalid: blocks[0] missing "
                "conclusion; blocks[0] missing source_anchors"
            ),
            (
                "pseudo_formalization_required: valid PF/BV packet did not "
                "produce any effective lane-routable pseudo-formal work-order rows"
            ),
        ],
        history=[
            {
                "attempt_index": 0,
                "ok": False,
                "errors": ["blocks[0] missing conclusion"],
            }
        ],
    )

    manifest = write_formalizer_pseudo_formal_packet_eval_failure_manifest(
        out_dir=tmp_path / "out",
        provider_name="anthropic",
        model="claude-sonnet",
        exc=exc,
    )

    issue_summary = manifest["pseudo_formal_failure_validation_issue_summary"]
    concrete_seed = manifest[
        "pseudo_formal_failure_concrete_lane_routable_repair_seed"
    ]
    concrete_block = concrete_seed["blocks"][0]
    rows = pseudo_formal_routable_work_order_rows(
        pseudo_formal_block_work_order_rows(concrete_seed)
    )

    assert issue_summary["n_missing_conclusion"] == 1
    assert issue_summary["n_missing_source_anchors"] == 1
    assert issue_summary["n_no_lane_routable_work_order_rows"] == 1
    assert manifest["pseudo_formal_failure_required_target_lanes"] == [
        "source_theorem_exact_semantic_definition",
        "source_to_bridge",
    ]
    assert concrete_block["conclusion"]
    assert concrete_block["source_anchors"][0]["id"] == (
        "proof_body:rank_threshold_step"
    )
    assert concrete_block["semantic_primitive_requirements"]
    assert concrete_block["lean_feasibility"] == "needs_semantic_definition"
    assert any(
        row["target_lane"] == PSEUDO_FORMAL_TARGET_LANE_EXACT_SEMANTIC_DEFINITION
        and row["source_anchors"][0]["id"] == "proof_body:rank_threshold_step"
        and row["semantic_primitive_requirements"]
        for row in rows
    )
    result = json.loads(
        Path(manifest["artifacts"]["result_json"]).read_text(encoding="utf-8")
    )
    assert result["pseudo_formal_failure_concrete_lane_routable_repair_seed"][
        "blocks"
    ][0]["source_anchors"][0]["id"] == "proof_body:rank_threshold_step"


def test_formalizer_pseudo_formal_packet_eval_cli_fixture_gate(
    tmp_path: Path,
) -> None:
    response_file = tmp_path / "formalizer_response.json"
    _write_static_formalizer_response(response_file)

    base_args = [
        "formalizer-pseudo-formal-packet-eval",
        "--provider",
        "static",
        "--static-response-file",
        str(response_file),
        "--env-file",
        str(tmp_path / "missing.env"),
    ]

    assert main([*base_args, "--out", str(tmp_path / "strict")]) == 1
    assert (
        main(
            [
                *base_args,
                "--out",
                str(tmp_path / "fixture_ok"),
                "--allow-fixture-success",
            ]
        )
        == 0
    )
