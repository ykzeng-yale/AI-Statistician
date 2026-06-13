from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash


FORMAL_VERIFIER_AGENTIC_PROOF_EXECUTION_MATERIALIZER_SCHEMA_VERSION = 1
PROOF_EVIDENCE_STATUS = "AGENTIC_PROOF_EXECUTION_MATERIALIZER_NOT_PROOF_EVIDENCE"
PROOF_EVIDENCE_BOUNDARY = (
    "Agentic proof execution materializer rows create bounded Lean work "
    "artifacts and transcripts for live proof-state tooling. They are not "
    "theorem proof evidence; promotion still requires safety checks, local "
    "Lean/AXLE kernel verification, replay calibration, and residual-gap "
    "validation."
)
FORBIDDEN_ARTIFACT_TOKENS = ("sorry", "admit", "axiom", "unsafe")


@dataclass(frozen=True)
class FormalVerifierAgenticProofExecutionMaterializerRow:
    schema_version: int
    materialization_id: str
    execution_queue_id: str
    population_entry_id: str
    display_name: str
    target_theorem_name: str
    candidate_bridge_lemma_name: str
    residual_gap: str
    population_bucket: str
    materialization_status: str
    candidate_artifact_path: str
    execution_transcript_path: str
    target_lean_file: str
    target_lean_line: int
    target_lean_column: int
    target_lean_declaration: str
    source_theorem_target_known: bool
    materialization_mode: str
    evolve_block_start_line: int
    evolve_block_end_line: int
    target_blockers: tuple[str, ...]
    reused_kernel_overlay_subclaims: tuple[str, ...]
    static_contract_status: str
    forbidden_tokens_found: tuple[str, ...]
    live_goal_location_ready: bool
    live_proof_state_request: dict[str, object]
    kernel_verified: bool
    proof_evidence_status: str
    proof_evidence_boundary: str
    ok: bool
    errors: tuple[str, ...] = ()


def export_formal_verifier_agentic_proof_execution_materializer(
    formal_verifier_agentic_proof_execution_queue_dir: Path,
    out_dir: Path | None = None,
    *,
    overwrite: bool = False,
) -> dict[str, object]:
    """Materialize bounded Lean artifacts for ready agentic proof queue rows."""

    errors: list[str] = []
    queue_manifest_path = (
        formal_verifier_agentic_proof_execution_queue_dir
        / "formal_verifier_agentic_proof_execution_queue_manifest.json"
    )
    queue_payload = _read_json(queue_manifest_path, errors)
    rows = [
        _materializer_row(row, overwrite=overwrite)
        for row in queue_payload.get("rows", [])
        if isinstance(row, dict)
    ]
    by_status = Counter(row.materialization_status for row in rows)
    payload: dict[str, object] = {
        "schema_version": (
            FORMAL_VERIFIER_AGENTIC_PROOF_EXECUTION_MATERIALIZER_SCHEMA_VERSION
        ),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "formal_verifier_agentic_proof_execution_queue_dir": str(
            formal_verifier_agentic_proof_execution_queue_dir
        ),
        "formal_verifier_agentic_proof_execution_queue_manifest": str(
            queue_manifest_path
        ),
        "overwrite": overwrite,
        "n_queue_rows": len(queue_payload.get("rows", []) or []),
        "n_materializer_rows": len(rows),
        "n_materialized_artifacts": by_status.get("MATERIALIZED_LEAN_ARTIFACT", 0)
        + by_status.get("EXISTING_LEAN_ARTIFACT_REUSED", 0),
        "n_new_artifacts": by_status.get("MATERIALIZED_LEAN_ARTIFACT", 0),
        "n_existing_artifacts_reused": by_status.get(
            "EXISTING_LEAN_ARTIFACT_REUSED", 0
        ),
        "n_source_discovery_rows_skipped": by_status.get(
            "SOURCE_DISCOVERY_ROW_NOT_MATERIALIZED", 0
        ),
        "n_live_goal_location_ready": sum(
            1 for row in rows if row.live_goal_location_ready
        ),
        "n_live_proof_state_requests": sum(
            1 for row in rows if row.live_proof_state_request
        ),
        "n_lean_lsp_mcp_ready_requests": sum(
            1
            for row in rows
            if "lean_lsp_mcp"
            in row.live_proof_state_request.get("provider_preferences", ())
        ),
        "n_kernel_verified": sum(1 for row in rows if row.kernel_verified),
        "n_exact_source_theorem_candidate_artifacts": sum(
            1
            for row in rows
            if row.materialization_mode == "exact_source_theorem_candidate"
        ),
        "n_route_probe_artifacts": sum(
            1 for row in rows if row.materialization_mode == "route_probe"
        ),
        "n_ok": sum(1 for row in rows if row.ok),
        "all_ok": not errors and all(row.ok for row in rows),
        "errors": errors,
        "by_materialization_status": dict(sorted(by_status.items())),
        "rows": [asdict(row) for row in rows],
        "materializer_fingerprint": stable_hash([asdict(row) for row in rows]),
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
        "limitations": [
            "materialized artifacts are proof-worker inputs, not verified theorem outputs",
            "ordinary proof-worker rows still materialize route probes as operational work contracts",
            "source-theorem promotion rows materialize exact theorem candidates only when a statement sketch is present",
            "kernel_verified is false until a separate Lean/AXLE verifier accepts the artifact",
        ],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (
            out_dir
            / "formal_verifier_agentic_proof_execution_materializer_manifest.json"
        ).write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        (
            out_dir / "formal_verifier_agentic_proof_execution_materializer.jsonl"
        ).write_text(
            "\n".join(json.dumps(asdict(row), sort_keys=True) for row in rows)
            + ("\n" if rows else ""),
            encoding="utf-8",
        )
        (
            out_dir / "formal_verifier_agentic_proof_execution_materializer.md"
        ).write_text(_markdown_report(payload), encoding="utf-8")
    return payload


def _materializer_row(
    row: dict[str, Any],
    *,
    overwrite: bool,
) -> FormalVerifierAgenticProofExecutionMaterializerRow:
    errors: list[str] = []
    execution_queue_id = str(row.get("execution_queue_id", ""))
    population_entry_id = str(row.get("population_entry_id", ""))
    display_name = str(row.get("display_name", ""))
    target_theorem_name = str(row.get("target_theorem_name", ""))
    candidate_bridge_lemma_name = str(row.get("candidate_bridge_lemma_name", ""))
    residual_gap = str(row.get("residual_gap", ""))
    population_bucket = str(row.get("population_bucket", ""))
    candidate_artifact_raw = str(row.get("candidate_artifact_path", ""))
    execution_transcript_raw = str(row.get("execution_transcript_path", ""))
    candidate_artifact_path = Path(candidate_artifact_raw)
    execution_transcript_path = Path(execution_transcript_raw)
    kernel_overlay_context = row.get("kernel_overlay_context", {})
    if not isinstance(kernel_overlay_context, dict):
        kernel_overlay_context = {}
    target_blockers = _str_tuple(kernel_overlay_context.get("target_blockers", []))
    reused_subclaims = _str_tuple(
        kernel_overlay_context.get("already_kernel_verified_subclaims", [])
    )
    source_theorem_target_known = bool(
        kernel_overlay_context.get("source_theorem_target_known", False)
    )
    materialization_mode = _materialization_mode(row)
    materialization_id = (
        "formal_verifier_agentic_proof_execution_materializer:"
        + stable_hash([execution_queue_id, candidate_artifact_path])[:16]
    )
    if not execution_queue_id:
        errors.append("execution_queue_id missing")
    if not candidate_artifact_raw:
        errors.append("candidate_artifact_path missing")
    if not execution_transcript_raw:
        errors.append("execution_transcript_path missing")

    target_lean_line = 0
    target_lean_column = 0
    evolve_start = 0
    evolve_end = 0
    target_lean_declaration = (
        _safe_identifier(
            target_theorem_name
            or candidate_bridge_lemma_name
            or display_name
            or "source_theorem_candidate",
        )
        if materialization_mode == "exact_source_theorem_candidate"
        else _safe_identifier(
            candidate_bridge_lemma_name or display_name or "agentic_proof_candidate",
            suffix="_route_probe",
        )
    )
    status = "MATERIALIZATION_BLOCKED"
    forbidden_tokens_found: tuple[str, ...] = ()
    live_proof_state_request: dict[str, object] = {}
    if population_bucket == "source_discovery_attempt":
        status = "SOURCE_DISCOVERY_ROW_NOT_MATERIALIZED"
    elif not errors:
        if (
            materialization_mode == "exact_source_theorem_candidate"
            and not str(row.get("lean_statement_sketch", "") or "").strip()
        ):
            errors.append("lean_statement_sketch missing for exact source theorem candidate")
        if (
            materialization_mode == "exact_source_theorem_candidate"
            and not source_theorem_target_known
        ):
            errors.append("source theorem target is not resolved")
    if not errors and population_bucket != "source_discovery_attempt":
        candidate_artifact_path.parent.mkdir(parents=True, exist_ok=True)
        execution_transcript_path.parent.mkdir(parents=True, exist_ok=True)
        if candidate_artifact_path.exists() and not overwrite:
            source = candidate_artifact_path.read_text(encoding="utf-8")
            status = "EXISTING_LEAN_ARTIFACT_REUSED"
        else:
            source = _candidate_source(
                declaration_name=target_lean_declaration,
                row=row,
                target_blockers=target_blockers,
                reused_subclaims=reused_subclaims,
                materialization_mode=materialization_mode,
            )
            candidate_artifact_path.write_text(source, encoding="utf-8")
            status = "MATERIALIZED_LEAN_ARTIFACT"
        location = _artifact_location(source, target_lean_declaration)
        target_lean_line = int(location.get("target_lean_line", 0))
        target_lean_column = int(location.get("target_lean_column", 0))
        evolve_start = int(location.get("evolve_block_start_line", 0))
        evolve_end = int(location.get("evolve_block_end_line", 0))
        forbidden_tokens_found = tuple(
            token for token in FORBIDDEN_ARTIFACT_TOKENS if token in source
        )
        if forbidden_tokens_found:
            errors.append(
                "candidate artifact contains forbidden tokens: "
                + ", ".join(forbidden_tokens_found)
            )
        if target_lean_line <= 0:
            errors.append("target Lean line could not be inferred")
        live_proof_state_request = _live_proof_state_request(
            row=row,
            candidate_artifact_path=candidate_artifact_path,
            target_lean_line=target_lean_line,
            target_lean_column=target_lean_column,
            target_lean_declaration=target_lean_declaration,
            target_blockers=target_blockers,
            reused_subclaims=reused_subclaims,
        )
        _write_transcript(
            execution_transcript_path,
            row=row,
            materialization_id=materialization_id,
            candidate_artifact_path=candidate_artifact_path,
            target_lean_line=target_lean_line,
            target_lean_column=target_lean_column,
            target_lean_declaration=target_lean_declaration,
            status=status,
            live_proof_state_request=live_proof_state_request,
        )
    static_contract_status = (
        "STATIC_CONTRACT_READY_FOR_LIVE_GOAL"
        if not errors and target_lean_line > 0 and status != "SOURCE_DISCOVERY_ROW_NOT_MATERIALIZED"
        else "STATIC_CONTRACT_NOT_READY_FOR_LIVE_GOAL"
    )
    ok = not errors
    return FormalVerifierAgenticProofExecutionMaterializerRow(
        schema_version=FORMAL_VERIFIER_AGENTIC_PROOF_EXECUTION_MATERIALIZER_SCHEMA_VERSION,
        materialization_id=materialization_id,
        execution_queue_id=execution_queue_id,
        population_entry_id=population_entry_id,
        display_name=display_name,
        target_theorem_name=target_theorem_name,
        candidate_bridge_lemma_name=candidate_bridge_lemma_name,
        residual_gap=residual_gap,
        population_bucket=population_bucket,
        materialization_status=status,
        candidate_artifact_path=str(candidate_artifact_path),
        execution_transcript_path=str(execution_transcript_path),
        target_lean_file=str(candidate_artifact_path) if target_lean_line > 0 else "",
        target_lean_line=target_lean_line,
        target_lean_column=target_lean_column,
        target_lean_declaration=target_lean_declaration,
        source_theorem_target_known=source_theorem_target_known,
        materialization_mode=materialization_mode,
        evolve_block_start_line=evolve_start,
        evolve_block_end_line=evolve_end,
        target_blockers=target_blockers,
        reused_kernel_overlay_subclaims=reused_subclaims,
        static_contract_status=static_contract_status,
        forbidden_tokens_found=forbidden_tokens_found,
        live_goal_location_ready=(
            ok and target_lean_line > 0 and status != "SOURCE_DISCOVERY_ROW_NOT_MATERIALIZED"
        ),
        live_proof_state_request=live_proof_state_request
        if ok and target_lean_line > 0 and status != "SOURCE_DISCOVERY_ROW_NOT_MATERIALIZED"
        else {},
        kernel_verified=False,
        proof_evidence_status=PROOF_EVIDENCE_STATUS,
        proof_evidence_boundary=PROOF_EVIDENCE_BOUNDARY,
        ok=ok,
        errors=tuple(errors),
    )


def _candidate_source(
    *,
    declaration_name: str,
    row: dict[str, Any],
    target_blockers: tuple[str, ...],
    reused_subclaims: tuple[str, ...],
    materialization_mode: str,
) -> str:
    if materialization_mode == "exact_source_theorem_candidate":
        return _exact_source_theorem_candidate_source(
            declaration_name=declaration_name,
            row=row,
            reused_subclaims=reused_subclaims,
        )
    props = tuple(dict.fromkeys(reused_subclaims + target_blockers)) or (
        "open_residual_goal",
    )
    binders = "\n".join(f"    ({_safe_identifier(prop)} : True)" for prop in props)
    metadata = {
        "execution_queue_id": row.get("execution_queue_id", ""),
        "target_theorem_name": row.get("target_theorem_name", ""),
        "residual_gap": row.get("residual_gap", ""),
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
    }
    metadata_lines = "\n".join(
        f"-- {key}: {value}" for key, value in metadata.items() if value
    )
    return (
        "/-!\n"
        "Bounded Lean work artifact for an agentic proof-worker queue row.\n"
        "This route probe is operational input for live proof-state tooling.\n"
        "It is not theorem proof evidence for the referenced source claim.\n"
        "-/\n\n"
        "namespace AIStatisticianAgenticProofExecution\n\n"
        f"{metadata_lines}\n"
        f"theorem {declaration_name}\n"
        f"{binders} :\n"
        "    True := by\n"
        "  -- AI_STAT_EVOLVE_BLOCK_START\n"
        "  exact True.intro\n"
        "  -- AI_STAT_EVOLVE_BLOCK_END\n\n"
        "end AIStatisticianAgenticProofExecution\n"
    )


def _materialization_mode(row: dict[str, Any]) -> str:
    explicit = str(
        row.get("source_theorem_materialization_mode")
        or row.get("materialization_mode")
        or ""
    )
    if explicit == "exact_source_theorem_candidate":
        return "exact_source_theorem_candidate"
    if str(row.get("strategy_id", "") or "") == (
        "runtime_source_theorem_promotion_exact_target_attempt"
    ):
        return "exact_source_theorem_candidate"
    return "route_probe"


def _exact_source_theorem_candidate_source(
    *,
    declaration_name: str,
    row: dict[str, Any],
    reused_subclaims: tuple[str, ...],
) -> str:
    sketch = str(row.get("lean_statement_sketch", "") or "").strip()
    metadata = {
        "execution_queue_id": row.get("execution_queue_id", ""),
        "target_theorem_name": row.get("target_theorem_name", ""),
        "residual_gap": row.get("residual_gap", ""),
        "materialization_mode": "exact_source_theorem_candidate",
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
    }
    metadata_lines = "\n".join(
        f"-- {key}: {value}" for key, value in metadata.items() if value
    )
    support_lines = "\n".join(
        f"-- kernel_verified_support: {item}" for item in reused_subclaims
    )
    import_lines = "\n".join(f"import {item}" for item in _target_imports(row))
    import_block = f"{import_lines}\n\n" if import_lines else ""
    body = _lean_statement_with_evolve_block(sketch)
    return (
        f"{import_block}"
        "/-!\n"
        "Bounded Lean exact-source-theorem candidate artifact.\n"
        "Downstream local Lean/AXLE verification decides whether this exact declaration is proof evidence.\n"
        "-/\n\n"
        f"{metadata_lines}\n"
        f"{support_lines}\n"
        f"{body}\n"
    )


def _lean_statement_with_evolve_block(statement: str) -> str:
    statement = _normalize_lean_statement_syntax(statement)
    if "AI_STAT_EVOLVE_BLOCK_START" in statement:
        return statement.rstrip() + "\n"
    match = re.search(r":=\s*by\b", statement)
    if match is None:
        return (
            statement.rstrip()
            + " := by\n"
            + "  -- AI_STAT_EVOLVE_BLOCK_START\n"
            + "  -- ProofEngineer must fill the exact source-theorem proof body here.\n"
            + "  -- AI_STAT_EVOLVE_BLOCK_END\n"
        )
    prefix = statement[: match.end()].rstrip()
    proof_body = statement[match.end() :].strip("\n")
    proof_lines = _indent_lean_proof_body(proof_body)
    return (
        prefix
        + "\n"
        + "  -- AI_STAT_EVOLVE_BLOCK_START\n"
        + proof_lines
        + "\n"
        + "  -- AI_STAT_EVOLVE_BLOCK_END\n"
    )


def _indent_lean_proof_body(proof_body: str) -> str:
    stripped = proof_body.strip()
    if not stripped:
        return "  -- ProofEngineer must fill the exact source-theorem proof body here."
    if any(token in stripped for token in FORBIDDEN_ARTIFACT_TOKENS):
        return "  -- ProofEngineer must fill the exact source-theorem proof body here."
    lines = stripped.splitlines()
    return "\n".join(
        line if line.startswith((" ", "\t")) else "  " + line
        for line in lines
    )


def _normalize_lean_statement_syntax(statement: str) -> str:
    statement = _normalize_lean_declaration_header(statement)
    return statement.replace("Type*", "Type _")


def _target_imports(row: dict[str, Any]) -> tuple[str, ...]:
    context = row.get("kernel_overlay_context", {})
    if not isinstance(context, dict):
        context = {}
    target_location = context.get("target_location", {})
    if not isinstance(target_location, dict):
        target_location = {}
    raw_imports = target_location.get("target_imports", row.get("lean_imports", []))
    if not isinstance(raw_imports, list):
        return ()
    imports: list[str] = []
    for value in raw_imports:
        module = str(value).strip()
        if module and _safe_lean_import(module) and module not in imports:
            imports.append(module)
    return tuple(imports)


def _safe_lean_import(module: str) -> bool:
    part = r"[A-Za-z_][A-Za-z0-9_']*"
    return re.fullmatch(rf"{part}(?:\.{part})*", module) is not None


def _normalize_lean_declaration_header(statement: str) -> str:
    lines = statement.splitlines()
    normalized: list[str] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        stripped = line.strip()
        next_line = lines[index + 1] if index + 1 < len(lines) else ""
        next_stripped = next_line.lstrip()
        if (
            re.match(r"^(theorem|lemma)\s+[A-Za-z0-9_'.]+$", stripped)
            and next_stripped.startswith(("{", "(", "[", ":"))
        ):
            normalized.append(line.rstrip() + " " + next_stripped)
            index += 2
            continue
        normalized.append(line)
        index += 1
    return "\n".join(normalized)


def _artifact_location(source: str, declaration_name: str) -> dict[str, object]:
    lines = source.splitlines()
    target_line = 0
    start_line = 0
    end_line = 0
    for index, line in enumerate(lines, start=1):
        stripped = line.strip()
        if stripped == "-- AI_STAT_EVOLVE_BLOCK_START":
            start_line = index
            target_line = index + 1 if index < len(lines) else index
        if stripped == "-- AI_STAT_EVOLVE_BLOCK_END":
            end_line = index
    return {
        "target_lean_line": target_line,
        "target_lean_column": 3 if target_line > 0 else 0,
        "target_lean_declaration": declaration_name,
        "evolve_block_start_line": start_line,
        "evolve_block_end_line": end_line,
    }


def _live_proof_state_request(
    *,
    row: dict[str, Any],
    candidate_artifact_path: Path,
    target_lean_line: int,
    target_lean_column: int,
    target_lean_declaration: str,
    target_blockers: tuple[str, ...],
    reused_subclaims: tuple[str, ...],
) -> dict[str, object]:
    requested_tools = _str_tuple(row.get("proof_state_provider_plan", ()))
    mcp_tools = tuple(
        tool
        for tool in (
            "lean_goal",
            "lean_diagnostic_messages",
            "lean_hover",
            "lean_local_search",
            "lean_multi_attempt",
        )
        if tool in requested_tools or tool in {"lean_goal", "lean_diagnostic_messages"}
    )
    return {
        "schema_version": 1,
        "request_id": "live_proof_state_request:"
        + stable_hash(
            [
                row.get("execution_queue_id", ""),
                str(candidate_artifact_path),
                target_lean_line,
                target_lean_column,
                target_lean_declaration,
            ]
        )[:16],
        "provider_preferences": (
            "lean_lsp_mcp",
            "local_lean_proof_state_adapter",
            "local.lake_env_lean",
        ),
        "mcp_tool_calls": tuple(
            {
                "tool": tool,
                "arguments": {
                    "file": str(candidate_artifact_path),
                    "line": target_lean_line,
                    "column": target_lean_column,
                    "declaration": target_lean_declaration,
                },
            }
            for tool in mcp_tools
        ),
        "fallback_adapter": "formalization-gap-planner-local-proof-state-adapter",
        "candidate_artifact_path": str(candidate_artifact_path),
        "target_lean_file": str(candidate_artifact_path),
        "target_lean_line": target_lean_line,
        "target_lean_column": target_lean_column,
        "target_lean_declaration": target_lean_declaration,
        "source_theorem_target_known": bool(
            row.get("source_theorem_target_known", False)
            or (
                isinstance(row.get("kernel_overlay_context", {}), dict)
                and row.get("kernel_overlay_context", {}).get(
                    "source_theorem_target_known",
                    False,
                )
            )
        ),
        "goal_cache_key": str(row.get("goal_cache_key", "")),
        "candidate_database_key": str(row.get("candidate_database_key", "")),
        "candidate_lineage_key": str(row.get("candidate_lineage_key", "")),
        "proof_sketch_population_key": str(row.get("proof_sketch_population_key", "")),
        "target_blockers": target_blockers,
        "reused_kernel_overlay_subclaims": reused_subclaims,
        "expected_transcript_events": (
            "lean_goal_result",
            "lean_diagnostic_messages_result",
            "lean_multi_attempt_result",
            "local_lean_or_axle_verifier_result",
        ),
        "proof_evidence_status": "LIVE_PROOF_STATE_REQUEST_NOT_PROOF_EVIDENCE",
        "proof_evidence_boundary": (
            "This request is an operational proof-state work packet. Tool output "
            "is diagnostic/search evidence until the resulting candidate passes "
            "safety checks, local Lean/AXLE kernel verification, replay "
            "calibration, and residual-gap validation."
        ),
    }


def _write_transcript(
    path: Path,
    *,
    row: dict[str, Any],
    materialization_id: str,
    candidate_artifact_path: Path,
    target_lean_line: int,
    target_lean_column: int,
    target_lean_declaration: str,
    status: str,
    live_proof_state_request: dict[str, object],
) -> None:
    transcript_row = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "materialization_id": materialization_id,
        "execution_queue_id": row.get("execution_queue_id", ""),
        "event": "candidate_artifact_materialized",
        "materialization_status": status,
        "candidate_artifact_path": str(candidate_artifact_path),
        "target_lean_file": str(candidate_artifact_path),
        "target_lean_line": target_lean_line,
        "target_lean_column": target_lean_column,
        "target_lean_declaration": target_lean_declaration,
        "live_proof_state_request": live_proof_state_request,
        "kernel_verified": False,
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
    }
    path.write_text(json.dumps(transcript_row, sort_keys=True) + "\n", encoding="utf-8")


def _safe_identifier(raw: str, *, suffix: str = "") -> str:
    cleaned = "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in raw).strip("_")
    if not cleaned:
        cleaned = "agentic_proof_candidate"
    if cleaned[0].isdigit():
        cleaned = "n_" + cleaned
    if suffix and not cleaned.endswith(suffix):
        cleaned = cleaned + suffix
    return cleaned


def _str_tuple(values: object) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        values = [values]
    if not isinstance(values, (list, tuple, set)):
        return ()
    return tuple(str(item) for item in values if str(item))


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
        "# Formal Verifier Agentic Proof Execution Materializer",
        "",
        f"- Queue rows: {payload.get('n_queue_rows')}",
        f"- Materialized artifacts: {payload.get('n_materialized_artifacts')}",
        f"- New artifacts: {payload.get('n_new_artifacts')}",
        f"- Live goal location ready: {payload.get('n_live_goal_location_ready')}",
        f"- Live proof-state requests: {payload.get('n_live_proof_state_requests')}",
        f"- Lean-LSP/MCP-ready requests: {payload.get('n_lean_lsp_mcp_ready_requests')}",
        f"- Kernel verified: {payload.get('n_kernel_verified')}",
        f"- Fingerprint: `{payload.get('materializer_fingerprint')}`",
        "",
        str(payload.get("proof_evidence_boundary", "")),
        "",
        "## Rows",
        "",
    ]
    for row in payload.get("rows", []):
        if not isinstance(row, dict):
            continue
        lines.append(
            f"- #{row.get('target_lean_declaration')} "
            f"`{row.get('materialization_status')}` "
            f"line={row.get('target_lean_line')} "
            f"live_request={bool(row.get('live_proof_state_request'))} "
            f"artifact=`{row.get('candidate_artifact_path')}`"
        )
        if row.get("errors"):
            lines.append(f"  errors: {row.get('errors')}")
    return "\n".join(lines) + "\n"
