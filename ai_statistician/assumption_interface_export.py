from __future__ import annotations

import json
import re
import shutil
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash


ASSUMPTION_INTERFACE_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class AssumptionInterfaceTarget:
    schema_version: int
    target_id: str
    primitive: str
    interface_name: str
    source_action_id: str
    source_gap_ids: tuple[str, ...]
    source_task_ids: tuple[str, ...]
    candidate_declarations: tuple[str, ...]
    expected_premises: tuple[str, ...]
    lean_file: str
    lean_statement: str
    non_vacuity_declaration: str
    downstream_use_declaration: str
    local_lean_checked: bool
    local_lean_compiled: bool
    local_lean_errors: tuple[str, ...]
    required_gate: str
    evidence_boundary: str
    ok: bool
    errors: tuple[str, ...] = ()


def export_assumption_interfaces(
    proof_bank_actions_dir: Path,
    out_dir: Path | None = None,
    *,
    lean_project: str | Path | None = None,
    lean_timeout: int = 90,
) -> dict[str, object]:
    """Export assumption-interface actions as concrete Lean predicate targets.

    These targets are not proof-bank theorems. They give the Formalizer a
    reusable predicate/interface file plus a small downstream-use theorem so the
    assumption can be consumed by future identification proofs without claiming
    the assumption itself has been proved.
    """

    manifest_path = proof_bank_actions_dir / "proof_bank_action_manifest.json"
    errors: list[str] = []
    manifest = _read_json(manifest_path, errors)
    actions = [
        row
        for row in manifest.get("actions", [])
        if isinstance(row, dict) and row.get("action_class") == "formalize_assumption_interface"
    ]
    lean_dir = out_dir / "lean" if out_dir is not None else Path("")
    if out_dir is not None:
        lean_dir.mkdir(parents=True, exist_ok=True)
    rows = [
        _target_for_action(
            row,
            lean_dir=lean_dir,
            lean_project=Path(lean_project) if lean_project else None,
            lean_timeout=lean_timeout,
            write_file=out_dir is not None,
        )
        for row in actions
    ]
    by_primitive_kind = {"assumption_interface": len(rows)}
    payload: dict[str, object] = {
        "schema_version": ASSUMPTION_INTERFACE_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "proof_bank_actions_dir": str(proof_bank_actions_dir),
        "proof_bank_action_manifest": str(manifest_path),
        "n_interfaces": len(rows),
        "n_ok": sum(1 for row in rows if row.ok),
        "n_local_lean_checked": sum(1 for row in rows if row.local_lean_checked),
        "n_local_lean_compiled": sum(1 for row in rows if row.local_lean_compiled),
        "local_lean_enabled": bool(lean_project),
        "local_lean_project": str(lean_project or ""),
        "local_lean_timeout": lean_timeout,
        "by_primitive_kind": by_primitive_kind,
        "all_ok": not errors and all(row.ok for row in rows),
        "all_local_lean_compiled": (
            bool(rows)
            and all(row.local_lean_checked and row.local_lean_compiled for row in rows)
            if lean_project
            else False
        ),
        "target_fingerprint": stable_hash([asdict(row) for row in rows]),
        "targets": [asdict(row) for row in rows],
        "errors": errors,
        "limitations": [
            "assumption-interface targets are not proof-bank theorem evidence",
            "a compiling predicate/interface does not prove the statistical assumption",
            "downstream identification theorems must explicitly assume this interface before using it",
        ],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "assumption_interface_manifest.json").write_text(
            json.dumps(payload, indent=2, default=str),
            encoding="utf-8",
        )
        (out_dir / "assumption_interfaces.jsonl").write_text(
            "\n".join(json.dumps(asdict(row), sort_keys=True) for row in rows)
            + ("\n" if rows else ""),
            encoding="utf-8",
        )
        (out_dir / "assumption_interfaces.md").write_text(_markdown_report(payload), encoding="utf-8")
    return payload


def _target_for_action(
    action: dict[str, Any],
    *,
    lean_dir: Path,
    lean_project: Path | None,
    lean_timeout: int,
    write_file: bool,
) -> AssumptionInterfaceTarget:
    primitive = str(action.get("primitive", ""))
    interface_name = _interface_name(primitive)
    lean_statement = _lean_interface_statement(interface_name)
    lean_file = lean_dir / f"{primitive or 'assumption_interface'}.lean"
    if write_file:
        lean_file.write_text(lean_statement, encoding="utf-8")
    errors = _static_errors(primitive, lean_statement)
    local_checked = False
    local_compiled = False
    local_errors: tuple[str, ...] = ()
    if lean_project is not None and write_file:
        local_checked = True
        local_compiled, local_errors = _run_local_lean(lean_file, lean_project, lean_timeout)
        if not local_compiled:
            errors.append("local Lean compile failed")
    return AssumptionInterfaceTarget(
        schema_version=ASSUMPTION_INTERFACE_SCHEMA_VERSION,
        target_id=f"assumption_interface:{primitive or stable_hash(action)[:12]}",
        primitive=primitive,
        interface_name=interface_name,
        source_action_id=str(action.get("action_id", "")),
        source_gap_ids=tuple(str(item) for item in action.get("source_gap_ids", []) or [] if str(item)),
        source_task_ids=tuple(str(item) for item in action.get("source_task_ids", []) or [] if str(item)),
        candidate_declarations=tuple(
            str(item) for item in action.get("candidate_declarations", []) or [] if str(item)
        ),
        expected_premises=tuple(str(item) for item in action.get("expected_premises", []) or [] if str(item))[:32],
        lean_file=str(lean_file),
        lean_statement=lean_statement,
        non_vacuity_declaration=f"{interface_name}_intro",
        downstream_use_declaration=f"{interface_name}_downstream_use",
        local_lean_checked=local_checked,
        local_lean_compiled=local_compiled,
        local_lean_errors=local_errors,
        required_gate=str(action.get("required_gate", "")),
        evidence_boundary=(
            "This Lean file formalizes an assumption predicate/interface and a downstream-use theorem. "
            "It does not prove the assumption itself."
        ),
        ok=not errors,
        errors=tuple(errors),
    )


def _lean_interface_statement(interface_name: str) -> str:
    return f"""import Mathlib

open MeasureTheory ProbabilityTheory

namespace AIStatistician.AssumptionInterfaces

/-!
Reusable AI Statistician assumption interface.

This file intentionally defines a predicate and downstream-use theorem. It does not prove
the statistical assumption from no premises.
-/

/-- Conditional exchangeability / unconfoundedness as a reusable assumption
interface for causal identification traces. The two exchangeability propositions
are parameters so downstream identification theorems must state and use the
actual causal exchangeability content explicitly. -/
structure {interface_name}
    {{Ω X : Type*}} [MeasurableSpace Ω] [MeasurableSpace X]
    (μ : Measure Ω)
    (covariates : Ω → X)
    (treatment : Ω → Bool)
    (y0 y1 : Ω → ℝ)
    (y0_exchangeable y1_exchangeable : Prop) : Prop where
  covariates_measurable : Measurable covariates
  treatment_measurable : Measurable treatment
  y0_integrable : Integrable y0 μ
  y1_integrable : Integrable y1 μ
  y0_exchangeability : y0_exchangeable
  y1_exchangeability : y1_exchangeable

theorem {interface_name}_intro
    {{Ω X : Type*}} [MeasurableSpace Ω] [MeasurableSpace X]
    (μ : Measure Ω)
    (covariates : Ω → X)
    (treatment : Ω → Bool)
    (y0 y1 : Ω → ℝ)
    (y0_exchangeable y1_exchangeable : Prop)
    (hX : Measurable covariates)
    (hT : Measurable treatment)
    (h0int : Integrable y0 μ)
    (h1int : Integrable y1 μ)
    (h0 : y0_exchangeable)
    (h1 : y1_exchangeable) :
    {interface_name} μ covariates treatment y0 y1 y0_exchangeable y1_exchangeable := by
  exact {{
    covariates_measurable := hX
    treatment_measurable := hT
    y0_integrable := h0int
    y1_integrable := h1int
    y0_exchangeability := h0
    y1_exchangeability := h1
  }}

theorem {interface_name}_downstream_use
    {{Ω X : Type*}} [MeasurableSpace Ω] [MeasurableSpace X]
    {{μ : Measure Ω}}
    {{covariates : Ω → X}}
    {{treatment : Ω → Bool}}
    {{y0 y1 : Ω → ℝ}}
    {{y0_exchangeable y1_exchangeable : Prop}}
    (h : {interface_name} μ covariates treatment y0 y1 y0_exchangeable y1_exchangeable) :
    y0_exchangeable ∧ y1_exchangeable := by
  exact And.intro h.y0_exchangeability h.y1_exchangeability

end AIStatistician.AssumptionInterfaces
"""


def _static_errors(primitive: str, lean_statement: str) -> list[str]:
    errors: list[str] = []
    if not primitive:
        errors.append("missing primitive")
    if "sorry" in lean_statement or "admit" in lean_statement or "axiom" in lean_statement:
        errors.append("Lean interface contains forbidden proof placeholder")
    for pattern in ("structure ", "_intro", "_downstream_use", "does not prove"):
        if pattern not in lean_statement:
            errors.append(f"Lean interface missing expected pattern: {pattern}")
    return errors


def _run_local_lean(lean_file: Path, lean_project: Path, timeout_s: int) -> tuple[bool, tuple[str, ...]]:
    if shutil.which("lake") is None:
        return False, ("lake executable not found",)
    if not lean_project.exists():
        return False, (f"lean project does not exist: {lean_project}",)
    try:
        result = subprocess.run(
            ["lake", "env", "lean", str(lean_file.resolve())],
            cwd=str(lean_project),
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
    except subprocess.TimeoutExpired:
        return False, (f"local Lean timed out after {timeout_s}s",)
    except Exception as exc:
        return False, (f"{type(exc).__name__}: {exc}",)
    errors: list[str] = []
    if result.stdout.strip():
        errors.append(result.stdout.strip())
    if result.stderr.strip():
        errors.append(result.stderr.strip())
    return result.returncode == 0, tuple(errors)


def _interface_name(primitive: str) -> str:
    if primitive == "conditional_exchangeability":
        return "ConditionalExchangeability"
    cleaned = re.sub(r"[^A-Za-z0-9]+", " ", primitive).title().replace(" ", "")
    return cleaned or "AssumptionInterface"


def _read_json(path: Path, errors: list[str]) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        errors.append(f"missing {path}")
    except json.JSONDecodeError as exc:
        errors.append(f"invalid JSON in {path}: {exc}")
    return {}


def _markdown_report(payload: dict[str, object]) -> str:
    lines = [
        "# Assumption Interface Targets",
        "",
        f"- Proof-bank actions: `{payload.get('proof_bank_actions_dir')}`",
        f"- Interfaces: {payload.get('n_ok')}/{payload.get('n_interfaces')} export-clean",
        f"- Local Lean checked: {payload.get('n_local_lean_checked')}",
        f"- Local Lean compiled: {payload.get('n_local_lean_compiled')}",
        f"- Local Lean project: `{payload.get('local_lean_project')}`",
        f"- Fingerprint: `{payload.get('target_fingerprint')}`",
        "",
        "These are assumption predicate/interface targets, not proof-bank theorem evidence.",
        "",
        "## Targets",
        "",
    ]
    for row in payload.get("targets", []):
        if not isinstance(row, dict):
            continue
        lines.extend(
            [
                f"### `{row.get('primitive')}`",
                "",
                f"- Interface: `{row.get('interface_name')}`",
                f"- Lean file: `{row.get('lean_file')}`",
                f"- Local Lean compiled: {row.get('local_lean_compiled')}",
                f"- Source action: `{row.get('source_action_id')}`",
                f"- Evidence boundary: {row.get('evidence_boundary')}",
                "",
            ]
        )
    lines.extend(["## Honesty Boundary", ""])
    for item in payload.get("limitations", []):
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"
