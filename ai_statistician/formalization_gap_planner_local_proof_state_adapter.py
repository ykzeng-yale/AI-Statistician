from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash
from .formalization_gap_planner_refinement_evidence import (
    PROOF_EVIDENCE_BOUNDARY,
    refinement_tool_response_json_schema,
    validate_refinement_tool_response_row,
)


FORMALIZATION_GAP_PLANNER_LOCAL_PROOF_STATE_ADAPTER_SCHEMA_VERSION = 1
PROOF_EVIDENCE_STATUS = (
    "FORMALIZATION_GAP_PLANNER_LOCAL_PROOF_STATE_ADAPTER_NOT_PROOF_EVIDENCE"
)
ADAPTER_TOOL_NAME = "local_lean_proof_state_adapter"
TARGET_PROVER_FAMILY = "lean4"
PLACEHOLDER_RE = re.compile(r"\b(sorry|admit|axiom)\b")
FORMAL_GAP_PLACEHOLDER_RE = re.compile(
    r"\bFORMAL_GAP\b|\bh_frontier_missing[A-Za-z0-9_']*"
)
LEAN_COMMAND_RE = re.compile(
    r"(?m)^\s*(import|namespace|section|variable|theorem|lemma|example|def|noncomputable)\b"
)


def export_formalization_gap_planner_local_proof_state_adapter_responses(
    formalization_gap_planner_refinement_queue_dir: Path,
    out_dir: Path | None = None,
    *,
    lean_project: Path | None = None,
    lean_timeout: int = 90,
    base_response_jsonl: Path | None = None,
    max_items: int = 0,
) -> dict[str, object]:
    """Emit proof-state feedback responses from local Lean when available."""

    errors: list[str] = []
    queue_manifest_path = (
        formalization_gap_planner_refinement_queue_dir
        / "formalization_gap_planner_refinement_queue_manifest.json"
    )
    queue_payload = _read_json(queue_manifest_path, errors)
    queue_rows = [
        row for row in queue_payload.get("rows", []) if isinstance(row, dict)
    ]
    if max_items > 0:
        queue_rows = queue_rows[:max_items]
    proof_rows = [
        row for row in queue_rows if str(row.get("hook_kind", "")) == "proof_state_feedback"
    ]
    target_proof_rows = [row for row in proof_rows if _row_targets_local_lean(row)]
    skipped_non_target_rows = [
        row for row in proof_rows if not _row_targets_local_lean(row)
    ]
    base_responses = _read_jsonl(base_response_jsonl, errors) if base_response_jsonl else []
    base_by_item = {
        str(row.get("refinement_item_id", "")): row
        for row in base_responses
        if str(row.get("refinement_item_id", ""))
    }
    lean_command = _lean_command(lean_project)
    responses = [
        _proof_state_response(
            row,
            lean_command=lean_command,
            lean_project=lean_project,
            lean_timeout=max(1, int(lean_timeout)),
        )
        for row in target_proof_rows
    ]
    merged_by_item = dict(base_by_item)
    for response in responses:
        merged_by_item[str(response.get("refinement_item_id", ""))] = response
    merged_responses = sorted(
        merged_by_item.values(),
        key=lambda row: (
            str(row.get("display_name", "")),
            str(row.get("evidence_kind", "")),
            str(row.get("refinement_item_id", "")),
        ),
    )
    response_schema = refinement_tool_response_json_schema()
    local_response_schema_errors = [
        validate_refinement_tool_response_row(response, response_schema)
        for response in responses
    ]
    merged_response_schema_errors = [
        validate_refinement_tool_response_row(response, response_schema)
        for response in merged_responses
    ]
    n_local_response_schema_valid = sum(
        1 for row_errors in local_response_schema_errors if not row_errors
    )
    n_merged_response_schema_valid = sum(
        1 for row_errors in merged_response_schema_errors if not row_errors
    )
    by_attempt_status = Counter(str(row.get("attempt_status", "")) for row in responses)
    by_attempt_class = Counter(
        str(row.get("prover_attempt_class", "")) for row in responses
    )
    payload: dict[str, object] = {
        "schema_version": FORMALIZATION_GAP_PLANNER_LOCAL_PROOF_STATE_ADAPTER_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "component_name": "formalization_gap_planner_local_proof_state_adapter",
        "target_prover_family": TARGET_PROVER_FAMILY,
        "formalization_gap_planner_refinement_queue_dir": str(
            formalization_gap_planner_refinement_queue_dir
        ),
        "formalization_gap_planner_refinement_queue_manifest": str(queue_manifest_path),
        "base_response_jsonl": str(base_response_jsonl or ""),
        "prover_project": str(lean_project or ""),
        "prover_timeout": lean_timeout,
        "prover_command": " ".join(lean_command) if lean_command else "",
        "prover_command_available": bool(lean_command),
        "lean_project": str(lean_project or ""),
        "lean_timeout": lean_timeout,
        "lean_command": " ".join(lean_command) if lean_command else "",
        "lean_command_available": bool(lean_command),
        "n_queue_rows": len(queue_rows),
        "n_proof_state_feedback_rows": len(proof_rows),
        "n_target_proof_state_feedback_rows": len(target_proof_rows),
        "n_skipped_non_target_proof_state_feedback_rows": len(
            skipped_non_target_rows
        ),
        "n_base_responses": len(base_responses),
        "n_local_proof_state_responses": len(responses),
        "n_merged_responses": len(merged_responses),
        "n_local_response_schema_valid": n_local_response_schema_valid,
        "n_local_response_schema_invalid": len(local_response_schema_errors)
        - n_local_response_schema_valid,
        "n_merged_response_schema_valid": n_merged_response_schema_valid,
        "n_merged_response_schema_invalid": len(merged_response_schema_errors)
        - n_merged_response_schema_valid,
        "local_response_schema_errors": local_response_schema_errors,
        "merged_response_schema_errors": merged_response_schema_errors,
        "n_target_prover_scaffold_accepted": by_attempt_class.get(
            "target_prover_scaffold_accepted", 0
        ),
        "n_target_prover_failed": by_attempt_class.get("target_prover_failed", 0),
        "n_target_prover_unavailable": by_attempt_class.get(
            "target_prover_unavailable", 0
        ),
        "n_non_target_prover_skeleton": by_attempt_class.get(
            "non_target_prover_skeleton", 0
        ),
        "n_kernel_scaffold_accepted": by_attempt_status.get("local_lean_scaffold_accepted", 0),
        "n_local_lean_failed": by_attempt_status.get("local_lean_failed", 0),
        "n_local_lean_unavailable": by_attempt_status.get("local_lean_unavailable", 0),
        "n_placeholder_blocked": by_attempt_status.get("placeholder_blocked", 0),
        "n_formal_gap_scaffold_blocked": by_attempt_status.get(
            "formal_gap_scaffold_blocked", 0
        ),
        "n_non_lean_skeleton": by_attempt_status.get("non_lean_skeleton", 0),
        "n_missing_skeleton": by_attempt_status.get("missing_theorem_skeleton", 0),
        "all_ok": not errors
        and bool(proof_rows)
        and len(responses) == len(target_proof_rows)
        and n_local_response_schema_valid == len(responses)
        and n_merged_response_schema_valid == len(merged_responses),
        "errors": errors,
        "by_prover_attempt_class": dict(sorted(by_attempt_class.items())),
        "by_attempt_status": dict(sorted(by_attempt_status.items())),
        "by_skipped_target_prover_family": dict(
            sorted(
                Counter(
                    _row_target_prover_family(row)
                    for row in skipped_non_target_rows
                ).items()
            )
        ),
        "responses": responses,
        "skipped_non_target_proof_state_feedback_rows": [
            {
                "refinement_item_id": str(row.get("refinement_item_id", "")),
                "route_id": str(row.get("route_id", "")),
                "display_name": str(row.get("display_name", "")),
                "target_prover_family": _row_target_prover_family(row),
                "skip_reason": (
                    "local Lean proof-state adapter handles only Lean target "
                    "prover rows; use target-prover adapter feedback for this row"
                ),
            }
            for row in skipped_non_target_rows
        ],
        "refinement_tool_response_schema": response_schema,
        "merged_response_ids": [
            str(row.get("refinement_item_id", "")) for row in merged_responses
        ],
        "responses_fingerprint": stable_hash(responses),
        "merged_responses_fingerprint": stable_hash(merged_responses),
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
        "limitations": [
            "local proof-state responses are refinement diagnostics, not target theorem proof evidence",
            "non-Lean proof-state rows are skipped so target-prover-specific adapters can answer them without Lean alias leakage",
            "accepted temporary scaffolds still require verifier replay and calibration before promotion",
            "placeholder skeletons are not sent to the target prover because sorry/admit can mask missing proof work",
            "FORMAL_GAP and h_frontier_missing skeletons are blocked before target-prover execution because they are roadmap scaffolds, not theorem proof candidates",
        ],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = (
            out_dir / "formalization_gap_planner_local_proof_state_adapter_manifest.json"
        )
        responses_path = (
            out_dir / "formalization_gap_planner_refinement_evidence_responses.jsonl"
        )
        local_responses_path = (
            out_dir / "formalization_gap_planner_local_proof_state_adapter_responses.jsonl"
        )
        response_schema_path = (
            out_dir / "formalization_gap_planner_refinement_tool_response.schema.json"
        )
        payload["manifest_path"] = str(manifest_path)
        payload["responses_jsonl"] = str(responses_path)
        payload["local_responses_jsonl"] = str(local_responses_path)
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
            "\n".join(json.dumps(row, sort_keys=True) for row in merged_responses)
            + ("\n" if merged_responses else ""),
            encoding="utf-8",
        )
        local_responses_path.write_text(
            "\n".join(json.dumps(row, sort_keys=True) for row in responses)
            + ("\n" if responses else ""),
            encoding="utf-8",
        )
        (out_dir / "formalization_gap_planner_local_proof_state_adapter.md").write_text(
            _markdown_report(payload),
            encoding="utf-8",
        )
    return payload


def _proof_state_response(
    queue_row: dict[str, Any],
    *,
    lean_command: tuple[str, ...],
    lean_project: Path | None,
    lean_timeout: int,
) -> dict[str, object]:
    skeleton = str(queue_row.get("theorem_skeleton", "")).strip()
    target_primitives = _str_tuple(queue_row.get("target_primitives", []))
    diagnostics: list[str] = []
    residual_goals: list[str] = []
    route_revision_reasons: list[str] = []
    attempt_status = ""
    if not skeleton:
        attempt_status = "missing_theorem_skeleton"
        diagnostics.append("proof-state feedback requires theorem_skeleton, but none was queued")
        residual_goals.extend(_residuals_for_primitives(target_primitives, "missing skeleton"))
    elif PLACEHOLDER_RE.search(skeleton):
        attempt_status = "placeholder_blocked"
        diagnostics.append("theorem_skeleton contains sorry/admit/axiom; local proof-state adapter did not run it")
        residual_goals.extend(_residuals_for_primitives(target_primitives, "placeholder proof"))
    elif FORMAL_GAP_PLACEHOLDER_RE.search(skeleton):
        attempt_status = "formal_gap_scaffold_blocked"
        diagnostics.append(
            "theorem_skeleton contains FORMAL_GAP or h_frontier_missing placeholder assumptions; local proof-state adapter did not treat it as proof-state acceptance"
        )
        residual_goals.extend(
            _residuals_for_primitives(target_primitives, "formal-gap placeholder scaffold")
        )
        route_revision_reasons.append(
            "replace h_frontier_missing/FORMAL_GAP scaffold with non-placeholder Lean theorem before proof-state acceptance"
        )
    elif not _looks_like_lean_command(skeleton):
        attempt_status = "non_lean_skeleton"
        diagnostics.append(
            "theorem_skeleton is not a Lean command; materialize a full theorem/lemma/example statement before proof-state feedback"
        )
        diagnostics.append(f"queued theorem_skeleton={skeleton[:160]!r}")
        residual_goals.extend(_residuals_for_primitives(target_primitives, "non-Lean theorem skeleton"))
        route_revision_reasons.append("materialize Lean theorem skeleton before proof-state feedback")
    elif not lean_command:
        attempt_status = "local_lean_unavailable"
        diagnostics.append("local Lean command unavailable; install lean or configure lake project")
        residual_goals.extend(_residuals_for_primitives(target_primitives, "local Lean unavailable"))
    else:
        result = _run_local_lean(
            _lean_source(skeleton),
            lean_command=lean_command,
            lean_project=lean_project,
            timeout_s=lean_timeout,
        )
        diagnostics.extend(result["diagnostics"])
        attempt_status = str(result["attempt_status"])
        if result["returncode"] == 0:
            diagnostics.append(
                "local Lean accepted the temporary proof-state scaffold; this is diagnostic feedback, not proof evidence"
            )
        else:
            residual_goals.extend(
                _residuals_for_primitives(target_primitives, result["first_error"] or "local Lean failed")
            )
            route_revision_reasons.append("local Lean failed on proof-state scaffold")
    route_revision_recommended = attempt_status in {
        "formal_gap_scaffold_blocked",
        "local_lean_failed",
        "non_lean_skeleton",
    }
    prover_attempt_class = _prover_attempt_class(attempt_status)
    return {
        "refinement_item_id": str(queue_row.get("refinement_item_id", "")),
        "route_id": str(queue_row.get("route_id", "")),
        "display_name": str(queue_row.get("display_name", "")),
        "evidence_kind": "prover_feedback",
        "tool_name": ADAPTER_TOOL_NAME,
        "target_prover_family": TARGET_PROVER_FAMILY,
        "prover_adapter_id": ADAPTER_TOOL_NAME,
        "attempt_status": attempt_status,
        "prover_attempt_class": prover_attempt_class,
        "prover_diagnostics": tuple(diagnostics or ["no proof-state diagnostic emitted"]),
        "residual_goals": tuple(sorted(dict.fromkeys(residual_goals))),
        "route_revision_recommended": route_revision_recommended,
        "route_revision_reasons": tuple(route_revision_reasons),
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
    }


def _row_targets_local_lean(row: dict[str, Any]) -> bool:
    target = _target_prover_key(_row_target_prover_family(row))
    return target in {"", "lean4"}


def _row_target_prover_family(row: dict[str, Any]) -> str:
    for field_name in ("target_prover_family", "target_prover"):
        text = str(row.get(field_name, "") or "").strip()
        if text:
            return text
    trace = row.get("llm_route_planner_hook_trace", {})
    if isinstance(trace, dict):
        for field_name in ("target_prover_family", "target_prover"):
            text = str(trace.get(field_name, "") or "").strip()
            if text:
                return text
    return ""


def _target_prover_key(value: object) -> str:
    key = re.sub(
        r"[^a-z0-9]+",
        "_",
        str(value or "").strip().lower(),
    ).strip("_")
    return {
        "lean": "lean4",
        "lean_4": "lean4",
        "coq": "rocq",
        "coq_rocq": "rocq",
        "rocq_coq": "rocq",
        "isabelle_hol": "isabelle",
    }.get(key, key)


def _run_local_lean(
    source: str,
    *,
    lean_command: tuple[str, ...],
    lean_project: Path | None,
    timeout_s: int,
) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="fgp_proof_state_") as tmp:
        lean_file = Path(tmp) / "ProofStateProbe.lean"
        lean_file.write_text(source, encoding="utf-8")
        command = (*lean_command, str(lean_file))
        try:
            proc = subprocess.run(
                command,
                cwd=str(lean_project) if lean_project is not None else None,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout_s,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            return {
                "attempt_status": "local_lean_failed",
                "returncode": -1,
                "diagnostics": [f"local Lean timed out after {timeout_s}s: {exc}"],
                "first_error": "local Lean timeout",
            }
        except Exception as exc:
            return {
                "attempt_status": "local_lean_failed",
                "returncode": -1,
                "diagnostics": [f"local Lean invocation failed: {type(exc).__name__}: {exc}"],
                "first_error": str(exc),
            }
    combined = "\n".join(item for item in (proc.stdout, proc.stderr) if item).strip()
    diagnostics = _diagnostic_lines(combined)
    return {
        "attempt_status": "local_lean_scaffold_accepted"
        if proc.returncode == 0
        else "local_lean_failed",
        "returncode": proc.returncode,
        "diagnostics": diagnostics
        or [f"local Lean exited with return code {proc.returncode}"],
        "first_error": diagnostics[0] if diagnostics and proc.returncode != 0 else "",
    }


def _lean_command(lean_project: Path | None) -> tuple[str, ...]:
    if lean_project is not None and shutil.which("lake") is not None:
        return ("lake", "env", "lean")
    if shutil.which("lean") is not None:
        return ("lean",)
    return tuple()


def _looks_like_lean_command(skeleton: str) -> bool:
    return bool(LEAN_COMMAND_RE.search(skeleton))


def _lean_source(skeleton: str) -> str:
    if "import " in skeleton or "namespace " in skeleton:
        return skeleton.rstrip() + "\n"
    return "\n".join(
        [
            "namespace FormalizationGapPlannerProofState",
            "",
            skeleton.rstrip(),
            "",
            "end FormalizationGapPlannerProofState",
            "",
        ]
    )


def _residuals_for_primitives(
    primitives: tuple[str, ...],
    reason: str,
) -> list[str]:
    return [f"{primitive}: {reason}" for primitive in primitives] or [reason]


def _prover_attempt_class(attempt_status: str) -> str:
    return {
        "local_lean_scaffold_accepted": "target_prover_scaffold_accepted",
        "local_lean_failed": "target_prover_failed",
        "local_lean_unavailable": "target_prover_unavailable",
        "non_lean_skeleton": "non_target_prover_skeleton",
        "placeholder_blocked": "placeholder_blocked",
        "formal_gap_scaffold_blocked": "formal_gap_scaffold_blocked",
        "missing_theorem_skeleton": "missing_theorem_skeleton",
    }.get(attempt_status, attempt_status or "unknown_prover_attempt")


def _diagnostic_lines(text: str) -> list[str]:
    if not text:
        return []
    lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            lines.append(stripped[:500])
    return lines[:20]


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


def _read_jsonl(path: Path | None, errors: list[str]) -> list[dict[str, Any]]:
    if path is None:
        return []
    rows: list[dict[str, Any]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        errors.append(f"missing JSONL file: {path}")
        return []
    for line_no, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except Exception as exc:
            errors.append(f"failed to parse {path}:{line_no}: {type(exc).__name__}: {exc}")
            continue
        if isinstance(payload, dict):
            rows.append(payload)
    return rows


def _str_tuple(values: Any) -> tuple[str, ...]:
    if isinstance(values, str):
        return (values,) if values else tuple()
    if not isinstance(values, (list, tuple, set)):
        return tuple()
    return tuple(dict.fromkeys(str(item) for item in values if str(item)))


def _markdown_report(payload: dict[str, object]) -> str:
    lines = [
        "# Formalization Gap Planner Local Proof-State Adapter",
        "",
        f"- Queue rows: {payload.get('n_queue_rows')}",
        f"- Proof-state rows: {payload.get('n_proof_state_feedback_rows')}",
        f"- Target proof-state rows: {payload.get('n_target_proof_state_feedback_rows')}",
        f"- Skipped non-target proof-state rows: {payload.get('n_skipped_non_target_proof_state_feedback_rows')}",
        f"- Local responses: {payload.get('n_local_proof_state_responses')}",
        f"- Merged responses: {payload.get('n_merged_responses')}",
        f"- Local response schema valid: {payload.get('n_local_response_schema_valid')}/{payload.get('n_local_proof_state_responses')}",
        f"- Merged response schema valid: {payload.get('n_merged_response_schema_valid')}/{payload.get('n_merged_responses')}",
        f"- Target prover scaffold accepted: {payload.get('n_target_prover_scaffold_accepted')}",
        f"- Target prover failed: {payload.get('n_target_prover_failed')}",
        f"- Target prover unavailable: {payload.get('n_target_prover_unavailable')}",
        f"- Non-target-prover skeleton: {payload.get('n_non_target_prover_skeleton')}",
        f"- Scaffold accepted: {payload.get('n_kernel_scaffold_accepted')}",
        f"- Local Lean failed: {payload.get('n_local_lean_failed')}",
        f"- Local Lean unavailable: {payload.get('n_local_lean_unavailable')}",
        f"- Placeholder blocked: {payload.get('n_placeholder_blocked')}",
        f"- Formal-gap scaffold blocked: {payload.get('n_formal_gap_scaffold_blocked')}",
        f"- Non-Lean skeleton: {payload.get('n_non_lean_skeleton')}",
        f"- All OK: {payload.get('all_ok')}",
        "",
        "## Boundary",
        "",
        str(payload.get("proof_evidence_boundary", PROOF_EVIDENCE_BOUNDARY)),
        "",
        "## Attempt Status",
        "",
    ]
    for status, count in dict(payload.get("by_attempt_status", {})).items():
        lines.append(f"- `{status}`: {count}")
    return "\n".join(lines) + "\n"
