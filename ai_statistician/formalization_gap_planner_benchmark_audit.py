from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash
from .formalization_gap_planner_benchmark import (
    PROOF_EVIDENCE_BOUNDARY as BENCHMARK_PROOF_EVIDENCE_BOUNDARY,
    ROUTE_TRUTH_STATUSES,
    benchmark_route_row_json_schema,
    validate_benchmark_route_row,
)
from .formalization_gap_planner_contract import PORTABLE_FORMALIZATION_GAP_PLAN_SCHEMA_ID


FORMALIZATION_GAP_PLANNER_BENCHMARK_AUDIT_SCHEMA_VERSION = 1
PROOF_EVIDENCE_STATUS = "FORMALIZATION_GAP_PLANNER_BENCHMARK_AUDIT_NOT_PROOF_EVIDENCE"
PROOF_EVIDENCE_BOUNDARY = (
    "Formalization gap planner benchmark-audit rows validate route-truth "
    "quality, coverage labels, source refs, derived evaluation splits, and "
    "proof-boundary discipline. They are not theorem proof evidence."
)
CORE_COVERAGE_STATUSES = ("exact_exists", "wrapper_needed", "bridge_needed")


@dataclass(frozen=True)
class FormalizationGapPlannerBenchmarkAuditCheck:
    schema_version: int
    check_id: str
    check_name: str
    category: str
    expected: str
    observed: str
    ok: bool
    severity: str
    errors: tuple[str, ...] = ()


@dataclass(frozen=True)
class FormalizationGapPlannerBenchmarkSplitRow:
    schema_version: int
    split_row_id: str
    display_name: str
    theorem_family: str
    evaluation_split: str
    split_reason: str
    route_truth_status: str
    n_required_primitives: int
    n_source_refs: int
    kernel_verified: bool
    n_kernel_verification_witnesses: int


def audit_formalization_gap_planner_benchmark(
    formalization_gap_planner_benchmark_dir: Path,
    out_dir: Path | None = None,
) -> dict[str, object]:
    """Audit route-truth benchmark quality for publication and reuse."""

    errors: list[str] = []
    benchmark_dir = formalization_gap_planner_benchmark_dir
    manifest_path = benchmark_dir / "formalization_gap_planner_benchmark_manifest.json"
    ground_truth_path = benchmark_dir / "formalization_gap_planner_ground_truth.json"
    routes_jsonl_path = benchmark_dir / "formalization_gap_planner_benchmark_routes.jsonl"
    route_schema_path = benchmark_dir / "formalization_gap_planner_benchmark_route.schema.json"
    report_path = benchmark_dir / "formalization_gap_planner_benchmark.md"
    manifest = _read_json(manifest_path, errors)
    routes = _dict_rows(manifest.get("routes", []))
    split_rows = tuple(_split_row(idx, route) for idx, route in enumerate(routes))
    checks: list[FormalizationGapPlannerBenchmarkAuditCheck] = []
    checks.extend(_manifest_checks(manifest_path, manifest, routes))
    checks.extend(
        _artifact_checks(
            ground_truth_path,
            routes_jsonl_path,
            route_schema_path,
            report_path,
        )
    )
    checks.extend(_coverage_checks(routes))
    checks.extend(_route_checks(routes))
    checks.extend(_split_checks(split_rows, routes))
    by_category = Counter(check.category for check in checks)
    by_family = Counter(str(row.get("theorem_family", "")) for row in routes)
    by_target_prover = _target_prover_family_counts(routes)
    by_truth_status = Counter(str(row.get("route_truth_status", "")) for row in routes)
    by_coverage_status = _coverage_status_counts(routes)
    by_split = Counter(row.evaluation_split for row in split_rows)
    payload: dict[str, object] = {
        "schema_version": FORMALIZATION_GAP_PLANNER_BENCHMARK_AUDIT_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "component_name": "formalization_gap_planner_benchmark_audit",
        "formalization_gap_planner_benchmark_dir": str(benchmark_dir),
        "formalization_gap_planner_benchmark_manifest": str(manifest_path),
        "n_checks": len(checks),
        "n_ok": sum(1 for check in checks if check.ok),
        "n_failed": sum(1 for check in checks if not check.ok),
        "n_routes": len(routes),
        "n_route_row_schema_valid": sum(
            1
            for check in checks
            if check.check_name.startswith("route_")
            and check.check_name.endswith("_schema_valid")
            and check.ok
        ),
        "n_route_row_schema_invalid": sum(
            1
            for check in checks
            if check.check_name.startswith("route_")
            and check.check_name.endswith("_schema_valid")
            and not check.ok
        ),
        "n_theorem_families": len({key for key in by_family if key}),
        "n_target_prover_families": len({key for key in by_target_prover if key}),
        "n_routes_with_target_prover_family": sum(
            1 for row in routes if _target_prover_key(row.get("target_prover_family", ""))
        ),
        "n_coverage_statuses": len({key for key in by_coverage_status if key}),
        "n_routes_with_source_refs": sum(
            1 for row in routes if _str_tuple(row.get("source_refs", []))
        ),
        "n_kernel_verified_routes": sum(1 for row in routes if row.get("kernel_verified")),
        "n_kernel_verification_witnesses": sum(
            len(_dict_rows(row.get("kernel_verification_witnesses", [])))
            for row in routes
        ),
        "n_kernel_verified_routes_with_witnesses": sum(
            1
            for row in routes
            if row.get("kernel_verified")
            and _dict_rows(row.get("kernel_verification_witnesses", []))
        ),
        "n_kernel_verified_routes_missing_witnesses": sum(
            1
            for row in routes
            if row.get("kernel_verified")
            and not _dict_rows(row.get("kernel_verification_witnesses", []))
        ),
        "n_routes_with_expected_residuals": sum(
            1 for row in routes if _str_tuple(row.get("expected_residual_primitives", []))
        ),
        "n_expected_residual_primitives": sum(
            len(_str_tuple(row.get("expected_residual_primitives", [])))
            for row in routes
        ),
        "n_derived_split_rows": len(split_rows),
        "n_evaluation_splits": len({row.evaluation_split for row in split_rows}),
        "by_check_category": dict(sorted(by_category.items())),
        "by_theorem_family": dict(sorted(by_family.items())),
        "by_target_prover_family": by_target_prover,
        "by_route_truth_status": dict(sorted(by_truth_status.items())),
        "by_coverage_status": dict(sorted(by_coverage_status.items())),
        "by_evaluation_split": dict(sorted(by_split.items())),
        "derived_split_rows": [asdict(row) for row in split_rows],
        "all_ok": not errors and bool(checks) and all(check.ok for check in checks),
        "errors": errors,
        "checks": [asdict(check) for check in checks],
        "benchmark_audit_fingerprint": stable_hash(
            [[asdict(check) for check in checks], [asdict(row) for row in split_rows]]
        ),
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
        "benchmark_proof_evidence_boundary": str(
            manifest.get("proof_evidence_boundary", BENCHMARK_PROOF_EVIDENCE_BOUNDARY)
        ),
        "limitations": (
            "benchmark audit validates route-truth data quality only",
            "expert-curated route truth is not a substitute for target-prover kernel replay",
            "derived evaluation splits are deterministic packaging metadata, not a statistical guarantee",
        ),
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "formalization_gap_planner_benchmark_audit_manifest.json").write_text(
            json.dumps(payload, indent=2, default=str),
            encoding="utf-8",
        )
        (out_dir / "formalization_gap_planner_benchmark_audit.jsonl").write_text(
            "\n".join(json.dumps(asdict(row), sort_keys=True) for row in split_rows)
            + ("\n" if split_rows else ""),
            encoding="utf-8",
        )
        (out_dir / "formalization_gap_planner_benchmark_audit.md").write_text(
            _markdown_report(payload),
            encoding="utf-8",
        )
    return payload


def _manifest_checks(
    manifest_path: Path,
    manifest: dict[str, Any],
    routes: list[dict[str, Any]],
) -> list[FormalizationGapPlannerBenchmarkAuditCheck]:
    boundary = str(manifest.get("proof_evidence_boundary", ""))
    row_target_counts = _target_prover_family_counts(routes)
    manifest_target_counts = _count_map(manifest.get("by_target_prover_family", {}))
    return [
        _check(
            "benchmark_manifest_exists",
            "manifest",
            "manifest file exists",
            str(manifest_path.exists()),
            manifest_path.exists(),
        ),
        _check(
            "benchmark_component",
            "manifest",
            "formalization_gap_planner_benchmark",
            str(manifest.get("component_name", "")),
            manifest.get("component_name") == "formalization_gap_planner_benchmark",
        ),
        _check(
            "benchmark_all_ok",
            "manifest",
            "all_ok true",
            str(manifest.get("all_ok", "")),
            bool(manifest.get("all_ok", False)),
        ),
        _check(
            "benchmark_schema",
            "manifest",
            PORTABLE_FORMALIZATION_GAP_PLAN_SCHEMA_ID,
            str(manifest.get("portable_schema_id", "")),
            manifest.get("portable_schema_id") == PORTABLE_FORMALIZATION_GAP_PLAN_SCHEMA_ID,
        ),
        _check(
            "benchmark_routes_present",
            "manifest",
            "at least three route-truth rows",
            str(len(routes)),
            len(routes) >= 3,
        ),
        _check(
            "benchmark_target_prover_summary",
            "manifest",
            "manifest target-prover family counts match route rows",
            f"manifest={manifest_target_counts}; rows={row_target_counts}",
            manifest_target_counts == row_target_counts
            and int(manifest.get("n_target_prover_families", 0) or 0)
            == len(row_target_counts),
        ),
        _check(
            "benchmark_boundary",
            "proof_boundary",
            "not theorem proof evidence",
            boundary[:160],
            "not theorem proof evidence" in boundary,
        ),
    ]


def _artifact_checks(
    ground_truth_path: Path,
    routes_jsonl_path: Path,
    route_schema_path: Path,
    report_path: Path,
) -> list[FormalizationGapPlannerBenchmarkAuditCheck]:
    return [
        _check(
            "benchmark_ground_truth_copy",
            "artifact",
            "ground truth copy exists",
            str(ground_truth_path.exists()),
            ground_truth_path.exists(),
        ),
        _check(
            "benchmark_routes_jsonl",
            "artifact",
            "routes jsonl exists",
            str(routes_jsonl_path.exists()),
            routes_jsonl_path.exists(),
        ),
        _check(
            "benchmark_route_schema",
            "artifact",
            "route-row schema exists",
            str(route_schema_path.exists()),
            route_schema_path.exists(),
        ),
        _check(
            "benchmark_report",
            "artifact",
            "markdown report exists",
            str(report_path.exists()),
            report_path.exists(),
        ),
    ]


def _coverage_checks(routes: list[dict[str, Any]]) -> list[FormalizationGapPlannerBenchmarkAuditCheck]:
    families = {str(row.get("theorem_family", "")) for row in routes if row.get("theorem_family")}
    target_families = _target_prover_family_counts(routes)
    statuses = set(_coverage_status_counts(routes))
    truth_statuses = {
        str(row.get("route_truth_status", "")) for row in routes if row.get("route_truth_status")
    }
    return [
        _check(
            "benchmark_theorem_family_floor",
            "coverage",
            "at least three theorem families",
            ",".join(sorted(families)),
            len(families) >= 3,
        ),
        _check(
            "benchmark_target_prover_family_present",
            "coverage",
            "every route declares a target prover family",
            str(target_families),
            bool(target_families)
            and sum(target_families.values()) == len(routes)
            and "unknown" not in target_families,
        ),
        _check(
            "benchmark_core_coverage_statuses",
            "coverage",
            ",".join(CORE_COVERAGE_STATUSES),
            ",".join(sorted(statuses)),
            set(CORE_COVERAGE_STATUSES).issubset(statuses),
        ),
        _check(
            "benchmark_route_truth_statuses_known",
            "coverage",
            ",".join(ROUTE_TRUTH_STATUSES),
            ",".join(sorted(truth_statuses)),
            truth_statuses.issubset(set(ROUTE_TRUTH_STATUSES)) and bool(truth_statuses),
        ),
        _check(
            "benchmark_source_ref_floor",
            "coverage",
            "every route has at least two source refs",
            str(
                [
                    len(_str_tuple(row.get("source_refs", [])))
                    for row in routes
                ]
            ),
            all(len(_str_tuple(row.get("source_refs", []))) >= 2 for row in routes),
        ),
    ]


def _route_checks(routes: list[dict[str, Any]]) -> list[FormalizationGapPlannerBenchmarkAuditCheck]:
    checks: list[FormalizationGapPlannerBenchmarkAuditCheck] = []
    route_schema = benchmark_route_row_json_schema()
    seen_names: set[str] = set()
    for idx, row in enumerate(routes):
        schema_errors = validate_benchmark_route_row(row, route_schema)
        display_name = str(row.get("display_name", ""))
        required = set(_str_tuple(row.get("required_primitives", [])))
        existing = set(_str_tuple(row.get("actual_existing_reuse_primitives", [])))
        delta = set(_str_tuple(row.get("actual_delta_primitives", [])))
        residual = set(_str_tuple(row.get("expected_residual_primitives", [])))
        coverage = row.get("coverage_by_primitive", {})
        coverage_keys = set(str(key) for key in coverage) if isinstance(coverage, dict) else set()
        classified = existing | delta
        duplicate_name = display_name in seen_names
        seen_names.add(display_name)
        route_label = display_name or f"row:{idx}"
        kernel_verified = bool(row.get("kernel_verified", False))
        kernel_truth_status = row.get("route_truth_status") == "kernel_verified_route_truth"
        witnesses = _dict_rows(row.get("kernel_verification_witnesses", []))
        checks.extend(
            [
                _check(
                    f"route_{idx}_schema_valid",
                    "route_contract",
                    "route row satisfies benchmark route schema",
                    "; ".join(schema_errors) if schema_errors else "ok",
                    not schema_errors,
                    errors=schema_errors,
                ),
                _check(
                    f"route_{idx}_ok",
                    "route_contract",
                    "normalized route truth row has ok=true",
                    "; ".join(_str_tuple(row.get("errors", []))) or str(row.get("ok", "")),
                    bool(row.get("ok", False)),
                    errors=_str_tuple(row.get("errors", [])),
                ),
                _check(
                    f"route_{idx}_identity",
                    "route_contract",
                    "display name and theorem family present",
                    route_label,
                    bool(display_name) and bool(row.get("theorem_family")),
                ),
                _check(
                    f"route_{idx}_unique_display_name",
                    "route_contract",
                    "display names unique",
                    display_name,
                    bool(display_name) and not duplicate_name,
                ),
                _check(
                    f"route_{idx}_required_primitives",
                    "route_contract",
                    "required primitives present",
                    f"{route_label}: {len(required)}",
                    bool(required),
                ),
                _check(
                    f"route_{idx}_classified_primitives_cover_required",
                    "route_contract",
                    "existing reuse plus delta equals required primitives",
                    f"{route_label}: missing={sorted(required - classified)} extra={sorted(classified - required)}",
                    classified == required,
                ),
                _check(
                    f"route_{idx}_coverage_labels_cover_required",
                    "route_contract",
                    "coverage labels cover required primitives",
                    f"{route_label}: missing={sorted(required - coverage_keys)}",
                    required.issubset(coverage_keys),
                ),
                _check(
                    f"route_{idx}_expected_residuals_are_required",
                    "route_contract",
                    "expected residual primitives are a subset of required primitives",
                    f"{route_label}: extra={sorted(residual - required)} residual={sorted(residual)}",
                    residual.issubset(required),
                ),
                _check(
                    f"route_{idx}_source_refs",
                    "route_contract",
                    "at least two source refs",
                    f"{route_label}: {len(_str_tuple(row.get('source_refs', [])))}",
                    len(_str_tuple(row.get("source_refs", []))) >= 2,
                ),
                _check(
                    f"route_{idx}_kernel_verified_status_consistent",
                    "proof_boundary",
                    "kernel_verified iff route_truth_status is kernel_verified_route_truth",
                    f"{route_label}: kernel={row.get('kernel_verified')} status={row.get('route_truth_status')}",
                    kernel_verified == kernel_truth_status,
                ),
                _check(
                    f"route_{idx}_kernel_verification_witness",
                    "proof_boundary",
                    "kernel-verified route truth carries at least one kernel witness",
                    f"{route_label}: witnesses={len(witnesses)} kernel={kernel_verified}",
                    (not kernel_verified) or bool(witnesses),
                ),
            ]
        )
    return checks


def _split_checks(
    split_rows: tuple[FormalizationGapPlannerBenchmarkSplitRow, ...],
    routes: list[dict[str, Any]],
) -> list[FormalizationGapPlannerBenchmarkAuditCheck]:
    splits = {row.evaluation_split for row in split_rows}
    return [
        _check(
            "benchmark_split_rows_cover_routes",
            "splits",
            "one derived split row per route",
            f"{len(split_rows)}/{len(routes)}",
            len(split_rows) == len(routes),
        ),
        _check(
            "benchmark_split_floor",
            "splits",
            "at least two derived evaluation splits",
            ",".join(sorted(splits)),
            len(splits) >= 2,
        ),
        _check(
            "benchmark_heldout_split_present",
            "splits",
            "heldout_eval split present",
            ",".join(sorted(splits)),
            "heldout_eval" in splits,
        ),
    ]


def _split_row(
    idx: int,
    row: dict[str, Any],
) -> FormalizationGapPlannerBenchmarkSplitRow:
    coverage_statuses = set()
    coverage = row.get("coverage_by_primitive", {})
    if isinstance(coverage, dict):
        coverage_statuses = {str(value) for value in coverage.values()}
    if "source_discovery_needed" in coverage_statuses:
        split = "source_gap_stress"
        reason = "contains source_discovery_needed coverage labels"
    elif idx % 3 == 2:
        split = "heldout_eval"
        reason = "deterministic every-third route holdout assignment"
    else:
        split = "public_dev"
        reason = "deterministic public development assignment"
    return FormalizationGapPlannerBenchmarkSplitRow(
        schema_version=FORMALIZATION_GAP_PLANNER_BENCHMARK_AUDIT_SCHEMA_VERSION,
        split_row_id="formalization_gap_planner_benchmark_split:"
        + stable_hash([idx, row.get("display_name", ""), split])[:16],
        display_name=str(row.get("display_name", "")),
        theorem_family=str(row.get("theorem_family", "")),
        evaluation_split=split,
        split_reason=reason,
        route_truth_status=str(row.get("route_truth_status", "")),
        n_required_primitives=len(_str_tuple(row.get("required_primitives", []))),
        n_source_refs=len(_str_tuple(row.get("source_refs", []))),
        kernel_verified=bool(row.get("kernel_verified", False)),
        n_kernel_verification_witnesses=len(
            _dict_rows(row.get("kernel_verification_witnesses", []))
        ),
    )


def _coverage_status_counts(routes: list[dict[str, Any]]) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for row in routes:
        coverage = row.get("coverage_by_primitive", {})
        if isinstance(coverage, dict):
            counter.update(str(value) for value in coverage.values() if str(value))
    return dict(sorted(counter.items()))


def _target_prover_family_counts(routes: list[dict[str, Any]]) -> dict[str, int]:
    return dict(
        sorted(
            Counter(
                _target_prover_key(row.get("target_prover_family", "")) or "unknown"
                for row in routes
            ).items()
        )
    )


def _target_prover_key(value: object) -> str:
    key = str(value).strip().lower().replace("-", "_")
    aliases = {
        "lean": "lean4",
        "lean_4": "lean4",
        "coq": "rocq",
        "coq8": "rocq",
    }
    key = aliases.get(key, key)
    if key.startswith("lean4"):
        return "lean4"
    if key.startswith("rocq"):
        return "rocq"
    if key.startswith("isabelle"):
        return "isabelle"
    if key.startswith("agda"):
        return "agda"
    if key.startswith("hol4"):
        return "hol4"
    return key


def _count_map(value: Any) -> dict[str, int]:
    if not isinstance(value, dict):
        return {}
    result: dict[str, int] = {}
    for key, item in value.items():
        parsed = _int_or_none(item)
        if parsed is None:
            continue
        result[str(key)] = parsed
    return dict(sorted(result.items()))


def _int_or_none(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _check(
    check_name: str,
    category: str,
    expected: str,
    observed: str,
    ok: bool,
    *,
    severity: str = "error",
    errors: tuple[str, ...] = (),
) -> FormalizationGapPlannerBenchmarkAuditCheck:
    return FormalizationGapPlannerBenchmarkAuditCheck(
        schema_version=FORMALIZATION_GAP_PLANNER_BENCHMARK_AUDIT_SCHEMA_VERSION,
        check_id="formalization_gap_planner_benchmark_audit:"
        + stable_hash([check_name, category, expected])[:16],
        check_name=check_name,
        category=category,
        expected=expected,
        observed=observed,
        ok=ok,
        severity=severity,
        errors=errors if not ok else (),
    )


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


def _dict_rows(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [row for row in value if isinstance(row, dict)]


def _str_tuple(values: Any) -> tuple[str, ...]:
    if isinstance(values, str):
        return (values,) if values else tuple()
    if not isinstance(values, (list, tuple, set)):
        return tuple()
    return tuple(dict.fromkeys(str(item) for item in values if str(item)))


def _markdown_report(payload: dict[str, object]) -> str:
    lines = [
        "# Formalization Gap Planner Benchmark Audit",
        "",
        f"- Checks: {payload.get('n_ok')}/{payload.get('n_checks')}",
        f"- Failed: {payload.get('n_failed')}",
        f"- Routes: {payload.get('n_routes')}",
        f"- Route row schema valid: {payload.get('n_route_row_schema_valid')}/{payload.get('n_routes')}",
        f"- Theorem families: {payload.get('n_theorem_families')}",
        f"- Target prover families: {payload.get('by_target_prover_family')}",
        f"- Coverage statuses: {payload.get('n_coverage_statuses')}",
        f"- Evaluation splits: {payload.get('n_evaluation_splits')}",
        f"- Kernel-verified routes: {payload.get('n_kernel_verified_routes')}",
        f"- Kernel verification witnesses: {payload.get('n_kernel_verification_witnesses')}",
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
        if isinstance(check, dict) and not check.get("ok")
    ]
    if not failed:
        lines.append("- None")
    for check in failed:
        lines.append(
            f"- `{check.get('check_name')}` expected={check.get('expected')} "
            f"observed={check.get('observed')}"
        )
    lines.extend(["", "## Derived Splits", ""])
    for row in payload.get("derived_split_rows", []):
        if not isinstance(row, dict):
            continue
        lines.append(
            f"- `{row.get('display_name')}` split={row.get('evaluation_split')} "
            f"reason={row.get('split_reason')}"
        )
    return "\n".join(lines) + "\n"
