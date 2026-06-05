from __future__ import annotations

import json
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash


LEAN_BLUEPRINT_KNOWLEDGE_SCHEMA_VERSION = 1
LEAN_BLUEPRINT_ROOT = Path("/Users/yukang/.codex/external/leanblueprint")
LEAN_BLUEPRINT_URL = "https://github.com/PatrickMassot/leanblueprint"

BLUEPRINT_BOUNDARY = (
    "LeanBlueprint metadata is visualization, planning, and source-grounding "
    "evidence. A blueprint node or Lean declaration link is not proof evidence "
    "until the linked Lean declaration is checked under the target project."
)


@dataclass(frozen=True)
class BlueprintMacro:
    macro: str
    role: str
    graph_field: str
    ai_statistician_use: str


@dataclass(frozen=True)
class BlueprintStatus:
    status: str
    source_signal: str
    visual_meaning: str
    ai_statistician_use: str


BLUEPRINT_MACROS: tuple[BlueprintMacro, ...] = (
    BlueprintMacro(
        macro=r"\lean{decls}",
        role="link informal statement/proof text to Lean declaration names",
        graph_field="formal_declaration_links",
        ai_statistician_use="align informal theory nodes with candidate Lean declarations and retrieval hits",
    ),
    BlueprintMacro(
        macro=r"\leanok",
        role="mark the surrounding statement or proof as formalized",
        graph_field="formalization_status",
        ai_statistician_use="visualize which route nodes are already formalized versus still planned",
    ),
    BlueprintMacro(
        macro=r"\uses{labels}",
        role="declare prerequisite statement/proof labels for dependency graph edges",
        graph_field="dependency_edges",
        ai_statistician_use="export informal knowledge DAG and proof-route prerequisite edges",
    ),
    BlueprintMacro(
        macro=r"\notready",
        role="mark a node whose statement is not ready to formalize",
        graph_field="readiness_status",
        ai_statistician_use="separate conceptual exposition gaps from Lean proof-search gaps",
    ),
    BlueprintMacro(
        macro=r"\discussion{issue}",
        role="attach a GitHub issue to a blueprint node",
        graph_field="discussion_links",
        ai_statistician_use="route stalled formalization nodes to tracked human/agent follow-up threads",
    ),
    BlueprintMacro(
        macro=r"\proves{label}",
        role="connect a proof environment to the statement it proves",
        graph_field="proof_to_statement_edges",
        ai_statistician_use="separate statement dependencies from proof dependencies in two-DAG exports",
    ),
    BlueprintMacro(
        macro=r"\mathlibok",
        role="mark a node as already merged into Mathlib",
        graph_field="mathlib_status",
        ai_statistician_use="prefer Mathlib-reuse routes and avoid duplicating library facts",
    ),
    BlueprintMacro(
        macro=r"\graphcolor{type}{color}{description}",
        role="customize dependency-graph status colors",
        graph_field="visual_style",
        ai_statistician_use="map route status to stable visualization colors for dashboards",
    ),
)

BLUEPRINT_STATUSES: tuple[BlueprintStatus, ...] = (
    BlueprintStatus(
        status="stated",
        source_signal=r"\leanok on statement",
        visual_meaning="statement is formalized",
        ai_statistician_use="candidate theorem statement exists in Lean and can anchor retrieval",
    ),
    BlueprintStatus(
        status="proved",
        source_signal=r"\leanok on proof",
        visual_meaning="proof is formalized",
        ai_statistician_use="candidate completed route, still requiring local project verification before proof-ledger promotion",
    ),
    BlueprintStatus(
        status="can_state",
        source_signal="all statement prerequisites are formalized and node is not marked notready",
        visual_meaning="statement is ready to formalize",
        ai_statistician_use="good next target for autoformalization or statement repair",
    ),
    BlueprintStatus(
        status="can_prove",
        source_signal="statement and proof prerequisites are formalized",
        visual_meaning="proof is ready to formalize",
        ai_statistician_use="good next target for proof search or proof-repair workers",
    ),
    BlueprintStatus(
        status="not_ready",
        source_signal=r"\notready",
        visual_meaning="blueprint needs more conceptual work",
        ai_statistician_use="send to theory/refinement queue instead of prover queue",
    ),
    BlueprintStatus(
        status="fully_proved",
        source_signal="node and graph ancestors are proved or definitions",
        visual_meaning="closed dependency subgraph",
        ai_statistician_use="safe visualization milestone for a theorem-route component",
    ),
    BlueprintStatus(
        status="mathlib",
        source_signal=r"\mathlibok",
        visual_meaning="already upstreamed to Mathlib",
        ai_statistician_use="prefer direct Mathlib source retrieval and local Lean import checks",
    ),
)


def export_lean_blueprint_knowledge(
    out_dir: Path,
    *,
    blueprint_root: Path | str | None = None,
) -> dict[str, object]:
    """Export LeanBlueprint as a knowledge-base and visualization adapter."""

    root = Path(blueprint_root).expanduser() if blueprint_root else LEAN_BLUEPRINT_ROOT
    out_dir.mkdir(parents=True, exist_ok=True)
    source = _source_metadata(root)
    macros = [asdict(row) for row in BLUEPRINT_MACROS]
    statuses = [asdict(row) for row in BLUEPRINT_STATUSES]
    graph = _knowledge_graph(macros, statuses)
    adapter_contract = _adapter_contract()
    payload: dict[str, object] = {
        "schema_version": LEAN_BLUEPRINT_KNOWLEDGE_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source": source,
        "boundary": BLUEPRINT_BOUNDARY,
        "macros": macros,
        "statuses": statuses,
        "knowledge_graph": graph,
        "adapter_contract": adapter_contract,
        "recommended_actions": _recommended_actions(source),
        "all_ok": bool(source["exists"] and source["has_blueprint_package"] and source["has_client"]),
    }
    payload["fingerprint"] = stable_hash(
        {
            "schema_version": LEAN_BLUEPRINT_KNOWLEDGE_SCHEMA_VERSION,
            "source": source,
            "macros": macros,
            "statuses": statuses,
            "adapter_contract": adapter_contract,
        }
    )
    (out_dir / "lean_blueprint_knowledge_manifest.json").write_text(
        json.dumps(payload, indent=2, default=str) + "\n",
        encoding="utf-8",
    )
    (out_dir / "lean_blueprint_knowledge_graph.json").write_text(
        json.dumps(graph, indent=2, default=str) + "\n",
        encoding="utf-8",
    )
    (out_dir / "lean_blueprint_visualization_adapter_plan.json").write_text(
        json.dumps(adapter_contract, indent=2, default=str) + "\n",
        encoding="utf-8",
    )
    (out_dir / "lean_blueprint_knowledge.md").write_text(
        _markdown_report(payload),
        encoding="utf-8",
    )
    return payload


def _source_metadata(root: Path) -> dict[str, object]:
    return {
        "source_id": "lean_blueprint",
        "name": "LeanBlueprint",
        "url": LEAN_BLUEPRINT_URL,
        "citation": (
            "Patrick Massot. LeanBlueprint: A plasTeX plugin to build "
            "formalization blueprints. 2020. Software."
        ),
        "root": str(root),
        "exists": root.exists(),
        "license_policy": "Apache-2.0",
        "usage_policy": "integration_reference_no_training_export",
        "git_commit": _git_output(root, "rev-parse", "HEAD") if root.exists() else "",
        "remote_url": _git_output(root, "remote", "get-url", "origin") if root.exists() else "",
        "has_blueprint_package": (root / "leanblueprint" / "Packages" / "blueprint.py").exists(),
        "has_client": (root / "leanblueprint" / "client.py").exists(),
        "has_templates": (root / "leanblueprint" / "templates").exists(),
        "has_static_css": (root / "leanblueprint" / "static" / "blueprint.css").exists(),
    }


def _knowledge_graph(macros: list[dict[str, object]], statuses: list[dict[str, object]]) -> dict[str, object]:
    nodes: list[dict[str, object]] = [
        {
            "id": "lean_blueprint",
            "label": "LeanBlueprint",
            "kind": "tool",
            "role": "plasTeX plugin and CLI for formalization blueprints",
        },
        {
            "id": "informal_exposition",
            "label": "Informal Exposition",
            "kind": "input",
            "role": "LaTeX definitions, lemmas, theorems, and proofs",
        },
        {
            "id": "blueprint_dependency_graph",
            "label": "Blueprint Dependency Graph",
            "kind": "graph",
            "role": "statement/proof DAG with formalization status",
        },
        {
            "id": "lean_declaration_links",
            "label": "Lean Declaration Links",
            "kind": "formal_links",
            "role": "Lean names and doc-gen URLs attached to blueprint nodes",
        },
        {
            "id": "ai_statistician_visualization",
            "label": "AI-Statistician Visualization",
            "kind": "downstream_adapter",
            "role": "future route DAG and proof-status dashboard input",
        },
    ]
    nodes.extend(
        {
            "id": "macro:" + str(row["macro"]).strip("\\").split("{", 1)[0],
            "label": row["macro"],
            "kind": "blueprint_macro",
            "role": row["role"],
            "graph_field": row["graph_field"],
            "ai_statistician_use": row["ai_statistician_use"],
        }
        for row in macros
    )
    nodes.extend(
        {
            "id": "status:" + str(row["status"]),
            "label": row["status"],
            "kind": "blueprint_status",
            "source_signal": row["source_signal"],
            "visual_meaning": row["visual_meaning"],
            "ai_statistician_use": row["ai_statistician_use"],
        }
        for row in statuses
    )
    edges: list[dict[str, object]] = [
        {"source": "informal_exposition", "target": "lean_blueprint", "relation": "parsed_by"},
        {"source": "lean_blueprint", "target": "blueprint_dependency_graph", "relation": "emits"},
        {"source": "lean_blueprint", "target": "lean_declaration_links", "relation": "emits"},
        {"source": "blueprint_dependency_graph", "target": "ai_statistician_visualization", "relation": "feeds"},
        {"source": "lean_declaration_links", "target": "ai_statistician_visualization", "relation": "feeds"},
    ]
    edges.extend(
        {
            "source": "macro:" + str(row["macro"]).strip("\\").split("{", 1)[0],
            "target": "blueprint_dependency_graph",
            "relation": "populates",
            "field": row["graph_field"],
        }
        for row in macros
        if row["graph_field"] != "formal_declaration_links"
    )
    edges.extend(
        {
            "source": "macro:" + str(row["macro"]).strip("\\").split("{", 1)[0],
            "target": "lean_declaration_links",
            "relation": "populates",
            "field": row["graph_field"],
        }
        for row in macros
        if row["graph_field"] == "formal_declaration_links"
    )
    edges.extend(
        {
            "source": "status:" + str(row["status"]),
            "target": "ai_statistician_visualization",
            "relation": "renders_as_status",
        }
        for row in statuses
    )
    return {
        "schema": "ai_statistician.blueprint_knowledge_graph.v1",
        "nodes": nodes,
        "edges": edges,
        "n_nodes": len(nodes),
        "n_edges": len(edges),
    }


def _adapter_contract() -> dict[str, object]:
    return {
        "adapter_id": "lean_blueprint_visualization_adapter",
        "source_id": "lean_blueprint",
        "input_contract": {
            "blueprint_tex_root": "blueprint/src or equivalent LaTeX source directory",
            "required_macros": [row.macro for row in BLUEPRINT_MACROS[:4]],
            "optional_macros": [row.macro for row in BLUEPRINT_MACROS[4:]],
        },
        "output_contract": {
            "nodes": (
                "label",
                "kind",
                "lean_decls",
                "lean_urls",
                "leanok",
                "notready",
                "mathlibok",
                "can_state",
                "can_prove",
                "proved",
                "fully_proved",
                "discussion_issue",
            ),
            "edges": ("source_label", "target_label", "relation", "source_macro"),
            "status_fields": tuple(row.status for row in BLUEPRINT_STATUSES),
        },
        "planned_ai_statistician_mapping": {
            "informal_knowledge_dag_nodes": "blueprint nodes from definitions, lemmas, propositions, theorems, and corollaries",
            "informal_knowledge_dag_edges": r"\uses prerequisite edges",
            "lean_realization_dag_nodes": r"\lean declaration links plus local formal-source hits",
            "proof_progress_status": "leanok/notready/mathlibok/can_state/can_prove/proved/fully_proved",
            "human_agent_followup": r"\discussion issue links and notready nodes",
        },
        "proof_boundary": BLUEPRINT_BOUNDARY,
    }


def _recommended_actions(source: dict[str, object]) -> list[str]:
    actions = [
        "Use LeanBlueprint exports to visualize theorem-route DAGs produced by formalization-gap planning.",
        r"Map AI-Statistician route nodes to \label, prerequisite edges to \uses, Lean declarations to \lean, and proof status to \leanok/\notready/\mathlibok.",
        "Keep Blueprint output as planning/visualization metadata; promote proof status only after local Lean verification.",
    ]
    if not source.get("exists"):
        actions.insert(0, f"Clone {LEAN_BLUEPRINT_URL} into {LEAN_BLUEPRINT_ROOT}.")
    return actions


def _git_output(root: Path, *args: str) -> str:
    try:
        return subprocess.check_output(
            ["git", "-C", str(root), *args],
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=10,
        ).strip()
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return ""


def _markdown_report(payload: dict[str, object]) -> str:
    source = dict(payload.get("source", {}) or {})
    lines = [
        "# LeanBlueprint Knowledge Integration",
        "",
        f"- Source: [{source.get('name')}]({source.get('url')})",
        f"- Local root: `{source.get('root')}`",
        f"- Commit: `{str(source.get('git_commit', ''))[:12]}`",
        f"- License policy: `{source.get('license_policy')}`",
        f"- Usage policy: `{source.get('usage_policy')}`",
        f"- All ok: `{payload.get('all_ok')}`",
        "",
        "## Boundary",
        "",
        str(payload.get("boundary", BLUEPRINT_BOUNDARY)),
        "",
        "## Macros",
        "",
        "| Macro | Graph field | AI-Statistician use |",
        "|---|---|---|",
    ]
    for row in payload.get("macros", []):
        if isinstance(row, dict):
            lines.append(f"| `{row.get('macro')}` | `{row.get('graph_field')}` | {row.get('ai_statistician_use')} |")
    lines.extend(["", "## Statuses", "", "| Status | Signal | Visualization use |", "|---|---|---|"])
    for row in payload.get("statuses", []):
        if isinstance(row, dict):
            lines.append(f"| `{row.get('status')}` | `{row.get('source_signal')}` | {row.get('ai_statistician_use')} |")
    lines.extend(["", "## Artifacts", ""])
    lines.append("- `lean_blueprint_knowledge_graph.json`: visualization-ready nodes/edges.")
    lines.append("- `lean_blueprint_visualization_adapter_plan.json`: downstream adapter contract.")
    lines.extend(["", "## Recommended Actions", ""])
    for action in payload.get("recommended_actions", []):
        lines.append(f"- {action}")
    return "\n".join(lines) + "\n"
