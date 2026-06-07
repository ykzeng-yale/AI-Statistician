from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from .fingerprint import stable_hash
from .formalization_gap_planner_llm_route_planner import (
    export_formalization_gap_planner_llm_route_planner,
)
from .formalization_gap_planner_standalone import (
    FORMALIZATION_GAP_PLANNER_STANDALONE_INPUT_COMPONENT,
    FORMALIZATION_GAP_PLANNER_STANDALONE_INPUT_SCHEMA_ID,
    export_formalization_gap_planner_standalone_plan,
    validate_standalone_input_payload,
)


FORMALIZATION_GAP_PLANNER_RUNTIME_HANDOFF_AUDIT_SCHEMA_VERSION = 1
RUNTIME_HANDOFF_AUDIT_ROW_SCHEMA_ID = (
    "urn:ai-statistician:schemas:"
    "formalization-gap-planner-runtime-handoff-audit-row:1"
)
PROOF_EVIDENCE_STATUS = (
    "FORMALIZATION_GAP_PLANNER_RUNTIME_HANDOFF_AUDIT_NOT_PROOF_EVIDENCE"
)
PROOF_EVIDENCE_BOUNDARY = (
    "Formalization gap planner runtime handoff audit rows validate that AI "
    "Statistician runtime bridge artifacts are replayable as standalone "
    "formalization-gap planner input and that LLM route-planner handoffs remain "
    "cost-controlled until explicitly invoked. They are audit evidence, not "
    "theorem proof evidence."
)
RUNTIME_BRIDGE_PROOF_EVIDENCE_STATUS = (
    "RUNTIME_FORMALIZATION_GAP_PLANNER_BRIDGE_NOT_PROOF_EVIDENCE"
)


@dataclass(frozen=True)
class FormalizationGapPlannerRuntimeHandoffAuditCheck:
    schema_version: int
    check_id: str
    check_name: str
    category: str
    handoff_id: str
    bridge_id: str
    expected: str
    observed: str
    ok: bool
    severity: str
    errors: tuple[str, ...] = ()


def audit_formalization_gap_planner_runtime_handoffs(
    runtime_formalization_gap_planner_handoffs_jsonl: Path,
    out_dir: Path | None = None,
    *,
    run_smoke: bool = True,
) -> dict[str, object]:
    """Audit runtime-to-standalone formalization-gap planner handoff rows.

    The smoke path is intentionally offline. It replays the standalone planner
    and stages Anthropic LLM route-planner request packets without
    ``--invoke-provider`` or API calls.
    """

    errors: list[str] = []
    handoffs_path = runtime_formalization_gap_planner_handoffs_jsonl
    handoff_rows = _read_jsonl(handoffs_path, errors)
    smoke_root = out_dir / "runtime_handoff_smoke" if out_dir is not None else None
    checks: list[FormalizationGapPlannerRuntimeHandoffAuditCheck] = [
        _check(
            "handoff_jsonl_exists",
            "artifacts",
            "",
            "",
            "handoff JSONL file exists",
            str(handoffs_path.exists()),
            handoffs_path.exists(),
        ),
        _check(
            "handoff_rows_present",
            "artifacts",
            "",
            "",
            "at least one runtime handoff row",
            str(len(handoff_rows)),
            bool(handoff_rows),
        ),
    ]
    smoke_summaries: list[dict[str, object]] = []
    for idx, handoff in enumerate(handoff_rows):
        row_checks, smoke_summary = _audit_handoff_row(
            handoff,
            row_index=idx,
            run_smoke=run_smoke,
            smoke_root=smoke_root,
        )
        checks.extend(row_checks)
        smoke_summaries.append(smoke_summary)

    check_dicts = [asdict(check) for check in checks]
    row_schema = runtime_handoff_audit_row_json_schema()
    row_schema_errors = [
        validate_runtime_handoff_audit_row(row, row_schema) for row in check_dicts
    ]
    n_row_schema_valid = sum(1 for row_errors in row_schema_errors if not row_errors)
    by_category: dict[str, int] = {}
    for check in checks:
        by_category[check.category] = by_category.get(check.category, 0) + 1
    payload: dict[str, object] = {
        "schema_version": FORMALIZATION_GAP_PLANNER_RUNTIME_HANDOFF_AUDIT_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "component_name": "formalization_gap_planner_runtime_handoff_audit",
        "runtime_formalization_gap_planner_handoffs_jsonl": str(handoffs_path),
        "run_smoke": run_smoke,
        "smoke_root": str(smoke_root or ""),
        "n_handoffs": len(handoff_rows),
        "n_checks": len(checks),
        "n_ok": sum(1 for check in checks if check.ok),
        "n_failed": sum(1 for check in checks if not check.ok),
        "n_row_schema_valid": n_row_schema_valid,
        "n_row_schema_invalid": len(row_schema_errors) - n_row_schema_valid,
        "n_seed_schema_valid": sum(
            1 for summary in smoke_summaries if summary.get("seed_schema_ok")
        ),
        "n_cost_control_ok": sum(
            1 for summary in smoke_summaries if summary.get("cost_control_ok")
        ),
        "n_live_explicit_ok": sum(
            1 for summary in smoke_summaries if summary.get("live_explicit_ok")
        ),
        "n_standalone_smoke_ok": sum(
            1 for summary in smoke_summaries if summary.get("standalone_smoke_ok")
        ),
        "n_llm_prompt_smoke_ok": sum(
            1 for summary in smoke_summaries if summary.get("llm_prompt_smoke_ok")
        ),
        "n_llm_prompt_packets": sum(
            int(summary.get("llm_prompt_packets", 0) or 0)
            for summary in smoke_summaries
        ),
        "n_llm_prompt_awaiting_response": sum(
            int(summary.get("llm_prompt_awaiting_response", 0) or 0)
            for summary in smoke_summaries
        ),
        "n_seed_routes": sum(
            int(summary.get("seed_routes", 0) or 0) for summary in smoke_summaries
        ),
        "n_seed_primitives": sum(
            int(summary.get("seed_primitives", 0) or 0)
            for summary in smoke_summaries
        ),
        "n_seed_residual_goals": sum(
            int(summary.get("seed_residual_goals", 0) or 0)
            for summary in smoke_summaries
        ),
        "n_seed_candidate_declaration_rows": sum(
            int(summary.get("seed_candidate_declaration_rows", 0) or 0)
            for summary in smoke_summaries
        ),
        "n_seed_primitives_with_candidate_declaration_rows": sum(
            int(summary.get("seed_primitives_with_candidate_declaration_rows", 0) or 0)
            for summary in smoke_summaries
        ),
        "by_category": dict(sorted(by_category.items())),
        "checks": check_dicts,
        "row_schema_errors": row_schema_errors,
        "runtime_handoff_audit_row_schema": row_schema,
        "smoke_summaries": smoke_summaries,
        "all_ok": (
            not errors
            and bool(handoff_rows)
            and all(check.ok for check in checks)
            and n_row_schema_valid == len(row_schema_errors)
        ),
        "errors": errors,
        "runtime_handoff_audit_fingerprint": stable_hash(check_dicts),
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
        "limitations": [
            "prompt smoke runs stage request packets only and do not call Anthropic",
            "standalone planner replay is route-planning evidence, not proof evidence",
            "semantic adequacy still requires source-grounding and target-prover replay",
        ],
    }
    if out_dir is not None:
        _write_outputs(out_dir, payload)
    return payload


def runtime_handoff_audit_row_json_schema() -> dict[str, object]:
    required = [
        "schema_version",
        "check_id",
        "check_name",
        "category",
        "handoff_id",
        "bridge_id",
        "expected",
        "observed",
        "ok",
        "severity",
        "errors",
    ]
    string_array = {"type": "array", "items": {"type": "string"}}
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": RUNTIME_HANDOFF_AUDIT_ROW_SCHEMA_ID,
        "title": "Formalization gap planner runtime handoff audit check row",
        "type": "object",
        "additionalProperties": False,
        "required": required,
        "properties": {
            "schema_version": {
                "type": "integer",
                "const": FORMALIZATION_GAP_PLANNER_RUNTIME_HANDOFF_AUDIT_SCHEMA_VERSION,
            },
            "check_id": {"type": "string", "minLength": 1},
            "check_name": {"type": "string", "minLength": 1},
            "category": {
                "type": "string",
                "enum": [
                    "artifacts",
                    "cost_control",
                    "llm_prompt_smoke",
                    "proof_boundary",
                    "row",
                    "standalone_seed",
                    "standalone_smoke",
                    "target_prover",
                ],
            },
            "handoff_id": {"type": "string"},
            "bridge_id": {"type": "string"},
            "expected": {"type": "string"},
            "observed": {"type": "string"},
            "ok": {"type": "boolean"},
            "severity": {"type": "string", "enum": ["error", "warning", "info"]},
            "errors": string_array,
        },
    }


def validate_runtime_handoff_audit_row(
    row: Mapping[str, object],
    schema: Mapping[str, object] | None = None,
) -> list[str]:
    row_schema = schema or runtime_handoff_audit_row_json_schema()
    if not isinstance(row, Mapping):
        return ["row must be an object"]
    errors: list[str] = []
    required = tuple(row_schema.get("required", ()))
    for field_name in required:
        if field_name not in row:
            errors.append(f"{field_name} required")
    properties = row_schema.get("properties", {})
    if isinstance(properties, Mapping):
        for field_name, field_schema in properties.items():
            if field_name in row and isinstance(field_schema, Mapping):
                errors.extend(_schema_property_errors(field_name, row[field_name], field_schema))
    allowed = set(required)
    for field_name in row:
        if field_name not in allowed:
            errors.append(f"{field_name} unexpected")
    return sorted(set(errors))


def _audit_handoff_row(
    handoff: Mapping[str, Any],
    *,
    row_index: int,
    run_smoke: bool,
    smoke_root: Path | None,
) -> tuple[list[FormalizationGapPlannerRuntimeHandoffAuditCheck], dict[str, object]]:
    handoff_id = str(handoff.get("handoff_id", f"row:{row_index}"))
    bridge_id = str(handoff.get("bridge_id", ""))
    seed_path = Path(str(handoff.get("standalone_seed_path", "")))
    standalone_plan_cli = str(handoff.get("standalone_plan_cli", ""))
    prompt_cli = str(handoff.get("llm_route_planner_prompt_cli", ""))
    live_cli = str(handoff.get("llm_route_planner_live_cli", ""))
    handoff_target = str(handoff.get("target_prover_family", "")).strip()
    summary: dict[str, object] = {
        "handoff_id": handoff_id,
        "bridge_id": bridge_id,
        "standalone_seed_path": str(seed_path),
        "target_prover_family": handoff_target,
        "seed_exists": seed_path.exists(),
        "seed_schema_ok": False,
        "cost_control_ok": False,
        "live_explicit_ok": False,
        "standalone_smoke_ok": False,
        "llm_prompt_smoke_ok": False,
        "llm_prompt_packets": 0,
        "llm_prompt_awaiting_response": 0,
        "seed_routes": 0,
        "seed_primitives": 0,
        "seed_residual_goals": 0,
        "seed_candidate_declaration_rows": 0,
        "seed_primitives_with_candidate_declaration_rows": 0,
    }
    seed_errors: list[str] = []
    seed_payload = _read_json(seed_path, seed_errors)
    validation_errors = validate_standalone_input_payload(seed_payload)
    seed_schema_ok = not seed_errors and not validation_errors
    summary["seed_schema_ok"] = seed_schema_ok
    summary.update(_seed_context_counts(seed_payload))
    seed_target = str(seed_payload.get("target_prover_family", "")).strip()
    cost_control_ok = _prompt_cli_cost_control_ok(prompt_cli)
    live_explicit_ok = _live_cli_explicit_ok(live_cli)
    summary["cost_control_ok"] = cost_control_ok
    summary["live_explicit_ok"] = live_explicit_ok
    checks = [
        _row_check(
            "row_artifact_kind",
            "row",
            handoff_id,
            bridge_id,
            "RuntimeFormalizationGapPlannerHandoff",
            str(handoff.get("artifact_kind", "")),
            handoff.get("artifact_kind") == "RuntimeFormalizationGapPlannerHandoff",
        ),
        _row_check(
            "row_bridge_id_present",
            "row",
            handoff_id,
            bridge_id,
            "bridge_id nonempty",
            bridge_id,
            bool(bridge_id),
        ),
        _row_check(
            "row_seed_path_exists",
            "standalone_seed",
            handoff_id,
            bridge_id,
            "standalone seed path exists",
            str(seed_path.exists()),
            seed_path.exists(),
        ),
        _row_check(
            "row_seed_component",
            "standalone_seed",
            handoff_id,
            bridge_id,
            FORMALIZATION_GAP_PLANNER_STANDALONE_INPUT_COMPONENT,
            str(seed_payload.get("component_name", "")),
            seed_payload.get("component_name")
            == FORMALIZATION_GAP_PLANNER_STANDALONE_INPUT_COMPONENT,
        ),
        _row_check(
            "row_target_prover_family_present",
            "target_prover",
            handoff_id,
            bridge_id,
            "handoff target_prover_family nonempty",
            handoff_target,
            bool(handoff_target),
        ),
        _row_check(
            "row_seed_target_prover_family_present",
            "target_prover",
            handoff_id,
            bridge_id,
            "standalone seed target_prover_family nonempty",
            seed_target,
            bool(seed_target),
        ),
        _row_check(
            "row_seed_target_prover_family_matches_handoff",
            "target_prover",
            handoff_id,
            bridge_id,
            handoff_target or "<handoff target>",
            seed_target,
            bool(handoff_target) and seed_target == handoff_target,
        ),
        _row_check(
            "row_seed_schema_valid",
            "standalone_seed",
            handoff_id,
            bridge_id,
            "validate_standalone_input_payload has no errors",
            "; ".join([*seed_errors, *validation_errors]),
            seed_schema_ok,
        ),
        _row_check(
            "row_seed_routes_present",
            "standalone_seed",
            handoff_id,
            bridge_id,
            "at least one seed route",
            str(len(seed_payload.get("routes", [])) if isinstance(seed_payload.get("routes"), list) else 0),
            isinstance(seed_payload.get("routes"), list) and bool(seed_payload.get("routes")),
        ),
        _row_check(
            "row_recommended_provider",
            "cost_control",
            handoff_id,
            bridge_id,
            "anthropic",
            str(handoff.get("recommended_llm_provider", "")),
            handoff.get("recommended_llm_provider") == "anthropic",
        ),
        _row_check(
            "row_recommended_model_tier",
            "cost_control",
            handoff_id,
            bridge_id,
            "auto",
            str(handoff.get("recommended_model_tier", "")),
            handoff.get("recommended_model_tier") == "auto",
        ),
        _row_check(
            "row_standalone_cli_present",
            "row",
            handoff_id,
            bridge_id,
            "formalization-gap-planner-standalone-plan command",
            standalone_plan_cli,
            "formalization-gap-planner-standalone-plan" in standalone_plan_cli,
        ),
        _row_check(
            "row_prompt_cli_cost_control",
            "cost_control",
            handoff_id,
            bridge_id,
            "Anthropic auto prompt-only command without --invoke-provider",
            prompt_cli,
            cost_control_ok,
        ),
        _row_check(
            "row_live_cli_explicit",
            "cost_control",
            handoff_id,
            bridge_id,
            "Anthropic auto command with explicit --invoke-provider",
            live_cli,
            live_explicit_ok,
        ),
        _row_check(
            "row_cost_control_text",
            "cost_control",
            handoff_id,
            bridge_id,
            "cost_control explains prompt first and explicit live execution",
            str(handoff.get("cost_control", "")),
            "prompt" in str(handoff.get("cost_control", "")).lower()
            and "explicit" in str(handoff.get("cost_control", "")).lower(),
        ),
        _row_check(
            "row_proof_evidence_status",
            "proof_boundary",
            handoff_id,
            bridge_id,
            RUNTIME_BRIDGE_PROOF_EVIDENCE_STATUS,
            str(handoff.get("proof_evidence_status", "")),
            handoff.get("proof_evidence_status") == RUNTIME_BRIDGE_PROOF_EVIDENCE_STATUS,
        ),
        _row_check(
            "row_proof_evidence_boundary",
            "proof_boundary",
            handoff_id,
            bridge_id,
            "not theorem proof evidence",
            str(handoff.get("proof_evidence_boundary", ""))[:180],
            "not theorem proof evidence"
            in str(handoff.get("proof_evidence_boundary", "")).lower(),
        ),
        _row_check(
            "row_no_kernel_proof_claim",
            "proof_boundary",
            handoff_id,
            bridge_id,
            "no kernel-verified/proved claim",
            _proof_claim_observed(handoff),
            not _has_kernel_proof_claim(handoff),
        ),
    ]
    if run_smoke and seed_schema_ok:
        standalone_ok, standalone_observed = _run_standalone_smoke(
            seed_path,
            handoff_id=handoff_id,
            smoke_root=smoke_root,
        )
        summary["standalone_smoke_ok"] = standalone_ok
        checks.append(
            _row_check(
                "row_standalone_smoke",
                "standalone_smoke",
                handoff_id,
                bridge_id,
                "standalone planner all_ok true",
                standalone_observed,
                standalone_ok,
            )
        )
        llm_ok, llm_observed, llm_counts = _run_llm_prompt_smoke(
            seed_path,
            handoff_id=handoff_id,
            smoke_root=smoke_root,
        )
        summary.update(llm_counts)
        summary["llm_prompt_smoke_ok"] = llm_ok
        checks.append(
            _row_check(
                "row_llm_prompt_smoke",
                "llm_prompt_smoke",
                handoff_id,
                bridge_id,
                "prompt-only Anthropic route planner stages awaiting requests",
                llm_observed,
                llm_ok,
            )
        )
    elif run_smoke:
        checks.extend(
            [
                _row_check(
                    "row_standalone_smoke",
                    "standalone_smoke",
                    handoff_id,
                    bridge_id,
                    "standalone planner all_ok true",
                    "skipped because seed schema invalid",
                    False,
                ),
                _row_check(
                    "row_llm_prompt_smoke",
                    "llm_prompt_smoke",
                    handoff_id,
                    bridge_id,
                    "prompt-only Anthropic route planner stages awaiting requests",
                    "skipped because seed schema invalid",
                    False,
                ),
            ]
        )
    return checks, summary


def _seed_context_counts(seed_payload: Mapping[str, Any]) -> dict[str, int]:
    routes = [
        dict(route)
        for route in seed_payload.get("routes", [])
        if isinstance(route, Mapping)
    ]
    primitives = [
        dict(primitive)
        for route in routes
        for primitive in route.get("primitives", [])
        if isinstance(primitive, Mapping)
    ]
    residual_goals = [
        residual_goal
        for route in routes
        for residual_goal in _str_tuple(
            _dict_value(route.get("replan_metadata", {})).get("residual_goals", [])
        )
    ]
    candidate_declaration_rows = [
        row
        for primitive in primitives
        for row in _dict_tuple(primitive.get("candidate_declaration_rows", []))
    ]
    return {
        "seed_routes": len(routes),
        "seed_primitives": len(primitives),
        "seed_residual_goals": len(residual_goals),
        "seed_candidate_declaration_rows": len(candidate_declaration_rows),
        "seed_primitives_with_candidate_declaration_rows": sum(
            1 for primitive in primitives if primitive.get("candidate_declaration_rows")
        ),
    }


def _run_standalone_smoke(
    seed_path: Path,
    *,
    handoff_id: str,
    smoke_root: Path | None,
) -> tuple[bool, str]:
    try:
        payload = export_formalization_gap_planner_standalone_plan(
            seed_path,
            _smoke_dir(smoke_root, handoff_id) / "standalone_plan"
            if smoke_root is not None
            else None,
            max_routes=20,
        )
    except Exception as exc:  # pragma: no cover - defensive audit surface
        return False, f"{type(exc).__name__}: {exc}"
    return bool(payload.get("all_ok", False)), (
        f"all_ok={payload.get('all_ok')} "
        f"goal_plans={payload.get('n_goal_plans')} "
        f"errors={payload.get('errors')}"
    )


def _run_llm_prompt_smoke(
    seed_path: Path,
    *,
    handoff_id: str,
    smoke_root: Path | None,
) -> tuple[bool, str, dict[str, int]]:
    try:
        payload = export_formalization_gap_planner_llm_route_planner(
            seed_path,
            _smoke_dir(smoke_root, handoff_id) / "llm_route_planner_prompt"
            if smoke_root is not None
            else None,
            provider_name="anthropic",
            model_tier="auto",
            max_repair_attempts=1,
            invoke_provider=False,
        )
    except Exception as exc:  # pragma: no cover - defensive audit surface
        return (
            False,
            f"{type(exc).__name__}: {exc}",
            {"llm_prompt_packets": 0, "llm_prompt_awaiting_response": 0},
        )
    n_packets = int(payload.get("n_request_packets", 0) or 0)
    n_awaiting = int(payload.get("n_awaiting_llm_response", 0) or 0)
    ok = (
        bool(payload.get("all_ok", False))
        and n_packets > 0
        and n_awaiting == n_packets
        and bool(payload.get("invoke_provider", True)) is False
        and str(payload.get("provider_name", "")) == "anthropic"
        and str(payload.get("model_tier_selection_mode", "")) == "auto"
    )
    return ok, (
        f"all_ok={payload.get('all_ok')} provider={payload.get('provider_name')} "
        f"invoke_provider={payload.get('invoke_provider')} "
        f"tier_mode={payload.get('model_tier_selection_mode')} "
        f"packets={n_packets} awaiting={n_awaiting} errors={payload.get('errors')}"
    ), {
        "llm_prompt_packets": n_packets,
        "llm_prompt_awaiting_response": n_awaiting,
    }


def _prompt_cli_cost_control_ok(prompt_cli: str) -> bool:
    return (
        "formalization-gap-planner-llm-route-planner" in prompt_cli
        and "--provider anthropic" in prompt_cli
        and "--model-tier auto" in prompt_cli
        and "--max-repair-attempts 1" in prompt_cli
        and "--invoke-provider" not in prompt_cli
    )


def _live_cli_explicit_ok(live_cli: str) -> bool:
    return (
        "formalization-gap-planner-llm-route-planner" in live_cli
        and "--provider anthropic" in live_cli
        and "--model-tier auto" in live_cli
        and "--max-repair-attempts 1" in live_cli
        and "--invoke-provider" in live_cli
    )


def _smoke_dir(smoke_root: Path | None, handoff_id: str) -> Path:
    root = smoke_root or Path()
    return root / _safe_identifier(handoff_id)


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


def _read_jsonl(path: Path, errors: list[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        errors.append(f"missing JSONL file: {path}")
        return []
    except Exception as exc:
        errors.append(f"failed to read {path}: {type(exc).__name__}: {exc}")
        return []
    for idx, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except Exception as exc:
            errors.append(f"failed to parse {path}:{idx}: {type(exc).__name__}: {exc}")
            continue
        if isinstance(value, dict):
            rows.append(value)
        else:
            errors.append(f"{path}:{idx} is not a JSON object")
    return rows


def _dict_value(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _dict_tuple(value: Any) -> tuple[dict[str, object], ...]:
    if not isinstance(value, (list, tuple, set)):
        return tuple()
    return tuple(dict(item) for item in value if isinstance(item, Mapping))


def _str_tuple(value: Any) -> tuple[str, ...]:
    if value is None:
        return tuple()
    if isinstance(value, str):
        return (value,) if value else tuple()
    if isinstance(value, Mapping):
        return tuple(str(key) for key in value if str(key))
    if isinstance(value, (list, tuple, set)):
        return tuple(str(item) for item in value if str(item))
    return (str(value),) if str(value) else tuple()


def _check(
    check_name: str,
    category: str,
    handoff_id: str,
    bridge_id: str,
    expected: str,
    observed: str,
    ok: bool,
    *,
    severity: str = "error",
) -> FormalizationGapPlannerRuntimeHandoffAuditCheck:
    return FormalizationGapPlannerRuntimeHandoffAuditCheck(
        schema_version=FORMALIZATION_GAP_PLANNER_RUNTIME_HANDOFF_AUDIT_SCHEMA_VERSION,
        check_id="formalization_gap_planner_runtime_handoff_audit:"
        + stable_hash([check_name, category, handoff_id, bridge_id, expected])[:16],
        check_name=check_name,
        category=category,
        handoff_id=handoff_id,
        bridge_id=bridge_id,
        expected=expected,
        observed=observed,
        ok=ok,
        severity=severity,
        errors=() if ok else (f"expected {expected}; observed {observed}",),
    )


def _row_check(
    check_name: str,
    category: str,
    handoff_id: str,
    bridge_id: str,
    expected: str,
    observed: str,
    ok: bool,
    *,
    severity: str = "error",
) -> FormalizationGapPlannerRuntimeHandoffAuditCheck:
    return _check(
        f"{check_name}:{_safe_identifier(handoff_id)[:40]}",
        category,
        handoff_id,
        bridge_id,
        expected,
        observed,
        ok,
        severity=severity,
    )


def _schema_property_errors(
    field_name: str,
    value: object,
    schema: Mapping[str, object],
) -> list[str]:
    errors: list[str] = []
    expected_type = schema.get("type")
    if expected_type == "string":
        if not isinstance(value, str):
            errors.append(f"{field_name} must be string")
            return errors
        if isinstance(schema.get("minLength"), int) and len(value) < int(schema["minLength"]):
            errors.append(f"{field_name} must be non-empty")
        pattern = schema.get("pattern")
        if isinstance(pattern, str) and not re.search(pattern, value):
            errors.append(f"{field_name} must match {pattern}")
        enum = schema.get("enum")
        if isinstance(enum, list) and value not in enum:
            errors.append(f"{field_name} must be one of {enum}")
        const = schema.get("const")
        if const is not None and value != const:
            errors.append(f"{field_name} must equal {const}")
    elif expected_type == "integer":
        if not isinstance(value, int) or isinstance(value, bool):
            errors.append(f"{field_name} must be integer")
            return errors
        const = schema.get("const")
        if const is not None and value != const:
            errors.append(f"{field_name} must equal {const}")
    elif expected_type == "boolean":
        if not isinstance(value, bool):
            errors.append(f"{field_name} must be boolean")
    elif expected_type == "array":
        if not isinstance(value, (list, tuple)):
            errors.append(f"{field_name} must be array")
            return errors
        item_schema = schema.get("items", {})
        if isinstance(item_schema, Mapping) and item_schema.get("type") == "string":
            for index, item in enumerate(value):
                if not isinstance(item, str):
                    errors.append(f"{field_name}[{index}] must be string")
    return errors


def _has_kernel_proof_claim(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = str(key).lower()
            if key_text in {"kernel_verified", "full_frontier_theorem_proved"} and item is True:
                return True
            if key_text in {"proof_evidence_status", "claim_status"} and (
                "KERNEL_VERIFIED" in str(item) or "PROVED" in str(item)
            ):
                if "NOT_PROOF_EVIDENCE" not in str(item):
                    return True
            if _has_kernel_proof_claim(item):
                return True
    if isinstance(value, (list, tuple)):
        return any(_has_kernel_proof_claim(item) for item in value)
    return False


def _proof_claim_observed(value: Any) -> str:
    return "kernel/proved claim present" if _has_kernel_proof_claim(value) else "none"


def _safe_identifier(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("._") or "runtime_handoff"


def _write_outputs(out_dir: Path, payload: Mapping[str, object]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "formalization_gap_planner_runtime_handoff_audit_manifest.json").write_text(
        json.dumps(payload, indent=2, default=str),
        encoding="utf-8",
    )
    (out_dir / "formalization_gap_planner_runtime_handoff_audit.jsonl").write_text(
        "\n".join(
            json.dumps(row, sort_keys=True)
            for row in payload.get("checks", [])
            if isinstance(row, dict)
        )
        + ("\n" if payload.get("checks") else ""),
        encoding="utf-8",
    )
    (
        out_dir / "formalization_gap_planner_runtime_handoff_audit_row.schema.json"
    ).write_text(
        json.dumps(runtime_handoff_audit_row_json_schema(), indent=2),
        encoding="utf-8",
    )
    (out_dir / "formalization_gap_planner_runtime_handoff_audit.md").write_text(
        _markdown_report(payload),
        encoding="utf-8",
    )


def _markdown_report(payload: Mapping[str, object]) -> str:
    lines = [
        "# Formalization Gap Planner Runtime Handoff Audit",
        "",
        f"- Handoffs: {payload.get('n_handoffs')}",
        f"- Checks: {payload.get('n_ok')}/{payload.get('n_checks')}",
        f"- Cost control OK: {payload.get('n_cost_control_ok')}",
        f"- Standalone smoke OK: {payload.get('n_standalone_smoke_ok')}",
        f"- LLM prompt smoke OK: {payload.get('n_llm_prompt_smoke_ok')}",
        f"- Prompt packets: {payload.get('n_llm_prompt_packets')}",
        f"- Awaiting LLM response: {payload.get('n_llm_prompt_awaiting_response')}",
        f"- Seed routes/primitives: {payload.get('n_seed_routes')}/{payload.get('n_seed_primitives')}",
        f"- Seed residual goals: {payload.get('n_seed_residual_goals')}",
        (
            f"- Seed candidate declaration rows: "
            f"{payload.get('n_seed_candidate_declaration_rows')} "
            f"across {payload.get('n_seed_primitives_with_candidate_declaration_rows')} primitives"
        ),
        f"- All OK: {payload.get('all_ok')}",
        "",
        "## Boundary",
        "",
        str(payload.get("proof_evidence_boundary", PROOF_EVIDENCE_BOUNDARY)),
        "",
        "## Failed Checks",
        "",
    ]
    failed = [
        check
        for check in payload.get("checks", [])
        if isinstance(check, Mapping) and not check.get("ok")
    ]
    if not failed:
        lines.append("- none")
    for check in failed:
        lines.append(
            f"- `{check.get('check_name')}` category={check.get('category')} "
            f"handoff={check.get('handoff_id')} observed={check.get('observed')}"
        )
    return "\n".join(lines) + "\n"
