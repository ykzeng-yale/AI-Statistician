from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from .fingerprint import stable_hash
from .llm_json_repair import (
    PacketValidationError,
    extract_json_object,
    generate_validated_json_packet,
)
from .model_backend import (
    GeneratorBackend,
    GeneratorRequest,
    LIVE_EVALUATION_CLAUDE_MODEL_TIER,
    is_live_generator_backend,
    normalize_generator_provider_name,
    resolve_live_evaluation_model,
    resolve_generator_model,
)
from .pseudo_formalization import (
    PSEUDO_FORMAL_FAITHFULNESS_REVIEW_ROW_KIND,
    PSEUDO_FORMAL_BLOCK_VERIFICATION_REQUEST_ROW_KIND,
    PSEUDO_FORMAL_BLOCK_ROUTING_LEARNING_TASK,
    PSEUDO_FORMAL_BLOCK_ROUTING_METHOD_STAGE,
    PSEUDO_FORMAL_BLOCK_ROUTING_MEMORY_STATUS,
    PSEUDO_FORMAL_BLOCK_ROUTING_QUEUE_NAME,
    PSEUDO_FORMAL_BLOCK_ROUTING_QUEUE_STATUS_BY_TARGET_LANE,
    PSEUDO_FORMAL_BLOCK_ROUTING_TRIGGER,
    PSEUDO_FORMAL_DEFAULT_AGGREGATION_RULE,
    PSEUDO_FORMAL_DEFAULT_CALIBRATION_STRICTNESS,
    PSEUDO_FORMAL_INDEPENDENT_BLOCK_VERIFIER_PROVENANCES,
    PSEUDO_FORMAL_TARGET_LANE_FORMAL_GAP,
    PSEUDO_FORMAL_VERIFICATION_METHOD_CONTRACT_ID,
    PSEUDO_FORMALIZATION_NOT_PROOF_EVIDENCE,
    PSEUDO_FORMALIZATION_PROOF_BOUNDARY,
    pseudo_formal_block_structural_quality,
    pseudo_formal_work_order_row_has_reviewable_source_anchor,
)


PSEUDO_FORMAL_BLOCK_VERIFIER_WORKER_SCHEMA_VERSION = 1
PSEUDO_FORMAL_BLOCK_VERIFIER_PROMPT_PACKET_KIND = (
    "PseudoFormalBlockVerifierPromptPacket"
)
PSEUDO_FORMAL_BLOCK_VERIFIER_RESPONSE_KIND = "PseudoFormalBlockVerifierResponse"
PSEUDO_FORMAL_BLOCK_VERIFIER_FEEDBACK_TRIGGER = (
    "PSEUDO_FORMAL_INDEPENDENT_BLOCK_VERIFICATION_FEEDBACK"
)
PSEUDO_FORMAL_BLOCK_VERIFIER_FEEDBACK_NOT_PROOF_EVIDENCE = (
    "PSEUDO_FORMAL_BLOCK_VERIFIER_FEEDBACK_NOT_PROOF_EVIDENCE"
)
PSEUDO_FORMAL_BLOCK_VERIFIER_COMPONENT_GATE_NOT_PROOF_EVIDENCE = (
    "PSEUDO_FORMAL_BLOCK_VERIFIER_COMPONENT_GATE_NOT_PROOF_EVIDENCE"
)
PSEUDO_FORMAL_FAITHFULNESS_REVIEW_STATUSES = (
    "faithful",
    "unfaithful",
    "needs_review",
)


PSEUDO_FORMAL_BLOCK_VERIFIER_RESPONSE_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": [
        "prompt_packet_id",
        "faithfulness_review",
        "block_verification",
    ],
    "additionalProperties": True,
    "properties": {
        "prompt_packet_id": {"type": "string"},
        "source_pseudo_formal_work_order_id": {"type": "string"},
        "source_block_id": {"type": "string"},
        "faithfulness_review": {
            "type": "object",
            "required": ["status", "reason"],
            "additionalProperties": False,
            "properties": {
                "status": {
                    "enum": list(PSEUDO_FORMAL_FAITHFULNESS_REVIEW_STATUSES)
                },
                "reason": {"type": "string", "minLength": 1},
            },
        },
        "block_verification": {
            "type": "object",
            "required": [
                "verdict",
                "reason",
                "verifier_provenance",
                "independent_verifier",
                "rollout_count",
            ],
            "additionalProperties": True,
            "properties": {
                "verdict": {"enum": ["accepted", "failed"]},
                "reason": {"type": "string"},
                "verifier_provenance": {
                    "enum": list(PSEUDO_FORMAL_INDEPENDENT_BLOCK_VERIFIER_PROVENANCES)
                },
                "independent_verifier": {"type": "boolean"},
                "strictness_threshold": {"type": "string"},
                "aggregation_rule": {"type": "string"},
                "rollout_count": {"type": "integer", "minimum": 1},
            },
        },
        "cited_dependency_statement_ids": {
            "type": "array",
            "items": {"type": "string"},
        },
        "issues": {"type": "array", "items": {"type": "string"}},
        "proof_evidence_status": {"type": "string"},
    },
}


def export_pseudo_formal_block_verifier_prompt_packets(
    runtime_learning_jsonl_paths: Sequence[Path],
    out_dir: Path | None = None,
    *,
    max_packets: int = 20,
) -> dict[str, Any]:
    """Export bounded prompt packets for independent PF block verification."""

    errors: list[str] = []
    source_rows = _read_runtime_learning_rows(runtime_learning_jsonl_paths, errors)
    request_rows = pseudo_formal_block_verifier_request_rows(
        source_rows,
        max_packets=max_packets,
    )
    packets = [_prompt_packet_from_request(row) for row in request_rows]
    by_status = Counter(str(packet.get("packet_status", "")) for packet in packets)
    payload: dict[str, Any] = {
        "schema_version": PSEUDO_FORMAL_BLOCK_VERIFIER_WORKER_SCHEMA_VERSION,
        "artifact_kind": "PseudoFormalBlockVerifierPromptPacketManifest",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_runtime_learning_jsonl_paths": [
            str(path) for path in runtime_learning_jsonl_paths
        ],
        "max_packets": max_packets,
        "n_source_rows": len(source_rows),
        "n_request_rows": len(request_rows),
        "n_prompt_packets": len(packets),
        "n_ok_prompt_packets": sum(1 for packet in packets if packet.get("ok") is True),
        "all_ok": not errors and all(packet.get("ok") is True for packet in packets),
        "errors": errors,
        "by_packet_status": dict(sorted(by_status.items())),
        "packets": packets,
        "proof_evidence_status": PSEUDO_FORMAL_BLOCK_VERIFIER_FEEDBACK_NOT_PROOF_EVIDENCE,
        "proof_evidence_boundary": PSEUDO_FORMALIZATION_PROOF_BOUNDARY,
        "limitations": [
            "prompt packets are verifier tasks, not theorem proof evidence",
            "verifier responses must be validated before entering runtime learning memory",
            "accepted PF/BV feedback remains non-proof until target-prover kernel replay",
        ],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = out_dir / "pseudo_formal_block_verifier_prompt_packets_manifest.json"
        jsonl_path = out_dir / "pseudo_formal_block_verifier_prompt_packets.jsonl"
        report_path = out_dir / "pseudo_formal_block_verifier_prompt_packets.md"
        payload["prompt_packets_jsonl"] = str(jsonl_path)
        payload["manifest_path"] = str(manifest_path)
        manifest_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        jsonl_path.write_text(
            "\n".join(json.dumps(packet, sort_keys=True) for packet in packets)
            + ("\n" if packets else ""),
            encoding="utf-8",
        )
        report_path.write_text(_prompt_packet_markdown(payload), encoding="utf-8")
    return payload


def export_pseudo_formal_block_verifier_response_validation(
    prompt_packets_manifest_path: Path,
    response_jsonl_path: Path,
    out_dir: Path | None = None,
) -> dict[str, Any]:
    """Validate independent PF block-verifier responses into learning rows."""

    errors: list[str] = []
    prompt_payload = _read_json(prompt_packets_manifest_path, errors)
    packets = [
        packet
        for packet in prompt_payload.get("packets", [])
        if isinstance(packet, Mapping)
    ]
    packets_by_id = {str(packet.get("prompt_packet_id", "")): packet for packet in packets}
    responses = _read_jsonl(response_jsonl_path, errors)
    validation_rows = [
        _validate_response_row(response, packets_by_id)
        for response in responses
        if isinstance(response, Mapping)
    ]
    learning_rows = [
        row["runtime_learning_row"]
        for row in validation_rows
        if row.get("ok") is True and isinstance(row.get("runtime_learning_row"), Mapping)
    ]
    by_status = Counter(str(row.get("validation_status", "")) for row in validation_rows)
    payload: dict[str, Any] = {
        "schema_version": PSEUDO_FORMAL_BLOCK_VERIFIER_WORKER_SCHEMA_VERSION,
        "artifact_kind": "PseudoFormalBlockVerifierResponseValidationManifest",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "prompt_packets_manifest_path": str(prompt_packets_manifest_path),
        "response_jsonl_path": str(response_jsonl_path),
        "n_prompt_packets": len(packets),
        "n_responses": len(responses),
        "n_valid_responses": sum(1 for row in validation_rows if row.get("ok") is True),
        "n_runtime_learning_rows": len(learning_rows),
        "all_ok": not errors and bool(responses) and all(
            row.get("ok") is True for row in validation_rows
        ),
        "errors": errors,
        "by_validation_status": dict(sorted(by_status.items())),
        "rows": validation_rows,
        "runtime_learning_rows": learning_rows,
        "proof_evidence_status": PSEUDO_FORMAL_BLOCK_VERIFIER_FEEDBACK_NOT_PROOF_EVIDENCE,
        "proof_evidence_boundary": PSEUDO_FORMALIZATION_PROOF_BOUNDARY,
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = out_dir / "pseudo_formal_block_verifier_response_validation_manifest.json"
        validation_jsonl = out_dir / "pseudo_formal_block_verifier_response_validation.jsonl"
        learning_jsonl = out_dir / "runtime_learning_rows.jsonl"
        report_path = out_dir / "pseudo_formal_block_verifier_response_validation.md"
        payload["manifest_path"] = str(manifest_path)
        payload["response_validation_jsonl"] = str(validation_jsonl)
        payload["runtime_learning_rows_jsonl"] = str(learning_jsonl)
        manifest_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        validation_jsonl.write_text(
            "\n".join(json.dumps(row, sort_keys=True) for row in validation_rows)
            + ("\n" if validation_rows else ""),
            encoding="utf-8",
        )
        learning_jsonl.write_text(
            "\n".join(json.dumps(row, sort_keys=True) for row in learning_rows)
            + ("\n" if learning_rows else ""),
            encoding="utf-8",
        )
        report_path.write_text(_response_validation_markdown(payload), encoding="utf-8")
    return payload


def export_pseudo_formal_block_verifier_llm_responses(
    prompt_packets_manifest_path: Path,
    out_dir: Path | None = None,
    *,
    provider: GeneratorBackend,
    provider_name: str = "anthropic",
    model: str = "",
    model_tier: str = "sonnet",
    max_packets: int = 20,
    max_tokens: int = 2000,
    temperature: float = 0.0,
    max_repair_attempts: int = 1,
) -> dict[str, Any]:
    """Call a generator-only LLM to answer PF BlockVerifier prompt packets."""

    errors: list[str] = []
    prompt_payload = _read_json(prompt_packets_manifest_path, errors)
    prompt_packets = [
        packet
        for packet in prompt_payload.get("packets", [])
        if isinstance(packet, Mapping) and packet.get("ok") is True
    ][: max(0, max_packets)]
    resolved_model = resolve_generator_model(
        provider_name=provider_name,
        requested_model=model,
        model_tier=model_tier,
    )
    responses: list[dict[str, Any]] = []
    response_rows: list[dict[str, Any]] = []
    for packet in prompt_packets:
        row = _llm_response_for_prompt_packet(
            packet,
            provider=provider,
            provider_name=provider_name,
            model=resolved_model,
            model_tier=model_tier,
            max_tokens=max_tokens,
            temperature=temperature,
            max_repair_attempts=max_repair_attempts,
        )
        response_rows.append(row)
        if row.get("ok") is True and isinstance(row.get("response"), Mapping):
            responses.append(dict(row["response"]))
    by_status = Counter(str(row.get("llm_response_status", "")) for row in response_rows)
    payload: dict[str, Any] = {
        "schema_version": PSEUDO_FORMAL_BLOCK_VERIFIER_WORKER_SCHEMA_VERSION,
        "artifact_kind": "PseudoFormalBlockVerifierLlmResponseManifest",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "prompt_packets_manifest_path": str(prompt_packets_manifest_path),
        "provider_name": provider_name,
        "backend_provider_name": str(getattr(provider, "provider_name", "") or ""),
        "model": resolved_model,
        "model_tier": model_tier,
        "max_packets": max_packets,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "max_repair_attempts": max_repair_attempts,
        "n_prompt_packets": len(prompt_packets),
        "n_llm_response_rows": len(response_rows),
        "n_ok_responses": len(responses),
        "all_ok": not errors and len(responses) == len(prompt_packets),
        "errors": errors,
        "by_llm_response_status": dict(sorted(by_status.items())),
        "rows": response_rows,
        "responses": responses,
        "proof_evidence_status": PSEUDO_FORMAL_BLOCK_VERIFIER_FEEDBACK_NOT_PROOF_EVIDENCE,
        "proof_evidence_boundary": PSEUDO_FORMALIZATION_PROOF_BOUNDARY,
        "next_gate": (
            "Run pseudo-formal-block-verifier-response-validation on the response "
            "JSONL before feeding results back into AgentRuntime."
        ),
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = out_dir / "pseudo_formal_block_verifier_llm_response_manifest.json"
        response_rows_jsonl = out_dir / "pseudo_formal_block_verifier_llm_response_rows.jsonl"
        responses_jsonl = out_dir / "pseudo_formal_block_verifier_responses.jsonl"
        report_path = out_dir / "pseudo_formal_block_verifier_llm_responses.md"
        payload["manifest_path"] = str(manifest_path)
        payload["response_rows_jsonl"] = str(response_rows_jsonl)
        payload["responses_jsonl"] = str(responses_jsonl)
        manifest_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        response_rows_jsonl.write_text(
            "\n".join(json.dumps(row, sort_keys=True) for row in response_rows)
            + ("\n" if response_rows else ""),
            encoding="utf-8",
        )
        responses_jsonl.write_text(
            "\n".join(json.dumps(row, sort_keys=True) for row in responses)
            + ("\n" if responses else ""),
            encoding="utf-8",
        )
        report_path.write_text(_llm_response_markdown(payload), encoding="utf-8")
    return payload


def pseudo_formal_block_verifier_request_rows(
    rows: Sequence[Mapping[str, Any]],
    *,
    max_packets: int = 20,
) -> list[dict[str, Any]]:
    """Select pending, structurally bound PF/BV requests for a verifier turn."""

    packet_limit = max(0, int(max_packets))
    if packet_limit == 0:
        return []
    request_rows: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        candidate = _with_verifier_dispatch_identity(row)
        if _is_independent_bv_request_row(candidate):
            request_rows.append(candidate)
        if len(request_rows) >= packet_limit:
            break
    return request_rows


def _pseudo_formal_review_outcome_counts(
    validation_rows: Sequence[Mapping[str, Any]],
) -> dict[str, int]:
    verdict_counts = Counter(
        str(
            (
                row.get("block_verification", {})
                if isinstance(row.get("block_verification", {}), Mapping)
                else {}
            ).get("verdict", "")
            or ""
        )
        for row in validation_rows
    )
    faithfulness_counts = Counter(
        str(
            (
                row.get("faithfulness_review", {})
                if isinstance(row.get("faithfulness_review", {}), Mapping)
                else {}
            ).get("status", "")
            or ""
        )
        for row in validation_rows
    )
    return {
        "n_accepted_blocks": int(verdict_counts.get("accepted", 0) or 0),
        "n_failed_blocks": int(verdict_counts.get("failed", 0) or 0),
        "n_faithful_blocks": int(faithfulness_counts.get("faithful", 0) or 0),
        "n_unfaithful_blocks": int(
            faithfulness_counts.get("unfaithful", 0) or 0
        ),
        "n_blocks_needing_faithfulness_review": int(
            faithfulness_counts.get("needs_review", 0) or 0
        ),
        "n_accepted_and_faithful_blocks": sum(
            1
            for row in validation_rows
            if str(
                (
                    row.get("block_verification", {})
                    if isinstance(row.get("block_verification", {}), Mapping)
                    else {}
                ).get("verdict", "")
                or ""
            )
            == "accepted"
            and str(
                (
                    row.get("faithfulness_review", {})
                    if isinstance(row.get("faithfulness_review", {}), Mapping)
                    else {}
                ).get("status", "")
                or ""
            )
            == "faithful"
        ),
    }


def run_pseudo_formal_block_verifier_rows(
    rows: Sequence[Mapping[str, Any]],
    *,
    provider: GeneratorBackend,
    provider_name: str = "anthropic",
    model: str = "",
    model_tier: str = "sonnet",
    max_packets: int = 20,
    max_tokens: int = 2000,
    temperature: float = 0.0,
    max_repair_attempts: int = 1,
    question_id: str = "",
    out_dir: Path | None = None,
) -> dict[str, Any]:
    """Run an in-memory PF/BV turn for a typed AgentRuntime worker.

    This is the same prompt, JSON-repair, and validation path used by the
    standalone component gate. It accepts already lineage-bound runtime rows so
    an AgentRuntime subsystem does not need to export and re-import a second
    orchestration queue.
    """

    request_rows = pseudo_formal_block_verifier_request_rows(
        rows,
        max_packets=max_packets,
    )
    prompt_packets = [_prompt_packet_from_request(row) for row in request_rows]
    ok_packets = [packet for packet in prompt_packets if packet.get("ok") is True]
    resolved_model = resolve_generator_model(
        provider_name=provider_name,
        requested_model=model,
        model_tier=model_tier,
    )
    response_rows = [
        _llm_response_for_prompt_packet(
            packet,
            provider=provider,
            provider_name=provider_name,
            model=resolved_model,
            model_tier=model_tier,
            max_tokens=max_tokens,
            temperature=temperature,
            max_repair_attempts=max_repair_attempts,
        )
        for packet in ok_packets
    ]
    responses = [
        dict(row["response"])
        for row in response_rows
        if row.get("ok") is True and isinstance(row.get("response"), Mapping)
    ]
    packets_by_id = {
        str(packet.get("prompt_packet_id", "") or ""): packet
        for packet in ok_packets
    }
    validation_rows = [
        _validate_response_row(response, packets_by_id) for response in responses
    ]
    runtime_learning_rows = [
        dict(row["runtime_learning_row"])
        for row in validation_rows
        if row.get("ok") is True
        and isinstance(row.get("runtime_learning_row"), Mapping)
    ]
    if str(question_id or "").strip():
        runtime_learning_rows = [
            {**row, "question_id": str(question_id).strip()}
            for row in runtime_learning_rows
        ]
    backend_provider_names = _component_backend_provider_names(
        {"rows": response_rows}
    )
    normalized_provider_name = normalize_generator_provider_name(provider_name)
    live_generator = bool(normalized_provider_name and backend_provider_names) and all(
        is_live_generator_backend(normalized_provider_name, backend_provider_name)
        for backend_provider_name in backend_provider_names
    )
    prompt_errors = [
        str(error)
        for packet in prompt_packets
        for error in packet.get("errors", []) or []
    ]
    response_errors = [
        str(error)
        for row in response_rows
        for error in row.get("errors", []) or []
    ]
    validation_errors = [
        str(error)
        for row in validation_rows
        for error in row.get("errors", []) or []
    ]
    review_outcome_counts = _pseudo_formal_review_outcome_counts(validation_rows)
    all_ok = bool(request_rows) and (
        len(ok_packets)
        == len(response_rows)
        == len(validation_rows)
        == len(runtime_learning_rows)
        == len(request_rows)
    ) and not (prompt_errors or response_errors or validation_errors)
    payload: dict[str, Any] = {
        "schema_version": PSEUDO_FORMAL_BLOCK_VERIFIER_WORKER_SCHEMA_VERSION,
        "artifact_kind": "PseudoFormalBlockVerifierRuntimeTurnManifest",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "provider_name": normalized_provider_name,
        "backend_provider_names": backend_provider_names,
        "model": resolved_model,
        "model_tier": model_tier,
        "live_generator": live_generator,
        "static_or_fixture_only": not live_generator,
        "n_source_rows": len(rows),
        "n_request_rows": len(request_rows),
        "n_prompt_packets": len(prompt_packets),
        "n_ok_prompt_packets": len(ok_packets),
        "n_response_rows": len(response_rows),
        "n_valid_responses": sum(
            1 for row in validation_rows if row.get("ok") is True
        ),
        "n_runtime_learning_rows": len(runtime_learning_rows),
        **review_outcome_counts,
        "all_ok": all_ok,
        "errors": [*prompt_errors, *response_errors, *validation_errors],
        "request_row_hashes": [stable_hash(row) for row in request_rows],
        "prompt_packets": prompt_packets,
        "response_rows": response_rows,
        "validation_rows": validation_rows,
        "runtime_learning_rows": runtime_learning_rows,
        "proof_evidence_status": (
            PSEUDO_FORMAL_BLOCK_VERIFIER_FEEDBACK_NOT_PROOF_EVIDENCE
        ),
        "proof_evidence_boundary": PSEUDO_FORMALIZATION_PROOF_BOUNDARY,
        "boundary": (
            "This runtime turn is independent pseudo-formal block-verifier "
            "feedback. It is not Lean/AXLE proof evidence and cannot promote a "
            "theorem without target-prover kernel replay."
        ),
    }
    payload["manifest_id"] = "pseudo_formal_block_verifier_runtime_turn:" + stable_hash(
        {
            "provider_name": normalized_provider_name,
            "model": resolved_model,
            "model_tier": model_tier,
            "request_row_hashes": payload["request_row_hashes"],
            "response_rows": response_rows,
            "validation_rows": validation_rows,
            "runtime_learning_rows": runtime_learning_rows,
        }
    )[:20]
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = out_dir / "pseudo_formal_block_verifier_runtime_turn.json"
        prompt_path = out_dir / "prompt_packets.jsonl"
        response_path = out_dir / "response_rows.jsonl"
        validation_path = out_dir / "validation_rows.jsonl"
        learning_path = out_dir / "runtime_learning_rows.jsonl"
        payload.update(
            {
                "manifest_path": str(manifest_path),
                "prompt_packets_jsonl": str(prompt_path),
                "response_rows_jsonl": str(response_path),
                "validation_rows_jsonl": str(validation_path),
                "runtime_learning_rows_jsonl": str(learning_path),
            }
        )
        manifest_path.write_text(
            json.dumps(payload, indent=2, default=str),
            encoding="utf-8",
        )
        for path, output_rows in (
            (prompt_path, prompt_packets),
            (response_path, response_rows),
            (validation_path, validation_rows),
            (learning_path, runtime_learning_rows),
        ):
            path.write_text(
                "".join(
                    json.dumps(dict(row), sort_keys=True, default=str) + "\n"
                    for row in output_rows
                ),
                encoding="utf-8",
            )
    return payload


def run_pseudo_formal_block_verifier_component_gate(
    runtime_learning_jsonl_paths: Sequence[Path],
    out_dir: Path,
    *,
    provider: GeneratorBackend,
    provider_name: str = "anthropic",
    model: str = "",
    model_tier: str = LIVE_EVALUATION_CLAUDE_MODEL_TIER,
    max_packets: int = 20,
    max_tokens: int = 2000,
    temperature: float = 0.0,
    max_repair_attempts: int = 1,
) -> dict[str, Any]:
    """Run the full PF/BV prompt -> LLM response -> validation component gate."""

    if str(model_tier or "").strip().lower() == LIVE_EVALUATION_CLAUDE_MODEL_TIER:
        model = resolve_live_evaluation_model(provider_name, model)
    out_dir.mkdir(parents=True, exist_ok=True)
    prompt_out = out_dir / "prompt_packets"
    response_out = out_dir / "llm_responses"
    validation_out = out_dir / "response_validation"
    prompt_payload = export_pseudo_formal_block_verifier_prompt_packets(
        runtime_learning_jsonl_paths,
        prompt_out,
        max_packets=max_packets,
    )
    llm_payload = export_pseudo_formal_block_verifier_llm_responses(
        Path(str(prompt_payload.get("manifest_path", ""))),
        response_out,
        provider=provider,
        provider_name=provider_name,
        model=model,
        model_tier=model_tier,
        max_packets=max_packets,
        max_tokens=max_tokens,
        temperature=temperature,
        max_repair_attempts=max_repair_attempts,
    )
    response_jsonl = Path(
        str(
            llm_payload.get("responses_jsonl", "")
            or response_out / "pseudo_formal_block_verifier_responses.jsonl"
        )
    )
    validation_payload = export_pseudo_formal_block_verifier_response_validation(
        Path(str(prompt_payload.get("manifest_path", ""))),
        response_jsonl,
        validation_out,
    )
    backend_provider_names = _component_backend_provider_names(llm_payload)
    normalized_provider_name = normalize_generator_provider_name(provider_name)
    live_generator = bool(normalized_provider_name and backend_provider_names) and all(
        is_live_generator_backend(normalized_provider_name, backend_provider_name)
        for backend_provider_name in backend_provider_names
    )
    static_or_fixture_only = not live_generator
    fixture_plumbing_ok = bool(
        prompt_payload.get("all_ok")
        and llm_payload.get("all_ok")
        and validation_payload.get("all_ok")
        and int(validation_payload.get("n_runtime_learning_rows", 0) or 0) > 0
    )
    capability_evidence_ok = bool(fixture_plumbing_ok and live_generator)
    validation_rows = [
        row for row in validation_payload.get("rows", []) if isinstance(row, Mapping)
    ]
    review_outcome_counts = _pseudo_formal_review_outcome_counts(validation_rows)
    runtime_learning_rows = [
        row
        for row in validation_payload.get("runtime_learning_rows", [])
        if isinstance(row, Mapping)
    ]
    manifest_path = out_dir / "pseudo_formal_block_verifier_component_gate_manifest.json"
    payload: dict[str, Any] = {
        "schema_version": PSEUDO_FORMAL_BLOCK_VERIFIER_WORKER_SCHEMA_VERSION,
        "artifact_kind": "PseudoFormalBlockVerifierComponentGateManifest",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "provider_name": normalized_provider_name,
        "backend_provider_name": (
            backend_provider_names[0]
            if len(backend_provider_names) == 1
            else ",".join(backend_provider_names)
        ),
        "component_backend_provider_names": backend_provider_names,
        "model": str(llm_payload.get("model", "") or ""),
        "model_tier": model_tier,
        "live_generator": live_generator,
        "static_or_fixture_only": static_or_fixture_only,
        "fixture_plumbing_ok": fixture_plumbing_ok,
        "capability_evidence_ok": capability_evidence_ok,
        "n_source_runtime_learning_jsonl_paths": len(runtime_learning_jsonl_paths),
        "source_runtime_learning_jsonl_paths": [
            str(path) for path in runtime_learning_jsonl_paths
        ],
        "n_prompt_packets": int(prompt_payload.get("n_prompt_packets", 0) or 0),
        "n_ok_prompt_packets": int(
            prompt_payload.get("n_ok_prompt_packets", 0) or 0
        ),
        "n_llm_response_rows": int(llm_payload.get("n_llm_response_rows", 0) or 0),
        "n_ok_responses": int(llm_payload.get("n_ok_responses", 0) or 0),
        "n_valid_responses": int(
            validation_payload.get("n_valid_responses", 0) or 0
        ),
        "n_runtime_learning_rows": int(
            validation_payload.get("n_runtime_learning_rows", 0) or 0
        ),
        **review_outcome_counts,
        "prompt_packets_all_ok": bool(prompt_payload.get("all_ok", False)),
        "llm_responses_all_ok": bool(llm_payload.get("all_ok", False)),
        "response_validation_all_ok": bool(validation_payload.get("all_ok", False)),
        "all_ok": fixture_plumbing_ok,
        "runtime_learning_rows": [dict(row) for row in runtime_learning_rows],
        "proof_evidence_status": (
            PSEUDO_FORMAL_BLOCK_VERIFIER_COMPONENT_GATE_NOT_PROOF_EVIDENCE
        ),
        "proof_evidence_boundary": PSEUDO_FORMALIZATION_PROOF_BOUNDARY,
        "boundary": (
            "This component gate exercises pseudo-formal block-verifier "
            "prompting, LLM response generation, and response validation. It is "
            "not Lean/AXLE proof evidence and cannot promote a source theorem "
            "without target-prover kernel replay."
        ),
        "artifacts": {
            "manifest_json": str(manifest_path),
            "prompt_packets_manifest_json": str(prompt_payload.get("manifest_path", "")),
            "prompt_packets_jsonl": str(prompt_payload.get("prompt_packets_jsonl", "")),
            "llm_response_manifest_json": str(llm_payload.get("manifest_path", "")),
            "llm_response_rows_jsonl": str(llm_payload.get("response_rows_jsonl", "")),
            "responses_jsonl": str(llm_payload.get("responses_jsonl", "")),
            "response_validation_manifest_json": str(
                validation_payload.get("manifest_path", "")
            ),
            "response_validation_jsonl": str(
                validation_payload.get("response_validation_jsonl", "")
            ),
            "runtime_learning_rows_jsonl": str(
                validation_payload.get("runtime_learning_rows_jsonl", "")
            ),
        },
        "next_gate": (
            "Feed validated runtime_learning_rows back into a future "
            "AgentRuntime turn as non-proof PF/BV memory; do not count accepted "
            "PF/BV blocks as kernel proof."
        ),
    }
    manifest_path.write_text(
        json.dumps(payload, indent=2, default=str),
        encoding="utf-8",
    )
    (out_dir / "pseudo_formal_block_verifier_component_gate.md").write_text(
        _component_gate_markdown(payload),
        encoding="utf-8",
    )
    return payload


def _llm_response_for_prompt_packet(
    packet: Mapping[str, Any],
    *,
    provider: GeneratorBackend,
    provider_name: str,
    model: str,
    model_tier: str,
    max_tokens: int,
    temperature: float,
    max_repair_attempts: int,
) -> dict[str, Any]:
    prompt_packet_id = str(packet.get("prompt_packet_id", "") or "")
    request = GeneratorRequest(
        system_prompt=str(packet.get("system_prompt", "") or PSEUDO_FORMAL_BLOCK_VERIFIER_SYSTEM_PROMPT),
        user_prompt=str(packet.get("user_prompt", "") or ""),
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        schema=PSEUDO_FORMAL_BLOCK_VERIFIER_RESPONSE_JSON_SCHEMA,
        metadata={
            "subsystem": "PseudoFormalBlockVerifier",
            "agent": "LLMPseudoFormalBlockVerifier",
            "provider_name": provider_name,
            "model_tier": model_tier,
            "prompt_packet_id": prompt_packet_id,
            "source_pseudo_formal_work_order_id": str(
                packet.get("source_pseudo_formal_work_order_id", "") or ""
            ),
        },
    )

    def build_packet(
        payload: Mapping[str, Any],
        response: Any,
        raw_text: str,
    ) -> dict[str, Any]:
        normalized = dict(payload)
        normalized["provider_name"] = provider_name
        normalized["backend_provider_name"] = str(response.provider or "")
        normalized["model"] = str(response.model or model)
        normalized["model_tier"] = model_tier
        normalized["raw_response_fingerprint"] = stable_hash(raw_text)
        normalized["proof_evidence_status"] = (
            PSEUDO_FORMAL_BLOCK_VERIFIER_FEEDBACK_NOT_PROOF_EVIDENCE
        )
        normalized["proof_evidence_boundary"] = PSEUDO_FORMALIZATION_PROOF_BOUNDARY
        return normalized

    def validate_packet(candidate: Mapping[str, Any]) -> list[str]:
        validation = _validate_response_row(candidate, {prompt_packet_id: packet})
        return [str(error) for error in validation.get("errors", []) or []]

    try:
        response_packet = generate_validated_json_packet(
            provider=provider,
            request=request,
            extract_payload=lambda text: extract_json_object(
                text,
                label="PF BlockVerifier response",
            ),
            build_packet=build_packet,
            validate_packet=validate_packet,
            validation_label="pseudo_formal_block_verifier_response",
            max_repair_attempts=max_repair_attempts,
        )
    except PacketValidationError as exc:
        return {
            "schema_version": PSEUDO_FORMAL_BLOCK_VERIFIER_WORKER_SCHEMA_VERSION,
            "artifact_kind": "PseudoFormalBlockVerifierLlmResponseRow",
            "prompt_packet_id": prompt_packet_id,
            "source_pseudo_formal_work_order_id": str(
                packet.get("source_pseudo_formal_work_order_id", "") or ""
            ),
            "ok": False,
            "llm_response_status": "validation_failed",
            "errors": list(exc.errors),
            "llm_json_repair_history": list(exc.history),
            "response": {},
            "proof_evidence_status": PSEUDO_FORMAL_BLOCK_VERIFIER_FEEDBACK_NOT_PROOF_EVIDENCE,
            "proof_evidence_boundary": PSEUDO_FORMALIZATION_PROOF_BOUNDARY,
        }
    except Exception as exc:
        return {
            "schema_version": PSEUDO_FORMAL_BLOCK_VERIFIER_WORKER_SCHEMA_VERSION,
            "artifact_kind": "PseudoFormalBlockVerifierLlmResponseRow",
            "prompt_packet_id": prompt_packet_id,
            "source_pseudo_formal_work_order_id": str(
                packet.get("source_pseudo_formal_work_order_id", "") or ""
            ),
            "ok": False,
            "llm_response_status": "provider_failed",
            "errors": [f"{type(exc).__name__}: {exc}"],
            "llm_json_repair_history": [],
            "response": {},
            "proof_evidence_status": (
                PSEUDO_FORMAL_BLOCK_VERIFIER_FEEDBACK_NOT_PROOF_EVIDENCE
            ),
            "proof_evidence_boundary": PSEUDO_FORMALIZATION_PROOF_BOUNDARY,
        }
    return {
        "schema_version": PSEUDO_FORMAL_BLOCK_VERIFIER_WORKER_SCHEMA_VERSION,
        "artifact_kind": "PseudoFormalBlockVerifierLlmResponseRow",
        "prompt_packet_id": prompt_packet_id,
        "source_pseudo_formal_work_order_id": str(
            packet.get("source_pseudo_formal_work_order_id", "") or ""
        ),
        "ok": True,
        "llm_response_status": "valid_response",
        "errors": [],
        "llm_json_repair_attempts": int(
            response_packet.get("llm_json_repair_attempts", 0) or 0
        ),
        "llm_json_repair_history": list(
            response_packet.get("llm_json_repair_history", []) or []
        ),
        "response": response_packet,
        "proof_evidence_status": PSEUDO_FORMAL_BLOCK_VERIFIER_FEEDBACK_NOT_PROOF_EVIDENCE,
        "proof_evidence_boundary": PSEUDO_FORMALIZATION_PROOF_BOUNDARY,
    }


def _prompt_packet_from_request(row: Mapping[str, Any]) -> dict[str, Any]:
    input_summary = _input_summary(row)
    question_id = str(
        row.get("question_id", "")
        or input_summary.get("question_id", "")
        or ""
    ).strip()
    work_order_id = str(
        row.get("source_pseudo_formal_work_order_id", "")
        or input_summary.get("work_order_id", "")
        or row.get("work_order_id", "")
        or ""
    ).strip()
    source_block_id = str(
        row.get("source_block_id", "") or input_summary.get("source_block_id", "") or ""
    ).strip()
    target_theorem_name = str(
        row.get("target_theorem_name", "")
        or input_summary.get("target_theorem_name", "")
        or row.get("source_theorem_id", "")
        or input_summary.get("source_theorem_id", "")
        or ""
    ).strip()
    dependency_context = _mapping_list_value(
        row,
        input_summary,
        "dependency_statement_context",
    )
    premises = _string_list_value(row, input_summary, "source_block_premises")
    source_anchors = _mapping_list_value(
        row,
        input_summary,
        "source_anchors",
    )
    proof_text = str(
        row.get("source_block_proof_text", "")
        or input_summary.get("source_block_proof_text", "")
        or ""
    ).strip()
    source_request_row_kind = str(
        row.get("row_kind", "")
        or input_summary.get("row_kind", "")
        or ""
    )
    packet_errors = _request_packet_errors(
        source_request_row_kind=source_request_row_kind,
        work_order_id=work_order_id,
        source_block_id=source_block_id,
        source_block_conclusion=str(
            row.get("source_block_conclusion", "")
            or input_summary.get("source_block_conclusion", "")
            or ""
        ).strip(),
        dependency_context=dependency_context,
        premises=premises,
        proof_text=proof_text,
        source_anchors=source_anchors,
    )
    prompt_packet_id = "pseudo_formal_block_verifier_prompt:" + stable_hash(
        [work_order_id, source_block_id, target_theorem_name, dependency_context, premises, proof_text]
    )[:16]
    packet = {
        "schema_version": PSEUDO_FORMAL_BLOCK_VERIFIER_WORKER_SCHEMA_VERSION,
        "artifact_kind": PSEUDO_FORMAL_BLOCK_VERIFIER_PROMPT_PACKET_KIND,
        "prompt_packet_id": prompt_packet_id,
        "packet_status": "ready" if not packet_errors else "invalid_request_context",
        "ok": not packet_errors,
        "errors": packet_errors,
        "question_id": question_id,
        "source_pseudo_formal_work_order_id": work_order_id,
        "source_agenda_id": str(
            row.get("source_agenda_id", "") or input_summary.get("agenda_id", "") or ""
        ),
        "source_theorem_id": str(
            row.get("source_theorem_id", "")
            or input_summary.get("source_theorem_id", "")
            or ""
        ),
        "target_theorem_name": target_theorem_name,
        "target_ids": _string_list_value(row, input_summary, "target_ids"),
        "source_block_id": source_block_id,
        "source_block_type": str(
            row.get("source_block_type", "")
            or input_summary.get("source_block_type", "")
            or ""
        ),
        "source_block_conclusion": str(
            row.get("source_block_conclusion", "")
            or input_summary.get("source_block_conclusion", "")
            or ""
        ),
        "block_depth": row.get("block_depth", input_summary.get("block_depth", 1)),
        "dependency_scope": str(
            row.get("dependency_scope", "")
            or input_summary.get("dependency_scope", "")
            or ""
        ),
        "dependency_ids": _string_list_value(row, input_summary, "dependency_ids"),
        "dependency_statement_context": dependency_context,
        "scope_parent_id": str(
            row.get("scope_parent_id", "")
            or input_summary.get("scope_parent_id", "")
            or ""
        ),
        "inherited_scope": _string_list_value(row, input_summary, "inherited_scope"),
        "source_block_premises": premises,
        "source_block_proof_text": proof_text,
        "source_anchors": source_anchors,
        "source_request_row_kind": source_request_row_kind,
        "strictness_threshold": _strictness_threshold(row, input_summary),
        "aggregation_rule": PSEUDO_FORMAL_DEFAULT_AGGREGATION_RULE,
        "system_prompt": PSEUDO_FORMAL_BLOCK_VERIFIER_SYSTEM_PROMPT,
        "user_prompt": _block_verifier_user_prompt(
            prompt_packet_id=prompt_packet_id,
            work_order_id=work_order_id,
            source_block_id=source_block_id,
            target_theorem_name=target_theorem_name,
            row=row,
            dependency_context=dependency_context,
            premises=premises,
            proof_text=proof_text,
            source_anchors=source_anchors,
        ),
        "expected_response_schema": PSEUDO_FORMAL_BLOCK_VERIFIER_RESPONSE_JSON_SCHEMA,
        "proof_evidence_status": PSEUDO_FORMAL_BLOCK_VERIFIER_FEEDBACK_NOT_PROOF_EVIDENCE,
        "proof_evidence_boundary": PSEUDO_FORMALIZATION_PROOF_BOUNDARY,
        "request_row_fingerprint": stable_hash(row),
    }
    return packet


PSEUDO_FORMAL_BLOCK_VERIFIER_SYSTEM_PROMPT = (
    "You are the independent reviewer for one pseudo-formal proof block. Assess "
    "source faithfulness and local logical validity as separate questions. For "
    "faithfulness, use only the supplied source anchors and excerpts; return "
    "needs_review when they are insufficient. For local validity, use only the "
    "explicit premises, inherited scope, declared dependency statements, "
    "conclusion, and local proof text. Do not use hidden dependency proof bodies, outside "
    "assumptions, or target-prover claims. Return strict JSON only."
)


def _block_verifier_user_prompt(
    *,
    prompt_packet_id: str,
    work_order_id: str,
    source_block_id: str,
    target_theorem_name: str,
    row: Mapping[str, Any],
    dependency_context: Sequence[Mapping[str, Any]],
    premises: Sequence[str],
    proof_text: str,
    source_anchors: Sequence[Mapping[str, Any]],
) -> str:
    payload = {
        "task": "independent_pseudo_formal_block_review",
        "prompt_packet_id": prompt_packet_id,
        "source_pseudo_formal_work_order_id": work_order_id,
        "target_theorem_name": target_theorem_name,
        "source_block_id": source_block_id,
        "source_block_conclusion": str(row.get("source_block_conclusion", "") or ""),
        "source_block_premises": list(premises),
        "inherited_scope": _string_list(row.get("inherited_scope", [])),
        "dependency_statement_context": [dict(item) for item in dependency_context],
        "local_proof_text": proof_text,
        "source_anchors": [dict(item) for item in source_anchors],
        "current_author_faithfulness_status": str(
            row.get("faithfulness_status", "") or ""
        ),
        "review_dimensions": {
            "source_faithfulness": (
                "Does the block preserve the supplied source claims without "
                "strengthening, weakening, omission, or scope drift?"
            ),
            "local_validity": (
                "Does the conclusion follow from only the supplied bounded context?"
            ),
        },
        "allowed_faithfulness_statuses": list(
            PSEUDO_FORMAL_FAITHFULNESS_REVIEW_STATUSES
        ),
        "allowed_verdicts": ["accepted", "failed"],
        "nonproof_boundary": PSEUDO_FORMALIZATION_PROOF_BOUNDARY,
        "required_output": {
            "prompt_packet_id": prompt_packet_id,
            "source_pseudo_formal_work_order_id": work_order_id,
            "source_block_id": source_block_id,
            "faithfulness_review": {
                "status": "faithful|unfaithful|needs_review",
                "reason": "specific source-comparison rationale",
            },
            "block_verification": {
                "verdict": "accepted|failed",
                "reason": "specific local rationale",
                "verifier_provenance": "independent_block_verifier",
                "independent_verifier": True,
                "strictness_threshold": PSEUDO_FORMAL_DEFAULT_CALIBRATION_STRICTNESS,
                "aggregation_rule": PSEUDO_FORMAL_DEFAULT_AGGREGATION_RULE,
                "rollout_count": 1,
            },
            "cited_dependency_statement_ids": [],
            "issues": [],
            "proof_evidence_status": PSEUDO_FORMAL_BLOCK_VERIFIER_FEEDBACK_NOT_PROOF_EVIDENCE,
        },
    }
    return json.dumps(payload, indent=2, sort_keys=True)


def _validate_response_row(
    response: Mapping[str, Any],
    packets_by_id: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    prompt_packet_id = str(response.get("prompt_packet_id", "") or "").strip()
    packet = packets_by_id.get(prompt_packet_id, {})
    errors: list[str] = []
    if not prompt_packet_id:
        errors.append("prompt_packet_id missing")
    if not packet:
        errors.append("prompt_packet_id does not match a prompt packet")
    faithfulness_review = _normalized_faithfulness_review(response)
    faithfulness_status = str(faithfulness_review.get("status", "") or "")
    faithfulness_reason = str(faithfulness_review.get("reason", "") or "")
    if faithfulness_status not in PSEUDO_FORMAL_FAITHFULNESS_REVIEW_STATUSES:
        errors.append(
            "faithfulness_review.status must be one of: "
            + ", ".join(PSEUDO_FORMAL_FAITHFULNESS_REVIEW_STATUSES)
        )
    if not faithfulness_reason:
        errors.append("faithfulness_review.reason is required")
    block_verification = _normalized_block_verification(response)
    verdict = str(block_verification.get("verdict", "") or "").strip()
    reason = str(block_verification.get("reason", "") or "").strip()
    provenance = str(block_verification.get("verifier_provenance", "") or "").strip()
    if verdict not in {"accepted", "failed"}:
        errors.append("block_verification.verdict must be accepted or failed")
    if not reason:
        errors.append("block_verification.reason is required")
    if provenance not in PSEUDO_FORMAL_INDEPENDENT_BLOCK_VERIFIER_PROVENANCES:
        errors.append("block_verification.verifier_provenance must be independent")
    if block_verification.get("independent_verifier") is not True:
        errors.append("block_verification.independent_verifier must be true")
    rollout_count = _int_like(block_verification.get("rollout_count"), default=0)
    if rollout_count < 1:
        errors.append("block_verification.rollout_count must be >= 1")
    if bool(response.get("kernel_verified", False)) or bool(
        response.get("source_theorem_kernel_verified", False)
    ):
        errors.append("PF/BV response must not claim kernel verification")
    if packet and str(response.get("source_block_id", "") or packet.get("source_block_id", "")) != str(
        packet.get("source_block_id", "")
    ):
        errors.append("source_block_id does not match prompt packet")
    learning_row: dict[str, Any] = {}
    if not errors and packet:
        learning_row = _runtime_learning_row_from_response(
            packet,
            response,
            faithfulness_review=faithfulness_review,
            block_verification=block_verification,
        )
    validation_status = "valid" if not errors else "invalid_response"
    return {
        "schema_version": PSEUDO_FORMAL_BLOCK_VERIFIER_WORKER_SCHEMA_VERSION,
        "artifact_kind": "PseudoFormalBlockVerifierResponseValidationRow",
        "prompt_packet_id": prompt_packet_id,
        "source_pseudo_formal_work_order_id": str(
            packet.get("source_pseudo_formal_work_order_id", "")
            or response.get("source_pseudo_formal_work_order_id", "")
            or ""
        ),
        "source_block_id": str(
            packet.get("source_block_id", "") or response.get("source_block_id", "") or ""
        ),
        "validation_status": validation_status,
        "ok": not errors,
        "errors": errors,
        "faithfulness_review": faithfulness_review,
        "block_verification": block_verification,
        "runtime_learning_row": learning_row,
        "proof_evidence_status": PSEUDO_FORMAL_BLOCK_VERIFIER_FEEDBACK_NOT_PROOF_EVIDENCE,
        "proof_evidence_boundary": PSEUDO_FORMALIZATION_PROOF_BOUNDARY,
    }


def _runtime_learning_row_from_response(
    packet: Mapping[str, Any],
    response: Mapping[str, Any],
    *,
    faithfulness_review: Mapping[str, Any],
    block_verification: Mapping[str, Any],
) -> dict[str, Any]:
    work_order_id = str(packet.get("source_pseudo_formal_work_order_id", "") or "")
    target_ids = _string_list(packet.get("target_ids", []))
    structural_quality = _packet_structural_quality(packet)
    worker_commands = _pseudo_formal_block_verifier_worker_commands()
    verifier_feedback_id = "pseudo_formal_block_verifier_feedback:" + stable_hash(
        [
            packet.get("prompt_packet_id", ""),
            faithfulness_review,
            block_verification,
        ]
    )[:16]
    faithfulness_status = str(faithfulness_review.get("status", "") or "")
    source_request_row_kind = str(
        packet.get("source_request_row_kind", "")
        or PSEUDO_FORMAL_BLOCK_VERIFICATION_REQUEST_ROW_KIND
    )
    row = {
        "schema_version": PSEUDO_FORMAL_BLOCK_VERIFIER_WORKER_SCHEMA_VERSION,
        "artifact_kind": "RuntimeLearningRow",
        "question_id": str(packet.get("question_id", "") or ""),
        "learning_task": PSEUDO_FORMAL_BLOCK_ROUTING_LEARNING_TASK,
        "pseudo_formal_method_contract_id": PSEUDO_FORMAL_VERIFICATION_METHOD_CONTRACT_ID,
        "pseudo_formal_pipeline_stage": PSEUDO_FORMAL_BLOCK_ROUTING_METHOD_STAGE,
        "target_theorem_name": str(packet.get("target_theorem_name", "") or ""),
        "target_ids": target_ids,
        "next_owner_subsystem": "Formalizer/ProofEngineer",
        "memory_status": PSEUDO_FORMAL_BLOCK_ROUTING_MEMORY_STATUS,
        "source_agenda_id": str(packet.get("source_agenda_id", "") or ""),
        "source_pseudo_formal_work_order_id": work_order_id,
        "source_formalizer_proposal_id": str(
            packet.get("source_formalizer_proposal_id", "") or ""
        ),
        "source_formalization_manifest_id": str(
            packet.get("source_formalization_manifest_id", "") or ""
        ),
        "source_packet_id": str(packet.get("source_packet_id", "") or ""),
        "source_theorem_id": str(packet.get("source_theorem_id", "") or ""),
        "source_block_id": str(packet.get("source_block_id", "") or ""),
        "source_block_type": str(packet.get("source_block_type", "") or ""),
        "source_block_conclusion": str(packet.get("source_block_conclusion", "") or ""),
        "block_depth": packet.get("block_depth", 1),
        "dependency_scope": str(packet.get("dependency_scope", "") or ""),
        "dependency_ids": _string_list(packet.get("dependency_ids", [])),
        "dependency_statement_context": [
            dict(item)
            for item in packet.get("dependency_statement_context", []) or []
            if isinstance(item, Mapping)
        ],
        "scope_parent_id": str(packet.get("scope_parent_id", "") or ""),
        "inherited_scope": _string_list(packet.get("inherited_scope", [])),
        "source_block_premises": _string_list(packet.get("source_block_premises", [])),
        "source_block_proof_text": str(packet.get("source_block_proof_text", "") or ""),
        "structural_quality": dict(structural_quality),
        "structural_quality_ok": bool(structural_quality.get("all_ok", False)),
        "structural_quality_issues": list(structural_quality.get("issues", []) or []),
        "faithfulness_status": faithfulness_status,
        "faithfulness_review": dict(faithfulness_review),
        "faithfulness_repair_status": (
            "not_required"
            if faithfulness_status == "faithful"
            else "needs_repair"
            if faithfulness_status == "unfaithful"
            else "unavailable"
        ),
        "block_verification": dict(block_verification),
        "block_verification_verifier_provenance": str(
            block_verification.get("verifier_provenance", "") or ""
        ),
        "block_verification_independent": True,
        "independent_block_verification_required": False,
        "independent_block_verification_status": "completed",
        "independent_block_verification_completed": True,
        "block_verifier_feedback_id": verifier_feedback_id,
        "block_verifier_prompt_packet_id": str(packet.get("prompt_packet_id", "") or ""),
        "bv_calibration": {
            "strictness_threshold": str(
                block_verification.get(
                    "strictness_threshold",
                    PSEUDO_FORMAL_DEFAULT_CALIBRATION_STRICTNESS,
                )
                or PSEUDO_FORMAL_DEFAULT_CALIBRATION_STRICTNESS
            ),
            "aggregation_rule": str(
                block_verification.get("aggregation_rule", PSEUDO_FORMAL_DEFAULT_AGGREGATION_RULE)
                or PSEUDO_FORMAL_DEFAULT_AGGREGATION_RULE
            ),
            "pessimistic_acceptance": (
                str(block_verification.get("verdict", "") or "") == "accepted"
                and faithfulness_status == "faithful"
            ),
            "rollout_count": _int_like(block_verification.get("rollout_count"), default=1),
        },
        "pseudo_formal_block_verifier_worker": dict(worker_commands),
        "recommended_commands": list(worker_commands["recommended_commands"]),
        "source_anchors": [
            dict(item)
            for item in packet.get("source_anchors", []) or []
            if isinstance(item, Mapping)
        ],
        "runtime_generated_queue_name": PSEUDO_FORMAL_BLOCK_ROUTING_QUEUE_NAME,
        "runtime_queue_status": PSEUDO_FORMAL_BLOCK_ROUTING_QUEUE_STATUS_BY_TARGET_LANE[
            PSEUDO_FORMAL_TARGET_LANE_FORMAL_GAP
        ],
        "row_kind": source_request_row_kind,
        "target_lane": PSEUDO_FORMAL_TARGET_LANE_FORMAL_GAP,
        "reason": str(block_verification.get("reason", "") or ""),
        "input_summary": {
            "trigger": PSEUDO_FORMAL_BLOCK_VERIFIER_FEEDBACK_TRIGGER,
            "prompt_packet_id": str(packet.get("prompt_packet_id", "") or ""),
            "work_order_id": work_order_id,
            "row_kind": source_request_row_kind,
            "target_lane": PSEUDO_FORMAL_TARGET_LANE_FORMAL_GAP,
            "source_theorem_id": str(packet.get("source_theorem_id", "") or ""),
            "source_block_id": str(packet.get("source_block_id", "") or ""),
            "source_block_conclusion": str(packet.get("source_block_conclusion", "") or ""),
            "dependency_statement_context": [
                dict(item)
                for item in packet.get("dependency_statement_context", []) or []
                if isinstance(item, Mapping)
            ],
            "source_block_premises": _string_list(packet.get("source_block_premises", [])),
            "source_block_proof_text": str(packet.get("source_block_proof_text", "") or ""),
            "structural_quality": dict(structural_quality),
            "structural_quality_ok": bool(structural_quality.get("all_ok", False)),
            "structural_quality_issues": list(
                structural_quality.get("issues", []) or []
            ),
            "faithfulness_review": dict(faithfulness_review),
            "faithfulness_status": faithfulness_status,
            "block_verification": dict(block_verification),
            "block_verification_verifier_provenance": str(
                block_verification.get("verifier_provenance", "") or ""
            ),
            "block_verification_independent": True,
            "independent_block_verification_required": False,
            "independent_block_verification_status": "completed",
            "runtime_queue_status": PSEUDO_FORMAL_BLOCK_ROUTING_QUEUE_STATUS_BY_TARGET_LANE[
                PSEUDO_FORMAL_TARGET_LANE_FORMAL_GAP
            ],
            "proof_evidence_status": PSEUDO_FORMALIZATION_NOT_PROOF_EVIDENCE,
            "proof_evidence_boundary": PSEUDO_FORMALIZATION_PROOF_BOUNDARY,
            "pseudo_formal_block_verifier_worker": dict(worker_commands),
            "recommended_commands": list(worker_commands["recommended_commands"]),
        },
        "target_behavior": (
            "consume independent PF/BV block-verifier feedback for the bounded "
            "pseudo-formal block; repair, split, or route the block without "
            "treating BV as theorem proof"
        ),
        "acceptance_gate": (
            "PF/BV feedback can guide Formalizer/RAG/source-to-bridge work only; "
            "source theorem proof promotion still requires target-prover kernel replay"
        ),
        "kernel_verified": False,
        "source_theorem_kernel_verified": False,
        "proof_evidence_status": PSEUDO_FORMALIZATION_NOT_PROOF_EVIDENCE,
        "proof_evidence_boundary": PSEUDO_FORMALIZATION_PROOF_BOUNDARY,
        "boundary": PSEUDO_FORMALIZATION_PROOF_BOUNDARY,
    }
    return row


def _packet_structural_quality(packet: Mapping[str, Any]) -> dict[str, Any]:
    return pseudo_formal_block_structural_quality(
        {
            "premises": _string_list(packet.get("source_block_premises", [])),
            "dependency_ids": _string_list(packet.get("dependency_ids", [])),
            "inherited_scope": _string_list(packet.get("inherited_scope", [])),
            "source_anchors": [
                dict(item)
                for item in packet.get("source_anchors", []) or []
                if isinstance(item, Mapping)
            ],
            "conclusion": str(packet.get("source_block_conclusion", "") or ""),
            "proof_text": str(packet.get("source_block_proof_text", "") or ""),
        }
    )


def _pseudo_formal_block_verifier_worker_commands() -> dict[str, Any]:
    prompt_packets_command = (
        "python -m ai_statistician.cli pseudo-formal-block-verifier-prompt-packets "
        "--runtime-learning-jsonl <runtime_learning_rows.jsonl> --out <prompt_out>"
    )
    llm_response_command = (
        "python -m ai_statistician.cli pseudo-formal-block-verifier-llm-responses "
        "--prompt-packets-manifest <prompt_out>/"
        "pseudo_formal_block_verifier_prompt_packets_manifest.json --provider "
        "anthropic --out <llm_response_out>"
    )
    response_validation_command = (
        "python -m ai_statistician.cli "
        "pseudo-formal-block-verifier-response-validation "
        "--prompt-packets-manifest <prompt_out>/"
        "pseudo_formal_block_verifier_prompt_packets_manifest.json "
        "--response-jsonl <llm_response_out>/"
        "pseudo_formal_block_verifier_responses.jsonl --out <validation_out>"
    )
    component_gate_command = (
        "python -m ai_statistician.cli pseudo-formal-block-verifier-component-gate "
        "--runtime-learning-jsonl <runtime_learning_rows.jsonl> --provider "
        "anthropic --out <component_gate_out>"
    )
    return {
        "prompt_packets_command": prompt_packets_command,
        "llm_response_command": llm_response_command,
        "response_validation_command": response_validation_command,
        "component_gate_command": component_gate_command,
        "recommended_commands": [
            component_gate_command,
            prompt_packets_command,
            llm_response_command,
            response_validation_command,
        ],
        "proof_evidence_status": (
            PSEUDO_FORMAL_BLOCK_VERIFIER_FEEDBACK_NOT_PROOF_EVIDENCE
        ),
        "boundary": (
            "These commands reproduce PF/BV feedback generation for routing and "
            "repair memory only. They do not generate Lean/AXLE proof evidence."
        ),
    }


def _with_verifier_dispatch_identity(row: Mapping[str, Any]) -> dict[str, Any]:
    """Bind generic work-order identity without inventing mathematical content."""

    candidate = dict(row)
    input_summary = _input_summary(candidate)
    method_contract_id = str(
        candidate.get("pseudo_formal_method_contract_id", "")
        or input_summary.get("pseudo_formal_method_contract_id", "")
        or ""
    )
    row_id = str(candidate.get("row_id", "") or "").strip()
    if (
        method_contract_id == PSEUDO_FORMAL_VERIFICATION_METHOD_CONTRACT_ID
        and row_id
    ):
        candidate.setdefault(
            "learning_task",
            PSEUDO_FORMAL_BLOCK_ROUTING_LEARNING_TASK,
        )
        candidate.setdefault("source_pseudo_formal_work_order_id", row_id)
        candidate.setdefault("work_order_id", row_id)
    return candidate


def _is_independent_bv_request_row(row: Mapping[str, Any]) -> bool:
    input_summary = _input_summary(row)
    if str(row.get("learning_task", "") or input_summary.get("learning_task", "") or "") != (
        PSEUDO_FORMAL_BLOCK_ROUTING_LEARNING_TASK
    ):
        return False
    row_kind = str(
        row.get("row_kind", "")
        or row.get("pseudo_formal_row_kind", "")
        or input_summary.get("row_kind", "")
        or input_summary.get("pseudo_formal_row_kind", "")
        or ""
    )
    if row_kind not in {
        PSEUDO_FORMAL_BLOCK_VERIFICATION_REQUEST_ROW_KIND,
        PSEUDO_FORMAL_FAITHFULNESS_REVIEW_ROW_KIND,
    }:
        return False
    block_verification = _mapping_value(row, input_summary, "block_verification")
    verdict = str(block_verification.get("verdict", "") or "")
    independent = bool(
        row.get("block_verification_independent", False)
        or input_summary.get("block_verification_independent", False)
        or block_verification.get("independent_verifier", False)
    )
    return not (independent and verdict in {"accepted", "failed"})


def _request_packet_errors(
    *,
    source_request_row_kind: str,
    work_order_id: str,
    source_block_id: str,
    source_block_conclusion: str,
    dependency_context: Sequence[Mapping[str, Any]],
    premises: Sequence[str],
    proof_text: str,
    source_anchors: Sequence[Mapping[str, Any]],
) -> list[str]:
    errors: list[str] = []
    if not work_order_id:
        errors.append("source_pseudo_formal_work_order_id missing")
    if not source_block_id:
        errors.append("source_block_id missing")
    if not source_block_conclusion:
        errors.append("source_block_conclusion missing")
    if not proof_text:
        errors.append("source_block_proof_text missing")
    if (
        source_request_row_kind == PSEUDO_FORMAL_FAITHFULNESS_REVIEW_ROW_KIND
        and not pseudo_formal_work_order_row_has_reviewable_source_anchor(
            {"source_anchors": source_anchors}
        )
    ):
        errors.append(
            "source_anchors require a non-empty excerpt for independent "
            "faithfulness review"
        )
    return errors


def _normalized_faithfulness_review(
    response: Mapping[str, Any],
) -> dict[str, str]:
    review = response.get("faithfulness_review", {})
    if not isinstance(review, Mapping):
        review = {}
    return {
        "status": str(review.get("status", "") or "").strip(),
        "reason": str(review.get("reason", "") or "").strip(),
    }


def _normalized_block_verification(response: Mapping[str, Any]) -> dict[str, Any]:
    block_verification = response.get("block_verification", {})
    if not isinstance(block_verification, Mapping):
        block_verification = {}
    verdict = str(
        block_verification.get("verdict", response.get("verdict", "")) or ""
    ).strip()
    strictness = str(
        block_verification.get(
            "strictness_threshold",
            PSEUDO_FORMAL_DEFAULT_CALIBRATION_STRICTNESS,
        )
        or PSEUDO_FORMAL_DEFAULT_CALIBRATION_STRICTNESS
    )
    aggregation_rule = str(
        block_verification.get("aggregation_rule", PSEUDO_FORMAL_DEFAULT_AGGREGATION_RULE)
        or PSEUDO_FORMAL_DEFAULT_AGGREGATION_RULE
    )
    provenance = str(
        block_verification.get("verifier_provenance", "") or ""
    )
    return {
        "verdict": verdict,
        "reason": str(
            block_verification.get("reason", response.get("reason", "")) or ""
        ).strip(),
        "verifier_provenance": provenance,
        "independent_verifier": bool(
            block_verification.get("independent_verifier", False)
        ),
        "strictness_threshold": strictness,
        "aggregation_rule": aggregation_rule,
        "rollout_count": _int_like(block_verification.get("rollout_count"), default=0),
    }


def _strictness_threshold(
    row: Mapping[str, Any],
    input_summary: Mapping[str, Any],
) -> str:
    for source in (row, input_summary):
        bv_calibration = source.get("bv_calibration", {})
        if isinstance(bv_calibration, Mapping):
            value = str(bv_calibration.get("strictness_threshold", "") or "")
            if value:
                return value
        block_verification = source.get("block_verification", {})
        if isinstance(block_verification, Mapping):
            value = str(block_verification.get("strictness_threshold", "") or "")
            if value:
                return value
    return PSEUDO_FORMAL_DEFAULT_CALIBRATION_STRICTNESS


def _read_runtime_learning_rows(
    paths: Sequence[Path],
    errors: list[str],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in paths:
        rows.extend(_read_jsonl(path, errors))
    return rows


def _read_json(path: Path, errors: list[str]) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"{path}: {exc}")
        return {}
    return payload if isinstance(payload, dict) else {}


def _read_jsonl(path: Path, errors: list[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        errors.append(f"{path}: {exc}")
        return rows
    for line_number, line in enumerate(lines, start=1):
        text = line.strip()
        if not text:
            continue
        try:
            payload = json.loads(text)
        except json.JSONDecodeError as exc:
            errors.append(f"{path}:{line_number}: {exc}")
            continue
        if isinstance(payload, dict):
            rows.append(payload)
        else:
            errors.append(f"{path}:{line_number}: JSON row is not an object")
    return rows


def _component_backend_provider_names(payload: Mapping[str, Any]) -> list[str]:
    names: list[str] = []
    raw_values = payload.get("component_backend_provider_names", [])
    if isinstance(raw_values, str):
        raw_values = [raw_values]
    elif isinstance(raw_values, Mapping):
        raw_values = raw_values.values()
    else:
        try:
            raw_values = list(raw_values or [])
        except TypeError:
            raw_values = [raw_values]
    for value in raw_values:
        normalized = normalize_generator_provider_name(value)
        if normalized:
            names.append(normalized)
    scalar = normalize_generator_provider_name(payload.get("backend_provider_name", ""))
    if scalar:
        for value in scalar.split(","):
            normalized = normalize_generator_provider_name(value)
            if normalized:
                names.append(normalized)
    response_rows = payload.get("rows", [])
    if isinstance(response_rows, Sequence) and not isinstance(
        response_rows, (str, bytes, bytearray)
    ):
        for row in response_rows:
            if not isinstance(row, Mapping):
                continue
            response = row.get("response", {})
            if isinstance(response, Mapping):
                normalized = normalize_generator_provider_name(
                    response.get("backend_provider_name", "")
                )
                if normalized:
                    names.append(normalized)
            normalized = normalize_generator_provider_name(
                row.get("backend_provider_name", "")
            )
            if normalized:
                names.append(normalized)
    return list(dict.fromkeys(names))


def _input_summary(row: Mapping[str, Any]) -> dict[str, Any]:
    value = row.get("input_summary", {})
    return dict(value) if isinstance(value, Mapping) else {}


def _mapping_value(
    row: Mapping[str, Any],
    input_summary: Mapping[str, Any],
    key: str,
) -> dict[str, Any]:
    row_value = row.get(key)
    input_value = input_summary.get(key)
    if isinstance(row_value, Mapping) and row_value:
        return dict(row_value)
    if isinstance(input_value, Mapping):
        return dict(input_value)
    if isinstance(row_value, Mapping):
        return dict(row_value)
    return {}


def _mapping_list_value(
    row: Mapping[str, Any],
    input_summary: Mapping[str, Any],
    key: str,
) -> list[dict[str, Any]]:
    row_value = row.get(key)
    input_value = input_summary.get(key)
    value = row_value if isinstance(row_value, list) and row_value else input_value
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, Mapping)]


def _string_list_value(
    row: Mapping[str, Any],
    input_summary: Mapping[str, Any],
    key: str,
) -> list[str]:
    row_value = row.get(key)
    input_value = input_summary.get(key)
    value = row_value if isinstance(row_value, list) and row_value else input_value
    return _string_list(value)


def _string_list(value: Any) -> list[str]:
    if isinstance(value, str):
        values = [value]
    elif isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        values = list(value)
    else:
        values = []
    return list(dict.fromkeys(str(item).strip() for item in values if str(item).strip()))


def _int_like(value: Any, *, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _prompt_packet_markdown(payload: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# Pseudo-Formal BlockVerifier Prompt Packets",
            "",
            f"Prompt packets: {payload.get('n_prompt_packets', 0)}",
            f"Ready packets: {payload.get('n_ok_prompt_packets', 0)}",
            f"All ok: {payload.get('all_ok', False)}",
            "",
            "These packets are independent PF/BV verifier tasks only. They are not proof evidence.",
        ]
    )


def _response_validation_markdown(payload: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# Pseudo-Formal BlockVerifier Response Validation",
            "",
            f"Responses: {payload.get('n_responses', 0)}",
            f"Valid responses: {payload.get('n_valid_responses', 0)}",
            f"Runtime learning rows: {payload.get('n_runtime_learning_rows', 0)}",
            f"All ok: {payload.get('all_ok', False)}",
            "",
            "Validated rows are PF/BV feedback only and cannot promote theorem proof claims.",
        ]
    )


def _llm_response_markdown(payload: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# Pseudo-Formal BlockVerifier LLM Responses",
            "",
            f"Provider: {payload.get('provider_name', '')}",
            f"Model: {payload.get('model', '')}",
            f"Prompt packets: {payload.get('n_prompt_packets', 0)}",
            f"Valid responses: {payload.get('n_ok_responses', 0)}",
            f"All ok: {payload.get('all_ok', False)}",
            "",
            "LLM responses are verifier feedback only. Run response validation "
            "before using them as runtime learning memory.",
        ]
    )


def _component_gate_markdown(payload: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# Pseudo-Formal BlockVerifier Component Gate",
            "",
            f"Provider: {payload.get('provider_name', '')}",
            f"Backend provider: {payload.get('backend_provider_name', '')}",
            f"Live generator: {payload.get('live_generator', False)}",
            f"Static or fixture only: {payload.get('static_or_fixture_only', False)}",
            f"Prompt packets: {payload.get('n_ok_prompt_packets', 0)}/{payload.get('n_prompt_packets', 0)}",
            f"LLM responses: {payload.get('n_ok_responses', 0)}/{payload.get('n_llm_response_rows', 0)}",
            f"Valid responses: {payload.get('n_valid_responses', 0)}",
            f"Runtime learning rows: {payload.get('n_runtime_learning_rows', 0)}",
            f"Capability evidence ok: {payload.get('capability_evidence_ok', False)}",
            f"Proof evidence status: {payload.get('proof_evidence_status', '')}",
            "",
            str(payload.get("boundary", "")),
        ]
    )
