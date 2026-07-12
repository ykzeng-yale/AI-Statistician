from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping

from .fingerprint import stable_hash


ARTIFACT_KIND = "RuntimeLeanProofRepairTrajectory"
SCHEMA_VERSION = 1
CODEXPROVER_PROTOCOL = "codex_prover_lean_tool_use_protocol_v1"
BOUNDARY = (
    "Proof-repair trajectories record candidate generation, diagnostics, tool "
    "health, and exact-checker lineage. Provider, RAG, MCP, LSP, failed-attempt, "
    "and trajectory artifacts are not proof authority. Only the bound local "
    "Lean/AXLE exact-checker manifest may verify the source theorem."
)


def build_runtime_lean_proof_repair_trajectory(
    *,
    work_order: Mapping[str, Any],
    provider_result: Mapping[str, Any],
    exact_result: Mapping[str, Any] | None,
    lean_project: str = "",
) -> dict[str, Any]:
    request = _mapping(work_order.get("request", {}))
    provider = dict(provider_result)
    exact = dict(exact_result) if isinstance(exact_result, Mapping) else {}
    request_fingerprint = str(request.get("request_fingerprint", "") or "")
    target_declaration = str(
        request.get("target_lean_declaration", "") or ""
    )
    statement = str(request.get("target_theorem_statement", "") or "")
    statement_hash = str(
        request.get("target_theorem_statement_hash", "")
        or (stable_hash(statement) if statement else "")
    )
    work_order_hash = stable_hash(dict(work_order))
    provider_result_hash = stable_hash(provider)
    exact_result_hash = stable_hash(exact) if exact else ""
    exact_verified = bool(
        exact
        and exact.get("runtime_verification_contract_satisfied", False)
        and _int(exact.get("n_source_theorem_kernel_verified", 0)) > 0
    )
    attempts = [_provider_attempt(provider, statement_hash=statement_hash)]
    attempts.extend(
        _exact_attempt(
            row,
            index=index,
            statement_hash=statement_hash,
            exact_manifest_authoritative=exact_verified,
        )
        for index, row in enumerate(exact.get("rows", []) or [], start=1)
        if isinstance(row, Mapping)
    )
    exact_manifest_path = str(
        exact.get("manifest_path", "")
        or exact.get("manifest_id", "")
        or "PENDING_EXACT_CHECKER"
    )
    provider_descriptor = _mapping(provider.get("provider_descriptor", {}))
    tool_health_events = _tool_health_events(provider, exact)
    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "artifact_kind": ARTIFACT_KIND,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "protocol_source": {
            "repository": "ykzeng-yale/CodexProver",
            "protocol_id": CODEXPROVER_PROTOCOL,
            "proof_repair_schema": (
                "proof_repair_trajectory_manifest.schema.json"
            ),
            "reuse_mode": "typed runtime adaptation; no heuristic source editor",
        },
        "question_id": str(work_order.get("question_id", "") or ""),
        "theorem_or_claim_id": target_declaration,
        "lean_project_path": str(lean_project or ""),
        "work_order_id": str(work_order.get("work_order_id", "") or ""),
        "work_order_hash": work_order_hash,
        "request_fingerprint": request_fingerprint,
        "target_theorem_statement_hash": statement_hash,
        "provider": str(provider.get("provider", "") or ""),
        "provider_descriptor": provider_descriptor,
        "provider_result_id": str(provider.get("result_id", "") or ""),
        "provider_result_hash": provider_result_hash,
        "exact_candidate_rerun_manifest_id": str(
            exact.get("manifest_id", "") or ""
        ),
        "exact_candidate_rerun_manifest_hash": exact_result_hash,
        "candidate_lineage": {
            "source_lineage_id": str(request.get("source_lineage_id", "") or ""),
            "source_work_order_id": str(
                request.get("source_work_order_id", "") or ""
            ),
            "execution_queue_id": str(
                request.get("execution_queue_id", "") or ""
            ),
            "source_candidate_artifact_path": str(
                request.get("lineage_candidate_artifact_path", "") or ""
            ),
            "source_candidate_artifact_hash": str(
                request.get("lineage_candidate_artifact_hash", "") or ""
            ),
            "statement_header_changed": False,
            "assumptions_strengthened": False,
        },
        "repair_attempts": attempts,
        "tool_health_events": tool_health_events,
        "guidance_evidence": {
            "mcp_or_lsp_guidance_used": bool(
                provider.get("mcp_guidance_manifest")
                or provider.get("lean_lsp_feedback")
            ),
            "mcp_guidance_manifest": str(
                provider.get("mcp_guidance_manifest", "") or ""
            ),
            "diagnostics_recorded": any(
                bool(attempt.get("diagnostics")) for attempt in attempts
            ),
            "goal_state_recorded": bool(
                provider.get("goal_state") or provider.get("openprover_summary")
            ),
            "search_or_retrieval_recorded": True,
            "provider_output_can_verify": False,
        },
        "final_exact_checker_manifest": {
            "required": True,
            "available": bool(exact),
            "path": exact_manifest_path,
            "artifact_hash": exact_result_hash,
            "success": exact_verified,
            "sorry_free": bool(exact_verified),
            "mcp_output_can_verify": False,
        },
        "extracted_lessons": [
            {
                "lesson_type": (
                    "exact_checker_success"
                    if exact_verified
                    else _dominant_failure_class(attempts)
                ),
                "public_safe": True,
                "reusable_pattern": (
                    "preserve the exact statement, bind every candidate and "
                    "diagnostic by hash, and return failed checks to the coding agent"
                ),
                "memory_action": (
                    "promote exact-checked proof body and dependency lineage"
                    if exact_verified
                    else "retain as non-proof repair feedback"
                ),
            }
        ],
        "authority_boundary": {
            "exact_checker_manifest_is_authority": True,
            "provider_output_can_verify": False,
            "mcp_output_can_verify": False,
            "failed_attempts_can_verify": False,
            "tool_health_events_can_verify": False,
            "retrieval_can_verify": False,
            "hidden_answers_used_for_generation": False,
        },
        "promotion": {
            "source_theorem_kernel_verified": exact_verified,
            "full_ai_statistician_ready": False,
            "update_goal_allowed": False,
        },
        "proof_evidence_status": (
            "TRAJECTORY_BOUND_EXACT_CHECKER_SUCCESS"
            if exact_verified
            else "PROOF_REPAIR_TRAJECTORY_NOT_PROOF_EVIDENCE"
        ),
        "proof_evidence_boundary": BOUNDARY,
    }
    fingerprint = stable_hash(payload)
    payload["trajectory_fingerprint"] = fingerprint
    payload["trajectory_id"] = "lean_proof_repair_trajectory:" + fingerprint[:20]
    return payload


def validate_runtime_lean_proof_repair_trajectory(
    trajectory: Mapping[str, Any],
    *,
    work_order: Mapping[str, Any],
    provider_result: Mapping[str, Any],
    exact_result: Mapping[str, Any] | None,
) -> tuple[str, ...]:
    payload = dict(trajectory)
    errors: list[str] = []
    if payload.get("artifact_kind") != ARTIFACT_KIND:
        errors.append("trajectory artifact_kind mismatch")
    fingerprint = str(payload.get("trajectory_fingerprint", "") or "")
    fingerprint_payload = dict(payload)
    fingerprint_payload.pop("trajectory_id", None)
    fingerprint_payload.pop("trajectory_fingerprint", None)
    # Architect control is attached by AgentRuntime after the immutable
    # trajectory is built. It is orchestration metadata, not trajectory input.
    fingerprint_payload.pop("runtime_architect_control", None)
    if not fingerprint or stable_hash(fingerprint_payload) != fingerprint:
        errors.append("trajectory fingerprint mismatch")
    if str(payload.get("trajectory_id", "") or "") != (
        "lean_proof_repair_trajectory:" + fingerprint[:20]
    ):
        errors.append("trajectory identity mismatch")
    if str(payload.get("work_order_hash", "") or "") != stable_hash(
        dict(work_order)
    ):
        errors.append("trajectory work-order hash mismatch")
    if str(payload.get("work_order_id", "") or "") != str(
        work_order.get("work_order_id", "") or ""
    ):
        errors.append("trajectory work-order identity mismatch")
    if str(payload.get("question_id", "") or "") != str(
        work_order.get("question_id", "") or ""
    ):
        errors.append("trajectory question identity mismatch")
    request = _mapping(work_order.get("request", {}))
    if str(payload.get("request_fingerprint", "") or "") != str(
        request.get("request_fingerprint", "") or ""
    ):
        errors.append("trajectory request fingerprint mismatch")
    statement = str(request.get("target_theorem_statement", "") or "")
    recorded_statement_hash = str(
        request.get("target_theorem_statement_hash", "") or ""
    )
    computed_statement_hash = stable_hash(statement) if statement else ""
    if (
        recorded_statement_hash
        and computed_statement_hash
        and recorded_statement_hash != computed_statement_hash
    ):
        errors.append("work-order target theorem statement hash mismatch")
    expected_statement_hash = recorded_statement_hash or computed_statement_hash
    if str(payload.get("target_theorem_statement_hash", "") or "") != (
        expected_statement_hash
    ):
        errors.append("trajectory target theorem statement hash mismatch")
    if str(payload.get("provider_result_hash", "") or "") != stable_hash(
        dict(provider_result)
    ):
        errors.append("trajectory provider-result hash mismatch")
    if str(payload.get("provider_result_id", "") or "") != str(
        provider_result.get("result_id", "") or ""
    ):
        errors.append("trajectory provider-result identity mismatch")
    exact = dict(exact_result) if isinstance(exact_result, Mapping) else {}
    expected_exact_hash = stable_hash(exact) if exact else ""
    if str(payload.get("exact_candidate_rerun_manifest_hash", "") or "") != (
        expected_exact_hash
    ):
        errors.append("trajectory exact-checker hash mismatch")
    if str(payload.get("exact_candidate_rerun_manifest_id", "") or "") != str(
        exact.get("manifest_id", "") or ""
    ):
        errors.append("trajectory exact-checker identity mismatch")
    exact_verified = bool(
        exact
        and exact.get("runtime_verification_contract_satisfied", False)
        and _int(exact.get("n_source_theorem_kernel_verified", 0)) > 0
    )
    promotion = _mapping(payload.get("promotion", {}))
    final_checker = _mapping(payload.get("final_exact_checker_manifest", {}))
    if bool(promotion.get("source_theorem_kernel_verified", False)) != exact_verified:
        errors.append("trajectory proof promotion mismatch")
    if bool(final_checker.get("success", False)) != exact_verified:
        errors.append("trajectory exact-checker success mismatch")
    authority = _mapping(payload.get("authority_boundary", {}))
    for key in (
        "provider_output_can_verify",
        "mcp_output_can_verify",
        "failed_attempts_can_verify",
        "tool_health_events_can_verify",
        "retrieval_can_verify",
        "hidden_answers_used_for_generation",
    ):
        if authority.get(key) is not False:
            errors.append(f"trajectory authority boundary {key} must be false")
    if authority.get("exact_checker_manifest_is_authority") is not True:
        errors.append("trajectory exact checker is not authoritative")
    attempts = payload.get("repair_attempts", [])
    if not isinstance(attempts, list) or not attempts:
        errors.append("trajectory repair_attempts missing")
    if exact_verified and not any(
        isinstance(row, Mapping) and row.get("proof_authority") is True
        for row in attempts or []
    ):
        errors.append("trajectory verified proof has no authoritative attempt")
    if not exact_verified and any(
        isinstance(row, Mapping) and row.get("proof_authority") is True
        for row in attempts or []
    ):
        errors.append("trajectory failed proof has an authoritative attempt")
    return tuple(dict.fromkeys(errors))


def _provider_attempt(
    provider: Mapping[str, Any],
    *,
    statement_hash: str,
) -> dict[str, Any]:
    bodies = [
        str(value)
        for value in provider.get("source_theorem_candidate_proof_bodies", []) or []
        if str(value).strip()
    ]
    status = str(provider.get("status", "") or "")
    diagnostics = [
        str(value)
        for value in provider.get("failure_feedback", []) or []
        if str(value).strip()
    ]
    if provider.get("error"):
        diagnostics.append(str(provider.get("error")))
    return {
        "attempt_id": str(provider.get("result_id", "") or "provider_attempt"),
        "attempt_kind": "external_coding_agent_proof_search",
        "status": "success" if bodies else "failed" if status == "PROVIDER_ERROR" else "blocked",
        "failure_class": "search_or_retrieval" if not bodies else "candidate_generated",
        "statement_preserved": True,
        "target_theorem_statement_hash": statement_hash,
        "candidate_proof_body_hashes": [stable_hash(body) for body in bodies],
        "diagnostics": diagnostics,
        "proof_authority": False,
    }


def _exact_attempt(
    row: Mapping[str, Any],
    *,
    index: int,
    statement_hash: str,
    exact_manifest_authoritative: bool,
) -> dict[str, Any]:
    diagnostics = [
        str(value)
        for value in (
            row.get("runtime_owned_local_lean_diagnostics", [])
            or row.get("diagnostics", [])
            or []
        )
        if str(value).strip()
    ]
    verified = bool(
        exact_manifest_authoritative
        and row.get("source_theorem_kernel_verified", False)
        and row.get("runtime_owned_local_lean_compiled", False)
    )
    return {
        "attempt_id": str(
            row.get("candidate_id", "")
            or row.get("candidate_artifact_path", "")
            or f"exact_candidate_{index}"
        ),
        "attempt_kind": "runtime_owned_exact_checker",
        "status": "success" if verified else "failed",
        "failure_class": "exact_checker_success" if verified else _failure_class(diagnostics),
        "statement_preserved": bool(row.get("exact_signature_preserved", False)),
        "target_theorem_statement_hash": statement_hash,
        "candidate_proof_body_hash": str(
            row.get("candidate_proof_body_hash", "") or ""
        ),
        "candidate_artifact_path": str(
            row.get("candidate_artifact_path", "") or ""
        ),
        "candidate_artifact_hash": str(
            row.get("candidate_artifact_hash", "") or ""
        ),
        "diagnostics": diagnostics,
        "proof_authority": verified,
    }


def _tool_health_events(
    provider: Mapping[str, Any],
    exact: Mapping[str, Any],
) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    if str(provider.get("status", "") or "") == "PROVIDER_ERROR":
        events.append(
            {
                "event_type": "proof_search_provider",
                "status": "failed",
                "summary": str(provider.get("error", "") or "provider error"),
                "proof_authority": False,
            }
        )
    if exact:
        events.append(
            {
                "event_type": "checker_environment",
                "status": (
                    "success"
                    if exact.get("runtime_verification_contract_satisfied", False)
                    else "failed"
                ),
                "summary": "; ".join(
                    str(value)
                    for value in exact.get(
                        "runtime_verification_contract_errors", []
                    )
                    or []
                )[:1000],
                "proof_authority": False,
            }
        )
    return events


def _failure_class(diagnostics: list[str]) -> str:
    text = "\n".join(diagnostics).lower()
    if "timeout" in text or "timed out" in text:
        return "timeout"
    if "unknown module" in text or ".olean" in text:
        return "cache_or_import_frontier"
    if "type mismatch" in text or "unknown identifier" in text:
        return "type_error"
    if "unsolved goals" in text or "tactic" in text:
        return "tactic_failure"
    return "other"


def _dominant_failure_class(attempts: list[dict[str, Any]]) -> str:
    for attempt in reversed(attempts):
        failure = str(attempt.get("failure_class", "") or "")
        if failure and failure not in {"candidate_generated", "exact_checker_success"}:
            return failure
    return "proof_search_incomplete"


def _mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0
