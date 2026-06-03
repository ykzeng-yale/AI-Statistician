from __future__ import annotations

import importlib.util
import json
import os
import shutil
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash
from .formalization_gap_planner_benchmark import (
    default_formalization_gap_planner_ground_truth_path,
)


FORMALIZATION_GAP_PLANNER_ADAPTER_REGISTRY_SCHEMA_VERSION = 1
PROOF_EVIDENCE_STATUS = "FORMALIZATION_GAP_PLANNER_ADAPTER_REGISTRY_NOT_PROOF_EVIDENCE"
PROOF_EVIDENCE_BOUNDARY = (
    "Formalization gap planner adapter registry rows describe tool readiness "
    "and response contracts. They are not theorem proof evidence. Only a "
    "target-prover kernel check can prove a theorem or bridge lemma."
)


@dataclass(frozen=True)
class FormalizationGapPlannerAdapterRegistryRow:
    schema_version: int
    adapter_id: str
    adapter_name: str
    component_kind: str
    hook_kind: str
    evidence_kind: str
    adapter_surface: str
    role: str
    output_contract_fields: tuple[str, ...]
    required_commands: tuple[str, ...]
    required_python_packages: tuple[str, ...]
    required_env_vars: tuple[str, ...]
    optional_paths: tuple[str, ...]
    detected_commands: dict[str, bool]
    detected_python_packages: dict[str, bool]
    detected_env_vars: dict[str, bool]
    detected_paths: dict[str, bool]
    readiness_status: str
    readiness_reasons: tuple[str, ...]
    install_hint: str
    resource_urls: tuple[str, ...]
    online_dependency: bool
    portable_to_prover_families: tuple[str, ...]
    response_contract_boundary: str
    proof_evidence_status: str
    proof_evidence_boundary: str
    ok: bool
    errors: tuple[str, ...] = ()


def export_formalization_gap_planner_adapter_registry(
    out_dir: Path | None = None,
    *,
    lean_rag_db_path: Path | None = None,
    paper_library_dir: Path | None = None,
) -> dict[str, object]:
    """Export the frontier adapter registry for refinement-loop integrations."""

    adapter_specs = _adapter_specs(
        lean_rag_db_path=lean_rag_db_path,
        paper_library_dir=paper_library_dir,
    )
    rows = tuple(_registry_row(spec) for spec in adapter_specs)
    by_component = Counter(row.component_kind for row in rows)
    by_hook = Counter(row.hook_kind for row in rows)
    by_status = Counter(row.readiness_status for row in rows)
    payload: dict[str, object] = {
        "schema_version": FORMALIZATION_GAP_PLANNER_ADAPTER_REGISTRY_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "component_name": "formalization_gap_planner_adapter_registry",
        "n_adapters": len(rows),
        "n_ready_local_or_configured": sum(
            1
            for row in rows
            if row.readiness_status in {"READY_LOCAL", "READY_CONFIGURED"}
        ),
        "n_contract_only": by_status.get("CONTRACT_ONLY", 0),
        "n_needs_install": by_status.get("NEEDS_INSTALL", 0),
        "n_needs_credentials": by_status.get("NEEDS_CREDENTIALS", 0),
        "n_needs_configuration": by_status.get("NEEDS_CONFIGURATION", 0),
        "n_ok": sum(1 for row in rows if row.ok),
        "all_ok": bool(rows) and all(row.ok for row in rows),
        "by_component_kind": dict(sorted(by_component.items())),
        "by_hook_kind": dict(sorted(by_hook.items())),
        "by_readiness_status": dict(sorted(by_status.items())),
        "rows": [asdict(row) for row in rows],
        "adapter_registry_fingerprint": stable_hash([asdict(row) for row in rows]),
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
        "usage_order": [
            "use READY_LOCAL adapters for deterministic regression tests",
            "prefer READY_CONFIGURED live adapters for real literature, library, and prover-feedback refinement",
            "record every live adapter output through formalization_gap_planner_refinement_evidence",
            "apply accepted proposals through formalization_gap_planner_route_revision_overlay before replay",
        ],
        "limitations": [
            "readiness checks are local preflights and do not validate remote API availability",
            "contract-only adapters document integration targets but need implementation before live use",
            "adapter outputs are refinement evidence until a prover kernel verifies the revised route",
        ],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "formalization_gap_planner_adapter_registry_manifest.json").write_text(
            json.dumps(payload, indent=2, default=str),
            encoding="utf-8",
        )
        (out_dir / "formalization_gap_planner_adapter_registry.jsonl").write_text(
            "\n".join(json.dumps(asdict(row), sort_keys=True) for row in rows)
            + ("\n" if rows else ""),
            encoding="utf-8",
        )
        (out_dir / "formalization_gap_planner_adapter_registry.md").write_text(
            _markdown_report(payload),
            encoding="utf-8",
        )
    return payload


def _registry_row(spec: dict[str, Any]) -> FormalizationGapPlannerAdapterRegistryRow:
    required_commands = _str_tuple(spec.get("required_commands", []))
    required_packages = _str_tuple(spec.get("required_python_packages", []))
    required_env_vars = _str_tuple(spec.get("required_env_vars", []))
    optional_paths = _str_tuple(spec.get("optional_paths", []))
    detected_commands = {command: shutil.which(command) is not None for command in required_commands}
    detected_packages = {
        package: importlib.util.find_spec(package) is not None
        for package in required_packages
    }
    detected_env_vars = {name: bool(os.environ.get(name)) for name in required_env_vars}
    detected_paths = {path: Path(path).exists() for path in optional_paths}
    readiness_status, readiness_reasons = _readiness(
        spec,
        detected_commands=detected_commands,
        detected_packages=detected_packages,
        detected_env_vars=detected_env_vars,
        detected_paths=detected_paths,
    )
    errors = []
    for field_name in (
        "adapter_id",
        "adapter_name",
        "component_kind",
        "hook_kind",
        "evidence_kind",
        "adapter_surface",
        "role",
    ):
        if not str(spec.get(field_name, "")):
            errors.append(f"{field_name} missing")
    if not _str_tuple(spec.get("output_contract_fields", [])):
        errors.append("output_contract_fields missing")
    return FormalizationGapPlannerAdapterRegistryRow(
        schema_version=FORMALIZATION_GAP_PLANNER_ADAPTER_REGISTRY_SCHEMA_VERSION,
        adapter_id=str(spec.get("adapter_id", "")),
        adapter_name=str(spec.get("adapter_name", "")),
        component_kind=str(spec.get("component_kind", "")),
        hook_kind=str(spec.get("hook_kind", "")),
        evidence_kind=str(spec.get("evidence_kind", "")),
        adapter_surface=str(spec.get("adapter_surface", "")),
        role=str(spec.get("role", "")),
        output_contract_fields=_str_tuple(spec.get("output_contract_fields", [])),
        required_commands=required_commands,
        required_python_packages=required_packages,
        required_env_vars=required_env_vars,
        optional_paths=optional_paths,
        detected_commands=detected_commands,
        detected_python_packages=detected_packages,
        detected_env_vars=detected_env_vars,
        detected_paths=detected_paths,
        readiness_status=readiness_status,
        readiness_reasons=tuple(readiness_reasons),
        install_hint=str(spec.get("install_hint", "")),
        resource_urls=_str_tuple(spec.get("resource_urls", [])),
        online_dependency=bool(spec.get("online_dependency", False)),
        portable_to_prover_families=_str_tuple(
            spec.get("portable_to_prover_families", ["lean4", "rocq", "isabelle", "agda"])
        ),
        response_contract_boundary=str(
            spec.get(
                "response_contract_boundary",
                "adapter must emit JSONL rows accepted by formalization_gap_planner_refinement_evidence",
            )
        ),
        proof_evidence_status=PROOF_EVIDENCE_STATUS,
        proof_evidence_boundary=PROOF_EVIDENCE_BOUNDARY,
        ok=not errors,
        errors=tuple(errors),
    )


def _readiness(
    spec: dict[str, Any],
    *,
    detected_commands: dict[str, bool],
    detected_packages: dict[str, bool],
    detected_env_vars: dict[str, bool],
    detected_paths: dict[str, bool],
) -> tuple[str, list[str]]:
    if spec.get("builtin_ready"):
        return "READY_LOCAL", ["built-in adapter is available in this package"]
    missing_commands = [name for name, present in detected_commands.items() if not present]
    missing_packages = [name for name, present in detected_packages.items() if not present]
    missing_env = [name for name, present in detected_env_vars.items() if not present]
    missing_required_paths = [
        name
        for name, present in detected_paths.items()
        if not present and name in set(_str_tuple(spec.get("required_paths", [])))
    ]
    if missing_commands or missing_packages:
        reasons = []
        if missing_commands:
            reasons.append("missing commands: " + ", ".join(missing_commands))
        if missing_packages:
            reasons.append("missing python packages: " + ", ".join(missing_packages))
        return "NEEDS_INSTALL", reasons
    if missing_env:
        return "NEEDS_CREDENTIALS", ["missing env vars: " + ", ".join(missing_env)]
    if missing_required_paths:
        return "NEEDS_CONFIGURATION", [
            "missing required paths: " + ", ".join(missing_required_paths)
        ]
    if spec.get("contract_only"):
        return "CONTRACT_ONLY", ["integration target documented; live adapter not implemented locally"]
    if detected_paths and not any(detected_paths.values()):
        return "NEEDS_CONFIGURATION", ["no configured optional path currently exists"]
    if detected_commands or detected_packages or detected_env_vars or detected_paths:
        return "READY_CONFIGURED", ["required local preflight checks passed"]
    return "READY_LOCAL", ["no local dependency required"]


def _adapter_specs(
    *,
    lean_rag_db_path: Path | None,
    paper_library_dir: Path | None,
) -> tuple[dict[str, Any], ...]:
    lean_rag_paths = _lean_rag_paths(lean_rag_db_path)
    paper_paths = _path_tuple(paper_library_dir)
    return (
        {
            "adapter_id": "local_route_truth_benchmark_adapter",
            "adapter_name": "Local route-truth benchmark adapter",
            "component_kind": "offline_regression",
            "hook_kind": "all_refinement_hooks",
            "evidence_kind": "all_refinement_response_contracts",
            "adapter_surface": "python_module",
            "role": "deterministic response producer for local regression tests",
            "output_contract_fields": (
                "refinement_item_id",
                "evidence_kind",
                "tool_name",
                "route_revision_recommended",
            ),
            "optional_paths": _path_tuple(default_formalization_gap_planner_ground_truth_path()),
            "builtin_ready": True,
            "resource_urls": (),
            "install_hint": "included in ai_statistician.formalization_gap_planner_refinement_adapters",
        },
        {
            "adapter_id": "paperclip_cli_mcp",
            "adapter_name": "Paperclip CLI/MCP literature adapter",
            "component_kind": "literature_discovery",
            "hook_kind": "literature_discovery",
            "evidence_kind": "literature_route_evidence",
            "adapter_surface": "cli_or_mcp",
            "role": "search and read source papers or documents for source-backed informal route DAG nodes",
            "output_contract_fields": ("source_refs", "route_evidence_nodes"),
            "required_commands": ("paperclip",),
            "online_dependency": True,
            "resource_urls": ("https://paperclip.gxl.ai/docs",),
            "install_hint": "install and configure Paperclip CLI/MCP for corpus access",
        },
        {
            "adapter_id": "paperqa2_local_library",
            "adapter_name": "PaperQA2 local-library adapter",
            "component_kind": "literature_discovery",
            "hook_kind": "literature_discovery",
            "evidence_kind": "literature_route_evidence",
            "adapter_surface": "python_package",
            "role": "question-answer over a local PDF/text/source library with citation-bearing context",
            "output_contract_fields": ("source_refs", "route_evidence_nodes"),
            "required_python_packages": ("paperqa",),
            "optional_paths": paper_paths,
            "online_dependency": False,
            "resource_urls": ("https://github.com/Future-House/paper-qa",),
            "install_hint": "pip install paper-qa and provide --paper-library-dir for local corpora",
        },
        {
            "adapter_id": "openscholar_semantic_scholar",
            "adapter_name": "OpenScholar/Semantic Scholar literature adapter",
            "component_kind": "literature_discovery",
            "hook_kind": "literature_discovery",
            "evidence_kind": "literature_route_evidence",
            "adapter_surface": "external_api_or_local_retriever",
            "role": "large-scale scientific literature synthesis and passage retrieval for uncertain theorem routes",
            "output_contract_fields": ("source_refs", "route_evidence_nodes"),
            "required_env_vars": ("SEMANTIC_SCHOLAR_API_KEY",),
            "online_dependency": True,
            "contract_only": True,
            "resource_urls": (
                "https://github.com/akariasai/openscholar",
                "https://www.semanticscholar.org/product/api",
            ),
            "install_hint": "configure Semantic Scholar/OpenScholar retrieval and map passages into route_evidence_nodes",
        },
        {
            "adapter_id": "local_formal_source_index",
            "adapter_name": "AI Statistician local formal-source index",
            "component_kind": "lean_library_grounding",
            "hook_kind": "lean_library_grounding",
            "evidence_kind": "lean_library_grounding",
            "adapter_surface": "python_module",
            "role": "local declaration search over indexed Lean/source roots",
            "output_contract_fields": ("lean_declaration_hits", "coverage_updates"),
            "builtin_ready": True,
            "resource_urls": (),
            "install_hint": "included in ai_statistician.formal_source_index",
        },
        {
            "adapter_id": "local_lean_rag_dependency_graph",
            "adapter_name": "Local Lean RAG dependency graph adapter",
            "component_kind": "lean_library_grounding",
            "hook_kind": "lean_library_grounding",
            "evidence_kind": "lean_library_grounding",
            "adapter_surface": "sqlite_dependency_graph",
            "role": "reuse declaration dependency metadata, FTS signatures, and graph neighborhoods for coverage updates",
            "output_contract_fields": ("lean_declaration_hits", "coverage_updates"),
            "optional_paths": lean_rag_paths,
            "resource_urls": (),
            "install_hint": "pass --lean-rag-db or set AI_STATISTICIAN_LEAN_RAG_DB to a stat_inference.sqlite graph",
        },
        {
            "adapter_id": "loogle_leansearchclient",
            "adapter_name": "Loogle/LeanSearchClient adapter",
            "component_kind": "lean_library_grounding",
            "hook_kind": "lean_library_grounding",
            "evidence_kind": "lean_library_grounding",
            "adapter_surface": "lean_command_or_cli",
            "role": "query Lean/Mathlib declarations by constant, name, expression shape, or conclusion shape",
            "output_contract_fields": ("lean_declaration_hits", "coverage_updates"),
            "required_commands": ("lake",),
            "online_dependency": True,
            "contract_only": True,
            "resource_urls": ("https://loogle.lean-lang.org/",),
            "install_hint": "install LeanSearchClient/Loogle integration in the target Lean project",
        },
        {
            "adapter_id": "leanexplore_mcp",
            "adapter_name": "LeanExplore MCP/API adapter",
            "component_kind": "lean_library_grounding",
            "hook_kind": "lean_library_grounding",
            "evidence_kind": "lean_library_grounding",
            "adapter_surface": "mcp_or_python_api",
            "role": "semantic and lexical declaration retrieval for theorem-proving agents",
            "output_contract_fields": ("lean_declaration_hits", "coverage_updates"),
            "required_python_packages": ("lean_explore",),
            "online_dependency": True,
            "resource_urls": ("https://arxiv.org/abs/2506.11085",),
            "install_hint": "install lean-explore or configure a LeanExplore MCP/API endpoint",
        },
        {
            "adapter_id": "local_lake_lean",
            "adapter_name": "Local Lake/Lean proof-state adapter",
            "component_kind": "proof_state_feedback",
            "hook_kind": "proof_state_feedback",
            "evidence_kind": "prover_feedback",
            "adapter_surface": "cli",
            "role": "compile skeletons or leaf lemmas and record diagnostics/residual proof obligations",
            "output_contract_fields": ("prover_diagnostics", "residual_goals"),
            "required_commands": ("lean",),
            "resource_urls": ("https://lean-lang.org/",),
            "install_hint": "run formalization-gap-planner-local-proof-state-adapter; pass --lean-project to use lake env lean when a Lake project is available",
        },
        {
            "adapter_id": "lean_lsp_mcp",
            "adapter_name": "lean-lsp-mcp proof-state adapter",
            "component_kind": "proof_state_feedback",
            "hook_kind": "proof_state_feedback",
            "evidence_kind": "prover_feedback",
            "adapter_surface": "mcp",
            "role": "obtain Lean diagnostics, goal states, completions, and project build feedback through LSP",
            "output_contract_fields": ("prover_diagnostics", "residual_goals"),
            "required_commands": ("uvx", "lake"),
            "online_dependency": False,
            "resource_urls": ("https://github.com/oOo0oOo/lean-lsp-mcp",),
            "install_hint": "install uvx and run lean-lsp-mcp in a built Lake project",
        },
        {
            "adapter_id": "leandojo_reprover",
            "adapter_name": "LeanDojo/ReProver adapter",
            "component_kind": "proof_state_feedback",
            "hook_kind": "proof_state_feedback",
            "evidence_kind": "prover_feedback",
            "adapter_surface": "python_package",
            "role": "programmatic Lean interaction and retrieval-augmented premise/proof attempts",
            "output_contract_fields": ("prover_diagnostics", "residual_goals"),
            "required_python_packages": ("lean_dojo",),
            "online_dependency": False,
            "resource_urls": ("https://arxiv.org/abs/2306.15626",),
            "install_hint": "install LeanDojo in an isolated environment and map attempt results into prover_feedback",
        },
        {
            "adapter_id": "route_revision_overlay",
            "adapter_name": "Built-in route-revision overlay",
            "component_kind": "route_revision",
            "hook_kind": "route_revision",
            "evidence_kind": "route_revision_proposal",
            "adapter_surface": "python_module",
            "role": "apply accepted evidence proposals back to current route plans as non-mutating overlays",
            "output_contract_fields": (
                "route_revision_summary",
                "revised_selected_primitives",
                "revised_delta_primitives",
                "revised_informal_knowledge_dag_nodes",
                "revised_lean_realization_dag_nodes",
            ),
            "builtin_ready": True,
            "resource_urls": (),
            "install_hint": "included in ai_statistician.formalization_gap_planner_route_revision_overlay",
        },
    )


def _lean_rag_paths(lean_rag_db_path: Path | None) -> tuple[str, ...]:
    paths: list[Path] = []
    if lean_rag_db_path is not None:
        paths.append(lean_rag_db_path)
    env_path = os.environ.get("AI_STATISTICIAN_LEAN_RAG_DB")
    if env_path:
        paths.append(Path(env_path))
    paths.append(Path("runs/current_status_lean_rag_dependency_graph/stat_inference.sqlite"))
    return _path_tuple(*paths)


def _path_tuple(*paths: Path | None) -> tuple[str, ...]:
    return tuple(str(path) for path in paths if path is not None and str(path))


def _str_tuple(values: Any) -> tuple[str, ...]:
    if isinstance(values, str):
        return (values,) if values else tuple()
    if not isinstance(values, (list, tuple, set)):
        return tuple()
    return tuple(dict.fromkeys(str(item) for item in values if str(item)))


def _markdown_report(payload: dict[str, object]) -> str:
    lines = [
        "# Formalization Gap Planner Adapter Registry",
        "",
        f"- Adapters: {payload.get('n_adapters')}",
        f"- Ready local/configured: {payload.get('n_ready_local_or_configured')}",
        f"- Contract only: {payload.get('n_contract_only')}",
        f"- Needs install: {payload.get('n_needs_install')}",
        f"- Needs credentials: {payload.get('n_needs_credentials')}",
        f"- Needs configuration: {payload.get('n_needs_configuration')}",
        f"- All OK: {payload.get('all_ok')}",
        "",
        "## Boundary",
        "",
        str(payload.get("proof_evidence_boundary", PROOF_EVIDENCE_BOUNDARY)),
        "",
        "## Adapters",
        "",
    ]
    for row in payload.get("rows", []):
        if not isinstance(row, dict):
            continue
        lines.append(
            f"- `{row.get('adapter_id')}` {row.get('hook_kind')} "
            f"status={row.get('readiness_status')}"
        )
        reasons = row.get("readiness_reasons", [])
        if reasons:
            lines.append("  reasons: " + "; ".join(str(item) for item in reasons[:3]))
    return "\n".join(lines) + "\n"
