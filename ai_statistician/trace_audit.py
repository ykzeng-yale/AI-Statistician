from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path


REQUIRED_TRACE_KEYS = {
    "trace_version",
    "created_at",
    "provenance",
    "question",
    "estimator",
    "proofs",
    "algorithm",
    "simulation",
    "status",
}


@dataclass(frozen=True)
class TraceAuditRow:
    question_id: str
    trace_path: str
    ok: bool
    errors: tuple[str, ...] = ()


def audit_run_traces(run_dir: Path, out_dir: Path | None = None) -> dict[str, object]:
    """Validate per-question traces against their run manifest."""

    manifest_path = run_dir / "manifest.json"
    rows: list[TraceAuditRow] = []
    manifest_errors: list[str] = []
    if not manifest_path.exists():
        manifest_errors.append(f"missing run manifest: {manifest_path}")
        manifest: dict[str, object] = {}
        summaries: list[dict[str, object]] = []
    else:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        summaries = list(manifest.get("questions", []))

    manifest_provenance = manifest.get("provenance")
    n_accepted = 0
    n_formal_blocked = 0
    n_simulation_blocked = 0
    for summary in summaries:
        question_id = str(summary.get("question", "<missing>"))
        trace_path = run_dir / f"{question_id}.json"
        errors: list[str] = []
        data: dict[str, object] = {}
        if not trace_path.exists():
            errors.append(f"missing trace file: {trace_path}")
        else:
            try:
                data = json.loads(trace_path.read_text(encoding="utf-8"))
            except Exception as exc:
                errors.append(f"failed to parse trace JSON: {type(exc).__name__}: {exc}")
        if data:
            errors.extend(_validate_trace(data, question_id, summary, manifest_provenance))
            status = data.get("status")
            if status == "ACCEPTED":
                n_accepted += 1
            elif status == "FORMAL_BLOCKED":
                n_formal_blocked += 1
            elif status == "SIMULATION_BLOCKED":
                n_simulation_blocked += 1
        rows.append(
            TraceAuditRow(
                question_id=question_id,
                trace_path=str(trace_path),
                ok=not errors,
                errors=tuple(errors),
            )
        )

    if manifest:
        if int(manifest.get("n_questions", -1)) != len(rows):
            manifest_errors.append("manifest n_questions does not match trace rows")
        if int(manifest.get("n_accepted", -1)) != n_accepted:
            manifest_errors.append("manifest n_accepted does not match trace statuses")
        if int(manifest.get("n_formal_blocked", -1)) != n_formal_blocked:
            manifest_errors.append("manifest n_formal_blocked does not match trace statuses")
        if int(manifest.get("n_simulation_blocked", -1)) != n_simulation_blocked:
            manifest_errors.append("manifest n_simulation_blocked does not match trace statuses")

    payload = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "run_dir": str(run_dir),
        "manifest": str(manifest_path),
        "n_traces": len(rows),
        "n_ok": sum(1 for row in rows if row.ok),
        "all_ok": not manifest_errors and all(row.ok for row in rows),
        "manifest_errors": manifest_errors,
        "rows": [asdict(row) for row in rows],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "trace_audit_manifest.json").write_text(
            json.dumps(payload, indent=2, default=str),
            encoding="utf-8",
        )
    return payload


def _validate_trace(
    data: dict[str, object],
    question_id: str,
    summary: dict[str, object],
    manifest_provenance: object,
) -> list[str]:
    errors: list[str] = []
    missing = sorted(REQUIRED_TRACE_KEYS - set(data))
    if missing:
        errors.append(f"missing trace keys: {', '.join(missing)}")
    if data.get("trace_version") != 1:
        errors.append(f"unexpected trace_version: {data.get('trace_version')!r}")
    if manifest_provenance is not None and data.get("provenance") != manifest_provenance:
        errors.append("trace provenance does not match run manifest provenance")

    question = data.get("question")
    if not isinstance(question, dict) or question.get("id") != question_id:
        errors.append("trace question.id does not match filename/manifest")

    if data.get("status") != summary.get("status"):
        errors.append("trace status does not match manifest summary")

    algorithm = data.get("algorithm")
    if not isinstance(algorithm, dict):
        errors.append("algorithm section missing or not an object")
    else:
        if algorithm.get("registry_status") != "vetted":
            errors.append("algorithm registry_status is not vetted")
        implementation_hash = str(algorithm.get("implementation_hash", ""))
        if len(implementation_hash) != 64:
            errors.append("algorithm implementation_hash is not a SHA-256 hex digest")

    proofs = data.get("proofs")
    if not isinstance(proofs, list) or not proofs:
        errors.append("proofs section missing or empty")
    else:
        ok_count = sum(1 for proof in proofs if isinstance(proof, dict) and proof.get("ok") is True)
        expected_formal = summary.get("formal")
        if expected_formal and expected_formal != f"{ok_count}/{len(proofs)}":
            errors.append("proof success count does not match manifest formal summary")
        for idx, proof in enumerate(proofs):
            if not isinstance(proof, dict):
                errors.append(f"proof {idx} is not an object")
                continue
            if not proof.get("obligation_id"):
                errors.append(f"proof {idx} missing obligation_id")
            if not proof.get("verifier"):
                errors.append(f"proof {idx} missing verifier")

    simulation = data.get("simulation")
    if not isinstance(simulation, dict) or not isinstance(simulation.get("metrics"), dict):
        errors.append("simulation metrics missing")
    else:
        metric_keys = {
            "n_runs",
            "n_failed",
            "bias",
            "relative_bias",
            "rmse",
            "empirical_se",
            "mean_estimated_se",
            "coverage_95",
        }
        missing_metrics = sorted(metric_keys - set(simulation["metrics"]))
        if missing_metrics:
            errors.append(f"missing simulation metrics: {', '.join(missing_metrics)}")
    return errors
