from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Mapping

from .fingerprint import stable_hash
from .lean_candidate_identity import run_lean_candidate_identity_probe
from .lean_project import (
    LeanProjectExecutor,
    canonical_model_authored_lean_project,
)


KERNEL_PROMOTION_BOUNDARY = (
    "Promotion reruns the exact hash-bound model-authored source and support project "
    "in the configured Lean foundation after independent semantic review. It never "
    "edits source, infers imports, or selects a proof."
)


def lean_kernel_promotion_evidence_errors(
    formalization_manifest: Mapping[str, Any],
    *,
    blackboard_artifacts: Mapping[str, Mapping[str, Any]],
    expected_question_id: str = "",
    expected_formal_target_contract: Mapping[str, Any] | None = None,
) -> list[str]:
    """Validate persisted exact-target promotion evidence without rerunning Lean."""

    errors: list[str] = []
    if formalization_manifest.get("artifact_kind") != "RuntimeFormalizationManifest":
        errors.append("formalization manifest has the wrong artifact kind")
        return errors
    manifest_id = str(formalization_manifest.get("manifest_id", "") or "")
    stored_manifest = blackboard_artifacts.get(manifest_id, {})
    if not manifest_id or not isinstance(stored_manifest, Mapping):
        errors.append("formalization manifest identity is not present on the blackboard")
    elif stable_hash(stored_manifest) != stable_hash(formalization_manifest):
        errors.append("formalization manifest does not match its blackboard artifact")

    question = formalization_manifest.get("question", {})
    question = question if isinstance(question, Mapping) else {}
    question_id = str(question.get("id", "") or "")
    if expected_question_id and question_id != expected_question_id:
        errors.append("formalization manifest question identity mismatch")

    expected_contract = (
        expected_formal_target_contract
        if isinstance(expected_formal_target_contract, Mapping)
        else {}
    )
    observed_contract = question.get("formal_target_contract", {})
    observed_contract = (
        observed_contract if isinstance(observed_contract, Mapping) else {}
    )
    if expected_contract and stable_hash(observed_contract) != stable_hash(
        expected_contract
    ):
        errors.append("formalization manifest frozen target contract mismatch")

    counts = formalization_manifest.get("counts", {})
    counts = counts if isinstance(counts, Mapping) else {}
    manifest_target_ids = tuple(
        str(value or "").strip()
        for value in formalization_manifest.get(
            "source_theorem_kernel_verified_target_ids", []
        )
        or []
        if str(value or "").strip()
    )
    manifest_target_names = tuple(
        str(value or "").strip()
        for value in formalization_manifest.get(
            "source_theorem_kernel_verified_target_names", []
        )
        or []
        if str(value or "").strip()
    )
    if formalization_manifest.get("source_theorem_kernel_verified") is not True:
        errors.append("formalization manifest does not record exact kernel closure")
    try:
        verified_count = int(counts.get("source_theorem_kernel_verified", 0) or 0)
    except (TypeError, ValueError):
        verified_count = 0
    if verified_count <= 0:
        errors.append("formalization manifest has no kernel-verified theorem count")
    if (
        str(formalization_manifest.get("proof_evidence_status", "") or "")
        != "EXACT_SOURCE_THEOREM_KERNEL_VERIFIED"
    ):
        errors.append("formalization manifest proof authority is not exact kernel evidence")

    promotion_id = str(
        formalization_manifest.get("lean_kernel_promotion_id", "") or ""
    )
    promotion = blackboard_artifacts.get(promotion_id, {})
    if not promotion_id or not isinstance(promotion, Mapping):
        errors.append("formalization manifest has no bound kernel promotion artifact")
        return list(dict.fromkeys(errors))
    promotion_target_ids = tuple(
        str(value or "").strip()
        for value in promotion.get("target_ids", []) or []
        if str(value or "").strip()
    )
    if (
        promotion.get("artifact_kind") != "LeanKernelPromotionResult"
        or str(promotion.get("promotion_id", "") or "") != promotion_id
    ):
        errors.append("bound kernel promotion identity is invalid")
    if expected_question_id and str(promotion.get("question_id", "") or "") != (
        expected_question_id
    ):
        errors.append("kernel promotion question identity mismatch")
    if not manifest_target_ids or manifest_target_ids != promotion_target_ids:
        errors.append("kernel promotion target ids do not match the formalization manifest")

    expected_target_id = str(expected_contract.get("target_id", "") or "")
    expected_declaration = str(
        expected_contract.get("declaration_name", "") or ""
    )
    if expected_target_id and expected_target_id not in promotion_target_ids:
        errors.append("kernel promotion does not close the frozen target id")
    if expected_declaration and str(
        promotion.get("target_lean_declaration", "") or ""
    ) != expected_declaration:
        errors.append("kernel promotion declaration does not match the frozen target")
    if expected_declaration and manifest_target_names != (expected_declaration,):
        errors.append("formalization manifest target name does not match the frozen target")

    required_true_fields = (
        "source_theorem_kernel_verified",
        "local_lean_checked",
        "local_lean_compiled",
        "candidate_identity_lean_verified",
        "candidate_axiom_audit_clean",
        "exact_source_hash_preserved",
        "independent_semantic_review_accepted",
    )
    for field_name in required_true_fields:
        if promotion.get(field_name) is not True:
            errors.append(f"kernel promotion {field_name} is not true")
    if not str(promotion.get("candidate_source_hash", "") or ""):
        errors.append("kernel promotion has no immutable candidate source hash")
    if promotion.get("runtime_edited_source") is not False:
        errors.append("kernel promotion does not preserve model source ownership")
    if promotion.get("runtime_selected_proof") is not False:
        errors.append("kernel promotion records runtime proof selection")
    if promotion.get("blockers"):
        errors.append("kernel promotion still has blockers")
    if (
        str(promotion.get("proof_evidence_status", "") or "")
        != "EXACT_MODEL_SOURCE_KERNEL_VERIFIED"
    ):
        errors.append("kernel promotion proof authority is not exact model source")
    return list(dict.fromkeys(errors))


def evaluate_lean_kernel_promotion(
    *,
    blackboard_artifacts: Mapping[str, Mapping[str, Any]],
    environment_feedback: Mapping[str, Any],
    lean_project: Path | None,
    lean_timeout: int,
) -> dict[str, Any] | None:
    """Promote one unchanged reviewed source, or return its exact blockers."""

    if str(environment_feedback.get("overall_verdict", "") or "") != "ACCEPT":
        return None
    materialization_id = str(
        environment_feedback.get("candidate_materialization_id", "") or ""
    ).strip()
    candidate_id = str(environment_feedback.get("candidate_id", "") or "").strip()
    expected_source_hash = str(
        environment_feedback.get("candidate_source_hash", "") or ""
    ).strip()
    expected_lean_project_hash = str(
        environment_feedback.get("candidate_lean_project_hash", "") or ""
    ).strip()
    review_execution_id = str(
        environment_feedback.get("semantic_review_execution_id", "") or ""
    ).strip()
    review_packet_id = str(
        environment_feedback.get("semantic_review_packet_id", "") or ""
    ).strip()
    expected_review_packet_hash = str(
        environment_feedback.get("semantic_review_packet_hash", "") or ""
    ).strip()
    if not all(
        (
            materialization_id,
            candidate_id,
            expected_source_hash,
            review_execution_id,
            review_packet_id,
            expected_review_packet_hash,
        )
    ):
        return None

    blockers: list[str] = []
    materialization = _artifact(blackboard_artifacts, materialization_id)
    review_execution = _artifact(blackboard_artifacts, review_execution_id)
    review_packet = _artifact(blackboard_artifacts, review_packet_id)
    if materialization.get("artifact_kind") != (
        "RuntimeFormalizerLeanCandidateMaterialization"
    ):
        blockers.append("candidate materialization is missing or has the wrong kind")
    if review_execution.get("artifact_kind") != (
        "RuntimeFormalTargetSemanticReviewExecutionManifest"
    ):
        blockers.append("semantic review execution is missing or has the wrong kind")
    if stable_hash(review_packet) != expected_review_packet_hash:
        blockers.append("semantic review packet hash mismatch")
    if str(review_packet.get("overall_verdict", "") or "") != "ACCEPT":
        blockers.append("independent semantic review did not accept the target")

    execution_bindings = {
        "candidate_materialization_id": materialization_id,
        "candidate_id": candidate_id,
        "candidate_source_hash": expected_source_hash,
        "review_packet_id": review_packet_id,
        "review_packet_hash": expected_review_packet_hash,
    }
    if expected_lean_project_hash:
        execution_bindings["candidate_lean_project_hash"] = (
            expected_lean_project_hash
        )
    for key, expected in execution_bindings.items():
        if str(review_execution.get(key, "") or "") != expected:
            blockers.append(f"semantic review execution {key} mismatch")
    reviewed_project_hash = str(
        review_execution.get("candidate_lean_project_hash", "") or ""
    ).strip()
    if reviewed_project_hash != expected_lean_project_hash:
        blockers.append("semantic review execution Lean project binding mismatch")
    if review_execution.get("semantic_review_accepted") is not True:
        blockers.append("semantic review execution is not accepted")

    candidate_rows = [
        dict(row)
        for row in materialization.get("candidate_rows", []) or []
        if isinstance(row, Mapping)
        and str(row.get("candidate_id", "") or "") == candidate_id
        and str(row.get("source_hash", "") or "") == expected_source_hash
        and (
            not expected_lean_project_hash
            or str(row.get("lean_project_hash", "") or "")
            == expected_lean_project_hash
        )
    ]
    if len(candidate_rows) != 1:
        blockers.append("candidate row is not uniquely bound to the reviewed source")
        candidate: dict[str, Any] = {}
    else:
        candidate = candidate_rows[0]
    if candidate and candidate.get("source_theorem_candidate_evidence_eligible") is not True:
        blockers.append("candidate is not marked as the bound source-theorem target")

    question = (
        materialization.get("question", {})
        if isinstance(materialization.get("question", {}), Mapping)
        else {}
    )
    question_id = str(question.get("id", "") or "").strip()
    if not question_id:
        blockers.append("candidate materialization is not bound to a question")
    target_ids = list(candidate.get("target_ids", []) or [])
    if not target_ids:
        blockers.append("reviewed candidate has no immutable target id")
    source_lineage_id = str(
        candidate.get("candidate_lineage_binding_id", "") or ""
    ).strip()
    if not source_lineage_id:
        source_lineage_id = "lean_source_lineage:" + stable_hash(
            [materialization_id, candidate_id, expected_source_hash]
        )[:20]

    artifact_path_text = str(candidate.get("artifact_path", "") or "").strip()
    artifact_path = Path(artifact_path_text).expanduser() if artifact_path_text else None
    source = ""
    if artifact_path is None or not artifact_path.is_file():
        blockers.append("reviewed Lean source artifact is missing")
    else:
        try:
            source = artifact_path.read_text(encoding="utf-8")
        except OSError as exc:
            blockers.append(f"reviewed Lean source is unreadable: {exc}")
    if source and stable_hash(source) != expected_source_hash:
        blockers.append("reviewed Lean source hash mismatch")
    candidate_lean_project: dict[str, Any] = {}
    raw_candidate_lean_project = candidate.get("lean_project", {})
    project_payload_present = isinstance(raw_candidate_lean_project, Mapping) and bool(
        raw_candidate_lean_project
    )
    if source and (project_payload_present or expected_lean_project_hash):
        try:
            candidate_lean_project = canonical_model_authored_lean_project(
                raw_candidate_lean_project,
                target_source=source,
            )
        except ValueError as exc:
            blockers.append(str(exc))
        else:
            observed_project_hash = str(
                candidate_lean_project.get("project_hash", "") or ""
            )
            if observed_project_hash != expected_lean_project_hash:
                blockers.append("reviewed Lean project hash mismatch")
    declaration = str(
        candidate.get("candidate_lean_declaration", "")
        or candidate.get("target_lean_declaration", "")
        or ""
    ).strip()
    if not declaration:
        blockers.append("reviewed candidate declaration is missing")
    if lean_project is None or not Path(lean_project).exists():
        blockers.append("configured Lean project is missing")

    kernel_check: dict[str, Any] = {}
    if not blockers and artifact_path is not None:
        if candidate_lean_project:
            with TemporaryDirectory(prefix="ai-statistician-lean-promotion-") as tmp:
                kernel_check = LeanProjectExecutor(
                    active_project=Path(lean_project),
                    workspace_root=Path(tmp),
                    timeout_s=lean_timeout,
                ).check_target(
                    target_source=source,
                    candidate_lean_declaration=declaration,
                    project_files=candidate_lean_project["support_files"],
                    support_build_order=candidate_lean_project[
                        "support_build_order"
                    ],
                )
                kernel_check.pop("lean_project", None)
        else:
            kernel_check = dict(
                run_lean_candidate_identity_probe(
                    artifact_path=artifact_path,
                    candidate_lean_declaration=declaration,
                    lean_project=Path(lean_project),
                    lean_timeout=lean_timeout,
                )
            )
        if kernel_check.get("local_lean_source_compiled") is not True:
            blockers.append("exact reviewed source did not compile in local Lean")
        if kernel_check.get("candidate_identity_lean_verified") is not True:
            blockers.append("Lean did not verify the reviewed declaration identity")
        if kernel_check.get("candidate_axiom_audit_clean") is not True:
            blockers.append("reviewed declaration failed the Lean axiom audit")

    verified = not blockers
    result = {
        "schema_version": 1,
        "artifact_kind": "LeanKernelPromotionResult",
        "promotion_id": "lean_kernel_promotion:"
        + stable_hash(
            [
                materialization_id,
                candidate_id,
                expected_source_hash,
                expected_lean_project_hash,
                review_execution_id,
                kernel_check,
            ]
        )[:20],
        "candidate_materialization_id": materialization_id,
        "question_id": question_id,
        "candidate_id": candidate_id,
        "candidate_source_hash": expected_source_hash,
        "candidate_lean_project_hash": expected_lean_project_hash,
        "candidate_artifact_path": artifact_path_text,
        "target_lean_declaration": declaration,
        "target_ids": target_ids,
        "source_lineage_id": source_lineage_id,
        "semantic_review_execution_id": review_execution_id,
        "semantic_review_packet_id": review_packet_id,
        "semantic_review_packet_hash": expected_review_packet_hash,
        "source_theorem_kernel_verified": verified,
        "local_lean_checked": bool(kernel_check.get("local_lean_attempted", False)),
        "local_lean_compiled": bool(
            kernel_check.get("local_lean_compiled", False)
        ),
        "candidate_identity_lean_verified": bool(
            kernel_check.get("candidate_identity_lean_verified", False)
        ),
        "candidate_axiom_audit_clean": bool(
            kernel_check.get("candidate_axiom_audit_clean", False)
        ),
        "exact_source_hash_preserved": bool(
            source and stable_hash(source) == expected_source_hash
        ),
        "exact_lean_project_hash_preserved": bool(
            not expected_lean_project_hash
            or str(candidate_lean_project.get("project_hash", "") or "")
            == expected_lean_project_hash
        ),
        "independent_semantic_review_accepted": bool(
            review_execution.get("semantic_review_accepted") is True
        ),
        "kernel_check": kernel_check,
        "blockers": blockers,
        "runtime_edited_source": False,
        "runtime_selected_proof": False,
        "proof_evidence_status": (
            "EXACT_MODEL_SOURCE_KERNEL_VERIFIED"
            if verified
            else "LEAN_KERNEL_PROMOTION_BLOCKED"
        ),
        "proof_evidence_boundary": KERNEL_PROMOTION_BOUNDARY,
    }
    return result


def _artifact(
    artifacts: Mapping[str, Mapping[str, Any]], artifact_id: str
) -> dict[str, Any]:
    value = artifacts.get(artifact_id, {})
    return dict(value) if isinstance(value, Mapping) else {}
