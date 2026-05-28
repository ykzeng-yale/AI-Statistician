from __future__ import annotations

import importlib.util
import json
import os
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping

from .algorithms import all_algorithms
from .proof_bank import all_obligations


MANIFEST_NAMES = {
    "algorithm_audit_manifest.json",
    "evaluation_manifest.json",
    "intake_audit_manifest.json",
    "manifest.json",
    "proof_audit_manifest.json",
    "retrieval_audit_manifest.json",
    "system_audit_manifest.json",
    "trace_audit_manifest.json",
}


@dataclass(frozen=True)
class DoctorCheck:
    name: str
    status: str
    required: bool
    detail: str


def build_doctor_report(
    *,
    root: Path | None = None,
    env_file: Path | None = None,
    environ: Mapping[str, str] | None = None,
    max_manifests: int = 12,
) -> dict[str, object]:
    """Inspect local readiness without running expensive Lean/LLM work."""

    project_root = (root or Path.cwd()).resolve()
    env = dict(os.environ if environ is None else environ)
    env_path = (env_file or project_root / ".env")
    if not env_path.is_absolute():
        env_path = project_root / env_path
    dotenv_values = _read_dotenv(env_path)

    checks = [
        _python_check(),
        _import_check("numpy", required=True, label="required package: numpy"),
        _path_check(project_root / "ai_statistician", required=True, label="package directory"),
        _path_check(project_root / "examples" / "questions.json", required=True, label="example questions"),
        _registry_check("proof bank obligations", len(all_obligations())),
        _registry_check("vetted algorithms", len(all_algorithms())),
        _path_check(env_path, required=False, label=".env file"),
        _key_check("AXLE_API_KEY", env, dotenv_values, label="AXLE key"),
        _import_check("axle", required=False, label="optional package: axle"),
        _key_check("ANTHROPIC_API_KEY", env, dotenv_values, label="Anthropic key"),
        _import_check("anthropic", required=False, label="optional package: anthropic"),
        _openprover_check(env),
        _path_check(
            project_root / "docs" / "production_design.md",
            required=False,
            label="production design doc",
        ),
    ]
    manifests = _latest_manifests(project_root / "runs", max_count=max_manifests)
    latest_system_audit = next(
        (row for row in manifests if row["name"] == "system_audit_manifest.json"),
        None,
    )
    if latest_system_audit:
        checks.append(
            DoctorCheck(
                name="latest system audit",
                status="OK",
                required=False,
                detail=str(latest_system_audit["path"]),
            )
        )
    else:
        checks.append(
            DoctorCheck(
                name="latest system audit",
                status="WARN",
                required=False,
                detail="no runs/**/system_audit_manifest.json found",
            )
        )

    required_ok = all(check.status != "FAIL" for check in checks if check.required)
    axle_key = _env_presence("AXLE_API_KEY", env, dotenv_values)["present"]
    anthropic_key = _env_presence("ANTHROPIC_API_KEY", env, dotenv_values)["present"]
    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "root": str(project_root),
        "env_file": str(env_path),
        "summary": {
            "required_ok": required_ok,
            "real_lean_ready": axle_key and _has_module("axle"),
            "llm_theory_ready": anthropic_key and _has_module("anthropic"),
            "openprover_available": _openprover_path(env).exists(),
            "n_obligations": len(all_obligations()),
            "n_algorithms": len(all_algorithms()),
            "latest_system_audit": latest_system_audit,
        },
        "checks": [asdict(check) for check in checks],
        "latest_manifests": manifests,
    }
    return report


def write_doctor_manifest(report: dict[str, object], out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "doctor_manifest.json"
    path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    return path


def _read_dotenv(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip().strip("'\"")
    return values


def _env_presence(key: str, env: Mapping[str, str], dotenv_values: Mapping[str, str]) -> dict[str, object]:
    if env.get(key):
        return {"present": True, "source": "environment"}
    if dotenv_values.get(key):
        return {"present": True, "source": ".env"}
    return {"present": False, "source": None}


def _key_check(
    key: str,
    env: Mapping[str, str],
    dotenv_values: Mapping[str, str],
    *,
    label: str,
) -> DoctorCheck:
    presence = _env_presence(key, env, dotenv_values)
    if presence["present"]:
        return DoctorCheck(label, "OK", False, f"{key} present via {presence['source']} (value redacted)")
    return DoctorCheck(label, "WARN", False, f"{key} not found; real external path will be unavailable")


def _python_check() -> DoctorCheck:
    version = ".".join(str(part) for part in sys.version_info[:3])
    status = "OK" if sys.version_info >= (3, 11) else "FAIL"
    return DoctorCheck("python version", status, True, f"Python {version} at {sys.executable}")


def _has_module(module: str) -> bool:
    return importlib.util.find_spec(module) is not None


def _import_check(module: str, *, required: bool, label: str) -> DoctorCheck:
    if _has_module(module):
        return DoctorCheck(label, "OK", required, f"module {module!r} is importable")
    status = "FAIL" if required else "WARN"
    return DoctorCheck(label, status, required, f"module {module!r} is not importable")


def _path_check(path: Path, *, required: bool, label: str) -> DoctorCheck:
    if path.exists():
        return DoctorCheck(label, "OK", required, str(path.resolve()))
    status = "FAIL" if required else "WARN"
    return DoctorCheck(label, status, required, f"missing: {path.resolve()}")


def _registry_check(label: str, count: int) -> DoctorCheck:
    status = "OK" if count > 0 else "FAIL"
    return DoctorCheck(label, status, True, f"{count} registered")


def _openprover_path(env: Mapping[str, str]) -> Path:
    return Path(env.get("OPENPROVER_SRC", "/Users/yukang/Documents/OpenProver/src")).expanduser()


def _openprover_check(env: Mapping[str, str]) -> DoctorCheck:
    path = _openprover_path(env)
    if path.exists():
        return DoctorCheck("OpenProver checkout", "OK", False, str(path.resolve()))
    return DoctorCheck("OpenProver checkout", "WARN", False, f"not found at {path}")


def _latest_manifests(run_dir: Path, *, max_count: int) -> list[dict[str, object]]:
    if not run_dir.exists():
        return []
    rows: list[dict[str, object]] = []
    for path in run_dir.rglob("*.json"):
        if path.name not in MANIFEST_NAMES:
            continue
        stat = path.stat()
        rows.append(
            {
                "name": path.name,
                "path": str(path.resolve()),
                "modified_at": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
                "size_bytes": stat.st_size,
            }
        )
    return sorted(rows, key=lambda row: str(row["modified_at"]), reverse=True)[:max_count]
