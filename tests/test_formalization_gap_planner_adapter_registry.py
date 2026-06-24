from __future__ import annotations

from pathlib import Path

from ai_statistician.formalization_gap_planner_adapter_registry import (
    adapter_registry_row_json_schema,
    export_formalization_gap_planner_adapter_registry,
)
from ai_statistician.formalization_gap_planner_component_resource_registry import (
    PORTABLE_REUSE_TARGETS,
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
    assert payload["n_adapter_row_schema_valid"] == payload["n_adapters"]
    assert payload["n_adapter_row_schema_invalid"] == 0
    assert payload["adapter_row_schema"]["$id"] == adapter_registry_row_json_schema()["$id"]
    assert payload["n_ready_local_or_configured"] >= 3
    adapter_ids = {row["adapter_id"] for row in payload["rows"]}
    assert "local_route_truth_benchmark_adapter" in adapter_ids
    assert "local_literature_corpus" in adapter_ids
    assert "paperclip_cli_mcp" in adapter_ids
    assert "local_formal_source_index" in adapter_ids
    assert "local_target_formal_source_index" in adapter_ids
    assert "local_lean_rag_dependency_graph" in adapter_ids
    assert "lean_lsp_mcp" in adapter_ids
    assert "rocq_lsp_serapi" in adapter_ids
    assert "isabelle_sledgehammer_afp" in adapter_ids
    assert "agda_search_auto" in adapter_ids
    assert "hol4_tactic_kernel_tools" in adapter_ids
    assert "hol_light_tactic_search" in adapter_ids
    assert "mizar_mml_search" in adapter_ids
    assert "metamath_set_mm" in adapter_ids
    assert "route_revision_overlay" in adapter_ids
    by_id = {row["adapter_id"]: row for row in payload["rows"]}
    assert by_id["local_route_truth_benchmark_adapter"]["readiness_status"] == "READY_LOCAL"
    assert by_id["route_revision_overlay"]["readiness_status"] == "READY_LOCAL"
    assert by_id["local_lean_rag_dependency_graph"]["detected_paths"][str(lean_rag_db)]
    assert by_id["local_literature_corpus"]["detected_paths"][str(paper_dir)]
    assert by_id["paperqa2_local_library"]["detected_paths"][str(paper_dir)]
    assert "source_refs" in by_id["paperclip_cli_mcp"]["output_contract_fields"]
    assert "route_evidence_nodes" in by_id["local_literature_corpus"]["output_contract_fields"]
    assert "formal_declaration_hits" in by_id["local_formal_source_index"][
        "output_contract_fields"
    ]
    assert "lean_declaration_hits" in by_id["local_formal_source_index"]["output_contract_fields"]
    assert by_id["local_formal_source_index"]["portable_to_prover_families"] == (
        "lean4",
    )
    assert set(
        by_id["local_target_formal_source_index"]["portable_to_prover_families"]
    ) == set(PORTABLE_REUSE_TARGETS)
    assert "formal_declaration_hits" in by_id["local_target_formal_source_index"][
        "output_contract_fields"
    ]
    assert (
        "lean_declaration_hits"
        not in by_id["local_target_formal_source_index"]["output_contract_fields"]
    )
    assert "prover_diagnostics" in by_id["lean_lsp_mcp"]["output_contract_fields"]
    assert by_id["lean_lsp_mcp"]["portable_to_prover_families"] == ("lean4",)
    assert by_id["rocq_lsp_serapi"]["portable_to_prover_families"] == ("rocq",)
    assert by_id["isabelle_sledgehammer_afp"]["portable_to_prover_families"] == (
        "isabelle",
    )
    assert by_id["agda_search_auto"]["portable_to_prover_families"] == ("agda",)
    assert by_id["hol4_tactic_kernel_tools"]["portable_to_prover_families"] == (
        "hol4",
    )
    assert by_id["hol_light_tactic_search"]["portable_to_prover_families"] == (
        "hol_light",
    )
    assert by_id["mizar_mml_search"]["portable_to_prover_families"] == ("mizar",)
    assert by_id["metamath_set_mm"]["portable_to_prover_families"] == (
        "metamath",
    )
    for adapter_id in (
        "rocq_lsp_serapi",
        "isabelle_sledgehammer_afp",
        "agda_search_auto",
        "hol4_tactic_kernel_tools",
        "hol_light_tactic_search",
        "mizar_mml_search",
        "metamath_set_mm",
    ):
        assert "prover_diagnostics" in by_id[adapter_id]["output_contract_fields"]
        assert "formal_declaration_hits" in by_id[adapter_id]["output_contract_fields"]
        assert "lean_declaration_hits" not in by_id[adapter_id]["output_contract_fields"]
    assert "revised_formal_realization_dag_nodes" in by_id[
        "route_revision_overlay"
    ]["output_contract_fields"]
    assert "revised_lean_realization_dag_nodes" in by_id[
        "route_revision_overlay"
    ]["output_contract_fields"]
    assert "not theorem proof evidence" in payload["proof_evidence_boundary"]
    assert (
        root
        / "registry"
        / "formalization_gap_planner_adapter_registry_manifest.json"
    ).exists()
    assert (
        root
        / "registry"
        / "formalization_gap_planner_adapter_registry_row.schema.json"
    ).exists()
