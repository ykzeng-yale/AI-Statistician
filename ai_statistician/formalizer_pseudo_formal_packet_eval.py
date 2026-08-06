from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from .formalizer_llm import (
    FormalizerConfig,
    LLMFormalizerProofEngineerAgent,
    _validate_required_pseudo_formalization_packet,
    validate_formalizer_packet,
)
from .llm_json_repair import PacketValidationError
from .formalizer_repair_policy import formalizer_validation_feedback_envelope
from .pseudo_formal_block_verifier_worker import (
    pseudo_formal_block_verifier_request_rows,
)
from .model_backend import (
    AnthropicGeneratorBackend,
    LIVE_EVALUATION_CLAUDE_MODEL_TIER,
    OpenAIResponsesGeneratorBackend,
    StaticJSONGeneratorBackend,
    generator_backend_provider_name,
    is_live_generator_backend,
    resolve_live_evaluation_model,
)
from .pseudo_formalization import (
    PSEUDO_FORMAL_FAITHFULNESS_REVIEW_ROW_KIND,
    PSEUDO_FORMALIZATION_NOT_PROOF_EVIDENCE,
    PSEUDO_FORMAL_NON_ROUTABLE_WORK_ORDER_ROW_KINDS,
    PSEUDO_FORMAL_TARGET_LANE_EXACT_SEMANTIC_DEFINITION,
    PSEUDO_FORMAL_TARGET_LANE_SOURCE_TO_BRIDGE,
    pseudo_formal_block_work_order_rows,
    pseudo_formal_routable_work_order_rows,
    pseudo_formal_work_order_row_has_required_lineage,
    pseudo_formal_work_order_row_has_reviewable_source_anchor,
    pseudo_formal_work_order_row_has_semantic_requirements,
    pseudo_formal_work_order_row_has_source_anchor,
    validate_pseudo_formal_packet,
)
from .research_schema import OpenResearchQuestion


FORMALIZER_PSEUDO_FORMAL_PACKET_EVAL_NOT_PROOF_EVIDENCE = (
    "FORMALIZER_PSEUDO_FORMAL_PACKET_EVAL_NOT_PROOF_EVIDENCE"
)


def run_formalizer_pseudo_formal_packet_eval(
    *,
    out_dir: Path,
    provider_name: str = "anthropic",
    model: str = "",
    static_response_file: Path | None = None,
    llm_timeout_seconds: float | None = None,
    max_tokens: int = 5000,
    temperature: float = 0.1,
    max_repair_attempts: int = 1,
) -> dict[str, Any]:
    """Run a narrow Formalizer PF/BV packet emission and routing eval.

    The eval asks the generator-backed Formalizer to satisfy a required
    pseudo-formalization feedback contract. Passing means the worker emitted
    schema-valid PF/BV packets with effective lane-routable work rows. This is
    capability evidence for Formalizer routing only, not theorem proof evidence.
    """

    out_dir.mkdir(parents=True, exist_ok=True)
    provider_name = provider_name.strip().lower()
    provider = _formalizer_pseudo_formal_packet_eval_provider(
        provider_name=provider_name,
        static_response_file=static_response_file,
        llm_timeout_seconds=llm_timeout_seconds,
    )
    backend_provider_name = generator_backend_provider_name(provider, provider_name)
    resolved_model = resolve_live_evaluation_model(
        provider_name,
        model,
    )
    question = _pseudo_formal_packet_eval_question()
    theory_packet = _pseudo_formal_packet_eval_theory_packet()
    feedback = _pseudo_formal_packet_eval_feedback()
    formalizer = LLMFormalizerProofEngineerAgent(
        provider=provider,
        config=FormalizerConfig(
            provider_name=provider_name,
            model=resolved_model,
            model_tier=LIVE_EVALUATION_CLAUDE_MODEL_TIER,
            max_tokens=max_tokens,
            temperature=temperature,
            max_repair_attempts=max_repair_attempts,
        ),
    )
    packet = formalizer.propose(
        question=question,
        theory_packet=theory_packet,
        simulation_manifest={
            "manifest_id": "simulation:formalizer_pseudo_formal_packet_eval",
            "simulation_passed": True,
            "proof_evidence_status": "SIMULATION_NOT_PROOF_EVIDENCE",
        },
        algorithm_manifest={
            "manifest_id": "algorithm:formalizer_pseudo_formal_packet_eval",
            "n_executed": 1,
            "promotion_ready": False,
        },
        registered_problem={
            "question_id": question.id,
            "problem_class": "formalizer_pseudo_formal_packet_eval",
            "dgp": "Synthetic no-data component eval for PF/BV packet routing.",
            "estimand": "No statistical estimand; this eval targets PF/BV routing.",
            "assumptions": ["source proof body has a blocked semantic step"],
            "asymptotic_regime": "not applicable",
        },
        theorem_goals=[],
        proof_bank_obligation_catalog=[],
        proof_bank_runtime_memory_summary={},
        environment_feedback=feedback,
    )
    manifest = _formalizer_pseudo_formal_packet_eval_manifest(
        out_dir=out_dir,
        question=question,
        packet=packet,
        provider_name=provider_name,
        backend_provider_name=backend_provider_name,
        model=resolved_model,
        feedback=feedback,
    )
    manifest = _write_formalizer_pseudo_formal_packet_eval_artifacts(
        manifest=manifest,
        out_dir=out_dir,
    )
    return manifest


def write_formalizer_pseudo_formal_packet_eval_failure_manifest(
    *,
    out_dir: Path,
    provider_name: str,
    model: str,
    exc: Exception,
) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    backend_provider_name = provider_name
    live_generator = is_live_generator_backend(provider_name, backend_provider_name)
    manifest_path = out_dir / "formalizer_pseudo_formal_packet_eval_manifest.json"
    result_path = out_dir / "formalizer_pseudo_formal_packet_eval_result.json"
    errors = (
        list(exc.errors)
        if isinstance(exc, PacketValidationError)
        else [f"{type(exc).__name__}: {exc}"]
    )
    history = list(exc.history) if isinstance(exc, PacketValidationError) else []
    invalid_packet = (
        dict(exc.last_invalid_packet)
        if isinstance(exc, PacketValidationError)
        and isinstance(exc.last_invalid_packet, Mapping)
        else {}
    )
    validation_feedback = formalizer_validation_feedback_envelope(
        errors,
        validation_label=(
            exc.validation_label
            if isinstance(exc, PacketValidationError)
            else "Formalizer PF/BV component eval"
        ),
        invalid_packet=invalid_packet,
        attempt_history=history,
    )
    required_target_lanes = list(
        _pseudo_formal_packet_eval_feedback().get(
            "pseudo_formal_block_routing_target_lanes",
            [],
        )
    )
    manifest: dict[str, Any] = {
        "schema_version": 1,
        "artifact_kind": "FormalizerPseudoFormalPacketEvalManifest",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "provider_name": provider_name,
        "backend_provider_name": backend_provider_name,
        "model": model,
        "live_generator": live_generator,
        "static_or_fixture_only": not live_generator,
        "component_eval": "Formalizer/ProofEngineer PF/BV packet emission",
        "result_status": "FAILED",
        "failure_type": type(exc).__name__,
        "errors": errors,
        "llm_json_repair_history": history,
        "formalizer_validation_feedback": validation_feedback,
        "pseudo_formal_failure_required_target_lanes": required_target_lanes,
        "model_owned_repair_required": True,
        "runtime_selected_mathematical_content": False,
        "capability_evidence_ok": False,
        "fixture_plumbing_ok": False,
        "nonproof_boundary_preserved": True,
        "raw_model_output_written": False,
        "source_theorem_kernel_verified": False,
        "full_frontier_theorem_proved": False,
        "proof_evidence_status": (
            FORMALIZER_PSEUDO_FORMAL_PACKET_EVAL_NOT_PROOF_EVIDENCE
        ),
        "boundary": _formalizer_pseudo_formal_packet_eval_boundary(),
        "artifacts": {
            "manifest_json": str(manifest_path),
            "result_json": str(result_path),
        },
    }
    result_path.write_text(
        json.dumps(
            {
                "result_status": "FAILED",
                "errors": errors,
                "llm_json_repair_history": history,
                "formalizer_validation_feedback": validation_feedback,
                "pseudo_formal_failure_required_target_lanes": (
                    required_target_lanes
                ),
                "model_owned_repair_required": True,
                "runtime_selected_mathematical_content": False,
                "nonproof_boundary_preserved": (
                    manifest["nonproof_boundary_preserved"]
                ),
                "raw_model_output_written": manifest["raw_model_output_written"],
                "source_theorem_kernel_verified": (
                    manifest["source_theorem_kernel_verified"]
                ),
                "full_frontier_theorem_proved": (
                    manifest["full_frontier_theorem_proved"]
                ),
                "proof_evidence_status": manifest["proof_evidence_status"],
            },
            indent=2,
            sort_keys=True,
            default=str,
        ),
        encoding="utf-8",
    )
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True, default=str),
        encoding="utf-8",
    )
    return manifest


def _formalizer_pseudo_formal_packet_eval_provider(
    *,
    provider_name: str,
    static_response_file: Path | None,
    llm_timeout_seconds: float | None,
):
    if provider_name == "anthropic":
        return AnthropicGeneratorBackend(timeout_s=llm_timeout_seconds)
    if provider_name == "openai":
        return OpenAIResponsesGeneratorBackend(timeout_s=llm_timeout_seconds)
    if provider_name == "static":
        if static_response_file is None:
            raise ValueError("static provider requires --static-response-file")
        return StaticJSONGeneratorBackend(
            static_response_file.read_text(encoding="utf-8")
        )
    raise ValueError(
        "unsupported Formalizer PF/BV eval provider: "
        f"{provider_name!r}; expected anthropic, openai, or static"
    )


def _pseudo_formal_packet_eval_question() -> OpenResearchQuestion:
    return OpenResearchQuestion(
        id="formalizer_pseudo_formal_packet_probe",
        title="Formalizer PF/BV packet probe",
        description=(
            "Component capability eval for required pseudo-formal block "
            "decomposition and lane-routable residual work-order emission."
        ),
        tags=("formalizer", "pseudo_formal", "capability-eval"),
    )


def _pseudo_formal_packet_eval_theory_packet() -> dict[str, Any]:
    return {
        "packet_id": "theory:formalizer_pseudo_formal_packet_eval",
        "theorem_cards": [
            {
                "id": "theorem:coverage",
                "claim": (
                    "finite-sample coverage follows from a source "
                    "rank-threshold semantic step"
                ),
            }
        ],
        "theory_derivation_trace": {
            "trace_id": "trace:formalizer_pseudo_formal_packet_eval",
            "derivation_steps": [
                {
                    "step_id": "rank_threshold_step",
                    "claim": (
                        "exchangeability gives a rank-threshold coverage event"
                    ),
                    "anchor_id": "proof_body:rank_threshold_step",
                }
            ],
        },
    }


def _pseudo_formal_packet_eval_feedback() -> dict[str, Any]:
    return {
        "pseudo_formalization_required": True,
        "pseudo_formalization_required_reason": (
            "component eval for blocked proof-body/PF activation"
        ),
        "pseudo_formal_block_routing_target_lanes": [
            PSEUDO_FORMAL_TARGET_LANE_EXACT_SEMANTIC_DEFINITION,
            PSEUDO_FORMAL_TARGET_LANE_SOURCE_TO_BRIDGE,
        ],
        "source_theorem_proof_body_adapter_feedback": {
            "diagnostics": [
                {
                    "failure_classification": (
                        "source_theorem_semantic_alignment_unreviewed"
                    ),
                    "message": (
                        "source theorem proof-body repair is blocked until the "
                        "rank-threshold semantic step is decomposed into "
                        "source-anchored PF/BV blocks"
                    ),
                }
            ]
        },
    }


def _formalizer_pseudo_formal_packet_eval_manifest(
    *,
    out_dir: Path,
    question: OpenResearchQuestion,
    packet: Mapping[str, Any],
    provider_name: str,
    backend_provider_name: str,
    model: str,
    feedback: Mapping[str, Any],
) -> dict[str, Any]:
    formalizer_errors = validate_formalizer_packet(packet)
    required_errors = _validate_required_pseudo_formalization_packet(
        packet,
        environment_feedback=feedback,
        proof_bank_runtime_memory_summary={},
    )
    pf_packets = [
        row for row in packet.get("pseudo_formal_proof_packets", []) or []
        if isinstance(row, Mapping)
    ]
    pf_error_rows: list[dict[str, Any]] = []
    work_order_rows: list[dict[str, Any]] = []
    for index, pf_packet in enumerate(pf_packets):
        errors = validate_pseudo_formal_packet(pf_packet)
        if errors:
            pf_error_rows.append({"index": index, "errors": errors})
        work_order_rows.extend(pseudo_formal_block_work_order_rows(pf_packet))
    for row in work_order_rows:
        row["question_id"] = question.id
        row["question_title"] = question.title
    routable_rows = pseudo_formal_routable_work_order_rows(work_order_rows)
    diagnostic_rows = [
        dict(row)
        for row in work_order_rows
        if str(row.get("row_kind", "") or "")
        in PSEUDO_FORMAL_NON_ROUTABLE_WORK_ORDER_ROW_KINDS
    ]
    live_generator = is_live_generator_backend(provider_name, backend_provider_name)
    valid_packet = not formalizer_errors and not required_errors and not pf_error_rows
    routable_rows_present = bool(routable_rows)
    packet_present = bool(pf_packets)
    routable_target_lanes = sorted(
        {str(row.get("target_lane", "") or "") for row in routable_rows}
    )
    exact_semantic_definition_lane_present = (
        PSEUDO_FORMAL_TARGET_LANE_EXACT_SEMANTIC_DEFINITION in routable_target_lanes
    )
    exact_semantic_rows = [
        row
        for row in routable_rows
        if str(row.get("target_lane", "") or "")
        == PSEUDO_FORMAL_TARGET_LANE_EXACT_SEMANTIC_DEFINITION
    ]
    exact_semantic_rows_with_source_anchors = [
        row
        for row in exact_semantic_rows
        if pseudo_formal_work_order_row_has_source_anchor(row)
    ]
    exact_semantic_rows_with_semantic_requirements = [
        row
        for row in exact_semantic_rows
        if pseudo_formal_work_order_row_has_semantic_requirements(row)
    ]
    exact_semantic_rows_with_lineage = [
        row
        for row in exact_semantic_rows
        if pseudo_formal_work_order_row_has_required_lineage(row)
    ]
    exact_semantic_rows_source_anchored = bool(exact_semantic_rows) and len(
        exact_semantic_rows_with_source_anchors
    ) == len(exact_semantic_rows)
    exact_semantic_rows_semantic_requirements_present = bool(
        exact_semantic_rows
    ) and len(exact_semantic_rows_with_semantic_requirements) == len(
        exact_semantic_rows
    )
    exact_semantic_rows_lineage_complete = bool(exact_semantic_rows) and len(
        exact_semantic_rows_with_lineage
    ) == len(exact_semantic_rows)
    required_target_lanes = {
        str(value)
        for value in feedback.get("pseudo_formal_block_routing_target_lanes", [])
        or []
        if str(value).strip()
    }
    required_lane_blocked_source_ids = {
        str(row.get("source_block_id", "") or "")
        for row in work_order_rows
        if str(row.get("blocked_target_lane", "") or "")
        in required_target_lanes
    }
    independent_review_rows = pseudo_formal_block_verifier_request_rows(
        work_order_rows
    )
    faithfulness_review_handoff_rows = [
        row
        for row in independent_review_rows
        if str(row.get("row_kind", "") or "")
        == PSEUDO_FORMAL_FAITHFULNESS_REVIEW_ROW_KIND
        and str(row.get("source_block_id", "") or "")
        in required_lane_blocked_source_ids
    ]
    faithfulness_review_handoff_source_anchored = bool(
        faithfulness_review_handoff_rows
    ) and all(
        pseudo_formal_work_order_row_has_reviewable_source_anchor(row)
        for row in faithfulness_review_handoff_rows
    )
    faithfulness_review_handoff_lineage_complete = bool(
        faithfulness_review_handoff_rows
    ) and all(
        pseudo_formal_work_order_row_has_required_lineage(row)
        for row in faithfulness_review_handoff_rows
    )
    faithfulness_review_handoff_ready = bool(
        faithfulness_review_handoff_rows
        and faithfulness_review_handoff_source_anchored
        and faithfulness_review_handoff_lineage_complete
    )
    exact_semantic_definition_rows_ready = bool(
        exact_semantic_definition_lane_present
        and exact_semantic_rows_source_anchored
        and exact_semantic_rows_semantic_requirements_present
        and exact_semantic_rows_lineage_complete
    )
    required_lane_progress_ready = bool(
        exact_semantic_definition_rows_ready
        or faithfulness_review_handoff_ready
    )
    nonproof_boundary = (
        packet.get("kernel_verified") is False
        and packet.get("full_frontier_theorem_proved") is False
        and all(
            pf_packet.get("proof_evidence_status")
            == PSEUDO_FORMALIZATION_NOT_PROOF_EVIDENCE
            and pf_packet.get("kernel_verified") is False
            and pf_packet.get("source_theorem_kernel_verified") is False
            for pf_packet in pf_packets
        )
    )
    capability_requirements = {
        "live_generator": live_generator,
        "formalizer_packet_valid": bool(valid_packet),
        "pseudo_formal_packets_present": packet_present,
        "routable_work_order_rows_present": routable_rows_present,
        "required_lane_progress_ready": required_lane_progress_ready,
        "exact_semantic_definition_rows_ready_when_materialized": bool(
            not exact_semantic_definition_lane_present
            or exact_semantic_definition_rows_ready
        ),
        "faithfulness_review_handoff_ready_when_required": bool(
            not faithfulness_review_handoff_rows
            or faithfulness_review_handoff_ready
        ),
        "nonproof_boundary_preserved": bool(nonproof_boundary),
    }
    fixture_requirements = {
        key: value
        for key, value in capability_requirements.items()
        if key != "live_generator"
    }
    manifest_path = out_dir / "formalizer_pseudo_formal_packet_eval_manifest.json"
    result_path = out_dir / "formalizer_pseudo_formal_packet_eval_result.json"
    work_order_rows_path = out_dir / "pseudo_formal_work_order_rows.jsonl"
    routable_rows_path = out_dir / "pseudo_formal_routable_work_order_rows.jsonl"
    exact_rows_path = out_dir / "pseudo_formal_exact_semantic_definition_rows.jsonl"
    review_rows_path = out_dir / "pseudo_formal_faithfulness_review_handoff_rows.jsonl"
    diagnostic_rows_path = out_dir / "pseudo_formal_diagnostic_work_order_rows.jsonl"
    return {
        "schema_version": 1,
        "artifact_kind": "FormalizerPseudoFormalPacketEvalManifest",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "question_id": question.id,
        "question_title": question.title,
        "provider_name": provider_name,
        "backend_provider_name": backend_provider_name,
        "model": model,
        "model_tier": LIVE_EVALUATION_CLAUDE_MODEL_TIER,
        "live_generator": live_generator,
        "static_or_fixture_only": not live_generator,
        "component_eval": "Formalizer/ProofEngineer PF/BV packet emission",
        "result_status": "OK" if valid_packet else "FAILED_VALIDATION",
        "completion_mode": (
            "required_target_lane_materialized"
            if exact_semantic_definition_rows_ready
            else "independent_faithfulness_review_handoff"
            if faithfulness_review_handoff_ready
            else "required_lane_progress_missing"
        ),
        "n_pseudo_formal_packets": len(pf_packets),
        "n_pseudo_formal_packet_validation_error_sets": len(pf_error_rows),
        "n_pseudo_formal_work_order_rows": len(work_order_rows),
        "n_pseudo_formal_routable_work_order_rows": len(routable_rows),
        "n_pseudo_formal_diagnostic_work_order_rows": len(diagnostic_rows),
        "exact_semantic_definition_lane_present": exact_semantic_definition_lane_present,
        "n_pseudo_formal_exact_semantic_definition_rows": len(exact_semantic_rows),
        "n_pseudo_formal_exact_semantic_definition_rows_with_source_anchors": len(
            exact_semantic_rows_with_source_anchors
        ),
        "n_pseudo_formal_exact_semantic_definition_rows_with_semantic_requirements": len(
            exact_semantic_rows_with_semantic_requirements
        ),
        "n_pseudo_formal_exact_semantic_definition_rows_with_lineage": len(
            exact_semantic_rows_with_lineage
        ),
        "exact_semantic_definition_rows_source_anchored": exact_semantic_rows_source_anchored,
        "exact_semantic_definition_rows_semantic_requirements_present": (
            exact_semantic_rows_semantic_requirements_present
        ),
        "exact_semantic_definition_rows_lineage_complete": (
            exact_semantic_rows_lineage_complete
        ),
        "n_pseudo_formal_faithfulness_review_handoff_rows": len(
            faithfulness_review_handoff_rows
        ),
        "faithfulness_review_handoff_source_anchored": (
            faithfulness_review_handoff_source_anchored
        ),
        "faithfulness_review_handoff_lineage_complete": (
            faithfulness_review_handoff_lineage_complete
        ),
        "faithfulness_review_handoff_ready": faithfulness_review_handoff_ready,
        "pseudo_formal_routable_row_kinds": sorted(
            {str(row.get("row_kind", "") or "") for row in routable_rows}
        ),
        "pseudo_formal_routable_target_lanes": sorted(
            routable_target_lanes
        ),
        "pseudo_formal_diagnostic_row_kinds": sorted(
            {str(row.get("row_kind", "") or "") for row in diagnostic_rows}
        ),
        "formalizer_validation_errors": formalizer_errors,
        "required_pseudo_formalization_errors": required_errors,
        "pseudo_formal_packet_validation_errors": pf_error_rows,
        "llm_json_repair_attempts": packet.get("llm_json_repair_attempts"),
        "llm_json_repair_history": packet.get("llm_json_repair_history", []),
        "raw_model_output_written": False,
        "capability_evidence_ok": bool(all(capability_requirements.values())),
        "fixture_plumbing_ok": bool(all(fixture_requirements.values())),
        "capability_evidence_requirements": capability_requirements,
        "fixture_plumbing_requirements": fixture_requirements,
        "source_theorem_kernel_verified": False,
        "full_frontier_theorem_proved": False,
        "proof_evidence_status": (
            FORMALIZER_PSEUDO_FORMAL_PACKET_EVAL_NOT_PROOF_EVIDENCE
        ),
        "boundary": _formalizer_pseudo_formal_packet_eval_boundary(),
        "artifacts": {
            "manifest_json": str(manifest_path),
            "result_json": str(result_path),
            "work_order_rows_jsonl": str(work_order_rows_path),
            "routable_work_order_rows_jsonl": str(routable_rows_path),
            "exact_semantic_definition_rows_jsonl": str(exact_rows_path),
            "faithfulness_review_handoff_rows_jsonl": str(review_rows_path),
            "diagnostic_work_order_rows_jsonl": str(diagnostic_rows_path),
        },
        "_artifact_rows": {
            "work_order_rows": work_order_rows,
            "routable_work_order_rows": routable_rows,
            "exact_semantic_definition_rows": exact_semantic_rows,
            "faithfulness_review_handoff_rows": faithfulness_review_handoff_rows,
            "diagnostic_work_order_rows": diagnostic_rows,
        },
    }


def _write_formalizer_pseudo_formal_packet_eval_artifacts(
    *,
    manifest: Mapping[str, Any],
    out_dir: Path,
) -> dict[str, Any]:
    manifest_path = out_dir / "formalizer_pseudo_formal_packet_eval_manifest.json"
    result_path = out_dir / "formalizer_pseudo_formal_packet_eval_result.json"
    artifact_rows = (
        dict(manifest.get("_artifact_rows", {}) or {})
        if isinstance(manifest.get("_artifact_rows", {}), Mapping)
        else {}
    )
    public_manifest = {
        key: value for key, value in manifest.items() if key != "_artifact_rows"
    }
    artifacts = (
        dict(public_manifest.get("artifacts", {}) or {})
        if isinstance(public_manifest.get("artifacts", {}), Mapping)
        else {}
    )
    _write_jsonl_rows(
        Path(str(artifacts.get("work_order_rows_jsonl", ""))),
        artifact_rows.get("work_order_rows", []),
    )
    _write_jsonl_rows(
        Path(str(artifacts.get("routable_work_order_rows_jsonl", ""))),
        artifact_rows.get("routable_work_order_rows", []),
    )
    _write_jsonl_rows(
        Path(str(artifacts.get("exact_semantic_definition_rows_jsonl", ""))),
        artifact_rows.get("exact_semantic_definition_rows", []),
    )
    _write_jsonl_rows(
        Path(str(artifacts.get("faithfulness_review_handoff_rows_jsonl", ""))),
        artifact_rows.get("faithfulness_review_handoff_rows", []),
    )
    _write_jsonl_rows(
        Path(str(artifacts.get("diagnostic_work_order_rows_jsonl", ""))),
        artifact_rows.get("diagnostic_work_order_rows", []),
    )
    result = {
        key: public_manifest.get(key)
        for key in (
            "result_status",
            "completion_mode",
            "formalizer_validation_errors",
            "required_pseudo_formalization_errors",
            "pseudo_formal_packet_validation_errors",
            "n_pseudo_formal_packets",
            "n_pseudo_formal_work_order_rows",
            "n_pseudo_formal_routable_work_order_rows",
            "n_pseudo_formal_diagnostic_work_order_rows",
            "n_pseudo_formal_exact_semantic_definition_rows",
            "n_pseudo_formal_exact_semantic_definition_rows_with_source_anchors",
            "n_pseudo_formal_exact_semantic_definition_rows_with_semantic_requirements",
            "n_pseudo_formal_exact_semantic_definition_rows_with_lineage",
            "n_pseudo_formal_faithfulness_review_handoff_rows",
            "faithfulness_review_handoff_ready",
            "pseudo_formal_routable_row_kinds",
            "pseudo_formal_routable_target_lanes",
            "pseudo_formal_diagnostic_row_kinds",
            "llm_json_repair_attempts",
            "llm_json_repair_history",
        )
    }
    result["artifacts"] = {
        key: artifacts.get(key)
        for key in (
            "work_order_rows_jsonl",
            "routable_work_order_rows_jsonl",
            "exact_semantic_definition_rows_jsonl",
            "faithfulness_review_handoff_rows_jsonl",
            "diagnostic_work_order_rows_jsonl",
        )
    }
    result_path.write_text(
        json.dumps(result, indent=2, sort_keys=True, default=str),
        encoding="utf-8",
    )
    manifest_path.write_text(
        json.dumps(public_manifest, indent=2, sort_keys=True, default=str),
        encoding="utf-8",
    )
    return public_manifest


def _write_jsonl_rows(path: Path, rows: Any) -> None:
    if str(path) in {"", "."}:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    safe_rows = [
        dict(row)
        for row in (rows or [])
        if isinstance(row, Mapping)
    ]
    path.write_text(
        "".join(
            json.dumps(row, sort_keys=True, default=str) + "\n"
            for row in safe_rows
        ),
        encoding="utf-8",
    )


def _formalizer_pseudo_formal_packet_eval_boundary() -> str:
    return (
        "This component eval checks whether Formalizer/ProofEngineer can emit "
        "schema-valid pseudo-formal proof packets with effective lane-routable "
        "work-order rows under required PF/BV activation. The packets are "
        "decomposition and routing artifacts only. They are not theorem proof "
        "evidence, not source theorem kernel verification, and not full frontier "
        "theorem closure."
    )
