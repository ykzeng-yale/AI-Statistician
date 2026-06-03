from __future__ import annotations

from pathlib import Path

from ai_statistician.formalization_gap_planner_adapter_registry import (
    export_formalization_gap_planner_adapter_registry,
)


def test_formalization_gap_planner_adapter_registry_exports_contracts() -> None:
    root = Path("runs/test_formalization_gap_planner_adapter_registry")
    lean_rag_db = root / "stat_inference.sqlite"
    paper_dir = root / "papers"
    lean_rag_db.parent.mkdir(parents=True, exist_ok=True)
    paper_dir.mkdir(parents=True, exist_ok=True)
    lean_rag_db.write_text("", encoding="utf-8")

    payload = export_formalization_gap_planner_adapter_registry(
        root / "registry",
        lean_rag_db_path=lean_rag_db,
        paper_library_dir=paper_dir,
    )

    assert payload["all_ok"]
    assert payload["n_adapters"] >= 10
    assert payload["n_ready_local_or_configured"] >= 3
    adapter_ids = {row["adapter_id"] for row in payload["rows"]}
    assert "local_route_truth_benchmark_adapter" in adapter_ids
    assert "paperclip_cli_mcp" in adapter_ids
    assert "local_formal_source_index" in adapter_ids
    assert "local_lean_rag_dependency_graph" in adapter_ids
    assert "lean_lsp_mcp" in adapter_ids
    assert "route_revision_overlay" in adapter_ids
    by_id = {row["adapter_id"]: row for row in payload["rows"]}
    assert by_id["local_route_truth_benchmark_adapter"]["readiness_status"] == "READY_LOCAL"
    assert by_id["route_revision_overlay"]["readiness_status"] == "READY_LOCAL"
    assert by_id["local_lean_rag_dependency_graph"]["detected_paths"][str(lean_rag_db)]
    assert by_id["paperqa2_local_library"]["detected_paths"][str(paper_dir)]
    assert "source_refs" in by_id["paperclip_cli_mcp"]["output_contract_fields"]
    assert "lean_declaration_hits" in by_id["local_formal_source_index"]["output_contract_fields"]
    assert "prover_diagnostics" in by_id["lean_lsp_mcp"]["output_contract_fields"]
    assert "not theorem proof evidence" in payload["proof_evidence_boundary"]
    assert (
        root
        / "registry"
        / "formalization_gap_planner_adapter_registry_manifest.json"
    ).exists()
