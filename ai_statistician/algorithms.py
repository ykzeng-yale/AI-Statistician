from __future__ import annotations

import hashlib
import inspect
import json
import math
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

import numpy as np

from .fingerprint import stable_hash


EstimateFn = Callable[[np.ndarray], dict[str, float]]


@dataclass(frozen=True)
class AlgorithmRecord:
    id: str
    summary: str
    implementation: EstimateFn
    version: str = "v1"
    registry_status: str = "vetted"

    def implementation_hash(self) -> str:
        source = inspect.getsource(self.implementation)
        return hashlib.sha256(source.encode("utf-8")).hexdigest()


@dataclass
class AlgorithmAuditResult:
    algorithm_id: str
    ok: bool
    implementation_hash: str
    checks: list[str]
    errors: list[str]


def sample_mean_normal_ci(data: np.ndarray) -> dict[str, float]:
    n = len(data)
    estimate = float(np.mean(data))
    sd = float(np.std(data, ddof=1)) if n > 1 else 0.0
    se = sd / math.sqrt(n) if n else float("nan")
    return {"estimate": estimate, "se": se, "lo": estimate - 1.96 * se, "hi": estimate + 1.96 * se}


def bernoulli_wilson_ci(data: np.ndarray) -> dict[str, float]:
    n = len(data)
    phat = float(np.mean(data))
    z = 1.96
    denom = 1.0 + z * z / n
    center = (phat + z * z / (2 * n)) / denom
    half = z * math.sqrt((phat * (1 - phat) / n) + (z * z / (4 * n * n))) / denom
    # Report the estimator's asymptotic SE around the point estimator, while
    # coverage uses the Wilson interval.
    se = math.sqrt(max(phat * (1 - phat), 0.0) / n)
    return {"estimate": phat, "se": se, "lo": center - half, "hi": center + half}


def sample_variance_chi_square_ci(data: np.ndarray) -> dict[str, float]:
    n = len(data)
    if n <= 1:
        return {"estimate": float("nan"), "se": float("nan"), "lo": float("nan"), "hi": float("nan")}
    estimate = float(np.var(data, ddof=1))
    df = n - 1
    se = estimate * math.sqrt(2.0 / df)
    q025 = _chi_square_ppf_wilson_hilferty(0.025, df)
    q975 = _chi_square_ppf_wilson_hilferty(0.975, df)
    lo = df * estimate / q975
    hi = df * estimate / q025
    return {"estimate": estimate, "se": se, "lo": lo, "hi": hi}


def constant_mean(data: np.ndarray) -> dict[str, float]:
    estimate = float(np.mean(data))
    return {"estimate": estimate, "se": 0.0, "lo": estimate, "hi": estimate}


ALGORITHMS: dict[str, AlgorithmRecord] = {
    "sample_mean_normal_ci": AlgorithmRecord(
        id="sample_mean_normal_ci",
        summary="sample mean plus normal/t confidence-style standard error",
        implementation=sample_mean_normal_ci,
    ),
    "bernoulli_wilson_ci": AlgorithmRecord(
        id="bernoulli_wilson_ci",
        summary="sample proportion with Wilson score interval",
        implementation=bernoulli_wilson_ci,
    ),
    "sample_variance_chi_square_ci": AlgorithmRecord(
        id="sample_variance_chi_square_ci",
        summary="unbiased normal sample variance with chi-square confidence interval",
        implementation=sample_variance_chi_square_ci,
    ),
    "constant_mean": AlgorithmRecord(
        id="constant_mean",
        summary="constant-valued estimator",
        implementation=constant_mean,
    ),
}


def get_algorithm(algorithm_id: str) -> AlgorithmRecord:
    try:
        return ALGORITHMS[algorithm_id]
    except KeyError as exc:
        supported = ", ".join(sorted(ALGORITHMS))
        raise KeyError(f"unknown algorithm {algorithm_id!r}; supported: {supported}") from exc


def all_algorithms() -> list[AlgorithmRecord]:
    return list(ALGORITHMS.values())


def algorithm_registry_fingerprint() -> str:
    return stable_hash(
        [
            {
                "id": record.id,
                "summary": record.summary,
                "version": record.version,
                "registry_status": record.registry_status,
                "implementation_hash": record.implementation_hash(),
            }
            for record in sorted(all_algorithms(), key=lambda row: row.id)
        ]
    )


def audit_algorithm(record: AlgorithmRecord) -> AlgorithmAuditResult:
    errors: list[str] = []
    checks: list[str] = []
    try:
        if record.id == "sample_mean_normal_ci":
            row = record.implementation(np.array([1.0, 2.0, 3.0, 4.0]))
            _assert_close(row["estimate"], 2.5, errors, "sample mean estimate")
            expected_se = float(np.std([1.0, 2.0, 3.0, 4.0], ddof=1) / math.sqrt(4))
            _assert_close(row["se"], expected_se, errors, "sample mean SE")
            _assert_interval(row, errors, contains=row["estimate"])
            checks.extend(["estimate equals arithmetic mean", "SE uses ddof=1", "CI contains estimate"])
        elif record.id == "bernoulli_wilson_ci":
            row = record.implementation(np.array([1.0, 0.0, 1.0, 1.0, 0.0]))
            _assert_close(row["estimate"], 0.6, errors, "sample proportion estimate")
            _assert_interval(row, errors, contains=row["estimate"], bounds=(0.0, 1.0))
            if not row["se"] > 0:
                errors.append("Wilson SE should be positive for mixed Bernoulli sample")
            checks.extend(["estimate equals sample proportion", "Wilson CI is ordered", "SE positive"])
        elif record.id == "sample_variance_chi_square_ci":
            row = record.implementation(np.array([1.0, 2.0, 3.0, 4.0]))
            expected = float(np.var([1.0, 2.0, 3.0, 4.0], ddof=1))
            _assert_close(row["estimate"], expected, errors, "unbiased sample variance")
            expected_se = expected * math.sqrt(2.0 / 3.0)
            _assert_close(row["se"], expected_se, errors, "sample variance SE")
            _assert_interval(row, errors, contains=row["estimate"])
            checks.extend(["estimate uses ddof=1", "SE uses chi-square variance", "CI contains estimate"])
        elif record.id == "constant_mean":
            row = record.implementation(np.array([3.0, 3.0, 3.0]))
            _assert_close(row["estimate"], 3.0, errors, "constant estimate")
            _assert_close(row["se"], 0.0, errors, "constant SE")
            _assert_close(row["lo"], 3.0, errors, "constant lower CI")
            _assert_close(row["hi"], 3.0, errors, "constant upper CI")
            checks.extend(["estimate exact", "SE zero", "CI degenerate at constant"])
        else:
            errors.append(f"no audit case registered for {record.id}")
    except Exception as exc:
        errors.append(f"{type(exc).__name__}: {exc}")
    return AlgorithmAuditResult(
        algorithm_id=record.id,
        ok=not errors,
        implementation_hash=record.implementation_hash(),
        checks=checks,
        errors=errors,
    )


def audit_algorithm_registry(out_dir: Path | None = None) -> dict[str, object]:
    results = [audit_algorithm(record) for record in all_algorithms()]
    payload = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "registry_fingerprint": algorithm_registry_fingerprint(),
        "n_algorithms": len(results),
        "n_ok": sum(1 for result in results if result.ok),
        "all_ok": all(result.ok for result in results),
        "algorithms": [asdict(result) for result in results],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "algorithm_audit_manifest.json").write_text(
            json.dumps(payload, indent=2, default=str),
            encoding="utf-8",
        )
    return payload


def _assert_close(actual: float, expected: float, errors: list[str], label: str, tol: float = 1e-10) -> None:
    if not math.isfinite(actual) or abs(actual - expected) > tol:
        errors.append(f"{label}: got {actual}, expected {expected}")


def _assert_interval(
    row: dict[str, float],
    errors: list[str],
    *,
    contains: float | None = None,
    bounds: tuple[float, float] | None = None,
) -> None:
    lo = float(row["lo"])
    hi = float(row["hi"])
    if not lo <= hi:
        errors.append(f"interval not ordered: lo={lo}, hi={hi}")
    if contains is not None and not lo <= contains <= hi:
        errors.append(f"interval [{lo}, {hi}] does not contain {contains}")
    if bounds is not None:
        lower, upper = bounds
        if lo < lower or hi > upper:
            errors.append(f"interval [{lo}, {hi}] outside [{lower}, {upper}]")


def _chi_square_ppf_wilson_hilferty(p: float, df: int) -> float:
    if df <= 0:
        return float("nan")
    if p == 0.025:
        z = -1.959963984540054
    elif p == 0.975:
        z = 1.959963984540054
    else:
        raise ValueError("only 0.025 and 0.975 chi-square quantiles are used")
    term = 1.0 - 2.0 / (9.0 * df) + z * math.sqrt(2.0 / (9.0 * df))
    return df * max(term, 1e-12) ** 3
