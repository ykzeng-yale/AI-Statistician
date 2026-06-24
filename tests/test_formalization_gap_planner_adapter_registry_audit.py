from __future__ import annotations

import json
import shutil
from pathlib import Path

from ai_statistician.formalization_gap_planner_adapter_registry import (
    adapter_registry_row_json_schema,
    export_formalization_gap_planner_adapter_registry,
)
from ai_statistician.formalization_gap_planner_component_resource_registry import (
    PORTABLE_REUSE_TARGETS,
)
from ai_statistician.formalization_gap_planner_adapter_registry_audit import (
    audit_formalization_gap_planner_adapter_registry,
)


def test_adapter_registry_audit_validates_frontier_tool_contracts() -> None:
    root = Path("runs/test_formalization_gap_planner_adapter_registry_audit")
    registry_dir = root / "registry"
    audit_dir = root / "audit"
    reject_dir = root / "reject"
    lean_rag_db = root / "stat_inference.sqlite"
    paper_dir = root / "papers"
    shutil.rmtree(root, ignore_errors=True)
    lean_rag_db.parent.mkdir(parents=True, exist_ok=True)
    paper_dir.mkdir(parents=True, exist_ok=True)
    lean_rag_db.write_text("", encoding="utf-8")

    registry_payload = export_formalization_gap_planner_adapter_registry(
        registry_dir,
        lean_rag_db_path=lean_rag_db,
        paper_library_dir=paper_dir,
    )
    audit_payload = audit_formalization_gap_planner_adapter_registry(
        registry_dir,
        audit_dir,
    )

    assert registry_payload["all_ok"]
    assert audit_payload["all_ok"]
    assert audit_payload["n_failed"] == 0
    assert registry_payload["n_adapter_row_schema_valid"] == registry_payload["n_adapters"]
    assert registry_payload["n_adapter_row_schema_invalid"] == 0
    assert audit_payload["n_adapter_row_schema_valid"] == audit_payload["n_registry_rows"]
    assert audit_payload["n_adapter_row_schema_invalid"] == 0
    assert audit_payload["n_adapter_jsonl_row_schema_valid"] == audit_payload["n_registry_jsonl_rows"]
    assert audit_payload["n_adapter_jsonl_row_schema_invalid"] == 0
    assert audit_payload["n_required_adapter_ids_present"] == audit_payload["n_required_adapter_ids"]
    assert audit_payload["n_required_component_kinds_present"] >= 6
    assert audit_payload["n_required_hook_kinds_present"] >= 5
    assert audit_payload["n_mcp_or_cli_surfaces"] > 0
    assert set(
        audit_payload["target_coverage_by_hook_kind"]["formal_library_grounding"]
    ) == set(PORTABLE_REUSE_TARGETS)
    assert set(
        audit_payload["target_coverage_by_hook_kind"]["proof_state_feedback"]
    ) == set(PORTABLE_REUSE_TARGETS)
    assert set(
        audit_payload["target_specific_coverage_by_hook_kind"][
            "proof_state_feedback"
        ]
    ) == set(PORTABLE_REUSE_TARGETS)
    assert any(
        check["check_name"] == "required_adapter_ids" and check["ok"]
        for check in audit_payload["checks"]
    )
    assert any(
        check["check_name"] == "formal_library_grounding_targets_covered"
        and check["ok"]
        for check in audit_payload["checks"]
    )
    assert any(
        check["check_name"] == "proof_state_feedback_targets_covered"
        and check["ok"]
        for check in audit_payload["checks"]
    )
    assert any(
        check["check_name"]
        == "target_specific_proof_state_feedback_targets_covered"
        and check["ok"]
        for check in audit_payload["checks"]
    )
    assert any(
        check["check_name"].endswith("_lean_alias_target_scope") and check["ok"]
        for check in audit_payload["checks"]
    )
    assert any(
        check["check_name"].endswith("_no_kernel_claim_field") and check["ok"]
        for check in audit_payload["checks"]
    )
    assert any(
        check["check_name"] == "adapter_registry_row_schema_id" and check["ok"]
        for check in audit_payload["checks"]
    )
    assert "not theorem proof evidence" in audit_payload["proof_evidence_boundary"]
    assert json.loads(
        (
            registry_dir / "formalization_gap_planner_adapter_registry_row.schema.json"
        ).read_text(encoding="utf-8")
    )["$id"] == adapter_registry_row_json_schema()["$id"]
    assert (
        audit_dir
        / "formalization_gap_planner_adapter_registry_audit_manifest.json"
    ).exists()

    manifest_path = registry_dir / "formalization_gap_planner_adapter_registry_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["rows"] = [
        row
        for row in manifest["rows"]
        if row.get("adapter_id") != "paperclip_cli_mcp"
    ]
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    rejected = audit_formalization_gap_planner_adapter_registry(
        registry_dir,
        reject_dir,
    )

    assert not rejected["all_ok"]
    failed = {
        check["check_name"]
        for check in rejected["checks"]
        if not check["ok"]
    }
    assert "required_adapter_ids" in failed

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["rows"] = [
        row
        for row in manifest["rows"]
        if row.get("adapter_id")
        not in {"rocq_lsp_serapi", "isabelle_sledgehammer_afp", "agda_search_auto"}
    ]
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    rejected_targets = audit_formalization_gap_planner_adapter_registry(
        registry_dir,
        root / "reject_targets",
    )

    assert not rejected_targets["all_ok"]
    target_failed = {
        check["check_name"]
        for check in rejected_targets["checks"]
        if not check["ok"]
    }
    assert "target_specific_proof_state_feedback_targets_covered" in target_failed
