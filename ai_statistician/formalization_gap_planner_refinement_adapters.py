from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash
from .formalization_gap_planner_benchmark import (
    default_formalization_gap_planner_ground_truth_path,
    load_formalization_gap_planner_ground_truth,
)
from .formalization_gap_planner_refinement_evidence import (
    PROOF_EVIDENCE_BOUNDARY,
    refinement_tool_response_json_schema,
    validate_refinement_tool_response_row,
)


FORMALIZATION_GAP_PLANNER_REFINEMENT_ADAPTER_SCHEMA_VERSION = 1
PROOF_EVIDENCE_STATUS = "FORMALIZATION_GAP_PLANNER_REFINEMENT_ADAPTER_NOT_PROOF_EVIDENCE"
ADAPTER_TOOL_NAME = "local_route_truth_benchmark_adapter"


def export_formalization_gap_planner_refinement_adapter_responses(
    formalization_gap_planner_refinement_queue_dir: Path,
    out_dir: Path | None = None,
    *,
    ground_truth_path: Path | None = None,
    max_items: int = 0,
) -> dict[str, object]:
    """Produce conservative local responses for gap-planner refinement rows.

    The adapter uses the reusable benchmark route-truth file as deterministic
    local evidence. It is intentionally not a proof adapter: it can supply
    source refs, coverage labels, residual diagnostics, and route-revision
    proposals, but it never upgrades a theorem to verified status.
    """

    errors: list[str] = []
    queue_manifest_path = (
        formalization_gap_planner_refinement_queue_dir
        / "formalization_gap_planner_refinement_queue_manifest.json"
    )
    queue_payload = _read_json(queue_manifest_path, errors)
    raw_queue_rows = [
        row for row in queue_payload.get("rows", []) if isinstance(row, dict)
    ]
    queue_rows = raw_queue_rows[:max_items] if max_items > 0 else raw_queue_rows
    ground_truth_payload = load_formalization_gap_planner_ground_truth(ground_truth_path)
    truth_rows = [
        row for row in ground_truth_payload.get("routes", []) if isinstance(row, dict)
    ]
    truth_by_display_name = {
        str(row.get("display_name", "")): row
        for row in truth_rows
        if str(row.get("display_name", ""))
    }

    responses = [
        _response_for_queue_row(row, truth_by_display_name.get(str(row.get("display_name", ""))))
        for row in queue_rows
    ]
    response_schema = refinement_tool_response_json_schema()
    response_schema_errors = [
        validate_refinement_tool_response_row(response, response_schema)
        for response in responses
    ]
    n_response_schema_valid = sum(
        1 for row_errors in response_schema_errors if not row_errors
    )
    by_hook_kind = Counter(str(row.get("hook_kind", "")) for row in queue_rows)
    by_evidence_kind = Counter(str(row.get("evidence_kind", "")) for row in responses)
    n_ground_truth_matched = sum(
        1
        for row in queue_rows
        if str(row.get("display_name", "")) in truth_by_display_name
    )
    payload: dict[str, object] = {
        "schema_version": FORMALIZATION_GAP_PLANNER_REFINEMENT_ADAPTER_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "component_name": "formalization_gap_planner_refinement_adapter_responses",
        "formalization_gap_planner_refinement_queue_dir": str(
            formalization_gap_planner_refinement_queue_dir
        ),
        "formalization_gap_planner_refinement_queue_manifest": str(queue_manifest_path),
        "ground_truth_path": str(
            ground_truth_path or default_formalization_gap_planner_ground_truth_path()
        ),
        "ground_truth_benchmark_id": ground_truth_payload.get("benchmark_id", ""),
        "max_items": max_items,
        "n_queue_rows": len(queue_rows),
        "n_responses": len(responses),
        "n_ground_truth_matched": n_ground_truth_matched,
        "n_ground_truth_unmatched": len(queue_rows) - n_ground_truth_matched,
        "n_literature_responses": by_evidence_kind.get("literature_route_evidence", 0),
        "n_formal_grounding_responses": (
            by_evidence_kind.get("formal_library_grounding", 0)
            + by_evidence_kind.get("lean_library_grounding", 0)
        ),
        "n_lean_grounding_responses": by_evidence_kind.get("lean_library_grounding", 0),
        "n_prover_feedback_responses": by_evidence_kind.get("prover_feedback", 0),
        "n_route_revision_responses": by_evidence_kind.get(
            "route_revision_proposal", 0
        ),
        "n_route_revision_recommended": sum(
            1 for row in responses if bool(row.get("route_revision_recommended", False))
        ),
        "n_response_schema_valid": n_response_schema_valid,
        "n_response_schema_invalid": len(response_schema_errors)
        - n_response_schema_valid,
        "response_schema_errors": response_schema_errors,
        "n_ok": len(responses),
        "all_ok": not errors
        and bool(queue_rows)
        and len(responses) == len(queue_rows)
        and n_response_schema_valid == len(responses)
        and bool(ground_truth_payload.get("all_ok", False)),
        "errors": errors + [str(error) for error in ground_truth_payload.get("errors", [])],
        "by_hook_kind": dict(sorted(by_hook_kind.items())),
        "by_evidence_kind": dict(sorted(by_evidence_kind.items())),
        "responses": responses,
        "refinement_tool_response_schema": response_schema,
        "responses_fingerprint": stable_hash(responses),
        "response_contract": (
            "Responses are keyed by refinement_item_id and are accepted by "
            "formalization_gap_planner_refinement_evidence."
        ),
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
        "limitations": [
            "benchmark route truth is planning/evaluation evidence, not Lean kernel proof evidence",
            "generated formal declaration hits are coverage-grounding records and may include negative search labels",
            "live Paperclip/PaperQA/OpenScholar, LeanSearch/Loogle, and Lean/LSP adapters should replace this local adapter when available",
        ],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = out_dir / "formalization_gap_planner_refinement_adapter_manifest.json"
        responses_path = (
            out_dir / "formalization_gap_planner_refinement_evidence_responses.jsonl"
        )
        response_schema_path = (
            out_dir / "formalization_gap_planner_refinement_tool_response.schema.json"
        )
        payload["manifest_path"] = str(manifest_path)
        payload["responses_jsonl"] = str(responses_path)
        payload["response_schema_path"] = str(response_schema_path)
        manifest_path.write_text(
            json.dumps(payload, indent=2, default=str),
            encoding="utf-8",
        )
        response_schema_path.write_text(
            json.dumps(response_schema, indent=2),
            encoding="utf-8",
        )
        responses_path.write_text(
            "\n".join(json.dumps(row, sort_keys=True) for row in responses)
            + ("\n" if responses else ""),
            encoding="utf-8",
        )
        (out_dir / "formalization_gap_planner_refinement_adapter.md").write_text(
            _markdown_report(payload),
            encoding="utf-8",
        )
    return payload


def _response_for_queue_row(
    queue_row: dict[str, Any],
    truth_row: dict[str, Any] | None,
) -> dict[str, object]:
    hook_kind = str(queue_row.get("hook_kind", ""))
    if hook_kind == "literature_discovery":
        return _literature_response(queue_row, truth_row)
    if _is_formal_library_grounding_hook(hook_kind):
        return _lean_grounding_response(queue_row, truth_row)
    if hook_kind == "proof_state_feedback":
        return _prover_feedback_response(queue_row, truth_row)
    if hook_kind == "route_revision":
        return _route_revision_response(queue_row, truth_row)
    return _unsupported_hook_response(queue_row, hook_kind)


def _base_response(
    queue_row: dict[str, Any],
    *,
    evidence_kind: str,
    tool_name: str = ADAPTER_TOOL_NAME,
) -> dict[str, object]:
    response = {
        "refinement_item_id": str(queue_row.get("refinement_item_id", "")),
        "route_id": str(queue_row.get("route_id", "")),
        "display_name": str(queue_row.get("display_name", "")),
        "evidence_kind": evidence_kind,
        "tool_name": tool_name,
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
    }
    for field_name in (
        "resource_request_ids",
        "resource_ids",
        "resource_request_bindings",
        "llm_route_planner_hook_trace",
    ):
        value = queue_row.get(field_name, [])
        if value:
            response[field_name] = value
    return response


def _literature_response(
    queue_row: dict[str, Any],
    truth_row: dict[str, Any] | None,
) -> dict[str, object]:
    source_refs = _source_refs(queue_row, truth_row)
    primitives = _selected_primitives(queue_row, truth_row)
    matched_truth = truth_row is not None
    response = _base_response(
        queue_row,
        evidence_kind="literature_route_evidence",
    )
    response.update(
        {
            "source_refs": source_refs,
            "route_evidence_nodes": _route_evidence_nodes(
                source_refs,
                primitives,
                matched_truth=matched_truth,
            ),
            "route_revision_recommended": not matched_truth,
            "route_revision_reasons": ()
            if matched_truth
            else (
                "no benchmark route-truth match; attach source-backed route evidence manually",
            ),
        }
    )
    return response


def _lean_grounding_response(
    queue_row: dict[str, Any],
    truth_row: dict[str, Any] | None,
) -> dict[str, object]:
    coverage = _coverage_updates_for_row(queue_row, truth_row)
    lean_hits = [
        _lean_grounding_hit(primitive, coverage_status)
        for primitive, coverage_status in coverage.items()
    ]
    revision_reasons = _coverage_revision_reasons(coverage, truth_row)
    response = _base_response(
        queue_row,
        evidence_kind="formal_library_grounding",
    )
    response.update(
        {
            "formal_declaration_hits": lean_hits,
            "lean_declaration_hits": lean_hits,
            "coverage_updates": coverage,
            "route_revision_recommended": bool(revision_reasons),
            "route_revision_reasons": tuple(revision_reasons),
        }
    )
    return response


def _prover_feedback_response(
    queue_row: dict[str, Any],
    truth_row: dict[str, Any] | None,
) -> dict[str, object]:
    prover_status = str(queue_row.get("prover_feedback_status", ""))
    first_error = str(queue_row.get("prover_feedback_first_error", ""))
    error_category = str(queue_row.get("prover_feedback_error_category", ""))
    coverage = _coverage_updates_for_row(queue_row, truth_row)
    failed = _is_failed_prover_feedback(prover_status)
    diagnostics = []
    residual_goals = []
    revision_reasons = []
    if failed:
        if error_category:
            diagnostics.append(f"prover feedback category: {error_category}")
        diagnostics.append(first_error or f"prover feedback status: {prover_status}")
        residual_goals = [
            f"{primitive}: {coverage_status}"
            for primitive, coverage_status in coverage.items()
            if coverage_status != "exact_exists"
        ]
        if not residual_goals:
            residual_goals = [f"unclosed proof state under status {prover_status}"]
        revision_reasons.append("failed prover feedback requires route repair")
    else:
        diagnostics.append(
            "No kernel-verified proof feedback recorded; run leaf or full-route Lean/LSP attempts before any proof claim."
        )
        if prover_status and prover_status != "no_calibration_signal":
            diagnostics.append(f"current prover feedback status: {prover_status}")
    response = _base_response(
        queue_row,
        evidence_kind="prover_feedback",
        tool_name="local_replay_calibration_adapter",
    )
    response.update(
        {
            "attempt_status": _attempt_status(prover_status, failed),
            "prover_diagnostics": tuple(diagnostics),
            "residual_goals": tuple(residual_goals),
            "route_revision_recommended": bool(revision_reasons),
            "route_revision_reasons": tuple(revision_reasons),
        }
    )
    return response


def _attempt_status(prover_status: str, failed: bool) -> str:
    if prover_status and prover_status != "no_calibration_signal":
        return prover_status
    if failed:
        return "local_lean_failed"
    return "awaiting_full_route_attempt"


def _route_revision_response(
    queue_row: dict[str, Any],
    truth_row: dict[str, Any] | None,
) -> dict[str, object]:
    selected = _selected_primitives(queue_row, truth_row)
    coverage = _coverage_updates_for_row(queue_row, truth_row)
    delta = _delta_primitives(queue_row, truth_row, coverage)
    reasons = _route_revision_reasons(queue_row, truth_row, coverage)
    source_refs = _source_refs(queue_row, truth_row)
    response = _base_response(
        queue_row,
        evidence_kind="route_revision_proposal",
        tool_name="local_route_revision_adapter",
    )
    response.update(
        {
            "source_refs": source_refs,
            "route_revision_summary": _route_revision_summary(
                queue_row,
                truth_row,
                selected,
                delta,
            ),
            "revised_selected_primitives": selected,
            "revised_delta_primitives": delta,
            "revised_informal_knowledge_dag_nodes": _informal_dag_nodes(
                selected,
                source_refs,
            ),
            "revised_formal_realization_dag_nodes": _lean_dag_nodes(coverage),
            "revised_lean_realization_dag_nodes": _lean_dag_nodes(coverage),
            "route_revision_recommended": True,
            "route_revision_reasons": tuple(reasons),
        }
    )
    return response


def _unsupported_hook_response(queue_row: dict[str, Any], hook_kind: str) -> dict[str, object]:
    response = _base_response(queue_row, evidence_kind="")
    response.update(
        {
            "prover_diagnostics": (f"unsupported refinement hook: {hook_kind}",),
            "route_revision_recommended": True,
            "route_revision_reasons": ("unsupported refinement hook requires manual routing",),
        }
    )
    return response


def _source_refs(
    queue_row: dict[str, Any],
    truth_row: dict[str, Any] | None,
) -> tuple[str, ...]:
    if truth_row is not None:
        refs = _str_tuple(truth_row.get("source_refs", []))
        if refs:
            return refs
    queries = _str_tuple(queue_row.get("queries", []))
    return queries or ("manual_source_search_required",)


def _selected_primitives(
    queue_row: dict[str, Any],
    truth_row: dict[str, Any] | None,
) -> tuple[str, ...]:
    target = _str_tuple(queue_row.get("target_primitives", []))
    if target:
        return target
    if truth_row is not None:
        return _str_tuple(truth_row.get("required_primitives", []))
    return ("manual_route_primitive_discovery_required",)


def _delta_primitives(
    queue_row: dict[str, Any],
    truth_row: dict[str, Any] | None,
    coverage: dict[str, str],
) -> tuple[str, ...]:
    if truth_row is not None:
        delta = _str_tuple(truth_row.get("actual_delta_primitives", []))
        if delta:
            selected = set(_selected_primitives(queue_row, truth_row))
            filtered = tuple(primitive for primitive in delta if primitive in selected)
            return filtered or delta
    return tuple(
        primitive
        for primitive, coverage_status in coverage.items()
        if coverage_status != "exact_exists"
    )


def _coverage_updates_for_row(
    queue_row: dict[str, Any],
    truth_row: dict[str, Any] | None,
) -> dict[str, str]:
    primitives = _selected_primitives(queue_row, truth_row)
    if truth_row is None:
        return {primitive: "source_discovery_needed" for primitive in primitives}
    raw_coverage = truth_row.get("coverage_by_primitive", {})
    truth_coverage = {
        str(key): str(value)
        for key, value in raw_coverage.items()
        if isinstance(raw_coverage, dict) and str(key) and str(value)
    }
    return {
        primitive: truth_coverage.get(primitive, "source_discovery_needed")
        for primitive in primitives
    }


def _lean_grounding_hit(primitive: str, coverage_status: str) -> dict[str, object]:
    exact = coverage_status == "exact_exists"
    return {
        "primitive": primitive,
        "coverage_status": coverage_status,
        "hit_status": "benchmark_exact_reuse_label"
        if exact
        else "benchmark_no_exact_declaration_label",
        "declaration": f"benchmark_route_truth.{primitive}" if exact else "",
        "is_kernel_verified_declaration_hit": False,
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
    }


def _coverage_revision_reasons(
    coverage: dict[str, str],
    truth_row: dict[str, Any] | None,
) -> list[str]:
    reasons = []
    if truth_row is None:
        reasons.append(
            "no benchmark route-truth match; formal-library coverage must be searched"
        )
    for primitive, coverage_status in coverage.items():
        if coverage_status != "exact_exists":
            reasons.append(f"{primitive} classified as {coverage_status}")
    return reasons


def _route_revision_reasons(
    queue_row: dict[str, Any],
    truth_row: dict[str, Any] | None,
    coverage: dict[str, str],
) -> list[str]:
    reasons = _coverage_revision_reasons(coverage, truth_row)
    evaluation_signal = str(queue_row.get("evaluation_signal", ""))
    if evaluation_signal and evaluation_signal != "no_evaluation_signal":
        reasons.append(f"evaluation signal: {evaluation_signal}")
    prover_status = str(queue_row.get("prover_feedback_status", ""))
    if _is_failed_prover_feedback(prover_status):
        reasons.append(f"prover feedback status: {prover_status}")
    return reasons or ["route revision hook requested an explicit revised DAG"]


def _route_evidence_nodes(
    source_refs: tuple[str, ...],
    primitives: tuple[str, ...],
    *,
    matched_truth: bool,
) -> tuple[dict[str, object], ...]:
    return tuple(
        {
            "node_id": "route_source:" + stable_hash([source_ref, primitives])[:12],
            "kind": "source_ref",
            "label": source_ref,
            "supports_primitives": primitives,
            "evidence_status": "benchmark_route_truth"
            if matched_truth
            else "manual_source_search_required",
        }
        for source_ref in source_refs
    )


def _informal_dag_nodes(
    primitives: tuple[str, ...],
    source_refs: tuple[str, ...],
) -> tuple[dict[str, object], ...]:
    return tuple(
        {
            "node_id": "informal_route_primitive:" + stable_hash([primitive])[:12],
            "kind": "required_primitive",
            "label": primitive,
            "source_refs": source_refs,
            "evidence_status": "route_revision_candidate_not_proof",
        }
        for primitive in primitives
    )


def _lean_dag_nodes(coverage: dict[str, str]) -> tuple[dict[str, object], ...]:
    return tuple(
        {
            "node_id": "lean_realization_primitive:" + stable_hash([primitive])[:12],
            "kind": _lean_node_kind(coverage_status),
            "label": primitive,
            "coverage_status": coverage_status,
            "planned_action": _planned_action(coverage_status),
            "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        }
        for primitive, coverage_status in coverage.items()
    )


def _is_formal_library_grounding_hook(hook_kind: str) -> bool:
    return hook_kind in {"formal_library_grounding", "lean_library_grounding"}


def _lean_node_kind(coverage_status: str) -> str:
    return {
        "exact_exists": "existing_reuse",
        "wrapper_needed": "wrapper",
        "bridge_needed": "bridge_lemma",
        "source_discovery_needed": "source_discovery",
        "theory_missing": "new_theory",
    }.get(coverage_status, "coverage_review")


def _planned_action(coverage_status: str) -> str:
    return {
        "exact_exists": "reuse_existing_declaration_after_live_search",
        "wrapper_needed": "add_statement_wrapper_or_notation_bridge",
        "bridge_needed": "prove_minimal_bridge_lemma",
        "source_discovery_needed": "run_literature_and_library_source_discovery",
        "theory_missing": "add_new_primitive_theory_only_if_unavoidable",
    }.get(coverage_status, "manual_coverage_review")


def _route_revision_summary(
    queue_row: dict[str, Any],
    truth_row: dict[str, Any] | None,
    selected: tuple[str, ...],
    delta: tuple[str, ...],
) -> str:
    display_name = str(queue_row.get("display_name", "theorem"))
    if truth_row is None:
        return (
            f"Revise {display_name} by first collecting source-backed route evidence "
            "and live Lean coverage for the queued primitives."
        )
    notes = str(truth_row.get("notes", ""))
    return (
        f"Revise {display_name} toward benchmark route truth: "
        f"selected={len(selected)} primitives, delta={len(delta)} primitives. {notes}"
    ).strip()


def _is_failed_prover_feedback(status: str) -> bool:
    normalized = status.strip().lower()
    if not normalized:
        return False
    if normalized in {
        "no_calibration_signal",
        "awaiting_full_route_attempt",
        "awaiting_leaf_route_attempt",
        "not_attempted",
        "missing_attempt",
    }:
        return False
    return any(
        token in normalized
        for token in (
            "fail",
            "failed",
            "residual",
            "rejected",
            "error",
            "timeout",
            "unclosed",
            "not_kernel_verified",
        )
    )


def _str_tuple(values: Any) -> tuple[str, ...]:
    if isinstance(values, str):
        return (values,) if values else tuple()
    if not isinstance(values, (list, tuple, set)):
        return tuple()
    return tuple(dict.fromkeys(str(item) for item in values if str(item)))


def _read_json(path: Path, errors: list[str]) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        errors.append(f"missing JSON file: {path}")
        return {}
    except Exception as exc:
        errors.append(f"failed to parse {path}: {type(exc).__name__}: {exc}")
        return {}
    return payload if isinstance(payload, dict) else {}


def _markdown_report(payload: dict[str, object]) -> str:
    lines = [
        "# Formalization Gap Planner Refinement Adapter",
        "",
        f"- Queue rows: {payload.get('n_queue_rows')}",
        f"- Responses: {payload.get('n_responses')}",
        f"- Response schema valid: {payload.get('n_response_schema_valid')}/{payload.get('n_responses')}",
        f"- Ground-truth matched: {payload.get('n_ground_truth_matched')}",
        f"- Route revisions recommended: {payload.get('n_route_revision_recommended')}",
        f"- All OK: {payload.get('all_ok')}",
        "",
        "## Boundary",
        "",
        str(payload.get("proof_evidence_boundary", PROOF_EVIDENCE_BOUNDARY)),
        "",
        "## Responses",
        "",
    ]
    for row in payload.get("responses", []):
        if not isinstance(row, dict):
            continue
        lines.append(
            f"- `{row.get('display_name')}` {row.get('evidence_kind')} "
            f"revision={row.get('route_revision_recommended')}"
        )
    return "\n".join(lines) + "\n"
