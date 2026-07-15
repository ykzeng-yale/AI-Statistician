from __future__ import annotations

from typing import Any, Mapping

from .fingerprint import stable_hash


TYPED_REPAIR_HANDOFF_KIND = "architect_pre_authorized_typed_repair_backedge"


def build_typed_repair_handoff_contract(
    *,
    source_reviewer_subsystem: str,
    source_task_id: str,
    target_repair_subsystem: str,
    target_task_id: str,
    feedback_artifact_id: str,
    feedback_artifact_kind: str,
    feedback_execution_id: str,
    feedback_execution_artifact_kind: str,
    feedback_type: str,
    revision_count: int,
    max_revisions: int,
) -> dict[str, Any]:
    contract: dict[str, Any] = {
        "schema_version": 1,
        "contract_kind": TYPED_REPAIR_HANDOFF_KIND,
        "architect_pre_authorized": True,
        "source_reviewer_subsystem": source_reviewer_subsystem,
        "source_task_id": source_task_id,
        "target_repair_subsystem": target_repair_subsystem,
        "target_task_id": target_task_id,
        "feedback_artifact_id": feedback_artifact_id,
        "feedback_artifact_kind": feedback_artifact_kind,
        "feedback_execution_id": feedback_execution_id,
        "feedback_execution_artifact_kind": feedback_execution_artifact_kind,
        "feedback_type": feedback_type,
        "revision_count": max(0, int(revision_count or 0)),
        "max_revisions": max(0, int(max_revisions or 0)),
        "proof_evidence_status": "NOT_PROOF_EVIDENCE",
    }
    contract["contract_fingerprint"] = stable_hash(contract)
    return contract


def typed_repair_handoff_contract_errors(
    contract: Mapping[str, Any] | None,
    *,
    source_reviewer_subsystem: str,
    source_task_id: str,
    target_repair_subsystem: str,
    target_task_id: str,
    environment_feedback: Mapping[str, Any] | None,
    produced_artifacts: Mapping[str, Mapping[str, Any]] | None,
) -> list[str]:
    if not isinstance(contract, Mapping) or not contract:
        return ["typed repair handoff contract missing"]
    errors: list[str] = []
    expected_scalars = {
        "contract_kind": TYPED_REPAIR_HANDOFF_KIND,
        "source_reviewer_subsystem": source_reviewer_subsystem,
        "source_task_id": source_task_id,
        "target_repair_subsystem": target_repair_subsystem,
        "target_task_id": target_task_id,
        "proof_evidence_status": "NOT_PROOF_EVIDENCE",
    }
    for field, expected in expected_scalars.items():
        if str(contract.get(field, "") or "") != expected:
            errors.append(f"typed repair handoff {field} mismatch")
    if contract.get("architect_pre_authorized") is not True:
        errors.append("typed repair handoff is not Architect pre-authorized")

    revision_count = _safe_int(contract.get("revision_count", 0))
    max_revisions = _safe_int(contract.get("max_revisions", 0))
    if revision_count <= 0 or revision_count > max_revisions:
        errors.append("typed repair handoff revision budget is invalid")

    contract_without_fingerprint = {
        key: value
        for key, value in contract.items()
        if key != "contract_fingerprint"
    }
    if str(contract.get("contract_fingerprint", "") or "") != stable_hash(
        contract_without_fingerprint
    ):
        errors.append("typed repair handoff fingerprint mismatch")

    feedback = environment_feedback if isinstance(environment_feedback, Mapping) else {}
    feedback_type = str(contract.get("feedback_type", "") or "")
    if str(feedback.get("feedback_type", "") or "") != feedback_type:
        errors.append("typed repair handoff feedback_type mismatch")
    packet_id = str(contract.get("feedback_artifact_id", "") or "")
    execution_id = str(contract.get("feedback_execution_id", "") or "")
    if str(feedback.get("semantic_review_packet_id", "") or "") != packet_id:
        errors.append("typed repair handoff review packet lineage mismatch")
    if str(feedback.get("semantic_review_execution_id", "") or "") != execution_id:
        errors.append("typed repair handoff review execution lineage mismatch")

    artifacts = produced_artifacts if isinstance(produced_artifacts, Mapping) else {}
    _validate_artifact(
        errors,
        artifacts=artifacts,
        artifact_id=packet_id,
        expected_kind=str(contract.get("feedback_artifact_kind", "") or ""),
        label="review packet",
    )
    _validate_artifact(
        errors,
        artifacts=artifacts,
        artifact_id=execution_id,
        expected_kind=str(
            contract.get("feedback_execution_artifact_kind", "") or ""
        ),
        label="review execution",
    )
    return sorted(set(errors))


def _validate_artifact(
    errors: list[str],
    *,
    artifacts: Mapping[str, Mapping[str, Any]],
    artifact_id: str,
    expected_kind: str,
    label: str,
) -> None:
    artifact = artifacts.get(artifact_id, {})
    if not artifact_id or not isinstance(artifact, Mapping) or not artifact:
        errors.append(f"typed repair handoff {label} artifact missing")
        return
    if str(artifact.get("artifact_kind", "") or "") != expected_kind:
        errors.append(f"typed repair handoff {label} artifact kind mismatch")


def _safe_int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0
