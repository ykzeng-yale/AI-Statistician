from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash
from .formalization_gap_planner_contract import (
    LIBRARY_AWARE_FORMALIZATION_GAP_PLANNER_NAME,
    PORTABLE_FORMALIZATION_GAP_PLAN_SCHEMA_ID,
)


FORMALIZATION_GAP_PLANNER_SOURCE_GROUNDING_AUDIT_SCHEMA_VERSION = 1
SOURCE_GROUNDING_ROW_SCHEMA_ID = (
    "urn:ai-statistician:schemas:"
    "formalization-gap-planner-source-grounding-row:1"
)
PROOF_EVIDENCE_STATUS = (
    "FORMALIZATION_GAP_PLANNER_SOURCE_GROUNDING_AUDIT_NOT_PROOF_EVIDENCE"
)
PROOF_EVIDENCE_BOUNDARY = (
    "Source-grounding audit rows check whether informal route-DAG nodes have "
    "source refs, declared formal-gap boundaries, or bounded literature-search "
    "work orders. They are source-route discipline checks, not theorem proof "
    "evidence."
)
SOURCE_BACKED = "source_backed"
SOURCE_SEARCH_PENDING = "source_search_pending"
FORMAL_BOUNDARY_DECLARED = "formal_boundary_declared"
UNACCOUNTED = "unaccounted"
GROUNDING_STATUSES = (
    SOURCE_BACKED,
    SOURCE_SEARCH_PENDING,
    FORMAL_BOUNDARY_DECLARED,
    UNACCOUNTED,
)


@dataclass(frozen=True)
class FormalizationGapPlannerSourceGroundingRow:
    schema_version: int
    source_grounding_id: str
    goal_plan_id: str
    route_id: str
    display_name: str
    node_source: str
    node_id: str
    node_kind: str
    node_label: str
    source_refs: tuple[str, ...]
    informal_proof_steps: tuple[str, ...]
    residual_goals: tuple[str, ...]
    residual_primitives: tuple[str, ...]
    residual_evidence_ids: tuple[str, ...]
    residual_attempt_status: str
    residual_diagnostic_signature: str
    literature_hook_present: bool
    literature_queries: tuple[str, ...]
    grounding_status: str
    required_next_action: str
    proof_evidence_status: str
    proof_evidence_boundary: str
    ok: bool
    errors: tuple[str, ...] = ()


def audit_formalization_gap_planner_source_grounding(
    goal_conditioned_minimal_formalization_plan_dir: Path,
    out_dir: Path | None = None,
    *,
    formalization_gap_planner_refinement_evidence_dir: Path | None = None,
) -> dict[str, object]:
    """Audit source-backed or source-search status for route and residual nodes."""

    errors: list[str] = []
    plan_dir = goal_conditioned_minimal_formalization_plan_dir
    manifest_path = plan_dir / "goal_conditioned_minimal_formalization_plan_manifest.json"
    manifest = _read_json(manifest_path, errors)
    if manifest.get("component_name") != LIBRARY_AWARE_FORMALIZATION_GAP_PLANNER_NAME:
        errors.append("input manifest is not the library-aware formalization gap planner")
    if manifest.get("portable_schema_id") != PORTABLE_FORMALIZATION_GAP_PLAN_SCHEMA_ID:
        errors.append("input manifest portable schema id mismatch")
    plan_rows = [row for row in manifest.get("rows", []) if isinstance(row, dict)]
    plan_by_route_id = {
        str(row.get("route_id", "")): row
        for row in plan_rows
        if str(row.get("route_id", ""))
    }
    refinement_rows = _read_refinement_evidence_rows(
        formalization_gap_planner_refinement_evidence_dir,
        errors,
    )
    informal_rows = [
        _source_grounding_row(plan_row, node)
        for plan_row in plan_rows
        for node in _informal_nodes(plan_row)
    ]
    residual_rows = [
        _source_grounding_row(plan_row, node)
        for plan_row, node in [
            *_plan_trace_residual_node_pairs(plan_rows),
            *_refinement_residual_node_pairs(
                refinement_rows,
                plan_by_route_id=plan_by_route_id,
                errors=errors,
            ),
        ]
    ]
    rows = [*informal_rows, *residual_rows]
    by_status: dict[str, int] = {}
    for row in rows:
        by_status[row.grounding_status] = by_status.get(row.grounding_status, 0) + 1
    residual_by_status: dict[str, int] = {}
    for row in residual_rows:
        residual_by_status[row.grounding_status] = (
            residual_by_status.get(row.grounding_status, 0) + 1
        )
    row_dicts = [asdict(row) for row in rows]
    source_grounding_row_schema = source_grounding_row_json_schema()
    row_schema_errors = [
        validate_source_grounding_row(row, source_grounding_row_schema)
        for row in row_dicts
    ]
    n_row_schema_valid = sum(1 for row_errors in row_schema_errors if not row_errors)
    n_row_schema_invalid = len(row_schema_errors) - n_row_schema_valid
    payload: dict[str, object] = {
        "schema_version": FORMALIZATION_GAP_PLANNER_SOURCE_GROUNDING_AUDIT_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "component_name": "formalization_gap_planner_source_grounding_audit",
        "audited_component": str(manifest.get("component_name", "")),
        "portable_schema_id": str(manifest.get("portable_schema_id", "")),
        "goal_conditioned_minimal_formalization_plan_dir": str(plan_dir),
        "goal_conditioned_minimal_formalization_plan_manifest": str(manifest_path),
        "formalization_gap_planner_refinement_evidence_dir": str(
            formalization_gap_planner_refinement_evidence_dir or ""
        ),
        "target_prover_family": str(manifest.get("target_prover_family", "")),
        "library_snapshot_ref": str(manifest.get("library_snapshot_ref", "")),
        "n_plan_rows": len(plan_rows),
        "n_refinement_evidence_rows": len(refinement_rows),
        "n_source_grounding_rows": len(rows),
        "n_informal_route_grounding_rows": len(informal_rows),
        "n_residual_grounding_rows": len(residual_rows),
        "n_residual_goals": len(
            {
                residual_goal
                for row in residual_rows
                for residual_goal in row.residual_goals
            }
        ),
        "n_residual_primitives": len(
            {
                primitive
                for row in residual_rows
                for primitive in row.residual_primitives
            }
        ),
        "n_residual_rows_with_source_refs": sum(
            1 for row in residual_rows if row.source_refs
        ),
        "n_residual_source_backed": residual_by_status.get(SOURCE_BACKED, 0),
        "n_residual_source_search_pending": residual_by_status.get(
            SOURCE_SEARCH_PENDING, 0
        ),
        "n_residual_formal_boundary_declared": residual_by_status.get(
            FORMAL_BOUNDARY_DECLARED, 0
        ),
        "n_residual_unaccounted": residual_by_status.get(UNACCOUNTED, 0),
        "residual_source_grounding_ok": all(row.ok for row in residual_rows),
        "n_ok": sum(1 for row in rows if row.ok),
        "n_failed": sum(1 for row in rows if not row.ok),
        "n_source_backed": by_status.get(SOURCE_BACKED, 0),
        "n_source_search_pending": by_status.get(SOURCE_SEARCH_PENDING, 0),
        "n_formal_boundary_declared": by_status.get(FORMAL_BOUNDARY_DECLARED, 0),
        "n_unaccounted": by_status.get(UNACCOUNTED, 0),
        "n_row_schema_valid": n_row_schema_valid,
        "n_row_schema_invalid": n_row_schema_invalid,
        "source_grounding_row_schema": source_grounding_row_schema,
        "by_grounding_status": dict(sorted(by_status.items())),
        "by_residual_grounding_status": dict(sorted(residual_by_status.items())),
        "by_node_source": _by_node_source(rows),
        "rows": row_dicts,
        "all_ok": (
            not errors
            and bool(rows)
            and all(row.ok for row in rows)
            and n_row_schema_invalid == 0
        ),
        "errors": errors,
        "source_grounding_fingerprint": stable_hash(row_dicts),
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
        "limitations": [
            "source refs identify route grounding, not formal proof correctness",
            "source_search_pending rows must be resolved by literature adapters before route confidence increases",
            "formal_boundary_declared rows are honest blockers, not completed theorem evidence",
            "prover residual rows are route-repair obligations and must be source-backed, source-search pending, or explicitly boundary-declared before promotion",
        ],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (
            out_dir / "formalization_gap_planner_source_grounding_audit_manifest.json"
        ).write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        (out_dir / "formalization_gap_planner_source_grounding_audit.jsonl").write_text(
            "\n".join(json.dumps(row, sort_keys=True) for row in row_dicts)
            + ("\n" if rows else ""),
            encoding="utf-8",
        )
        (
            out_dir / "formalization_gap_planner_source_grounding_row.schema.json"
        ).write_text(
            json.dumps(source_grounding_row_schema, indent=2),
            encoding="utf-8",
        )
        (out_dir / "formalization_gap_planner_source_grounding_audit.md").write_text(
            _markdown_report(payload),
            encoding="utf-8",
        )
    return payload


def source_grounding_row_json_schema() -> dict[str, object]:
    string_array = {"type": "array", "items": {"type": "string"}}
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": SOURCE_GROUNDING_ROW_SCHEMA_ID,
        "title": "Formalization Gap Planner Source-Grounding Row",
        "description": (
            "Per-informal-route-node source-grounding contract. Rows record "
            "whether an informal DAG node has source refs, a declared formal "
            "boundary, or a bounded literature-search obligation. Rows may "
            "also represent prover residual goals that need the same source "
            "discipline before route repair. They are not theorem proof "
            "evidence."
        ),
        "type": "object",
        "additionalProperties": True,
        "required": [
            "schema_version",
            "source_grounding_id",
            "goal_plan_id",
            "route_id",
            "display_name",
            "node_id",
            "node_kind",
            "node_label",
            "source_refs",
            "informal_proof_steps",
            "literature_hook_present",
            "literature_queries",
            "grounding_status",
            "required_next_action",
            "proof_evidence_status",
            "proof_evidence_boundary",
            "ok",
        ],
        "properties": {
            "schema_version": {
                "type": "integer",
                "const": FORMALIZATION_GAP_PLANNER_SOURCE_GROUNDING_AUDIT_SCHEMA_VERSION,
            },
            "source_grounding_id": {"type": "string", "minLength": 1},
            "goal_plan_id": {"type": "string", "minLength": 1},
            "route_id": {"type": "string", "minLength": 1},
            "display_name": {"type": "string", "minLength": 1},
            "node_source": {"type": "string"},
            "node_id": {"type": "string", "minLength": 1},
            "node_kind": {"type": "string", "minLength": 1},
            "node_label": {"type": "string", "minLength": 1},
            "source_refs": string_array,
            "informal_proof_steps": string_array,
            "residual_goals": string_array,
            "residual_primitives": string_array,
            "residual_evidence_ids": string_array,
            "residual_attempt_status": {"type": "string"},
            "residual_diagnostic_signature": {"type": "string"},
            "literature_hook_present": {"type": "boolean"},
            "literature_queries": string_array,
            "grounding_status": {"enum": list(GROUNDING_STATUSES)},
            "required_next_action": {"type": "string", "minLength": 1},
            "proof_evidence_status": {"const": PROOF_EVIDENCE_STATUS},
            "proof_evidence_boundary": {"type": "string", "minLength": 1},
            "ok": {"type": "boolean"},
            "errors": string_array,
        },
    }


def validate_source_grounding_row(
    row: dict[str, Any],
    schema: dict[str, object] | None = None,
) -> list[str]:
    row_schema = schema or source_grounding_row_json_schema()
    if not isinstance(row, dict):
        return ["source grounding row must be an object"]
    errors: list[str] = []
    required = row_schema.get("required", [])
    if isinstance(required, list):
        for field_name in required:
            if isinstance(field_name, str) and field_name not in row:
                errors.append(f"{field_name} required")
    properties = row_schema.get("properties", {})
    if isinstance(properties, dict):
        for field_name, field_schema in properties.items():
            if not isinstance(field_name, str) or field_name not in row:
                continue
            if isinstance(field_schema, dict):
                errors.extend(
                    _schema_property_errors(field_name, row[field_name], field_schema)
                )
    boundary = str(row.get("proof_evidence_boundary", "")).lower()
    if "not theorem proof evidence" not in boundary:
        errors.append("proof_evidence_boundary must say not theorem proof evidence")
    return errors


def _source_grounding_row(
    plan_row: dict[str, Any],
    node: dict[str, Any],
) -> FormalizationGapPlannerSourceGroundingRow:
    source_refs = _source_refs(node)
    informal_steps = _str_tuple(node.get("informal_proof_steps", []))
    literature_queries = tuple(
        dict.fromkeys(
            [
                *_literature_queries(plan_row),
                *_str_tuple(node.get("literature_queries", [])),
            ]
        )
    )
    literature_hook_present = bool(literature_queries)
    status = _grounding_status(
        node,
        source_refs=source_refs,
        literature_hook_present=literature_hook_present,
    )
    errors = () if status != UNACCOUNTED else ("no source refs, formal boundary, or literature hook",)
    return FormalizationGapPlannerSourceGroundingRow(
        schema_version=FORMALIZATION_GAP_PLANNER_SOURCE_GROUNDING_AUDIT_SCHEMA_VERSION,
        source_grounding_id="formalization_gap_planner_source_grounding:"
        + stable_hash(
            [
                plan_row.get("goal_plan_id", ""),
                plan_row.get("route_id", ""),
                node.get("node_id", ""),
                node.get("node_source", "informal_knowledge_dag"),
                source_refs,
                status,
            ]
        )[:20],
        goal_plan_id=str(plan_row.get("goal_plan_id", "")),
        route_id=str(plan_row.get("route_id", "")),
        display_name=str(plan_row.get("display_name", "")),
        node_source=str(node.get("node_source", "informal_knowledge_dag")),
        node_id=str(node.get("node_id", "")),
        node_kind=str(node.get("node_type", node.get("kind", ""))),
        node_label=str(node.get("label", "")),
        source_refs=source_refs,
        informal_proof_steps=informal_steps,
        residual_goals=_str_tuple(node.get("residual_goals", [])),
        residual_primitives=_str_tuple(node.get("residual_primitives", [])),
        residual_evidence_ids=_str_tuple(node.get("residual_evidence_ids", [])),
        residual_attempt_status=str(node.get("residual_attempt_status", "")),
        residual_diagnostic_signature=str(node.get("residual_diagnostic_signature", "")),
        literature_hook_present=literature_hook_present,
        literature_queries=literature_queries,
        grounding_status=status,
        required_next_action=_required_next_action(status),
        proof_evidence_status=PROOF_EVIDENCE_STATUS,
        proof_evidence_boundary=PROOF_EVIDENCE_BOUNDARY,
        ok=status != UNACCOUNTED,
        errors=errors,
    )


def _grounding_status(
    node: dict[str, Any],
    *,
    source_refs: tuple[str, ...],
    literature_hook_present: bool,
) -> str:
    if source_refs:
        return SOURCE_BACKED
    label = str(node.get("label", "")).lower()
    kind = str(node.get("node_type", node.get("kind", ""))).lower()
    attempt_status = str(node.get("residual_attempt_status", "")).lower()
    if (
        kind in {"hidden_assumption_or_gap", "route_blocker", "prover_residual_goal"}
        or attempt_status
    ) and (
        "h_frontier_missing" in label
        or "formal_gap" in label
        or "allowed-sorry" in label
        or "placeholder" in label
        or attempt_status == "formal_gap_scaffold_blocked"
    ):
        return FORMAL_BOUNDARY_DECLARED
    if literature_hook_present:
        return SOURCE_SEARCH_PENDING
    return UNACCOUNTED


def _required_next_action(status: str) -> str:
    if status == SOURCE_BACKED:
        return "use attached source refs during route review"
    if status == FORMAL_BOUNDARY_DECLARED:
        return "keep the formal-gap boundary explicit until replay removes it"
    if status == SOURCE_SEARCH_PENDING:
        return "run bounded literature discovery and attach accepted source refs"
    return "add source refs or a bounded literature-discovery hook before promotion"


def _informal_nodes(plan_row: dict[str, Any]) -> list[dict[str, Any]]:
    nodes: list[dict[str, Any]] = []
    graph = plan_row.get("informal_knowledge_dag", {})
    if isinstance(graph, dict):
        nodes.extend(node for node in graph.get("nodes", []) if isinstance(node, dict))
    trace = plan_row.get("standalone_input_trace", {})
    if isinstance(trace, dict):
        for node in trace.get("revised_informal_knowledge_dag_nodes", []):
            if not isinstance(node, dict):
                continue
            traced_node = dict(node)
            traced_node.setdefault(
                "node_source",
                "standalone_input_trace_revised_informal_dag",
            )
            traced_node.setdefault(
                "node_type",
                traced_node.get("semantic_role", "llm_revised_informal_dag_node"),
            )
            traced_node.setdefault(
                "label",
                traced_node.get("claim", traced_node.get("node_id", "")),
            )
            nodes.append(traced_node)
    return nodes


def _plan_trace_residual_node_pairs(
    plan_rows: list[dict[str, Any]],
) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    pairs: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for plan_row in plan_rows:
        trace = plan_row.get("standalone_input_trace", {})
        if not isinstance(trace, dict):
            continue
        residual_goals = _str_tuple(trace.get("residual_goals", []))
        if not residual_goals:
            continue
        residual_primitives = tuple(
            dict.fromkeys(
                [
                    *_str_tuple(trace.get("alignment_edge_primitives", [])),
                    *_str_tuple(trace.get("revised_delta_primitives", [])),
                    *_str_tuple(trace.get("revised_selected_primitives", [])),
                ]
            )
        )
        evidence_ids = _str_tuple(trace.get("applied_refinement_evidence_ids", []))
        source_refs = _str_tuple(trace.get("source_refs", []))
        for index, residual_goal in enumerate(residual_goals):
            pairs.append(
                (
                    plan_row,
                    {
                        "node_id": "prover_residual:"
                        + stable_hash(
                            [
                                plan_row.get("route_id", ""),
                                "standalone_input_trace",
                                index,
                                residual_goal,
                            ]
                        )[:16],
                        "node_source": "standalone_replan_metadata",
                        "kind": "prover_residual_goal",
                        "node_type": "prover_residual_goal",
                        "label": residual_goal,
                        "source_refs": source_refs,
                        "informal_proof_steps": _str_tuple(
                            trace.get("route_revision_reasons", [])
                        ),
                        "residual_goals": (residual_goal,),
                        "residual_primitives": _residual_primitives_from_goal(
                            residual_goal,
                            plan_row,
                            residual_primitives,
                        ),
                        "residual_evidence_ids": evidence_ids,
                        "residual_attempt_status": ",".join(
                            _str_tuple(trace.get("applied_prover_attempt_statuses", []))
                        ),
                        "residual_diagnostic_signature": ",".join(
                            _str_tuple(
                                trace.get("applied_prover_diagnostic_signatures", [])
                            )
                        ),
                    },
                )
            )
    return pairs


def _refinement_residual_node_pairs(
    refinement_rows: list[dict[str, Any]],
    *,
    plan_by_route_id: dict[str, dict[str, Any]],
    errors: list[str],
) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    pairs: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for evidence_row in refinement_rows:
        residual_goals = _str_tuple(evidence_row.get("residual_goals", []))
        if not residual_goals:
            continue
        route_id = str(evidence_row.get("route_id", ""))
        plan_row = plan_by_route_id.get(route_id)
        if plan_row is None:
            errors.append(f"refinement evidence residual references unknown route_id: {route_id}")
            continue
        source_refs = _evidence_source_refs(evidence_row)
        seed_primitives = tuple(
            dict.fromkeys(
                [
                    *_str_tuple(evidence_row.get("revised_delta_primitives", [])),
                    *_str_tuple(evidence_row.get("revised_selected_primitives", [])),
                    *_str_tuple(evidence_row.get("target_primitives", [])),
                    *_str_tuple(evidence_row.get("residual_primitives", [])),
                    *_str_tuple(evidence_row.get("predicted_residual_primitives", [])),
                ]
            )
        )
        evidence_ids = tuple(
            item
            for item in (
                str(evidence_row.get("refinement_evidence_id", "")),
                str(evidence_row.get("refinement_item_id", "")),
            )
            if item
        )
        for index, residual_goal in enumerate(residual_goals):
            pairs.append(
                (
                    plan_row,
                    {
                        "node_id": "prover_residual:"
                        + stable_hash(
                            [
                                evidence_row.get("refinement_evidence_id", ""),
                                evidence_row.get("refinement_item_id", ""),
                                index,
                                residual_goal,
                            ]
                        )[:16],
                        "node_source": "refinement_evidence_prover_feedback",
                        "kind": "prover_residual_goal",
                        "node_type": "prover_residual_goal",
                        "label": residual_goal,
                        "source_refs": source_refs,
                        "informal_proof_steps": _str_tuple(
                            evidence_row.get("route_revision_reasons", [])
                        ),
                        "residual_goals": (residual_goal,),
                        "residual_primitives": _residual_primitives_from_goal(
                            residual_goal,
                            plan_row,
                            seed_primitives,
                        ),
                        "residual_evidence_ids": evidence_ids,
                        "residual_attempt_status": str(
                            evidence_row.get("prover_attempt_status", "")
                        ),
                        "residual_diagnostic_signature": str(
                            evidence_row.get("prover_diagnostic_signature", "")
                        ),
                    },
                )
            )
    return pairs


def _read_refinement_evidence_rows(
    refinement_evidence_dir: Path | None,
    errors: list[str],
) -> list[dict[str, Any]]:
    if refinement_evidence_dir is None:
        return []
    manifest_path = (
        refinement_evidence_dir
        / "formalization_gap_planner_refinement_evidence_manifest.json"
    )
    jsonl_path = (
        refinement_evidence_dir / "formalization_gap_planner_refinement_evidence.jsonl"
    )
    if not manifest_path.exists():
        return _read_jsonl(jsonl_path, errors)
    manifest = _read_json(manifest_path, errors)
    manifest_rows = [
        row for row in manifest.get("rows", []) if isinstance(row, dict)
    ]
    if manifest_rows:
        return manifest_rows
    return _read_jsonl(jsonl_path, errors)


def _read_jsonl(path: Path, errors: list[str]) -> list[dict[str, Any]]:
    if not path.exists():
        errors.append(f"missing JSONL file: {path}")
        return []
    rows: list[dict[str, Any]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"invalid JSON in {path}:{line_no}: {exc}")
            continue
        if isinstance(payload, dict):
            rows.append(payload)
        else:
            errors.append(f"JSONL row is not an object: {path}:{line_no}")
    return rows


def _evidence_source_refs(evidence_row: dict[str, Any]) -> tuple[str, ...]:
    refs = [*_source_refs(evidence_row)]
    for node in evidence_row.get("route_evidence_nodes", []) or []:
        if isinstance(node, dict):
            refs.extend(_source_refs(node))
    return tuple(dict.fromkeys(refs))


def _residual_primitives_from_goal(
    residual_goal: str,
    plan_row: dict[str, Any],
    seed_primitives: tuple[str, ...],
) -> tuple[str, ...]:
    selected = _str_tuple(plan_row.get("selected_primitives", []))
    primitives: list[str] = [*seed_primitives]
    lower_goal = residual_goal.lower()
    for primitive in selected:
        primitive_lower = primitive.lower()
        primitive_phrase = primitive.replace("_", " ").lower()
        if primitive_lower in lower_goal or primitive_phrase in lower_goal:
            primitives.append(primitive)
    prefix = residual_goal.split(":", 1)[0].strip()
    if prefix and re.fullmatch(r"[A-Za-z0-9_./-]+", prefix):
        primitives.append(prefix)
    return tuple(dict.fromkeys(item for item in primitives if item))


def _by_node_source(
    rows: list[FormalizationGapPlannerSourceGroundingRow],
) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        counts[row.node_source] = counts.get(row.node_source, 0) + 1
    return dict(sorted(counts.items()))


def _literature_queries(plan_row: dict[str, Any]) -> tuple[str, ...]:
    queries: list[str] = []
    for hook in plan_row.get("interactive_refinement_hooks", []) or []:
        if not isinstance(hook, dict):
            continue
        if str(hook.get("hook_kind", "")) != "literature_discovery":
            continue
        queries.extend(str(query) for query in hook.get("queries", []) or [] if str(query))
    return tuple(dict.fromkeys(queries))


def _source_refs(node: dict[str, Any]) -> tuple[str, ...]:
    refs: list[str] = []
    for field_name in ("source_refs", "source_ref", "source_gap_ids", "source_task_ids"):
        value = node.get(field_name, [])
        if isinstance(value, str):
            if value:
                refs.append(value)
        elif isinstance(value, (list, tuple, set)):
            refs.extend(str(item) for item in value if str(item))
    return tuple(dict.fromkeys(refs))


def _str_tuple(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,) if value else ()
    if isinstance(value, (list, tuple, set)):
        return tuple(str(item) for item in value if str(item))
    return (str(value),) if str(value) else ()


def _schema_property_errors(
    field_name: str,
    value: Any,
    field_schema: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    expected_type = field_schema.get("type")
    if expected_type == "string":
        if not isinstance(value, str):
            errors.append(f"{field_name} must be a string")
        elif field_schema.get("minLength") and len(value) < int(
            field_schema["minLength"]
        ):
            errors.append(f"{field_name} must be nonempty")
    elif expected_type == "integer":
        if not isinstance(value, int) or isinstance(value, bool):
            errors.append(f"{field_name} must be an integer")
    elif expected_type == "boolean" and not isinstance(value, bool):
        errors.append(f"{field_name} must be a boolean")
    elif expected_type == "array":
        if not isinstance(value, (list, tuple)):
            errors.append(f"{field_name} must be an array")
        else:
            item_schema = field_schema.get("items", {})
            if isinstance(item_schema, dict) and item_schema.get("type") == "string":
                for idx, item in enumerate(value):
                    if not isinstance(item, str):
                        errors.append(f"{field_name}[{idx}] must be a string")
    elif expected_type == "object" and not isinstance(value, dict):
        errors.append(f"{field_name} must be an object")
    if "const" in field_schema and value != field_schema["const"]:
        errors.append(f"{field_name} must equal {field_schema['const']!r}")
    enum_values = field_schema.get("enum")
    if isinstance(enum_values, list) and value not in enum_values:
        errors.append(f"{field_name} must be one of {enum_values!r}")
    return errors


def _read_json(path: Path, errors: list[str]) -> dict[str, Any]:
    if not path.exists():
        errors.append(f"missing JSON file: {path}")
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f"invalid JSON in {path}: {exc}")
        return {}
    return payload if isinstance(payload, dict) else {}


def _markdown_report(payload: dict[str, object]) -> str:
    lines = [
        "# Formalization Gap Planner Source-Grounding Audit",
        "",
        f"- Rows: {payload.get('n_source_grounding_rows')}",
        f"- Informal route rows: {payload.get('n_informal_route_grounding_rows')}",
        f"- Residual rows: {payload.get('n_residual_grounding_rows')}",
        f"- Source-backed: {payload.get('n_source_backed')}",
        f"- Source-search pending: {payload.get('n_source_search_pending')}",
        f"- Formal boundary declared: {payload.get('n_formal_boundary_declared')}",
        f"- Unaccounted: {payload.get('n_unaccounted')}",
        f"- Residual source-backed: {payload.get('n_residual_source_backed')}",
        f"- Residual pending: {payload.get('n_residual_source_search_pending')}",
        f"- Residual unaccounted: {payload.get('n_residual_unaccounted')}",
        (
            f"- Row schema valid: {payload.get('n_row_schema_valid')}/"
            f"{payload.get('n_source_grounding_rows')}"
        ),
        f"- All OK: {payload.get('all_ok')}",
        "",
        "## Boundary",
        "",
        str(payload.get("proof_evidence_boundary", PROOF_EVIDENCE_BOUNDARY)),
        "",
        "## Unaccounted Nodes",
        "",
    ]
    failed = [
        row
        for row in payload.get("rows", [])
        if isinstance(row, dict) and row.get("grounding_status") == UNACCOUNTED
    ]
    if not failed:
        lines.append("- None")
    for row in failed:
        lines.append(
            f"- `{row.get('display_name')}` node=`{row.get('node_label')}` "
            f"kind={row.get('node_kind')} source={row.get('node_source', '')}"
        )
    return "\n".join(lines) + "\n"
