from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash
from .formalization_gap_planner_contract import PORTABLE_FORMALIZATION_GAP_PLAN_SCHEMA_ID


FORMALIZATION_GAP_PLANNER_BENCHMARK_SCHEMA_VERSION = 1
DEFAULT_FORMALIZATION_GAP_PLANNER_GROUND_TRUTH_PATH = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "formalization_gap_planner_ground_truth.json"
)
ROUTE_TRUTH_STATUSES = (
    "expert_curated_route_truth",
    "literature_curated_route_truth",
    "kernel_verified_route_truth",
)
PROOF_EVIDENCE_BOUNDARY = (
    "Formalization gap planner benchmark rows are route-truth evaluation data, "
    "not theorem proof evidence. Kernel proof evidence still requires the "
    "target prover to verify the theorem or bridge lemma with no placeholders."
)


@dataclass(frozen=True)
class FormalizationGapPlannerBenchmarkRoute:
    schema_version: int
    benchmark_route_id: str
    display_name: str
    theorem_family: str
    target_prover_family: str
    route_truth_status: str
    required_primitives: tuple[str, ...]
    actual_existing_reuse_primitives: tuple[str, ...]
    actual_delta_primitives: tuple[str, ...]
    coverage_by_primitive: dict[str, str]
    source_refs: tuple[str, ...]
    kernel_verified: bool
    notes: str
    ok: bool
    errors: tuple[str, ...] = ()


def default_formalization_gap_planner_ground_truth_path() -> Path:
    return DEFAULT_FORMALIZATION_GAP_PLANNER_GROUND_TRUTH_PATH


def load_formalization_gap_planner_ground_truth(
    ground_truth_path: Path | None = None,
) -> dict[str, object]:
    """Load and validate the reusable route-truth benchmark file."""

    errors: list[str] = []
    path = ground_truth_path or DEFAULT_FORMALIZATION_GAP_PLANNER_GROUND_TRUTH_PATH
    payload = _read_json(path, errors)
    rows = tuple(_benchmark_route(row) for row in _truth_rows(payload))
    return {
        "schema_version": FORMALIZATION_GAP_PLANNER_BENCHMARK_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "component_name": "formalization_gap_planner_benchmark",
        "portable_schema_id": PORTABLE_FORMALIZATION_GAP_PLAN_SCHEMA_ID,
        "ground_truth_path": str(path),
        "source_schema_version": payload.get("schema_version", 0),
        "benchmark_id": payload.get("benchmark_id", ""),
        "benchmark_name": payload.get("benchmark_name", ""),
        "description": payload.get("description", ""),
        "n_routes": len(rows),
        "n_ok": sum(1 for row in rows if row.ok),
        "n_kernel_verified_routes": sum(1 for row in rows if row.kernel_verified),
        "n_required_primitives": sum(len(row.required_primitives) for row in rows),
        "n_actual_delta_primitives": sum(len(row.actual_delta_primitives) for row in rows),
        "n_existing_reuse_primitives": sum(
            len(row.actual_existing_reuse_primitives) for row in rows
        ),
        "by_theorem_family": dict(
            sorted(Counter(row.theorem_family for row in rows).items())
        ),
        "by_route_truth_status": dict(
            sorted(Counter(row.route_truth_status for row in rows).items())
        ),
        "by_coverage_status": _coverage_status_counts(rows),
        "all_ok": not errors and bool(rows) and all(row.ok for row in rows),
        "errors": errors,
        "routes": [asdict(row) for row in rows],
        "raw_ground_truth": payload,
        "benchmark_fingerprint": stable_hash([asdict(row) for row in rows]),
        "proof_evidence_boundary": str(
            payload.get("proof_evidence_boundary", PROOF_EVIDENCE_BOUNDARY)
        ),
        "limitations": [
            "route-truth rows are planner benchmark labels, not theorem proof evidence",
            "expert-curated rows should be upgraded to kernel_verified_route_truth when a target prover route is available",
            "display_name matching keeps the benchmark stable across route-id hash changes but still requires careful theorem naming",
        ],
    }


def export_formalization_gap_planner_benchmark(
    out_dir: Path,
    *,
    ground_truth_path: Path | None = None,
) -> dict[str, object]:
    """Write a reusable benchmark manifest and route-truth copy."""

    payload = load_formalization_gap_planner_ground_truth(ground_truth_path)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "formalization_gap_planner_benchmark_manifest.json").write_text(
        json.dumps(payload, indent=2, default=str),
        encoding="utf-8",
    )
    raw_ground_truth = payload.get("raw_ground_truth", {})
    (out_dir / "formalization_gap_planner_ground_truth.json").write_text(
        json.dumps(raw_ground_truth, indent=2, default=str),
        encoding="utf-8",
    )
    (out_dir / "formalization_gap_planner_benchmark_routes.jsonl").write_text(
        "\n".join(json.dumps(row, sort_keys=True) for row in payload["routes"])
        + ("\n" if payload["routes"] else ""),
        encoding="utf-8",
    )
    (out_dir / "formalization_gap_planner_benchmark.md").write_text(
        _markdown_report(payload),
        encoding="utf-8",
    )
    return payload


def _benchmark_route(row: dict[str, Any]) -> FormalizationGapPlannerBenchmarkRoute:
    errors: list[str] = []
    display_name = str(row.get("display_name", ""))
    theorem_family = str(row.get("theorem_family", ""))
    target_prover_family = str(row.get("target_prover_family", ""))
    route_truth_status = str(row.get("route_truth_status", ""))
    required = _str_tuple(row.get("required_primitives", []))
    existing = _str_tuple(row.get("actual_existing_reuse_primitives", []))
    delta = _str_tuple(row.get("actual_delta_primitives", []))
    coverage_raw = row.get("coverage_by_primitive", {})
    coverage = {
        str(key): str(value)
        for key, value in coverage_raw.items()
        if str(key) and str(value)
    } if isinstance(coverage_raw, dict) else {}
    source_refs = _str_tuple(row.get("source_refs", []))

    for field_name, value in (
        ("display_name", display_name),
        ("theorem_family", theorem_family),
        ("target_prover_family", target_prover_family),
        ("route_truth_status", route_truth_status),
    ):
        if not value:
            errors.append(f"{field_name} missing")
    if route_truth_status and route_truth_status not in ROUTE_TRUTH_STATUSES:
        errors.append(f"unsupported route_truth_status: {route_truth_status}")
    if not required:
        errors.append("required_primitives missing")
    if not coverage:
        errors.append("coverage_by_primitive missing")
    missing_coverage = tuple(sorted(set(required) - set(coverage)))
    if missing_coverage:
        errors.append(
            "coverage_by_primitive missing required primitives: "
            + ", ".join(missing_coverage[:8])
        )
    extra_classified = tuple(sorted((set(existing) | set(delta)) - set(required)))
    if extra_classified:
        errors.append(
            "reuse/delta primitives not in required_primitives: "
            + ", ".join(extra_classified[:8])
        )
    if not source_refs:
        errors.append("source_refs missing")
    return FormalizationGapPlannerBenchmarkRoute(
        schema_version=FORMALIZATION_GAP_PLANNER_BENCHMARK_SCHEMA_VERSION,
        benchmark_route_id="formalization_gap_planner_benchmark_route:"
        + stable_hash([display_name, required, existing, delta])[:16],
        display_name=display_name,
        theorem_family=theorem_family,
        target_prover_family=target_prover_family,
        route_truth_status=route_truth_status,
        required_primitives=required,
        actual_existing_reuse_primitives=existing,
        actual_delta_primitives=delta,
        coverage_by_primitive=coverage,
        source_refs=source_refs,
        kernel_verified=bool(row.get("kernel_verified", False)),
        notes=str(row.get("notes", "")),
        ok=not errors,
        errors=tuple(errors),
    )


def _truth_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    for field_name in ("routes", "rows", "ground_truth_routes"):
        rows = payload.get(field_name, [])
        if isinstance(rows, list):
            return [row for row in rows if isinstance(row, dict)]
    return []


def _coverage_status_counts(
    rows: tuple[FormalizationGapPlannerBenchmarkRoute, ...],
) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.coverage_by_primitive.values())
    return dict(sorted(counter.items()))


def _str_tuple(values: Any) -> tuple[str, ...]:
    if isinstance(values, str):
        return (values,) if values else tuple()
    if not isinstance(values, (list, tuple, set)):
        return tuple()
    return tuple(sorted(dict.fromkeys(str(item) for item in values if str(item))))


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
        "# Formalization Gap Planner Benchmark",
        "",
        f"- Benchmark: `{payload.get('benchmark_id')}`",
        f"- Routes: {payload.get('n_routes')}",
        f"- Required primitives: {payload.get('n_required_primitives')}",
        f"- Delta primitives: {payload.get('n_actual_delta_primitives')}",
        f"- Existing-reuse primitives: {payload.get('n_existing_reuse_primitives')}",
        f"- Kernel-verified route truth: {payload.get('n_kernel_verified_routes')}",
        f"- All OK: {payload.get('all_ok')}",
        "",
        "## Boundary",
        "",
        str(payload.get("proof_evidence_boundary", PROOF_EVIDENCE_BOUNDARY)),
        "",
        "## Routes",
        "",
    ]
    for row in payload.get("routes", []):
        if not isinstance(row, dict):
            continue
        lines.append(
            f"- `{row.get('display_name')}` family={row.get('theorem_family')} "
            f"required={len(row.get('required_primitives', []))} "
            f"delta={len(row.get('actual_delta_primitives', []))} "
            f"status={row.get('route_truth_status')}"
        )
    return "\n".join(lines) + "\n"
